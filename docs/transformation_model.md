# Transformation Model

This document defines the current semantic contract for transformations in
SEMIROH.

It is normative where stated. Implementation details that are not part of the
semantic contract must not be inferred from the Python reference
implementation.

## 1. Transformation definitions

A transformation definition is an immutable semantic value describing a
potential state transition.

A definition is independent of a particular source `StateID`.

Conceptually:

    TransformationDefinition
        =
        semantic changes
        +
        explicit continuity mappings

A definition may therefore be reused against multiple compatible source
states.

Application is a separate operation:

    TransformationDefinition
        +
    SourceState
        →
    TransformationResult

The definition describes the intended semantic changes and explicit
continuity information.

The result describes what happened when that definition was applied to one
particular source state.

The current definition does not yet include contracts, constraints, effects,
capabilities, or provenance as semantic components. Those are separate
models whose interaction with transformations remains to be specified.

## 2. State transitions

A transformation takes one immutable semantic state and produces another
immutable semantic state.

Conceptually:

    S₀ → S₁

The source state remains unchanged. The destination is a distinct immutable
state.

A transformation result consists conceptually of:

    source state
    destination state
    explicit entity continuity mapping
    optional provenance

Continuity mapping and provenance describe the transition. They are not
properties of either state.

## 3. Transformation changes

A transformation definition may contain immutable entity changes.

Each change identifies:

    EntityID
    semantic Value

The changed value must belong to the entity identified by the change.

Changes are canonically ordered by `EntityID`.

A definition cannot contain multiple changes for the same entity.

Applying a change replaces the value associated with that entity in the
destination state.

A change does not by itself establish identity continuity.

For example:

    Entity E : value A
        →
    Entity E : value B

changes the semantic value while retaining the entity in the destination.

Whether `E` is considered continuous across the transition is determined by
the explicit continuity mapping.

## 4. Partial transformation semantics

A transformation definition is a partial description of changes to a source
state.

For every entity in the source state, its treatment is determined as follows:

    explicitly mapped
        →
    continuity or disappearance is declared by the mapping

    not explicitly mapped
        →
    the entity is preserved in the destination state

Preservation of an entity in the destination does not itself assert identity
continuity.

Therefore an unmentioned entity may remain present with the same `EntityID`
and value while having no `EntityMapping` in the transformation result.

This distinction is intentional:

    state preservation
        ≠
    declared continuity

The absence of a mapping must not manufacture continuity.

For an entity explicitly changed but not mapped:

    existing source entity
        →
    changed destination value
    with no declared continuity mapping

For an entity explicitly changed and mapped:

    existing source entity
        →
    changed destination value
    with explicitly declared continuity

For an entity explicitly mapped to zero destinations:

    source entity
        →
    disappearance

An explicit disappearance mapping therefore takes precedence over a value
change for the same source entity: the entity is absent from the destination.

More generally, the presence of an explicitly mapped source entity in the
destination is decided by the mappings alone (see section 6). A value change
for a source entity that the mappings remove from the destination has no
effect.

## 5. Transformation mappings

A transformation definition may contain explicit continuity mappings.

A definition-level mapping is state-independent:

    source entity → destination entities

The concrete mapping produced by applying the definition is associated with
the actual source `StateID`.

Each source entity may occur at most once in the definition's mapping relation.

Destination entities are canonically ordered.

The mapping cardinality determines the declared continuity relationship:

    0 destinations
        disappearance

    1 destination
        unambiguous continuity

    >1 destinations
        split / non-unique continuity

Multiple source entities may map to the same destination entity.

Therefore the relation supports:

    one → zero
    one → one
    one → many
    many → one
    many → many

The mapping is a continuity relation, not an assertion of semantic equality.

## 6. Applying a transformation definition

Applying a definition validates its mapping against the source and produced
destination state.

Every mapping source must identify an entity present in the source state.

Every non-empty mapping destination must identify an entity present in the
destination state.

Destination entities may be introduced by the definition's changes.

A source mapped to an empty destination tuple disappears from the destination
state.

A source mapped to one or more destinations is present in the destination
state if and only if it is itself a destination of some mapping in the same
definition. Therefore:

    A → A
        A remains present

    A → B
        A is absent (B continues A)

    A → B
    B → A
        both remain present (a swap)

    A → B
    B → C
        A is absent; B and C are present (a shift)

An explicit disappearance is not overridden by appearing as a destination.
A mapping whose destinations include an entity explicitly mapped to zero
destinations therefore names an entity absent from the destination state and
is invalid.

A source entity that is not explicitly mapped remains in the destination
state, subject to any value change explicitly specified for that entity.

Destination validation is performed against the resulting destination state,
after changes have been applied and mapped sources have been removed.

A destination entity with no incoming mapping is a newly created destination
entity.

