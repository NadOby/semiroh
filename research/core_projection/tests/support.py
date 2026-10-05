"""Generators and independent references for the instrument tests.

Everything here is test machinery: the references are deliberately written
differently from ``core.py`` (greatest fixpoint, brute-force permutations,
explicit Unknown/Known case analysis) so they can disagree with it.
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from itertools import permutations
from typing import Iterator

from core_projection.core import Atom, CState

ATOMS = (None, Atom("symbol", "a"), Atom("int", 1), Atom("bool", True))
ROLES = ("x", "y")


def seeds(count: int) -> tuple[int, ...]:
    """Deterministic seeds; SHEAR_SEED replays, SHEAR_CASES enlarges."""

    requested = os.environ.get("SHEAR_SEED")

    if requested is not None:
        return tuple(int(s) for s in requested.split(",") if s.strip())

    heavy = os.environ.get("SHEAR_CASES")

    return tuple(range(int(heavy) if heavy not in (None, "", "0") else count))


def random_state(rng: random.Random, max_handles: int = 5) -> CState:
    """A random small state; sharing and cycles occur freely."""

    size = rng.randint(1, max_handles)
    pool = ATOMS[: rng.randint(1, len(ATOMS))]
    relations = {}

    for handle in range(size):
        roles = {}

        for name in ROLES:
            if rng.random() < 0.6:
                roles[name] = tuple(
                    rng.randrange(size) for _ in range(rng.randint(0, 2))
                )

        relations[handle] = (rng.choice(pool), roles)

    return CState(relations)


def doubled(state: CState) -> CState:
    """Two disjoint copies of the state: it has at least the swap as an automorphism."""

    offset = max(state.handles, default=-1) + 1

    return CState({
        **{h: (state.atom(h), state.roles(h)) for h in state},
        **{
            h + offset: (
                state.atom(h),
                {n: tuple(t + offset for t in ts) for n, ts in state.roles(h).items()},
            )
            for h in state
        },
    })


def cycle(length: int, atom: Atom | None = None, chords: bool = False) -> CState:
    """A directed cycle of equal occurrences: ``length`` rotational automorphisms.

    With ``chords`` every occurrence also points to itself under role ``y``.
    """

    return CState({
        h: (
            atom,
            {"x": ((h + 1) % length,), **({"y": (h,)} if chords else {})},
        )
        for h in range(length)
    })


def permuted(rng: random.Random, state: CState) -> tuple[CState, dict[int, int]]:
    """The state under a random renaming of its handles, and the renaming."""

    fresh = rng.sample(range(100), len(state))
    renaming = dict(zip(state.handles, fresh))

    return state.relabel(renaming), renaming


def unfold(
    rng: random.Random,
    state: CState,
    max_copies: int = 3,
) -> tuple[CState, dict[int, list[int]]]:
    """An equal-valued state with different sharing.

    Each handle becomes 1..max_copies copies; every target picks a random copy
    of its original. Each copy is bisimilar to the handle it came from.
    """

    copies: dict[int, list[int]] = {}
    next_handle = 0

    for handle in state:
        count = rng.randint(1, max_copies)
        copies[handle] = list(range(next_handle, next_handle + count))
        next_handle += count

    relations = {}

    for handle in state:
        for copy in copies[handle]:
            relations[copy] = (
                state.atom(handle),
                {
                    name: tuple(rng.choice(copies[t]) for t in targets)
                    for name, targets in state.roles(handle).items()
                },
            )

    return CState(relations), copies


# -- references ------------------------------------------------------------


def naive_bisimilar_pairs(left: CState, right: CState) -> set[tuple[int, int]]:
    """Greatest fixpoint over all pairs: the textbook definition."""

    pairs = {
        (x, y)
        for x in left
        for y in right
        if left.atom(x) == right.atom(y)
        and {n: len(t) for n, t in left.roles(x).items()}
        == {n: len(t) for n, t in right.roles(y).items()}
    }

    changed = True

    while changed:
        changed = False

        for x, y in sorted(pairs):
            right_roles = right.roles(y)

            if any(
                (s, t) not in pairs
                for name, targets in left.roles(x).items()
                for s, t in zip(targets, right_roles[name])
            ):
                pairs.discard((x, y))
                changed = True

    return pairs


def is_isomorphism(left: CState, right: CState, mapping: dict[int, int]) -> bool:
    """Check the charter section 3.11 conditions directly."""

    if sorted(mapping) != list(left.handles):
        return False

    if sorted(mapping.values()) != list(right.handles):
        return False

    for handle in left:
        image = mapping[handle]

        if left.atom(handle) != right.atom(image):
            return False

        left_roles, right_roles = left.roles(handle), right.roles(image)

        if left_roles.keys() != right_roles.keys():
            return False

        for name, targets in left_roles.items():
            if tuple(mapping[t] for t in targets) != right_roles[name]:
                return False

    return True


def brute_force_isomorphisms(left: CState, right: CState) -> Iterator[dict[int, int]]:
    if len(left) != len(right):
        return

    for images in permutations(right.handles):
        mapping = dict(zip(left.handles, images))

        if is_isomorphism(left, right, mapping):
            yield mapping


@dataclass(frozen=True)
class Unknown:
    pass


@dataclass(frozen=True)
class Known:
    targets: frozenset[int]


def option(continuity, source: int) -> Unknown | Known:
    return Known(continuity[source]) if source in continuity else Unknown()


def naive_compose(first, second, source: int) -> Unknown | Known:
    """Explicit case analysis on ``Unknown | Known(set)`` for one source."""

    outcome = option(first, source)

    if isinstance(outcome, Unknown):
        return Unknown()

    final: set[int] = set()

    for middle in sorted(outcome.targets):
        step = option(second, middle)

        if isinstance(step, Unknown):
            return Unknown()

        final |= step.targets

    return Known(frozenset(final))


def random_continuity(
    rng: random.Random,
    sources: range,
    destinations: range,
) -> dict[int, frozenset[int]]:
    result = {}

    for source in sources:
        if rng.random() < 0.7:
            result[source] = frozenset(
                rng.sample(list(destinations), rng.randint(0, min(2, len(destinations))))
            )

    return result
