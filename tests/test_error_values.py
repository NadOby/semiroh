"""Exact error values and graph form for failures the acceptance file only
classifies.

Each test pins a part of docs/error_handling.md (catalogue §6, detail §4,
graph form §2) that the mutation campaign showed no test observed.
"""

from __future__ import annotations

import unittest
from typing import Any

from shear import (
    AllOf,
    CellDeclaration,
    ConstraintResult,
    EntityID,
    EvaluationContext,
    Evaluator,
    External,
    IntRange,
    IsKind,
    Relation,
    Role,
    Runtime,
    canonical_serialize,
    canonicalize,
)
from shear.bytecode import CALL_DEPTH_LIMIT
from shear.examples._support import program
from shear.lang import Function, LanguageError, links, load, run
from shear.relations import relation_of
from shear.syntax import parse, render_program

F = EntityID("f")
G = EntityID("g")
CELL = EntityID("cell")
LOW = EntityID("low")
HIGH = EntityID("high")
ORDER = EntityID("order")
MAKE = EntityID("make")
APPLY = EntityID("apply")
APPLYV = EntityID("applyv")


def same(left: Any, right: Any) -> bool:
    return canonical_serialize(canonicalize(left)) == canonical_serialize(
        canonicalize(right)
    )


def failed_value(result: Any) -> tuple:
    assert result[0] == "failed", result
    return result[1]


def nodes_of(runtime: Runtime, function: EntityID, kind: str) -> list:
    state = runtime.active.state
    found = []

    for entity in state.owned_subtree(function):
        if entity == function:
            continue

        relation = relation_of(state.values[entity])

        if relation is not None and relation.kind == kind:
            found.append(entity)

    return found


class RuntimeErrorValueTests(unittest.TestCase):
    def assertSame(self, actual: Any, expected: Any) -> None:
        self.assertTrue(same(actual, expected), f"{actual!r} != {expected!r}")

    def test_a_relation_rejected_write_is_caught_with_its_error_value(self) -> None:
        def ordered(subject: Any) -> ConstraintResult:
            roles = dict(subject[2])
            return (
                ConstraintResult.SATISFIED
                if roles["low"] <= roles["high"]
                else ConstraintResult.VIOLATED
            )

        runtime = Runtime(
            load(program({
                LOW: CellDeclaration(IsKind("int"), 0),
                HIGH: CellDeclaration(IsKind("int"), 10),
                ORDER: Relation(
                    "bound",
                    {"low": LOW, "high": HIGH},
                    payload=AllOf(
                        Role("low", IsKind("int")),
                        Role("high", IsKind("int")),
                        External("ordered"),
                    ),
                ),
                F: Function(("v",), ("catch", ("write", "low", ("arg", "v")))),
                EntityID("f.links"): links(F, low=LOW),
            })),
            EvaluationContext({"ordered": Evaluator(ordered)}),
        )
        (write,) = nodes_of(runtime, F, "write")

        self.assertSame(
            run(runtime, F, 20),
            (
                "failed",
                (
                    "runtime",
                    "relation_rejected",
                    (
                        ("constraint", "violated"),
                        ("operation", "write"),
                        ("relation", ORDER),
                    ),
                    (F, write),
                ),
            ),
        )
        self.assertEqual(runtime.read(LOW), 0)

    def test_an_activation_rejection_is_caught_with_only_its_reason(self) -> None:
        def activate(value: int) -> tuple:
            return (
                "activate",
                "g",
                ("function", ("lit", ()), ("lit", ("lit", value))),
            )

        runtime = Runtime(load(program({
            G: Function((), ("lit", 1)),
            F: Function(
                (),
                ("tuple", activate(2), ("catch", activate(3))),
            ),
            EntityID("f.links"): links(F, g=G),
        })))
        first, second = sorted(
            nodes_of(runtime, F, "activate"),
            key=lambda entity: entity.value,
        )

        result = run(runtime, F, may_activate=True)

        self.assertIsNone(result[0])
        self.assertSame(
            failed_value(result[1]),
            (
                "runtime",
                "activation_rejected",
                (("reason", "the previous version is still held"),),
                (F, second),
            ),
        )
        self.assertEqual(run(runtime, G), 2)


