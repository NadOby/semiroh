"""A compiler written in SEMIROH, and a program that rewrites itself
(docs/self_hosting.md, roadmap task 8).

``compiler_entities()`` is the lowering pass of bytecode.md written in the
language: ``lower(e)`` takes an expression in input form, as ``("code", f)``
returns it, and gives the chunk of that expression with every ``EVAL``,
``GOTO``, ``BRANCH``, ``LETBIND`` and ``CLOSURE`` holding the chunk of its
child instead of a reference to it. It covers every operation but ``quote``,
``unquote``, ``function``, ``activate`` and ``trial``, which lower to a
``RAISE``. ``tests/test_self_hosting.py`` checks it against
``semiroh.bytecode`` on the whole language it covers, and on the compiler
itself.

The examples here run the compiler on a few expressions, and a program that
reads its own function with ``code``, swaps in a version that counts its
calls, and compiles what it installed.
"""

from __future__ import annotations

from typing import Any

from .. import ActivationRejected, CellDeclaration, EntityID, IntRange
from ..lang import Function, LanguageError, links
from . import Example, Raises, Step
from ._support import program

LOWER = EntityID("lower")
UPPER = EntityID("upper")
EVALS = EntityID("evals")
SEQ_CODE = EntityID("seq_code")
SELF_LOWER = EntityID("self_lower")

# The operations the compiler lowers.
LOWERED = frozenset({
    "lit",
    "arg",
    "add",
    "sub",
    "mul",
    "lt",
    "eq",
    "if",
    "seq",
    "call",
    "tuple",
    "len",
    "item",
    "slice",
    "concat",
    "let",
    "ref",
    "apply",
    "read",
    "write",
    "code",
    "label",
    "applyv",
    "linksof",
    "closure",
})


def _lit(value: Any) -> tuple:
    return ("lit", value)


def _arg(name: str) -> tuple:
    return ("arg", name)


def _item(tuple_: tuple, index: int) -> tuple:
    return ("item", tuple_, _lit(index))


def _op(name: str, *operands: tuple) -> tuple:
    """An instruction: its opcode and operands, built from expressions."""

    return ("tuple", _lit(name), *operands)


def _chunk(*instructions: tuple) -> tuple:
    """A finished chunk: the instructions and END."""

    return ("concat", ("tuple", *instructions), _END_CHUNK)


_END_CHUNK = ("tuple", _lit(("END",)))


def _lower(expression: tuple) -> tuple:
    return ("call", "lower", expression)


def _eval(expression: tuple) -> tuple:
    return _op("EVAL", _lower(expression))


def _sub_expr(index: int) -> tuple:
    return _item(_arg("e"), index)


def _child(index: int) -> tuple:
    """The instruction that evaluates operand ``index`` of ``e``."""

    return _eval(_sub_expr(index))


def _is(name: str) -> tuple:
    return ("eq", _arg("op"), _lit(name))


def _length_minus(amount: int) -> tuple:
    return ("sub", ("len", _arg("e")), _lit(amount))


