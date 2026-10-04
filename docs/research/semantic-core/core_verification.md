# Core Alloy Verification Evidence

Status: experimental research  
Branch: `research/semantic-core`  
Alloy version: `6.2.0`

This document records bounded formal evidence and solver observations for the
candidate semantic core.

It is not normative SHEAR semantics.

Shared verification policy and document index belong in:

```text
docs/research/semantic-core/alloy_verification.md
```

Alloy Java API and runner details belong in:

```text
docs/research/semantic-core/alloy_api_reference.md
```

Chronological research history belongs in:

```text
docs/research/semantic-core/project_diary.md
```

## 1. Formal scope

Candidate semantic model:

```text
formal/core_model.als
```

Verification entrypoint:

```text
formal/core.als
```

The split is intentional.

`core_model.als` contains candidate semantic structures and predicates.

`core.als` contains verification-only structures, assertions, witnesses and
bounded commands.

Verification scaffolding such as:

```text
BisimWitness
CompositionCase
```

is not proposed as SHEAR semantic ontology.

## 2. Candidate equality

Current structural/value equality is based on bisimulation.

For related relation occurrences, the current predicate requires:

```text
equal atomic content
equal role-name sets
equal target-sequence positions within each role
pairwise related targets at corresponding positions
```

The bisimulation relation need not be one-to-one.

This deliberately permits candidate value equality across different sharing
topologies.

Current equality is intended to be independent from:

```text
EntityID
host object identity
allocation identity
RelationRef spelling
continuity
```

Cyclic equality is currently interpreted through the same bisimulation
mechanism but remains an explicit research target rather than a settled
semantic decision.

## 3. Verification commands

Current core commands:

```text
0  IdentityIsBisimulation
1  ReverseIsBisimulation
2  CompositionIsBisimulation
3  DistinctEntitiesCanNameEqualValues
4  SharingDoesNotForceInequality
5  ReverseWitnessExists
6  CompositionWitnessesExist
```

Expected results:

```text
0  UNSAT
1  UNSAT
2  UNSAT
3  SAT
4  SAT
5  SAT
6  SAT
```

Interpretation:

```text
UNSAT check passed
    no counterexample exists within the selected bounds

SAT witness exists
    at least one satisfying structure exists within the selected bounds
```

These are bounded Alloy results.

They are not unbounded proofs.

## 4. Evidence categories

The current commands do not all provide the same kind of evidence.

### Derived bounded properties

```text
IdentityIsBisimulation
ReverseIsBisimulation
CompositionIsBisimulation
```

These search for bounded counterexamples to algebraic properties of the
candidate bisimulation relation.

### Semantic witnesses

```text
DistinctEntitiesCanNameEqualValues
SharingDoesNotForceInequality
```

These demonstrate that the model admits intended semantic distinctions.

### Non-vacuity witnesses

```text
ReverseWitnessExists
CompositionWitnessesExist
```

These demonstrate that the interesting structures constrained by the
corresponding algebraic checks actually occur within the selected bounds.

The non-vacuity witnesses were added because a passing implication can otherwise
create false confidence when its antecedent is unrealizable.

## 5. Identity and reversal evidence

Current bounded results support:

```text
identity relation satisfies the candidate bisimulation constraints

a valid bisimulation can be reversed and still satisfy the candidate
bisimulation constraints
```

`ReverseWitnessExists` additionally requires an actual nonempty structural
scenario rather than only an empty or trivial relation.

This closes the identified bounded vacuity concern for reversal at the selected
scope.

It does not establish an unbounded theorem.

## 6. Composition evidence

The current composition property checks whether two compatible valid
bisimulations compose into another valid bisimulation.

Conceptually:

```text
left --firstPairs--> middle --secondPairs--> right
```

and verifies:

```text
firstPairs.secondPairs
```

as a bisimulation between:

```text
left
right
```

The composition check has consistently been the dominant observed cost of the
core verification suite.

## 7. Historical SAT4J evidence

### Sequential run

Run:

```text
37129982325
```

Observed:

```text
IdentityIsBisimulation:
    UNSAT

ReverseIsBisimulation:
    UNSAT

CompositionIsBisimulation:
    unresolved
```

The sequential job continued until approximately the GitHub Actions platform
execution limit.

The composition result from that run is:

```text
no result
```

not:

```text
property failure
```

and not:

```text
property success
```

### Isolated composition run

Run:

```text
37140819564
```

Observed:

```text
CompositionIsBisimulation:
    no result within approximately 120 minutes
```

