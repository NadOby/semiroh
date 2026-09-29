"""Unit tests for continuity inference beyond the acceptance tests
(docs/continuity_inference.md): the matching rules of ``semiroh.matching``,
moves between functions, and ``rebase``.
"""

import random
import unittest

from semiroh import EntityID, State, Value
from semiroh.lang import Function, _definition_of, define, function_at, links, load, run
from semiroh.matching import match, shapes
from semiroh.relations import Relation, relation_of
from semiroh.runtime import ActivationConflict, Runtime
from semiroh.syntax import parse
from semiroh.transforms import (
    TransformationConflict,
    rebase,
    touched,
    transform_with_mapping,
)

F = EntityID("f")
G = EntityID("g")
H = EntityID("h")


def lit(value) -> Relation:
    return Relation("lit", {}, value)


def op(kind: str, *operands: EntityID) -> Relation:
    return Relation(kind, {f"o{index}": node for index, node in enumerate(operands)})


def side(prefix: str, *relations: Relation) -> dict[EntityID, Relation]:
    """Nodes named ``<prefix><index>``; operands name earlier indexes."""

    return {EntityID(f"{prefix}{index}"): r for index, r in enumerate(relations)}


def o(index: int) -> EntityID:
    return EntityID(f"o{index}")


def n(index: int) -> EntityID:
    return EntityID(f"n{index}")


def random_tree(rng: random.Random, prefix: str, nodes: dict, depth: int) -> EntityID:
    entity = EntityID(f"{prefix}{len(nodes)}")
    nodes[entity] = None
    choice = rng.randrange(3) if depth > 0 else 0

    if choice == 0:
        relation = lit(rng.randrange(2))
    elif choice == 1:
        relation = op("neg", random_tree(rng, prefix, nodes, depth - 1))
    else:
        relation = op(
            "add",
            random_tree(rng, prefix, nodes, depth - 1),
            random_tree(rng, prefix, nodes, depth - 1),
        )

    nodes[entity] = relation
    return entity


def random_edit(rng: random.Random):
    """An edit of one to three entries over small trees full of repeats."""

    old: dict = {}
    new: dict = {}
    positions = []

    for _ in range(rng.randint(1, 3)):
        before = random_tree(rng, "o", old, rng.randint(0, 3))
        after = random_tree(rng, "n", new, rng.randint(0, 3))
        positions.append((after, before if rng.random() < 0.8 else None))

    return old, new, positions


def shuffled(rng: random.Random, nodes: dict) -> dict:
    items = list(nodes.items())
    rng.shuffle(items)
    return dict(items)


