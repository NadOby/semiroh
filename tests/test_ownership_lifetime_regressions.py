"""Regression tests for gaps found while reviewing task/3-creation-and-lifetime.

These cover two combinations that the acceptance and property tests in
tests/test_ownership_lifetime.py and tests/test_properties.py do not
exercise directly: a placement targeting an entity that is present in the
source but left entirely unmapped (no explicit continuity at all, so it is
not caught by the mapping-destination check at construction time), and an
owned-subtree cascade (ownership_model.md section 7) occurring together
with an explicitly supplied destination ownership relation.
"""

import unittest

from shear import EntityID, OwnershipError, State, Value, transform_with_mapping

ROOT = EntityID("root")
CHILD = EntityID("child")
GRANDCHILD = EntityID("grandchild")
SIBLING = EntityID("sibling")


def tree() -> State:
    """root owns child, which owns grandchild; sibling is top-level."""

    return State.create(
        {
            entity: Value.create(entity, index)
            for index, entity in enumerate((ROOT, CHILD, GRANDCHILD, SIBLING))
        },
        {ROOT: (CHILD,), CHILD: (GRANDCHILD,)},
    )


class PlacementOfUnmappedSourceEntityTests(unittest.TestCase):
    def test_placement_of_an_entirely_unmapped_source_entity_is_rejected(
        self,
    ) -> None:
        # SIBLING is present in the source and named by nothing at all (not
        # a mapping source, not a mapping destination), so it implicitly
        # continues into the destination. A placement for it is a
        # reparenting of an existing entity, not a creation
        # (ownership_model.md section 10), and must be rejected even though
        # no mapping makes it a "mapping destination".
        state = tree()

        with self.assertRaises(OwnershipError):
            transform_with_mapping(state, {}, {}, placements={SIBLING: ROOT})


class CascadeWithExplicitOwnershipTests(unittest.TestCase):
    def test_cascade_removes_unnamed_descendants_even_with_explicit_ownership(
        self,
    ) -> None:
        # ROOT ends and CHILD/GRANDCHILD are unnamed, so they must cascade
        # away (ownership_model.md section 7) whether or not the caller also
        # supplies an explicit destination ownership relation.
        state = tree()

        result = transform_with_mapping(state, {}, {ROOT: ()}, ownership={})

        self.assertFalse(result.destination.contains(ROOT))
        self.assertFalse(result.destination.contains(CHILD))
        self.assertFalse(result.destination.contains(GRANDCHILD))
        self.assertTrue(result.destination.contains(SIBLING))


if __name__ == "__main__":
    unittest.main()
