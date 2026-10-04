"""Acceptance tests for the first program (docs/first_program.md).

These tests define the behaviour of `shear.lang`. The implementation is
done when they pass unchanged.

Programs are written in the input format and loaded into graph form
(graph_form.md); host edits use `define` or plain core transformations.
"""

import unittest

from shear import (
    ActivationRejected,
    CellContentRejected,
    CellDeclaration,
    EntityID,
    IntRange,
    Runtime,
    State,
    Value,
    relation_of,
    transform_with_mapping,
)
from shear.lang import Function, LanguageError, define, links, load, run

SQUARE = EntityID("square")
DOUBLE = EntityID("double")
TWICE = EntityID("twice")
QUAD = EntityID("quad")
QUAD_LINKS = EntityID("quad.links")
COUNTER = EntityID("counter")
INCREMENT = EntityID("increment")
INCREMENT_LINKS = EntityID("increment.links")


def double_function() -> Function:
    return Function(("x",), ("add", ("arg", "x"), ("arg", "x")))


def increment_function(step: int) -> Function:
    return Function(
        (),
        ("write", "counter", ("add", ("read", "counter"), ("lit", step))),
    )


def program(step: int = 1, counter_limit: int = 100) -> State:
    entities = {
        SQUARE: Function(("x",), ("mul", ("arg", "x"), ("arg", "x"))),
        DOUBLE: double_function(),
        QUAD: Function(
            ("x",),
            ("call", "double", ("call", "double", ("arg", "x"))),
        ),
        QUAD_LINKS: links(QUAD, double=DOUBLE),
        COUNTER: CellDeclaration(IntRange(0, counter_limit), 0),
        INCREMENT: increment_function(step),
        INCREMENT_LINKS: links(INCREMENT, counter=COUNTER),
    }

    return load(State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    }))


def identity(state: State) -> dict:
    """Declare every entity continuous with itself."""

    return {entity: entity for entity in state.values}


class RunningTests(unittest.TestCase):
    def test_runs_a_function(self) -> None:
        self.assertEqual(run(Runtime(program()), SQUARE, 7), 49)

    def test_calls_go_through_links(self) -> None:
        self.assertEqual(run(Runtime(program()), QUAD, 3), 12)

    def test_cells_keep_content_without_changing_program_state(self) -> None:
        state = program()
        runtime = Runtime(state)

        self.assertEqual(run(runtime, INCREMENT), 1)
        self.assertEqual(run(runtime, INCREMENT), 2)
        self.assertEqual(runtime.read(COUNTER), 2)
        self.assertEqual(runtime.active.id, state.id)

    def test_cell_constraints_apply_during_execution(self) -> None:
        runtime = Runtime(program(counter_limit=2))
        run(runtime, INCREMENT)
        run(runtime, INCREMENT)

        with self.assertRaises(CellContentRejected):
            run(runtime, INCREMENT)

        self.assertEqual(runtime.read(COUNTER), 2)

    def test_running_leaves_no_holds(self) -> None:
        runtime = Runtime(program())
        run(runtime, QUAD, 1)

        self.assertEqual(runtime.active.holds, frozenset())

        with self.assertRaises(LanguageError):
            run(runtime, SQUARE)  # missing argument

        self.assertEqual(runtime.active.holds, frozenset())

    def test_language_errors(self) -> None:
        broken = EntityID("broken")

        for body in (("frobnicate",), ("call", "missing")):
            with self.subTest(body=body):
                state = load(State.create({
                    broken: Value.create(broken, Function((), body)),
                }))

                with self.assertRaises(LanguageError):
                    run(Runtime(state), broken)


class SelfModificationTests(unittest.TestCase):
    def test_program_changes_behaviour_by_activation(self) -> None:
        runtime = Runtime(program(step=1))
        old = runtime.active
        self.assertEqual(run(runtime, INCREMENT), 1)

        source = runtime.active.state
        runtime.activate(define(source, {INCREMENT: increment_function(10)}))

        self.assertEqual(run(runtime, INCREMENT), 11)
        self.assertTrue(old.retired)

    def test_renamed_function_keeps_callers_working(self) -> None:
        runtime = Runtime(program())
        source = runtime.active.state
        mappings = identity(source)
        mappings[DOUBLE] = TWICE

        result = transform_with_mapping(
            source,
            {TWICE: source.values[DOUBLE].content},
            mappings,
        )
        runtime.activate(result)

        state = runtime.active.state
        self.assertFalse(state.contains(DOUBLE))
        calls = [
            relation_of(state.values[node])
            for node in state.owned_subtree(QUAD)
            if relation_of(state.values[node]).kind == "call"
        ]
        self.assertEqual(len(calls), 2)

        for call in calls:
            self.assertEqual(call.roles["target"], TWICE)

        self.assertEqual(run(runtime, QUAD, 3), 12)

    def test_rejected_activation_keeps_the_running_program(self) -> None:
        runtime = Runtime(program())
        run(runtime, INCREMENT)
        run(runtime, INCREMENT)
        source = runtime.active.state

        narrowed = transform_with_mapping(
            source,
            {COUNTER: CellDeclaration(IntRange(0, 1), 0)},
            identity(source),
        )

        with self.assertRaises(ActivationRejected):
            runtime.activate(narrowed)

        self.assertEqual(run(runtime, INCREMENT), 3)


if __name__ == "__main__":
    unittest.main()
