"""O3: state identity (plan section 3.3).

``StateID`` equality in ``main`` against isomorphism of the projected states,
for the same program built twice, with every ``EntityID`` consistently
renamed (order-preserving and order-reversing) and with one literal changed.
The order-reversing renaming is an addition to the plan: ``main`` sorts
ownership children and map entries by ``EntityID`` spelling, so it shows
whether the projection is spelling-free.
"""

from __future__ import annotations

from typing import Any, Iterator

from shear.canonical import CanonicalNode
from shear.identity import EntityID
from shear.state import State
from shear.values import Value

from core_projection.core import isomorphic
from core_projection.observables import gap_rows
from core_projection.project import Mode, ProjectionGap, project, rename_entities
from core_projection.rows import AGREE, PREDICTED, UNEXPECTED, Row

SECTION_3_11 = "section 3.11 (EntityID is not part of state identity)"


def prefix_rename(entity: EntityID) -> EntityID:
    """Order-preserving: every name gains the same prefix."""

    return EntityID("x/" + entity.value)


def reverse_rename(entity: EntityID) -> EntityID:
    """Order-reversing bijection on strings of code points below U+10FFFF.

    Each code point is complemented and U+10FFFF is appended, so a name sorts
    after its extensions exactly when it sorted before them.
    """

    top = 0x10FFFF

    return EntityID("".join(chr(top - ord(c)) for c in entity.value) + chr(top))


def change_one_literal(state: State) -> State | None:
    """``state`` with the first ``lit`` relation that holds an int changed by one."""

    for entity in sorted(state.values):
        content = state.values[entity].content

        if not (isinstance(content, CanonicalNode) and content[1] == "relation"):
            continue

        kind, roles, payload = content[2]

        if kind == "lit" and type(payload) is int:
            changed = CanonicalNode(("__type__", "relation", (kind, roles, payload + 1)))
            values = dict(state.values)
            values[entity] = Value(entity, changed)

            return State.create(values, state.ownership)

    return None


def identity_pairs(state: State, twin: State | None) -> Iterator[tuple[str, State, State]]:
    if twin is not None:
        yield "built twice", state, twin

    yield "renamed (order-preserving)", state, rename_entities(state, prefix_rename)
    yield "renamed (order-reversing)", state, rename_entities(state, reverse_rename)

    changed = change_one_literal(state)

    if changed is not None:
        yield "one literal changed", state, changed


def identity_rows(case: str, state: State, twin: State | None = None) -> list[Row]:
    """``StateID`` equality against candidate isomorphism, for derived state pairs.

    ``twin`` is the same program loaded again, when the caller has one.
    """

    rows: list[Row] = []

    for label, left, right in identity_pairs(state, twin):
        main_equal = left.id == right.id
        main_word = "same StateID" if main_equal else "different StateID"

        for mode in Mode:
            observable = f"O3/{mode.name}/{label}"

            try:
                projections = project(left, mode), project(right, mode)
            except ProjectionGap as error:
                rows += gap_rows(case, observable, error)
                continue

            iso = isomorphic(projections[0].cstate, projections[1].cstate)
            word = "isomorphic" if iso else "not isomorphic"
            classification, note = _identity_class(
                label, mode, main_equal, iso, spelling_cause(left)
            )
            rows.append(Row(case, observable, main_word, word, classification, note))

    return rows


def spelling_cause(state: State) -> str | None:
    """A structure in ``state`` whose projection depends on ``EntityID`` spelling.

    ``main`` sorts a map's entries by key, so a map keyed by ``entity_id``
    nodes lists its entries in key-spelling order, and the projection keeps
    that order (role ``entries`` is a sequence). Ownership used to be the
    other such structure; it is now one relation per edge.
    """

    def keyed_by_entity(content: Any) -> bool:
        if isinstance(content, CanonicalNode):
            kind, payload = content[1], content[2]

            if kind == "map":
                return any(
                    isinstance(key, CanonicalNode) and key[1] == "entity_id"
                    for key, _ in payload
                ) or any(keyed_by_entity(value) for _, value in payload)

            if kind in ("entity_id", "version_id", "state_id", "bytes"):
                return False

            return keyed_by_entity(payload)

        if type(content) in (tuple, list):
            return any(keyed_by_entity(item) for item in content)

        return False

    if any(keyed_by_entity(value.content) for value in state.values.values()):
        return "map keyed by entity_id (entries are listed in key-spelling order)"

    return None


def _identity_class(
    label: str,
    mode: Mode,
    main_equal: bool,
    iso: bool,
    cause: str | None = None,
) -> tuple[str, str]:
    renamed = label.startswith("renamed")

    if main_equal:
        if iso:
            return AGREE, ""

        return UNEXPECTED, "main identical, candidate not isomorphic"

    if renamed and iso:
        return PREDICTED, f"predicted: {SECTION_3_11}"

    if not iso:
        if renamed and mode is Mode.STRUCT:
            # STRUCT holds no spelling; section 3.11 predicts isomorphism.
            return UNEXPECTED, (
                "renaming changed the projected structure; cause: "
                + (cause or "not identified")
            )

        return AGREE, ""

    return UNEXPECTED, "candidate isomorphic where main differs; no cited prediction"
