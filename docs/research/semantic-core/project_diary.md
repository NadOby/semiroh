# Semantic Core Project Diary

Branch: `research/semantic-core`  
Status: append-only research log  
Timezone: `Europe/Berlin`

This file records the chronological development of the semantic-core experiment.

It is not:

```text
a normative SHEAR specification
the current research handoff
a replacement for verification evidence documents
```

Current continuation state belongs in:

```text
handoff.md
```

Detailed formal evidence belongs in the relevant verification documents.

## Diary rules

Entries are appended chronologically.

Entry headings use ISO-8601 timestamps with the local Europe/Berlin UTC offset:

```text
YYYY-MM-DDTHH:MM+HH:MM
```

For example:

```text
2026-10-04T05:56+02:00
```

Historical entries are not rewritten merely because later evidence changes the
interpretation.

If an earlier entry becomes incorrect or incomplete, append a new entry that
references and corrects it.

When useful, distinguish:

```text
FACT
INTERPRETATION
DECISION
OPEN
```

These labels describe epistemic status:

```text
FACT
    directly established by repository state, executed experiment, or other
    concrete evidence

INTERPRETATION
    current explanation of established observations

DECISION
    research or architectural choice made at that point

OPEN
    unresolved question, hypothesis, or planned experiment
```

Commit timestamps, GitHub Actions timestamps and other external event times
should be recorded separately when they matter.

The diary-entry timestamp records when the diary entry itself was made. It must
not be presented as the exact timestamp of reconstructed historical events.

---

## 2026-10-04T05:56+02:00 – Retrospective baseline

This first entry is a retrospective baseline reconstructed from the current
branch and recorded evidence.

It is intentionally not a fabricated event-by-event history.

### FACT

The semantic-core experiment is isolated on:

```text
research/semantic-core
```

Its purpose is to test three independent hypotheses:

```text
H1 – representation
H2 – construction
H3 – practicality
```

The candidate relational core currently has formal Alloy representation in:

```text
formal/core_model.als
```

with verification experiments in:

```text
formal/core.als
```

The transformation/continuity layer currently has candidate representation in:

```text
formal/transformation_model.als
```

with verification experiments in:

```text
formal/transformation.als
```

The current candidate distinguishes:

```text
structural/value equality
semantic/domain equivalence
continuity
transformation
```

and does not assume that one implies another.

### FACT – Core verification

The core experiment has dedicated GitHub Actions verification and an
instrumented Alloy 6.2 runner.

Important bounded experiments currently include:

```text
IdentityIsBisimulation
ReverseIsBisimulation
CompositionIsBisimulation
DistinctEntitiesCanNameEqualValues
SharingDoesNotForceInequality
ReverseWitnessExists
CompositionWitnessesExist
```

Explicit non-vacuity witnesses were added for the reversal and composition
properties.

Glucose successfully completed the bounded composition check.

The composition experiment was initially expensive.

Observed completed Glucose solver durations included approximately:

```text
48 min 56 s
95 min 36 s
```

Verification-only search-surface reduction later produced an observed solve of
approximately:

```text
17 min 54 s
```

in run:

```text
37159091258
```

The reduced search surface changed verification scaffolding rather than the
candidate `bisimulation` predicate.

Representational equivalence of the old and new scaffolding was argued but was
not independently mechanically proved.

Instrumentation showed that the dominant observed cost was SAT search rather
than parsing, Alloy loading, CNF translation, or JVM heap pressure.

Hybrid decomposition showed no demonstrated practical advantage and was removed
from the routine semantic-core workflow.

### FACT – Transformation continuity representation

The candidate transformation layer explicitly distinguishes:

```text
Unknown

Known({})
    explicit disappearance

Known({x, ...})
    declared continuation
```

The Alloy representation uses `ContinuityClaim` as modeling scaffolding so that
unknown continuity is distinguishable from explicit disappearance.

The initial transformation verification suite contains bounded checks and
witnesses for:

```text
unknown versus disappearance
1 -> 0 disappearance
1 -> 1 continuation
1 -> many split
many -> 1 merge
one claim per source occurrence
state containment
independent claims
equal values without inferred continuity
```

The first complete successful transformation verification run was:

```text
37161864993
```

All transformation commands `0` through `9` met their declared expectations.

### FACT – Verification infrastructure

Core and transformation experiments use separate CI lanes.

This prevents transformation-only experiments from repeatedly launching the
expensive core composition check.

The shared runner:

```text
.github/scripts/AlloyRunner.java
```

records structured information including:

```text
command
expected result
solver
effective options
scope/bound events
translation events
CNF variables
clauses
solver result timing
wall timing
memory observations
final SAT / UNSAT result
```

The runner currently enforces declared:

```text
expect 0
expect 1
```

results but does not yet reject commands whose expectation is unspecified.

### FACT – Current candidate limitations

The Alloy `View` currently contains:

```text
state
entry
entities
```

but the `entities` mapping is not derived from `entry`.

