"""Unit tests for text syntax version 0: tokenizer, parser, renderer.

The acceptance tests are in ``tests/test_syntax.py``; these pin each
construct of docs/syntax.md on its own.
"""

import unittest

from semiroh import CellDeclaration, EntityID, IntRange, IsKind, Runtime
from semiroh.cells import cell_declaration
from semiroh.examples._support import program
from semiroh.lang import Function, function_of, links, load, run
from semiroh.relations import relation_of
from semiroh.syntax import SourceError, parse, render, render_program, tokenize

X, Y, Z = ("arg", "x"), ("arg", "y"), ("arg", "z")
ONE, TWO = ("lit", 1), ("lit", 2)


def kinds(text):
    return [(token.kind, token.value) for token in tokenize(text)]


def function(text, name="f"):
    return function_of(parse(text).values[EntityID(name)])


def body(source, params="x, y", extra=""):
    """The body of ``fn f(params)`` whose text is ``source`` (one line)."""

    return function(f"{extra}fn f({params}):\n    {source}\n").body


def error(text):
    with_error = None

    try:
        parse(text)
    except SourceError as caught:
        with_error = caught

    if with_error is None:
        raise AssertionError(f"no SourceError for {text!r}")

    return with_error


def links_of(state, name):
    relation = relation_of(state.values[EntityID(f"{name}.links")])
    return {role: target.value for role, target in relation.roles.items()}


def text_of(source):
    return render_program(load(parse(source)))


class TokenizerTests(unittest.TestCase):
    def test_tokens_and_blocks(self) -> None:
        self.assertEqual(
            kinds("fn f(x):\n    x  # comment\n\n    # only a comment\ny\n"),
            [
                ("name", "fn"), ("name", "f"), ("op", "("), ("name", "x"), ("op", ")"),
                ("op", ":"), ("newline", None),
                ("indent", None), ("name", "x"), ("newline", None),
                ("dedent", None), ("name", "y"), ("newline", None),
                ("eof", None),
            ],
        )

    def test_dedents_close_every_open_block(self) -> None:
        tokens = kinds("a:\n    b:\n        c\n")

        self.assertEqual([kind for kind, _ in tokens[-4:]], ["newline", "dedent", "dedent", "eof"])

    def test_operators_and_numbers(self) -> None:
        self.assertEqual(
            [value for _, value in kinds("0..100 == = < + - * . , :")[:-2]],
            [0, "..", 100, "==", "=", "<", "+", "-", "*", ".", ",", ":"],
        )

    def test_positions_are_one_based(self) -> None:
        token = tokenize("ab  cd")[1]

        self.assertEqual((token.value, token.line, token.column), ("cd", 1, 5))

    def test_strings_are_json(self) -> None:
        self.assertEqual(kinds('"a\\"b\\n\\u0041 привет"')[0], ("string", 'a"b\nA привет'))

    def test_backquoted_names(self) -> None:
        token = tokenize("`a.b\\`c` `len`")[0]

        self.assertEqual((token.kind, token.value, token.quoted), ("name", "a.b`c", True))
        self.assertTrue(tokenize("`len`")[0].quoted)
        self.assertFalse(tokenize("len")[0].quoted)

    def test_bad_text_is_rejected_with_a_position(self) -> None:
        for text, line, column in (
            ("a\n\tb", 2, 1),  # tab indentation
            ("a\n    b\n  c", 3, 3),  # dedent to no level
            ('a "b', 1, 3),  # unterminated string
            ('"\\x"', 1, 1),  # bad escape
            ("`", 1, 1),  # unterminated name
            ("``", 1, 1),  # empty name
            ("12ab", 1, 1),  # number run into letters
            ("a $", 1, 3),  # unknown character
            ("a\t+ b", 1, 2),  # tab inside a line
        ):
            with self.subTest(text=text):
                with self.assertRaises(SourceError) as caught:
                    tokenize(text)

                self.assertEqual((caught.exception.line, caught.exception.column), (line, column))


