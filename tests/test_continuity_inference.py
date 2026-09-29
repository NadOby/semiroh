"""Acceptance tests for continuity inference (docs/continuity_inference.md)."""

import unittest

from semiroh import EntityID
from semiroh.continuity import CASES, Case, Expect, check
from semiroh.lang import define, function_at, function_of, load
from semiroh.runtime import ActivationRejected, Runtime
from semiroh.syntax import parse
from semiroh.transforms import transform_with_mapping

F = EntityID("f")
G = EntityID("g")
DOUBLE = "fn double(x):\n    x * 2\n\n"


def redefine(name, program):
    def operation(state):
        function = function_of(parse(program).values[EntityID(name)])
        return define(state, {EntityID(name): function})

    return operation


def edit(name, label, expression):
    def operation(state):
        return define(state, {(EntityID(name), label): expression})

    return operation


def probe(source, operation, **expect):
    return Case(
        name="probe", group="inferred", source=source, operation=operation,
        expect=Expect(**expect), status="holds", note="acceptance",
    )


class CorpusTests(unittest.TestCase):
    def test_every_case_holds(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                self.assertEqual(case.status, "holds")
                self.assertEqual(check(case), ())


class MatchingTests(unittest.TestCase):
    def test_one_old_node_and_two_equal_new_ones_keep_neither(self) -> None:
        case = probe(
            "fn f(x):\n    x + 1\n",
            redefine("f", "fn f(x):\n    x * x + 1\n"),
            gone=("node:f@0",),
            new=("after:f@0", "after:f@0.0", "after:f@0.1"),
            kept=("node:f@1",),
            changed=("node:f@",),
        )

        self.assertEqual(check(case), ())

    def test_the_largest_unique_subtree_is_kept_whole(self) -> None:
        case = probe(
            "fn f(x):\n    x + x\n",
            redefine("f", "fn f(x):\n    (x + x) * 2\n"),
            kept=("node:f@", "node:f@0", "node:f@1"),
            at={
                "node:f@": "after:f@0",
                "node:f@0": "after:f@0.0",
                "node:f@1": "after:f@0.1",
            },
            new=("after:f@", "after:f@1"),
        )

        self.assertEqual(check(case), ())

    def test_a_changed_kind_at_the_root_gives_a_new_node(self) -> None:
        case = probe(
            "fn f(x):\n    x + 1\n",
            redefine("f", "fn f(x):\n    x - 1\n"),
            kept=("node:f@0", "node:f@1"),
            at={"node:f@0": "after:f@0", "node:f@1": "after:f@1"},
            gone=("node:f@",),
            new=("after:f@",),
        )

        self.assertEqual(check(case), ())

    def test_an_identical_body_leaves_the_state_unchanged(self) -> None:
        state = load(parse(DOUBLE + "fn f(x):\n    double(label(k, x)) + 1\n"))
        result = define(state, {F: function_at(state, F)})

        self.assertEqual(result.destination.id, state.id)


class LabelTests(unittest.TestCase):
    SOURCE = DOUBLE + "fn f(x):\n    label(k, x) + double(1)\n"

    def test_a_wrapped_label_keeps_the_node_below_and_names_the_new_one(self) -> None:
        wrap = edit("f", "k", ("call", "double", ("arg", "x")))
        case = probe(
            self.SOURCE,
            wrap,
            kept=("node:f@0", "node:f@1", "node:f@1.0"),
            at={"node:f@0": "after:f@0.0"},
            new=("after:f@0",),
            changed=("node:f@",),
        )

        self.assertEqual(check(case), ())

        expected = parse(DOUBLE + "fn f(x):\n    label(k, double(x)) + double(1)\n")
        destination = wrap(load(parse(self.SOURCE))).destination
        self.assertEqual(function_at(destination, F), function_of(expected.values[F]))

    def test_a_label_edit_that_changes_the_kind_gives_a_new_node(self) -> None:
        case = probe(
            "fn f(x):\n    label(k, 1) + x\n",
            edit("f", "k", ("mul", ("arg", "x"), ("lit", 3))),
            gone=("node:f@0",),
            new=("after:f@0", "after:f@0.0", "after:f@0.1"),
            kept=("node:f@1",),
            changed=("node:f@",),
        )

        self.assertEqual(check(case), ())

    def test_a_label_edit_matches_only_inside_its_label(self) -> None:
        case = probe(
            "fn f(x):\n    label(k, 1) + x\n",
            edit("f", "k", ("arg", "x")),
            gone=("node:f@0",),
            new=("after:f@0",),
            kept=("node:f@1",),
        )

        self.assertEqual(check(case), ())


class RebaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = load(parse("fn f(x):\n    label(left, 1) + label(right, 2)\n"))
        self.left = define(self.state, {(F, "left"): ("lit", 10)})
        self.right = define(self.state, {(F, "right"): ("lit", 20)})
        self.both = define(
            self.state,
            {(F, "left"): ("lit", 10), (F, "right"): ("lit", 20)},
        )

    def test_disjoint_edits_rebase_and_commute(self) -> None:
        from semiroh.transforms import rebase

        onto_left = rebase(self.right, self.left)
        onto_right = rebase(self.left, self.right)

        self.assertEqual(onto_left.source.id, self.left.destination.id)
        self.assertEqual(onto_left.destination.id, self.both.destination.id)
        self.assertEqual(onto_right.destination.id, self.both.destination.id)

    def test_the_runtime_rebases_a_disjoint_result(self) -> None:
        runtime = Runtime(self.state)
        runtime.activate(self.left)
        runtime.activate(self.right)

        self.assertEqual(runtime.active.state.id, self.both.destination.id)

    def test_overlapping_edits_conflict(self) -> None:
        from semiroh.transforms import TransformationConflict, rebase

        other = define(self.state, {(F, "left"): ("lit", 30)})

        with self.assertRaises(TransformationConflict):
            rebase(other, self.left)

        runtime = Runtime(self.state)
        runtime.activate(self.left)

        with self.assertRaises(TransformationConflict) as raised:
            runtime.activate(other)

        self.assertIsInstance(raised.exception, ActivationRejected)

    def test_an_edit_inside_a_removed_function_conflicts(self) -> None:
        from semiroh.transforms import TransformationConflict, rebase

        state = load(parse("fn g(x):\n    label(k, 1) + x\n\nfn f(x):\n    x\n"))
        owned = state.owned_subtree(G) | {G}
        mappings = {entity: entity for entity in state.values if entity not in owned}
        mappings[G] = ()
        removal = transform_with_mapping(state, {}, mappings)
        inside = define(state, {(G, "k"): ("lit", 10)})

        with self.assertRaises(TransformationConflict):
            rebase(inside, removal)

    def test_a_result_from_an_unknown_state_is_stale_not_a_conflict(self) -> None:
        from semiroh.transforms import TransformationConflict

        later = define(self.left.destination, {(F, "right"): ("lit", 20)})
        runtime = Runtime(self.state)

        with self.assertRaises(ActivationRejected) as raised:
            runtime.activate(later)

        self.assertNotIsInstance(raised.exception, TransformationConflict)

    def test_rebase_needs_a_common_source(self) -> None:
        from semiroh.transforms import TransformationConflict, rebase

        later = define(self.left.destination, {(F, "right"): ("lit", 20)})

        with self.assertRaises(ValueError) as raised:
            rebase(later, self.right)

        self.assertNotIsInstance(raised.exception, TransformationConflict)


if __name__ == "__main__":
    unittest.main()
