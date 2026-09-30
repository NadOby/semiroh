"""Mutation testing: does the suite notice a planted bug?

``EngineTests`` check the machinery in ``tests/mutation.py`` on a tiny
package and always run.

``SuiteMutationTests`` plant seeded single-site bugs in the production model
and run the whole suite against each.  They run only when ``SEMIROH_MUTATE``
is set to a positive number of mutants sampled per target:

    SEMIROH_MUTATE=1 python -m tests.test_mutation
    SEMIROH_MUTATE=40 SEMIROH_MUTATE_SEED=7 \
        python -m tests.test_mutation

Known survivors live in ``tests/mutation_catalog.py``.  Only reviewed
equivalent changes and intentionally unspecified behaviour may remain there.
A semantic test gap must receive a regression test instead of being
whitelisted.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import mutation
from tests.mutation_catalog import SURVIVORS, TARGETS


CALC = """\
_unused = 0


def add(a, b):
    return a + b
"""

CALC_TESTS = """\
import unittest

from calc import add


class AddTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)


if __name__ == "__main__":
    unittest.main()
"""


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
        for index in range(mutation.site_count(CALC)):
            _, mutant = mutation.mutate(
                CALC,
                "calc.py",
                index,
            )

            if mutant.kind == kind and mutant.text == text:
                return index

        raise AssertionError(
            f"no {kind} site on {text!r}"
        )

    def test_the_unmutated_copy_passes(self) -> None:
        done = subprocess.run(
            self.command,
            cwd=self.root,
            capture_output=True,
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
        self.assertEqual(
            (mutant.kind, mutant.line),
            ("arithmetic", 5),
        )

    def test_a_seeded_sample_repeats(self) -> None:
        big = "\n".join(
            f"x{n} = {n} + 1"
            for n in range(50)
        )

        first = mutation.sample(
            big,
            10,
            seed=3,
        )

        self.assertEqual(
            first,
            mutation.sample(big, 10, seed=3),
        )
        self.assertNotEqual(
            first,
            mutation.sample(big, 10, seed=4),
        )
        self.assertEqual(len(first), 10)

    def test_returning_none_is_not_a_mutation(self) -> None:
        self.assertEqual(
            mutation.site_count(
                "def f():\n    return None\n"
            ),
            0,
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

    def test_a_mutant_that_changes_nothing_survives(
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

        self.assertEqual(
            [(item.kind, item.text) for item in found],
            [("constant", "_unused = 0")],
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
        escaped = []

        for target in TARGETS:
            source = (
                mutation.ROOT / target
            ).read_text()
            indexes = mutation.sample(
                source,
                count,
                seed,
            )

            for mutant in mutation.survivors(
                mutation.ROOT,
                target,
                indexes,
                mutation.SUITE,
            ):
                key = (
                    target,
                    mutant.kind,
                    mutant.text,
                )
                classification = SURVIVORS.get(key)

                if classification is None:
                    escaped.append(
                        f"{target}:{mutant.line} "
                        f"{mutant.kind}: "
                        f"{mutant.text}"
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
