"""Generated differential tests for host and embedded closure execution."""

from __future__ import annotations

import random
import unittest

from semiroh import EntityID, Runtime, canonical_serialize, canonicalize
from semiroh.examples import self_hosting, vm
from semiroh.examples._support import program
from semiroh.lang import (
    Function,
    LanguageError,
    define,
    function_at,
    links,
    load,
    run,
)


TARGET = EntityID("closure_diff_target")
HELPER = EntityID("closure_diff_helper")
CASES = 60

_BASE = None


def same(actual, expected) -> bool:
    return canonical_serialize(canonicalize(actual)) == canonical_serialize(
        canonicalize(expected)
    )


def base_state():
    global _BASE

    if _BASE is None:
        _BASE = load(
            program(
                {
                    **self_hosting.compiler_entities(),
                    **vm.vm_entities(),
                    TARGET: Function(("x",), ("lit", 0)),
                    EntityID("closure_diff_target.links"): links(
                        TARGET,
                        helper=HELPER,
                    ),
                    HELPER: Function(
                        ("a",),
                        ("add", ("arg", "a"), ("lit", 1)),
                    ),
                    EntityID("closure_diff_helper.links"): links(HELPER),
                }
            )
        )

    return _BASE


def runtime(body: tuple) -> Runtime:
    state = define(
        base_state(),
        {
            TARGET: Function(("x",), body),
        },
    ).destination

    return Runtime(state)


def link_table() -> tuple:
    return (("helper", HELPER),)


def outcome(call):
    try:
        return ("value", call())
    except LanguageError:
        return ("raised", "LanguageError")


def host(body: tuple, argument):
    rt = runtime(body)
    return outcome(lambda: run(rt, TARGET, argument))


def embedded(body: tuple, argument):
    rt = runtime(body)
    state = rt.active.state

    chunk = run(
        rt,
        self_hosting.LOWER,
        function_at(state, TARGET).body,
    )

    return outcome(
        lambda: run(
            rt,
            vm.VM,
            chunk,
            ("x",),
            (argument,),
            link_table(),
        )
    )


class Generator:
    """Generate closure-heavy expressions in the host/VM common subset."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.names = 0

    def number(
        self,
        depth: int,
        scope: tuple[str, ...] = ("x",),
    ) -> tuple:
        if depth <= 0:
            name = self.rng.choice(scope)

            return self.rng.choice(
                [
                    ("arg", name),
                    ("lit", self.rng.randint(-4, 6)),
                ]
            )

        kind = self.rng.choice(
            [
                "add",
                "sub",
                "mul",
                "let",
                "direct",
                "applyv",
                "nested",
                "capture-closure",
            ]
        )

        if kind in ("add", "sub", "mul"):
            return (
                kind,
                self.number(depth - 1, scope),
                self.number(depth - 1, scope),
            )

        if kind == "let":
            self.names += 1
            name = f"n{self.names}"

            value = self.number(depth - 1, scope)
            body = self.number(depth - 1, scope + (name,))

            return ("let", name, value, body)

        if kind == "direct":
            self.names += 1
            captured = f"c{self.names}"

            value = self.number(depth - 1, scope)
            argument = self.number(depth - 1, scope)

            return (
                "let",
                captured,
                value,
                (
                    "apply",
                    (
                        "closure",
                        ("y",),
                        (captured,),
                        (
                            "add",
                            ("arg", captured),
                            ("arg", "y"),
                        ),
                    ),
                    argument,
                ),
            )

        if kind == "applyv":
            self.names += 1
            captured = f"v{self.names}"

            value = self.number(depth - 1, scope)
            argument = self.number(depth - 1, scope)

            return (
                "let",
                captured,
                value,
                (
                    "applyv",
                    (
                        "closure",
                        ("y",),
                        (captured,),
                        (
                            "sub",
                            ("arg", captured),
                            ("arg", "y"),
                        ),
                    ),
                    ("tuple", argument),
                ),
            )

        if kind == "nested":
            self.names += 1
            captured = f"k{self.names}"

            value = self.number(depth - 1, scope)
            argument = self.number(depth - 1, scope)

            return (
                "let",
                captured,
                value,
                (
                    "apply",
                    (
                        "apply",
                        (
                            "closure",
                            ("a",),
                            (captured,),
                            (
                                "closure",
                                ("b",),
                                ("a", captured),
                                (
                                    "add",
                                    ("arg", captured),
                                    (
                                        "add",
                                        ("arg", "a"),
                                        ("arg", "b"),
                                    ),
                                ),
                            ),
                        ),
                        argument,
                    ),
                    self.number(depth - 1, scope),
                ),
            )

        self.names += 1
        closure_name = f"f{self.names}"
        argument = self.number(depth - 1, scope)

        return (
            "let",
            closure_name,
            (
                "closure",
                ("z",),
                (),
                ("add", ("arg", "z"), ("lit", 1)),
            ),
            (
                "apply",
                (
                    "closure",
                    ("y",),
                    (closure_name,),
                    (
                        "apply",
                        ("arg", closure_name),
                        ("arg", "y"),
                    ),
                ),
                argument,
            ),
        )


class ClosureDifferentialTests(unittest.TestCase):
    def test_generated_closure_programs_agree(self) -> None:
        computed = 0

        for seed in range(CASES):
            body = Generator(seed).number(4)

            for argument in (-2, 3):
                with self.subTest(
                    seed=seed,
                    argument=argument,
                    body=body,
                ):
                    expected = host(body, argument)
                    actual = embedded(body, argument)

                    self.assertEqual(
                        expected[0],
                        "value",
                        (
                            f"valid generator produced a failure\n"
                            f"seed={seed} argument={argument}\n"
                            f"body={body!r}\n"
                            f"host={expected!r}"
                        ),
                    )

                    self.assertEqual(actual[0], expected[0])

                    self.assertTrue(
                        same(actual[1], expected[1]),
                        (
                            f"seed={seed} argument={argument}\n"
                            f"body={body!r}\n"
                            f"host={expected!r}\n"
                            f"embedded={actual!r}"
                        ),
                    )

                    computed += 1

        self.assertEqual(computed, CASES * 2)


if __name__ == "__main__":
    unittest.main()
