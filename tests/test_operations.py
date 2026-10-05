"""One authoritative operation shape (shear/operations.py, roadmap task 19).

Each implementation keeps its own semantics, but none may know an operation
the table does not, and lowering must know every one. The kinds an
implementation dispatches on are read from its source: an operation added
to one place only fails here.
"""

import ast
import dataclasses
import inspect
import textwrap
import unittest

from shear import bytecode, continuity, lang, operations
from shear.examples import self_hosting

KINDS = frozenset(operations.OPERATIONS)


def dispatched(function, variable: str) -> frozenset[str]:
    """Kinds compared against ``variable`` anywhere in ``function``."""

    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    found: set[str] = set()

    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Name)
            and node.left.id == variable
        ):
            continue

        for part in (inner for c in node.comparators for inner in ast.walk(c)):
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                found.add(part.value)
            elif isinstance(part, ast.Name) and part.id in ("_BINARY", "BINARY"):
                found.update(operations.BINARY)
            elif isinstance(part, ast.Name) and part.id == "INVALID_KIND":
                found.add(operations.INVALID)

    return frozenset(found)


class OperationTableTests(unittest.TestCase):
    def test_the_language_derives_its_tables_from_the_operations(self) -> None:
        self.assertEqual(lang.NODE_KINDS, KINDS)
        self.assertEqual(lang._ARITY, operations.ARITY)
        self.assertEqual(continuity._OPERANDS, operations.CODE_ROLES)

    def test_lowering_handles_exactly_the_operations(self) -> None:
        self.assertEqual(dispatched(bytecode.lower, "kind"), KINDS)

    def test_building_and_collapsing_know_no_other_operation(self) -> None:
        self.assertLessEqual(dispatched(lang._Builder._relation, "op"), KINDS)
        self.assertLessEqual(dispatched(lang._collapse, "kind"), KINDS)

    def test_the_self_hosted_compiler_lowers_known_operations(self) -> None:
        # ``label`` is input form only: transparent, it costs no node.
        self.assertLessEqual(self_hosting.LOWERED, KINDS | {"label"})

    def test_ordered_and_positional_shapes_are_consistent(self) -> None:
        for kind, shape in operations.OPERATIONS.items():
            with self.subTest(kind=kind):
                self.assertEqual(shape.kind, kind)
                self.assertLessEqual(shape.ordered, frozenset(shape.code))

                if shape.positional:
                    ordered = [role for role in shape.code if role in shape.ordered]
                    self.assertLessEqual(len(ordered), 1)

                    if ordered:
                        self.assertEqual(shape.code[-1], ordered[0])
                        self.assertIsNone(shape.arity)
                    else:
                        self.assertEqual(shape.arity, len(shape.code))


    def test_the_shared_shapes_cannot_be_changed_in_place(self) -> None:
        # Every language module reads the same Shape objects; one changed in
        # place would silently change them all.
        shape = operations.OPERATIONS["add"]

        with self.assertRaises(dataclasses.FrozenInstanceError):
            shape.arity = 3

if __name__ == "__main__":
    unittest.main()
