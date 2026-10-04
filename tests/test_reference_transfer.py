"""Tests for state-local reference transfer."""

import unittest

from shear import (
    AmbiguousEntityMapping,
    CrossStateReference,
    EntityID,
    MissingEntityMapping,
    Reference,
    StaleReference,
    State,
    Value,
    transfer_reference,
    transform_with_mapping,
    version_id_for,
)


class ReferenceTransferTests(unittest.TestCase):
    def test_created_entity_has_no_predecessor_for_reference_transfer(
        self,
    ) -> None:
        source = EntityID("source")
        created = EntityID("created")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                created: 42,
            },
            {},
        )

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(
                state.reference(source),
                result,
            )

        self.assertTrue(
            result.destination.contains(created)
        )

    def test_split_mapping_cannot_transfer_reference(self) -> None:
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
            transfer_reference(
                state.reference(source),
                result,
            )

    def test_disappearance_cannot_transfer_reference(self) -> None:
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

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(
                state.reference(source),
                result,
            )

    def test_merge_allows_both_references_to_transfer(self) -> None:
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

        first_reference = transfer_reference(
            state.reference(first),
            result,
        )

        second_reference = transfer_reference(
            state.reference(second),
            result,
        )

        self.assertEqual(first_reference.entity, merged)
        self.assertEqual(second_reference.entity, merged)
        self.assertEqual(
            first_reference.state,
            result.destination.id,
        )
        self.assertEqual(
            second_reference.state,
            result.destination.id,
        )

    def test_transferred_reference_is_pinned_to_destination_version(
        self,
    ) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        result = transform_with_mapping(
            state,
            {
                destination: 42,
            },
            {
                source: destination,
            },
        )

        transferred = transfer_reference(
            state.reference(source),
            result,
        )

        self.assertEqual(
            transferred.version,
            version_id_for(
                result.destination.values[destination]
            ),
        )
        self.assertEqual(
            result.destination.resolve(transferred),
            result.destination.values[destination],
        )

    def test_transfer_rejects_stale_source_reference(self) -> None:
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

        actual_version = state.reference(source).version
        stale_version = version_id_for(
            Value.create(source, 999)
        )

        self.assertNotEqual(
            stale_version,
            actual_version,
        )

        stale_reference = Reference(
            state=state.id,
            entity=source,
            version=stale_version,
        )

        with self.assertRaises(StaleReference):
            transfer_reference(
                stale_reference,
                result,
            )

    def test_transfer_rejects_reference_from_another_state(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        other_state = State.create({
            source: Value.create(source, 2),
        })

        result = transform_with_mapping(
            state,
            {
                destination: 3,
            },
            {
                source: destination,
            },
        )

        other_reference = other_state.reference(source)

        with self.assertRaises(CrossStateReference):
            transfer_reference(
                other_reference,
                result,
            )

    def test_transfer_requires_the_exact_source_version_even_when_entity_is_preserved(
        self,
    ) -> None:
        source = EntityID("source")

        initial = State.create({
            source: Value.create(source, 1),
        })

        changed = transform_with_mapping(
            initial,
            {
                source: 2,
            },
            {
                source: source,
            },
        )

        self.assertEqual(
            changed.destination.reference(source).entity,
            source,
        )
        self.assertNotEqual(
            changed.destination.reference(source).version,
            initial.reference(source).version,
        )

        with self.assertRaises(StaleReference):
            transfer_reference(
                Reference(
                    state=initial.id,
                    entity=source,
                    version=version_id_for(
                        Value.create(source, 999)
                    ),
                ),
                changed,
            )

        transferred = transfer_reference(
            initial.reference(source),
            changed,
        )

        self.assertEqual(
            transferred.entity,
            source,
        )
        self.assertEqual(
            transferred.version,
            changed.destination.reference(source).version,
        )

    def test_disappearance_does_not_provide_a_mapping_for_next_transform(
        self,
    ) -> None:
        source = EntityID("source")
        replacement = EntityID("replacement")

        initial = State.create({
            source: Value.create(source, 1),
        })

        disappeared = transform_with_mapping(
            initial,
            {},
            {
                source: (),
            },
        )

        next_result = transform_with_mapping(
            disappeared.destination,
            {
                replacement: 2,
            },
            {},
        )

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(
                initial.reference(source),
                disappeared,
            )

        with self.assertRaises(CrossStateReference):
            transfer_reference(
                initial.reference(source),
                next_result,
            )

    def test_sequential_mapping_requires_each_intermediate_state(
        self,
    ) -> None:
        first = EntityID("first")
        second = EntityID("second")
        third = EntityID("third")

        initial = State.create({
            first: Value.create(first, 1),
        })

        first_result = transform_with_mapping(
            initial,
            {
                second: 2,
            },
            {
                first: second,
            },
        )

        second_result = transform_with_mapping(
            first_result.destination,
            {
                third: 3,
            },
            {
                second: third,
            },
        )

        with self.assertRaises(CrossStateReference):
            transfer_reference(
                initial.reference(first),
                second_result,
            )

        transferred = transfer_reference(
            initial.reference(first),
            first_result,
        )
        transferred = transfer_reference(
            transferred,
            second_result,
        )

        self.assertEqual(transferred.entity, third)


if __name__ == "__main__":
    unittest.main()
