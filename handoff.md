# Semantic Core Research Handoff

Branch: `research/semantic-core`  
Status: active architectural experiment

This is the compact authoritative continuation checkpoint for the semantic-core
research.

It is not a historical log or verification archive.

## Working procedure

GitHub writes are performed manually by the user.

Normal workflow:

1. inspect the live branch before judging current state;
2. work one file/change at a time;
3. provide commit message, direct GitHub link and complete file contents;
4. user commits manually;
5. re-read the committed file;
6. continue from live state only.

Exception:

```text
docs/research/semantic-core/project_diary.md
```

is append-only, so diary updates should normally be supplied as small append
blocks rather than complete-file replacements.

Alloy execution happens in GitHub Actions.

Do not download Alloy locally or claim local Alloy execution.

## Research objective

Test whether SHEAR can be reconstructed from a smaller explicit semantic basis
centred on generalized relations while preserving:

```text
intended semantics
constructibility
independent verification
computational practicality
implementation practicality
```

The candidate core is a hypothesis.

The branch must remain capable of falsifying it.

Do not change production semantics merely to make the candidate model succeed.

## Independent hypotheses

```text
H1 – Representation

Can intended current SHEAR semantics be represented in the candidate core
without losing intended semantic distinctions?


H2 – Construction

Can current and planned higher semantics be constructed from the smaller basis
using a sufficiently small generic mechanism?


H3 – Practicality

Can those representations and constructions be implemented and verified with
acceptable computational and implementation complexity?
```

Success at one level does not imply success at another.

## Current candidate core

Working hypothesis:

```text
Relation = {
    atom  : Atom?,
    roles : Role -> Sequence<RelationRef>
}
```

`RelationRef` is a state-local occurrence handle.

It is not persistent semantic identity.

Current candidate ontology includes:

```text
Atom
Role
Relation
State
View
EntityID
```

`RoleUse`, `Slot`, `BisimWitness`, `CompositionCase` and `ContinuityClaim` are
currently Alloy/modeling scaffolding rather than accepted SHEAR primitives.

There is no fundamental graph-semantic distinction between:

```text
node
edge
hyperedge
ordinary graph value
```

The candidate graph-semantic object is `Relation`.

## State, view and identity

A state is currently modeled as a finite relational structure.

There is no universal semantic root.

A view contains:

```text
state
entry
entities : EntityID -> RelationOccurrence
```

`EntityID` is not intrinsic to relation value.

Different IDs may designate structurally equal values.

Important limitation:

```text
view-scoped EntityID mapping
```

is modeled, but:

```text
entry-derived EntityID namespace
```

has not been established.

## Structural/value equality

Current candidate equality is bisimulation over relational structure.

It is intended to be independent from:

```text
EntityID
host identity
allocation identity
RelationRef spelling
continuity
```

Current bounded evidence supports:

```text
bisimulation identity
bisimulation reversal
bisimulation composition
distinct EntityIDs naming equal values
equal values with different sharing topology
non-vacuous reversal and composition scenarios
```

These are bounded Alloy results, not unbounded proofs.

Important unresolved equality work:

```text
negative equality witnesses
explicit cyclic equality experiments
```

In particular, it remains unresolved whether value equality should preserve
finite cycle topology or only coinductive relational unfolding.

## Transformation and continuity

Current candidate transformation contains:

```text
source State
destination State
explicit continuity information
```

Conceptually:

```text
Continuity<T> =
    Unknown
    | Known(Set<T>)
```

where:

```text
Unknown
    no continuity assertion

Known({})
    explicit disappearance

Known({x})
    unique continuation

Known({x, y, ...})
    split
```

Many source occurrences may continue into one destination.

Destination ordering is not currently semantic continuity information.

Continuity is not inferred from:

```text
structural equality
EntityID
position
preservation
host identity
```

Current bounded evidence supports representability of:

```text
unknown
disappearance
1 -> 1 continuation
split
merge
multiple independent claims
equal values without continuity
```

First complete successful transformation verification:

```text
run 37161864993
```

## Semantic distinctions to preserve

Keep separate:

```text
structural/value equality
semantic/domain equivalence
continuity
transformation
```

None automatically implies another.

## Formal structure

```text
formal/core_model.als
    candidate core semantic model

formal/core.als
    core verification entrypoint

formal/transformation_model.als
    candidate transformation/continuity model

formal/transformation.als
    transformation verification entrypoint

.github/scripts/AlloyRunner.java
    shared instrumented runner

.github/workflows/semantic-core.yml
    core verification workflow

.github/workflows/transformation.yml
    transformation verification workflow
```

