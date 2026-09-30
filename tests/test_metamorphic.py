"""Metamorphic verification of semantics-preserving operation changes."""

from __future__ import annotations

import random
import unittest

from semiroh import EntityID, State, Value, transform
from tests.generation import seeds


A = EntityID("a")
B = EntityID("b")
C = EntityID("c")
CASES = 200


def state(a: int, b: int, c: int) -> State:
    return State.create(
        {
            A: Value.create(A, a),
            B: Value.create(B, b),
            C: Value.create(C, c),
        }
    )


class TransformationMetamorphicTests(unittest.TestCase):
    def test_independent_changes_commute(self) -> None:
        for seed in seeds(CASES):
            rng = random.Random(seed)
            source = state(
                rng.randint(-10, 10),
                rng.randint(-10, 10),
                rng.randint(-10, 10),
            )
            new_a = rng.randint(-10, 10)
            new_b = rng.randint(-10, 10)

            left_then_right = transform(
                transform(source, {A: new_a}),
                {B: new_b},
            )
            right_then_left = transform(
                transform(source, {B: new_b}),
                {A: new_a},
            )

            with self.subTest(seed=seed):
                self.assertEqual(
                    left_then_right.id,
                    right_then_left.id,
                )

    def test_batched_and_sequential_independent_changes_agree(
        self,
    ) -> None:
        for seed in seeds(CASES):
            rng = random.Random(seed)
            source = state(
                rng.randint(-10, 10),
                rng.randint(-10, 10),
                rng.randint(-10, 10),
            )
            new_a = rng.randint(-10, 10)
            new_b = rng.randint(-10, 10)

            sequential = transform(
                transform(source, {A: new_a}),
                {B: new_b},
            )
            batched = transform(
                source,
                {
                    A: new_a,
                    B: new_b,
                },
            )

            with self.subTest(seed=seed):
                self.assertEqual(sequential.id, batched.id)

    def test_repeating_the_same_change_is_idempotent(self) -> None:
        for seed in seeds(CASES):
            rng = random.Random(seed)
            source = state(
                rng.randint(-10, 10),
                rng.randint(-10, 10),
                rng.randint(-10, 10),
            )
            replacement = rng.randint(-10, 10)

            once = transform(source, {A: replacement})
            twice = transform(once, {A: replacement})

            with self.subTest(seed=seed):
                self.assertEqual(once.id, twice.id)


if __name__ == "__main__":
    unittest.main()
