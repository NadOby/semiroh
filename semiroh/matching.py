"""Continuity inference for ``define`` (docs/continuity_inference.md §2).

:func:`match` decides which new node of an edit keeps the identity of
which old node. It is the one place the rules live; ``lang.define`` builds
the two sides and calls it.

- **Rule 1, unchanged subtrees.** From the largest size down, a new
  subtree whose shape occurs exactly once among the old subtrees not
  matched yet and exactly once among the new subtrees not matched yet is
  matched whole, node by node.
- **Rule 2, the edited position.** Each new root then takes the old node at
  its position when neither is matched and both have the same kind.

Nothing else is matched. The result depends only on the two sides, not on
the order they are given in: every subtree of one size is decided against
the counts taken before any of them is matched, and matching one never
changes the count of another shape of the same size.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Mapping

from .canonical import canonical_serialize
from .identity import EntityID
from .relations import Endpoint, Relation


def _items(endpoint: Endpoint) -> tuple[EntityID, ...]:
    return endpoint if isinstance(endpoint, tuple) else (endpoint,)


def shapes(
    nodes: Mapping[EntityID, Relation],
    table: dict[tuple, int] | None = None,
) -> dict[EntityID, tuple[int, int]]:
    """Each node's ``(shape, size)``.

    The shape of a subtree is its kind, its payload and its roles, with an
    endpoint that is one of ``nodes`` (an operand) compared by shape and
    any other endpoint (a called function, a cell) by ``EntityID``. Shapes
    are numbered in ``table``, so two sides numbered in one table compare
    by number. The size is the number of nodes in the subtree.
    """

    table = {} if table is None else table
    found: dict[EntityID, tuple[int, int]] = {}

    def visit(entity: EntityID) -> tuple[int, int]:
        if entity in found:
            return found[entity]

        node = nodes[entity]
        size = 1
        roles = []

        for role, endpoint in node.roles.items():
            keys = []

            for item in _items(endpoint):
                if item in nodes:
                    shape, count = visit(item)
                    size += count
                    keys.append((True, shape))
                else:
                    keys.append((False, item))

            roles.append((role, tuple(keys)))

        key = (node.kind, canonical_serialize(node.payload), tuple(roles))
        found[entity] = (table.setdefault(key, len(table)), size)

        return found[entity]

    for entity in nodes:
        visit(entity)

    return found


def match(
    old: Mapping[EntityID, Relation],
    new: Mapping[EntityID, Relation],
    positions: Iterable[tuple[EntityID, EntityID | None]],
) -> dict[EntityID, EntityID]:
    """Map each new node that keeps an identity to the old node it keeps.

    ``old`` and ``new`` are the two sides of every entry of one edit (the
    pool), as node entity to node relation; their entities are disjoint.
    ``positions`` pairs each entry's new root with the old node at that
    position, or None when there is none (a function the edit creates).
    """

    table: dict[tuple, int] = {}
    old_shapes = shapes(old, table)
    new_shapes = shapes(new, table)
    kept: dict[EntityID, EntityID] = {}
    used: set[EntityID] = set()

    def pair(mine: EntityID, theirs: EntityID) -> None:
        kept[mine] = theirs
        used.add(theirs)
        before = old[theirs].roles

        for role, endpoint in new[mine].roles.items():
            for child, counterpart in zip(_items(endpoint), _items(before[role])):
                if child in new:
                    pair(child, counterpart)

    old_by_size: dict[int, list[EntityID]] = {}
    new_by_size: dict[int, list[EntityID]] = {}

    for entity, (_, size) in old_shapes.items():
        old_by_size.setdefault(size, []).append(entity)

    for entity, (_, size) in new_shapes.items():
        new_by_size.setdefault(size, []).append(entity)

    for size in sorted(new_by_size, reverse=True):
        candidates = [entity for entity in new_by_size[size] if entity not in kept]
        counts = Counter(new_shapes[entity][0] for entity in candidates)
        olds: dict[int, list[EntityID]] = {}

        for entity in old_by_size.get(size, ()):
            if entity not in used:
                olds.setdefault(old_shapes[entity][0], []).append(entity)

        for entity in candidates:
            shape = new_shapes[entity][0]
            found = olds.get(shape, ())

            if counts[shape] == 1 and len(found) == 1:
                pair(entity, found[0])

    for root, position in positions:
        if (
            position is not None
            and root not in kept
            and position not in used
            and new[root].kind == old[position].kind
        ):
            kept[root] = position
            used.add(position)

    return kept
