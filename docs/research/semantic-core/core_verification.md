# Core Alloy Verification Evidence

Status: experimental research  
Branch: `research/semantic-core`  
Alloy version: `6.2.0`

This document records bounded formal evidence and solver observations for the
candidate semantic core.

It is not normative SHEAR semantics.

Shared verification policy:

```text
docs/research/semantic-core/alloy_verification.md
```

Alloy API and runner details:

```text
docs/research/semantic-core/alloy_api_reference.md
```

Chronological research history:

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

`core.als` contains verification-only structures, assertions, witnesses, and
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

Cyclic equality uses the same candidate bisimulation mechanism but remains an
explicit research target rather than a settled semantic decision.

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

Evidence classification:

```text
IdentityIsBisimulation
ReverseIsBisimulation
CompositionIsBisimulation
    derived bounded properties

DistinctEntitiesCanNameEqualValues
SharingDoesNotForceInequality
    semantic witnesses

ReverseWitnessExists
CompositionWitnessesExist
    non-vacuity witnesses
```

These are bounded Alloy results, not unbounded proofs.

## 4. Current bounded evidence

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

The non-vacuity witnesses require actual relevant structures rather than merely
allowing implication-shaped checks to pass through unrealizable antecedents.

This reduces bounded vacuity risk.

It does not establish the corresponding properties without bounds.

## 5. Composition verification

The composition property checks whether two compatible valid bisimulations
compose into another valid bisimulation.

Conceptually:

```text
left --firstPairs--> middle --secondPairs--> right
```

and checks:

```text
bisimulation[
    left,
    right,
    firstPairs.secondPairs
]
```

`CompositionIsBisimulation` has consistently been the dominant observed cost of
the core suite and is therefore the primary worst-case solver workload.

## 6. Composition search-surface refactor

The original composition verification searched over two independent:

```text
BisimWitness
```

objects and then searched for compatible pairs.

That introduced verification-only freedom around:

```text
witness identity
endpoint assignments
compatible and incompatible witness pairs
independently represented pair relations
```

The verification scaffolding was changed to a direct:

```text
CompositionCase
```

containing:

```text
left
middle
right
firstPairs
secondPairs
```

with the relevant compatibility and bisimulation constraints.

The candidate semantic predicate:

```text
bisimulation
```

was unchanged.

The old and new SAT encodings are not identical.

The intended equivalence between the two verification representations has been
argued manually but not mechanically established.

Correct classification:

```text
verification search-surface refactor
intended representational equivalence
```

not:

```text
formally proved equivalent encodings
```

## 7. Instrumentation and bottleneck

Before the search-surface refactor, an instrumented composition run observed
approximately:

```text
primary variables: 506
total variables:   167253
clauses:           377687
```

After the refactor:

```text
primary variables: 360
total variables:   164761
clauses:           373172
```

Approximate changes:

```text
primary variables: -29%
total variables:   -1.5%
clauses:           -1.2%
```

CNF construction completed quickly relative to SAT solving.

Observed bottleneck classification:

```text
SAT search
```

rather than:

```text
parsing
model loading
CNF translation
workflow setup
JVM heap pressure
```

The large runtime improvement despite relatively small changes in total
variables and clauses also shows that those aggregate counts alone are poor
predictors of search difficulty for this experiment.

## 8. Historical solver observations

### SAT4J

Run `37129982325` completed the identity and reversal checks but did not produce
a composition result before the workflow execution limit.

Run `37140819564` isolated composition and again produced no result within
approximately 120 minutes.

Classification:

```text
no result within operational limit
```

not semantic failure or success.

### Glucose before search-surface refactor

Run `37142378947`:

```text
CompositionIsBisimulation:
    UNSAT

solver duration:
    approximately 2936 s
    approximately 48 min 56 s
```

Run `37148637570`:

```text
CompositionIsBisimulation:
    UNSAT

solver duration:
    approximately 5736 s
    approximately 95 min 36 s
```

The model and command were unchanged between these observations.

This demonstrated substantial wall-time variance on GitHub-hosted runners.

### Glucose after search-surface refactor

Run:

```text
37159091258
```

Commit:

```text
bceaae4d93edbdee798b047791423dc3778ab000
```

Observed:

```text
CompositionIsBisimulation:
    UNSAT

solver:
    Glucose

mode:
    batch

solver duration:
    approximately 1074 s
    approximately 17 min 54 s

primary variables:
    360

total variables:
    164761

clauses:
    373172
```

Relevant scopes:

```text
3 State
6 Rel
2 Role
6 RoleUse
6 Slot
3 Atom

0 EntityID
0 View
0 BisimWitness
exactly 1 CompositionCase
```

This was materially faster than the earlier Glucose observations.

Because Glucose runtime variance is substantial, the observed ratios are not
stable benchmark factors.

