"""Unit tests for the tiny language in shear.lang (docs/first_program.md).

The acceptance tests in ``test_first_program.py`` pin the language's
observable behaviour end to end. These tests exercise the interpreter and
the ``Function``/``links`` records directly: every operation, every
``LanguageError`` case, a seeded property comparing ``run`` against a
plain reference evaluator, and one comparing ``quote`` without holes with
``lit``. Programs are loaded into graph form (docs/graph_form.md); the
graph form itself (nodes, ``load``, ``define``, ``function_at``) has its own
tests at the end, including a seeded round-trip property.
"""

import random
import unittest

from shear import (
    ActivationRejected,
    CellContentRejected,
    CellDeclaration,
    EntityID,
    IntRange,
    Runtime,
    State,
    Value,
    relation_of,
)
from shear.lang import (
    FUNCTION_ROLE,
    Function,
    LanguageError,
    define,
    function_at,
    function_of,
    links,
    load,
    run,
)
from shear.transforms import transform_with_mapping

F = EntityID("f")
F_LINKS = EntityID("f.links")
G = EntityID("g")
CELL = EntityID("cell")


def make_state(entities: dict) -> State:
    """A program in the input format, loaded into graph form."""

    return load(State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    }))


def unbounded_cell(initial: int = 0) -> CellDeclaration:
    return CellDeclaration(IntRange(), initial)


def function_only(body: tuple, params: tuple[str, ...] = ()) -> State:
    """A state holding a single function F, with no links relation."""

    return make_state({F: Function(params, body)})


class FunctionRecordTests(unittest.TestCase):
    def test_round_trips_through_a_value(self) -> None:
        function = Function(("x", "y"), ("add", ("arg", "x"), ("arg", "y")))

        self.assertEqual(function_of(Value.create(F, function)), function)

    def test_body_with_nested_tuples_round_trips(self) -> None:
        function = Function(
            ("x",),
            ("if", ("lt", ("arg", "x"), ("lit", 0)), ("lit", 0), ("arg", "x")),
        )

        self.assertEqual(function_of(Value.create(F, function)), function)

    def test_non_function_value_holds_no_function(self) -> None:
        self.assertIsNone(function_of(Value.create(F, 1)))
        self.assertIsNone(function_of(Value.create(F, ("add", 1, 2))))

    def test_rejects_duplicate_parameter_names(self) -> None:
        with self.assertRaises(TypeError):
            Function(("x", "x"), ("lit", 1))

    def test_rejects_empty_body(self) -> None:
        with self.assertRaises(TypeError):
            Function((), ())

    def test_bool_and_int_literals_make_distinct_functions(self) -> None:
        self.assertNotEqual(
            Function((), ("lit", 1)),
            Function((), ("lit", True)),
        )


class LinksTests(unittest.TestCase):
    def test_links_relation_carries_the_function_role(self) -> None:
        relation = links(F, double=G)

        self.assertEqual(relation.kind, "links")
        self.assertEqual(relation.roles[FUNCTION_ROLE], F)
        self.assertEqual(relation.roles["double"], G)

    def test_function_is_a_reserved_link_name(self) -> None:
        # "function" is both the reserved role and links()'s own first
        # parameter, so passing it as a link target collides at the call
        # site itself.
        with self.assertRaises(TypeError):
            links(F, function=G)