class RuleOneTests(unittest.TestCase):
    def test_a_shape_twice_among_the_old_keeps_neither(self) -> None:
        old = side("o", lit(1), lit(1))
        new = side("n", lit(1))

        self.assertEqual(match(old, new, []), {})

    def test_a_shape_twice_among_the_new_keeps_neither(self) -> None:
        old = side("o", lit(1))
        new = side("n", lit(1), lit(1))

        self.assertEqual(match(old, new, []), {})

    def test_a_unique_shape_is_kept_even_when_its_size_repeats(self) -> None:
        old = side("o", lit(1), lit(2))
        new = side("n", lit(2), lit(1))

        self.assertEqual(match(old, new, []), {n(0): o(1), n(1): o(0)})

    def test_the_largest_unique_subtree_keeps_its_ambiguous_leaves(self) -> None:
        # Each `lit 1` alone is ambiguous; inside the unique `add` they are
        # matched pairwise by role.
        old = side("o", lit(1), lit(1), op("add", o(0), o(1)))
        new = side("n", lit(1), lit(1), op("add", n(0), n(1)), op("neg", n(2)))

        self.assertEqual(
            match(old, new, [(n(3), o(2))]),
            {n(2): o(2), n(0): o(0), n(1): o(1)},
        )

    def test_a_larger_match_makes_the_remaining_copy_unique(self) -> None:
        # `lit 1` occurs twice on each side. Largest first, the unique `add`
        # takes one copy on each side, and the copy left is then unique
        # among what is not matched yet; smallest first would keep neither.
        old = side(
            "o", lit(1), lit(2), op("add", o(0), o(1)), lit(1),
            op("mul", o(2), o(3)),
        )
        new = side(
            "n", lit(1), lit(2), op("add", n(0), n(1)), lit(1),
            op("sub", n(3), n(2)),
        )

        self.assertEqual(
            match(old, new, [(n(4), o(4))]),
            {n(2): o(2), n(0): o(0), n(1): o(1), n(3): o(3)},
        )

    def test_a_repeated_large_subtree_keeps_only_what_is_unique_below(self) -> None:
        # `neg 5` twice among the new keeps neither; the unique `lit 7`
        # below the root is still kept on its own.
        old = side("o", lit(5), op("neg", o(0)), lit(7), op("add", o(1), o(2)))
        new = side(
            "n", lit(5), op("neg", n(0)), lit(5), op("neg", n(2)), lit(7),
            op("mul", n(1), n(3), n(4)),
        )

        self.assertEqual(match(old, new, [(n(5), o(3))]), {n(4): o(2)})

    def test_shapes_compare_other_endpoints_by_entity(self) -> None:
        call = EntityID("callee")
        other = EntityID("other")
        table: dict = {}
        old = shapes({o(0): Relation("call", {"function": call})}, table)
        same = shapes({n(0): Relation("call", {"function": call})}, table)
        differs = shapes({n(1): Relation("call", {"function": other})}, table)

        self.assertEqual(old[o(0)], same[n(0)])
        self.assertNotEqual(old[o(0)], differs[n(1)])

    def test_the_order_of_operands_in_one_role_is_part_of_the_shape(self) -> None:
        # `seq` holds its items in one role. Reordered, it is another shape:
        # the items are kept on their own, each by its content, and are
        # not paired by position under a matched `seq`.
        old = side("o", lit(1), lit(2), Relation("seq", {"items": (o(0), o(1))}))
        new = side("n", lit(2), lit(1), Relation("seq", {"items": (n(0), n(1))}))
        table: dict = {}

        self.assertNotEqual(
            shapes(old, table)[o(2)], shapes(new, table)[n(2)]
        )
        self.assertEqual(
            match(old, new, [(n(2), o(2))]),
            {n(0): o(1), n(1): o(0), n(2): o(2)},
        )


class RuleTwoTests(unittest.TestCase):
    def test_the_position_is_kept_when_the_kind_is_the_same(self) -> None:
        old = side("o", lit(1), lit(2), op("add", o(0), o(1)))
        new = side("n", lit(3), lit(4), op("add", n(0), n(1)))

        self.assertEqual(match(old, new, [(n(2), o(2))]), {n(2): o(2)})

    def test_a_changed_kind_or_no_position_keeps_nothing(self) -> None:
        old = side("o", lit(1), lit(2), op("add", o(0), o(1)))
        new = side("n", lit(3), lit(4), op("mul", n(0), n(1)))

        self.assertEqual(match(old, new, [(n(2), o(2))]), {})
        self.assertEqual(match(old, new, [(n(2), None)]), {})

    def test_a_position_matched_by_rule_one_is_not_reused(self) -> None:
        # The old body moves under the new root, which has the same kind.
        old = side("o", lit(1), lit(2), op("add", o(0), o(1)))
        new = side(
            "n", lit(1), lit(2), op("add", n(0), n(1)), lit(3),
            op("add", n(2), n(3)),
        )

        self.assertEqual(
            match(old, new, [(n(4), o(2))]),
            {n(2): o(2), n(0): o(0), n(1): o(1)},
        )

    def test_a_root_matched_by_rule_one_keeps_that_match(self) -> None:
        # Unwrapping: the new body is the old body's inner `add`. Rule 1
        # matches it to the inner node; the old root is free and has the
        # same kind, but the position only serves a root nothing matched.
        old = side(
            "o", lit(1), lit(2), op("add", o(0), o(1)), lit(3),
            op("add", o(2), o(3)),
        )
        new = side("n", lit(1), lit(2), op("add", n(0), n(1)))

        self.assertEqual(
            match(old, new, [(n(2), o(4))]),
            {n(2): o(2), n(0): o(0), n(1): o(1)},
        )

    def test_unwrapping_a_body_keeps_the_inner_node_and_drops_the_old_root(
        self,
    ) -> None:
        state = load(input_state({
            F: Function(
                ("x",),
                ("add", ("add", ("arg", "x"), ("lit", 1)), ("lit", 2)),
            ),
        }))
        root = _body(state)
        inner = relation_of(state.values[root]).roles["left"]

        result = define(state, {F: Function(("x",), ("add", ("arg", "x"), ("lit", 1)))})

        self.assertEqual(_body(result.destination), inner)
        self.assertFalse(result.destination.contains(root))
        self.assertEqual(result.mapping_for(root).destination_entities, ())
        self.assertEqual(result.mapping_for(inner).destination_entities, (inner,))
        self.assertEqual(run(Runtime(result.destination), F, 5), 6)


