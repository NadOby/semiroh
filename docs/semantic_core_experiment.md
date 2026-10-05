# Semantic Core Verification Experiment

Status: experimental research  
Branch: `research/semantic-core`

This branch investigates whether SHEAR can be described and implemented from a smaller, more explicit semantic basis than the current Python representation.

The work is intentionally falsification-oriented. The candidate core is a hypothesis, not a replacement design.

No production semantic change should be made merely to make the candidate model succeed.

## 1. Motivation

Recent verification work exposed repeated failures around semantic boundaries rather than graph manipulation itself:

- host values versus semantic values;
- mutable construction versus immutable semantic state;
- graph structure versus external representations;
- identity versus value/version/state;
- transformations versus continuity;
- malformed structures versus execution;
- closures versus captured environments;
- runtime state versus semantic versions.

The current implementation also contains pragmatic representational layers that may not correspond directly to the intended ontology.

In particular, the implementation currently distinguishes entities, values and relation records, while the intended generalized-hypergraph model may admit a smaller basis in which relations are the fundamental graph-semantic object and identity is represented separately.

The experiment asks whether that smaller basis is sufficient, constructive, verifiable and practical.

## 2. Experimental hypotheses

The work separates three hypotheses.

### H1 – Representation

Every intended current semantic state can be represented without semantic loss in the candidate relational core.

This includes preservation of distinctions that are intentionally observable.

### H2 – Construction

Current and planned semantics can be constructed from the core using a small number of generic mechanisms rather than requiring each higher-level concept to become a primitive.

Examples to investigate include:

- ownership;
- lifetime;
- constraints;
- functions;
- closures;
- execution;
- effects;
- capabilities;
- provenance;
- identity/versioning.

### H3 – Practicality

The smaller core does not impose unacceptable cost elsewhere.

Costs to evaluate include:

- asymptotic complexity;
- constant-factor runtime cost;
- graph size;
- matching/traversal cost;
- incremental-update cost;
- compiler complexity;
- verification complexity;
- implementation complexity;
- inability to build efficient derived indexes or caches.

H1 may succeed while H2 fails.

H1 and H2 may succeed while H3 makes the architecture unsuitable.

The experiment must preserve these outcomes as distinct results.

## 3. Candidate semantic core

The following is the current working model. None of it is final unless separately promoted into the normative design.

### 3.1 Relation

The fundamental graph-semantic object is a relation.

There is no fundamental semantic distinction between:

- node;
- edge;
- hyperedge;
- ordinary graph value.

Conceptually:

```text
Relation = {
    atom  : Atom?,
    roles : Role -> Sequence<RelationRef>
}
```

`RelationRef` is a local formal handle used to describe a finite structure, sharing and cycles.

It is not persistent semantic identity.

### 3.2 Atom

An atom is irreducible local content needed to terminate relational structure.

Initial candidates include:

```text
Bool
Int
Text
Bytes
Symbol
```

The exact atom domain is unresolved.

Structured semantic information should normally be represented relationally rather than hidden inside arbitrary host containers.

### 3.3 Nullary relations

A relation may have no roles.

Examples such as:

```text
1
"foo"
true
```

can therefore be represented as nullary relations carrying atomic content.

A separate semantic `Value` object is not assumed by the candidate core.

### 3.4 Roles, order and multiplicity

Relations have named roles.

Role declaration order itself is not intended to matter.

Targets within a role may be an ordered sequence where ordering or multiplicity is meaningful.

For example:

```text
pair(1, 1)
```

does not require two intrinsically different instances of `1`.

Repeated occurrence is structural multiplicity.

However:

```text
pair(1, 1)
```

and:

```text
pair(dup(1))
```

are different structures.

They may be declared equivalent by higher semantics, but that equivalence is not structural equality.

### 3.5 Structural equality

Relation equality is fundamentally equality by relational value/structure rather than allocation identity.

Two independently represented `1` relations may therefore be equal even when used in different enclosing relations.

Sharing topology alone should not automatically create semantic inequality.

For cyclic structures, bisimulation is the current candidate formal interpretation of value equality.

This has not yet been accepted as final semantics and must be tested against intended cyclic and recursive cases.

