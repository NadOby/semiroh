# Relation Model

This document describes relations: the first concrete structure of the
semantic graph.

Two problems motivate it. References to other entities inside values are
plain `EntityID`s that nothing tracks, so a rename or disappearance leaves
them dangling. And constraints can only describe one entity, although many
useful constraints relate several.

Each section is marked:

- **Given**: already stated by other documents;
- **Open**: options are listed; no direction is chosen.

## 1. Relations are entities

**Given** (semantic_graph.md §2): there is no fundamental semantic
distinction between nodes and edges.

**Decided.**

A relation is an entity whose value is a relation record. It has an
`EntityID`, versions, and continuity like any other entity, and it lives in
program state like any other value.

    entity a : 1
    entity b : 2
    entity r : Relation(kind="depends_on", roles={from: a, to: b})

The semantic graph is therefore the state itself: entities whose values are
not relation records act as nodes, and relation entities act as hyperedges.
No separate edge store is added.

Consequences:

- a relation can be referenced, versioned, transformed, and mapped like any
  entity;
- a relation can relate other relations, which gives relations about
  relations without extra machinery;
- parallel relations of the same kind between the same entities are
  distinct entities.

## 2. Relation records

**Decided.**

A relation record is a semantic value with:

    kind      a string naming the relation kind
    roles     role name → one EntityID, or an ordered tuple of EntityIDs
    payload   optional semantic value

Named roles make hyperedges readable and order-independent: a relation of
arity three is `{caller: f, callee: g, site: s}`, not a positional triple.
An ordered tuple within one role covers genuinely ordered endpoints such as
arguments.

Relation records are canonical like other records, so equal records have equal
identity. The kind is not interpreted by the core model; meaning comes from
the tools, constraints, and metaprograms that use it.

## 3. Referential integrity

**Decided.**

Every endpoint of every relation must be present in the same state. A state
with a dangling endpoint cannot be constructed.

This is a structural check, like the check that ownership refers only to
present entities. It evaluates nothing, so program state stays pure data.

Cycles are allowed: relations are ordinary references, and ordinary
references may form arbitrary cycles (ownership_model.md §2).

Recursive destruction follows the same rule. Destroying an owned subtree
fails if a relation outside the subtree points into it: the relation must be
changed or removed first, because relations are never removed implicitly
(section 5).

## 4. References inside ordinary values

**Decided:** raw `EntityID`s in ordinary values are data.

An `EntityID` can also appear inside an ordinary value, for example a list of
entity names held by a metaprogram. The options considered were:

    data
        raw EntityIDs in content are data, not references: no integrity
        check and no update across transformations. Relations are the only
        tracked references.

    forbidden
        raw EntityIDs may appear only inside model records such as relation
        records. Every reference to an entity is then tracked.

    implicit relations
        raw EntityIDs are treated as unnamed relations and tracked.

Data was chosen. Metaprograms need entity names as data, and implicit
relations would give every value hidden graph structure. The hazard of stale
names remains, but it becomes a visible choice: a reference that must stay
valid is written as a relation.

## 5. Relations across transformations

**Decided:** relations follow declared continuity.

A transformation can remove an entity that relations still point to, or
declare that an entity continues as a different one. A relation that the
transformation explicitly changes or removes is taken as given; its new
endpoints are checked (section 3). The question is what happens to a relation
the transformation does not change.

    explicit
        a transformation must itself change or remove every relation that
        points to an entity it removes; otherwise it is rejected.

    follow continuity
        an endpoint whose entity the transformation maps follows that
        mapping, as reference transfer does. It is rewritten to the single
        destination entity, including when several sources merge into it.
        A mapped endpoint whose entity disappears or splits cannot be
        followed, and the transformation is rejected unless it changes or
        removes that relation explicitly. An endpoint whose entity the
        transformation does not map is unchanged, like any preserved content.

Following continuity was chosen. It infers nothing: it follows declared
continuity, one step, exactly as `transfer_reference` does, and it keeps
renames cheap.

A mapped endpoint follows its mapping even when its entity is still present.
In a swap (`a → b`, `b → a`) or a shift (`a → b`, `b → c`), entity `b` is
present afterwards but continues a different entity. A relation to `a`
therefore points to `b` afterwards, and a relation to `b` points to `a` or
`c`, never silently to whatever now carries the old name. Rewriting endpoints produces a new version of the relation;
like any entity, the relation's own continuity must still be declared by the
transformation (tools generate `r → r`).

Unlike ownership edges, relations are never removed implicitly. An ownership
edge is not an entity, so dropping it when an endpoint disappears loses no
declared identity. A relation is an entity, and removing it silently would
be an undeclared disappearance.

## 6. Ownership

**Decided.** Ownership stays a separate relation in state for now.

Ownership has lifetime semantics and structural invariants (one owner,
acyclic, recursive destruction) that general relations do not. Expressing it
as a relation kind with extra constraints is possible later; nothing in this
model depends on it.

## 7. Constraints over several entities

**Decided** (direction). **Open** (the full set of constraint primitives).

A constraint relation carries a constraint as its payload. The subject of
that constraint is the map from role name to the current content of each
endpoint: the value of an ordinary entity, or the runtime content of a cell.

    Relation(kind="constraint",
             roles={low: min_cell, high: max_cell},
             payload=<constraint over {low: ..., high: ...}>)

Evaluation follows the existing rules for cells: it happens in a runtime,
with the runtime's evaluation context, and anything but `Satisfied` rejects.

- loading a version evaluates every constraint relation;
- a cell write re-evaluates every constraint relation that has that cell as
  an endpoint, and a rejected write leaves the cell unchanged;
- activation and trial runs evaluate every constraint relation of the
  destination state against the staged content.

Constraints over a role map need primitives that do not exist yet. The first
set is a projection, `Role(name, constraint)`, and `External` evaluators that
receive the whole map. Comparisons between roles can follow.

## 8. Queries and indexes

**Decided.** Finding the relations that touch an entity needs an index. An
index is derived implementation data: it is rebuilt from state content and
never contributes to `StateID` (README §29).

## 9. What this does not add

Relations add structure, not a computational model. In line with the design
pressures in `priors.md`:

- transformations remain ordinary functions over immutable states; there is
  no graph rewriting and no pattern matching;
- there is no traversal language;
- the kind of a relation has no built-in meaning in the core.

## 10. Current implementation status

Nothing in this document is implemented yet.

A first implementation would add, in order: the relation record and its
canonical form; the integrity check in state construction; relation handling
in transformation application (section 5); a derived index; and constraint
relations with the first role-map primitives.

## 11. Unresolved areas

- constraint primitives over role maps beyond `Role` and `External`
  (section 7);
- whether ownership becomes a relation kind (section 6);
- relation kinds with semantics the core must enforce;
- persistence and indexing strategy for large graphs.

## 12. Design principle

A reference that must stay valid is a relation. Relations are entities: they
have identity, versions, and declared continuity, they are checked
structurally in every state, and they follow continuity only where the
transformation declares it.
