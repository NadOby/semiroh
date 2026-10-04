"""Identity primitives for the SEMIROH semantic model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class EntityID:
    """Conceptual identity preserved across semantic states."""

    value: str


@dataclass(frozen=True, order=True)
class VersionID:
    """Identity of one exact semantic version of an entity."""

    value: str


@dataclass(frozen=True, order=True)
class StateID:
    """Identity of one exact immutable semantic state."""

    value: str


@dataclass(frozen=True)
class Entity:
    """Semantic entity identified by an EntityID."""

    id: EntityID
