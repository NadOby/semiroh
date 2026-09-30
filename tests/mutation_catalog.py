"""Mutation targets and reviewed survivor classifications."""

from __future__ import annotations


EQUIVALENT = "equivalent"
UNSPECIFIED = "unspecified"

CLASSIFICATIONS = frozenset({
    EQUIVALENT,
    UNSPECIFIED,
})


# Production semantic implementation exercised by mutation campaigns.
#
# Examples are normally inputs/fixtures rather than implementation, but the
# embedded compiler and VM are independent implementations and therefore are
# deliberate mutation targets.
TARGETS = (
    "semiroh/bytecode.py",
    "semiroh/canonical.py",
    "semiroh/cells.py",
    "semiroh/closures.py",
    "semiroh/constraints.py",
    "semiroh/continuity.py",
    "semiroh/equality.py",
    "semiroh/fold.py",
    "semiroh/lang.py",
    "semiroh/machine.py",
    "semiroh/matching.py",
    "semiroh/ownership.py",
    "semiroh/reconcile.py",
    "semiroh/references.py",
    "semiroh/relations.py",
    "semiroh/runtime.py",
    "semiroh/state.py",
    "semiroh/syntax.py",
    "semiroh/transforms.py",
    "semiroh/values.py",
    "semiroh/examples/self_hosting.py",
    "semiroh/examples/vm.py",
)


# Python files intentionally not mutation targets.  This makes omissions
# explicit rather than allowing new semantic modules to fall out of mutation
# coverage silently.
OMITTED = {
    "semiroh/__init__.py":
        "public re-export surface; semantic behaviour lives in its modules",
    "semiroh/identity.py":
        "declarative frozen identifier records with no semantic algorithm",
    "semiroh/examples/__init__.py":
        "example/corpus harness rather than a semantic implementation",
    "semiroh/examples/_support.py":
        "example construction helper rather than semantic implementation",
    "semiroh/examples/closures.py":
        "example program exercised through the corpus",
    "semiroh/examples/control.py":
        "example program exercised through the corpus",
    "semiroh/examples/data.py":
        "example program exercised through the corpus",
    "semiroh/examples/higher_order.py":
        "example program exercised through the corpus",
    "semiroh/examples/ledger.py":
        "example program exercised through the corpus",
    "semiroh/examples/missing.py":
        "wanted-feature corpus data rather than implementation",
    "semiroh/examples/recursion.py":
        "example program exercised through the corpus",
    "semiroh/examples/self_modification.py":
        "example program exercised through the corpus",
    "semiroh/examples/side_effects.py":
        "example program exercised through the corpus",
}


