"""Recursion-tagged canary programs (docs/corpus.md section 3).

The language has no modulo or division operator (only ``add``, ``sub`` and
``mul``), so ``gcd`` uses subtraction-based Euclid, and the Collatz example
builds its own even/odd test and halving out of recursive subtraction by 2.
"""

from __future__ import annotations

from .. import EntityID
from ..lang import Function, links
from . import Example, Step
from ._support import program


def _factorial() -> Example:
    entry = EntityID("factorial")
    entities = {
        entry: Function(
            ("n",),
            (
                "if",
                ("eq", ("arg", "n"), ("lit", 0)),
                ("lit", 1),
                (
                    "mul",
                    ("arg", "n"),
                    ("call", "factorial", ("sub", ("arg", "n"), ("lit", 1))),
                ),
            ),
        ),
        EntityID("factorial.links"): links(entry, factorial=entry),
    }

    return Example(
        name="factorial",
        tags=frozenset({"recursion"}),
        program=program(entities),
        scenarios=(
            (
                Step(entry, (0,), 1),
                Step(entry, (1,), 1),
                Step(entry, (5,), 120),
                Step(entry, (7,), 5040),
            ),
        ),
        description="n! by straightforward recursion on n.",
    )


def _fibonacci() -> Example:
    entry = EntityID("fibonacci")
    entities = {
        entry: Function(
            ("n",),
            (
                "if",
                ("lt", ("arg", "n"), ("lit", 2)),
                ("arg", "n"),
                (
                    "add",
                    ("call", "fibonacci", ("sub", ("arg", "n"), ("lit", 1))),
                    ("call", "fibonacci", ("sub", ("arg", "n"), ("lit", 2))),
                ),
            ),
        ),
        EntityID("fibonacci.links"): links(entry, fibonacci=entry),
    }

    return Example(
        name="fibonacci",
        tags=frozenset({"recursion"}),
        program=program(entities),
        scenarios=(
            (
                Step(entry, (0,), 0),
                Step(entry, (1,), 1),
                Step(entry, (10,), 55),
            ),
        ),
        description="Naive doubly-recursive Fibonacci.",
    )


def _sum_to_n() -> Example:
    entry = EntityID("sum_to_n")
    entities = {
        entry: Function(
            ("n",),
            (
                "if",
                ("eq", ("arg", "n"), ("lit", 0)),
                ("lit", 0),
                (
                    "add",
                    ("arg", "n"),
                    ("call", "sum_to_n", ("sub", ("arg", "n"), ("lit", 1))),
                ),
            ),
        ),
        EntityID("sum_to_n.links"): links(entry, sum_to_n=entry),
    }

    return Example(
        name="sum_to_n",
        tags=frozenset({"recursion"}),
        program=program(entities),
        scenarios=(
            (
                Step(entry, (0,), 0),
                Step(entry, (10,), 55),
                Step(entry, (100,), 5050),
            ),
        ),
        description="1 + 2 + ... + n by recursion.",
    )


def _gcd() -> Example:
    entry = EntityID("gcd")
    entities = {
        entry: Function(
            ("a", "b"),
            (
                "if",
                ("eq", ("arg", "a"), ("lit", 0)),
                ("arg", "b"),
                (
                    "if",
                    ("eq", ("arg", "b"), ("lit", 0)),
                    ("arg", "a"),
                    (
                        "if",
                        ("lt", ("arg", "a"), ("arg", "b")),
                        (
                            "call",
                            "gcd",
                            ("arg", "a"),
                            ("sub", ("arg", "b"), ("arg", "a")),
                        ),
                        (
                            "call",
                            "gcd",
                            ("sub", ("arg", "a"), ("arg", "b")),
                            ("arg", "b"),
                        ),
                    ),
                ),
            ),
        ),
        EntityID("gcd.links"): links(entry, gcd=entry),
    }

    return Example(
        name="gcd",
        tags=frozenset({"recursion"}),
        program=program(entities),
        scenarios=(
            (
                Step(entry, (48, 18), 6),
                Step(entry, (0, 5), 5),
                Step(entry, (7, 0), 7),
            ),
        ),
        description=(
            "Euclid's algorithm by repeated subtraction, since the "
            "language has no modulo operator."
        ),
    )


def _collatz_step_count() -> Example:
    is_even = EntityID("collatz_is_even")
    half = EntityID("collatz_half")
    step_count = EntityID("collatz_step_count_from")
    entry = EntityID("collatz_step_count")
    entities = {
        is_even: Function(
            ("n",),
            (
                "if",
                ("eq", ("arg", "n"), ("lit", 0)),
                ("lit", True),
                (
                    "if",
                    ("eq", ("arg", "n"), ("lit", 1)),
                    ("lit", False),
                    ("call", "is_even", ("sub", ("arg", "n"), ("lit", 2))),
                ),
            ),
        ),
        EntityID("collatz_is_even.links"): links(is_even, is_even=is_even),
        half: Function(
            ("n",),
            (
                "if",
                ("eq", ("arg", "n"), ("lit", 0)),
                ("lit", 0),
                (
                    "add",
                    ("lit", 1),
                    ("call", "half", ("sub", ("arg", "n"), ("lit", 2))),
                ),
            ),
        ),
        EntityID("collatz_half.links"): links(half, half=half),
        step_count: Function(
            ("n", "acc"),
            (
                "if",
                ("eq", ("arg", "n"), ("lit", 1)),
                ("arg", "acc"),
                (
                    "if",
                    ("call", "is_even", ("arg", "n")),
                    (
                        "call",
                        "step_count",
                        ("call", "half", ("arg", "n")),
                        ("add", ("arg", "acc"), ("lit", 1)),
                    ),
                    (
                        "call",
                        "step_count",
                        ("add", ("mul", ("lit", 3), ("arg", "n")), ("lit", 1)),
                        ("add", ("arg", "acc"), ("lit", 1)),
                    ),
                ),
            ),
        ),
        EntityID("collatz_step_count_from.links"): links(
            step_count,
            is_even=is_even,
            half=half,
            step_count=step_count,
        ),
        entry: Function(("n",), ("call", "step_count", ("arg", "n"), ("lit", 0))),
        EntityID("collatz_step_count.links"): links(entry, step_count=step_count),
    }

    return Example(
        name="collatz_step_count",
        tags=frozenset({"recursion"}),
        program=program(entities),
        scenarios=(
            (
                Step(entry, (1,), 0),
                Step(entry, (6,), 8),
                Step(entry, (12,), 9),
            ),
        ),
        description=(
            "Steps to reach 1 under the Collatz map. Even/odd and halving "
            "are themselves recursive since there is no modulo or division "
            "operator."
        ),
    )


EXAMPLES: tuple[Example, ...] = (
    _factorial(),
    _fibonacci(),
    _sum_to_n(),
    _gcd(),
    _collatz_step_count(),
)
