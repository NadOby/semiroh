"""Seeded stateful verification across runtime subsystem boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import random
import unittest

from semiroh import (
    ActivationRejected,
    CellContentRejected,
    CellDeclaration,
    ConstraintResult,
    EntityID,
    IntRange,
    Runtime,
    State,
    Value,
    cells_of,
    transform_with_mapping,
)
from tests.generation import minimize_sequence, reproduction, seeds


CELL = EntityID("cell")
VALUE = EntityID("value")
SAT = ConstraintResult.SATISFIED

CASES = 120
STEPS = 40


@dataclass(frozen=True)
class Action:
    kind: str
    value: int = 0


def program() -> State:
    return State.create(
        {
            CELL: Value.create(
                CELL,
                CellDeclaration(IntRange(-20, 20), 0),
            ),
            VALUE: Value.create(VALUE, 0),
        }
    )


def actions_for(seed: int) -> tuple[Action, ...]:
    rng = random.Random(seed)
    kinds = (
        "write",
        "bad-write",
        "enter",
        "keep",
        "release",
        "trial",
        "activate",
    )

    return tuple(
        Action(
            rng.choice(kinds),
            rng.randint(-5, 5),
        )
        for _ in range(STEPS)
    )


def snapshot(runtime: Runtime) -> tuple:
    return (
        runtime.active,
        runtime.versions,
        tuple(
            (
                version,
                dict(version.cells),
                version.holds,
                version.retired,
            )
            for version in runtime.versions
        ),
    )


def candidate(runtime: Runtime, delta: int):
    source = runtime.active.state
    current = source.values[VALUE].content

    return transform_with_mapping(
        source,
        {VALUE: current + delta},
        {
            CELL: CELL,
            VALUE: VALUE,
        },
    )


def check_invariants(runtime: Runtime, live: list) -> None:
    if not runtime.versions:
        raise AssertionError("runtime owns no active version")

    if runtime.versions[0] is not runtime.active:
        raise AssertionError("active version is not first")

    if len(runtime.versions) > 2:
        raise AssertionError(
            f"runtime owns {len(runtime.versions)} versions"
        )

    if runtime.active.retired:
        raise AssertionError("active version is retired")

    expected_previous = (
        runtime.versions[1]
        if len(runtime.versions) == 2
        else None
    )

    if runtime.previous is not expected_previous:
        raise AssertionError("previous-version view disagrees with ownership")

    recorded = set()

    for version in runtime.versions:
        if version.retired:
            raise AssertionError("loaded version is retired")

        for hold in version.holds:
            if hold.released:
                raise AssertionError("released hold remains recorded")

            if hold.version is not version:
                raise AssertionError("hold points at the wrong version")

            if hold in recorded:
                raise AssertionError("hold belongs to multiple versions")

            recorded.add(hold)

        declarations = cells_of(version.state)

        for entity, content in version.cells.items():
            declaration = declarations.get(entity)

            if declaration is None:
                raise AssertionError(
                    f"runtime content exists for non-cell {entity!r}"
                )

            result = declaration.constraint.evaluate(
                content,
                runtime.context,
            )

            if result is not SAT:
                raise AssertionError(
                    f"cell {entity!r} contains invalid runtime content"
                )

    expected_live = {
        hold
        for hold in live
        if not hold.released
    }

    if recorded != expected_live:
        raise AssertionError(
            "runtime hold records disagree with live handles"
        )


def execute(actions: tuple[Action, ...]) -> None:
    runtime = Runtime(program())
    live = []

    for index, action in enumerate(actions):
        try:
            if action.kind == "write":
                runtime.write(CELL, action.value)

            elif action.kind == "bad-write":
                before = snapshot(runtime)

                try:
                    runtime.write(CELL, "not-an-int")
                except CellContentRejected:
                    pass
                else:
                    raise AssertionError(
                        "invalid write was accepted"
                    )

                if snapshot(runtime) != before:
                    raise AssertionError(
                        "rejected write changed runtime state"
                    )

            elif action.kind == "enter":
                live.append(runtime.enter(VALUE))

            elif action.kind == "keep":
                live.append(
                    runtime.keep(
                        runtime.active.state.reference(VALUE)
                    )
                )

            elif action.kind == "release":
                if live:
                    hold = live.pop(0)

                    if not hold.released:
                        hold.release()

            elif action.kind == "trial":
                before = snapshot(runtime)
                result = candidate(runtime, action.value)
                trial = runtime.trial(result)

                if trial.active.state != result.destination:
                    raise AssertionError(
                        "trial loaded the wrong destination"
                    )

                if dict(trial.active.cells) != {
                    CELL: runtime.read(CELL),
                }:
                    raise AssertionError(
                        "trial transferred wrong cell content"
                    )

                if snapshot(runtime) != before:
                    raise AssertionError(
                        "trial changed the main runtime"
                    )

            elif action.kind == "activate":
                before = snapshot(runtime)
                result = candidate(runtime, action.value)

                try:
                    runtime.activate(result)
                except ActivationRejected:
                    if runtime.previous is None:
                        raise

                    if snapshot(runtime) != before:
                        raise AssertionError(
                            "rejected activation changed runtime state"
                        )

            else:
                raise AssertionError(
                    f"unknown generated action {action.kind!r}"
                )

            check_invariants(runtime, live)

        except Exception as exc:
            raise AssertionError(
                f"step={index} action={action!r}: {exc}"
            ) from exc


def fails(actions: tuple[Action, ...]) -> bool:
    try:
        execute(actions)
    except AssertionError:
        return True

    return False


class StatefulSequenceTests(unittest.TestCase):
    def test_seeded_runtime_sequences_preserve_global_invariants(self) -> None:
        for seed in seeds(CASES):
            actions = actions_for(seed)

            with self.subTest(seed=seed):
                try:
                    execute(actions)
                except AssertionError as exc:
                    reduced = minimize_sequence(actions, fails)

                    self.fail(
                        f"{exc}\n"
                        f"seed={seed}\n"
                        f"reproduce: "
                        f"{reproduction(__name__, seed)}\n"
                        f"minimized={reduced!r}"
                    )


if __name__ == "__main__":
    unittest.main()
