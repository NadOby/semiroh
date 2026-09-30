"""Bounded exhaustive verification over tiny semantic domains."""

from __future__ import annotations

from itertools import product
import unittest

from semiroh import EntityID, TransformationDefinition, compose


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


def relations() -> tuple[TransformationDefinition, ...]:
    out = []

    for choices in product(OPTIONS, repeat=len(UNIVERSE)):
        mappings = {
            source: destinations
            for source, destinations in zip(UNIVERSE, choices)
            if destinations is not None
        }
        out.append(
            TransformationDefinition.create(mappings=mappings)
        )

    return tuple(out)


RELATIONS = relations()


def explicit(definition: TransformationDefinition):
    return {
        mapping.source_entity: mapping.destination_entities
        for mapping in definition.mappings
    }


def expected(
    first: TransformationDefinition,
    second: TransformationDefinition,
    source: EntityID,
) -> tuple[str, tuple[EntityID, ...]]:
    """Independent relational oracle for two-step explicit continuity."""

    first_relation = explicit(first)
    second_relation = explicit(second)

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
    def test_every_two_entity_relation_pair_matches_the_oracle(self) -> None:
        checked = 0

        for first in RELATIONS:
            for second in RELATIONS:
                result = compose(first, second)

                for source in UNIVERSE:
                    wanted = expected(first, second, source)
                    observed = actual(result, source)

                    self.assertEqual(
                        observed,
                        wanted,
                        (
                            f"first={explicit(first)!r}\n"
                            f"second={explicit(second)!r}\n"
                            f"source={source!r}"
                        ),
                    )

                checked += 1

        self.assertEqual(checked, 25 * 25)


if __name__ == "__main__":
    unittest.main()
