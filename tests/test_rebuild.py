"""Acceptance tests for rebuilding the compiler with its own output
(docs/vm_in_shear.md section 7, roadmap task 27, issue #63).

Each ``swap_all`` run compiles the retained compiler source with the
``lower`` that is active then and installs the result, so generation 1 is
produced by the host-run compiler, and generations 2 and 3 by the compiler
that generation 1 installed, running on the SHEAR interpreter.
"""

from __future__ import annotations

import unittest
from unittest import mock

from shear import EntityID, Runtime, bytecode
from shear.examples import self_hosting, vm
from shear.examples._support import program
from shear.lang import function_at, load, run
from tests import test_vm
from tests.test_vm import same

LOWER = self_hosting.LOWER
GENERATIONS = 3


def _twin_chunk_requests(entities: list) -> list[str]:
    prefixes = tuple(vm.source_name(name).value for name in vm.SWAPPED)
    return [e.value for e in entities if e.value.startswith(prefixes)]


class RebuildTests(unittest.TestCase):
    _built = None

    @classmethod
    def built(cls):
        """One runtime taken through three generations, with the host-lowering
        requests made while generations 2 and 3 were produced."""

        if cls._built is None:
            runtime = Runtime(load(program(vm.bootstrap_entities())))
            state = runtime.active.state
            originals = {
                name: function_at(state, EntityID(name)) for name in vm.SWAPPED
            }
            twins = {
                name: function_at(state, vm.source_name(name))
                for name in vm.SWAPPED
            }
            expressions = test_vm.BootstrapTests.EXPRESSIONS
            native = {
                name: run(runtime, LOWER, twin.body) for name, twin in twins.items()
            }
            before = [run(runtime, LOWER, e) for e in expressions]
            records, requests = [], []
            real = bytecode.chunk_of

            for generation in range(GENERATIONS):
                seen: list = []

                def spy(state, entity, owner=None, _seen=seen):
                    _seen.append(entity)
                    return real(state, entity, owner)

                with mock.patch.object(bytecode, "chunk_of", spy):
                    run(runtime, vm.SWAP_ALL, may_activate=True)

                records.append(run(runtime, vm.GENERATION))
                requests.append(_twin_chunk_requests(seen))

            after = [run(runtime, LOWER, e) for e in expressions]
            cls._built = (
                runtime, originals, twins, native, before, after, records, requests,
            )

        return cls._built

    def test_the_source_is_retained_as_graph_code_that_is_never_swapped(self) -> None:
        runtime, originals, twins, *_ = self.built()
        state = runtime.active.state

        for name in vm.SWAPPED:
            with self.subTest(function=name):
                self.assertEqual(twins[name].params, originals[name].params)
                self.assertEqual(twins[name].body, originals[name].body)
                self.assertEqual(
                    function_at(state, vm.source_name(name)).body, twins[name].body
                )
                self.assertEqual(
                    function_at(state, EntityID(name)).body[:2], ("call", "vm")
                )

    def test_each_run_installs_the_next_generation(self) -> None:
        records = self.built()[6]

        self.assertEqual([record[0] for record in records], [1, 2, 3])

        for record in records:
            self.assertEqual([name for name, _ in record[1]], list(vm.SWAPPED))

    def test_every_generation_agrees_with_the_host_compiler(self) -> None:
        native, records = self.built()[3], self.built()[6]

        for record in records:
            for name, chunk in record[1]:
                with self.subTest(generation=record[0], function=name):
                    same(self, chunk, native[name])

    def test_the_rebuilt_compiler_compiles_the_curated_expressions_as_before(self) -> None:
        _, _, _, _, before, after, *_ = self.built()

        for expression, then, now in zip(test_vm.BootstrapTests.EXPRESSIONS, before, after):
            with self.subTest(expression=expression):
                same(self, now, then)

    def test_generations_two_and_three_never_run_the_host_compiler(self) -> None:
        requests = self.built()[7]

        # Generation 1 is produced by the host-run compiler. After it, the
        # retained source is data for the installed compiler: the host machine
        # never lowers or runs it.
        for generation, seen in enumerate(requests[1:], start=2):
            with self.subTest(generation=generation):
                self.assertEqual(seen, [])

    def test_swapping_still_needs_the_capability(self) -> None:
        from shear import ActivationRejected

        runtime = Runtime(load(program(vm.bootstrap_entities())))

        with self.assertRaises(ActivationRejected):
            run(runtime, vm.SWAP_ALL)


if __name__ == "__main__":
    unittest.main()
