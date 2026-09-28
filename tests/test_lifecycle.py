"""Tests for semantic destruction and lifecycle behavior."""

import unittest

from semiroh import (
    EntityID,
    State,
    Value,
)


class LifecycleTests(unittest.TestCase):
    def test_destroy_removes_owned_subtree(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        leaf = EntityID("leaf")
        independent = EntityID("independent")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
                leaf: Value.create(leaf, 2),
                independent: Value.create(independent, 3),
            },
            {
                root: (child,),
                child: (leaf,),
            },
        )

        destroyed = state.destroy(root)

        self.assertFalse(destroyed.contains(root))
        self.assertFalse(destroyed.contains(child))
        self.assertFalse(destroyed.contains(leaf))
        self.assertTrue(destroyed.contains(independent))
        self.assertEqual(destroyed.ownership, {})

    def test_destroy_child_preserves_owner_and_unrelated_entities(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        sibling = EntityID("sibling")
        leaf = EntityID("leaf")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
                sibling: Value.create(sibling, 2),
                leaf: Value.create(leaf, 3),
            },
            {
                root: (child, sibling),
                child: (leaf,),
            },
        )

        destroyed = state.destroy(child)

        self.assertTrue(destroyed.contains(root))
        self.assertTrue(destroyed.contains(sibling))
        self.assertFalse(destroyed.contains(child))
        self.assertFalse(destroyed.contains(leaf))

        self.assertEqual(
            destroyed.ownership,
            {
                root: (sibling,),
            },
        )

    def test_destroy_does_not_mutate_original_state(self) -> None:
        root = EntityID("root")
        child = EntityID("child")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
            },
            {
                root: (child,),
            },
        )

        destroyed = state.destroy(root)

        self.assertTrue(state.contains(root))
        self.assertTrue(state.contains(child))
        self.assertEqual(
            state.ownership,
            {
                root: (child,),
            },
        )

        self.assertEqual(destroyed.values, {})
        self.assertEqual(destroyed.ownership, {})


if __name__ == "__main__":
    unittest.main()
