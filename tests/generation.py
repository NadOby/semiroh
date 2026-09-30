"""Helpers for reproducible generated verification."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from typing import TypeVar


T = TypeVar("T")


def case_count(default: int) -> int:
    """Return the ordinary or explicitly requested generated-case budget."""

    requested = os.environ.get("SEMIROH_CASES")

    if requested in (None, "", "0"):
        return default

    value = int(requested)

    if value < 1:
        raise ValueError("SEMIROH_CASES must be a positive integer or 0")

    return value


def seeds(count: int, variable: str = "SEMIROH_SEED") -> tuple[int, ...]:
    """Return deterministic seeds for normal, heavy, or replay execution.

    SEMIROH_SEED accepts one integer or a comma-separated list and takes
    precedence over SEMIROH_CASES.  SEMIROH_CASES enlarges the ordinary
    range while preserving deterministic seeds starting at zero.
    """

    requested = os.environ.get(variable)

    if requested is None:
        return tuple(range(case_count(count)))

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