class ExpressionTests(unittest.TestCase):
    def test_literals(self) -> None:
        self.assertEqual(body("(1, -2, true, false, none)"), (
            "tuple", ONE, ("lit", -2), ("lit", True), ("lit", False), ("lit", None),
        ))
        self.assertEqual(body('"a\\"b\\u0041 привет"'), ("lit", 'a"bA привет'))

    def test_tuples_and_groups(self) -> None:
        self.assertEqual(body("()"), ("tuple",))
        self.assertEqual(body("(x,)"), ("tuple", X))
        self.assertEqual(body("(x, y,)"), ("tuple", X, Y))
        self.assertEqual(body("(x)"), X)

    def test_precedence_and_associativity(self) -> None:
        self.assertEqual(body("x + y * 2"), ("add", X, ("mul", Y, TWO)))
        self.assertEqual(body("x * y + 2"), ("add", ("mul", X, Y), TWO))
        self.assertEqual(body("(x + y) * 2"), ("mul", ("add", X, Y), TWO))
        self.assertEqual(body("x - y - 1"), ("sub", ("sub", X, Y), ONE))
        self.assertEqual(body("x < y + 1"), ("lt", X, ("add", Y, ONE)))
        self.assertEqual(body("x + 1 == y"), ("eq", ("add", X, ONE), Y))
        self.assertEqual(body("x - -1"), ("sub", X, ("lit", -1)))

    def test_comparisons_are_not_chained(self) -> None:
        for source in ("x < y < 1", "x == y == 1", "x < y == 1", "(x < y) < 1 == 2"):
            with self.subTest(source=source):
                caught = error(f"fn f(x, y):\n    {source}\n")

                self.assertIn("chained", caught.message)
                self.assertEqual(caught.line, 2)

        self.assertEqual(body("(x < y) < 1")[0], "lt")

    def test_inline_if(self) -> None:
        self.assertEqual(body("x if y < 1 else 2"), ("if", ("lt", Y, ONE), X, TWO))
        self.assertEqual(
            body("1 if x < 2 else 3 if x < 4 else 5"),
            ("if", ("lt", X, TWO), ONE, ("if", ("lt", X, ("lit", 4)), ("lit", 3), ("lit", 5))),
        )
        self.assertEqual(
            body("(x if y < 1 else 2) + 1"),
            ("add", ("if", ("lt", Y, ONE), X, TWO), ONE),
        )

    def test_builtin_operations(self) -> None:
        self.assertEqual(body("len(x)"), ("len", X))
        self.assertEqual(body("item(x, 0)"), ("item", X, ("lit", 0)))
        self.assertEqual(body("slice(x, 0, 1)"), ("slice", X, ("lit", 0), ONE))
        self.assertEqual(body("concat(x, y)"), ("concat", X, Y))
        self.assertEqual(body("apply(x, y)"), ("applyv", X, Y))

    def test_wrong_argument_counts_are_source_errors(self) -> None:
        for source in ("len()", "len(x, y)", "item(x)", "slice(x, y)", "concat(x)", "apply(x)"):
            with self.subTest(source=source):
                self.assertEqual(error(f"fn f(x, y):\n    {source}\n").line, 2)

    def test_names(self) -> None:
        text = "cell c: int = 0\nfn g(a):\n    a\n"

        self.assertEqual(body("c", extra=text), ("read", "c"))
        self.assertEqual(body("g(x)", extra=text), ("call", "g", X))
        self.assertEqual(body("x(y, 1)"), ("apply", X, Y, ONE))
        self.assertEqual(body("ref(g)", extra=text), ("ref", "g"))
        self.assertEqual(body("code(g)", extra=text), ("code", "g"))
        self.assertEqual(body("linksof(g)", extra=text), ("linksof", "g"))

    def test_names_may_be_used_before_they_are_declared(self) -> None:
        self.assertEqual(function("fn f():\n    g(1)\n\nfn g(a):\n    a\n").body, ("call", "g", ONE))

    def test_name_rules(self) -> None:
        text = "cell c: int = 0\nfn g(a):\n    a\n"

        for source, why in (
            ("z", "unknown name"),
            ("g", "function read as a value"),
            ("c(1)", "call of a cell"),
            ("len", "reserved word as a name"),
            ("ref(c)", "ref of a cell"),
            ("ref(z)", "ref of an unknown name"),
        ):
            with self.subTest(why=why):
                self.assertEqual(error(f"{text}fn f(x):\n    {source}\n").line, 5)

        self.assertEqual(error("cell c: int = 0\nfn f(c):\n    c\n").line, 2)  # local and global
        self.assertEqual(error("cell c: int = 0\nfn f():\n    let c = 1\n    c\n").line, 3)
        self.assertEqual(error("fn f(x, x):\n    x\n").line, 1)  # duplicate parameter
        self.assertEqual(error("fn f():\n    1\nfn f():\n    2\n").line, 3)  # declared twice

    def test_backquoted_names_are_never_keywords(self) -> None:
        state = parse("fn `a.b`(`len`):\n    `len`\n\nfn f():\n    `a.b`(1)\n")

        self.assertEqual(function_of(state.values[EntityID("a.b")]).params, ("len",))
        self.assertEqual(function_of(state.values[EntityID("a.b")]).body, ("arg", "len"))
        self.assertEqual(function_of(state.values[EntityID("f")]).body, ("call", "a.b", ONE))

    def test_reserved_names_cannot_be_declared_bare(self) -> None:
        for name in ("fn", "cell", "let", "quote", "concat", "true"):
            with self.subTest(name=name):
                self.assertEqual(error(f"fn {name}(x):\n    x\n").line, 1)

        self.assertEqual(error("cell len: int = 0\n").line, 1)
        self.assertEqual(error("fn f(if):\n    1\n").line, 1)


