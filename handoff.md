# Semantic Core Research Handoff

Branch: `research/semantic-core`  
Status: active architectural experiment

This file is the compact continuation checkpoint for the semantic-core research.

The durable experiment charter is:

`docs/semantic_core_experiment.md`

Update this file when a significant decision, counterexample, verified result, or next step changes.

Keep it compact. It is not a historical log.

## Working procedure

GitHub writes are performed manually by the user in this workflow.

Normal procedure:

1. inspect the live branch before making conclusions;
2. work one file/change at a time;
3. provide:
   - commit message;
   - direct GitHub file link;
   - complete file contents;
4. user pastes and commits the file;
5. re-read the committed file from the live branch;
6. only then continue to the next change.

Prefer complete files over patches because editing is often done on mobile.

Do not assume an earlier chat snapshot is current when the repository can be inspected.

## Purpose

Test whether SHEAR can be reconstructed from a smaller, explicit semantic basis centred on generalized relations while preserving:

- intended semantics;
- constructibility of planned features;
- independent verification;
- acceptable computational complexity;
- acceptable implementation complexity.

The candidate core is a hypothesis.

The branch must remain capable of falsifying it.

Do not change production semantics merely to make the candidate model succeed.

## Branch isolation

This branch was created for semantic-core research.

It should initially contain:

```text
formal/reference models
projection experiments
differential verification
complexity experiments
documentation
dedicated verification runners
```

Production code should not depend on the experimental model during the initial research phase.

Tasks 18, 18a, 19 and the project rename are proceeding separately and are expected not to introduce intentional logic changes.

When those changes reach `main`, rebase this branch and verify that expectation rather than assuming it.

## Current hypotheses

### H1 – Representation

Every intended current semantic state can be projected into the candidate core without losing intended semantic distinctions.

### H2 – Construction

Current and planned higher semantics can be constructed from the core using a sufficiently small generic basis.

### H3 – Practicality

The resulting semantics permit acceptable:

- asymptotic complexity;
- runtime performance;
- graph size;
- incremental operation;
- static analysis;
- verification;
- implementation complexity.

These hypotheses are independent.

A result may support H1 while falsifying H2 or H3.

## Current candidate core

Working hypothesis only.

```text
Relation = {
    atom  : Atom?,
    roles : Role -> Sequence<RelationRef>
}
```

`RelationRef` is a state-local formal handle.

It exists to express:

- finite graph structure;
- sharing;
- cycles;
- local references.

It is not persistent semantic identity.

### Relation ontology

There is no fundamental graph-semantic distinction between:

```text
node
edge
hyperedge
ordinary graph value
```

Relations are the graph-semantic object.

A relation may be nullary.

### Atom

Atoms terminate relational structure.

Current initial candidates:

```text
Bool
Int
Text
Bytes
Symbol
```

The exact atom domain is unresolved.

Structured semantic information should normally be represented relationally rather than hidden in arbitrary host structures.

### Equality

Structural/value equality is based on relational structure rather than:

```text
EntityID
allocation identity
host object identity
local RelationRef spelling
```

Two separately occurring relations can therefore have equal value.

For cyclic structures, bisimulation is the current candidate formalization.

That remains to be tested rather than assumed final.

### Multiplicity

Repeated equal values do not require separate intrinsic identities.

For example:

```text
pair(1, 1)
```

does not require two different identities for `1`.

However:

```text
pair(1, 1)
```

and:

```text
pair(dup(1))
```

are different structures.

They may later be declared semantically equivalent, but that is not structural equality.

### State

A state is currently hypothesized as a finite relational structure.

It does not intrinsically require one universal root.

### Entry point

An arbitrary relation may act as an entry point for interpreting a program, module, library, subsystem, or other view.

The same relational state may therefore admit multiple entry points.

### EntityID

`EntityID` is not currently assumed to be intrinsic to relation value.

The working model is an entry-scoped finite mapping:

```text
EntityID ⇀ RelationOccurrence
```

Conceptually this is hash-map-like, but its implementation is not part of the semantic commitment.

This allows:

```text
A != B
```

while:

```text
value(A) == value(B)
```

if the two entity names designate structurally equal values.

### Transformation

A transformation relates an immutable source state and destination state and carries explicit continuity.

Conceptually:

```text
SourceOccurrence
    ⇀ Sequence<DestinationOccurrence>
```

Cases:

```text
none
    continuity unknown / not asserted

some []
    explicit disappearance

some [x]
    one continuation

some [x, y, ...]
    split
```

Many sources may continue into one destination.

