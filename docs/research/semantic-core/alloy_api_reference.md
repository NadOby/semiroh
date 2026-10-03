# Alloy 6.2 API Reference for Semantic-Core Experiments

Status: experimental infrastructure reference  
Branch: `research/semantic-core`  
Pinned Alloy version: `6.2.0`

This document records the Alloy Java API controls relevant to the SHEAR
semantic-core experiment.

Its purpose is to avoid repeatedly rediscovering Alloy 6.2 behaviour from
upstream source while designing verification experiments.

This is not normative SHEAR semantics.

Where behaviour matters to experimental validity, distinguish:

```text
semantic / bounded-problem control
search-strategy control
diagnostic control
output / infrastructure control
```

Changing the first category changes what is being checked.

Changing search strategy should preserve the same bounded problem, but may
substantially alter runtime.

Diagnostic controls should not affect the result being checked.

## 1. Execution environment

All Alloy execution for this experiment occurs in GitHub Actions.

The repository does not rely on local execution of the Alloy JAR.

Pinned environment:

```text
Alloy:
    6.2.0

Java:
    17

formal model:
    formal/core.als

runner:
    .github/scripts/AlloyRunner.java

workflow:
    .github/workflows/semantic-core.yml
```

The workflow downloads and caches the official Alloy 6.2.0 distribution JAR.

The Java runner is compiled against that JAR inside GitHub Actions.

Successful runner compilation is therefore also an API-compatibility check
against the pinned Alloy release.

## 2. Main execution path

The custom runner deliberately follows Alloy's standard execution path:

```java
CompUtil.parseEverything_fromFile(...)
TranslateAlloyToKodkod.execute_commandFromBook(...)
```

The runner does not directly construct Kodkod formulas.

This keeps the experimental harness close to stock Alloy while exposing Java
API controls unavailable or inconvenient through the CLI.

## 3. `A4Options`

`A4Options` is the principal mutable configuration object for
Alloy-to-Kodkod translation and solving.

All defaults below are Alloy 6.2.0 defaults.

### 3.1 `inferPartialInstance`

```java
boolean inferPartialInstance = true;
```

Classification:

```text
search / preprocessing control
```

Purpose:

Alloy may infer a partial instance and simplify bounds before solving.

Expected effect:

```text
same intended bounded problem
possibly smaller search space
possibly different translation cost
```

For controlled benchmarks, record this value.

Current SHEAR runner:

```text
true
```

### 3.2 `symmetry`

```java
int symmetry = 20;
```

Classification:

```text
search-strategy control
```

Purpose:

Controls the amount of symmetry breaking performed by Alloy.

Upstream guidance states approximately:

```text
UNSAT:
    stronger symmetry breaking often helps

SAT:
    weaker symmetry breaking often helps

too much symmetry analysis:
    can itself become expensive
```

The default is:

```text
20
```

This is a particularly relevant parameter for:

```text
CompositionIsBisimulation
```

because the current bounded result is UNSAT.

Changing symmetry should not be described as changing verification scope.

However, benchmarks must record it because it can significantly affect
runtime and CNF structure.

### 3.3 `skolemDepth`

```java
int skolemDepth = 0;
```

Classification:

```text
translation control
potentially representation-sensitive
```

Purpose:

Controls maximum Skolem-function depth.

Default:

```text
0
```

which permits Skolem constants but not deeper Skolem functions.

Do not vary this casually in performance benchmarks without understanding the
effect on translation and generated instances.

### 3.4 `coreMinimization`

```java
int coreMinimization = 2;
```

Classification:

```text
diagnostic / UNSAT-core control
```

Modes documented by Alloy:

```text
0 = guaranteed local minimum
1 = faster, less accurate
2 = faster strategy
```

Current default:

```text
2
```

Relevant primarily when using a solver capable of producing UNSAT proofs /
cores.

It is not currently part of the ordinary semantic-core verification result.

### 3.5 `coreGranularity`

```java
int coreGranularity = 0;
```

Classification:

```text
diagnostic / UNSAT-core control
```

Purpose:

Controls how deeply Alloy expands formulas when constructing an UNSAT core.

Documented range includes:

```text
0:
    top-level conjuncts

3:
    expands quantifiers
```

Higher granularity may provide more precise diagnostic cores at additional
cost.

### 3.6 `solver`

```java
SATFactory solver = SATFactory.DEFAULT;
```

Classification:

```text
search-strategy control
```

