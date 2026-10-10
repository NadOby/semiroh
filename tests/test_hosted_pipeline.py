"""Plan-owned Task 30 bootstrap/admission acceptance; issue #66.

See docs/hosted_pipeline.md. The interface below is a provisional host-only
verification boundary, not a new SHEAR language capability:

    HostedSession(target_runtime).compiler_source_state
    .seed_manifest                   # roots, code_nodes, fixed_services,
                                     # compiler_source_state_id
    .rebuild_through(generation)     # GenerationReport sequence
    .compiler_artifacts(generation) # {(EntityID, VersionID): chunk}
    .invalidate_compiler_generation(generation)
    .attempt_seed_lower(node)        # diagnostic; fail closed if undeclared
    .prepare(compiler_generation=1)
    .produce(node), .admit(node, version, chunk, evidence)
    .run(entry, *args), .trace()

GenerationReport: generation, producer_generation,
compiler_source_state_id, artifact_ids. The corpus tests use the same
HostedSession boundary. These tests must fail before implementation; do not
replace the hosted implementation with lang.run or fake trace events.
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
from shear import machine
from shear.examples._support import program
from shear.hosted_bootstrap import AdmissionRejected, HostedSession
from shear.lang import Function, LanguageError, links, load
from shear.operations import OPERATIONS
from shear.reconcile import reconcile
from shear.syntax import parse


TARGET = EntityID("gh66_target")
CALLER = EntityID("gh66_caller")
RAISER = EntityID("gh66_raiser")
CATCHER = EntityID("gh66_catcher")
SEED_ROOTS = frozenset({
    EntityID("lower"), EntityID("upper"), EntityID("evals"),
    EntityID("seq_code"), EntityID("compile_node"),
})


def fixture():
    """A target program with no compiler entities or compiler links."""
    return Runtime(load(program({
        TARGET: Function(("x",), ("add", ("arg", "x"), ("lit", 3))),
        CALLER: Function(("x",), ("call", "callee", ("arg", "x"))),
        EntityID("gh66_caller.links"): links(CALLER, callee=TARGET),
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


def independent_seed_closure(state):
    """Traverse canonical definitions and link roles, not a seed builder.

    A function's entire owned executable subtree belongs to the seed;
    linked compiler functions (not cells) are transitively included.
    """
    pending = list(SEED_ROOTS)
    visited = set()
    expected = set()
    owners = {}

    while pending:
        function = pending.pop()
        if function in visited:
            continue
        visited.add(function)
        definition = relation_of(state.values[function])
        assert definition.kind == "definition", function

        for entity in state.owned_subtree(function):
            if entity == function:
                continue
            relation = relation_of(state.values[entity])
            assert relation is not None and relation.kind in OPERATIONS
            assert relation.kind != "invalid", entity
            key = (entity, state.values[entity].version_id)
            expected.add(key)
            owners[key] = function

        for role, target in definition.roles.items():
            if not role.startswith("link:"):
                continue
            targets = (target,) if isinstance(target, EntityID) else target
            for linked in targets:
                value = state.values[linked]
                relation = relation_of(value)
                if relation is not None and relation.kind == "definition":
                    pending.append(linked)

    return expected, owners


class CompilerBoundaryTests(unittest.TestCase):

    def test_compiler_free_target_does_not_acquire_compiler_code(self):
        target = fixture()
        target_before = snapshot(target.active.state)
        self.assertTrue(SEED_ROOTS.isdisjoint(target.active.state.values))

        session = HostedSession(target)
        compiler = session.compiler_source_state
        compiler_before = snapshot(compiler)

        self.assertNotEqual(compiler.id, target.active.state.id)
        self.assertTrue(SEED_ROOTS <= set(compiler.values))
        self.assertEqual(
            session.seed_manifest.compiler_source_state_id, compiler.id,
        )

        session.prepare(compiler_generation=1)
        self.assertEqual(session.run(CALLER, 4), 7)
        self.assertEqual(snapshot(target.active.state), target_before)
        self.assertEqual(snapshot(compiler), compiler_before)
        self.assertTrue(SEED_ROOTS.isdisjoint(target.active.state.values))

        executed = [e for e in session.trace()
                    if e.kind == "execute" and e.route == "admitted-host"]
        self.assertTrue(executed)
        self.assertTrue(all(e.target_state_id == target_before[0]
                            for e in executed))


class GenerationTests(unittest.TestCase):

    def test_three_generations_execute_their_predecessors(self):
        runtime = fixture()
        session = HostedSession(runtime)
        compiler = session.compiler_source_state
        target_before = snapshot(runtime.active.state)
        compiler_before = snapshot(compiler)

        # Independent observation at the existing machine entry boundary.
        # Implementation-generated reports/trace are insufficient by themselves.
        with mock.patch.object(machine, "_execute", wraps=machine._execute) as run_spy:
            reports = session.rebuild_through(3)

        self.assertEqual(
            [(r.generation, r.producer_generation) for r in reports],
            [(1, 0), (2, 1), (3, 2)],
        )
        self.assertEqual(
            [r.compiler_source_state_id for r in reports], [compiler.id] * 3,
        )
        compiler_calls = [
            call for call in run_spy.call_args_list
            if call.args and call.args[0].active.state.id == compiler.id
        ]
        self.assertGreaterEqual(len(compiler_calls), 3)
        self.assertTrue(any(call.args[2] == EntityID("compile_node")
                            for call in compiler_calls))

        expected_nodes, _ = independent_seed_closure(compiler)
        prior_ids = set()
        for g, report in enumerate(reports, 1):
            with self.subTest(generation=g):
                actual = session.compiler_artifacts(g)
                self.assertEqual(set(actual), expected_nodes)
                ids = set(report.artifact_ids)
                self.assertTrue(ids)
                self.assertFalse(prior_ids & ids)
                prior_ids |= ids

                # Independent oracle, with no host lowering in production.
                for (entity, _version), chunk in actual.items():
                    self.assertEqual(
                        chunk,
                        bytecode.lower(relation_of(compiler.values[entity])),
                    )

        self.assertEqual(
            session.compiler_artifacts(1), session.compiler_artifacts(2),
        )
        self.assertEqual(
            session.compiler_artifacts(2), session.compiler_artifacts(3),
        )

        events = session.trace()
        for g in (1, 2, 3):
            self.assertTrue(any(
                event.kind == "produce"
                and event.route == "shear-compiler"
                and event.generation == g
                and event.compiler_generation == g - 1
                for event in events
            ), f"No compiler production observed for G{g}")

        session.prepare(compiler_generation=3)
        with (
            mock.patch.object(bytecode, "chunk_of", side_effect=no_host_lowering),
            mock.patch.object(bytecode, "lower_value", side_effect=no_host_lowering),
        ):
            self.assertEqual(session.run(CALLER, 4), 7)

        self.assertEqual(snapshot(runtime.active.state), target_before)
        self.assertEqual(snapshot(compiler), compiler_before)

    def test_a_missing_predecessor_blocks_a_successor(self):
        # Two independent negative interventions: implausible ancestry
        # labels and unrelated execution do not satisfy this requirement.
        for predecessor in (1, 2):
            with self.subTest(missing_generation=predecessor):
                session = HostedSession(fixture())
                session.rebuild_through(predecessor)
                session.invalidate_compiler_generation(predecessor)
                with self.assertRaises(AdmissionRejected):
                    session.rebuild_through(predecessor + 1)

    def test_seed_is_the_exact_independently_derived_closure(self):
        session = HostedSession(fixture())
        compiler = session.compiler_source_state
        manifest = session.seed_manifest
        expected, owners = independent_seed_closure(compiler)

        self.assertEqual(manifest.compiler_source_state_id, compiler.id)
        self.assertEqual(set(manifest.roots), SEED_ROOTS)
        self.assertTrue(manifest.fixed_services)
        declared = {
            (entry.entity, entry.version) for entry in manifest.code_nodes
        }
        self.assertEqual(len(declared), len(manifest.code_nodes))
        self.assertEqual(declared, expected)
        for entry in manifest.code_nodes:
            self.assertEqual(owners[(entry.entity, entry.version)], entry.owner)

        # A second session must not silently authorize target-specific code.
        target = fixture()
        second = HostedSession(target)
        self.assertEqual(second.seed_manifest, manifest)
        foreign = body_node(target.active.state, TARGET)
        self.assertNotIn(foreign, compiler.values)
        with self.assertRaises(AdmissionRejected):
            second.attempt_seed_lower(foreign)
        self.assertEqual(second.seed_manifest, manifest)

        session.rebuild_through(3)
        lower_events = [e for e in session.trace() if e.kind == "host-lower"]
        self.assertTrue(lower_events)
        for event in lower_events:
            self.assertEqual(event.route, "declared-seed")
            self.assertIn((event.entity, event.version), expected)
        self.assertEqual(manifest, session.seed_manifest)

    def test_rebuild_does_not_define_or_activate_either_source(self):
        runtime = fixture()
        session = HostedSession(runtime)
        original = runtime.active.state
        compiler = session.compiler_source_state
        target_before, compiler_before = snapshot(original), snapshot(compiler)
        session.rebuild_through(3)
        self.assertIs(runtime.active.state, original)
        self.assertEqual(snapshot(runtime.active.state), target_before)
        self.assertEqual(snapshot(compiler), compiler_before)
        self.assertFalse(any(e.kind in {"define", "activate"}
                             for e in session.trace()))


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
        self.assertEqual(chunk, bytecode.lower(relation_of(self.state.values[self.node])))
        self.assertIsNotNone(self.session.admit(self.node, self.version, chunk, evidence))

    def test_forged_evidence_is_rejected(self):
        chunk, _ = self.session.produce(self.node)
        for fake in (object(), ("shear-compiler", TARGET.value),
                     ("admitted", self.node.value)):
            with self.subTest(evidence=type(fake).__name__):
                with self.assertRaises(AdmissionRejected):
                    self.session.admit(self.node, self.version, chunk, fake)

    def test_evidence_cannot_authorize_another_version(self):
        chunk, evidence = self.session.produce(self.node)
        with self.assertRaises(AdmissionRejected):
            self.session.admit(self.node, VersionID("incorrect-version"),
                               chunk, evidence)

    def test_evidence_cannot_authorize_modified_chunk(self):
        chunk, evidence = self.session.produce(self.node)
        altered = list(chunk)
        index = next(i for i, instruction in enumerate(altered)
                     if instruction[0] == "EVAL")
        altered[index] = ("EVAL", body_node(self.state, CALLER))
        self.assertNotEqual(tuple(altered), chunk)
        with self.assertRaises(AdmissionRejected):
            self.session.admit(self.node, self.version, tuple(altered), evidence)

    def test_linked_callee_is_admitted(self):
        self.assertEqual(self.session.run(CALLER, 5), 8)
        executed = [e for e in self.session.trace()
                    if e.kind == "execute" and e.route == "admitted-host"]
        self.assertTrue(executed)
        self.assertIn(self.node, {e.entity for e in executed})
        self.assertTrue(all(e.artifact_id and e.version is not None
                            for e in executed))


class ErrorOperatorTests(unittest.TestCase):

    def test_catch_raise_and_unmatched_filter(self):
        runtime = Runtime(load(program({
            RAISER: Function(("x",), ("raise", ("lit", "own_error"),
                                      ("arg", "x"))),
            CATCHER: Function(("x",), ("catch",
                  ("call", "raiser", ("arg", "x")), ("own_error",))),
            EntityID("gh66_catcher.links"): links(CATCHER, raiser=RAISER),
        })))
        session = HostedSession(runtime)
        session.prepare(compiler_generation=1)
        raised_node = body_node(runtime.active.state, RAISER)
        expected = ("failed", ("program", "own_error", 7,
                               (RAISER, raised_node)))
        self.assertEqual(session.run(CATCHER, 7), expected)
        with self.assertRaises(LanguageError) as caught:
            session.run(RAISER, 7)
        self.assertEqual(caught.exception.error, expected[1])


class CommandTests(unittest.TestCase):

    def command(self, source_text, edited_text=None):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "original.txt"
            source.write_text(source_text, encoding="utf-8")
            args = [
                sys.executable, "-m", "shear.hosted_bootstrap",
                "--source-file", str(source), "--entry", "answer",
                "--args-json", "[40]",
            ]
            if edited_text is not None:
                edited = Path(directory) / "edited.txt"
                edited.write_text(edited_text, encoding="utf-8")
                args.extend(["--edited-source-file", str(edited),
                             "--edit-mode", "prepare"])
            result = subprocess.run(args, capture_output=True, text=True,
                                    timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_compiler_free_source_text_to_admitted_execution(self):
        output = self.command("fn answer(x):\n    x + 2\n")
        self.assertEqual(output["result"], 42)
        self.assertEqual(output["route"], "admitted-host")
        self.assertTrue(output["executed_artifacts"])

    def test_reconciliation_stages_candidate_without_activation(self):
        original = "fn answer(x):\n    x + 1\n"
        edited = "fn answer(x):\n    x + 2\n"
        base = load(parse(original))
        candidate = reconcile(base, edited).destination
        entry = EntityID("answer")
        old_body = body_node(base, entry)
        new_body = body_node(candidate, entry)
        output = self.command(original, edited)

        self.assertEqual(output["result"], 41)
        self.assertEqual(output["candidate_result"], 42)
        self.assertEqual(output["route"], "admitted-host")
        self.assertEqual(output["base_state_id"], base.id.value)
        self.assertEqual(output["candidate_state_id"], candidate.id.value)
        self.assertEqual(output["active_state_id"], base.id.value)
        self.assertNotEqual(base.id, candidate.id)
        self.assertIn(entry, base.values)
        self.assertIn(entry, candidate.values)

        continuity = output["continuity"][entry.value]
        self.assertEqual(continuity["entity"], entry.value)
        self.assertEqual(continuity["original_body"], old_body.value)
        self.assertEqual(continuity["candidate_body"], new_body.value)
        self.assertEqual(continuity["original_version"],
                         base.values[old_body].version_id.value)
        self.assertEqual(continuity["candidate_version"],
                         candidate.values[new_body].version_id.value)
        self.assertTrue(output["executed_artifacts"])
        seen_states = {
            event["target_state_id"] for event in output["executed_artifacts"]
            if event["route"] == "admitted-host"
        }
        self.assertEqual(seen_states, {base.id.value, candidate.id.value})


if __name__ == "__main__":
    unittest.main()
