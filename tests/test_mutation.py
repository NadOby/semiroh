"""Mutation testing: does the suite notice a planted bug?

``EngineTests`` check the machinery in ``tests/mutation.py`` on a tiny
package and always run.

``SuiteMutationTests`` plant deterministic single-site bugs in the production
model and run the whole suite against each. They run only when
``SEMIROH_MUTATE`` is set to a positive number of mutants per target and may
be divided into disjoint mutation batches and target shards:

    SEMIROH_MUTATE=3 python -m tests.test_mutation

    SEMIROH_MUTATE=3 \
    SEMIROH_MUTATE_SEED=1 \
    SEMIROH_MUTATE_BATCH=4 \
    SEMIROH_MUTATE_SHARDS=4 \
    SEMIROH_MUTATE_SHARD=2 \
        python -m tests.test_mutation

For a fixed source tree, count and seed, batches are disjoint and together
cover every mutation site exactly once. Target shards partition the mutation
targets without changing which mutants are selected for each target.

Known survivors live in ``tests/mutation_catalog.py``. Only exact reviewed
mutation sites with equivalent or intentionally unspecified behaviour may
remain there. A semantic test gap must receive a regression test instead of
being whitelisted.
"""

from __future__ import annotations

import ast
import os
import sys
import tempfile
import unittest
from pathlib import Path

from tests import mutation
from tests.mutation_catalog import (
    SURVIVORS,
    SURVIVOR_SOURCE_BLOBS,
    TARGETS,
)


CALC = """\
_unused = 0


def add(a, b):
    return a + b
"""

CALC_TESTS = """\
import os
from pathlib import Path
import unittest

from calc import add


class AddTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)


@unittest.skipIf(
    os.environ.get("SEMIROH_MUTATION_SUBPROCESS") == "1",
    "source integrity is harness metadata, not a mutation kill oracle",
)
class SourceIntegrityTests(unittest.TestCase):
    def test_source_is_unmodified(self):
        source = Path("calc.py").read_text()
        self.assertIn("_unused = 0", source)


if __name__ == "__main__":
    unittest.main()
"""

OPERATOR_SOURCE = """\
def probe(a, b):
    value = False
    if a < b:
        return a and b
    return a + b
"""


def _targets_for_shard(
    targets: tuple[str, ...],
    shards: int,
    shard: int,
) -> tuple[str, ...]:
    if shards < 1:
        raise ValueError(
            "SEMIROH_MUTATE_SHARDS must be a positive integer"
        )

    if shard < 0 or shard >= shards:
        raise ValueError(
            "SEMIROH_MUTATE_SHARD must be between 0 and "
            "SEMIROH_MUTATE_SHARDS - 1"
        )

    return tuple(
        target
        for index, target in enumerate(targets)
        if index % shards == shard
    )


