"""Reconcile edited source text with an existing graph-form program.

The graph is authoritative.  ``reconcile`` parses a complete edited source
view, compares its declarations with the graph, and expresses the supported
difference through :func:`semiroh.lang.define`.  ``define`` performs the
actual continuity inference.

Task 15 deliberately keeps this layer small.  Version 0 has one program
namespace and supports function creation, removal, body edits and link-table
edits.  Cell declaration edits are rejected until cell migration semantics
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
    """Reject cell creation, removal or declaration changes.

    Runtime cell contents and declaration migration need explicit semantics.
    Treating an edited declaration as an ordinary replacement would silently
    choose those semantics, so task 15 does not do it.
    """

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


def reconcile(state: State, text: str) -> TransformResult:
    """Reconcile complete edited program ``text`` against graph ``state``.

    Parsing and name resolution are performed from the complete edited text,
    not from the old graph.  Consequently a removed declaration cannot remain
    accidentally resolvable merely because it existed before the edit.

    Unchanged functions are omitted from the edit set.  Changed function
    bodies are passed to :func:`lang.define`, whose continuity matcher keeps
    unambiguous old nodes.  Link-table changes are supplied independently, so
    changing a resolved global reference need not manufacture a different
    function body.  Removed functions map to ``None`` and new functions are
    ordinary whole-function definitions.

    Cell declarations must currently be identical to the graph's declarations;
    see :class:`ReconcileError`.
    """

    edited = parse(text)
    _check_cells(state, edited)

    before = _graph_functions(state)
    after = _input_functions(edited)
    parsed_links = _input_links(edited)

    edits: dict[EntityID, Any] = {}

    before_ids = set(before)
    after_ids = set(after)

    for entity in sorted(before_ids - after_ids):
        edits[entity] = None

    for entity in sorted(after_ids):
        desired_function = after[entity]
        current_function = before.get(entity)

        if current_function is None or current_function != desired_function:
            edits[entity] = desired_function

        desired_relation = parsed_links.get(entity)
        desired_links = _link_targets(desired_relation)
        current_links = (
            {}
            if current_function is None
            else _graph_links(state, entity)
        )

        if desired_links != current_links:
            # ``define`` accepts a links relation under any EntityID key and
            # identifies its function through FUNCTION_ROLE.  Constructing it
            # here also represents the important non-empty -> empty change,
            # for which the parser naturally emits no links entity.
            edits[EntityID(f"{entity.value}.reconcile.links")] = links(
                entity,
                **desired_links,
            )

    return define(state, edits)
