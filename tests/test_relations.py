"""Tests for relations: records, integrity, index, and continuity."""

import unittest

from semiroh import (
    DanglingRelation,
    EntityID,
    Relation,
    State,
    Value,
    relation_index,
    relation_of,
    relations_of,
)

A = EntityID("a")
B = EntityID("b")
C = EntityID("c")
R = EntityID("r")
S = EntityID("s")


def graph(**entities: object) -> State:
    return State.create({
        EntityID(name): Value.create(EntityID(name), content)
        for name, content in entities.items()
    })


def edge(kind: str = "depends_on", **roles: object) -> Relation:
    return Relation(kind, roles)


class RelationRecordTests(unittest.TestCase):
    def test_role_order_does_not_affect_identity(self) -> None:
        self.assertEqual(
            Relation("call", {"caller": A, "callee": B}),
            Relation("call", {"callee": B, "caller": A}),
        )

    def test_order_within_a_role_matters(self) -> None:
        self.assertNotEqual(
            Relation("call", {"args": (A, B)}),
            Relation("call", {"args": (B, A)}),
        )

    def test_kind_and_payload_are_part_of_identity(self) -> None:
        base = Relation("uses", {"to": A}, payload=1)

        self.assertNotEqual(base, Relation("reads", {"to": A}, payload=1))
        self.assertNotEqual(base, Relation("uses", {"to": A}, payload=True))

    def test_sequences_are_normalized_to_tuples(self) -> None:
        self.assertEqual(
            Relation("call", {"args": [A, B]}).roles["args"],
            (A, B),
        )

    def test_invalid_records_are_rejected(self) -> None:
        for kind, roles in [
            ("", {"to": A}),
            ("r", {}),
            ("r", {"": A}),
            ("r", {"to": "a"}),
            ("r", {"to": (A, "b")}),
        ]:
            with self.subTest(kind=kind, roles=roles):
                with self.assertRaises(TypeError):
                    Relation(kind, roles)  # type: ignore[arg-type]

    def test_record_round_trips_through_a_value(self) -> None:
        record = Relation("call", {"callee": B, "args": (A, C)}, payload=[1])

        self.assertEqual(relation_of(Value.create(R, record)), record)

    def test_ordinary_values_are_not_relations(self) -> None:
        for content in (1, ("__type__", "relation", ("r", (), None)), {"to": A}):
            with self.subTest(content=content):
                self.assertIsNone(relation_of(Value.create(R, content)))

    def test_endpoints_cover_every_role(self) -> None:
        self.assertEqual(
            Relation("call", {"callee": B, "args": (A, C, A)}).endpoints,
            {A, B, C},
        )

    def test_with_endpoints_replaces_only_given_entities(self) -> None:
        record = Relation("call", {"callee": B, "args": (A, C)})

        self.assertEqual(
            record.with_endpoints({A: C}),
            Relation("call", {"callee": B, "args": (C, C)}),
        )


class RelationIntegrityTests(unittest.TestCase):
    def test_relation_between_present_entities_is_accepted(self) -> None:
        state = graph(a=1, b=2, r=edge(source=A, target=B))

        self.assertEqual(dict(relations_of(state)), {R: edge(source=A, target=B)})

    def test_dangling_endpoint_is_rejected(self) -> None:
        with self.assertRaises(DanglingRelation):
            graph(a=1, r=edge(source=A, target=B))

    def test_relations_may_relate_relations_and_form_cycles(self) -> None:
        state = graph(
            a=1,
            r=edge(source=A, target=S),
            s=edge(source=R, target=S),
        )

        self.assertEqual(set(relations_of(state)), {R, S})

    def test_destroy_fails_when_an_outside_relation_points_in(self) -> None:
        state = State.create(
            {
                A: Value.create(A, 1),
                B: Value.create(B, 2),
                R: Value.create(R, edge(source=A, target=B)),
            },
            {A: (B,)},
        )

        with self.assertRaises(DanglingRelation):
            state.destroy(A)

    def test_destroy_succeeds_when_the_relation_is_destroyed_too(self) -> None:
        state = State.create(
            {
                A: Value.create(A, 1),
                B: Value.create(B, 2),
                R: Value.create(R, edge(source=A, target=B)),
            },
            {A: (B, R)},
        )

        self.assertEqual(set(state.destroy(A).values), set())


class RelationIndexTests(unittest.TestCase):
    def test_index_lists_relation_and_role_per_entity(self) -> None:
        state = graph(
            a=1,
            b=2,
            r=edge(source=A, target=B),
            s=edge("call", args=(A, A), callee=R),
        )

        self.assertEqual(
            dict(relation_index(state)),
            {
                A: ((R, "source"), (S, "args")),
                B: ((R, "target"),),
                R: ((S, "callee"),),
            },
        )

    def test_index_is_not_part_of_state_identity(self) -> None:
        state = graph(a=1, r=edge(to=A))
        relation_index(state)

        self.assertEqual(
            state.id,
            graph(a=1, r=edge(to=A)).id,
        )


if __name__ == "__main__":
    unittest.main()
