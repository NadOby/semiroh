"""Tests for graph-ledger measurements and documented values."""

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
    def test_script_runs_and_prints_its_measurements(self):
        completed = subprocess.run(
            [sys.executable, "-m", "semiroh.examples.ledger"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            json.loads(completed.stdout),
            measurements(),
        )

    def test_documented_measurements_match_the_model(self):
        text = LEDGER.read_text(encoding="utf-8")
        actual = measurements()

        leaf_41 = actual["incremental_compilation"]["leaf_edit_41"]
        leaf_401 = actual["incremental_compilation"]["leaf_edit_401"]
        growing = actual["incremental_compilation"]["growing_replacement"]
        continuity = actual["continuity"]
        fold = actual["fold"]

        required_prose = (
            (
                f"A labelled leaf in a {leaf_41['nodes']}-node function "
                f"relowers {leaf_41['re_lowered']} node."
            ),
            (
                f"The same edit in a {leaf_401['nodes']}-node function "
                f"also relowers {leaf_401['re_lowered']} node."
            ),
            (
                f"The replacement creates {growing['created_nodes']} new "
                f"nodes, retains {growing['retained_nodes']} existing nodes "
                f"in the function, and relowers "
                f"{growing['re_lowered']} nodes."
            ),
            (
                f"The corpus contains {continuity['cases']} cases and "
                f"{continuity['holding']} currently hold."
            ),
            (
                f"The corpus fold contains {fold['folded_nodes']} folded "
                f"roots and their mappings record "
                f"{fold['recorded_sources']} source identities in total."
            ),
        )

        for sentence in required_prose:
            self.assertIn(sentence, text)

    def test_continuity_table_matches_actual_transformations(self):
        text = LEDGER.read_text(encoding="utf-8")
        actual = measurements()["continuity"]["per_case"]

        rows = {
            name: int(count)
            for name, count in re.findall(
                r"^\| `([^`]+)` \| \d+ \| (\d+) \|$",
                text,
                flags=re.MULTILINE,
            )
        }

        expected = {
            name: data["kept_identities"]
            for name, data in actual.items()
            if isinstance(data["kept_identities"], int)
        }

        self.assertEqual(rows, expected)

    def test_fold_table_matches_actual_transformation(self):
        text = LEDGER.read_text(encoding="utf-8")
        actual = measurements()["fold"]["sources_per_folded_node"]

        rows = {
            entity: int(count)
            for entity, count in re.findall(
                r"^\| `([^`]+)` \| (\d+) sources \|$",
                text,
                flags=re.MULTILINE,
            )
        }

        self.assertEqual(rows, actual)


if __name__ == "__main__":
    unittest.main()