Stock default:

```text
SAT4J
```

The semantic-core workflow currently explicitly selects:

```text
glucose
```

Changing the SAT solver should preserve the same bounded Alloy problem, but
runtime characteristics can differ dramatically.

Observed example for current composition check:

```text
SAT4J:
    no result within 120 minutes in isolated run
    no result before 6-hour Actions cutoff in earlier sequential run

Glucose:
    UNSAT in 2936 s
    UNSAT in 5736 s
```

These timings also show substantial run-to-run variance.

### 3.7 `solverDirectory`

```java
String solverDirectory = "";
```

Classification:

```text
infrastructure control
```

Purpose:

Base directory for external solver binaries when a solver refers to a
relative executable path.

Not relevant to the currently used built-in/native Glucose configuration.

### 3.8 `tempDirectory`

```java
String tempDirectory = System.getProperty("java.io.tmpdir");
```

Classification:

```text
infrastructure control
```

Purpose:

Directory for temporary Alloy files.

Should not affect semantics.

May matter for external solvers, CNF recording or diagnostic output.

### 3.9 `originalFilename`

```java
String originalFilename = "";
```

Classification:

```text
diagnostic metadata
```

Purpose:

Records the original source filename for generated comments and diagnostics.

The custom runner explicitly sets:

```java
options.originalFilename = model;
```

This should not alter the checked problem.

### 3.10 `recordKodkod`

```java
boolean recordKodkod = false;
```

Classification:

```text
diagnostic control
```

Purpose:

Retains original Kodkod input and resulting Kodkod information.

Potential use:

```text
inspect problematic translation
compare encodings
retain generated backend representation
diagnose unexpected CNF growth
```

Possible cost:

```text
additional memory
additional output
additional I/O
```

Default and current setting:

```text
false
```

Enable only for targeted diagnosis.

### 3.11 `noOverflow`

```java
boolean noOverflow = false;
```

Classification:

```text
SEMANTIC / bounded-problem control
```

Purpose:

When enabled, only solutions without arithmetic overflow are accepted.

Changing this can change SAT/UNSAT results.

Therefore:

```text
noOverflow=false
```

and:

```text
noOverflow=true
```

must be treated as different verification configurations.

It must not be changed merely to improve runtime.

### 3.12 `unrolls`

```java
int unrolls = -1;
```

Classification:

```text
SEMANTIC / translation control
```

Purpose:

Controls recursion / loop unrolling.

Default:

```text
-1
```

meaning unrolling is disabled unless otherwise required/configured.

Changing this can alter what recursive constructs are represented and must not
be considered a pure performance optimization.

### 3.13 `decompose_mode`

```java
int decompose_mode = 0;
```

Classification:

```text
search-strategy control
```

Modes:

```text
0 = off / batch
1 = hybrid
2 = parallel
```

Current baseline:

```text
0
```

Current decomposition experiment:

```text
1
```

The stock Alloy CLI does not expose this setting directly in the execution path
used by this project.

The custom Java runner exists partly to expose this control explicitly.

### 3.14 `decompose_threads`

```java
int decompose_threads = 4;
```

Classification:

```text
search-strategy / execution control
```

Default:

```text
4
```

Relevant when decomposition is enabled.

For reproducible decomposition benchmarks, record both:

```text
decompose_mode
decompose_threads
```

Changing thread count should not change the bounded property, but may alter:

```text
wall time
CPU scheduling
memory consumption
search order
runtime variance
```

## 4. Current complete `A4Options` baseline

The current instrumented batch Glucose configuration is:

```text
solver               = glucose
inferPartialInstance = true
symmetry             = 20
skolemDepth           = 0
coreMinimization      = 2
coreGranularity       = 0
recordKodkod          = false
noOverflow            = false
unrolls               = -1
decompose_mode        = 0
decompose_threads     = 4
originalFilename      = formal/core.als
```

Hybrid composition differs only in:

```text
decompose_mode = 1
```

All other listed settings remain unchanged.

This makes the current batch-versus-Hybrid experiment a controlled comparison.

## 5. Stock CLI comparison

Alloy 6.2.0 CLI creates an `A4Options` object using the same defaults.

For the invocation previously used by SHEAR:

```text
alloy exec
    --solver glucose
    --command <index>
    formal/core.als
```

the effective solver-related defaults correspond to the Java runner baseline:

```text
solver               = glucose
inferPartialInstance = true
symmetry             = 20
skolemDepth           = 0
coreMinimization      = 2
coreGranularity       = 0
recordKodkod          = false
noOverflow            = false
unrolls               = -1
decompose_mode        = 0
decompose_threads     = 4
```

Therefore switching ordinary matrix execution from the stock CLI to
`AlloyRunner` does not intentionally change the bounded verification problem or
search configuration.

It adds instrumentation.

### 5.1 CLI symmetry quirk

In Alloy 6.2.0 source, the CLI exposes a symmetry option, but `_exec()` assigns:

```java
opt.symmetry = options.depth(opt.symmetry);
```

rather than using the symmetry accessor.

This appears inconsistent with the CLI option declaration.

It does not affect the historical SHEAR runs because no depth or symmetry
override was supplied.

For controlled research experiments, prefer the Java API and explicitly record
the actual `A4Options.symmetry` value.

## 6. `A4Reporter`

`A4Reporter` provides observational callbacks from parsing, translation and
solving.

The SHEAR runner uses these callbacks to expose backend behaviour without
changing the checked formula.

### 6.1 `warning`

Instrumented signature:

```java
warning(ErrorWarning warning)
```

Current output:

```text
ALLOY_TRACE event=warning ...
```

Purpose:

Retain Alloy warnings in CI logs.

Warnings must not silently disappear merely because verification returned the
expected SAT/UNSAT result.

### 6.2 `scope`

Instrumented signature:

```java
scope(String message)
```

Current output:

```text
ALLOY_TRACE event=scope ...
```

Purpose:

Expose Alloy's resolved scope information.

Useful when verifying that a supposedly identical benchmark actually used the
same bounded universe.

### 6.3 `bound`

Instrumented signature:

```java
bound(String message)
```

Current output:

```text
ALLOY_TRACE event=bound ...
```

Purpose:

Expose computed bounds and bound-processing information.

Useful for diagnosing:

```text
unexpected instance-space growth
partial-instance effects
different translation structure
```

### 6.4 `translate`

Instrumented signature:

```java
translate(
    String solver,
    int bitwidth,
    int maxseq,
    int mintrace,
    int maxtrace,
    int skolemDepth,
    int symmetry,
    String strategy
)
```

Current output:

```text
ALLOY_METRIC event=translate ...
```

Recorded fields:

```text
solver
bitwidth
maxseq
mintrace
maxtrace
skolem_depth
symmetry
strategy
elapsed_ms
sequence
```

This callback provides the effective translation configuration rather than only
the settings requested by the runner.

### 6.5 `solve`

Instrumented signature:

```java
solve(
    int plength,
    int primaryVars,
    int totalVars,
    int clauses
)
```

Current output:

```text
ALLOY_METRIC event=cnf ...
```

Recorded fields:

```text
prefix_length
primary_vars
total_vars
clauses
elapsed_ms
sequence
```

This is currently one of the most important diagnostic hooks.

It lets us distinguish:

```text
large relational translation
large SAT encoding
hard SAT search
```

For decomposition, multiple solve/CNF events may occur.

Therefore events are numbered rather than assuming exactly one CNF per command.

### 6.6 `resultSAT`

Instrumented signature:

```java
resultSAT(
    Object command,
    long solvingTime,
    Object solution
)
```

Current output:

```text
ALLOY_METRIC event=solver_result result=SAT ...
```

The reported time comes from Alloy/backend execution rather than the outer
GitHub Actions wall clock.

### 6.7 `resultUNSAT`

Instrumented signature:

```java
resultUNSAT(
    Object command,
    long solvingTime,
    Object solution
)
```

Current output:

```text
ALLOY_METRIC event=solver_result result=UNSAT ...
```

This is especially relevant for:

```text
IdentityIsBisimulation
ReverseIsBisimulation
CompositionIsBisimulation
```

### 6.8 `minimizing`

Instrumented signature:

```java
minimizing(
    Object command,
    int before
)
```

Purpose:

Reports start of UNSAT-core minimization.

Current output:

```text
ALLOY_METRIC event=core_minimization_start ...
```

### 6.9 `minimized`

Instrumented signature:

```java
minimized(
    Object command,
    int before,
    int after
)
```

Purpose:

Reports result of UNSAT-core minimization.

Current output:

```text
ALLOY_METRIC event=core_minimization_end ...
```

## 7. Runner-level instrumentation

Not all useful diagnostics come directly from Alloy.

The custom runner also records process-level data.