That historical job used an explicit timeout and was cancelled when the limit
was reached.

Again:

```text
timeout != counterexample
timeout != proof
```

SAT4J was therefore operationally much less practical for this observed
composition problem than Glucose.

That is a solver-performance observation, not a semantic statement.

## 8. Initial completed Glucose evidence

### First completed composition

Run:

```text
37142378947
```

Observed:

```text
CompositionIsBisimulation:
    UNSAT

solver duration:
    approximately 2936 s
    approximately 48 min 56 s
```

This was the first completed bounded composition result using the original
composition search surface.

### Repeat

Run:

```text
37148637570
```

Observed:

```text
CompositionIsBisimulation:
    UNSAT

solver duration:
    approximately 5736 s
    approximately 95 min 36 s
```

The formal model and composition command were unchanged relative to the earlier
completed Glucose run.

The approximately twofold runtime difference demonstrates substantial
run-to-run variance on the observed GitHub-hosted environment.

Therefore individual wall-clock measurements should not be treated as stable
fine-grained benchmarks.

## 9. Instrumentation result

The custom runner established that the expensive composition command reaches
the SAT solver quickly.

Before the search-surface refactor, an instrumented composition execution
produced approximately:

```text
primary variables:
    506

total variables:
    167253

clauses:
    377687
```

CNF construction completed in seconds.

The long execution then occurred inside SAT solving.

Observed bottleneck classification:

```text
SAT search
```

rather than:

```text
parsing
Alloy model loading
CNF translation
GitHub Actions setup
JVM heap pressure
```

This does not establish which logical feature inside the encoding creates the
hard SAT search.

## 10. Non-vacuity work

The original reversal and composition assertions had a false-confidence risk:
their important antecedents might have been unrealizable.

Explicit commands were added:

```text
ReverseWitnessExists
CompositionWitnessesExist
```

`ReverseWitnessExists` requires a nontrivial valid bisimulation involving actual
relational structure.

`CompositionWitnessesExist` requires:

```text
three-state chain
two compatible valid nonempty bisimulations
nonempty relational composition
composed source occurrence with actual role structure
```

Both produce SAT witnesses within their configured bounds.

Therefore:

```text
bounded witness exists:
    relevant reversal scenario

bounded witness exists:
    relevant compatible composition scenario
```

This reduces vacuity risk.

It does not prove the corresponding algebraic properties without bounds.

## 11. Composition search-surface refactor

The original composition verification used two independent verification
objects:

```text
BisimWitness
```

and searched for compatible pairs among them.

Conceptually the old structure was:

```text
first:
    left
    middle
    firstPairs

second:
    middle
    right
    secondPairs
```

but Alloy also had to search irrelevant freedom around:

```text
witness identity
endpoint assignments
compatible pairs
incompatible pairs
two independently represented pair relations
```

The verification scaffolding was changed to:

```text
CompositionCase
```

which directly represents:

```text
left
middle
right
firstPairs
secondPairs
```

with facts requiring:

```text
some firstPairs
some secondPairs
bisimulation[left, middle, firstPairs]
bisimulation[middle, right, secondPairs]
```

The checked conclusion is directly:

```text
bisimulation[
    left,
    right,
    firstPairs.secondPairs
]
```

The candidate semantic predicate:

```text
bisimulation
```

was not changed.

This was a verification search-surface change.

## 12. Representational-equivalence caveat

The old and new composition SAT encodings are not identical.

The intended argument is that:

```text
two compatible BisimWitness objects
```

and:

```text
one CompositionCase containing the same endpoints and pair relations
```

represent the same composition scenario relevant to the checked property.

That equivalence has been argued manually.

It has not itself been separately mechanically proved.

Therefore the correct status is:

```text
intended representational equivalence
```

not:

```text
formally proved equivalent encodings
```

## 13. Optimized composition result

Run:

```text
37159091258
```

Commit:

```text
bceaae4d93edbdee798b047791423dc3778ab000
```

Command:

```text
CompositionIsBisimulation
```

Solver:

```text
Glucose
```

Mode:

```text
batch
```

Result:

```text
UNSAT
```

Relevant semantic scopes:

```text
3 State
6 Rel
2 Role
6 RoleUse
6 Slot
3 Atom
```

Irrelevant or verification-only signatures were restricted:

```text
0 EntityID
0 View
0 BisimWitness
exactly 1 CompositionCase
```

Instrumented encoding:

```text
primary variables:
    360

total variables:
    164761

clauses:
    373172
```

Compared with the earlier instrumented search surface:

