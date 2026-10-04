# Semantic Core Research Handoff

Branch: `research/semantic-core`  
Status: active architectural experiment

This is the compact authoritative continuation checkpoint for the semantic-core
research.

It is not a historical log.

Durable experiment charter:

```text
docs/semantic_core_experiment.md
```

Current Alloy evidence:

```text
docs/research/semantic-core/alloy_verification.md
```

Latest external review and project assessment:

```text
docs/research/semantic-core/peer_reviews/2026-10-04-semantic-core-recommendations.md
```

Update this file when a significant semantic decision, counterexample, bounded
result or immediate research target changes.

## Working procedure

GitHub writes are performed manually by the user.

Normal workflow:

1. inspect the live branch before judging current state;
2. work one file/change at a time;
3. provide a commit message, direct GitHub link and complete file contents;
4. user commits manually;
5. re-read the committed file from the live branch;
6. continue only from the live state.

Prefer complete files over patches because editing is often done on mobile.

Alloy execution happens in GitHub Actions.

Do not claim local Alloy execution or download Alloy locally for experiments.

## Research objective

Test whether SHEAR can be reconstructed from a smaller explicit semantic basis
centred on generalized relations while preserving:

```text
intended semantics
constructibility
independent verification
computational practicality
implementation practicality
```

The candidate core is a hypothesis.

The branch must remain capable of falsifying it.

Do not change production semantics merely to make the candidate model succeed.

## Independent hypotheses

### H1 – Representation

Can intended current SHEAR semantics be represented in the candidate core
without losing semantic distinctions?

### H2 – Construction

Can current and planned higher semantics be constructed from the smaller basis
using a sufficiently small generic extension mechanism?

### H3 – Practicality

Can those representations and constructions support acceptable:

```text
runtime complexity
memory complexity
incremental operation
static analysis
verification
implementation complexity
```

H1, H2 and H3 are independent.

Success at one does not imply success at the others.

## Current candidate core

Working hypothesis:

```text
Relation = {
    atom  : Atom?,
    roles : Role -> Sequence<RelationRef>
}
```

`RelationRef` is a state-local occurrence handle used to express:

```text
finite structure
sharing
cycles
local references
```

It is not persistent semantic identity.

### Relation ontology

There is currently no fundamental graph-semantic distinction between:

```text
node
edge
hyperedge
ordinary graph value
```

The candidate graph-semantic object is `Relation`.

Relations may be nullary.

### Atom

Atoms terminate relational structure.

The concrete atom domain remains unresolved.

Current candidates include:

```text
Bool
Int
Text
Bytes
Symbol
```

### Role

`Role` is currently a primitive candidate category.

Whether role identity can or should itself be derived relationally is an open
research question.

Do not eliminate it merely to minimize primitive count.

### State

A `State` is currently modeled as a finite collection of relation occurrences.

A relation occurrence belongs to exactly one state in the Alloy model.

There is no universal semantic root.

### View and EntityID

Current Alloy scaffolding:

```text
View {
    state
    entry
    entities : EntityID -> lone RelationOccurrence
}
```

`EntityID` is not intrinsic to relation value.

Different entity IDs may designate structurally equal values.

Important limitation:

```text
view-scoped mapping
```

is currently modeled, but:

```text
entry-derived identity namespace
```

has NOT been established.

The `entities` mapping is not currently derived from `entry`.

## Structural/value equality

Current candidate equality is bisimulation over relational structure.

It is independent from:

```text
EntityID
host identity
allocation identity
RelationRef spelling
continuity
```

Current bounded evidence supports:

```text
identity relation is a bisimulation
bisimulation reversal
bisimulation composition
distinct EntityIDs naming equal values
equal values with different sharing topology
```

Explicit non-vacuity witnesses exist for reversal and composition scenarios.

These are bounded Alloy results, not unbounded proofs.

An important unresolved question is cyclic equality:

```text
one-node cycle
vs
two-node bisimilar cycle
```

The experiment must determine whether finite graph topology itself is semantic
or whether equality is fundamentally coinductive/unfolding-based.

## Transformation and continuity

Current candidate concrete transformation:

```text
Transformation {
    source
    destination
}
```

with explicit continuity claims.

Conceptually, continuity for one source occurrence is:

```text
Unknown
|
Known(Set<DestinationOccurrence>)
```

where:

```text
Unknown
    no continuity assertion

Known({})
    explicit disappearance

Known({x})
    unique continuation

Known({x, y, ...})
    split
```

Many source occurrences may designate the same destination, so merge remains
representable.

Destination ordering is NOT currently semantic continuity information.

The Alloy model therefore uses a set of destinations, not an ordered sequence.

Continuity is not inferred from:

```text
structural equality
EntityID spelling
preservation
position
host identity
```

## Established bounded transformation evidence

Separate transformation verification exists.

Current bounded checks/witnesses support representability of:

```text
unknown continuity
explicit disappearance
1 -> 1 continuation
1 -> many split
many -> 1 merge
multiple independent claims
one claim per source occurrence
source/destination state containment
equal values without continuity
```

The first complete successful transformation verification run was:

```text
37161864993
```

All transformation commands `0` through `9` met their declared expectations.

This establishes representation behaviour only within the selected bounds.

## Semantic distinctions to preserve

Keep separate:

```text
structural equality
semantic/domain equivalence
continuity
transformation
```

None automatically implies another.

## Formal structure

Candidate semantic model:

```text
formal/core_model.als
```

