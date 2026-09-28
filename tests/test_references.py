"""Tests for state-pinned and version-pinned references."""

import unittest

from semiroh import (
    Reference,
    StateID,
    VersionID,
    CrossStateReference,
    EntityID,
    MissingEntityMapping,
    State,
    StaleReference,
    Value,
    project_entity,
    rebind_reference,
    semantic_equal,
    transfer_reference,
    transform,
    transform_with_mapping,
    version_id_for,
)

from semiroh.references import make_reference


class ReferenceTests(unittest.TestCase):
    def test_reference_is_version_pinned(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        reference = state.reference(foo)

        self.assertEqual(reference.state, state.id)
        self.assertEqual(reference.entity, foo)
        self.assertEqual(
            reference.version,
            version_id_for(state.values[foo]),
        )

    def test_cross_state_reference_does_not_rebind(self) -> None:
        foo = EntityID("foo")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = transform(first, {
            foo: 2,
        })

        with self.assertRaises(CrossStateReference):
            second.resolve(first.reference(foo))

    def test_stale_reference_is_detectable(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        reference = state.reference(foo)

        stale = type(reference)(
            state=state.id,
            entity=foo,
            version=version_id_for(
                Value.create(foo, 2)
            ),
        )

        with self.assertRaises(StaleReference):
            state.resolve(stale)

    def test_transfer_requires_explicit_mapping(self) -> None:
        foo = EntityID("foo")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = State.create({
            foo: Value.create(foo, 2),
        })

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(
                first.reference(foo),
                transform_with_mapping(
                    first,
                    {},
                    {},
                ),
            )

        self.assertNotEqual(second.id, first.id)

    def test_explicit_mapping_preserves_entity_identity(self) -> None:
        foo = EntityID("foo")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        result = transform_with_mapping(
            first,
            {foo: 2},
            {foo: foo},
        )

        source_reference = first.reference(foo)
        destination_reference = transfer_reference(
            source_reference,
            result,
        )

        self.assertEqual(project_entity(source_reference), foo)
        self.assertEqual(project_entity(destination_reference), foo)

        self.assertEqual(destination_reference.entity, foo)
        self.assertEqual(
            destination_reference.version,
            version_id_for(result.destination.values[foo]),
        )

        self.assertNotEqual(
            source_reference.version,
            destination_reference.version,
        )

    def test_explicit_mapping_can_rename_entity(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        result = transform_with_mapping(
            first,
            {bar: 2},
            {foo: bar},
        )

        destination_reference = transfer_reference(
            first.reference(foo),
            result,
        )

        self.assertEqual(destination_reference.entity, bar)
        self.assertEqual(
            destination_reference.version,
            version_id_for(result.destination.values[bar]),
        )

        self.assertEqual(
            result.destination.resolve(
                destination_reference
            ).content,
            2,
        )

    def test_rebind_is_not_transfer(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = State.create({
            foo: Value.create(foo, 1),
        })

        second = State.create({
            bar: Value.create(bar, 99),
        })

        source_reference = first.reference(foo)

        destination_reference = rebind_reference(
            source_reference,
            second,
            bar,
        )

        self.assertEqual(destination_reference.state, second.id)
        self.assertEqual(destination_reference.entity, bar)
        self.assertEqual(
            destination_reference.version,
            version_id_for(second.values[bar]),
        )

        self.assertEqual(project_entity(destination_reference), bar)
        self.assertNotEqual(
            project_entity(destination_reference),
            project_entity(source_reference),
        )

    def test_version_fast_path_for_exact_value(self) -> None:
        foo = EntityID("foo")

        first = State.create({
            foo: Value.create(foo, 42),
        })

        second = State.create({
            foo: Value.create(foo, 42),
        })

        source = first.reference(foo)
        destination = second.reference(foo)

        self.assertEqual(source.entity, destination.entity)
        self.assertEqual(source.version, destination.version)
        self.assertTrue(
            semantic_equal(
                first.resolve(source),
                second.resolve(destination),
            )
        )


class ReferenceConstructionTests(unittest.TestCase):
    def test_make_reference_rejects_value_of_another_entity(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        state = State.create({
            foo: Value.create(foo, 1),
            bar: Value.create(bar, 2),
        })

        with self.assertRaises(ValueError):
            make_reference(
                state.id,
                foo,
                state.values[bar],
            )


class RebindingTests(unittest.TestCase):
    def test_reference_that_cannot_be_transferred_can_be_rebound(self) -> None:
        foo = EntityID("foo")

        first = State.create({
            foo: Value.create(foo, 1),
        })
        second = transform(first, {foo: 2})

        stale = first.reference(foo)

        self.assertEqual(
            rebind_reference(stale, second, foo),
            second.reference(foo),
        )

    def test_original_reference_is_not_validated(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })
        foreign = Reference(
            StateID("elsewhere"),
            EntityID("missing"),
            VersionID("unknown"),
        )

        self.assertEqual(
            rebind_reference(foreign, state, foo),
            state.reference(foo),
        )

    def test_rebinding_requires_a_reference(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        with self.assertRaises(TypeError):
            rebind_reference(foo, state, foo)  # type: ignore[arg-type]

    def test_rebinding_to_absent_entity_is_rejected(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        with self.assertRaises(KeyError):
            rebind_reference(
                state.reference(foo),
                state,
                EntityID("missing"),
            )


if __name__ == "__main__":
    unittest.main()