Core and transformation verification are intentionally separate.

## Documentation structure

```text
docs/semantic_core_experiment.md
    experiment charter

docs/research/semantic-core/alloy_verification.md
    shared Alloy verification policy and index

docs/research/semantic-core/core_verification.md
    core bounded evidence and solver observations

docs/research/semantic-core/transformation_verification.md
    established transformation/continuity bounded evidence

docs/research/semantic-core/continuity_composition.md
    active continuity-composition hypothesis

docs/research/semantic-core/alloy_api_reference.md
    Alloy 6.2 API and runner reference

docs/research/semantic-core/project_diary.md
    append-only chronological research log

docs/research/semantic-core/peer_reviews/
    external reviews and project assessments
```

The documentation split is complete.

Do not allow evidence, active design hypotheses, chronology and handoff state to
collapse back into one document.

## Verification discipline

Use precise language:

```text
bounded check passed
bounded counterexample found
bounded witness exists
experimentally observed
no result
not established
```

Do not describe bounded UNSAT as an unbounded theorem.

For important implication-shaped properties, pair checks with explicit
non-vacuity witnesses where practical.

Distinguish:

```text
model sanity checks
derived bounded properties
SAT witnesses
negative witnesses
non-vacuity witnesses
```

The Alloy runner currently enforces declared `expect` values but still accepts
unspecified expectations.

Rejecting unspecified `expect` in verification CI is an accepted hardening task.

## Current solver evidence

The expensive core property is:

```text
CompositionIsBisimulation
```

Instrumentation showed that observed runtime is dominated by SAT search rather
than parsing, CNF construction or JVM heap pressure.

Completed Glucose observations include approximately:

```text
48 min 56 s
95 min 36 s
17 min 54 s after verification search-surface reduction
```

Runtime variance is substantial.

Do not interpret these as stable benchmark ratios.

Hybrid decomposition showed no demonstrated advantage and was removed from the
routine workflow.

Detailed evidence belongs in:

```text
docs/research/semantic-core/core_verification.md
```

## Projection strategy

Primary H1 experiment:

```text
π : CurrentModel -> CandidateCore
```

For:

```text
current_op(S) = S'
```

test:

```text
π(current_op(S))
    ≈
core_op(π(S))
```

over relevant semantic observables.

Mismatch classifications may include:

```text
candidate-core defect
current-model defect
projection defect
representational difference
documented semantic commitment
implicit semantic assumption
implementation artifact
historical drift
unresolved design decision
```

No substantial current-model projection has yet been implemented.

## Active semantic target – continuity composition

The current active design document is:

```text
docs/research/semantic-core/continuity_composition.md
```

Leading candidate composition semantics:

```text
Unknown ; anything
    => Unknown

Known({}) ; anything
    => Known({})

Known({b1, ..., bn}) ; second
    => Unknown
       if any relevant bi has unknown second-step continuity

    => Known(union of all known second-step destination sets)
       otherwise
```

Examples:

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

```text
A -> {B, C}
B -> D
C -> E
=> A -> {D, E}
```

```text
A -> {B, C}
B -> D
C -> Unknown
=> A -> Unknown
```

This is still a hypothesis.

It has not yet been encoded or verified.

## Immediate next formal work

Encode continuity composition independently of full transformation composition.

Initial experiment should cover:

```text
known -> known
known -> disappearance
known -> unknown
first-step disappearance
first-step unknown
complete split composition
split with disappearing branch
split with unknown branch
merge after split
state containment
no continuity inferred from value equality
```

Then test:

```text
associativity
```

with explicit non-vacuity witnesses.

Only after the basic composition algebra is coherent investigate:

```text
information refinement / monotonicity
full transformation composition
ownership propagation
reference transfer
```

## Other accepted peer-review work

Still pending:

```text
negative equality witnesses
cyclic equality experiments
explicit-expect CI hardening
persistent machine-readable Alloy results
structured continuity witnesses
formal mutation experiments
first narrow CurrentModel projection
entry-scoped EntityID investigation
Role bootstrap-boundary investigation
```

The peer-review assessment is recorded at:

```text
docs/research/semantic-core/peer_reviews/
2026-10-04-semantic-core-recommendations.md
```

## Not established

Current research has not established:

```text
H1 in general
H2 in general
H3 in general

entry-derived identity
continuity composition
continuity associativity
information-refinement semantics of Unknown
transformation composition
ownership derivation
reference semantics
higher semantic construction
unbounded equality theorems
```

The next milestone is therefore not additional ontology.

It is demonstrating or falsifying a nontrivial compositional operation using the
existing candidate basis.
