"""Tests for semantic constraints and three-valued composition."""

import random
import unittest
from typing import Any

from semiroh import (
    AllOf,
    AnyOf,
    Constraint,
    ConstraintResult,
    EntityID,
    EvaluationContext,
    External,
    IntRange,
    IsKind,
    Length,
    Not,
    OneOf,
    SemanticConstraint,
    State,
    Value,
    canonicalize,
    kind_of,
)

SAT = ConstraintResult.SATISFIED
VIO = ConstraintResult.VIOLATED
UNK = ConstraintResult.UNKNOWN

# Named evaluators that ignore the subject, for truth-table tests.
CONSTANTS = EvaluationContext({
    "sat": Constraint(lambda _: SAT),
    "vio": Constraint(lambda _: VIO),
    "unk": Constraint(lambda _: UNK),
})
CONSTANT = {
    SAT: External("sat"),
    VIO: External("vio"),
    UNK: External("unk"),
}


class PrimitiveConstraintTests(unittest.TestCase):
    def test_kinds_of_canonical_content(self) -> None:
        for content, kind in [
            (None, "none"),
            (True, "bool"),
            (1, "int"),
            ("a", "str"),
            (b"a", "bytes"),
            (EntityID("e"), "entity_id"),
            ((1,), "tuple"),
            ([1], "list"),
            ({"a": 1}, "map"),
        ]:
            with self.subTest(content=content):
                self.assertEqual(kind_of(content), kind)
                self.assertEqual(IsKind(kind).evaluate(content), SAT)

    def test_bool_is_not_int(self) -> None:
        self.assertEqual(IsKind("int").evaluate(True), VIO)
        self.assertEqual(IntRange(0, 1).evaluate(True), VIO)

    def test_unknown_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            IsKind("float")

    def test_int_range_bounds_are_inclusive(self) -> None:
        constraint = IntRange(0, 10)

        self.assertEqual(constraint.evaluate(0), SAT)
        self.assertEqual(constraint.evaluate(10), SAT)
        self.assertEqual(constraint.evaluate(-1), VIO)
        self.assertEqual(constraint.evaluate(11), VIO)
        self.assertEqual(constraint.evaluate("5"), VIO)
        self.assertEqual(IntRange(min=5).evaluate(10**30), SAT)

    def test_invalid_bounds_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            IntRange(2, 1)

        with self.assertRaises(TypeError):
            IntRange(0, True)  # type: ignore[arg-type]

        with self.assertRaises(ValueError):
            Length(-1)

    def test_length_applies_to_sized_kinds(self) -> None:
        constraint = Length(2, 3)

        for subject, expected in [
            ("ab", SAT),
            ("abcd", VIO),
            (b"\x00\x01", SAT),
            (b"\x00", VIO),
            ((1, 2, 3), SAT),
            ([1, 2], SAT),
            ({"a": 1, "b": 2}, SAT),
            (12, VIO),
            (None, VIO),
        ]:
            with self.subTest(subject=subject):
                self.assertEqual(constraint.evaluate(subject), expected)

    def test_one_of_is_type_aware(self) -> None:
        self.assertEqual(OneOf(1, "a").evaluate(1), SAT)
        self.assertEqual(OneOf(1).evaluate(True), VIO)
        self.assertEqual(OneOf((1, 2)).evaluate([1, 2]), VIO)
        self.assertNotEqual(OneOf(True), OneOf(1))


class ExternalConstraintTests(unittest.TestCase):
    def test_missing_evaluator_is_unknown(self) -> None:
        self.assertEqual(External("even").evaluate(2), UNK)

    def test_registered_evaluator_decides(self) -> None:
        context = EvaluationContext({
            "even": Constraint(lambda value: SAT if value % 2 == 0 else VIO),
        })

        self.assertEqual(External("even").evaluate(2, context), SAT)
        self.assertEqual(External("even").evaluate(3, context), VIO)

    def test_evaluator_receives_canonical_subject(self) -> None:
        seen = []

        def record(subject: Any) -> ConstraintResult:
            seen.append(subject)
            return SAT

        context = EvaluationContext({"record": Constraint(record)})
        External("record").evaluate([1, 2], context)

        self.assertEqual(seen, [canonicalize([1, 2])])

    def test_externals_must_be_evaluators(self) -> None:
        with self.assertRaises(TypeError):
            EvaluationContext({"f": lambda _: SAT})  # type: ignore[dict-item]


class CompositionTests(unittest.TestCase):
    def test_truth_tables_follow_strong_kleene_logic(self) -> None:
        order = {VIO: 0, UNK: 1, SAT: 2}

        for left in (SAT, VIO, UNK):
            for right in (SAT, VIO, UNK):
                with self.subTest(left=left, right=right):
                    both = AllOf(CONSTANT[left], CONSTANT[right])
                    either = AnyOf(CONSTANT[left], CONSTANT[right])

                    self.assertEqual(
                        both.evaluate(0, CONSTANTS),
                        min(left, right, key=order.get),
                    )
                    self.assertEqual(
                        either.evaluate(0, CONSTANTS),
                        max(left, right, key=order.get),
                    )

        self.assertEqual(Not(CONSTANT[SAT]).evaluate(0, CONSTANTS), VIO)
        self.assertEqual(Not(CONSTANT[VIO]).evaluate(0, CONSTANTS), SAT)
        self.assertEqual(Not(CONSTANT[UNK]).evaluate(0, CONSTANTS), UNK)

    def test_empty_compositions(self) -> None:
        self.assertEqual(AllOf().evaluate(0), SAT)
        self.assertEqual(AnyOf().evaluate(0), VIO)

    def test_components_have_set_semantics(self) -> None:
        a = IntRange(0, 5)
        b = IsKind("int")

        self.assertEqual(AllOf(a, b), AllOf(b, a, a))
        self.assertEqual(len(AllOf(b, a, a).parts), 2)
        self.assertNotEqual(AllOf(a, b), AnyOf(a, b))

    def test_components_must_be_semantic_constraints(self) -> None:
        with self.assertRaises(TypeError):
            AllOf(Constraint(lambda _: SAT))  # type: ignore[arg-type]