class LanguageErrorValueTests(unittest.TestCase):
    def assertSame(self, actual: Any, expected: Any) -> None:
        self.assertTrue(same(actual, expected), f"{actual!r} != {expected!r}")

    def test_code_of_a_cell_is_not_a_function(self) -> None:
        runtime = Runtime(load(program({
            CELL: CellDeclaration(IntRange(0, 9), 0),
            F: Function((), ("catch", ("code", "cell"))),
            EntityID("f.links"): links(F, cell=CELL),
        })))
        (code,) = nodes_of(runtime, F, "code")

        self.assertSame(
            run(runtime, F),
            (
                "failed",
                (
                    "language",
                    "not_a_function",
                    (("entity", CELL), ("operation", "code")),
                    (F, code),
                ),
            ),
        )

    def test_ref_and_linksof_of_a_cell_are_not_a_function(self) -> None:
        for operation in ("ref", "linksof"):
            with self.subTest(operation=operation):
                runtime = Runtime(load(program({
                    CELL: CellDeclaration(IntRange(0, 9), 0),
                    F: Function((), ("catch", (operation, "cell"))),
                    EntityID("f.links"): links(F, cell=CELL),
                })))
                (node,) = nodes_of(runtime, F, operation)

                self.assertSame(
                    run(runtime, F),
                    (
                        "failed",
                        (
                            "language",
                            "not_a_function",
                            (("entity", CELL), ("operation", operation)),
                            (F, node),
                        ),
                    ),
                )

    def test_applying_a_non_callable_names_the_applying_operation(self) -> None:
        for operation, body in (
            ("apply", ("apply", ("lit", 7), ("lit", 1))),
            ("applyv", ("applyv", ("lit", 7), ("lit", (1,)))),
        ):
            with self.subTest(operation=operation):
                runtime = Runtime(load(program({F: Function((), ("catch", body))})))
                result = run(runtime, F)

                self.assertEqual(result[1][:2], ("language", "wrong_kind"))
                self.assertEqual(dict(result[1][2])["operation"], operation)

    def test_applying_a_stale_closure_names_the_applying_operation(self) -> None:
        state = load(program({
            MAKE: Function(
                ("n",),
                ("closure", ("x",), ("n",), ("add", ("arg", "n"), ("arg", "x"))),
            ),
            APPLY: Function(
                ("f", "x"),
                ("catch", ("apply", ("arg", "f"), ("arg", "x"))),
            ),
            APPLYV: Function(
                ("f", "args"),
                ("catch", ("applyv", ("arg", "f"), ("arg", "args"))),
            ),
        }))
        closure = run(Runtime(state), MAKE, 4)
        changed = Runtime(state.with_changes({MAKE: 0}))

        for entry, operation, args in (
            (APPLY, "apply", (3,)),
            (APPLYV, "applyv", ((3,),)),
        ):
            with self.subTest(operation=operation):
                (node,) = nodes_of(changed, entry, operation)
                self.assertSame(
                    run(changed, entry, closure, *args),
                    (
                        "failed",
                        (
                            "language",
                            "not_a_function",
                            (("entity", MAKE), ("operation", operation)),
                            (entry, node),
                        ),
                    ),
                )


class MalformedCatchGraphFormTests(unittest.TestCase):
    def assertSame(self, actual: Any, expected: Any) -> None:
        self.assertTrue(same(actual, expected), f"{actual!r} != {expected!r}")

    def test_a_malformed_catch_loads_as_an_invalid_node(self) -> None:
        cases = (
            (
                ("catch",),
                "catch takes one or two operands, got 0",
            ),
            (
                ("catch", ("lit", 1), ("a",), ("b",)),
                "catch takes one or two operands, got 3",
            ),
            (
                ("catch", ("lit", 1), ("a", "a")),
                "catch kinds must be a non-empty tuple of distinct "
                "non-empty strings",
            ),
        )

        for body, problem in cases:
            with self.subTest(body=body):
                runtime = Runtime(load(program({F: Function((), body)})))
                (invalid,) = nodes_of(runtime, F, "invalid")
                relation = relation_of(runtime.active.state.values[invalid])

                self.assertEqual(relation.roles, {})
                self.assertSame(relation.payload, (problem, body))

                with self.assertRaises(LanguageError) as raised:
                    run(runtime, F)

                self.assertEqual(
                    raised.exception.error[:2],
                    ("language", "invalid_code"),
                )
                self.assertEqual(raised.exception.error[3], (F, invalid))


class CatchFrameTests(unittest.TestCase):
    def test_a_call_caught_directly_still_takes_a_call_level(self) -> None:
        """The body of a catch is not in tail position (language_data.md
        section 4), so the catch's own call level counts toward the limit."""

        runtime = Runtime(load(program({
            F: Function(("n",), ("catch", ("call", "g", ("arg", "n")))),
            G: Function(
                ("n",),
                (
                    "if",
                    ("lt", ("arg", "n"), ("lit", 1)),
                    ("lit", 0),
                    ("add", ("lit", 1), ("call", "g", ("sub", ("arg", "n"), ("lit", 1)))),
                ),
            ),
            EntityID("f.links"): links(F, g=G),
            EntityID("g.links"): links(G, g=G),
        })))

        self.assertEqual(
            run(runtime, F, CALL_DEPTH_LIMIT - 2),
            ("ok", CALL_DEPTH_LIMIT - 2),
        )
        self.assertEqual(
            run(runtime, F, CALL_DEPTH_LIMIT - 1)[1][:2],
            ("limit", "depth_limit"),
        )


class CatchRenderingTests(unittest.TestCase):
    def test_a_hand_built_malformed_catch_renders_as_raw(self) -> None:
        for kinds in ((), ("a", "a"), (1,), ("",)):
            with self.subTest(kinds=kinds):
                state = load(program({F: Function((), ("catch", ("lit", 1)))}))
                runtime = Runtime(state)
                (catch,) = nodes_of(runtime, F, "catch")
                relation = relation_of(state.values[catch])
                broken = state.with_changes({
                    catch: Relation("catch", relation.roles, kinds),
                })

                text = render_program(broken)

                self.assertIn("raw(", text)
                self.assertNotIn("catch(", text)

    def test_a_non_ascii_catch_kind_renders_as_written(self) -> None:
        text = 'fn f():\n    catch(1, "fehlt\u00e9", "\u043d\u0435\u0442")\n'

        self.assertEqual(render_program(load(parse(text))), text)


if __name__ == "__main__":
    unittest.main()