Creation therefore has no synthetic source entity:

    ∅ → new entity

Creation is not identity transfer from an implicit predecessor.

A transformation result contains only explicitly declared continuity mappings.
It does not contain implicit mappings for entities merely because they happen
to exist in both source and destination states.

## 7. Plain transformations

A transformation without an explicit continuity mapping changes semantic state
content without asserting which entities are continuous across the transition.

`transform(state, changes)` therefore establishes only:

    state content before
    →
    state content after

It does not establish identity continuity.

A caller must not infer continuity merely because the same `EntityID` appears
in both states.

## 8. References

A `Reference` is bound to:

    StateID
    EntityID
    VersionID

A reference therefore identifies a particular version of an entity in a
particular state.

A reference is valid only when all three components agree with the state.

Reference resolution against a state requires:

1. the reference's `StateID` to equal the state's `StateID`;
2. the referenced entity to exist in that state; and
3. the reference's `VersionID` to equal the current version of that entity.

## 9. Reference transfer

Reference transfer is strictly state-local and one-step.

A reference may be transferred only through a transformation whose source
state is exactly the state named by the reference.

The transfer operation therefore has the form:

    Reference(S₀, E, V)
        +
    Transformation(S₀ → S₁)
        →
    Reference(S₁, E', V')

The reference must first be valid against the transformation's source state.

The preconditions are:

1. `reference.state == transformation.source.id`;
2. the referenced entity exists in the transformation's source state; and
3. the reference's version equals the current version of that source entity.

Violations have distinct meanings:

    wrong StateID
        → CrossStateReference

    absent source EntityID
        → missing source entity error

    wrong VersionID
        → StaleReference

After these checks, the explicit transformation mapping determines whether the
reference can be transferred.

A source mapped to zero destinations cannot produce a destination reference.

A source mapped to exactly one destination produces a reference to that
destination entity.

A source mapped to multiple destinations cannot be transferred without an
explicit choice and therefore produces `AmbiguousEntityMapping`.

An unmentioned source entity has no declared continuity mapping and therefore
cannot be transferred through the transformation.

The resulting reference is bound to the destination state and the current
version of the mapped destination entity.

## 10. Transformation composition

Transformation composition must be distinguished from application of one
transformation after another.

Given:

    S₀ → S₁
    S₁ → S₂

a reference in `S₀` must be transferred through the first transformation before
it can be transferred through the second:

    Reference(S₀)
        →
    Reference(S₁)
        →
    Reference(S₂)

The second transformation cannot directly consume the `S₀` reference.

The current composition operation composes explicit continuity information,
not complete transformation semantics.

In particular, composing two transformation definitions does not currently
compose their entity changes into a new set of semantic state changes.

Therefore the following are distinct questions:

    continuity composition
        →
    how explicitly mapped entities relate across both transitions

    semantic transformation composition
        →
    what complete destination state results from applying both transformations

The first is currently implemented.

The second remains unspecified.

A composition result therefore must not be interpreted as a complete
replacement for a transformation definition unless and until full semantic
composition is formally defined.

## 11. Composition and unknown continuity

Continuity composition can produce three semantic situations for a source
entity:

    known continuity
    known disappearance
    unknown

`Unknown` means that the available explicit continuity information is
insufficient to establish the final destination.

It does not mean disappearance.

For example:

    A → B
    B preserved without explicit mapping

does not establish:

    A → B

because preservation is not an explicit continuity declaration.

The composed result is therefore unknown for `A`.

Likewise:

    A → B
    B → ∅

establishes:

    A → ∅

because disappearance is explicitly declared.

Unknown continuity must remain distinct from both continuity and disappearance.

Already-unknown continuity remains unknown through later composition unless
later information explicitly resolves the relevant relation.

The complete composition semantics are specified separately in
`transformation_composition.md` and
`transformation_composition_api.md`.

## 12. Rebinding

Rebinding is distinct from reference transfer.

Reference transfer preserves an explicitly asserted continuity relation.

Rebinding explicitly chooses an entity in a destination state without claiming
that the chosen entity is the continuation of the original reference.

Conceptually:

    transfer
        =
    follow declared continuity

    rebind
        =
    explicitly choose a new state-local target

Rebinding therefore does not preserve conceptual identity.

## 13. Ownership

Ownership is part of semantic state content.

Transformation mappings do not implicitly modify ownership.

When no destination ownership relation is explicitly supplied, the
transformation preserves the existing ownership relation subject to removal
of entities that disappear.

An entity disappearing from the destination removes ownership edges involving
that entity.

This does not imply recursive deletion of its owned descendants.

Recursive subtree destruction is a separate state operation.

When explicit destination ownership is supplied, it defines the destination
ownership relation directly and must refer only to destination entities.

Ownership and ordinary entity continuity are therefore separate relations.

## 14. State identity

State identity is derived from semantic state content.

