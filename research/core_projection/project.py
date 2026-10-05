"""The projection pi: main states into the candidate core.

Plan section 3.2. This module reads ``shear`` (the candidate side, ``core.py``,
does not). ``project`` turns a ``main`` ``State`` in graph form into a
``CState`` plus the view that names each entity's root occurrence;
``decode`` is the inverse on content (the data-fragment interpretation for H2).

Two modes treat the ``EntityID`` inside content differently:

* ``STRUCT`` (charter-faithful): a reference becomes a direct role target to
  the referenced entity's root handle.
* ``REF`` (control only): a reference becomes a nullary ``symbol`` atom holding
  the ``EntityID`` string, which puts ``EntityID`` into value.

A third mode, ``NAMED`` (revision 1, charter section 3.12), lives in
``project_named.py``; ``project`` and ``decode`` dispatch to it.

Nothing here adds candidate semantics; where the plan's table is silent the
choice is recorded in a docstring and reported as a deviation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Mapping

from shear.canonical import CanonicalNode, canonical_serialize
from shear.identity import EntityID
from shear.relations import Relation
from shear.state import State
from shear.values import Value

from core_projection.core import Atom, CState

if TYPE_CHECKING:
    from core_projection.project_named import NamedProjection

__all__ = [
    "Gap",
    "Lost",
    "Mode",
    "Projection",
    "ProjectionGap",
    "decode",
    "normalize_arity",
    "project",
    "rename_entities",
]


class ProjectionGap(Exception):
    """The input has no representation under the plan's projection rules."""


class Mode(Enum):
    STRUCT = "struct"
    REF = "ref"
    NAMED = "named"  # revision 1; see project_named.py


@dataclass(frozen=True)
class Gap:
    """An identity that sits inside content and was flattened to an atom."""

    entity: EntityID
    kind: str  # "version_id" or "state_id"


@dataclass(frozen=True)
class Lost:
    """What ``decode`` returns for a flattened ``VersionID`` or ``StateID``."""

    value: str


@dataclass(frozen=True)
class Projection:
    """``cstate`` plus the view and the handle of each ownership edge's relation."""

    mode: Mode
    cstate: CState
    view: Mapping[EntityID, int]
    ownership_handles: Mapping[tuple[EntityID, EntityID], int]
    gaps: tuple[Gap, ...]

    def entity_of(self, handle: int) -> EntityID | None:
        """The entity whose root occurrence is ``handle``, if any."""

        for entity, root in self.view.items():
            if root == handle:
                return entity

        return None


def _node(kind: str, payload: Any) -> CanonicalNode:
    return CanonicalNode(("__type__", kind, payload))


# ---------------------------------------------------------------------------
# project
# ---------------------------------------------------------------------------


