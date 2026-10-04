# Prior Art and Design Risks

This document tracks conceptually related programming-language and semantic-model projects.

The purpose is not to copy their designs or treat prior art as authoritative. It is to identify independently explored design space, validate that particular abstractions are workable, and expose failure modes that SHEAR may otherwise encounter.

A design appearing here does not imply that SHEAR should adopt it. Likewise, a problem encountered by another language does not necessarily invalidate the corresponding SHEAR design: different constraints can produce different outcomes.

## Design-space map

| SHEAR area | Prior art | What it gives us | Risk / question to watch |
|---|---|---|---|
| Hypergraph as semantic substrate | LMNtal | Hierarchical graph rewriting demonstrates that graph-native computation can form the basis of a practical language. | Graph rewriting can become the entire computational model. Avoid making every ordinary operation a rewrite-system problem. |
| Program as hypergraph | Clef / Program Hypergraph | PHG explicitly generalizes program semantic graphs from binary edges to arbitrary-arity directed hyperedges. | A general semantic graph can absorb increasingly large amounts of compiler machinery. Keep the semantic substrate smaller than the entire compiler unless there is a concrete reason not to. |
| Identity distinct from state and value | Clojure | Clojure provides strong prior art for treating identity as a logical entity associated with successive immutable states. | SHEAR has immutable `State` objects and explicit transformations rather than mutable identities. Avoid accidentally reconstructing mutable identity through another mechanism. |
| Explicit immutable versions | Clojure and persistent-data systems | Persistent immutable values demonstrate that previous semantic states can remain valid and addressable. | Persistence alone does not establish conceptual identity continuity. SHEAR's explicit entity mappings solve a different problem. |
| Ownership separate from identity | Sec | Sec explicitly separates value, object, storage, ownership responsibility, borrowing authority, reference validity and provenance. | Each additional semantic distinction increases bookkeeping and implementation complexity. Every distinction should earn its place. |
| Persistent identity independent of ownership | CobaltC | Provides prior art for persistent object identity that is not itself equivalent to ownership. | Stable identity can easily turn into a second implicit reference or ownership system. Keep identity and access deliberately separate. |
| Explicit lifetime / no GC | Sec, CobaltC, Cation | Demonstrates that value-oriented and immutable semantics can coexist with explicit resource and lifetime models. | Lifetime machinery can dominate a language. Do not expose implementation lifetime as semantic identity unless required. |
| Transformation as computation | LMNtal and graph-rewriting languages | Graph transformation provides an established computational model for directly transforming graph structures. | Rewrite systems introduce matching, evaluation-order, confluence and termination problems. SHEAR may benefit from keeping transformations ordinary functions over immutable states. |
| Compiler-internal evaluation | Cation | Cation treats compilation as evaluation and attempts to make the distinction between compile-time and runtime smaller. | Compile-time execution creates difficult termination, resource-bound and bootstrapping problems. |
| First-class metaprogramming | Logos | Logos uses ordinary language mechanisms for compile-time computation rather than introducing a completely separate macro language. | Once compile-time computation becomes ordinary computation, phase separation, termination and resource limits become unavoidable design questions. |
| Everything represented in one graph | Logos | Demonstrates how programs, types, proofs and compiler-related machinery can be represented within a common semantic structure. | "Everything is graph data" is elegant but can make the compiler/toolchain itself part of the language's semantic surface and dramatically increase scope. |
| Hypergraph plus proofs | Clef | Shows that semantic hypergraphs can carry proof-related information as first-class structure. | Powerful semantic representations tend to accumulate optimization, proof, verification and domain-specific concerns. |
| Minimal language primitives | Cation | Demonstrates an explicit attempt to keep the core language small. | A small syntax or primitive set does not guarantee small semantics. Complexity can migrate into types, compilation and metaprogramming. |
| Compiler in every program | Forth, Smalltalk and Lisp images (SBCL), Terra, Synthesis kernel | Programs that carry their compiler and generate native code at runtime exist, including in firmware and OS-kernel contexts. | Image size, reproducibility, and platforms that forbid runtime code generation. |
| Live state transfer at activation | Erlang/OTP hot code loading | Two coexisting module versions; `code_change` converts process state on upgrade. SHEAR's adopted direction, in spirit. | The version bound terminates processes still running purged code; SHEAR needs an equivalent policy without GC. |
| Updating running native programs | DSU for C (Ginseng, Kitsune) | Explicit update points and state transformers make live updates of C programs workable. | Writing state transformers is a real tooling burden; update timing is the main safety question. |
| Per-thread switching | Linux kernel livepatch (https://docs.kernel.org/livepatch/livepatch.html) | Each task switches to patched code once no affected function is on its stack. | Tasks that never reach a safe point block the transition. |
| Live data migration after redefinition | Common Lisp (CLOS) | `update-instance-for-redefined-class` converts existing instances after a class changes. | Lazy conversion spreads work and failure points across later execution. |
| Reclaiming old versions without GC | RCU | Old versions are freed after a grace period without blocking readers. | Requires well-defined quiescent points in every thread. |

## Projects worth watching

### LMNtal

LMNtal is a programming language based on hierarchical graph rewriting. It is particularly relevant to SHEAR's graph-first direction.

Relevant questions:

- How much computation should be expressed as graph transformation?
- What happens to evaluation-order semantics when computation is naturally expressed as rewriting?
- How much matching and rewriting machinery is required before the graph model becomes cumbersome?
- Which graph properties are semantic and which are implementation mechanisms?

Reference:

https://github.com/lmntal/lmntal-compiler

### Clef / Program Hypergraph

Clef's Program Hypergraph model is particularly relevant because it independently treats program structure as a directed hypergraph rather than restricting the primitive relation to binary edges.

Relevant questions:

- Which properties genuinely require hyperedges?
- How should semantic identity be represented independently of graph topology?
- How much compiler information should inhabit the semantic graph?
- Can a general graph representation remain minimal while still supporting introspection and metaprogramming?

References:

https://clef-lang.com/spec/draft/program-hypergraph/

https://clef-lang.com/docs/internals/pipeline/proof-aware-compilation/

### Clojure

Clojure is useful prior art for the distinction between identity, state and immutable values.

Its conceptual model distinguishes a stable identity from the immutable values associated with that identity over time.

Relevant questions:

- What exactly constitutes conceptual identity?
- When does a new value represent a new version of an existing entity?
- Which operations preserve identity?
- Which operations create a new entity?
- How much of this distinction belongs in the language semantics rather than the runtime?

Reference:

https://clojure.org/about/state

### Sec

Sec explores a fairly explicit separation between values, objects, storage, ownership, borrowing, references and provenance.

This is particularly relevant to SHEAR because several of these concepts are intentionally kept separate rather than collapsed into one pointer/object abstraction.

Relevant questions:

- Which distinctions are actually necessary?
- How complicated does ownership become when it is part of the semantic model?
- How should reference validity interact with object identity?
- How much provenance needs to be preserved?

Reference:

https://www.sec-lang.com/01-introduction.html

### CobaltC

CobaltC explores persistent object identity independently from ownership and borrowing.

Relevant questions:

- Can an entity retain conceptual identity while ownership changes?
- How should persistent identity interact with destruction?
- How can identity remain useful without becoming implicit shared ownership?
- Which lifetime properties must be statically represented?

Reference:

https://strawberry9.github.io/the-wrong-memory/Appendix_06.html

### Cation

Cation is relevant to SHEAR's interest in a small language core, compile-time evaluation and reducing the distinction between compile-time and runtime computation.

Relevant questions:

- How much can compilation legitimately be treated as evaluation?
- Where should the boundary between compile-time and runtime remain?
- How should termination and resource limits work?
- What happens when compile-time computation becomes powerful enough to construct arbitrary programs?

Reference:

https://cation-lang.org/design/

### Logos

Logos explores an unusually reflective architecture in which the program, types, proofs, grammar and compiler-related machinery can participate in a common graph-based representation.

Relevant questions:

- How much of the compiler should be exposed to the language?
- Can metaprogramming remain ordinary computation?
- Where should bootstrapping boundaries exist?
- What should be immutable and what may be programmatically modified?
- How can reflective power avoid making the semantic model unmanageably large?

References:

https://logoslang.dev/

https://logos-lang.dev/metacall/introduction/

### Erlang/OTP hot code loading

Erlang keeps at most two versions of a module, current and old. Fully
qualified calls always enter the current version, while processes already
running old code continue in it. Loading a third version purges the old one
and terminates processes still running it. `code_change` callbacks convert
process state during an upgrade.

This is the closest precedent for SHEAR's activation direction: live state
crosses a code change through explicit conversion. See
[`docs/activation_model.md`](docs/activation_model.md).

Relevant questions:

- What replaces process termination as the purge policy in a language
  without GC?
- Where do conversion functions live relative to the transformation?
- Which calls switch to the new version, and which stay in the old one?

References:

https://www.erlang.org/doc/system/code_loading.html

## Recurring design pressures

Several recurring patterns appear across these projects.

### 1. Foundational abstractions attract additional responsibilities

A clean abstraction tends to become useful for more things than originally intended.

For example:

- Hypergraphs attract rewriting, concurrency, proofs and optimization.
- Reflection attracts compiler manipulation and language-extension mechanisms.
- Ownership attracts borrowing, lifetime analysis and provenance.
- Immutable state attracts persistence and concurrency mechanisms.
- Stable identity attracts reference management and lifecycle semantics.

This does not mean those extensions are undesirable. It means that usefulness of the underlying abstraction should not by itself justify making it responsible for every adjacent concern.

### 2. Minimal primitives do not imply minimal semantics

Reducing syntax or primitive operations can simply move complexity elsewhere.

Possible destinations include:

- type systems;
- compile-time evaluation;
- metaprogramming;
- ownership analysis;
- lifetime analysis;
- graph normalization;
- graph rewriting;
- implicit compiler transformations.

SHEAR should therefore evaluate minimality by total semantic complexity, not merely by the number of surface constructs.

### 3. Identity is unusually easy to conflate

Several distinct concepts can look like "the same object":

```text
value
entity
version
state membership
reference
storage location
ownership
access authority
```

Collapsing them may make simple programs easier to describe, but tends to make transformations, persistence, aliasing and lifecycle semantics harder to specify.

SHEAR should preserve distinctions when they represent genuinely different semantic facts, while resisting distinctions that exist only because of implementation details.

### 4. Reflection creates phase problems

Powerful metaprogramming eventually raises:

- termination;
- resource limits;
- evaluation order;
- bootstrapping;
- compiler availability;
- semantic self-modification;
- reproducibility;
- security and isolation.

The existence of first-class metaprogramming should therefore not imply unrestricted compile-time execution.

### 5. Graph-native semantics create representation pressure

A graph is an attractive universal representation because relationships become explicit.

However, once everything is represented as graph structure, questions appear about:

- canonicalization;
- identity;
- traversal;
- matching;
- normalization;
- graph rewriting;
- persistence;
- provenance;
- graph size;
- incremental compilation.

The semantic graph should remain the source of truth without automatically becoming the mechanism responsible for every compiler operation.

## Working principle for SHEAR

Prior art should be treated as evidence about explored design space.

A useful classification is:

```text
Validated:
    Another system demonstrates that the abstraction can work.

Pressure:
    Another system demonstrates an important complexity introduced by
    the abstraction.

Failure mode:
    Another system demonstrates a concrete problem that SHEAR
    should explicitly test against.

Uncertain:
    The systems are sufficiently different that their experience
    cannot be transferred directly.

Open:
    No sufficiently similar prior art has been identified.
```

The important question is therefore not:

> "Does another language do this?"

but:

> "What happened when another language operated under similar constraints?"

And even more importantly:

> "Which problems came from the abstraction itself, and which came from that language's other design choices?"

## Current conceptual neighbourhood

A rough map of the relevant design space is:

```text
                         graph rewriting
                              |
                           LMNtal
                              |
                              |
hypergraph semantics ---- SHEAR ---- persistent identity/state
       |                      |                    |
    Clef/PHG                  |                 Clojure
                              |
                       semantic ownership
                         /           \
                       Sec          CobaltC
                              |
                       reflective compiler
                         /           \
                      Logos        Cation
```

SHEAR does not currently appear to be a direct derivative of any one of these systems. Its closest conceptual relationship is instead the intersection of several independently explored ideas:

```text
hypergraph semantics
        +
persistent semantic identity
        +
immutable versioned state
        +
explicit continuity mappings
        +
independent ownership
        +
first-class transformation
        +
reflective/metaprogrammable compilation
```

That intersection is the part for which prior art is currently much weaker.

This makes the individual precedents useful primarily as sources of constraints, counterexamples and design questions rather than as templates.
