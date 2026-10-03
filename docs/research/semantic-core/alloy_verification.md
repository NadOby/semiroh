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

## 1. Current formal model

The bounded model is:

```text
formal/core.als
```

Current commands:

```text
0  IdentityIsBisimulation
1  ReverseIsBisimulation
2  CompositionIsBisimulation
3  DistinctEntitiesCanNameEqualValues
4  SharingDoesNotForceInequality
```

Expected results:

```text
0  UNSAT
1  UNSAT
2  UNSAT
3  SAT
4  SAT
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

The first workflow executed all Alloy commands sequentially.

That made one pathological command hide the status of all later commands.

The workflow was changed to:

1. discover Alloy command indices;
2. run each command in an independent GitHub Actions matrix job;
3. preserve the command's original scopes and expectation;
4. allow expensive commands to continue without blocking unrelated results.

This localized nearly all current verification cost to:

```text
CompositionIsBisimulation
```

The other four commands consistently complete in seconds.

Command isolation is therefore both a performance feature and an epistemic
requirement.

A pathological command must not obscure successful or failed verification of
unrelated properties.

## 3. Solver evidence

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

The job reached the GitHub Actions approximately six-hour execution limit.

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

Command 2 was isolated into its own job.

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

The explicit research timeout has since been removed.

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

This was the first completed bounded result for the current composition scope.

It establishes only:

```text
no composition counterexample exists within that bounded command
```

It does not establish general bisimulation composition.

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

The formal model and composition command were unchanged.

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

### 3.5 Current solver interpretation

Current evidence supports:

```text
verified:
    composition dominates current bounded verification cost

verified:
    Glucose can prove the current bounded composition command UNSAT

verified:
    SAT4J is dramatically less practical for this command
    under observed runs

verified:
    commands 0, 1, 3 and 4 are comparatively inexpensive

verified:
    Glucose runtime for composition has substantial run-to-run variance
```

Not established:

```text
why composition is expensive

whether translation or SAT search dominates

whether relational join is the main source of difficulty

whether symmetry breaking is near-optimal

whether decomposition improves this model

whether another solver performs better than Glucose

how runtime scales with scope
```

## 4. Decomposed analysis

Alloy 6.2.0 exposes Pardinus decomposition through the Java API:

```text
decompose_mode = 0
    batch / off

decompose_mode = 1
    Hybrid

decompose_mode = 2
    Parallel
```

The current Hybrid experiment uses:

```text
solver:
    glucose

decompose_mode:
    1

decompose_threads:
    4
```

with the same:

```text
formal model
composition command
scope
expectation
symmetry setting
partial-instance setting
```

as the batch Glucose comparison.

Therefore decomposition mode is the intentional independent variable.

An earlier Hybrid run exceeded both completed batch Glucose timings without
producing a result at the time it was inspected.

That establishes:

```text
no observed Hybrid speed advantage in that run
```

but not yet:

```text
Hybrid is universally slower
Hybrid is hung
Hybrid cannot solve the command
```

A long silent period was particularly difficult to interpret because the
original runner used:

```java
A4Reporter.NOP
```

and therefore emitted no internal translation/solver diagnostics while
executing.

This motivated the instrumented runner.

## 5. Instrumented runner

The experimental runner is:

```text
.github/scripts/AlloyRunner.java
```

It uses:

```text
CompUtil.parseEverything_fromFile(...)
TranslateAlloyToKodkod.execute_commandFromBook(...)
```

rather than constructing a separate solver pipeline.

The runner now records:

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

The relevant API details and classifications are documented in:

```text
docs/research/semantic-core/alloy_api_reference.md
```

## 6. Instrumented workflow migration

The workflow now routes every normal matrix command through
`AlloyRunner`, rather than using the stock Alloy CLI for normal commands and
the custom runner only for Hybrid.

Current workflow:

```text
.github/workflows/semantic-core.yml
```

Run:

```text
37156350195
```

verified the migration operationally.

Completed successfully through the instrumented runner:

```text
command 0
command 1
command 3
command 4
```

At the latest inspection:

```text
command 2 batch Glucose:
    in progress

command 2 Hybrid Glucose:
    in progress
