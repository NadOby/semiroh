"""Acceptance tests for constant folding as a graph transformation
(docs/constant_folding.md, roadmap task 9).
"""

import random
import unittest

from shear import CellDeclaration, EntityID, IntRange, Runtime, State
from shear.bytecode import lowered_count
from shear.examples._support import program
from shear.fold import fold_constants, sources_of
from shear.lang import (
    Function,
    LanguageError,
    _definition_of,
    define,
    function_at,
    links,
    load,
    run,
)
from shear.relations import relation_of

F = EntityID("f")
G = EntityID("g")
C = EntityID("c")


def state_of(body: tuple, params: tuple = ("x",), extra: dict | None = None) -> State:
    return load(program({
        F: Function(params, body),
        EntityID("f.links"): links(F, c=C, f=F),
        C: CellDeclaration(IntRange(0, 100), 0),
        **(extra or {}),
    }))


def body_of(state: State) -> tuple:
    return function_at(state, F).body


def nodes(state: State, function: EntityID = F) -> list[EntityID]:
    return sorted(state.owned_subtree(function), key=lambda item: item.value)


def root_of(state: State) -> EntityID:
    return _definition_of(state.values[F]).body


def x() -> tuple:
    return ("arg", "x")


class FoldsTests(unittest.TestCase):
    def test_arithmetic_on_literals_becomes_one_literal(self) -> None:
        state = state_of(("add", x(), ("mul", ("add", ("lit", 1), ("lit", 2)), ("lit", 5))))

        result = fold_constants(state)

        self.assertEqual(body_of(result.destination), ("add", x(), ("lit", 15)))

    def test_every_operation_it_folds(self) -> None:
        cases = {
            ("add", ("lit", 2), ("lit", 3)): 5,
            ("sub", ("lit", 2), ("lit", 3)): -1,
            ("mul", ("lit", 2), ("lit", 3)): 6,
            ("lt", ("lit", 2), ("lit", 3)): True,
            ("lt", ("lit", 3), ("lit", 3)): False,
            ("eq", ("lit", 3), ("lit", 3)): True,
            ("eq", ("lit", (1, 2)), ("lit", (1, 2))): True,
            ("eq", ("lit", 1), ("lit", 2)): False,
        }

        for expression, value in cases.items():
            with self.subTest(expression=expression):
                folded = fold_constants(state_of(expression)).destination

                self.assertEqual(body_of(folded), ("lit", value))
                self.assertIs(type(body_of(folded)[1]), type(value))

    def test_eq_is_semantic_equality_not_python_equality(self) -> None:
        # 1 == True in Python; the language keeps them apart.
        folded = fold_constants(state_of(("eq", ("lit", 1), ("lit", True)))).destination

        self.assertEqual(body_of(folded), ("lit", False))

    def test_if_on_a_constant_condition_becomes_the_branch(self) -> None:
        for cond, expected in ((True, ("arg", "x")), (False, ("mul", x(), x()))):
            with self.subTest(cond=cond):
                state = state_of(("if", ("lit", cond), x(), ("mul", x(), x())))

                self.assertEqual(
                    body_of(fold_constants(state).destination), expected
                )

    def test_a_computed_condition_folds_too(self) -> None:
        state = state_of(("if", ("lt", ("lit", 1), ("lit", 2)), ("add", x(), ("lit", 1)), ("lit", 0)))

        self.assertEqual(
            body_of(fold_constants(state).destination), ("add", x(), ("lit", 1))
        )

    def test_a_constant_if_inside_arithmetic_folds_the_whole_expression(self) -> None:
        state = state_of(("add", ("lit", 1), ("if", ("lit", True), ("lit", 2), x())))

        self.assertEqual(body_of(fold_constants(state).destination), ("lit", 3))

    def test_folds_inside_the_branches_that_stay(self) -> None:
        state = state_of(
            ("if", ("lt", x(), ("lit", 0)), ("add", ("lit", 1), ("lit", 1)), ("mul", ("lit", 3), ("lit", 3)))
        )

        self.assertEqual(
            body_of(fold_constants(state).destination),
            ("if", ("lt", x(), ("lit", 0)), ("lit", 2), ("lit", 9)),
        )

    def test_every_function_of_the_state_is_folded(self) -> None:
        state = state_of(
            ("add", ("lit", 1), ("lit", 1)),
            extra={
                G: Function((), ("mul", ("lit", 2), ("lit", 2))),
                EntityID("g.links"): links(G),
            },
        )

        folded = fold_constants(state).destination

        self.assertEqual(function_at(folded, F).body, ("lit", 2))
        self.assertEqual(function_at(folded, G).body, ("lit", 4))