### 3.6 State

A state is a finite relational structure.

The state itself does not require one globally privileged root.

Basic candidate well-formedness includes:

- every referenced local relation handle exists;
- role names within a relation are well formed and unambiguous;
- atoms belong to the accepted atom domain.

Additional state invariants should be introduced only when required by semantics.

### 3.7 Entry points

An arbitrary relation may act as an interpretation entry point.

Examples include:

- program;
- module;
- library;
- subsystem.

The same relational state may therefore support multiple entry points.

The entry point is not assumed to be an intrinsic global root of the state.

### 3.8 EntityID

`EntityID` is not currently assumed to be intrinsic to every relation value.

The working model associates an entity namespace with an entry point:

```text
EntityID ⇀ RelationOccurrence
```

Conceptually this behaves like a finite map or hash-map-like namespace exposed from the entry point.

The exact representation remains open:

- it may be represented explicitly as relational structure reachable from the entry relation;
- a formal model may temporarily represent it as a field on a `View`;
- an implementation may use a hash map or another index.

These representations must not be conflated with the semantics of the mapping itself.

This separation permits:

```text
A != B
```

while:

```text
value(A) == value(B)
```

if both names refer to structurally equal relational values.

### 3.9 Transformation

A transformation relates an immutable source state to an immutable destination state.

It also carries explicit continuity information.

Conceptually:

```text
continuity :
    SourceOccurrence
        ⇀ Sequence<DestinationOccurrence>
```

The important cases are:

```text
none
    continuity unknown / not asserted

some []
    explicit disappearance

some [x]
    one-to-one continuation

some [x, y, ...]
    split
```

Multiple sources may continue into one destination.

Continuity is not inferred from:

- structural equality;
- equal atoms;
- equal positions;
- reused local handles;
- equal `EntityID` spelling;
- host identity.

Preservation of structure is not automatically continuity.

### 3.10 Distinct semantic relations

The candidate model keeps these separate:

```text
structural equality
semantic equivalence
continuity
transformation
```

Structural equality means equal relational value.

Semantic equivalence means that different structures are explicitly considered equivalent under some higher semantics.

Continuity states how occurrences relate across a transformation.

A transformation describes a change between states.

None should automatically imply another.

### 3.11 Experimental state identity

Status: experimental projection hypothesis, recorded for plan step 4 of
`handoff.md`. It is not accepted SHEAR semantics.

Two candidate states have the same experimental `StateID` iff there is a
bijection between their occurrence handles that preserves:

- atoms (atoms themselves are not renamed);
- role names (role names themselves are not renamed);
- each role's target sequence, including order and multiplicity;
- every relation target.

That is, the states are isomorphic as finite relational structures.

The definition fixes equality only. It specifies no hash algorithm or
canonical form.

#### What is excluded

`EntityID` bindings of views are not part of state equivalence. Including them
would import `main`'s identity machinery into the candidate and evade H1.

Anything a projection represents as relations inside the state is included. If
a projection encodes `EntityID`s or ownership as relational structure, those
become part of state identity through the isomorphism, not through a separate
rule.

The candidate currently has no ownership. `main`'s `StateID` covers ownership,
so how ownership is represented is part of what the projection must show.

#### Isomorphism, not bisimulation

State identity is finer than value equality. Two states whose occurrences are
pairwise bisimilar but whose sharing differs are not isomorphic and have
different experimental `StateID`s.

#### Equivalence, not correspondence

Equal experimental `StateID`s establish that an isomorphism exists. They do
not choose one.

For independently constructed states `M1` and `M2` with equal `StateID`, the
isomorphisms `M1 → M2` form a coset of the automorphism group of `M1`. A
continuity composition through `M1` and `M2` is well defined iff its result is
the same for every isomorphism in that coset.

- When `M1` has no non-trivial automorphism, the isomorphism is unique and
  composition is well defined.
- When `M1` has symmetric occurrences, composition may depend on the choice.
  Such a dependence observed in the experiment is an H1 failure, not a
  projection defect.

#### Expected relation to `main`

`main`'s `StateID` hashes `(EntityID, VersionID)` pairs and ownership. Two
`main` states with the same content under different `EntityID` naming have
different `StateID`s.

