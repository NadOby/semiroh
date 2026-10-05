"""Instrument tests for the candidate core.

These check that bisimulation, isomorphism and composition work as defined.
They assert no experimental outcome.
"""

from __future__ import annotations

import ast
import random
import unittest
from pathlib import Path

from core_projection.core import (
    Atom,
    CState,
    bisimilar,
    compose,
    inverse,
    isomorphic,
    isomorphisms,
    make_continuity,
    transport,
)
from core_projection.tests.support import (
    Known,
    Unknown,
    brute_force_isomorphisms,
    cycle,
    doubled,
    is_isomorphism,
    naive_bisimilar_pairs,
    naive_compose,
    permuted,
    random_continuity,
    random_state,
    seeds,
    unfold,
)

SYM = Atom("symbol", "s")
ONE = Atom("int", 1)


def rel(atom=None, **roles):
    return (atom, {name: tuple(targets) for name, targets in roles.items()})


def equal(left, a, right, b):
    return bisimilar(left, a, right, b)


class CStateTests(unittest.TestCase):
    def test_every_target_must_exist(self):
        with self.assertRaises(ValueError):
            CState({0: rel(SYM, x=[1])})

    def test_atoms_are_tagged(self):
        self.assertNotEqual(Atom("bool", True), Atom("int", 1))
        self.assertNotEqual(Atom("text", "a"), Atom("symbol", "a"))

        with self.assertRaises(TypeError):
            Atom("int", True)

        with self.assertRaises(TypeError):
            Atom("none", 0)

        with self.assertRaises(ValueError):
            Atom("float", 1.0)

    def test_roles_are_validated_and_order_insensitive(self):
        with self.assertRaises(TypeError):
            CState({0: (None, {"": ()})})

        left = CState({0: (None, {"x": (), "y": ()})})
        right = CState({0: (None, {"y": (), "x": ()})})

        self.assertEqual(left, right)

    def test_relabel_requires_a_bijection(self):
        state = CState({0: rel(), 1: rel()})

        with self.assertRaises(ValueError):
            state.relabel({0: 5, 1: 5})

        with self.assertRaises(ValueError):
            state.relabel({0: 5})

    def test_candidate_side_does_not_import_main(self):
        source = Path(__file__).parent.parent / "core.py"
        modules = set()

        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.add((node.module or "").split(".")[0])

        self.assertNotIn("shear", modules)


