"""Tests for the CI test-lane partition."""

from pathlib import Path
import unittest

from tests.lanes import LANES, suite_for, validate_partition


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


if __name__ == "__main__":
    unittest.main()