For projected states, the expected relationship is therefore:

```text
main StateIDs equal       =>  candidate StateIDs equal       expected to hold
candidate StateIDs equal  =>  main StateIDs equal            expected to fail
```

The second direction is expected to fail exactly where `main` states differ
only in `EntityID` naming, or in ownership the projection does not represent.
Such failures are predicted, and are classified rather than patched. Any other
failure in either direction is unexpected evidence.

#### Complexity

The cost of deciding or canonicalizing this equivalence for SHEAR-sized
states is not established. Ordered, labelled role targets restrict the
possible isomorphisms, but no bound is claimed here. It is an H3 question and
does not block the H1 experiment.

#### Stability

This hypothesis stays unchanged through the first projection attempt. It may
change only as part of the single candidate revision allowed at plan step 7.

## 4. Deliberate limits of the core

The project does not currently seek a complete relational algebra.

The purpose is to define only enough structure to make required semantics unambiguous and constructible.

Do not introduce machinery merely to make the system more mathematically pure.

A candidate primitive should earn its place by showing that without it required behaviour becomes:

- ambiguous;
- circular;
- non-constructible;
- unverifiable;
- or computationally impractical.

## 5. Candidate higher mechanisms

The following mechanisms have been proposed as possible generic extensions:

```text
Match / Binding
Predicate / Guard
Rewrite / Rule
Observation
```

They are hypotheses to test, not accepted kernel features.

This distinction is particularly important for generic graph matching and rewriting.

The current implementation intentionally uses ordinary functions over immutable states rather than making graph rewriting the universal computational model.

The experiment must therefore test whether matching or rewriting is actually required as core semantics, can remain derived/library/compiler machinery, or should be rejected entirely.

## 6. Planned derivation targets

The experiment should attempt to derive or reconstruct at least:

```text
ownership
lifetime
constraints
function semantics
closure semantics
execution
effects
capabilities
provenance
generation behaviour
StateID semantics
VersionID semantics
canonical representation
references
activation/trial semantics
```

Failure to derive one of these is useful evidence.

Each failure must be classified rather than patched implicitly.

Possible classifications:

```text
missing fundamental mechanism
missing derived rule
current documented semantic commitment
implementation artifact
performance requirement
representation requirement
unresolved design decision
```

## 7. Verification strategy

### 7.1 Projection

Define a semantics-preserving projection:

```text
π : CurrentModel -> CandidateCore
```

The first question is not whether the new representation is elegant.

It is whether the projection preserves all intended semantic distinctions.

Examples include:

- semantic value equality;
- entity distinction;
- relation topology;
- continuity;
- ownership;
- reference validity;
- transformation outcomes.

### 7.2 Commuting operations

For a current operation:

```text
current_op(S) = S'
```

test whether:

```text
π(current_op(S))
```

agrees with the candidate-model operation:

```text
core_op(π(S))
```

for all relevant observables.

Conceptually:

```text
           current_op
      S ----------------> S'
      |                    |
    π |                    | π
      v                    v
   CoreS --------------> CoreS'
             core_op
```

A mismatch must be classified rather than automatically resolved in favour of either side.

### 7.3 Formal bounded exploration

A bounded model checker such as Alloy is a candidate for early structural experiments.

Possible modules:

```text
formal/
    core
    entities
    transformations
    ownership
    references
    constraints
```

The modules should be layered.

A higher module may use only mechanisms already accepted below it.

Counterexamples should be retained and, where practical, converted into executable regression cases.

Alloy is not currently selected as the final formal foundation.

### 7.4 General proof

If properties survive bounded exploration and appear important enough to prove generally, a theorem prover may later be introduced.

Possible systems include Lean, Rocq or Isabelle.

No theorem prover is selected at this stage.

### 7.5 Executable differential verification

An executable model should independently compare candidate semantics against the current implementation.

Verification code must not reuse production algorithms when doing so would destroy oracle independence.

Where useful:

```text
formal witness
    -> executable candidate case
    -> current implementation
```

and:

```text
current generated case
    -> projection
    -> candidate/formal checks
```

should both be supported.

## 8. Complexity verification

Semantic derivability alone is insufficient.