Transformation mappings do not contribute to `StateID`.

Transformation provenance does not contribute to `StateID`.

Therefore two transformations may produce semantically identical destination
states while carrying different mappings or provenance, without producing
different state identities for that reason.

Conversely, changing semantic state content or ownership changes the state
identity when the resulting semantic content differs.

## 15. Canonicalization and determinism

The representation of transformation mappings is canonical.

For a mapping:

    source → (destination₁, destination₂, ...)

destination entities are stored in canonical `EntityID` order.

Mapping records are likewise stored in canonical source-entity order.

Equivalent mappings expressed in different input orders therefore produce the
same canonical mapping representation.

This ordering is semantic determinism, not an assertion that the ordering
itself represents an additional relationship between entities.

## 16. Mapping validation

A valid transformation mapping must satisfy:

- every mapping belongs to the transformation's source state;
- every mapping source exists in the source state;
- each source entity occurs at most once in the mapping relation;
- destination entities are unique within each mapping;
- mapped destination entities exist in the destination state;
- destination entity lists are canonically ordered;
- mapping records are canonically ordered.

Invalid transition mappings must be rejected rather than silently normalized
into a different semantic relation, except where canonical ordering is an
explicitly supported normalization.

## 17. Provenance

Provenance is metadata associated with a transformation.

It is not semantic state content and does not affect `StateID`.

The current model does not require provenance to form a globally traversable
history graph.

A future provenance model may define richer historical relationships, but such
relationships must not be inferred from ordinary entity mappings.

## 18. Reversibility

A transformation mapping describes forward continuity.

A forward mapping does not imply that the transformation is reversible.

In particular:

    one → many
    many → one
    one → zero

may lose information required to uniquely reconstruct the source.

A transformation may be lossless, lossy, or otherwise constrained by additional
semantics that have yet to be specified.

Exact state restoration, including restoration of a historical `StateID`, is
not implied merely by applying an apparent inverse transformation.

A future reversible-transformation model must specify its own requirements for
invertibility and information preservation.

## 19. Semantic versus implementation concerns

The following are semantic requirements:

- immutable source and destination states;
- explicit continuity mappings;
- partial transformation semantics;
- explicit zero/one/many mapping cardinality;
- explicit creation and disappearance;
- preservation of unmentioned entities without implicit continuity;
- state-local, version-aware reference transfer;
- distinction between transfer and rebinding;
- separation of ownership from continuity;
- state identity independence from mappings and provenance;
- deterministic canonical mapping representation;
- distinction between known continuity, known disappearance, and unknown
  continuity during current mapping composition.

The following are implementation choices unless separately specified:

- Python class structure;
- exception inheritance hierarchy beyond the semantic distinctions required
  above;
- internal container types;
- serialization implementation;
- hashing implementation;
- helper-function decomposition.

Tests must target the semantic contract rather than incidental implementation
details.

## 20. Current implementation status

The Python reference model currently implements:

- immutable transformation definitions;
- immutable entity changes;
- explicit continuity mappings;
- transformation application;
- transformation results;
- reference transfer;
- explicit rebinding;
- ownership handling during transformation;
- continuity composition;
- propagation of unknown continuity during composition.

The current composition implementation composes continuity mappings only.

It does not yet provide full semantic composition of entity changes and
resulting state content.

The following remain future work:

- first-class transformation semantic identity;
- full transformation equality;
- full semantic composition;
- formal lossless/lossy semantics;
- transformation deltas and distance measures;
- richer provenance/history semantics;
- generalized graph/hypergraph interaction;
- persistent representation of transformation definitions.

## 21. Current unresolved areas

The following are intentionally not fully specified yet:

- whether a transformation is itself a first-class semantic value beyond its
  current definition/result distinction;
- transformation identity and equality;
- formal composition of complete transformation semantics;
- formal composition of entity changes;
- formal distinction between lossless and lossy transformations;
- transformation deltas and distance measures;
- richer provenance/history semantics;
- interaction with the eventual generalized graph/hypergraph model;
- whether transformation definitions should have their own persistent semantic
  representation;
- interaction between transformations and contract guarantees;
- formal constraint-preservation semantics.

These questions must be resolved before they are treated as stable semantics.

## 22. Design principle

A transformation is an explicit semantic transition between immutable states.

A transformation definition describes only the entities it explicitly changes
or maps. Entities not mentioned by the definition are preserved as state
content, but their continuity is not implicitly declared.

An entity's continuity across a transition exists only where the transition
explicitly declares it.

A reference follows one such declaration at a time.

Composition currently combines explicit continuity information only. It does
not imply that complete semantic transformation composition has been defined.

Neither `EntityID` reuse, structural similarity, state adjacency, preservation
of state content, nor historical provenance is sufficient to manufacture
continuity that the transformation did not declare.