class BisimilarWitnessTests(unittest.TestCase):
    """The Alloy witness set, executed."""

    def pair(self, left_rel, right_rel):
        left = CState({0: left_rel})
        right = CState({0: right_rel})

        return bisimilar(left, 0, right, 0)

    def test_reflexive_on_cycles(self):
        state = CState({0: rel(SYM, x=[0])})

        self.assertTrue(equal(state, 0, state, 0))

    def test_different_atoms(self):
        self.assertFalse(self.pair(rel(SYM), rel(Atom("symbol", "t"))))
        self.assertFalse(self.pair(rel(None), rel(Atom("none"))))
        self.assertFalse(self.pair(rel(Atom("bool", True)), rel(ONE)))
        self.assertTrue(self.pair(rel(ONE), rel(Atom("int", 1))))

    def test_different_role_sets(self):
        self.assertFalse(self.pair(rel(SYM, x=[]), rel(SYM, y=[])))
        self.assertFalse(self.pair(rel(SYM, x=[]), rel(SYM, x=[], y=[])))

    def test_present_empty_role_differs_from_absent_role(self):
        self.assertFalse(self.pair(rel(SYM, x=[]), rel(SYM)))

    def test_target_order_and_multiplicity(self):
        state = CState({
            0: rel(Atom("symbol", "p")),
            1: rel(Atom("symbol", "q")),
            2: rel(SYM, x=[0, 1]),
            3: rel(SYM, x=[1, 0]),
            4: rel(SYM, x=[0, 0]),
            5: rel(SYM, x=[0]),
        })

        self.assertFalse(equal(state, 2, state, 3))
        self.assertFalse(equal(state, 4, state, 5))
        self.assertTrue(equal(state, 2, state, 2))

    def test_equal_values_with_different_sharing_are_equal(self):
        shared = CState({0: rel(ONE), 1: rel(SYM, x=[0, 0])})
        separate = CState({0: rel(ONE), 1: rel(ONE), 2: rel(SYM, x=[0, 1])})

        self.assertTrue(equal(shared, 1, separate, 2))

    def test_pair_of_equal_atoms_differs_from_wrapped_single(self):
        # pair(1, 1) versus pair(dup(1)), charter section 3.4.
        flat = CState({0: rel(ONE), 1: rel(SYM, x=[0, 0])})
        nested = CState({
            0: rel(ONE),
            1: rel(Atom("symbol", "dup"), x=[0]),
            2: rel(SYM, x=[1]),
        })

        self.assertFalse(equal(flat, 1, nested, 2))

    def test_self_cycle_equals_two_node_cycle(self):
        one = CState({0: rel(SYM, x=[0])})
        two = CState({0: rel(SYM, x=[1]), 1: rel(SYM, x=[0])})

        self.assertTrue(equal(one, 0, two, 0))
        self.assertTrue(equal(two, 0, one, 0))

    def test_cycles_with_different_atoms_or_a_chain_end_differ(self):
        one = CState({0: rel(SYM, x=[0])})
        marked = CState({0: rel(SYM, x=[1]), 1: rel(Atom("symbol", "t"), x=[0])})
        chain = CState({0: rel(SYM, x=[1]), 1: rel(SYM, x=[2]), 2: rel(SYM, x=[])})

        self.assertFalse(equal(one, 0, marked, 0))
        self.assertFalse(equal(one, 0, chain, 0))

    def test_unknown_handles_are_rejected(self):
        state = CState({0: rel()})

        with self.assertRaises(KeyError):
            bisimilar(state, 0, state, 1)


