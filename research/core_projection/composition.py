"""O4: composition of continuity, ``main`` against the candidate (plan section 3.3).

A ``Link`` is two steps ``S0 -> S1 -> S2`` given by their mappings. ``main``
composes the mappings with ``transforms.compose``. The candidate projects the
three states and composes continuity on handles, in two ways:

* ``a`` (shared): both steps use one projection of the middle state;
* ``b`` (independent): the second step uses its own projection of the middle
  state, whose handles are renamed by a seeded permutation (handles carry no
  meaning), and the steps are joined by every isomorphism between the two
  middle projections (charter section 3.11).

``compose`` rejects ``TransformResult``; as the plan says, the ``main`` side is
built from the results' mappings (``link_from_results``).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Mapping

from shear.identity import EntityID
from shear.state import State
from shear.transforms import TransformResult, TransformationDefinition
from shear.transforms import compose as main_compose

from core_projection.core import compose, isomorphisms, transport
from core_projection.project import Mode, project
from core_projection.rows import AGREE, PREDICTED, UNEXPECTED, Row

ISOMORPHISM_LIMIT = 64

SECTION_3_11 = "section 3.11 (the result depends on which isomorphism joins the steps)"

Mappings = Mapping[EntityID, tuple[EntityID, ...]]

# A source's outcome. ("known", names) | ("unknown",) | ("absent",) on the
# ``main`` side (absent: neither mapped nor unknown) and
# ("known", names) | ("unknown",) | ("varies", n) on the candidate side.
Outcome = tuple


@dataclass(frozen=True)
class Link:
    """Two steps. ``middle_second`` is the middle state as the second step names it.

    It equals ``middle`` when the steps share their middle state; a different
    state of equal structure models a middle state built independently.
    ``cannot_join`` says why ``main`` cannot compose such steps, when it cannot.
    """

    name: str
    start: State
    middle: State
    middle_second: State
    end: State
    first: Mappings
    second: Mappings
    cannot_join: str | None = None

    @property
    def shared(self) -> bool:
        return self.middle is self.middle_second or self.middle == self.middle_second


def mappings_of(result: TransformResult) -> dict[EntityID, tuple[EntityID, ...]]:
    return {m.source_entity: m.destination_entities for m in result.mappings}


def link_from_results(name: str, first: TransformResult, second: TransformResult) -> Link:
    """Steps built by ``main`` itself; the second starts where the first ended."""

    if first.destination != second.source:
        raise ValueError(f"{name}: the second step does not start at the first step's destination")

    return Link(
        name, first.source, first.destination, second.source, second.destination,
        mappings_of(first), mappings_of(second),
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main_outcomes(link: Link) -> dict[EntityID, Outcome]:
    """``transforms.compose`` on the mappings, one outcome per source entity."""

    composed = main_compose(
        TransformationDefinition.create(mappings=link.first),
        TransformationDefinition.create(mappings=link.second),
    )
    outcomes: dict[EntityID, Outcome] = {}

    for entity in sorted(link.start.values):
        mapping = composed.mapping_for(entity)

        if mapping is not None:
            outcomes[entity] = ("known", frozenset(mapping.destination_entities))
        elif entity in composed.unknown_sources:
            outcomes[entity] = ("unknown",)
        else:
            outcomes[entity] = ("absent",)

    return outcomes


# ---------------------------------------------------------------------------
# candidate
# ---------------------------------------------------------------------------


def _continuity(
    mapping: Mappings,
    source_view: Mapping[EntityID, int],
    destination_view: Mapping[EntityID, int],
) -> dict[int, frozenset[int]]:
    return {
        source_view[source]: frozenset(destination_view[d] for d in destinations)
        for source, destinations in mapping.items()
    }


def _names(handles: frozenset[int], view: Mapping[EntityID, int]) -> frozenset[EntityID]:
    entity_at = {root: entity for entity, root in view.items()}

    return frozenset(entity_at[handle] for handle in handles)


def candidate_shared(link: Link, mode: Mode) -> dict[EntityID, Outcome]:
    """Variant a: one projection of the middle state serves both steps."""

    start, middle, end = (project(s, mode) for s in (link.start, link.middle, link.end))
    first = _continuity(link.first, start.view, middle.view)
    second = _continuity(link.second, middle.view, end.view)
    result = compose(first, second)

    return {
        entity: ("known", _names(result[start.view[entity]], end.view))
        if start.view[entity] in result
        else ("unknown",)
        for entity in sorted(link.start.values)
    }


def candidate_independent(
    link: Link,
    mode: Mode,
    seed: int = 0,
) -> tuple[dict[EntityID, Outcome], int]:
    """Variant b: join independent middle projections by every isomorphism.

    Returns each source's outcome and the number of isomorphisms found
    (at most ``ISOMORPHISM_LIMIT``). A source whose result differs between
    isomorphisms is ``("varies", n)``; with no isomorphism it is unknown.
    """

    start, middle, end = (project(s, mode) for s in (link.start, link.middle, link.end))
    second_middle = project(link.middle_second, mode)
    rng = random.Random(seed)
    handles = list(second_middle.cstate.handles)
    renaming = dict(zip(handles, rng.sample(range(len(handles) * 3 + 10), len(handles))))
    second_cstate = second_middle.cstate.relabel(renaming)
    second_view = {entity: renaming[root] for entity, root in second_middle.view.items()}

    first = _continuity(link.first, start.view, middle.view)
    second = _continuity(link.second, second_view, end.view)
    results = [
        compose(transport(first, iso, destinations=True), second)
        for iso in isomorphisms(middle.cstate, second_cstate, limit=ISOMORPHISM_LIMIT)
    ]
    outcomes: dict[EntityID, Outcome] = {}

    for entity in sorted(link.start.values):
        seen = {
            ("known", _names(result[start.view[entity]], end.view))
            if start.view[entity] in result
            else ("unknown",)
            for result in results
        }

        if not seen:
            outcomes[entity] = ("unknown",)
        elif len(seen) == 1:
            outcomes[entity] = next(iter(seen))
        else:
            outcomes[entity] = ("varies", len(seen))

    return outcomes, len(results)


# ---------------------------------------------------------------------------
# rows
# ---------------------------------------------------------------------------


def _word(outcome: Outcome) -> str:
    if outcome[0] == "known":
        return f"Known({len(outcome[1])})"

    if outcome[0] == "varies":
        return "varies across isomorphisms"

    return "Unknown" if outcome[0] == "unknown" else "absent (not mapped)"


def classify(main: Outcome, candidate: Outcome, cannot_join: str | None) -> tuple[str, str]:
    """Classification and note for one source.

    ``absent`` and ``unknown`` on the ``main`` side both correspond to the
    candidate's Unknown and count as agreement; the rows keep the words
    apart so the two are counted separately. A candidate Known where ``main``
    has none is unexpected unless ``main`` could not join the steps at all.
    """

    if candidate[0] == "varies":
        return PREDICTED, f"predicted: {SECTION_3_11}"

    if candidate[0] == "unknown":
        if main[0] == "known":
            return UNEXPECTED, "main composes, candidate is Unknown"

        return AGREE, ""

    if main[0] == "known":
        if main[1] == candidate[1]:
            return AGREE, ""

        return UNEXPECTED, "both compose, destinations differ"

    if cannot_join:
        return PREDICTED, f"predicted: {cannot_join}"

    return UNEXPECTED, "candidate composes where main has no result"


def composition_rows(link: Link, seed: int = 0) -> list[Row]:
    """O4 rows for one link, both modes, variant a (when shared) and b."""

    main = main_outcomes(link)
    rows: list[Row] = []

    for mode in Mode:
        variants: list[tuple[str, dict[EntityID, Outcome], str]] = []

        if link.shared:
            variants.append(("a", candidate_shared(link, mode), ""))

        outcomes, found = candidate_independent(link, mode, seed)
        count = f">= {ISOMORPHISM_LIMIT}" if found >= ISOMORPHISM_LIMIT else str(found)
        variants.append(("b", outcomes, f"isomorphisms joining the middle states: {count}"))

        for variant, candidate, detail in variants:
            for entity, outcome in candidate.items():
                classification, note = classify(main[entity], outcome, link.cannot_join)

                if outcome[0] == "varies" or variant == "b":
                    note = "; ".join(part for part in (note, detail) if part)

                rows.append(Row(
                    link.name, f"O4{variant}/{mode.name}",
                    _word(main[entity]), _word(outcome), classification, note,
                    examples=(entity.value,),
                ))

    return rows
