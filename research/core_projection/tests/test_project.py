"""Instrument tests for the projection.

These check the projection's own invariants on synthetic ``main`` states. They
assert no experimental outcome (equality, identity or composition results
against ``main`` belong in the report).
"""

from __future__ import annotations

import random
import unittest

from shear.canonical import canonical_serialize
from shear.identity import EntityID, StateID, VersionID
from shear.relations import Relation
from shear.state import State
from shear.values import Value

from core_projection.core import bisimilar, isomorphic
from core_projection.project import (
    Gap,
    Lost,
    Mode,
    ProjectionGap,
    decode,
    normalize_arity,
    project,
    rename_entities,
)
from core_projection.tests.main_support import eid, random_main_state
from core_projection.tests.support import seeds

MODES = (Mode.STRUCT, Mode.REF)


def state_of(**contents):
    return State.create(
        {EntityID(name): Value(EntityID(name), content) for name, content in contents.items()}
    )


def same(left, right):
    return canonical_serialize(left) == canonical_serialize(right)


class ProjectionInvariantTests(unittest.TestCase):
    def test_targets_exist_and_roots_are_distinct(self):
        for seed in seeds(150):
            for mode in MODES:
                with self.subTest(seed=seed, mode=mode):
                    state = random_main_state(random.Random(seed))
                    projection = project(state, mode)

                    # CState validates every target; the view covers every entity.
                    self.assertEqual(set(projection.view), set(state.values))
                    self.assertEqual(
                        len(set(projection.view.values())), len(state.values)
                    )
                    self.assertTrue(
                        all(root in projection.cstate for root in projection.view.values())
                    )

    def test_entities_share_nothing_except_references_and_ownership(self):
        for seed in seeds(150):
            for mode in MODES:
                with self.subTest(seed=seed, mode=mode):
                    state = random_main_state(random.Random(seed))
                    projection = project(state, mode)
                    cstate = projection.cstate
                    roots = set(projection.view.values())
                    owners = set(projection.ownership_handles.values())
                    indegree = {handle: 0 for handle in cstate}

                    for handle in cstate:
                        for targets in cstate.roles(handle).values():
                            for target in targets:
                                indegree[target] += 1

                    for handle in cstate:
                        if handle in owners:
                            self.assertEqual(indegree[handle], 0)
                        elif handle not in roots:
                            self.assertEqual(indegree[handle], 1, handle)

    def test_projection_is_deterministic_and_ignores_construction_order(self):
        for seed in seeds(100):
            for mode in MODES:
                with self.subTest(seed=seed, mode=mode):
                    rng = random.Random(seed)
                    state = random_main_state(rng)
                    entities = list(state.values)
                    rng.shuffle(entities)
                    owners = list(state.ownership)
                    rng.shuffle(owners)
                    shuffled = State.create(
                        {e: state.values[e] for e in entities},
                        {o: state.ownership[o] for o in owners},
                    )

                    first = project(state, mode)
                    again = project(shuffled, mode)

                    self.assertEqual(first.cstate, project(state, mode).cstate)
                    self.assertTrue(isomorphic(first.cstate, again.cstate))

    def test_struct_projection_ignores_entity_spelling(self):
        for seed in seeds(100):
            with self.subTest(seed=seed):
                state = random_main_state(random.Random(seed))
                renamed = rename_entities(state, lambda e: EntityID("x/" + e.value))

                self.assertTrue(
                    isomorphic(
                        project(state, Mode.STRUCT).cstate,
                        project(renamed, Mode.STRUCT).cstate,
                    )
                )

    def test_bool_and_int_stay_distinct(self):
        state = state_of(t=True, o=1, tup=(True, 1))

        for mode in MODES:
            with self.subTest(mode=mode):
                projection = project(state, mode)
                cstate, view = projection.cstate, projection.view
                items = cstate.roles(view[EntityID("tup")])["items"]

                self.assertNotEqual(
                    cstate.atom(view[EntityID("t")]), cstate.atom(view[EntityID("o")])
                )
                self.assertFalse(
                    bisimilar(cstate, view[EntityID("t")], cstate, view[EntityID("o")])
                )
                self.assertNotEqual(cstate.atom(items[0]), cstate.atom(items[1]))


