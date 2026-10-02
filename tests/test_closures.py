"""Acceptance tests for lexical closures (docs/closures.md, roadmap task 17)."""

import unittest
from unittest import mock

from semiroh import (
    AnyOf,
    CellDeclaration,
    EntityID,
    IntRange,
    IsKind,
    Runtime,
)
from semiroh import bytecode
from semiroh.examples import EXAMPLES, MISSING
from semiroh.examples._support import program
from semiroh.lang import (
    Function,
    LanguageError,
    define,
    function_at,
    links,
    load,
    run,
)
from semiroh.relations import relation_of


MAKE = EntityID("make")
APPLY = EntityID("apply")
APPLYV = EntityID("applyv")
PASS = EntityID("pass")
CALLER = EntityID("caller")
COMPOSE = EntityID("compose")
DOUBLE = EntityID("double")
STORE = EntityID("store")
CELL = EntityID("cell")
F = EntityID("f")
LOOP = EntityID("loop")


def loaded(entities: dict):
    return load(program(entities))


def make_adder_body() -> tuple:
    return (
        "closure",
        ("x",),
        ("n",),
        ("add", ("arg", "n"), ("arg", "x")),
    )


def helpers() -> dict:
    return {
        MAKE: Function(("n",), make_adder_body()),
        APPLY: Function(
            ("f", "x"),
            ("apply", ("arg", "f"), ("arg", "x")),
        ),
        APPLYV: Function(
            ("f", "args"),
            ("applyv", ("arg", "f"), ("arg", "args")),
        ),
    }


class BasicClosureTests(unittest.TestCase):
    def test_make_adder_returns_a_callable_closure(self) -> None:
        runtime = Runtime(loaded(helpers()))

        add4 = run(runtime, MAKE, 4)

        self.assertEqual(run(runtime, APPLY, add4, 3), 7)

    def test_returned_closure_survives_its_creating_frame(self) -> None:
        runtime = Runtime(loaded(helpers()))

        add7 = run(runtime, MAKE, 7)

        # MAKE's frame is gone before this separate run starts.
        self.assertEqual(run(runtime, APPLY, add7, 5), 12)

    def test_closure_rejects_owner_that_is_no_longer_a_function(self) -> None:
        state = loaded(helpers())
        closure = run(Runtime(state), MAKE, 4)

        changed = state.with_changes({
            MAKE: 0,
        })

        with self.assertRaises(LanguageError):
            run(
                Runtime(changed),
                APPLY,
                closure,
                3,
            )

    def test_closures_can_be_passed_and_returned_as_values(self) -> None:
        entities = {
            **helpers(),
            PASS: Function(("value",), ("arg", "value")),
        }
        runtime = Runtime(loaded(entities))
        original = run(runtime, MAKE, 9)

        returned = run(runtime, PASS, original)

        self.assertEqual(run(runtime, APPLY, returned, 1), 10)

    def test_applyv_accepts_a_closure(self) -> None:
        runtime = Runtime(loaded(helpers()))
        add4 = run(runtime, MAKE, 4)

        self.assertEqual(run(runtime, APPLYV, add4, (6,)), 10)

    def test_closure_call_checks_arity(self) -> None:
        runtime = Runtime(loaded(helpers()))
        add4 = run(runtime, MAKE, 4)

        with self.assertRaises(LanguageError):
            run(runtime, APPLYV, add4, ())

        with self.assertRaises(LanguageError):
            run(runtime, APPLYV, add4, (1, 2))

    def test_creating_and_calling_a_closure_needs_no_activation_grant(
        self,
    ) -> None:
        runtime = Runtime(loaded(helpers()))

        # may_activate is deliberately left at its default False.
        add4 = run(runtime, MAKE, 4)

        self.assertEqual(run(runtime, APPLY, add4, 2), 6)

    def test_closure_can_be_stored_and_read_as_an_ordinary_value(self) -> None:
        state = loaded({
            CELL: CellDeclaration(
                AnyOf(IsKind("none"), IsKind("closure")),
                None,
            ),
            STORE: Function(
                ("n",),
                ("write", "cell", make_adder_body()),
            ),
            EntityID("store.links"): links(STORE, cell=CELL),
            CALLER: Function(
                ("x",),
                ("apply", ("read", "cell"), ("arg", "x")),
            ),
            EntityID("caller.links"): links(CALLER, cell=CELL),
        })
        runtime = Runtime(state)

        run(runtime, STORE, 4)

        self.assertEqual(run(runtime, CALLER, 3), 7)


