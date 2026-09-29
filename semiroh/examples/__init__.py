"""The canary corpus: example programs with expected results (docs/corpus.md).

Every interpreter, and every representation of code, must run the whole
corpus unchanged; a broken interpreter must fail it
(``tests/test_corpus.py``). This module defines the data format (``Raises``,
``Step``, ``Example``, ``Wanted``) and ``play``, then aggregates the tier-1
programs from the per-tag submodules and the wanted programs from
``missing.py``.

Programs are data: they are built with ``semiroh.lang`` (``Function``,
``links``) and core constructors. Host code appears only as evaluators in an
example's ``context``, never inside a program body.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .. import (
    EntityID,
    EvaluationContext,
    Runtime,
    State,
    canonical_serialize,
    canonicalize,
)
from ..lang import load

TAGS = frozenset({
    "recursion",
    "side effects",
    "control",
    "self-modification",
    "data",
    "higher order",
})


@dataclass(frozen=True)
class Raises:
    """Expected outcome of a step that must raise ``error``.

    A subclass of ``error`` counts.
    """

    error: type[BaseException]


@dataclass(frozen=True)
class Step:
    """One run of a scenario.

    ``run(runtime, entry, *args, may_activate=...)`` must return a value
    semantically equal to ``expect`` (compared by canonical serialization,
    so ``True != 1``), or raise as ``Raises`` says; afterwards each cell in
    ``cells`` must hold that content.
    """

    entry: EntityID
    args: tuple[Any, ...]
    expect: Any
    may_activate: bool = False
    cells: Mapping[EntityID, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "args", tuple(self.args))
        object.__setattr__(self, "cells", dict(self.cells))


@dataclass(frozen=True)
class Example:
    """A named program with tags, its state, and the scenarios that run it.

    ``program`` is a ``State`` in the input format (tuple ``Function``
    bodies and ``links`` relations). Each scenario is a tuple of ``Step``\\ s
    run in order against one fresh ``Runtime(load(program), context)``.
    """

    name: str
    tags: frozenset[str]
    program: State
    scenarios: tuple[tuple[Step, ...], ...]
    context: EvaluationContext | None = None
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(
            self,
            "scenarios",
            tuple(tuple(scenario) for scenario in self.scenarios),
        )


@dataclass(frozen=True)
class Wanted:
    """A program the language cannot express yet, and the feature it needs."""

    name: str
    needs: str


class ExampleFailed(AssertionError):
    """The corpus, or the interpreter running it, disagreed with a step."""


def _semantically_equal(left: Any, right: Any) -> bool:
    return canonical_serialize(canonicalize(left)) == canonical_serialize(
        canonicalize(right)
    )


def play(example: Example, run: Callable[..., Any]) -> None:
    """Run every scenario of ``example`` with ``run``.

    The program is loaded into graph form (``semiroh.lang.load``) once, and
    each scenario starts a fresh runtime from it.

    Raises ``ExampleFailed``, naming the example, scenario and step, at the
    first mismatch. A step expecting a value that raises instead is a
    mismatch too, and so is a step expecting a raise that returns normally.
    """

    program = load(example.program)

    for scenario_index, scenario in enumerate(example.scenarios):
        runtime = Runtime(program, example.context)

        for step_index, step in enumerate(scenario):
            label = (
                f"{example.name}: scenario {scenario_index}, "
                f"step {step_index} ({step.entry.value})"
            )

            try:
                actual = run(
                    runtime,
                    step.entry,
                    *step.args,
                    may_activate=step.may_activate,
                )
            except Exception as exc:
                if not isinstance(step.expect, Raises):
                    raise ExampleFailed(
                        f"{label}: expected {step.expect!r}, raised "
                        f"{type(exc).__name__}: {exc}"
                    ) from exc

                if not isinstance(exc, step.expect.error):
                    raise ExampleFailed(
                        f"{label}: expected to raise "
                        f"{step.expect.error.__name__}, raised "
                        f"{type(exc).__name__}: {exc}"
                    ) from exc
            else:
                if isinstance(step.expect, Raises):
                    raise ExampleFailed(
                        f"{label}: expected to raise "
                        f"{step.expect.error.__name__}, returned {actual!r}"
                    )

                if not _semantically_equal(actual, step.expect):
                    raise ExampleFailed(
                        f"{label}: expected {step.expect!r}, got {actual!r}"
                    )

            for cell, expected_content in step.cells.items():
                actual_content = runtime.read(cell)

                if not _semantically_equal(actual_content, expected_content):
                    raise ExampleFailed(
                        f"{label}: cell {cell.value} expected "
                        f"{expected_content!r}, got {actual_content!r}"
                    )


# Submodules build on the data format above, so they are imported only now
# that it is fully defined; each does `from . import Example, Step, ...`.
from . import (  # noqa: E402
    control,
    data,
    higher_order,
    missing,
    recursion,
    self_hosting,
    self_modification,
    side_effects,
    vm,
)

EXAMPLES: tuple[Example, ...] = (
    recursion.EXAMPLES
    + control.EXAMPLES
    + side_effects.EXAMPLES
    + self_modification.EXAMPLES
    + data.EXAMPLES
    + higher_order.EXAMPLES
    + self_hosting.EXAMPLES
    + vm.EXAMPLES
)

MISSING: tuple[Wanted, ...] = missing.MISSING

__all__ = [
    "TAGS",
    "Raises",
    "Step",
    "Example",
    "Wanted",
    "ExampleFailed",
    "play",
    "EXAMPLES",
    "MISSING",
]
