"""Instrument tests for the runner: the report states what the rows hold."""

from __future__ import annotations

import unittest

from core_projection import run
from core_projection.rows import AGREE, PREDICTED, UNEXPECTED, Row, counts


class RenderTests(unittest.TestCase):
    ROWS = [
        Row("c1", "O1/STRUCT", "equal", "equal", AGREE, count=5),
        Row("c1", "O1/STRUCT", "unequal", "equal", PREDICTED, "predicted: a | b", count=2, examples=("x ~ y",)),
        Row("c2", "O3/REF/renamed", "different StateID", "isomorphic", UNEXPECTED),
    ]

    def test_every_non_agree_row_appears_once_and_agree_rows_do_not(self):
        report = run.render(self.ROWS)
        section = report.split("## Every row that is not agree")[1].split("## Adversarial")[0]

        self.assertIn("x ~ y", section)
        self.assertIn("c2", section)
        self.assertNotIn("| equal | equal |", section)

    def test_pipes_in_notes_do_not_break_the_table(self):
        self.assertIn("predicted: a \\| b", run.render(self.ROWS))

    def test_counts_table_matches_row_counts(self):
        report = run.render(self.ROWS)

        self.assertIn("| O1/STRUCT | 5 | 2 | 0 | 0 | 7 |", report)
        self.assertIn("Overall: agree 5, predicted mismatch 2, unexpected mismatch 1, gap 0", report)
        self.assertEqual(sum(counts(self.ROWS).values()), 8)


class CollectTests(unittest.TestCase):
    def test_a_limited_run_produces_rows_for_every_observable_family(self):
        rows = run.collect(limit=1)
        families = {row.observable.split("/")[0].rstrip("ab") for row in rows}

        self.assertTrue({"O0", "O1", "O2", "O3", "O4", "O5", "adv2"} <= families)
        self.assertIn("# Projection experiment report", run.render(rows))


if __name__ == "__main__":
    unittest.main()
