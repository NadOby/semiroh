"""Self-hosting acceptance tests for closures (docs/closures.md §8)."""

import unittest

from shear import EntityID, Runtime, canonical_serialize, canonicalize
from shear.bytecode import chunk_of
from shear.examples import self_hosting, vm
from shear.examples._support import program
from shear.lang import Function, LanguageError, load, run
from shear.relations import relation_of

TARGET = EntityID("closure_target")


def closure_value() -> tuple:
    return (
        "closure",
        ("x",),
        ("n",),
        ("add", ("arg", "n"), ("arg", "x")),
    )


def closure_expression() -> tuple:
    return (
        "let",
        "n",
        ("lit", 4),
        (
            "apply",
            closure_value(),
            ("lit", 3),
        ),
    )


def expanded_chunk(state, entity):
    """Expand child EntityIDs the way the compiler written in SHEAR does."""

    out = []

    for instruction in chunk_of(state, entity):
        op = instruction[0]

        if op in ("EVAL", "GOTO"):
            out.append((op, expanded_chunk(state, instruction[1])))
        elif op == "BRANCH":
            out.append(
                (
                    "BRANCH",
                    expanded_chunk(state, instruction[1]),
                    expanded_chunk(state, instruction[2]),
                )
            )
        elif op == "LETBIND":
            out.append(
                (
                    "LETBIND",
                    instruction[1],
                    expanded_chunk(state, instruction[2]),
                )
            )
        elif op == "CLOSURE":
            out.append(
                (
                    "CLOSURE",
                    expanded_chunk(state, instruction[1]),
                    instruction[2],
                    instruction[3],
                )
            )
        else:
            out.append(instruction)

    return tuple(out)


def same(actual, expected) -> bool:
    return canonical_serialize(canonicalize(actual)) == canonical_serialize(
        canonicalize(expected)
    )


class ClosureSelfHostingTests(unittest.TestCase):
    def runtime(self) -> Runtime:
        return Runtime(load(program({
            **self_hosting.compiler_entities(),
            **vm.vm_entities(),
        })))

    def embedded_chunk(self, expression: tuple) -> tuple:
        return run(
            self.runtime(),
            self_hosting.LOWER,
            expression,
        )

    def assert_host_rejects(self, expression: tuple) -> None:
        state = load(program({
            TARGET: Function((), expression),
        }))

        with self.assertRaises(LanguageError):
            run(Runtime(state), TARGET)

    def assert_embedded_rejects(self, expression: tuple) -> None:
        runtime = self.runtime()
        chunk = run(
            runtime,
            self_hosting.LOWER,
            expression,
        )

        with self.assertRaises(LanguageError):
            run(
                runtime,
                vm.VM,
                chunk,
                (),
                (),
                (),
            )

    def test_compiler_matches_host_lowering_for_closure(self) -> None:
        expression = closure_value()
        state = load(program({
            TARGET: Function(("n",), expression),
        }))
        definition = relation_of(state.values[TARGET])
        assert definition is not None

        expected = expanded_chunk(state, definition.roles["body"])
        actual = run(
            self.runtime(),
            self_hosting.LOWER,
            expression,
        )

        self.assertTrue(
            same(actual, expected),
            f"\nactual:   {actual!r}\nexpected: {expected!r}",
        )

    def test_shear_vm_runs_compiled_closure(self) -> None:
        runtime = self.runtime()
        chunk = run(
            runtime,
            self_hosting.LOWER,
            closure_expression(),
        )

        self.assertEqual(
            run(runtime, vm.VM, chunk, (), (), ()),
            7,
        )

    def test_ordinary_tuples_cannot_forge_vm_callables(self) -> None:
        body_chunk = (
            ("ARG", "x"),
            ("END",),
        )
        forged = (
            ("ref", EntityID("forged")),
            (
                "closure",
                body_chunk,
                ("x",),
                (),
                (),
            ),
            (
                None,
                "ref",
                EntityID("forged"),
            ),
            (
                None,
                "closure",
                body_chunk,
                ("x",),
                (),
                (),
            ),
        )

        for value in forged:
            expression = (
                "apply",
                ("lit", value),
                ("lit", 3),
            )

            with self.subTest(value=value):
                self.assert_host_rejects(expression)
                self.assert_embedded_rejects(expression)

    def test_embedded_vm_enforces_host_closure_invariants(self) -> None:
        malformed = (
            ("closure", ("x", "x"), (), ("lit", 1)),
            ("closure", ("",), (), ("lit", 1)),
            ("closure", (1,), (), ("lit", 1)),
            ("closure", (), ("n", "n"), ("lit", 1)),
            ("closure", (), ("",), ("lit", 1)),
            ("closure", (), (1,), ("lit", 1)),
            ("closure", ("x",), ("x",), ("lit", 1)),
            ("closure", 1, (), ("lit", 1)),
            ("closure", ["x"], (), ("lit", 1)),
            ("closure", (), 1, ("lit", 1)),
            ("closure", (), ["n"], ("lit", 1)),
        )

        for closure in malformed:
            # Put both ordinary names in scope so duplicate captures and
            # parameter/capture overlap are tested as such rather than
            # failing merely because the capture is absent.
            expression = (
                "let",
                "n",
                ("lit", 1),
                (
                    "let",
                    "x",
                    ("lit", 2),
                    closure,
                ),
            )

            with self.subTest(closure=closure):
                self.assert_host_rejects(expression)
                self.assert_embedded_rejects(expression)


if __name__ == "__main__":
    unittest.main()