def _lower_body() -> tuple:
    cases = [
        ("lit", _chunk(_op("LIT", _sub_expr(1)))),
        ("arg", _chunk(_op("ARG", _sub_expr(1)))),
        ("eq", _chunk(_child(1), _child(2), _op("EQ"))),
        (
            "if",
            _chunk(
                _child(1),
                _op(
                    "BRANCH",
                    _lower(_sub_expr(2)),
                    _lower(_sub_expr(3)),
                ),
            ),
        ),
        (
            "seq",
            (
                "if",
                ("eq", ("len", _arg("e")), _lit(1)),
                _chunk(
                    _op(
                        "RAISE",
                        _lit("seq needs at least one expression"),
                    )
                ),
                (
                    "concat",
                    (
                        "call",
                        "seq_code",
                        _arg("e"),
                        _lit(1),
                    ),
                    _END_CHUNK,
                ),
            ),
        ),
        (
            "call",
            (
                "concat",
                (
                    "concat",
                    (
                        "call",
                        "evals",
                        _arg("e"),
                        _lit(2),
                        _lit(()),
                    ),
                    (
                        "tuple",
                        _op(
                            "CALL",
                            _sub_expr(1),
                            _length_minus(2),
                        ),
                    ),
                ),
                _END_CHUNK,
            ),
        ),
        (
            "tuple",
            (
                "concat",
                (
                    "concat",
                    (
                        "call",
                        "evals",
                        _arg("e"),
                        _lit(1),
                        _lit(()),
                    ),
                    (
                        "tuple",
                        _op(
                            "MKTUPLE",
                            _length_minus(1),
                        ),
                    ),
                ),
                _END_CHUNK,
            ),
        ),
        (
            "len",
            _chunk(
                _child(1),
                _op("TUPLE", _lit("len")),
                _op("LEN"),
            ),
        ),
        (
            "item",
            _chunk(
                _child(1),
                _op("TUPLE", _lit("item")),
                _child(2),
                _op("INT", _lit("item")),
                _op("ITEM"),
            ),
        ),
        (
            "slice",
            _chunk(
                _child(1),
                _op("TUPLE", _lit("slice")),
                _child(2),
                _op("INT", _lit("slice")),
                _child(3),
                _op("INT", _lit("slice")),
                _op("SLICE"),
            ),
        ),
        (
            "concat",
            _chunk(
                _child(1),
                _op("TUPLE", _lit("concat")),
                _child(2),
                _op("TUPLE", _lit("concat")),
                _op("CONCAT"),
            ),
        ),
        (
            "let",
            _chunk(
                _op(
                    "LETCHECK",
                    _sub_expr(1),
                ),
                _child(2),
                _op(
                    "LETBIND",
                    _sub_expr(1),
                    _lower(_sub_expr(3)),
                ),
            ),
        ),
        (
            "ref",
            _chunk(
                _op(
                    "REF",
                    _sub_expr(1),
                )
            ),
        ),
        (
            "closure",
            _chunk(
                _op(
                    "CLOSURE",
                    _lower(_sub_expr(3)),
                    _sub_expr(1),
                    _sub_expr(2),
                )
            ),
        ),
        (
            "apply",
            (
                "concat",
                (
                    "concat",
                    (
                        "tuple",
                        _child(1),
                        _op("REFCHECK"),
                    ),
                    (
                        "concat",
                        (
                            "call",
                            "evals",
                            _arg("e"),
                            _lit(2),
                            _lit(()),
                        ),
                        (
                            "tuple",
                            _op(
                                "APPLY",
                                _length_minus(2),
                            ),
                        ),
                    ),
                ),
                _END_CHUNK,
            ),
        ),
        (
            "applyv",
            _chunk(
                _child(1),
                _op("REFCHECK"),
                _child(2),
                _op("TUPLE", _lit("applyv")),
                _op("APPLYV"),
            ),
        ),
        (
            "linksof",
            _chunk(
                _op(
                    "LINKS",
                    _sub_expr(1),
                )
            ),
        ),
        (
            "read",
            _chunk(
                _op(
                    "READ",
                    _sub_expr(1),
                )
            ),
        ),
        (
            "write",
            _chunk(
                _child(2),
                _op(
                    "WRITE",
                    _sub_expr(1),
                ),
            ),
        ),
        (
            "code",
            _chunk(
                _op(
                    "CODE",
                    _sub_expr(1),
                )
            ),
        ),
        (
            "label",
            _lower(_sub_expr(2)),
        ),
    ]

    chain: tuple = _chunk(
        _op(
            "RAISE",
            _lit("unknown operation"),
        )
    )

    for name, chunk in reversed(cases):
        chain = (
            "if",
            _is(name),
            chunk,
            chain,
        )

    arithmetic = _chunk(
        _child(1),
        _op(
            "INT",
            _arg("op"),
        ),
        _child(2),
        _op(
            "INT",
            _arg("op"),
        ),
        ("tuple", _arg("up")),
    )

    return (
        "let",
        "op",
        _item(_arg("e"), 0),
        (
            "let",
            "up",
            (
                "call",
                "upper",
                _arg("op"),
            ),
            (
                "if",
                (
                    "eq",
                    _arg("up"),
                    _lit(None),
                ),
                chain,
                arithmetic,
            ),
        ),
    )


def _upper_body() -> tuple:
    body: tuple = _lit(None)

    for name in reversed(
        (
            "add",
            "sub",
            "mul",
            "lt",
        )
    ):
        body = (
            "if",
            (
                "eq",
                _arg("op"),
                _lit(name),
            ),
            _lit(name.upper()),
            body,
        )

    return body


def _evals_body() -> tuple:
    e = _arg("e")
    i = _arg("i")
    acc = _arg("acc")

    return (
        "if",
        (
            "lt",
            i,
            ("len", e),
        ),
        (
            "call",
            "evals",
            e,
            (
                "add",
                i,
                _lit(1),
            ),
            (
                "concat",
                acc,
                (
                    "tuple",
                    _op(
                        "EVAL",
                        _lower(
                            (
                                "item",
                                e,
                                i,
                            )
                        ),
                    ),
                ),
            ),
        ),
        acc,
    )


def _seq_code_body() -> tuple:
    e = _arg("e")
    i = _arg("i")

    return (
        "if",
        (
            "eq",
            i,
            _length_minus(1),
        ),
        (
            "tuple",
            _op(
                "GOTO",
                _lower(
                    (
                        "item",
                        e,
                        i,
                    )
                ),
            ),
        ),
        (
            "concat",
            (
                "tuple",
                _op(
                    "EVAL",
                    _lower(
                        (
                            "item",
                            e,
                            i,
                        )
                    ),
                ),
                _op("POP"),
            ),
            (
                "call",
                "seq_code",
                e,
                (
                    "add",
                    i,
                    _lit(1),
                ),
            ),
        ),
    )


