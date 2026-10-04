"""Shared construction helper for canary corpus programs.

Not part of the corpus data format itself (docs/corpus.md section 2); it
just avoids repeating the ``State``/``Value`` plumbing in every example
module.
"""

from __future__ import annotations

from typing import Any, Mapping

from .. import EntityID, State, Value


def program(entities: Mapping[EntityID, Any]) -> State:
    """Build a State from a mapping of entity to semantic content."""

    return State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    })
