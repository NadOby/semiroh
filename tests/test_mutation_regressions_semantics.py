"""Mutation regressions for core semantic records and canonicalization."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from semiroh import (
    AllOf,
    AnyOf,
    CellDeclaration,
    Constraint,
    ConstraintResult,
    Entity,
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
    VersionID,
    canonical_serialize,
    canonicalize,
)
from semiroh.canonical import CanonicalNode
from semiroh.closures import Closure, closure_value
from semiroh.lang import FUNCTION_ROLE, Function, load
from semiroh.transforms import (
    EntityChange,
    TransformationMapping,
)


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
            (
                EntityID("identity"),
                "value",
                "changed",
            ),
            (
                VersionID("version"),
                "value",
                "changed",
            ),
            (
                StateID("state"),
                "value",
                "changed",
            ),
            (
                Entity(EntityID("entity-record")),
                "id",
                OTHER,
            ),
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
                EntityChange(
                    ENTITY,
                    value,
                ),
                "entity",
                OTHER,
            ),
            (
                TransformationMapping(
                    ENTITY,
                    (ENTITY,),
                ),
                "destination_entities",
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
            State.create({
                ENTITY: Value.create(
                    ENTITY,
                    1,
                ),
            }),
        )

        for record in records:
            with self.subTest(record=type(record).__name__):
                self.assertIs(
                    record == object(),
                    False,
                )

    def test_equal_cell_declarations_have_equal_hashes(self) -> None:
        first = CellDeclaration(
            IsKind("int"),
            0,
        )
        second = CellDeclaration(
            IsKind("int"),
            0,
        )

        self.assertEqual(first, second)
        self.assertEqual(
            hash(first),
            hash(second),
        )
        self.assertEqual(
            {first: "cell"}[second],
            "cell",
        )

    def test_equal_functions_have_equal_hashes(self) -> None:
        first = Function(
            ("x",),
            ("arg", "x"),
        )
        second = Function(
            ("x",),
            ("arg", "x"),
        )

        self.assertEqual(first, second)
        self.assertEqual(
            hash(first),
            hash(second),
        )
        self.assertEqual(
            {first: "function"}[second],
            "function",
        )


class LanguageGraphMutationRegressionTests(unittest.TestCase):
    def test_load_keeps_non_links_relation_with_function_role(self) -> None:
        function = Function(
            (),
            ("lit", 1),
        )
        metadata = Relation(
            "metadata",
            {
                FUNCTION_ROLE: ENTITY,
            },
        )
        state = State.create({
            ENTITY: Value.create(
                ENTITY,
                function,
            ),
            OTHER: Value.create(
                OTHER,
                metadata,
            ),
        })

        loaded = load(state)

        self.assertIn(OTHER, loaded.values)
        self.assertEqual(
            loaded.values[OTHER],
            state.values[OTHER],
        )


class ConstraintMutationRegressionTests(unittest.TestCase):
    def test_default_length_accepts_empty_sized_values(self) -> None:
        self.assertEqual(
            Length().evaluate(""),
            ConstraintResult.SATISFIED,
        )

    def test_external_name_must_not_be_empty(self) -> None:
        with self.assertRaises(TypeError):
            External("")

    def test_from_content_rejects_plain_tuple_forgery(self) -> None:
        forged = (
            "__type__",
            "constraint",
            ("is_kind", "int"),
        )

        with self.assertRaisesRegex(
            ValueError,
            "content is not a semantic constraint",
        ):
            Constraint.from_content(forged)


class CanonicalSerializationRegressionTests(unittest.TestCase):
    def test_mapping_order_is_irrelevant_when_values_are_equal(
        self,
    ) -> None:
        first = {
            "a": 0,
            "b": 0,
        }
        second = {
            "b": 0,
            "a": 0,
        }

        self.assertEqual(
            canonical_serialize(first),
            canonical_serialize(second),
        )

    def test_state_id_serializes_to_bytes(self) -> None:
        encoded = canonical_serialize(
            StateID("state"),
        )

        self.assertIsInstance(
            encoded,
            bytes,
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

    def test_canonical_closure_rejects_malformed_entity_tag(
        self,
    ) -> None:
        malformed_owner = CanonicalNode((
            "__type__",
            "wrong",
            OWNER.value,
        ))
        encoded = CanonicalNode((
            "__type__",
            "closure",
            (
                malformed_owner,
                canonicalize(BODY),
                canonicalize(()),
                canonicalize(()),
            ),
        ))

        self.assertIsNone(
            closure_value(encoded),
        )


if __name__ == "__main__":
    unittest.main()