class MatchingProperties(unittest.TestCase):
    def test_the_result_does_not_depend_on_the_order_of_either_side(self) -> None:
        for seed in range(300):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                old, new, positions = random_edit(rng)
                expected = match(old, new, positions)

                for _ in range(3):
                    order = positions[:]
                    rng.shuffle(order)

                    self.assertEqual(
                        match(shuffled(rng, old), shuffled(rng, new), order),
                        expected,
                    )

    def test_every_kept_node_is_kept_once_by_a_rule(self) -> None:
        for seed in range(300):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                old, new, positions = random_edit(rng)
                kept = match(old, new, positions)
                table: dict = {}
                old_shapes = shapes(old, table)
                new_shapes = shapes(new, table)

                self.assertEqual(len(set(kept.values())), len(kept))

                for mine, theirs in kept.items():
                    self.assertEqual(new[mine].kind, old[theirs].kind)
                    self.assertTrue(
                        new_shapes[mine] == old_shapes[theirs]
                        or (mine, theirs) in positions
                    )


def input_state(entities: dict) -> State:
    return State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    })


class MoveTests(unittest.TestCase):
    def test_a_node_moved_to_another_function_changes_its_owner(self) -> None:
        state = load(input_state({
            F: Function(("x",), ("add", ("mul", ("lit", 3), ("lit", 4)), ("arg", "x"))),
            G: Function((), ("lit", 0)),
        }))
        product = next(
            node for node in state.owned_children(F)
            if relation_of(state.values[node]).kind == "mul"
        )
        result = define(state, {
            F: Function(("x",), ("arg", "x")),
            G: Function((), ("add", ("mul", ("lit", 3), ("lit", 4)), ("lit", 1))),
        })
        destination = result.destination

        self.assertIn(product, destination.owned_children(G))
        self.assertNotIn(product, destination.owned_children(F))
        self.assertEqual(
            destination.values[product].version_id,
            state.values[product].version_id,
        )
        self.assertEqual(result.mapping_for(product).destination_entities, (product,))
        self.assertIn(product, touched(result))
        self.assertEqual(run(Runtime(destination), G), 13)


def _body(state: State) -> EntityID:
    return _definition_of(state.values[F]).body


LABELS = "fn f(x):\n    label(a, 1) + label(b, 2) + label(c, 3) + label(d, 4) + x\n"


