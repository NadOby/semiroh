"""Instrument tests for the observables O0-O3 and O5.

They check that each observable measures what it says it measures: counts
against brute force, classification rules against their table, builders
against the plan's description. They assert no experimental outcome; what
``main`` and the candidate actually say belongs in the report.
"""

from __future__ import annotations

import random
import unittest
from collections import Counter
from dataclasses import replace
from itertools import combinations

from shear.canonical import CanonicalNode
from shear.equality import semantic_equal
from shear.identity import EntityID
from shear.lang import load
from shear.relations import Relation, relation_of
from shear.state import State
from shear.syntax import parse
from shear.values import Value

from core_projection import churn, identity, observables
from core_projection.core import Atom, CState, bisimilar
from core_projection.project import Mode, decode, normalize_arity, project
from core_projection.rows import AGREE, GAP, PREDICTED, UNEXPECTED, Row, aggregate, counts
from core_projection.tests.main_support import eid, random_main_state
from core_projection.tests.support import seeds

MODES = (Mode.STRUCT, Mode.REF)


def state_of(**contents):
    return State.create(
        {EntityID(name): Value(EntityID(name), content) for name, content in contents.items()}
    )


def by_class(rows, observable):
    return Counter({
        classification: n
        for (name, classification), n in counts(rows).items()
        if name == observable
    })


class RowTests(unittest.TestCase):
    def test_aggregate_conserves_counts_and_caps_examples(self):
        rows = [Row("c", "O", "a", "b", AGREE, examples=(str(i),)) for i in range(7)]
        rows.append(Row("c", "O", "a", "c", UNEXPECTED))
        folded = aggregate(rows)

        self.assertEqual([row.count for row in folded], [7, 1])
        self.assertEqual(folded[0].examples, ("0", "1", "2"))
        self.assertEqual(sum(row.count for row in folded), len(rows))

    def test_unknown_classification_is_rejected(self):
        with self.assertRaises(ValueError):
            Row("c", "O", "a", "b", "maybe")


class RoundTripRowTests(unittest.TestCase):
    def test_one_element_tuple_is_exact_failure_but_agrees_modulo_arity(self):
        unit = Relation("call", {"args": (eid(1),)})
        state = state_of(e0=unit, e1=1)

        for mode in MODES:
            with self.subTest(mode=mode):
                rows = observables.roundtrip_rows("c", state)
                exact = by_class(rows, f"O0/{mode.name}/exact")
                modulo = by_class(rows, f"O0/{mode.name}/modulo-arity")

                self.assertEqual(exact, Counter({PREDICTED: 1, AGREE: 1}))
                self.assertEqual(modulo, Counter({AGREE: 2}))

    def test_classification_matches_direct_recomputation(self):
        for seed in seeds(120):
            with self.subTest(seed=seed):
                state = random_main_state(random.Random(seed), unit_tuples=True)
                rows = observables.roundtrip_rows("c", state)

                for mode in MODES:
                    decoded = decode(project(state, mode))
                    expected_exact, expected_modulo = Counter(), Counter()

                    for entity, value in state.values.items():
                        got = decoded[entity]
                        same = got == value.content or (
                            observables._key(got) == observables._key(value.content)
                        )
                        modulo = observables._key(normalize_arity(got)) == observables._key(
                            normalize_arity(value.content)
                        )
                        expected_exact[AGREE if same else PREDICTED if modulo else UNEXPECTED] += 1
                        expected_modulo[AGREE if modulo else UNEXPECTED] += 1

                    self.assertEqual(by_class(rows, f"O0/{mode.name}/exact"), expected_exact)
                    self.assertEqual(by_class(rows, f"O0/{mode.name}/modulo-arity"), expected_modulo)

    def test_identity_inside_content_is_a_gap(self):
        node = CanonicalNode(("__type__", "version_id", "v1"))
        rows = observables.roundtrip_rows("c", state_of(e0=(node,)))

        self.assertEqual(by_class(rows, "O0/STRUCT/exact"), Counter({GAP: 1}))
        self.assertEqual(by_class(rows, "O0/REF/modulo-arity"), Counter({GAP: 1}))

    def test_bare_reference_is_a_gap_in_struct_only(self):
        rows = observables.roundtrip_rows("c", state_of(e0=eid(1), e1=1))

        self.assertEqual(by_class(rows, "O0/STRUCT/exact"), Counter({GAP: 1}))
        self.assertNotIn(GAP, by_class(rows, "O0/REF/exact"))


