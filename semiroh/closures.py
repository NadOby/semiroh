"""Executable lexical closure values (docs/closures.md)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import (
    CanonicalNode,
    SemanticRecord,
    _node,
    canonical_serialize,
    canonicalize,
)
from .identity import EntityID


def _decode_structure(value: Any) -> Any:
    """Decode container structure while leaving semantic leaf values tagged."""

    if not isinstance(value, CanonicalNode):
        return value

    kind = value[1]

    if kind == "tuple":
        return tuple(_decode_structure(item) for item in value[2])

    if kind == "list":
        return [_decode_structure(item) for item in value[2]]

    if kind == "map":
        return {
            _decode_structure(key): _decode_structure(item)
            for key, item in value[2]
        }

    return value


def _entity(value: Any) -> EntityID | None:
    if isinstance(value, EntityID):
        return value

    if (
        isinstance(value, CanonicalNode)
        and value[1] == "entity_id"
        and isinstance(value[2], str)
    ):
        return EntityID(value[2])

    return None


@dataclass(frozen=True, eq=False)
class Closure(SemanticRecord):
    """Executable graph code and values captured from a lexical scope."""

    owner: EntityID
    body: EntityID
    params: tuple[str, ...]
    captures: tuple[tuple[str, Any], ...]

    def __post_init__(self) -> None:
        params = tuple(self.params)
        captures = tuple(self.captures)

        if not isinstance(self.owner, EntityID):
            raise TypeError("closure owner must be an EntityID")

        if not isinstance(self.body, EntityID):
            raise TypeError("closure body must be an EntityID")

        if not all(
            isinstance(name, str) and name
            for name in params
        ):
            raise TypeError(
                "closure parameters must be non-empty strings"
            )

        if len(params) != len(set(params)):
            raise TypeError("duplicate closure parameter name")

        if not all(
            isinstance(pair, tuple)
            and len(pair) == 2
            and isinstance(pair[0], str)
            and pair[0]
            for pair in captures
        ):
            raise TypeError(
                "closure captures need non-empty string names"
            )

        capture_names = tuple(
            name
            for name, _ in captures
        )

        if len(capture_names) != len(set(capture_names)):
            raise TypeError("duplicate closure capture name")

        if set(params) & set(capture_names):
            raise TypeError(
                "closure parameter and capture names overlap"
            )

        object.__setattr__(self, "params", params)
        object.__setattr__(self, "captures", captures)

    def canonical_node(self) -> CanonicalNode:
        return _node(
            "closure",
            (
                canonicalize(self.owner),
                canonicalize(self.body),
                canonicalize(self.params),
                canonicalize(self.captures),
            ),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Closure):
            return NotImplemented

        return (
            canonical_serialize(self)
            == canonical_serialize(other)
        )

    def __hash__(self) -> int:
        return hash(canonical_serialize(self))


def closure_value(value: Any) -> Closure | None:
    """Decode a live or canonical closure value."""

    if isinstance(value, Closure):
        return value

    if not (
        isinstance(value, CanonicalNode)
        and value[1] == "closure"
        and isinstance(value[2], tuple)
        and len(value[2]) == 4
    ):
        return None

    owner_value, body_value, params_value, captures_value = value[2]
    owner = _entity(owner_value)
    body = _entity(body_value)

    if owner is None or body is None:
        return None

    params = _decode_structure(params_value)
    captures = _decode_structure(captures_value)

    try:
        return Closure(
            owner,
            body,
            params,
            captures,
        )
    except (TypeError, ValueError):
        return None
