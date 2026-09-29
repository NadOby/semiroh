"""Acceptance tests for node edits (graph_form.md section 9, roadmap task 5)."""

import unittest

from semiroh import (
    ActivationRejected,
    CellDeclaration,
    EntityID,
    IntRange,
    Runtime,
    State,
    Value,
    relation_of,
)
from semiroh.lang import (
    Function,
    LanguageError,
    _definition_of,
    define,
    function_at,
    links,
    load,
    run,
)

COUNTER = EntityID("counter")
INCREMENT = EntityID("increment")
INCREMENT_LINKS = EntityID("increment.links")
TUNE = EntityID("tune")
TUNE_LINKS = EntityID("tune.links")
TRY = EntityID("try")
TRY_LINKS = EntityID("try.links")

INCREMENT_BODY = (
    "write",
    "counter",
    ("add", ("read", "counter"), ("label", "step", ("lit", 1))),
)
STEP_CODE = ("quote", ("lit", ("unquote", ("arg", "n"))))


def source(extra: dict | None = None) -> State:
    entities = {
        COUNTER: CellDeclaration(IntRange(0, 100), 0),
        INCREMENT: Function((), INCREMENT_BODY),
        INCREMENT_LINKS: links(INCREMENT, counter=COUNTER),
        TUNE: Function(("n",), ("activate", ("increment", "step"), STEP_CODE)),
        TUNE_LINKS: links(TUNE, increment=INCREMENT),
        TRY: Function(
            ("n",),
            ("trial", ("call", "increment"), ("increment", "step"), STEP_CODE),
        ),
        TRY_LINKS: links(TRY, increment=INCREMENT),
        **(extra or {}),
    }

    return State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    })


def nodes(state: State, function: EntityID) -> dict:
    return {
        entity: state.values[entity].version_id
        for entity in state.owned_subtree(function)
    }


def changed(before: dict, after: dict) -> set:
    return {entity for entity in before if after.get(entity) != before[entity]}


class LabelTests(unittest.TestCase):
    def test_label_is_transparent_and_kept(self) -> None:
        state = load(source())

        self.assertEqual(run(Runtime(state), INCREMENT), 1)
        self.assertEqual(function_at(state, INCREMENT), Function((), INCREMENT_BODY))

    def test_duplicate_label_is_rejected(self) -> None:
        body = ("add", ("label", "a", ("lit", 1)), ("label", "a", ("lit", 2)))

        with self.assertRaises(LanguageError):
            load(source({EntityID("twice"): Function((), body)}))