class LeavesAloneTests(unittest.TestCase):
    def unchanged(self, body: tuple) -> None:
        state = state_of(body)
        result = fold_constants(state)

        self.assertEqual(result.destination.id, state.id)

    def test_what_would_raise_stays_and_still_raises(self) -> None:
        for body in (
            ("add", ("lit", "a"), ("lit", 1)),
            ("add", ("lit", True), ("lit", 1)),
            ("lt", ("lit", "a"), ("lit", 1)),
            ("if", ("lit", 1), ("lit", 2), ("lit", 3)),
            ("mul", ("lit", None), ("lit", 2)),
        ):
            with self.subTest(body=body):
                self.unchanged(body)

    def test_the_rest_of_the_expression_still_folds_around_an_error(self) -> None:
        state = state_of(
            ("add", ("add", ("lit", "a"), ("lit", 1)), ("mul", ("lit", 2), ("lit", 3)))
        )

        self.assertEqual(
            body_of(fold_constants(state).destination),
            ("add", ("add", ("lit", "a"), ("lit", 1)), ("lit", 6)),
        )

    def test_effects_and_unknowns_are_not_constants(self) -> None:
        for body in (
            ("add", ("read", "c"), ("lit", 1)),
            ("seq", ("write", "c", ("lit", 1)), ("lit", 2)),
            ("call", "f", ("lit", 1)),
            ("add", x(), ("lit", 1)),
        ):
            with self.subTest(body=body):
                self.unchanged(body)

    def test_a_literal_is_not_rewritten(self) -> None:
        self.unchanged(("lit", 5))

    def test_folding_twice_changes_nothing_more(self) -> None:
        once = fold_constants(
            state_of(("if", ("lt", ("lit", 1), ("lit", 2)), ("add", ("lit", 1), x()), ("lit", 0)))
        ).destination

        self.assertEqual(fold_constants(once).destination.id, once.id)


