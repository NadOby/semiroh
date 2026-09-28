"""Seeded randomized property tests for the semantic model.

These tests generate cases from fixed seeds with the standard library only,
so failures are reproducible (each case reports its seed) and the test suite
keeps no third-party dependencies.

Each property is derived from an explicit statement in the specification
documents; random generation only explores cases, it does not define rules.
"""

from __future__ import annotations

import random
import unittest
from typing import Any

from semiroh import (
    AmbiguousEntityMapping,
    CompositionResult,
    EntityID,
    MissingEntityMapping,
    OwnershipError,
    State,
    TransformationDefinition,
    Value,
    canonical_serialize,
    canonicalize,
    compose,
    same_version,
    semantic_equal,
    transfer_reference,
    transform_with_mapping,
)

CASES = 300


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def random_scalar(rng: random.Random) -> Any:
    choice = rng.randrange(7)

    if choice == 0:
        return None

    if choice == 1:
        return rng.choice([True, False])

    if choice == 2:
        # Include 0 and 1 so that bool/int collisions are exercised.
        return rng.choice([0, 1, -1, 2, 10**20])

    if choice == 3:
        return rng.choice(["", "a", "b", "__type__", "tuple"])

    if choice == 4:
        return rng.choice([b"", b"a", b"\x00"])

    if choice == 5:
        return EntityID(rng.choice(["x", "y"]))

    return rng.choice([0, 1, True, False])


def random_value(rng: random.Random, depth: int = 3) -> Any:
    if depth == 0 or rng.random() < 0.4:
        return random_scalar(rng)

    kind = rng.randrange(3)
    items = [random_value(rng, depth - 1) for _ in range(rng.randrange(4))]

    if kind == 0:
        return tuple(items)

    if kind == 1:
        return items

    mapping: dict[Any, Any] = {}

    for item in items:
        key = random_scalar(rng)
        mapping[key] = item

    return mapping


def typed(value: Any) -> Any:
    """Type-exact structural form, independent of container order."""

    if isinstance(value, dict):
        return (
            "dict",
            frozenset(
                (typed(key), typed(item))
                for key, item in value.items()
            ),
        )

    if isinstance(value, (tuple, list)):
        return (
            type(value).__name__,
            tuple(typed(item) for item in value),
        )

    return (type(value).__name__, value)


def shuffled_copy(rng: random.Random, value: Any) -> Any:
    """Rebuild a value with dictionaries in a different insertion order."""

    if isinstance(value, dict):
        items = list(value.items())
        rng.shuffle(items)
        return {key: shuffled_copy(rng, item) for key, item in items}

    if isinstance(value, tuple):
        return tuple(shuffled_copy(rng, item) for item in value)

    if isinstance(value, list):
        return [shuffled_copy(rng, item) for item in value]

    return value


