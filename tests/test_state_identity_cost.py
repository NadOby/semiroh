"""Acceptance tests for cheap state identity (docs/state_model.md section 4).

StateID must stay a function of exact semantic content, while deriving it
must not re-serialize content a transformation leaves unchanged.
"""

import random
import time
import unittest

from shear import EntityID, State, Value, transform_with_mapping


def random_content(rng: random.Random) -> object:
    choice = rng.randrange(5)

    if choice == 0:
        return rng.randint(-3, 3)

    if choice == 1:
        return rng.choice((True, False, None))

    if choice == 2:
        return rng.choice(("a", "b", ""))

    if choice == 3:
        return tuple(rng.randint(0, 2) for _ in range(rng.randrange(3)))

    return {rng.choice(("k", "l")): rng.randint(0, 2)}


def random_state_content(rng: random.Random) -> tuple[dict, dict]:
    entities = [EntityID(f"e{i}") for i in range(rng.randint(1, 6))]
    values = {entity: random_content(rng) for entity in entities}
    ownership = {}

    if len(entities) > 1 and rng.random() < 0.5:
        ownership = {entities[0]: tuple(entities[1:rng.randint(2, len(entities))])}

    return values, ownership


def other(content: object) -> object:
    """Different content; for bools and 0/1, what Python equality confuses."""

    if isinstance(content, bool):
        return int(content)

    if isinstance(content, int) and content in (0, 1):
        return bool(content)

    return "changed"


def build(values: dict, ownership: dict, order: list | None = None) -> State:
    order = order if order is not None else list(values)

    return State.create(
        {entity: Value.create(entity, values[entity]) for entity in order},
        ownership,
    )


class StateIdentityProperties(unittest.TestCase):
    def test_identity_follows_exact_content(self) -> None:
        for seed in range(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                values, ownership = random_state_content(rng)
                state = build(values, ownership)

                # Construction order and history do not matter.
                shuffled = list(values)
                rng.shuffle(shuffled)
                self.assertEqual(build(values, ownership, shuffled).id, state.id)

                entity = rng.choice(list(values))
                via_transform = transform_with_mapping(
                    build({**values, entity: "changed"}, ownership),
                    {entity: values[entity]},
                    {e: e for e in values},
                ).destination
                self.assertEqual(via_transform.id, state.id)

                # Any change of a value is a different state, including
                # changes Python equality cannot see (True == 1).
                changed = build({**values, entity: other(values[entity])}, ownership)
                self.assertNotEqual(changed.id, state.id)

    def test_identity_binds_content_to_its_entity(self) -> None:
        a = EntityID("a")
        b = EntityID("b")

        self.assertNotEqual(
            build({a: 1, b: 2}, {}).id,
            build({a: 2, b: 1}, {}).id,
        )

    def test_identity_includes_ownership(self) -> None:
        a = EntityID("a")
        b = EntityID("b")

        self.assertNotEqual(
            build({a: 1, b: 2}, {a: (b,)}).id,
            build({a: 1, b: 2}, {}).id,
        )


class StateIdentityCostTests(unittest.TestCase):
    def transform_time(self, content_size: int) -> float:
        entities = [EntityID(f"e{i}") for i in range(1000)]
        state = State.create({
            entity: Value.create(entity, tuple(range(content_size)))
            for entity in entities
        })
        mappings = {entity: entity for entity in entities}
        best = float("inf")

        for _ in range(3):
            start = time.perf_counter()

            for step in range(3):
                state = transform_with_mapping(
                    state,
                    {entities[0]: (step,)},
                    mappings,
                ).destination

            best = min(best, time.perf_counter() - start)

        return best

    def test_cost_does_not_depend_on_unchanged_content(self) -> None:
        small = self.transform_time(1)
        large = self.transform_time(300)

        # Re-serializing every entity makes the large case several times
        # slower; deriving identity from kept VersionIDs does not.
        self.assertLess(large / small, 2.5)


if __name__ == "__main__":
    unittest.main()
