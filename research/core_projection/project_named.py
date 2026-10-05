"""The projection into the revised candidate: ``Mode.NAMED`` (revision plan section 4.2).

The content table is ``project.py``'s, unchanged: ``_NamedBuilder`` is the
``REF`` builder, which already puts a fresh nullary occurrence wherever
content refers to an entity. Here each such occurrence is recorded and then
replaced by a ``Named`` target, so content, handle allocation and gaps follow
one table in all three modes. What is new:

* an ``entity_id`` becomes ``Named(EntityID string)`` instead of a role
  target to a root handle (``STRUCT``) or an atom holding the string (``REF``);
* each entity's root is bound to its name, inside the state;
* an entity whose whole content is a reference (``STRUCT`` could not project
  it) is a relation ``symbol:ref`` with one role ``target``, a ``Named``
  target. The plan does not name the atom or the role; both are recorded as
  a deviation;
* each ownership edge is an ``owns`` relation with ``Named`` owner and owned
  targets (one relation per edge, as in the other modes).

Content symbols may not collide with the encoding's reserved prefixes
(``name:``, ``binding:``) or, outside a bare reference, with ``ref``; the
projection fails closed with ``ProjectionGap``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from shear.canonical import CanonicalNode
from shear.identity import EntityID
from shear.relations import Relation
from shear.state import State

from core_projection.core import Atom
from core_projection.named import Contained, Name, Named, NState, ReservedAtom, Target
from core_projection.project import (
    Gap,
    Lost,
    Mode,
    ProjectionGap,
    _Builder,
    _node,
)

__all__ = ["BARE_REFERENCE", "NamedProjection", "decode_named", "project_named"]

BARE_REFERENCE = "ref"
BARE_REFERENCE_ROLE = "target"


@dataclass(frozen=True)
class NamedProjection:
    """``nstate`` plus the view (entity to root handle) and the ownership relations.

    It has no ``cstate``: code that reads the candidate state must choose
    explicitly how a ``NAMED`` state is read.
    """

    mode: Mode
    nstate: NState
    view: Mapping[EntityID, int]
    ownership_handles: Mapping[tuple[EntityID, EntityID], int]
    gaps: tuple[Gap, ...]

    def entity_of(self, handle: int) -> EntityID | None:
        for entity, root in self.view.items():
            if root == handle:
                return entity

        return None


class _NamedBuilder(_Builder):
    """The ``REF`` builder, recording where references were put."""

    def __init__(self, state: State) -> None:
        super().__init__(state, Mode.REF)
        self.references: dict[int, str] = {}
        self.bare: set[int] = set()

    def reference(self, node: CanonicalNode) -> int:
        handle = super().reference(node)
        self.references[handle] = node[2]

        return handle

    def build(self, content: Any, handle: int | None = None) -> int:
        if handle is not None and isinstance(content, CanonicalNode) and content[1] == "entity_id":
            target = self.reference(content)
            self.add(handle, Atom("symbol", BARE_REFERENCE), {BARE_REFERENCE_ROLE: (target,)})
            self.bare.add(handle)

            return handle

        return super().build(content, handle)


def project_named(state: State) -> NamedProjection:
    """Project a graph-form ``main`` state into the revised candidate."""

    builder = _NamedBuilder(state)

    for entity in sorted(state.values):
        builder.entity = entity
        builder.build(state.values[entity].content, builder.view[entity])

    def named(entity: EntityID, where: str) -> Named:
        if entity not in builder.view:
            raise ProjectionGap(f"{where} refers to absent entity {entity.value}")

        return Named(Name(entity.value))

    relations: dict[int, tuple[Atom | None, dict[str, tuple[Target, ...]]]] = {}

    for handle, (atom, roles) in builder.relations.items():
        if handle in builder.references:
            continue

        if (
            atom is not None
            and atom.tag == "symbol"
            and atom.value == BARE_REFERENCE
            and handle not in builder.bare
        ):
            raise ProjectionGap(f"content symbol {BARE_REFERENCE!r} collides with the bare-reference atom")

        owner = next((e for e, root in builder.view.items() if root == handle), None)
        where = owner.value if owner is not None else "an entity"
        relations[handle] = (
            atom,
            {
                role: tuple(
                    named(EntityID(builder.references[t]), where)
                    if t in builder.references
                    else Contained(t)
                    for t in targets
                )
                for role, targets in roles.items()
            },
        )

    ownership_handles: dict[tuple[EntityID, EntityID], int] = {}

    for owner in sorted(state.ownership):
        for child in state.ownership[owner]:
            handle = builder.fresh()
            ownership_handles[(owner, child)] = handle
            relations[handle] = (
                Atom("symbol", "owns"),
                {
                    "owner": (named(owner, "an ownership edge"),),
                    "owned": (named(child, "an ownership edge"),),
                },
            )

    try:
        nstate = NState(
            relations,
            {Name(entity.value): root for entity, root in builder.view.items()},
        )
    except ReservedAtom as error:
        raise ProjectionGap(str(error)) from error

    return NamedProjection(
        mode=Mode.NAMED,
        nstate=nstate,
        view=dict(builder.view),
        ownership_handles=ownership_handles,
        gaps=tuple(builder.gaps),
    )


def decode_named(projection: NamedProjection) -> dict[EntityID, Any]:
    """Recover each entity's canonical content from its root occurrence.

    As ``decode``: the single endpoint and the one-element tuple decode alike
    (arity collapse), and a flattened ``VersionID``/``StateID`` decodes to
    ``Lost``. A reference is a ``Named`` target and decodes to its name.
    """

    nstate = projection.nstate

    def reference(target: Target) -> Any:
        if not isinstance(target, Named):
            raise ValueError("an entity reference must be a Named target")

        return _node("entity_id", target.name.value)

    def target_value(target: Target) -> Any:
        return reference(target) if isinstance(target, Named) else value(target.handle)

    def value(h: int) -> Any:
        atom = nstate.atom(h)
        roles = nstate.roles(h)

        if atom is None:
            raise ValueError(f"occurrence {h} has no atom")

        if atom.tag in ("none", "bool", "int", "text"):
            return atom.value

        if atom.tag == "bytes":
            return _node("bytes", atom.value.hex())

        name = atom.value

        if name == BARE_REFERENCE and BARE_REFERENCE_ROLE in roles:
            return reference(roles[BARE_REFERENCE_ROLE][0])

        if not roles and not name.startswith("relation:"):
            return Lost(name)

        if name in ("tuple", "list"):
            return _node(name, tuple(target_value(t) for t in roles["items"]))

        if name == "raw_tuple":
            return tuple(target_value(t) for t in roles["items"])

        if name == "raw_list":
            return [target_value(t) for t in roles["items"]]

        if name == "map":
            pairs = []

            for entry in roles["entries"]:
                parts = nstate.roles(entry.handle)
                pairs.append((target_value(parts["key"][0]), target_value(parts["value"][0])))

            return _node("map", tuple(pairs))

        if name.startswith("relation:"):
            endpoints = {}

            for role, targets in roles.items():
                if role == "payload":
                    continue

                entities = tuple(EntityID(reference(t)[2]) for t in targets)
                endpoints[role] = entities[0] if len(entities) == 1 else entities

            payload = target_value(roles["payload"][0]) if "payload" in roles else None

            return Relation(name[len("relation:"):], endpoints, payload).canonical_node()

        return _node(name, target_value(roles["payload"][0]))

    return {entity: value(root) for entity, root in projection.view.items()}
