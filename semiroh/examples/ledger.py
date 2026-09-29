"""Measurements for docs/graph_ledger.md.

Run from the repository root:

    python3 -m semiroh.examples.ledger

Every reported number is derived from the live model.  Corpus expectations
are used only by continuity.check to say whether a case holds; measurement
counts themselves come from states and TransformResult mappings.
"""

from __future__ import annotations

import json
from typing import Any

from semiroh import EntityID, State, Value
from semiroh.bytecode import lowered_count
from semiroh.continuity import CASES, check
from semiroh.fold import sources_of
from semiroh.lang import Function, define, links, load, run
from semiroh.runtime import Runtime
from semiroh.syntax import parse
from semiroh.transforms import TransformResult


def _program(functions: dict[str, Function]) -> State:
    entities: dict[EntityID, Any] = {}

    for name, function in functions.items():
        entity = EntityID(name)
        entities[entity] = function
        entities[EntityID(f"{name}.links")] = links(entity)

    return State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    })


def _runtime(functions: dict[str, Function]) -> Runtime:
    return Runtime(load(_program(functions)))


def _lit(value: Any) -> tuple[Any, ...]:
    return ("lit", value)


def _leaf_edit_measurement(chain_length: int) -> dict[str, int]:
    """Edit one labelled leaf after every node has already been lowered."""

    body: tuple[Any, ...] = ("label", "edit", _lit(1))

    for index in range(chain_length):
        body = ("add", body, _lit(index))

    runtime = _runtime({"big": Function((), body)})
    function = EntityID("big")

    run(runtime, function)

    node_count = len(runtime.active.state.owned_subtree(function))

    runtime.activate(
        define(
            runtime.active.state,
            {(function, "edit"): _lit(5)},
        )
    )

    before = lowered_count()
    run(runtime, function)
    relowered = lowered_count() - before

    return {
        "nodes": node_count,
        "re_lowered": relowered,
    }


def _growing_edit_measurement() -> dict[str, int]:
    """Replace one lowered leaf by a larger expression.

    ``created_nodes`` is measured from the source and destination ownership
    sets.  It is deliberately not the syntactic size of ``replacement``:
    continuity inference may retain the edited leaf as the new subtree root.
    """

    function = EntityID("wide")
    runtime = _runtime({
        "wide": Function(
            ("n",),
            (
                "add",
                ("add", ("arg", "n"), _lit(1)),
                (
                    "add",
                    ("label", "edit", _lit(2)),
                    ("mul", ("arg", "n"), _lit(3)),
                ),
            ),
        )
    })

    run(runtime, function, 4)

    source = runtime.active.state
    source_nodes = set(source.owned_subtree(function))

    replacement = (
        "mul",
        _lit(2),
        ("add", _lit(1), _lit(1)),
    )
    result = define(
        source,
        {(function, "edit"): replacement},
    )

    destination_nodes = set(result.destination.owned_subtree(function))
    created_nodes = len(destination_nodes - source_nodes)
    retained_nodes = len(destination_nodes & source_nodes)

    runtime.activate(result)

    before = lowered_count()
    run(runtime, function, 4)
    relowered = lowered_count() - before

    return {
        "created_nodes": created_nodes,
        "retained_nodes": retained_nodes,
        "re_lowered": relowered,
    }


def _kept_identities(result: TransformResult) -> int:
    """Count source entities that map to the same EntityID."""

    return sum(
        mapping.source_entity in mapping.destination_entities
        for mapping in result.mappings
    )


def _continuity_measurements() -> dict[str, Any]:
    """Run every corpus operation and measure its actual identity retention."""

    cases: dict[str, dict[str, Any]] = {}
    holding = 0

    for case in CASES:
        problems = check(case)

        if not problems:
            holding += 1

        source = load(parse(case.source))

        try:
            result = case.operation(source)
        except BaseException as error:
            cases[case.name] = {
                "group": case.group,
                "holds": not problems,
                "outcome": "rejected",
                "exception": type(error).__name__,
                "kept_identities": 0,
            }
            continue

        results = result if isinstance(result, tuple) else (result,)
        kept = [_kept_identities(item) for item in results]

        cases[case.name] = {
            "group": case.group,
            "holds": not problems,
            "outcome": "result",
            "kept_identities": kept[0] if len(kept) == 1 else kept,
        }

    return {
        "cases": len(CASES),
        "holding": holding,
        "per_case": cases,
    }


def _fold_measurements() -> dict[str, Any]:
    """Measure folds from the actual transformation, not corpus expectations."""

    case = next(case for case in CASES if case.name == "fold")
    source = load(parse(case.source))
    result = case.operation(source)

    if isinstance(result, tuple):
        raise AssertionError(
            "fold corpus case unexpectedly produced multiple results"
        )

    folded: dict[str, int] = {}

    for entity in sorted(
        set(source.values) & set(result.destination.values),
        key=lambda item: item.value,
    ):
        before = source.values[entity]
        after = result.destination.values[entity]

        if before.version == after.version:
            continue

        sources = sources_of(result, entity)

        if len(sources) <= 1:
            continue

        folded[entity.value] = len(sources)

    return {
        "folded_nodes": len(folded),
        "sources_per_folded_node": folded,
        "recorded_sources": sum(folded.values()),
    }


def measurements() -> dict[str, Any]:
    return {
        "incremental_compilation": {
            "leaf_edit_41": _leaf_edit_measurement(20),
            "leaf_edit_401": _leaf_edit_measurement(200),
            "growing_replacement": _growing_edit_measurement(),
        },
        "continuity": _continuity_measurements(),
        "fold": _fold_measurements(),
    }


def main() -> None:
    print(json.dumps(measurements(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