class ReferenceModeTests(unittest.TestCase):
    def setUp(self):
        x, r = EntityID("x"), EntityID("r")
        self.state = State.create({
            x: Value(x, 7),
            r: Value(r, Relation("k", {"a": x, "b": (x, x)})),
        })

    def test_struct_targets_are_root_handles(self):
        projection = project(self.state, Mode.STRUCT)
        roles = projection.cstate.roles(projection.view[EntityID("r")])
        x = projection.view[EntityID("x")]

        self.assertEqual(roles["a"], (x,))
        self.assertEqual(roles["b"], (x, x))

    def test_ref_targets_are_fresh_atoms_holding_the_name(self):
        projection = project(self.state, Mode.REF)
        cstate = projection.cstate
        roles = cstate.roles(projection.view[EntityID("r")])
        targets = roles["a"] + roles["b"]

        self.assertEqual(len(set(targets)), 3)
        self.assertTrue(all(cstate.atom(t).value == "x" for t in targets))
        self.assertNotIn(projection.view[EntityID("x")], targets)

    def test_two_entities_with_equal_content_but_different_targets(self):
        # Adversarial case 1 shape: only the referenced identity differs.
        a, b, p, q = (EntityID(n) for n in "abpq")
        state = State.create({
            a: Value(a, 1),
            b: Value(b, 1),
            p: Value(p, Relation("k", {"t": a})),
            q: Value(q, Relation("k", {"t": b})),
        })

        for mode, expected in ((Mode.STRUCT, True), (Mode.REF, False)):
            with self.subTest(mode=mode):
                projection = project(state, mode)
                view = projection.view

                self.assertEqual(
                    bisimilar(projection.cstate, view[p], projection.cstate, view[q]),
                    expected,
                )

    def test_dangling_reference_is_a_gap_in_struct_only(self):
        state = state_of(t=(EntityID("ghost"),))

        with self.assertRaises(ProjectionGap):
            project(state, Mode.STRUCT)

        self.assertEqual(len(project(state, Mode.REF).cstate), 2)

    def test_bare_reference_entity_is_a_gap_in_struct_only(self):
        x, y = EntityID("x"), EntityID("y")
        state = State.create({x: Value(x, 1), y: Value(y, x)})

        with self.assertRaises(ProjectionGap):
            project(state, Mode.STRUCT)

        self.assertEqual(decode(project(state, Mode.REF))[y][1], "entity_id")

    def test_self_reference_is_a_cycle_in_struct(self):
        f = EntityID("f")
        state = State.create({f: Value(f, Relation("def", {"link:f": f}))})
        projection = project(state, Mode.STRUCT)
        root = projection.view[f]

        self.assertEqual(projection.cstate.roles(root)["link:f"], (root,))


class GapAndCollisionTests(unittest.TestCase):
    def test_payload_role_name_collision_is_a_gap(self):
        x, r = EntityID("x"), EntityID("r")
        state = State.create({
            x: Value(x, 1),
            r: Value(r, Relation("k", {"payload": x})),
        })

        for mode in MODES:
            with self.subTest(mode=mode), self.assertRaises(ProjectionGap):
                project(state, mode)

    def test_identity_inside_content_is_recorded_not_decoded(self):
        state = state_of(v=VersionID("v1"), s=StateID("s1"))

        for mode in MODES:
            with self.subTest(mode=mode):
                projection = project(state, mode)

                self.assertEqual(
                    sorted((g.entity.value, g.kind) for g in projection.gaps),
                    [("s", "state_id"), ("v", "version_id")],
                )
                self.assertIsInstance(projection.gaps[0], Gap)

        decoded = decode(project(state, Mode.STRUCT))

        self.assertEqual(decoded[EntityID("v")], Lost("v1"))