def _survivor_pin_errors(
    root: Path,
    survivors: dict[
        mutation.MutationKey,
        tuple[str, str],
    ],
    pins: dict[str, str],
) -> tuple[str, ...]:
    """Return reasons reviewed survivor classifications are not current."""

    classified_targets = {
        key[0]
        for key in survivors
    }
    pinned_targets = set(pins)
    errors = []

    for target in sorted(
        classified_targets - pinned_targets
    ):
        errors.append(
            f"{target}: classified survivors have no reviewed source pin"
        )

    for target in sorted(
        pinned_targets - classified_targets
    ):
        errors.append(
            f"{target}: source pin has no classified survivors"
        )

    for target in sorted(
        classified_targets & pinned_targets
    ):
        path = root / target
        reviewed = pins[target]

        if not path.is_file():
            errors.append(
                f"{target}: reviewed source is missing\n"
                f"  reviewed: {reviewed}\n"
                "  current:  <missing>"
            )
            continue

        current = mutation.git_blob_id(
            path.read_bytes()
        )

        if current != reviewed:
            errors.append(
                f"{target}: stale survivor review\n"
                f"  reviewed: {reviewed}\n"
                f"  current:  {current}"
            )

    return tuple(errors)


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        (self.root / "calc.py").write_text(CALC)
        (self.root / "test_calc.py").write_text(CALC_TESTS)
        self.command = [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-f",
            "-q",
        ]

    def index_of(self, kind: str, text: str) -> int:
        matches = [
            mutant
            for mutant in mutation.site_descriptions(
                CALC,
                "calc.py",
            )
            if mutant.kind == kind
            and mutant.text == text
        ]

        self.assertEqual(
            len(matches),
            1,
            f"expected one {kind} site on {text!r}",
        )

        return matches[0].index

    def test_the_unmutated_copy_passes(self) -> None:
        done = mutation.baseline(
            self.root,
            self.command,
        )

        self.assertEqual(
            done.returncode,
            0,
            done.stderr.decode(),
        )

    def test_a_mutant_changes_exactly_one_site(self) -> None:
        index = self.index_of(
            "arithmetic",
            "return a + b",
        )

        source, mutant = mutation.mutate(
            CALC,
            "calc.py",
            index,
        )

        self.assertIn("return a - b", source)
        self.assertIn("_unused = 0", source)

        self.assertEqual(mutant.index, index)
        self.assertEqual(mutant.kind, "arithmetic")
        self.assertEqual(mutant.line, 5)
        self.assertEqual(mutant.text, "return a + b")
        self.assertEqual(mutant.occurrence, 0)

    def test_every_mutation_operator_changes_parseable_ast(self) -> None:
        expected = {
            "compare": "if a >= b:",
            "arithmetic": "return a - b",
            "boolean": "return a or b",
            "if": "if not a < b:",
            "constant": "value = True",
            "return": "return None",
        }
        sites = mutation.site_descriptions(
            OPERATOR_SOURCE,
            "operators.py",
        )
        original = ast.dump(
            ast.parse(OPERATOR_SOURCE),
            include_attributes=False,
        )

        self.assertEqual(
            {site.kind for site in sites},
            set(expected),
        )

        for kind, fragment in expected.items():
            with self.subTest(kind=kind):
                site = next(
                    site
                    for site in sites
                    if site.kind == kind
                )
                mutated, described = mutation.mutate(
                    OPERATOR_SOURCE,
                    "operators.py",
                    site.index,
                )

                parsed = ast.parse(mutated)

                self.assertNotEqual(
                    ast.dump(
                        parsed,
                        include_attributes=False,
                    ),
                    original,
                )
                self.assertIn(fragment, mutated)
                self.assertEqual(described, site)

    def test_site_key_distinguishes_nodes_on_one_line(self) -> None:
        source = "values = (0, False)\n"

        constants = [
            mutant
            for mutant in mutation.site_descriptions(
                source,
                "same-line.py",
            )
            if mutant.kind == "constant"
        ]

        self.assertEqual(len(constants), 2)
        self.assertEqual(
            constants[0].text,
            constants[1].text,
        )
        self.assertEqual(
            [mutant.occurrence for mutant in constants],
            [0, 1],
        )
        self.assertNotEqual(
            constants[0].key,
            constants[1].key,
        )

    def test_nested_sites_on_one_line_remain_distinct(self) -> None:
        source = "value = 1 + 2 + 3\n"

        arithmetic = [
            mutant
            for mutant in mutation.site_descriptions(
                source,
                "nested.py",
            )
            if mutant.kind == "arithmetic"
        ]

        self.assertEqual(len(arithmetic), 2)
        self.assertEqual(
            arithmetic[0].text,
            arithmetic[1].text,
        )
        self.assertEqual(
            [mutant.occurrence for mutant in arithmetic],
            [0, 1],
        )
        self.assertNotEqual(
            arithmetic[0].key,
            arithmetic[1].key,
        )

    def test_site_key_survives_unrelated_edits_elsewhere(self) -> None:
        original = """\
value = 1 + 2
"""
        edited = """\
unrelated = 99
value = 1 + 2
"""

        original_site = next(
            mutant
            for mutant in mutation.site_descriptions(
                original,
                "stable.py",
            )
            if mutant.kind == "arithmetic"
        )
        edited_site = next(
            mutant
            for mutant in mutation.site_descriptions(
                edited,
                "stable.py",
            )
            if mutant.kind == "arithmetic"
        )

        self.assertNotEqual(
            original_site.index,
            edited_site.index,
        )
        self.assertNotEqual(
            original_site.line,
            edited_site.line,
        )
        self.assertEqual(
            original_site.key,
            edited_site.key,
        )

    def test_seeded_batches_repeat(self) -> None:
        big = "\n".join(
            f"x{n} = {n} + 1"
            for n in range(50)
        )

        first = mutation.sample(
            big,
            10,
            seed=3,
            batch=2,
        )

        self.assertEqual(
            first,
            mutation.sample(
                big,
                10,
                seed=3,
                batch=2,
            ),
        )
        self.assertNotEqual(
            first,
            mutation.sample(
                big,
                10,
                seed=4,
                batch=2,
            ),
        )
        self.assertEqual(len(first), 10)

    def test_batches_are_disjoint(self) -> None:
        big = "\n".join(
            f"x{n} = {n} + 1"
            for n in range(30)
        )

        first = set(
            mutation.sample(
                big,
                7,
                seed=1,
                batch=0,
            )
        )
        second = set(
            mutation.sample(
                big,
                7,
                seed=1,
                batch=1,
            )
        )
        third = set(
            mutation.sample(
                big,
                7,
                seed=1,
                batch=2,
            )
        )

        self.assertTrue(first.isdisjoint(second))
        self.assertTrue(first.isdisjoint(third))
        self.assertTrue(second.isdisjoint(third))

    def test_all_batches_cover_every_site_exactly_once(self) -> None:
        big = "\n".join(
            f"x{n} = {n} + 1"
            for n in range(23)
        )
        sites = mutation.site_count(big)
        count = 5

        batches = []

        for batch in range((sites + count - 1) // count):
            batches.extend(
                mutation.sample(
                    big,
                    count,
                    seed=9,
                    batch=batch,
                )
            )

        self.assertEqual(
            sorted(batches),
            list(range(sites)),
        )
        self.assertEqual(
            len(batches),
            len(set(batches)),
        )

    def test_batch_after_exhaustion_is_empty(self) -> None:
        source = "x = 1 + 2\n"

        self.assertEqual(
            mutation.sample(
                source,
                1,
                seed=1,
                batch=mutation.site_count(source),
            ),
            [],
        )

    def test_invalid_batch_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mutation.sample(
                "x = 1 + 2\n",
                1,
                seed=1,
                batch=-1,
            )

    def test_target_shards_are_disjoint_and_exhaustive(self) -> None:
        targets = tuple(
            f"target-{index}"
            for index in range(17)
        )
        shards = [
            set(_targets_for_shard(targets, 4, shard))
            for shard in range(4)
        ]

        self.assertEqual(
            set().union(*shards),
            set(targets),
        )
        self.assertEqual(
            sum(len(shard) for shard in shards),
            len(targets),
        )

    def test_invalid_target_shard_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _targets_for_shard(("target",), 0, 0)

        with self.assertRaises(ValueError):
            _targets_for_shard(("target",), 1, 1)

    def test_returning_none_is_not_a_mutation(self) -> None:
        self.assertEqual(
            mutation.site_count(
                "def f():\n    return None\n"
            ),
            0,
        )

    def test_current_survivor_source_pin_is_accepted(self) -> None:
        key: mutation.MutationKey = (
            "calc.py",
            "constant",
            "_unused = 0",
            0,
        )
        survivors = {
            key: (
                "equivalent",
                "fixture classification",
            )
        }
        pins = {
            "calc.py": mutation.git_blob_id(
                (self.root / "calc.py").read_bytes()
            )
        }

        self.assertEqual(
            _survivor_pin_errors(
                self.root,
                survivors,
                pins,
            ),
            (),
        )

    def test_source_edit_invalidates_survivor_pin(self) -> None:
        key: mutation.MutationKey = (
            "calc.py",
            "constant",
            "_unused = 0",
            0,
        )
        survivors = {
            key: (
                "equivalent",
                "fixture classification",
            )
        }
        reviewed = mutation.git_blob_id(
            (self.root / "calc.py").read_bytes()
        )

        (self.root / "calc.py").write_text(
            CALC + "\nunrelated = 1\n"
        )

        errors = _survivor_pin_errors(
            self.root,
            survivors,
            {"calc.py": reviewed},
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "stale survivor review",
            errors[0],
        )
        self.assertIn(
            f"reviewed: {reviewed}",
            errors[0],
        )
        self.assertIn(
            "current:",
            errors[0],
        )

    def test_missing_and_obsolete_survivor_pins_are_rejected(
        self,
    ) -> None:
        key: mutation.MutationKey = (
            "calc.py",
            "constant",
            "_unused = 0",
            0,
        )
        survivors = {
            key: (
                "equivalent",
                "fixture classification",
            )
        }

        errors = _survivor_pin_errors(
            self.root,
            survivors,
            {
                "obsolete.py": "0" * 40,
            },
        )

        self.assertEqual(len(errors), 2)
        self.assertTrue(
            any(
                "calc.py: classified survivors have no reviewed source pin"
                in error
                for error in errors
            )
        )
        self.assertTrue(
            any(
                "obsolete.py: source pin has no classified survivors"
                in error
                for error in errors
            )
        )

    def test_a_mutant_that_changes_behaviour_is_killed(
        self,
    ) -> None:
        index = self.index_of(
            "arithmetic",
            "return a + b",
        )

        _, dead = mutation.killed(
            self.root,
            "calc.py",
            index,
            self.command,
        )

        self.assertTrue(dead)

    def test_source_meta_test_does_not_false_kill_equivalent_mutant(
        self,
    ) -> None:
        index = self.index_of(
            "constant",
            "_unused = 0",
        )

        found = mutation.survivors(
            self.root,
            "calc.py",
            [index],
            self.command,
        )

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].index, index)
        self.assertEqual(
            found[0].key,
            (
                "calc.py",
                "constant",
                "_unused = 0",
                0,
            ),
        )

    def test_a_mutant_that_hangs_is_killed(self) -> None:
        index = self.index_of(
            "arithmetic",
            "return a + b",
        )
        hang = [
            sys.executable,
            "-c",
            "import time; time.sleep(30)",
        ]

        _, dead = mutation.killed(
            self.root,
            "calc.py",
            index,
            hang,
            timeout=0.5,
        )

        self.assertTrue(dead)


