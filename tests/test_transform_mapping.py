"""Tests for explicit transformation mappings."""

import unittest

from semiroh import (
    transfer_reference,
    AmbiguousEntityMapping,
    EntityID,
    EntityMapping,
    MissingEntityMapping,
    OwnershipError,
    State,
    TransformResult,
    Value,
    transform_with_mapping,
)


class TransformMappingTests(unittest.TestCase):
    def test_mapped_entities_returns_single_destination(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        result = transform_with_mapping(
            state,
            {
                bar: 2,
            },
            {
                foo: bar,
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(foo)),
            (bar,),
        )

    def test_creation_does_not_require_a_source_mapping(self) -> None:
        created = EntityID("created")

        state = State.create({})

        result = transform_with_mapping(
            state,
            {
                created: 42,
            },
            {},
        )

        self.assertTrue(
            result.destination.contains(created)
        )
        self.assertEqual(
            result.mappings,
            (),
        )

    def test_split_mapping_returns_all_destinations(self) -> None:
        source = EntityID("source")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                source: (right, left),
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(source)),
            (left, right),
        )

    def test_split_mapping_is_ambiguous_for_mapped_entity(self) -> None:
        source = EntityID("source")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                source: (left, right),
            },
        )

        with self.assertRaises(AmbiguousEntityMapping):
            result.mapped_entity(state.reference(source))

    def test_explicit_disappearance_removes_source_entity(self) -> None:
        source = EntityID("source")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {},
            {
                source: (),
            },
        )

        self.assertFalse(
            result.destination.contains(source)
        )
        self.assertEqual(
            result.mapped_entities(state.reference(source)),
            (),
        )

    def test_explicit_disappearance_is_distinct_from_missing_mapping(
        self,
    ) -> None:
        source = EntityID("source")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {},
            {
                source: (),
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(source)),
            (),
        )

        with self.assertRaises(MissingEntityMapping):
            transform_with_mapping(
                state,
                {},
                {},
            ).mapped_entity(state.reference(source))

    def test_owner_disappearing_while_children_remain_is_rejected(
        self,
    ) -> None:
        root = EntityID("root")
        child = EntityID("child")
        sibling = EntityID("sibling")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
                sibling: Value.create(sibling, 3),
            },
            {
                root: (child, sibling),
            },
        )

        # The children would change owner implicitly (become unowned).
        with self.assertRaises(OwnershipError):
            transform_with_mapping(
                state,
                {},
                {
                    root: (),
                },
            )

        # Supplying destination ownership states the change explicitly.
        result = transform_with_mapping(
            state,
            {},
            {
                root: (),
            },
            ownership={},
        )

        self.assertFalse(
            result.destination.contains(root)
        )
        self.assertTrue(
            result.destination.contains(child)
        )
        self.assertTrue(
            result.destination.contains(sibling)
        )
        self.assertEqual(
            result.destination.ownership,
            {},
        )

    def test_disappearance_removes_entity_from_parent_ownership(self) -> None:
        root = EntityID("root")
        child = EntityID("child")
        sibling = EntityID("sibling")

        state = State.create(
            {
                root: Value.create(root, 1),
                child: Value.create(child, 2),
                sibling: Value.create(sibling, 3),
            },
            {
                root: (child, sibling),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                child: (),
            },
        )

        self.assertFalse(
            result.destination.contains(child)
        )
        self.assertEqual(
            result.destination.ownership,
            {
                root: (sibling,),
            },
        )

    def test_merge_maps_multiple_sources_to_one_destination(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        merged = EntityID("merged")

        state = State.create({
            first: Value.create(first, 1),
            second: Value.create(second, 2),
        })

        result = transform_with_mapping(
            state,
            {
                merged: 3,
            },
            {
                first: merged,
                second: merged,
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(first)),
            (merged,),
        )
        self.assertEqual(
            result.mapped_entities(state.reference(second)),
            (merged,),
        )

        self.assertEqual(
            result.mapped_entity(state.reference(first)),
            merged,
        )
        self.assertEqual(
            result.mapped_entity(state.reference(second)),
            merged,
        )

    def test_many_to_many_mapping_returns_complete_relation(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            first: Value.create(first, 1),
            second: Value.create(second, 2),
        })

        result = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                first: (right, left),
                second: (left, right),
            },
        )

        self.assertEqual(
            result.mapped_entities(state.reference(first)),
            (left, right),
        )
        self.assertEqual(
            result.mapped_entities(state.reference(second)),
            (left, right),
        )

    def test_mapping_destination_order_is_canonicalized(self) -> None:
        source = EntityID("source")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            source: Value.create(source, 1),
        })

        result_a = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                source: (right, left),
            },
        )

        result_b = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                source: (left, right),
            },
        )

        self.assertEqual(result_a.mappings, result_b.mappings)

    def test_mapping_source_order_is_canonicalized(self) -> None:
        first = EntityID("first")
        second = EntityID("second")
        left = EntityID("left")
        right = EntityID("right")

        state = State.create({
            first: Value.create(first, 1),
            second: Value.create(second, 2),
        })

        result_a = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                second: (right,),
                first: (left,),
            },
        )

        result_b = transform_with_mapping(
            state,
            {
                left: 10,
                right: 20,
            },
            {
                first: (left,),
                second: (right,),
            },
        )

        self.assertEqual(result_a.mappings, result_b.mappings)

    def test_duplicate_destinations_are_rejected(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        with self.assertRaises(ValueError):
            transform_with_mapping(
                state,
                {
                    destination: 2,
                },
                {
                    source: (
                        destination,
                        destination,
                    ),
                },
            )

    def test_mapping_requires_existing_source_entity(self) -> None:
        source = EntityID("source")
        missing = EntityID("missing")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        with self.assertRaises(KeyError):
            transform_with_mapping(
                state,
                {
                    destination: 2,
                },
                {
                    missing: destination,
                },
            )

    def test_mapping_requires_existing_destination_entity(self) -> None:
        source = EntityID("source")
        missing = EntityID("missing")

        state = State.create({
            source: Value.create(source, 1),
        })

        with self.assertRaises(KeyError):
            transform_with_mapping(
                state,
                {},
                {
                    source: missing,
                },
            )

    def test_mapping_accepts_bare_entity_id_compatibility_form(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                destination: 2,
            },
            {
                source: destination,
            },
        )

        self.assertEqual(
            result.mapped_entities(
                state.reference(source)
            ),
            (destination,),
        )

    def test_transition_mapping_affects_destination_state_identity(
        self,
    ) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        mapped = transform_with_mapping(
            state,
            {
                destination: 2,
            },
            {
                source: destination,
            },
        )

        unmapped = transform_with_mapping(
            state,
            {
                destination: 2,
            },
            {},
        )

        self.assertNotEqual(
            mapped.destination.id,
            unmapped.destination.id,
        )

    def test_transition_mapping_carries_ownership_to_the_continuation(
        self,
    ) -> None:
        source = EntityID("source")
        destination = EntityID("destination")
        child = EntityID("child")

        state = State.create(
            {
                source: Value.create(source, 1),
                destination: Value.create(destination, 2),
                child: Value.create(child, 3),
            },
            {
                source: (child,),
            },
        )

        result = transform_with_mapping(
            state,
            {},
            {
                source: destination,
            },
        )

        # destination continues source, so it keeps source's children.
        self.assertEqual(
            result.destination.ownership,
            {
                destination: (child,),
            },
        )
        self.assertFalse(
            result.destination.contains(source),
        )
        self.assertTrue(
            result.destination.contains(destination),
        )
        self.assertTrue(
            result.destination.contains(child),
        )

    def test_transform_result_rejects_mapping_for_wrong_source_state(
        self,
    ) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = State.create({
            bar: Value.create(bar, 2),
        })

        with self.assertRaises(ValueError):
            TransformResult(
                source=first,
                destination=second,
                mappings=(
                    EntityMapping(
                        source_state=second.id,
                        source_entity=foo,
                        destination_entities=(bar,),
                    ),
                ),
            )

    def test_transform_result_rejects_missing_source_entity(self) -> None:
        foo = EntityID("foo")
        missing = EntityID("missing")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = State.create({
            bar: Value.create(bar, 2),
        })

        with self.assertRaises(ValueError):
            TransformResult(
                source=first,
                destination=second,
                mappings=(
                    EntityMapping(
                        source_state=first.id,
                        source_entity=missing,
                        destination_entities=(bar,),
                    ),
                ),
            )

    def test_transform_result_rejects_missing_destination_entity(
        self,
    ) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")
        missing = EntityID("missing")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = State.create({
            bar: Value.create(bar, 2),
        })

        with self.assertRaises(ValueError):
            TransformResult(
                source=first,
                destination=second,
                mappings=(
                    EntityMapping(
                        source_state=first.id,
                        source_entity=foo,
                        destination_entities=(missing,),
                    ),
                ),
    )


class MappedSourcePresenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.a = EntityID("a")
        self.b = EntityID("b")
        self.c = EntityID("c")

        self.state = State.create({
            self.a: Value.create(self.a, 1),
            self.b: Value.create(self.b, 2),
        })

    def test_swap_mapping_can_be_applied(self) -> None:
        result = transform_with_mapping(
            self.state,
            {},
            {
                self.a: self.b,
                self.b: self.a,
            },
        )

        self.assertTrue(result.destination.contains(self.a))
        self.assertTrue(result.destination.contains(self.b))

        # Content is unchanged; only declared continuity differs.
        self.assertEqual(result.destination.id, self.state.id)

        transferred = transfer_reference(
            self.state.reference(self.a),
            result,
        )

        self.assertEqual(transferred.entity, self.b)

    def test_shift_chain_can_be_applied(self) -> None:
        result = transform_with_mapping(
            self.state,
            {
                self.c: 3,
            },
            {
                self.a: self.b,
                self.b: self.c,
            },
        )

        self.assertFalse(result.destination.contains(self.a))
        self.assertTrue(result.destination.contains(self.b))
        self.assertTrue(result.destination.contains(self.c))

        self.assertEqual(
            transfer_reference(
                self.state.reference(self.a),
                result,
            ).entity,
            self.b,
        )
        self.assertEqual(
            transfer_reference(
                self.state.reference(self.b),
                result,
            ).entity,
            self.c,
        )

    def test_destination_declared_to_disappear_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            transform_with_mapping(
                self.state,
                {},
                {
                    self.a: self.b,
                    self.b: (),
                },
            )

    def test_retained_mapped_source_receives_its_change(self) -> None:
        result = transform_with_mapping(
            self.state,
            {
                self.a: 10,
            },
            {
                self.a: self.b,
                self.b: self.a,
            },
        )

        self.assertEqual(
            result.destination.values[self.a],
            Value.create(self.a, 10),
        )

    def test_change_to_a_source_mapped_elsewhere_is_rejected(
        self,
    ) -> None:
        # The mappings remove a, so a change to a is contradictory.
        with self.assertRaises(ValueError):
            transform_with_mapping(
                self.state,
                {
                    self.a: 99,
                    self.c: 3,
                },
                {
                    self.a: self.c,
                },
            )
