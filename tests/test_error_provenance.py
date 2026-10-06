"""Catch accepts only errors that originated in its own SHEAR run.

``catch`` turns a failure into ``("failed", error)`` only when the machine
of the same logical run created that error. A host exception that merely
carries an ``.error`` tuple, or a SHEAR error escaping an independent ``run``
started by host code such as an external evaluator, escapes unchanged.
Nested execution that belongs to the same run, such as ``trial``, stays
catchable. An exception escaping an evaluator is a failure of the model
(error_handling.md section 1), so it escapes even when its class is one the
machine maps, such as a rejection raised by another runtime.
"""

from __future__ import annotations

import unittest
from typing import Any, Callable

from shear import (
    ActivationRejected,
    CellContentRejected,
    CellError,
    IntRange,
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
from shear.lang import Function, LanguageError, define, links, load, run

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


def _guarded_program(body: Any, evaluator: Callable[[Any], ConstraintResult]) -> Runtime:
    """``body`` runs with cell ``audited`` checked by ``evaluator``; the
    initial content 0 is accepted without calling it."""

    def audit(value: Any) -> ConstraintResult:
        if value == 0 and not calls:
            calls.append(value)
            return ConstraintResult.SATISFIED
        return evaluator(value)

    calls: list = []
    context = EvaluationContext(externals={"audit": Evaluator(audit)})
    return Runtime(
        load(program({
            AUDITED: CellDeclaration(External("audit"), 0),
            G: Function((), ("lit", 1)),
            F: Function(("v",), body),
            EntityID("f.links"): links(F, audited=AUDITED, g=G),
        })),
        context,
    )


class HostCallbackFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inner_cell = EntityID("inner")
        self.inner_function = EntityID("inner_function")
        self.inner = Runtime(load(program({
            self.inner_cell: CellDeclaration(IntRange(0, 0), 0),
            self.inner_function: Function((), ("lit", 1)),
        })))

    def raising(self, operation: Callable[[], Any]) -> tuple[list, Callable]:
        raised: list = []

        def evaluator(value: Any) -> ConstraintResult:
            try:
                operation()
            except BaseException as exc:
                raised.append(exc)
                raise
            return ConstraintResult.SATISFIED

        return raised, evaluator

    def test_another_runtimes_rejected_write_escapes_catch_write(self) -> None:
        raised, evaluator = self.raising(
            lambda: self.inner.write(self.inner_cell, 1)
        )
        runtime = _guarded_program(
            ("catch", ("write", "audited", ("arg", "v"))), evaluator
        )

        with self.assertRaises(CellContentRejected) as caught:
            run(runtime, F, 1)

        self.assertIs(caught.exception, raised[0])
        self.assertFalse(hasattr(caught.exception, "error"))
        self.assertEqual(runtime.read(AUDITED), 0)

    def test_another_runtimes_non_cell_write_escapes_unwrapped(self) -> None:
        raised, evaluator = self.raising(
            lambda: self.inner.write(self.inner_function, 1)
        )
        runtime = _guarded_program(
            ("catch", ("write", "audited", ("arg", "v"))), evaluator
        )

        with self.assertRaises(CellError) as caught:
            run(runtime, F, 1)

        self.assertIs(caught.exception, raised[0])
        self.assertNotIsInstance(caught.exception, LanguageError)

    def test_another_runtimes_rejected_activation_escapes_activate_and_trial(
        self,
    ) -> None:
        unrelated = load(program({G: Function((), ("lit", 9))}))
        stale = define(unrelated, {G: Function((), ("lit", 8))})
        replacement = ("function", ("lit", ()), ("lit", ("lit", 2)))
        bodies = {
            "activate": ("catch", ("activate", "g", replacement)),
            "trial": ("catch", ("trial", ("call", "g"), "g", replacement)),
        }

        for operation, body in bodies.items():
            with self.subTest(operation=operation):
                raised, evaluator = self.raising(
                    lambda: self.inner.activate(stale)
                )
                runtime = _guarded_program(body, evaluator)
                before = runtime.active.state.id

                with self.assertRaises(ActivationRejected) as caught:
                    run(runtime, F, 0, may_activate=True)

                self.assertIs(caught.exception, raised[0])
                self.assertFalse(hasattr(caught.exception, "error"))
                self.assertEqual(runtime.active.state.id, before)

    def test_a_rejecting_evaluator_is_still_a_catchable_runtime_error(self) -> None:
        runtime = _guarded_program(
            ("catch", ("write", "audited", ("arg", "v"))),
            lambda value: ConstraintResult.VIOLATED,
        )

        result = run(runtime, F, 1)

        self.assertEqual(result[1][:2], ("runtime", "cell_rejected"))
        self.assertEqual(dict(result[1][2])["cell"], AUDITED)


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