Therefore current evidence supports:

```text
view-scoped EntityID mapping
```

but not yet:

```text
entry-derived EntityID namespace
```

No substantial projection:

```text
π : CurrentModel -> CandidateCore
```

has yet been implemented.

Continuity composition has not yet been defined.

Transformation composition, ownership derivation and reference propagation have
not yet been established.

### FACT – External review

An external semantic-core review was received and assessed.

The review record is:

```text
docs/research/semantic-core/peer_reviews/
2026-10-04-semantic-core-recommendations.md
```

The review identified several useful next experiments and verification-hardening
tasks.

The project assessment accepted most recommendations, with qualifications where
the reviewer proposed semantics rather than merely testing them.

### DECISION – Immediate semantic target

The next semantic experiment is continuity composition.

It should be defined independently before full transformation composition.

The critical distinction to preserve is:

```text
known continuation
explicit disappearance
unknown
```

Important initial cases include:

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

and split composition with both complete and partial downstream knowledge.

Associativity should be tested after the binary composition rule is explicit.

### OPEN – Equality

The current equality candidate is bisimulation.

Important remaining falsification work includes:

```text
negative equality witnesses
explicit cyclic equality experiments
```

A central unresolved question is whether value equality denotes:

```text
finite graph topology
```

or:

```text
coinductive / potentially infinite relational unfolding
```

when those differ.

### OPEN – Information semantics

The review proposed treating:

```text
Unknown
```

as the least-informed continuity result, with a possible refinement relation
such as:

```text
Unknown <= Known(S)
```

This is plausible but is not established semantics.

It should be tested rather than assumed.

### DECISION – Documentation structure

The existing:

```text
docs/research/semantic-core/alloy_verification.md
```

has grown large enough to mix distinct concerns.

The planned documentation split is:

```text
alloy_verification.md
    compact verification policy, index and current status

core_verification.md
    core Alloy evidence, solver experiments and historical measurements

transformation_verification.md
    transformation and continuity evidence

project_diary.md
    append-only chronological research development
```

The existing:

```text
alloy_api_reference.md
```

remains the Alloy API/reference document.

Peer reviews remain under:

```text
peer_reviews/
```

The purpose of the split is to keep current evidence documents readable without
discarding research history.

---

## 2026-10-04T06:17+02:00 – Verification documentation refactor completed

### FACT

The planned verification-documentation refactor has been completed.

The documentation is now separated by responsibility:

```text
docs/research/semantic-core/alloy_verification.md
    shared Alloy verification policy and navigation

docs/research/semantic-core/core_verification.md
    bounded core evidence and relevant solver/performance observations

docs/research/semantic-core/transformation_verification.md
    bounded transformation/continuity representation evidence

docs/research/semantic-core/continuity_composition.md
    active semantic hypothesis for continuity composition

docs/research/semantic-core/alloy_api_reference.md
    Alloy 6.2 API and runner reference

docs/research/semantic-core/project_diary.md
    append-only chronological research record

docs/research/semantic-core/peer_reviews/
    external reviews and project assessments
```

The former `alloy_verification.md` combined:

```text
shared verification policy
core evidence
solver history
transformation evidence
future transformation work
```

in one document.

It has been replaced by a substantially narrower policy/index document.

### FACT

`core_verification.md` now contains the previously mixed core-specific evidence,
including:

```text
bisimulation checks
non-vacuity witnesses
solver history
composition performance observations
verification search-surface experiments
```

### FACT

The first split version of `transformation_verification.md` remained too large.

Although it separated transformation material from core material, it still
combined:

```text
established evidence
formalization history
future composition design
information-refinement hypotheses
dependency planning
```

This was identified as a second form of documentation monolith rather than a
successful final decomposition.

### DECISION

`transformation_verification.md` was reduced to established bounded evidence and
interpretation of the current continuity representation.

Active continuity-composition design was moved into:

```text
docs/research/semantic-core/continuity_composition.md
```

Historical workflow failures and development chronology belong in this diary
rather than the evidence document.

### DECISION

The documentation boundary is now:

```text
verification evidence
    what has actually been checked or witnessed

active design hypothesis
    what is proposed for the next experiment

project diary
    how the research arrived there

handoff
    what the next working session needs to know
```

This boundary should be preserved as the research grows.

### FACT

The active continuity-composition document currently records the leading
candidate algebra:

```text
Unknown

Known(Set<DestinationOccurrence>)
```

with conservative composition when any relevant downstream branch is unknown.

That composition rule remains:

```text
hypothesis
```

not established semantics.

### OPEN

The next formal semantic work remains:

```text
encode continuity composition in Alloy

test basic known / disappearance / unknown cases

test split and merge composition

test equality independence through composition

test associativity

investigate information refinement only after the basic algebra is coherent
```

### DECISION

Before returning to peer-review findings or new formal work, `handoff.md` should
be refreshed once more so it records the completed documentation structure
rather than describing the split as planned.
