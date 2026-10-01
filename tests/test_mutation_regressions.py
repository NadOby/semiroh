"""Permanent regressions for semantic gaps found by mutation testing."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from semiroh import (
    AllOf,
    AnyOf,
    CellDeclaration,
    EntityID,
    External,
    IntRange,
    IsKind,
    Length,
    Not,
    OneOf,
    Relation,
    Role,
    State,
    StateID,
    Value,
    canonicalize,
    transform_with_mapping,
)
from semiroh.closures import Closure, closure_value
from semiroh.lang import Function
from semiroh.transforms import rebase


ENTITY = EntityID("entity")
OTHER = EntityID("other")
OWNER = EntityID("owner")
BODY = EntityID("body")


class SemanticRecordImmutabilityTests(unittest.TestCase):
    def test_public_semantic_records_are_immutable(self) -> None:
        value = Value.create(ENTITY, 1)
        state = State.create({
            ENTITY: value,
        })
        reference = state.reference(ENTITY)
        kind = IsKind("int")

        cases = (
            (value, "content", 2),
            (state, "values", {}),
            (reference, "entity", OTHER),
            (
                CellDeclaration(kind, 1),
                "initial",
                2,
            ),
            (
                Closure(
                    OWNER,
                    BODY,
                    ("x",),
                    (),
                ),
                "owner",
                OTHER,
            ),
            (
                Relation("example", {}),
                "kind",
                "changed",
            ),
            (
                Function(
                    ("x",),
                    ("arg", "x"),
                ),
                "params",
                (),
            ),
            (
                IsKind("int"),
                "kind",
                "str",
            ),
            (
                IntRange(0, 2),
                "min",
                1,
            ),
            (
                Length(0, 2),
                "min",
                1,
            ),
            (
                OneOf(1, 2),
                "values",
                (),
            ),
            (
                AllOf(kind),
                "parts",
                (),
            ),
            (
                AnyOf(kind),
                "parts",
                (),
            ),
            (
                Not(kind),
                "part",
                IsKind("str"),
            ),
            (
                Role("item", kind),
                "name",
                "changed",
            ),
            (
                External("external"),
                "name",
                "changed",
            ),
        )

        for record, field, replacement in cases:
            with self.subTest(record=type(record).__name__):
                with self.assertRaises(FrozenInstanceError):
                    setattr(record, field, replacement)

    def test_state_id_cannot_be_supplied_by_caller(self) -> None:
        with self.assertRaises(TypeError):
            State(
                id=StateID("forged"),
                values={
                    ENTITY: Value.create(ENTITY, 1),
                },
            )


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