class EqualityRowTests(unittest.TestCase):
    def brute_force(self, state, mode):
        projection = project(state, mode)
        outcomes = Counter()

        for left, right in combinations(sorted(state.values), 2):
            main = semantic_equal(state.values[left], state.values[right])
            candidate = bisimilar(
                projection.cstate, projection.view[left],
                projection.cstate, projection.view[right],
            )
            outcomes[(main, candidate)] += 1

        return outcomes

    def test_pair_outcomes_match_brute_force(self):
        words = {"equal": True, "unequal": False}

        for seed in seeds(150):
            for mode in MODES:
                with self.subTest(seed=seed, mode=mode):
                    state = random_main_state(random.Random(seed), max_entities=8)
                    rows = [
                        row for row in observables.equality_rows("c", state)
                        if row.observable == f"O1/{mode.name}"
                    ]
                    measured = Counter()

                    for row in rows:
                        measured[(words[row.main_result], words[row.candidate_result])] += row.count

                    self.assertEqual(measured, self.brute_force(state, mode))

    def test_classes_are_the_bisimilarity_partition(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                state = random_main_state(random.Random(seed), max_entities=8)
                entities = sorted(state.values)

                for mode in MODES:
                    projection = project(state, mode)
                    classes = observables.bisimulation_classes(projection, entities)

                    for i, j in combinations(range(len(entities)), 2):
                        self.assertEqual(
                            classes[i] == classes[j],
                            bisimilar(
                                projection.cstate, projection.view[entities[i]],
                                projection.cstate, projection.view[entities[j]],
                            ),
                        )

    def enriched(self, rng):
        """A random state plus, per relation, a twin that differs only in arity
        and a twin that refers to clones of its referents instead."""

        state = random_main_state(rng, max_entities=5, unit_tuples=True)
        values = dict(state.values)

        for entity in sorted(state.values):
            relation = relation_of(state.values[entity])

            if relation is None:
                continue

            arity = {
                role: (endpoint,) if isinstance(endpoint, EntityID) else endpoint
                for role, endpoint in relation.roles.items()
            }
            values[EntityID(f"w.{entity.value}")] = Value(
                EntityID(f"w.{entity.value}"), Relation(relation.kind, arity, relation.payload)
            )
            cloned = {}

            def clone(target):
                name = EntityID(f"k.{target.value}")
                values[name] = Value(name, state.values[target].content)

                return name

            for role, endpoint in relation.roles.items():
                cloned[role] = (
                    clone(endpoint)
                    if isinstance(endpoint, EntityID)
                    else tuple(clone(t) for t in endpoint)
                )

            values[EntityID(f"v.{entity.value}")] = Value(
                EntityID(f"v.{entity.value}"), Relation(relation.kind, cloned, relation.payload)
            )

        return State.create(values)

    def test_classification_counts_match_independent_recomputation(self):
        key = observables._key

        for seed in seeds(120):
            with self.subTest(seed=seed):
                state = self.enriched(random.Random(seed))
                rows = observables.equality_rows("c", state)

                for mode in MODES:
                    projection = project(state, mode)
                    expected = Counter()

                    for left, right in combinations(sorted(state.values), 2):
                        a, b = state.values[left], state.values[right]
                        main = semantic_equal(a, b)
                        candidate = bisimilar(
                            projection.cstate, projection.view[left],
                            projection.cstate, projection.view[right],
                        )

                        if main == candidate:
                            expected[AGREE] += 1
                            continue

                        row = observables._equality_mismatch(
                            "c", "O1", mode, main,
                            key(normalize_arity(a.content)) == key(normalize_arity(b.content)),
                            key(observables._mask(a.content)) == key(observables._mask(b.content)),
                            key(observables._mask(normalize_arity(a.content)))
                            == key(observables._mask(normalize_arity(b.content))),
                            (),
                        )
                        expected[(row.classification, row.note)] += 1

                    measured = Counter()

                    for row in rows:
                        if row.observable != f"O1/{mode.name}":
                            continue

                        measured[
                            AGREE if row.classification == AGREE else (row.classification, row.note)
                        ] += row.count

                    self.assertEqual(measured, expected)

    def test_enriched_states_exercise_every_prediction(self):
        # Guards the generator against vacuity: both cited predictions must
        # occur, or the property above could not see a miswired flag.
        seen = set()

        for seed in seeds(120):
            state = self.enriched(random.Random(seed))

            for row in observables.equality_rows("c", state):
                if row.classification == PREDICTED:
                    seen.add(row.note)

        self.assertTrue(any("adversarial 1" in note and "arity" not in note for note in seen))
        self.assertTrue(any("arity" in note and "adversarial 1" not in note for note in seen))

    def test_mismatch_rules(self):
        def label(mode, main_equal, arity=False, masked=False, both=False):
            row = observables._equality_mismatch("c", "O1", mode, main_equal, arity, masked, both, ())
            return row.classification, row.note

        struct, ref = Mode.STRUCT, Mode.REF

        self.assertEqual(label(struct, True)[0], UNEXPECTED)
        self.assertEqual(label(ref, True)[0], UNEXPECTED)
        self.assertEqual(label(struct, False)[0], UNEXPECTED)
        self.assertIn("arity", label(struct, False, arity=True)[1])
        self.assertIn("arity", label(ref, False, arity=True)[1])
        self.assertIn("adversarial 1", label(struct, False, masked=True)[1])
        self.assertEqual(label(ref, False, masked=True)[0], UNEXPECTED)
        self.assertEqual(label(ref, False, both=True)[0], UNEXPECTED)
        note = label(struct, False, both=True)[1]
        self.assertTrue("arity" in note and "adversarial 1" in note)

    def test_mask_blanks_entity_ids_and_nothing_else(self):
        relation = Relation("add", {"left": eid(1), "right": (eid(2), eid(3))}, payload=eid(4))
        masked = observables._mask(Value(eid(0), relation).content)
        other = observables._mask(
            Value(eid(0), Relation("add", {"left": eid(9), "right": (eid(8), eid(7))}, payload=eid(6))).content
        )
        different_kind = observables._mask(Value(eid(0), Relation("sub", {"left": eid(1), "right": (eid(2), eid(3))}, payload=eid(4))).content)

        self.assertEqual(observables._key(masked), observables._key(other))
        self.assertNotEqual(observables._key(masked), observables._key(different_kind))
        self.assertEqual(observables._mask(5), 5)
        self.assertEqual(observables._mask(b"x"), b"x")


class LinkRowTests(unittest.TestCase):
    PROGRAM = "fn double(x):\n    x * 2\n\nfn quad(x):\n    double(double(x))\n"

    def test_link_targets_reads_link_roles_of_the_definition(self):
        state = load(parse(self.PROGRAM))
        targets = {
            entity: observables.link_targets(value.content)
            for entity, value in state.values.items()
        }

        self.assertEqual(targets[EntityID("quad")], {"link:double": EntityID("double")})
        self.assertEqual(targets[EntityID("double")], {})
        self.assertEqual(
            sum(1 for found in targets.values() if found), 1
        )

    def test_recovery_returns_the_declared_target_and_can_see_another(self):
        state = load(parse(self.PROGRAM))
        quad, double = EntityID("quad"), EntityID("double")

        for mode in MODES:
            with self.subTest(mode=mode):
                projection = project(state, mode)
                cstate = projection.cstate
                root = projection.view[quad]
                target = cstate.roles(root)["link:double"][0]

                self.assertEqual(observables.recovered_target(projection, quad, "link:double"), double)

                # Make the candidate say something else and the observable must follow it.
                relations = {h: (cstate.atom(h), dict(cstate.roles(h))) for h in cstate}

                if mode is Mode.STRUCT:
                    relations[root] = (
                        cstate.atom(root),
                        {**cstate.roles(root), "link:double": (root,)},
                    )
                else:
                    relations[target] = (Atom("symbol", "quad"), {})

                tampered = replace(projection, cstate=CState(relations))

                self.assertEqual(observables.recovered_target(tampered, quad, "link:double"), quad)


class IdentityRowTests(unittest.TestCase):
    def names(self, rng):
        return {
            "".join(rng.choice("ab/0") for _ in range(rng.randint(0, 4)))
            for _ in range(12)
        }

    def test_reverse_rename_is_an_order_reversing_bijection(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                names = sorted(self.names(random.Random(seed)))
                images = [identity.reverse_rename(EntityID(n)).value for n in names]

                self.assertEqual(len(set(images)), len(names))
                self.assertEqual(images, sorted(images, reverse=True))

    def test_prefix_rename_preserves_order(self):
        for seed in seeds(60):
            with self.subTest(seed=seed):
                names = sorted(self.names(random.Random(seed)))
                images = [identity.prefix_rename(EntityID(n)).value for n in names]

                self.assertEqual(images, sorted(images))

    def test_change_one_literal_changes_exactly_one_value(self):
        state = load(parse("fn f(x):\n    x + 1\n"))
        changed = identity.change_one_literal(state)

        self.assertIsNotNone(changed)
        self.assertNotEqual(changed.id, state.id)
        self.assertEqual(set(changed.values), set(state.values))
        self.assertEqual(
            [e for e in state.values if state.values[e] != changed.values[e]].__len__(), 1
        )
        self.assertEqual(changed.ownership, state.ownership)

    def test_change_one_literal_is_none_without_an_int_literal(self):
        self.assertIsNone(identity.change_one_literal(state_of(e0=1)))

    def test_pairs_cover_the_plan_cases(self):
        state = load(parse("fn f(x):\n    x + 1\n"))
        labels = [label for label, _, _ in identity.identity_pairs(state, load(parse("fn f(x):\n    x + 1\n")))]

        self.assertEqual(
            labels,
            ["built twice", "renamed (order-preserving)", "renamed (order-reversing)", "one literal changed"],
        )

    def test_rules(self):
        rule = identity._identity_class
        struct, ref = Mode.STRUCT, Mode.REF

        self.assertEqual(rule("built twice", struct, True, True)[0], AGREE)
        self.assertEqual(rule("built twice", struct, True, False)[0], UNEXPECTED)
        self.assertEqual(rule("built twice", struct, False, True)[0], UNEXPECTED)
        for label in ("renamed (order-preserving)", "renamed (order-reversing)"):
            self.assertEqual(rule(label, struct, False, True)[0], PREDICTED)
            self.assertEqual(rule(label, ref, False, True)[0], PREDICTED)
            self.assertEqual(rule(label, struct, False, False)[0], UNEXPECTED)
            self.assertEqual(rule(label, ref, False, False)[0], AGREE)
        self.assertEqual(rule("one literal changed", struct, False, False)[0], AGREE)
        self.assertEqual(rule("one literal changed", struct, False, True)[0], UNEXPECTED)

    def test_unexpected_rename_names_its_cause(self):
        rule = identity._identity_class
        label = "renamed (order-reversing)"

        self.assertIn("not identified", rule(label, Mode.STRUCT, False, False)[1])
        self.assertIn("map keyed by entity_id", rule(label, Mode.STRUCT, False, False, "map keyed by entity_id")[1])

    def test_spelling_cause_finds_maps_keyed_by_entity_id_only(self):
        a, b = EntityID("a"), EntityID("b")
        keyed = state_of(a=1, b=2, m={a: 1, b: 2})
        nested = state_of(a=1, b=2, m=({"k": {a: 1, b: 2}},))
        plain = state_of(a=1, b=2, m={"k": a})

        self.assertIn("map keyed by entity_id", identity.spelling_cause(keyed))
        self.assertIn("map keyed by entity_id", identity.spelling_cause(nested))
        self.assertIsNone(identity.spelling_cause(plain))

    def test_a_map_keyed_by_entity_id_shows_up_as_an_attributed_unexpected_row(self):
        # Entries are listed in key order, so reversing the names reverses the
        # entries; the instrument must report it, with the cause.
        a, b = EntityID("a"), EntityID("b")
        rows = identity.identity_rows("c", state_of(a=1, b=2, m={a: 10, b: 20}))
        struct = [r for r in rows if r.observable == "O3/STRUCT/renamed (order-reversing)"]

        self.assertEqual([r.classification for r in struct], [UNEXPECTED])
        self.assertIn("map keyed by entity_id", struct[0].note)

    def test_ownership_alone_does_not_make_a_renaming_visible(self):
        a, b, c = (EntityID(n) for n in "abc")
        state = State.create({e: Value(e, 0) for e in (a, b, c)}, {a: [b, c]})
        rows = identity.identity_rows("c", state)

        for row in rows:
            if row.observable.startswith("O3/STRUCT/renamed"):
                self.assertEqual(row.candidate_result, "isomorphic")

    def test_rows_compare_state_ids_with_isomorphism(self):
        state = load(parse("fn f(x):\n    x + 1\n"))
        rows = identity.identity_rows("c", state, load(parse("fn f(x):\n    x + 1\n")))
        built_twice = [row for row in rows if "built twice" in row.observable]

        self.assertEqual({row.main_result for row in built_twice}, {"same StateID"})
        self.assertEqual({row.candidate_result for row in built_twice}, {"isomorphic"})
        renamed = [row for row in rows if "order-preserving" in row.observable]
        self.assertEqual({row.main_result for row in renamed}, {"different StateID"})


class ChurnRowTests(unittest.TestCase):
    def test_leaf_edit_scenarios_have_the_ledger_sizes(self):
        for chain, nodes in ((20, 41), (200, 401)):
            with self.subTest(chain=chain):
                before, after, function = churn.leaf_edit_states(chain)

                self.assertEqual(len(before.owned_subtree(function)), nodes)

    def test_main_changes_one_version(self):
        before, after, _ = churn.leaf_edit_states(20)
        changed = [
            e for e in set(before.values) & set(after.values)
            if before.values[e].version_id != after.values[e].version_id
        ]

        self.assertEqual(len(changed), 1)

    def test_first_literal_is_edited_in_pre_order_and_only_it(self):
        edit = churn._first_literal_edited

        self.assertEqual(edit(("add", ("lit", 1), ("lit", 2))), (("add", ("lit", 2), ("lit", 2)), True))
        self.assertEqual(edit(("if", ("arg", "n"), ("lit", "a"))), (("if", ("arg", "n"), ("lit", "a'")), True))
        self.assertEqual(edit(("lit", True)), (("lit", True), False))
        self.assertEqual(edit(("arg", "n")), (("arg", "n"), False))
        self.assertEqual(
            edit(("let", "lit", ("lit", None), ("lit", 7))),
            (("let", "lit", ("lit", None), ("lit", 8)), True),
        )

    def test_cross_function_edit_stays_inside_the_callee_in_main(self):
        before, after, callee = churn.cross_function_states()
        inside = before.owned_subtree(callee) | after.owned_subtree(callee) | {callee}
        changed = {
            e for e in set(before.values) & set(after.values)
            if before.values[e].version_id != after.values[e].version_id
        }

        self.assertTrue(changed)
        self.assertLessEqual(changed, inside)
        self.assertTrue(any(
            callee.value != name and callee in observables.link_targets(before.values[name].content).values()
            for name in before.values
        ))

    def test_cross_function_edit_without_a_literal_leaf_is_rejected(self):
        with self.assertRaises(ValueError):
            churn.cross_function_states("map", "double")

    def test_class_rules(self):
        rule = churn.churn_class
        struct, ref = Mode.STRUCT, Mode.REF

        self.assertEqual(rule(struct, 1, 1)[0], AGREE)
        self.assertEqual(rule(ref, 1, 1)[0], AGREE)
        self.assertEqual(rule(struct, 22, 1)[0], PREDICTED)
        self.assertIn("direction review section 3.3", rule(struct, 22, 1)[1])
        self.assertEqual(rule(ref, 22, 1)[0], UNEXPECTED)
        self.assertEqual(rule(struct, 0, 1)[0], UNEXPECTED)

    def test_rows_report_main_counts_as_recomputed_from_the_states(self):
        for chain, case in ((20, "leaf_edit_41"), (200, "leaf_edit_401")):
            before, after, _ = churn.leaf_edit_states(chain)
            shared = set(before.values) & set(after.values)
            changed = sum(before.values[e].version_id != after.values[e].version_id for e in shared)
            rows = [r for r in churn.churn_rows() if r.case == case]

            self.assertTrue(rows)
            self.assertTrue(all(
                r.main_result.startswith(f"{changed} of {len(shared)} entities change VersionID")
                for r in rows
            ))

    def test_rows_for_every_scenario_and_mode(self):
        rows = churn.churn_rows()

        self.assertEqual(
            sorted((row.case, row.observable) for row in rows),
            sorted(
                (case, f"O5/{mode.name}")
                for case in ("leaf_edit_41", "leaf_edit_401", "cross-function: compiler, edit in upper")
                for mode in MODES
            ),
        )


if __name__ == "__main__":
    unittest.main()