class HostNodeEditTests(unittest.TestCase):
    def test_replacing_one_node_changes_only_that_node(self) -> None:
        state = load(source())
        before = nodes(state, INCREMENT)

        result = define(state, {(INCREMENT, "step"): ("lit", 10)})
        after = nodes(result.destination, INCREMENT)

        self.assertEqual(set(after), set(before))
        self.assertEqual(len(changed(before, after)), 1)
        self.assertEqual(
            result.destination.values[INCREMENT].version_id,
            state.values[INCREMENT].version_id,
        )

        runtime = Runtime(state)
        runtime.activate(result)

        self.assertEqual(run(runtime, INCREMENT), 10)

    def test_a_replacement_may_keep_the_label_of_the_node_it_replaces(self) -> None:
        state = load(source())

        result = define(state, {(INCREMENT, "step"): ("label", "step", ("lit", 10))})

        runtime = Runtime(state)
        runtime.activate(result)

        self.assertEqual(run(runtime, INCREMENT), 10)

        # and the label still names the replacement
        again = define(runtime.active.state, {(INCREMENT, "step"): ("lit", 20)})
        runtime.activate(again)

        self.assertEqual(run(runtime, INCREMENT), 30)

    def test_replacing_with_a_larger_expression_and_back_renews_the_position(
        self,
    ) -> None:
        # A label edit that changes the node's kind gives the position a new
        # node (continuity_inference.md §2): the old `lit` disappears and
        # its parent changes to name the new one; nothing else changes.
        state = load(source())
        before = nodes(state, INCREMENT)
        step = _definition_of(state.values[INCREMENT]).labels["step"]
        parent = next(
            node for node in before
            if step in relation_of(state.values[node]).endpoints
        )

        larger = define(state, {(INCREMENT, "step"): ("add", ("lit", 2), ("lit", 3))})
        grown = nodes(larger.destination, INCREMENT)
        created = set(grown) - set(before)

        self.assertTrue(created)
        self.assertEqual(set(before) - set(grown), {step})
        self.assertEqual(larger.mapping_for(step).destination_entities, ())
        self.assertEqual(changed(before, grown), {step, parent})
        self.assertIn(
            _definition_of(larger.destination.values[INCREMENT]).labels["step"],
            created,
        )
        self.assertEqual(
            function_at(larger.destination, INCREMENT),
            Function(
                (),
                (
                    "write",
                    "counter",
                    (
                        "add",
                        ("read", "counter"),
                        ("label", "step", ("add", ("lit", 2), ("lit", 3))),
                    ),
                ),
            ),
        )

        smaller = define(larger.destination, {(INCREMENT, "step"): ("lit", 1)})

        for node in created:
            self.assertFalse(smaller.destination.contains(node))
            self.assertEqual(smaller.mapping_for(node).destination_entities, ())

        # Back to a literal: the same program, with one new node at the
        # position (the kind changed again), which the parent now names.
        back = nodes(smaller.destination, INCREMENT)

        self.assertEqual(
            function_at(smaller.destination, INCREMENT),
            function_at(state, INCREMENT),
        )
        self.assertEqual(changed(before, back), {step, parent})
        self.assertEqual(len(set(back) - set(before) - created), 1)

    def test_host_errors(self) -> None:
        state = load(source())

        for edits in (
            {(INCREMENT, "missing"): ("lit", 1)},
            {(INCREMENT, "step"): Function((), ("lit", 1))},
            {INCREMENT: ("lit", 1)},
            {(INCREMENT, "step"): ("add", ("label", "step", ("lit", 1)), ("lit", 1))},
        ):
            with self.subTest(edits=edits):
                with self.assertRaises(LanguageError):
                    define(state, edits)


class LanguageNodeEditTests(unittest.TestCase):
    def test_program_edits_one_node_of_another_function(self) -> None:
        runtime = Runtime(load(source()))
        before = nodes(runtime.active.state, INCREMENT)

        run(runtime, TUNE, 7, may_activate=True)

        self.assertEqual(len(changed(before, nodes(runtime.active.state, INCREMENT))), 1)
        self.assertEqual(run(runtime, INCREMENT), 7)

    def test_trial_of_a_node_edit_leaves_the_program_alone(self) -> None:
        runtime = Runtime(load(source()))
        state = runtime.active.state

        self.assertEqual(run(runtime, TRY, 5, may_activate=True), 5)
        self.assertEqual(runtime.active.id, state.id)
        self.assertEqual(runtime.read(COUNTER), 0)

    def test_node_edits_need_the_capability(self) -> None:
        runtime = Runtime(load(source()))
        state = runtime.active.state

        for entry in (TUNE, TRY):
            with self.subTest(entry=entry):
                with self.assertRaises(ActivationRejected):
                    run(runtime, entry, 3)

                self.assertEqual(runtime.active.id, state.id)

    def test_language_errors(self) -> None:
        for body in (
            ("activate", ("increment", "missing"), ("lit", ("lit", 1))),
            ("activate", ("increment", "step"), ("function", ("lit", ()), ("lit", ("lit", 1)))),
            ("trial", ("call", "increment"), ("increment", "missing"), ("lit", ("lit", 1))),
        ):
            with self.subTest(body=body):
                broken = EntityID("broken")
                runtime = Runtime(load(source({
                    broken: Function((), body),
                    EntityID("broken.links"): links(broken, increment=INCREMENT),
                })))
                state = runtime.active.state

                with self.assertRaises(LanguageError):
                    run(runtime, broken, may_activate=True)

                self.assertEqual(runtime.active.id, state.id)


if __name__ == "__main__":
    unittest.main()
