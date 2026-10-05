"""Instrument tests for O4 and the adversarial builders.

The candidate and ``main`` compositions are compared with an independent
reference on random mappings; the builders are checked against the plan's
description. No experimental outcome is asserted.
"""

from __future__ import annotations

import random
import unittest

from shear.equality import semantic_equal
from shear.identity import EntityID
from shear.state import State
from shear.values import Value

from core_projection import adversarial, composition
from core_projection.composition import Link
from core_projection.core import isomorphisms
from core_projection.project import Mode, project
from core_projection.rows import AGREE, PREDICTED, UNEXPECTED
from core_projection.tests.support import seeds

MODES = (Mode.STRUCT, Mode.REF)


def state_of(prefix, count, offset):
    return State.create({
        EntityID(f"{prefix}{i}"): Value(EntityID(f"{prefix}{i}"), offset + i)
        for i in range(count)
    })


def random_mapping(rng, sources, destinations):
    mapping = {}

    for source in sources:
        if rng.random() < 0.8:
            mapping[source] = tuple(
                sorted(rng.sample(destinations, rng.randint(0, min(2, len(destinations)))))
            )

    return mapping


def random_link(rng):
    start, middle, end = (state_of(p, rng.randint(1, 4), o) for p, o in (("a", 0), ("b", 100), ("c", 200)))

    return Link(
        "random", start, middle, middle, end,
        random_mapping(rng, sorted(start.values), sorted(middle.values)),
        random_mapping(rng, sorted(middle.values), sorted(end.values)),
    )


def reference(link):
    """Explicit Unknown | Known case analysis; ``main``'s third outcome is ``absent``."""

    outcomes = {}

    for source in sorted(link.start.values):
        if source not in link.first:
            outcomes[source] = ("absent",)
            continue

        final, unknown = set(), False

        for middle in link.first[source]:
            if middle not in link.second:
                unknown = True
            else:
                final |= set(link.second[middle])

        outcomes[source] = ("unknown",) if unknown else ("known", frozenset(final))

    return outcomes


def as_candidate(outcomes):
    return {
        source: ("unknown",) if outcome[0] == "absent" else outcome
        for source, outcome in outcomes.items()
    }


class RandomLinkTests(unittest.TestCase):
    def test_main_side_matches_the_reference(self):
        for seed in seeds(200):
            with self.subTest(seed=seed):
                link = random_link(random.Random(seed))

                self.assertEqual(composition.main_outcomes(link), reference(link))

    def test_shared_candidate_matches_the_reference(self):
        for seed in seeds(200):
            for mode in MODES:
                with self.subTest(seed=seed, mode=mode):
                    link = random_link(random.Random(seed))

                    self.assertEqual(
                        composition.candidate_shared(link, mode), as_candidate(reference(link))
                    )

    def test_independent_candidate_matches_the_reference_whatever_the_relabelling(self):
        for seed in seeds(200):
            for mode in MODES:
                with self.subTest(seed=seed, mode=mode):
                    link = random_link(random.Random(seed))

                    for relabelling in (0, 1, 2):
                        outcomes, found = composition.candidate_independent(link, mode, relabelling)

                        self.assertEqual(found, 1)
                        self.assertEqual(outcomes, as_candidate(reference(link)))


class LinkShapeTests(unittest.TestCase):
    def all_links(self):
        return adversarial.case_3_links() + adversarial.case_4_links() + adversarial.chain_links()

    def test_every_mapping_names_entities_of_its_states(self):
        for link in self.all_links():
            with self.subTest(link=link.name):
                for source, destinations in link.first.items():
                    self.assertIn(source, link.start.values)
                    self.assertTrue(all(d in link.middle.values for d in destinations))

                for source, destinations in link.second.items():
                    self.assertIn(source, link.middle_second.values)
                    self.assertTrue(all(d in link.end.values for d in destinations))

    def test_chains_are_real_two_step_chains(self):
        chains = adversarial.chain_links()

        self.assertTrue(5 <= len(chains) <= 10)
        self.assertEqual(len({link.name for link in chains}), len(chains))
        self.assertTrue(all(link.shared and link.cannot_join is None for link in chains))

    def test_case_4_main_outcomes(self):
        known = lambda *names: ("known", frozenset(EntityID(n) for n in names))
        expected = {
            "chain": {"a": known("c")},
            "disappearance": {"a": known()},
            "unknown": {"a": ("unknown",), "z": ("absent",)},
            "split": {"a": known("d", "e")},
            "split, one branch disappears": {"a": known("e")},
            "split, one branch unknown": {"a": ("unknown",)},
            "merge after split": {"a": known("d")},
            "merge": {"a": known("d"), "b": known("d")},
        }

        for link in adversarial.case_4_links():
            name = link.name.removeprefix("adversarial 4: ")

            with self.subTest(case=name):
                self.assertEqual(
                    composition.main_outcomes(link),
                    {EntityID(k): v for k, v in expected[name].items()},
                )

    def test_case_3_middle_states_are_symmetric_or_not_as_described(self):
        by_name = {link.name.removeprefix("adversarial 3: "): link for link in adversarial.case_3_links()}
        expected = {
            "symmetric, differently named": 2,
            "asymmetric control, differently named": 1,
            "symmetric, same naming": 2,
            "asymmetric control, same naming": 1,
        }

        for mode in MODES:
            for name, count in expected.items():
                with self.subTest(mode=mode, case=name):
                    link = by_name[name]
                    left = project(link.middle, mode).cstate
                    right = project(link.middle_second, mode).cstate

                    self.assertEqual(len(list(isomorphisms(left, right))), count)

        self.assertFalse(by_name["symmetric, differently named"].shared)
        self.assertTrue(by_name["symmetric, same naming"].shared)

    def test_two_referents_differ_in_main_though_their_targets_are_equal(self):
        state = adversarial.two_referents_state()
        value = lambda name: state.values[EntityID(name)]

        self.assertTrue(semantic_equal(value("x"), value("y")))
        self.assertFalse(semantic_equal(value("r1"), value("r2")))


class ClassifyTests(unittest.TestCase):
    def test_table(self):
        known = lambda *n: ("known", frozenset(n))
        classify = composition.classify

        self.assertEqual(classify(known("a"), known("a"), None)[0], AGREE)
        self.assertEqual(classify(known("a"), known("b"), None)[0], UNEXPECTED)
        self.assertEqual(classify(known("a"), ("unknown",), None)[0], UNEXPECTED)
        self.assertEqual(classify(("unknown",), ("unknown",), None)[0], AGREE)
        self.assertEqual(classify(("absent",), ("unknown",), None)[0], AGREE)
        self.assertEqual(classify(("unknown",), known("a"), None)[0], UNEXPECTED)
        self.assertEqual(classify(("absent",), known("a"), None)[0], UNEXPECTED)
        self.assertEqual(classify(("unknown",), known("a"), "why")[0], PREDICTED)
        self.assertEqual(classify(known("a"), ("varies", 2), None)[0], PREDICTED)

    def test_absent_and_unknown_stay_separate_rows(self):
        link = adversarial.case_4_links()[2]
        rows = composition.composition_rows(link)
        words = {row.main_result for row in rows}

        self.assertEqual(words, {"Unknown", "absent (not mapped)"})


class RecursionRowTests(unittest.TestCase):
    def test_one_row_per_mode(self):
        rows = adversarial.recursion_rows()

        self.assertEqual([row.observable for row in rows], ["adv2/STRUCT", "adv2/REF"])


if __name__ == "__main__":
    unittest.main()
