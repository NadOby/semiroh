# Transformation Composition

This document defines the current semantics of composing transformation
continuity relations in SHEAR.

The current composition operation composes explicit continuity information
only. It does not yet define full semantic composition of transformation
changes or complete state transitions.

## 1. Scope

Given two sequential transformations:

    S₀ → S₁
    S₁ → S₂

composition determines what can be established about continuity from entities
in `S₀` to entities in `S₂`.

Conceptually:

    T₁ : S₀ → S₁
    T₂ : S₁ → S₂

    compose(T₁, T₂)
        →
    continuity information from S₀ to S₂

The current composition operation does not construct the complete semantic
state transition obtained by applying `T₁` and then `T₂`.

In particular, entity changes are not currently composed into a new
`TransformationDefinition`.

## 2. Explicit continuity only

Composition follows explicit continuity mappings.

It does not infer continuity from:

- preservation of an entity;
- equal `EntityID`s;
- equal semantic values;
- structural similarity;
- state adjacency;
- provenance;
- historical knowledge.

For example:

    A → B
    B is preserved by T₂

does not establish:

    A → B

because T₂ contains no explicit continuity mapping for `B`.

The composed result for `A` is therefore `Unknown`.

## 3. Composition inputs

The first composition input may be either:

    TransformationDefinition

or:

    CompositionResult

The second composition input may likewise be either:

    TransformationDefinition

or:

    CompositionResult

A `TransformationDefinition` contains explicit mappings.

A `CompositionResult` contains previously composed mappings and sources whose
continuity is already known to be unknown.

This allows unknown information to propagate through multiple composition
steps.

## 4. Known continuity

Suppose:

    T₁:
        A → B

    T₂:
        B → C

Both mappings are explicit.

Composition establishes:

    A → C

The result contains a mapping for `A` whose destination is `C`.

The intermediate entity `B` is not retained as part of the composed
relationship.

## 5. Known disappearance

Suppose:

    T₁:
        A → B

    T₂:
        B → ∅

The disappearance is explicit.

Composition establishes:

    A → ∅

This is a known disappearance, not an unknown result.

## 6. Unknown continuity

Suppose:

    T₁:
        A → B

and `T₂` contains neither:

    B → C

nor:

    B → ∅

Then the final treatment of `A` cannot be established from explicit
continuity information.

The composed result records:

    A -> Unknown

Unknown is distinct from disappearance.

The implementation represents this through the `unknown_sources` collection
rather than by encoding unknown as an empty destination tuple.

Therefore:

    empty mapping
        =
    known disappearance

while:

    unknown_sources contains A
        =
    continuity result for A is unknown

## 7. Unknown propagation

If a previously composed relation already establishes:

    A → Unknown

then composing it with another relation does not manufacture a definitive
result.

The source remains unknown unless the composition input explicitly contains
information capable of resolving that relation.

Unknown therefore propagates conservatively.

This prevents missing information in an earlier composition stage from being
silently converted into continuity or disappearance later.

## 8. Split mappings

A transformation may explicitly map one source entity to multiple destination
entities:

    A → (B, C)

This is a valid one-to-many continuity relation.

If the second transformation explicitly maps both destinations:

    B → D
    C → E

composition establishes:

    A → (D, E)

Destination entities are treated with set semantics.

The resulting destination collection therefore contains each destination
entity at most once.

## 9. Split followed by merge

Suppose:

    T₁:
        A → (B, C)

    T₂:
        B → D
        C → D

Composition establishes:

    A → D

The duplicate intermediate paths converge on the same destination entity.

Because destination endpoints have set semantics, `D` occurs only once in the
composed mapping.

## 10. Partial information in a split

Suppose:

    T₁:
        A → (B, C)

and:

    T₂:
        B → D

with no explicit mapping for `C`.

The result for `A` is:

    Unknown

It must not become:

    A → D

because that would discard the unresolved `C` branch.

It must also not become:

    A → ∅

because disappearance has not been established.

A composed source is known only when every intermediate destination reached by
that source has a definitive explicit result.

## 11. Explicit disappearance in a split

Suppose:

    T₁:
        A → (B, C)

and:

    T₂:
        B → D
        C → ∅

Composition establishes:

    A → D

The disappearance of `C` is explicit, so it does not make the overall result
unknown.

More generally, composition ignores intermediate branches that are explicitly
known to disappear and retains the destinations of branches with known
continuity.

If all intermediate branches explicitly disappear:

    A → (B, C)
    B → ∅
    C → ∅

then:

    A → ∅

## 12. Unknown versus disappearance

The distinction is fundamental.

Consider:

    A → B

followed by no explicit mapping for `B`.

The result is:

    Unknown

Consider instead:

    A → B
    B → ∅

The result is:

    Disappeared

These cases must not share the same representation.

An empty destination tuple therefore means a known disappearance only.

## 13. Composition result

A `CompositionResult` contains:

    mappings
    unknown_sources

A mapping establishes a definitive continuity result.

An entry in `unknown_sources` establishes that composition could not
determine a definitive continuity result for that source.

A source cannot simultaneously appear in both collections.

The representation is immutable and canonically ordered.

## 14. Sources with no mapping

