
"""Acceptance tests for the task-23 diagnostic (issue #60).

The Plan owns this contract. Execute implements tests.content_baseline.
Timing runs only through manually dispatched CI, never these tests.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import unittest

from tests import content_baseline
from tests.mutation_catalog import SURVIVORS, SURVIVOR_SOURCE_BLOBS


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "shear/canonical.py",
    "shear/values.py",
    "shear/relations.py",
}
CONVERTERS = {"canonicalize", "canonical_serialize", "relation_of"}


def direct_calls() -> set[tuple[str, int, int, str]]:
    """Independently locate selected conversion calls in production."""
    found = set()

    for path in (ROOT / "shear").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()

        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Call):
                continue

            callee = node.func
            name = (
                callee.id if isinstance(callee, ast.Name)
                else callee.attr if isinstance(callee, ast.Attribute)
                else None
            )

            if name in CONVERTERS:
                found.add((relative, node.lineno, node.col_offset, name))

    return found


def sample_measurement() -> dict:
    """Schema fixture, not a claim that these numbers were measured."""
    output = (("END",),)

    return {
        "workload": "lower(lower)",
        "revision": "a" * 40,
        "ci_run_url": "https://github.com/NadOby/shear/actions/runs/1",
        "hardware": {
            "python": "3.12",
            "os": "Linux",
            "cpu": "fixture CPU",
            "cores": 2,
        },
        "routes": {
            "native": {
                "seconds": [1.0, 1.1, 1.2],
                "peak_traced_bytes": 1024,
                "output": output,
            },
            "shear_vm": {
                "seconds": [4.0, 4.1, 4.2],
                "peak_traced_bytes": 2048,
                "output": output,
            },
        },
        "sizes": {
            "compiler_chunk_bytes": 100,
            "derived_chunk_count": 2,
            "derived_chunk_bytes": 200,
            "state_content_bytes": 300,
            "image_exclusions": ["host runtime machinery"],
        },
        "edit": {
            "phase_seconds": {
                "define": 0.1,
                "lower": 0.2,
                "activate": 0.3,
            },
            "total_seconds": 0.6,
            "affected_nodes": 1,
            "affected_chunks": 1,
            "before": 1,
            "after": 2,
        },
    }


class ContentBaselineTests(unittest.TestCase):
    def test_inventory_is_deterministic_and_serializable(self) -> None:
        first = content_baseline.collect_inventory()
        second = content_baseline.collect_inventory()

        self.assertEqual(
            json.dumps(first, sort_keys=True),
            json.dumps(second, sort_keys=True),
        )
        self.assertNotIn("timings", first)
        self.assertTrue(first["conversion_sites"])

    def test_conversion_sites_are_source_grounded(self) -> None:
        sites = content_baseline.collect_inventory()["conversion_sites"]
        observed = set()

        for site in sites:
            with self.subTest(site=site):
                key = (
                    site["path"], site["line"],
                    site["column"], site["callee"],
                )
                self.assertNotIn(key, observed)
                observed.add(key)

                self.assertTrue((ROOT / site["path"]).is_file())
                self.assertTrue(site["function"])
                self.assertTrue(site["source_representation"])
                self.assertTrue(site["destination_representation"])
                self.assertIn(
                    site["kind"],
                    {"direct", "recursive", "preserving"},
                )
                self.assertIn(
                    site["necessity"],
                    {"semantic", "implementation"},
                )
                self.assertIn(
                    site["retention"],
                    {"retained", "reconstructed", "neither"},
                )
                self.assertIn("overlap", site)

        expected = direct_calls()
        self.assertTrue(expected)
        self.assertFalse(expected - observed)

    def test_representations_and_boundaries_are_classified(self) -> None:
        report = content_baseline.collect_inventory()

        findings = {
            entry["subject"]: entry
            for entry in report["representations"]
        }
        self.assertTrue({
            "Value.content",
            "Relation.roles",
            "Relation.payload",
            "relation_of cache",
        } <= findings.keys())

        for finding in findings.values():
            self.assertTrue(finding["classification"])
            self.assertTrue(finding["evidence"])

        boundaries = report["boundaries"]
        self.assertTrue(boundaries)

        for boundary in boundaries:
            self.assertTrue(boundary["function"])
            self.assertTrue(boundary["source_representation"])
            self.assertTrue(boundary["destination_representation"])
            self.assertIn("host_service", boundary)

        self.assertTrue({
            "shear/examples/self_hosting.py",
            "shear/examples/vm.py",
        } <= {entry["path"] for entry in boundaries})

    def test_survivors_match_the_reviewed_catalog(self) -> None:
        report = content_baseline.collect_inventory()

        expected = {
            key: value
            for key, value in SURVIVORS.items()
            if key[0] in TARGETS
        }
        actual = {}

        for entry in report["survivors"]:
            key = (
                entry["target"],
                entry["kind"],
                entry["source"],
                entry["occurrence"],
            )
            self.assertNotIn(key, actual)
            actual[key] = (
                entry["classification"],
                entry["reason"],
            )

        self.assertEqual(actual, expected)
        self.assertEqual(
            report["source_pins"],
            {
                target: SURVIVOR_SOURCE_BLOBS.get(target)
                for target in TARGETS
            },
        )
        self.assertIn("mutation_test_gaps", report)

    def test_measurement_schema_rejects_incomplete_evidence(self) -> None:
        valid = sample_measurement()
        content_baseline.validate_measurement(valid)

        missing = copy.deepcopy(valid)
        del missing["sizes"]["state_content_bytes"]

        with self.assertRaises(ValueError):
            content_baseline.validate_measurement(missing)

        insufficient = copy.deepcopy(valid)
        insufficient["routes"]["native"]["seconds"] = [1.0]

        with self.assertRaises(ValueError):
            content_baseline.validate_measurement(insufficient)

        disagreeing = copy.deepcopy(valid)
        disagreeing["routes"]["shear_vm"]["output"] = (("LIT", 1),)

        with self.assertRaises(ValueError):
            content_baseline.validate_measurement(disagreeing)


if __name__ == "__main__":
    unittest.main()