class OperationTests(unittest.TestCase):
    def test_lit_returns_the_literal(self) -> None:
        self.assertEqual(run(Runtime(function_only(("lit", 42))), F), 42)
        self.assertIs(run(Runtime(function_only(("lit", True))), F), True)

    def test_arg_returns_the_bound_parameter(self) -> None:
        state = function_only(("arg", "x"), params=("x",))

        self.assertEqual(run(Runtime(state), F, 5), 5)

    def test_add(self) -> None:
        state = function_only(("add", ("lit", 2), ("lit", 3)))

        self.assertEqual(run(Runtime(state), F), 5)

    def test_sub(self) -> None:
        state = function_only(("sub", ("lit", 5), ("lit", 3)))

        self.assertEqual(run(Runtime(state), F), 2)

    def test_mul(self) -> None:
        state = function_only(("mul", ("lit", 4), ("lit", 3)))

        self.assertEqual(run(Runtime(state), F), 12)

    def test_lt(self) -> None:
        less = function_only(("lt", ("lit", 2), ("lit", 3)))
        not_less = function_only(("lt", ("lit", 3), ("lit", 2)))

        self.assertIs(run(Runtime(less), F), True)
        self.assertIs(run(Runtime(not_less), F), False)

    def test_eq_distinguishes_bool_from_int(self) -> None:
        same_kind = function_only(("eq", ("lit", 1), ("lit", 1)))
        different_kind = function_only(("eq", ("lit", 1), ("lit", True)))

        self.assertIs(run(Runtime(same_kind), F), True)
        self.assertIs(run(Runtime(different_kind), F), False)

    def test_if_picks_the_matching_branch(self) -> None:
        when_true = function_only(("if", ("lit", True), ("lit", 1), ("lit", 2)))
        when_false = function_only(("if", ("lit", False), ("lit", 1), ("lit", 2)))

        self.assertEqual(run(Runtime(when_true), F), 1)
        self.assertEqual(run(Runtime(when_false), F), 2)

    def test_seq_evaluates_in_order_and_returns_the_last(self) -> None:
        state = make_state({
            F: Function(
                (),
                ("seq", ("write", "c", ("lit", 1)), ("write", "c", ("lit", 2))),
            ),
            F_LINKS: links(F, c=CELL),
            CELL: unbounded_cell(0),
        })
        runtime = Runtime(state)

        self.assertEqual(run(runtime, F), 2)
        self.assertEqual(runtime.read(CELL), 2)

    def test_call_invokes_the_linked_function(self) -> None:
        state = make_state({
            F: Function(("x",), ("call", "g", ("arg", "x"))),
            F_LINKS: links(F, g=G),
            G: Function(("x",), ("mul", ("arg", "x"), ("lit", 2))),
        })

        self.assertEqual(run(Runtime(state), F, 5), 10)

    def test_read_and_write_go_through_the_linked_cell(self) -> None:
        state = make_state({
            F: Function((), ("write", "c", ("lit", 7))),
            F_LINKS: links(F, c=CELL),
            CELL: unbounded_cell(0),
        })
        runtime = Runtime(state)

        self.assertEqual(run(runtime, F), 7)
        self.assertEqual(runtime.read(CELL), 7)
        self.assertEqual(runtime.active.id, state.id)

    def test_arguments_are_canonicalized_before_binding(self) -> None:
        # bool and int must bind distinctly, even as run() arguments.
        state = function_only(
            ("eq", ("arg", "x"), ("lit", True)),
            params=("x",),
        )

        self.assertIs(run(Runtime(state), F, True), True)
        self.assertIs(run(Runtime(state), F, 1), False)


