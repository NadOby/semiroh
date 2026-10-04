"""Tests for relations: records, integrity, index, and continuity."""

import random
import time
import unittest

from shear import (
    DanglingRelation,
    EntityID,
    MissingEntityMapping,
    Relation,
    RelationRewrite,
    State,
    TransformResult,
    TransformationDefinition,
    Value,
    transfer_reference,
    transform_with_mapping,
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
            ("r", [("to", A)]),
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

    def test_a_relation_may_have_no_roles(self) -> None:
        # A nullary relation, such as a literal leaf of code in graph form:
        # it relates nothing, so nothing can dangle and nothing indexes it.
        record = Relation("lit", {}, payload=1)
        state = graph(a=1, r=record)

        self.assertEqual(record.endpoints, frozenset())
        self.assertEqual(relation_of(state.values[R]), record)
        self.assertEqual(dict(relations_of(state)), {R: record})
        self.assertEqual(dict(relation_index(state)), {})
        self.assertNotEqual(record, Relation("lit", {}, payload=2))
        self.assertNotEqual(record, Relation("arg", {}, payload=1))

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

    def test_integrity_check_is_linear_in_the_number_of_relations(self) -> None:
        def build_time(count: int) -> float:
            values = {A: Value.create(A, 1)}

            for index in range(count):
                entity = EntityID(f"r{index}")
                values[entity] = Value.create(entity, edge(to=A))

            best = float("inf")

            for _ in range(3):
                start = time.perf_counter()
                State.create(values)
                best = min(best, time.perf_counter() - start)

            return best

        small = build_time(300)
        large = build_time(1200)

        # Four times the relations: about four times the work. Checking
        # each relation against every entity of the state is quadratic and
        # makes it about sixteen times.
        self.assertLess(large / small, 8)


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


def relation_at(state: State, entity: EntityID) -> Relation:
    record = relation_of(state.values[entity])
    assert record is not None
    return record


class RelationContinuityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = graph(a=1, b=2, r=edge(source=A, target=B))

    def test_rename_rewrites_the_endpoint(self) -> None:
        result = transform_with_mapping(self.state, {C: 3}, {A: C})

        self.assertEqual(
            relation_at(result.destination, R),
            edge(source=C, target=B),
        )

    def test_merge_rewrites_every_merged_endpoint(self) -> None:
        result = transform_with_mapping(self.state, {C: 3}, {A: C, B: C})

        self.assertEqual(
            relation_at(result.destination, R),
            edge(source=C, target=C),
        )

    def test_swap_and_shift_follow_mapped_endpoints(self) -> None:
        swapped = transform_with_mapping(self.state, {}, {A: B, B: A})
        shifted = transform_with_mapping(self.state, {C: 3}, {A: B, B: C})

        self.assertEqual(
            relation_at(swapped.destination, R),
            edge(source=B, target=A),
        )
        self.assertEqual(
            relation_at(shifted.destination, R),
            edge(source=B, target=C),
        )

    def test_unmapped_endpoints_are_unchanged(self) -> None:
        result = transform_with_mapping(self.state, {C: 3}, {B: C})

        self.assertEqual(
            relation_at(result.destination, R),
            edge(source=A, target=C),
        )

    def test_disappearing_endpoint_is_rejected(self) -> None:
        with self.assertRaises(DanglingRelation):
            transform_with_mapping(self.state, {}, {A: ()})

    def test_split_endpoint_is_rejected(self) -> None:
        with self.assertRaises(DanglingRelation):
            transform_with_mapping(self.state, {C: 3}, {A: (A, C)})

    def test_explicit_change_of_the_relation_wins(self) -> None:
        result = transform_with_mapping(
            self.state,
            {R: edge(source=B, target=B)},
            {A: ()},
        )

        self.assertEqual(
            relation_at(result.destination, R),
            edge(source=B, target=B),
        )

    def test_explicit_removal_of_the_relation_is_accepted(self) -> None:
        result = transform_with_mapping(self.state, {}, {A: (), R: ()})

        self.assertFalse(result.destination.contains(R))

    def test_explicit_change_must_not_dangle(self) -> None:
        with self.assertRaises(DanglingRelation):
            transform_with_mapping(
                self.state,
                {R: edge(source=A, target=C)},
                {},
            )

    def test_following_does_not_declare_the_relations_own_continuity(
        self,
    ) -> None:
        reference = self.state.reference(R)
        unmapped = transform_with_mapping(self.state, {C: 3}, {A: C})

        with self.assertRaises(MissingEntityMapping):
            transfer_reference(reference, unmapped)

        mapped = transform_with_mapping(self.state, {C: 3}, {A: C, R: R})
        transferred = transfer_reference(reference, mapped)

        self.assertEqual(transferred.entity, R)
        self.assertNotEqual(transferred.version, reference.version)

    def test_relations_about_relations_follow_renamed_relations(self) -> None:
        state = graph(
            a=1,
            b=2,
            r=edge(source=A, target=B),
            s=edge("about", subject=R),
        )

        result = transform_with_mapping(
            state,
            {C: edge(source=A, target=B)},
            {R: C},
        )

        self.assertEqual(
            relation_at(result.destination, S),
            edge("about", subject=C),
        )


class RelationRewriteRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = graph(a=1, b=2, r=edge(source=A, target=B))

    def test_rename_is_recorded(self) -> None:
        result = transform_with_mapping(self.state, {C: 3}, {A: C})

        self.assertEqual(
            result.relation_rewrites,
            (RelationRewrite(R, ((A, C),)),),
        )

    def test_swap_records_both_endpoints(self) -> None:
        result = transform_with_mapping(self.state, {}, {A: B, B: A})

        self.assertEqual(
            result.relation_rewrites,
            (RelationRewrite(R, ((A, B), (B, A))),),
        )

    def test_unrewritten_relations_are_not_recorded(self) -> None:
        identity = transform_with_mapping(self.state, {}, {A: A, B: B})
        explicit = transform_with_mapping(
            self.state,
            {C: 3, R: edge(source=C, target=B)},
            {A: C},
        )

        self.assertEqual(identity.relation_rewrites, ())
        self.assertEqual(explicit.relation_rewrites, ())

    def test_record_must_match_the_states(self) -> None:
        result = transform_with_mapping(self.state, {C: 3}, {A: C})

        with self.assertRaises(ValueError):
            TransformResult(
                source=result.source,
                destination=result.destination,
                mappings=result.mappings,
                relation_rewrites=(RelationRewrite(R, ((B, C),)),),
            )

    def test_invalid_rewrite_records_are_rejected(self) -> None:
        for endpoints in [(), ((A, A),), ((B, C), (A, C)), ((A, B), (A, C))]:
            with self.subTest(endpoints=endpoints):
                with self.assertRaises(ValueError):
                    RelationRewrite(R, endpoints)


class RelationContinuityProperties(unittest.TestCase):
    def test_apply_follows_mapped_endpoints_or_rejects(self) -> None:
        plain = [EntityID(f"e{index}") for index in range(4)]
        relations = [EntityID(f"r{index}") for index in range(3)]
        created = [EntityID(f"n{index}") for index in range(2)]
        outcomes = {"applied": 0, "dangling": 0}

        for seed in range(500):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                values = {entity: Value.create(entity, 0) for entity in plain}

                for index, entity in enumerate(relations):
                    targets = plain + relations[:index]
                    values[entity] = Value.create(
                        entity,
                        edge(
                            source=rng.choice(targets),
                            target=rng.choice(targets),
                        ),
                    )

                state = State.create(values)
                sources = sorted(values)

                changes = {entity: 0 for entity in created}

                for entity in relations:
                    if rng.random() < 0.15:
                        changes[entity] = edge(
                            source=rng.choice(plain + created),
                            target=rng.choice(plain + created),
                        )

                mappings = {}

                for entity in sources:
                    roll = rng.random()

                    if roll < 0.55:
                        continue

                    if roll < 0.65:
                        mappings[entity] = ()
                    else:
                        mappings[entity] = tuple(
                            rng.sample(
                                sources + created,
                                rng.choice([1, 1, 1, 2]),
                            )
                        )

                disappearing = {
                    entity for entity, targets in mappings.items()
                    if not targets
                }
                targeted = {
                    target
                    for targets in mappings.values()
                    for target in targets
                }

                # A change to a relation the mappings remove is
                # contradictory; drop it.
                for entity in relations:
                    if entity in mappings and (
                        not mappings[entity] or entity not in targeted
                    ):
                        changes.pop(entity, None)
                destinations = {
                    target
                    for targets in mappings.values()
                    for target in targets
                }

                if destinations & disappearing:
                    continue  # rejected earlier as a missing destination

                present = {
                    entity for entity in sources
                    if entity not in disappearing
                    and (entity not in mappings or entity in destinations)
                } | set(created)

                expect_dangling = False

                for entity in relations:
                    if entity not in present:
                        continue

                    if entity in changes:
                        record = changes[entity]
                        if not record.endpoints <= present:
                            expect_dangling = True
                        continue

                    for endpoint in relation_at(state, entity).endpoints:
                        if endpoint in mappings and len(mappings[endpoint]) != 1:
                            expect_dangling = True

                definition = TransformationDefinition.create(
                    changes=changes,
                    mappings=mappings,
                )

                if expect_dangling:
                    with self.assertRaises(DanglingRelation):
                        definition.apply(state)
                    outcomes["dangling"] += 1
                    continue

                result = definition.apply(state)
                destination = result.destination
                outcomes["applied"] += 1
                expected_rewrites = []

                for entity in relations:
                    if entity not in present or entity in changes:
                        continue

                    old = relation_at(state, entity)
                    expected = old.with_endpoints({
                        endpoint: mappings[endpoint][0]
                        for endpoint in old.endpoints
                        if endpoint in mappings
                    })

                    self.assertEqual(relation_at(destination, entity), expected)

                    moved = tuple(
                        (endpoint, mappings[endpoint][0])
                        for endpoint in sorted(old.endpoints)
                        if endpoint in mappings
                        and mappings[endpoint][0] != endpoint
                    )

                    if moved:
                        expected_rewrites.append(RelationRewrite(entity, moved))

                self.assertEqual(
                    result.relation_rewrites,
                    tuple(expected_rewrites),
                )

        self.assertGreater(outcomes["applied"], 50)
        self.assertGreater(outcomes["dangling"], 50)


if __name__ == "__main__":
    unittest.main()