class CaptureTests(unittest.TestCase):
    def test_capture_is_by_value(self) -> None:
        entities = {
            CELL: CellDeclaration(IntRange(-1000, 1000), 4),
            MAKE: Function(
                (),
                (
                    "let",
                    "n",
                    ("read", "cell"),
                    make_adder_body(),
                ),
            ),
            EntityID("make.links"): links(MAKE, cell=CELL),
            STORE: Function((), ("write", "cell", ("lit", 100))),
            EntityID("store.links"): links(STORE, cell=CELL),
            APPLY: Function(
                ("f", "x"),
                ("apply", ("arg", "f"), ("arg", "x")),
            ),
        }
        runtime = Runtime(loaded(entities))

        add_old_value = run(runtime, MAKE)
        run(runtime, STORE)

        self.assertEqual(runtime.read(CELL), 100)
        self.assertEqual(run(runtime, APPLY, add_old_value, 1), 5)

    def test_caller_scope_does_not_replace_a_capture(self) -> None:
        entities = {
            MAKE: Function(("n",), make_adder_body()),
            CALLER: Function(
                ("f", "n"),
                ("apply", ("arg", "f"), ("lit", 1)),
            ),
        }
        runtime = Runtime(loaded(entities))
        add4 = run(runtime, MAKE, 4)

        self.assertEqual(run(runtime, CALLER, add4, 100), 5)

    def test_compose_can_capture_another_closure(self) -> None:
        entities = {
            **helpers(),
            DOUBLE: Function(
                ("x",),
                ("add", ("arg", "x"), ("arg", "x")),
            ),
            COMPOSE: Function(
                ("f", "g"),
                (
                    "closure",
                    ("x",),
                    ("f", "g"),
                    (
                        "apply",
                        ("arg", "f"),
                        ("apply", ("arg", "g"), ("arg", "x")),
                    ),
                ),
            ),
        }
        runtime = Runtime(loaded(entities))

        add2 = run(runtime, MAKE, 2)
        composed = run(runtime, COMPOSE, add2, DOUBLE)

        self.assertEqual(run(runtime, APPLY, composed, 3), 8)

    def test_missing_declared_capture_is_an_error(self) -> None:
        state = loaded({
            F: Function(
                (),
                (
                    "closure",
                    (),
                    ("missing",),
                    ("lit", 1),
                ),
            ),
        })

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_undeclared_free_name_does_not_use_dynamic_scope(self) -> None:
        entities = {
            MAKE: Function(
                (),
                (
                    "closure",
                    (),
                    (),
                    ("arg", "outside"),
                ),
            ),
            CALLER: Function(
                ("f", "outside"),
                ("apply", ("arg", "f")),
            ),
        }
        runtime = Runtime(loaded(entities))
        closure = run(runtime, MAKE)

        with self.assertRaises(LanguageError):
            run(runtime, CALLER, closure, 99)

    def test_existing_closure_uses_the_continued_body_in_the_active_version(
        self,
    ) -> None:
        body = (
            "closure",
            ("x",),
            ("n",),
            (
                "label",
                "calc",
                ("add", ("arg", "n"), ("arg", "x")),
            ),
        )
        state = loaded({
            MAKE: Function(("n",), body),
            APPLY: Function(
                ("f", "x"),
                ("apply", ("arg", "f"), ("arg", "x")),
            ),
        })
        runtime = Runtime(state)
        add4 = run(runtime, MAKE, 4)

        runtime.activate(define(
            runtime.active.state,
            {
                (MAKE, "calc"): (
                    "add",
                    ("arg", "n"),
                    ("mul", ("arg", "x"), ("lit", 2)),
                ),
            },
        ))

        self.assertEqual(run(runtime, APPLY, add4, 3), 10)


