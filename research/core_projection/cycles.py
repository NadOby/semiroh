"""C0: contained cycles in projected ``NAMED`` states (revision plan section 4.2).

``main``'s canonical content is a tree and ``NAMED`` sends every reference
through a ``Named`` target, so the revision predicts no cycle among
``Contained`` targets in any projected state. A cycle would violate item 3 of
charter section 3.12 and is unexpected. The observable is counted over the
states ``run.state_rows`` projects (corpus programs and continuity-corpus
sources and destinations).
"""

from __future__ import annotations

from shear.state import State

from core_projection.observables import gap_rows
from core_projection.project import Mode, ProjectionGap, project
from core_projection.rows import AGREE, UNEXPECTED, Row

OBSERVABLE = "C0/NAMED"


def cycle_rows(case: str, state: State) -> list[Row]:
    """One row for ``state``: ``main`` has a tree, the candidate's containment is acyclic or not."""

    try:
        projection = project(state, Mode.NAMED)
    except ProjectionGap as error:
        return gap_rows(case, OBSERVABLE, error)

    cycle = projection.nstate.containment_cycle()

    if cycle is None:
        return [Row(case, OBSERVABLE, "content is a tree", "contained targets acyclic", AGREE)]

    return [Row(
        case, OBSERVABLE, "content is a tree", "contained targets cyclic", UNEXPECTED,
        "a contained cycle in a projected state", examples=(" -> ".join(map(str, cycle)),),
    )]
