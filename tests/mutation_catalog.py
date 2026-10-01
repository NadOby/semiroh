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
# Generation allocation entries from the historical catalog are deliberately
# not migrated: graph_form.md specifies exact generation semantics, so changing
# generation 0, next-generation allocation, or collision advancement is a
# semantic identity change and must be killed by regression tests.
#
# The historical bytecode _lowered initial-value entry is also not classified:
# bytecode.md specifies lowered_count() as an absolute process-start count, so
# changing its initial value is a semantic test gap now covered by a regression.
#
# A semantic test gap is never added here.
SURVIVORS: dict[
    MutationKey,
    tuple[str, str],
] = {
    (
        "semiroh/bytecode.py",
        "constant",
        "may_activate: bool = False,",
        0,
    ): (
        UNSPECIFIED,
        "bytecode.run is an internal execution wrapper; the language-level "
        "activation-capability contract is specified and tested through "
        "semiroh.lang.run",
    ),
    (
        "semiroh/closures.py",
        "boolean",
        "if owner is None or body is None:",
        0,
    ): (
        EQUIVALENT,
        "if exactly one decoded identity is absent, Closure construction "
        "rejects that non-EntityID and closure_value returns None through "
        "the same validation path",
    ),
    (
        "semiroh/constraints.py",
        "constant",
        "@dataclass(frozen=True, eq=False, init=False)",
        5,
    ): (
        EQUIVALENT,
        "this occurrence is AllOf's init=False flag; AllOf defines its own "
        "__init__, so changing dataclass init to True does not generate or "
        "replace the explicit constructor",
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
        "semiroh/ownership.py",
        "constant",
        "status[visited] = 2",
        0,
    ): (
        EQUIVALENT,
        "only status value 1 means on the current walk; every other stored "
        "value means the entity was already visited, so changing 2 to 3 "
        "does not alter cycle detection",
    ),
    (
        "semiroh/reconcile.py",
        "return",
        "return {}",
        1,
    ): (
        EQUIVALENT,
        "_graph_links is called only after function_at identified the same "
        "entity as a graph-form function; that implies _definition_of succeeds, "
        "so this missing-definition return cannot affect reconciliation",
    ),
    (
        "semiroh/reconcile.py",
        "return",
        "return dict(definition.links)",
        0,
    ): (
        EQUIVALENT,
        "returning None only causes reconcile to submit a redundant link-table "
        "edit; define compares the reconstructed definition with the current "
        "value and the resulting semantic state and mappings are unchanged",
    ),
    (
        "semiroh/state.py",
        "constant",
        "8,",
        1,
    ): (
        UNSPECIFIED,
        "the byte width used to delimit ownership count in the Python StateID "
        "encoding is an implementation representation detail; identity is "
        "specified by semantic content, not this particular byte layout",
    ),
    (
        "semiroh/syntax.py",
        "constant",
        "+ self.expr(value, locs, 2, True)[0]",
        1,
    ): (
        EQUIVALENT,
        "syntax rendering gives special behaviour only to modes 0 and 1; "
        "changing this internal mode from 2 to 3 therefore follows the same "
        "rendering and rejection paths for every expression",
    ),
    (
        "semiroh/values.py",
        "constant",
        "@dataclass(frozen=True, eq=False)",
        1,
    ): (
        EQUIVALENT,
        "Value defines its own __eq__ and __hash__, so enabling dataclass "
        "equality generation does not replace those explicit methods",
    ),
    (
        "semiroh/examples/self_hosting.py",
        "constant",
        "IntRange(0, 100),",
        1,
    ): (
        UNSPECIFIED,
        "the instrumentation cell's upper bound is example scaffolding rather "
        "than part of the embedded compiler's semantic contract",
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
    (
        "semiroh/matching.py",
        "constant",
        "keys.append((True, shape))",
        0,
    ): (
        EQUIVALENT,
        "the flag separates subtree shape integers from external endpoint "
        "EntityIDs; changing the flag cannot create a key collision because "
        "those payload types are disjoint",
    ),
}
