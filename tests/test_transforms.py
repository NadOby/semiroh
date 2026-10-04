"""Tests for semantic transformations and ownership behavior."""

import unittest

from shear import (
    EntityID,
    OwnershipError,
    State,
    Value,
    transform_with_mapping,
)


class TransformTests(unittest.TestCase):
    def test_state_identity_reflects_entity_mapping_effect(
        self,
    ) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        result_a = transform_with_mapping(
            first,
            {bar: 2},
            {foo: bar},
        )

        result_b = transform_with_mapping(
            first,
            {bar: 2},
            {},
        )

        self.assertNotEqual(
            result_a.destination.id,
            result_b.destination.id,
        )
        self.assertNotEqual(
            result_a.destination.id,
            first.id,
        )

    def test_transform_preserves_ownership_when_entities_are_unchanged(
        self,
    ) -> None:
        root = EntityID("root")
        child = EntityID("child")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {
                root: 10,
                child: 20,
            },
            {
                root: root,
                child: child,
            },
        )

        # Both entities remain present, and mappings do not modify ownership
        # (transformation_model.md §13, ownership_model.md §8-9).
        self.assertEqual(
            result.destination.ownership,
            {
                root: (child,),
            },
        )

    def test_transform_can_explicitly_remove_ownership(self) -> None:
        root = EntityID("root")
        child = EntityID("child")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: root,
                child: child,
            },
            ownership={},
        )

        self.assertEqual(result.destination.ownership, {})
        self.assertTrue(result.destination.contains(root))
        self.assertTrue(result.destination.contains(child))

    def test_transform_can_explicitly_change_ownership(self) -> None:
        root = EntityID("root")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create(
            {
                root: Value.create(root, 0),
                left: Value.create(left, 1),
                right: Value.create(right, 2),
            },
            {
                root: (left,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: root,
                left: left,
                right: right,
            },
            ownership={
                root: (right,),
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                root: (right,),
            },
        )

    def test_transform_carries_ownership_along_renames(
        self,
    ) -> None:
        root = EntityID("root")
        child = EntityID("child")
        new_root = EntityID("new_root")
        new_child = EntityID("new_child")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {
                new_root: 10,
                new_child: 11,
            },
            {
                root: new_root,
                child: new_child,
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                new_root: (new_child,),
            },
        )

        self.assertFalse(
            result.destination.contains(root),
        )
        self.assertFalse(
            result.destination.contains(child),
        )
        self.assertTrue(
            result.destination.contains(new_root),
        )
        self.assertTrue(
            result.destination.contains(new_child),
        )

        self.assertEqual(
            result.destination.owner_of(new_child),
            new_root,
        )

    def test_transform_can_explicitly_preserve_ownership_after_rename(
        self,
    ) -> None:
        root = EntityID("root")
        child = EntityID("child")
        new_root = EntityID("new_root")
        new_child = EntityID("new_child")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {
                new_root: 10,
                new_child: 11,
            },
            {
                root: new_root,
                child: new_child,
            },
            ownership={
                new_root: (new_child,),
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                new_root: (new_child,),
            },
        )

        self.assertEqual(
            result.destination.owner_of(new_child),
            new_root,
        )

    def test_transform_rejects_invalid_destination_ownership(self) -> None:
        root = EntityID("root")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create(
            {
                root: Value.create(root, 0),
                left: Value.create(left, 1),
                right: Value.create(right, 2),
            },
            {
                root: (left,),
            },
        )

        with self.assertRaises(OwnershipError):
            transform_with_mapping(
                state,
                {},
                {
                    root: root,
                    left: left,
                    right: right,
                },
                ownership={
                    root: (right,),
                    left: (right,),
                },
            )

    def test_transform_rejects_destination_ownership_cycle(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        leaf = EntityID("leaf")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
                leaf: Value.create(leaf, 2),
            },
        )

        with self.assertRaises(OwnershipError):
            transform_with_mapping(
                state,
                {},
                {
                    root: root,
                    child: child,
                    leaf: leaf,
                },
                ownership={
                    root: (child,),
                    child: (leaf,),
                    leaf: (root,),
                },
            )

    def test_transform_does_not_mutate_source_ownership(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        sibling = EntityID("sibling")

        state = State.create(
            {
                root: Value.create(root, 0),
                child: Value.create(child, 1),
                sibling: Value.create(sibling, 2),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: root,
                child: child,
                sibling: sibling,
            },
            ownership={
                root: (sibling,),
            },
        )

        self.assertEqual(
            state.ownership,
            {
                root: (child,),
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                root: (sibling,),
            },
        )

    def test_transform_changes_state_identity_when_ownership_changes(
        self,
    ) -> None:
        root = EntityID("root")
        child = EntityID("child")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: root,
                child: child,
            },
            ownership={},
        )

        self.assertNotEqual(result.destination.id, state.id)


class MappingOwnershipPreservationTests(unittest.TestCase):
    def test_identity_mapping_preserves_ownership(self) -> None:
        root = EntityID("root")
        child = EntityID("child")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
            },
            {
                root: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                root: root,
            },
        )

        self.assertEqual(result.destination.owner_of(child), root)

    def test_merged_owner_takes_over_the_children(self) -> None:
        source = EntityID("source")
        source_child = EntityID("source_child")
        target = EntityID("target")
        target_child = EntityID("target_child")

        state = State.create(
            {
                source: Value.create(source, 1),
                source_child: Value.create(source_child, 2),
                target: Value.create(target, 3),
                target_child: Value.create(target_child, 4),
            },
            {
                source: (source_child,),
                target: (target_child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                source: target,
            },
        )

        self.assertEqual(
            result.destination.ownership,
            {
                target: (source_child, target_child),
            },
        )

    def test_swap_carries_ownership(self) -> None:
        a = EntityID("a")
        b = EntityID("b")
        child = EntityID("child")

        state = State.create(
            {
                a: Value.create(a, 1),
                b: Value.create(b, 2),
                child: Value.create(child, 3),
            },
            {
                a: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                a: b,
                b: a,
            },
        )

        # b continues a, so b owns a's child.
        self.assertEqual(result.destination.ownership, {b: (child,)})


if __name__ == "__main__":
    unittest.main()
