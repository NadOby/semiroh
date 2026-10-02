"""Mutation regressions for continuity checking and rebase mapping."""

from __future__ import annotations

import unittest

from semiroh import (
    EntityID,
    Relation,
    State,
    Value,
    transform_with_mapping,
)
from semiroh.continuity import (
    Case,
    DesignatorError,
    Expect,
    check,
    resolve,
)
from semiroh.lang import load
from semiroh.relations import relation_of
from semiroh.syntax import parse
from semiroh.transforms import rebase


ENTITY = EntityID("entity")
OTHER = EntityID("other")


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
