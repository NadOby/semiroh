"""Self-hosting acceptance tests for closures (docs/closures.md §8)."""

import unittest

from semiroh import EntityID, Runtime, canonical_serialize, canonicalize
from semiroh.bytecode import chunk_of
from semiroh.examples import self_hosting, vm
from semiroh.examples._support import program
from semiroh.lang import Function, load, run
from semiroh.relations import relation_of

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
    """Expand child EntityIDs the way the compiler written in SEMIROH does."""

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

    def test_semiroh_vm_runs_compiled_closure(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