class BlockTests(unittest.TestCase):
    def test_let_wraps_the_rest_of_the_block(self) -> None:
        self.assertEqual(
            function("fn f(x):\n    let a = x + 1\n    let b = a * 2\n    a + b\n").body,
            (
                "let", "a", ("add", X, ONE),
                ("let", "b", ("mul", ("arg", "a"), TWO), ("add", ("arg", "a"), ("arg", "b"))),
            ),
        )

    def test_statements_make_a_seq(self) -> None:
        text = "cell c: int = 0\nfn f():\n    c = 1\n    let a = 2\n    a\n    c\n"

        self.assertEqual(function(text).body, (
            "seq",
            ("write", "c", ONE),
            ("let", "a", TWO, ("seq", ("arg", "a"), ("read", "c"))),
        ))

    def test_let_shadows_and_ends_with_its_block(self) -> None:
        self.assertEqual(
            function("fn f(x):\n    let x = 1\n    x\n").body,
            ("let", "x", ONE, X),
        )
        self.assertEqual(
            error("fn f(x):\n    if x < 1:\n        let a = 1\n        a\n    else:\n        2\n    a\n").line,
            7,
        )

    def test_a_let_value_may_be_a_cell_write(self) -> None:
        self.assertEqual(
            function("cell c: int = 0\nfn f():\n    let v = c = c + 1\n    v\n").body,
            ("let", "v", ("write", "c", ("add", ("read", "c"), ONE)), ("arg", "v")),
        )

    def test_block_if(self) -> None:
        text = "cell c: int = 0\nfn f(x):\n    if x < 1:\n        c = 1\n        2\n    else:\n        3\n    4\n"

        self.assertEqual(function(text).body, (
            "seq",
            ("if", ("lt", X, ONE), ("seq", ("write", "c", ONE), TWO), ("lit", 3)),
            ("lit", 4),
        ))

    def test_bad_blocks(self) -> None:
        for text, line in (
            ("fn f(x):\n    if x < 1:\n        1\n", 2),  # no else
            ("fn f(x):\n    else:\n        1\n", 2),  # else without if
            ("fn f(x):\n    if x < 1:\n    1\n", 3),  # missing indent
            ("fn f(x):\n    1\n        2\n", 3),  # unexpected indent
            ("fn f(x):\n1\n", 2),  # body not indented
            ("    fn f(x):\n        x\n", 1),  # indented declaration
            ("1\n", 1),  # not a declaration
            ("fn f():\n    let y = 1\n    let z = 2\n", 3),  # let at the end
            ("fn f(x):\n    x = 1 = 2\n", 2),  # assignment to a non-cell
            ("cell c: int = 0\nfn f():\n    c = 1 = 2\n", 3),
            ("fn f():\n    1 2\n", 2),  # two expressions on a line
        ):
            with self.subTest(text=text):
                self.assertEqual(error(text).line, line)

    def test_assignment_needs_a_cell(self) -> None:
        for source in ("f = 1", "z = 1"):
            with self.subTest(source=source):
                self.assertEqual(error(f"fn g():\n    1\nfn f(x):\n    {source}\n").line, 4)


