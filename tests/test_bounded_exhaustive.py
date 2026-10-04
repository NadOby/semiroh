"""Bounded exhaustive verification over tiny semantic domains."""

from __future__ import annotations

from itertools import product
import unittest

from shear import EntityID, TransformationDefinition, compose


A = EntityID("a")
B = EntityID("b")
UNIVERSE = (A, B)

# Every possible mapping state for one source over a two-entity universe:
# absent, known disappearance, either singleton, or the complete split.
OPTIONS = (
    None,
    (),
    (A,),
    (B,),
    (A, B),
)


RawRelation = dict[EntityID, tuple[EntityID, ...]]
RelationCase = tuple[RawRelation, TransformationDefinition]


def explicit(definition: TransformationDefinition) -> RawRelation:
    return {
        mapping.source_entity: mapping.destination_entities
        for mapping in definition.mappings
    }


def relation_key(
    relation: RawRelation,
) -> tuple[tuple[EntityID, tuple[EntityID, ...] | None], ...]:
    """Preserve the distinction between absent and explicit disappearance."""

    return tuple(
        (
            source,
            relation.get(source),
        )
        for source in UNIVERSE
    )


def relations() -> tuple[RelationCase, ...]:
    out = []

    for choices in product(OPTIONS, repeat=len(UNIVERSE)):
        raw = {
            source: destinations
            for source, destinations in zip(UNIVERSE, choices)
            if destinations is not None
        }
        definition = TransformationDefinition.create(
            mappings=raw,
        )
        out.append((
            raw,
            definition,
        ))

    return tuple(out)


RELATIONS = relations()


def expected(
    first_relation: RawRelation,
    second_relation: RawRelation,
    source: EntityID,
) -> tuple[str, tuple[EntityID, ...]]:
    """Independent relational oracle for two-step explicit continuity."""

    if source not in first_relation:
        return ("absent", ())

    intermediate = first_relation[source]

    if not intermediate:
        return ("known", ())

    destinations = set()

    for entity in intermediate:
        if entity not in second_relation:
            return ("unknown", ())

        destinations.update(second_relation[entity])

    return ("known", tuple(sorted(destinations)))


def actual(result, source: EntityID):
    mapping = result.mapping_for(source)

    if mapping is not None:
        return ("known", mapping.destination_entities)

    if source in result.unknown_sources:
        return ("unknown", ())

    return ("absent", ())


class BoundedExhaustiveCompositionTests(unittest.TestCase):
    def test_relation_domain_is_complete_and_preserved(self) -> None:
        raw_keys = set()
        constructed_keys = set()

        for raw, definition in RELATIONS:
            constructed = explicit(definition)

            self.assertEqual(
                constructed,
                raw,
                (
                    "TransformationDefinition.create changed the "
                    f"relation: raw={raw!r}, constructed={constructed!r}"
                ),
            )

            raw_keys.add(relation_key(raw))
            constructed_keys.add(relation_key(constructed))

        self.assertEqual(len(RELATIONS), 25)
        self.assertEqual(len(raw_keys), 25)
        self.assertEqual(len(constructed_keys), 25)

    def test_every_two_entity_relation_pair_matches_the_oracle(self) -> None:
        checked = 0

        for first_raw, first in RELATIONS:
            for second_raw, second in RELATIONS:
                result = compose(first, second)

                for source in UNIVERSE:
                    wanted = expected(
                        first_raw,
                        second_raw,
                        source,
                    )
                    observed = actual(result, source)

                    self.assertEqual(
                        observed,
                        wanted,
                        (
                            f"first={first_raw!r}\n"
                            f"second={second_raw!r}\n"
                            f"source={source!r}"
                        ),
                    )

                checked += 1

        self.assertEqual(checked, 25 * 25)


if __name__ == "__main__":
    unittest.main()
