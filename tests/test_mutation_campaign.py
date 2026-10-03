"""Tests for deterministic mutation campaign work selection and sharding."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import mutation
from tests import mutation_campaign
from tests import mutation_oracle
from tests.lanes import LANES


class MutationCampaignTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)

        self.targets = (
            "first.py",
            "second.py",
        )

        (self.root / "first.py").write_text(
            "\n".join(
                f"x{index} = {index} + 1"
                for index in range(12)
            )
            + "\n"
        )
        (self.root / "second.py").write_text(
            "\n".join(
                f"y{index} = {index} + 2"
                for index in range(9)
            )
            + "\n"
        )

    def old_selected_keys(
        self,
        count: int,
        seed: int,
        batch: int,
    ) -> set[mutation.MutationKey]:
        """Reproduce Task 18's per-target selection semantics."""

        selected: set[mutation.MutationKey] = set()

        for target in self.targets:
            source = (self.root / target).read_text()
            descriptions = mutation.site_descriptions(
                source,
                target,
            )
            indexes = mutation.sample(
                source,
                count,
                seed,
                batch=batch,
            )

            selected.update(
                descriptions[index].key
                for index in indexes
            )

        return selected

    def test_work_set_preserves_existing_selection(self) -> None:
        work = mutation_campaign.build_work_set(
            self.root,
            self.targets,
            count=7,
            seed=11,
            batch=1,
        )

        self.assertEqual(
            {
                mutant.key
                for mutant in work
            },
            self.old_selected_keys(
                count=7,
                seed=11,
                batch=1,
            ),
        )

    def test_work_set_is_deterministic(self) -> None:
        first = mutation_campaign.build_work_set(
            self.root,
            self.targets,
            count=8,
            seed=37,
            batch=0,
        )
        second = mutation_campaign.build_work_set(
            self.root,
            self.targets,
            count=8,
            seed=37,
            batch=0,
        )

        self.assertEqual(
            tuple(mutant.key for mutant in first),
            tuple(mutant.key for mutant in second),
        )

    def test_shards_are_disjoint_and_exhaustive(self) -> None:
        work = mutation_campaign.build_work_set(
            self.root,
            self.targets,
            count=7,
            seed=5,
            batch=0,
        )
        shards = [
            mutation_campaign.shard_work(
                work,
                shards=4,
                shard=shard,
            )
            for shard in range(4)
        ]

        full_keys = {
            mutant.key
            for mutant in work
        }
        shard_keys = [
            {
                mutant.key
                for mutant in shard
            }
            for shard in shards
        ]

        self.assertEqual(
            set().union(*shard_keys),
            full_keys,
        )
        self.assertEqual(
            sum(len(keys) for keys in shard_keys),
            len(full_keys),
        )

        for left in range(len(shard_keys)):
            for right in range(left + 1, len(shard_keys)):
                self.assertTrue(
                    shard_keys[left].isdisjoint(
                        shard_keys[right]
                    )
                )

    def test_shard_sizes_differ_by_at_most_one(self) -> None:
        work = mutation_campaign.build_work_set(
            self.root,
            self.targets,
            count=7,
            seed=3,
            batch=0,
        )
        sizes = [
            len(
                mutation_campaign.shard_work(
                    work,
                    shards=4,
                    shard=shard,
                )
            )
            for shard in range(4)
        ]

        self.assertLessEqual(
            max(sizes) - min(sizes),
            1,
        )

    def test_shard_count_does_not_change_selected_work(self) -> None:
        work = mutation_campaign.build_work_set(
            self.root,
            self.targets,
            count=9,
            seed=19,
            batch=0,
        )
        expected = {
            mutant.key
            for mutant in work
        }

        for shard_count in (1, 2, 3, 4, 7):
            with self.subTest(shards=shard_count):
                combined = {
                    mutant.key
                    for shard in range(shard_count)
                    for mutant in mutation_campaign.shard_work(
                        work,
                        shards=shard_count,
                        shard=shard,
                    )
                }

                self.assertEqual(
                    combined,
                    expected,
                )

    def test_work_for_shard_matches_explicit_sharding(self) -> None:
        work = mutation_campaign.build_work_set(
            self.root,
            self.targets,
            count=6,
            seed=13,
            batch=1,
        )

        self.assertEqual(
            mutation_campaign.work_for_shard(
                self.root,
                self.targets,
                count=6,
                seed=13,
                batch=1,
                shards=4,
                shard=2,
            ),
            mutation_campaign.shard_work(
                work,
                shards=4,
                shard=2,
            ),
        )

    def test_invalid_shards_are_rejected(self) -> None:
        work = mutation_campaign.build_work_set(
            self.root,
            self.targets,
            count=1,
            seed=1,
        )

        with self.assertRaises(ValueError):
            mutation_campaign.shard_work(
                work,
                shards=0,
                shard=0,
            )

        with self.assertRaises(ValueError):
            mutation_campaign.shard_work(
                work,
                shards=4,
                shard=-1,
            )

        with self.assertRaises(ValueError):
            mutation_campaign.shard_work(
                work,
                shards=4,
                shard=4,
            )

    def test_oracle_is_exactly_non_mutation_lanes(self) -> None:
        expected = tuple(
            module
            for lane, modules in LANES.items()
            if lane != "mutation"
            for module in modules
        )

        self.assertEqual(
            mutation_oracle.modules(),
            expected,
        )
        self.assertTrue(
            set(mutation_oracle.modules()).isdisjoint(
                LANES["mutation"]
            )
        )

    def test_baseline_and_mutant_use_same_oracle_command(self) -> None:
        source = (self.root / "first.py").read_text()
        mutant = next(
            site
            for site in mutation.site_descriptions(
                source,
                "first.py",
            )
            if site.kind == "arithmetic"
        )
        command = mutation_oracle.command()
        completed = subprocess.CompletedProcess(
            command,
            0,
            stdout=b"",
            stderr=b"",
        )

        with patch(
            "tests.mutation.subprocess.run",
            return_value=completed,
        ) as run:
            baseline = mutation.baseline(
                self.root,
                command,
            )
            _, dead = mutation.killed(
                self.root,
                "first.py",
                mutant.index,
                command,
            )

        self.assertEqual(baseline.returncode, 0)
        self.assertFalse(dead)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(
            run.call_args_list[0].args[0],
            command,
        )
        self.assertEqual(
            run.call_args_list[1].args[0],
            command,
        )
        self.assertEqual(
            run.call_args_list[0].kwargs["env"],
            run.call_args_list[1].kwargs["env"],
        )


if __name__ == "__main__":
    unittest.main()