class QuoteTests(unittest.TestCase):
    def test_quote_holes_and_template_names(self) -> None:
        text = "cell c: int = 0\nfn g(a):\n    a\n"

        self.assertEqual(body("quote(z + 1)", extra=text), ("quote", ("add", Z, ONE)))
        self.assertEqual(body("quote(c + g(z))", extra=text), ("quote", ("add", ("read", "c"), ("call", "g", Z))))
        self.assertEqual(body("quote(z(1))"), ("quote", ("apply", Z, ONE)))
        self.assertEqual(body("quote(z * unquote(x))"), ("quote", ("mul", Z, ("unquote", X))))
        self.assertEqual(body("quote(literal(x))"), ("quote", ("lit", ("unquote", X))))
        self.assertEqual(body("quote((z, 1))"), ("quote", ("tuple", Z, ONE)))

    def test_holes_are_back_in_the_enclosing_function(self) -> None:
        text = "fn g(a):\n    a\n"

        self.assertEqual(
            body("quote(unquote(g(x)) + literal(y))", extra=text),
            ("quote", ("add", ("unquote", ("call", "g", X)), ("lit", ("unquote", Y)))),
        )
        self.assertEqual(error("fn f(x):\n    quote(unquote(z))\n").line, 2)  # z is unknown out here

    def test_fn_is_a_function_with_a_literal_body(self) -> None:
        self.assertEqual(
            body("fn(z): z * literal(x)"),
            ("function", ("lit", ("z",)), ("quote", ("mul", Z, ("lit", ("unquote", X))))),
        )
        self.assertEqual(body("fn(): 1"), ("function", ("lit", ()), ("quote", ONE)))
        self.assertEqual(
            body("function((\"z\",), quote(z))"),
            ("function", ("tuple", ("lit", "z")), ("quote", Z)),
        )

    def test_fn_parameters_are_checked(self) -> None:
        self.assertEqual(error("cell c: int = 0\nfn f():\n    fn(c): c\n").line, 3)
        self.assertEqual(error("fn f():\n    fn(z, z): z\n").line, 2)

    def test_quote_misuse(self) -> None:
        for source in (
            "unquote(x)",
            "literal(x)",
            "quote(quote(1))",
            "quote(fn(z): z)",
            "quote(unquote(unquote(x)))",
        ):
            with self.subTest(source=source):
                self.assertEqual(error(f"fn f(x):\n    {source}\n").line, 2)

    def test_label_activate_trial(self) -> None:
        text = "fn g(a):\n    a\n"

        self.assertEqual(body("label(step, x + 1)"), ("label", "step", ("add", X, ONE)))
        self.assertEqual(body("label(`a b`, 1)"), ("label", "a b", ONE))
        self.assertEqual(
            body("activate(g = fn(a): a + 1, f.lbl = quote(2))", extra=text),
            (
                "activate",
                "g", ("function", ("lit", ("a",)), ("quote", ("add", ("arg", "a"), ONE))),
                ("f", "lbl"), ("quote", TWO),
            ),
        )
        self.assertEqual(
            body("trial(g(x), g = fn(a): a)", extra=text),
            ("trial", ("call", "g", X), "g", ("function", ("lit", ("a",)), ("quote", ("arg", "a")))),
        )
        self.assertEqual(body("trial(g(x))", extra=text), ("trial", ("call", "g", X)))
        self.assertEqual(error(f"{text}fn f():\n    activate(z = 1)\n").line, 4)
        self.assertEqual(error(f"{text}fn f():\n    activate()\n").line, 4)
        self.assertEqual(error(f"{text}fn f(x):\n    trial(x, g = 1)\n").line, 4)

    def test_raw_is_verbatim(self) -> None:
        self.assertEqual(body('raw(("add", ("lit", 1), ("lit", -2)))'), ("add", ONE, ("lit", -2)))
        self.assertEqual(body('x + raw(("lit", ("a", true, none)))'), ("add", X, ("lit", ("a", True, None))))
        self.assertEqual(body('quote(raw(("lit", (1, 2))))'), ("quote", ("lit", (1, 2))))
        self.assertEqual(error("fn f():\n    raw(5)\n").line, 1)  # a body must be a tuple
        self.assertEqual(error("fn f():\n    raw(<1>)\n").line, 2)

    def test_raw_names_become_links(self) -> None:
        state = parse('cell c: int = 0\nfn f():\n    raw(("read", "c"))\n')

        self.assertEqual(links_of(state, "f"), {"function": "f", "c": "c"})
        self.assertEqual(run(Runtime(load(state)), EntityID("f")), 0)