### 7.1 Runtime environment

Recorded:

```text
Java version
VM name
available processors
maximum JVM heap
```

Output prefix:

```text
ALLOY_METRIC event=runtime
```

This matters because GitHub-hosted runners may vary between executions.

### 7.2 Memory observations

Recorded at startup and completion:

```text
heap used
heap committed
heap maximum
```

Output:

```text
ALLOY_METRIC event=memory
```

These are JVM-level observations, not total operating-system process memory.

### 7.3 Heartbeat

During execution the runner emits approximately once per minute:

```text
ALLOY_HEARTBEAT
```

with:

```text
elapsed_s
heap_used_mb
heap_committed_mb
heap_max_mb
```

Interpretation:

```text
heartbeat present:
    Java process remains alive

heartbeat absent:
    not sufficient by itself to diagnose solver failure

changing heap:
    evidence of JVM allocation behaviour

constant heap:
    not evidence that the SAT solver is making no progress
```

The heartbeat does NOT measure SAT search progress.

It exists to avoid multi-hour periods of completely silent CI execution.

### 7.4 Wall-clock phases

The runner records:

```text
parse wall time
execute wall time
total wall time
```

These should be compared with Alloy's own reported solver time.

Useful decomposition:

```text
total
    = startup
    + parsing
    + translation
    + solving
    + result processing
```

The reporter provides additional intermediate timestamps to estimate where time
is being spent.

## 8. `SATFactory`

`SATFactory` represents available solver implementations.

Important capabilities include:

```text
solver ID
solver name
solver type
incremental support
proof / prover support
MaxSAT support
unbounded support
availability
description
```

The runner currently resolves a solver using:

```java
SATFactory.find(solverId)
```

If the requested solver is not available, execution fails rather than silently
falling back to another solver.

This is required for trustworthy solver benchmarks.

### 8.1 Solver ID

Use the factory ID as the canonical experimental identifier.

Examples verified in Alloy 6.2.0:

```text
sat4j
glucose
minisat
```

Do not infer additional solver IDs from names or old Alloy documentation.

Verify them against the pinned distribution before use.

### 8.2 Incremental capability

Incremental solvers can support enumeration of subsequent solutions.

This matters for:

```java
A4Solution.next()
```

but is not central to the current UNSAT composition benchmark.

### 8.3 Prover capability

Proof-capable solvers may expose UNSAT cores.

This is required for meaningful use of:

```java
A4Solution.highLevelCore()
```

Do not assume ordinary Glucose execution provides useful high-level cores.

### 8.4 Dynamic solver discovery

A future runner mode should expose installed solver metadata directly, for
example:

```text
--list-solvers
```

Desired output:

```text
id
name
type
available
incremental
prover
maxsat
unbounded
description
```

This will make solver experimentation self-describing inside GitHub Actions.

## 9. `Command`

Parsed Alloy commands are represented as immutable `Command` objects.

Relevant properties include:

```text
label
check versus run
formula
overall scope
bitwidth
max sequence length
per-signature scopes
exactness of signature scopes
expected result
```

The runner currently records:

```text
index
kind
label
expected
overall_scope
bitwidth
maxseq
scope_count
string form of command
```

### 9.1 Expected result

Alloy command expectation values used by the current runner:

```text
0  = UNSAT expected
1  = SAT expected
other = unspecified
```

The runner independently enforces these after solving.

Therefore:

```text
expected UNSAT + actual SAT
```

fails the job.

Likewise:

```text
expected SAT + actual UNSAT
```

fails the job.

### 9.2 Programmatic command changes

`Command` provides `change(...)` methods capable of producing modified command
objects.

This permits controlled scope experiments without editing the `.als` source.

Potential use:

```text
CompositionIsBisimulation

Rel = 3
Rel = 4
Rel = 5
Rel = 6
```

Such experiments can produce useful scaling curves.

However:

```text
changing scope = changing the bounded verification problem
```

It is not a pure performance optimization.

Every programmatically modified command must therefore log the full effective
scope.

## 10. `A4Solution`

`A4Solution` represents the result of solving a command.

### 10.1 `satisfiable()`

```java
boolean satisfiable()
```

Returns whether the solved instance is SAT.

This is the runner's authoritative final SAT/UNSAT classification.

### 10.2 `next()`

```java
A4Solution next()
```

Requests the next solution.

Requires an incremental solver.

Potential use:

```text
witness enumeration
model diversity checks
checking whether one witness shape dominates
```

