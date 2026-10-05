"""Observables O0-O2 (plan section 3.3): round trip, equality and link targets.

O3 is in ``identity.py``, O4 in ``composition.py``, O5 in ``churn.py``.
Each function compares what ``main`` says with what the candidate says about
the same state and returns ``Row``s. Classification is by rule, never by
outcome: a prediction is cited only where the plan or charter makes one, and
every other disagreement is ``unexpected``. Nothing here changes the
projection to make results agree.
"""

from __future__ import annotations

import random
from typing import Any

from shear.canonical import CanonicalNode, canonical_serialize
from shear.equality import semantic_equal
from shear.identity import EntityID
from shear.state import State

from core_projection.core import CState, bisimilar
from core_projection.named import Named
from core_projection.project import (
    Mode,
    Projection,
    ProjectionGap,
    decode,
    normalize_arity,
    project,
)
from core_projection.project_named import NamedProjection
from core_projection.rows import AGREE, GAP, PREDICTED, UNEXPECTED, Row

ARITY = "arity collapse (single endpoint and one-element tuple project alike)"
ADVERSARIAL_1 = "adversarial 1 (distinct referents with equal content)"

SELF_CHECK_PAIRS = 200


def _key(content: Any) -> bytes:
    return canonical_serialize(content)


def _mask(content: Any) -> Any:
    """Content with every ``entity_id`` payload blanked: same shape, no referent."""

    if isinstance(content, CanonicalNode):
        kind, payload = content[1], content[2]

        if kind == "entity_id":
            return CanonicalNode(("__type__", "entity_id", ""))

        if kind in ("version_id", "state_id", "bytes"):
            return content

        return CanonicalNode(("__type__", kind, _mask(payload)))

    if type(content) is tuple:
        return tuple(_mask(item) for item in content)

    if type(content) is list:
        return [_mask(item) for item in content]

    return content


def _intern(keys: list[bytes]) -> list[int]:
    seen: dict[bytes, int] = {}

    return [seen.setdefault(key, len(seen)) for key in keys]


def gap_rows(case: str, observable: str, error: ProjectionGap) -> list[Row]:
    return [Row(case, observable, "content", "no projection", GAP, "ProjectionGap", examples=(str(error),))]


# ---------------------------------------------------------------------------
# O0 round trip
# ---------------------------------------------------------------------------


def roundtrip_rows(case: str, state: State) -> list[Row]:
    """``decode(project(S))`` against ``S``, exactly and modulo arity.

    An exact failure that disappears once single endpoints are written as
    one-element tuples is the arity collapse; any other failure, and any
    failure modulo arity, is unexpected. Identities inside content are gaps.
    """

    rows: list[Row] = []

    for mode in Mode:
        exact_name = f"O0/{mode.name}/exact"
        modulo_name = f"O0/{mode.name}/modulo-arity"

        try:
            projection = project(state, mode)
        except ProjectionGap as error:
            rows += gap_rows(case, exact_name, error) + gap_rows(case, modulo_name, error)
            continue

        decoded = decode(projection)
        flattened = {gap.entity for gap in projection.gaps}

        for entity in sorted(state.values):
            if entity in flattened:
                for name in (exact_name, modulo_name):
                    rows.append(Row(
                        case, name, "content", "identity flattened to an atom", GAP,
                        "VersionID or StateID inside content", examples=(entity.value,),
                    ))

                continue

            original = state.values[entity].content
            got = decoded[entity]
            exact = _key(got) == _key(original)
            modulo = _key(normalize_arity(got)) == _key(normalize_arity(original))

            rows.append(_roundtrip_row(case, exact_name, entity, exact, modulo, allow_arity=True))
            rows.append(_roundtrip_row(case, modulo_name, entity, modulo, modulo, allow_arity=False))

    return rows


def _roundtrip_row(
    case: str,
    observable: str,
    entity: EntityID,
    equal: bool,
    modulo: bool,
    allow_arity: bool,
) -> Row:
    if equal:
        return Row(case, observable, "content", "decoded equals content", AGREE, examples=(entity.value,))

    if allow_arity and modulo:
        return Row(
            case, observable, "content", "decoded differs", PREDICTED,
            f"predicted: {ARITY}", examples=(entity.value,),
        )

    return Row(
        case, observable, "content", "decoded differs", UNEXPECTED,
        "differs beyond arity", examples=(entity.value,),
    )


# ---------------------------------------------------------------------------
# O1 equality
# ---------------------------------------------------------------------------


def _check_semantic_equal(state: State, entities: list[EntityID], keys: list[bytes]) -> None:
    """The main side groups by canonical bytes; confirm that is ``semantic_equal``."""

    count = len(entities)
    pairs = [(i, j) for i in range(count) for j in range(i + 1, count)]

    if len(pairs) > SELF_CHECK_PAIRS:
        pairs = random.Random(0).sample(pairs, SELF_CHECK_PAIRS)

    for i, j in pairs:
        left, right = state.values[entities[i]], state.values[entities[j]]

        if semantic_equal(left, right) != (keys[i] == keys[j]):
            raise AssertionError(
                f"grouping by canonical bytes disagrees with semantic_equal "
                f"on {entities[i].value}, {entities[j].value}"
            )


def _shape(cstate: CState, handle: int) -> tuple:
    return (
        cstate.atom(handle),
        tuple(sorted((name, len(targets)) for name, targets in cstate.roles(handle).items())),
    )


