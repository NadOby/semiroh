"""Regression tests for bytecode contracts found through mutation review."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

from semiroh import bytecode


ROOT = Path(__file__).resolve().parents[1]


class BytecodeRegressionTests(unittest.TestCase):
    def test_lowered_count_starts_at_zero_in_a_fresh_process(self) -> None:
        done = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from semiroh.bytecode import lowered_count; "
                    "print(lowered_count())"
                ),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            done.returncode,
            0,
            done.stderr,
        )
        self.assertEqual(
            done.stdout.strip(),
            "0",
        )

    def test_default_call_depth_limit_matches_specification(self) -> None:
        self.assertEqual(
            bytecode.CALL_DEPTH_LIMIT,
            100_000,
        )


if __name__ == "__main__":
    unittest.main()
