"""Task 23: semantic-content inventory and bootstrap measurement contract.

Inventory is deterministic and does not execute the compiler. Timing is
reserved for a separately dispatched CI diagnostic.
"""

from __future__ import annotations

import ast
from collections import Counter
import json
import math
from pathlib import Path
from typing import Any

from shear.canonical import canonical_serialize, canonicalize
from tests.mutation_catalog import SURVIVORS, SURVIVOR_SOURCE_BLOBS


ROOT = Path(__file__).resolve().parents[1]

TARGETS = (
    "shear/canonical.py",
    "shear/values.py",
    "shear/relations.py",
)

# Explicit conversion boundaries. Do not count arbitrary tuple construction
# or bytecode execution as a content conversion.
CONVERSIONS = {
    "canonicalize": (
        "host semantic value or record",
        "canonical semantic content",
    ),
    "canonical_serialize": (
        "semantic content",
        "canonical bytes",
    ),
    "relation_of": (
        "Value.content",
        "cached Relation or None",
    ),
    "_decode": (
        "canonical expression content",
        "host expression data",
    ),
    "_decode_endpoint": (
        "canonical endpoint",
        "EntityID endpoint",
    ),
    "_function_from_canonical": (
        "canonical function content",
        "Function input record",
    ),
    "function_of": (
        "Value.content",
        "Function input record or None",
    ),
    "function_at": (
        "graph-form function",
        "Function input record",
    ),
    "_compile": (
        "expression input tree",
        "graph-form relation nodes",
    ),
    "_collapse": (
        "graph-form relation nodes",
        "expression input tree",
    ),
}

RETAINED = {
    ("shear/values.py", "__post_init__", "canonicalize"),
    ("shear/relations.py", "relation_of", "canonicalize"),
}

SEMANTIC_SERIALIZATION = {
    "_identity_key",
    "_compute_version_id",
    "__eq__",
    "__hash__",
}