class _Builder:
    def __init__(self, state: State, mode: Mode) -> None:
        self.mode = mode
        # Root handles first, in sorted EntityID order; interior handles after.
        self.view = {
            entity: handle
            for handle, entity in enumerate(sorted(state.values))
        }
        self.next = len(self.view)
        self.relations: dict[int, tuple[Atom | None, dict[str, tuple[int, ...]]]] = {}
        self.gaps: list[Gap] = []
        self.entity: EntityID | None = None

    def fresh(self) -> int:
        handle = self.next
        self.next += 1

        return handle

    def add(self, handle: int, atom: Atom | None, roles: dict[str, tuple[int, ...]]) -> None:
        self.relations[handle] = (atom, roles)

    def reference(self, node: CanonicalNode) -> int:
        name = node[2]

        if self.mode is Mode.REF:
            handle = self.fresh()
            self.add(handle, Atom("symbol", name), {})

            return handle

        target = EntityID(name)

        if target not in self.view:
            raise ProjectionGap(
                f"{self.entity.value} refers to absent entity {name}"
            )

        return self.view[target]

    def endpoint(self, node: Any) -> tuple[int, ...]:
        """A relation role's targets; a single endpoint is a one-element sequence."""

        if isinstance(node, CanonicalNode) and node[1] == "entity_id":
            return (self.reference(node),)

        if isinstance(node, CanonicalNode) and node[1] == "tuple" and all(
            isinstance(item, CanonicalNode) and item[1] == "entity_id"
            for item in node[2]
        ):
            return tuple(self.reference(item) for item in node[2])

        raise ProjectionGap("relation endpoint is not an entity or a tuple of entities")

    def build(self, content: Any, handle: int | None = None) -> int:
        """Project ``content`` to a subtree and return its root handle.

        A ``handle`` is given for an entity's own root. An ``entity_id`` node
        elsewhere returns the referenced root (``STRUCT``) or a fresh atom
        (``REF``) instead of allocating a relation.
        """

        is_reference = isinstance(content, CanonicalNode) and content[1] == "entity_id"

        if is_reference:
            if handle is not None and self.mode is Mode.STRUCT:
                raise ProjectionGap(
                    f"{self.entity.value} is a bare reference; STRUCT has "
                    "no relation to put it in"
                )

            if handle is None:
                return self.reference(content)

        h = self.fresh() if handle is None else handle

        if is_reference:
            self.add(h, Atom("symbol", content[2]), {})
        elif content is None:
            self.add(h, Atom("none"), {})
        elif type(content) is bool:
            self.add(h, Atom("bool", content), {})
        elif type(content) is int:
            self.add(h, Atom("int", content), {})
        elif type(content) is str:
            self.add(h, Atom("text", content), {})
        elif type(content) is bytes:
            self.add(h, Atom("bytes", content), {})
        elif isinstance(content, CanonicalNode):
            self.node(h, content[1], content[2])
        elif type(content) in (tuple, list):
            # Raw Python sequences occur inside node payloads (cell and
            # constraint records). They are not ``tuple`` nodes, so they get
            # their own atoms; the plan's table does not cover them.
            name = "raw_tuple" if type(content) is tuple else "raw_list"
            items = tuple(self.build(item) for item in content)
            self.add(h, Atom("symbol", name), {"items": items})
        else:
            raise ProjectionGap(f"unsupported content type {type(content).__name__}")

        return h

    def node(self, h: int, kind: str, payload: Any) -> None:
        if kind == "bytes":
            self.add(h, Atom("bytes", bytes.fromhex(payload)), {})
        elif kind in ("tuple", "list"):
            items = tuple(self.build(item) for item in payload)
            self.add(h, Atom("symbol", kind), {"items": items})
        elif kind == "map":
            entries = []

            for key, value in payload:
                entry = self.fresh()
                key_handle = self.build(key)
                value_handle = self.build(value)
                self.add(
                    entry,
                    Atom("symbol", "entry"),
                    {"key": (key_handle,), "value": (value_handle,)},
                )
                entries.append(entry)

            self.add(h, Atom("symbol", "map"), {"entries": tuple(entries)})
        elif kind == "relation":
            relation_kind, roles, relation_payload = payload

            if any(name == "payload" for name, _ in roles):
                raise ProjectionGap(
                    f"relation {relation_kind!r} has a role named 'payload'"
                )

            built = {name: self.endpoint(endpoint) for name, endpoint in roles}

            if relation_payload is not None:
                built["payload"] = (self.build(relation_payload),)

            self.add(h, Atom("symbol", f"relation:{relation_kind}"), built)
        elif kind in ("version_id", "state_id"):
            self.gaps.append(Gap(self.entity, kind))
            self.add(h, Atom("symbol", payload), {})
        else:
            self.add(h, Atom("symbol", kind), {"payload": (self.build(payload),)})


def project(state: State, mode: Mode) -> "Projection | NamedProjection":
    """Project a graph-form ``main`` state into the candidate core.

    Each entity's content becomes a fresh subtree (no sharing between entities,
    no hash-consing) rooted at ``view[entity]``. Ownership becomes one ``owns``
    relation per ownership edge (role ``owner`` to the owner's root, role
    ``owned`` to the child's root), inside the state. Handle allocation follows
    sorted ``EntityID`` order and nothing else depends on the spelling.

    One relation per edge corrects the plan, which had one per owner listing
    its children "in main order": ``normalize_ownership`` stores children as
    ``sorted(set(...))``, so the order is not semantic and a sequence would
    let ``EntityID`` spelling into the projected structure.
    """

    if mode is Mode.NAMED:
        from core_projection.project_named import project_named

        return project_named(state)

    builder = _Builder(state, mode)

    for entity in sorted(state.values):
        builder.entity = entity
        builder.build(state.values[entity].content, builder.view[entity])

    ownership_handles: dict[tuple[EntityID, EntityID], int] = {}

    for owner in sorted(state.ownership):
        for child in state.ownership[owner]:
            handle = builder.fresh()
            ownership_handles[(owner, child)] = handle
            builder.add(
                handle,
                Atom("symbol", "owns"),
                {"owner": (builder.view[owner],), "owned": (builder.view[child],)},
            )

    return Projection(
        mode=mode,
        cstate=CState(builder.relations),
        view=dict(builder.view),
        ownership_handles=ownership_handles,
        gaps=tuple(builder.gaps),
    )


# ---------------------------------------------------------------------------
# decode
# ---------------------------------------------------------------------------