# Known surviving mutants that have been reviewed.
#
# Key:
#     (target path, mutation kind, stripped original source line)
#
# A test gap is deliberately NOT stored here.  It receives a regression test
# and should then be killed.  Only genuinely equivalent changes and behaviour
# outside the specified semantic contract may remain classified survivors.
SURVIVORS = {
    (
        "semiroh/bytecode.py",
        "constant",
        "_lowered = 0",
    ): (
        EQUIVALENT,
        "the counter is only observed as a difference",
    ),
    (
        "semiroh/bytecode.py",
        "constant",
        "may_activate: bool = False,",
    ): (
        EQUIVALENT,
        "the only caller supplies may_activate explicitly",
    ),
    (
        "semiroh/runtime.py",
        "return",
        'return f"Version({self.id.value[:12]}, holds={len(self._holds)})"',
    ): (
        UNSPECIFIED,
        "Version repr text is diagnostic, not semantic behaviour",
    ),
    (
        "semiroh/runtime.py",
        "constant",
        'return f"Version({self.id.value[:12]}, holds={len(self._holds)})"',
    ): (
        UNSPECIFIED,
        "Version repr text is diagnostic, not semantic behaviour",
    ),
    (
        "semiroh/examples/self_hosting.py",
        "constant",
        "hits: CellDeclaration(IntRange(0, 100), 0),",
    ): (
        UNSPECIFIED,
        "the instrumentation cell bound is not part of compiler semantics",
    ),
    (
        "semiroh/examples/self_hosting.py",
        "constant",
        'step(("quote", ("lit", 1)), (("RAISE", "unknown operation"), end)),',
    ): (
        EQUIVALENT,
        "the quoted template is not evaluated by this step",
    ),
    (
        "semiroh/bytecode.py",
        "constant",
        "control.append((_RETURN, 0, False, None, activation))",
    ): (
        EQUIVALENT,
        "the RETURN sentinel tail flag is never read",
    ),
    (
        "semiroh/examples/vm.py",
        "constant",
        'TRAP: Function((), ("item", ("tuple",), _lit(0))),',
    ): (
        EQUIVALENT,
        "every index of the empty tuple traps",
    ),
    (
        "semiroh/examples/vm.py",
        "constant",
        '("INT", ("seq", ("add", _top(), _lit(0)), _next(_STACK))),',
    ): (
        EQUIVALENT,
        "the addition checks integer kind and its numeric result is discarded",
    ),
    (
        "semiroh/bytecode.py",
        "boolean",
        "if type(left) in _PRIMITIVES and type(right) in _PRIMITIVES:",
    ): (
        EQUIVALENT,
        "the altered fast-path choice falls through to the agreeing slow path",
    ),
    (
        "semiroh/bytecode.py",
        "compare",
        "if type(left) in _PRIMITIVES and type(right) in _PRIMITIVES:",
    ): (
        EQUIVALENT,
        "the altered fast-path choice falls through to the agreeing slow path",
    ),
    (
        "semiroh/fold.py",
        "constant",
        "@dataclass(frozen=True)",
    ): (
        EQUIVALENT,
        "_Constant instances are never mutated",
    ),
    (
        "semiroh/fold.py",
        "return",
        "return entity",
    ): (
        EQUIVALENT,
        "the returned node matters only when the containing if is itself "
        "constant, in which case that if is replaced as a whole",
    ),
    (
        "semiroh/lang.py",
        "constant",
        "@dataclass(frozen=True, eq=False)",
    ): (
        EQUIVALENT,
        "Function defines explicit __eq__ and __hash__, so the dataclass "
        "eq flag does not generate replacement equality methods",
    ),
    (
        "semiroh/lang.py",
        "arithmetic",
        "current.generation + 1,",
    ): (
        EQUIVALENT,
        "generation is freshness-only; its exact numeric increment is not "
        "observable semantic identity",
    ),
    (
        "semiroh/matching.py",
        "constant",
        "size = 1",
    ): (
        EQUIVALENT,
        "the mutation scales every subtree size equally, preserving grouping "
        "and ordering",
    ),
    (
        "semiroh/lang.py",
        "compare",
        "if index is None:",
    ): (
        EQUIVALENT,
        "all current semantic callers supply the relation index",
    ),
    (
        "semiroh/lang.py",
        "constant",
        "generation += 1",
    ): (
        EQUIVALENT,
        "generation is freshness-only; its exact numeric increment is not "
        "observable semantic identity",
    ),
    (
        "semiroh/lang.py",
        "constant",
        "0 if current is None else current.generation + 1,",
    ): (
        EQUIVALENT,
        "generation is freshness-only; its exact numeric increment is not "
        "observable semantic identity",
    ),
    (
        "semiroh/matching.py",
        "constant",
        "keys.append((False, item))",
    ): (
        EQUIVALENT,
        "the flag only separates integer shape keys from EntityID endpoint "
        "keys, whose types cannot compare equal",
    ),
    (
        "semiroh/lang.py",
        "constant",
        'f"let name must be a non-empty string, got {rest[0]!r}",',
    ): (
        UNSPECIFIED,
        "exact diagnostic wording is not part of the language contract",
    ),
}
