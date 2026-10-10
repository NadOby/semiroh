"""Plan-owned behavioral acceptance for Task 29's execution-route spike.

The experimental API is intentionally absent from the Plan baseline.
The resulting red tests must become green through implementation, not
changes to the Plan's acceptance expectations.
"""

from __future__ import annotations

from importlib import import_module
import unittest
from unittest import mock

from shear import EntityID, Runtime, VersionID, bytecode, relation_of
from shear.examples import self_hosting
from shear.examples._support import program
from shear.lang import Function, define, function_at, links, load, run


TARGET = EntityID("route_target")
CALLER = EntityID("route_caller")
UNLINKED = EntityID("route_unlinked")
FORGER = EntityID("route_forger")


def fixture() -> Runtime:
    """Compiler, arithmetic target, linked caller and adversarial data."""
    entities = {
        **self_hosting.compiler_entities(),
        TARGET: Function(
            ("x",),
            ("add", ("arg", "x"), ("lit", 3)),
        ),
        CALLER: Function(
            ("x",),
            ("call", "callee", ("arg", "x")),
        ),
        EntityID("route_caller.links"): links(
            CALLER, callee=TARGET,
        ),
        UNLINKED: Function((), ("lit", 99)),
        FORGER: Function(
            (),
            (
                "tuple",
                ("lit", "shear-compiler"),
                ("lit", TARGET.value),
                ("lit", "claimed-version"),
                ("lit", "claimed-artifact"),
            ),
        ),
    }
    return Runtime(load(program(entities)))


def body_node(state, function: EntityID) -> EntityID:
    return relation_of(state.values[function]).roles["body"]


