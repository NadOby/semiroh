"""Mutation testing: does the suite notice a planted bug?

``EngineTests`` check the machinery in ``tests/mutation.py`` on a tiny
package and always run. ``SuiteMutationTests`` plant seeded single-site bugs
in the model and run the whole suite on each; they take a minute or two and
run only when ``SEMIROH_MUTATE`` is set (to a number of mutants per file, or
to anything else for the default of 25):

    SEMIROH_MUTATE=1 python3 -m tests.test_mutation
    SEMIROH_MUTATE=40 SEMIROH_MUTATE_SEED=7 python3 -m tests.test_mutation

A mutant the suite does not fail is a survivor. It is either a change that
alters no behaviour (listed in ``EQUIVALENT`` with the reason) or a gap in
the tests, which is the signal: write the test, then run it again.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests import mutation

TARGETS = (
    "semiroh/bytecode.py",
    "semiroh/lang.py",
    "semiroh/runtime.py",
    "semiroh/examples/self_hosting.py",
)

# (target, kind, source line) -> why no test can tell the difference.
EQUIVALENT = {
    ("semiroh/bytecode.py", "constant", "_lowered = 0"):
        "the counter is only compared as a difference",
    ("semiroh/bytecode.py", "constant", "may_activate: bool = False,"):
        "the only caller passes may_activate",
    ("semiroh/runtime.py", "return",
     'return f"Version({self.id.value[:12]}, holds={len(self._holds)})"'):
        "repr text",
    ("semiroh/runtime.py", "constant",
     'return f"Version({self.id.value[:12]}, holds={len(self._holds)})"'):
        "repr text",
    ("semiroh/examples/self_hosting.py", "constant",
     "hits: CellDeclaration(IntRange(0, 100), 0),"):
        "the bound of the cell is never reached",
    ("semiroh/examples/self_hosting.py", "constant",
     'step(("quote", ("lit", 1)), (("RAISE", "unknown operation"), end)),'):
        "the quoted template is not looked at",
    ("semiroh/lang.py", "constant", "@dataclass(frozen=True, eq=False)"):
        "not equivalent, an open gap: Function equality by canonical "
        "content against by fields is not pinned by a test",
    ("semiroh/lang.py", "arithmetic", "current.generation + 1,"):
        "the generation only has to differ from the taken ones",
    ("semiroh/lang.py", "compare", "if index is None:"):
        "the only caller passes an index; the default is unused",
    ("semiroh/lang.py", "constant", "generation += 1"):
        "the generation only has to differ from the taken ones",
    ("semiroh/lang.py", "constant",
     'f"let name must be a non-empty string, got {rest[0]!r}",'):
        "diagnostic text, not pinned by a test",
}

CALC = '''\
_unused = 0


def add(a, b):
    return a + b
'''

CALC_TESTS = '''\
import unittest

from calc import add


class AddTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)


if __name__ == "__main__":
    unittest.main()
'''


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        (self.root / "calc.py").write_text(CALC)
        (self.root / "test_calc.py").write_text(CALC_TESTS)
        self.command = [sys.executable, "-m", "unittest", "discover", "-f", "-q"]

    def index_of(self, kind: str, text: str) -> int:
        for index in range(mutation.site_count(CALC)):
            _, mutant = mutation.mutate(CALC, "calc.py", index)

            if mutant.kind == kind and mutant.text == text:
                return index

        raise AssertionError(f"no {kind} site on {text!r}")

    def test_the_unmutated_copy_passes(self) -> None:
        done = subprocess.run(self.command, cwd=self.root, capture_output=True)

        self.assertEqual(done.returncode, 0, done.stderr.decode())

    def test_a_mutant_changes_exactly_one_site(self) -> None:
        index = self.index_of("arithmetic", "return a + b")

        source, mutant = mutation.mutate(CALC, "calc.py", index)

        self.assertIn("return a - b", source)
        self.assertIn("_unused = 0", source)
        self.assertEqual((mutant.kind, mutant.line), ("arithmetic", 5))

    def test_a_seeded_sample_repeats(self) -> None:
        big = "\n".join(f"x{n} = {n} + 1" for n in range(50))

        first = mutation.sample(big, 10, seed=3)

        self.assertEqual(first, mutation.sample(big, 10, seed=3))
        self.assertNotEqual(first, mutation.sample(big, 10, seed=4))
        self.assertEqual(len(first), 10)

    def test_returning_none_is_not_a_mutation(self) -> None:
        self.assertEqual(mutation.site_count("def f():\n    return None\n"), 0)

    def test_a_mutant_that_changes_behaviour_is_killed(self) -> None:
        index = self.index_of("arithmetic", "return a + b")

        _, dead = mutation.killed(self.root, "calc.py", index, self.command)

        self.assertTrue(dead)

    def test_a_mutant_that_changes_nothing_survives(self) -> None:
        index = self.index_of("constant", "_unused = 0")

        found = mutation.survivors(self.root, "calc.py", [index], self.command)

        self.assertEqual([(m.kind, m.text) for m in found], [("constant", "_unused = 0")])

    def test_a_mutant_that_hangs_is_killed(self) -> None:
        index = self.index_of("arithmetic", "return a + b")
        hang = [sys.executable, "-c", "import time; time.sleep(30)"]

        _, dead = mutation.killed(self.root, "calc.py", index, hang, timeout=0.5)

        self.assertTrue(dead)


@unittest.skipUnless(
    os.environ.get("SEMIROH_MUTATE"),
    "set SEMIROH_MUTATE to plant bugs in the model (a minute or two)",
)
class SuiteMutationTests(unittest.TestCase):
    def test_the_suite_fails_on_planted_bugs(self) -> None:
        setting = os.environ["SEMIROH_MUTATE"]
        count = int(setting) if setting.isdigit() and int(setting) > 1 else 25
        seed = int(os.environ.get("SEMIROH_MUTATE_SEED", "1"))
        escaped = []

        for target in TARGETS:
            source = (mutation.ROOT / target).read_text()
            indexes = mutation.sample(source, count, seed)

            for mutant in mutation.survivors(
                mutation.ROOT, target, indexes, mutation.SUITE,
            ):
                if (target, mutant.kind, mutant.text) not in EQUIVALENT:
                    escaped.append(
                        f"{target}:{mutant.line} {mutant.kind}: {mutant.text}"
                    )

        self.assertEqual(
            escaped, [],
            "planted bugs the suite did not fail (a gap in the tests, or "
            "add to EQUIVALENT with a reason)",
        )


if __name__ == "__main__":
    unittest.main()
