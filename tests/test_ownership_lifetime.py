"""Acceptance tests for creation placement and disappearance of owned
subtrees (ownership_model.md sections 7 and 10, transformation_model.md
section 13).
"""

import unittest

from shear import (
    CellDeclaration,
    DanglingRelation,
    EntityID,
    IntRange,
    OwnershipError,
    Relation,
    Runtime,
    State,
    Value,
    transform_with_mapping,
)

ROOT = EntityID("root")
CHILD = EntityID("child")
GRANDCHILD = EntityID("grandchild")
SIBLING = EntityID("sibling")
NEW = EntityID("new")
NEWER = EntityID("newer")


def tree(extra: dict | None = None, ownership: dict | None = None) -> State:
    """root owns child, which owns grandchild; sibling is top-level."""

    values = {ROOT: 0, CHILD: 1, GRANDCHILD: 2, SIBLING: 3, **(extra or {})}

    return State.create(
        {entity: Value.create(entity, content) for entity, content in values.items()},
        ownership if ownership is not None else {ROOT: (CHILD,), CHILD: (GRANDCHILD,)},
    )


def identity(state: State, *except_for: EntityID) -> dict:
    return {entity: entity for entity in state.values if entity not in except_for}


class PlacementTests(unittest.TestCase):
    def test_created_entity_is_placed_under_its_owner(self) -> None:
        state = tree()
        result = transform_with_mapping(
            state, {NEW: 9}, identity(state), placements={NEW: ROOT}
        )

        self.assertEqual(result.destination.owner_of(NEW), ROOT)
        self.assertEqual(result.destination.ownership[ROOT], (CHILD, NEW))

    def test_created_entities_can_form_a_subtree(self) -> None:
        state = tree()
        result = transform_with_mapping(
            state,
            {NEW: 9, NEWER: 10},
            identity(state),
            placements={NEWER: NEW, NEW: SIBLING},
        )

        self.assertEqual(result.destination.owner_of(NEW), SIBLING)
        self.assertEqual(result.destination.owner_of(NEWER), NEW)

    def test_created_entity_without_placement_is_top_level(self) -> None:
        state = tree()
        result = transform_with_mapping(state, {NEW: 9}, identity(state))

        self.assertIsNone(result.destination.owner_of(NEW))

    def test_invalid_placements_are_rejected(self) -> None:
        state = tree()

        for changes, mappings, placements in (
            ({}, identity(state), {SIBLING: ROOT}),  # not created: a reparenting
            ({NEW: 9}, identity(state), {NEW: EntityID("absent")}),
            ({NEW: 9}, {**identity(state, SIBLING), SIBLING: NEW}, {NEW: ROOT}),  # continues sibling
            ({NEW: 9, NEWER: 10}, identity(state), {NEW: NEWER, NEWER: NEW}),  # cycle
            ({NEW: 9}, {**identity(state, ROOT), ROOT: ()}, {NEW: ROOT}),  # owner disappears
        ):
            with self.subTest(placements=placements, mappings=mappings):
                with self.assertRaises(OwnershipError):
                    transform_with_mapping(state, changes, mappings, placements=placements)

    def test_placements_and_explicit_ownership_are_exclusive(self) -> None:
        state = tree()

        with self.assertRaises(ValueError):
            transform_with_mapping(
                state,
                {NEW: 9},
                identity(state),
                ownership={ROOT: (NEW,)},
                placements={NEW: ROOT},
            )


class DisappearanceTests(unittest.TestCase):
    def test_owner_disappearance_ends_its_subtree(self) -> None:
        state = tree()
        result = transform_with_mapping(state, {}, {ROOT: ()})

        for entity in (ROOT, CHILD, GRANDCHILD):
            with self.subTest(entity=entity):
                self.assertFalse(result.destination.contains(entity))
                self.assertEqual(result.mapping_for(entity).destination_entities, ())

        self.assertTrue(result.destination.contains(SIBLING))
        self.assertEqual(dict(result.destination.ownership), {})

    def test_disappearance_matches_destruction(self) -> None:
        state = tree()

        self.assertEqual(
            transform_with_mapping(state, {}, {ROOT: ()}).destination.id,
            state.destroy(ROOT).id,
        )

    def test_named_descendant_keeps_what_its_mapping_says(self) -> None:
        state = tree()

        # Kept, so its owner changes: that must be explicit.
        with self.assertRaises(OwnershipError):
            transform_with_mapping(state, {}, {ROOT: (), CHILD: CHILD})

        result = transform_with_mapping(
            state, {}, {ROOT: (), CHILD: CHILD}, ownership={CHILD: (GRANDCHILD,)}
        )

        self.assertFalse(result.destination.contains(ROOT))
        self.assertIsNone(result.destination.owner_of(CHILD))
        self.assertEqual(result.destination.owner_of(GRANDCHILD), CHILD)

    def test_changing_an_ended_entity_is_rejected(self) -> None:
        state = tree()

        with self.assertRaises(ValueError):
            transform_with_mapping(state, {GRANDCHILD: 5}, {ROOT: ()})

    def test_relation_into_an_ended_subtree_is_rejected(self) -> None:
        pointer = EntityID("pointer")
        inner = EntityID("inner")
        state = State.create(
            {
                **{entity: Value.create(entity, 0) for entity in (ROOT, CHILD, SIBLING)},
                inner: Value.create(inner, Relation("points", {"target": CHILD})),
                pointer: Value.create(pointer, Relation("points", {"target": CHILD})),
            },
            {ROOT: (CHILD, inner)},
        )

        # A relation inside the subtree ends with it; one outside dangles.
        with self.assertRaises(DanglingRelation):
            transform_with_mapping(state, {}, {ROOT: ()})

        result = transform_with_mapping(state, {}, {ROOT: (), pointer: ()})

        self.assertFalse(result.destination.contains(inner))

    def test_activation_discards_cells_of_an_ended_subtree(self) -> None:
        owner = EntityID("module")
        owned_cell = EntityID("owned_cell")
        free_cell = EntityID("free_cell")
        state = State.create(
            {
                owner: Value.create(owner, 0),
                owned_cell: Value.create(owned_cell, CellDeclaration(IntRange(0, 9), 3)),
                free_cell: Value.create(free_cell, CellDeclaration(IntRange(0, 9), 4)),
            },
            {owner: (owned_cell,)},
        )
        runtime = Runtime(state)
        runtime.write(free_cell, 7)

        runtime.activate(
            transform_with_mapping(state, {}, {owner: (), free_cell: free_cell})
        )

        self.assertFalse(runtime.active.state.contains(owned_cell))
        self.assertEqual(runtime.read(free_cell), 7)


if __name__ == "__main__":
    unittest.main()