def replacement(
    chunk: tuple,
    opcode: str,
    instruction: tuple,
) -> tuple:
    """Alter an instruction without changing the chunk's tuple format."""
    result = list(chunk)
    matches = [
        index
        for index, current in enumerate(result)
        if current[0] == opcode
    ]
    if not matches:
        raise AssertionError(f"witness lacks {opcode}")
    result[matches[0]] = instruction
    return tuple(result)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.route = import_module("shear.execution_route_spike")
        self.runtime = fixture()
        self.state = self.runtime.active.state
        self.root = body_node(self.state, TARGET)

    def produce(self, node=None):
        return self.route.produce(
            self.runtime,
            self.root if node is None else node,
        )

    def admit(self, chunk, evidence, node=None, version=None):
        node = self.root if node is None else node
        version = (
            self.state.values[node].version_id
            if version is None else version
        )
        return self.route.admit(
            self.state, node, version, chunk, evidence,
        )

    def admit_function(self, function=TARGET):
        nodes = self.state.owned_subtree(function)
        for node in sorted(nodes):
            chunk, evidence = self.produce(node)
            self.admit(chunk, evidence, node)
        return nodes

    def test_compiler_produces_a_per_node_chunk(self):
        node = relation_of(self.state.values[self.root])
        self.assertEqual(node.kind, "add")

        chunk, evidence = self.produce()

        self.assertIsNotNone(evidence)
        self.assertEqual(chunk[-1], ("END",))
        self.assertEqual(chunk[-2], ("ADD",))
        self.assertEqual(
            tuple(ins[1] for ins in chunk if ins[0] == "EVAL"),
            (node.roles["left"], node.roles["right"]),
        )
        self.assertTrue(
            all(isinstance(ins, tuple) for ins in chunk)
        )

    def test_compiler_matches_independent_host_oracle(self):
        """Oracle invocation occurs only inside this test."""
        seen = set()

        for function in (TARGET, CALLER):
            for entity in sorted(self.state.owned_subtree(function)):
                node = relation_of(self.state.values[entity])
                seen.add(node.kind)

                with self.subTest(kind=node.kind, entity=entity):
                    produced, evidence = self.produce(entity)
                    expected = bytecode.lower(node)
                    self.assertEqual(produced, expected)
                    self.assertIsNotNone(evidence)

        self.assertEqual(seen, {"lit", "arg", "add", "call"})

    def test_genuine_production_is_admitted(self):
        chunk, evidence = self.produce()
        admitted = self.admit(chunk, evidence)
        self.assertIsNotNone(admitted)

    def test_arbitrary_python_evidence_is_rejected(self):
        chunk, _ = self.produce()

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(chunk, object())

    def test_shear_program_data_cannot_forge_evidence(self):
        chunk, _ = self.produce()
        fake = run(self.runtime, FORGER)

        self.assertIsInstance(fake, tuple)
        self.assertEqual(fake[0], "shear-compiler")
        self.assertEqual(fake[1], TARGET.value)

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(chunk, fake)

    def test_genuine_evidence_cannot_authorize_another_chunk(self):
        chunk, evidence = self.produce()
        foreign_node = body_node(self.state, UNLINKED)
        foreign_chunk, foreign_evidence = self.produce(foreign_node)

        self.assertNotEqual(chunk, foreign_chunk)

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(foreign_chunk, evidence)

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(chunk, foreign_evidence)

    def test_evidence_is_bound_to_its_node(self):
        chunk, evidence = self.produce()
        foreign = body_node(self.state, UNLINKED)

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(chunk, evidence, foreign)

    def test_wrong_version_is_rejected(self):
        chunk, evidence = self.produce()
        stale = VersionID("not-the-current-version")

        self.assertNotEqual(
            stale, self.state.values[self.root].version_id,
        )

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(chunk, evidence, version=stale)

    def test_modified_but_well_formed_output_is_rejected(self):
        chunk, evidence = self.produce()
        altered = replacement(chunk, "ADD", ("SUB",))

        self.assertNotEqual(altered, chunk)

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(altered, evidence)

    def test_foreign_child_reference_is_rejected(self):
        chunk, evidence = self.produce()
        foreign = body_node(self.state, UNLINKED)
        children = relation_of(
            self.state.values[self.root]
        ).endpoints

        self.assertNotIn(foreign, children)

        altered = replacement(
            chunk, "EVAL", ("EVAL", foreign),
        )

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(altered, evidence)

    def test_unlinked_function_operand_is_rejected(self):
        node = body_node(self.state, CALLER)
        chunk, evidence = self.produce(node)

        self.assertTrue(any(ins[0] == "CALL" for ins in chunk))

        altered = replacement(
            chunk, "CALL", ("CALL", UNLINKED, 1),
        )

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(altered, evidence, node)

    def test_admission_never_invokes_host_lowering(self):
        chunk, evidence = self.produce()

        with (
            mock.patch.object(
                bytecode, "lower",
                side_effect=AssertionError("host lowering in admission"),
            ),
            mock.patch.object(
                bytecode, "lower_value",
                side_effect=AssertionError("host lowering in admission"),
            ),
        ):
            self.assertIsNotNone(self.admit(chunk, evidence))

    def test_production_does_not_host_lower_the_target(self):
        self.assertNotIn(
            "_chunk", self.state.values[self.root].__dict__
        )

        target_relation = relation_of(
            self.state.values[self.root]
        )
        original_lower = bytecode.lower
        original_lower_value = bytecode.lower_value

        def guard_lower(relation):
            if relation == target_relation:
                raise AssertionError("host lowered the target relation")
            return original_lower(relation)

        def guard_value(value, entity, owner):
            if entity == self.root:
                raise AssertionError("host lowered the target node")
            return original_lower_value(value, entity, owner)

        with (
            mock.patch.object(
                bytecode, "lower", side_effect=guard_lower,
            ),
            mock.patch.object(
                bytecode, "lower_value", side_effect=guard_value,
            ),
        ):
            chunk, evidence = self.produce()

        self.assertIsNotNone(evidence)
        self.assertEqual(chunk[-1], ("END",))

    def test_rejected_artifact_cannot_execute_by_fallback(self):
        chunk, _ = self.produce()

        with self.assertRaises(self.route.AdmissionRejected):
            self.admit(chunk, object())

        with self.assertRaises(self.route.AdmissionRejected):
            self.route.run_admitted(self.runtime, TARGET, 4)

    def test_admitted_execution_preserves_semantic_source(self):
        original_state_id = self.state.id
        original_function = function_at(self.state, TARGET)
        nodes = self.state.owned_subtree(TARGET)
        versions = {
            node: self.state.values[node].version_id
            for node in nodes
        }

        self.admit_function()

        # Poison the ordinary host cache. The admitted path must not use it.
        self.state.values[self.root].__dict__["_chunk"] = (
            ("LIT", 777), ("END",),
        )

        original_chunk_of = bytecode.chunk_of
        original_lower_value = bytecode.lower_value

        def guard_chunk(state, entity, owner=None):
            if entity in nodes:
                raise AssertionError("ordinary host chunk fallback")
            return original_chunk_of(state, entity, owner)

        def guard_value(value, entity, owner):
            if entity in nodes:
                raise AssertionError("ordinary host lowering fallback")
            return original_lower_value(value, entity, owner)

        with (
            mock.patch.object(
                bytecode, "chunk_of", side_effect=guard_chunk,
            ),
            mock.patch.object(
                bytecode, "lower_value", side_effect=guard_value,
            ),
        ):
            actual = self.route.run_admitted(
                self.runtime, TARGET, 4,
            )

        self.assertEqual(actual, 7)
        self.assertEqual(self.runtime.active.state.id, original_state_id)
        self.assertEqual(
            function_at(self.runtime.active.state, TARGET),
            original_function,
        )
        self.assertEqual(
            {
                node: self.runtime.active.state.values[node].version_id
                for node in nodes
            },
            versions,
        )

    def test_admitted_linked_call_uses_admitted_callee(self):
        nodes = (
            self.admit_function(TARGET)
            | self.admit_function(CALLER)
        )
        original_chunk_of = bytecode.chunk_of

        def guard_chunk(state, entity, owner=None):
            if entity in nodes:
                raise AssertionError("linked call used host chunks")
            return original_chunk_of(state, entity, owner)

        with mock.patch.object(
            bytecode, "chunk_of", side_effect=guard_chunk,
        ):
            result = self.route.run_admitted(
                self.runtime, CALLER, 4,
            )

        self.assertEqual(result, 7)

    def test_trace_correlates_real_production_and_execution(self):
        self.assertEqual(self.route.trace(self.runtime), ())

        nodes = (
            self.admit_function(TARGET)
            | self.admit_function(CALLER)
        )
        self.assertEqual(
            self.route.run_admitted(self.runtime, CALLER, 4),
            7,
        )

        events = self.route.trace(self.runtime)
        self.assertIsInstance(events, tuple)

        for entity in sorted(nodes):
            version = self.state.values[entity].version_id
            relevant = [
                event
                for event in events
                if event.entity == entity and event.version == version
            ]

            with self.subTest(entity=entity):
                produced = [
                    e for e in relevant if e.kind == "produce"
                ]
                admitted = [
                    e for e in relevant if e.kind == "admit"
                ]
                executed = [
                    e for e in relevant if e.kind == "execute"
                ]

                self.assertEqual(len(produced), 1)
                self.assertEqual(len(admitted), 1)
                self.assertTrue(executed)

                producer = produced[0]
                self.assertEqual(producer.route, "shear-compiler")
                self.assertEqual(admitted[0].route, "host-admission")
                self.assertTrue(
                    all(e.route == "admitted-host" for e in executed)
                )

                # The producer must be identifiable as a SHEAR function,
                # not merely a label supplied with the target artifact.
                self.assertIsInstance(
                    producer.compiler_entity, EntityID,
                )
                self.assertIsInstance(
                    producer.compiler_version, VersionID,
                )
                self.assertNotIn(
                    producer.compiler_entity,
                    (TARGET, CALLER, UNLINKED, FORGER),
                )

                artifact = producer.artifact_id
                self.assertIsNotNone(artifact)
                self.assertTrue(
                    all(
                        e.artifact_id == artifact
                        for e in admitted + executed
                    )
                )

    def test_edit_invalidates_old_admitted_artifacts(self):
        self.admit_function()
        self.assertEqual(
            self.route.run_admitted(self.runtime, TARGET, 4), 7,
        )

        edit = define(
            self.runtime.active.state,
            {
                TARGET: Function(
                    ("x",),
                    ("add", ("arg", "x"), ("lit", 5)),
                ),
            },
        )
        self.runtime.activate(edit)

        self.assertNotEqual(
            self.runtime.active.state.id, self.state.id,
        )

        with self.assertRaises(self.route.AdmissionRejected):
            self.route.run_admitted(self.runtime, TARGET, 4)


if __name__ == "__main__":
    unittest.main()
