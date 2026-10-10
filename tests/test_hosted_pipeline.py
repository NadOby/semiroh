"""Plan-owned Task 30 bootstrap and admission acceptance.

See docs/hosted_pipeline.md and issue #66.

The public test boundary is provisional but normative for Execute:

HostedSession(runtime)
    .seed_manifest
    .rebuild_through(generation) -> tuple[GenerationReport, ...]
    .prepare(compiler_generation=1)
    .produce(node) -> (chunk, opaque_evidence)
    .admit(node, version, chunk, evidence)
    .run(entry, *args)
    .trace() -> tuple[RouteEvent, ...]

GenerationReport exposes generation, producer_generation,
source_state_id and artifact_ids.

Seed manifest exposes source_state_id, code_nodes and fixed_services.
Each code-node entry exposes entity and version.

RouteEvent retains Task 29's provenance fields and adds generation
and compiler_generation where applicable.

Tests deliberately fail until Execute implements this contract.
Do not introduce skips, ordinary-host fallback or fake trace events.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from shear import EntityID, Runtime, VersionID, bytecode, relation_of
from shear.examples import self_hosting
from shear.examples._support import program
from shear.hosted_bootstrap import AdmissionRejected, HostedSession
from shear.lang import Function, LanguageError, links, load


TARGET = EntityID("gh66_target")
CALLER = EntityID("gh66_caller")
RAISER = EntityID("gh66_raiser")
CATCHER = EntityID("gh66_catcher")


def fixture():
    return Runtime(load(program({
        **self_hosting.compiler_entities(),
        TARGET: Function(
            ("x",),
            ("add", ("arg", "x"), ("lit", 3)),
        ),
        CALLER: Function(
            ("x",),
            ("call", "callee", ("arg", "x")),
        ),
        EntityID("gh66_caller.links"): links(
            CALLER, callee=TARGET,
        ),
    })))


def body_node(state, function):
    return relation_of(state.values[function]).roles["body"]


def snapshot(state):
    return (
        state.id,
        tuple(sorted(
            (entity.value, value.version_id)
            for entity, value in state.values.items()
        )),
    )


def no_host_lowering(*args, **kwargs):
    raise AssertionError("Undeclared host lowering is forbidden")


class GenerationTests(unittest.TestCase):

    def test_three_real_generations(self):
        runtime = fixture()
        session = HostedSession(runtime)
        before = snapshot(runtime.active.state)

        reports = session.rebuild_through(3)

        self.assertEqual(
            [
                (r.generation, r.producer_generation)
                for r in reports
            ],
            [(1, 0), (2, 1), (3, 2)],
        )

        self.assertEqual(
            [r.source_state_id for r in reports],
            [before[0]] * 3,
        )

        artifact_sets = [
            frozenset(r.artifact_ids)
            for r in reports
        ]

        self.assertTrue(all(artifact_sets))

        for index, current in enumerate(artifact_sets):
            for previous in artifact_sets[:index]:
                self.assertFalse(
                    current & previous,
                    "Compiler generations reused artifact identity",
                )

        events = session.trace()

        for report in reports:
            productions = [
                e for e in events
                if e.kind == "produce"
                and e.route == "shear-compiler"
                and e.generation == report.generation
                and e.compiler_generation
                == report.producer_generation
            ]

            self.assertTrue(
                productions,
                f"G{report.generation} has no observed production",
            )

        session.prepare(compiler_generation=3)

        with (
            mock.patch.object(
                bytecode,
                "chunk_of",
                side_effect=no_host_lowering,
            ),
            mock.patch.object(
                bytecode,
                "lower_value",
                side_effect=no_host_lowering,
            ),
        ):
            self.assertEqual(session.run(CALLER, 4), 7)

        self.assertEqual(snapshot(runtime.active.state), before)

    def test_seed_is_finite_and_reproducible(self):
        runtime = fixture()

        first = HostedSession(runtime)
        second = HostedSession(runtime)

        manifest = first.seed_manifest

        self.assertEqual(manifest, second.seed_manifest)
        self.assertEqual(
            manifest.source_state_id,
            runtime.active.state.id,
        )
        self.assertTrue(manifest.code_nodes)
        self.assertTrue(manifest.fixed_services)

        declared = {
            (entry.entity, entry.version)
            for entry in manifest.code_nodes
        }

        self.assertEqual(
            len(declared),
            len(manifest.code_nodes),
            "Duplicate seed membership",
        )

        first.rebuild_through(3)

        seed_events = [
            event for event in first.trace()
            if event.kind == "host-lower"
        ]

        self.assertTrue(seed_events)

        for event in seed_events:
            with self.subTest(entity=event.entity):
                self.assertEqual(event.route, "declared-seed")
                self.assertIn(
                    (event.entity, event.version),
                    declared,
                )

        self.assertEqual(
            manifest,
            first.seed_manifest,
            "The bootstrap seed expanded during execution",
        )

    def test_rebuild_does_not_define_or_activate_source(self):
        runtime = fixture()
        original = runtime.active.state
        before = snapshot(original)

        session = HostedSession(runtime)
        session.rebuild_through(3)

        self.assertIs(runtime.active.state, original)
        self.assertEqual(snapshot(runtime.active.state), before)

        self.assertFalse(any(
            event.kind in {"define", "activate"}
            for event in session.trace()
        ))


class AdmissionTests(unittest.TestCase):

    def setUp(self):
        self.runtime = fixture()
        self.state = self.runtime.active.state
        self.node = body_node(self.state, TARGET)
        self.version = self.state.values[self.node].version_id

        self.session = HostedSession(self.runtime)
        self.session.prepare(compiler_generation=1)

    def test_genuine_compiler_output_matches_independent_oracle(self):
        chunk, evidence = self.session.produce(self.node)

        self.assertIsNotNone(evidence)

        relation = relation_of(self.state.values[self.node])

        # Host lowering is an oracle here, not an execution path.
        self.assertEqual(chunk, bytecode.lower(relation))

        admitted = self.session.admit(
            self.node, self.version, chunk, evidence,
        )
        self.assertIsNotNone(admitted)

    def test_forged_evidence_is_rejected(self):
        chunk, _ = self.session.produce(self.node)

        for fake in (
            object(),
            ("shear-compiler", TARGET.value),
            ("admitted", self.node.value),
        ):
            with self.subTest(evidence=type(fake).__name__):
                with self.assertRaises(AdmissionRejected):
                    self.session.admit(
                        self.node, self.version, chunk, fake,
                    )

    def test_evidence_cannot_authorize_another_version(self):
        chunk, evidence = self.session.produce(self.node)

        with self.assertRaises(AdmissionRejected):
            self.session.admit(
                self.node,
                VersionID("incorrect-version"),
                chunk,
                evidence,
            )

    def test_evidence_cannot_authorize_modified_chunk(self):
        chunk, evidence = self.session.produce(self.node)

        altered = list(chunk)
        index = next(
            i for i, instruction in enumerate(altered)
            if instruction[0] == "EVAL"
        )

        altered[index] = (
            "EVAL",
            body_node(self.state, CALLER),
        )

        self.assertNotEqual(tuple(altered), chunk)

        with self.assertRaises(AdmissionRejected):
            self.session.admit(
                self.node,
                self.version,
                tuple(altered),
                evidence,
            )

    def test_linked_callee_is_admitted(self):
        self.assertEqual(self.session.run(CALLER, 5), 8)

        executions = [
            e for e in self.session.trace()
            if e.kind == "execute"
            and e.route == "admitted-host"
        ]

        self.assertTrue(executions)

        self.assertIn(
            self.node,
            {e.entity for e in executions},
        )

        self.assertTrue(all(
            e.artifact_id and e.version is not None
            for e in executions
        ))


class ErrorOperatorTests(unittest.TestCase):

    def test_catch_raise_and_unmatched_filter(self):
        runtime = Runtime(load(program({
            RAISER: Function(
                ("x",),
                (
                    "raise",
                    ("lit", "own_error"),
                    ("arg", "x"),
                ),
            ),
            CATCHER: Function(
                ("x",),
                (
                    "catch",
                    ("call", "raiser", ("arg", "x")),
                    ("own_error",),
                ),
            ),
            EntityID("gh66_catcher.links"): links(
                CATCHER, raiser=RAISER,
            ),
        })))

        session = HostedSession(runtime)
        session.prepare(compiler_generation=1)

        raised_node = body_node(runtime.active.state, RAISER)

        expected = (
            "failed",
            (
                "program",
                "own_error",
                7,
                (RAISER, raised_node),
            ),
        )

        self.assertEqual(session.run(CATCHER, 7), expected)

        with self.assertRaises(LanguageError) as caught:
            session.run(RAISER, 7)

        self.assertEqual(caught.exception.error, expected[1])


class CommandTests(unittest.TestCase):

    def test_source_text_to_admitted_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "program.shear"
            source.write_text(
                "fn answer():\n"
                "    40 + 2\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "shear.hosted_bootstrap",
                    "--source-file",
                    str(source),
                    "--entry",
                    "answer",
                    "--args-json",
                    "[]",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

        self.assertEqual(
            result.returncode,
            0,
            result.stdout + result.stderr,
        )

        output = json.loads(result.stdout)

        self.assertEqual(output["result"], 42)
        self.assertEqual(output["route"], "admitted-host")
        self.assertTrue(output["executed_artifacts"])


if __name__ == "__main__":
    unittest.main()
