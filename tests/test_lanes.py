"""Tests for the CI test-lane partition."""

import contextlib
import io
from pathlib import Path
import unittest

from tests.lanes import LANES, lane_command, run_all, suite_for, validate_partition


class LanePartitionTests(unittest.TestCase):
    def test_every_ordinary_test_module_belongs_to_exactly_one_lane(self):
        validate_partition()

        ordinary = {
            path.stem
            for path in Path(__file__).parent.glob("test_*.py")
        }
        assigned = [
            module
            for modules in LANES.values()
            for module in modules
        ]

        self.assertEqual(set(assigned), ordinary)
        self.assertEqual(len(assigned), len(set(assigned)))

    def test_every_lane_loads_tests(self):
        for lane in LANES:
            with self.subTest(lane=lane):
                suite = suite_for(lane)
                self.assertGreater(suite.countTestCases(), 0)

    def test_unknown_lane_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "unknown test lane"):
            suite_for("not-a-lane")


    def test_all_runs_every_lane_once_with_its_own_command(self):
        seen = []

        def run(lane):
            seen.append(lane)
            return 0, ""

        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run_all(jobs=3, run=run), 0)

        self.assertEqual(sorted(seen), sorted(LANES))
        self.assertEqual(
            lane_command("core-model")[1:],
            ["-m", "tests.lanes", "core-model"],
        )

    def test_all_fails_when_any_lane_fails(self):
        def run(lane):
            return (1, "boom\n") if lane == "syntax-reconcile" else (0, "")

        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            self.assertEqual(run_all(jobs=2, run=run), 1)

        self.assertIn("===== syntax-reconcile (FAILED) =====\nboom", output.getvalue())


if __name__ == "__main__":
    unittest.main()
