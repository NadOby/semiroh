"""Regression tests for mutation campaign live progress reporting."""

from __future__ import annotations

import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import mutation
from tests import mutation_reporting


class MutationReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(
            temporary.cleanup
        )
        self.root = Path(
            temporary.name
        )

        (self.root / "first.py").write_text(
            "value = 1 + 2\n"
        )

        engine = (
            self.root
            / "tests"
            / "mutation.py"
        )
        engine.parent.mkdir()
        engine.write_text(
            "fixture mutation engine\n"
        )

    def test_slow_mutant_emits_progress_before_outcome(
        self,
    ) -> None:
        source = (
            self.root
            / "first.py"
        ).read_text()
        mutant = next(
            candidate
            for candidate
            in mutation.site_descriptions(
                source,
                "first.py",
            )
            if candidate.kind == "arithmetic"
        )

        def delayed_execute(
            root: Path,
            selected: mutation.Mutant,
            command: list[str],
        ) -> tuple[
            mutation.Mutant,
            bool,
            float,
        ]:
            time.sleep(0.10)

            return (
                selected,
                True,
                0.10,
            )

        report = (
            self.root
            / "heartbeat.jsonl"
        )

        with patch(
            "tests.mutation_reporting._execute_one",
            side_effect=delayed_execute,
        ):
            mutation_reporting.run_campaign(
                self.root,
                (mutant,),
                ["fixture-oracle"],
                {},
                report,
                {
                    "count": 1,
                    "seed": 1,
                    "batch": 0,
                    "shards": 1,
                    "shard": 0,
                },
                workers=1,
                progress_every=100,
                progress_interval_seconds=0.02,
                stream=io.StringIO(),
            )

        events = [
            json.loads(line)
            for line
            in report.read_text().splitlines()
        ]

        progress_index = next(
            index
            for index, event
            in enumerate(events)
            if (
                event["event"]
                == "progress"
                and event["completed"] == 0
            )
        )
        outcome_index = next(
            index
            for index, event
            in enumerate(events)
            if event["event"] == "mutant_outcome"
        )

        self.assertLess(
            progress_index,
            outcome_index,
        )
        self.assertEqual(
            events[
                progress_index
            ]["current_target"],
            "first.py",
        )


if __name__ == "__main__":
    unittest.main()
