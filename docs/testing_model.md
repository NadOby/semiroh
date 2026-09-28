# Testing Model

This document defines the role of the executable semantic test corpus in SEMIROH.

The Python implementation is an executable semantic reference model. Tests
validate semantic behaviour and architectural invariants against that model.

## 1. Purpose

The test corpus exists to expose contradictions in the semantic model.

It is not primarily a collection of implementation tests.

A test should establish a property of the semantic model wherever possible.

Implementation details may be tested when they themselves are part of a
semantic contract.

## 2. Semantic tests

Semantic tests should verify properties such as:

- immutable state behaviour;
- identity distinctions;
- semantic equality;
- version identity;
- reference validity;
- cross-state reference behaviour;
- explicit reference transfer;
- transformation mappings;
- ownership invariants;
- canonicalization;
- state identity;
- creation and disappearance.

Tests should use the public semantic operations rather than reaching into
implementation internals unless the internal detail is itself the behaviour
being specified.

## 3. Negative tests

Negative tests are important because invalid semantic states and operations
must not silently acquire arbitrary meanings.

Examples include:

- stale references;
- cross-state references;
- invalid ownership;
- ownership cycles;
- invalid mappings;
- duplicate mapping records;
- missing mapping destinations;
- ambiguous continuity;
- missing continuity.

A negative test should assert the semantic failure category whenever that
category is defined.

Tests should not use unnecessarily broad exception expectations.

For example, when the semantic contract requires an ambiguous mapping error,
the test should assert `AmbiguousEntityMapping`, not generic `Exception`.

## 4. Transformation tests

Transformation tests should cover semantic cardinalities:

    one -> zero
    one -> one
    one -> many
    many -> one
    many -> many

They should also cover:

- explicit creation;
- explicit disappearance;
- replacement of semantic value;
- continuity versus semantic equality;
- mapping validation;
- canonical mapping order;
- destination identity;
- state identity independence from mappings.

Transformation tests should not assume properties that have not been specified,
such as exact historical `StateID` restoration by an inverse transformation.

## 5. Reference-transfer tests

Reference-transfer tests should establish:

- references are state-local;
- references are version-pinned;
- valid references transfer through explicit mappings;
- stale references are rejected;
- references from another state are rejected;
- disappearance prevents transfer;
- split mappings are ambiguous;
- destination references use the destination value version;
- transfer is one-step;
- transformation chains require explicit intermediate transfer.

## 6. Ownership tests

Ownership tests should establish:

- at most one owner;
- no self ownership;
- no ownership cycles;
- owners and children must exist;
- ownership ordering is canonical;
- ownership affects semantic state identity;
- ordinary references can cycle independently of ownership;
- recursive destruction removes an ownership subtree.

Ownership tests should distinguish ownership semantics from transformation
continuity.

## 7. Identity tests

Identity tests should distinguish:

    EntityID
    VersionID
    StateID
    semantic equality

Important properties include:

- changing content can change `VersionID`;
- identical semantic content can produce identical `VersionID`;
- identical state content can produce identical `StateID`;
- different entities may contain semantically equal content;
- entity identity does not imply semantic equality.

## 8. Canonicalization tests

Canonicalization tests should verify that semantically equivalent unordered
representations receive the same canonical representation and semantic
identity.

They should not accidentally encode arbitrary implementation ordering as
semantic meaning.

Where ordering itself is semantic, the test should establish that explicitly.

## 9. Regression tests

A regression test is justified when a previously exposed semantic failure
represents a property that should remain stable.

The test should encode the underlying semantic invariant rather than merely
reproducing the exact implementation accident that caused the original bug.

## 10. Test anti-patterns

The corpus should avoid:

- generic exception assertions when a specific semantic error exists;
- asserting private implementation structure without semantic justification;
- modifying production semantics solely to satisfy a test;
- testing unspecified behaviour as though it were settled;
- duplicate tests that provide no additional semantic coverage;
- tests whose only purpose is increasing coverage statistics.

Passing tests are not evidence that the architecture is correct by themselves.

They are evidence only for the properties actually tested.

## 11. Test completeness

A feature should not be considered semantically specified merely because its
current implementation has tests.

Tests and specification have different roles:

    specification
        defines intended semantics

    implementation
        provides executable behaviour

    tests
        check that implementation satisfies selected semantic properties

A test may expose a missing specification decision rather than resolve that
decision automatically.

## 12. Property-based testing

Property-based testing should be used where generated cases can expose
counterexamples that are difficult to construct manually.

It is particularly suitable for:

- canonicalization;
- identity stability;
- immutable state evolution;
- mapping cardinalities;
- ownership forests;
- transformation composition;
- semantic equality.

Property-based tests must still be derived from explicit semantic properties.

Random generation must not manufacture semantic rules.

The current property tests (`tests/test_properties.py`) use seeded generators
from the standard library, so every failure is reproducible from its reported
seed and the test suite has no third-party dependencies.

A particularly useful property compares two independent parts of the model.
For example, following a reference one transition at a time must agree with
the result of continuity composition.

## 13. Formal verification

The executable test corpus is not a substitute for eventual formal semantics
or proofs.

Formal verification may later establish selected high-value invariants.

The Python model remains useful as an exploratory and regression-testing
environment even after formal models exist.

## 14. Current test architecture

The test suite is organized thematically under `tests/`.

Current semantic areas include:

- identity;
- canonicalization;
- references;
- state;
- ownership;
- lifecycle;
- transformations;
- transformation mapping;
- reference transfer;
- transformation composition;
- cross-cutting semantic properties.

The test organization should follow semantic concerns rather than individual
implementation modules where those differ.

## 15. Design principle

Tests are executable checks on the semantic model.

They should constrain implementation behaviour without silently becoming the
source of semantics themselves.
