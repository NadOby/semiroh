"""Mutation regressions for source parsing and tokenization."""

from __future__ import annotations

import unittest

from shear import EntityID
from shear.cells import cell_declaration
from shear.lang import function_of
from shear.syntax import SourceError, parse


class SyntaxLiteralRegressionTests(unittest.TestCase):
    def test_false_data_literal_remains_false(self) -> None:
        state = parse(
            "cell flag: bool = false\n"
        )
        declaration = cell_declaration(
            state.values[EntityID("flag")]
        )

        self.assertIsNotNone(declaration)
        assert declaration is not None
        self.assertIs(
            declaration.initial,
            False,
        )


class SyntaxParserRegressionTests(unittest.TestCase):
    def test_incomplete_expression_raises_source_error(self) -> None:
        with self.assertRaises(SourceError):
            parse(
                "fn f():\n"
                "    1 +\n"
            )

    def test_unexpected_expression_operator_raises_source_error(
        self,
    ) -> None:
        with self.assertRaises(SourceError):
            parse(
                "fn f():\n"
                "    +\n"
            )

    def test_cell_type_keyword_cannot_be_backquoted(self) -> None:
        with self.assertRaises(SourceError):
            parse(
                "cell c: `int` = 0\n"
            )

    def test_stray_operator_cannot_open_data_literal(self) -> None:
        with self.assertRaises(SourceError):
            parse(
                "cell c: int = +0)\n"
            )

    def test_label_requires_a_name(self) -> None:
        with self.assertRaises(SourceError):
            parse(
                "fn f():\n"
                "    label(1, 2)\n"
            )

    def test_invalid_backquoted_escape_has_exact_position(self) -> None:
        with self.assertRaises(SourceError) as caught:
            parse(
                "fn `a\\x`():\n"
                "    1\n"
            )

        self.assertEqual(
            (
                caught.exception.line,
                caught.exception.column,
            ),
            (1, 7),
        )

    def test_crlf_source_parses_like_lf_source(self) -> None:
        state = parse(
            "fn f():\r\n"
            "    1\r\n"
        )
        function = function_of(
            state.values[EntityID("f")]
        )

        self.assertIsNotNone(function)
        assert function is not None
        self.assertEqual(
            function.body,
            ("lit", 1),
        )

    def test_closure_parameter_and_capture_may_not_overlap(
        self,
    ) -> None:
        with self.assertRaises(SourceError):
            parse(
                "fn f(x):\n"
                "    closure(x) captures(x): x\n"
            )

    def test_links_relation_from_base_is_not_callable(self) -> None:
        base = parse(
            "fn keep():\n"
            "    1\n"
            "\n"
            "fn use():\n"
            "    keep()\n"
        )

        self.assertIn(
            EntityID("use.links"),
            base.values,
        )

        with self.assertRaises(SourceError):
            parse(
                "fn f():\n"
                "    `use.links`()\n",
                base=base,
            )


if __name__ == "__main__":
    unittest.main()
