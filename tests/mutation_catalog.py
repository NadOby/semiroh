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
#         mutation engine site index,
#         mutation kind,
#         source line number,
#         complete stripped source line,
#     )
#
# The index makes the site unambiguous even when several mutable constructs
# occur on one source line. Kind, line number and source text form a fingerprint
# checked against the current source, so stale classifications fail closed.
#
# The old survivor list was intentionally reset because its keys identified
# only (target, kind, source line) and could cover multiple mutation sites.
#
# Current survivors are rediscovered by mutation campaigns and classified
# individually.
#
# A semantic test gap is never added here. It receives a regression test and
# the mutant must then be killed.
SURVIVORS: dict[
    MutationKey,
    tuple[str, str],
] = {}
