"""Control-tagged canary programs (docs/corpus.md section 3)."""

from __future__ import annotations

from .. import EntityID
from ..lang import Function
from . import Example, Step
from ._support import program


def _abs_value() -> Example:
    entry = EntityID("abs_value")
    entities = {
        entry: Function(
            ("x",),
            (
                "if",
                ("lt", ("arg", "x"), ("lit", 0)),
                ("sub", ("lit", 0), ("arg", "x")),
                ("arg", "x"),
            ),
        ),
    }

    return Example(
        name="abs_value",
        tags=frozenset({"control"}),
        program=program(entities),
        scenarios=(
            (
                Step(entry, (5,), 5),
                Step(entry, (-5,), 5),
                Step(entry, (0,), 0),
            ),
        ),
        description="Absolute value by a single comparison against 0.",
    )


def _max_of_two() -> Example:
    entry = EntityID("max_of_two")
    entities = {
        entry: Function(
            ("a", "b"),
            (
                "if",
                ("lt", ("arg", "a"), ("arg", "b")),
                ("arg", "b"),
                ("arg", "a"),
            ),
        ),
    }

    return Example(
        name="max_of_two",
        tags=frozenset({"control"}),
        program=program(entities),
        scenarios=(
            (
                Step(entry, (3, 5), 5),
                Step(entry, (5, 3), 5),
                Step(entry, (-2, -7), -2),
            ),
        ),
        description="The larger of two ints.",
    )


def _clamp() -> Example:
    entry = EntityID("clamp")
    entities = {
        entry: Function(
            ("x", "lo", "hi"),
            (
                "if",
                ("lt", ("arg", "x"), ("arg", "lo")),
                ("arg", "lo"),
                (
                    "if",
                    ("lt", ("arg", "hi"), ("arg", "x")),
                    ("arg", "hi"),
                    ("arg", "x"),
                ),
            ),
        ),
    }

    return Example(
        name="clamp",
        tags=frozenset({"control"}),
        program=program(entities),
        scenarios=(
            (
                Step(entry, (5, 0, 10), 5),
                Step(entry, (-5, 0, 10), 0),
                Step(entry, (15, 0, 10), 10),
            ),
        ),
        description="Restrict x to [lo, hi] with two comparisons.",
    )


EXAMPLES: tuple[Example, ...] = (
    _abs_value(),
    _max_of_two(),
    _clamp(),
)