class OwnershipTests(unittest.TestCase):
    def test_one_owns_relation_per_owner_with_ordered_children(self):
        a, b, c, d = (EntityID(n) for n in "abcd")
        state = State.create(
            {e: Value(e, 0) for e in (a, b, c, d)},
            {a: [c, b], b: [d]},
        )
        projection = project(state, Mode.STRUCT)
        cstate, view = projection.cstate, projection.view
        handle = projection.ownership_handles[a]

        self.assertEqual(set(projection.ownership_handles), {a, b})
        self.assertEqual(cstate.atom(handle).value, "owns")
        self.assertEqual(cstate.roles(handle)["owner"], (view[a],))
        # main normalizes children to EntityID order: b before c.
        self.assertEqual(cstate.roles(handle)["owned"], (view[b], view[c]))

    def test_states_differing_only_in_ownership_are_not_isomorphic(self):
        a, b = EntityID("a"), EntityID("b")
        values = {a: Value(a, 0), b: Value(b, 0)}
        flat = State.create(values)
        owned = State.create(values, {a: [b]})

        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertFalse(
                    isomorphic(project(flat, mode).cstate, project(owned, mode).cstate)
                )

    def test_ownership_order_follows_entity_spelling(self):
        # Instrument fact, not an outcome: main stores children sorted by
        # EntityID, so the projection's `owned` sequence reads that order.
        a, b, c = (EntityID(n) for n in "abc")
        state = State.create({e: Value(e, 0) for e in (a, b, c)}, {a: [b, c]})
        flipped = rename_entities(state, lambda e: EntityID({"b": "z", "c": "y"}.get(e.value, e.value)))
        owned = []

        for item in (state, flipped):
            projection = project(item, Mode.STRUCT)
            owner = projection.ownership_handles[a]
            owned.append(
                [projection.entity_of(t).value for t in projection.cstate.roles(owner)["owned"]]
            )

        self.assertEqual(owned, [["b", "c"], ["y", "z"]])


class DecodeTests(unittest.TestCase):
    def test_round_trip_is_exact_without_one_element_endpoints(self):
        for seed in seeds(150):
            for mode in MODES:
                with self.subTest(seed=seed, mode=mode):
                    state = random_main_state(random.Random(seed))
                    decoded = decode(project(state, mode))

                    for entity, value in state.values.items():
                        self.assertTrue(same(decoded[entity], value.content), entity)

    def test_round_trip_with_one_element_endpoints_holds_modulo_arity(self):
        collapsed = 0

        for seed in seeds(150):
            for mode in MODES:
                with self.subTest(seed=seed, mode=mode):
                    state = random_main_state(random.Random(seed), unit_tuples=True)
                    decoded = decode(project(state, mode))

                    for entity, value in state.values.items():
                        self.assertTrue(
                            same(normalize_arity(decoded[entity]), normalize_arity(value.content))
                        )
                        collapsed += not same(decoded[entity], value.content)

        self.assertGreater(collapsed, 0)

    def test_single_endpoint_and_one_element_tuple_project_identically(self):
        x, one, tup = EntityID("x"), EntityID("one"), EntityID("tup")
        state = State.create({
            x: Value(x, 1),
            one: Value(one, Relation("k", {"a": x})),
            tup: Value(tup, Relation("k", {"a": (x,)})),
        })

        for mode in MODES:
            with self.subTest(mode=mode):
                projection = project(state, mode)
                view = projection.cstate, projection.view

                self.assertTrue(
                    bisimilar(view[0], view[1][one], view[0], view[1][tup])
                )

                decoded = decode(projection)

                self.assertTrue(same(decoded[one], state.values[one].content))
                self.assertFalse(same(decoded[tup], state.values[tup].content))
                self.assertTrue(
                    same(normalize_arity(decoded[tup]), normalize_arity(state.values[tup].content))
                )

    def test_normalize_arity_is_idempotent(self):
        for seed in seeds(100):
            with self.subTest(seed=seed):
                state = random_main_state(random.Random(seed), unit_tuples=True)

                for value in state.values.values():
                    once = normalize_arity(value.content)

                    self.assertTrue(same(normalize_arity(once), once))


class RenameTests(unittest.TestCase):
    def test_rename_is_consistent_and_invertible(self):
        for seed in seeds(100):
            with self.subTest(seed=seed):
                state = random_main_state(random.Random(seed))
                renamed = rename_entities(state, lambda e: EntityID("x/" + e.value))
                back = rename_entities(renamed, lambda e: EntityID(e.value[2:]))

                self.assertEqual(back, state)
                self.assertNotEqual(renamed.id, state.id)
                self.assertTrue(all(e.value.startswith("x/") for e in renamed.values))

    def test_rename_changes_references_inside_content(self):
        x, r = EntityID("x"), EntityID("r")
        state = State.create({
            x: Value(x, 1),
            r: Value(r, Relation("k", {"a": x}, payload=(x,))),
        })
        renamed = rename_entities(state, lambda e: EntityID(e.value.upper()))
        relation = renamed.values[EntityID("R")].content

        self.assertIn("X", repr(relation))
        self.assertNotIn("'x'", repr(relation))


if __name__ == "__main__":
    unittest.main()