class _ConversionCalls(ast.NodeVisitor):
    """Locate direct call expressions, preserving their enclosing function."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.scope: list[str] = []
        self.sites: list[dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_Call(self, node: ast.Call) -> None:
        callee = node.func
        name = (
            callee.id
            if isinstance(callee, ast.Name)
            else callee.attr
            if isinstance(callee, ast.Attribute)
            else None
        )

        if name in CONVERSIONS:
            function = ".".join(self.scope) or "<module>"
            source, destination = CONVERSIONS[name]

            kind = (
                "recursive"
                if self.scope and self.scope[-1] == name
                else "direct"
            )

            necessity = (
                "semantic"
                if name == "canonical_serialize"
                and self.scope
                and self.scope[-1] in SEMANTIC_SERIALIZATION
                else "implementation"
            )

            retention = (
                "retained"
                if name == "relation_of"
                else "retained"
                if (
                    self.path,
                    self.scope[-1] if self.scope else "",
                    name,
                ) in RETAINED
                else "reconstructed"
                if name in {
                    "_decode",
                    "_decode_endpoint",
                    "_function_from_canonical",
                    "function_of",
                    "function_at",
                    "_collapse",
                    "_compile",
                }
                else "neither"
            )

            self.sites.append({
                "path": self.path,
                "line": node.lineno,
                "column": node.col_offset,
                "callee": name,
                "function": function,
                "source_representation": source,
                "destination_representation": destination,
                "kind": kind,
                "necessity": necessity,
                "retention": retention,
                "overlap": (
                    "See other call sites of the same conversion; "
                    "shared callee does not establish redundant work."
                ),
            })

        self.generic_visit(node)


def _conversion_sites() -> list[dict[str, Any]]:
    sites: list[dict[str, Any]] = []

    for path in sorted((ROOT / "shear").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        visitor = _ConversionCalls(relative)
        visitor.visit(ast.parse(source, filename=relative))
        sites.extend(visitor.sites)

    return sorted(
        sites,
        key=lambda item: (
            item["path"],
            item["line"],
            item["column"],
            item["callee"],
        ),
    )


def _representations() -> list[dict[str, str]]:
    return [
        {
            "subject": "Value.content",
            "classification": (
                "Canonical semantic content retained by an immutable Value; "
                "not a second live host representation."
            ),
            "evidence": (
                "shear/values.py: Value.__post_init__ canonicalizes content; "
                "Value.version_id caches derived identity."
            ),
        },
        {
            "subject": "Relation.roles",
            "classification": (
                "Normalized immutable endpoint mapping in a live Relation; "
                "canonical endpoint tuples are held by Value.content."
            ),
            "evidence": (
                "shear/relations.py: Relation.__post_init__, "
                "Relation.canonical_node, relation_of."
            ),
        },
        {
            "subject": "Relation.payload",
            "classification": (
                "Canonicalized semantic payload of the Relation record; "
                "it is incorporated into Value.content when stored."
            ),
            "evidence": (
                "shear/relations.py: Relation.__post_init__ and "
                "Relation.canonical_node."
            ),
        },
        {
            "subject": "relation_of cache",
            "classification": (
                "Derived decoded-record cache on an immutable Value; "
                "not independent semantic state."
            ),
            "evidence": (
                "shear/relations.py: relation_of reads and writes "
                "Value._relation; semantic identity remains content-based."
            ),
        },
    ]


def _boundaries() -> list[dict[str, str]]:
    """Named conversion boundaries and remaining host services."""

    return [
        {
            "path": "shear/examples/self_hosting.py",
            "function": "compiler_entities",
            "source_representation": "host expression tuples",
            "destination_representation": "Function input records",
            "host_service": "Python constructs the initial compiler program.",
        },
        {
            "path": "shear/examples/self_hosting.py",
            "function": "_lower_body",
            "source_representation": "compiler algorithm expressed as Python tuples",
            "destination_representation": "SHEAR source expression",
            "host_service": "Python constructs source; SHEAR executes lowering.",
        },
        {
            "path": "shear/examples/vm.py",
            "function": "_compiled",
            "source_representation": "retained graph-form compiler source",
            "destination_representation": "compiler-produced expanded chunk",
            "host_service": (
                "The host implements code inspection and calls the "
                "active SHEAR compiler."
            ),
        },
        {
            "path": "shear/examples/vm.py",
            "function": "_swapped_function",
            "source_representation": "compiler-produced expanded chunk",
            "destination_representation": "interpreted compiler wrapper",
            "host_service": (
                "The host implements function construction, quote "
                "and activation operations."
            ),
        },
        {
            "path": "shear/examples/vm.py",
            "function": "bootstrap_entities",
            "source_representation": "Python-constructed compiler and VM definitions",
            "destination_representation": "loadable semantic program",
            "host_service": (
                "Python constructs the seed and supplies the host runtime."
            ),
        },
    ]


def _survivors() -> list[dict[str, Any]]:
    records = []

    for key, value in sorted(SURVIVORS.items()):
        target, kind, source, occurrence = key

        if target not in TARGETS:
            continue

        classification, reason = value
        records.append({
            "target": target,
            "kind": kind,
            "source": source,
            "occurrence": occurrence,
            "classification": classification,
            "reason": reason,
        })

    return records


def collect_inventory() -> dict[str, Any]:
    """Return a reproducible inventory of the checked-out source."""

    sites = _conversion_sites()
    by_callee = Counter(site["callee"] for site in sites)
    by_kind = Counter(site["kind"] for site in sites)

    return {
        "scope": "checked-out shear/ Python sources",
        "method": (
            "AST direct-call inventory for explicitly listed conversion "
            "functions; recursive calls are identified separately. "
            "Necessity and retention are preliminary call-site "
            "classifications requiring source review."
        ),
        "conversion_sites": sites,
        "counts": {
            "total": len(sites),
            "by_callee": dict(sorted(by_callee.items())),
            "by_kind": dict(sorted(by_kind.items())),
        },
        "representations": _representations(),
        "boundaries": _boundaries(),
        "survivors": _survivors(),
        "source_pins": {
            target: SURVIVOR_SOURCE_BLOBS.get(target)
            for target in TARGETS
        },
        "mutation_test_gaps": [],
        "mutation_gap_scope": (
            "No test gaps are inferred from the reviewed survivor catalog. "
            "Unclassified mutants and campaign coverage require separate "
            "mutation-run evidence."
        ),
    }


def _required(mapping: Any, fields: set[str], where: str) -> None:
    if not isinstance(mapping, dict):
        raise ValueError(f"{where} must be an object")

    missing = fields - mapping.keys()

    if missing:
        raise ValueError(
            f"{where} lacks: {', '.join(sorted(missing))}"
        )


def _number(value: Any, where: str, *, positive: bool = False) -> None:
    if type(value) not in (int, float):
        raise ValueError(f"{where} must be numeric")

    if not math.isfinite(value):
        raise ValueError(f"{where} must be finite")

    if value < 0 or (positive and value == 0):
        raise ValueError(f"{where} must be nonnegative or positive")


def validate_measurement(report: dict[str, Any]) -> None:
    """Reject incomplete or structurally inconsistent bootstrap evidence."""

    _required(
        report,
        {"workload", "revision", "ci_run_url", "hardware",
         "routes", "sizes", "edit"},
        "measurement",
    )

    if report["workload"] != "lower(lower)":
        raise ValueError("unexpected workload")

    revision = report["revision"]

    if (
        not isinstance(revision, str)
        or len(revision) != 40
        or any(char not in "0123456789abcdef" for char in revision)
    ):
        raise ValueError("revision must be a full commit SHA")

    if (
        not isinstance(report["ci_run_url"], str)
        or not report["ci_run_url"].startswith(
            "https://github.com/"
        )
        or "/actions/runs/" not in report["ci_run_url"]
    ):
        raise ValueError("CI run URL is missing or invalid")

    hardware = report["hardware"]
    _required(
        hardware,
        {"python", "os", "cpu", "cores"},
        "hardware",
    )

    for field in ("python", "os", "cpu"):
        if not isinstance(hardware[field], str) or not hardware[field]:
            raise ValueError(f"hardware.{field} is missing")

    if type(hardware["cores"]) is not int or hardware["cores"] < 1:
        raise ValueError("hardware.cores must be positive")

    routes = report["routes"]
    _required(routes, {"native", "shear_vm"}, "routes")

    for name in ("native", "shear_vm"):
        route = routes[name]
        _required(
            route,
            {"seconds", "peak_traced_bytes", "output"},
            name,
        )

        observations = route["seconds"]

        if not isinstance(observations, list) or len(observations) < 3:
            raise ValueError(f"{name} needs at least three observations")

        for seconds in observations:
            _number(seconds, f"{name}.seconds")

        peak = route["peak_traced_bytes"]

        if type(peak) is not int:
            raise ValueError(f"{name}.peak_traced_bytes must be integer")

        _number(peak, f"{name}.peak_traced_bytes")

        try:
            canonical_serialize(canonicalize(route["output"]))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name}.output is invalid") from exc

    native = canonical_serialize(canonicalize(routes["native"]["output"]))
    interpreted = canonical_serialize(
        canonicalize(routes["shear_vm"]["output"])
    )

    if native != interpreted:
        raise ValueError("compiler outputs differ between execution routes")

    sizes = report["sizes"]
    _required(
        sizes,
        {
            "compiler_chunk_bytes",
            "derived_chunk_count",
            "derived_chunk_bytes",
            "state_content_bytes",
            "image_exclusions",
        },
        "sizes",
    )

    for field in (
        "compiler_chunk_bytes",
        "derived_chunk_count",
        "derived_chunk_bytes",
        "state_content_bytes",
    ):
        if type(sizes[field]) is not int:
            raise ValueError(f"sizes.{field} must be integer")
        _number(sizes[field], f"sizes.{field}", positive=True)

    exclusions = sizes["image_exclusions"]

    if (
        not isinstance(exclusions, list)
        or not exclusions
        or not all(isinstance(item, str) and item for item in exclusions)
    ):
        raise ValueError("image proxy exclusions must be explicit")

    edit = report["edit"]
    _required(
        edit,
        {
            "phase_seconds",
            "total_seconds",
            "affected_nodes",
            "affected_chunks",
            "before",
            "after",
        },
        "edit",
    )
    _required(
        edit["phase_seconds"],
        {"define", "lower", "activate"},
        "edit.phase_seconds",
    )

    for phase in ("define", "lower", "activate"):
        _number(edit["phase_seconds"][phase], f"edit.{phase}")

    _number(edit["total_seconds"], "edit.total_seconds")

    for field in ("affected_nodes", "affected_chunks"):
        if type(edit[field]) is not int:
            raise ValueError(f"edit.{field} must be integer")
        _number(edit[field], f"edit.{field}", positive=True)

    if edit["before"] == edit["after"]:
        raise ValueError("the edit did not change the observed result")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("inventory",),
        help="Inventory is deterministic and performs no timing",
    )
    parser.parse_args(argv)

    print(json.dumps(collect_inventory(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
