# Reference Model

This document defines the current semantic model of references in SEMIROH.

A reference is a state-local, version-pinned handle to one semantic value.

## 1. Reference identity

A reference contains exactly three semantic components:

    StateID
    EntityID
    VersionID

Conceptually:

    Reference(S, E, V)

These components identify:

- the state in which the reference is valid;
- the conceptual entity being referenced;
- the exact semantic value version expected there.

## 2. Reference validity

A reference is valid against a state only when all three conditions hold:

1. the reference's `StateID` equals the state's `StateID`;
2. the referenced `EntityID` exists in the state;
3. the reference's `VersionID` equals the current version of that entity.

Failure of the state condition is a cross-state reference.

Failure of the entity condition means the entity is absent.

Failure of the version condition means the reference is stale.

## 3. State locality

References do not automatically follow entity identity across states.

Given:

    Reference(S₀, E, V)
    S₁ contains E

the reference remains a reference into `S₀`.

The existence of `E` in `S₁` does not rebind the reference.

Cross-state transfer must be explicit.

## 4. Reference transfer

Reference transfer follows an explicit continuity mapping through one
transformation.

Conceptually:

    Reference(S₀, E, V)
          +
    TransformResult(S₀ -> S₁)
          |
          v
    Reference(S₁, E', V')

Transfer is therefore a one-step operation.

Before following the mapping, the source reference must be valid against the
transformation's source state.

## 5. Transfer preconditions

The transfer operation requires:

    reference.state == transformation.source.id

The referenced entity must exist in the source state.

The reference version must equal the current source value version.

The three cases have distinct meanings:

    wrong StateID
        -> CrossStateReference

    absent EntityID
        -> missing source entity error

    wrong VersionID
        -> StaleReference

Only after these checks is the transformation mapping consulted.

## 6. Continuity result

The explicit mapping determines the transfer result.

A source entity mapped to no destinations cannot produce a destination
reference.

A source entity mapped to exactly one destination produces a destination
reference.

A source entity mapped to multiple destinations cannot be transferred without
an explicit choice.

The corresponding semantic outcomes are:

    zero destinations
        -> MissingEntityMapping

    one destination
        -> successful transfer

    multiple destinations
        -> AmbiguousEntityMapping

## 7. Destination version

A successful transfer produces a reference to the current value version of the
destination entity.

Therefore the destination reference is not required to preserve the source
`VersionID`.

Conceptually:

    Reference(S₀, E, V₀)
          |
          | continuity
          v
    Reference(S₁, E', V₁)

where `V₁` is the version currently present in `S₁`.

## 8. Transfer versus rebinding

Reference transfer and rebinding are different operations.

Transfer follows an explicitly declared continuity relation.

Rebinding explicitly chooses a destination entity without claiming that it is
the continuation of the source reference.

Conceptually:

    transfer
        = follow declared continuity

    rebind
        = explicitly choose a destination target

Rebinding therefore does not establish continuity.

Because rebinding asserts no relation to the original reference, the original
reference is neither validated nor consulted. A stale, cross-state, or
untransferable reference can be rebound; that is usually why rebinding is
needed.

## 9. One-step composition

Transformations are not implicitly composable for reference transfer.

Given:

    S₀ -> S₁
    S₁ -> S₂

a reference in `S₀` must be transferred first through the `S₀ -> S₁`
transformation and then through the `S₁ -> S₂` transformation.

The second transformation cannot directly consume the original `S₀`
reference.

This prevents ordinary mappings from becoming an implicit global history
graph.

## 10. Creation

A destination entity with no incoming mapping is a newly created destination
entity.

There is no synthetic source entity for creation.

Therefore a source reference cannot be transferred into a purely created
destination entity unless an explicit source-to-destination mapping exists.

## 11. Current implementation model

The Python reference model currently provides:

    Reference
    make_reference()
    project_entity()
    State.reference()
    State.resolve()
    transfer_reference()
    rebind_reference()

The exception types currently distinguish:

    CrossStateReference
    StaleReference
    MissingEntityMapping
    AmbiguousEntityMapping

These distinctions reflect semantic error categories rather than requiring a
particular Python exception hierarchy.

## 12. Unresolved areas

The following remain open:

- borrowing;
- alias analysis;
- lifetime analysis;
- raw pointer semantics;
- capability-backed references;
- references into moved representations;
- reference semantics in the eventual generalized graph/hypergraph model.

## 13. Design principle

A reference is not an ambient name and not merely an `EntityID`.

It is a capability to resolve one exact value in one exact semantic state.

Continuity across states must therefore be explicitly declared and explicitly
followed.
