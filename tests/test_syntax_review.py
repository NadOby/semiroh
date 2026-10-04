"""Regression tests found by review of text syntax version 0 (docs/syntax.md).

Each pins a rule of the syntax that a planted bug in ``shear/syntax.py`` got
past the earlier tests: precedence, the scope of ``unquote`` and ``literal``
holes, the columns of parser errors, and the ``else`` of an inline ``if``.
"""

import unittest

from shear import EntityID, Runtime
from shear.lang import load, run
from shear.syntax import SourceError, parse


def value_of(expression: str) -> object:
    rt = Runtime(load(parse(f"fn f():\n    {expression}\n")))
    return run(rt, EntityID("f"))


class PrecedenceTests(unittest.TestCase):
    def test_multiplication_binds_tighter_than_addition(self) -> None:
        for expression, expected in (
            ("1 + 2 * 3", 7),
            ("2 * 3 + 1", 7),
            ("10 - 2 * 3", 4),
            ("2 * 3 - 1", 5),
            ("10 - 2 - 3", 5),
            ("2 * 3 * 4", 24),
            ("1 + 2 * 3 == 7", True),
            ("1 + 1 < 2 * 2", True),
        ):
            with self.subTest(expression=expression):
                self.assertEqual(value_of(expression), expected)


class HoleScopeTests(unittest.TestCase):
    def test_a_hole_is_read_in_the_enclosing_function(self) -> None:
        for hole in ("unquote", "literal"):
            with self.subTest(hole=hole, case="unknown name"):
                # Not a parameter of the code being built, as it would be
                # inside the quote.
                with self.assertRaises(SourceError) as caught:
                    parse(f"fn f(k):\n    quote({hole}(y))\n")

                self.assertEqual(caught.exception.line, 2)

            with self.subTest(hole=hole, case="holes do not nest"):
                for inner in ("unquote(k)", "literal(k)"):
                    with self.assertRaises(SourceError):
                        parse(f"fn f(k):\n    quote({hole}({inner}))\n")

            with self.subTest(hole=hole, case="quote inside a hole"):
                parse(f"fn f(k):\n    quote({hole}(quote(1)))\n")

            with self.subTest(hole=hole, case="parameter and let name"):
                parse(f"fn f(k):\n    let m = k + 1\n    quote({hole}(m + k))\n")


class ErrorPositionTests(unittest.TestCase):
    def test_parser_errors_name_the_column(self) -> None:
        for text, line, column in (
            ("fn f():\n    y\n", 2, 5),  # unknown name
            ("fn f(x):\n    x = 1\n", 2, 5),  # assignment to a parameter
            ("fn len(x):\n    x\n", 1, 4),  # reserved name
            ("fn f():\n    1 < 2 < 3\n", 2, 11),  # chained comparison
        ):
            with self.subTest(text=text):
                with self.assertRaises(SourceError) as caught:
                    parse(text)

                self.assertEqual((caught.exception.line, caught.exception.column), (line, column))


class InlineIfTests(unittest.TestCase):
    def test_an_inline_if_needs_its_else(self) -> None:
        for text in ("fn f(c):\n    1 if c\n", "fn f(c):\n    (1 if c)\n"):
            with self.subTest(text=text):
                with self.assertRaises(SourceError) as caught:
                    parse(text)

                self.assertEqual(caught.exception.line, 2)


if __name__ == "__main__":
    unittest.main()
