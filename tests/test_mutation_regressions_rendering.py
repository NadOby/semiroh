"""Mutation regressions for syntax rendering and round trips."""

from __future__ import annotations

import unittest

from shear import CellDeclaration, EntityID, IsKind
from shear.examples._support import program
from shear.lang import Function, function_of, links, load
from shear.syntax import parse, render


class SyntaxRenderingRegressionTests(unittest.TestCase):
    def test_raw_trial_target_uses_current_entity_name(self) -> None:
        function = EntityID("f")
        target = EntityID("target")

        state = load(program({
            target: Function(
                (),
                ("lit", 0),
            ),
            function: Function(
                (),
                (
                    "trial",
                    ("lit", 0),
                    "alias",
                    ("lit", 1),
                ),
            ),
            EntityID("f.links"): links(
                function,
                alias=target,
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f():\n"
            '    raw(("trial", ("lit", 0), "target", ("lit", 1)))\n',
        )

    def test_backquoted_names_round_trip_escaping(self) -> None:
        function = EntityID("f")

        for name in (
            "a\\b",
            "a`b",
            "a\nb",
            "a\x01b",
            "a\x7fb",
        ):
            with self.subTest(name=repr(name)):
                state = load(program({
                    function: Function(
                        (name,),
                        ("arg", name),
                    ),
                }))
                text = render(
                    state,
                    function,
                )
                parsed = function_of(
                    parse(text).values[function]
                )

                self.assertIsNotNone(parsed)
                assert parsed is not None
                self.assertEqual(
                    parsed.params,
                    (name,),
                )
                self.assertEqual(
                    parsed.body,
                    ("arg", name),
                )

    def test_equality_is_parenthesized_inside_addition(self) -> None:
        function = EntityID("f")
        state = load(program({
            function: Function(
                ("x", "y"),
                (
                    "add",
                    (
                        "eq",
                        ("arg", "x"),
                        ("arg", "y"),
                    ),
                    ("lit", 1),
                ),
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f(x, y):\n"
            "    (x == y) + 1\n",
        )

    def test_function_and_closure_values_keep_inline_if_precedence(
        self,
    ) -> None:
        function = EntityID("f")
        function_value = (
            "function",
            ("lit", ("y",)),
            ("quote", ("arg", "y")),
        )
        closure_value = (
            "closure",
            ("y",),
            (),
            ("arg", "y"),
        )

        for value, expected in (
            (
                function_value,
                "((fn(y): y) if x else 0,)",
            ),
            (
                closure_value,
                "((closure(y) captures(): y) if x else 0,)",
            ),
        ):
            with self.subTest(expected=expected):
                state = load(program({
                    function: Function(
                        ("x",),
                        (
                            "tuple",
                            (
                                "if",
                                ("arg", "x"),
                                value,
                                ("lit", 0),
                            ),
                        ),
                    ),
                }))

                self.assertEqual(
                    render(state, function),
                    "fn f(x):\n"
                    f"    {expected}\n",
                )

    def test_single_item_seq_renders_without_recursing(self) -> None:
        function = EntityID("f")
        state = load(program({
            function: Function(
                (),
                (
                    "seq",
                    ("lit", 1),
                ),
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f():\n"
            "    1\n",
        )

    def test_non_tail_nested_seq_does_not_promote_let(self) -> None:
        function = EntityID("f")
        state = load(program({
            function: Function(
                (),
                (
                    "seq",
                    (
                        "seq",
                        (
                            "let",
                            "y",
                            ("lit", 1),
                            ("arg", "y"),
                        ),
                    ),
                    ("lit", 2),
                ),
            ),
        }))

        text = render(
            state,
            function,
        )

        self.assertIn(
            'raw(("let", "y",',
            text,
        )
        self.assertTrue(
            text.endswith("    2\n"),
        )

    def test_if_branch_keeps_tail_context_for_let(self) -> None:
        function = EntityID("f")
        state = load(program({
            function: Function(
                ("x",),
                (
                    "if",
                    ("arg", "x"),
                    (
                        "let",
                        "y",
                        ("lit", 1),
                        ("arg", "y"),
                    ),
                    ("lit", 0),
                ),
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f(x):\n"
            "    if x:\n"
            "        let y = 1\n"
            "        y\n"
            "    else:\n"
            "        0\n",
        )

    def test_general_apply_packs_multiple_arguments(self) -> None:
        function = EntityID("f")
        state = load(program({
            function: Function(
                ("x",),
                (
                    "apply",
                    (
                        "add",
                        ("arg", "x"),
                        ("arg", "x"),
                    ),
                    ("lit", 1),
                    ("lit", 2),
                ),
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f(x):\n"
            "    apply(x + x, (1, 2))\n",
        )

    def test_write_uses_current_target_name(self) -> None:
        function = EntityID("f")
        target = EntityID("target")
        state = load(program({
            target: CellDeclaration(
                IsKind("int"),
                0,
            ),
            function: Function(
                (),
                (
                    "write",
                    "alias",
                    ("lit", 1),
                ),
            ),
            EntityID("f.links"): links(
                function,
                alias=target,
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f():\n"
            "    target = 1\n",
        )

    def test_unquote_uses_current_target_name(self) -> None:
        function = EntityID("f")
        target = EntityID("target")
        state = load(program({
            target: Function(
                (),
                ("lit", 1),
            ),
            function: Function(
                (),
                (
                    "quote",
                    (
                        "unquote",
                        ("call", "alias"),
                    ),
                ),
            ),
            EntityID("f.links"): links(
                function,
                alias=target,
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f():\n"
            "    quote(unquote(target()))\n",
        )

    def test_global_call_colliding_with_local_renders_raw(
        self,
    ) -> None:
        function = EntityID("f")
        target = EntityID("g")
        state = load(program({
            target: Function(
                (),
                ("lit", 1),
            ),
            function: Function(
                ("g",),
                ("call", "alias"),
            ),
            EntityID("f.links"): links(
                function,
                alias=target,
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f(g):\n"
            '    raw(("call", "g"))\n',
        )

    def test_empty_activate_renders_raw(self) -> None:
        function = EntityID("f")
        state = load(program({
            function: Function(
                (),
                ("activate",),
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f():\n"
            '    raw(("activate",))\n',
        )

    def test_zero_argument_trial_renders_normally(self) -> None:
        function = EntityID("f")
        target = EntityID("target")
        state = load(program({
            target: Function(
                (),
                ("lit", 1),
            ),
            function: Function(
                (),
                (
                    "trial",
                    ("call", "alias"),
                ),
            ),
            EntityID("f.links"): links(
                function,
                alias=target,
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f():\n"
            "    trial(target())\n",
        )

    def test_malformed_trial_renders_raw(self) -> None:
        function = EntityID("f")
        state = load(program({
            function: Function(
                (),
                (
                    "trial",
                    ("call",),
                ),
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f():\n"
            '    raw(("trial", ("call",)))\n',
        )

    def test_raw_fallback_preserves_malformed_shapes_and_maps_links(
        self,
    ) -> None:
        function = EntityID("f")
        target = EntityID("target")
        cases = (
            (
                ("activate", ("alias", "k")),
                '("activate", ("target", "k"))',
            ),
            (
                (
                    "let",
                    "x",
                    ("call", "alias"),
                    ("lit", 0),
                    ("lit", 1),
                ),
                '("let", "x", ("call", "target"), ("lit", 0), ("lit", 1))',
            ),
            (
                (
                    "label",
                    "k",
                    ("call", "alias"),
                    ("lit", 0),
                ),
                '("label", "k", ("call", "target"), ("lit", 0))',
            ),
            (
                (
                    "closure",
                    ("x",),
                    (),
                    ("call", "alias"),
                    ("lit", 0),
                ),
                '("closure", ("x",), (), ("call", "target"), ("lit", 0))',
            ),
        )

        for expression, expected in cases:
            with self.subTest(expression=expression):
                state = load(program({
                    target: Function(
                        (),
                        ("lit", 0),
                    ),
                    function: Function(
                        (),
                        expression,
                    ),
                    EntityID("f.links"): links(
                        function,
                        alias=target,
                    ),
                }))

                self.assertEqual(
                    render(state, function),
                    "fn f():\n"
                    f"    raw({expected})\n",
                )

    def test_closure_inside_quote_renders_raw(self) -> None:
        function = EntityID("f")
        state = load(program({
            function: Function(
                (),
                (
                    "quote",
                    (
                        "closure",
                        ("x",),
                        (),
                        ("arg", "x"),
                    ),
                ),
            ),
        }))

        self.assertIn(
            'raw(("quote", ("closure",',
            render(state, function),
        )

    def test_global_cell_collision_keeps_argument_raw(self) -> None:
        function = EntityID("f")
        cell = EntityID("c")
        state = load(program({
            cell: CellDeclaration(
                IsKind("int"),
                0,
            ),
            function: Function(
                ("c",),
                ("arg", "c"),
            ),
        }))

        self.assertEqual(
            render(state, function),
            "fn f(c):\n"
            '    raw(("arg", "c"))\n',
        )


if __name__ == "__main__":
    unittest.main()