Core verification entrypoint:

```text
formal/core.als
```

Transformation semantic layer:

```text
formal/transformation_model.als
```

Transformation verification entrypoint:

```text
formal/transformation.als
```

Shared instrumented runner:

```text
.github/scripts/AlloyRunner.java
```

Core CI:

```text
.github/workflows/semantic-core.yml
```

Transformation CI:

```text
.github/workflows/transformation.yml
```

The two verification lanes are intentionally separated so transformation-only
changes do not repeatedly run the expensive core composition experiment.

## Verification discipline

Use precise evidence language:

```text
bounded check passed
bounded counterexample found
bounded witness exists
experimentally observed
not established
```

Do not treat a bounded UNSAT result as an unbounded theorem.

For important implication-shaped checks, pair the assertion with a SAT witness
showing that the interesting antecedent is realizable.

Distinguish:

```text
model sanity checks
derived bounded properties
SAT witnesses
negative witnesses
non-vacuity witnesses
```

The Alloy runner currently checks declared `expect` values but still permits
commands with unspecified expectations.

Requiring explicit expectations in verification CI is an accepted hardening
task.

## Solver evidence

Current important observation:

```text
core CompositionIsBisimulation
```

is the dominant observed Alloy cost.

Instrumentation established that the long runtime occurs primarily during SAT
search rather than:

```text
parsing
model loading
CNF translation
JVM heap pressure
```

Glucose completed the bounded composition check.

After reducing verification-only search freedom, the observed composition solve
was approximately:

```text
17 min 54 s
```

versus historical completed observations of approximately:

```text
48 min 56 s
95 min 36 s
```

Runtime variance is substantial.

Do not treat those ratios as stable benchmark factors.

Hybrid decomposition showed no demonstrated advantage and was removed from the
routine core workflow.

## Projection strategy

Primary H1 experiment:

```text
π : CurrentModel -> CandidateCore
```

For a current operation:

```text
current_op(S) = S'
```

test whether relevant observables satisfy:

```text
π(current_op(S))
    ≈
core_op(π(S))
```

A mismatch does not automatically make either side authoritative.

Classify mismatches as appropriate:

```text
candidate-core defect
current-model defect
projection defect
representation difference
documented semantic commitment
implicit semantic assumption
implementation artifact
historical drift
unresolved design decision
```

No substantial current-model projection has yet been implemented.

## Not established

The following remain open:

```text
full or substantial H1 projection
entry-derived identity namespace
continuity composition
continuity associativity
information refinement semantics of Unknown
transformation composition
ownership derivation
reference semantics
constraints
function/closure construction
execution semantics
effects
capabilities
provenance
generation semantics
StateID / VersionID semantics
canonical representation
H2 in general
H3 beyond initial formal measurements
```

## Proposed but unaccepted mechanisms

Possible higher construction mechanisms include:

```text
Match / Binding
Predicate / Guard
Rewrite / Rule
Observation
```

These are not accepted kernel primitives.

Do not introduce universal graph rewriting merely because it makes derivations
convenient.

Failure to derive a feature is evidence and should be classified before adding
a primitive.

## Immediate research target

The next semantic target is continuity composition.

For compatible transitions:

```text
A --first--> B --second--> C
```

the composition must preserve the distinction between:

```text
known continuation
explicit disappearance
unknown
```

Required initial cases include:

```text
A -> B
B -> C
=> A -> C
```

```text
A -> B
B -> {}
=> A -> {}
```

```text
A -> B
B -> Unknown
=> A -> Unknown
```

```text
A -> {}
=> A -> {}
```

and split composition:

```text
A -> {B, C}
B -> D
C -> E
=> A -> {D, E}
```

Critical unresolved partial-information case:

```text
A -> {B, C}
B -> D
C -> Unknown
```

Leading hypothesis:

```text
=> A -> Unknown
```

because the complete destination set is not known.

This must be explicitly accepted or falsified rather than emerging accidentally
from the encoding.

After binary composition is defined, check associativity:

```text
(T1 ; T2) ; T3
==
T1 ; (T2 ; T3)
```

A counterexample is valuable evidence.

## Near-term sequence

Current provisional order:

1. finish documentation refactoring and establish the append-only project diary;
2. define continuity composition;
3. add basic composition witnesses/checks;
4. test associativity;
5. investigate information refinement and monotonicity;
6. add negative equality witnesses;
7. add explicit cyclic-equality experiments;
8. require explicit `expect` in verification CI;
9. preserve significant machine-readable Alloy results;
10. add structured-value continuity witnesses;
11. build the first narrow projection from current SHEAR semantics;
12. begin commuting-diagram differential experiments;
13. investigate entry-scoped identity construction;
14. investigate whether `Role` is primitive or derived;
15. only then move toward full transformation composition and
    ownership/reference propagation.

This sequence is provisional.

Counterexamples or newly discovered dependencies may change it.

## Documentation direction

`alloy_verification.md` has grown beyond a comfortable single-document scope.

Planned split:

```text
alloy_verification.md
    compact verification policy / index / current status

core_verification.md
    core Alloy evidence and solver history

transformation_verification.md
    transformation and continuity evidence
```

Also establish:

```text
project_diary.md
```

as an append-only chronological research record.

Diary entries should use ISO-8601 timestamps in Europe/Berlin, for example:

```text
2026-10-04T05:42+02:00
```

Historical entries are never rewritten.

Corrections are appended as new timestamped entries.
