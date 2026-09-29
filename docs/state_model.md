# State Model

This document defines the current semantic state model of SEMIROH.

A semantic state is an immutable collection of semantic values together with
its semantic ownership relation.

## 1. Immutable states

A semantic state is immutable.

A transformation produces a new state rather than modifying its source state.

Conceptually:

    S₀
     |
     | transformation
     v
    S₁

`S₀` remains valid after `S₁` has been produced.

This permits:

- persistence;
- rollback;
- branching;
- speculation;
- caching;
- reproducible computation;
- alternative program versions.

## 2. State contents

The current semantic state model contains:

    values
    ownership

Values are associated with `EntityID`s.

Ownership is a semantic relation between entities in the state.

Transformation mappings and provenance are not state content.

They belong to transitions between states.

The current content of an explicitly mutable cell is not semantic state
content either. The cell itself (its existence, identity, and type) is a
semantic entity and belongs to the state; the content it currently holds is
runtime state, changed in place without producing a new semantic state.

## 3. Value membership

A state contains zero or more semantic values.

Each value is associated with one entity identity.

The state must not contain a value whose internal entity identity differs from
the `EntityID` under which it is stored.

A referenced entity either exists in the state or does not.

There is no implicit placeholder entity for an absent value.

## 4. State identity

`StateID` is derived from exact semantic state content.

The current content used for state identity includes:

- all entity/value pairs;
- the ownership relation.

It does not include the current content of mutable cells.

The ordering of semantically unordered mappings does not affect state identity.

Canonical serialization is used so that equivalent semantic content produces the
same state identity.

**Decided:**

`StateID` hashes each entity's `VersionID`, which is itself the
hash of the entity and its canonical content, together with the ownership
relation. A value's `VersionID` is derived once and kept with the value, so
deriving a new state's identity never serializes content again: the cost of
a transformation does not depend on the size of the content it leaves
unchanged. `StateID` stays derived from content and cannot be supplied.

## 5. History independence

State identity is independent of construction history.

For example:

    initial state
       |          \
       |           \
       v            v
    transform A   transform B
       |            |
       v            v
       S            S

If the resulting semantic state content is identical, both results represent
the same semantic state identity.

The transformations that produced them may still have different mappings or
provenance.

## 6. State evolution

The basic state evolution operation is replacement through immutable state
construction.

Conceptually:

    S₀ + changes -> S₁

The source state is not mutated.

A change to an existing entity may preserve its `EntityID` while producing a
new `VersionID` for its value.

That value change does not itself establish transformation continuity; explicit
continuity belongs to the transformation that produced the destination state.

## 7. Activation

Producing a state and activating a state are separate concepts.

Conceptually:

    S₀
     |
     | transform
     v
    S₁
     |
     | activate
     v
    active state

Activation selects a state for subsequent execution or observation.

It does not mutate the selected state and does not invalidate previous states.

Because every program carries its compiler and may modify itself, activation
can happen while the program is running. Runtime activation must carry live
runtime state, such as the content of mutable cells, across the change along
explicit continuity mappings. See
[`activation_model.md`](activation_model.md).

## 8. Ownership

Ownership is part of semantic state content.

Consequently, changing ownership can change `StateID` even when all values are
otherwise identical.

The ownership relation is subject to its own invariants, including:

- an entity has at most one owner;
- ownership is acyclic;
- ownership refers only to entities present in the state.

Ownership is distinct from ordinary references.

## 9. Destruction

The state model provides recursive destruction as a separate operation.

Destroying an entity removes that entity and its owned subtree.

This is different from transformation disappearance.

A transformation may explicitly map an entity to zero destinations while leaving
other destination entities intact.

Transformation disappearance therefore must not automatically be interpreted
as recursive subtree destruction.

## 10. State-relative references

References are bound to a particular state.

A reference cannot silently resolve against another state merely because an
entity with the same `EntityID` exists there.

Cross-state transfer is an explicit transformation operation.

## 11. Current implementation model

The Python reference model currently represents a state as:

    State(
        id,
        values,
        ownership
    )

The value and ownership mappings are exposed as immutable structures.

`State.create()` constructs a state and derives its `StateID`.

Direct construction performs the same validation. A `StateID` is always
derived from content and cannot be supplied by the caller.

`State.with_changes()` produces a new state.

A value holding a `CellDeclaration` declares a mutable cell. The declaration
(its constraint and initial content) is state content; the cell's current
content lives in a `Runtime` and is not.

`State.destroy()` produces a new state with an entity and its owned subtree
removed.

`State.resolve()` validates and resolves a state-relative, version-pinned
reference.

## 12. Unresolved areas

The following remain open:

- the complete semantic definition of state activation (see
  [`activation_model.md`](activation_model.md));
- persistent state representation;
- structural sharing requirements;
- the final generalized graph representation;
- state-level dependency semantics;
- state identity for future semantic constructs not yet represented;
- interaction between states and runtime execution state.

## 13. Design principle

A semantic state is a value, not a mutable container.

State evolution creates another state.

History explains how a state was reached; it does not define what the state is.
