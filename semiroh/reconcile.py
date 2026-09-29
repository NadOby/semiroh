"""Reconcile edited source text with an existing graph-form program.

The graph is authoritative. ``reconcile`` parses a complete edited source
view, compares its declarations with the graph, and expresses supported
changes through :func:`semiroh.lang.define`. ``define`` performs continuity
inference inside declarations that already have identity.

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
from .transforms import (
    EntityMapping,
    TransformResult,
    transform_with_mapping,
)


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


def _remove_functions(
    state: State,
    removed: set[EntityID],
) -> TransformResult:
    """Remove top-level functions without cross-name continuity inference."""

    gone: set[EntityID] = set()

    for function in removed:
        gone.add(function)
        gone.update(state.owned_subtree(function))

    mappings = {
        entity: (() if entity in gone else entity)
        for entity in state.values
    }

    ownership = {
        owner: tuple(
            child
            for child in children
            if child not in gone
        )
        for owner, children in state.ownership.items()
        if owner not in gone
    }

    return transform_with_mapping(
        state,
        {},
        mappings,
        ownership=ownership,
    )


def _function_edits(
    state: State,
    before: dict[EntityID, Function],
    after: dict[EntityID, Function],
    parsed_links: dict[EntityID, Relation],
) -> dict[EntityID, Any]:
    """Build edits for functions present in the edited source."""

    edits: dict[EntityID, Any] = {}

    for entity in sorted(after):
        desired_function = after[entity]
        current_function = before.get(entity)

        if current_function is None or current_function != desired_function:
            edits[entity] = desired_function

        desired_links = _link_targets(parsed_links.get(entity))
        current_links = (
            {}
            if current_function is None
            else _graph_links(state, entity)
        )

        if desired_links != current_links:
            edits[EntityID(f"{entity.value}.reconcile.links")] = links(
                entity,
                **desired_links,
            )

    return edits


def _combine(
    first: TransformResult,
    second: TransformResult,
) -> TransformResult:
    """Combine two consecutive concrete transformation results.

    ``compose`` operates on transformation definitions, not applied
    ``TransformResult`` objects. Reconciliation already has both concrete
    results, so follow each explicit first-stage destination through the
    second-stage mapping, using identity where the second stage does not name
    it.
    """

    if first.destination.id != second.source.id:
        raise ValueError(
            "cannot combine non-consecutive transformation results"
        )

    second_mappings = {
        mapping.source_entity: mapping.destination_entities
        for mapping in second.mappings
    }

    mappings: list[EntityMapping] = []

    for mapping in first.mappings:
        destinations: set[EntityID] = set()

        for intermediate in mapping.destination_entities:
            destinations.update(
                second_mappings.get(intermediate, (intermediate,))
            )

        mappings.append(
            EntityMapping(
                source_state=first.source.id,
                source_entity=mapping.source_entity,
                destination_entities=tuple(sorted(destinations)),
            )
        )

    return TransformResult(
        source=first.source,
        destination=second.destination,
        mappings=tuple(
            sorted(
                mappings,
                key=lambda mapping: mapping.source_entity,
            )
        ),
        provenance=(first.provenance, second.provenance),
        conversions=second.conversions,
        relation_rewrites=second.relation_rewrites,
    )


def reconcile(state: State, text: str) -> TransformResult:
    """Reconcile complete edited program ``text`` against graph ``state``.

    Parsing and name resolution use the complete edited text. Existing
    declarations retain their top-level identity and changed function bodies
    go through ``lang.define``, which infers continuity among their code nodes.

    A declaration absent from the edited source disappears. A declaration
    with a new top-level name is created independently; spelling alone is not
    evidence that it continues a removed declaration.

    Cell declarations must currently be identical to the graph's
    declarations.
    """

    edited = parse(text)
    _check_cells(state, edited)

    before = _graph_functions(state)
    after = _input_functions(edited)
    parsed_links = _input_links(edited)

    removed = set(before) - set(after)

    if removed:
        removal = _remove_functions(state, removed)
        intermediate = removal.destination
    else:
        removal = None
        intermediate = state

    intermediate_before = _graph_functions(intermediate)
    edits = _function_edits(
        intermediate,
        intermediate_before,
        after,
        parsed_links,
    )

    update = define(intermediate, edits)

    if removal is None:
        return update

    return _combine(removal, update)
