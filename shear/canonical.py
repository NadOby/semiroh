"""Canonical immutable serialization for SEMIROH semantic values."""

from __future__ import annotations

from typing import Any, Mapping

from .identity import EntityID, StateID, VersionID


class CanonicalNode(tuple):
    """Tagged node produced by :func:`canonicalize`.

    A ``CanonicalNode`` is an ordinary immutable tuple of the form
    ``("__type__", kind, payload)``. It compares and serializes exactly like
    the equivalent plain tuple, so it does not change any semantic identity.

    The distinct type exists only so that already-canonical content can be
    recognised: ``canonicalize`` returns a ``CanonicalNode`` unchanged instead
    of wrapping it again as a user tuple. This makes canonicalization
    idempotent.
    """

    __slots__ = ()


def _node(kind: str, payload: Any) -> CanonicalNode:
    return CanonicalNode(("__type__", kind, payload))


class SemanticRecord:
    """Base class for model records that are semantic values.

    A semantic record defines its own tagged canonical node. Canonicalization
    and canonical serialization use that node, so records participate in
    value and state identity like built-in semantic values.
    """

    def canonical_node(self) -> CanonicalNode:
        raise NotImplementedError


def _encode_length(length: int) -> bytes:
    return length.to_bytes(
        8,
        byteorder="big",
        signed=False,
    )


def _encode_bytes(value: bytes) -> bytes:
    return _encode_length(len(value)) + value


def _encode_text(value: str) -> bytes:
    return _encode_bytes(
        value.encode("utf-8")
    )


def canonical_serialize(value: Any) -> bytes:
    """Serialize supported semantic values deterministically.

    Canonical serialization is the basis for semantic identity. Type tags are
    therefore part of the representation and distinct semantic types must not
    collapse to the same byte sequence.
    """

    if isinstance(value, SemanticRecord):
        return canonical_serialize(value.canonical_node())

    if value is None:
        return b"N"

    if isinstance(value, bool):
        return b"B" + (
            b"\x01"
            if value
            else b"\x00"
        )

    if isinstance(value, int):
        return b"I" + _encode_bytes(
            str(value).encode("ascii")
        )

    if isinstance(value, str):
        return b"S" + _encode_text(value)

    if isinstance(value, bytes):
        return b"Y" + _encode_bytes(value)

    if isinstance(value, EntityID):
        return b"E" + _encode_text(value.value)

    if isinstance(value, VersionID):
        return b"V" + _encode_text(value.value)

    if isinstance(value, StateID):
        return b"T" + _encode_text(value.value)

    if isinstance(value, tuple):
        encoded_items = tuple(
            canonical_serialize(item)
            for item in value
        )

        return (
            b"U"
            + _encode_length(len(encoded_items))
            + b"".join(encoded_items)
        )

    if isinstance(value, list):
        encoded_items = tuple(
            canonical_serialize(item)
            for item in value
        )

        return (
            b"L"
            + _encode_length(len(encoded_items))
            + b"".join(encoded_items)
        )

    if isinstance(value, Mapping):
        encoded_items = [
            (
                canonical_serialize(key),
                canonical_serialize(item),
            )
            for key, item in value.items()
        ]

        encoded_items.sort(
            key=lambda item: item[0]
        )

        return (
            b"M"
            + _encode_length(len(encoded_items))
            + b"".join(
                key + item
                for key, item in encoded_items
            )
        )

    raise TypeError(
        "unsupported value for canonical semantic serialization: "
        f"{type(value).__name__}"
    )


def canonicalize(value: Any) -> Any:
    """Convert supported semantic values to immutable deterministic data.

    Canonicalization is idempotent: already-canonical content is returned
    unchanged, so ``canonicalize(canonicalize(x)) == canonicalize(x)``.
    """

    if isinstance(value, CanonicalNode):
        return value

    if isinstance(value, SemanticRecord):
        return value.canonical_node()

    if value is None or isinstance(
        value,
        (bool, int, str),
    ):
        return value

    if isinstance(value, bytes):
        return _node(
            "bytes",
            value.hex(),
        )

    if isinstance(value, EntityID):
        return _node(
            "entity_id",
            value.value,
        )

    if isinstance(value, VersionID):
        return _node(
            "version_id",
            value.value,
        )

    if isinstance(value, StateID):
        return _node(
            "state_id",
            value.value,
        )

    if isinstance(value, tuple):
        return _node(
            "tuple",
            tuple(
                canonicalize(item)
                for item in value
            ),
        )

    if isinstance(value, list):
        return _node(
            "list",
            tuple(
                canonicalize(item)
                for item in value
            ),
        )

    if isinstance(value, Mapping):
        items = [
            (
                canonicalize(key),
                canonicalize(item),
            )
            for key, item in value.items()
        ]

        items.sort(
            key=lambda item: canonical_serialize(item[0])
        )

        return _node(
            "map",
            tuple(items),
        )

    raise TypeError(
        "unsupported value for canonical semantic serialization: "
        f"{type(value).__name__}"
    )
