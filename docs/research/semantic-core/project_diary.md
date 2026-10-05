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
docs/research/semantic-core/handoff.md
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

## 2026-10-04 – Alloy verification hardening and consolidation

Continuity-composition verification was expanded with bounded positive,
negative, non-vacuity, associativity, and targeted mutation experiments.

The shared Alloy runner was hardened to reject commands without an explicit
`expect 0` or `expect 1` before solver execution.

A solver comparison used `CompositionIsBisimulation`, the historically dominant
core verification workload, without reducing its semantic scope.

Observed completed results included:

```text
lingeling.parallel:
    UNSAT
    approximately 166 s

glucose:
    UNSAT
    approximately 1494 s
```

Both used the same bounded problem and generated CNF dimensions:

```text
164761 variables
373172 clauses
```

`minisat`, `minisat.prover`, `sat4j`, and `sat4j.light` produced no SAT or UNSAT
result before the two-hour experiment cutoff.

The approximately 9x observed advantage over Glucose made
`lingeling.parallel` the routine CI solver. This is an engineering result for
the current workload, not a universal solver-performance claim.

The separate core, transformation, and transformation-mutation Alloy workflows
were consolidated into:

```text
.github/workflows/alloy-verification.yml
```

The consolidated workflow discovers commands across the verification
entrypoints, executes them independently, and runs on every push to
`research/semantic-core`.

Its first complete run passed all discovered verification commands.

The Python semantic-model workflow remains separate because it verifies a
different implementation layer.


## 2026-10-05T12:57+02:00 – First projection run (plan steps 5 and 6)

### FACT

The `main → candidate → observable` projection was implemented in
`research/core_projection/` and run once at `0950761` over the 26 corpus
programs, the continuity corpus and the adversarial cases, in a charter-faithful
mode (`STRUCT`) and a control mode (`REF`). The candidate was not changed.

Of the compared items, 3,963,165 agreed, 5,109 were predicted mismatches, 62
were unexpected and 0 were gaps. Full results and the deviations from the plan
are in `docs/research/semantic-core/projection_results.md`.

The unexpected mismatches are two groups:

```text
O3 STRUCT, order-reversing renaming: 60 of 67 states not isomorphic
O5 STRUCT, leaf edit: value class changes for 22 of 42 and 202 of 402
    entities, against 1 changed VersionID in main
```

Everything else was explained by a cited prediction: arity collapse (O0),
adversarial case 1 (4,379 O1 pairs), charter §3.11 (renamed states) and
adversarial case 3 (symmetric and differently named middle states). Eight
real two-step chains built with `main`'s own operations agreed with
`main`'s `compose` in every row.

### INTERPRETATION

The first group follows from the plan's ownership rule, which lists an owner's
children in `EntityID` order and so lets spelling into the projected
structure. It is a defect of the projection rule, not of the candidate.

The second group is a consequence of projecting references as role targets:
the value of an entity includes everything it reaches. Whether that counts
against H1 is a step-8 question.

### DECISION

Steps 5 and 6 are done. Step 7 (at most one candidate revision) and step 8 (H1
evaluation against the mechanism inventory) are separate tasks.

## 2026-10-05T14:33+02:00 – Projection re-run after review

### FACT

A review of the first projection run (entry 2026-10-05T12:57+02:00) asked for
four changes, made at `f45183d` and `cb74cea`; the experiment was run again at
`cb74cea`. The candidate was not changed.

```text
ownership projection: one owns relation per ownership edge
O5 STRUCT: predicted mismatch, direction review section 3.3
O5: a cross-function scenario (compiler, leaf edit inside upper)
handoff.md: moved under docs/research/semantic-core/
```

Result: 3,963,166 agree, 5,172 predicted, 0 unexpected, 0 gaps. Details in
`docs/research/semantic-core/projection_results.md`.

### INTERPRETATION

This corrects the first entry's reading of the two groups of unexpected
mismatches. The O3 group was a defect of the ownership rule: `main` stores
ownership children as `sorted(set(...))`, so their order is not semantic, and
with one relation per edge the order-reversing renaming gives isomorphic states
for all 67 states in `STRUCT`. The O5 group is the predicted consequence of
deriving version identity from candidate equality; it now appears in three
scenarios, the largest reaching all five functions of `compiler`.

### OPEN

Whether that churn counts against H1 is a step-8 question; step 7 has not
started.

## 2026-10-05T15:27+02:00 – Candidate revision 1 run (named roots)

### FACT

The single candidate revision was executed from `revision_plan.md`: charter
§3.12, `research/core_projection/named.py`, the `NAMED` projection mode, the
C0 observable (contained cycles) and a predictions check in the report. The
frozen candidate (`core.py`, modes `STRUCT` and `REF`) was not changed. The
experiment was run once, at `6739252`.

```text
predictions of revision_plan.md section 3: 10 of 10 hit
NAMED: 1,983,920 agree, 316 predicted (O0 arity collapse), 0 unexpected, 0 gaps
STRUCT and REF: per-observable counts identical to cb74cea
O1 NAMED 1,976,135 of 1,976,135 agree (STRUCT: 4,379 predicted mismatches)
O5 NAMED: 1, 1, 2 value-class changes = main's VersionID changes (STRUCT: 22, 202, 129)
C0: no contained cycle in 67 projected states; factorial's self-reference is a Named target
```

Details, and the choices the plan left open, in
`docs/research/semantic-core/projection_results.md` ("Revision 1 run").

### INTERPRETATION

The informative agreements are equality, links and version churn, which the
`REF` control also had but only with `EntityID` strings in atoms; `NAMED` holds
the names in targets and bindings. The agreements on renamed states and on
composition hold largely by the definition of the revision (names fixed in
state identity, continuity over names), so they restate it more than they test
it. The cost is charter §3.8: names become part of values that refer to them and
of state identity.

### OPEN

Whether revision 1 counts as the same candidate or as a new mechanism, and how
it scores against the mechanism inventory, is step 8, an Opus task.
