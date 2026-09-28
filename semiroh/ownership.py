"""Ownership relations for immutable semantic states."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .identity import EntityID


class OwnershipError(ValueError):
    """An ownership relation violates semantic ownership rules."""


OwnershipMap = Mapping[
    EntityID,
    Iterable[EntityID],
]


def normalize_ownership(
    ownership: OwnershipMap,
) -> dict[EntityID, tuple[EntityID, ...]]:
    """Validate and canonicalize an ownership forest.

    Owners with no children are omitted: ``{owner: ()}`` and ``{}`` describe
    the same ownership relation and therefore have the same canonical form.
    """

    normalized = {
        owner: tuple(sorted(set(children)))
        for owner, children in ownership.items()
    }

    normalized = {
        owner: children
        for owner, children in normalized.items()
        if children
    }

    parents: dict[EntityID, EntityID] = {}

    for owner, children in normalized.items():
        if owner in children:
            raise OwnershipError(
                f"entity {owner.value} cannot own itself"
            )

        for child in children:
            previous_owner = parents.get(child)

            if previous_owner is not None:
                raise OwnershipError(
                    f"entity {child.value} has multiple owners: "
                    f"{previous_owner.value} and {owner.value}"
                )

            parents[child] = owner

    # Ownership must be acyclic.
    # 0 = unvisited, 1 = currently visiting, 2 = completely visited.
    status: dict[EntityID, int] = {}

    def visit(entity: EntityID) -> None:
        current_status = status.get(entity, 0)

        if current_status == 1:
            raise OwnershipError(
                f"ownership cycle detected at {entity.value}"
            )

        if current_status == 2:
            return

        status[entity] = 1

        for child in normalized.get(entity, ()):
            visit(child)

        status[entity] = 2

    for owner in normalized:
        visit(owner)

    return normalized


def owner_of(
    ownership: OwnershipMap,
    entity: EntityID,
) -> EntityID | None:
    """Return the unique owner of an entity, if any."""

    for owner, children in ownership.items():
        if entity in children:
            return owner

    return None


def owned_children(
    ownership: OwnershipMap,
    owner: EntityID,
) -> tuple[EntityID, ...]:
    """Return entities directly owned by an owner."""

    return tuple(
        sorted(
            ownership.get(owner, ())
        )
    )


def owned_subtree(
    ownership: OwnershipMap,
    owner: EntityID,
) -> frozenset[EntityID]:
    """Return the complete recursively owned subtree."""

    result: set[EntityID] = set()
    stack = list(ownership.get(owner, ()))

    while stack:
        entity = stack.pop()

        if entity in result:
            continue

        result.add(entity)
        stack.extend(
            ownership.get(entity, ())
        )

    return frozenset(result)