class DeclarationTests(unittest.TestCase):
    def cell(self, declaration):
        return cell_declaration(parse(f"cell c: {declaration}\n").values[EntityID("c")])

    def test_cell_types(self) -> None:
        self.assertEqual(self.cell("int = 5"), CellDeclaration(IsKind("int"), 5))
        self.assertEqual(self.cell("bool = true"), CellDeclaration(IsKind("bool"), True))
        self.assertEqual(self.cell('str = "a"'), CellDeclaration(IsKind("str"), "a"))
        self.assertEqual(self.cell("tuple = (1, (2, 3), ())"), CellDeclaration(IsKind("tuple"), (1, (2, 3), ())))
        self.assertEqual(self.cell("entity = none"), CellDeclaration(IsKind("entity_id"), None))

    def test_int_ranges(self) -> None:
        self.assertEqual(self.cell("int in 0..100 = 0"), CellDeclaration(IntRange(0, 100), 0))
        self.assertEqual(self.cell("int in -5..-1 = -2"), CellDeclaration(IntRange(-5, -1), -2))
        self.assertEqual(self.cell("int in 0.. = 0"), CellDeclaration(IntRange(0, None), 0))
        self.assertEqual(self.cell("int in ..9 = 0"), CellDeclaration(IntRange(None, 9), 0))
        self.assertEqual(self.cell("int in .. = 0"), CellDeclaration(IntRange(None, None), 0))

    def test_bad_cells(self) -> None:
        for text in (
            "cell c: float = 0\n",
            "cell c: int in 5..1 = 0\n",
            "cell c: int\n",
            "cell c: int = x\n",
            "cell c: int = (1, 2\n",
            "cell c int = 0\n",
            "cell c: int = 0\ncell c: int = 1\n",
        ):
            with self.subTest(text=text):
                self.assertEqual(error(text).line, 1 if text.count("\n") == 1 else 2)

    def test_links_come_from_the_names_a_body_uses(self) -> None:
        state = parse(
            "cell c: int = 0\nfn h():\n    1\nfn f(x):\n    h() + c\nfn g():\n    1\nfn k():\n    len((1,))\n"
        )

        self.assertEqual(links_of(state, "f"), {"function": "f", "c": "c", "h": "h"})
        self.assertNotIn(EntityID("g.links"), state.values)
        self.assertNotIn(EntityID("k.links"), state.values)

    def test_code_installed_into_a_function_names_links_of_that_function(self) -> None:
        text = (
            "fn helper(x):\n    x * 10\n\nfn work(x):\n    x\n\n"
            "fn install():\n    activate(work = fn(x): helper(x))\n"
        )
        state = parse(text)
        rt = Runtime(load(state))

        self.assertEqual(links_of(state, "work"), {"function": "work", "helper": "helper"})

        run(rt, EntityID("install"), may_activate=True)
        self.assertEqual(run(rt, EntityID("work"), 3), 30)

    def test_the_links_entity_avoids_declared_names(self) -> None:
        state = parse("fn g():\n    1\nfn f():\n    g()\nfn `f.links`():\n    1\n")

        self.assertIn(EntityID("f.links.1"), state.values)


