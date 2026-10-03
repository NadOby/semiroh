"""Explicit semantic oracle used by mutation subprocesses.

Mutation campaigns must run the same semantic tests against the unmodified
baseline and every mutant. Harness-integrity and survivor-catalog tests remain
mandatory in ordinary CI but are not mutation-kill oracles.
"""

from __future__ import annotations

import sys
import unittest

from tests.lanes import LANES, validate_partition


EXCLUDED_LANES = frozenset({"mutation"})


def modules() -> tuple[str, ...]:
    """Return the exact ordered module set used as the mutation oracle."""

    validate_partition()

    return tuple(
        module
        for lane, lane_modules in LANES.items()
        if lane not in EXCLUDED_LANES
        for module in lane_modules
    )


def suite() -> unittest.TestSuite:
    """Build the explicit mutation semantic suite."""

    loader = unittest.defaultTestLoader
    result = unittest.TestSuite()

    for module in modules():
        result.addTests(
            loader.loadTestsFromName(
                f"tests.{module}"
            )
        )

    return result


def command() -> list[str]:
    """Return the subprocess command for the semantic oracle."""

    return [
        sys.executable,
        "-m",
        "tests.mutation_oracle",
    ]


def main() -> int:
    result = unittest.TextTestRunner(
        verbosity=0,
        failfast=True,
    ).run(suite())

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