Continuity is not automatically inferred from:

```text
structural equality
preservation
EntityID spelling
position
host identity
```

## Semantic distinctions to preserve

Keep separate:

```text
structural equality
semantic equivalence
continuity
transformation
```

None automatically implies another.

## Proposed but unaccepted mechanisms

Candidates currently worth testing:

```text
Match / Binding
Predicate / Guard
Rewrite / Rule
Observation
```

These are not accepted kernel primitives.

In particular, do not accidentally turn generic graph rewriting into the computational model merely because it makes derivations convenient.

Current SHEAR design deliberately has ordinary functions over immutable states and has previously treated universal graph rewriting/matching as a complexity risk.

Attempt to eliminate or demote these mechanisms before accepting them into the trusted core.

## Planned derivation targets

Try to construct or explain from the core:

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
references
StateID semantics
VersionID semantics
canonical representation
activation/trial semantics
```

Failure is evidence.

Do not automatically repair a failed derivation by adding a primitive.

Classify the failure first.

Useful classifications:

```text
missing fundamental mechanism
missing derived rule
documented semantic commitment
representation requirement
performance requirement
implementation artifact
historical drift
unresolved design decision
implementation defect
```

## Verification method

Primary mapping:

```text
π : CurrentModel -> CandidateCore
```

The projection must preserve intended semantic distinctions.

For a current operation:

```text
current_op(S) = S'
```

test a commuting relation:

```text
π(current_op(S))
    ≈
core_op(π(S))
```

where `≈` compares the relevant semantic observables.

A mismatch does not automatically mean either side is wrong.

Classify it.

## Formal verification direction

Early bounded structural exploration may use Alloy or an equivalent solver.

No permanent formal tool has been selected.

Possible layering:

```text
core
entities
transformations
ownership
references
constraints
...
```

Higher layers should depend only on previously accepted lower mechanisms.

Formal witnesses and counterexamples should be retained and converted to executable cases where practical.

Later general proofs may use Lean, Rocq, Isabelle, or another system if justified.

## Executable verification

The candidate model should eventually be compared independently with the current Python implementation.

Avoid reusing production algorithms in verification code when doing so would destroy oracle independence.

Useful directions:

```text
formal witness
    -> executable case
    -> current implementation
```

and:

```text
generated current case
    -> π
    -> candidate/formal check
```

## Complexity requirement

Semantic derivability is not sufficient.

For every significant derivation, track computational consequences.

Derived non-semantic structures are allowed:

```text
indexes
caches
memoization
compiled representations
lookup tables
```

The important question is:

> Does the semantic model permit an efficient implementation without requiring hidden semantic assumptions?

Do not optimize for mathematical purity alone.

## Open questions

### Q1 – Distinguished atoms

Should atoms include values such as:

```text
NaN
+Infinity
-Infinity
Nothing
Null
Undefined
```

Questions include:

- value versus structural absence;
- equality semantics of NaN;
- primitive versus derived infinities;
- competing representations of absence.

### Q2 – Bootstrap basis

What is the smallest non-circular basis from which the planned semantics can be constructed?

### Q3 – Excessive minimalism

Can reducing the core further harm:

```text
functionality
runtime complexity
memory complexity
static analysis
incremental compilation
verification
implementation complexity
```

The objective is the smallest sufficient basis, not the fewest primitives at any cost.

### Q4 – Semantic commitment versus drift

For each current behaviour classify it as:

```text
semantic commitment
derived semantic behaviour
representation choice
implementation artifact
historical drift
```

Do not reproduce implementation drift merely because it exists.

Do not remove real semantic distinctions merely because the new model is smaller.

## Current implementation tension

Current Python representation is approximately:

```text
EntityID
    ->
Value {
    entity,
    content
}
```

with relations represented as one form of semantic content.

The candidate model is closer to:

```text
RelationValue
+
entry-scoped EntityID -> RelationOccurrence
```

Current ownership is represented separately from ordinary relations.

These are research targets, not established defects.

## Current repository state

The experiment charter has been created at:

```text
docs/semantic_core_experiment.md
```

No formal model or production migration has yet been added on this branch.

## Immediate next step

After this file is committed:

1. re-read `handoff.md` from the live branch;
2. decide the initial experiment directory and runner structure;
3. create the smallest formal model covering only:
   - Relation;
   - State;
   - entry/view;
   - EntityID binding;
   - structural equality;
4. establish bounded properties and counterexamples;
5. keep production code untouched;
6. update this handoff when the experimental result changes what the next chat needs to know.
