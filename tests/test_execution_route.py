"""Acceptance evidence for Task 29's execution-route spike (GH-65).

The spike may reject or block either candidate. Its evidence must say so
explicitly rather than silently reporting incomplete coverage as success.
The source-preservation witness tests the existing wrapper baseline.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from shear import EntityID, Runtime
from shear.examples import vm
from shear.examples._support import program
from shear.lang import function_at, load, run


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "bootstrap.md"
HEADING = "## 7. Task 29 execution-route evidence"

ACCEPTANCE = {f"A{i}" for i in range(1, 12)}
PREDICTIONS = {f"P{i}" for i in range(1, 6)}
WORKLOAD = {
    f"{route}-W{number}"
    for route in ("A", "B")
    for number in range(3)
}
REQUIRED = ACCEPTANCE | PREDICTIONS | WORKLOAD

RESULT_STATUS = {"pass", "fail", "blocked"}
PREDICTION_STATUS = {"confirmed", "falsified", "inconclusive"}
RUN_LINK = "https://github.com/NadOby/shear/actions/runs/"


def evidence_rows() -> dict[str, tuple[str, str, str]]:
    """Read the Task 29 evidence table, not the Task 28 matrix."""
    text = REPORT.read_text(encoding="utf-8")
    if HEADING not in text:
        raise AssertionError("missing Task 29 evidence section")

    section = text.split(HEADING, 1)[1]
    rows = {}

    for line in section.splitlines():
        if not line.startswith("|"):
            continue

        fields = [field.strip() for field in line.strip("|").split("|")]
        if len(fields) != 4 or fields[0] not in REQUIRED:
            continue

        key, status, proof, finding = fields
        if key in rows:
            raise AssertionError(f"duplicate evidence row: {key}")
        rows[key] = (status.lower(), proof, finding)

    return rows


class ExistingRouteBoundaryTests(unittest.TestCase):
    def test_wrapper_swap_changes_active_semantic_source(self):
        runtime = Runtime(load(program(vm.bootstrap_entities())))
        before = runtime.active.state

        originals = {
            name: function_at(before, EntityID(name))
            for name in vm.SWAPPED
        }
        twins = {
            name: function_at(before, vm.source_name(name))
            for name in vm.SWAPPED
        }

        self.assertTrue(run(runtime, vm.SWAP_ALL, may_activate=True))
        after = runtime.active.state

        for name in vm.SWAPPED:
            with self.subTest(function=name):
                active = function_at(after, EntityID(name))
                retained = function_at(after, vm.source_name(name))

                self.assertNotEqual(active.body, originals[name].body)
                self.assertEqual(active.body[:2], ("call", "vm"))
                self.assertEqual(retained.body, twins[name].body)
                self.assertEqual(retained.params, twins[name].params)

    def test_existing_wrapper_witness_does_not_change_source_twins(self):
        runtime = Runtime(load(program(vm.bootstrap_entities())))
        before = runtime.active.state

        identities = {
            name: before.values[vm.source_name(name)].version_id
            for name in vm.SWAPPED
        }

        run(runtime, vm.SWAP_ALL, may_activate=True)
        after = runtime.active.state

        for name, version in identities.items():
            with self.subTest(function=name):
                self.assertEqual(
                    after.values[vm.source_name(name)].version_id,
                    version,
                )


class EvidenceContractTests(unittest.TestCase):
    def test_evidence_is_complete_and_has_unique_ids(self):
        rows = evidence_rows()
        self.assertEqual(set(rows), REQUIRED)

    def test_every_result_has_a_status_and_a_falsifiable_witness(self):
        for key, (status, proof, finding) in evidence_rows().items():
            with self.subTest(id=key):
                allowed = (
                    PREDICTION_STATUS
                    if key in PREDICTIONS
                    else RESULT_STATUS
                )
                self.assertIn(status, allowed)
                self.assertTrue(proof, f"{key}: missing proof")
                self.assertTrue(finding, f"{key}: missing finding")
                self.assertNotIn("TODO", proof.upper())
                self.assertNotIn("TODO", finding.upper())

    def test_pass_claims_have_ci_evidence(self):
        for key, (status, proof, _) in evidence_rows().items():
            if status == "pass":
                with self.subTest(id=key):
                    self.assertIn(
                        RUN_LINK,
                        proof,
                        f"{key}: passing claims need a CI run",
                    )

    def test_workload_comparison_includes_both_routes(self):
        rows = evidence_rows()

        for route in ("A", "B"):
            for number in range(3):
                self.assertIn(f"{route}-W{number}", rows)

        self.assertTrue(
            any(
                rows[key][0] == "pass"
                for key in ("A-W0", "B-W0")
            ),
            "at least one route must demonstrate compiler rebuilding",
        )

    def test_blocked_criteria_are_not_presented_as_passes(self):
        rows = evidence_rows()

        for key in ACCEPTANCE | WORKLOAD:
            status, proof, finding = rows[key]

            if status == "blocked":
                with self.subTest(id=key):
                    self.assertTrue(
                        re.search(
                            r"missing|requires|unsupported|unresolved|"
                            r"dependency|prerequisite|counterexample",
                            finding,
                            re.IGNORECASE,
                        ),
                        f"{key}: identify the concrete blocker",
                    )


if __name__ == "__main__":
    unittest.main()
