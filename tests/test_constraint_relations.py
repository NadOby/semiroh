"""Tests for constraint relations: constraints over several entities."""

import random
import unittest
from typing import Any

from semiroh import (
    ActivationRejected,
    AllOf,
    CellDeclaration,
    CellContentRejected,
    ConstraintResult,
    EntityID,
    EvaluationContext,
    Evaluator,
    External,
    IntRange,
    IsKind,
    Relation,
    RelationConstraintRejected,
    Role,
    Runtime,
    State,
    Value,
    canonicalize,
    constraint_relations,
    transform_with_mapping,
)

LOW = EntityID("low")
HIGH = EntityID("high")
LIMIT = EntityID("limit")
ORDER = EntityID("order")

SAT = ConstraintResult.SATISFIED
VIO = ConstraintResult.VIOLATED
UNK = ConstraintResult.UNKNOWN


def ordered(subject: Any) -> ConstraintResult:
    """Evaluator comparing two roles of a canonical role map."""

    roles = dict(subject[2])
    return SAT if roles["low"] <= roles["high"] else VIO


CONTEXT = EvaluationContext({"ordered": Evaluator(ordered)})

LOW_NOT_ABOVE_HIGH = Relation(
    "bound",
    {"low": LOW, "high": HIGH},
    payload=AllOf(
        Role("low", IsKind("int")),
        Role("high", IsKind("int")),
        External("ordered"),
    ),
)


def program(low: int = 0, high: int = 10, relation: Any = None) -> State:
    return State.create({
        LOW: Value.create(LOW, CellDeclaration(IsKind("int"), low)),
        HIGH: Value.create(HIGH, CellDeclaration(IsKind("int"), high)),
        ORDER: Value.create(ORDER, relation or LOW_NOT_ABOVE_HIGH),
    })


class ConstraintRelationRecognitionTests(unittest.TestCase):
    def test_a_constraint_payload_makes_a_constraint_relation(self) -> None:
        state = State.create({
            LOW: Value.create(LOW, 1),
            ORDER: Value.create(ORDER, Relation("anything", {"x": LOW}, IsKind("int"))),
            LIMIT: Value.create(LIMIT, Relation("constraint", {"x": LOW}, 5)),
        })

        self.assertEqual(set(constraint_relations(state)), {ORDER})


class LoadTests(unittest.TestCase):
    def test_satisfied_relation_loads(self) -> None:
        runtime = Runtime(program(), CONTEXT)

        self.assertEqual((runtime.read(LOW), runtime.read(HIGH)), (0, 10))

    def test_violated_relation_is_rejected_on_load(self) -> None:
        with self.assertRaises(RelationConstraintRejected) as raised:
            Runtime(program(low=11, high=10), CONTEXT)

        self.assertEqual(raised.exception.relation, ORDER)
        self.assertIs(raised.exception.result, VIO)

    def test_unknown_relation_is_rejected_on_load(self) -> None:
        with self.assertRaises(RelationConstraintRejected) as raised:
            Runtime(program())

        self.assertIs(raised.exception.result, UNK)

    def test_relation_over_ordinary_values_is_checked(self) -> None:
        state = State.create({
            LIMIT: Value.create(LIMIT, "not an int"),
            ORDER: Value.create(
                ORDER,
                Relation("typed", {"value": LIMIT}, Role("value", IsKind("int"))),
            ),
        })

        with self.assertRaises(RelationConstraintRejected):
            Runtime(state)


