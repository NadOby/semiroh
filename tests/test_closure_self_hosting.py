"""Self-hosting acceptance tests for closures (docs/closures.md §8)."""

import unittest

from semiroh import Runtime
from semiroh.examples import self_hosting, vm
from semiroh.examples._support import program
from semiroh.lang import load, run


def closure_expression() -> tuple:
    return (
        "let",
        "n",
        ("lit", 4),
        (
            "apply",
            (
                "closure",
                ("x",),
                ("n",),
                ("add", ("arg", "n"), ("arg", "x")),
            ),
            ("lit", 3),
        ),
    )


class ClosureSelfHostingTests(unittest.TestCase):
    def runtime(self) -> Runtime:
        return Runtime(load(program({
            **self_hosting.compiler_entities(),
            **vm.vm_entities(),
        })))

    def test_compiler_knows_closure(self) -> None:
        chunk = run(
            self.runtime(),
            self_hosting.LOWER,
            closure_expression(),
        )

        self.assertNotEqual(chunk[0][0], "RAISE")

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