class DeclaredContinuityTests(unittest.TestCase):
    def setUp(self) -> None:
        # add(x, mul(add(1, 2), 5)): the constant subtree has five nodes.
        self.state = state_of(
            ("add", x(), ("mul", ("add", ("lit", 1), ("lit", 2)), ("lit", 5)))
        )
        self.result = fold_constants(self.state)
        self.nodes = nodes(self.state)
        self.root = root_of(self.state)
        self.mul = relation_of(self.state.values[self.root]).roles["right"]

    def test_the_folded_root_keeps_its_entity_and_takes_the_literal(self) -> None:
        after = self.result.destination

        self.assertEqual(relation_of(after.values[self.mul]).kind, "lit")
        self.assertIn(self.mul, after.values)

    def test_every_node_of_the_folded_subtree_is_merged_into_its_root(self) -> None:
        subtree = self.state.owned_subtree(F) - {
            self.root,
            relation_of(self.state.values[self.root]).roles["left"],
        }

        self.assertEqual(len(subtree), 5)
        self.assertEqual(set(sources_of(self.result, self.mul)), set(subtree))

        for source in subtree:
            self.assertEqual(
                self.result.mapping_for(source).destination_entities, (self.mul,)
            )

    def test_the_merged_nodes_are_gone_and_the_others_stay(self) -> None:
        after = self.result.destination
        survivors = {entity for entity in self.nodes if entity in after.values}

        self.assertEqual(len(survivors), 3)
        self.assertEqual(set(after.owned_subtree(F)), survivors)

    def test_untouched_nodes_keep_their_entity_and_version(self) -> None:
        after = self.result.destination
        argument = relation_of(self.state.values[self.root]).roles["left"]

        self.assertEqual(
            after.values[argument].version_id, self.state.values[argument].version_id
        )
        self.assertEqual(sources_of(self.result, argument), (argument,))
        self.assertEqual(
            after.values[C].version_id, self.state.values[C].version_id
        )

    def test_the_parent_of_a_folded_root_is_untouched(self) -> None:
        after = self.result.destination

        # The folded root keeps its EntityID, so its parent does not change.
        self.assertEqual(relation_of(after.values[self.root]).roles["right"], self.mul)
        self.assertEqual(
            after.values[self.root].version_id, self.state.values[self.root].version_id
        )

    def test_an_if_merges_itself_and_its_condition_into_the_chosen_branch(self) -> None:
        state = state_of(("if", ("lt", ("lit", 1), ("lit", 2)), ("add", x(), ("lit", 1)), ("lit", 0)))
        result = fold_constants(state)
        root = root_of(state)
        roles = relation_of(state.values[root]).roles
        chosen, other = roles["then"], roles["else"]
        cond_roles = relation_of(state.values[roles["cond"]]).roles
        condition_nodes = {roles["cond"], *cond_roles.values()}

        self.assertEqual(
            set(sources_of(result, chosen)), {chosen, root, *condition_nodes}
        )
        self.assertEqual(result.mapping_for(other).destination_entities, ())
        self.assertNotIn(other, result.destination.values)
        self.assertNotIn(root, result.destination.values)
        self.assertEqual(
            _definition_of(result.destination.values[F]).body, chosen
        )

    def test_folded_code_is_the_state_that_loading_it_gives(self) -> None:
        # How the code was reached does not enter its identity: folding
        # add(x, mul(add(1, 2), 5)) gives the state that loading
        # add(x, 15) gives.
        direct = state_of(("add", x(), ("lit", 15)))

        self.assertEqual(self.result.destination.id, direct.id)


class LabelsTests(unittest.TestCase):
    def test_a_label_inside_a_folded_subtree_follows_to_its_root(self) -> None:
        state = state_of(("add", x(), ("label", "k", ("add", ("lit", 1), ("lit", 2)))))

        folded = fold_constants(state).destination

        self.assertEqual(body_of(folded), ("add", x(), ("label", "k", ("lit", 3))))

        edited = define(folded, {(F, "k"): ("lit", 10)}).destination
        self.assertEqual(run(Runtime(edited), F, 1), 11)

    def test_a_label_inside_a_folded_subtree_keeps_pointing_at_the_merge(self) -> None:
        state = state_of(("add", ("label", "k", ("lit", 1)), ("lit", 2)))

        folded = fold_constants(state).destination

        self.assertEqual(body_of(folded), ("label", "k", ("lit", 3)))
        labels = _definition_of(folded.values[F]).labels
        self.assertEqual(labels, {"k": root_of(folded)})

    def test_a_label_on_code_that_would_disappear_stops_the_fold(self) -> None:
        state = state_of(
            ("if", ("lit", True), ("lit", 1), ("label", "gone", ("add", x(), ("lit", 1))))
        )

        result = fold_constants(state)

        self.assertEqual(result.destination.id, state.id)
        self.assertIn("gone", _definition_of(state.values[F]).labels)

    def test_a_label_on_an_if_follows_to_the_chosen_branch(self) -> None:
        state = state_of(("label", "k", ("if", ("lit", True), x(), ("lit", 0))))

        folded = fold_constants(state).destination

        self.assertEqual(body_of(folded), ("label", "k", x()))


