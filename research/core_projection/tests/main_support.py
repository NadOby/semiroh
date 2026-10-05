"""Random synthetic ``main`` states for the projection tests."""

from __future__ import annotations

import random
from typing import Any

from shear.canonical import CanonicalNode
from shear.identity import EntityID
from shear.relations import Relation
from shear.state import State
from shear.values import Value


def eid(index: int) -> EntityID:
    return EntityID(f"e{index}")


def random_plain(rng: random.Random, names: int, depth: int = 0) -> Any:
    """Content built from primitives, bytes, sequences, maps and references."""

    options = ["none", "bool", "int", "str", "bytes", "ref"]

    if depth < 2:
        options += ["tuple", "list", "map"]

    kind = rng.choice(options)

    if kind == "none":
        return None

    if kind == "bool":
        return rng.random() < 0.5

    if kind == "int":
        return rng.randint(-3, 3)

    if kind == "str":
        return rng.choice(["a", "b", ""])

    if kind == "bytes":
        return rng.choice([b"", b"\x01\xff"])

    if kind == "ref":
        return eid(rng.randrange(names))

    items = [random_plain(rng, names, depth + 1) for _ in range(rng.randint(0, 3))]

    if kind == "tuple":
        return tuple(items)

    if kind == "list":
        return items

    return {f"k{i}": item for i, item in enumerate(items)}


def random_relation(rng: random.Random, names: int, unit_tuples: bool) -> Relation:
    roles: dict[str, Any] = {}

    for role in ("a", "b", "c"):
        if rng.random() < 0.6:
            if rng.random() < 0.5:
                roles[role] = eid(rng.randrange(names))
            else:
                length = rng.choice((0, 1, 2, 3) if unit_tuples else (0, 2, 3))
                roles[role] = tuple(eid(rng.randrange(names)) for _ in range(length))

    payload = random_plain(rng, names) if rng.random() < 0.5 else None

    return Relation(rng.choice(["add", "call", "lit"]), roles, payload)


def cell_like() -> CanonicalNode:
    """A ``cell`` record as main builds it: a node whose payload is a raw tuple."""

    constraint = CanonicalNode(("__type__", "constraint", ("int_range", 0, None)))

    return CanonicalNode(("__type__", "cell", (constraint, 0)))


def random_main_state(
    rng: random.Random,
    max_entities: int = 6,
    unit_tuples: bool = False,
    ownership: bool = True,
) -> State:
    count = rng.randint(1, max_entities)
    values: dict[EntityID, Value] = {}

    for index in range(count):
        kind = rng.choice(["plain", "relation", "relation", "relation", "cell"])

        if kind == "plain":
            content = random_plain(rng, count)

            if isinstance(content, EntityID):
                content = (content,)
        elif kind == "relation":
            content = random_relation(rng, count, unit_tuples)
        else:
            content = cell_like()

        values[eid(index)] = Value(eid(index), content)

    owned: dict[EntityID, list[EntityID]] = {}

    if ownership:
        order = list(range(count))
        rng.shuffle(order)

        for position in range(1, count):
            if rng.random() < 0.5:
                owner = eid(order[rng.randrange(position)])
                owned.setdefault(owner, []).append(eid(order[position]))

    return State.create(values, owned)
