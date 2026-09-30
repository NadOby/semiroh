"""Tests for generated-verification infrastructure."""

from __future__ import annotations

import os
import unittest
from unittest import mock

from tests.generation import minimize_sequence, reproduction, seeds


class SeedTests(unittest.TestCase):
    def test_default_seeds_are_deterministic(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(seeds(4), (0, 1, 2, 3))

    def test_one_seed_can_be_replayed(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SEMIROH_SEED": "37"},
            clear=True,
        ):
            self.assertEqual(seeds(100), (37,))

    def test_multiple_seeds_can_be_replayed(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SEMIROH_SEED": "7, 11,19"},
            clear=True,
        ):
            self.assertEqual(seeds(100), (7, 11, 19))

    def test_empty_seed_setting_is_rejected(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SEMIROH_SEED": " , "},
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
            "SEMIROH_SEED=17 "
            "python -m unittest tests.test_generated",
        )


if __name__ == "__main__":
    unittest.main()
