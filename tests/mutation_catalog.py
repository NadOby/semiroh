"""Mutation targets and reviewed survivor classifications."""

from __future__ import annotations

from tests.mutation import MutationKey


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


# Python files intentionally not mutation targets. This makes omissions
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


# Exact reviewed survivors.
#
# Key:
#
#     (
#         target path,
#         mutation kind,
#         complete stripped source line,
#         occurrence among sites with that same kind and source line,
#     )
#
# Unlike a global mutation index or source line number, this identity survives
# unrelated edits elsewhere in the file. The occurrence distinguishes multiple
# mutable constructs represented by the same source line.
#
# These classifications migrate the useful knowledge from the pre-Task-18
# mutation catalog. Broad historical entries that covered several sites are
# split where their reasoning applies independently.
#
# One historical entry is deliberately not migrated:
#
#     @dataclass(frozen=True, eq=False) in lang.py
#
# Its old reason explicitly called it an open test gap, not an equivalent
# mutation. Test gaps are fixed with regressions rather than classified here.
#
# The historical self-hosting quote-template entry is also omitted for now:
# formatting changes split its old broad source line into several sites, and
# the old record does not identify which current constant actually survived.
# A broad campaign may rediscover it under an exact key, at which point that
# exact site can be reviewed.
#
# A semantic test gap is never added here.
SURVIVORS: dict[
    MutationKey,
    tuple[str, str],
] = {
    (
        "semiroh/bytecode.py",
        "constant",
        "_lowered = 0",
        0,
    ): (
        EQUIVALENT,
        "the counter is only compared as a difference",
    ),
    (
        "semiroh/bytecode.py",
        "constant",
        "may_activate: bool = False,",
        0,
    ): (
        EQUIVALENT,
        "the relevant callers pass may_activate explicitly",
    ),
    (
        "semiroh/runtime.py",
        "return",
        'return f"Version({self.id.value[:12]}, holds={len(self._holds)})"',
        0,
    ): (
        UNSPECIFIED,
        "Version repr text is diagnostic and not part of the semantic contract",
    ),
    (
        "semiroh/runtime.py",
        "constant",
        'return f"Version({self.id.value[:12]}, holds={len(self._holds)})"',
        0,
    ): (
        UNSPECIFIED,
        "the number of StateID characters shown by repr is diagnostic only",
    ),
    (
        "semiroh/examples/self_hosting.py",
        "constant",
        "IntRange(0, 100),",
        1,
    ): (
        EQUIVALENT,
        "the upper bound of the instrumentation cell is never reached",
    ),
    (
        "semiroh/examples/vm.py",
        "constant",
        '("item", ("tuple",), _lit(0)),',
        0,
    ): (
        EQUIVALENT,
        "any index of the empty tuple traps",
    ),
    (
        "semiroh/examples/vm.py",
        "constant",
        '("add", _top(), _lit(0)),',
        0,
    ): (
        EQUIVALENT,
        "adding any int performs the operand check and the sum is discarded",
    ),
    (
        "semiroh/machine.py",
        "constant",
        "(_RETURN, 0, False, None, activation)",
        1,
    ): (
        EQUIVALENT,
        "the tail flag of the RETURN sentinel is never read",
    ),
    (
        "semiroh/machine.py",
        "boolean",
        "if type(left) in _PRIMITIVES and type(right) in _PRIMITIVES:",
        0,
    ): (
        EQUIVALENT,
        "the primitive branch is only a fast path; canonical comparison agrees",
    ),
    (
        "semiroh/machine.py",
        "compare",
        "if type(left) in _PRIMITIVES and type(right) in _PRIMITIVES:",
        0,
    ): (
        EQUIVALENT,
        "changing the left fast-path guard only changes which equivalent path runs",
    ),
    (
        "semiroh/machine.py",
        "compare",
        "if type(left) in _PRIMITIVES and type(right) in _PRIMITIVES:",
        1,
    ): (
        EQUIVALENT,
        "changing the right fast-path guard only changes which equivalent path runs",
    ),
    (
        "semiroh/fold.py",
        "constant",
        "@dataclass(frozen=True)",
        0,
    ): (
        EQUIVALENT,
        "nothing mutates _Constant instances",
    ),
    (
        "semiroh/fold.py",
        "return",
        "return entity",
        0,
    ): (
        EQUIVALENT,
        "the returned folded node is only consumed in a case where the enclosing "
        "constant if would already have folded as a whole",
    ),
    (
        "semiroh/lang.py",
        "compare",
        "if index is None:",
        0,
    ): (
        EQUIVALENT,
        "the relevant callers pass an index",
    ),
    (
        "semiroh/lang.py",
        "constant",
        "generation += 1",
        0,
    ): (
        EQUIVALENT,
        "the generation only has to differ from generations already taken",
    ),
    (
        "semiroh/lang.py",
        "arithmetic",
        "0 if current is None else current.generation + 1,",
        0,
    ): (
        EQUIVALENT,
        "the generation only has to differ from generations already taken",
    ),
    (
        "semiroh/lang.py",
        "constant",
        "0 if current is None else current.generation + 1,",
        0,
    ): (
        EQUIVALENT,
        "a newly created function only needs an available generation",
    ),
    (
        "semiroh/lang.py",
        "constant",
        "0 if current is None else current.generation + 1,",
        1,
    ): (
        EQUIVALENT,
        "an edited function only needs a generation different from those taken",
    ),
    (
        "semiroh/lang.py",
        "constant",
        'f"let name must be a non-empty string, got {rest[0]!r}",',
        0,
    ): (
        UNSPECIFIED,
        "the selected value appears only in diagnostic text",
    ),
    (
        "semiroh/matching.py",
        "constant",
        "size = 1",
        0,
    ): (
        EQUIVALENT,
        "starting at two doubles every subtree size, preserving grouping and order",
    ),
    (
        "semiroh/matching.py",
        "constant",
        "keys.append((False, item))",
        0,
    ): (
        EQUIVALENT,
        "the flag separates shape numbers from endpoint EntityIDs; their value "
        "types cannot collide",
    ),
}
