"""Regression tests for gaps in the language acceptance suites.

Each test here fails on a plausible bug that the broader acceptance suites
let through: data-operation edge cases, tail-position mistakes, and malformed
input-form expressions that must load as invalid graph nodes and fail only
when executed.
"""

import unittest

from semiroh import (
    CellDeclaration,
    EntityID,
    IntRange,
    Runtime,
    State,
    canonical_serialize,
    canonicalize,
)
from semiroh.examples._support import program
from semiroh.lang import Function, LanguageError, links, load, run

F = EntityID("f")
ONE = EntityID("one")
NONE = EntityID("none")
BUMP = EntityID("bump")
LOOP = EntityID("loop")
COUNTER = EntityID("counter")


def build(body: tuple, params: tuple = ()) -> State:
    """F with `body`, linked to small helpers that ignore their arguments."""

    n, acc = ("arg", "n"), ("arg", "acc")

    return load(program({
        F: Function(params, body),
        EntityID("f.links"): links(F, one=ONE, none=NONE, bump=BUMP),
        ONE: Function(("x",), ("lit", 1)),
        NONE: Function((), ("lit", 1)),
        COUNTER: CellDeclaration(IntRange(0, 100), 0),
        BUMP: Function(
            (),
            ("write", "counter", ("add", ("read", "counter"), ("lit", 1))),
        ),
        EntityID("bump.links"): links(BUMP, counter=COUNTER),
        # The tail call is in the then-branch of the `if`.
        LOOP: Function(
            ("n", "acc"),
            (
                "if",
                ("lt", ("lit", 0), n),
                ("call", "loop", ("sub", n, ("lit", 1)), ("add", acc, n)),
                acc,
            ),
        ),
        EntityID("loop.links"): links(LOOP, loop=LOOP),
    }))


class SliceAndItemTests(unittest.TestCase):
    def assertSame(self, actual: object, expected: object) -> None:
        self.assertEqual(
            canonical_serialize(canonicalize(actual)),
            canonical_serialize(canonicalize(expected)),
        )

    def test_slice_honours_its_stop_below_the_length(self) -> None:
        t = ("arg", "t")
        data = (4, 5, 6, 7)

        for start, stop in ((1, 3), (0, 1), (2, 2), (0, 0), (0, 4), (3, 4)):
            with self.subTest(start=start, stop=stop):
                body = ("slice", t, ("lit", start), ("lit", stop))

                self.assertSame(
                    run(Runtime(build(body, ("t",))), F, data),
                    data[start:stop],
                )

    def test_item_reaches_every_valid_index(self) -> None:
        t = ("arg", "t")
        data = (4, 5, 6, 7)

        for index in range(len(data)):
            with self.subTest(index=index):
                body = ("item", t, ("lit", index))

                self.assertEqual(
                    run(Runtime(build(body, ("t",))), F, data),
                    data[index],
                )


class ArityTests(unittest.TestCase):
    def test_a_wrong_number_of_arguments_raises_however_it_is_called(self) -> None:
        # The callees ignore their arguments, so a missing or an extra one is
        # noticed only by the arity check itself.
        wrong = {
            "call, too few": ("call", "one"),
            "call, too many": ("call", "none", ("lit", 5)),
            "apply, too few": ("apply", ("ref", "one")),
            "apply, too many": ("apply", ("ref", "none"), ("lit", 5)),
        }

        for label, call in wrong.items():
            for tail in (True, False):
                with self.subTest(call=label, tail=tail):
                    body = call if tail else ("add", ("lit", 0), call)
                    runtime = Runtime(build(body))

                    with self.assertRaises(LanguageError):
                        run(runtime, F)

                    self.assertEqual(runtime.active.holds, frozenset())


class MalformedInputFormTests(unittest.TestCase):
    def assertInvalidAtRun(self, body: tuple) -> None:
        # Loading malformed input-form code must succeed. The malformed
        # expression is represented by an invalid graph node and checked only
        # when execution reaches it.
        state = build(body)

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)

    def test_call_without_a_link_loads_as_invalid(self) -> None:
        self.assertInvalidAtRun(("call",))

    def test_ref_with_an_unknown_link_loads_as_invalid(self) -> None:
        self.assertInvalidAtRun(("ref", "missing"))

    def test_apply_without_a_function_loads_as_invalid(self) -> None:
        self.assertInvalidAtRun(("apply",))

    def test_trial_without_a_call_form_loads_as_invalid(self) -> None:
        self.assertInvalidAtRun(("trial",))


class LetScopeTests(unittest.TestCase):
    def test_sibling_lets_may_reuse_a_name(self) -> None:
        for body, expected in (
            (
                ("add",
                 ("let", "y", ("lit", 1), ("arg", "y")),
                 ("let", "y", ("lit", 2), ("arg", "y"))),
                3,
            ),
            (
                ("seq",
                 ("let", "y", ("lit", 1), ("lit", 0)),
                 ("let", "y", ("lit", 2), ("arg", "y"))),
                2,
            ),
        ):
            with self.subTest(body=body):
                self.assertEqual(run(Runtime(build(body)), F), expected)

    def test_a_let_name_is_unbound_after_the_let(self) -> None:
        body = ("seq", ("let", "y", ("lit", 1), ("lit", 0)), ("arg", "y"))

        with self.assertRaises(LanguageError):
            run(Runtime(build(body)), F)

    def test_a_let_value_is_computed_before_the_body_in_tail_position(self) -> None:
        # The let is the body root, so its body is in tail position; its
        # value is not, and must be a number when the body adds to it.
        body = (
            "let", "v", ("call", "one", ("lit", 7)),
            ("add", ("arg", "v"), ("lit", 1)),
        )

        self.assertEqual(run(Runtime(build(body)), F), 2)


class TailPositionTests(unittest.TestCase):
    def test_a_tail_call_in_the_then_branch_runs_in_constant_stack(self) -> None:
        runtime = Runtime(build(("lit", 0)))

        self.assertEqual(run(runtime, LOOP, 5000, 0), 12502500)
        self.assertEqual(runtime.active.holds, frozenset())

    def test_calls_before_the_last_item_of_a_seq_still_run(self) -> None:
        # Only the last item is in tail position; the first call must run
        # before the second, not be handed back as a tail call and dropped.
        runtime = Runtime(build(("seq", ("call", "bump"), ("call", "bump"))))

        self.assertEqual(run(runtime, F), 2)
        self.assertEqual(runtime.read(COUNTER), 2)
        self.assertEqual(runtime.active.holds, frozenset())


if __name__ == "__main__":
    unittest.main()
