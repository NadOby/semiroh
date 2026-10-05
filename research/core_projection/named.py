"""Candidate revision 1: named roots (charter section 3.12).

This module is the candidate side of the experiment, like ``core.py``, and
like it must not import ``shear``. It is additive: ``core.py`` is the record
of the frozen candidate and is only reused here, never changed.

A state is ``(relations, bindings)``::

    Relation = { atom : Atom?, roles : Role -> Sequence<Target> }
    Target   = Contained(handle) | Named(name)
    bindings : Name -> handle

Every ``Named`` target resolves to a binding of the same state, and
``Contained`` targets form an acyclic graph. Value equality is bisimulation
over ``Contained`` targets with ``Named`` targets equal iff their names are
equal; state identity is an isomorphism that fixes names; continuity is over
names with the unchanged composition rule.

The checks reuse ``core.py`` through an *encoding* of a state as a ``CState``
(``NState.encoding``). The encoding is injective and is built so that the
reused algorithms decide exactly the revised relations:

* every referenced name becomes one nullary leaf, atom ``symbol "name:<n>"``
  (one leaf per distinct name, not one per occurrence, so a name referenced
  ``k`` times adds no ``k!`` symmetries). The leaf has no edge to the bound
  root: bisimulation never looks through a name, or ``NAMED`` would silently
  become ``STRUCT``;
* every binding becomes a relation, atom ``symbol "binding:<n>"``, with one
  role ``root`` to the bound handle (identity must preserve bindings);
* content atoms that start with a reserved prefix are rejected when a state
  is built, so the encoding cannot be confused with content.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from types import MappingProxyType
from typing import Iterable, Iterator, Mapping

from core_projection import core
from core_projection.core import Atom, CState

__all__ = [
    "Contained",
    "ContainmentCycle",
    "Continuity",
    "Name",
    "Named",
    "NState",
    "RESERVED_PREFIXES",
    "ReservedAtom",
    "Target",
    "check_continuity",
    "compose",
    "equal",
    "isomorphic",
    "isomorphisms",
    "make_continuity",
]

NAME_PREFIX = "name:"
BINDING_PREFIX = "binding:"
RESERVED_PREFIXES = (NAME_PREFIX, BINDING_PREFIX)


class ContainmentCycle(ValueError):
    """``Contained`` targets form a cycle; cycles may pass through names only."""


class ReservedAtom(ValueError):
    """A content atom uses a prefix reserved for the encoding."""


@dataclass(frozen=True, order=True)
class Name:
    """A root's name. Names are part of values and of state identity."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or not self.value:
            raise TypeError("a name is a non-empty string")


@dataclass(frozen=True)
class Contained:
    """A target that is part of the relation's own content."""

    handle: int


@dataclass(frozen=True)
class Named:
    """A target that is the named root, compared by name."""

    name: Name


Target = Contained | Named

Roles = Mapping[str, tuple[Target, ...]]


def is_reserved(atom: Atom | None) -> bool:
    return (
        atom is not None
        and atom.tag == "symbol"
        and atom.value.startswith(RESERVED_PREFIXES)
    )


