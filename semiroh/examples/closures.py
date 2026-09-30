"""Lexical-closure canary programs (docs/closures.md, roadmap task 17)."""

from __future__ import annotations

from .. import EntityID
from ..lang import Function, links
from . import Example, Step
from ._support import program


def _make_adder() -> Example:
    make_adder = EntityID("make_adder")
    apply_adder = EntityID("apply_adder")

    entities = {
        make_adder: Function(
            ("n",),
            (
                "closure",
                ("x",),
                ("n",),
                (
                    "add",
                    ("arg", "n"),
                    ("arg", "x"),
                ),
            ),
        ),
        apply_adder: Function(
            ("n", "x"),
            (
                "apply",
                (
                    "call",
                    "make_adder",
                    ("arg", "n"),
                ),
                ("arg", "x"),
            ),
        ),
        EntityID("apply_adder.links"): links(
            apply_adder,
            make_adder=make_adder,
        ),
    }

    return Example(
        name="make_adder",
        tags=frozenset({
            "data",
            "higher order",
        }),
        program=program(entities),
        scenarios=(
            (
                Step(
                    apply_adder,
                    (4, 3),
                    7,
                ),
                Step(
                    apply_adder,
                    (-5, 12),
                    7,
                ),
            ),
        ),
        description=(
            "make_adder(n) returns an anonymous function that captures n "
            "by value and adds it to its argument after the creating call "
            "has returned."
        ),
    )


def _compose() -> Example:
    make_adder = EntityID("make_adder")
    compose = EntityID("compose")
    double = EntityID("double")
    run_compose = EntityID("run_compose")
    run_two_closures = EntityID("run_two_closures")

    entities = {
        make_adder: Function(
            ("n",),
            (
                "closure",
                ("x",),
                ("n",),
                (
                    "add",
                    ("arg", "n"),
                    ("arg", "x"),
                ),
            ),
        ),
        compose: Function(
            ("f", "g"),
            (
                "closure",
                ("x",),
                ("f", "g"),
                (
                    "apply",
                    ("arg", "f"),
                    (
                        "apply",
                        ("arg", "g"),
                        ("arg", "x"),
                    ),
                ),
            ),
        ),
        double: Function(
            ("x",),
            (
                "add",
                ("arg", "x"),
                ("arg", "x"),
            ),
        ),
        run_compose: Function(
            ("n", "x"),
            (
                "let",
                "add_n",
                (
                    "call",
                    "make_adder",
                    ("arg", "n"),
                ),
                (
                    "let",
                    "combined",
                    (
                        "call",
                        "compose",
                        ("arg", "add_n"),
                        ("ref", "double"),
                    ),
                    (
                        "apply",
                        ("arg", "combined"),
                        ("arg", "x"),
                    ),
                ),
            ),
        ),
        EntityID("run_compose.links"): links(
            run_compose,
            make_adder=make_adder,
            compose=compose,
            double=double,
        ),
        run_two_closures: Function(
            ("a", "b", "x"),
            (
                "let",
                "add_a",
                (
                    "call",
                    "make_adder",
                    ("arg", "a"),
                ),
                (
                    "let",
                    "add_b",
                    (
                        "call",
                        "make_adder",
                        ("arg", "b"),
                    ),
                    (
                        "let",
                        "combined",
                        (
                            "call",
                            "compose",
                            ("arg", "add_a"),
                            ("arg", "add_b"),
                        ),
                        (
                            "apply",
                            ("arg", "combined"),
                            ("arg", "x"),
                        ),
                    ),
                ),
            ),
        ),
        EntityID("run_two_closures.links"): links(
            run_two_closures,
            make_adder=make_adder,
            compose=compose,
        ),
    }

    return Example(
        name="compose",
        tags=frozenset({
            "data",
            "higher order",
        }),
        program=program(entities),
        scenarios=(
            (
                Step(
                    run_compose,
                    (2, 3),
                    8,
                ),
                Step(
                    run_two_closures,
                    (2, 3, 1),
                    6,
                ),
            ),
        ),
        description=(
            "compose(f, g) returns a closure capturing both callable "
            "values. One scenario captures a function reference and a "
            "closure; the other captures two closures."
        ),
    )


EXAMPLES: tuple[Example, ...] = (
    _make_adder(),
    _compose(),
  )
