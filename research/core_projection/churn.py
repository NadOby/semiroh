"""O5: version churn (plan section 3.3).

The ledger's leaf-edit scenario, rebuilt from the public language API:
entities whose ``VersionID`` changes in ``main`` against entities whose
candidate value class changes.
"""

from __future__ import annotations

from typing import Any

from shear.identity import EntityID
from shear.lang import Function, define, links, load
from shear.state import State
from shear.values import Value

from core_projection.core import bisimilar
from core_projection.project import Mode, project
from core_projection.rows import AGREE, UNEXPECTED, Row


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


def churn_rows() -> list[Row]:
    """Entities whose ``VersionID`` changes against those whose value class changes."""

    from shear.examples.ledger import measurements

    measured = measurements()["incremental_compilation"]
    rows: list[Row] = []

    for label, chain in (("leaf_edit_41", 20), ("leaf_edit_401", 200)):
        before, after, function = leaf_edit_states(chain)
        nodes = len(before.owned_subtree(function))
        ledger = measured[label]

        if nodes != ledger["nodes"]:
            raise AssertionError(f"{label}: rebuilt {nodes} nodes, ledger measured {ledger['nodes']}")

        shared = sorted(set(before.values) & set(after.values))
        changed_version = sum(
            before.values[entity].version_id != after.values[entity].version_id
            for entity in shared
        )
        main_word = (
            f"{changed_version} of {len(shared)} entities change VersionID; "
            f"{ledger['re_lowered']} relowered"
        )

        for mode in Mode:
            observable = f"O5/{mode.name}"
            projections = project(before, mode), project(after, mode)
            changed_class = sum(
                not bisimilar(
                    projections[0].cstate, projections[0].view[entity],
                    projections[1].cstate, projections[1].view[entity],
                )
                for entity in shared
            )
            word = f"{changed_class} of {len(shared)} entities change value class"

            if changed_class == changed_version:
                rows.append(Row(label, observable, main_word, word, AGREE))
            else:
                rows.append(Row(
                    label, observable, main_word, word, UNEXPECTED,
                    "no cited prediction; the candidate value of an entity includes "
                    "everything it reaches, so a change propagates to its referrers"
                    if mode is Mode.STRUCT
                    else "no cited prediction",
                ))

    return rows
