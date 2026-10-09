
"""Bootstrap support-boundary acceptance (roadmap task 28, GH-64).

The support matrix is documentation; implementation dispatch is the positive
authority. Only rejected and deferred operation sets are declared here.
Tests guard against host compilation or execution replacing an unsupported
SHEAR route.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from unittest import mock

from shear import Runtime, bytecode, operations
from shear import machine as host_machine
from shear.examples import self_hosting, vm
from shear.examples._support import program
from shear.lang import Function, LanguageError, _decode, load, run
from shear.relations import relation_of
from tests.test_operations import dispatched
from tests.test_self_hosting import (
    LOWER,
    T,
    body_root,
    same,
    single,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "bootstrap.md"

REJECTED = frozenset({"invalid"})
LOWER_DEFERRED = frozenset({
    "quote", "unquote", "function", "activate", "trial",
    "catch", "raise",
})
VM_DEFERRED = frozenset({
    "read", "write", "quote", "function", "activate", "trial",
    "catch", "raise", "code", "linksof",
})
VM_MISSING_INSTRUCTIONS = frozenset({
    "READ", "WRITE", "CODE", "LINKS", "QUOTE", "FUNCTION",
    "ACTIVATE", "TRIAL", "CATCH", "FAIL", "RAISE",
})

L = ("lit", 1)
X = ("arg", "x")
Q = ("quote", ("unquote", ("lit", 7)))

# Each witness must actually construct a node of the requested kind.
# Unquote is an internal quote-hole node, not a standalone input form.
WITNESSES = {
    "lit": L,
    "arg": X,
    "add": ("add", X, L),
    "sub": ("sub", X, L),
    "mul": ("mul", X, L),
    "lt": ("lt", X, L),
    "eq": ("eq", X, L),
    "if": ("if", ("lit", True), L, X),
    "seq": ("seq", L, X),
    "call": ("call", "f", X),
    "read": ("read", "c"),
    "write": ("write", "c", L),
    "quote": Q,
    "unquote": Q,
    "function": ("function", ("lit", ("x",)), ("lit", L)),
    "closure": ("closure", ("x",), (), X),
    "activate": ("activate", "f", L),
    "trial": ("trial", ("call", "f", L), "f", L),
    "tuple": ("tuple", L, X),
    "len": ("len", ("tuple", L)),
    "item": ("item", ("tuple", L), ("lit", 0)),
    "slice": ("slice", ("tuple", L), ("lit", 0), L),
    "concat": ("concat", ("tuple", L), ("tuple", X)),
    "let": ("let", "y", L, ("arg", "y")),
    "catch": ("catch", L),
    "raise": ("raise", ("lit", "test"), L),
    "ref": ("ref", "f"),
    "code": ("code", "f"),
    "linksof": ("linksof", "f"),
    "apply": ("apply", ("ref", "f"), X),
    "applyv": ("applyv", ("ref", "f"), ("tuple", X)),
    "invalid": ("not_a_bootstrap_operation",),
}


def _matrix() -> dict[str, tuple[str, str, str, str]]:
    """Read the documented operation rows, preserving duplicate detection."""

    pattern = re.compile(
        r"^\| `([a-z]+)` \| ([SRD]) \| ([SRD]) \|"
        r" ([SRD]) \| ([SRD]) \|$"
    )
    found = []

    for line in SPEC.read_text(encoding="utf-8").splitlines():
        match = pattern.fullmatch(line.strip())

        if match:
            found.append((match.group(1), match.groups()[1:]))

    names = [name for name, _ in found]

    if len(names) != len(set(names)):
        raise AssertionError("duplicate bootstrap operation row")

    return dict(found)


def _node_for(kind: str):
    """Load a realistic graph and find the required operation node."""

    state = single(WITNESSES[kind])
    matches = []

    for value in state.values.values():
        node = relation_of(value)

        if node is not None and node.kind == kind:
            matches.append(node)

    if not matches:
        raise AssertionError(f"witness did not construct {kind}")

    return matches[0]


def _opcodes(kind: str) -> frozenset[str]:
    return frozenset(instruction[0] for instruction in bytecode.lower(
        _node_for(kind)
    ))


def _expanded(state, entity):
    """Independently expand host graph chunks into SHEAR compiler form."""

    node = relation_of(state.values[entity])
    assert node is not None

    name = (
        _decode(node.payload)
        if node.kind in {
            "call", "ref", "code", "linksof", "read", "write",
        }
        else None
    )
    result = []

    for instruction in bytecode.chunk_of(state, entity):
        op = instruction[0]

        if op == "LIT":
            result.append(("LIT", _decode(instruction[1])))
        elif op in ("EVAL", "GOTO"):
            result.append((op, _expanded(state, instruction[1])))
        elif op == "BRANCH":
            result.append((
                "BRANCH",
                _expanded(state, instruction[1]),
                _expanded(state, instruction[2]),
            ))
        elif op == "LETBIND":
            result.append((
                "LETBIND",
                instruction[1],
                _expanded(state, instruction[2]),
            ))
        elif op == "CLOSURE":
            result.append((
                "CLOSURE",
                _expanded(state, instruction[1]),
                instruction[2],
                instruction[3],
            ))
        elif op == "CALL":
            result.append(("CALL", name, instruction[2]))
        elif op in ("REF", "CODE", "LINKS", "READ", "WRITE"):
            result.append((op, name))
        else:
            result.append(instruction)

    return tuple(result)


class MatrixTests(unittest.TestCase):
    def test_every_operation_has_exactly_one_witness_and_matrix_row(self):
        kinds = set(operations.OPERATIONS)

        self.assertEqual(set(WITNESSES), kinds)
        self.assertEqual(set(_matrix()), kinds)
        self.assertEqual(len(_matrix()), len(kinds))
        self.assertNotIn("label", kinds)

        for kind in kinds:
            with self.subTest(kind=kind):
                self.assertEqual(_node_for(kind).kind, kind)

    def test_host_lowering_dispatch_is_complete(self):
        self.assertEqual(
            dispatched(bytecode.lower, "kind"),
            frozenset(operations.OPERATIONS),
        )

        handled = dispatched(host_machine._execute, "op")

        for kind in operations.OPERATIONS:
            with self.subTest(kind=kind):
                chunk = bytecode.lower(_node_for(kind))
                self.assertEqual(chunk[-1], ("END",))
                self.assertLessEqual(
                    {instruction[0] for instruction in chunk},
                    handled,
                )

    def test_supported_statuses_follow_dispatch(self):
        table = _matrix()
        self.assertEqual(set(self_hosting.LOWERED) - {"label"},
                         set(operations.OPERATIONS) -
                         LOWER_DEFERRED - REJECTED)
        self.assertEqual(set(vm._ORDER), set(dict(vm._cases())))

        vm_instructions = set(vm._ORDER)

        for kind in operations.OPERATIONS:
            with self.subTest(kind=kind):
                host_status = "R" if kind in REJECTED else "S"
                lower_status = (
                    "R" if kind in REJECTED
                    else "D" if kind in LOWER_DEFERRED
                    else "S"
                )
                vm_status = (
                    "R" if kind in REJECTED
                    else "S" if _opcodes(kind) <= vm_instructions
                    else "D"
                )
                self.assertEqual(
                    table[kind],
                    (host_status, host_status,
                     lower_status, vm_status),
                )
                self.assertEqual(
                    vm_status == "D",
                    kind in VM_DEFERRED,
                )

    def test_host_rejects_invalid_code_explicitly(self):
        chunk = bytecode.lower(_node_for("invalid"))
        self.assertEqual(chunk[0][0], "RAISE")

        with self.assertRaises(LanguageError):
            run(Runtime(single(WITNESSES["invalid"])), T, 1)


class LoweringBoundaryTests(unittest.TestCase):
    def test_every_supported_shear_lowering_matches_host_expansion(self):
        runtime = Runtime(load(program(self_hosting.compiler_entities())))

        for kind in sorted(
            set(operations.OPERATIONS) - LOWER_DEFERRED - REJECTED
        ):
            with self.subTest(kind=kind):
                expression = WITNESSES[kind]
                state = single(expression)
                expected = _expanded(state, body_root(state, T))
                actual = run(runtime, LOWER, expression)
                same(self, actual, expected, kind)

    def test_deferred_lowering_does_not_invoke_host_lowering(self):
        runtime = Runtime(load(program(self_hosting.compiler_entities())))
        original = bytecode.lower
        forbidden = LOWER_DEFERRED | REJECTED

        def guarded(node):
            if node.kind in forbidden:
                raise AssertionError(
                    f"host lowering fallback for {node.kind}"
                )
            return original(node)

        with mock.patch.object(bytecode, "lower", side_effect=guarded):
            for kind in sorted(forbidden):
                with self.subTest(kind=kind):
                    # The interpreter sees input-form tuple data.
                    # Standalone unquote is intentional here.
                    expression = (
                        ("unquote", L)
                        if kind == "unquote"
                        else WITNESSES[kind]
                    )
                    result = run(runtime, LOWER, expression)
                    self.assertEqual(
                        result,
                        (("RAISE", "unknown operation"), ("END",)),
                    )


class InterpreterBoundaryTests(unittest.TestCase):
    def test_missing_instructions_are_exactly_the_declared_set(self):
        host_instructions = dispatched(host_machine._execute, "op")
        interpreted = set(vm._ORDER)

        self.assertTrue(VM_MISSING_INSTRUCTIONS.isdisjoint(interpreted))
        self.assertLessEqual(VM_MISSING_INSTRUCTIONS, host_instructions)

        for kind in VM_DEFERRED:
            with self.subTest(kind=kind):
                self.assertTrue(
                    _opcodes(kind) & VM_MISSING_INSTRUCTIONS
                )

        self.assertEqual(_opcodes("unquote"), {"GOTO", "END"})

    def test_unsupported_instruction_uses_interpreter_trap(self):
        # Replace only the interpreter's trap with an observable witness.
        # A host fallback cannot satisfy this assertion accidentally.
        marker = "bootstrap-unsupported-instruction"
        entities = vm.vm_entities()
        entities[vm.TRAP] = Function((), ("lit", marker))
        runtime = Runtime(load(program(entities)))

        self.assertEqual(
            run(runtime, vm.VM, (("LIT", 7), ("END",)),
                (), (), ()),
            7,
        )

        for opcode in sorted(VM_MISSING_INSTRUCTIONS):
            with self.subTest(opcode=opcode):
                self.assertEqual(
                    run(runtime, vm.VM, ((opcode,), ("END",)),
                        (), (), ()),
                    marker,
                )

    def test_unmodified_interpreter_trap_is_a_language_error(self):
        runtime = Runtime(load(program(vm.vm_entities())))

        with self.assertRaises(LanguageError):
            run(runtime, vm.VM, (("READ",), ("END",)),
                (), (), ())


class InventoryTests(unittest.TestCase):
    def test_every_host_service_has_contract_implementation_and_tests(self):
        content = SPEC.read_text(encoding="utf-8")
        section = content.split("## 3. Host-service inventory", 1)[1]
        section = section.split("### 3.1", 1)[0]
        rows = [
            line for line in section.splitlines()
            if line.startswith("| ") and not line.startswith(
                ("| Service ", "| ---")
            )
        ]

        self.assertGreaterEqual(len(rows), 15)

        for line in rows:
            with self.subTest(service=line.split("|")[1].strip()):
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                self.assertEqual(len(cells), 5)
                self.assertTrue(all(cells))

                names = re.findall(r"`(test_[a-z_]+\.py)`", cells[4])
                self.assertTrue(names)

                for name in names:
                    self.assertTrue(
                        (ROOT / "tests" / name).is_file(),
                        name,
                    )


if __name__ == "__main__":
    unittest.main()
