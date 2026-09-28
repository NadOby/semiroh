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
    #
    # Every entity has at most one owner (checked above), so a cycle exists
    # exactly when walking up the owner chain from some entity revisits an
    # entity on the current walk. The walk is iterative so that deep ownership
    # chains do not hit the interpreter recursion limit.
    # 1 = on the current walk, 2 = already verified acyclic.
    status: dict[EntityID, int] = {}

    for start in parents:
        path: list[EntityID] = []
        entity: EntityID | None = start

        while entity is not None and entity not in status:
            status[entity] = 1
            path.append(entity)
            entity = parents.get(entity)

        if entity is not None and status[entity] == 1:
            raise OwnershipError(
                f"ownership cycle detected at {entity.value}"
            )

        for visited in path:
            status[visited] = 2

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


def follow_ownership(
    ownership: OwnershipMap,
    mappings: Mapping[EntityID, tuple[EntityID, ...]],
) -> dict[EntityID, list[EntityID]]:
    """Carry ownership edges along declared continuity.

    Each endpoint of an edge that the mappings name follows its mapping, as
    relation endpoints do; unmapped endpoints stay. No entity that remains
    may change owner implicitly, so an owner that disappears or splits while
    its child remains, or a child that splits, is rejected: the
    transformation must then supply destination ownership explicitly. An edge
    whose child disappears goes with the child, because that disappearance
    is declared. The caller validates the resulting forest.
    """

    followed: dict[EntityID, list[EntityID]] = {}

    for owner, children in ownership.items():
        for child in children:
            if child in mappings:
                targets = mappings[child]

                if not targets:
                    continue

                if len(targets) > 1:
                    raise OwnershipError(
                        f"owned entity {child.value} splits; supply "
                        f"destination ownership explicitly"
                    )

                child_after = targets[0]
            else:
                child_after = child

            if owner in mappings:
                targets = mappings[owner]

                if len(targets) != 1:
                    outcome = "disappears" if not targets else "splits"
                    raise OwnershipError(
                        f"owner {owner.value} {outcome} while "
                        f"{child.value} remains; supply destination "
                        f"ownership explicitly"
                    )

                owner_after = targets[0]
            else:
                owner_after = owner

            followed.setdefault(owner_after, []).append(child_after)

    return followed
