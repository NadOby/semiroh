"""Checks for mutation target coverage and survivor classification."""

from __future__ import annotations

from collections import Counter
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


def descriptions(
    target: str,
) -> tuple[mutation.Mutant, ...]:
    source = (ROOT / target).read_text()

    return mutation.site_descriptions(
        source,
        target,
    )


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
            for path in (
                ROOT / "semiroh" / "examples"
            ).glob("*.py")
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
        self.assertTrue(
            set(TARGETS).isdisjoint(OMITTED)
        )

    def test_every_omission_has_a_reason(self) -> None:
        for path, reason in OMITTED.items():
            with self.subTest(path=path):
                self.assertTrue(reason.strip())

    def test_every_classified_survivor_names_a_target(self) -> None:
        for target, _, _, _, _ in SURVIVORS:
            with self.subTest(target=target):
                self.assertIn(target, TARGETS)

    def test_survivor_classifications_are_explicit(self) -> None:
        for key, (
            classification,
            reason,
        ) in SURVIVORS.items():
            with self.subTest(key=key):
                self.assertIn(
                    classification,
                    CLASSIFICATIONS,
                )
                self.assertTrue(reason.strip())

    def test_every_survivor_key_names_exactly_one_current_site(
        self,
    ) -> None:
        by_target: dict[
            str,
            Counter[mutation.MutationKey],
        ] = {}

        for target in {
            key[0]
            for key in SURVIVORS
        }:
            by_target[target] = Counter(
                mutant.key
                for mutant in descriptions(target)
            )

        for key in SURVIVORS:
            with self.subTest(key=key):
                self.assertEqual(
                    by_target[key[0]][key],
                    1,
                    (
                        "survivor classification must identify exactly one "
                        "current mutation site; update or remove stale "
                        f"classification {key!r}"
                    ),
                )

    def test_same_line_sites_have_distinct_keys(self) -> None:
        source = "values = (0, False)\n"

        constants = [
            mutant
            for mutant in mutation.site_descriptions(
                source,
                "example.py",
            )
            if mutant.kind == "constant"
        ]

        self.assertEqual(len(constants), 2)
        self.assertNotEqual(
            constants[0].key,
            constants[1].key,
        )

    def test_nested_same_start_sites_have_distinct_keys(self) -> None:
        source = "value = 1 + 2 + 3\n"

        arithmetic = [
            mutant
            for mutant in mutation.site_descriptions(
                source,
                "example.py",
            )
            if mutant.kind == "arithmetic"
        ]

        self.assertEqual(len(arithmetic), 2)
        self.assertNotEqual(
            arithmetic[0].key,
            arithmetic[1].key,
        )


if __name__ == "__main__":
    unittest.main()
