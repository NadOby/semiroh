"""Acceptance tests for code as graph form (roadmap.md task 4, D1).

Programs are written in the input format (Function bodies and links
relations) and loaded into graph form: each expression node is a relation
entity owned by its function. Renaming and removing functions are ordinary
core transformations; only whole-body replacement needs `define`.
"""

import unittest

from semiroh import (
    CellDeclaration,
    DanglingRelation,
    EntityID,
    IntRange,
    Runtime,
    State,
    Value,
    kind_of,
    relation_of,
    transform_with_mapping,
)
from semiroh.lang import Function, define, function_at, links, load, run

DOUBLE = EntityID("double")
TWICE = EntityID("twice")
QUAD = EntityID("quad")
QUAD_LINKS = EntityID("quad.links")
COUNTER = EntityID("counter")
INCREMENT = EntityID("increment")
INCREMENT_LINKS = EntityID("increment.links")
UNUSED = EntityID("unused")

FUNCTIONS = {
    DOUBLE: Function(("x",), ("add", ("arg", "x"), ("arg", "x"))),
    QUAD: Function(("x",), ("call", "double", ("call", "double", ("arg", "x")))),
    INCREMENT: Function(
        (),
        ("write", "counter", ("add", ("read", "counter"), ("lit", 1))),
    ),
    UNUSED: Function(("x",), ("if", ("lt", ("arg", "x"), ("lit", 0)), ("lit", 0), ("arg", "x"))),
}


def source_program() -> State:
    entities = {
        **FUNCTIONS,
        QUAD_LINKS: links(QUAD, double=DOUBLE),
        COUNTER: CellDeclaration(IntRange(0, 100), 0),
        INCREMENT_LINKS: links(INCREMENT, counter=COUNTER),
    }

    return State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    })


def identity(state: State, *except_for: EntityID) -> dict:
    return {entity: entity for entity in state.values if entity not in except_for}


def nodes(state: State, function: EntityID) -> dict:
    """Node entity -> VersionID for everything a function owns."""

    return {
        entity: state.values[entity].version_id
        for entity in state.owned_subtree(function)
    }


class LoadTests(unittest.TestCase):
    def test_code_lives_in_the_graph(self) -> None:
        state = load(source_program())

        for entity, value in state.values.items():
            with self.subTest(entity=entity):
                # No opaque tuple bodies and no links relations remain.
                self.assertNotEqual(kind_of(value.content), "function")
                relation = relation_of(value)
                self.assertFalse(relation is not None and relation.kind == "links")

        for function in FUNCTIONS:
            with self.subTest(function=function):
                owned = state.owned_subtree(function)
                self.assertTrue(owned)
                self.assertTrue(all(relation_of(state.values[n]) for n in owned))

    def test_functions_and_cells_keep_their_entities(self) -> None:
        state = load(source_program())

        for entity in (*FUNCTIONS, COUNTER):
            self.assertTrue(state.contains(entity))

    def test_load_is_deterministic_and_round_trips(self) -> None:
        state = load(source_program())

        self.assertEqual(load(source_program()).id, state.id)

        for function, source in FUNCTIONS.items():
            with self.subTest(function=function):
                self.assertEqual(function_at(state, function), source)

        self.assertIsNone(function_at(state, COUNTER))

    def test_loaded_program_runs(self) -> None:
        runtime = Runtime(load(source_program()))

        self.assertEqual(run(runtime, QUAD, 3), 12)
        self.assertEqual(run(runtime, INCREMENT), 1)
        self.assertEqual(runtime.read(COUNTER), 1)


class EditTests(unittest.TestCase):
    def test_define_replaces_one_body_and_nothing_else(self) -> None:
        state = load(source_program())
        old_nodes = nodes(state, INCREMENT)
        replacement = Function(
            (),
            ("write", "counter", ("add", ("read", "counter"), ("lit", 10))),
        )

        result = define(state, {INCREMENT: replacement})
        destination = result.destination

        self.assertEqual(function_at(destination, INCREMENT), replacement)

        # Every entity define creates is a new node owned by the function.
        created = set(destination.values) - set(state.values)
        self.assertTrue(created)
        self.assertEqual(created, set(nodes(destination, INCREMENT)))

        for node in old_nodes:
            self.assertFalse(destination.contains(node))
            self.assertEqual(result.mapping_for(node).destination_entities, ())

        # Other functions keep every node, with the same identity and version.
        for function in (DOUBLE, QUAD, UNUSED):
            self.assertEqual(nodes(destination, function), nodes(state, function))

        runtime = Runtime(state)
        run(runtime, INCREMENT)
        runtime.activate(result)

        self.assertEqual(run(runtime, INCREMENT), 11)

    def test_rename_is_an_ordinary_transformation(self) -> None:
        state = load(source_program())
        double_nodes = nodes(state, DOUBLE)

        result = transform_with_mapping(
            state,
            {TWICE: state.values[DOUBLE].content},
            {**identity(state, DOUBLE), DOUBLE: TWICE},
        )
        runtime = Runtime(state)
        runtime.activate(result)

        self.assertFalse(runtime.active.state.contains(DOUBLE))
        self.assertEqual(nodes(runtime.active.state, TWICE), double_nodes)
        self.assertEqual(run(runtime, QUAD, 3), 12)

    def test_removing_a_function_removes_its_nodes(self) -> None:
        state = load(source_program())
        unused_nodes = nodes(state, UNUSED)

        result = transform_with_mapping(state, {}, {UNUSED: ()})

        for node in unused_nodes:
            self.assertFalse(result.destination.contains(node))

        self.assertEqual(
            set(result.destination.values),
            set(state.values) - set(unused_nodes) - {UNUSED},
        )

    def test_removing_a_called_function_is_rejected(self) -> None:
        state = load(source_program())

        with self.assertRaises(DanglingRelation):
            transform_with_mapping(state, {}, {DOUBLE: ()})


if __name__ == "__main__":
    unittest.main()