@unittest.skipUnless(
    os.environ.get("SEMIROH_MUTATE"),
    "set SEMIROH_MUTATE to plant bugs in the model",
)
class SuiteMutationTests(unittest.TestCase):
    def test_the_suite_fails_on_planted_bugs(self) -> None:
        setting = os.environ["SEMIROH_MUTATE"]

        try:
            count = int(setting)
        except ValueError as exc:
            raise ValueError(
                "SEMIROH_MUTATE must be a positive integer"
            ) from exc

        if count < 1:
            raise ValueError(
                "SEMIROH_MUTATE must be a positive integer"
            )

        seed = int(
            os.environ.get(
                "SEMIROH_MUTATE_SEED",
                "1",
            )
        )
        batch = int(
            os.environ.get(
                "SEMIROH_MUTATE_BATCH",
                "0",
            )
        )
        shards = int(
            os.environ.get(
                "SEMIROH_MUTATE_SHARDS",
                "1",
            )
        )
        shard = int(
            os.environ.get(
                "SEMIROH_MUTATE_SHARD",
                "0",
            )
        )

        if batch < 0:
            raise ValueError(
                "SEMIROH_MUTATE_BATCH must be a non-negative integer"
            )

        pin_errors = _survivor_pin_errors(
            mutation.ROOT,
            SURVIVORS,
            SURVIVOR_SOURCE_BLOBS,
        )

        self.assertEqual(
            pin_errors,
            (),
            (
                "mutation campaign cannot use stale survivor classifications;"
                " re-review every affected survivor before updating its source"
                " pin:\n\n"
                + "\n\n".join(pin_errors)
            ),
        )

        targets = _targets_for_shard(
            TARGETS,
            shards,
            shard,
        )

        baseline = mutation.baseline(
            mutation.ROOT,
            mutation.SUITE,
        )

        self.assertEqual(
            baseline.returncode,
            0,
            (
                "mutation baseline failed on an unmodified repository copy; "
                "mutation results would be invalid\n\n"
                "stdout:\n"
                f"{baseline.stdout.decode(errors='replace')}\n"
                "stderr:\n"
                f"{baseline.stderr.decode(errors='replace')}"
            ),
        )

        escaped = []
        total_sites = 0
        selected_sites = 0
        targets_with_work = 0

        for target in targets:
            source = (
                mutation.ROOT / target
            ).read_text()
            sites = mutation.site_count(source)
            indexes = mutation.sample(
                source,
                count,
                seed,
                batch=batch,
            )

            total_sites += sites
            selected_sites += len(indexes)

            if indexes:
                targets_with_work += 1

            for mutant in mutation.survivors(
                mutation.ROOT,
                target,
                indexes,
                mutation.SUITE,
            ):
                classification = SURVIVORS.get(
                    mutant.key
                )

                if classification is None:
                    escaped.append(
                        f"{target}:site-{mutant.index}:"
                        f"line-{mutant.line} "
                        f"{mutant.kind}"
                        f"[{mutant.occurrence}]: "
                        f"{mutant.text}"
                    )

        print(
            "\nmutation batch "
            f"{batch}, shard {shard}/{shards}: "
            f"selected {selected_sites} sites across "
            f"{targets_with_work}/{len(targets)} shard targets; "
            f"{total_sites} mutation sites exist in this shard",
            flush=True,
        )
        print(
            "batch ordering: "
            f"count={count}, seed={seed}; "
            f"run batches 0..N until every shard selects 0 sites",
            flush=True,
        )

        if escaped:
            print(
                "\nunclassified surviving mutants:",
                flush=True,
            )

            for survivor in escaped:
                print(
                    f"  {survivor}",
                    flush=True,
                )

        self.assertEqual(
            escaped,
            [],
            (
                "unclassified surviving mutants; determine whether each is "
                "equivalent, intentionally unspecified, or a semantic test "
                "gap. Fix test gaps rather than classifying them."
            ),
        )


if __name__ == "__main__":
    unittest.main()