def bisimulation_classes(projection: "Projection | NamedProjection", entities: list[EntityID]) -> list[int]:
    """Class id of each entity's root under bisimilarity.

    Bisimilarity is an equivalence, so each root is compared with one
    representative per class; roots of different shape are never compared
    (``bisimilar`` would reject them at once).
    """

    if projection.mode is Mode.NAMED:
        # Equality over contained targets with names compared by name is
        # bisimilarity of the encoding, whose name leaves have no edge to
        # the bound roots (named.py).
        projection.nstate.require_acyclic()
        cstate = projection.nstate.encoding()
    else:
        cstate = projection.cstate

    classes: dict[tuple, list[tuple[int, int]]] = {}
    result: list[int] = []
    next_class = 0

    for entity in entities:
        root = projection.view[entity]
        representatives = classes.setdefault(_shape(cstate, root), [])

        for class_id, representative in representatives:
            if bisimilar(cstate, representative, cstate, root):
                result.append(class_id)
                break
        else:
            representatives.append((next_class, root))
            result.append(next_class)
            next_class += 1

    return result


def equality_rows(case: str, state: State) -> list[Row]:
    """``semantic_equal`` against ``bisimilar`` on every pair of entities."""

    entities = sorted(state.values)
    contents = [state.values[entity].content for entity in entities]
    raw_keys = [_key(content) for content in contents]
    _check_semantic_equal(state, entities, raw_keys)

    raw = _intern(raw_keys)
    arity = _intern([_key(normalize_arity(content)) for content in contents])
    masked = _intern([_key(_mask(content)) for content in contents])
    both = _intern([_key(_mask(normalize_arity(content))) for content in contents])
    rows: list[Row] = []

    for mode in Mode:
        observable = f"O1/{mode.name}"

        try:
            projection = project(state, mode)
        except ProjectionGap as error:
            rows += gap_rows(case, observable, error)
            continue

        candidate = bisimulation_classes(projection, entities)
        count = len(entities)

        for i in range(count):
            for j in range(i + 1, count):
                main_equal = raw[i] == raw[j]
                candidate_equal = candidate[i] == candidate[j]
                example = (f"{entities[i].value} ~ {entities[j].value}",)

                if main_equal == candidate_equal:
                    word = "equal" if main_equal else "unequal"
                    rows.append(Row(case, observable, word, word, AGREE, examples=example))
                    continue

                rows.append(_equality_mismatch(
                    case, observable, mode, main_equal,
                    arity[i] == arity[j], masked[i] == masked[j], both[i] == both[j],
                    example,
                ))

    return rows


def _equality_mismatch(
    case: str,
    observable: str,
    mode: Mode,
    main_equal: bool,
    arity_equal: bool,
    masked_equal: bool,
    both_equal: bool,
    example: tuple[str, ...],
) -> Row:
    if main_equal:
        return Row(
            case, observable, "equal", "unequal", UNEXPECTED,
            "main equal, candidate unequal", examples=example,
        )

    if arity_equal:
        classification, note = PREDICTED, f"predicted: {ARITY}"
    elif mode is Mode.STRUCT and masked_equal:
        classification, note = PREDICTED, f"predicted: {ADVERSARIAL_1}"
    elif mode is Mode.STRUCT and both_equal:
        classification, note = PREDICTED, f"predicted: {ARITY}; {ADVERSARIAL_1}"
    else:
        classification, note = UNEXPECTED, "candidate equal where main is unequal; no cited prediction"

    return Row(case, observable, "unequal", "equal", classification, note, examples=example)


# ---------------------------------------------------------------------------
# O2 link targets
# ---------------------------------------------------------------------------

LINK_PREFIX = "link:"


def link_targets(content: Any) -> dict[str, EntityID]:
    """The ``link:<name>`` roles of a ``definition`` relation, as main states them."""

    if not (isinstance(content, CanonicalNode) and content[1] == "relation"):
        return {}

    kind, roles, _ = content[2]

    if kind != "definition":
        return {}

    return {
        role: EntityID(endpoint[2])
        for role, endpoint in roles
        if role.startswith(LINK_PREFIX)
        and isinstance(endpoint, CanonicalNode)
        and endpoint[1] == "entity_id"
    }


def recovered_target(projection: "Projection | NamedProjection", entity: EntityID, role: str) -> EntityID | None:
    """The entity a link role of ``entity`` points to, read from the candidate.

    ``STRUCT``: the entity whose root is the role's target handle (``None``
    when the target is not a root). ``REF``: the ``EntityID`` the target atom holds.
    ``NAMED``: the name of the role's ``Named`` target (``None`` for a contained one).
    """

    if projection.mode is Mode.NAMED:
        target = projection.nstate.roles(projection.view[entity])[role][0]

        return EntityID(target.name.value) if isinstance(target, Named) else None

    handle = projection.cstate.roles(projection.view[entity])[role][0]

    if projection.mode is Mode.STRUCT:
        return projection.entity_of(handle)

    return EntityID(projection.cstate.atom(handle).value)


def link_rows(case: str, state: State) -> list[Row]:
    """The target of each link: declared in ``main``, recovered from the candidate."""

    rows: list[Row] = []

    for mode in Mode:
        observable = f"O2/{mode.name}"

        try:
            projection = project(state, mode)
        except ProjectionGap as error:
            rows += gap_rows(case, observable, error)
            continue

        for entity in sorted(state.values):
            for role, declared in link_targets(state.values[entity].content).items():
                recovered = recovered_target(projection, entity, role)
                example = (f"{entity.value} {role} -> {declared.value}",)

                if recovered == declared:
                    rows.append(Row(case, observable, "declared target", "recovered the same target", AGREE, examples=example))
                else:
                    rows.append(Row(
                        case, observable, "declared target", "recovered another target", UNEXPECTED,
                        f"recovered {recovered.value if recovered else 'no entity'}",
                        examples=example,
                    ))

    return rows