class BudgetTests(unittest.TestCase):
    def test_exhausted_budget_yields_unknown(self) -> None:
        constraint = AllOf(IsKind("int"), IntRange(0, 10))

        self.assertEqual(
            constraint.evaluate(5, EvaluationContext(budget=1)),
            UNK,
        )
        self.assertEqual(
            constraint.evaluate(5, EvaluationContext(budget=3)),
            SAT,
        )

    def test_zero_budget_evaluates_nothing(self) -> None:
        self.assertEqual(
            IsKind("int").evaluate(5, EvaluationContext(budget=0)),
            UNK,
        )

    def test_invalid_budget_is_rejected(self) -> None:
        for budget in (-1, True, 1.5):
            with self.subTest(budget=budget):
                with self.assertRaises(ValueError):
                    EvaluationContext(budget=budget)  # type: ignore[arg-type]


class ConstraintIdentityTests(unittest.TestCase):
    def test_constraints_can_be_program_state(self) -> None:
        rule = EntityID("rule")

        def state_with(constraint: SemanticConstraint) -> State:
            return State.create({rule: Value.create(rule, constraint)})

        self.assertEqual(
            state_with(AllOf(IntRange(0, 9), IsKind("int"))).id,
            state_with(AllOf(IsKind("int"), IntRange(0, 9))).id,
        )
        self.assertNotEqual(
            state_with(IntRange(0, 9)).id,
            state_with(IntRange(0, 10)).id,
        )

    def test_constraints_round_trip_through_content(self) -> None:
        constraint = AnyOf(
            AllOf(IsKind("str"), Length(1, 8)),
            Not(OneOf(None, (1, 2))),
            External("custom"),
            IntRange(max=0),
        )

        rebuilt = SemanticConstraint.from_content(canonicalize(constraint))

        self.assertEqual(rebuilt, constraint)
        self.assertEqual(hash(rebuilt), hash(constraint))

    def test_non_constraint_content_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SemanticConstraint.from_content(canonicalize((1, 2)))


# ---------------------------------------------------------------------------
# Seeded properties
# ---------------------------------------------------------------------------

CASES = 300
SUBJECTS = [None, True, False, 0, 1, 7, -3, "", "ab", b"x", (1, 2), [3], {"k": 1}]


def random_constraint(rng: random.Random, depth: int = 3) -> SemanticConstraint:
    if depth == 0 or rng.random() < 0.35:
        choice = rng.randrange(6)

        if choice == 0:
            return IsKind(rng.choice(sorted(("int", "str", "bool", "none", "tuple"))))

        if choice == 1:
            low = rng.randrange(-2, 3)
            return IntRange(low, low + rng.randrange(0, 8))

        if choice == 2:
            return Length(rng.randrange(0, 2), rng.choice([None, 1, 2]))

        if choice == 3:
            return OneOf(*rng.sample(SUBJECTS, rng.randrange(0, 3)))

        return External(rng.choice(["sat", "vio", "unk", "missing"]))

    kind = rng.randrange(3)
    parts = [random_constraint(rng, depth - 1) for _ in range(rng.randrange(0, 4))]

    if kind == 0:
        return AllOf(*parts)

    if kind == 1:
        return AnyOf(*parts)

    return Not(random_constraint(rng, depth - 1))


class ConstraintProperties(unittest.TestCase):
    def test_de_morgan_and_double_negation_hold(self) -> None:
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                a = random_constraint(rng)
                b = random_constraint(rng)
                subject = rng.choice(SUBJECTS)

                def result(constraint: SemanticConstraint) -> ConstraintResult:
                    return constraint.evaluate(subject, CONSTANTS)

                self.assertEqual(result(Not(Not(a))), result(a))
                self.assertEqual(
                    result(Not(AllOf(a, b))),
                    result(AnyOf(Not(a), Not(b))),
                )
                self.assertEqual(
                    result(Not(AnyOf(a, b))),
                    result(AllOf(Not(a), Not(b))),
                )

    def test_budget_only_ever_withholds_a_result(self) -> None:
        # constraint_model.md §5: a budget never establishes a result. With
        # any budget, evaluation yields either Unknown or the unbudgeted
        # result.
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                constraint = random_constraint(rng)
                subject = rng.choice(SUBJECTS)
                full = constraint.evaluate(subject, CONSTANTS)

                for budget in range(0, 12):
                    limited = constraint.evaluate(
                        subject,
                        EvaluationContext(CONSTANTS.externals, budget),
                    )

                    self.assertIn(limited, (UNK, full))

    def test_identity_is_stable_through_content(self) -> None:
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                constraint = random_constraint(rng)
                rebuilt = SemanticConstraint.from_content(
                    canonicalize(constraint)
                )

                self.assertEqual(rebuilt, constraint)

                for subject in SUBJECTS:
                    self.assertEqual(
                        rebuilt.evaluate(subject, CONSTANTS),
                        constraint.evaluate(subject, CONSTANTS),
                    )


if __name__ == "__main__":
    unittest.main()
