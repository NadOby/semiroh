"""Tests for executable evaluators and constraint results."""

import unittest

from semiroh import ConstraintResult, Evaluator, canonicalize


class EvaluatorTests(unittest.TestCase):
    def test_satisfied_result(self) -> None:
        evaluator = Evaluator(
            predicate=lambda value: (
                ConstraintResult.SATISFIED
                if value > 0
                else ConstraintResult.VIOLATED
            )
        )

        self.assertEqual(
            evaluator.evaluate(1),
            ConstraintResult.SATISFIED,
        )

    def test_violated_result(self) -> None:
        evaluator = Evaluator(
            predicate=lambda value: (
                ConstraintResult.SATISFIED
                if value > 0
                else ConstraintResult.VIOLATED
            )
        )

        self.assertEqual(
            evaluator.evaluate(-1),
            ConstraintResult.VIOLATED,
        )

    def test_unknown_result(self) -> None:
        evaluator = Evaluator(
            predicate=lambda _: ConstraintResult.UNKNOWN
        )

        self.assertEqual(
            evaluator.evaluate(None),
            ConstraintResult.UNKNOWN,
        )

    def test_invalid_predicate_result_is_rejected(self) -> None:
        evaluator = Evaluator(
            predicate=lambda _: True,  # type: ignore[return-value]
        )

        with self.assertRaises(TypeError):
            evaluator.evaluate(None)

    def test_predicate_receives_canonical_content(self) -> None:
        seen = []

        def record(subject: object) -> ConstraintResult:
            seen.append(subject)
            return ConstraintResult.SATISFIED

        Evaluator(predicate=record).evaluate([1, (2, b"x")])

        self.assertEqual(seen, [canonicalize([1, (2, b"x")])])

    def test_subject_must_be_canonicalizable(self) -> None:
        evaluator = Evaluator(
            predicate=lambda _: ConstraintResult.SATISFIED,
        )

        with self.assertRaises(TypeError):
            evaluator.evaluate(object())

    def test_description_is_preserved(self) -> None:
        evaluator = Evaluator(
            predicate=lambda _: ConstraintResult.UNKNOWN,
            description="value is known",
        )

        self.assertEqual(
            evaluator.description,
            "value is known",
        )

    def test_evaluator_is_immutable(self) -> None:
        evaluator = Evaluator(
            predicate=lambda _: ConstraintResult.UNKNOWN,
        )

        with self.assertRaises(AttributeError):
            evaluator.description = "changed"  # type: ignore[misc]

    def test_evaluator_api_is_exported(self) -> None:
        evaluator = Evaluator(
            predicate=lambda _: ConstraintResult.SATISFIED,
        )

        self.assertIsInstance(
            evaluator.evaluate(None),
            ConstraintResult,
        )

    def test_non_callable_predicate_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            Evaluator(
                predicate=42,  # type: ignore[arg-type]
            )

    def test_non_string_description_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            Evaluator(
                predicate=lambda _: ConstraintResult.UNKNOWN,
                description=42,  # type: ignore[arg-type]
            )

    def test_constraint_result_values_are_stable(self) -> None:
        self.assertEqual(
            ConstraintResult.SATISFIED.value,
            "satisfied",
        )
        self.assertEqual(
            ConstraintResult.VIOLATED.value,
            "violated",
        )
        self.assertEqual(
            ConstraintResult.UNKNOWN.value,
            "unknown",
        )

    def test_constraint_result_members_are_distinct(self) -> None:
        self.assertNotEqual(
            ConstraintResult.SATISFIED,
            ConstraintResult.VIOLATED,
        )
        self.assertNotEqual(
            ConstraintResult.SATISFIED,
            ConstraintResult.UNKNOWN,
        )
        self.assertNotEqual(
            ConstraintResult.VIOLATED,
            ConstraintResult.UNKNOWN,
        )

    def test_unknown_result_is_not_known(self) -> None:
        self.assertFalse(
            ConstraintResult.UNKNOWN.is_known
        )

    def test_satisfied_result_is_known(self) -> None:
        self.assertTrue(
            ConstraintResult.SATISFIED.is_known
        )

    def test_violated_result_is_known(self) -> None:
        self.assertTrue(
            ConstraintResult.VIOLATED.is_known
        )