Composition operates on continuity relations explicitly present in its inputs.

A source that is not present in the first relation's explicit mappings is not
automatically added to the result.

In particular, composition does not transform preservation into continuity.

This is consistent with the transformation model's distinction:

    preserved state content
        ≠
    declared continuity

The absence of a source from the composition result therefore does not itself
mean that the source disappeared.

## 15. Creation

A newly created entity has no synthetic predecessor.

Conceptually:

    ∅ → B

Creation alone therefore contributes no source mapping to composition.

If a previously existing source explicitly maps to `B` in the first
transformation, then `B` can participate in the second transformation like
any other intermediate destination.

For example:

    T₁:
        A → B

    T₂:
        B → C

produces:

    A → C

The fact that `B` was created by some earlier operation does not invalidate
the explicit mapping.

## 16. Identity transformation

An identity continuity relation may be represented explicitly as:

    A → A

When composed with:

    A → B

the resulting relation is:

    A → B

Likewise:

    A → B

followed by:

    B → B

produces:

    A → B

The identity relation is therefore neutral with respect to explicit
continuity composition.

This does not mean that an ordinary preserved entity implicitly behaves as an
identity mapping.

Identity composition applies only where the identity relation is explicitly
represented.

## 17. Associativity

For explicit continuity composition, the intended relation is associative.

Given three sequential transformations:

    T₁ : S₀ → S₁
    T₂ : S₁ → S₂
    T₃ : S₂ → S₃

the continuity information obtained by:

    compose(compose(T₁, T₂), T₃)

must agree with:

    compose(T₁, compose(T₂, T₃))

where the relevant intermediate mappings and unknown information are
represented by the current composition semantics.

Associativity concerns continuity composition only.

It does not establish associativity for full semantic transformation
composition, which has not yet been defined.

## 18. Composition is relational

The continuity mapping is a relation.

It is not required to be:

- injective;
- surjective;
- functional in the mathematical one-output sense;
- bijective.

The supported cardinalities include:

    one → zero
    one → one
    one → many
    many → one
    many → many

Composition therefore follows relational paths rather than assuming a
function-like one-to-one correspondence.

## 19. Destination set semantics

When several intermediate paths reach the same destination entity, the
destination occurs only once in the composed result.

For example:

    A → (B, C)

and:

    B → D
    C → D

produce:

    A → D

not:

    A → (D, D)

Canonical destination ordering is applied after duplicate endpoints have been
removed.

## 20. Canonical representation

Composition results are immutable.

Mappings are canonically ordered by source `EntityID`.

Destination entities inside each mapping are canonically ordered.

Unknown sources are represented as a set.

Equivalent continuity relations therefore have a deterministic representation
regardless of the input ordering used to construct them.

Canonicalization does not create semantic relationships that were absent from
the input.

## 21. Composition and references

Composition is not required for ordinary reference transfer.

Reference transfer remains one-step:

    Reference(S₀)
        →
    Reference(S₁)
        →
    Reference(S₂)

A reference may be transferred through the first transformation and then the
resulting reference through the second.

Composition can provide a derived continuity relation for analysis or other
semantic operations, but it does not alter the one-step reference-transfer
rule.

## 22. Composition and transformation changes

The current composition operation does not compose `EntityChange` values.

Suppose:

    T₁ changes A to value X

and:

    T₂ changes B to value Y

Even when:

    T₁ maps A → B

the current `compose` operation establishes only the continuity relationship
between the entities.

It does not construct a new change:

    A → value Y

nor does it construct a complete destination state.

This boundary is intentional until full semantic transformation composition
is specified.

## 23. Composition and state identity

Composition results do not modify either source state or destination state.

They do not contribute to `StateID`.

Two different composition histories may produce equivalent continuity
information without changing the identity of any state.

Likewise, a difference in provenance or composition path does not itself
constitute a semantic state difference.

## 24. Composition and provenance

The current composition result does not carry a full provenance history.

Composition therefore does not imply a globally traversable transformation
history graph.

A future provenance model may record the transformations used to derive a
composition result.

Such provenance must remain distinct from the continuity relation itself.

## 25. Current implementation boundary

The current implementation provides:

- composition of `TransformationDefinition` mappings;
- composition of `CompositionResult` mappings;
- known continuity;
- known disappearance;
- unknown continuity;
- propagation of previously unknown sources;
- split and merge composition;
- canonical destination set semantics.

It does not currently provide:

- composition of entity changes;
- construction of a complete composed destination state;
- composition of ownership semantics;
- composition of effects;
- composition of contracts;
- composition of constraints;
- composition of provenance;
- a general proof that two complete transformations are semantically
  equivalent.

These are separate future design problems.

## 26. Design principle

Transformation composition must be conservative.

Explicit continuity may be composed.

Explicit disappearance may be composed.

Missing continuity information must remain unknown.

Preservation must not be mistaken for continuity.

Unknown must not be mistaken for disappearance.

The current composition operation therefore answers a deliberately narrow
question:

    "What explicit continuity relationship can be established across these
    transformation mappings?"

It does not yet answer:

    "What complete semantic transformation results from applying these
    transformations sequentially?"

The latter requires a separate formal model before implementation.