class MetaprogrammingOperationTests(unittest.TestCase):
    def test_quote_without_holes_equals_lit(self) -> None:
        template = (
            "add",
            ("lit", 2),
            ("mul", ("lit", 3), ("lit", 4)),
        )
        state = function_only(("quote", template))

        self.assertEqual(
            run(Runtime(state), F),
            template,
        )

    def test_quote_and_unquote_use_function_scope(self) -> None:
        state = function_only(
            (
                "quote",
                (
                    "add",
                    ("unquote", ("arg", "x")),
                    ("lit", 2),
                ),
            ),
            params=("x",),
        )

        self.assertEqual(
            run(Runtime(state), F, 5),
            ("add", 5, ("lit", 2)),
        )

    def test_quote_rejects_malformed_unquote(self) -> None:
        state = function_only(
            ("quote", ("add", ("unquote",), ("lit", 1)))
        )

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_function_operation_builds_function(self) -> None:
        body = ("add", ("arg", "x"), ("lit", 1))
        state = function_only(
            (
                "function",
                ("lit", ("x",)),
                ("lit", body),
            )
        )

        self.assertEqual(
            run(Runtime(state), F),
            Function(("x",), body),
        )

    def test_function_operation_rejects_bad_parameters(self) -> None:
        state = function_only(
            (
                "function",
                ("lit", (1,)),
                ("lit", ("lit", 1)),
            )
        )

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_function_operation_rejects_duplicate_parameters(self) -> None:
        state = function_only(
            (
                "function",
                ("lit", ("x", "x")),
                ("lit", ("lit", 1)),
            )
        )

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_function_operation_rejects_empty_body(self) -> None:
        state = function_only(
            (
                "function",
                ("lit", ("x",)),
                ("lit", ()),
            )
        )

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_activate_checks_operands_before_capability(self) -> None:
        state = make_state({
            F: Function((), ("activate", "missing", ("lit", 1))),
            F_LINKS: links(F),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_activate_requires_capability_after_operand_checks(self) -> None:
        target = EntityID("target")
        target_links = EntityID("target.links")
        replacement = Function((), ("lit", 2))

        state = make_state({
            F: Function(
                (),
                ("activate", "target", ("lit", replacement)),
            ),
            F_LINKS: links(F, target=target),
            target: Function((), ("lit", 1)),
            target_links: links(target),
        })

        with self.assertRaises(ActivationRejected):
            run(Runtime(state), F)

    def test_activate_rejects_non_function_value(self) -> None:
        target = EntityID("target")

        state = make_state({
            F: Function(
                (),
                ("activate", "target", ("lit", 1)),
            ),
            F_LINKS: links(F, target=target),
            target: Function((), ("lit", 1)),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F, may_activate=True)

    def test_activate_rejects_duplicate_targets(self) -> None:
        target = EntityID("target")

        state = make_state({
            F: Function(
                (),
                (
                    "activate",
                    "target",
                    ("lit", Function((), ("lit", 2))),
                    "target",
                    ("lit", Function((), ("lit", 3))),
                ),
            ),
            F_LINKS: links(F, target=target),
            target: Function((), ("lit", 1)),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F, may_activate=True)

    def test_activate_changes_code_atomically(self) -> None:
        target = EntityID("target")
        target_links = EntityID("target.links")
        first = EntityID("first")
        first_links = EntityID("first.links")

        state = make_state({
            F: Function(
                (),
                (
                    "activate",
                    "target",
                    ("lit", Function((), ("lit", 2))),
                ),
            ),
            F_LINKS: links(F, target=target),
            target: Function((), ("lit", 1)),
            target_links: links(target),
            first: Function((), ("lit", 1)),
            first_links: links(first),
        })
        runtime = Runtime(state)

        self.assertIsNone(run(runtime, F, may_activate=True))
        self.assertEqual(
            function_at(runtime.active.state, target),
            Function((), ("lit", 2)),
        )
        self.assertEqual(
            function_at(runtime.active.state, first),
            Function((), ("lit", 1)),
        )

    def test_canonical_function_argument_can_activate(self) -> None:
        target = EntityID("target")

        state = make_state({
            F: Function(
                ("replacement",),
                ("activate", "target", ("arg", "replacement")),
            ),
            F_LINKS: links(F, target=target),
            target: Function((), ("lit", 1)),
        })
        runtime = Runtime(state)
        replacement = Function((), ("lit", 2))

        self.assertIsNone(
            run(runtime, F, replacement, may_activate=True)
        )
        self.assertEqual(
            function_at(runtime.active.state, target),
            replacement,
        )

    def test_activate_preserves_runtime_cell_content(self) -> None:
        target = EntityID("target")

        state = make_state({
            F: Function(
                (),
                ("activate", "target", ("lit", Function((), ("lit", 2)))),
            ),
            F_LINKS: links(F, target=target),
            target: Function((), ("lit", 1)),
            CELL: unbounded_cell(0),
        })
        runtime = Runtime(state)

        runtime.write(CELL, 17)
        run(runtime, F, may_activate=True)

        self.assertEqual(runtime.read(CELL), 17)

    def test_quote_preserves_nested_non_tuple_data(self) -> None:
        literal = (
            "outer",
            [1, 2, {"x": 3}],
            ("inner", ("lit", 4)),
        )
        state = function_only(("quote", literal))

        self.assertEqual(run(Runtime(state), F), literal)


class LanguageErrorTests(unittest.TestCase):
    def test_unknown_operation(self) -> None:
        with self.assertRaises(LanguageError):
            run(Runtime(function_only(("frobnicate",))), F)

    def test_unknown_link_name(self) -> None:
        state = make_state({
            F: Function((), ("call", "missing")),
            F_LINKS: links(F, g=G),
            G: Function((), ("lit", 1)),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_unknown_link_name_with_no_links_relation_at_all(self) -> None:
        with self.assertRaises(LanguageError):
            run(Runtime(function_only(("read", "missing"))), F)

    def test_function_role_is_not_an_ordinary_link(self) -> None:
        state = make_state({
            F: Function((), ("call", "function")),
            F_LINKS: links(F),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_wrong_number_of_call_arguments(self) -> None:
        state = make_state({
            F: Function((), ("call", "g")),
            F_LINKS: links(F, g=G),
            G: Function(("x",), ("arg", "x")),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_wrong_number_of_entry_arguments(self) -> None:
        state = function_only(("arg", "x"), params=("x",))

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)  # SQUARE-style: missing the argument

    def test_calling_something_that_is_not_a_function(self) -> None:
        state = make_state({
            F: Function((), ("call", "c")),
            F_LINKS: links(F, c=CELL),
            CELL: unbounded_cell(0),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_reading_something_that_is_not_a_cell(self) -> None:
        state = make_state({
            F: Function((), ("read", "g")),
            F_LINKS: links(F, g=G),
            G: Function((), ("lit", 1)),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_writing_something_that_is_not_a_cell(self) -> None:
        state = make_state({
            F: Function((), ("write", "g", ("lit", 1))),
            F_LINKS: links(F, g=G),
            G: Function((), ("lit", 1)),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_add_rejects_bool_operands(self) -> None:
        state = function_only(("add", ("lit", True), ("lit", 1)))

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_lt_rejects_bool_operands(self) -> None:
        state = function_only(("lt", ("lit", True), ("lit", 1)))

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_if_condition_must_be_bool(self) -> None:
        state = function_only(("if", ("lit", 1), ("lit", 1), ("lit", 2)))

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_cell_content_rejection_propagates_unchanged(self) -> None:
        state = make_state({
            F: Function((), ("write", "c", ("lit", 5))),
            F_LINKS: links(F, c=CELL),
            CELL: CellDeclaration(IntRange(0, 1), 0),
        })

        with self.assertRaises(CellContentRejected):
            run(Runtime(state), F)


class FrameCleanupTests(unittest.TestCase):
    def test_a_failed_call_still_releases_its_frame(self) -> None:
        state = make_state({
            F: Function((), ("call", "g")),
            F_LINKS: links(F, g=G),
            G: Function(("x",), ("arg", "x")),
        })
        runtime = Runtime(state)

        with self.assertRaises(LanguageError):
            run(runtime, F)

        self.assertEqual(runtime.active.holds, frozenset())


def _int_expr(rng: random.Random, depth: int) -> tuple:
    """A random expression that evaluates to an int (never bool)."""

    if depth <= 0 or rng.random() < 0.35:
        return ("lit", rng.randint(-25, 25))

    op = rng.choice(("add", "sub", "mul", "if"))

    if op == "if":
        return (
            "if",
            _bool_expr(rng, depth - 1),
            _int_expr(rng, depth - 1),
            _int_expr(rng, depth - 1),
        )

    return (
        op,
        _int_expr(rng, depth - 1),
        _int_expr(rng, depth - 1),
    )


def _bool_expr(rng: random.Random, depth: int) -> tuple:
    """A random expression that evaluates to a bool, from int operands."""

    op = rng.choice(("lt", "eq"))

    return (
        op,
        _int_expr(rng, depth),
        _int_expr(rng, depth),
    )


def _reference_eval(node: tuple) -> object:
    """Plain-Python evaluator mirroring the language semantics."""

    op, *rest = node

    if op == "lit":
        return rest[0]

    if op == "add":
        return _reference_eval(rest[0]) + _reference_eval(rest[1])

    if op == "sub":
        return _reference_eval(rest[0]) - _reference_eval(rest[1])

    if op == "mul":
        return _reference_eval(rest[0]) * _reference_eval(rest[1])

    if op == "lt":
        return _reference_eval(rest[0]) < _reference_eval(rest[1])

    if op == "eq":
        return _reference_eval(rest[0]) == _reference_eval(rest[1])

    if op == "if":
        condition, then, otherwise = rest

        return (
            _reference_eval(then)
            if _reference_eval(condition)
            else _reference_eval(otherwise)
        )

    raise AssertionError(
        f"unhandled op in reference evaluator: {op}"
    )


class ExpressionEvaluationProperties(unittest.TestCase):
    def test_run_matches_a_reference_evaluator(self) -> None:
        for seed in range(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                body = _int_expr(rng, depth=4)
                state = function_only(body)

                self.assertEqual(
                    run(Runtime(state), F),
                    _reference_eval(body),
                )


class MetaprogrammingProperties(unittest.TestCase):
    def test_quote_without_holes_matches_literal_for_nested_templates(self) -> None:
        for seed in range(50):
            with self.subTest(seed=seed):
                rng = random.Random(seed)

                def template(depth: int) -> tuple:
                    if depth <= 0 or rng.random() < 0.35:
                        return (
                            "lit",
                            rng.randint(-10, 10),
                        )

                    return (
                        rng.choice(("add", "sub", "mul")),
                        template(depth - 1),
                        template(depth - 1),
                    )

                value = template(4)
                quoted = function_only(("quote", value))
                literal = function_only(("lit", value))

                self.assertEqual(
                    run(Runtime(quoted), F),
                    run(Runtime(literal), F),
                )
                self.assertEqual(run(Runtime(quoted), F), value)


PREP = EntityID("prep")
PREP_LINKS = EntityID("prep.links")
POWER = EntityID("power")
MARKER = EntityID("marker")


class TrialOperationTests(unittest.TestCase):
    """Unit tests for ``trial`` (docs/language_trials.md)."""

    def test_trial_without_changes_runs_the_call_in_isolation(self) -> None:
        state = make_state({
            F: Function((), ("trial", ("call", "g"))),
            F_LINKS: links(F, g=G),
            G: Function((), ("write", "c", ("lit", 9))),
            EntityID("g.links"): links(G, c=CELL),
            CELL: unbounded_cell(0),
        })
        runtime = Runtime(state)

        self.assertEqual(run(runtime, F, may_activate=True), 9)
        self.assertEqual(runtime.read(CELL), 0)
        self.assertEqual(runtime.versions, (runtime.active,))
        self.assertEqual(runtime.active.holds, frozenset())

    def test_trial_runs_the_replaced_function_without_installing_it(self) -> None:
        state = make_state({
            F: Function(
                (),
                (
                    "trial",
                    ("call", "g"),
                    "g",
                    ("lit", Function((), ("lit", 42))),
                ),
            ),
            F_LINKS: links(F, g=G),
            G: Function((), ("lit", 1)),
        })
        runtime = Runtime(state)

        self.assertEqual(run(runtime, F, may_activate=True), 42)
        self.assertEqual(run(runtime, G), 1)

    def test_trial_first_operand_must_be_a_call_form(self) -> None:
        for body in (
            ("trial",),
            ("trial", ("lit", 1)),
            ("trial", ("call",)),
        ):
            with self.subTest(body=body):
                state = function_only(body)

                with self.assertRaises(LanguageError):
                    run(Runtime(state), F, may_activate=True)

    def test_trial_rejects_an_unknown_call_link(self) -> None:
        state = make_state({
            F: Function((), ("trial", ("call", "missing"))),
            F_LINKS: links(F),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F, may_activate=True)

    def test_trial_pair_errors(self) -> None:
        base = {
            F_LINKS: links(F, g=G, c=CELL),
            G: Function((), ("lit", 1)),
            CELL: unbounded_cell(0),
        }

        cases = {
            "odd pairs": ("trial", ("call", "g"), "g"),
            "duplicate target": (
                "trial",
                ("call", "g"),
                "g",
                ("lit", Function((), ("lit", 2))),
                "g",
                ("lit", Function((), ("lit", 3))),
            ),
            "target is not a function": (
                "trial",
                ("call", "g"),
                "c",
                ("lit", Function((), ("lit", 2))),
            ),
            "value is not a function": (
                "trial",
                ("call", "g"),
                "g",
                ("lit", 5),
            ),
        }

        for name, body in cases.items():
            with self.subTest(case=name):
                state = make_state({F: Function((), body), **base})

                with self.assertRaises(LanguageError):
                    run(Runtime(state), F, may_activate=True)

    def test_trial_checks_operands_before_the_capability(self) -> None:
        state = make_state({
            F: Function((), ("trial", ("call", "missing"))),
            F_LINKS: links(F),
        })

        # No may_activate at all: a LanguageError from the operand checks
        # must still win over ActivationRejected from the missing capability.
        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_trial_requires_the_capability_after_operand_checks(self) -> None:
        state = make_state({
            F: Function((), ("trial", ("call", "g"))),
            F_LINKS: links(F, g=G),
            G: Function((), ("lit", 1)),
        })

        with self.assertRaises(ActivationRejected):
            run(Runtime(state), F)

    def test_trial_builds_from_the_active_state_after_its_operands_activate(
        self,
    ) -> None:
        # prep() activates marker as a side effect of evaluating trial's own
        # pair value (its replacement for "power"). The transformation trial
        # builds must start from the state that leaves, not the one active
        # when trial began, or Runtime.trial rejects it as not starting from
        # the active state.
        state = make_state({
            F: Function(
                (),
                (
                    "trial",
                    ("call", "power", ("lit", 7)),
                    "power",
                    ("call", "prep"),
                ),
            ),
            F_LINKS: links(F, prep=PREP, power=POWER),
            PREP: Function(
                (),
                (
                    "seq",
                    (
                        "activate",
                        "marker",
                        ("lit", Function((), ("lit", 2))),
                    ),
                    ("lit", Function(("x",), ("lit", 99))),
                ),
            ),
            PREP_LINKS: links(PREP, marker=MARKER),
            POWER: Function(("x",), ("lit", 1)),
            MARKER: Function((), ("lit", 1)),
        })
        runtime = Runtime(state)

        self.assertEqual(run(runtime, F, may_activate=True), 99)
        self.assertEqual(run(runtime, MARKER), 2)
        self.assertEqual(run(runtime, POWER, 3), 1)
        self.assertEqual(runtime.versions, (runtime.active,))
        self.assertEqual(runtime.active.holds, frozenset())


def input_state(entities: dict) -> State:
    """A program in the input format, not loaded."""

    return State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    })


def nodes_of(state: State, function: EntityID) -> dict:
    return {
        node: relation_of(state.values[node])
        for node in state.owned_subtree(function)
    }


class GraphFormTests(unittest.TestCase):
    """The graph form itself (docs/graph_form.md)."""

    def test_leaves_are_relations_with_no_roles(self) -> None:
        state = function_only(("add", ("lit", 1), ("arg", "x")), params=("x",))
        nodes = nodes_of(state, F)
        by_kind = {relation.kind: node for node, relation in nodes.items()}

        self.assertEqual(set(by_kind), {"add", "lit", "arg"})
        self.assertEqual(dict(nodes[by_kind["lit"]].roles), {})
        self.assertEqual(dict(nodes[by_kind["arg"]].roles), {})
        self.assertEqual(
            dict(nodes[by_kind["add"]].roles),
            {"left": by_kind["lit"], "right": by_kind["arg"]},
        )

    def test_calls_reads_and_writes_name_their_targets_by_role(self) -> None:
        state = make_state({
            F: Function((), ("write", "c", ("call", "g"))),
            F_LINKS: links(F, c=CELL, g=G),
            G: Function((), ("read", "c")),
            EntityID("g.links"): links(G, c=CELL),
            CELL: unbounded_cell(0),
        })
        roles = {
            relation.kind: relation.roles
            for function in (F, G)
            for relation in nodes_of(state, function).values()
        }

        self.assertEqual(roles["write"]["cell"], CELL)
        self.assertEqual(roles["call"]["target"], G)
        self.assertEqual(roles["read"]["cell"], CELL)

    def test_load_leaves_graph_form_unchanged(self) -> None:
        state = make_state({
            F: Function((), ("call", "g")),
            F_LINKS: links(F, g=G),
            G: Function((), ("lit", 1)),
        })

        self.assertEqual(load(state).id, state.id)

    def test_load_rejects_a_function_with_two_links_relations(self) -> None:
        program = input_state({
            F: Function((), ("call", "g")),
            F_LINKS: links(F, g=G),
            EntityID("f.more"): links(F, g=G),
            G: Function((), ("lit", 1)),
        })

        with self.assertRaises(LanguageError):
            load(program)

    def test_running_an_unloaded_program_says_so(self) -> None:
        program = input_state({F: Function((), ("lit", 1))})

        with self.assertRaisesRegex(LanguageError, "load"):
            run(Runtime(program), F)

    def test_define_rejects_what_is_not_a_function_and_creates_an_absent_one(
        self,
    ) -> None:
        # define may create a function (continuity_inference.md §4), so an
        # absent entity is rejected only where there is nothing to create.
        absent = EntityID("absent")
        state = make_state({F: Function((), ("lit", 1)), CELL: unbounded_cell()})

        for edits in (
            {CELL: Function((), ("lit", 2))},
            {absent: None},
            {(absent, "step"): ("lit", 2)},
        ):
            with self.subTest(edits=edits):
                with self.assertRaises(LanguageError):
                    define(state, edits)

        created = define(state, {absent: Function((), ("lit", 2))}).destination

        self.assertEqual(function_at(created, absent), Function((), ("lit", 2)))
        self.assertEqual(run(Runtime(created), absent), 2)

    def test_repeated_defines_never_create_a_node_under_a_used_name(self) -> None:
        # Inference keeps unchanged nodes (continuity_inference.md §2), but a
        # created node never takes the name of an entity that exists or of a
        # node that disappeared. An unrelated entity already has the name
        # the next body would use.
        state = make_state({
            F: Function((), ("lit", 0)),
            EntityID("f/1.0"): 7,
        })
        seen = set(state.values)
        created_any = False

        for step in range(1, 5):
            body = ("add", ("lit", step), ("lit", 1))
            result = define(state, {F: Function((), body)})
            created = set(result.destination.values) - set(state.values)
            state = result.destination

            self.assertTrue(created.isdisjoint(seen))
            self.assertLessEqual(created, set(nodes_of(state, F)))
            self.assertEqual(run(Runtime(state), F), step + 1)
            created_any = created_any or bool(created)
            seen |= set(state.values)

        self.assertTrue(created_any)

    def test_define_depends_only_on_its_arguments(self) -> None:
        state = function_only(("lit", 1))
        replacement = Function(("x",), ("mul", ("arg", "x"), ("lit", 2)))

        self.assertEqual(
            define(state, {F: replacement}).destination.id,
            define(state, {F: replacement}).destination.id,
        )

    def test_new_bodies_resolve_links_through_their_own_function(self) -> None:
        helper = EntityID("helper")
        state = make_state({
            F: Function(
                (),
                (
                    "activate",
                    "g",
                    ("lit", Function((), ("call", "helper"))),
                ),
            ),
            F_LINKS: links(F, g=G),
            # G never calls helper itself, but its link table names it.
            G: Function((), ("lit", 1)),
            EntityID("g.links"): links(G, helper=helper),
            helper: Function((), ("lit", 42)),
        })
        runtime = Runtime(state)

        run(runtime, F, may_activate=True)

        self.assertEqual(run(runtime, G), 42)

    def test_activated_code_is_checked_when_it_runs(self) -> None:
        state = make_state({
            F: Function(
                (),
                ("activate", "g", ("lit", Function((), ("frobnicate",)))),
            ),
            F_LINKS: links(F, g=G),
            G: Function((), ("lit", 1)),
        })
        runtime = Runtime(state)

        self.assertIsNone(run(runtime, F, may_activate=True))
        self.assertEqual(
            function_at(runtime.active.state, G),
            Function((), ("frobnicate",)),
        )

        with self.assertRaises(LanguageError):
            run(runtime, G)

    def test_activate_evaluates_its_values_before_checking_links(self) -> None:
        replacement = Function((), ("lit", 2))
        state = make_state({
            F: Function(
                (),
                (
                    "activate",
                    "missing",
                    ("seq", ("write", "c", ("lit", 5)), ("lit", replacement)),
                ),
            ),
            F_LINKS: links(F, c=CELL),
            CELL: unbounded_cell(0),
        })
        runtime = Runtime(state)

        with self.assertRaises(LanguageError):
            run(runtime, F, may_activate=True)

        self.assertEqual(runtime.read(CELL), 5)


def _random_body(rng: random.Random, depth: int) -> tuple:
    """A random body in the input format, often malformed on purpose."""

    def expr(depth: int) -> object:
        if depth <= 0 or rng.random() < 0.3:
            return rng.choice([
                ("lit", rng.choice([1, True, "s", (1, ("lit", 2)), [3]])),
                ("arg", rng.choice(["x", 5])),
                ("read", rng.choice(["c", "missing"])),
                ("frobnicate",),
                ("lit",),
                7,
            ])

        op = rng.choice([
            "add", "if", "seq", "call", "write", "quote", "function",
            "activate", "trial",
        ])

        if op == "add":
            return ("add", expr(depth - 1), expr(depth - 1))

        if op == "if":
            return ("if", expr(depth - 1), expr(depth - 1), expr(depth - 1))

        if op == "seq":
            return ("seq", *(expr(depth - 1) for _ in range(rng.randrange(3))))

        if op == "call":
            link = rng.choice(["g", "c", "missing", "function"])
            args = (expr(depth - 1) for _ in range(rng.randrange(3)))
            return ("call", link, *args)

        if op == "write":
            return ("write", rng.choice(["c", "g"]), expr(depth - 1))

        if op == "quote":
            return ("quote", template(depth - 1))

        if op == "function":
            return ("function", expr(depth - 1), expr(depth - 1))

        pairs: list = []

        for _ in range(rng.randrange(3)):
            pairs += [rng.choice(["g", "missing"]), expr(depth - 1)]

        if rng.random() < 0.3:
            pairs.append("g")

        if op == "activate":
            return ("activate", *pairs)

        call = rng.choice([
            ("call", "g", expr(depth - 1)),
            ("call", "missing"),
            ("lit", 1),
        ])
        return ("trial", call, *pairs)

    def template(depth: int) -> object:
        if depth <= 0 or rng.random() < 0.3:
            return rng.choice([1, "x", [("unquote", 1)], {"k": ("unquote", 2)}])

        if rng.random() < 0.3:
            return rng.choice([
                ("unquote", expr(depth - 1)),
                ("unquote",),
                ("unquote", 1, 2),
            ])

        return tuple(template(depth - 1) for _ in range(rng.randrange(1, 4)))

    body = expr(depth)
    return body if isinstance(body, tuple) and body else ("seq", body)


class GraphFormProperties(unittest.TestCase):
    def test_load_and_define_round_trip_any_body_keeping_only_what_matches(
        self,
    ) -> None:
        # A node survives define only by continuity_inference.md §2: with
        # equal content (rule 1) or as the body root keeping its kind
        # (rule 2); every other old node is a recorded disappearance.
        for seed in range(300):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                source = Function(("x",), _random_body(rng, 4))
                replacement = Function((), _random_body(rng, 4))
                state = load(input_state({
                    F: source,
                    F_LINKS: links(F, g=G, c=CELL),
                    G: Function(("x",), ("arg", "x")),
                    CELL: unbounded_cell(0),
                }))

                self.assertEqual(function_at(state, F), source)

                result = define(state, {F: replacement})
                defined = result.destination
                root = relation_of(defined.values[F]).roles["body"]

                self.assertEqual(function_at(defined, F), replacement)

                for node in nodes_of(state, F):
                    if node not in defined.values:
                        self.assertEqual(
                            result.mapping_for(node).destination_entities, ()
                        )
                    elif defined.values[node] != state.values[node]:
                        self.assertEqual(node, root)
                        self.assertEqual(
                            relation_of(defined.values[node]).kind,
                            relation_of(state.values[node]).kind,
                        )


if __name__ == "__main__":
    unittest.main()
