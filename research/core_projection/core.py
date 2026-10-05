"""Candidate semantic core for the projection experiment.

This module is the candidate side of the experiment (charter section 3,
projection_plan.md section 3.1). It must not import ``shear`` and must not reuse
``main``'s algorithms: it is the independent oracle the projection is compared
against.

A candidate state is a finite relational structure::

    Relation = { atom : Atom?, roles : Role -> Sequence<RelationRef> }

Handles (``RelationRef``) are state-local ints that carry no meaning. There is
no universal root.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from types import MappingProxyType
from typing import Iterable, Iterator, Mapping

__all__ = [
    "Atom",
    "CState",
    "Continuity",
    "bisimilar",
    "compose",
    "inverse",
    "isomorphic",
    "isomorphisms",
    "make_continuity",
    "transport",
]

ATOM_TAGS = ("none", "bool", "int", "text", "bytes", "symbol")

_VALUE_TYPES: dict[str, type | None] = {
    "none": None,
    "bool": bool,
    "int": int,
    "text": str,
    "bytes": bytes,
    "symbol": str,
}


@dataclass(frozen=True)
class Atom:
    """Irreducible local content: a tag and a value of that tag's type.

    The tag is part of the atom, so ``Atom("bool", True) != Atom("int", 1)``.
    """

    tag: str
    value: object = None

    def __post_init__(self) -> None:
        if self.tag not in _VALUE_TYPES:
            raise ValueError(f"unknown atom tag {self.tag!r}")

        expected = _VALUE_TYPES[self.tag]

        if expected is None:
            if self.value is not None:
                raise TypeError("a 'none' atom carries no value")
        elif type(self.value) is not expected:
            raise TypeError(
                f"{self.tag!r} atom needs a {expected.__name__}, "
                f"not {type(self.value).__name__}"
            )


Roles = Mapping[str, tuple[int, ...]]


class CState:
    """An immutable finite relational structure.

    ``relations`` maps each handle to ``(atom | None, roles)`` where ``roles``
    maps a role name to the ordered sequence of target handles. A role that is
    present with an empty sequence differs from an absent role. Every target
    must be a handle of the state.
    """

    __slots__ = ("_relations", "_key")

    def __init__(
        self,
        relations: Mapping[int, tuple[Atom | None, Mapping[str, Iterable[int]]]],
    ) -> None:
        built: dict[int, tuple[Atom | None, Roles]] = {}

        for handle, (atom, roles) in relations.items():
            if type(handle) is not int:
                raise TypeError(f"handle {handle!r} is not an int")

            if atom is not None and not isinstance(atom, Atom):
                raise TypeError(f"atom of {handle} is not an Atom or None")

            frozen: dict[str, tuple[int, ...]] = {}

            for name, targets in sorted(roles.items()):
                if not isinstance(name, str) or not name:
                    raise TypeError("role names must be non-empty strings")

                frozen[name] = tuple(targets)

            built[handle] = (atom, MappingProxyType(frozen))

        for handle, (_, roles) in built.items():
            for name, targets in roles.items():
                for target in targets:
                    if target not in built:
                        raise ValueError(
                            f"role {name!r} of {handle} targets absent "
                            f"handle {target!r}"
                        )

        self._relations = MappingProxyType(dict(sorted(built.items())))
        self._key = tuple(
            (handle, atom, tuple(roles.items()))
            for handle, (atom, roles) in self._relations.items()
        )

    @property
    def handles(self) -> tuple[int, ...]:
        return tuple(self._relations)

    def atom(self, handle: int) -> Atom | None:
        return self._relations[handle][0]

    def roles(self, handle: int) -> Roles:
        return self._relations[handle][1]

    def relabel(self, renaming: Mapping[int, int]) -> "CState":
        """Return the same structure under a bijective renaming of handles."""

        if sorted(renaming) != list(self.handles) or len(
            set(renaming.values())
        ) != len(renaming):
            raise ValueError("renaming must be a bijection on the handles")

        return CState({
            renaming[handle]: (
                atom,
                {
                    name: tuple(renaming[t] for t in targets)
                    for name, targets in roles.items()
                },
            )
            for handle, (atom, roles) in self._relations.items()
        })

    def __contains__(self, handle: object) -> bool:
        return handle in self._relations

    def __len__(self) -> int:
        return len(self._relations)

    def __iter__(self) -> Iterator[int]:
        return iter(self._relations)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CState):
            return NotImplemented

        return self._key == other._key

    def __hash__(self) -> int:
        return hash(self._key)

    def __repr__(self) -> str:
        return f"CState({len(self)} handles)"


# ---------------------------------------------------------------------------
# Bisimulation (value equality)
# ---------------------------------------------------------------------------


def bisimilar(left: CState, a: int, right: CState, b: int) -> bool:
    """Whether occurrence ``a`` of ``left`` and ``b`` of ``right`` are equal values.

    Role targets are ordered and labelled, so each occurrence has at most one
    successor per (role, position). Equality is therefore decided exactly by a
    pair worklist over a union-find: pop a pair, skip it if the two sides are
    already merged, otherwise merge them, require equal atoms, role names and
    sequence lengths, and push the corresponding child pairs. No backtracking.
    """

    if a not in left or b not in right:
        raise KeyError("occurrence is not a handle of its state")

    parent: dict[tuple[int, int], tuple[int, int]] = {}

    def find(node: tuple[int, int]) -> tuple[int, int]:
        root = node

        while parent.get(root, root) != root:
            root = parent[root]

        while node != root:
            following = parent[node]
            parent[node] = root
            node = following

        return root

    work = [((0, a), (1, b))]

    while work:
        x, y = work.pop()
        root_x, root_y = find(x), find(y)

        if root_x == root_y:
            continue

        parent[root_x] = root_y

        if left.atom(x[1]) != right.atom(y[1]):
            return False

        left_roles = left.roles(x[1])
        right_roles = right.roles(y[1])

        if left_roles.keys() != right_roles.keys():
            return False

        for name, left_targets in left_roles.items():
            right_targets = right_roles[name]

            if len(left_targets) != len(right_targets):
                return False

            work.extend(
                ((0, s), (1, t))
                for s, t in zip(left_targets, right_targets)
            )

    return True


# ---------------------------------------------------------------------------
# Isomorphism (experimental state identity, charter section 3.11)
# ---------------------------------------------------------------------------


def _shape(state: CState, handle: int) -> tuple:
    return (
        state.atom(handle),
        tuple((name, len(targets)) for name, targets in state.roles(handle).items()),
    )


def _incoming(state: CState) -> dict[int, list[tuple[str, int, int]]]:
    found: dict[int, list[tuple[str, int, int]]] = {h: [] for h in state}

    for handle in state:
        for name, targets in state.roles(handle).items():
            for position, target in enumerate(targets):
                found[target].append((name, position, handle))

    return found


def _refine(
    left: CState,
    right: CState,
) -> tuple[dict[int, int], dict[int, int]] | None:
    """Colour refinement over both states with shared colour names.

    A colour starts as atom plus role signature and is refined by the colours
    of every ordered, labelled out-neighbour and every in-neighbour with its
    (role, position). Returns ``None`` when the colour histograms differ,
    which rules out any isomorphism.
    """

    states = (left, right)
    incoming = (_incoming(left), _incoming(right))
    names: dict[object, int] = {}
    colour: list[dict[int, int]] = [{}, {}]

    for side, state in enumerate(states):
        for handle in state:
            colour[side][handle] = names.setdefault(
                _shape(state, handle), len(names)
            )

    classes = len(names)

    while True:
        names = {}
        refined: list[dict[int, int]] = [{}, {}]

        for side, state in enumerate(states):
            for handle in state:
                signature = (
                    colour[side][handle],
                    tuple(
                        (name, tuple(colour[side][t] for t in targets))
                        for name, targets in state.roles(handle).items()
                    ),
                    tuple(sorted(
                        (name, position, colour[side][source])
                        for name, position, source in incoming[side][handle]
                    )),
                )
                refined[side][handle] = names.setdefault(signature, len(names))

        colour = refined

        if len(names) == classes:
            break

        classes = len(names)

    histogram = [
        sorted(side.values()) for side in colour
    ]

    if histogram[0] != histogram[1]:
        return None

    return colour[0], colour[1]


def isomorphisms(
    left: CState,
    right: CState,
    limit: int | None = None,
) -> Iterator[dict[int, int]]:
    """Enumerate the bijections ``left -> right`` that preserve the structure.

    A bijection of handles qualifies when it preserves atoms, role names, each
    role's target sequence (order and multiplicity) and every target
    (charter section 3.11). Colour refinement prunes candidates; the search
    then individualises one handle at a time and propagates the choice along
    role targets. At most ``limit`` mappings are produced.
    """

    found = _search(left, right)

    if limit is None:
        yield from found
    else:
        yield from islice(found, limit)


def isomorphic(left: CState, right: CState) -> bool:
    """Whether some isomorphism exists, i.e. equal experimental StateIDs."""

    return next(isomorphisms(left, right), None) is not None


def _search(left: CState, right: CState) -> Iterator[dict[int, int]]:
    if len(left) != len(right):
        return

    colours = _refine(left, right)

    if colours is None:
        return

    left_colour, right_colour = colours
    left_class: dict[int, list[int]] = {}
    right_class: dict[int, list[int]] = {}

    for handle in left:
        left_class.setdefault(left_colour[handle], []).append(handle)

    for handle in right:
        right_class.setdefault(right_colour[handle], []).append(handle)

    forward: dict[int, int] = {}
    backward: dict[int, int] = {}

    def assign(h: int, g: int, trail: list[int]) -> bool:
        pending = [(h, g)]

        while pending:
            h, g = pending.pop()

            if h in forward:
                if forward[h] != g:
                    return False

                continue

            if g in backward or left_colour[h] != right_colour[g]:
                return False

            forward[h] = g
            backward[g] = h
            trail.append(h)

            # Equal colours imply equal atom, role names and lengths.
            right_roles = right.roles(g)

            for name, targets in left.roles(h).items():
                pending.extend(zip(targets, right_roles[name]))

        return True

    def undo(trail: list[int]) -> None:
        for h in trail:
            del backward[forward.pop(h)]

    # Handles alone in their colour class are forced.
    for colour, handles in left_class.items():
        if len(handles) == 1 and not assign(
            handles[0], right_class[colour][0], []
        ):
            return

    order = sorted(
        left,
        key=lambda h: (len(left_class[left_colour[h]]), h),
    )

    def pick() -> int | None:
        return next((h for h in order if h not in forward), None)

    def candidates(h: int) -> list[int]:
        return [
            g for g in right_class[left_colour[h]] if g not in backward
        ]

    first = pick()

    if first is None:
        yield dict(forward)
        return

    # Explicit stack of [handle, candidates, next index, trail of the attempt].
    stack: list[list] = [[first, candidates(first), 0, None]]

    while stack:
        frame = stack[-1]
        handle, options = frame[0], frame[1]

        if frame[3] is not None:
            undo(frame[3])
            frame[3] = None

        descended = False

        while frame[2] < len(options):
            option = options[frame[2]]
            frame[2] += 1
            trail: list[int] = []

            if not assign(handle, option, trail):
                undo(trail)
                continue

            frame[3] = trail
            following = pick()

            if following is None:
                yield dict(forward)
                undo(trail)
                frame[3] = None
                continue

            stack.append([following, candidates(following), 0, None])
            descended = True
            break

        if not descended:
            stack.pop()


# ---------------------------------------------------------------------------
# Continuity
# ---------------------------------------------------------------------------

# A key present is Known(set); an absent key is Unknown. Known(frozenset())
# is explicit disappearance.
Continuity = Mapping[int, frozenset[int]]


def make_continuity(
    pairs: Mapping[int, Iterable[int]],
) -> dict[int, frozenset[int]]:
    """Build a continuity from ``source -> destinations`` (Known entries)."""

    return {source: frozenset(targets) for source, targets in pairs.items()}


def compose(first: Continuity, second: Continuity) -> dict[int, frozenset[int]]:
    """Compose two continuities (direction review section 5).

    With ``K1, K2`` the known sources and ``M1, M2`` the maps::

        K = { s in K1 | M1[s] subset of K2 }
        result = K <: M1.M2

    Unknown absorbs, explicit disappearance drops out, split branches union,
    and a split with any Unknown branch is Unknown. The two continuities must
    already share one handle space for the middle state; see ``transport``.
    """

    return {
        source: frozenset(
            final for middle in middles for final in second[middle]
        )
        for source, middles in first.items()
        if all(middle in second for middle in middles)
    }


def inverse(renaming: Mapping[int, int]) -> dict[int, int]:
    """Invert an injective renaming, such as an isomorphism."""

    result = {target: source for source, target in renaming.items()}

    if len(result) != len(renaming):
        raise ValueError("renaming is not injective")

    return result


def transport(
    continuity: Continuity,
    renaming: Mapping[int, int],
    *,
    sources: bool = False,
    destinations: bool = False,
) -> dict[int, frozenset[int]]:
    """Rename the source and/or destination handles of a continuity.

    ``renaming`` is typically an isomorphism between two states. Unknown stays
    Unknown and a Known set keeps its size and emptiness.
    """

    def rename(handle: int) -> int:
        return renaming[handle]

    renamed: dict[int, frozenset[int]] = {}

    for source, targets in continuity.items():
        key = rename(source) if sources else source

        if key in renamed:
            raise ValueError("renaming merged two sources")

        renamed[key] = (
            frozenset(rename(t) for t in targets) if destinations else targets
        )

    return renamed
