# Alloy Verification

Status: experimental research  
Branch: `research/semantic-core`  
Alloy version: `6.2.0`

This is the shared index and verification policy for Alloy experiments in the
semantic-core research branch.

It is not:

```text
a normative SHEAR specification
a chronological research log
a detailed result archive
```

Detailed evidence is kept in narrower documents.

## Documentation map

### Core verification

```text
docs/research/semantic-core/core_verification.md
```

Contains:

```text
bisimulation checks
value-equality witnesses
non-vacuity witnesses
solver history
composition performance evidence
search-surface experiments
```

### Transformation verification

```text
docs/research/semantic-core/transformation_verification.md
```

Contains:

```text
continuity representation
continuity composition
continuity associativity
unknown versus disappearance
split / merge witnesses
continuity independence from value equality
mutation evidence
current transformation-layer bounded evidence
```

### Active continuity-composition design

```text
docs/research/semantic-core/continuity_composition.md
```

Contains the candidate continuity-composition algebra and unresolved semantic
questions.

### Alloy API reference

```text
docs/research/semantic-core/alloy_api_reference.md
```

Contains:

```text
Alloy 6.2 Java API observations
runner integration details
solver/decomposition API information
configuration classifications
```

### Project diary

```text
docs/research/semantic-core/project_diary.md
```

Append-only chronological research record.

### Experiment charter

```text
docs/semantic_core_experiment.md
```

Defines the purpose and hypotheses of the semantic-core experiment.

### Peer reviews

```text
docs/research/semantic-core/peer_reviews/
```

External critique and project assessment.

## Formal layout

Candidate core model:

```text
formal/core_model.als
```

Core verification entrypoint:

```text
formal/core.als
```

Candidate transformation/continuity model:

```text
formal/transformation_model.als
```

Transformation verification entrypoints currently include:

```text
formal/transformation.als
formal/transformation_composition.als
formal/transformation_associativity.als
formal/transformation_composition_mutation.als
```

Shared instrumented runner:

```text
.github/scripts/AlloyRunner.java
```

Consolidated Alloy workflow:

```text
.github/workflows/alloy-verification.yml
```

The Python executable semantic-model tests remain separate:

```text
.github/workflows/semantic-model.yml
```

They verify a different implementation layer.

## Separation of semantics and verification

Formal-model structures must be classified explicitly.

A declaration may represent:

```text
candidate semantics
```

or:

```text
Alloy representation scaffolding
verification scaffolding
```

Those categories must not be silently conflated.

Current examples of scaffolding include:

```text
RoleUse
Slot
BisimWitness
CompositionCase
ContinuityClaim
```

unless a later semantic decision explicitly promotes one of them.

Convenience in Alloy is not evidence that an object belongs in the SHEAR
ontology.

## Bounded-result terminology

Alloy results in this research branch are bounded unless explicitly stated
otherwise.

Preferred terminology:

```text
bounded check passed
bounded counterexample found
bounded witness exists
bounded non-vacuity witness exists
experimentally observed
no result
not established
```

Avoid presenting bounded UNSAT as an unbounded theorem.

Avoid presenting SAT as evidence outside the selected bounds.

## Evidence categories

Green Alloy commands do not all carry equal epistemic weight.

Distinguish at least:

### Model sanity check

A check that substantially restates an existing model fact or structural
constraint.

Its value is primarily:

```text
encoding sanity
regression protection
test-harness confirmation
```

### Derived bounded property

A property that follows nontrivially from the candidate model within the
selected scope.

### SAT witness

Demonstrates that an interesting structure is realizable within the selected
scope.

### Negative witness

Demonstrates an intended distinction or inequality.

### Non-vacuity witness

Demonstrates that the important antecedent or scenario of another check is
actually realizable.

For important implication-shaped assertions, prefer pairing:

```text
check Property
```

with:

```text
run PropertyScenarioExists
```

where practical.

## Expected results

Research CI commands encode their expected result explicitly.

Current Alloy syntax uses:

```text
expect 0
```

for expected UNSAT and:

```text
expect 1
```

for expected SAT.

Verification behaviour is:

```text
expect 0 + UNSAT
    pass

expect 1 + SAT
    pass

expect 0 + SAT
    fail

expect 1 + UNSAT
    fail

unspecified expectation
    fail before solver execution
```

The shared runner enforces this contract.

Exploratory execution with unspecified expectations would require a separate
explicit mode if later needed.

## Command isolation

Verification commands run independently where practical.

A pathological command must not hide the result of unrelated properties.

The consolidated workflow:

```text
discovers Alloy commands
constructs a model + command matrix
runs commands in separate matrix jobs
preserves command scopes and expectations
fails if a top-level formal/*.als with commands is not a listed entrypoint
```

Top-level `formal/*.als` files without commands are libraries and need not be
listed.

It runs on every push to:

```text
research/semantic-core
```

This intentionally favors regression coverage over path-filtered execution
while the research branch is active.

## Solver policy

A solver outcome must be classified separately from workflow execution.

Relevant result classes include:

```text
SAT
UNSAT
timeout
cancelled
runner failure
solver unavailable
```

A timeout or cancellation is:

```text
no result
```

unless an actual SAT or UNSAT result was produced first.

It is neither a semantic counterexample nor verification success.

### Routine solver

The current routine Alloy verification solver is:

```text
lingeling.parallel
```

This is an engineering choice based on the expensive
`CompositionIsBisimulation` workload.

It is not:

```text
a semantic commitment
a claim that the solver is universally fastest
```

Detailed solver-performance evidence belongs in:

```text
docs/research/semantic-core/core_verification.md
```

## Runtime policy

Routine verification should remain practical enough to execute on every
research-branch commit without weakening semantic scopes.

For the historically dominant bounded command, the current engineering target
is:

```text
preferred:
    <= 5 minutes

operational solver-selection cutoff:
    10 minutes
```

These are CI practicality criteria, not semantic limits.

Semantic scopes must not be reduced merely to meet them.

Long runtime may reveal:

```text
poor formal encoding
combinatorial explosion
solver mismatch
symmetry problems
unexpected model growth
practicality problems
```

If a run reaches an external execution limit without producing SAT or UNSAT,
record:

```text
no result within execution limit
```

## Experimental-change classification

Before interpreting a faster or slower Alloy run, classify what changed.

### Potentially search-only

Examples:

```text
SAT solver
symmetry-breaking strength
decomposition strategy
decomposition thread count
partial-instance inference
verification scaffolding intended to preserve the checked property
```

### Potentially changes the bounded problem

Examples:

```text
scope
exact signature scope
bitwidth
maxseq
unrolls
noOverflow
facts
semantic predicates
assertion meaning
```

Reducing semantic scope merely to obtain a faster green result is not a
quality-preserving optimization.

It produces a different bounded problem.

## Representational refactors

Verification scaffolding may be refactored to reduce irrelevant search freedom.

When this happens, distinguish:

```text
semantic predicate unchanged
```

from:

```text
SAT encoding unchanged
```

These are not equivalent claims.

If two verification encodings are only argued to represent the same semantic
property, state:

```text
intended representational equivalence
```

unless the equivalence has itself been mechanically established.

## Instrumentation

The shared runner records structured observations including:

```text
runtime environment
solver metadata
effective Alloy options
command metadata
scope and bound events
translation events
CNF events
primary variables
total variables
clauses
solver-result timing
runner wall time
heap observations
warnings
final result
expected result
```

It can enumerate the solver factories exposed by the Alloy distribution with:

```text
AlloyRunner --list-solvers
```

Long-running commands additionally emit heartbeat information.

A heartbeat means only:

```text
the runner process is alive
```

It does not establish SAT-search progress.

For external native solvers, JVM heap observations do not measure the solver
process's native memory use.

## Performance interpretation

Useful H3-related measurements include:

```text
semantic scope
primary SAT variables
total SAT variables
clauses
translation time
solver time
memory observations
```

GitHub-hosted wall-clock measurements can vary substantially.

Small timing differences between isolated runs are weak evidence.

Prefer:

```text
large effects
repeated measurements
structural solver metrics
scope staircases
```

when making performance claims.

## Reproducibility and retained evidence

GitHub Actions logs are temporary.

For reproducible experiments, retain the experiment definition and material
observations rather than automatically committing raw CI artifacts.

Record significant observations with enough context to reproduce them,
including where relevant:

```text
Alloy version
commit
workflow/run provenance
model and command
semantic scope
solver
effective options
CNF dimensions
result
solver time
wall time
```

Raw machine-readable result files should be committed only when they provide
clear research value beyond a reproducible workflow and documented
observations.

## Oracle independence

When executable verification is added, avoid reusing production algorithms in
ways that destroy independence.

Desired directions include:

```text
formal witness
    ->
executable case
    ->
current implementation
```

and:

```text
current-model case
    ->
projection
    ->
candidate-model observation
```

A differential test that merely calls the same implementation on both sides is
not meaningful independent evidence.

## Current high-level status

Core evidence currently includes bounded support for:

```text
bisimulation identity
bisimulation reversal
bisimulation composition
distinct EntityIDs naming equal values
sharing topology not necessarily determining value equality
non-vacuous reversal and composition scenarios
```

Transformation evidence has expanded beyond representation into bounded
continuity-composition and associativity experiments.

Detailed commands, scopes, runs, and interpretation belong in their respective
evidence documents.

## Major open verification targets

Current important open work includes:

```text
information semantics of Unknown
negative equality witnesses
cyclic equality experiments
structured-value continuity witnesses
first CurrentModel -> CandidateCore projection
differential commuting-diagram experiments
entry/view identity experiments
Role bootstrap-boundary experiments
```

These are research targets, not established semantics.

## Documentation rule

Do not allow this file to become a second evidence archive.

Add detailed results to:

```text
core_verification.md
transformation_verification.md
```

Add chronological events and failed experiments to:

```text
project_diary.md
```

This file should remain the compact shared verification policy and navigation
point.
