"""Semantic and identity comparisons."""

from __future__ import annotations

from .canonical import canonical_serialize
from .values import Value


def semantic_equal(
    left: Value,
    right: Value,
) -> bool:
    """Compare semantic content, independently of entity identity.

    Comparison uses canonical serialization so that distinct semantic types
    that Python treats as equal (for example ``True`` and ``1``) remain
    distinct.
    """

    return canonical_serialize(left.content) == canonical_serialize(
        right.content
    )


def same_entity(
    left: Value,
    right: Value,
) -> bool:
    """Compare conceptual entity identity."""

    return left.entity == right.entity


def same_version(
    left: Value,
    right: Value,
) -> bool:
    """Compare exact semantic versions."""

    return left.version_id == right.version_id
