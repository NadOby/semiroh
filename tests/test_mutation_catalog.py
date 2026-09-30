"""Checks for mutation target coverage and survivor classification."""

from __future__ import annotations

from pathlib import Path
import unittest

from tests import mutation
from tests.mutation_catalog import (
    CLASSIFICATIONS,
    OMITTED,
    SURVIVORS,
    TARGETS,
)


ROOT = Path(__file__).resolve().parent.parent


class MutationCatalogTests(unittest.TestCase):
    def test_every_target_exists_and_has_mutation_sites(self) -> None:
        for target in TARGETS:
            with self.subTest(target=target):
                path = ROOT / target

                self.assertTrue(path.is_file(), target)
                self.assertGreater(
                    mutation.site_count(path.read_text()),
                    0,
                    target,
                )

    def test_every_top_level_semantic_module_is_accounted_for(self) -> None:
        modules = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "semiroh").glob("*.py")
        }

        accounted = {
            target
            for target in TARGETS
            if target.count("/") == 1
        } | {
            path
            for path in OMITTED
            if path.count("/") == 1
        }

        self.assertEqual(modules, accounted)

    def test_every_example_module_is_accounted_for(self) -> None:
        modules = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "semiroh" / "examples").glob("*.py")
        }

        accounted = {
            target
            for target in TARGETS
            if target.startswith("semiroh/examples/")
        } | {
            path
            for path in OMITTED
            if path.startswith("semiroh/examples/")
        }

        self.assertEqual(modules, accounted)

    def test_targets_and_omissions_do_not_overlap(self) -> None:
        self.assertTrue(set(TARGETS).isdisjoint(OMITTED))

    def test_every_omission_has_a_reason(self) -> None:
        for path, reason in OMITTED.items():
            with self.subTest(path=path):
                self.assertTrue(reason.strip())

    def test_every_classified_survivor_names_a_target(self) -> None:
        for target, _, _ in SURVIVORS:
            with self.subTest(target=target):
                self.assertIn(target, TARGETS)

    def test_survivor_classifications_are_explicit(self) -> None:
        for mutant, (classification, reason) in SURVIVORS.items():
            with self.subTest(mutant=mutant):
                self.assertIn(classification, CLASSIFICATIONS)
                self.assertTrue(reason.strip())


if __name__ == "__main__":
    unittest.main()