def decode(projection: "Projection | NamedProjection") -> dict[EntityID, Any]:
    """Recover each entity's canonical content from its root occurrence.

    The inverse on content. Two losses are inherent to the projection and are
    not hidden: a single endpoint and a one-element tuple project identically,
    so a one-element role decodes as a single endpoint (exact decoding differs
    from the input exactly there; see ``normalize_arity``); and a flattened
    ``VersionID``/``StateID`` decodes to ``Lost``.
    """

    if projection.mode is Mode.NAMED:
        from core_projection.project_named import decode_named

        return decode_named(projection)

    cstate = projection.cstate
    struct = projection.mode is Mode.STRUCT
    entity_at = {root: entity for entity, root in projection.view.items()}

    def endpoint_entity(target: int) -> EntityID:
        if struct:
            if target not in entity_at:
                raise ValueError(f"{target} is not an entity root")

            return entity_at[target]

        return EntityID(cstate.atom(target).value)

    def value(h: int, top: bool = False) -> Any:
        if struct and not top and h in entity_at:
            return _node("entity_id", entity_at[h].value)

        atom = cstate.atom(h)
        roles = cstate.roles(h)

        if atom is None:
            raise ValueError(f"occurrence {h} has no atom")

        if atom.tag in ("none", "bool", "int", "text"):
            return atom.value

        if atom.tag == "bytes":
            return _node("bytes", atom.value.hex())

        name = atom.value

        if not roles and not name.startswith("relation:"):
            # A flattened identity (STRUCT) or a reference (REF).
            return Lost(name) if struct else _node("entity_id", name)

        if name in ("tuple", "list"):
            return _node(name, tuple(value(i) for i in roles["items"]))

        if name == "raw_tuple":
            return tuple(value(i) for i in roles["items"])

        if name == "raw_list":
            return [value(i) for i in roles["items"]]

        if name == "map":
            pairs = []

            for entry in roles["entries"]:
                parts = cstate.roles(entry)
                pairs.append((value(parts["key"][0]), value(parts["value"][0])))

            return _node("map", tuple(pairs))

        if name.startswith("relation:"):
            endpoints = {}

            for role, targets in roles.items():
                if role == "payload":
                    continue

                entities = tuple(endpoint_entity(t) for t in targets)
                endpoints[role] = entities[0] if len(entities) == 1 else entities

            payload = value(roles["payload"][0]) if "payload" in roles else None

            return Relation(name[len("relation:"):], endpoints, payload).canonical_node()

        return _node(name, value(roles["payload"][0]))

    return {
        entity: value(root, top=True)
        for entity, root in projection.view.items()
    }


def normalize_arity(content: Any) -> Any:
    """Rewrite every single relation endpoint as a one-element tuple.

    ``decode(project(S))`` equals ``S`` exactly except for this distinction, which
    the projection collapses by rule (plan section 3.2). Comparing both sides
    after ``normalize_arity`` is the "modulo arity" comparison.
    """

    if isinstance(content, CanonicalNode):
        kind, payload = content[1], content[2]

        if kind == "relation":
            relation_kind, roles, relation_payload = payload

            return _node(
                "relation",
                (
                    relation_kind,
                    tuple(
                        (
                            role,
                            _node("tuple", (endpoint,))
                            if isinstance(endpoint, CanonicalNode)
                            and endpoint[1] == "entity_id"
                            else endpoint,
                        )
                        for role, endpoint in roles
                    ),
                    normalize_arity(relation_payload),
                ),
            )

        if kind in ("entity_id", "version_id", "state_id", "bytes"):
            return content

        return _node(kind, normalize_arity(payload))

    if type(content) is tuple:
        return tuple(normalize_arity(item) for item in content)

    if type(content) is list:
        return [normalize_arity(item) for item in content]

    return content


def rename_entities(
    state: State,
    rename: Callable[[EntityID], EntityID],
) -> State:
    """A ``main`` state with every ``EntityID`` consistently renamed.

    Entity keys, every ``entity_id`` node in content and the ownership relation
    are renamed; role names, kinds and other strings are not ``EntityID``s and
    stay. ``State`` re-sorts ownership children by the new names, and map entries
    are re-sorted by key as ``canonicalize`` would, so a renaming that changes
    the sort order changes the order ``main`` itself would have built.
    """

    def rewrite(content: Any) -> Any:
        if isinstance(content, CanonicalNode):
            kind, payload = content[1], content[2]

            if kind == "entity_id":
                return _node("entity_id", rename(EntityID(payload)).value)

            if kind in ("version_id", "state_id", "bytes"):
                return content

            if kind == "map":
                # main sorts entries by the canonical bytes of the key, so a
                # renamed key can change the order main would have built.
                pairs = [(rewrite(key), rewrite(value)) for key, value in payload]
                pairs.sort(key=lambda pair: canonical_serialize(pair[0]))

                return _node(kind, tuple(pairs))

            return _node(kind, rewrite(payload))

        if type(content) is tuple:
            return tuple(rewrite(item) for item in content)

        if type(content) is list:
            return [rewrite(item) for item in content]

        return content

    return State.create(
        {
            rename(entity): Value(rename(entity), rewrite(value.content))
            for entity, value in state.values.items()
        },
        {
            rename(owner): tuple(rename(child) for child in children)
            for owner, children in state.ownership.items()
        },
    )
