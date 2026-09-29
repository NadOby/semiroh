"""Tests for the graph-ledger measurements and quoted documentation values."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from semiroh.examples.ledger import measurements


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "graph_ledger.md"


class LedgerTests(unittest.TestCase):
    def test_script_runs_and_prints_its_measurements(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "semiroh.examples.ledger"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        printed = json.loads(completed.stdout)
        self.assertEqual(printed, measurements())

        # Leave the actual measured output visible in GitHub Actions so the
        # documentation can be written from a real run, not an estimate.
        print("\nGRAPH LEDGER MEASUREMENTS")
        print(json.dumps(printed, indent=2, sort_keys=True))

    def test_documented_measurements_match_the_model(self) -> None:
        if not LEDGER.exists():
            self.skipTest("docs/graph_ledger.md has not been added yet")

        text = LEDGER.read_text(encoding="utf-8")
        actual = measurements()

        quoted = {
            key: int(value)
            for key, value in re.findall(
                r"<!-- measurement:([a-z0-9_.-]+)=(\d+) -->",
                text,
            )
        }

        expected = {
            "leaf_edit_41.re_lowered": 2,
            #"leaf_edit_41.nodes":
                #actual["incremental_compilation"]["leaf_edit_41"]["nodes"],
            "leaf_edit_41.re_lowered":
                actual["incremental_compilation"]["leaf_edit_41"]["re_lowered"],
            "leaf_edit_401.nodes":
                actual["incremental_compilation"]["leaf_edit_401"]["nodes"],
            "leaf_edit_401.re_lowered":
                actual["incremental_compilation"]["leaf_edit_401"]["re_lowered"],
            "five_node_replacement.replacement_nodes":
                actual["incremental_compilation"]["five_node_replacement"][
                    "replacement_nodes"
                ],
            "five_node_replacement.re_lowered":
                actual["incremental_compilation"]["five_node_replacement"][
                    "re_lowered"
                ],
            "continuity.cases":
                actual["continuity"]["cases"],
            "continuity.holding":
                actual["continuity"]["holding"],
            "fold.folded_nodes":
                actual["fold"]["folded_nodes"],
            "fold.recorded_sources":
                actual["fold"]["recorded_sources"],
        }

        for case_name, case in actual["continuity"]["per_case"].items():
            expected[f"continuity.{case_name}.same_identity_claims"] = (
                case["same_identity_claims"]
            )

        for designator, count in actual["fold"][
            "sources_per_folded_node"
        ].items():
            expected[f"fold.{designator}.sources"] = count

        self.assertEqual(quoted, expected)


if __name__ == "__main__":
    unittest.main()