class NState:
    """An immutable state with named roots.

    ``relations`` maps each handle to ``(atom, roles)``; a role is an ordered
    sequence of ``Contained`` or ``Named`` targets, and a present empty role
    differs from an absent one. ``bindings`` maps names to handles. Every
    ``Contained`` target must be a handle, every ``Named`` target a bound
    name, and every binding a handle of the state. Acyclicity of containment
    is *checked on use* (``require_acyclic``), so that a projection can count
    cyclic states (observable C0) instead of crashing on them.
    """

    __slots__ = ("_relations", "_bindings", "_key", "_encoding", "_cycle")

    def __init__(
        self,
        relations: Mapping[int, tuple[Atom | None, Mapping[str, Iterable[Target]]]],
        bindings: Mapping[Name, int] = MappingProxyType({}),
    ) -> None:
        built: dict[int, tuple[Atom | None, Roles]] = {}

        for handle, (atom, roles) in relations.items():
            if type(handle) is not int:
                raise TypeError(f"handle {handle!r} is not an int")

            if atom is not None and not isinstance(atom, Atom):
                raise TypeError(f"atom of {handle} is not an Atom or None")

            if is_reserved(atom):
                raise ReservedAtom(
                    f"atom {atom.value!r} of {handle} starts with a reserved prefix"
                )

            frozen: dict[str, tuple[Target, ...]] = {}

            for role, targets in sorted(roles.items()):
                if not isinstance(role, str) or not role:
                    raise TypeError("role names must be non-empty strings")

                sequence = tuple(targets)

                if not all(isinstance(t, (Contained, Named)) for t in sequence):
                    raise TypeError(f"role {role!r} of {handle} has a non-target")

                frozen[role] = sequence

            built[handle] = (atom, MappingProxyType(frozen))

        bound: dict[Name, int] = {}

        for name, handle in bindings.items():
            if not isinstance(name, Name):
                raise TypeError(f"binding key {name!r} is not a Name")

            if handle not in built:
                raise ValueError(f"name {name.value!r} is bound to absent handle {handle!r}")

            bound[name] = handle

        for handle, (_, roles) in built.items():
            for role, targets in roles.items():
                for target in targets:
                    if isinstance(target, Contained) and target.handle not in built:
                        raise ValueError(
                            f"role {role!r} of {handle} contains absent handle "
                            f"{target.handle!r}"
                        )

                    if isinstance(target, Named) and target.name not in bound:
                        raise ValueError(
                            f"role {role!r} of {handle} names unbound "
                            f"{target.name.value!r}"
                        )

        self._relations = MappingProxyType(dict(sorted(built.items())))
        self._bindings = MappingProxyType(dict(sorted(bound.items())))
        self._key = (
            tuple(
                (handle, atom, tuple(roles.items()))
                for handle, (atom, roles) in self._relations.items()
            ),
            tuple(self._bindings.items()),
        )
        self._encoding: CState | None = None
        self._cycle: tuple[int, ...] | None | bool = False  # False: not computed

    # -- access ---------------------------------------------------------

    @property
    def handles(self) -> tuple[int, ...]:
        return tuple(self._relations)

    @property
    def bindings(self) -> Mapping[Name, int]:
        return self._bindings

    def atom(self, handle: int) -> Atom | None:
        return self._relations[handle][0]

    def roles(self, handle: int) -> Roles:
        return self._relations[handle][1]

    def relabel(self, renaming: Mapping[int, int]) -> "NState":
        """The same state under a bijective renaming of handles (names stay)."""

        if sorted(renaming) != list(self.handles) or len(set(renaming.values())) != len(renaming):
            raise ValueError("renaming must be a bijection on the handles")

        def rename(target: Target) -> Target:
            return Contained(renaming[target.handle]) if isinstance(target, Contained) else target

        return NState(
            {
                renaming[handle]: (
                    atom,
                    {role: tuple(rename(t) for t in targets) for role, targets in roles.items()},
                )
                for handle, (atom, roles) in self._relations.items()
            },
            {name: renaming[handle] for name, handle in self._bindings.items()},
        )

    def __contains__(self, handle: object) -> bool:
        return handle in self._relations

    def __len__(self) -> int:
        return len(self._relations)

    def __iter__(self) -> Iterator[int]:
        return iter(self._relations)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NState):
            return NotImplemented

        return self._key == other._key

    def __hash__(self) -> int:
        return hash(self._key)

    def __repr__(self) -> str:
        return f"NState({len(self)} handles, {len(self._bindings)} names)"

    # -- containment ----------------------------------------------------

    def containment_cycle(self) -> tuple[int, ...] | None:
        """A cycle of ``Contained`` targets as a handle path, or ``None``."""

        if self._cycle is False:
            self._cycle = _find_cycle(self)

        return self._cycle  # type: ignore[return-value]

    def require_acyclic(self) -> None:
        cycle = self.containment_cycle()

        if cycle is not None:
            raise ContainmentCycle(
                "contained targets form a cycle through handles "
                + " -> ".join(map(str, cycle))
            )

    # -- encoding -------------------------------------------------------

    def encoding(self) -> CState:
        """This state as a ``CState`` (see the module docstring).

        Original handles keep their numbers; name leaves and binding
        relations take the numbers above them, in sorted name order.
        """

        if self._encoding is None:
            self._encoding = _encode(self)

        return self._encoding


def _find_cycle(state: NState) -> tuple[int, ...] | None:
    colour: dict[int, int] = {}  # absent: unseen, 1: on the path, 2: done

    for start in state:
        if start in colour:
            continue

        path = [start]
        iterators = [_contained(state, start)]
        colour[start] = 1

        while path:
            advanced = False

            for child in iterators[-1]:
                if colour.get(child) == 1:
                    return tuple(path[path.index(child):]) + (child,)

                if child not in colour:
                    colour[child] = 1
                    path.append(child)
                    iterators.append(_contained(state, child))
                    advanced = True
                    break

            if not advanced:
                colour[path.pop()] = 2
                iterators.pop()

    return None


