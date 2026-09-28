"""Tests for semantic identity and equality."""

import unittest

from semiroh import (
    EntityID,
    Value,
    semantic_equal,
    same_entity,
    same_version,
    version_id_for,
)


class IdentityTests(unittest.TestCase):
    def test_entity_version_changes_when_content_changes(self) -> None:
        foo = EntityID("foo")

        first = Value.create(foo, 1)
        second = Value.create(foo, 2)

        self.assertEqual(first.entity, second.entity)
        self.assertNotEqual(
            first.version_id,
            second.version_id,
        )
        self.assertNotEqual(
            version_id_for(first),
            version_id_for(second),
        )
        self.assertTrue(same_entity(first, second))
        self.assertFalse(same_version(first, second))

    def test_identical_entity_versions_have_identical_version_ids(self) -> None:
        foo = EntityID("foo")

        first = Value.create(foo, 42)
        second = Value.create(foo, 42)

        self.assertEqual(
            first.version_id,
            second.version_id,
        )
        self.assertEqual(
            first.version_id,
            version_id_for(first),
        )
        self.assertTrue(semantic_equal(first, second))
        self.assertTrue(same_entity(first, second))

    def test_version_id_is_history_independent(self) -> None:
        foo = EntityID("foo")

        direct = Value.create(foo, 42)
        intermediate = Value.create(foo, 1)

        self.assertEqual(
            direct.version_id,
            Value.create(foo, 42).version_id,
        )
        self.assertNotEqual(
            direct.version_id,
            intermediate.version_id,
        )

    def test_same_entity_different_versions_are_not_equal(self) -> None:
        foo = EntityID("foo")

        first = Value.create(foo, 1)
        second = Value.create(foo, 2)

        self.assertTrue(same_entity(first, second))
        self.assertFalse(semantic_equal(first, second))
        self.assertFalse(same_version(first, second))

    def test_different_entities_same_content_are_equal(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = Value.create(foo, 42)
        second = Value.create(bar, 42)

        self.assertFalse(same_entity(first, second))
        self.assertTrue(semantic_equal(first, second))
        self.assertNotEqual(
            first.version_id,
            second.version_id,
        )


class TypeDistinctEqualityTests(unittest.TestCase):
    def test_bool_and_int_are_distinct_values(self) -> None:
        foo = EntityID("foo")

        as_bool = Value(foo, True)
        as_int = Value(foo, 1)

        self.assertNotEqual(as_bool, as_int)
        self.assertEqual(len({as_bool, as_int}), 2)
        self.assertFalse(semantic_equal(as_bool, as_int))
        self.assertFalse(same_version(as_bool, as_int))

    def test_nested_bool_and_int_are_distinct(self) -> None:
        foo = EntityID("foo")

        self.assertFalse(
            semantic_equal(
                Value(foo, (True, [False])),
                Value(foo, (1, [0])),
            )
        )

    def test_value_equality_agrees_with_version_identity(self) -> None:
        foo = EntityID("foo")

        pairs = [
            (Value(foo, (1, 2)), Value(foo, (1, 2))),
            (Value(foo, (1, 2)), Value(foo, [1, 2])),
            (Value(foo, {"a": 1}), Value(foo, {"a": True})),
        ]

        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertEqual(
                    left == right,
                    same_version(left, right),
                )


if __name__ == "__main__":
    unittest.main()