class HotSwapTests(unittest.TestCase):
    def test_a_running_program_swaps_to_the_folded_code(self) -> None:
        state = state_of(("add", x(), ("mul", ("lit", 3), ("lit", 4))))
        runtime = Runtime(state)

        before = [run(runtime, F, n) for n in (0, 5)]
        runtime.activate(fold_constants(runtime.active.state))
        after = [run(runtime, F, n) for n in (0, 5)]

        self.assertEqual(before, after)
        self.assertEqual(body_of(runtime.active.state), ("add", x(), ("lit", 12)))

    def test_only_the_changed_nodes_are_lowered_again(self) -> None:
        state = state_of(("add", x(), ("mul", ("lit", 3), ("lit", 4))))
        runtime = Runtime(state)
        run(runtime, F, 1)
        before = lowered_count()

        runtime.activate(fold_constants(runtime.active.state))
        run(runtime, F, 1)

        # Only the folded literal: its parent still names it, and the
        # argument node keeps its chunk.
        self.assertEqual(lowered_count() - before, 1)

    def test_folding_a_recursive_function_while_it_is_called(self) -> None:
        body = (
            "if",
            ("lt", x(), ("lit", 1)),
            ("add", ("lit", 1), ("lit", 1)),
            ("add", ("call", "f", ("sub", x(), ("lit", 1))), ("mul", ("lit", 2), ("lit", 3))),
        )
        state = state_of(body)
        runtime = Runtime(state)
        expected = run(runtime, F, 6)

        runtime.activate(fold_constants(runtime.active.state))

        self.assertEqual(run(runtime, F, 6), expected)
        self.assertEqual(
            body_of(runtime.active.state),
            (
                "if",
                ("lt", x(), ("lit", 1)),
                ("lit", 2),
                ("add", ("call", "f", ("sub", x(), ("lit", 1))), ("lit", 6)),
            ),
        )


class Generator:
    """Seeded random integer programs, some of which raise."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)

    def number(self, depth: int) -> tuple:
        rng = self.rng

        if depth == 0:
            return rng.choice([
                ("lit", rng.randint(-2, 3)), ("lit", rng.randint(-2, 3)),
                x(), ("lit", "s"), ("lit", True),
            ])

        kind = rng.choice(["add", "sub", "mul", "if", "if", "seq", "leaf"])

        if kind in ("add", "sub", "mul"):
            return (kind, self.number(depth - 1), self.number(depth - 1))
        if kind == "if":
            return ("if", self.boolean(depth - 1), self.number(depth - 1), self.number(depth - 1))
        if kind == "seq":
            return ("seq", self.number(depth - 1), self.number(depth - 1))

        return self.number(0)

    def boolean(self, depth: int) -> tuple:
        rng = self.rng
        kind = rng.choice(["lt", "eq", "lit", "lit", "bad"])

        if kind == "lt":
            return ("lt", self.number(depth), self.number(depth))
        if kind == "eq":
            return ("eq", self.number(depth), self.number(depth))
        if kind == "bad":
            return ("lit", 1)

        return ("lit", rng.choice([True, False]))


def outcome(state: State, argument: int):
    try:
        return "value", run(Runtime(state), F, argument)
    except LanguageError as error:
        return "raised", type(error).__name__, str(error)


class FoldPreservesBehaviourTests(unittest.TestCase):
    def test_seeded_random_programs_behave_the_same_after_folding(self) -> None:
        folded_something = 0
        raised = 0

        for seed in range(150):
            with self.subTest(seed=seed):
                state = state_of(Generator(seed).number(4))
                result = fold_constants(state)
                after = result.destination

                for argument in (-1, 0, 3):
                    self.assertEqual(outcome(after, argument), outcome(state, argument))

                raised += outcome(state, 0)[0] == "raised"
                folded_something += after.id != state.id
                self.assertLessEqual(len(nodes(after)), len(nodes(state)))
                self.assertEqual(fold_constants(after).destination.id, after.id)

        self.assertGreater(folded_something, 60)
        self.assertGreater(raised, 10)

    def test_the_mapping_accounts_for_every_source_node(self) -> None:
        for seed in range(60):
            with self.subTest(seed=seed):
                state = state_of(Generator(seed).number(4))
                result = fold_constants(state)

                for source in nodes(state):
                    mapping = result.mapping_for(source)

                    self.assertIsNotNone(mapping)
                    for destination in mapping.destination_entities:
                        self.assertIn(destination, result.destination.values)

                    if source in result.destination.values:
                        self.assertIn(source, sources_of(result, source))


if __name__ == "__main__":
    unittest.main()
