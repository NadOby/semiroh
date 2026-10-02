"""Mutation regressions for semantic records and transformation results."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from semiroh import (
    CompositionResult,
    EntityID,
    Relation,
    RelationRewrite,
    State,
    TransformResult,
    TransformationMapping,
    Value,
    canonicalize,
)
from semiroh.closures import Closure, closure_value


OWNER = EntityID("owner")
BODY = EntityID("body")
A = EntityID("a")
B = EntityID("b")
C = EntityID("c")
RELATION = EntityID("relation")


class SemanticRecordRegressionTests(unittest.TestCase):
    def test_canonical_closure_preserves_mapping_capture(self) -> None:
        original = Closure(
            OWNER,
            BODY,
            (),
            (
                (
                    "data",
                    {
                        "target": EntityID("captured"),
                    },
                ),
            ),
        )

        decoded = closure_value(canonicalize(original))

        self.assertIsNotNone(decoded)
        self.assertEqual(decoded, original)

    def test_closure_rejects_non_string_capture_name(self) -> None:
        with self.assertRaises(TypeError):
            Closure(
                OWNER,
                BODY,
                (),
                ((1, 2),),
            )

    def test_equal_semantic_records_have_equal_hashes(self) -> None:
        cases = (
            (
                Closure(
                    OWNER,
                    BODY,
                    ("x",),
                    (("n", 1),),
                ),
                Closure(
                    OWNER,
                    BODY,
                    ("x",),
                    (("n", 1),),
                ),
            ),
            (
                Relation(
                    "edge",
                    {"to": A},
                ),
                Relation(
                    "edge",
                    {"to": A},
                ),
            ),
        )

        for first, second in cases:
            with self.subTest(record=type(first).__name__):
                self.assertEqual(first, second)
                self.assertEqual(
                    hash(first),
                    hash(second),
                )
                self.assertEqual(
                    {first: "value"}[second],
                    "value",
                )

    def test_relation_compares_false_to_unrelated_type(self) -> None:
        relation = Relation(
            "edge",
            {"to": A},
        )

        self.assertIs(
            relation == object(),
            False,
        )


class TransformationRecordRegressionTests(unittest.TestCase):
    def test_composition_result_reports_known_sources_and_is_immutable(
        self,
    ) -> None:
        result = CompositionResult(
            mappings=(
                TransformationMapping(
                    source_entity=A,
                    destination_entities=(B,),
                ),
            ),
            unknown_sources=frozenset({C}),
        )

        self.assertEqual(
            result.known_sources,
            frozenset({A}),
        )

        with self.assertRaises(FrozenInstanceError):
            result.unknown_sources = frozenset()

    def test_relation_rewrite_is_immutable(self) -> None:
        rewrite = RelationRewrite(
            RELATION,
            ((A, B),),
        )

        with self.assertRaises(FrozenInstanceError):
            rewrite.endpoints = ((A, C),)

    def test_transform_result_rejects_rewrite_missing_from_destination(
        self,
    ) -> None:
        source = State.create({
            RELATION: Value.create(
                RELATION,
                Relation("metadata", {}),
            ),
        })
        destination = State.create({})
        rewrite = RelationRewrite(
            RELATION,
            ((A, B),),
        )

        with self.assertRaises(ValueError):
            TransformResult(
                source=source,
                destination=destination,
                mappings=(),
                relation_rewrites=(rewrite,),
            )


if __name__ == "__main__":
    unittest.main()
