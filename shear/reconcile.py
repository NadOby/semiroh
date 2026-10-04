"""Reconcile edited source text with an existing graph-form program.

The graph is authoritative. ``reconcile`` parses a complete edited source
view, compares its declarations with the graph, and expresses supported
changes through :func:`semiroh.lang.define`. ``define`` performs continuity
inference across the complete edit.

Task 15 deliberately keeps this layer small. Version 0 has one program
namespace and supports function creation, removal, body edits and link-table
edits. Cell declaration edits are rejected until cell migration semantics
are specified (docs/name_resolution.md).
"""

from __future__ import annotations

from typing import Any

from .cells import cell_declaration
from .identity import EntityID
from .lang import (
    FUNCTION_ROLE,
    LINKS_KIND,
    Function,
    _definition_of,
    define,
    function_at,
    function_of,
    links,
)
from .relations import Endpoint, Relation, relation_of
from .state import State
from .syntax import parse
from .transforms import TransformResult


__all__ = ["ReconcileError", "reconcile"]


class ReconcileError(ValueError):
    """A valid source edit that the current reconciler cannot represent."""


def _graph_functions(state: State) -> dict[EntityID, Function]:
    """Functions currently present in graph form."""

    found: dict[EntityID, Function] = {}

    for entity in sorted(state.values):
        function = function_at(state, entity)

        if function is not None:
            found[entity] = function

    return found


def _input_functions(state: State) -> dict[EntityID, Function]:
    """Functions declared by a parsed input-format state."""

    found: dict[EntityID, Function] = {}

    for entity in sorted(state.values):
        function = function_of(state.values[entity])

        if function is not None:
            found[entity] = function

    return found


def _cells(state: State) -> dict[EntityID, Any]:
    """Cell declarations of either input or graph form."""

    found: dict[EntityID, Any] = {}

    for entity in sorted(state.values):
        declaration = cell_declaration(state.values[entity])

        if declaration is not None:
            found[entity] = declaration

    return found


def _input_links(state: State) -> dict[EntityID, Relation]:
    """The links relation parsed for each function that has one."""

    found: dict[EntityID, Relation] = {}

    for entity in sorted(state.values):
        relation = relation_of(state.values[entity])

        if relation is None or relation.kind != LINKS_KIND:
            continue

        function = relation.roles.get(FUNCTION_ROLE)

        if not isinstance(function, EntityID):
            raise ReconcileError(
                f"{entity.value}: malformed links relation has no function"
            )

        if function in found:
            raise ReconcileError(
                f"{function.value}: more than one links relation"
            )

        found[function] = relation

    return found


def _link_targets(relation: Relation | None) -> dict[str, Endpoint]:
    """Link-name to endpoint, excluding the links relation's owner role."""

    if relation is None:
        return {}

    return {
        name: endpoint
        for name, endpoint in relation.roles.items()
        if name != FUNCTION_ROLE
    }


def _graph_links(state: State, function: EntityID) -> dict[str, Endpoint]:
    """Current resolved link table of a graph-form function."""

    value = state.values.get(function)

    if value is None:
        return {}

    definition = _definition_of(value)

    if definition is None:
        return {}

    return dict(definition.links)


def _check_cells(current: State, edited: State) -> None:
    """Reject cell creation, removal or declaration changes."""

    before = _cells(current)
    after = _cells(edited)

    removed = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    changed = sorted(
        entity
        for entity in set(before) & set(after)
        if before[entity] != after[entity]
    )

    if not (removed or added or changed):
        return

    parts: list[str] = []

    if added:
        parts.append(
            "added " + ", ".join(entity.value for entity in added)
        )

    if removed:
        parts.append(
            "removed " + ", ".join(entity.value for entity in removed)
        )

    if changed:
        parts.append(
            "changed " + ", ".join(entity.value for entity in changed)
        )

    raise ReconcileError(
        "cell declaration edits are not supported yet: "
        + "; ".join(parts)
    )


def _function_edits(
    state: State,
    before: dict[EntityID, Function],
    after: dict[EntityID, Function],
    parsed_links: dict[EntityID, Relation],
) -> list[tuple[EntityID, Any]]:
    """Build the complete function edit without synthetic entity names.

    ``lang.define`` uses an arbitrary EntityID key for a links relation, so a
    plain mapping cannot represent both a whole-function edit and a links
    edit under the same function key. Return ordered pairs here; ``reconcile``
    assigns collision-free temporary keys after considering every real entity
    in both source and edited states.
    """

    edits: list[tuple[EntityID, Any]] = []

    for entity in sorted(set(before) - set(after)):
        edits.append((entity, None))

    for entity in sorted(after):
        desired_function = after[entity]
        current_function = before.get(entity)

        if current_function is None or current_function != desired_function:
            edits.append((entity, desired_function))

        desired_links = _link_targets(parsed_links.get(entity))
        current_links = (
            {}
            if current_function is None
            else _graph_links(state, entity)
        )

        if desired_links != current_links:
            edits.append((entity, links(entity, **desired_links)))

    return edits


def _define_edits(
    state: State,
    edited: State,
    edits: list[tuple[EntityID, Any]],
) -> dict[EntityID, Any]:
    """Give links-relation edits keys that cannot collide with user entities.

    The key of a links relation is only an input slot to ``lang.define``; the
    relation's ``function`` role identifies the function it edits. Temporary
    keys are therefore chosen outside both the current and edited entity
    namespaces and are never installed in the resulting state.
    """

    result: dict[EntityID, Any] = {}
    occupied = set(state.values) | set(edited.values)

    serial = 0

    for entity, value in edits:
        if not (isinstance(value, Relation) and value.kind == LINKS_KIND):
            result[entity] = value
            continue

        while True:
            key = EntityID(f".reconcile/{serial}")
            serial += 1

            if key not in occupied and key not in result:
                break

        result[key] = value

    return result


def reconcile(state: State, text: str) -> TransformResult:
    """Reconcile complete edited program ``text`` against graph ``state``.

    Parsing and name resolution use the complete edited text. Existing
    declarations retain their top-level identity. Function removals,
    creations, body edits and link-table edits are submitted to one
    ``lang.define`` call, so continuity inference sees the complete edit and
    no intermediate state can contain dangling references.

    A declaration with a new top-level name is a new function entity. Its
    body nodes may nevertheless retain identity when task 13's matcher finds
    unambiguous continuity across the complete edit.

    Cell declarations must currently be identical to the graph's
    declarations.
    """

    edited = parse(text)
    _check_cells(state, edited)

    before = _graph_functions(state)
    after = _input_functions(edited)
    parsed_links = _input_links(edited)

    edits = _function_edits(
        state,
        before,
        after,
        parsed_links,
    )

    return define(
        state,
        _define_edits(state, edited, edits),
    )
