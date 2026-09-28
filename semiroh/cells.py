"""Mutable cell declarations in semantic program state."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import CanonicalNode, SemanticRecord, _node, canonicalize
from .identity import EntityID
from .state import State
from .values import Value


@dataclass(frozen=True)
class CellDeclaration(SemanticRecord):
    """Declaration of a mutable cell.

    The declaration is semantic program state: a cell's existence, identity,
    type, and initializer contribute to ``StateID``. The content a cell holds
    while the program runs is runtime state and lives in a ``Runtime``.

    ``type`` is an opaque semantic tag. The model compares cell types for
    equality but does not check content against them.
    """

    type: str
    initial: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.type, str) or not self.type:
            raise TypeError(
                "cell type must be a non-empty string"
            )

        object.__setattr__(
            self,
            "initial",
            canonicalize(self.initial),
        )

    def canonical_node(self) -> CanonicalNode:
        return _node(
            "cell",
            (
                self.type,
                self.initial,
            ),
        )


def cell_declaration(value: Value) -> CellDeclaration | None:
    """Return the cell declaration held by a value, if it declares a cell."""

    content = value.content

    if isinstance(content, CanonicalNode) and content[1] == "cell":
        cell_type, initial = content[2]

        return CellDeclaration(
            cell_type,
            initial,
        )

    return None


def cells_of(state: State) -> Mapping[EntityID, CellDeclaration]:
    """Return the mutable cells declared in a state, in canonical order."""

    cells = {}

    for entity in sorted(state.values):
        declaration = cell_declaration(state.values[entity])

        if declaration is not None:
            cells[entity] = declaration

    return MappingProxyType(cells)
