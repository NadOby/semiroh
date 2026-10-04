"""Tests for generated-verification infrastructure."""

from __future__ import annotations

import os
import unittest
from unittest import mock

from tests.generation import (
    case_count,
    minimize_sequence,
    reproduction,
    seeds,
)


class SeedTests(unittest.TestCase):
    def test_default_seeds_are_deterministic(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(case_count(4), 4)
            self.assertEqual(seeds(4), (0, 1, 2, 3))

    def test_heavy_budget_extends_the_deterministic_range(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SHEAR_CASES": "7"},
            clear=True,
        ):
            self.assertEqual(case_count(4), 7)
            self.assertEqual(seeds(4), tuple(range(7)))

    def test_zero_heavy_budget_means_the_ordinary_default(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SHEAR_CASES": "0"},
            clear=True,
        ):
            self.assertEqual(case_count(4), 4)
            self.assertEqual(seeds(4), (0, 1, 2, 3))

    def test_invalid_heavy_budget_is_rejected(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SHEAR_CASES": "-1"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                case_count(4)

    def test_one_seed_can_be_replayed(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SHEAR_SEED": "37"},
            clear=True,
        ):
            self.assertEqual(seeds(100), (37,))

    def test_replay_takes_precedence_over_heavy_budget(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "SHEAR_CASES": "1000",
                "SHEAR_SEED": "37",
            },
            clear=True,
        ):
            self.assertEqual(seeds(4), (37,))

    def test_multiple_seeds_can_be_replayed(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SHEAR_SEED": "7, 11,19"},
            clear=True,
        ):
            self.assertEqual(seeds(100), (7, 11, 19))

    def test_empty_seed_setting_is_rejected(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SHEAR_SEED": " , "},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                seeds(10)


class ReductionTests(unittest.TestCase):
    def test_sequence_is_reduced_to_the_failure_cause(self) -> None:
        original = (
            "irrelevant-a",
            "arm",
            "irrelevant-b",
            "fire",
            "irrelevant-c",
        )

        def fails(items: tuple[str, ...]) -> bool:
            return "arm" in items and "fire" in items

        reduced = minimize_sequence(original, fails)

        self.assertEqual(set(reduced), {"arm", "fire"})
        self.assertTrue(fails(reduced))

    def test_nonfailing_sequence_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            minimize_sequence((1, 2, 3), lambda _: False)

    def test_reproduction_command_names_seed_and_module(self) -> None:
        self.assertEqual(
            reproduction("tests.test_generated", 17),
            "SHEAR_SEED=17 "
            "python -m unittest tests.test_generated",
        )


class StaleVariableTests(unittest.TestCase):
    def test_a_variable_with_the_old_project_prefix_fails_loudly(self) -> None:
        import subprocess
        import sys

        clean = {k: v for k, v in os.environ.items() if not k.startswith("SEMIROH_")}
        stale = subprocess.run(
            [sys.executable, "-c", "import tests"],
            env={**clean, "SEMIROH_SEED": "1"},
            capture_output=True,
            text=True,
        )
        fresh = subprocess.run(
            [sys.executable, "-c", "import tests"],
            env={**clean, "SHEAR_SEED": "1"},
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("SEMIROH_SEED", stale.stderr)
        self.assertEqual(fresh.returncode, 0, fresh.stderr)

if __name__ == "__main__":
    unittest.main()
