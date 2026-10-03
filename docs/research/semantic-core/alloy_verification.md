# Alloy Verification Notes

Status: experimental research  
Branch: `research/semantic-core`  
Alloy version: `6.2.0`

This document records verification results, infrastructure observations and
interpretation for the semantic-core experiment.

It is not normative SHEAR semantics.

Detailed Alloy 6.2 Java API information is kept separately in:

```text
docs/research/semantic-core/alloy_api_reference.md
```

The semantic experiment itself is described in:

```text
docs/semantic_core_experiment.md
```

## 1. Current formal structure

The semantic model is:

```text
formal/core_model.als
```

The verification entrypoint is:

```text
formal/core.als
```

The split is intentional.

`core_model.als` contains the candidate semantic structures and predicates.

`core.als` contains:

```text
verification scaffolding
assertions
witness scenarios
bounded commands
```

Verification-only structures such as:

```text
BisimWitness
CompositionCase
```

are not proposed SHEAR semantic primitives.

Current commands:

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
UNSAT check:
    no counterexample exists within the selected bounds

SAT witness:
    at least one satisfying structure exists within the selected bounds
```

Neither establishes an unbounded theorem.

## 2. Command isolation

The first workflow executed Alloy commands sequentially.

That allowed one pathological command to hide the status of all later
commands.

The workflow was changed to:

1. discover Alloy command indices;
2. run each command in an independent GitHub Actions matrix job;
3. preserve each command's declared scopes and expectation;
4. allow expensive commands to continue without blocking unrelated results.

This localized nearly all current verification cost to:

```text
CompositionIsBisimulation
```

Commands:

```text
0
1
3
4
5
6
```

complete comparatively quickly in the observed runs.

Command isolation is therefore both a performance feature and an epistemic
requirement.

A pathological command must not obscure successful or failed verification of
unrelated properties.

## 3. Historical solver evidence

### 3.1 SAT4J sequential run

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
    unresolved when GitHub Actions terminated the job
```

The job reached approximately the GitHub Actions six-hour execution limit.

This is:

```text
no result
```

It is neither a passing nor failing composition result.

### 3.2 SAT4J isolated composition

Run:

```text
37140819564
```

Observed:

```text
CompositionIsBisimulation:
    no result within 120 minutes
```

The job was cancelled by the explicit historical 120-minute timeout.

Again:

```text
timeout != verification failure
timeout != verification success
```

The explicit research timeout was subsequently removed.

### 3.3 Glucose completed composition – first run

Run:

```text
37142378947
```

Observed:

```text
CompositionIsBisimulation:
    UNSAT

elapsed:
    2936 s

equivalent:
    48 min 56 s
```

This was the first completed bounded composition result at the original
composition search surface.

### 3.4 Glucose completed composition – repeat

Run:

```text
37148637570
```

Observed:

```text
CompositionIsBisimulation:
    UNSAT

elapsed:
    5736 s

equivalent:
    95 min 36 s
```

The formal model and composition command were unchanged relative to the first
completed Glucose run.

The difference between:

```text
2936 s
```

and:

```text
5736 s
```

is almost a factor of two.

Therefore single-run wall-clock timing is not a sufficiently stable basis for
fine-grained solver comparisons on GitHub-hosted runners.

## 4. Instrumented runner

The experimental runner is:

```text
.github/scripts/AlloyRunner.java
```

It uses:

```text
CompUtil.parseEverything_fromFile(...)
TranslateAlloyToKodkod.execute_commandFromBook(...)
```

rather than constructing an independent solver pipeline.

The runner records:

```text
runtime environment
solver capabilities
effective A4Options
command metadata
parse wall time
resolved scope messages
resolved bound messages
translation events
CNF events
primary variables
total variables
clause count
Alloy-reported solver-result time
runner execution wall time
total wall time
JVM heap observations
warnings
final result
expectation result
```

Long executions additionally emit periodic:

```text
ALLOY_HEARTBEAT
```

records containing elapsed time and JVM heap observations.

A heartbeat means:

```text
the Java runner process is alive
```

It does not mean:

```text
the SAT search has made measurable progress
```

The relevant Alloy API details and classifications are documented in:

```text
docs/research/semantic-core/alloy_api_reference.md
```

## 5. Instrumentation result

Instrumentation established that the expensive composition command reaches the
SAT solver quickly.

Before the search-surface refactor, an instrumented batch composition run
produced approximately:

```text
primary variables:
    506

total variables:
    167253

clauses:
    377687
```

CNF translation completed in seconds.

The subsequent long period occurred inside SAT solving.

Therefore the dominant observed cost is:

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

This does not identify which part of the logical encoding creates the hard SAT
instance.

## 6. Non-vacuity verification

The original reversal and composition assertions had a residual
false-confidence risk.