Not currently used in the semantic-core CI.

### 10.3 `highLevelCore()`

```java
Pair<Set<Pos>, Set<Pos>> highLevelCore()
```

For an UNSAT solution with suitable proof information, returns source-level
positions participating in the high-level core.

Potential use:

```text
identify facts necessary for UNSAT
diagnose unexpectedly strong invariants
detect assertions made trivial by unrelated facts
```

This may become important for checking false confidence in the formal model.

A small UNSAT core does not by itself prove the model is correct.

It only identifies constraints sufficient for the bounded UNSAT result.

## 11. Controls by experimental category

### 11.1 Safe observational changes

These may be added without intentionally changing the bounded problem:

```text
A4Reporter instrumentation
wall-clock timing
JVM memory measurement
heartbeat
solver metadata reporting
recording effective options
logging scopes
logging bounds
logging CNF sizes
```

`recordKodkod` is also diagnostic but may introduce substantial resource
overhead.

### 11.2 Search-strategy experiments

These are candidates for controlled performance A/B tests:

```text
solver
symmetry
decompose_mode
decompose_threads
inferPartialInstance
```

Change one at a time where practical.

Repeat expensive benchmarks because current Glucose results show substantial
runtime variance.

### 11.3 Different bounded problems

The following must NOT be presented as quality-preserving speedups:

```text
smaller scope
different exact scopes
different bitwidth
different maxseq
different command formula
different unrolls where relevant
different noOverflow semantics
```

They may be useful experiments, but must be labelled as different bounded
problems.

## 12. Benchmark interpretation

For each expensive run, retain at minimum:

```text
git commit
Alloy version
Java version

command index
command label
check/run
expected result

solver

symmetry
inferPartialInstance
skolemDepth
noOverflow
unrolls

decompose_mode
decompose_threads

bitwidth
maxseq
resolved scopes

primary variables
total variables
clauses

Alloy/backend solve time
runner execute wall time
runner total wall time

maximum/observed heap
final SAT/UNSAT result
```

For decomposed runs, retain every CNF event rather than only the last one.

## 13. Current performance evidence

Current composition benchmark:

```text
command:
    CompositionIsBisimulation

current scope:
    unchanged between reported benchmark runs
```

Observed:

```text
SAT4J isolated:
    > 120 min
    terminated by workflow timeout
    no semantic result

SAT4J earlier sequential:
    composition still unresolved when GitHub Actions terminated
    the job at approximately 6 h
    no semantic result

Glucose run 1:
    UNSAT
    2936 s
    48 min 56 s

Glucose run 2:
    UNSAT
    5736 s
    95 min 36 s

Glucose Hybrid:
    experimental
    historically exceeded both completed batch Glucose timings
    final interpretation must use the corresponding run result
```

Important consequence:

```text
single-run wall time is not a stable performance estimator
```

The two successful Glucose runs differ by nearly a factor of two.

Therefore performance comparisons should prefer:

```text
large effects
or
multiple repetitions
```

over conclusions based on small timing differences.

## 14. Known limitations of current instrumentation

The heartbeat establishes process liveness only.

It does not expose:

```text
SAT conflicts
learned clauses
restart count
decision count
propagation count
percentage complete
remaining search space
```

The `solve(...)` reporter callback reports generated CNF size but not continuous
SAT-search progress.

Native solver-specific statistics may require deeper integration than the
standard Alloy `A4Reporter` interface.

Do not infer solver progress from elapsed time or stable heap usage.

## 15. Planned runner extensions

Useful next additions:

```text
dynamic --list-solvers mode

explicit symmetry argument

explicit inferPartialInstance argument

structured machine-readable metrics output

scope override / sweep support

optional recordKodkod mode

optional prover/core experiment mode
```

These should be added only when needed by an experiment.

Avoid turning the verification harness into a second Alloy CLI without a clear
research purpose.

## 16. Source-of-truth policy

For this branch:

```text
formal/core.als
    source of the bounded formal model

.github/scripts/AlloyRunner.java
    source of execution/instrumentation behaviour

.github/workflows/semantic-core.yml
    source of CI orchestration

docs/research/semantic-core/alloy_api_reference.md
    local reference for verified Alloy 6.2 API behaviour

docs/research/semantic-core/alloy_verification.md
    experiment results and interpretation
```

If the pinned Alloy version changes, this document must be revalidated.

Do not assume these API details remain identical in later Alloy releases.