def compiler_entities(
    extra: dict[str, EntityID] | None = None,
) -> dict[EntityID, Any]:
    """The compiler's functions and links, and ``self_lower``, which compiles
    the compiler's own ``lower`` by reading it with ``code``. ``extra`` adds
    link names to every function (the interpreter of ``vm.py``, so that they
    can be swapped for versions that run on it).
    """

    more = extra or {}

    return {
        LOWER: Function(
            ("e",),
            _lower_body(),
        ),
        EntityID("lower.links"): links(
            LOWER,
            lower=LOWER,
            upper=UPPER,
            evals=EVALS,
            seq_code=SEQ_CODE,
            **more,
        ),
        UPPER: Function(
            ("op",),
            _upper_body(),
        ),
        EntityID("upper.links"): links(
            UPPER,
            **more,
        ),
        EVALS: Function(
            ("e", "i", "acc"),
            _evals_body(),
        ),
        EntityID("evals.links"): links(
            EVALS,
            evals=EVALS,
            lower=LOWER,
            **more,
        ),
        SEQ_CODE: Function(
            ("e", "i"),
            _seq_code_body(),
        ),
        EntityID("seq_code.links"): links(
            SEQ_CODE,
            seq_code=SEQ_CODE,
            lower=LOWER,
            **more,
        ),
        SELF_LOWER: Function(
            (),
            (
                "call",
                "lower",
                _item(
                    ("code", "lower"),
                    1,
                ),
            ),
        ),
        EntityID("self_lower.links"): links(
            SELF_LOWER,
            lower=LOWER,
            **more,
        ),
    }


def _compiler() -> Example:
    def step(
        expression: tuple,
        expect: Any,
    ) -> Step:
        return Step(
            LOWER,
            (expression,),
            expect,
        )

    end = ("END",)
    x = (
        ("ARG", "x"),
        end,
    )
    one = (
        ("LIT", 1),
        end,
    )

    return Example(
        name="compiler",
        tags=frozenset({
            "data",
            "recursion",
        }),
        program=program(
            compiler_entities()
        ),
        scenarios=(
            (
                step(
                    ("lit", 7),
                    (
                        ("LIT", 7),
                        end,
                    ),
                ),
                step(
                    ("arg", "x"),
                    x,
                ),
                step(
                    (
                        "add",
                        ("arg", "x"),
                        ("lit", 1),
                    ),
                    (
                        (
                            "EVAL",
                            x,
                        ),
                        (
                            "INT",
                            "add",
                        ),
                        (
                            "EVAL",
                            one,
                        ),
                        (
                            "INT",
                            "add",
                        ),
                        ("ADD",),
                        end,
                    ),
                ),
                step(
                    (
                        "if",
                        (
                            "lt",
                            ("arg", "x"),
                            ("lit", 1),
                        ),
                        ("lit", 1),
                        ("arg", "x"),
                    ),
                    (
                        (
                            "EVAL",
                            (
                                (
                                    "EVAL",
                                    x,
                                ),
                                (
                                    "INT",
                                    "lt",
                                ),
                                (
                                    "EVAL",
                                    one,
                                ),
                                (
                                    "INT",
                                    "lt",
                                ),
                                ("LT",),
                                end,
                            ),
                        ),
                        (
                            "BRANCH",
                            one,
                            x,
                        ),
                        end,
                    ),
                ),
                step(
                    ("seq",),
                    (
                        (
                            "RAISE",
                            "seq needs at least one expression",
                        ),
                        end,
                    ),
                ),
                step(
                    (
                        "seq",
                        ("lit", 1),
                        ("arg", "x"),
                    ),
                    (
                        (
                            "EVAL",
                            one,
                        ),
                        ("POP",),
                        (
                            "GOTO",
                            x,
                        ),
                        end,
                    ),
                ),
                step(
                    (
                        "call",
                        "f",
                        ("lit", 1),
                        ("arg", "x"),
                    ),
                    (
                        (
                            "EVAL",
                            one,
                        ),
                        (
                            "EVAL",
                            x,
                        ),
                        (
                            "CALL",
                            "f",
                            2,
                        ),
                        end,
                    ),
                ),
                step(
                    (
                        "let",
                        "a",
                        ("lit", 1),
                        ("arg", "a"),
                    ),
                    (
                        (
                            "LETCHECK",
                            "a",
                        ),
                        (
                            "EVAL",
                            one,
                        ),
                        (
                            "LETBIND",
                            "a",
                            (
                                (
                                    "ARG",
                                    "a",
                                ),
                                end,
                            ),
                        ),
                        end,
                    ),
                ),
                step(
                    (
                        "label",
                        "k",
                        ("lit", 1),
                    ),
                    one,
                ),
                step(
                    (
                        "closure",
                        ("x",),
                        ("n",),
                        (
                            "add",
                            ("arg", "n"),
                            ("arg", "x"),
                        ),
                    ),
                    (
                        (
                            "CLOSURE",
                            (
                                (
                                    "EVAL",
                                    (
                                        (
                                            "ARG",
                                            "n",
                                        ),
                                        end,
                                    ),
                                ),
                                (
                                    "INT",
                                    "add",
                                ),
                                (
                                    "EVAL",
                                    (
                                        (
                                            "ARG",
                                            "x",
                                        ),
                                        end,
                                    ),
                                ),
                                (
                                    "INT",
                                    "add",
                                ),
                                ("ADD",),
                                end,
                            ),
                            ("x",),
                            ("n",),
                        ),
                        end,
                    ),
                ),
                step(
                    (
                        "quote",
                        ("lit", 1),
                    ),
                    (
                        (
                            "RAISE",
                            "unknown operation",
                        ),
                        end,
                    ),
                ),
            ),
        ),
        description=(
            "lower(e), the lowering pass of bytecode.md written in SEMIROH: "
            "an expression in input form in, its chunk out with children "
            "in place of references (self_hosting.md section 3)."
        ),
    )