A passing implication does not establish that its important antecedent is
realizable.

Explicit witness commands were therefore added:

```text
5  ReverseWitnessExists
6  CompositionWitnessesExist
```

Both successfully produced SAT witnesses.

`ReverseWitnessExists` requires:

```text
two distinct states
a valid nonempty bisimulation
a related source occurrence with actual role structure
```

`CompositionWitnessesExist` requires:

```text
a genuine three-state chain
two valid compatible bisimulations
a nonempty relational composition
a composed source occurrence with actual role structure
```

Both witness commands passed in GitHub Actions.

Therefore the previously identified bounded non-vacuity concern is closed for
the currently selected witness bounds.

This means:

```text
verified:
    the relevant reversal structure exists within the selected bounds

verified:
    the relevant compatible composition structure exists within the selected
    bounds
```

It does not mean:

```text
the algebraic properties are proved without bounds
```

## 7. Composition search-surface refactor

The original composition verification used two arbitrary:

```text
BisimWitness
```

objects and checked:

```text
first.right = second.left implies
    bisimulation[
        first.left,
        second.right,
        first.pairs.second.pairs
    ]
```

This required Alloy to search:

```text
witness identity
endpoint assignments
compatible witness pairs
incompatible witness pairs
two arbitrary pair relations
```

while only compatible witnesses matter to the property.

The verification scaffolding was changed to:

```text
CompositionCase
```

which directly represents:

```text
left --firstPairs--> middle --secondPairs--> right
```

with facts requiring both pair relations to be valid nonempty
bisimulations.

The assertion is now directly:

```text
bisimulation[
    c.left,
    c.right,
    c.firstPairs.c.secondPairs
]
```

The semantic `bisimulation` predicate itself was not changed.

The meaningful semantic signature bounds for the composition experiment remain:

```text
3 State
6 Rel
2 Role
6 RoleUse
6 Slot
3 Atom
```

Verification-only and irrelevant signatures are explicitly scoped:

```text
0 EntityID
0 View
0 BisimWitness
exactly 1 CompositionCase
```

The old and new SAT problems are therefore not identical encodings.

The intended equivalence is representational:

```text
old:
    two valid BisimWitness objects sharing the middle State

new:
    one CompositionCase directly containing the same left, middle, right,
    firstPairs and secondPairs
```

This equivalence argument has not itself been separately mechanically proved.

## 8. Search-surface result

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

Instrumented encoding:

```text
primary variables:
    360

total variables:
    164761

clauses:
    373172
```

Compared with the previous instrumented search surface:

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
    1122 ms

solver-reported time:
    1073944 ms

runner execution wall time:
    1074005 ms

total runner wall time:
    1074443 ms
```

Equivalent solver duration:

```text
approximately 17 min 54 s
```

This is materially faster than both previous completed Glucose observations:

```text
48 min 56 s
95 min 36 s
```

The observed speedups are approximately:

```text
2.7x relative to the 48 min 56 s run

5.3x relative to the 95 min 36 s run
```

Because historical composition runtime has substantial variance, these ratios
must not be treated as stable benchmark factors.

However, the new run is sufficiently below both previous completed observations
to support:

```text
strong evidence:
    reducing verification search freedom materially improved this bounded
    composition check
```

The result also demonstrates that total CNF variable and clause counts alone
are poor predictors of solver difficulty here.

A large reduction in primary search variables coincided with a much larger
runtime improvement than the change in total CNF size.

## 9. Current solver interpretation

Current evidence supports:

```text
verified:
    composition dominates current bounded core verification cost

verified:
    Glucose proves the current bounded composition check UNSAT

verified:
    SAT4J was dramatically less practical for the observed composition
    experiments

verified:
    SAT search dominates composition runtime after translation

verified:
    the original composition wrapper exposed substantial avoidable search
    freedom

verified:
    explicit non-vacuity witnesses exist for reversal and composition

verified:
    commands 0, 1, 3, 4, 5 and 6 are comparatively inexpensive

verified:
    Glucose composition runtime has substantial run-to-run variance
```

Not established:

```text
which internal part of bisimulation dominates remaining SAT difficulty

whether Slot / Int sequence representation is the main remaining source

whether role matching dominates

whether symmetry breaking is near-optimal

how the optimized command scales with larger semantic bounds

whether another modern SAT solver performs better

whether the CompositionCase representational equivalence should be proved in a
separate formalism
```

## 10. Hybrid decomposition

Alloy 6.2.0 exposes Pardinus decomposition through the Java API:

```text
decompose_mode = 0
    batch / off

decompose_mode = 1
    Hybrid

decompose_mode = 2
    Parallel
