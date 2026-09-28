"""Runtime state: loaded versions, mutable cell content, and holds.

Program states are immutable semantic values. A ``Runtime`` is the mutable
runtime state of one running program: the content of its mutable cells and
the record of what depends on which loaded version.

Ownership follows activation_model.md section 7: the runtime root owns the
loaded versions, and each version owns the content of its cells. Holds record
that running code or runtime-held references depend on a version.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from .canonical import canonicalize
from .cells import cells_of
from .identity import EntityID, StateID
from .references import CrossStateReference, Reference
from .state import State


class CellError(ValueError):
    """A cell operation named an entity that is not a mutable cell."""


class Version:
    """A program state loaded into a runtime.

    A version is owned by the runtime root and owns the content of its
    mutable cells. Cell content is runtime state: writing it never changes the
    version's program state or ``StateID``.
    """

    def __init__(self, state: State) -> None:
        self._state = state
        self._cells: dict[EntityID, Any] = {
            entity: declaration.initial
            for entity, declaration in cells_of(state).items()
        }
        self._holds: set[Hold] = set()

    @property
    def state(self) -> State:
        return self._state

    @property
    def id(self) -> StateID:
        return self._state.id

    @property
    def cells(self) -> Mapping[EntityID, Any]:
        """Read-only view of current cell content."""

        return MappingProxyType(self._cells)

    @property
    def holds(self) -> frozenset[Hold]:
        """Holds currently recorded on this version."""

        return frozenset(self._holds)

    def __repr__(self) -> str:
        return f"Version({self.id.value[:12]}, holds={len(self._holds)})"


class Hold:
    """Runtime-internal record that something depends on a version.

    A hold is deliberately narrower than a borrow: it covers a whole version,
    it is tracked dynamically by the runtime, and it has no lifetimes,
    aliasing rules, or presence in types.
    """

    def __init__(self, version: Version) -> None:
        self._version = version
        self._released = False
        version._holds.add(self)

    @property
    def version(self) -> Version:
        return self._version

    @property
    def released(self) -> bool:
        return self._released

    def release(self) -> None:
        if self._released:
            raise ValueError("hold is already released")

        self._version._holds.discard(self)
        self._released = True


class Frame(Hold):
    """Simulated frame executing the code of an entity in a version."""

    def __init__(self, version: Version, entity: EntityID) -> None:
        super().__init__(version)
        self._entity = entity

    @property
    def entity(self) -> EntityID:
        return self._entity


class KeptReference(Hold):
    """A reference held by runtime state, holding the version it points into."""

    def __init__(self, version: Version, reference: Reference) -> None:
        super().__init__(version)
        self._reference = reference

    @property
    def reference(self) -> Reference:
        return self._reference


class Runtime:
    """Mutable runtime state of one running program.

    The runtime root owns the loaded versions. Until activation is modelled,
    the only loaded version is the active one, created from the initial
    program state with every cell set to its declared initial content.
    """

    def __init__(self, state: State) -> None:
        self._active = Version(state)
        self._versions: list[Version] = [self._active]

    @property
    def active(self) -> Version:
        return self._active

    @property
    def versions(self) -> tuple[Version, ...]:
        """Loaded versions owned by the runtime root, active first."""

        return tuple(self._versions)

    def _active_cell(self, cell: EntityID) -> None:
        if not self._active.state.contains(cell):
            raise KeyError(
                f"{cell.value} is absent from {self._active.id.value}"
            )

        if cell not in self._active._cells:
            raise CellError(f"{cell.value} is not a mutable cell")

    def read(self, cell: EntityID) -> Any:
        """Return the current content of a cell in the active version."""

        self._active_cell(cell)

        return self._active._cells[cell]

    def write(self, cell: EntityID, content: Any) -> None:
        """Replace the content of a cell in the active version in place.

        The content is canonicalized, so later changes to the supplied object
        do not affect the cell. Program state and ``StateID`` are unchanged.
        """

        self._active_cell(cell)
        self._active._cells[cell] = canonicalize(content)

    def enter(self, entity: EntityID) -> Frame:
        """Start a simulated frame executing code of an entity."""

        if not self._active.state.contains(entity):
            raise KeyError(
                f"{entity.value} is absent from {self._active.id.value}"
            )

        return Frame(self._active, entity)

    def keep(self, reference: Reference) -> KeptReference:
        """Hold a reference in runtime state.

        The reference must resolve against a loaded version, which it then
        holds.
        """

        for version in self._versions:
            if version.id == reference.state:
                version.state.resolve(reference)
                return KeptReference(version, reference)

        raise CrossStateReference(
            f"reference belongs to {reference.state.value}, "
            f"which is not loaded in this runtime"
        )
