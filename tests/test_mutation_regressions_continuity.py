"""Mutation regressions for continuity checking and rebase mapping."""

from __future__ import annotations

import unittest

from semiroh import (
    ActivationRejected,
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
    _restate,
    check,
    resolve,
)
from semiroh.lang import (
    Function,
    LanguageError,
    define,
    function_at,
    links,
    load,
)
from semiroh.relations import relation_of
from semiroh.syntax import parse
from semiroh.transforms import rebase


ENTITY = EntityID("entity")
OTHER = EntityID("other")
F = EntityID("f")
G = EntityID("g")


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


class LanguageDefineRegressionTests(unittest.TestCase):
    def test_label_edit_subtree_does_not_follow_call_target(self) -> None:
        links_entity = EntityID("f.links")
        state = load(
            State.create({
                F: Value.create(
                    F,
                    Function(
                        (),
                        (
                            "label",
                            "spot",
                            ("call", "g"),
                        ),
                    ),
                ),
                G: Value.create(
                    G,
                    Function(
                        (),
                        ("lit", 1),
                    ),
                ),
                links_entity: Value.create(
                    links_entity,
                    links(
                        F,
                        g=G,
                    ),
                ),
            })
        )

        destination = define(
            state,
            {
                (F, "spot"): ("lit", 2),
            },
        ).destination

        self.assertEqual(
            function_at(destination, F),
            Function(
                (),
                (
                    "label",
                    "spot",
                    ("lit", 2),
                ),
            ),
        )

    def test_simultaneous_node_edits_cannot_introduce_same_label(
        self,
    ) -> None:
        state = load(
            State.create({
                F: Value.create(
                    F,
                    Function(
                        (),
                        (
                            "add",
                            (
                                "label",
                                "left",
                                ("lit", 1),
                            ),
                            (
                                "label",
                                "right",
                                ("lit", 2),
                            ),
                        ),
                    ),
                ),
            })
        )

        with self.assertRaises(LanguageError):
            define(
                state,
                {
                    (F, "left"):
                        (
                            "label",
                            "new",
                            ("lit", 10),
                        ),
                    (F, "right"):
                        (
                            "label",
                            "new",
                            ("lit", 20),
                        ),
                },
            )

    def test_node_edit_may_introduce_unique_nested_label(self) -> None:
        state = load(
            State.create({
                F: Value.create(
                    F,
                    Function(
                        (),
                        (
                            "label",
                            "spot",
                            ("lit", 1),
                        ),
                    ),
                ),
            })
        )

        destination = define(
            state,
            {
                (F, "spot"): (
                    "add",
                    (
                        "label",
                        "fresh",
                        ("lit", 2),
                    ),
                    ("lit", 3),
                ),
            },
        ).destination

        self.assertEqual(
            function_at(destination, F),
            Function(
                (),
                (
                    "label",
                    "spot",
                    (
                        "add",
                        (
                            "label",
                            "fresh",
                            ("lit", 2),
                        ),
                        ("lit", 3),
                    ),
                ),
            ),
        )

    def test_simultaneous_function_edits_keep_their_own_bodies(
        self,
    ) -> None:
        state = load(
            State.create({
                F: Value.create(
                    F,
                    Function(
                        (),
                        ("lit", 1),
                    ),
                ),
                G: Value.create(
                    G,
                    Function(
                        (),
                        ("lit", 2),
                    ),
                ),
            })
        )
        replacement_f = Function(
            (),
            ("lit", 10),
        )
        replacement_g = Function(
            (),
            ("lit", 20),
        )

        destination = define(
            state,
            {
                F: replacement_f,
                G: replacement_g,
            },
        ).destination

        self.assertEqual(
            function_at(destination, F),
            replacement_f,
        )
        self.assertEqual(
            function_at(destination, G),
            replacement_g,
        )


class ContinuityOperationRegressionTests(unittest.TestCase):
    def test_restate_preserves_replacement_program_link_table(self) -> None:
        source = load(
            parse(
                "fn g():\n"
                "    1\n"
                "\n"
                "fn f():\n"
                "    0\n"
            )
        )
        operation = _restate(
            "fn g():\n"
            "    1\n"
            "\n"
            "fn f():\n"
            "    g()\n"
        )

        destination = operation(source).destination
        definition = relation_of(destination.values[F])

        self.assertIsNotNone(definition)
        assert definition is not None
        self.assertEqual(
            definition.roles["link:g"],
            G,
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

    @staticmethod
    def _disjoint_pair(state: State):
        return (
            define(
                state,
                {
                    G: Function(
                        (),
                        ("lit", 3),
                    ),
                },
            ),
            define(
                state,
                {
                    F: Function(
                        ("x",),
                        ("lit", 0),
                    ),
                },
            ),
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

    def test_expected_activation_exception_is_accepted(self) -> None:
        result = self._foreign_result()

        case = Case(
            name="expected-activation-exception",
            group="inferred",
            source="fn f():\n    1\n",
            operation=lambda _: result,
            expect=Expect(rejected=ActivationRejected),
            status="probe",
            note="mutation regression",
        )

        self.assertEqual(
            check(case),
            (),
        )

    def test_invalid_at_merge_and_split_targets_are_mismatches(
        self,
    ) -> None:
        def identity(state: State):
            return transform_with_mapping(
                state,
                {},
                {
                    entity: entity
                    for entity in state.values
                },
            )

        case = Case(
            name="invalid-structural-designators",
            group="inferred",
            source="fn f():\n    1\n",
            operation=identity,
            expect=Expect(
                at={
                    "node:f@": "after:f@9",
                },
                merged={
                    "fn:f": "after:f@9",
                },
                split={
                    "fn:f": (
                        "fn:f",
                        "after:f@9",
                    ),
                },
            ),
            status="probe",
            note="mutation regression",
        )

        problems = check(case)

        self.assertEqual(
            len(problems),
            3,
        )
        self.assertTrue(
            all(
                "after:f@9" in problem
                for problem in problems
            )
        )

    def test_competing_checker_uses_nonidentity_mapping_record(
        self,
    ) -> None:
        case = Case(
            name="competing-mapping-record",
            group="competing",
            source=(
                "fn f(x):\n"
                "    x + 1\n"
                "\n"
                "fn g():\n"
                "    2\n"
            ),
            operation=self._disjoint_pair,
            expect=Expect(
                gone=(
                    "node:f@",
                ),
                merged={
                    "fn:g": "fn:g",
                },
            ),
            status="probe",
            note="mutation regression",
        )

        self.assertEqual(
            check(case),
            (),
        )

    def test_competing_checker_checks_cell_expectations(self) -> None:
        case = Case(
            name="competing-cell-check",
            group="competing",
            source=(
                "cell c: int = 0\n"
                "\n"
                "fn f(x):\n"
                "    x + 1\n"
                "\n"
                "fn g():\n"
                "    2\n"
            ),
            operation=self._disjoint_pair,
            expect=Expect(
                cells={
                    "cell:c": 0,
                },
            ),
            status="probe",
            note="mutation regression",
            writes={
                "cell:c": 5,
            },
        )

        problems = check(case)

        self.assertEqual(
            len(problems),
            2,
        )
        self.assertTrue(
            all(
                "cells cell:c" in problem
                and "holds 5" in problem
                for problem in problems
            )
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
