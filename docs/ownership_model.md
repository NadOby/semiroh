# Ownership Model

This document defines the current semantic ownership model of SEMIROH.

Ownership is a semantic state relation concerned with lifetime authority.
Ordinary references are a separate relation concerned with access.

## 1. Ownership relation

Ownership is represented as a directed relation:

    owner -> owned entity

The current model requires ownership to form a forest.

An entity may have at most one owner.

An entity may own multiple children.

Ownership must be acyclic.

## 2. Ownership versus references

Ownership and ordinary references are independent relations.

Conceptually:

    ownership
        = lifetime authority

    reference
        = access relationship

Ordinary references may form arbitrary cycles.

An ordinary reference cycle therefore does not create an ownership cycle and
does not by itself determine object lifetime.

## 3. Ownership invariants

A valid ownership relation must satisfy:

- every owner exists in the containing state;
- every owned entity exists in the containing state;
- an entity has at most one owner;
- an entity cannot own itself;
- ownership contains no recursive cycle.

Invalid ownership relations are rejected.

## 4. Canonical representation

Ownership children are represented canonically.

The order in which children are supplied must not change the semantic ownership
relation.

Canonical ordering therefore ensures deterministic state identity and
deterministic inspection.

An owner listed with no children describes the same ownership relation as an
owner that is not listed. Such entries are omitted from the canonical
representation and therefore do not affect state identity.

An entry naming an entity absent from the state is still rejected, even when
its child collection is empty.

## 5. Ownership queries

The semantic state provides the following conceptual queries:

    owner_of(entity)
    owned_children(owner)
    owned_subtree(owner)

`owner_of()` returns the unique owner, if one exists.

`owned_children()` returns the direct children.

`owned_subtree()` returns the complete recursively owned subtree.

## 6. Destruction

Destruction is an immutable state transformation.

Destroying an entity removes:

    entity
    +
    recursively owned descendants

from the resulting state.

The original state remains unchanged.

Destruction therefore differs from mutation.

## 7. Transformation disappearance

Transformation disappearance is distinct from recursive destruction.

When a transformation explicitly maps:

    E -> ()

the source entity disappears from the destination state.

This does not automatically mean that every entity formerly owned by `E` is
also removed. Because the entities it owns would otherwise change owner
implicitly, such a transformation must state the destination ownership
explicitly (section 9).

Transformation semantics operate on the explicitly defined destination state.

Recursive subtree destruction is a separate state operation.

## 8. Transformation mappings

Ownership edges follow declared continuity. When a transformation maps

    source entity -> destination entity

the destination entity continues the source entity, so it keeps the source's
place in the ownership forest: it owns what the source owned and is owned by
what owned the source. This matches how relation endpoints follow continuity
(relation_model.md section 5).

This reverses an earlier rule that continuity mappings never modify
ownership. That rule silently orphaned the children of a renamed owner, which
is an implicit ownership change.

## 9. Omitted ownership

When a transformation does not explicitly provide destination ownership,
edges follow declared continuity, and no entity that remains may change owner
implicitly. The exact rules are in transformation_model.md section 13.

An ownership change that following cannot express, such as orphaning,
reparenting, or resolving a split, is stated by supplying the destination
ownership explicitly (section 10).

## 10. Explicit destination ownership

A transformation may provide an explicit destination ownership relation.

Such a relation describes the destination state directly.

It must refer only to destination entities and must satisfy the ownership
invariants.

It is not interpreted as a continuity mapping.

## 11. Ownership transfer

Ownership transfer is conceptually different from ordinary entity continuity.

Reparenting changes the ownership relation.

It does not necessarily change conceptual entity identity.

Physical movement of an object's representation is a separate concern.

## 12. Current implementation model

The Python reference model currently provides:

    OwnershipMap
    normalize_ownership()
    owner_of()
    owned_children()
    owned_subtree()

`State.create()` validates ownership as part of state construction.

`State.destroy()` performs recursive subtree destruction.

## 13. Unresolved areas

The following remain open:

- explicit ownership transfer semantics;
- physical move semantics;
- pinning;
- borrowing;
- alias analysis;
- lifetime analysis;
- interaction with concurrency;
- capability-based ownership authority;
- representation-level lifetime guarantees.

Deferred until the first program implementations need them:

- how ownership becomes part of the graph: one relation per ownership, one
  member list per owner, or the current store with the same rules;
- whether deletion and disappearance are one operation, differing only
  between the semantic and runtime regimes, so that an owner's disappearance
  ends its owned subtree;
- whether the top of the forest is owned by a virtual runtime root or by an
  explicit program root entity, to which modules, libraries, and entry points
  attach;
- how creation places a new entity under its owner, including as a
  guarantee that every transformation carries.

## 14. Design principle

Ownership determines lifetime authority.

References determine access.

Neither relation should silently become the other.
