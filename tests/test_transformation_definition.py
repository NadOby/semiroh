"""Tests for immutable transformation definitions."""

import unittest

from semiroh import (
    AmbiguousEntityMapping,
    EntityChange,
    EntityID,
    MissingEntityMapping,
    State,
    TransformationDefinition,
    TransformationMapping,
    Value,
)


class TransformationDefinitionTests(unittest.TestCase):
    def test_definition_is_immutable(self) -> None:
        foo = EntityID("foo")

        definition = TransformationDefinition.create(
            changes={foo: 42},
        )

        with self.assertRaises(AttributeError):
            definition.changes = ()

    def test_changes_are_canonicalized_by_entity(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        first = TransformationDefinition.create(
            changes={
                bar: 2,
                foo: 1,
            },
        )

        second = TransformationDefinition.create(
            changes={
                foo: 1,
                bar: 2,
            },
        )

        self.assertEqual(first, second)

        self.assertEqual(
            tuple(change.entity for change in first.changes),
            tuple(sorted((foo, bar))),
        )

    def test_mappings_are_canonicalized_by_source_entity(self) -> None:
        source_a = EntityID("source-a")
        source_b = EntityID("source-b")
        destination_a = EntityID("destination-a")
        destination_b = EntityID("destination-b")

        first = TransformationDefinition.create(
            mappings={
                source_b: destination_b,
                source_a: destination_a,
            },
        )

        second = TransformationDefinition.create(
            mappings={
                source_a: destination_a,
                source_b: destination_b,
            },
        )

        self.assertEqual(first, second)

        self.assertEqual(
            tuple(
                mapping.source_entity
                for mapping in first.mappings
            ),
            tuple(sorted((source_a, source_b))),
        )

    def test_change_contains_immutable_semantic_value(self) -> None:
        foo = EntityID("foo")
        value = Value.create(foo, 42)

        change = EntityChange(
            entity=foo,
            value=value,
        )

        self.assertEqual(change.entity, foo)
        self.assertEqual(change.value, value)

    def test_change_rejects_value_for_another_entity(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        with self.assertRaises(ValueError):
            EntityChange(
                entity=foo,
                value=Value.create(bar, 42),
            )

    def test_duplicate_changes_are_rejected(self) -> None:
        foo = EntityID("foo")

        with self.assertRaises(ValueError):
            TransformationDefinition(
                changes=(
                    EntityChange(
                        entity=foo,
                        value=Value.create(foo, 1),
                    ),
                    EntityChange(
                        entity=foo,
                        value=Value.create(foo, 2),
                    ),
                ),
                mappings=(),
            )

    def test_duplicate_mappings_are_rejected(self) -> None:
        foo = EntityID("foo")
        bar = EntityID("bar")

        with self.assertRaises(ValueError):
            TransformationDefinition(
                changes=(),
                mappings=(
                    TransformationMapping(
                        source_entity=foo,
                        destination_entities=(bar,),
                    ),
                    TransformationMapping(
                        source_entity=foo,
                        destination_entities=(),
                    ),
                ),
            )

    def test_mapping_destination_entities_are_canonicalized(self) -> None:
        source = EntityID("source")
        first = EntityID("destination-a")
        second = EntityID("destination-b")

        mapping = TransformationMapping(
            source_entity=source,
            destination_entities=tuple(
                sorted((second, first))
            ),
        )

        self.assertEqual(
            mapping.destination_entities,
            (first, second),
        )

    def test_mapping_rejects_duplicate_destination_entities(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        with self.assertRaises(ValueError):
            TransformationMapping(
                source_entity=source,
                destination_entities=(
                    destination,
                    destination,
                ),
            )

    def test_mapping_rejects_noncanonical_destination_order(self) -> None:
        source = EntityID("source")
        first = EntityID("destination-a")
        second = EntityID("destination-b")

        with self.assertRaises(ValueError):
            TransformationMapping(
                source_entity=source,
                destination_entities=(
                    second,
                    first,
                ),
            )

    def test_unmentioned_entity_is_preserved_unchanged(self) -> None:
        unchanged = EntityID("unchanged")
        changed = EntityID("changed")

        state = State.create({
            unchanged: Value.create(unchanged, 1),
            changed: Value.create(changed, 2),
        })

        definition = TransformationDefinition.create(
            changes={
                changed: 20,
            },
            mappings={
                changed: changed,
            },
        )

        result = definition.apply(state)

        self.assertTrue(
            result.destination.contains(unchanged),
        )
        self.assertEqual(
            result.destination.values[unchanged].content,
            1,
        )
        self.assertEqual(
            result.destination.values[changed].content,
            20,
        )

    def test_unmentioned_entity_has_no_implicit_continuity_mapping(self) -> None:
        unchanged = EntityID("unchanged")
        changed = EntityID("changed")

        state = State.create({
            unchanged: Value.create(unchanged, 1),
            changed: Value.create(changed, 2),
        })

        definition = TransformationDefinition.create(
            changes={
                changed: 20,
            },
            mappings={
                changed: changed,
            },
        )

        result = definition.apply(state)

        self.assertEqual(
            result.mappings,
            (
                result.mappings[0],
            ),
        )
        self.assertEqual(
            result.mappings[0].source_entity,
            changed,
        )

        with self.assertRaises(MissingEntityMapping):
            result.mapped_entity(state.reference(unchanged))

    def test_existing_entity_can_change_without_mapping(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create(
            changes={
                foo: 2,
            },
        )

        result = definition.apply(state)

        self.assertTrue(
            result.destination.contains(foo),
        )
        self.assertEqual(
            result.destination.values[foo].content,
            2,
        )
        self.assertEqual(
            result.mappings,
            (),
        )

    def test_new_entity_is_created_without_mapping(self) -> None:
        created = EntityID("created")

        state = State.create({})

        definition = TransformationDefinition.create(
            changes={
                created: 42,
            },
        )

        result = definition.apply(state)

        self.assertTrue(
            result.destination.contains(created),
        )
        self.assertEqual(
            result.destination.values[created].content,
            42,
        )
        self.assertEqual(
            result.mappings,
            (),
        )

    def test_mapping_source_must_exist_even_when_value_is_changed(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")
        missing = EntityID("missing")

        state = State.create({
            source: Value.create(source, 1),
        })

        definition = TransformationDefinition.create(
            changes={
                destination: 2,
            },
            mappings={
                missing: destination,
            },
        )

        with self.assertRaises(KeyError):
            definition.apply(state)

    def test_mapping_destination_can_be_created_by_a_change(self) -> None:
        source = EntityID("source")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
        })

        definition = TransformationDefinition.create(
            changes={
                destination: 2,
            },
            mappings={
                source: destination,
            },
        )

        result = definition.apply(state)

        self.assertTrue(
            result.destination.contains(destination),
        )
        self.assertFalse(
            result.destination.contains(source),
        )
        self.assertEqual(
            result.destination.values[destination].content,
            2,
        )
        self.assertEqual(
            result.mapped_entities(state.reference(source)),
            (destination,),
        )

    def test_apply_replaces_existing_value_with_explicit_continuity(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create(
            changes={
                foo: 2,
            },
            mappings={
                foo: foo,
            },
        )

        result = definition.apply(state)

        self.assertEqual(
            result.destination.values[foo].content,
            2,
        )
        self.assertTrue(
            result.destination.contains(foo),
        )
        self.assertNotEqual(
            result.destination.id,
            state.id,
        )

        self.assertEqual(
            result.mapped_entities(state.reference(foo)),
            (foo,),
        )

    def test_mapping_source_change_removes_source_without_implicit_mapping_for_others(
        self,
    ) -> None:
        source = EntityID("source")
        unchanged = EntityID("unchanged")
        destination = EntityID("destination")

        state = State.create({
            source: Value.create(source, 1),
            unchanged: Value.create(unchanged, 2),
        })

        definition = TransformationDefinition.create(
            changes={
                destination: 20,
            },
            mappings={
                source: destination,
            },
        )

        result = definition.apply(state)

        self.assertFalse(
            result.destination.contains(source),
        )
        self.assertEqual(
            result.destination.values[destination].content,
            20,
        )
        self.assertEqual(
            result.destination.values[unchanged].content,
            2,
        )
        self.assertEqual(
            len(result.mappings),
            1,
        )
        self.assertEqual(
            result.mappings[0].source_entity,
            source,
        )

    def test_change_to_a_disappearing_entity_is_rejected(self) -> None:
        # Changing an entity and declaring its disappearance is
        # contradictory; it is rejected rather than resolved silently.
        foo = EntityID("foo")

        with self.assertRaises(ValueError):
            TransformationDefinition.create(
                changes={
                    foo: 99,
                },
                mappings={
                    foo: (),
                },
            )

    def test_apply_can_disappear_an_entity(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create(
            mappings={
                foo: (),
            },
        )

        result = definition.apply(state)

        self.assertFalse(
            result.destination.contains(foo),
        )
        self.assertEqual(
            result.mappings[0].destination_entities,
            (),
        )

        with self.assertRaises(MissingEntityMapping):
            result.mapped_entity(state.reference(foo))

    def test_apply_can_split_an_entity(self) -> None:
        source = EntityID("source")
        first = EntityID("destination-a")
        second = EntityID("destination-b")

        state = State.create({
            source: Value.create(source, 1),
            first: Value.create(first, 2),
            second: Value.create(second, 3),
        })

        definition = TransformationDefinition.create(
            mappings={
                source: (second, first),
            },
        )

        result = definition.apply(state)

        self.assertEqual(
            result.mappings[0].destination_entities,
            (first, second),
        )

        with self.assertRaises(AmbiguousEntityMapping):
            result.mapped_entity(state.reference(source))

    def test_apply_does_not_modify_source_state(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create(
            changes={
                foo: 2,
            },
            mappings={
                foo: foo,
            },
        )

        result = definition.apply(state)

        self.assertEqual(
            state.values[foo].content,
            1,
        )
        self.assertEqual(
            result.destination.values[foo].content,
            2,
        )

    def test_empty_definition_preserves_state_content(self) -> None:
        foo = EntityID("foo")

        state = State.create({
            foo: Value.create(foo, 1),
        })

        definition = TransformationDefinition.create()

        result = definition.apply(state)

        self.assertEqual(
            result.destination.id,
            state.id,
        )
        self.assertEqual(
            result.destination.values,
            state.values,
        )
        self.assertEqual(
            result.destination.ownership,
            state.ownership,
        )
        self.assertEqual(
            result.mappings,
            (),
        )


class ConversionDeclarationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.a = EntityID("a")
        self.b = EntityID("b")
        self.c = EntityID("c")

        self.state = State.create({
            self.a: Value.create(self.a, 1),
            self.b: Value.create(self.b, 2),
        })

    def test_conversions_are_canonically_ordered(self) -> None:
        definition = TransformationDefinition.create(
            changes={self.c: 0},
            mappings={self.a: self.c, self.b: self.b},
            conversions={self.c: "to_c", self.b: "to_b"},
        )

        self.assertEqual(
            definition.conversions,
            ((self.b, "to_b"), (self.c, "to_c")),
        )

    def test_result_carries_conversions(self) -> None:
        result = TransformationDefinition.create(
            changes={self.c: 0},
            mappings={self.a: self.c},
            conversions={self.c: "to_c"},
        ).apply(self.state)

        self.assertEqual(result.conversion_for(self.c), "to_c")
        self.assertIsNone(result.conversion_for(self.b))

    def test_conversion_must_target_a_mapping_destination(self) -> None:
        definition = TransformationDefinition.create(
            changes={self.c: 0},
            conversions={self.c: "to_c"},
        )

        with self.assertRaises(ValueError):
            definition.apply(self.state)

    def test_invalid_conversion_records_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TransformationDefinition(
                changes=(),
                mappings=(),
                conversions=((self.c, "x"), (self.b, "y")),
            )

        with self.assertRaises(ValueError):
            TransformationDefinition(
                changes=(),
                mappings=(),
                conversions=((self.b, "x"), (self.b, "y")),
            )

        with self.assertRaises(TypeError):
            TransformationDefinition(
                changes=(),
                mappings=(),
                conversions=((self.b, ""),),
            )
