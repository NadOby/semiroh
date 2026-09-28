"""Immutable semantic states."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import canonical_serialize
from .identity import EntityID, StateID
from .ownership import (
    OwnershipError,
    OwnershipMap,
    normalize_ownership,
    owned_children,
    owned_subtree,
    owner_of,
)
from .references import (
    CrossStateReference,
    Reference,
    StaleReference,
    make_reference,
)
from .values import Value, version_id_for


def _state_content(
    values: Mapping[EntityID, Value],
    ownership: Mapping[
        EntityID,
        tuple[EntityID, ...],
    ],
) -> bytes:
    canonical_values = [
        (
            canonical_serialize(entity),
            canonical_serialize(values[entity].content),
        )
        for entity in sorted(values)
    ]

    canonical_values.sort(
        key=lambda item: item[0]
    )

    canonical_ownership = [
        (
            canonical_serialize(owner),
            canonical_serialize(children),
        )
        for owner, children in ownership.items()
    ]

    canonical_ownership.sort(
        key=lambda item: item[0]
    )

    return (
        b"STATE"
        + len(canonical_values).to_bytes(
            8,
            byteorder="big",
            signed=False,
        )
        + b"".join(
            entity + content
            for entity, content in canonical_values
        )
        + len(canonical_ownership).to_bytes(
            8,
            byteorder="big",
            signed=False,
        )
        + b"".join(
            owner + children
            for owner, children in canonical_ownership
        )
    )


@dataclass(frozen=True)
class State:
    """Immutable semantic state.

    State identity is derived only from semantic content.
    Transformation mappings and provenance are not state content.

    Ownership is part of semantic state content.

    Equality and hashing are semantic: two states with identical canonical
    semantic content are equal regardless of how their mappings were supplied.

    ``StateID`` is always derived from the validated content during
    construction and cannot be supplied by the caller.
    """

    id: StateID = field(init=False)
    values: Mapping[EntityID, Value]
    ownership: Mapping[
        EntityID,
        tuple[EntityID, ...],
    ] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for entity, value in self.values.items():
            if value.entity != entity:
                raise ValueError(
                    f"value entity {value.entity.value} does not match "
                    f"state key {entity.value}"
                )

        immutable_values = MappingProxyType(
            dict(self.values)
        )

        supplied_ownership = {
            owner: tuple(children)
            for owner, children in self.ownership.items()
        }

        # Presence is checked on the supplied relation, before normalization
        # drops owners with no children, so that an absent entity is rejected
        # even when it is listed with an empty child collection.
        for owner, children in supplied_ownership.items():
            if owner not in immutable_values:
                raise OwnershipError(
                    f"owner {owner.value} is absent from state"
                )

            for child in children:
                if child not in immutable_values:
                    raise OwnershipError(
                        f"owned entity {child.value} is absent from state"
                    )

        immutable_ownership = MappingProxyType(
            dict(normalize_ownership(supplied_ownership))
        )

        state_id = StateID(
            sha256(
                _state_content(
                    immutable_values,
                    immutable_ownership,
                )
            ).hexdigest()
        )

        object.__setattr__(self, "values", immutable_values)
        object.__setattr__(self, "ownership", immutable_ownership)
        object.__setattr__(self, "id", state_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return NotImplemented

        return (
            self.id == other.id
            and self._content_bytes() == other._content_bytes()
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def _content_bytes(self) -> bytes:
        return _state_content(
            self.values,
            self.ownership,
        )

    @property
    def semantic_digest(self) -> str:
        """Return the canonical SHA-256 digest of semantic state content."""

        return sha256(
            self._content_bytes()
        ).hexdigest()

    @staticmethod
    def create(
        values: Mapping[EntityID, Value],
        ownership: OwnershipMap | None = None,
    ) -> "State":
        return State(
            values=values,
            ownership=ownership or {},
        )

    def reference(
        self,
        entity: EntityID,
    ) -> Reference:
        if entity not in self.values:
            raise KeyError(
                f"{entity.value} is absent from {self.id.value}"
            )

        return make_reference(
            self.id,
            entity,
            self.values[entity],
        )

    def resolve(
        self,
        reference: Reference,
    ) -> Value:
        if reference.state != self.id:
            raise CrossStateReference(
                f"reference belongs to {reference.state.value}, "
                f"not {self.id.value}"
            )

        try:
            value = self.values[reference.entity]
        except KeyError as exc:
            raise KeyError(
                f"{reference.entity.value} is absent from "
                f"{self.id.value}"
            ) from exc

        actual_version = version_id_for(value)

        if actual_version != reference.version:
            raise StaleReference(
                f"reference expects version {reference.version.value}, "
                f"but state contains {actual_version.value}"
            )

        return value

    def contains(
        self,
        entity: EntityID,
    ) -> bool:
        return entity in self.values

    def owner_of(
        self,
        entity: EntityID,
    ) -> EntityID | None:
        if entity not in self.values:
            raise KeyError(
                f"{entity.value} is absent from {self.id.value}"
            )

        return owner_of(
            self.ownership,
            entity,
        )

    def owned_children(
        self,
        owner: EntityID,
    ) -> tuple[EntityID, ...]:
        if owner not in self.values:
            raise KeyError(
                f"{owner.value} is absent from {self.id.value}"
            )

        return owned_children(
            self.ownership,
            owner,
        )

    def owned_subtree(
        self,
        owner: EntityID,
    ) -> frozenset[EntityID]:
        if owner not in self.values:
            raise KeyError(
                f"{owner.value} is absent from {self.id.value}"
            )

        return owned_subtree(
            self.ownership,
            owner,
        )

    def with_changes(
        self,
        changes: Mapping[EntityID, Any],
    ) -> "State":
        values = dict(self.values)

        for entity, content in changes.items():
            values[entity] = Value(
                entity,
                content,
            )

        return State.create(
            values,
            self.ownership,
        )

    def destroy(
        self,
        entity: EntityID,
    ) -> "State":
        """Produce a new state with an entity and its owned subtree removed."""

        if entity not in self.values:
            raise KeyError(
                f"{entity.value} is absent from {self.id.value}"
            )

        removed = {
            entity,
            *self.owned_subtree(entity),
        }

        values = {
            current_entity: value
            for current_entity, value in self.values.items()
            if current_entity not in removed
        }

        ownership = {
            owner: tuple(
                child
                for child in children
                if child not in removed
            )
            for owner, children in self.ownership.items()
            if owner not in removed
        }

        ownership = {
            owner: children
            for owner, children in ownership.items()
            if children
        }

        return State.create(
            values,
            ownership,
        )
