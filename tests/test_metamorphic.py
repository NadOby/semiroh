"""Metamorphic verification of semantics-preserving operation changes."""

from __future__ import annotations

import random
import unittest

from semiroh import EntityID, Runtime, State, Value, transform
from semiroh.lang import Function, define, function_at, load, run
from semiroh.reconcile import reconcile
from semiroh.syntax import parse, render_program
from semiroh.transforms import rebase
from tests.generation import seeds


A = EntityID("a")
B = EntityID("b")
C = EntityID("c")

F = EntityID("f")
G = EntityID("g")
H = EntityID("h")

CASES = 200
LANGUAGE_CASES = 60


def state(a: int, b: int, c: int) -> State:
    return State.create(
        {
            A: Value.create(A, a),
            B: Value.create(B, b),
            C: Value.create(C, c),
        }
    )


def language_state(seed: int) -> State:
    rng = random.Random(seed)
    add = rng.randint(0, 9)
    multiply = rng.randint(1, 9)
    finish = rng.randint(0, 9)

    source = (
        "fn f(x):\n"
        f"    x + {add}\n"
        "\n"
        "fn g(x):\n"
        f"    f(x) * {multiply}\n"
        "\n"
        "fn h(x):\n"
        "    let y = g(x)\n"
        f"    y + {finish}\n"
    )

    return load(parse(source))


def assert_same_language_program(
    case: unittest.TestCase,
    left: State,
    right: State,
) -> None:
    """Compare source projection and observable execution, not graph history."""

    case.assertEqual(
        render_program(left),
        render_program(right),
    )

    for entity in (F, G, H):
        case.assertEqual(
            function_at(left, entity),
            function_at(right, entity),
        )

    for argument in (-3, 0, 5):
        case.assertEqual(
            run(Runtime(left), H, argument),
            run(Runtime(right), H, argument),
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


class LanguageMetamorphicTests(unittest.TestCase):
    def test_rendered_program_reconciles_to_a_noop(self) -> None:
        for seed in seeds(LANGUAGE_CASES):
            source = language_state(seed)
            rendered = render_program(source)

            destination = reconcile(
                source,
                rendered,
            ).destination

            with self.subTest(seed=seed):
                self.assertEqual(
                    destination.id,
                    source.id,
                )

    def test_defining_a_function_from_its_projection_is_a_noop(
        self,
    ) -> None:
        for seed in seeds(LANGUAGE_CASES):
            source = language_state(seed)

            for entity in (F, G, H):
                projected = function_at(
                    source,
                    entity,
                )
                destination = define(
                    source,
                    {entity: projected},
                ).destination

                with self.subTest(
                    seed=seed,
                    function=entity.value,
                ):
                    self.assertEqual(
                        destination.id,
                        source.id,
                    )

    def test_rebased_independent_defines_match_one_combined_define(
        self,
    ) -> None:
        for seed in seeds(LANGUAGE_CASES):
            rng = random.Random(seed)
            source = language_state(seed)

            new_f = Function(
                ("x",),
                (
                    "add",
                    ("arg", "x"),
                    ("lit", rng.randint(10, 19)),
                ),
            )
            new_g = Function(
                ("x",),
                (
                    "mul",
                    (
                        "call",
                        "f",
                        ("arg", "x"),
                    ),
                    ("lit", rng.randint(2, 9)),
                ),
            )

            left = define(
                source,
                {F: new_f},
            )
            right = define(
                source,
                {G: new_g},
            )
            combined = define(
                source,
                {
                    F: new_f,
                    G: new_g,
                },
            )

            right_after_left = rebase(
                right,
                left,
            )
            left_after_right = rebase(
                left,
                right,
            )

            with self.subTest(seed=seed):
                assert_same_language_program(
                    self,
                    right_after_left.destination,
                    combined.destination,
                )
                assert_same_language_program(
                    self,
                    left_after_right.destination,
                    combined.destination,
                )


if __name__ == "__main__":
    unittest.main()
