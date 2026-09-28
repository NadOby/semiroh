"""Tests for semantic constraints."""

import unittest

from semiroh import Constraint, ConstraintResult, canonicalize


class ConstraintTests(unittest.TestCase):
    def test_satisfied_constraint(self) -> None:
        constraint = Constraint(
            predicate=lambda value: (
                ConstraintResult.SATISFIED
                if value > 0
                else ConstraintResult.VIOLATED
            )
        )

        self.assertEqual(
            constraint.evaluate(1),
            ConstraintResult.SATISFIED,
        )

    def test_violated_constraint(self) -> None:
        constraint = Constraint(
            predicate=lambda value: (
                ConstraintResult.SATISFIED
                if value > 0
                else ConstraintResult.VIOLATED
            )
        )

        self.assertEqual(
            constraint.evaluate(-1),
            ConstraintResult.VIOLATED,
        )

    def test_unknown_constraint(self) -> None:
        constraint = Constraint(
            predicate=lambda _: ConstraintResult.UNKNOWN
        )

        self.assertEqual(
            constraint.evaluate(None),
            ConstraintResult.UNKNOWN,
        )

    def test_invalid_predicate_result_is_rejected(self) -> None:
        constraint = Constraint(
            predicate=lambda _: True,  # type: ignore[return-value]
        )

        with self.assertRaises(TypeError):
            constraint.evaluate(None)

    def test_predicate_receives_canonical_content(self) -> None:
        seen = []

        def record(subject: object) -> ConstraintResult:
            seen.append(subject)
            return ConstraintResult.SATISFIED

        Constraint(predicate=record).evaluate([1, (2, b"x")])

        self.assertEqual(seen, [canonicalize([1, (2, b"x")])])

    def test_subject_must_be_canonicalizable(self) -> None:
        constraint = Constraint(
            predicate=lambda _: ConstraintResult.SATISFIED,
        )

        with self.assertRaises(TypeError):
            constraint.evaluate(object())

    def test_description_is_preserved(self) -> None:
        constraint = Constraint(
            predicate=lambda _: ConstraintResult.UNKNOWN,
            description="value is known",
        )

        self.assertEqual(
            constraint.description,
            "value is known",
        )

    def test_constraint_is_immutable(self) -> None:
        constraint = Constraint(
            predicate=lambda _: ConstraintResult.UNKNOWN,
        )

        with self.assertRaises(AttributeError):
            constraint.description = "changed"  # type: ignore[misc]

    def test_constraint_api_is_exported(self) -> None:
        constraint = Constraint(
            predicate=lambda _: ConstraintResult.SATISFIED,
        )

        self.assertIsInstance(
            constraint.evaluate(None),
            ConstraintResult,
        )

    def test_non_callable_predicate_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            Constraint(
                predicate=42,  # type: ignore[arg-type]
            )

    def test_non_string_description_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            Constraint(
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
