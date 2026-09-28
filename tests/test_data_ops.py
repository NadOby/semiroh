"""Acceptance tests for tuples, let, function references and tail calls
(docs/language_data.md)."""

import unittest

from semiroh import (
    CellDeclaration,
    EntityID,
    IsKind,
    Runtime,
    State,
    Value,
    canonical_serialize,
    canonicalize,
)
from semiroh.examples import EXAMPLES, MISSING, TAGS
from semiroh.lang import Function, LanguageError, links, load, run

F = EntityID("f")
DOUBLE = EntityID("double")
QUAD = EntityID("quad")
TWICE = EntityID("twice")
CALLER = EntityID("caller")
FCELL = EntityID("fcell")
STORE = EntityID("store")
USE = EntityID("use")
SUM = EntityID("sum")


def program(functions: dict, **link_targets: dict) -> State:
    """functions: entity -> Function; link_targets: name of entity -> links."""

    entities = dict(functions)

    for entity in list(functions):
        targets = link_targets.get(entity.value)

        if targets:
            entities[EntityID(f"{entity.value}.links")] = links(entity, **targets)

    return load(State.create({
        entity: Value.create(entity, content) for entity, content in entities.items()
    }))


def one(body: tuple, params: tuple = ("t",)) -> State:
    return program({F: Function(params, body)})


BASE = {
    DOUBLE: Function(("x",), ("add", ("arg", "x"), ("arg", "x"))),
    QUAD: Function(("x",), ("call", "double", ("call", "double", ("arg", "x")))),
}
BASE_LINKS = {"quad": {"double": DOUBLE}}


class TupleTests(unittest.TestCase):
    def assertSame(self, actual: object, expected: object) -> None:
        self.assertEqual(
            canonical_serialize(canonicalize(actual)),
            canonical_serialize(canonicalize(expected)),
        )

    def test_tuple_operations(self) -> None:
        t = ("arg", "t")
        body = (
            "tuple",
            ("len", t),
            ("item", t, ("lit", 1)),
            ("slice", t, ("lit", 1), ("lit", 3)),
            ("concat", t, ("tuple", ("lit", 9))),
            ("tuple",),
        )

        self.assertSame(
            run(Runtime(one(body)), F, (4, 5, 6)),
            (3, 5, (5, 6), (4, 5, 6, 9), ()),
        )

    def test_tuple_errors(self) -> None:
        t = ("arg", "t")

        for body in (
            ("item", t, ("lit", 3)),
            ("item", t, ("lit", -1)),
            ("item", t, ("lit", True)),
            ("item", ("lit", 5), ("lit", 0)),
            ("len", ("lit", 5)),
            ("slice", t, ("lit", 2), ("lit", 1)),
            ("slice", t, ("lit", 0), ("lit", 4)),
            ("slice", t, ("lit", -1), ("lit", 2)),
            ("concat", t, ("lit", 1)),
        ):
            with self.subTest(body=body):
                with self.assertRaises(LanguageError):
                    run(Runtime(one(body)), F, (4, 5, 6))


class LetTests(unittest.TestCase):
    def test_let_binds_a_local_name(self) -> None:
        body = (
            "let", "y", ("mul", ("arg", "x"), ("lit", 2)),
            ("let", "z", ("add", ("arg", "y"), ("lit", 1)),
             ("add", ("arg", "z"), ("arg", "x"))),
        )

        self.assertEqual(run(Runtime(one(body, ("x",))), F, 3), 10)

    def test_let_rejects_shadowing_and_bad_names(self) -> None:
        for body in (
            ("let", "x", ("lit", 1), ("arg", "x")),  # shadows a parameter
            ("let", "y", ("lit", 1), ("let", "y", ("lit", 2), ("arg", "y"))),
            ("let", "", ("lit", 1), ("lit", 0)),
            ("let", 5, ("lit", 1), ("lit", 0)),
        ):
            with self.subTest(body=body):
                with self.assertRaises(LanguageError):
                    run(Runtime(one(body, ("x",))), F, 3)


class ReferenceTests(unittest.TestCase):
    def test_apply_calls_a_passed_function(self) -> None:
        state = program(
            {
                **BASE,
                TWICE: Function(
                    ("f", "x"),
                    ("apply", ("arg", "f"), ("apply", ("arg", "f"), ("arg", "x"))),
                ),
                CALLER: Function((), ("call", "twice", ("ref", "double"), ("lit", 5))),
            },
            **BASE_LINKS,
            caller={"twice": TWICE, "double": DOUBLE},
        )

        self.assertEqual(run(Runtime(state), CALLER), 20)

    def test_a_cell_can_hold_a_reference(self) -> None:
        state = program(
            {
                **BASE,
                FCELL: CellDeclaration(IsKind("entity_id"), DOUBLE),
                STORE: Function((), ("write", "fcell", ("ref", "quad"))),
                USE: Function(("x",), ("apply", ("read", "fcell"), ("arg", "x"))),
            },
            **BASE_LINKS,
            store={"fcell": FCELL, "quad": QUAD},
            use={"fcell": FCELL},
        )
        runtime = Runtime(state)

        self.assertEqual(run(runtime, USE, 3), 6)
        run(runtime, STORE)
        self.assertEqual(run(runtime, USE, 3), 12)

    def test_reference_errors(self) -> None:
        for body in (
            ("apply", ("lit", 5), ("lit", 1)),  # not a reference
            ("ref", "fcell"),  # a cell, not a function
            ("apply", ("ref", "double")),  # wrong arity
        ):
            with self.subTest(body=body):
                state = program(
                    {
                        **BASE,
                        FCELL: CellDeclaration(IsKind("entity_id"), DOUBLE),
                        F: Function((), body),
                    },
                    **BASE_LINKS,
                    f={"double": DOUBLE, "fcell": FCELL},
                )

                with self.assertRaises(LanguageError):
                    run(Runtime(state), F)


class TailCallTests(unittest.TestCase):
    def test_tail_calls_run_in_constant_stack(self) -> None:
        n, acc = ("arg", "n"), ("arg", "acc")
        state = program(
            {
                SUM: Function(
                    ("n", "acc"),
                    (
                        "if",
                        ("eq", n, ("lit", 0)),
                        acc,
                        (
                            "let", "next", ("sub", n, ("lit", 1)),
                            ("seq",
                             ("lit", None),
                             ("call", "sum", ("arg", "next"), ("add", acc, n))),
                        ),
                    ),
                ),
            },
            sum={"sum": SUM},
        )
        runtime = Runtime(state)

        self.assertEqual(run(runtime, SUM, 5000, 0), 12502500)
        self.assertEqual(runtime.active.holds, frozenset())


class CorpusTierTwoTests(unittest.TestCase):
    def test_new_tags_are_covered(self) -> None:
        self.assertLessEqual({"data", "higher order"}, set(TAGS))

        for tag in ("data", "higher order"):
            self.assertTrue(any(tag in example.tags for example in EXAMPLES))

        # The sort-swap canary: higher order code changed while running.
        self.assertTrue(any(
            {"higher order", "self-modification"} <= set(example.tags)
            for example in EXAMPLES
        ))

    def test_found_gaps_are_closed(self) -> None:
        closed = {"insertion_sort", "map_and_fold", "local_variables", "deep_loop"}

        self.assertFalse(closed & {wanted.name for wanted in MISSING})


if __name__ == "__main__":
    unittest.main()