Each proposed derivation should record its computational consequences.

Examples of desirable implementation bounds include:

```text
entity lookup:
    O(1) expected or O(log n) deterministic

relation incidence lookup:
    derived index permitted

ownership parent lookup:
    O(1) expected or O(log n)

owned subtree:
    O(size of subtree)

affected constraint lookup:
    proportional to affected indexed relations,
    not the entire graph

structural equality:
    graph-aware/memoized,
    not exponential recursive expansion
```

Derived implementation structures are allowed.

Indexes, caches, compiled forms and memoization need not be semantic state merely because they are required for performance.

The relevant question is:

> Does the semantic model permit an efficient implementation without requiring hidden semantic assumptions?

## 9. Migration strategy

This branch is not initially a production migration branch.

The candidate model must first survive verification.

The intended progression is:

```text
formal hypothesis
    ↓
current -> core projection
    ↓
differential checks
    ↓
derivation experiments
    ↓
complexity checks
    ↓
verified semantic cut
```

Only a verified semantic cut should later become a candidate for production migration.

Production conversion should occur incrementally behind compatibility boundaries rather than through a wholesale rewrite.

An old subsystem should be removed only after the replacement has:

- representation coverage;
- semantic differential coverage;
- an independent oracle;
- acceptable complexity;
- regression coverage.

## 10. Branch isolation

`research/semantic-core` is intentionally isolated from production development.

Initial rules:

- branch from `main`;
- no intentional production semantic changes;
- formal/reference-model code must not become a production dependency;
- verification runners should be independent from normal CI where practical;
- failures of the candidate model are valid experimental outcomes;
- do not modify production semantics merely to satisfy the experiment.

Tasks 18, 18a, 19 and the project rename are expected to proceed independently.

They are not expected to introduce semantic changes, but that expectation must be verified when this branch is rebased onto the resulting `main`.

Any unexpected semantic differential after rebase is evidence to investigate.

## 11. Open questions

### Q1 – Distinguished atoms

Should `Atom` include distinguished values such as:

```text
NaN
+Infinity
-Infinity
Nothing
Null
Undefined
```

Questions include:

- should absence be an atom or structural absence;
- how should `NaN` interact with structural equality;
- should infinities be primitive;
- would generic sentinels create ambiguous alternative representations?

No decision yet.

### Q2 – Minimal bootstrap basis

What is the smallest non-circular set of mechanisms from which the planned higher semantics can be constructed?

Candidate mechanisms currently under investigation include:

```text
relation
state
structural equality
entry point
EntityID binding
transformation
continuity
match/binding
predicate
rewrite
observation
```

The last four are particularly provisional.

### Q3 – Cost of excessive minimalism

Can reducing the semantic basis too aggressively damage:

- runtime performance;
- asymptotic complexity;
- analyzability;
- incremental compilation;
- verification;
- implementation simplicity;
- functionality?

The objective is not the fewest possible primitives.

The objective is the smallest sufficient basis under semantic, implementation, verification and complexity constraints.

### Q4 – Semantic commitment versus implementation drift

For each current behaviour, determine whether it is:

```text
intended semantic commitment
derived semantic behaviour
representation choice
implementation artifact
historical drift
```

The candidate core should not reproduce implementation drift merely because it exists.

Conversely, it must not discard a real semantic distinction merely because a smaller model appears cleaner.

## 12. Experiment ledger

Important hypotheses and failures should be recorded explicitly.

Suggested fields:

```text
Hypothesis
Required property
Evidence
Counterexample
Status
Required addition/change
Complexity consequence
Current-code consequence
```

Do not allow a failed hypothesis to disappear through silent modification of the model.

## 13. Initial work

The first experimental slice should remain small:

1. formalize the candidate relation/state/view model;
2. test structural equality and local-handle renaming;
3. define the current-to-core projection for atomic and structured values;
4. test separation of value equality from `EntityID`;
5. represent current relations;
6. add transformation/continuity;
7. test ownership as the first substantial derivation;
8. record every missing primitive or complexity problem;
9. only then expand toward references, constraints, graph-form code, closures and runtime behaviour.

The primary result of this branch is evidence about the semantic basis.

Successful code is secondary.