class BaseTests(unittest.TestCase):
    BASE = "cell c: int = 0\n\nfn keep():\n    c\n\nfn old():\n    keep()\n\nfn other():\n    old()\n"

    def test_undeclared_entities_of_the_base_are_kept(self) -> None:
        base = parse(self.BASE)
        state = parse("fn old():\n    c + 1\n", base=base)

        self.assertEqual(set(state.values) - set(base.values), set())
        self.assertEqual(state.values[EntityID("keep")], base.values[EntityID("keep")])
        self.assertEqual(state.values[EntityID("keep.links")], base.values[EntityID("keep.links")])
        self.assertEqual(state.values[EntityID("other.links")], base.values[EntityID("other.links")])
        self.assertEqual(function_of(state.values[EntityID("old")]).body, ("add", ("read", "c"), ONE))

    def test_links_of_declared_functions_are_replaced(self) -> None:
        base = parse(self.BASE)
        state = parse("fn old():\n    c + 1\n", base=base)

        self.assertEqual(links_of(base, "old"), {"function": "old", "keep": "keep"})
        self.assertEqual(links_of(state, "old"), {"function": "old", "c": "c"})

    def test_a_replaced_function_runs_in_the_base_program(self) -> None:
        state = parse("fn old():\n    keep() + 5\n", base=parse(self.BASE))

        self.assertEqual(run(Runtime(load(state)), EntityID("other")), 5)

    def test_names_need_the_base(self) -> None:
        self.assertEqual(error("fn f():\n    keep()\n").line, 2)
        state = parse("fn f():\n    keep()\n", base=parse(self.BASE))

        self.assertEqual(function_of(state.values[EntityID("f")]).body, ("call", "keep"))

    def test_a_declaration_replaces_an_entity_of_another_kind(self) -> None:
        state = parse("fn c():\n    1\n", base=parse(self.BASE))

        self.assertEqual(function_of(state.values[EntityID("c")]).body, ONE)