class BisimilarPropertyTests(unittest.TestCase):
    def test_agrees_with_greatest_fixpoint_on_random_pairs(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                left = random_state(rng)
                kind = rng.choice(("fresh", "unfolded", "unfolded"))

                if kind == "fresh":
                    right = random_state(rng)
                else:
                    right, _ = unfold(rng, left)

                expected = naive_bisimilar_pairs(left, right)

                for a in left:
                    for b in right:
                        self.assertEqual(
                            bisimilar(left, a, right, b),
                            (a, b) in expected,
                            (a, b),
                        )

    def test_unfolding_preserves_value_equality(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_state(rng)
                unfolded, copies = unfold(rng, state)

                for handle, images in copies.items():
                    for image in images:
                        self.assertTrue(bisimilar(state, handle, unfolded, image))

    def test_symmetric_and_reflexive(self):
        for seed in seeds(100):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                left = random_state(rng)
                right = random_state(rng)

                for a in left:
                    self.assertTrue(bisimilar(left, a, left, a))

                    for b in right:
                        self.assertEqual(
                            bisimilar(left, a, right, b),
                            bisimilar(right, b, left, a),
                        )


class IsomorphismTests(unittest.TestCase):
    def test_symmetric_state_has_two_automorphisms_and_the_control_one(self):
        symmetric = CState({
            0: rel(ONE),
            1: rel(SYM, x=[0]),
            2: rel(ONE),
            3: rel(SYM, x=[2]),
        })
        control = CState({
            0: rel(ONE),
            1: rel(SYM, x=[0]),
            2: rel(Atom("int", 2)),
            3: rel(SYM, x=[2]),
        })

        self.assertEqual(len(list(isomorphisms(symmetric, symmetric))), 2)
        self.assertEqual(len(list(isomorphisms(control, control))), 1)

    def test_connected_symmetries_are_all_found(self):
        for length in range(1, 6):
            for chords in (False, True):
                with self.subTest(length=length, chords=chords):
                    state = cycle(length, SYM, chords)

                    self.assertEqual(len(list(isomorphisms(state, state))), length)

        swap = CState({0: rel(SYM, x=[0, 1]), 1: rel(SYM, x=[1, 0])})

        self.assertEqual(len(list(isomorphisms(swap, swap))), 2)

    def test_mixed_components_regression(self):
        # Found by a planted bug (non-injective assignment) that only 3 of 20000
        # random states expose: a swap component next to rigid components.
        state = CState({
            0: rel(None, x=[1]),
            1: rel(None, x=[0, 1], y=[]),
            2: rel(None, x=[3]),
            3: rel(None, x=[2]),
            4: rel(None, x=[4]),
        })
        other = state.relabel({0: 73, 1: 4, 2: 31, 3: 23, 4: 39})
        found = list(isomorphisms(state, other))

        self.assertEqual(len(found), 2)
        self.assertTrue(all(is_isomorphism(state, other, m) for m in found))
        self.assertEqual(len(list(isomorphisms(state, state))), 2)

    def test_equal_unconnected_values_permute_freely(self):
        state = CState({h: rel(SYM) for h in range(3)})

        self.assertEqual(len(list(isomorphisms(state, state))), 6)
        self.assertEqual(len(list(isomorphisms(state, state, limit=2))), 2)

    def test_empty_states_are_isomorphic_once(self):
        empty = CState({})

        self.assertEqual(list(isomorphisms(empty, empty)), [{}])

    def test_size_and_sharing_matter(self):
        shared = CState({0: rel(ONE), 1: rel(SYM, x=[0, 0])})
        separate = CState({0: rel(ONE), 1: rel(ONE), 2: rel(SYM, x=[0, 1])})

        self.assertFalse(isomorphic(shared, separate))
        self.assertFalse(isomorphic(separate, shared))

    def test_a_doubled_state_has_a_swapping_automorphism(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = doubled(random_state(rng, max_handles=3))
                found = list(isomorphisms(state, state))

                self.assertGreaterEqual(len(found), 2)
                self.assertTrue(all(is_isomorphism(state, state, m) for m in found))
                self.assertEqual(len(found), len({tuple(sorted(m.items())) for m in found}))

    def test_random_state_is_isomorphic_to_a_permutation_of_itself(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_state(rng, max_handles=7)
                other, renaming = permuted(rng, state)

                self.assertTrue(isomorphic(state, other))

                for mapping in isomorphisms(state, other, limit=3):
                    self.assertTrue(is_isomorphism(state, other, mapping))

                self.assertTrue(
                    any(
                        mapping == renaming
                        for mapping in isomorphisms(state, other)
                    )
                )

    def test_one_atom_change_breaks_isomorphism(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_state(rng, max_handles=7)
                victim = rng.choice(state.handles)
                changed = CState({
                    handle: (
                        Atom("symbol", "changed") if handle == victim else state.atom(handle),
                        state.roles(handle),
                    )
                    for handle in state
                })
                other, _ = permuted(rng, changed)

                self.assertFalse(isomorphic(state, other))

    def test_agrees_with_brute_force(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                kind = rng.choice(("permuted", "fresh", "doubled", "cycle"))

                if kind == "doubled":
                    left = doubled(random_state(rng, max_handles=3))
                elif kind == "cycle":
                    left = cycle(rng.randint(2, 5), rng.choice((None, SYM)), rng.random() < 0.5)
                else:
                    left = random_state(rng, max_handles=5)

                if kind == "fresh":
                    right = random_state(rng, max_handles=5)
                else:
                    right, _ = permuted(rng, left)

                found = sorted(
                    tuple(sorted(m.items())) for m in isomorphisms(left, right)
                )
                expected = sorted(
                    tuple(sorted(m.items()))
                    for m in brute_force_isomorphisms(left, right)
                )

                self.assertEqual(found, expected)


class CompositionTests(unittest.TestCase):
    def test_named_cases(self):
        chain = compose(make_continuity({1: [2]}), make_continuity({2: [3]}))
        gone = compose(make_continuity({1: []}), make_continuity({}))
        unknown_first = compose({}, make_continuity({2: [3]}))
        unknown_second = compose(make_continuity({1: [2]}), {})
        split = compose(
            make_continuity({1: [2, 3]}),
            make_continuity({2: [4], 3: [5]}),
        )
        split_gone = compose(
            make_continuity({1: [2, 3]}),
            make_continuity({2: [], 3: [5]}),
        )
        split_unknown = compose(
            make_continuity({1: [2, 3]}),
            make_continuity({2: [4]}),
        )
        merge = compose(
            make_continuity({1: [2, 3]}),
            make_continuity({2: [4], 3: [4]}),
        )

        self.assertEqual(chain, {1: frozenset({3})})
        self.assertEqual(gone, {1: frozenset()})
        self.assertEqual(unknown_first, {})
        self.assertEqual(unknown_second, {})
        self.assertEqual(split, {1: frozenset({4, 5})})
        self.assertEqual(split_gone, {1: frozenset({5})})
        self.assertEqual(split_unknown, {})
        self.assertEqual(merge, {1: frozenset({4})})

    def test_agrees_with_case_analysis(self):
        for seed in seeds(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                first = random_continuity(rng, range(5), range(10, 15))
                second = random_continuity(rng, range(10, 15), range(20, 25))
                result = compose(first, second)

                for source in range(5):
                    expected = naive_compose(first, second, source)

                    if isinstance(expected, Unknown):
                        self.assertNotIn(source, result)
                    else:
                        self.assertEqual(Known(result[source]), expected)

    def test_unknown_never_becomes_explicit_disappearance(self):
        for seed in seeds(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                first = random_continuity(rng, range(5), range(10, 15))
                second = random_continuity(rng, range(10, 15), range(20, 25))
                result = compose(first, second)

                for source, final in result.items():
                    self.assertIn(source, first)

                    if not final:
                        self.assertTrue(
                            all(second[m] == frozenset() for m in first[source])
                        )

    def test_associative(self):
        for seed in seeds(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                a = random_continuity(rng, range(5), range(10, 15))
                b = random_continuity(rng, range(10, 15), range(20, 25))
                c = random_continuity(rng, range(20, 25), range(30, 35))

                self.assertEqual(
                    compose(compose(a, b), c),
                    compose(a, compose(b, c)),
                )

    def test_refining_unknown_never_changes_a_known_result(self):
        for seed in seeds(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                first = random_continuity(rng, range(5), range(10, 15))
                second = random_continuity(rng, range(10, 15), range(20, 25))
                richer = dict(second)

                for middle in range(10, 15):
                    richer.setdefault(middle, frozenset({20 + middle % 5}))

                before = compose(first, second)
                after = compose(first, richer)

                for source, final in before.items():
                    self.assertEqual(after[source], final)


class TransportTests(unittest.TestCase):
    def test_composing_through_an_isomorphism_commutes_with_renaming(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                middle = random_state(rng, max_handles=5)
                other, iso = permuted(rng, middle)
                first = random_continuity(rng, range(40, 44), range(len(middle)))
                first = {
                    s: frozenset(middle.handles[i] for i in t)
                    for s, t in first.items()
                }
                second = random_continuity(rng, range(len(other)), range(20, 24))
                second = {
                    other.handles[i]: t for i, t in second.items()
                }

                forward = compose(
                    transport(first, iso, destinations=True), second
                )
                backward = compose(
                    first, transport(second, inverse(iso), sources=True)
                )

                self.assertEqual(forward, backward)

    def test_transport_keeps_unknown_and_disappearance(self):
        renaming = {1: 5, 2: 6, 3: 7}
        moved = transport(
            make_continuity({1: [], 2: [3]}), renaming,
            sources=True, destinations=True,
        )

        self.assertEqual(moved, {5: frozenset(), 6: frozenset({7})})
        self.assertNotIn(7, moved)

    def test_transport_rejects_a_merging_renaming(self):
        with self.assertRaises(ValueError):
            transport(
                make_continuity({1: [], 2: []}), {1: 9, 2: 9}, sources=True
            )

        with self.assertRaises(ValueError):
            inverse({1: 9, 2: 9})


if __name__ == "__main__":
    unittest.main()
