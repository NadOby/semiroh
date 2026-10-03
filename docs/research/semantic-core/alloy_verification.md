# Alloy Verification Notes

Status: experimental research  
Branch: `research/semantic-core`  
Alloy version: 6.2.0

This document records verification infrastructure, performance observations and Alloy API findings for the semantic-core experiment.

It is not normative SHEAR semantics.

The semantic experiment itself is described in `docs/semantic_core_experiment.md`. This document records evidence about how the current formal model is checked and how reliable or practical those checks are.

## 1. Current formal model

The current bounded model is in:

```text
formal/core.als
```

The initial command set contains:

```text
0  IdentityIsBisimulation
1  ReverseIsBisimulation
2  CompositionIsBisimulation
3  DistinctEntitiesCanNameEqualValues
4  SharingDoesNotForceInequality
```

The first three are checks expected to be UNSAT.

The last two are witness searches expected to be SAT.

These are bounded results only. Passing a check does not establish a general theorem.

Witness searches establish existence within the selected bounds, not universal validity.

## 2. Command isolation

The first workflow executed all Alloy commands sequentially.

This obscured which command dominated runtime.

The workflow was changed to:

1. discover Alloy command indices;
2. create one GitHub Actions matrix job per command;
3. execute the commands independently and in parallel;
4. preserve each command's original scope and expectation.

This immediately localized nearly all verification cost to:

```text
CompositionIsBisimulation
```

The other commands complete in seconds at the current bounds.

Command isolation should therefore remain part of the verification infrastructure even if the solver strategy changes.

It is useful both for performance and epistemics: one pathological check must not hide successful execution of unrelated checks.

## 3. Solver observations

### 3.1 SAT4J

SAT4J was the initial solver.

At the current bounds:

```text
IdentityIsBisimulation
    completes in seconds

ReverseIsBisimulation
    completes in seconds

DistinctEntitiesCanNameEqualValues
    completes in seconds

SharingDoesNotForceInequality
    completes in seconds

CompositionIsBisimulation
    pathological runtime
```

A previous sequential run and an isolated SAT4J composition run both demonstrated that composition, rather than Alloy invocation in general, is the dominant cost.

Long runtime is retained as diagnostic evidence rather than automatically hidden behind a short timeout.

### 3.2 Glucose

The matrix was repeated with the Alloy 6.2.0 `glucose` solver.

The four inexpensive commands again completed successfully.

The composition check completed successfully with:

```text
result: UNSAT
elapsed: 2936 s
```

Equivalent wall time:

```text
48 min 56 s
```

This is the first completed result for the current composition scope.

It demonstrates that the composition assertion is solvable at the present bounds, but remains operationally expensive.

This result should not be interpreted as a general proof of bisimulation composition.

### 3.3 Interpretation

The evidence currently supports:

```text
verified:
    composition dominates bounded verification cost

verified:
    Glucose can prove the current bounded composition check UNSAT

verified:
    the remaining current commands are comparatively cheap

not yet established:
    why composition is difficult

not yet established:
    whether the main cost is Alloy translation, CNF size,
    SAT search, symmetry, or the relational encoding itself

not yet established:
    whether another solver or decomposition strategy scales better
```

## 4. Decomposed analysis

Alloy 6.2.0 exposes Pardinus decomposition through the Java API:

```text
decompose_mode = 0
    off / batch

decompose_mode = 1
    hybrid

decompose_mode = 2
    parallel
```

It also exposes:

```text
decompose_threads
```

The stock Alloy CLI does not expose these controls directly.

A small Java runner was therefore added at:

```text
.github/scripts/AlloyRunner.java
```

The runner deliberately uses the same main parsing and execution path as normal Alloy execution:

```text
CompUtil.parseEverything_fromFile(...)
TranslateAlloyToKodkod.execute_commandFromBook(...)
```

but allows decomposition parameters to be set explicitly.

Before using it for the expensive command, CI verifies that:

1. the requested command index still names `CompositionIsBisimulation`;
2. the Java runner compiles against the pinned Alloy distribution;
3. the runner can execute a known-fast command in ordinary batch mode;
4. its result matches the command expectation.

A direct comparison is currently running between:

```text
Glucose batch
```

and:

```text
Glucose Hybrid
decompose_threads = 4
```

on the same composition command and same Alloy scopes.

Until that run completes, no performance conclusion about Hybrid decomposition is justified.

## 5. Why the Java API is useful

The Java API provides substantially more experimental control than the stock CLI.

The runner should therefore evolve into a small verification harness rather than remain only a decomposition adapter.

### 5.1 Reporter instrumentation

`A4Reporter` provides callbacks for:

```text
parse(...)
typecheck(...)
warning(...)
scope(...)
bound(...)
translate(...)
solve(...)
resultSAT(...)
resultUNSAT(...)
minimizing(...)
minimized(...)
```

The most immediately useful callback is:

```text
solve(plength, primaryVars, totalVars, clauses)
```

It exposes:

```text
primary SAT variables
total SAT variables
CNF clause count
```

`resultSAT(...)` and `resultUNSAT(...)` additionally provide solver timing.

Together these can distinguish:

```text
large Alloy/Kodkod translation
large generated CNF
hard SAT search
decomposition overhead
```

This is more useful than wall-clock duration alone.

Future expensive runs should record at least:

```text
command
solver
decomposition mode
decomposition threads
symmetry setting
primary variables
total variables
clauses
solver time
wall time
SAT / UNSAT
expected result
```

### 5.2 Solver discovery

`SATFactory` exposes the solvers actually available in the running Alloy distribution.

Useful properties include:

```text
id
name
type
availability
incremental
prover
maxsat
unbounded
description
```

The harness can therefore discover solver capabilities dynamically rather than maintaining an assumed hard-coded solver list.

A future runner mode such as:

```text
--list-solvers
```

would be useful for reproducible solver experiments.

### 5.3 Symmetry breaking

`A4Options.symmetry` controls symmetry breaking.

The default is:

```text
20
```

Alloy's own API documentation notes that stronger symmetry breaking often helps UNSAT problems, although excessive symmetry processing can itself become expensive.

Because the pathological composition command is UNSAT, symmetry is a plausible performance parameter to investigate.

Changing symmetry is intended as a search optimization rather than a change to the bounded property being checked.

It should nevertheless be benchmarked rather than assumed beneficial.

### 5.4 Partial-instance inference

Alloy exposes:

```text
inferPartialInstance
```

which allows bounds to be simplified using inferred partial instances before solving.

This is another performance-related control worth recording explicitly in experiments.

Changing it should not silently become part of the semantic model.

### 5.5 Kodkod recording

Alloy exposes:

```text
recordKodkod
```

which can retain the translated Kodkod representation.

This may help diagnose pathological checks or compare different encodings.

It should be enabled selectively because recording large intermediate representations can itself add cost and generate substantial output.

### 5.6 Unsat cores

With an appropriate prover/core-capable solver, Alloy can expose high-level unsat cores through:

```text
A4Solution.highLevelCore()
```

This maps an UNSAT result back toward source positions.

Potential uses include identifying which parts of a large assertion or fact set are actually involved in the proof.

This is currently a diagnostic possibility, not part of the normal verification lane.

## 6. Command-level control

The Java API exposes parsed `Command` objects directly.

Relevant command data includes:

```text
label
check/run
overall scope
bitwidth
max sequence length
per-signature scopes
exact scopes
expected result
formula
```

`Command` is immutable but provides `change(...)` methods that construct modified commands.

This allows controlled experiments such as:

```text
Rel scope = 3
Rel scope = 4
Rel scope = 5
...
```

without editing `formal/core.als`.

This is particularly useful for measuring scaling curves.

However, scope changes are not merely solver optimizations.

A different scope is a different bounded verification problem.

Results from scope sweeps must therefore always record the exact command scopes and must not be presented as equivalent checks.

## 7. Controls that may change semantics

Performance experiments must distinguish search controls from semantic controls.

Controls that can alter the bounded problem or its semantics include:

```text
scope
bitwidth
maxseq
unrolls
noOverflow
command formula
exact signature scopes
```

These must never be changed merely to obtain a faster green result.

In particular:

```text
smaller scope
```

is not a quality-preserving optimization.

It weakens bounded coverage.

The current reduced scopes were introduced only as an initial bootstrap after larger runs exhausted available resources. They should be treated as explicit bounded assumptions, not as a solver optimization.

## 8. Controls intended primarily for search strategy

Current candidates for performance experiments that preserve the same bounded command include:

```text
SAT solver
symmetry-breaking strength
decompose mode
decompose thread count
partial-instance inference
```

Any comparison should keep all other relevant settings constant.

Prefer A/B experiments with one changed parameter.

## 9. Runtime policy

Long verification runtime is itself evidence.

The research workflow should therefore not automatically convert every long-running command into an arbitrary timeout failure.

A pathological increase in runtime may indicate:

```text
poor encoding
combinatorial explosion
insufficient symmetry breaking
solver mismatch
decomposition failure
unexpected model growth
semantic structure that scales badly
```

Routine CI may eventually need a bounded-duration lane.

If introduced, it should remain distinct from the unrestricted research verification lane.

A timeout means:

```text
no verification result obtained
```

not:

```text
property failed
```

and not:

```text
property passed
```

## 10. Next instrumentation step

Before performing many more expensive solver experiments, extend `AlloyRunner` with an `A4Reporter` implementation that records:

```text
resolved translation configuration
primary variable count
total variable count
clause count
solver time
wall time
result
```

This should be observational instrumentation only.

After that, useful controlled experiments include:

```text
Hybrid versus batch

decomposition thread-count sweep

symmetry sweep

additional SAT solver comparison

scope scaling curve for CompositionIsBisimulation
```

The objective is not merely to make the current check faster.

The objective is to understand why it is expensive and whether the formal representation remains practical as the model grows.

## 11. Current evidence summary

As of the current experiment:

```text
bounded equality identity:
    passes at current scope

bounded bisimulation reversal:
    passes at current scope

bounded bisimulation composition:
    proven UNSAT with Glucose at current scope
    2936 s

distinct EntityIDs naming equal values:
    witness found

shared versus duplicated equal structure:
    witness found

command-level CI isolation:
    working

custom Java Alloy runner:
    compiles and passes batch smoke test

Glucose Hybrid composition:
    experiment in progress

stock Glucose composition repeat:
    experiment in progress
```

These findings describe the current bounded experiment only.

They should not be promoted into normative SHEAR semantics without separate semantic review.
