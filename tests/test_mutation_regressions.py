"""Permanent regressions for semantic gaps found by mutation testing."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from semiroh import (
    AllOf,
    AnyOf,
    CellDeclaration,
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
    transform_with_mapping,
)
from semiroh.canonical import CanonicalNode
from semiroh.cells import cell_declaration
from semiroh.closures import Closure, closure_value
from semiroh.continuity import (
    Case,
    DesignatorError,
    Expect,
    check,
    resolve,
)
from semiroh.examples._support import program
from semiroh.lang import Function, links, load
from semiroh.relations import relation_of
from semiroh.syntax import SourceError, parse, render
from semiroh.transforms import (
    EntityChange,
    TransformationMapping,
    rebase,
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


class SyntaxLiteralRegressionTests(unittest.TestCase):
    def test_false_data_literal_remains_false(self) -> None:
        state = parse(
            "cell flag: bool = false\n"
        )
        declaration = cell_declaration(
            state.values[EntityID("flag")]
        )

        self.assertIsNotNone(declaration)
        assert declaration is not None
        self.assertIs(
            declaration.initial,
            False,
        )


class SyntaxParserRegressionTests(unittest.TestCase):
    def test_incomplete_expression_raises_source_error(self) -> None:
        with self.assertRaises(SourceError):
            parse(
                "fn f():\n"
                "    1 +\n"
            )


class SyntaxRenderingRegressionTests(unittest.TestCase):
    def test_raw_trial_target_uses_current_entity_name(self) -> None:
        function = EntityID("f")
        target = EntityID("target")

        state = load(program({
            target: Function(
                (),
                ("lit", 0),
            ),
            function: Function(
                (),
                (
                    "trial",
                    ("lit", 0),
                    "alias",
                    ("lit", 1),
                ),
            ),
            EntityID("f.links"): links(
                function,
                alias=target,
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f():\n"
            '    raw(("trial", ("lit", 0), "target", ("lit", 1)))\n',
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


class ContinuityDesignatorRegressionTests(unittest.TestCase):
    def test_path_through_non_node_raises_designator_error(self) -> None:
        state = load(
            parse(
                "cell c: int = 0\n"
                "\n"
                "fn f(x):\n"
                "    x + 1\n"
            )
        )

        root = resolve("node:f@", state)
        node = relation_of(state.values[root])
        self.assertIsNotNone(node)
        assert node is not None

        roles = dict(node.roles)
        roles["left"] = EntityID("c")

        values = dict(state.values)
        values[root] = Value.create(
            root,
            Relation(
                node.kind,
                roles,
                node.payload,
            ),
        )
        malformed = State.create(
            values,
            state.ownership,
        )

        with self.assertRaises(DesignatorError):
            resolve(
                "node:f@0.0",
                malformed,
            )


class ContinuityCheckerRegressionTests(unittest.TestCase):
    @staticmethod
    def _foreign_result():
        foreign = State.create({})
        return transform_with_mapping(
            foreign,
            {},
            {},
        )

    def test_wrong_activation_exception_is_a_mismatch(self) -> None:
        result = self._foreign_result()

        case = Case(
            name="wrong-activation-exception",
            group="inferred",
            source="fn f():\n    1\n",
            operation=lambda _: result,
            expect=Expect(rejected=KeyError),
            status="probe",
            note="mutation regression",
        )

        problems = check(case)

        self.assertEqual(len(problems), 1)
        self.assertIn(
            "ActivationRejected",
            problems[0],
        )

    def test_unexpected_activation_exception_is_a_mismatch(self) -> None:
        result = self._foreign_result()

        case = Case(
            name="unexpected-activation-exception",
            group="inferred",
            source="fn f():\n    1\n",
            operation=lambda _: result,
            expect=Expect(),
            status="probe",
            note="mutation regression",
        )

        problems = check(case)

        self.assertEqual(len(problems), 1)
        self.assertIn(
            "ActivationRejected",
            problems[0],
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
