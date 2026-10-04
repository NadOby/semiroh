"""Deterministic generated malformed-language cases."""

from __future__ import annotations

import random
import unittest

from shear import EntityID, Runtime
from shear.examples._support import program
from shear.lang import (
    Function,
    LanguageError,
    function_at,
    links,
    load,
    run,
)
from tests.generation import reproduction, seeds


F = EntityID("malformed")
CASES = 120

KINDS = (
    "unknown-operation",
    "wrong-arity",
    "bad-let-name",
    "bad-arithmetic",
    "bad-condition",
    "bad-tuple-operation",
    "non-callable",
    "bad-closure-container",
    "bad-closure-name",
    "duplicate-closure-name",
    "overlapping-closure-name",
    "missing-capture",
)


class Generator:
    """Generate invalid expressions whose rejection is specified."""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = random.Random(seed)

    def expression(self) -> tuple[str, tuple]:
        kind = KINDS[self.seed % len(KINDS)]
        rng = self.rng
        one = ("lit", 1)

        if kind == "unknown-operation":
            return kind, (f"unknown_{self.seed}", one)

        if kind == "wrong-arity":
            choices = (
                ("add", one),
                ("sub", one),
                ("mul", one),
                ("if", ("lit", True), one),
                ("len", ("tuple",), one),
                ("item", ("tuple", one)),
                ("slice", ("tuple", one), one),
                ("concat", ("tuple",)),
            )
            return kind, rng.choice(choices)

        if kind == "bad-let-name":
            name = rng.choice(("", 0, None, ()))
            return kind, ("let", name, one, one)

        if kind == "bad-arithmetic":
            bad = rng.choice(("s", True, None, (1,)))
            op = rng.choice(("add", "sub", "mul", "lt"))
            return kind, (op, ("lit", bad), one)

        if kind == "bad-condition":
            condition = rng.choice((0, 1, "yes", None, ()))
            return kind, ("if", ("lit", condition), one, one)

        if kind == "bad-tuple-operation":
            choices = (
                ("len", one),
                ("item", ("tuple", one), ("lit", "0")),
                ("item", ("tuple",), ("lit", 0)),
                ("slice", one, ("lit", 0), ("lit", 1)),
                ("concat", one, ("tuple",)),
            )
            return kind, rng.choice(choices)

        if kind == "non-callable":
            return kind, (
                "apply",
                ("lit", rng.choice((0, "f", None, ()))),
                one,
            )

        if kind == "bad-closure-container":
            if rng.choice((True, False)):
                params = rng.choice((1, None, ["x"]))
                captures = ()
            else:
                params = ()
                captures = rng.choice((1, None, ["x"]))

            return kind, (
                "closure",
                params,
                captures,
                one,
            )

        if kind == "bad-closure-name":
            bad = rng.choice(("", 1, None))
            return kind, (
                "closure",
                (bad,),
                (),
                one,
            )

        if kind == "duplicate-closure-name":
            name = f"x{rng.randrange(4)}"
            return kind, (
                "closure",
                (name, name),
                (),
                one,
            )

        if kind == "overlapping-closure-name":
            return kind, (
                "closure",
                ("x",),
                ("x",),
                one,
            )

        if kind == "missing-capture":
            return kind, (
                "closure",
                (),
                ("missing",),
                one,
            )

        raise AssertionError(kind)


class MalformedGenerationTests(unittest.TestCase):
    def state(self, expression: tuple):
        return load(
            program(
                {
                    F: Function(("x",), expression),
                    EntityID("malformed.links"): links(F, f=F),
                }
            )
        )

    def test_invalid_label_names_are_rejected_at_load(self) -> None:
        for name in ("", 1):
            with self.subTest(name=name):
                with self.assertRaises(LanguageError):
                    self.state(
                        ("label", name, ("lit", 1))
                    )

    def test_generated_malformed_bodies_round_trip_and_reject(self) -> None:
        selected = seeds(CASES)
        seen = set()

        for seed in selected:
            kind, expression = Generator(seed).expression()
            seen.add(kind)
            replay = reproduction(__name__, seed)

            with self.subTest(
                seed=seed,
                kind=kind,
                expression=expression,
            ):
                state = self.state(expression)

                self.assertEqual(
                    function_at(state, F),
                    Function(("x",), expression),
                    f"reproduce: {replay}",
                )

                runtime = Runtime(state)

                with self.assertRaises(
                    LanguageError,
                    msg=(
                        f"seed={seed} kind={kind}\n"
                        f"expression={expression!r}\n"
                        f"reproduce: {replay}"
                    ),
                ):
                    run(runtime, F, 3)

        if (
            len(selected) >= len(KINDS)
            and selected == tuple(range(len(selected)))
        ):
            self.assertEqual(seen, set(KINDS))


if __name__ == "__main__":
    unittest.main()
