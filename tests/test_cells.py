"""Tests for mutable cell declarations in program state."""

import unittest

from shear import (
    CellDeclaration,
    IntRange,
    IsKind,
    EntityID,
    State,
    Value,
    canonicalize,
    cell_declaration,
    cells_of,
)


class CellDeclarationTests(unittest.TestCase):
    def test_declaration_round_trips_through_a_value(self) -> None:
        counter = EntityID("counter")

        declaration = CellDeclaration(IsKind("int"), 0)
        value = Value.create(counter, declaration)

        self.assertEqual(cell_declaration(value), declaration)

    def test_initial_content_is_canonical(self) -> None:
        declaration = CellDeclaration(IsKind("list"), [1, 2])

        self.assertEqual(declaration.initial, canonicalize([1, 2]))

    def test_ordinary_values_are_not_cells(self) -> None:
        foo = EntityID("foo")

        for content in (
            1,
            "cell",
            ("__type__", "cell", ("int", 0)),
            {"type": "int", "initial": 0},
        ):
            with self.subTest(content=content):
                self.assertIsNone(
                    cell_declaration(Value.create(foo, content))
                )

    def test_cell_constraint_must_be_a_constraint(self) -> None:
        for constraint in ("int", 1, None):
            with self.subTest(constraint=constraint):
                with self.assertRaises(TypeError):
                    CellDeclaration(constraint, 0)  # type: ignore[arg-type]

    def test_declaration_equality_is_type_aware(self) -> None:
        self.assertNotEqual(
            CellDeclaration(IsKind("bool"), True),
            CellDeclaration(IsKind("bool"), 1),
        )

    def test_declaring_a_cell_does_not_check_its_initial_content(self) -> None:
        # Program state is pure data; a runtime checks content on load.
        counter = EntityID("counter")

        state = State.create({
            counter: Value.create(
                counter,
                CellDeclaration(IsKind("int"), "not an int"),
            ),
        })

        self.assertEqual(
            cells_of(state)[counter].initial,
            "not an int",
        )

    def test_declaration_is_part_of_state_identity(self) -> None:
        counter = EntityID("counter")

        def state_with(declaration: CellDeclaration) -> State:
            return State.create({
                counter: Value.create(counter, declaration),
            })

        base = state_with(CellDeclaration(IsKind("int"), 0))

        self.assertEqual(base.id, state_with(CellDeclaration(IsKind("int"), 0)).id)
        self.assertNotEqual(base.id, state_with(CellDeclaration(IntRange(0), 0)).id)
        self.assertNotEqual(base.id, state_with(CellDeclaration(IsKind("int"), 1)).id)

    def test_cells_of_lists_only_cells(self) -> None:
        counter = EntityID("counter")
        limit = EntityID("limit")
        name = EntityID("name")

        state = State.create({
            counter: Value.create(counter, CellDeclaration(IsKind("int"), 0)),
            limit: Value.create(limit, 10),
            name: Value.create(name, CellDeclaration(IsKind("str"), "")),
        })

        self.assertEqual(
            dict(cells_of(state)),
            {
                counter: CellDeclaration(IsKind("int"), 0),
                name: CellDeclaration(IsKind("str"), ""),
            },
        )


if __name__ == "__main__":
    unittest.main()