class WriteTests(unittest.TestCase):
    def test_write_breaking_the_relation_is_rejected(self) -> None:
        runtime = Runtime(program(), CONTEXT)

        with self.assertRaises(RelationConstraintRejected) as raised:
            runtime.write(LOW, 11)

        self.assertEqual(raised.exception.relation, ORDER)
        self.assertEqual(runtime.read(LOW), 0)

    def test_write_keeping_the_relation_is_accepted(self) -> None:
        runtime = Runtime(program(), CONTEXT)

        runtime.write(HIGH, 20)
        runtime.write(LOW, 15)

        self.assertEqual((runtime.read(LOW), runtime.read(HIGH)), (15, 20))

    def test_cell_constraint_is_checked_before_the_relation(self) -> None:
        runtime = Runtime(program(), CONTEXT)

        with self.assertRaises(CellContentRejected):
            runtime.write(LOW, "text")

    def test_untouched_cells_do_not_evaluate_the_relation(self) -> None:
        calls = []

        def counting(subject: Any) -> ConstraintResult:
            calls.append(subject)
            return ordered(subject)

        state = State.create({
            LOW: Value.create(LOW, CellDeclaration(IsKind("int"), 0)),
            HIGH: Value.create(HIGH, CellDeclaration(IsKind("int"), 10)),
            LIMIT: Value.create(LIMIT, CellDeclaration(IsKind("int"), 0)),
            ORDER: Value.create(ORDER, LOW_NOT_ABOVE_HIGH),
        })
        runtime = Runtime(
            state,
            EvaluationContext({"ordered": Evaluator(counting)}),
        )
        calls.clear()

        runtime.write(LIMIT, 99)

        self.assertEqual(calls, [])


class ActivationTests(unittest.TestCase):
    def test_activation_checks_relations_against_staged_content(self) -> None:
        source = program()
        runtime = Runtime(source, CONTEXT)
        runtime.write(LOW, 5)
        narrowed = Relation(
            "bound",
            {"low": LOW, "high": HIGH},
            payload=AllOf(External("ordered"), Role("low", IntRange(0, 3))),
        )
        result = transform_with_mapping(
            source,
            {ORDER: narrowed},
            {LOW: LOW, HIGH: HIGH},
        )
        before = (runtime.active, dict(runtime.active.cells))

        with self.assertRaises(ActivationRejected) as raised:
            runtime.activate(result)

        self.assertEqual(raised.exception.relation, ORDER)
        self.assertEqual((runtime.active, dict(runtime.active.cells)), before)

        with self.assertRaises(ActivationRejected):
            runtime.trial(result)

    def test_relation_following_a_rename_keeps_holding(self) -> None:
        source = program()
        runtime = Runtime(source, CONTEXT)
        renamed = EntityID("upper")

        runtime.activate(
            transform_with_mapping(
                source,
                {renamed: CellDeclaration(IsKind("int"), 0)},
                {LOW: LOW, HIGH: renamed},
            )
        )

        self.assertEqual(runtime.read(renamed), 10)

        with self.assertRaises(RelationConstraintRejected):
            runtime.write(LOW, 11)


class ConstraintRelationProperties(unittest.TestCase):
    def test_random_writes_never_break_the_relation(self) -> None:
        # A write is accepted exactly when both the cell constraint and the
        # relation hold afterwards; the relation holds after every step.
        for seed in range(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                runtime = Runtime(program(), CONTEXT)

                for _ in range(30):
                    cell = rng.choice([LOW, HIGH])
                    content = rng.choice([rng.randrange(-5, 25), "x", True])
                    low, high = runtime.read(LOW), runtime.read(HIGH)
                    after = {LOW: low, HIGH: high, cell: content}
                    valid = (
                        IsKind("int").evaluate(content) is SAT
                        and after[LOW] <= after[HIGH]
                    )

                    if valid:
                        runtime.write(cell, content)
                    else:
                        with self.assertRaises(
                            (CellContentRejected, RelationConstraintRejected)
                        ):
                            runtime.write(cell, content)

                    self.assertLessEqual(runtime.read(LOW), runtime.read(HIGH))
                    self.assertEqual(
                        runtime.read(cell),
                        canonicalize(content) if valid else (low if cell == LOW else high),
                    )


if __name__ == "__main__":
    unittest.main()
