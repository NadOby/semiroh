"""Acceptance tests for source reconciliation (docs/name_resolution.md)."""

import unittest

from semiroh import EntityID
from semiroh.lang import function_at, load
from semiroh.reconcile import ReconcileError, reconcile
from semiroh.syntax import parse, render_program


F = EntityID("f")
G = EntityID("g")


def program(text):
    return load(parse(text))


def owned(state, function):
    return set(state.owned_children(function))


class ReconcileTests(unittest.TestCase):
    def test_identical_source_is_a_noop(self):
        text = "fn f(x):\n    x + 1\n"
        state = program(text)

        result = reconcile(state, text)

        self.assertEqual(result.destination.id, state.id)

    def test_changed_body_preserves_unambiguous_descendants(self):
        before = "fn f(x):\n    x + 1\n"
        after = "fn f(x):\n    x - 1\n"
        state = program(before)
        old = owned(state, F)

        result = reconcile(state, after)
        destination = result.destination
        new = owned(destination, F)

        # The root changes kind, while the unchanged argument and literal
        # retain their graph identities through continuity inference.
        self.assertEqual(len(old & new), 2)
        self.assertEqual(
            function_at(destination, F),
            function_at(program(after), F),
        )

    def test_insert_preserves_the_old_subtree(self):
        before = "fn f(x):\n    x + x\n"
        after = "fn f(x):\n    (x + x) * 2\n"
        state = program(before)
        old = owned(state, F)

        destination = reconcile(state, after).destination
        new = owned(destination, F)

        self.assertTrue(old <= new)
        self.assertEqual(len(new - old), 2)

    def test_function_can_be_added(self):
        before = "fn f(x):\n    x\n"
        after = before + "\nfn g(x):\n    x + 1\n"
        state = program(before)

        destination = reconcile(state, after).destination

        self.assertIsNotNone(function_at(destination, F))
        self.assertIsNotNone(function_at(destination, G))
        self.assertEqual(
            function_at(destination, G),
            function_at(program(after), G),
        )

    def test_function_can_be_removed(self):
        before = (
            "fn f(x):\n"
            "    x\n"
            "\n"
            "fn g(x):\n"
            "    x + 1\n"
        )
        after = "fn f(x):\n    x\n"
        state = program(before)

        destination = reconcile(state, after).destination

        self.assertIsNotNone(function_at(destination, F))
        self.assertIsNone(function_at(destination, G))
        self.assertNotIn(G, destination.values)

    def test_bare_top_level_rename_is_remove_and_create(self):
        before = "fn f(x):\n    x + 1\n"
        after = "fn g(x):\n    x + 1\n"
        state = program(before)
        old_nodes = owned(state, F)

        destination = reconcile(state, after).destination

        self.assertIsNone(function_at(destination, F))
        self.assertIsNotNone(function_at(destination, G))
        self.assertFalse(old_nodes & owned(destination, G))

    def test_reference_can_change_target(self):
        before = (
            "fn f(x):\n"
            "    x + 1\n"
            "\n"
            "fn g(x):\n"
            "    x + 2\n"
            "\n"
            "fn use(x):\n"
            "    f(x)\n"
        )
        after = (
            "fn f(x):\n"
            "    x + 1\n"
            "\n"
            "fn g(x):\n"
            "    x + 2\n"
            "\n"
            "fn use(x):\n"
            "    g(x)\n"
        )
        use = EntityID("use")
        state = program(before)

        destination = reconcile(state, after).destination

        self.assertEqual(
            function_at(destination, use),
            function_at(program(after), use),
        )
        self.assertEqual(render_program(destination), render_program(program(after)))

    def test_reference_can_be_removed_from_link_table(self):
        before = (
            "fn f(x):\n"
            "    x + 1\n"
            "\n"
            "fn use(x):\n"
            "    f(x)\n"
        )
        after = (
            "fn f(x):\n"
            "    x + 1\n"
            "\n"
            "fn use(x):\n"
            "    x\n"
        )
        state = program(before)

        destination = reconcile(state, after).destination

        self.assertEqual(render_program(destination), render_program(program(after)))

    def test_unchanged_other_function_keeps_all_nodes(self):
        before = (
            "fn f(x):\n"
            "    x + 1\n"
            "\n"
            "fn g(x):\n"
            "    x * 2\n"
        )
        after = (
            "fn f(x):\n"
            "    x - 1\n"
            "\n"
            "fn g(x):\n"
            "    x * 2\n"
        )
        state = program(before)
        old_g = owned(state, G)

        destination = reconcile(state, after).destination

        self.assertEqual(owned(destination, G), old_g)
        for node in old_g:
            self.assertIs(destination.values[node], state.values[node])

    def test_cell_declaration_change_is_rejected(self):
        before = (
            "cell count: int = 0\n"
            "\n"
            "fn f():\n"
            "    count\n"
        )
        after = (
            "cell count: int = 1\n"
            "\n"
            "fn f():\n"
            "    count\n"
        )
        state = program(before)

        with self.assertRaises(ReconcileError):
            reconcile(state, after)

    def test_cell_addition_is_rejected(self):
        before = "fn f(x):\n    x\n"
        after = (
            "cell count: int = 0\n"
            "\n"
            "fn f(x):\n"
            "    x\n"
        )

        with self.assertRaises(ReconcileError):
            reconcile(program(before), after)

    def test_cell_removal_is_rejected(self):
        before = (
            "cell count: int = 0\n"
            "\n"
            "fn f():\n"
            "    count\n"
        )
        after = "fn f():\n    0\n"

        with self.assertRaises(ReconcileError):
            reconcile(program(before), after)


if __name__ == "__main__":
    unittest.main()
