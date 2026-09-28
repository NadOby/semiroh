"""Tests for semantic ownership."""

import unittest

from semiroh import (
    EntityID,
    OwnershipError,
    State,
    Value,
)


class OwnershipTests(unittest.TestCase):
    def test_ownership_has_single_owner(self) -> None:
        root = EntityID("root")
        left = EntityID("left")
        right = EntityID("right")

        with self.assertRaises(OwnershipError):
            State.create(
                {
                    root: Value.create(root, 0),
                    left: Value.create(left, 1),
                    right: Value.create(right, 2),
                },
                {
                    root: (left,),
                    right: (left,),
                },
            )

    def test_ownership_rejects_self_cycle(self) -> None:
        foo = EntityID("foo")

        with self.assertRaises(OwnershipError):
            State.create(
                {
                    foo: Value.create(foo, 1),
                },
                {
                    foo: (foo,),
                },
            )

    def test_ownership_rejects_recursive_cycle(self) -> None:
        a = EntityID("a")
        b = EntityID("b")
        c = EntityID("c")

        with self.assertRaises(OwnershipError):
            State.create(
                {
                    a: Value.create(a, 1),
                    b: Value.create(b, 2),
                    c: Value.create(c, 3),
                },
                {
                    a: (b,),
                    b: (c,),
                    c: (a,),
                },
            )

    def test_ownership_requires_existing_entities(self) -> None:
        owner = EntityID("owner")
        missing = EntityID("missing")

        with self.assertRaises(OwnershipError):
            State.create(
                {
                    owner: Value.create(owner, 1),
                },
                {
                    owner: (missing,),
                },
            )

    def test_owner_and_children_queries(self) -> None:
        root = EntityID("root")
        left = EntityID("left")
        right = EntityID("right")
        leaf = EntityID("leaf")

        state = State.create(
            {
                root: Value.create(root, 0),
                left: Value.create(left, 1),
                right: Value.create(right, 2),
                leaf: Value.create(leaf, 3),
            },
            {
                root: (left, right),
                left: (leaf,),
            },
        )

        self.assertIsNone(state.owner_of(root))
        self.assertEqual(state.owner_of(left), root)
        self.assertEqual(state.owner_of(leaf), left)

        self.assertEqual(
            state.owned_children(root),
            (left, right),
        )

        self.assertEqual(
            state.owned_children(left),
            (leaf,),
        )

        self.assertEqual(
            state.owned_subtree(root),
            frozenset({left, right, leaf}),
        )

        self.assertEqual(
            state.owned_subtree(left),
            frozenset({leaf}),
        )

    def test_ownership_affects_state_identity(self) -> None:
        root = EntityID("root")
        child = EntityID("child")

        without_ownership = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
            },
        )

        with_ownership = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
            },
            {
                root: (child,),
            },
        )

        self.assertNotEqual(
            without_ownership.id,
            with_ownership.id,
        )

    def test_ownership_order_does_not_affect_state_identity(self) -> None:
        root = EntityID("root")
        left = EntityID("left")
        right = EntityID("right")

        first = State.create(
            {
                root: Value.create(root, 0),
                left: Value.create(left, 1),
                right: Value.create(right, 2),
            },
            {
                root: (right, left),
            },
        )

        second = State.create(
            {
                root: Value.create(root, 0),
                left: Value.create(left, 1),
                right: Value.create(right, 2),
            },
            {
                root: (left, right),
            },
        )

        self.assertEqual(first.id, second.id)

    def test_ordinary_reference_cycles_do_not_affect_ownership(self) -> None:
        a = EntityID("a")
        b = EntityID("b")

        state = State.create(
            {
                a: Value.create(a, {
                    "reference": b,
                }),
                b: Value.create(b, {
                    "reference": a,
                }),
            },
            {
                a: (b,),
            },
        )

        self.assertEqual(state.owner_of(b), a)
        self.assertIsNone(state.owner_of(a))


class OwnershipNormalizationTests(unittest.TestCase):
    def test_empty_ownership_entry_does_not_change_state_identity(
        self,
    ) -> None:
        foo = EntityID("foo")

        values = {
            foo: Value.create(foo, 1),
        }

        self.assertEqual(
            State.create(values, {foo: ()}).id,
            State.create(values).id,
        )
        self.assertEqual(
            State.create(values, {foo: []}).ownership,
            {},
        )

    def test_empty_ownership_entry_for_absent_owner_is_rejected(
        self,
    ) -> None:
        foo = EntityID("foo")
        ghost = EntityID("ghost")

        with self.assertRaises(OwnershipError):
            State.create(
                {
                    foo: Value.create(foo, 1),
                },
                {
                    ghost: (),
                },
            )

    def test_deep_ownership_chain_is_supported(self) -> None:
        depth = 5000
        entities = [EntityID(f"e{index:05d}") for index in range(depth)]

        state = State.create(
            {
                entity: Value.create(entity, index)
                for index, entity in enumerate(entities)
            },
            {
                entities[index]: (entities[index + 1],)
                for index in range(depth - 1)
            },
        )

        self.assertEqual(
            len(state.owned_subtree(entities[0])),
            depth - 1,
        )

    def test_deep_ownership_cycle_is_detected(self) -> None:
        depth = 5000
        entities = [EntityID(f"e{index:05d}") for index in range(depth)]

        with self.assertRaises(OwnershipError):
            State.create(
                {
                    entity: Value.create(entity, index)
                    for index, entity in enumerate(entities)
                },
                {
                    entities[index]: (entities[(index + 1) % depth],)
                    for index in range(depth)
                },
            )


if __name__ == "__main__":
    unittest.main()