def _instrument() -> Example:
    work = EntityID("work")
    hits = EntityID("hits")
    instrument = EntityID("instrument")
    counted = (
        "write",
        "hits",
        (
            "add",
            ("read", "hits"),
            ("lit", 1),
        ),
    )
    entities = {
        hits: CellDeclaration(
            IntRange(0, 100),
            0,
        ),
        work: Function(
            ("x",),
            (
                "add",
                ("arg", "x"),
                ("lit", 1),
            ),
        ),
        EntityID("work.links"): links(
            work,
            hits=hits,
        ),
        instrument: Function(
            (),
            (
                "seq",
                (
                    "activate",
                    "work",
                    (
                        "function",
                        _item(
                            ("code", "work"),
                            0,
                        ),
                        (
                            "quote",
                            (
                                "seq",
                                counted,
                                (
                                    "unquote",
                                    _item(
                                        ("code", "work"),
                                        1,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                (
                    "call",
                    "lower",
                    _item(
                        ("code", "work"),
                        1,
                    ),
                ),
            ),
        ),
        EntityID("instrument.links"): links(
            instrument,
            work=work,
            lower=LOWER,
        ),
        **compiler_entities(),
    }

    end = ("END",)

    add = (
        (
            "EVAL",
            (
                (
                    "ARG",
                    "x",
                ),
                end,
            ),
        ),
        (
            "INT",
            "add",
        ),
        (
            "EVAL",
            (
                (
                    "LIT",
                    1,
                ),
                end,
            ),
        ),
        (
            "INT",
            "add",
        ),
        ("ADD",),
        end,
    )

    count = (
        (
            "EVAL",
            (
                (
                    "READ",
                    "hits",
                ),
                end,
            ),
        ),
        (
            "INT",
            "add",
        ),
        (
            "EVAL",
            (
                (
                    "LIT",
                    1,
                ),
                end,
            ),
        ),
        (
            "INT",
            "add",
        ),
        ("ADD",),
        end,
    )

    installed = (
        (
            "EVAL",
            (
                (
                    (
                        "EVAL",
                        count,
                    ),
                    (
                        "WRITE",
                        "hits",
                    ),
                    end,
                )
            ),
        ),
        ("POP",),
        (
            "GOTO",
            add,
        ),
        end,
    )

    return Example(
        name="instrument",
        tags=frozenset({
            "self-modification",
            "side effects",
        }),
        program=program(entities),
        scenarios=(
            (
                Step(
                    work,
                    (5,),
                    6,
                    cells={
                        hits: 0,
                    },
                ),
                Step(
                    instrument,
                    (),
                    Raises(
                        ActivationRejected
                    ),
                ),
                Step(
                    instrument,
                    (),
                    installed,
                    may_activate=True,
                ),
                Step(
                    work,
                    (5,),
                    6,
                    cells={
                        hits: 1,
                    },
                ),
                Step(
                    work,
                    (7,),
                    8,
                    cells={
                        hits: 2,
                    },
                ),
            ),
        ),
        description=(
            "A program reads its own function with `code`, swaps in a version "
            "that counts its calls, and compiles the installed code with its "
            "own compiler, which sees the new version (self_hosting.md "
            "section 4)."
        ),
    )


EXAMPLES: tuple[Example, ...] = (
    _compiler(),
    _instrument(),
            )
