"""Thin acceptance tests for the code-as-graph spike (docs/spikes/code_as_graph.md).

These check the spike's four end-to-end criteria; they are not a
replacement for lang.py's own test coverage.
"""

import unittest

from semiroh import CellDeclaration, EntityID, IntRange, Runtime, State, Value
from semiroh.graph_code import (
    convert_program,
    edit_node,
    install_function,
    remove_function,
    rename_function,
    run_node,
)
from semiroh.relations import relation_of

from . import test_metaprogramming as mp


class PowerCompilerTests(unittest.TestCase):
    def test_compiler_runs_with_code_as_graph_and_installs_generated_code(self) -> None:
        graph_state = convert_program(mp.program())
        runtime = Runtime(graph_state, mp.CONTEXT)

        self.assertEqual(run_node(runtime, mp.POWER, 2), 1)
        self.assertIsNone(run_node(runtime, mp.COMPILE, 3, may_activate=True))
        self.assertEqual(run_node(runtime, mp.POWER, 2), 8)


class LocalEditTests(unittest.TestCase):
    def _fixture(self) -> tuple[State, EntityID]:
        counter = EntityID("counter")
        state = State.create({
            counter: Value(counter, CellDeclaration(IntRange(0, 100), 0)),
        })
        double = EntityID("double")
        result = install_function(
            state, double, ("x",), ("mul", ("arg", "x"), ("lit", 2))
        )
        return result.destination, double

    def test_editing_one_node_touches_only_that_node(self) -> None:
        state, double = self._fixture()
        nodes = state.owned_children(double)
        target = next(
            node for node in nodes
            if relation_of(state.values[node]).kind == "lit"
        )
        before = {node: state.values[node] for node in nodes if node != target}

        after = edit_node(state, target, payload=3).destination

        for entity, value in before.items():
            self.assertEqual(after.values[entity], value)

        self.assertEqual(relation_of(after.values[target]).payload, 3)


class OwnershipTests(unittest.TestCase):
    def test_creating_a_function_places_its_nodes_under_it(self) -> None:
        double = EntityID("double")
        after = install_function(
            State.create({}), double, ("x",), ("mul", ("arg", "x"), ("lit", 2))
        ).destination

        nodes = after.owned_children(double)
        self.assertTrue(nodes)
        self.assertEqual(after.owner_of(nodes[0]), double)

    def test_removing_a_function_removes_its_nodes(self) -> None:
        double = EntityID("double")
        state = install_function(
            State.create({}), double, ("x",), ("mul", ("arg", "x"), ("lit", 2))
        ).destination
        nodes = state.owned_children(double)

        after = remove_function(state, double)

        self.assertNotIn(double, after.values)
        for node in nodes:
            self.assertNotIn(node, after.values)


class RenameTests(unittest.TestCase):
    def test_rename_keeps_callers_working(self) -> None:
        callee = EntityID("callee")
        state = install_function(State.create({}), callee, (), ("lit", 1)).destination
        caller = EntityID("caller")
        state = install_function(state, caller, (), ("call", callee)).destination

        renamed = EntityID("callee2")
        after = rename_function(state, callee, renamed).destination

        self.assertNotIn(callee, after.values)
        self.assertEqual(run_node(Runtime(after), caller), 1)


if __name__ == "__main__":
    unittest.main()
