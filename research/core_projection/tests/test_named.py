"""Instrument tests for the named-roots model (charter section 3.12).

They check that equality, identity and composition work as defined; they
assert no experimental outcome.
"""

from __future__ import annotations

import ast
import random
import unittest
from pathlib import Path

from core_projection.core import Atom
from core_projection.named import (
    Contained,
    ContainmentCycle,
    Name,
    Named,
    NState,
    ReservedAtom,
    check_continuity,
    compose,
    equal,
    isomorphic,
    isomorphisms,
    make_continuity,
)
from core_projection.tests.support import (
    Known,
    Unknown,
    naive_compose,
    seeds,
)
from core_projection.tests.support_named import (
    NAMES,
    brute_force_nisomorphisms,
    decode_encoding,
    is_nisomorphism,
    naive_tree,
    permuted_n,
    random_nstate,
)

SYM = Atom("symbol", "s")
ONE = Atom("int", 1)
A, B, C = NAMES


def rel(atom=None, **roles):
    return (atom, {role: tuple(targets) for role, targets in roles.items()})


def c(handle):
    return Contained(handle)


def n(name):
    return Named(name)


class NStateTests(unittest.TestCase):
    def test_contained_targets_must_exist(self):
        with self.assertRaises(ValueError):
            NState({0: rel(SYM, x=[c(1)])})

    def test_named_targets_must_be_bound(self):
        with self.assertRaises(ValueError):
            NState({0: rel(SYM, x=[n(A)])})

        NState({0: rel(SYM, x=[n(A)])}, {A: 0})

    def test_bindings_must_name_existing_handles(self):
        with self.assertRaises(ValueError):
            NState({0: rel(SYM)}, {A: 3})

        with self.assertRaises(TypeError):
            NState({0: rel(SYM)}, {"a": 0})

    def test_targets_are_typed(self):
        with self.assertRaises(TypeError):
            NState({0: rel(SYM, x=[0])})

    def test_reserved_atoms_are_rejected(self):
        for value in ("name:a", "binding:a", "name:", "binding:x:y"):
            with self.subTest(value=value):
                with self.assertRaises(ReservedAtom):
                    NState({0: rel(Atom("symbol", value))})

        # Only symbols are reserved: a text atom may hold the same characters.
        NState({0: rel(Atom("text", "name:a"))})
        NState({0: rel(Atom("symbol", "names"))})

    def test_relabel_requires_a_bijection(self):
        state = NState({0: rel(SYM), 1: rel(SYM)}, {A: 0})

        with self.assertRaises(ValueError):
            state.relabel({0: 5, 1: 5})

        with self.assertRaises(ValueError):
            state.relabel({0: 5})

    def test_relabel_moves_bindings_and_keeps_names(self):
        state = NState({0: rel(SYM, x=[c(1), n(A)]), 1: rel(ONE)}, {A: 1})
        moved = state.relabel({0: 7, 1: 3})

        self.assertEqual(moved.bindings, {A: 3})
        self.assertEqual(moved.roles(7)["x"], (c(3), n(A)))

    def test_candidate_side_does_not_import_main(self):
        source = Path(__file__).parent.parent / "named.py"
        modules = set()

        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.add((node.module or "").split(".")[0])

        self.assertNotIn("shear", modules)

    def test_frozen_core_does_not_import_the_revision(self):
        # The frozen candidate must not know the revision exists.
        source = Path(__file__).parent.parent / "core.py"
        modules = set()

        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.add(node.module or "")

        self.assertFalse(any("named" in module for module in modules))