The defensible conclusion is:

```text
strong experimental evidence:
    reducing verification-only search freedom materially improved this bounded
    composition problem
```

## 9. Solver-selection benchmark

Run:

```text
37195954192
```

Purpose:

```text
compare available finite SAT solvers on the same worst-case
CompositionIsBisimulation command
```

The experiment preserved the model, command, scope, and runner configuration
while varying the solver.

The generated composition CNF for the completed comparison had:

```text
total variables:
    164761

clauses:
    373172
```

Completed results:

```text
lingeling.parallel:
    UNSAT
    solver time approximately 166 s
    approximately 2 min 46 s

glucose:
    UNSAT
    solver time approximately 1494 s
    approximately 24 min 54 s
```

Observed ratio on this controlled comparison:

```text
glucose / lingeling.parallel:
    approximately 9.0x
```

The following jobs reached the two-hour experiment cutoff without producing a
SAT or UNSAT result:

```text
minisat
minisat.prover
sat4j
sat4j.light
```

Their classification is:

```text
no result within experiment time limit
```

not failure of the checked property.

The benchmark therefore provides strong engineering evidence for selecting:

```text
lingeling.parallel
```

as the routine solver for the current Alloy verification suite.

This selection is not evidence that `lingeling.parallel` is universally faster
on Alloy or on every future SHEAR model.

It establishes only that it was decisively more practical on the current
dominant bounded workload.

Because `lingeling.parallel` is an external parallel solver, the observed
advantage has not been decomposed into:

```text
solver-family advantage
parallel-search advantage
```

That distinction is not currently required for the CI decision.

## 10. Routine verification consequence

The historical worst-case core command moved from:

```text
Glucose:
    approximately 17–96 minutes across completed historical observations
```

to:

```text
lingeling.parallel:
    approximately 2 min 46 s in the controlled benchmark
```

The routine engineering target was:

```text
preferred:
    <= 5 minutes

solver-selection cutoff:
    10 minutes
```

`lingeling.parallel` crossed the preferred threshold in the benchmark without
changing semantic scope.

The consolidated workflow therefore uses it for routine Alloy verification:

```text
.github/workflows/alloy-verification.yml
```

The first complete consolidated verification run succeeded across all
discovered commands.

This is verification-infrastructure evidence, not additional semantic evidence.

## 11. Hybrid decomposition experiment

Alloy exposes Pardinus decomposition modes:

```text
0  batch/off
1  Hybrid
2  Parallel
```

Historical Hybrid composition experiments did not demonstrate a practical
advantage over batch solving for this problem.

Instrumentation showed essentially the same underlying composition CNF scale
before entering long solver execution.

Correct conclusion:

```text
no demonstrated advantage for the observed experiment
```

not:

```text
Hybrid is universally slower
```

The dedicated Hybrid lane was therefore removed from routine CI.

## 12. Performance interpretation

Solver metrics provide limited H3 evidence.

Useful quantities include:

```text
semantic scope
primary variables
total variables
clauses
translation time
solver time
memory observations
```

GitHub-hosted wall-clock time is noisy.

Small differences should not be overinterpreted.

Prefer:

```text
large effects
repeated observations
structural solver metrics
scope staircases
```

when performance itself becomes the research target.

Changing semantic scope merely to obtain a faster green result is not a
quality-preserving optimization.

A smaller scope is a different bounded problem.

The current solver benchmark changed solver only and therefore did not weaken
the checked bounded semantic problem.

## 13. What is not established

Current core evidence does not establish:

```text
unbounded equality theorems

whether finite graph topology should be semantic for cyclic values

negative equality discrimination across all intended structural differences

that the current atom domain is sufficient

that Role is semantically primitive

that View identity is derived from entry

projection equivalence with current SHEAR semantics

H1 in general

H2 in general

H3 in general
```

Specific open equality experiments include:

```text
DifferentAtomsAreNotEqual
DifferentRoleSetsAreNotEqual
DifferentTargetOrderIsNotEqual
DifferentTargetMultiplicityIsNotEqual
PresentEmptyRoleDiffersFromAbsentRole
```

Explicit cyclic falsification should include:

```text
one-node self-cycle
vs
two-node alternating cycle
```

The current bisimulation may treat these as equal.

Whether that is intended coinductive equality or an unwanted loss of finite
graph topology remains unresolved.

## 14. Next core-specific work

High-value core falsification work includes:

```text
negative equality witnesses
explicit cyclic equality experiments
formal mutation experiments against equality constraints
entry/view identity experiments
Role bootstrap-boundary experiments
first narrow CurrentModel -> CandidateCore projection
```

The existing composition check remains regression evidence.

Further solver tuning is not currently a priority unless verification cost again
becomes an H3 bottleneck.
