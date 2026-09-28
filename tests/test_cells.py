"""Tests for mutable cell declarations in program state."""

import unittest

from semiroh import (
    CellDeclaration,
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

        declaration = CellDeclaration("int", 0)
        value = Value.create(counter, declaration)

        self.assertEqual(cell_declaration(value), declaration)

    def test_initial_content_is_canonical(self) -> None:
        declaration = CellDeclaration("list", [1, 2])

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

    def test_cell_type_must_be_a_non_empty_string(self) -> None:
        for cell_type in ("", 1, None):
            with self.subTest(cell_type=cell_type):
                with self.assertRaises(TypeError):
                    CellDeclaration(cell_type, 0)  # type: ignore[arg-type]

    def test_declaration_is_part_of_state_identity(self) -> None:
        counter = EntityID("counter")

        def state_with(declaration: CellDeclaration) -> State:
            return State.create({
                counter: Value.create(counter, declaration),
            })

        base = state_with(CellDeclaration("int", 0))

        self.assertEqual(base.id, state_with(CellDeclaration("int", 0)).id)
        self.assertNotEqual(base.id, state_with(CellDeclaration("i64", 0)).id)
        self.assertNotEqual(base.id, state_with(CellDeclaration("int", 1)).id)

    def test_cells_of_lists_only_cells(self) -> None:
        counter = EntityID("counter")
        limit = EntityID("limit")
        name = EntityID("name")

        state = State.create({
            counter: Value.create(counter, CellDeclaration("int", 0)),
            limit: Value.create(limit, 10),
            name: Value.create(name, CellDeclaration("str", "")),
        })

        self.assertEqual(
            dict(cells_of(state)),
            {
                counter: CellDeclaration("int", 0),
                name: CellDeclaration("str", ""),
            },
        )


if __name__ == "__main__":
    unittest.main()
