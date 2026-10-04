"""Mutable cell declarations in semantic program state."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import (
    CanonicalNode,
    SemanticRecord,
    _node,
    canonical_serialize,
    canonicalize,
)
from .constraints import Constraint
from .identity import EntityID
from .state import State
from .values import Value


@dataclass(frozen=True, eq=False)
class CellDeclaration(SemanticRecord):
    """Declaration of a mutable cell.

    The declaration is semantic program state: a cell's existence, identity,
    constraint, and initial content contribute to ``StateID``. The content a
    cell holds while the program runs is runtime state and lives in a
    ``Runtime``.

    The constraint is the cell's type: content must satisfy it. Program state
    is pure data, so declaring a cell does not evaluate the constraint; a
    runtime checks the initial content when it loads a version, and checks
    every write.
    """

    constraint: Constraint
    initial: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.constraint, Constraint):
            raise TypeError(
                "cell constraint must be a Constraint"
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
                self.constraint.canonical_node(),
                self.initial,
            ),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CellDeclaration):
            return NotImplemented

        return canonical_serialize(self) == canonical_serialize(other)

    def __hash__(self) -> int:
        return hash(canonical_serialize(self))


def cell_declaration(value: Value) -> CellDeclaration | None:
    """Return the cell declaration held by a value, if it declares a cell."""

    content = value.content

    if isinstance(content, CanonicalNode) and content[1] == "cell":
        constraint, initial = content[2]

        return CellDeclaration(
            Constraint.from_content(constraint),
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