class ContainmentTests(unittest.TestCase):
    def test_self_containment_is_a_cycle(self):
        state = NState({0: rel(SYM, x=[c(0)])})

        self.assertEqual(state.containment_cycle(), (0, 0))

        with self.assertRaises(ContainmentCycle):
            state.require_acyclic()

    def test_longer_containment_cycle(self):
        state = NState({0: rel(SYM, x=[c(1)]), 1: rel(SYM, y=[c(2)]), 2: rel(SYM, x=[c(0)])})

        self.assertIsNotNone(state.containment_cycle())

    def test_cycle_through_a_name_is_allowed(self):
        state = NState({0: rel(SYM, x=[n(A)])}, {A: 0})

        self.assertIsNone(state.containment_cycle())
        self.assertTrue(equal(state, 0, state, 0))

    def test_sharing_is_not_a_cycle(self):
        state = NState({0: rel(SYM, x=[c(1), c(1)], y=[c(2)]), 1: rel(ONE, x=[c(3)]), 2: rel(SYM, x=[c(3)]), 3: rel(ONE)})

        self.assertIsNone(state.containment_cycle())

    def test_equal_and_isomorphisms_reject_a_cycle(self):
        cyclic = NState({0: rel(SYM, x=[c(0)])})
        fine = NState({0: rel(SYM)})

        with self.assertRaises(ContainmentCycle):
            equal(cyclic, 0, fine, 0)

        with self.assertRaises(ContainmentCycle):
            equal(fine, 0, cyclic, 0)

        with self.assertRaises(ContainmentCycle):
            list(isomorphisms(cyclic, cyclic))

        with self.assertRaises(ContainmentCycle):
            isomorphic(fine, cyclic)

    def test_random_cycle_detection_agrees_with_depth_limit(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                size = rng.randint(1, 5)
                relations = {
                    h: (SYM, {"x": tuple(c(rng.randrange(size)) for _ in range(rng.randint(0, 2)))})
                    for h in range(size)
                }
                state = NState(relations)

                # A graph with `size` nodes has a cycle iff some walk of length
                # `size` exists (explicit reference, no DFS).
                reach = {h: {t.handle for t in state.roles(h)["x"]} for h in state}
                frontier = set(state.handles)

                for _ in range(size):
                    frontier = {t for h in frontier for t in reach[h]}

                self.assertEqual(state.containment_cycle() is not None, bool(frontier))


class EqualWitnessTests(unittest.TestCase):
    """The Alloy witness set, executed over the revised model."""

    def pair(self, left_rel, right_rel, left_bind=None, right_bind=None):
        left = NState({0: left_rel}, left_bind or {})
        right = NState({0: right_rel}, right_bind or {})

        return equal(left, 0, right, 0)

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
        state = NState({
            0: rel(Atom("symbol", "p")),
            1: rel(Atom("symbol", "q")),
            2: rel(SYM, x=[c(0), c(1)]),
            3: rel(SYM, x=[c(1), c(0)]),
            4: rel(SYM, x=[c(0), c(0)]),
            5: rel(SYM, x=[c(0)]),
        })

        self.assertFalse(equal(state, 2, state, 3))
        self.assertFalse(equal(state, 2, state, 4))
        self.assertFalse(equal(state, 4, state, 5))
        self.assertTrue(equal(state, 2, state, 2))

    def test_equal_values_with_different_sharing_are_equal(self):
        shared = NState({0: rel(SYM, x=[c(1), c(1)]), 1: rel(ONE)})
        unshared = NState({0: rel(SYM, x=[c(1), c(2)]), 1: rel(ONE), 2: rel(ONE)})

        self.assertTrue(equal(shared, 0, unshared, 0))

    def test_named_targets_with_different_names_are_unequal_even_if_bound_content_is_equal(self):
        # The leaf for a name has no edge to the bound root: if it had, this
        # would compare 5 with 5 and NAMED would collapse into STRUCT.
        state = NState(
            {0: rel(SYM, of=[n(A)]), 1: rel(SYM, of=[n(B)]), 2: rel(ONE), 3: rel(ONE)},
            {A: 2, B: 3},
        )

        self.assertTrue(equal(state, 2, state, 3))
        self.assertFalse(equal(state, 0, state, 1))

    def test_named_targets_with_equal_names_are_equal_even_if_bound_content_differs(self):
        left = NState({0: rel(SYM, of=[n(A)]), 1: rel(ONE)}, {A: 1})
        right = NState({0: rel(SYM, of=[n(A)]), 1: rel(Atom("int", 2))}, {A: 1})

        self.assertTrue(equal(left, 0, right, 0))
        self.assertFalse(equal(left, 1, right, 1))

    def test_contained_and_named_targets_differ(self):
        state = NState({0: rel(SYM, x=[c(1)]), 1: rel(ONE), 2: rel(SYM, x=[n(A)])}, {A: 1})

        self.assertFalse(equal(state, 0, state, 2))

    def test_self_reference_through_a_name_is_a_value(self):
        left = NState({0: rel(SYM, link=[n(A)])}, {A: 0})
        right = NState({5: rel(SYM, link=[n(A)])}, {A: 5})
        other = NState({5: rel(SYM, link=[n(B)])}, {B: 5})

        self.assertTrue(equal(left, 0, right, 5))
        self.assertFalse(equal(left, 0, other, 5))

    def test_unknown_handles_are_rejected(self):
        state = NState({0: rel(SYM)})

        with self.assertRaises(KeyError):
            equal(state, 0, state, 1)


class EqualPropertyTests(unittest.TestCase):
    def test_agrees_with_explicit_trees_on_random_pairs(self):
        for seed in seeds(300):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                left, right = random_nstate(rng), random_nstate(rng)

                for a in left:
                    for b in right:
                        self.assertEqual(
                            equal(left, a, right, b),
                            naive_tree(left, a) == naive_tree(right, b),
                        )

    def test_symmetric_and_reflexive(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                left, right = random_nstate(rng), random_nstate(rng)

                for a in left:
                    self.assertTrue(equal(left, a, left, a))

                    for b in right:
                        self.assertEqual(equal(left, a, right, b), equal(right, b, left, a))

    def test_renaming_the_bindings_of_a_name_changes_no_value_that_does_not_mention_it(self):
        # Rebinding a name to other content changes values by name only: a
        # value compares the same before and after unless it mentions the name.
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_nstate(rng)

                if not state.bindings:
                    continue

                name = rng.choice(sorted(state.bindings))
                target = rng.choice(state.handles)
                rebound = NState(
                    {h: (state.atom(h), state.roles(h)) for h in state},
                    {**state.bindings, name: target},
                )

                for h in state:
                    self.assertTrue(equal(state, h, rebound, h))


class IsomorphismTests(unittest.TestCase):
    def test_names_are_fixed(self):
        left = NState({0: rel(SYM, of=[n(A)]), 1: rel(ONE)}, {A: 1})
        renamed = NState({0: rel(SYM, of=[n(B)]), 1: rel(ONE)}, {B: 1})

        self.assertFalse(isomorphic(left, renamed))
        self.assertTrue(isomorphic(left, left.relabel({0: 4, 1: 2})))

    def test_binding_to_a_different_handle_breaks_isomorphism(self):
        left = NState({0: rel(ONE), 1: rel(ONE)}, {A: 0})
        right = NState({0: rel(ONE), 1: rel(ONE)}, {A: 0, B: 1})

        self.assertFalse(isomorphic(left, right))

    def test_binding_distinguishes_equal_handles(self):
        # Two equal roots, one bound: the bound one must map to the bound one.
        left = NState({0: rel(ONE, x=[c(2)]), 1: rel(ONE, x=[c(3)]), 2: rel(SYM), 3: rel(SYM)}, {A: 0})
        right = NState({0: rel(ONE, x=[c(2)]), 1: rel(ONE, x=[c(3)]), 2: rel(SYM), 3: rel(SYM)}, {A: 1})

        self.assertTrue(isomorphic(left, right))
        self.assertEqual(list(isomorphisms(left, right)), [{0: 1, 1: 0, 2: 3, 3: 2}])

    def test_two_identical_anonymous_components_have_two_automorphisms(self):
        # Sequences are ordered, so the symmetry is between separate parents.
        state = NState({0: rel(SYM, x=[c(2)]), 1: rel(SYM, x=[c(3)]), 2: rel(ONE), 3: rel(ONE)})

        found = list(isomorphisms(state, state))

        self.assertEqual(len(found), 2)
        self.assertTrue(all(is_nisomorphism(state, state, m) for m in found))

    def test_a_name_referenced_many_times_adds_no_symmetry(self):
        # One leaf per distinct name: k references do not add k! automorphisms.
        for k in (1, 4, 7):
            with self.subTest(k=k):
                state = NState({0: rel(SYM, x=[n(A)] * k), 1: rel(ONE)}, {A: 1})

                self.assertEqual(len(list(isomorphisms(state, state))), 1)

    def test_naming_removes_the_symmetry_of_otherwise_equal_roots(self):
        anonymous = NState({0: rel(ONE), 1: rel(ONE)})
        named = NState({0: rel(ONE), 1: rel(ONE)}, {A: 0, B: 1})

        self.assertEqual(len(list(isomorphisms(anonymous, anonymous))), 2)
        self.assertEqual(len(list(isomorphisms(named, named))), 1)

    def test_empty_states_are_isomorphic_once(self):
        empty = NState({})

        self.assertEqual(list(isomorphisms(empty, empty)), [{}])

    def test_limit(self):
        state = NState({h: rel(ONE) for h in range(4)})

        self.assertEqual(len(list(isomorphisms(state, state, limit=5))), 5)
        self.assertEqual(len(list(isomorphisms(state, state))), 24)

    def test_random_state_is_isomorphic_to_a_permutation_of_itself(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_nstate(rng, max_handles=7)
                other, renaming = permuted_n(rng, state)

                self.assertTrue(isomorphic(state, other))

                for mapping in isomorphisms(state, other, limit=3):
                    self.assertTrue(is_nisomorphism(state, other, mapping))

                self.assertTrue(any(m == renaming for m in isomorphisms(state, other)))

    def test_renaming_one_binding_breaks_isomorphism(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_nstate(rng, max_handles=7)
                free = [name for name in NAMES if name not in state.bindings]

                if not state.bindings or not free:
                    continue

                old = rng.choice(sorted(state.bindings))
                new = rng.choice(free)

                def rename(target):
                    return Named(new) if isinstance(target, Named) and target.name == old else target

                changed = NState(
                    {
                        h: (state.atom(h), {r: tuple(rename(t) for t in ts) for r, ts in state.roles(h).items()})
                        for h in state
                    },
                    {(new if name == old else name): handle for name, handle in state.bindings.items()},
                )
                other, _ = permuted_n(rng, changed)

                self.assertFalse(isomorphic(state, other))

    def test_one_atom_change_breaks_isomorphism(self):
        for seed in seeds(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_nstate(rng, max_handles=7)
                victim = rng.choice(state.handles)
                changed = NState(
                    {
                        h: (Atom("symbol", "changed") if h == victim else state.atom(h), state.roles(h))
                        for h in state
                    },
                    state.bindings,
                )
                other, _ = permuted_n(rng, changed)

                self.assertFalse(isomorphic(state, other))

    def test_agrees_with_brute_force(self):
        for seed in seeds(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                left = random_nstate(rng, max_handles=5)

                if rng.random() < 0.5:
                    right, _ = permuted_n(rng, left)
                else:
                    right = random_nstate(rng, max_handles=5)

                found = sorted(tuple(sorted(m.items())) for m in isomorphisms(left, right))
                expected = sorted(tuple(sorted(m.items())) for m in brute_force_nisomorphisms(left, right))

                self.assertEqual(found, expected)


class EncodingTests(unittest.TestCase):
    def test_the_encoding_is_injective(self):
        for seed in seeds(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_nstate(rng)

                self.assertEqual(decode_encoding(state.encoding()), state)

    def test_one_leaf_per_distinct_name_and_one_relation_per_binding(self):
        state = NState({0: rel(SYM, x=[n(A), n(A), n(B)], y=[n(A)]), 1: rel(ONE)}, {A: 1, B: 1, C: 0})
        encoding = state.encoding()
        atoms = [encoding.atom(h) for h in encoding]

        self.assertEqual(sum(a == Atom("symbol", "name:a") for a in atoms), 1)
        self.assertEqual(sum(a == Atom("symbol", "name:b") for a in atoms), 1)
        self.assertEqual(sum(a == Atom("symbol", "name:c") for a in atoms), 0)
        self.assertEqual(
            sorted(a.value for a in atoms if a.tag == "symbol" and a.value.startswith("binding:")),
            ["binding:a", "binding:b", "binding:c"],
        )

    def test_name_leaves_have_no_edge_to_the_bound_root(self):
        state = NState({0: rel(SYM, of=[n(A)]), 1: rel(ONE)}, {A: 1})
        encoding = state.encoding()
        leaf = next(h for h in encoding if encoding.atom(h) == Atom("symbol", "name:a"))

        self.assertEqual(dict(encoding.roles(leaf)), {})

    def test_distinct_states_have_distinct_encodings(self):
        seen = {}

        for seed in seeds(200):
            state = random_nstate(random.Random(seed))
            previous = seen.setdefault(state.encoding(), state)

            self.assertEqual(previous, state)


class ContinuityTests(unittest.TestCase):
    def test_named_cases(self):
        first = make_continuity({A: [B], C: [B, C]})
        second = make_continuity({B: [A], C: []})

        self.assertEqual(compose(first, second), {A: frozenset({A}), C: frozenset({A})})
        self.assertEqual(compose(first, make_continuity({B: [A]})), {A: frozenset({A})})

    def test_unknown_names_do_not_join(self):
        # The second step knows other names than the first step produced.
        first = make_continuity({A: [B]})
        second = make_continuity({C: [A]})

        self.assertEqual(compose(first, second), {})

    def test_check_continuity_requires_bound_names(self):
        source = NState({0: rel(SYM)}, {A: 0})
        destination = NState({0: rel(SYM)}, {B: 0})

        check_continuity(make_continuity({A: [B]}), source, destination)

        with self.assertRaises(ValueError):
            check_continuity(make_continuity({C: [B]}), source, destination)

        with self.assertRaises(ValueError):
            check_continuity(make_continuity({A: [C]}), source, destination)

    def test_agrees_with_case_analysis(self):
        names = NAMES + (Name("d"), Name("e"))

        for seed in seeds(300):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                first = _random_named_continuity(rng, names)
                second = _random_named_continuity(rng, names)
                result = compose(first, second)

                for source in names:
                    expected = naive_compose(first, second, source)

                    if isinstance(expected, Unknown):
                        self.assertNotIn(source, result)
                    else:
                        self.assertIsInstance(expected, Known)
                        self.assertEqual(result[source], expected.targets)

    def test_associative(self):
        names = NAMES + (Name("d"), Name("e"))

        for seed in seeds(300):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                one, two, three = (_random_named_continuity(rng, names) for _ in range(3))

                self.assertEqual(compose(compose(one, two), three), compose(one, compose(two, three)))


def _random_named_continuity(rng, names):
    result = {}

    for source in names:
        if rng.random() < 0.7:
            result[source] = frozenset(rng.sample(names, rng.randint(0, 2)))

    return result


if __name__ == "__main__":
    unittest.main()