class ValidationTests(unittest.TestCase):
    def test_parameter_and_capture_names_are_validated(self) -> None:
        bad = (
            ("closure", ("x", "x"), (), ("lit", 1)),
            ("closure", ("",), (), ("lit", 1)),
            ("closure", (1,), (), ("lit", 1)),
            ("closure", (), ("n", "n"), ("lit", 1)),
            ("closure", (), ("",), ("lit", 1)),
            ("closure", (), (1,), ("lit", 1)),
            ("closure", ("x",), ("x",), ("lit", 1)),
        )

        for body in bad:
            with self.subTest(body=body):
                with self.assertRaises(LanguageError):
                    run(Runtime(loaded({F: Function((), body)})), F)

    def test_parameter_and_capture_containers_must_be_tuples(self) -> None:
        bad = (
            ("closure", 1, (), ("lit", 1)),
            ("closure", ["x"], (), ("lit", 1)),
            ("closure", (), 1, ("lit", 1)),
            ("closure", (), ["n"], ("lit", 1)),
        )

        for body in bad:
            with self.subTest(body=body):
                with self.assertRaises(LanguageError):
                    run(Runtime(loaded({F: Function((), body)})), F)

    def test_function_code_value_is_still_not_callable(self) -> None:
        body = (
            "apply",
            (
                "function",
                ("lit", ("x",)),
                ("lit", ("arg", "x")),
            ),
            ("lit", 4),
        )

        with self.assertRaises(LanguageError):
            run(Runtime(loaded({F: Function((), body)})), F)

    def test_non_callable_is_rejected_before_later_arguments_run(self) -> None:
        body = (
            "apply",
            (
                "function",
                ("lit", ("x",)),
                ("lit", ("arg", "x")),
            ),
            (
                "seq",
                ("write", "cell", ("lit", 7)),
                ("lit", 4),
            ),
        )
        state = loaded({
            CELL: CellDeclaration(IntRange(0, 10), 0),
            F: Function((), body),
            EntityID("f.links"): links(F, cell=CELL),
        })
        runtime = Runtime(state)

        with self.assertRaises(LanguageError):
            run(runtime, F)

        self.assertEqual(runtime.read(CELL), 0)


class TailCallTests(unittest.TestCase):
    def test_tail_closure_applications_do_not_grow_the_call_stack(self) -> None:
        n = ("arg", "n")
        body = (
            "if",
            ("eq", n, ("lit", 0)),
            ("lit", "done"),
            (
                "let",
                "again",
                ("ref", "loop"),
                (
                    "let",
                    "step",
                    (
                        "closure",
                        ("m",),
                        ("again",),
                        ("apply", ("arg", "again"), ("arg", "m")),
                    ),
                    (
                        "apply",
                        ("arg", "step"),
                        ("sub", n, ("lit", 1)),
                    ),
                ),
            ),
        )
        state = loaded({
            LOOP: Function(("n",), body),
            EntityID("loop.links"): links(LOOP, loop=LOOP),
        })

        with mock.patch.object(bytecode, "CALL_DEPTH_LIMIT", 20):
            self.assertEqual(run(Runtime(state), LOOP, 2000), "done")


class GraphFormTests(unittest.TestCase):
    def test_closure_survives_graph_form_round_trip(self) -> None:
        body = (
            "let",
            "n",
            ("lit", 4),
            make_adder_body(),
        )
        state = loaded({F: Function((), body)})

        self.assertEqual(function_at(state, F), Function((), body))

    def test_malformed_closure_metadata_is_not_normalized_by_round_trip(
        self,
    ) -> None:
        body = (
            "closure",
            ["x"],
            ["n"],
            ("lit", 1),
        )
        expected = Function((), body)
        state = loaded({F: expected})

        self.assertEqual(function_at(state, F), expected)

    def test_closure_is_a_graph_node_with_its_body_as_a_child(self) -> None:
        state = loaded({
            F: Function(("n",), make_adder_body()),
        })

        closures = []

        for value in state.values.values():
            node = relation_of(value)

            if node is not None and node.kind == "closure":
                closures.append(node)

        self.assertEqual(len(closures), 1)
        self.assertEqual(set(closures[0].roles), {"body"})
        self.assertIsInstance(closures[0].roles["body"], EntityID)


class CorpusTests(unittest.TestCase):
    def test_make_adder_and_compose_are_corpus_programs(self) -> None:
        names = {example.name for example in EXAMPLES}

        self.assertIn("make_adder", names)
        self.assertIn("compose", names)

    def test_closures_close_the_last_known_corpus_gap(self) -> None:
        self.assertEqual(MISSING, ())


if __name__ == "__main__":
    unittest.main()