```text
primary variables:
    506 -> 360
    approximately 29% reduction

total variables:
    167253 -> 164761
    approximately 1.5% reduction

clauses:
    377687 -> 373172
    approximately 1.2% reduction
```

Timing:

```text
CNF callback:
    approximately 1122 ms

Alloy-reported solver time:
    1073944 ms

runner execution wall time:
    approximately 1074005 ms

total runner wall time:
    approximately 1074443 ms
```

Equivalent solver duration:

```text
approximately 17 min 54 s
```

The observed runtime was materially below the two earlier completed Glucose
observations:

```text
48 min 56 s
95 min 36 s
```

Approximate observed ratios:

```text
2.7x relative to 48 min 56 s
5.3x relative to 95 min 36 s
```

Because runtime variance is known to be large, these ratios are not stable
benchmark factors.

The defensible interpretation is:

```text
strong experimental evidence:
    reducing verification-only search freedom materially improved this bounded
    composition problem
```

The result also indicates that total CNF variable and clause counts alone are
poor predictors of search difficulty in this experiment.

The largest relative change was in primary search variables.

## 14. Hybrid decomposition experiments

Alloy exposes Pardinus decomposition modes:

```text
0  batch/off
1  Hybrid
2  Parallel
```

Historical experiments also ran composition under Hybrid decomposition.

Observed Hybrid executions did not demonstrate a practical advantage over
batch Glucose for this problem.

Instrumentation showed essentially the same underlying composition CNF scale
before entering a long solver execution.

No evidence established that Hybrid is semantically different or universally
slower.

The correct conclusion is limited to:

```text
no demonstrated advantage for the observed experiment
```

The dedicated Hybrid job was therefore removed from routine semantic-core CI.

It can be reintroduced later for an explicit decomposition benchmark if there
is a reason to do so.

## 15. Current bounded evidence summary

Current evidence supports:

```text
IdentityIsBisimulation:
    bounded check passed

ReverseIsBisimulation:
    bounded check passed

ReverseWitnessExists:
    bounded non-vacuity witness exists

CompositionIsBisimulation:
    bounded check passed

CompositionWitnessesExist:
    bounded non-vacuity witness exists

DistinctEntitiesCanNameEqualValues:
    bounded witness exists

SharingDoesNotForceInequality:
    bounded witness exists
```

Operational observations:

```text
composition dominates current core verification cost

Glucose completed the current bounded composition problem

SAT4J did not complete the observed expensive composition experiments within
the historical operational limits

SAT search dominates observed composition runtime after translation

verification-only search freedom materially affected solver difficulty

Glucose wall-clock runtime varies substantially between executions
```

## 16. What is not established

The current core evidence does not establish:

```text
unbounded equality theorems

that finite graph topology should or should not be semantic for cyclic values

negative equality discrimination across all intended structural differences

that the current atom domain is sufficient

that Role is semantically primitive

that View identity is derived from entry

projection equivalence with current SHEAR semantics

H1 in general

H2

H3 beyond the limited formal-complexity observations recorded here
```

Specific open equality experiments include:

```text
DifferentAtomsAreNotEqual
DifferentRoleSetsAreNotEqual
DifferentTargetOrderIsNotEqual
DifferentRoleMultiplicityIsNotEqual
PresentEmptyRoleDiffersFromAbsentRole
```

and explicit cyclic cases such as:

```text
one-node cycle
vs
two-node bisimilar cycle
```

These are future falsification work, not established conclusions.

## 17. Performance interpretation

Solver metrics are evidence for H3 only in a limited sense.

Useful recorded quantities include:

```text
semantic scope
primary variables
total variables
clauses
translation time
solver time
memory observations
```

GitHub-hosted wall-clock time is noisier.

Small timing differences should not be overinterpreted.

For future stable properties, scope staircases may be useful:

```text
scope 3
scope 4
scope 5
scope 6
...
```

but changing semantic scope merely to obtain a faster green result is not a
quality-preserving optimization.

A smaller scope is a different bounded problem.

## 18. Next core-specific work

The immediate project-wide semantic target is continuity composition, not more
solver tuning of the existing bisimulation composition experiment.

Core-specific falsification work remains important and should follow without
being conflated with transformation work.

High-value next core experiments include:

```text
negative equality witnesses

explicit cyclic equality witnesses

formal mutation experiments against equality constraints

entry/view identity experiments

Role bootstrap-boundary experiments

first narrow projection from current SHEAR values into the candidate core
```

The existing core composition check should remain as regression evidence while
the research moves upward.
