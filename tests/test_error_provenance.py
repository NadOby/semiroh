"""Catch accepts only errors that originated in its own SHEAR run.

``catch`` turns a failure into ``("failed", error)`` only when the machine
of the same logical run created that error. A host exception that merely
carries an ``.error`` tuple, or a SHEAR error escaping an independent ``run``
started by host code such as an external evaluator, escapes unchanged.
Nested execution that belongs to the same run, such as ``trial``, stays
catchable.
"""

from __future__ import annotations

import unittest
from typing import Any, Callable

from shear import (
    CellContentRejected,
    CellDeclaration,
    ConstraintResult,
    EntityID,
    EvaluationContext,
    Evaluator,
    External,
    Runtime,
    canonical_serialize,
    canonicalize,
)
from shear.examples._support import program
from shear.lang import Function, LanguageError, links, load, run

F = EntityID("f")
G = EntityID("g")
POWER = EntityID("power")
AUDITED = EntityID("audited")


def same(left: Any, right: Any) -> bool:
    return canonical_serialize(canonicalize(left)) == canonical_serialize(
        canonicalize(right)
    )


class _Forged(Exception):
    """A host exception that imitates a SHEAR error."""


def _inner_runtime(body: Any) -> Runtime:
    return Runtime(load(program({G: Function((), body)})))


def _outer(predicate: Callable[[Any], ConstraintResult]) -> Runtime:
    """A program whose one write is checked by ``predicate`` under catch.

    The initial content 0 is always accepted; ``predicate`` sees only writes.
    """

    def audit(value: Any) -> ConstraintResult:
        if value == 0:
            return ConstraintResult.SATISFIED
        return predicate(value)

    context = EvaluationContext(externals={"audit": Evaluator(audit)})
    return Runtime(
        load(program({
            AUDITED: CellDeclaration(External("audit"), 0),
            F: Function(
                ("v",),
                ("catch", ("write", "audited", ("arg", "v"))),
            ),
            EntityID("f.links"): links(F, audited=AUDITED),
        })),
        context,
    )


class ForeignErrorTests(unittest.TestCase):
    def test_a_forged_error_attribute_is_not_catchable(self) -> None:
        forged = ("program", "forged", 0, (F, F))

        def predicate(value: Any) -> ConstraintResult:
            exc = _Forged("host failure")
            exc.error = forged
            raise exc

        runtime = _outer(predicate)

        with self.assertRaises(_Forged) as raised:
            run(runtime, F, 1)

        self.assertEqual(str(raised.exception), "host failure")
        self.assertIs(raised.exception.error, forged)
        self.assertEqual(runtime.read(AUDITED), 0)

    def test_an_independent_run_failure_escapes_the_outer_catch(self) -> None:
        inner = _inner_runtime(("raise", ("lit", "inner"), ("lit", 7)))

        def predicate(value: Any) -> ConstraintResult:
            run(inner, G)
            return ConstraintResult.SATISFIED

        runtime = _outer(predicate)

        with self.assertRaises(LanguageError) as raised:
            run(runtime, F, 1)

        self.assertEqual(type(raised.exception).__name__, "Raised")
        self.assertEqual(str(raised.exception), "g: inner")
        origin, kind, detail, where = raised.exception.error
        self.assertEqual((origin, kind, detail), ("program", "inner", 7))
        self.assertEqual(where[0], G)
        self.assertEqual(runtime.read(AUDITED), 0)

    def test_an_independent_run_still_catches_its_own_errors(self) -> None:
        inner = _inner_runtime(
            ("catch", ("raise", ("lit", "inner"), ("lit", 7)))
        )
        seen = []

        def predicate(value: Any) -> ConstraintResult:
            seen.append(run(inner, G))
            return ConstraintResult.SATISFIED

        runtime = _outer(predicate)

        self.assertTrue(same(run(runtime, F, 1), ("ok", 1)))
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][0], "failed")
        self.assertEqual(seen[0][1][:3], ("program", "inner", 7))
        self.assertEqual(runtime.read(AUDITED), 1)

    def test_the_outer_run_catches_its_own_errors_after_an_inner_run(self) -> None:
        inner = _inner_runtime(("raise", ("lit", "inner"), ("lit", 7)))

        def predicate(value: Any) -> ConstraintResult:
            try:
                run(inner, G)
            except LanguageError:
                return ConstraintResult.VIOLATED
            return ConstraintResult.SATISFIED

        runtime = _outer(predicate)
        result = run(runtime, F, 1)

        self.assertEqual(result[0], "failed")
        self.assertEqual(result[1][:2], ("runtime", "cell_rejected"))
        self.assertEqual(runtime.read(AUDITED), 0)

    def test_a_runtime_rejection_escaping_an_inner_run_is_not_caught(self) -> None:
        inner_context = EvaluationContext(externals={
            "never": Evaluator(
                lambda value: ConstraintResult.SATISFIED
                if value == 0
                else ConstraintResult.VIOLATED
            ),
        })
        cell = EntityID("cell")
        inner = Runtime(
            load(program({
                cell: CellDeclaration(External("never"), 0),
                G: Function((), ("write", "cell", ("lit", 1))),
                EntityID("g.links"): links(G, cell=cell),
            })),
            inner_context,
        )

        def predicate(value: Any) -> ConstraintResult:
            run(inner, G)
            return ConstraintResult.SATISFIED

        runtime = _outer(predicate)

        with self.assertRaises(CellContentRejected) as raised:
            run(runtime, F, 1)

        self.assertEqual(raised.exception.error[:2], ("runtime", "cell_rejected"))
        self.assertEqual(raised.exception.error[3][0], G)


class SameRunTests(unittest.TestCase):
    def test_a_raise_under_trial_is_caught_by_the_enclosing_catch(self) -> None:
        runtime = Runtime(
            load(program({
                POWER: Function(("x",), ("lit", 1)),
                F: Function(
                    ("x",),
                    (
                        "catch",
                        (
                            "trial",
                            ("call", "power", ("arg", "x")),
                            "power",
                            (
                                "function",
                                ("lit", ("y",)),
                                (
                                    "lit",
                                    ("raise", ("lit", "nested"), ("arg", "y")),
                                ),
                            ),
                        ),
                        ("nested",),
                    ),
                ),
                EntityID("f.links"): links(F, power=POWER),
            }))
        )
        before = runtime.active.state.id

        result = run(runtime, F, 3, may_activate=True)

        self.assertEqual(result[0], "failed")
        origin, kind, detail, where = result[1]
        self.assertEqual((origin, kind, detail), ("program", "nested", 3))
        self.assertEqual(where[0], POWER)
        self.assertEqual(runtime.active.state.id, before)
        self.assertEqual(runtime.active.holds, frozenset())


if __name__ == "__main__":
    unittest.main()
