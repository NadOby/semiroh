# Transformation Alloy Verification Evidence

Status: experimental research  
Branch: `research/semantic-core`  
Alloy version: `6.2.0`

This document records bounded evidence for the current transformation and
continuity representation.

It is not normative SHEAR semantics.

Shared verification policy:

```text
docs/research/semantic-core/alloy_verification.md
```

Active continuity-composition hypothesis:

```text
docs/research/semantic-core/continuity_composition.md
```

Chronological research history:

```text
docs/research/semantic-core/project_diary.md
```

## Formal scope

Candidate model:

```text
formal/transformation_model.als
```

Verification entrypoint:

```text
formal/transformation.als
```

Workflow:

```text
.github/workflows/transformation.yml
```

The transformation layer imports:

```text
formal/core_model.als
```

but is verified separately from the core verification entrypoint.

## Current representation

The model currently represents a concrete transition:

```text
Transformation {
    source
    destination
}
```

with explicit continuity information for source relation occurrences.

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

The Alloy model represents this distinction using:

```text
ContinuityClaim
```

because a bare relation:

```text
Rel -> set Rel
```

would otherwise collapse:

```text
unknown
```

and:

```text
known empty destination set
```

`ContinuityClaim` is currently modeling scaffolding, not a proposed independent
SHEAR primitive.

## Representation constraints

For each continuity claim:

```text
sourceOccurrence
    belongs to transformation.source

destinations
    belong to transformation.destination
```

For one transformation and one source occurrence, at most one continuity claim
exists.

Different source occurrences may point to the same destination.

Therefore the representation permits:

```text
1 -> 0
1 -> 1
1 -> many
many -> 1
```

Destination ordering is not currently semantic continuity information.

## Equality independence

Continuity is not inferred from:

```text
structural equality
EntityID
position
preservation
host identity
```

The intended distinction is:

```text
value equality != continuity
```

This is directly exercised by the verification suite.

## Verification commands

Current commands:

```text
0  UnknownIsNotExplicitDisappearance
1  UnknownAndDisappearanceCanCoexist
2  ExplicitDisappearanceExists
3  UniqueContinuationExists
4  SplitExists
5  MergeExists
6  ClaimPerSourceIsFunctional
7  ClaimsStayInsideTheirTransformation
8  IndependentClaimsCanCoexist
9  EqualValuesWithoutContinuity
```

Expected results:

```text
0  UNSAT
1  SAT
2  SAT
3  SAT
4  SAT
5  SAT
6  UNSAT
7  UNSAT
8  SAT
9  SAT
```

These are bounded expectations.

## Evidence categories

### Semantic distinction

```text
UnknownIsNotExplicitDisappearance
```

checks that unknown continuity and explicit disappearance are distinct.

### Representability witnesses

```text
UnknownAndDisappearanceCanCoexist
ExplicitDisappearanceExists
UniqueContinuationExists
SplitExists
MergeExists
IndependentClaimsCanCoexist
EqualValuesWithoutContinuity
```

show that the corresponding scenarios are realizable within the selected
bounds.

### Model sanity checks

```text
ClaimPerSourceIsFunctional
ClaimsStayInsideTheirTransformation
```

largely restate structural constraints already imposed by the model.

Their evidential value is primarily:

```text
encoding sanity
regression protection
verification-harness confirmation
```

rather than discovery of a new semantic theorem.

## Successful bounded run

First complete successful transformation verification:

```text
run:
    37161864993

commit:
    8c48ad6f8a60434820ac3a7734815b4cb9fc72c2

solver:
    Glucose

result:
    workflow success
```

All commands `0` through `9` executed and met their declared expectations.

This was the first workflow run that successfully parsed the candidate
transformation model, discovered the complete command set and executed all
initial representation checks.

Earlier workflow failures occurred before semantic command execution and
therefore produced no semantic result.

Their chronology belongs in:

```text
project_diary.md
```

## Current bounded evidence

```text
UnknownIsNotExplicitDisappearance
    bounded check passed

UnknownAndDisappearanceCanCoexist
    bounded witness exists

ExplicitDisappearanceExists
    bounded witness exists

UniqueContinuationExists
    bounded witness exists

SplitExists
    bounded witness exists

MergeExists
    bounded witness exists

ClaimPerSourceIsFunctional
    bounded model-sanity check passed

ClaimsStayInsideTheirTransformation
    bounded model-sanity check passed

IndependentClaimsCanCoexist
    bounded witness exists

EqualValuesWithoutContinuity
    bounded witness exists
```

## Interpretation

Within the selected bounds, the representation supports:

```text
unknown continuity

explicit disappearance

unique continuation

split continuity

merge continuity

multiple independent continuity claims

structurally equal values without asserted continuity
```

In particular:

```text
Unknown != Known({})
```

is represented explicitly.

Also:

```text
valueEqual(A, B)
```

does not force:

```text
A continuesTo B
```

in the current model.

## What is not established

This evidence does not establish:

```text
continuity composition

associativity

information-refinement semantics of Unknown

transformation composition

transformation application

creation semantics

ownership propagation

reference transfer

provenance

structured-value continuity behaviour in general

interaction with cyclic values

unbounded properties
```

Those questions must be tested separately.

## Current next boundary

The representation experiment is sufficiently coherent to proceed to continuity
composition.

The active hypothesis and intended falsification cases are maintained in:

```text
docs/research/semantic-core/continuity_composition.md
```

Do not add composition design discussion to this file unless and until it
becomes established verification evidence.