def _contained(state: NState, handle: int) -> Iterator[int]:
    for targets in state.roles(handle).values():
        for target in targets:
            if isinstance(target, Contained):
                yield target.handle


def _encode(state: NState) -> CState:
    base = max(state.handles, default=-1) + 1
    referenced = sorted({
        target.name
        for handle in state
        for targets in state.roles(handle).values()
        for target in targets
        if isinstance(target, Named)
    })
    leaf = {name: base + index for index, name in enumerate(referenced)}
    binding = {
        name: base + len(referenced) + index
        for index, name in enumerate(state.bindings)
    }
    relations: dict[int, tuple[Atom | None, dict[str, tuple[int, ...]]]] = {}

    for handle in state:
        relations[handle] = (
            state.atom(handle),
            {
                role: tuple(
                    t.handle if isinstance(t, Contained) else leaf[t.name]
                    for t in targets
                )
                for role, targets in state.roles(handle).items()
            },
        )

    for name, handle in leaf.items():
        relations[handle] = (Atom("symbol", NAME_PREFIX + name.value), {})

    for name, handle in binding.items():
        relations[handle] = (
            Atom("symbol", BINDING_PREFIX + name.value),
            {"root": (state.bindings[name],)},
        )

    return CState(relations)


# ---------------------------------------------------------------------------
# value equality
# ---------------------------------------------------------------------------


def equal(left: NState, a: int, right: NState, b: int) -> bool:
    """Whether ``a`` of ``left`` and ``b`` of ``right`` are equal values.

    Bisimulation over ``Contained`` targets; ``Named`` targets are equal iff
    their names are. Containment must be acyclic in both states.
    """

    left.require_acyclic()
    right.require_acyclic()

    return core.bisimilar(left.encoding(), a, right.encoding(), b)


# ---------------------------------------------------------------------------
# state identity
# ---------------------------------------------------------------------------


def isomorphisms(
    left: NState,
    right: NState,
    limit: int | None = None,
) -> Iterator[dict[int, int]]:
    """The bijections of handles ``left -> right`` that preserve the structure.

    A bijection qualifies when it preserves atoms, role names, sequences,
    ``Contained`` targets, ``Named`` targets (names are *not* renamed) and
    bindings (each name binds corresponding handles). Containment must be
    acyclic in both states. At most ``limit`` mappings are produced.
    """

    left.require_acyclic()
    right.require_acyclic()
    # Name leaves and binding relations are forced by their unique atoms, so
    # restricting an encoded isomorphism to the original handles loses nothing
    # and repeats nothing.
    found = (
        {h: g for h, g in mapping.items() if h in left}
        for mapping in core.isomorphisms(left.encoding(), right.encoding())
    )

    return islice(found, limit) if limit is not None else found


def isomorphic(left: NState, right: NState) -> bool:
    """Whether the states have equal experimental identity (charter section 3.12)."""

    return next(isomorphisms(left, right), None) is not None


# ---------------------------------------------------------------------------
# continuity over names
# ---------------------------------------------------------------------------

# A name present is Known(set of names); an absent name is Unknown.
Continuity = Mapping[Name, frozenset[Name]]


def make_continuity(pairs: Mapping[Name, Iterable[Name]]) -> dict[Name, frozenset[Name]]:
    """Build a continuity from ``source -> destinations`` (Known entries)."""

    return {source: frozenset(targets) for source, targets in pairs.items()}


def check_continuity(continuity: Continuity, source: NState, destination: NState) -> None:
    """Every source name is bound in ``source``, every destination in ``destination``."""

    for name, targets in continuity.items():
        if name not in source.bindings:
            raise ValueError(f"source name {name.value!r} is not bound in the source state")

        for target in targets:
            if target not in destination.bindings:
                raise ValueError(
                    f"destination name {target.value!r} is not bound in the destination state"
                )


def compose(first: Continuity, second: Continuity) -> dict[Name, frozenset[Name]]:
    """Compose two continuities by name; the rule is ``core.compose`` unchanged.

    With ``K1, K2`` the known sources and ``M1, M2`` the maps,
    ``K = { s in K1 | M1[s] subset of K2 }`` and the result is ``K <: M1.M2``.
    The steps join exactly where the first step's destination names are the
    second step's source names; no isomorphism between middle states is
    involved.
    """

    return core.compose(first, second)