class RebaseTests(unittest.TestCase):
    def test_touched_holds_what_changes_value_owner_or_identity(self) -> None:
        state = load(parse("fn f(x):\n    label(k, 1) + x\n"))
        step = _definition_of(state.values[F]).labels["k"]
        same = define(state, {F: function_at(state, F)})
        leaf = define(state, {(F, "k"): ("lit", 10)})
        wrapped = define(state, {(F, "k"): ("mul", ("lit", 1), ("lit", 5))})
        created = set(wrapped.destination.values) - set(state.values)

        self.assertEqual(same.destination.id, state.id)
        self.assertEqual(touched(same), frozenset())
        self.assertEqual(touched(leaf), {step})
        # The kept `lit 1` moves under the new `mul`: its parent and the
        # function's label change, and it is itself unchanged.
        self.assertIn(step, wrapped.destination.values)
        self.assertEqual(touched(wrapped), created | {F, _body(state)})

    def test_a_created_node_whose_name_is_taken_moves_to_a_free_generation(
        self,
    ) -> None:
        state = load(parse("fn f(x):\n    label(k, 1) + x\n"))
        result = define(state, {(F, "k"): ("mul", ("lit", 2), ("lit", 3))})
        created = sorted(set(result.destination.values) - set(state.values))
        squatter = created[0]
        onto = transform_with_mapping(
            state, {squatter: 7}, {entity: entity for entity in state.values}
        )

        self.assertEqual(squatter.value.split("/")[1].split(".")[0], "1")

        rebased = rebase(result, onto)
        renamed = set(rebased.destination.values) - set(onto.destination.values)

        self.assertEqual(rebased.destination.values[squatter].content, 7)
        self.assertEqual(
            {entity.value.split(".")[0] for entity in renamed}, {"f/2"}
        )
        self.assertEqual(len(renamed), len(created))
        self.assertEqual(
            function_at(rebased.destination, F), function_at(result.destination, F)
        )

        runtime = Runtime(state)
        runtime.activate(onto)
        runtime.activate(result)

        self.assertEqual(runtime.active.state.id, rebased.destination.id)

    def test_two_results_that_create_one_function_conflict(self) -> None:
        state = load(parse("fn f(x):\n    x\n"))
        one = define(state, {H: Function((), ("lit", 1))})
        two = define(state, {H: Function((), ("lit", 2))})

        with self.assertRaises(TransformationConflict):
            rebase(two, one)

    def test_a_created_owned_entity_that_is_not_a_node_name_conflicts(
        self,
    ) -> None:
        # Only `<f>/<generation>.<index>` is renamed; any other created name
        # both results take is a conflict, even when owned by the function.
        state = load(parse("fn f(x):\n    x\n"))
        same = {entity: entity for entity in state.values}

        for name in ("f/1", "f/x.1", "f/1.x", "f/extra"):
            with self.subTest(name=name):
                entity = EntityID(name)
                one = transform_with_mapping(state, {entity: 1}, same, placements={entity: F})
                two = transform_with_mapping(state, {entity: 2}, same, placements={entity: F})

                with self.assertRaises(TransformationConflict):
                    rebase(two, one)

    def test_results_and_their_records_are_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from semiroh.transforms import TransformationDefinition

        state = load(parse("fn f(x):\n    label(k, 1) + x\n"))
        result = define(state, {(F, "k"): ("lit", 10)})
        definition = TransformationDefinition.create({}, {F: F})

        for record, field in (
            (result, "destination"),
            (result.mappings[0], "destination_entities"),
            (definition, "changes"),
        ):
            with self.subTest(record=type(record).__name__):
                with self.assertRaises(FrozenInstanceError):
                    setattr(record, field, None)

    def test_a_combined_state_that_fails_a_check_conflicts(self) -> None:
        # Disjoint touched sets, but the new call in f names g, which the
        # other result removes.
        state = load(parse("fn g(y):\n    y\n\nfn f(x):\n    x\n"))
        mappings = {
            entity: entity for entity in state.values
            if entity not in state.owned_subtree(G) | {G}
        }
        mappings[G] = ()
        removal = transform_with_mapping(state, {}, mappings)
        caller = define(state, {
            F: Function(("x",), ("call", "g", ("arg", "x"))),
            EntityID("f.links"): links(F, g=G),
        })

        self.assertTrue(touched(removal).isdisjoint(touched(caller)))

        with self.assertRaises(TransformationConflict):
            rebase(caller, removal)

        runtime = Runtime(state)
        runtime.activate(removal)

        with self.assertRaises(ActivationConflict):
            runtime.activate(caller)

        self.assertEqual(runtime.active.state.id, removal.destination.id)

    def test_disjoint_edits_that_create_nothing_commute(self) -> None:
        state = load(parse(LABELS))

        for seed in range(100):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                labels = ["a", "b", "c", "d"]
                rng.shuffle(labels)
                cut = rng.randint(1, 3)
                # Fresh values, so no new literal matches an old one by rule 1.
                values = rng.sample(range(10, 1000), 4)
                edits = {(F, label): ("lit", value) for label, value in zip(labels, values)}
                left = define(state, {key: edits[key] for key in list(edits)[:cut]})
                right = define(state, {key: edits[key] for key in list(edits)[cut:]})
                both = define(state, edits).destination.id

                self.assertEqual(rebase(left, right).destination.id, both)
                self.assertEqual(rebase(right, left).destination.id, both)

                runtime = Runtime(state)
                runtime.activate(left)
                runtime.activate(right)

                self.assertEqual(runtime.active.state.id, both)

    def test_a_rename_skips_a_name_the_result_keeps_and_the_other_removed(
        self,
    ) -> None:
        state = load(parse("fn f(x):\n    label(a, x + 1) + label(b, x + 2)\n"))
        state = define(
            state, {(F, "a"): ("add", ("mul", ("arg", "x"), ("lit", 3)), ("lit", 1))}
        ).destination
        # A second generation-2 node under `a`, while generation 1 is free.
        state = define(
            state, {(F, "a"): ("add", ("lit", 7), ("arg", "x"))}
        ).destination
        lone = EntityID("f/2.1")
        b = ("add", ("mul", ("arg", "x"), ("lit", 4)), ("lit", 2))
        a = ("add", ("arg", "x"), ("mul", ("arg", "x"), ("lit", 5)))
        result = define(state, {(F, "b"): b})
        onto = define(state, {(F, "a"): a})

        self.assertIn(lone, state.values)
        self.assertNotIn(lone, onto.destination.values)
        self.assertIn(EntityID("f/1.1"), result.destination.values)
        self.assertIn(EntityID("f/1.1"), onto.destination.values)

        rebased = rebase(result, onto)
        renamed = set(rebased.destination.values) - set(onto.destination.values)

        self.assertEqual({entity.value.split(".")[0] for entity in renamed}, {"f/3"})
        self.assertEqual(
            function_at(rebased.destination, F),
            function_at(define(state, {(F, "a"): a, (F, "b"): b}).destination, F),
        )

    def test_the_runtime_rebases_from_the_last_time_the_source_was_active(
        self,
    ) -> None:
        state = load(parse("fn f(x):\n    label(left, 1) + label(right, 2)\n"))
        away = define(state, {(F, "left"): ("lit", 10)})
        back = define(away.destination, {(F, "left"): ("lit", 1)})
        right = define(state, {(F, "right"): ("lit", 20)})
        late = define(state, {(F, "left"): ("lit", 30)})
        runtime = Runtime(state)

        for result in (away, back, right):
            runtime.activate(result)

        self.assertEqual(back.destination.id, state.id)

        runtime.activate(late)

        self.assertEqual(
            runtime.active.state.id,
            define(
                state, {(F, "left"): ("lit", 30), (F, "right"): ("lit", 20)}
            ).destination.id,
        )


class LabelScopeTests(unittest.TestCase):
    def test_a_node_outside_the_label_does_not_make_one_inside_ambiguous(
        self,
    ) -> None:
        state = load(parse("fn f(x):\n    label(k, x) + x\n"))
        inside, outside = EntityID("f/0.1"), EntityID("f/0.2")
        result = define(state, {(F, "k"): ("mul", ("arg", "x"), ("lit", 2))})
        after = result.destination
        labelled = _definition_of(after.values[F]).labels["k"]

        self.assertEqual(_definition_of(state.values[F]).labels["k"], inside)
        self.assertNotEqual(labelled, inside)
        self.assertIn(inside, relation_of(after.values[labelled]).roles.values())
        self.assertEqual(after.values[inside], state.values[inside])
        self.assertEqual(after.values[outside], state.values[outside])


if __name__ == "__main__":
    unittest.main()
