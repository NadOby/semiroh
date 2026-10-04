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
unknown versus disappearance
split / merge witnesses
continuity independence from value equality
current transformation-layer bounded evidence
```

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

Use it for:

```text
experiments
failed approaches
counterexamples
interpretations
decisions
corrections
```

### Research handoff

```text
handoff.md
```

Compact authoritative continuation state.

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

Transformation verification entrypoint:

```text
formal/transformation.als
```

Shared instrumented runner:

```text
.github/scripts/AlloyRunner.java
```

Core workflow:

```text
.github/workflows/semantic-core.yml
```

Transformation workflow:

```text
.github/workflows/transformation.yml
```

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

Avoid presenting:

```text
UNSAT
```

as an unbounded theorem.

Avoid presenting:

```text
SAT
```

as evidence outside the selected bounds.

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

Research CI commands should encode hypotheses explicitly.

Current Alloy syntax uses:

```text
expect 0
```

for expected UNSAT and:

```text
expect 1
```

for expected SAT.

Desired verification behaviour is:

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
    fail in verification CI
```

The current runner enforces declared expectations but still permits an
unspecified expectation.

Rejecting unspecified expectations is an accepted verification-hardening task.

Exploratory execution may later support an explicit mode that allows
unspecified outcomes.

## Command isolation

Verification commands should run independently where practical.

A pathological command must not hide the result of unrelated properties.

The current workflows therefore:

```text
discover Alloy commands
run commands in separate matrix jobs
preserve command scopes and expectations
```

Core and transformation verification also use separate workflows.

This prevents transformation-only research from repeatedly launching the
expensive core composition experiment.

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

It is not a semantic counterexample.

It is not verification success.

## Runtime policy

The unrestricted research workflows should not impose short solver timeouts
merely to keep CI fast or green.

Long runtime may itself reveal:

```text
poor formal encoding
combinatorial explosion
solver mismatch
symmetry problems
unexpected model growth
practicality problems
```

GitHub Actions still imposes external platform limits.

If a run reaches such a limit, record:

```text
no result within platform execution limit
```

A future routine regression lane may intentionally use operational time limits.

If so, keep that distinct from unrestricted research verification.

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

Long-running commands additionally emit heartbeat information.

A heartbeat means only:

```text
the runner process is alive
```

It does not establish SAT-search progress.

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

## Machine-readable evidence

The runner already emits structured metric lines.

Important research results should eventually survive ordinary GitHub Actions log
retention.

Accepted direction:

```text
complete CI artifacts where useful
+
small versioned machine-readable records for significant results
```

Possible formats:

```text
JSON
JSONL
```

The exact persistent-result layout has not yet been chosen.

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

Transformation evidence currently includes bounded support for representing:

```text
unknown continuity
explicit disappearance
unique continuation
split
merge
multiple independent continuity claims
equal values without inferred continuity
```

Detailed commands, scopes, runs and interpretation belong in their respective
evidence documents.

## Major open verification targets

Current important open work includes:

```text
continuity composition
continuity associativity
information semantics of Unknown
negative equality witnesses
cyclic equality experiments
structured-value continuity witnesses
explicit-expect CI hardening
persistent machine-readable results
formal mutation experiments
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

Add current continuation state to:

```text
handoff.md
```

This file should remain the compact shared verification policy and navigation
point.
