"""Measurements for docs/graph_ledger.md.

Run from the repository root:

    python3 -m semiroh.examples.ledger

The output is JSON so tests and documentation can compare measurements without
depending on presentation text.
"""

from __future__ import annotations

import json
from typing import Any

from semiroh import EntityID, State, Value
from semiroh.bytecode import lowered_count
from semiroh.continuity import CASES, check, resolve
from semiroh.fold import sources_of
from semiroh.lang import Function, define, links, load, run
from semiroh.runtime import Runtime
from semiroh.syntax import parse


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
    """Replace one lowered leaf by a five-node expression."""

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

    replacement = (
        "mul",
        _lit(2),
        ("add", _lit(1), _lit(1)),
    )
    runtime.activate(
        define(
            runtime.active.state,
            {(function, "edit"): replacement},
        )
    )

    before = lowered_count()
    run(runtime, function, 4)
    relowered = lowered_count() - before

    return {
        "replacement_nodes": 5,
        "re_lowered": relowered,
    }


def _continuity_measurements() -> dict[str, Any]:
    cases: dict[str, dict[str, Any]] = {}
    holding = 0

    for case in CASES:
        problems = check(case)

        if not problems:
            holding += 1

        source = load(parse(case.source))
        same_identity: set[EntityID] = set()

        # These expectation fields explicitly assert that a source entity
        # retains its EntityID across the operation.  Deduplicate entities
        # because a case may mention one both as kept/changed and with `at`.
        for designator in (
            *case.expect.kept,
            *case.expect.changed,
            *case.expect.at.keys(),
        ):
            same_identity.add(resolve(designator, source))

        cases[case.name] = {
            "group": case.group,
            "holds": not problems,
            "same_identity_claims": len(same_identity),
        }

    return {
        "cases": len(CASES),
        "holding": holding,
        "per_case": cases,
    }


def _fold_measurements() -> dict[str, Any]:
    case = next(case for case in CASES if case.name == "fold")
    source = load(parse(case.source))
    result = case.operation(source)

    if isinstance(result, tuple):
        raise AssertionError("fold corpus case unexpectedly produced multiple results")

    counts: dict[str, int] = {}

    for designator in case.expect.changed:
        entity = resolve(designator, source, result.destination)
        counts[designator] = len(sources_of(result, entity))

    return {
        "folded_nodes": len(counts),
        "sources_per_folded_node": counts,
        "recorded_sources": sum(counts.values()),
    }


def measurements() -> dict[str, Any]:
    return {
        "incremental_compilation": {
            "leaf_edit_41": _leaf_edit_measurement(20),
            "leaf_edit_401": _leaf_edit_measurement(200),
            "five_node_replacement": _growing_edit_measurement(),
        },
        "continuity": _continuity_measurements(),
        "fold": _fold_measurements(),
    }


def main() -> None:
    print(json.dumps(measurements(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