```

Historical experiments ran composition with Glucose Hybrid decomposition.

Observed Hybrid executions did not demonstrate a practical advantage over
batch Glucose.

Instrumented Hybrid also generated essentially the same underlying composition
CNF scale before entering a long solver execution.

No evidence established that Hybrid was universally slower or semantically
different.

The dedicated Hybrid job was retained only as an experimental benchmark.

It has now been removed from:

```text
.github/workflows/semantic-core.yml
```

Future routine semantic-core commits therefore execute composition once through
the normal instrumented Glucose matrix.

An already-started historical workflow may still contain a Hybrid job because
GitHub Actions uses the workflow definition from the commit that created that
run.

## 11. Experimental configuration control

Performance experiments must distinguish search controls from changes to the
bounded problem.

Search-strategy candidates include:

```text
SAT solver
symmetry-breaking strength
decompose mode
decompose thread count
partial-instance inference
verification scaffolding that preserves the checked property
```

Controls that may change the bounded problem or semantics include:

```text
scope
exact semantic signature scope
bitwidth
maxseq
unrolls
noOverflow
semantic predicate
facts
assertion meaning
```

These must not be changed merely to obtain a faster green result.

In particular:

```text
smaller semantic scope
```

is not a quality-preserving optimization.

It weakens bounded coverage.

Search-surface reductions must also be justified separately from semantic
changes.

A faster SAT instance is useful only if it still represents the intended
property.

## 12. Runtime policy

Long runtime is experimental evidence.

The research workflow should not automatically impose a short hard solver
timeout merely to keep CI green.

Pathological runtime may indicate:

```text
poor formal encoding
combinatorial explosion
solver mismatch
symmetry problems
unexpected model growth
semantic structure that scales badly
```

GitHub Actions still imposes an external platform execution limit.

If that limit is reached, record:

```text
no result within platform execution limit
```

not:

```text
failed property
```

A future routine verification lane may intentionally impose shorter operational
limits.

If so, it should remain distinct from unrestricted research verification.

## 13. Timing methodology

The Glucose observations demonstrate large runtime variance.

Therefore solver comparisons should use:

```text
multiple repetitions
```

or require an effect substantially larger than observed baseline noise.

For every expensive run retain at minimum:

```text
git commit
Alloy version
runner version

command
effective scopes
expected result

solver
symmetry
partial-instance setting
decomposition mode
decomposition threads

primary variables
total variables
clauses

Alloy-reported solving time
runner wall time

runtime environment
heap observations

final SAT / UNSAT / no-result status
```

A small wall-time difference between two single runs is not strong evidence.

The approximately 18-minute optimized composition result is meaningful because
it is substantially below both previous completed observations, but repeated
measurements would still be required for a stable performance estimate.

## 14. Current evidence summary

```text
IdentityIsBisimulation:
    bounded UNSAT check passes

ReverseIsBisimulation:
    bounded UNSAT check passes
    explicit structural non-vacuity witness passes SAT

CompositionIsBisimulation:
    bounded UNSAT check passes
    explicit compatible three-state non-vacuity witness passes SAT

historical Glucose composition:
    2936 s
    5736 s

optimized composition search surface:
    1073944 ms solver time
    approximately 17 min 54 s
    UNSAT

DistinctEntitiesCanNameEqualValues:
    SAT witness passes

SharingDoesNotForceInequality:
    SAT witness passes

SAT4J composition:
    no result in observed 120-minute isolated run
    no result before observed approximately six-hour sequential cutoff

command isolation:
    working

custom Java runner:
    compiles and executes against pinned Alloy 6.2.0 in GitHub Actions

instrumentation:
    deployed to all semantic-core matrix commands

Hybrid benchmark:
    no demonstrated advantage
    removed from future routine semantic-core workflow runs
```

These findings describe the current bounded experiment only.

They must not be promoted into normative SHEAR semantics without separate
semantic review.

## 15. Next verification work

The core bisimulation experiment is now sufficiently instrumented to stop
making solver tuning the immediate focus.

The next semantic layer is transformation continuity.

Current candidate model:

```text
formal/transformation_model.als
```

Before defining continuity composition or transformation application, verify the
representation itself.

Required bounded properties and witnesses:

```text
unknown continuity differs from explicit disappearance

one -> zero continuity exists

one -> one continuity exists

one -> many continuity exists

many -> one continuity exists

at most one explicit claim exists per source occurrence

continuity claims cannot escape their transformation's source and destination
states

structural equality alone does not manufacture continuity
```

Transformation verification should use a separate entrypoint and CI lane so
changes to transformation experiments do not repeatedly launch the expensive
core composition check.

Only after these representation properties pass should the experiment add:

```text
continuity composition
transformation application
ownership propagation
reference transfer
```

The objective remains:

```text
determine whether the candidate semantic core is sufficiently expressive,
verifiable and operationally tractable without hiding semantic weakness behind
implementation or verification artifacts
```
