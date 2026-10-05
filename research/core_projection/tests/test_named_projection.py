"""Instrument tests for the NAMED projection and its observables (revision 1).

They check the projection's own invariants, the dispatch of the observables
and the machinery of the predictions and reproduction checks. They assert no
experimental outcome.
"""

from __future__ import annotations

import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from shear.identity import EntityID, VersionID
from shear.relations import Relation
from shear.state import State
from shear.values import Value

from core_projection import baseline, composition, cycles, identity, observables, predictions
from core_projection.named import Contained, Name, Named, NState
from core_projection.project import Mode, ProjectionGap, decode, normalize_arity, project, rename_entities
from core_projection.project_named import BARE_REFERENCE, NamedProjection
from core_projection.rows import AGREE, CLASSIFICATIONS, PREDICTED, UNEXPECTED, Row
from core_projection.tests.main_support import eid, random_main_state
from core_projection.tests.support import seeds
from core_projection.tests.test_project import same, state_of

X, Y = EntityID("x"), EntityID("y")


class NamedProjectionTests(unittest.TestCase):
    def test_every_entity_root_is_bound_to_its_name(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                state = random_main_state(random.Random(seed))
                projection = project(state, Mode.NAMED)

                self.assertIsInstance(projection, NamedProjection)
                self.assertEqual(
                    dict(projection.nstate.bindings),
                    {Name(e.value): root for e, root in projection.view.items()},
                )
                self.assertEqual(set(projection.view), set(state.values))

    def test_references_are_named_targets_never_contained_roots(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                state = random_main_state(random.Random(seed))
                projection = project(state, Mode.NAMED)
                roots = set(projection.view.values())
                nstate = projection.nstate

                for handle in nstate:
                    for targets in nstate.roles(handle).values():
                        for target in targets:
                            if isinstance(target, Contained):
                                self.assertNotIn(target.handle, roots)

    def test_every_interior_occurrence_is_contained_exactly_once(self):
        # No orphan occurrences (for example left-over reference placeholders)
        # and no sharing: entities share nothing but names.
        for seed in seeds(150):
            with self.subTest(seed=seed):
                state = random_main_state(random.Random(seed))
                projection = project(state, Mode.NAMED)
                nstate = projection.nstate
                roots = set(projection.view.values())
                owns = set(projection.ownership_handles.values())
                indegree = {handle: 0 for handle in nstate}

                for handle in nstate:
                    for targets in nstate.roles(handle).values():
                        for target in targets:
                            if isinstance(target, Contained):
                                indegree[target.handle] += 1

                for handle in nstate:
                    if handle in roots or handle in owns:
                        self.assertEqual(indegree[handle], 0, handle)
                    else:
                        self.assertEqual(indegree[handle], 1, handle)

    def test_projected_containment_is_acyclic_even_for_self_reference(self):
        f = EntityID("f")
        state = State.create({f: Value(f, Relation("def", {"link:f": f}))})
        projection = project(state, Mode.NAMED)
        root = projection.view[f]

        self.assertEqual(projection.nstate.roles(root)["link:f"], (Named(Name("f")),))
        self.assertIsNone(projection.nstate.containment_cycle())

        for seed in seeds(150):
            with self.subTest(seed=seed):
                random_state = random_main_state(random.Random(seed))

                self.assertIsNone(project(random_state, Mode.NAMED).nstate.containment_cycle())

    def test_round_trip_is_exact_and_holds_modulo_arity(self):
        collapsed = 0

        for seed in seeds(150):
            with self.subTest(seed=seed):
                plain = random_main_state(random.Random(seed))
                decoded = decode(project(plain, Mode.NAMED))

                for entity, value in plain.values.items():
                    self.assertTrue(same(decoded[entity], value.content), entity)

                units = random_main_state(random.Random(seed), unit_tuples=True)
                decoded = decode(project(units, Mode.NAMED))

                for entity, value in units.values.items():
                    self.assertTrue(same(normalize_arity(decoded[entity]), normalize_arity(value.content)))
                    collapsed += not same(decoded[entity], value.content)

        self.assertGreater(collapsed, 0)

    def test_projection_ignores_construction_order(self):
        for seed in seeds(100):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_main_state(rng)
                entities = list(state.values)
                rng.shuffle(entities)
                shuffled = State.create({e: state.values[e] for e in entities}, dict(state.ownership))

                self.assertEqual(project(state, Mode.NAMED).nstate, project(shuffled, Mode.NAMED).nstate)

    def test_the_projection_keeps_names_so_a_renamed_state_is_not_isomorphic(self):
        from core_projection.named import isomorphic

        for seed in seeds(100):
            with self.subTest(seed=seed):
                state = random_main_state(random.Random(seed))
                renamed = rename_entities(state, lambda e: EntityID("x/" + e.value))

                self.assertFalse(
                    isomorphic(project(state, Mode.NAMED).nstate, project(renamed, Mode.NAMED).nstate)
                )

    def test_bare_reference_entity_projects_as_a_relation_with_one_named_target(self):
        state = State.create({X: Value(X, 1), Y: Value(Y, X)})
        projection = project(state, Mode.NAMED)
        root = projection.view[Y]

        self.assertEqual(projection.nstate.atom(root).value, BARE_REFERENCE)
        self.assertEqual(dict(projection.nstate.roles(root)), {"target": (Named(Name("x")),)})
        self.assertEqual(decode(projection)[Y][1], "entity_id")
        self.assertEqual(decode(projection)[Y][2], "x")

    def test_dangling_reference_is_a_gap(self):
        with self.assertRaises(ProjectionGap):
            project(state_of(t=(EntityID("ghost"),)), Mode.NAMED)

    def test_owns_relation_per_edge_with_named_endpoints(self):
        a, b, c, d = (EntityID(n) for n in "abcd")
        state = State.create({e: Value(e, 0) for e in (a, b, c, d)}, {a: [c, b], b: [d]})
        projection = project(state, Mode.NAMED)
        nstate = projection.nstate

        self.assertEqual(set(projection.ownership_handles), {(a, b), (a, c), (b, d)})

        for (owner, child), handle in projection.ownership_handles.items():
            self.assertEqual(nstate.atom(handle).value, "owns")
            self.assertEqual(
                dict(nstate.roles(handle)),
                {"owner": (Named(Name(owner.value)),), "owned": (Named(Name(child.value)),)},
            )

    def test_reserved_content_symbols_fail_closed(self):
        for symbol in ("name:a", "binding:a"):
            with self.subTest(symbol=symbol):
                state = State.create({X: Value(X, VersionID(symbol))})

                with self.assertRaises(ProjectionGap):
                    project(state, Mode.NAMED)

        # The bare-reference atom is reserved outside a bare reference.
        with self.assertRaises(ProjectionGap):
            project(State.create({X: Value(X, VersionID(BARE_REFERENCE))}), Mode.NAMED)

    def test_frozen_modes_are_unchanged_by_the_new_mode(self):
        # STRUCT and REF still project to CStates, not named states.
        state = state_of(a=1, b=(EntityID("a"),))

        for mode in (Mode.STRUCT, Mode.REF):
            self.assertFalse(isinstance(project(state, mode), NamedProjection))


class ObservableDispatchTests(unittest.TestCase):
    def test_two_referents_are_unequal_under_named(self):
        # Adversarial 1: x and y have equal content, r1 and r2 refer to them.
        r1, r2 = EntityID("r1"), EntityID("r2")
        state = State.create({
            X: Value(X, 5),
            Y: Value(Y, 5),
            r1: Value(r1, Relation("wraps", {"of": X})),
            r2: Value(r2, Relation("wraps", {"of": Y})),
        })
        rows = [r for r in observables.equality_rows("case", state) if r.observable == "O1/NAMED"]

        self.assertTrue(rows)
        self.assertTrue(all(r.classification == AGREE for r in rows))
        self.assertIn(("unequal", "unequal"), {(r.main_result, r.candidate_result) for r in rows})

    def test_link_targets_are_read_from_named_targets(self):
        f, g = EntityID("f"), EntityID("g")
        state = State.create({
            f: Value(f, Relation("definition", {"link:g": g})),
            g: Value(g, 1),
        })
        projection = project(state, Mode.NAMED)

        self.assertEqual(observables.recovered_target(projection, f, "link:g"), g)

    def test_identity_class_for_named(self):
        renamed = "renamed (order-preserving)"

        self.assertEqual(identity._identity_class(renamed, Mode.NAMED, False, False)[0], AGREE)
        self.assertEqual(identity._identity_class(renamed, Mode.NAMED, False, True)[0], UNEXPECTED)
        # The section 3.11 prediction still applies to the frozen modes.
        self.assertEqual(identity._identity_class(renamed, Mode.REF, False, True)[0], PREDICTED)
        self.assertEqual(identity._identity_class("built twice", Mode.NAMED, True, False)[0], UNEXPECTED)
        self.assertEqual(identity._identity_class("one literal changed", Mode.NAMED, False, True)[0], UNEXPECTED)

    def test_named_composition_cites_no_section_3_11_prediction(self):
        known = ("known", frozenset({EntityID("x")}))

        # candidate composes where main has none: predicted for the frozen modes, not for NAMED
        self.assertEqual(
            composition.classify(("unknown",), known, "reason", Mode.STRUCT)[0], PREDICTED
        )
        self.assertEqual(
            composition.classify(("unknown",), known, "reason", Mode.NAMED)[0], UNEXPECTED
        )
        self.assertEqual(composition.classify(("unknown",), ("varies", 2), None, Mode.STRUCT)[0], PREDICTED)
        self.assertEqual(composition.classify(("unknown",), ("varies", 2), None, Mode.NAMED)[0], UNEXPECTED)

    def test_independent_middle_states_join_by_name_without_isomorphisms(self):
        start = State.create({EntityID("p"): Value(EntityID("p"), 1)})
        middle = State.create({EntityID("a"): Value(EntityID("a"), 2)})
        other = State.create({EntityID("c"): Value(EntityID("c"), 2)})
        end = State.create({EntityID("x"): Value(EntityID("x"), 3)})
        same_name = composition.Link(
            "same", start, middle, middle, end,
            {EntityID("p"): (EntityID("a"),)}, {EntityID("a"): (EntityID("x"),)},
        )
        different = composition.Link(
            "different", start, middle, other, end,
            {EntityID("p"): (EntityID("a"),)}, {EntityID("c"): (EntityID("x"),)},
        )

        self.assertEqual(
            composition.candidate_independent(same_name, Mode.NAMED)[0][EntityID("p")],
            ("known", frozenset({EntityID("x")})),
        )
        outcomes, found = composition.candidate_independent(different, Mode.NAMED)

        self.assertEqual(outcomes[EntityID("p")], ("unknown",))
        self.assertEqual(found, 0)


class CycleObservableTests(unittest.TestCase):
    def test_projected_states_have_no_contained_cycle(self):
        for seed in seeds(100):
            with self.subTest(seed=seed):
                rows = cycles.cycle_rows("case", random_main_state(random.Random(seed)))

                self.assertEqual([r.classification for r in rows], [AGREE])

    def test_a_contained_cycle_is_unexpected(self):
        cyclic = NState({0: (None, {"x": (Contained(0),)})})
        fake = NamedProjection(Mode.NAMED, cyclic, {X: 0}, {}, ())

        with mock.patch.object(cycles, "project", return_value=fake):
            rows = cycles.cycle_rows("case", state_of(a=1))

        self.assertEqual([r.classification for r in rows], [UNEXPECTED])
        self.assertEqual(rows[0].examples, ("0 -> 0",))


def row(observable, classification=AGREE, count=1, case="c", main="m", candidate="k"):
    return Row(case, observable, main, candidate, classification, count=count)


class PredictionTests(unittest.TestCase):
    def good_rows(self):
        return [
            row("O0/NAMED/modulo-arity", count=5),
            row("O0/NAMED/exact", count=3),
            row("O0/NAMED/exact", PREDICTED, count=2),
            row("O0/STRUCT/exact", PREDICTED, count=2),
            row("O1/NAMED", count=9),
            row("O2/NAMED", count=2),
            row("O3/NAMED/built twice"),
            row("O3/NAMED/one literal changed"),
            row("O3/NAMED/renamed (order-preserving)"),
            row("O3/NAMED/renamed (order-reversing)"),
            row("O4a/NAMED", case="chain: x"),
            row("O4b/NAMED", case="adversarial 4: split"),
            row("O4b/NAMED", case="adversarial 3: symmetric, differently named", main="Unknown", candidate="Unknown"),
            row("O4b/NAMED", case="adversarial 3: symmetric, same naming", main="Known(1)", candidate="Known(1)"),
            row("O5/NAMED", case="a", main="1 of 42 entities change VersionID", candidate="1 of 42 changed"),
            row("O5/NAMED", case="b", main="1 of 402 entities change VersionID", candidate="1 of 402"),
            row("O5/NAMED", case="c", main="2 of 549 entities change VersionID; 2 removed", candidate="2 of 549"),
            row("C0/NAMED", count=7),
        ]

    def test_every_claim_holds_on_conforming_rows(self):
        judged = predictions.verdicts(self.good_rows())

        self.assertEqual(len(judged), len(predictions.CLAIMS))
        self.assertTrue(all(v.hit for v in judged), [v for v in judged if not v.hit])

    def test_each_claim_misses_when_its_rows_do_not_conform(self):
        broken = {
            "O0": ("O0/NAMED/modulo-arity", UNEXPECTED),
            "O1": ("O1/NAMED", UNEXPECTED),
            "O2": ("O2/NAMED", UNEXPECTED),
            "O3 built twice / literal changed": ("O3/NAMED/built twice", UNEXPECTED),
            "O3 renamed (both orders)": ("O3/NAMED/renamed (order-preserving)", UNEXPECTED),
            "O4 shared and independent middle states": ("O4a/NAMED", UNEXPECTED),
            "contained cycles in projected states": ("C0/NAMED", UNEXPECTED),
        }

        for observable, (target, classification) in broken.items():
            with self.subTest(observable=observable):
                rows = [
                    replace(r, classification=classification) if r.observable == target and r.case in ("c", "chain: x") else r
                    for r in self.good_rows()
                ]
                verdict = next(v for v in predictions.verdicts(rows) if v.observable == observable)

                self.assertFalse(verdict.hit, verdict)

    def test_adversarial_3_claims_check_the_words_and_cases(self):
        rows = self.good_rows()
        known = [
            replace(r, candidate_result="Known(1)") if "differently named" in r.case else r for r in rows
        ]
        varying = [
            replace(r, candidate_result="varies across isomorphisms") if "same naming" in r.case else r for r in rows
        ]
        by_name = {v.observable: v for v in predictions.verdicts(known)}
        by_vary = {v.observable: v for v in predictions.verdicts(varying)}

        self.assertFalse(by_name["adversarial 3, differently named"].hit)
        self.assertFalse(by_vary["adversarial 3, symmetric with same naming"].hit)

    def test_o5_requires_the_stated_version_counts(self):
        rows = [
            replace(r, main_result=r.main_result.replace("1 of 42", "3 of 42")) if r.case == "a" else r
            for r in self.good_rows()
        ]

        self.assertFalse(next(v for v in predictions.verdicts(rows) if v.observable.startswith("O5")).hit)

    def test_arity_collapse_count_must_match_struct(self):
        rows = self.good_rows() + [row("O0/NAMED/exact", PREDICTED, count=1)]

        self.assertFalse(next(v for v in predictions.verdicts(rows) if v.observable == "O0").hit)

    def test_a_claim_with_no_rows_is_a_miss(self):
        self.assertFalse(any(v.hit for v in predictions.verdicts([])))


REPORT_TEXT = """# Results

## Full report of the re-run (`cb74cea`)

### Counts per observable and classification

| observable | agree | predicted mismatch | unexpected mismatch | gap | total |
|---|---|---|---|---|---|
| O1/REF | 10 | 0 | 0 | 0 | 10 |
| O1/STRUCT | 7 | 3 | 0 | 0 | 10 |
| O5/REF | 1 | 0 | 0 | 0 | 1 |
| O5/STRUCT | 0 | 1 | 0 | 0 | 1 |

### Every row that is not agree

### Version churn (O5)

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| s | O5/STRUCT | 1 of 4 changes | 3 of 4 change | predicted mismatch | 1 | note |  |
| s | O5/REF | 1 of 4 changes | 1 of 4 change | agree | 1 |  |  |
"""


class BaselineTests(unittest.TestCase):
    def report(self, text=REPORT_TEXT):
        directory = Path(tempfile.mkdtemp())
        path = directory / "report.md"
        path.write_text(text)

        return path

    def live(self, struct_predicted=3):
        return [
            Row("a", "O1/REF", "u", "u", AGREE, count=10),
            Row("a", "O1/STRUCT", "u", "u", AGREE, count=10 - struct_predicted),
            Row("a", "O1/STRUCT", "u", "e", PREDICTED, count=struct_predicted),
            Row("s", "O5/STRUCT", "1 of 4 changes", "3 of 4 change", PREDICTED),
            Row("s", "O5/REF", "1 of 4 changes", "1 of 4 change", AGREE),
            Row("a", "O1/NAMED", "u", "u", AGREE, count=99),  # not a frozen mode: not compared
        ]

    def test_parses_the_frozen_mode_counts(self):
        self.assertEqual(
            baseline.recorded_counts(self.report()),
            {
                ("O1/REF", AGREE): 10, ("O1/STRUCT", AGREE): 7, ("O1/STRUCT", PREDICTED): 3,
                ("O5/REF", AGREE): 1, ("O5/STRUCT", PREDICTED): 1,
            },
        )

    def test_matching_rows_reproduce(self):
        self.assertEqual(baseline.differences(self.live(), self.report()), [])

    def test_one_changed_count_is_reported_per_observable(self):
        found = baseline.differences(self.live(struct_predicted=4), self.report())

        self.assertEqual(len(found), 2)
        self.assertTrue(all("O1/STRUCT" in line for line in found))

    def test_a_changed_churn_word_is_reported(self):
        rows = self.live()
        rows[3] = replace(rows[3], candidate_result="4 of 4 change")

        self.assertEqual(len(baseline.differences(rows, self.report())), 1)

    def test_a_missing_observable_or_a_missing_section_fails_closed(self):
        self.assertTrue(baseline.differences([r for r in self.live() if r.observable != "O1/REF"], self.report()))

        with self.assertRaises(ValueError):
            baseline.recorded_counts(self.report("# nothing here\n"))

        with self.assertRaises(ValueError):
            baseline.recorded_counts(self.report(REPORT_TEXT.replace("| 7 | 3 | 0 | 0 | 10 |", "| 7 | 3 | 0 | 0 | 11 |")))

    def test_the_committed_record_parses(self):
        counts = baseline.recorded_counts()

        self.assertIn(("O1/STRUCT", PREDICTED), counts)
        self.assertTrue(all(classification in CLASSIFICATIONS for _, classification in counts))
        self.assertGreaterEqual(len(baseline.recorded_churn()), 6)


if __name__ == "__main__":
    unittest.main()
