# Identity Model

This document defines the current identity model of SHEAR.

It distinguishes conceptual entity identity, semantic value version identity,
semantic state identity, and runtime identity.

It is normative where stated. Implementation details of the Python reference
model are not themselves semantic requirements.

## 1. Identity kinds

SHEAR distinguishes several kinds of identity.

### Entity identity

`EntityID` identifies a conceptual entity.

It represents continuity of an entity across semantic states when a
transformation explicitly establishes that continuity.

Entity identity answers:

    Is this the same conceptual entity?

Entity identity does not establish semantic equality.

### Version identity

`VersionID` identifies one exact semantic value version of an entity.

A value version is determined by the semantic value represented by the entity,
not by the history through which that value was produced.

Therefore:

    same EntityID
        does not imply
    same VersionID

Two versions of one entity may have the same conceptual identity while
representing different semantic values.

### State identity

`StateID` identifies one exact immutable semantic state.

State identity is derived from semantic state content.

Transformation history, mapping metadata, and provenance do not contribute to
state identity.

### Runtime identity

Runtime identity identifies a runtime instance, allocation, handle, or resource
incarnation.

Runtime identity is distinct from semantic identity.

A runtime object may represent a semantic value without becoming identical to
that semantic value.

## 2. Identity versus equality

Identity and semantic equality are different relations.

In particular:

    Entity identity != semantic equality
    Version identity != entity identity
    State identity != provenance
    Runtime identity != semantic identity

Two distinct entities may contain semantically equal values.

One entity may have multiple semantic value versions.

Two independently produced states may have identical semantic content and
therefore the same `StateID`.

## 3. Entity identity and continuity

An `EntityID` does not by itself establish continuity between states.

If an entity with the same `EntityID` appears in two states, this alone does
not establish that the second occurrence is the continuation of the first.

Continuity must be established by the relevant transformation.

Conceptually:

    S₀ contains E
        |
        | explicit transformation mapping
        v
    S₁ contains E

The mapping establishes continuity.

Without that mapping, the transformation has not asserted continuity merely
because the identifier happens to be reused.

## 4. Version identity

A semantic value version is identified independently of the entity's history.

For example:

    Value(E, 42)
    Value(E, 42)

produces the same semantic value version.

Whereas:

    Value(E, 1)
    Value(E, 2)

produces different versions even though both values have the same `EntityID`.

This makes value identity content-based rather than history-based.

## 5. State identity

State identity is determined by exact semantic state content.

Semantic state content includes the values present in the state and the
semantic ownership relation.

It does not include:

- transformation mappings;
- transformation provenance;
- the path by which the state was reached;
- cache state;
- source text;
- implementation-specific runtime objects.

Consequently, two independently produced states with identical semantic
content have the same state identity.

## 6. Canonicalization

Semantic identity requires deterministic representation of semantic content.

Canonical serialization provides the basis for this determinism.

Equivalent semantic structures must serialize identically under the canonical
representation.

The canonical representation must not depend on incidental container
iteration order.

Canonicalization is therefore part of the identity mechanism rather than
merely a formatting convention.

Canonicalization is idempotent: canonicalizing already-canonical content
returns it unchanged. Content taken from an existing value can therefore be
reused to construct another value without changing its semantic identity.

Semantic equality is decided by canonical serialization, not by the equality
of the host language. For example, the Python reference model must treat
`True` and `1` as distinct values even though Python considers them equal,
because their canonical serializations differ.

## 7. Current implementation model

The Python reference implementation currently represents these identities as
immutable value objects:

    EntityID
    VersionID
    StateID

`EntityID`, `VersionID`, and `StateID` are separate types and must not be
interchanged.

The reference model also provides an `Entity` value identified by an
`EntityID`.

These implementation structures exist to expose and test the semantic
distinctions above.

## 8. Unresolved areas

The following remain intentionally open:

- whether identity kinds will acquire additional semantic forms;
- the final identity model for transformations themselves;
- identity of representations;
- identity of capabilities and resources;
- interaction with the eventual generalized graph model (partly answered
  by §10);
- the precise relationship between semantic identity and persistent storage.

These must not be inferred merely from the current Python representation.

## 9. Design principle

Identity answers a different question from equality.

Conceptually:

    EntityID   -> conceptual continuity
    VersionID  -> exact semantic value
    StateID    -> exact semantic state
    runtime ID -> runtime incarnation

No identity kind should silently substitute for another.

## 10. Identity is primitive

**Decided:**

From the semantic-core experiment, closed 2026-10-05. The research branch `research/semantic-core` tested whether SHEAR could be
rebuilt from a smaller basis of generalized relations, with `EntityID` kept
out of values. It projected every corpus program, the continuity corpus and
adversarial cases into that candidate and compared observables with `main`.
The branch is archived at tag `semantic-core-experiment-2026-10`
(`docs/research/semantic-core/h1_evaluation.md` there holds the full
evaluation).

Results:

- With references reduced to structure, equality conflated 4,379 entity
  pairs in real programs that `main` keeps apart, and one leaf edit changed
  the value of every ancestor and transitive caller (129 of 549 entities in
  the `compiler` corpus program, against 2 `VersionID` changes in `main`).
- The single allowed revision restored agreement on every tested observable
  only by putting names back into values, state identity and continuity –
  the architecture `main` already has.

Four independent semantic relationships must therefore remain
distinguishable. They are relationships, not primitive edge types:

    within a state:
        structural / value containment
        named reference to a stable entity identity
        ownership (an edge set with forest constraints)

    between states:
        continuity, declared by transformations over names

**`EntityID` is not continuity; it is the stable vocabulary in which
continuity can be stated.** It cannot be derived from the current state
alone: an identity derived from position, path, content or topology can say
"same position" or "same content", never "same thing, moved". That rejects
paths as identity, not selectors used inside a reference anchored at a
stable identity, such as `(EntityID(A), field y)`.

Simplifications of the model should therefore remove duplicate mechanisms
within these relationships, not reduce identity, time or lifetime to graph
topology. Follow-up audits and experiments are in `docs/roadmap.md`, tasks 20
to 25.