class RenderTests(unittest.TestCase):
    def rendered(self, fns, name="f"):
        """Render function ``name`` of a graph-form program of ``fns``."""

        return render(load(program(fns)), EntityID(name))

    def one(self, params, tree, **targets):
        entities = {EntityID("f"): Function(params, tree)}

        if targets:
            entities[EntityID("f.links")] = links(EntityID("f"), **targets)

        return self.rendered(entities)

    def test_operator_precedence_is_kept_with_parentheses(self) -> None:
        for tree, text in (
            (("mul", ("add", X, Y), Z), "(x + y) * z"),
            (("add", X, ("mul", Y, Z)), "x + y * z"),
            (("sub", ("sub", X, Y), Z), "x - y - z"),
            (("sub", X, ("sub", Y, Z)), "x - (y - z)"),
            (("mul", X, ("mul", Y, Z)), "x * (y * z)"),
            (("add", ("if", ("lt", X, Y), X, Y), Z), "(x if x < y else y) + z"),
            (("lt", ("lt", X, Y), Z), "(x < y) < z"),
            (("eq", ("add", X, ONE), ("lit", -1)), "x + 1 == -1"),
            (("sub", X, ("lit", -1)), "x - -1"),
            (("tuple", ("if", X, ("if", Y, X, Y), ("if", Z, X, Y))), "((x if y else y) if x else x if z else y,)"),
        ):
            with self.subTest(text=text):
                self.assertEqual(self.one(("x", "y", "z"), tree), f"fn f(x, y, z):\n    {text}\n")

    def test_the_last_statement_if_is_a_block_and_a_nested_one_is_inline(self) -> None:
        self.assertEqual(
            self.one(("x", "y"), ("if", X, ("if", Y, ONE, TWO), ("add", ("if", X, ONE, TWO), ONE))),
            "fn f(x, y):\n"
            "    if x:\n"
            "        if y:\n"
            "            1\n"
            "        else:\n"
            "            2\n"
            "    else:\n"
            "        (1 if x else 2) + 1\n",
        )

    def test_statements_lets_and_writes(self) -> None:
        entities = {
            EntityID("c"): CellDeclaration(IsKind("int"), 0),
            EntityID("f"): Function(("x",), (
                "seq",
                ("write", "c", ONE),
                ("seq", ("read", "c"), ("read", "c")),
                ("let", "a", ("write", "c", X), ("let", "b", ("arg", "a"), ("add", ("arg", "a"), ("arg", "b")))),
            )),
            EntityID("f.links"): links(EntityID("f"), c=EntityID("c")),
        }

        self.assertEqual(
            self.rendered(entities),
            "fn f(x):\n    c = 1\n    c\n    c\n    let a = c = x\n    let b = a\n    a + b\n",
        )

    def test_forms_the_syntax_cannot_express_print_as_raw(self) -> None:
        f, c = EntityID("f"), EntityID("c")
        cell = {c: CellDeclaration(IsKind("int"), 0), EntityID("f.links"): links(f, c=c)}

        for tree, text in (
            (("frobnicate", ONE), 'raw(("frobnicate", ("lit", 1)))'),
            (("add", ONE), 'raw(("add", ("lit", 1)))'),
            (("call", "nowhere"), 'raw(("call", "nowhere"))'),
            (("arg", "nowhere"), 'raw(("arg", "nowhere"))'),
            (("unquote", ONE), 'raw(("unquote", ("lit", 1)))'),
            (("seq",), 'raw(("seq",))'),
            (("add", ("let", "a", X, ("arg", "a")), X), 'raw(("let", "a", ("arg", "x"), ("arg", "a"))) + x'),
            (("add", ("write", "c", ONE), X), 'raw(("write", "c", ("lit", 1))) + x'),
            (("quote", ("write", "c", ONE)), 'raw(("quote", ("write", "c", ("lit", 1))))'),
            (("quote", ("bogus", 1)), 'raw(("quote", ("bogus", 1)))'),
            (("quote", 5), 'raw(("quote", 5))'),
        ):
            with self.subTest(text=text):
                self.assertEqual(
                    self.rendered({f: Function(("x",), tree), **cell}),
                    f"fn f(x):\n    {text}\n",
                )

    def test_general_apply_has_source_syntax(self) -> None:
        self.assertEqual(
            self.one(
                ("x",),
                ("apply", ("add", X, X), ONE),
            ),
            "fn f(x):\n    apply(x + x, (1,))\n",
        )

    def test_raw_names_its_targets_by_their_current_entity_names(self) -> None:
        f, c = EntityID("f"), EntityID("c")
        state = load(program({
            c: CellDeclaration(IsKind("int"), 7),
            f: Function(("x",), ("add", ("write", "alias", ONE), X)),
            EntityID("f.links"): links(f, alias=c),
        }))
        text = render(state, f)

        self.assertEqual(text, 'fn f(x):\n    raw(("write", "c", ("lit", 1))) + x\n')

        again = parse(text, base=parse("cell c: int = 7\n"))

        self.assertEqual(links_of(again, "f"), {"function": "f", "c": "c"})
        self.assertEqual(run(Runtime(load(again)), f, 2), 3)

    def test_a_literal_that_is_not_data_prints_as_raw_the_parser_rejects(self) -> None:
        text = self.one(("x",), ("lit", EntityID("e")))

        self.assertIn("raw(", text)
        self.assertIn("<", text)

    def test_literals(self) -> None:
        for value, text in (
            (5, "5"),
            (True, "true"),
            (None, "none"),
            ("a\nб", '"a\\nб"'),
            ((1, (2,), ()), "(1, (2,), ())"),
            (("lit", 1), "quote(1)"),
            (("arg", "q"), "quote(q)"),
            (("add", ("lit", 1), ("arg", "q")), "quote(1 + q)"),
            (("x",), '("x",)'),
            (("unquote", ("lit", 1)), '("unquote", ("lit", 1))'),
            (("lit", (1, 2)), '("lit", (1, 2))'),
        ):
            with self.subTest(text=text):
                self.assertEqual(self.one(("x",), ("lit", value)), f"fn f(x):\n    {text}\n")

    def test_quotes_and_function_values(self) -> None:
        g = EntityID("g")
        entities = {
            g: Function(("a",), X),
            EntityID("f"): Function(("x", "y"), (
                "seq",
                ("quote", ("add", ("arg", "q"), ("unquote", ("call", "g", X)))),
                ("quote", ("lit", ("unquote", X))),
                ("function", ("lit", ("q",)), ("quote", ("add", ("arg", "q"), ONE))),
                ("function", ("lit", ("q",)), ("lit", ("add", ("arg", "q"), ONE))),
                ("function", ("tuple", ("lit", "q")), ("quote", ("arg", "q"))),
                ("function", X, ("lit", ("lit", 1))),
                ("activate", "g", ("function", ("lit", ()), ("lit", ("lit", "new")))),
                ("activate", ("g", "lbl"), ("quote", ("call", "g", ("arg", "q")))),
                ("trial", ("call", "g", X), "g", ("function", ("lit", ("q",)), ("quote", ("arg", "q")))),
                ("label", "step", ("add", X, ONE)),
                ("apply", X, Y),
                ("applyv", X, ("tuple", ONE)),
                ("tuple",),
                ("tuple", X),
                ("ref", "g"),
                ("code", "g"),
                ("linksof", "g"),
            )),
            EntityID("f.links"): links(EntityID("f"), g=g),
        }

        self.assertEqual(
            self.rendered(entities),
            "fn f(x, y):\n"
            "    quote(q + unquote(g(x)))\n"
            "    quote(literal(x))\n"
            "    fn(q): q + 1\n"
            "    fn(q): q + 1\n"
            '    function(("q",), quote(q))\n'
            "    function(x, quote(1))\n"
            '    activate(g = fn(): "new")\n'
            "    activate(g.lbl = quote(g(q)))\n"
            "    trial(g(x), g = fn(q): q)\n"
            "    label(step, x + 1)\n"
            "    x(y)\n"
            "    apply(x, (1,))\n"
            "    ()\n"
            "    (x,)\n"
            "    ref(g)\n"
            "    code(g)\n"
            "    linksof(g)\n",
        )

    def test_names_are_backquoted_when_they_are_not_plain(self) -> None:
        odd, reserved, f = EntityID("a.b"), EntityID("len"), EntityID("f")
        text = self.rendered({
            odd: Function(("if",), ("arg", "if")),
            reserved: Function(("x",), X),
            f: Function(("x",), ("add", ("call", "p", X), ("call", "q", X))),
            EntityID("f.links"): links(f, p=odd, q=reserved),
        })

        self.assertEqual(text, "fn f(x):\n    `a.b`(x) + `len`(x)\n")
        self.assertEqual(
            self.rendered({odd: Function(("if",), ("arg", "if"))}, "a.b"),
            "fn `a.b`(`if`):\n    `if`\n",
        )

    def test_names_that_clash_with_a_global_print_as_raw(self) -> None:
        g, f = EntityID("g"), EntityID("f")

        text = self.rendered({
            g: Function(("a",), ("arg", "a")),
            f: Function(("g",), ("arg", "g")),
        }, "f")

        self.assertEqual(text, 'fn f(g):\n    raw(("arg", "g"))\n')

    def test_a_link_name_that_is_not_its_target_prints_the_target(self) -> None:
        g, f = EntityID("target"), EntityID("f")

        self.assertEqual(
            self.rendered({
                g: Function((), ONE),
                f: Function((), ("call", "alias")),
                EntityID("f.links"): links(f, alias=g),
            }),
            "fn f():\n    target()\n",
        )

    def test_render_needs_a_function(self) -> None:
        state = load(program({EntityID("c"): CellDeclaration(IsKind("int"), 0)}))

        for entity in (EntityID("c"), EntityID("missing")):
            with self.subTest(entity=entity):
                with self.assertRaises(ValueError):
                    render(state, entity)

    def test_program_layout(self) -> None:
        state = load(program({
            EntityID("b"): CellDeclaration(IntRange(None, 5), -1),
            EntityID("a"): CellDeclaration(IsKind("tuple"), (1, "x")),
            EntityID("e"): CellDeclaration(IsKind("entity_id"), None),
            EntityID("odd"): CellDeclaration(IsKind("bytes"), None),
            EntityID("z"): Function((), ONE),
            EntityID("m"): Function((), TWO),
        }))

        self.assertEqual(
            render_program(state),
            "cell a: tuple = (1, \"x\")\n"
            "cell b: int in ..5 = -1\n"
            "cell e: entity = none\n"
            "# cell odd: not expressible in the syntax\n"
            "\n"
            "fn m():\n    2\n"
            "\n"
            "fn z():\n    1\n",
        )
        self.assertEqual(render_program(load(program({}))), "")

    def test_text_is_a_fixpoint_and_renders_what_it_parsed(self) -> None:
        source = (
            "cell counter: int in 0..100 = 0\n"
            "cell names: tuple = (\"a\", (1,), ())\n"
            "\n"
            "fn fib(n):\n"
            "    if n < 2:\n"
            "        n\n"
            "    else:\n"
            "        let a = fib(n - 1)\n"
            "        let b = fib(n - 2)\n"
            "        a + b\n"
            "\n"
            "fn install(k):\n"
            "    counter = counter + 1\n"
            "    activate(fib = fn(n): n * literal(k), install.step = quote(unquote(k)))\n"
            "    label(step, trial(fib(1), fib = fn(n): n))\n"
            "    (apply(ref(fib), (1,)), code(fib), linksof(fib), len(names), quote(z(1)))\n"
        )

        self.assertEqual(text_of(source), source)


if __name__ == "__main__":
    unittest.main()
