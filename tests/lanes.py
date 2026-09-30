"""Semantic partitions of the ordinary deterministic test suite.

CI runs these lanes independently.  The partition is deliberately explicit:
adding a new ordinary test module without assigning it to exactly one lane is
an error rather than silently reducing CI coverage.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


LANES: dict[str, tuple[str, ...]] = {
    "core-model": (
        "test_canonical",
        "test_cells",
        "test_constraint_relations",
        "test_constraints",
        "test_evaluators",
        "test_identity",
        "test_lanes",
        "test_ledger",
        "test_lifecycle",
        "test_ownership",
        "test_ownership_lifetime",
        "test_ownership_lifetime_regressions",
        "test_references",
        "test_relations",
        "test_state",
        "test_state_identity_cost",
    ),
    "language-runtime": (
        "test_activation",
        "test_bytecode",
        "test_closures",
        "test_data_graph_form",
        "test_data_ops",
        "test_data_regressions",
        "test_first_program",
        "test_graph_form",
        "test_lang",
        "test_language_trials",
        "test_metaprogramming",
        "test_runtime",
        "test_trial_runs",
    ),
    "transform-continuity": (
        "test_bounded_exhaustive",
        "test_continuity_corpus",
        "test_continuity_inference",
        "test_continuity_units",
        "test_fold",
        "test_matching",
        "test_node_edits",
        "test_reference_transfer",
        "test_transform_composition",
        "test_transform_mapping",
        "test_transformation_definition",
        "test_transforms",
    ),
    "syntax-reconcile": (
        "test_reconcile",
        "test_syntax",
        "test_syntax_links",
        "test_syntax_review",
        "test_syntax_units",
    ),
    "compiler-self-hosting": (
        "test_closure_differential",
        "test_closure_self_hosting",
        "test_self_hosting",
    ),
    "vm-bootstrap": (
        "test_vm",
    ),
    "cross-boundary": (
        "test_corpus",
        "test_docs",
        "test_malformed_generation",
        "test_properties",
    ),
    "mutation": (
        "test_mutation",
    ),
}


def _ordinary_modules() -> set[str]:
    directory = Path(__file__).parent

    return {
        path.stem
        for path in directory.glob("test_*.py")
    }


def validate_partition() -> None:
    assigned: dict[str, str] = {}

    for lane, modules in LANES.items():
        for module in modules:
            previous = assigned.get(module)

            if previous is not None:
                raise RuntimeError(
                    f"{module} belongs to both {previous!r} and {lane!r}"
                )

            assigned[module] = lane

    ordinary = _ordinary_modules()
    configured = set(assigned)

    missing = ordinary - configured
    stale = configured - ordinary

    if missing or stale:
        problems = []

        if missing:
            problems.append(
                "unassigned: " + ", ".join(sorted(missing))
            )

        if stale:
            problems.append(
                "missing files: " + ", ".join(sorted(stale))
            )

        raise RuntimeError(
            "invalid test-lane partition; " + "; ".join(problems)
        )


def suite_for(lane: str) -> unittest.TestSuite:
    try:
        modules = LANES[lane]
    except KeyError as exc:
        raise RuntimeError(
            f"unknown test lane {lane!r}; choose from "
            + ", ".join(sorted(LANES))
        ) from exc

    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()

    for module in modules:
        suite.addTests(
            loader.loadTestsFromName(f"tests.{module}")
        )

    return suite


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    validate_partition()

    if len(args) != 1:
        print(
            "usage: python -m tests.lanes <lane>",
            file=sys.stderr,
        )
        print(
            "lanes: " + ", ".join(sorted(LANES)),
            file=sys.stderr,
        )
        return 2

    try:
        suite = suite_for(args[0])
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    result = unittest.TextTestRunner(
        verbosity=2,
    ).run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
