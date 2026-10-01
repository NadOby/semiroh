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
    SURVIVOR_ENGINE_BLOB,
    SURVIVOR_SOURCE_BLOBS,
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


def current_blob(target: str) -> str:
    return mutation.git_blob_id(
        (ROOT / target).read_bytes()
    )


@unittest.skipIf(
    mutation.in_mutation_subprocess(),
    "mutation catalog integrity is harness metadata, not a semantic kill oracle",
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
        for target, _, _, _ in SURVIVORS:
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

    def test_survivor_mutation_engine_matches_reviewed_version(
        self,
    ) -> None:
        current = current_blob("tests/mutation.py")

        self.assertEqual(
            current,
            SURVIVOR_ENGINE_BLOB,
            (
                "stale survivor mutation-engine review\n"
                f"  reviewed: {SURVIVOR_ENGINE_BLOB}\n"
                f"  current:  {current}\n"
                "re-review every classified survivor before updating the "
                "mutation-engine pin"
            ),
        )

    def test_survivor_source_pins_exactly_cover_classified_targets(
        self,
    ) -> None:
        classified_targets = {
            key[0]
            for key in SURVIVORS
        }

        self.assertEqual(
            set(SURVIVOR_SOURCE_BLOBS),
            classified_targets,
            (
                "every target with reviewed survivors must have exactly one "
                "reviewed source-version pin, and targets without survivors "
                "must not retain stale pins"
            ),
        )

    def test_survivor_source_pins_name_mutation_targets(self) -> None:
        for target in SURVIVOR_SOURCE_BLOBS:
            with self.subTest(target=target):
                self.assertIn(target, TARGETS)

    def test_survivor_sources_match_reviewed_versions(self) -> None:
        for target, reviewed in SURVIVOR_SOURCE_BLOBS.items():
            with self.subTest(target=target):
                current = current_blob(target)

                self.assertEqual(
                    current,
                    reviewed,
                    (
                        f"stale survivor review for {target}\n"
                        f"  reviewed: {reviewed}\n"
                        f"  current:  {current}\n"
                        "re-review every classified survivor in this target "
                        "before updating its source pin"
                    ),
                )

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
        self.assertEqual(
            [mutant.occurrence for mutant in constants],
            [0, 1],
        )
        self.assertNotEqual(
            constants[0].key,
            constants[1].key,
        )

    def test_nested_same_line_sites_have_distinct_keys(self) -> None:
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
        self.assertEqual(
            [mutant.occurrence for mutant in arithmetic],
            [0, 1],
        )
        self.assertNotEqual(
            arithmetic[0].key,
            arithmetic[1].key,
        )

    def test_unrelated_edit_invalidates_reviewed_source_version(
        self,
    ) -> None:
        original = b"value = 1 + 2\n"
        edited = b"unrelated = 99\nvalue = 1 + 2\n"

        original_site = next(
            mutant
            for mutant in mutation.site_descriptions(
                original.decode(),
                "example.py",
            )
            if mutant.kind == "arithmetic"
        )
        edited_site = next(
            mutant
            for mutant in mutation.site_descriptions(
                edited.decode(),
                "example.py",
            )
            if mutant.kind == "arithmetic"
        )

        # The compact site key may legitimately remain unchanged. It is valid
        # only inside one explicitly reviewed source version.
        self.assertEqual(
            original_site.key,
            edited_site.key,
        )
        self.assertNotEqual(
            mutation.git_blob_id(original),
            mutation.git_blob_id(edited),
        )


if __name__ == "__main__":
    unittest.main()
