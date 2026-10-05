"""Generators and independent references for the named-roots instrument tests.

Like ``support.py``, the references are written differently from the code
they check: explicit trees instead of bisimulation, brute-force permutations
instead of refinement, and an explicit decoder for the encoding.
"""

from __future__ import annotations

import random
from itertools import permutations
from typing import Iterator

from core_projection.core import Atom
from core_projection.named import Contained, Name, Named, NState
from core_projection.tests.support import ATOMS, ROLES

NAMES = tuple(Name(n) for n in ("a", "b", "c"))


def random_nstate(rng: random.Random, max_handles: int = 5) -> NState:
    """A random small acyclic state: contained targets point to larger handles.

    Names are bound to random handles, so two states bind the same name to
    different content, and a ``Named`` target may point at any bound name.
    """

    size = rng.randint(1, max_handles)
    pool = ATOMS[: rng.randint(1, len(ATOMS))]
    bound = rng.sample(NAMES, rng.randint(0, len(NAMES)))
    relations = {}

    for handle in range(size):
        roles = {}

        for role in ROLES:
            if rng.random() < 0.6:
                targets = []

                for _ in range(rng.randint(0, 2)):
                    if bound and rng.random() < 0.4:
                        targets.append(Named(rng.choice(bound)))
                    elif handle + 1 < size:
                        targets.append(Contained(rng.randrange(handle + 1, size)))

                roles[role] = tuple(targets)

        relations[handle] = (rng.choice(pool), roles)

    return NState(relations, {name: rng.randrange(size) for name in bound})


def naive_tree(state: NState, handle: int) -> tuple:
    """The value at ``handle`` as an explicit tree (containment is acyclic)."""

    return (
        state.atom(handle),
        tuple(
            (
                role,
                tuple(
                    ("contained", naive_tree(state, t.handle))
                    if isinstance(t, Contained)
                    else ("named", t.name.value)
                    for t in targets
                ),
            )
            for role, targets in state.roles(handle).items()
        ),
    )


def permuted_n(rng: random.Random, state: NState) -> tuple[NState, dict[int, int]]:
    fresh = rng.sample(range(100), len(state))
    renaming = dict(zip(state.handles, fresh))

    return state.relabel(renaming), renaming


def is_nisomorphism(left: NState, right: NState, mapping: dict[int, int]) -> bool:
    """The conditions of charter section 3.12 item 5, checked directly."""

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

        for role, targets in left_roles.items():
            others = right_roles[role]

            if len(targets) != len(others):
                return False

            for t, o in zip(targets, others):
                if isinstance(t, Contained):
                    if not (isinstance(o, Contained) and mapping[t.handle] == o.handle):
                        return False
                elif not (isinstance(o, Named) and o.name == t.name):
                    return False

    if left.bindings.keys() != right.bindings.keys():
        return False

    return all(mapping[left.bindings[n]] == right.bindings[n] for n in left.bindings)


def brute_force_nisomorphisms(left: NState, right: NState) -> Iterator[dict[int, int]]:
    if len(left) != len(right):
        return

    for images in permutations(right.handles):
        mapping = dict(zip(left.handles, images))

        if is_nisomorphism(left, right, mapping):
            yield mapping


def decode_encoding(cstate) -> NState:
    """Rebuild a state from its encoding alone, to show the encoding is injective.

    Name leaves and binding relations are recognised by their reserved atoms;
    everything else is content, and keeps its handle number.
    """

    leaves = {}
    bindings = {}
    content = {}

    for handle in cstate:
        atom = cstate.atom(handle)

        if atom is not None and atom.tag == "symbol" and atom.value.startswith("name:"):
            leaves[handle] = Name(atom.value[len("name:"):])
        elif atom is not None and atom.tag == "symbol" and atom.value.startswith("binding:"):
            bindings[Name(atom.value[len("binding:"):])] = cstate.roles(handle)["root"][0]
        else:
            content[handle] = (atom, cstate.roles(handle))

    return NState(
        {
            handle: (
                atom,
                {
                    role: tuple(
                        Named(leaves[t]) if t in leaves else Contained(t) for t in targets
                    )
                    for role, targets in roles.items()
                },
            )
            for handle, (atom, roles) in content.items()
        },
        bindings,
    )
