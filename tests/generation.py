"""Helpers for reproducible generated verification."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from typing import TypeVar


T = TypeVar("T")


def seeds(count: int, variable: str = "SEMIROH_SEED") -> tuple[int, ...]:
    """Return the ordinary deterministic seed range or requested replay seeds.

    SEMIROH_SEED accepts one integer or a comma-separated list.  Generated
    tests can therefore print a command that reproduces exactly one failure.
    """

    requested = os.environ.get(variable)

    if requested is None:
        return tuple(range(count))

    values = tuple(
        int(item.strip())
        for item in requested.split(",")
        if item.strip()
    )

    if not values:
        raise ValueError(f"{variable} did not contain a seed")

    return values


def minimize_sequence(
    items: Sequence[T],
    fails: Callable[[tuple[T, ...]], bool],
) -> tuple[T, ...]:
    """Reduce a failing sequence while preserving failure.

    This is a small deterministic delta-debugging reducer.  It removes chunks,
    increasing granularity only when no chunk at the current size can go.
    """

    current = tuple(items)

    if not fails(current):
        raise ValueError("sequence does not fail")

    parts = 2

    while len(current) > 1:
        chunk = max(1, (len(current) + parts - 1) // parts)
        reduced = False

        for start in range(0, len(current), chunk):
            candidate = current[:start] + current[start + chunk :]

            if candidate and fails(candidate):
                current = candidate
                parts = max(2, parts - 1)
                reduced = True
                break

        if reduced:
            continue

        if parts >= len(current):
            break

        parts = min(len(current), parts * 2)

    return current


def reproduction(module: str, seed: int) -> str:
    return (
        f"SEMIROH_SEED={seed} "
        f"python -m unittest {module}"
    )
