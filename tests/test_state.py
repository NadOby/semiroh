"""Tests for immutable semantic states and values."""

import unittest

from shear import (
    OwnershipError,
    StateID,
    EntityID,
    State,
    Value,
)


class StateTests(unittest.TestCase):
    def test_state_identity_is_history_independent(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 42),
            bar: Value.create(bar, 10),
        })

        second = State.create({
            bar: Value.create(bar, 10),
            foo: Value.create(foo, 42),
        })

        self.assertEqual(first.id, second.id)
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))

    def test_state_values_are_immutable(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        with self.assertRaises(TypeError):
            state.values[foo] = Value.create(foo, 2)

        self.assertEqual(state.values[foo].content, 1)

    def test_state_ownership_is_immutable(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        state = State.create(
            {
                foo: Value.create(foo, 1),
                bar: Value.create(bar, 2),
            },
            {
                foo: (bar,),
            },
        )

        with self.assertRaises(TypeError):
            state.ownership[foo] = (bar,)

        self.assertEqual(state.ownership[foo], (bar,))

    def test_value_content_is_immutable(self) -> None:
        foo = EntityID("foo")

        original = [1, 2, 3]
        value = Value.create(foo, original)

        original.append(4)

        self.assertEqual(
            value.content,
            (
                "__type__",
                "list",
                (1, 2, 3),
            ),
        )

        with self.assertRaises(TypeError):
            value.content[2] += (4,)

    def test_direct_value_construction_is_immutable(self) -> None:
        foo = EntityID("foo")

        original = [1, 2, 3]
        value = Value(foo, original)

        original.append(4)

        self.assertEqual(
            value.content,
            (
                "__type__",
                "list",
                (1, 2, 3),
            ),
        )

    def test_original_input_mapping_cannot_mutate_state(self) -> None:
        foo = EntityID("foo")

        values = {
            foo: Value.create(foo, 1),
        }

        state = State.create(values)

        values[foo] = Value.create(foo, 2)

        self.assertEqual(state.values[foo].content, 1)

    def test_original_ownership_mapping_cannot_mutate_state(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        ownership = {
            foo: [bar],
        }

        state = State.create(
            {
                foo: Value.create(foo, 1),
                bar: Value.create(bar, 2),
            },
            ownership,
        )

        ownership[foo].append(foo)

        self.assertEqual(state.ownership[foo], (bar,))

    def test_state_identity_is_full_sha256(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        self.assertEqual(len(state.id.value), 64)
        self.assertTrue(
            all(
                character in "0123456789abcdef"
                for character in state.id.value
            )
        )

    def test_state_rejects_entity_key_mismatch(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        with self.assertRaises(ValueError):
            State.create({
                foo: Value.create(bar, 42),
            })

    def test_semantic_digest_matches_state_id(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 42),
        })

        self.assertEqual(
            state.semantic_digest,
            state.id.value,
        )

    def test_semantic_digest_is_deterministic(self) -> None:
        foo = EntityID("foo")

        first = State.create({
            foo: Value.create(
                foo,
                {
                    "a": [1, 2],
                    "b": ("x", "y"),
                },
            ),
        })

        second = State.create({
            foo: Value.create(
                foo,
                {
                    "b": ("x", "y"),
                    "a": [1, 2],
                },
            ),
        })

        self.assertEqual(
            first.semantic_digest,
            second.semantic_digest,
        )

    def test_state_equality_detects_different_values(self) -> None:
        foo = EntityID("foo")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = State.create({
            foo: Value.create(foo, 2),
        })

        self.assertNotEqual(first, second)

    def test_state_equality_includes_ownership(self) -> None:
        owner = EntityID("owner")
        child = EntityID("child")

        first = State.create(
            {
                owner: Value.create(owner, "owner"),
                child: Value.create(child, "child"),
            },
            {
                owner: (child,),
            },
        )

        second = State.create(
            {
                owner: Value.create(owner, "owner"),
                child: Value.create(child, "child"),
            },
        )

        self.assertNotEqual(first, second)

    def test_state_equality_ignores_input_mapping_order(self) -> None:
        first_entity = EntityID("first")
        second_entity = EntityID("second")

        first = State.create({
            first_entity: Value.create(
                first_entity,
                "one",
            ),
            second_entity: Value.create(
                second_entity,
                "two",
            ),
        })

        second = State.create({
            second_entity: Value.create(
                second_entity,
                "two",
            ),
            first_entity: Value.create(
                first_entity,
                "one",
            ),
        })

        self.assertEqual(first, second)
        self.assertEqual(first.id, second.id)


class StateContentStabilityTests(unittest.TestCase):
    def test_reapplying_existing_content_keeps_state_identity(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, (1, [2, 3])),
        })

        again = state.with_changes({
            foo: state.values[foo].content,
        })

        self.assertEqual(again.id, state.id)
        self.assertEqual(again, state)


class StateConstructionTests(unittest.TestCase):
    def test_state_identity_cannot_be_supplied(self) -> None:
        with self.assertRaises(TypeError):
            State(  # type: ignore[call-arg]
                id=StateID("forged"),
                values={},
            )

    def test_direct_construction_matches_create(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        values = {
            foo: Value.create(foo, 1),
            bar: Value.create(bar, 2),
        }

        self.assertEqual(
            State(values=values, ownership={foo: [bar]}),
            State.create(values, {foo: (bar,)}),
        )

    def test_direct_construction_validates_ownership(self) -> None:
        foo = EntityID("foo")
        ghost = EntityID("ghost")

        with self.assertRaises(OwnershipError):
            State(
                values={foo: Value.create(foo, 1)},
                ownership={ghost: (foo,)},
            )


if __name__ == "__main__":
    unittest.main()
