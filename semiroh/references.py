"""State-pinned and version-pinned semantic references."""

from __future__ import annotations

from dataclasses import dataclass

from .identity import EntityID, StateID, VersionID
from .values import Value, version_id_for


class CrossStateReference(ValueError):
    """A reference was resolved against the wrong semantic state."""


class StaleReference(ValueError):
    """A reference's expected entity version is not present."""


class MissingEntityMapping(ValueError):
    """No explicit cross-state identity mapping exists."""


class AmbiguousEntityMapping(ValueError):
    """A cross-state identity mapping has multiple destinations."""


@dataclass(frozen=True)
class Reference:
    """State-pinned and version-pinned semantic reference."""

    state: StateID
    entity: EntityID
    version: VersionID


def project_entity(reference: Reference) -> EntityID:
    """Project a reference to conceptual entity identity."""

    return reference.entity


def make_reference(
    state_id: StateID,
    entity: EntityID,
    value: Value,
) -> Reference:
    """Create a reference to one exact value in one state."""

    if value.entity != entity:
        raise ValueError(
            f"value entity {value.entity.value} does not match "
            f"reference entity {entity.value}"
        )

    return Reference(
        state=state_id,
        entity=entity,
        version=version_id_for(value),
    )
