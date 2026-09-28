# Semantic Graph

This document describes the current architectural model of the SEMIROH
semantic graph.

The graph is the canonical representation of the semantic program.

## 1. Canonical representation

The semantic graph is the canonical program representation.

Source code, intermediate representations, machine code, documentation, debug
information, and other artifacts are representations or derived products of
the semantic program.

Conceptually:

    semantic program
          |
          +--> source representation
          |
          +--> semantic IR
          |
          +--> machine representation
          |
          +--> documentation
          |
          +--> debug information

No particular textual or machine representation is inherently the program
itself.

## 2. Generalized graph model

SEMIROH's fundamental semantic structure is a generalization of a hypergraph
in which there is no distinction between nodes and edges.

There are only entities. An entity whose value is a relation record relates
other entities, and every entity, including a relation, can itself be
related. Whether an entity relates others depends only on its value, not on a
separate kind of graph element.

"Node" and "edge" are therefore not terms of the model. Where the
documentation says "edge", as in "ownership edge", it is informal shorthand
for one relationship between two entities.

A semantic value may participate in zero or more relations.

A value with no participating relation can therefore exist as an atomic or
leaf semantic value.

Conceptually:

    value
      |
      +--> relation
      |
      +--> relation
      |
      +--> relation

## 3. Relations

Relations may represent semantic relationships such as:

- containment;
- application;
- typing;
- dependency;
- reference;
- description;
- transformation;
- provenance;
- authority;
- constraints.

The same general relation mechanism is intended to support both ordinary
program structure and higher-level semantic information.

## 4. Semantic values

Everything semantically meaningful is intended to be representable as a
semantic value.

Examples include:

- ordinary data;
- types;
- functions;
- constraints;
- effects;
- capabilities;
- contracts;
- transformations;
- modules;
- semantic states;
- representations;
- resources;
- metadata.

This avoids requiring a fundamentally separate object model for
metaprogramming.

## 5. Graph expansion

Not every semantic value needs to expose its complete internal structure in
the graph.

Values may be:

    inline semantic value
    opaque represented value
    external resource

An opaque value remains semantically meaningful while its internal structure
is intentionally not expanded.

Expansion is an explicit transformation.

This permits large, compressed, computationally expensive, or external values
to remain manageable without making the entire physical representation part
of the semantic graph.

## 6. Identity in the graph

Semantically meaningful entities have semantic identity.

The graph must distinguish:

    entity identity
    semantic value identity
    state identity
    runtime identity

Structural similarity is not sufficient to establish entity continuity across
states.

Continuity belongs to explicit transformations.

## 7. State and graph

Semantic states are immutable snapshots of semantic content.

A state contains semantic values and ownership relations.

Transformations produce new states.

Transformation mappings and provenance belong to transitions rather than to
state identity.

## 8. Program structure and metaprogramming

There is no fundamental requirement for source text to be the privileged
representation of program structure.

Metaprograms can operate directly on semantic values and semantic graph
structures.

Conceptually:

    semantic value
          |
          v
    semantic function
          |
          v
    semantic value / transformation

This permits tooling and program generation to operate without reconstructing
source text merely to inspect or modify semantic structure.

## 9. Representations

A semantic value may have multiple representations.

For example:

    semantic value
       |
       +--> source representation
       |
       +--> semantic IR
       |
       +--> LLVM IR
       |
       +--> machine code
       |
       +--> serialized representation

Representation transformations may preserve semantic identity while changing
physical representation.

Representation equality is therefore distinct from semantic equality.

## 10. Tooling

Because the graph is canonical, semantic tooling should operate primarily on
semantic entities rather than source text.

Potential tooling includes:

- semantic navigation;
- graph inspection;
- graph visualization;
- semantic search;
- refactoring;
- transformation inspection;
- provenance inspection;
- dependency analysis;
- contract inspection;
- constraint inspection;
- effect inspection;
- documentation generation;
- verification.

## 11. Current implementation status

The Python reference model currently implements the identity, value, state,
reference, ownership, and transformation components needed to explore this
architecture.

The generalized graph itself is not yet fully specified or implemented.
[`relation_model.md`](relation_model.md) defines its first concrete structure:
relations are entities whose values are relation records.

The architecture described here therefore establishes direction rather than
claiming a completed graph representation.

## 12. Unresolved areas

Important open questions include:

- the exact graph representation;
- graph persistence;
- graph traversal semantics;
- graph-local versus global identity;
- opaque-value boundaries;
- interaction between graph structure and type constraints;
- interaction with program modification.

## 13. Design principle

The semantic graph is the program's semantic representation.

Other representations should be derived from it rather than becoming competing
definitions of program meaning.