def type_confused_copy(value: Any) -> Any:
    """Swap bools and the ints 0/1, which Python considers equal to them."""

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int) and value in (0, 1):
        return bool(value)

    if isinstance(value, dict):
        return {
            type_confused_copy(key): type_confused_copy(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return tuple(type_confused_copy(item) for item in value)

    if isinstance(value, list):
        return [type_confused_copy(item) for item in value]

    return value


def entity_names(count: int, prefix: str = "e") -> list[EntityID]:
    return [EntityID(f"{prefix}{index:02d}") for index in range(count)]


def random_state(rng: random.Random) -> State:
    entities = entity_names(rng.randrange(1, 7))

    values = {
        entity: Value(entity, rng.randrange(5))
        for entity in entities
    }

    # Assign each entity an owner among earlier entities, or none. This always
    # produces a forest.
    ownership: dict[EntityID, list[EntityID]] = {}

    for index, entity in enumerate(entities):
        if index and rng.random() < 0.4:
            owner = entities[rng.randrange(index)]
            ownership.setdefault(owner, []).append(entity)

    return State.create(values, ownership)


def random_definition(
    rng: random.Random,
    source_entities: list[EntityID],
    new_prefix: str,
) -> tuple[TransformationDefinition, set[EntityID]]:
    """Return a random definition and the set of entities it creates."""

    new_entities = entity_names(rng.randrange(4), prefix=new_prefix)

    # Occasionally leave a new entity uncreated so that invalid destinations
    # are also exercised.
    created = {
        entity
        for entity in new_entities
        if rng.random() < 0.9
    }

    changes: dict[EntityID, Any] = {
        entity: rng.randrange(5)
        for entity in source_entities
        if rng.random() < 0.3
    }
    changes.update({entity: rng.randrange(5) for entity in created})

    candidates = source_entities + new_entities
    mappings: dict[EntityID, tuple[EntityID, ...]] = {}

    for entity in source_entities:
        if rng.random() < 0.6:
            count = rng.choice([0, 1, 1, 1, 2, 3])
            count = min(count, len(candidates))
            mappings[entity] = tuple(rng.sample(candidates, count))

    # A change to an entity the mappings remove is contradictory and is
    # rejected; keep generated definitions valid.
    for entity in removed_by(mappings):
        changes.pop(entity, None)

    definition = TransformationDefinition.create(
        changes=changes,
        mappings=mappings,
    )

    return definition, created


def removed_by(
    mappings: dict[EntityID, tuple[EntityID, ...]],
) -> set[EntityID]:
    """Sources the mappings remove, computed independently of the model."""

    destinations = {
        destination
        for targets in mappings.values()
        for destination in targets
    }

    return {
        source
        for source, targets in mappings.items()
        if not targets or source not in destinations
    }


def cascaded_disappearances(
    ownership: Any,
    mappings: dict[EntityID, tuple[EntityID, ...]],
) -> set[EntityID]:
    """Entities that disappear because an ended owner's subtree ends with it.

    Computed independently from the source ownership and the definition's
    mappings, never by calling the implementation: ownership_model.md
    section 7 / transformation_model.md section 13 say every entity in a
    disappearing owner's owned subtree that the mappings do not name, as a
    source or a destination, disappears too, recursively, and the cascade
    does not descend past a named entity.
    """

    # Derived bottom-up, unlike the implementation's top-down walk, so the
    # two do not share a traversal: an unnamed entity ends when the nearest
    # ancestor that is either named or explicitly disappearing is the latter.
    named = set(mappings)

    for targets in mappings.values():
        named.update(targets)

    parent = {
        child: owner
        for owner, children in ownership.items()
        for child in children
    }
    cascaded: set[EntityID] = set()

    for entity in parent:
        if entity in named:
            continue

        ancestor = parent.get(entity)

        while ancestor is not None:
            if mappings.get(ancestor) == ():
                cascaded.add(entity)
                break

            if ancestor in named:
                break

            ancestor = parent.get(ancestor)

    return cascaded


def followed_ownership(
    ownership: Any,
    mappings: dict[EntityID, tuple[EntityID, ...]],
) -> dict[EntityID, tuple[EntityID, ...]] | None:
    """Expected ownership under declared continuity, or None if rejected.

    transformation_model.md §13: mapped endpoints follow their mapping; an
    edge whose child disappears goes; an owner that disappears or splits
    while its child remains, or a child that splits, is rejected; the result
    must be a forest. ownership_model.md §7: an entity that cascades away
    because its owner's subtree ended counts as disappearing here too, for
    both ends of an edge.
    """

    cascaded = cascaded_disappearances(ownership, mappings)
    effective = dict(mappings)

    for entity in cascaded:
        effective[entity] = ()

    parent: dict[EntityID, EntityID] = {}

    for owner, children in ownership.items():
        for child in children:
            child_targets = effective.get(child, (child,))

            if not child_targets:
                continue

            owner_targets = effective.get(owner, (owner,))

            if len(child_targets) != 1 or len(owner_targets) != 1:
                return None

            child_after, owner_after = child_targets[0], owner_targets[0]

            if child_after == owner_after:
                return None

            if parent.get(child_after, owner_after) != owner_after:
                return None

            parent[child_after] = owner_after

    for start in parent:
        seen = set()
        node: EntityID | None = start

        while node is not None:
            if node in seen:
                return None

            seen.add(node)
            node = parent.get(node)

    forest: dict[EntityID, list[EntityID]] = {}

    for child, owner in parent.items():
        forest.setdefault(owner, []).append(child)

    return {owner: tuple(sorted(children)) for owner, children in forest.items()}


def apply_stating_ownership(
    definition: TransformationDefinition,
    state: State,
) -> Any:
    """Apply, stating empty destination ownership if following rejects.

    For properties about continuity rather than ownership: a rejected
    implicit ownership change is replaced by an explicit one. A change to an
    entity that cascades away because its owner's subtree ended is dropped
    first (computed independently, as in `cascaded_disappearances`): these
    properties are about continuity, not about that change/disappearance
    contradiction, which `test_apply_follows_the_presence_and_validity_rules`
    already covers.
    """

    cascaded = cascaded_disappearances(
        state.ownership,
        {
            mapping.source_entity: mapping.destination_entities
            for mapping in definition.mappings
        },
    )

    if {change.entity for change in definition.changes} & cascaded:
        definition = TransformationDefinition(
            changes=tuple(
                change
                for change in definition.changes
                if change.entity not in cascaded
            ),
            mappings=definition.mappings,
            conversions=definition.conversions,
            placements=definition.placements,
        )

    try:
        return definition.apply(state)
    except OwnershipError:
        return definition.apply(state, ownership={})


def random_relation(
    rng: random.Random,
    universe: list[EntityID],
) -> TransformationDefinition:
    mappings = {
        entity: tuple(rng.sample(universe, rng.choice([0, 1, 1, 2])))
        for entity in universe
        if rng.random() < 0.7
    }

    return TransformationDefinition.create(mappings=mappings)


def composed_outcome(
    result: CompositionResult,
    entity: EntityID,
) -> tuple[str, tuple[EntityID, ...]]:
    mapping = result.mapping_for(entity)

    if mapping is not None:
        return ("known", mapping.destination_entities)

    if entity in result.unknown_sources:
        return ("unknown", ())

    return ("absent", ())


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


class CanonicalizationProperties(unittest.TestCase):
    def test_canonicalize_is_idempotent(self) -> None:
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                once = canonicalize(random_value(rng))

                self.assertEqual(canonicalize(once), once)
                self.assertEqual(
                    canonical_serialize(canonicalize(once)),
                    canonical_serialize(once),
                )

    def test_serialization_equality_matches_type_exact_equality(self) -> None:
        # identity_model.md §6: equivalent structures serialize identically;
        # canonical.py: distinct semantic types must not collapse.
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                left = random_value(rng)
                right = rng.choice(
                    [
                        random_value(rng),
                        shuffled_copy(rng, left),
                        type_confused_copy(left),
                    ]
                )

                self.assertEqual(
                    canonical_serialize(canonicalize(left))
                    == canonical_serialize(canonicalize(right)),
                    typed(left) == typed(right),
                )

    def test_value_equality_matches_version_identity(self) -> None:
        entity = EntityID("v")

        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                raw = random_value(rng)
                left = Value(entity, raw)
                right = Value(
                    entity,
                    rng.choice(
                        [
                            random_value(rng),
                            left.content,
                            type_confused_copy(raw),
                        ]
                    ),
                )

                self.assertEqual(left == right, same_version(left, right))
                self.assertEqual(
                    left == right,
                    semantic_equal(left, right),
                )

                if left == right:
                    self.assertEqual(hash(left), hash(right))


class OwnershipProperties(unittest.TestCase):
    def test_ownership_input_form_does_not_affect_state_identity(
        self,
    ) -> None:
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_state(rng)

                reshaped: dict[EntityID, list[EntityID]] = {
                    owner: list(reversed(children))
                    for owner, children in state.ownership.items()
                }

                # Add empty entries for some entities without children.
                for entity in state.values:
                    if entity not in reshaped and rng.random() < 0.5:
                        reshaped[entity] = []

                self.assertEqual(
                    State.create(state.values, reshaped).id,
                    state.id,
                )

    def test_closing_an_ownership_path_into_a_cycle_is_rejected(
        self,
    ) -> None:
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                entities = entity_names(rng.randrange(2, 30))

                # A single chain e0 -> e1 -> ... -> eN, closed back to e0.
                ownership = {
                    entities[index]: (entities[index + 1],)
                    for index in range(len(entities) - 1)
                }
                ownership[entities[-1]] = (entities[0],)

                with self.assertRaises(OwnershipError):
                    State.create(
                        {entity: Value(entity, 0) for entity in entities},
                        ownership,
                    )



def random_forest(rng: random.Random) -> State:
    """A state whose ownership is a random forest, often several levels deep."""

    entities = entity_names(rng.randrange(2, 12))
    ownership: dict[EntityID, list[EntityID]] = {}

    for index, entity in enumerate(entities[1:], start=1):
        if rng.random() < 0.8:
            ownership.setdefault(entities[rng.randrange(index)], []).append(entity)

    return State.create(
        {entity: Value(entity, index) for index, entity in enumerate(entities)},
        {owner: tuple(children) for owner, children in ownership.items()},
    )


class EndedSubtreeProperties(unittest.TestCase):
    """ownership_model.md section 7: an owner's disappearance ends its subtree."""

    def test_disappearance_matches_destruction(self) -> None:
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_forest(rng)
                ended = rng.choice(sorted(state.values))
                result = transform_with_mapping(state, {}, {ended: ()})
                destroyed = state.destroy(ended)

                self.assertEqual(result.destination.id, destroyed.id)

                for entity in set(state.values) - set(destroyed.values):
                    self.assertEqual(
                        result.mapping_for(entity).destination_entities, ()
                    )

    def test_named_entities_stop_the_cascade(self) -> None:
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_forest(rng)
                entities = sorted(state.values)
                ended = rng.choice(entities)
                kept = [
                    entity
                    for entity in entities
                    if entity != ended and rng.random() < 0.3
                ]
                mappings = {ended: (), **{entity: (entity,) for entity in kept}}
                expected_gone = {ended} | cascaded_disappearances(
                    state.ownership, mappings
                )

                result = transform_with_mapping(state, {}, mappings, ownership={})

                self.assertEqual(
                    set(result.destination.values),
                    set(entities) - expected_gone,
                )


class TransformationProperties(unittest.TestCase):
    def test_apply_follows_the_presence_and_validity_rules(self) -> None:
        # transformation_model.md §4, §6, §13; ownership_model.md §7.
        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_state(rng)
                sources = sorted(state.values)
                definition, created = random_definition(rng, sources, "n")

                disappearing = {
                    mapping.source_entity
                    for mapping in definition.mappings
                    if not mapping.destination_entities
                }
                destinations = {
                    entity
                    for mapping in definition.mappings
                    for entity in mapping.destination_entities
                }
                mapped = {
                    mapping.source_entity
                    for mapping in definition.mappings
                }
                declared = {
                    mapping.source_entity: mapping.destination_entities
                    for mapping in definition.mappings
                }
                cascaded = cascaded_disappearances(state.ownership, declared)
                available = set(sources) | created

                changed_cascaded = {
                    change.entity for change in definition.changes
                } & cascaded

                if changed_cascaded:
                    # A change to an entity that cascades away because its
                    # owner's subtree ended is rejected the same way as a
                    # change to an explicitly removed entity.
                    with self.assertRaises(ValueError):
                        definition.apply(state)
                    continue

                expected_valid = (
                    destinations <= available
                    and not destinations & disappearing
                )

                if not expected_valid:
                    with self.assertRaises(KeyError):
                        definition.apply(state)
                    continue

                expected_ownership = followed_ownership(
                    state.ownership,
                    declared,
                )

                if expected_ownership is None:
                    with self.assertRaises(OwnershipError):
                        definition.apply(state)
                    continue

                result = definition.apply(state)
                destination = result.destination
                changes = {
                    change.entity: change.value
                    for change in definition.changes
                }

                for entity in sources:
                    present = (
                        entity not in disappearing
                        and entity not in cascaded
                        and (entity not in mapped or entity in destinations)
                    )

                    self.assertEqual(destination.contains(entity), present)

                    if present:
                        self.assertEqual(
                            destination.values[entity],
                            changes.get(entity, state.values[entity]),
                        )

                for entity in created:
                    self.assertTrue(destination.contains(entity))

                # Ownership follows declared continuity (option B).
                self.assertEqual(
                    dict(destination.ownership),
                    expected_ownership,
                )

    def test_chained_reference_transfer_agrees_with_composition(
        self,
    ) -> None:
        # Composition of explicit continuity (transformation_composition.md)
        # must agree with following references one step at a time
        # (reference_model.md, transformation_model.md §9-10).
        checked = 0

        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                state = random_state(rng)

                first, _ = random_definition(rng, sorted(state.values), "n")

                try:
                    first_result = apply_stating_ownership(first, state)
                except KeyError:
                    continue

                second, _ = random_definition(
                    rng,
                    sorted(first_result.destination.values),
                    "m",
                )

                try:
                    second_result = apply_stating_ownership(
                        second,
                        first_result.destination,
                    )
                except KeyError:
                    continue

                composed = compose(first, second)

                for entity in state.values:
                    outcome, destinations = composed_outcome(
                        composed,
                        entity,
                    )

                    try:
                        middle = transfer_reference(
                            state.reference(entity),
                            first_result,
                        )
                        final = transfer_reference(middle, second_result)
                    except AmbiguousEntityMapping:
                        # A split along the path; composition may still be
                        # known (for example split-then-merge).
                        continue
                    except MissingEntityMapping:
                        # No continuation along a unique path: composition
                        # must not claim a known non-empty destination set.
                        self.assertTrue(
                            outcome in ("absent", "unknown")
                            or destinations == (),
                            f"{entity.value}: transfer failed but "
                            f"composition is {outcome} {destinations}",
                        )
                        continue

                    checked += 1

                    self.assertEqual(
                        (outcome, destinations),
                        ("known", (final.entity,)),
                    )

        self.assertGreater(checked, 50)

    def test_definition_changing_a_removed_entity_is_rejected(self) -> None:
        # transformation_model.md §4: a definition that changes an entity
        # and removes it through its mappings is contradictory.
        entities = entity_names(5)
        outcomes = {"accepted": 0, "rejected": 0}

        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                mappings = {
                    entity: tuple(rng.sample(entities, rng.choice([0, 1, 1, 2])))
                    for entity in entities
                    if rng.random() < 0.5
                }
                changes = {
                    entity: 0
                    for entity in entities
                    if rng.random() < 0.3
                }

                if set(changes) & removed_by(mappings):
                    outcomes["rejected"] += 1

                    with self.assertRaises(ValueError):
                        TransformationDefinition.create(
                            changes=changes,
                            mappings=mappings,
                        )
                else:
                    outcomes["accepted"] += 1
                    TransformationDefinition.create(
                        changes=changes,
                        mappings=mappings,
                    )

        self.assertGreater(outcomes["accepted"], 50)
        self.assertGreater(outcomes["rejected"], 50)

    def test_composition_is_associative(self) -> None:
        # transformation_composition.md §17.
        universe = entity_names(5)

        for seed in range(CASES):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                first = random_relation(rng, universe)
                second = random_relation(rng, universe)
                third = random_relation(rng, universe)

                self.assertEqual(
                    compose(compose(first, second), third),
                    compose(first, compose(second, third)),
                )


if __name__ == "__main__":
    unittest.main()
