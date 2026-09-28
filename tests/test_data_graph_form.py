"""Graph form of tuples, let, references and apply, and frames under tail
calls (docs/graph_form.md section 3, docs/language_data.md). Complements
the acceptance tests in test_data_ops.py."""

import unittest

from semiroh import EntityID, Runtime
from semiroh.examples._support import program
from semiroh.lang import Function, LanguageError, function_at, links, load, run
from semiroh.relations import relation_of

F = EntityID("f")
G = EntityID("g")
LOOP = EntityID("loop")
FAIL = EntityID("fail")

ROLES = {
    "tuple": {"items"},
    "len": {"tuple"},
    "item": {"tuple", "index"},
    "slice": {"tuple", "start", "stop"},
    "concat": {"left", "right"},
    "let": {"value", "body"},
    "ref": {"target"},
    "apply": {"function", "args"},
}


def loaded(body: tuple) -> tuple:
    state = load(program({
        F: Function((), body),
        G: Function(("n",), ("arg", "n")),
        EntityID("f.links"): links(F, g=G),
    }))

    return state, body


class GraphFormTests(unittest.TestCase):
    def test_new_operations_round_trip_through_function_at(self) -> None:
        state, body = loaded((
            "let", "y", ("tuple", ("lit", 1), ("ref", "g")),
            ("apply", ("item", ("arg", "y"), ("lit", 1)),
             ("len", ("concat", ("slice", ("arg", "y"), ("lit", 0), ("lit", 1)),
                      ("tuple",)))),
        ))

        self.assertEqual(function_at(state, F), Function((), body))

    def test_new_operations_use_the_documented_roles(self) -> None:
        state, _ = loaded((
            "let", "y", ("tuple", ("ref", "g")),
            ("apply", ("item", ("arg", "y"), ("lit", 0)),
             ("len", ("concat", ("slice", ("arg", "y"), ("lit", 0), ("lit", 1)),
                      ("tuple",)))),
        ))
        seen = {}

        for value in state.values.values():
            node = relation_of(value)

            if node is not None and node.kind in ROLES:
                seen[node.kind] = set(node.roles)

        self.assertEqual(seen, ROLES)

    def test_a_let_with_a_bad_name_round_trips_and_fails_when_run(self) -> None:
        body = ("let", 5, ("lit", 1), ("lit", 0))
        state, _ = loaded(body)

        self.assertEqual(function_at(state, F), Function((), body))

        with self.assertRaises(LanguageError):
            run(Runtime(state), F)


class FrameTests(unittest.TestCase):
    def test_a_tail_call_that_raises_leaks_no_hold(self) -> None:
        n = ("arg", "n")
        state = load(program({
            LOOP: Function(
                ("n",),
                (
                    "if",
                    ("eq", n, ("lit", 0)),
                    ("call", "fail"),  # wrong arity, raised in the callee
                    ("call", "loop", ("sub", n, ("lit", 1))),
                ),
            ),
            EntityID("loop.links"): links(LOOP, loop=LOOP, fail=FAIL),
            FAIL: Function(("x",), ("arg", "x")),
        }))
        runtime = Runtime(state)

        with self.assertRaises(LanguageError):
            run(runtime, LOOP, 50)

        self.assertEqual(runtime.active.holds, frozenset())

    def test_apply_of_an_absent_entity_is_a_language_error(self) -> None:
        for tail in (True, False):
            with self.subTest(tail=tail):
                call = ("apply", ("lit", EntityID("gone")), ("lit", 1))
                body = call if tail else ("add", ("lit", 1), call)
                runtime = Runtime(loaded(body)[0])

                with self.assertRaises(LanguageError):
                    run(runtime, F)

                self.assertEqual(runtime.active.holds, frozenset())


if __name__ == "__main__":
    unittest.main()
