"""Permanent regressions for semantic gaps found by mutation testing."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from semiroh import (
    AllOf,
    CellDeclaration,
    EntityID,
    State,
    Value,
    canonicalize,
    transform_with_mapping,
)
from semiroh.closures import Closure, closure_value
from semiroh.transforms import rebase


ENTITY = EntityID("entity")
OTHER = EntityID("other")
OWNER = EntityID("owner")
BODY = EntityID("body")


class SemanticRecordImmutabilityTests(unittest.TestCase):
    def test_public_pinned_semantic_records_are_immutable(self) -> None:
        value = Value.create(ENTITY, 1)
        state = State.create({
            ENTITY: value,
        })
        reference = state.reference(ENTITY)
        constraint = AllOf()

        cases = (
            (value, "content", 2),
            (state, "values", {}),
            (reference, "entity", OTHER),
            (constraint, "parts", (AllOf(),)),
        )

        for record, field, replacement in cases:
            with self.subTest(record=type(record).__name__):
                with self.assertRaises(FrozenInstanceError):
                    setattr(record, field, replacement)


class SemanticEqualityRegressionTests(unittest.TestCase):
    def test_unrelated_semantic_records_compare_false(self) -> None:
        records = (
            Value.create(ENTITY, 1),
            CellDeclaration(AllOf(), 1),
            AllOf(),
            Closure(
                OWNER,
                BODY,
                ("x",),
                (),
            ),
        )

        for record in records:
            with self.subTest(record=type(record).__name__):
                self.assertIs(
                    record == object(),
                    False,
                )


class ClosureCanonicalRegressionTests(unittest.TestCase):
    def test_canonical_closure_decodes_primitive_params_and_captures(
        self,
    ) -> None:
        original = Closure(
            OWNER,
            BODY,
            ("x",),
            (("n", 4),),
        )

        decoded = closure_value(canonicalize(original))

        self.assertEqual(decoded, original)

    def test_canonical_closure_decodes_list_capture_structure(
        self,
    ) -> None:
        original = Closure(
            OWNER,
            BODY,
            (),
            (("items", [1, 2]),),
        )

        decoded = closure_value(canonicalize(original))

        self.assertEqual(decoded, original)
        self.assertEqual(
            decoded.captures,
            (("items", [1, 2]),),
        )


class RebaseMappingRegressionTests(unittest.TestCase):
    def test_rebase_preserves_explicit_identity_mapping(self) -> None:
        source = State.create({
            ENTITY: Value.create(ENTITY, 1),
            OTHER: Value.create(OTHER, 2),
        })

        identity = transform_with_mapping(
            source,
            {},
            {
                ENTITY: ENTITY,
            },
        )
        onto = transform_with_mapping(
            source,
            {
                OTHER: 3,
            },
            {},
        )

        rebased = rebase(identity, onto)
        mapping = rebased.mapping_for(ENTITY)

        self.assertIsNotNone(mapping)
        self.assertEqual(
            mapping.destination_entities,
            (ENTITY,),
        )


if __name__ == "__main__":
    unittest.main()