```

This establishes that instrumentation itself does not prevent the inexpensive
commands from executing and satisfying their expectations.

The long composition jobs are now positioned to produce substantially more
diagnostic information than the historical CLI runs.

## 7. Experimental configuration control

Performance experiments must distinguish search controls from changes to the
bounded problem.

Search-strategy candidates include:

```text
SAT solver
symmetry-breaking strength
decompose mode
decompose thread count
partial-instance inference
```

These should normally be varied one at a time.

Controls that may change the bounded problem or semantics include:

```text
scope
exact signature scope
bitwidth
maxseq
unrolls
noOverflow
command formula
facts
assertions
```

These must not be changed merely to obtain a faster green result.

In particular:

```text
smaller scope
```

is not a quality-preserving optimization.

It weakens bounded coverage.

## 8. Runtime policy

Long runtime is experimental evidence.

The research workflow should not automatically impose a short hard solver
timeout merely to keep CI green.

Pathological runtime may indicate:

```text
poor formal encoding
combinatorial explosion
solver mismatch
symmetry problems
decomposition failure
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

If so, it should remain distinct from the unrestricted research lane.

## 9. Timing methodology

The current Glucose observations demonstrate large runtime variance.

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

## 10. Potential composition pathology

The current assertion checks composition of two explicit bisimulation
witnesses.

Conceptually:

```text
first.pairs
second.pairs
```

are relational witnesses and composition uses:

```text
(first.pairs).(second.pairs)
```

The bounded command contains:

```text
3 State
6 Rel
2 Role
6 RoleUse
6 Slot
3 Atom
exactly 2 BisimWitness
```

A plausible hypothesis is that the search space involving:

```text
two arbitrary valid bisimulation relations
plus relational composition
plus an UNSAT proof obligation
```

is expensive.

This is currently a hypothesis.

It is not yet supported by profiling evidence.

The new CNF and timing instrumentation should help determine whether cost is
primarily associated with:

```text
translation
CNF size
SAT search
decomposition
```

before changing the formal encoding.

## 11. Non-vacuity risk

Passing:

```text
ReverseIsBisimulation
```

and:

```text
CompositionIsBisimulation
```

does not by itself prove that the checked implication is exercised by a useful
model.

For composition, the antecedent includes:

```text
first.right = second.left
```

If no suitable pair of witnesses exists within the selected bounds, the
assertion could pass vacuously.

Therefore bounded theorem checks must be paired with explicit witness searches
showing that their important antecedents are realizable.

Required future witnesses include:

```text
a valid nontrivial BisimWitness for reversal

two valid BisimWitness objects such that:
    first.right = second.left

preferably:
    their relational composition is nonempty
```

Until these exist, bounded composition success carries a residual
false-confidence risk.

## 12. Current evidence summary

```text
IdentityIsBisimulation:
    bounded UNSAT check passes

ReverseIsBisimulation:
    bounded UNSAT check passes
    non-vacuity witness still required

CompositionIsBisimulation:
    bounded UNSAT check passes with Glucose
    2936 s in one run
    5736 s in another run
    non-vacuity witness still required

DistinctEntitiesCanNameEqualValues:
    SAT witness found

SharingDoesNotForceInequality:
    SAT witness found

SAT4J composition:
    no result in observed 120-minute isolated run
    no result before observed 6-hour sequential cutoff

command isolation:
    working

custom Java runner:
    compiles against pinned Alloy 6.2.0 in GitHub Actions

instrumentation:
    deployed to all normal matrix commands

instrumented inexpensive commands:
    successful

instrumented batch composition:
    in progress at latest inspection

instrumented Hybrid composition:
    in progress at latest inspection
```

These findings describe the current bounded experiment only.

They must not be promoted into normative SHEAR semantics without separate
semantic review.

## 13. Next verification steps

Immediate priorities:

```text
1. collect the first complete instrumented composition result;

2. compare batch and Hybrid:
       translation events
       CNF sizes
       solver-reported time
       wall time
       memory behaviour;

3. add explicit non-vacuity witnesses for reversal and composition;

4. only then run controlled search-strategy experiments such as:
       symmetry sweep
       decomposition thread sweep
       additional solver comparison;

5. later measure scope scaling without presenting smaller scopes
   as equivalent verification.
```

The objective is not merely to make Alloy green or fast.

The objective is to determine whether the candidate semantic core is
verifiable without hiding semantic weakness or impractical computational cost.
