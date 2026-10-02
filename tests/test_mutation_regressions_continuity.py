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
