"""Semantic values and version identity."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from .canonical import canonical_serialize, canonicalize
from .identity import EntityID, VersionID


@dataclass(frozen=True, eq=False)
class Value:
    """Immutable semantic value.

    Equality and hashing are defined by entity identity plus canonical
    serialization of the content, not by Python equality of the content.
    Python considers ``True == 1``; SEMIROH does not, because their canonical
    serializations differ.
    """

    entity: EntityID
    content: Any

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "content",
            canonicalize(self.content),
        )

    def _identity_key(self) -> tuple[EntityID, bytes]:
        return (
            self.entity,
            canonical_serialize(self.content),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Value):
            return NotImplemented

        return self._identity_key() == other._identity_key()

    def __hash__(self) -> int:
        return hash(self._identity_key())

    @staticmethod
    def create(
        entity: EntityID,
        content: Any,
    ) -> "Value":
        return Value(entity, content)

    @property
    def version_id(self) -> VersionID:
        """Return the exact semantic version identity of this value."""

        return version_id_for(self)


def version_id_for(value: Value) -> VersionID:
    """Derive exact version identity from entity and semantic content."""

    encoded = (
        b"VERSION"
        + canonical_serialize(value.entity)
        + canonical_serialize(value.content)
    )

    return VersionID(
        sha256(encoded).hexdigest()
    )
