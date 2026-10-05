"""O5: version churn (plan section 3.3, extended after review).

The ledger's leaf-edit scenarios, rebuilt from the public language API, and
one leaf edit inside a called function of a corpus program: entities whose
``VersionID`` changes in ``main`` against entities whose candidate value
class changes.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from shear.canonical import CanonicalNode
from shear.identity import EntityID
from shear.lang import Function, define, function_at, links, load
from shear.state import State
from shear.values import Value

from core_projection.core import bisimilar
from core_projection.named import equal as named_equal
from core_projection.project import Mode, project
from core_projection.rows import AGREE, PREDICTED, UNEXPECTED, Row


def leaf_edit_states(chain_length: int) -> tuple[State, State, EntityID]:
    """The ledger's leaf-edit scenario from the public language API.

    A chain of ``chain_length`` additions around one labelled leaf; the edit
    replaces the leaf. Returns the program before, after, and the function.
    """

    body: tuple[Any, ...] = ("label", "edit", ("lit", 1))

    for index in range(chain_length):
        body = ("add", body, ("lit", index))

    function = EntityID("big")
    program = State.create({
        function: Value.create(function, Function((), body)),
        EntityID("big.links"): Value.create(EntityID("big.links"), links(function)),
    })
    before = load(program)
    after = define(before, {(function, "edit"): ("lit", 5)}).destination

    return before, after, function


PREDICTION = (
    "predicted: direction review section 3.3 (version identity derived from "
    "candidate equality propagates to ancestors and referrers)"
)

CROSS_FUNCTION = ("compiler", "upper")


def _first_literal_edited(body: Any) -> tuple[Any, bool]:
    """``body`` with its first ``lit`` leaf (pre-order) changed, and whether one was."""

    if type(body) is tuple and len(body) == 2 and body[0] == "lit":
        value = body[1]

        if type(value) is int:
            return ("lit", value + 1), True

        if type(value) is str:
            return ("lit", value + "'"), True

        return body, False

    if type(body) is tuple:
        items = list(body)

        for index, item in enumerate(items):
            edited, found = _first_literal_edited(item)

            if found:
                items[index] = edited

                return tuple(items), True

    return body, False


def cross_function_states(
    program: str = CROSS_FUNCTION[0],
    callee: str = CROSS_FUNCTION[1],
) -> tuple[State, State, EntityID]:
    """A corpus program before and after one leaf of a called function is edited.

    The edit replaces the body of ``callee`` with one whose first literal
    leaf differs, through ``lang.define``, so continuity inference keeps every
    other node. Returns the state before, after, and the callee.
    """

    from shear.examples import EXAMPLES

    before = load(next(e.program for e in EXAMPLES if e.name == program))
    function = EntityID(callee)
    current = function_at(before, function)
    body, found = _first_literal_edited(current.body)

    if not found:
        raise ValueError(f"{callee} has no literal leaf to edit")

    after = define(before, {function: replace(current, body=body)}).destination

    return before, after, function


def _churn_rows(case: str, before: State, after: State, main_extra: str = "") -> list[Row]:
    shared = sorted(set(before.values) & set(after.values))
    changed_version = [
        e for e in shared if before.values[e].version_id != after.values[e].version_id
    ]
    functions = [e for e in shared if _is_function(before.values[e].content)]
    removed = len(set(before.values) - set(after.values))
    created = len(set(after.values) - set(before.values))
    main_word = f"{len(changed_version)} of {len(shared)} entities change VersionID"

    if removed or created:
        main_word += f"; {removed} removed, {created} created"

    main_word += main_extra
    rows: list[Row] = []

    for mode in Mode:
        projections = project(before, mode), project(after, mode)
        changed_class = [e for e in shared if not _same_class(mode, projections, e)]
        reached = sum(e in set(changed_class) for e in functions)
        word = (
            f"{len(changed_class)} of {len(shared)} entities change value class "
            f"({reached} of {len(functions)} functions)"
        )
        observable = f"O5/{mode.name}"

        classification, note = churn_class(mode, len(changed_class), len(changed_version))
        rows.append(Row(case, observable, main_word, word, classification, note))

    return rows


def _same_class(mode: Mode, projections, entity: EntityID) -> bool:
    before, after = projections

    if mode is Mode.NAMED:
        return named_equal(before.nstate, before.view[entity], after.nstate, after.view[entity])

    return bisimilar(before.cstate, before.view[entity], after.cstate, after.view[entity])


def churn_class(mode: Mode, changed_class: int, changed_version: int) -> tuple[str, str]:
    """Equal counts agree; under ``STRUCT`` more value classes than versions is
    the review's prediction; anything else is unexpected."""

    if changed_class == changed_version:
        return AGREE, ""

    if mode is Mode.STRUCT and changed_class > changed_version:
        return PREDICTED, PREDICTION

    return UNEXPECTED, "no cited prediction"


def _is_function(content: Any) -> bool:
    return (
        isinstance(content, CanonicalNode)
        and content[1] == "relation"
        and content[2][0] == "definition"
    )


def churn_rows() -> list[Row]:
    """Entities whose ``VersionID`` changes against those whose value class changes.

    The ledger's two leaf-edit scenarios, then one leaf edit inside a called
    function of a corpus program, where the change crosses function boundaries.
    """

    from shear.examples.ledger import measurements

    measured = measurements()["incremental_compilation"]
    rows: list[Row] = []

    for label, chain in (("leaf_edit_41", 20), ("leaf_edit_401", 200)):
        before, after, function = leaf_edit_states(chain)
        nodes = len(before.owned_subtree(function))
        ledger = measured[label]

        if nodes != ledger["nodes"]:
            raise AssertionError(f"{label}: rebuilt {nodes} nodes, ledger measured {ledger['nodes']}")

        rows += _churn_rows(label, before, after, f"; {ledger['re_lowered']} relowered")

    before, after, callee = cross_function_states()
    rows += _churn_rows(f"cross-function: {CROSS_FUNCTION[0]}, edit in {callee.value}", before, after)

    return rows
