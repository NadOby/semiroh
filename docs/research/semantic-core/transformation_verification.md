# Transformation Alloy Verification Evidence

Status: experimental research  
Branch: `research/semantic-core`  
Alloy version: `6.2.0`

This document records bounded formal evidence for the candidate transformation
and continuity layer.

It is not normative SHEAR semantics.

Shared verification policy and document index belong in:

```text
docs/research/semantic-core/alloy_verification.md
```

Core bisimulation evidence belongs in:

```text
docs/research/semantic-core/core_verification.md
```

Chronological research history belongs in:

```text
docs/research/semantic-core/project_diary.md
```

## 1. Formal scope

Candidate transformation model:

```text
formal/transformation_model.als
```

Verification entrypoint:

```text
formal/transformation.als
```

Dedicated workflow:

```text
.github/workflows/transformation.yml
```

The transformation workflow is intentionally separate from the core workflow.

Transformation-only changes therefore do not repeatedly launch the expensive
core bisimulation-composition experiment.

The transformation layer currently depends on:

```text
formal/core_model.als
```

but does not import the core verification entrypoint.

## 2. Current modeled object

The current Alloy model represents one concrete transition:

```text
Transformation {
    source      : one State
    destination : one State
}
```

It does not yet model a reusable transformation definition or transformation
application.

The model currently represents:

```text
source state
destination state
explicit continuity claims
```

It does not yet represent:

```text
semantic changes / state construction
reusable transformation definitions
transformation application
continuity composition
transformation composition
ownership propagation
reference transfer
creation semantics
provenance
```

These absences are deliberate.

Higher semantics should not be silently inferred from the current
representation.

## 3. Continuity representation

For one source occurrence, the intended conceptual information state is:

```text
Unknown
|
Known(Set<DestinationOccurrence>)
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

The Alloy representation uses:

```text
ContinuityClaim {
    transformation
    sourceOccurrence
    destinations
}
```

`ContinuityClaim` is modeling scaffolding for the distinction between:

```text
no claim
```

and:

```text
claim with an empty destination set
```

It is not currently proposed as an independent SHEAR semantic primitive.

## 4. Why a claim object is required

A plain Alloy relation such as:

```text
Rel -> set Rel
```

cannot by itself distinguish:

```text
unknown continuity
```

from:

```text
explicit disappearance
```

because both would otherwise be represented by an absence of destination
tuples.

The presence or absence of `ContinuityClaim` therefore carries information
separate from the destination set itself.

Conceptually:

```text
no claim
    Unknown

claim + {}
    Known({})

claim + {x, ...}
    Known({x, ...})
```

This distinction is fundamental to the current continuity experiment.

## 5. Destination ordering

The current Alloy continuity representation uses:

```text
set Rel
```

for destinations.

Destination order is intentionally not modeled as semantic continuity
information.

Current SHEAR transformation semantics may use canonical ordering for
deterministic representation, but that does not currently imply an additional
continuity relationship.

Therefore:

```text
Known({B, C})
```

and an alternative serialization order of the same destination set are not
intended to express different continuity semantics.

This differs from ordered target sequences inside ordinary relation roles,
where sequence position is currently semantic.

## 6. Continuity constraints

A continuity claim must remain inside the states of its transformation:

```text
sourceOccurrence
    in transformation.source.rels

destinations
    in transformation.destination.rels
```

For a given transformation and source occurrence, at most one explicit claim
may exist.

This gives one source occurrence exactly one of:

```text
Unknown
Known({})
Known({x})
Known({x, y, ...})
```

without multiple contradictory claims.

Different source occurrences may designate the same destination.

Therefore many-to-one continuity remains representable.

## 7. Continuity is independent from value equality

Continuity is not inferred from:

```text
structural/value equality
Atom equality
position
EntityID
host identity
preservation
```

Two structurally equal occurrences may have unknown continuity.

Two structurally different occurrences may still be explicitly declared
continuous.

This distinction is central to the candidate model:

```text
value equality != continuity
```

Neither relationship automatically implies the other.

## 8. Verification commands

Current transformation commands:

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

Interpretation:

```text
UNSAT check passed
    no counterexample exists within the selected bounds

SAT witness exists
    at least one satisfying structure exists within the selected bounds
```

These are bounded results.

They are not unbounded proofs.

## 9. Evidence categories

The commands provide several different kinds of evidence.

### Semantic distinction check

```text
UnknownIsNotExplicitDisappearance
```

Checks that an occurrence cannot simultaneously satisfy the model's unknown and
explicit-disappearance predicates.

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

These show that intended structures are realizable within the selected bounds.

### Model sanity checks

```text
ClaimPerSourceIsFunctional
ClaimsStayInsideTheirTransformation
```

These substantially restate constraints already imposed by model facts.

Their main value is therefore:

```text
encoding sanity
regression protection
test-harness confirmation
```

rather than discovery of a nontrivial derived theorem.

This distinction should be retained when summarizing green Alloy results.

## 10. Successful bounded run

The first complete successful transformation verification run was:

```text
37161864993
```

Commit:

```text
8c48ad6f8a60434820ac3a7734815b4cb9fc72c2
```

Commit message:

```text
Fix continuity claim uniqueness constraint
```

Solver:

```text
Glucose
```

Result:

```text
workflow success
```

Command discovery succeeded.

All commands:

```text
0
1
2
3
4
5
6
7
8
9
```

completed successfully and met their declared expectations.

This was the first run to provide complete semantic evidence for the initial
continuity-representation suite.

## 11. Unknown and disappearance

Current bounded evidence supports the intended distinction:

```text
Unknown
!=
Known({})
```

`UnknownIsNotExplicitDisappearance` passed as an UNSAT bounded check.

`UnknownAndDisappearanceCanCoexist` produced a SAT witness.

The latter matters because it demonstrates that the two states are not merely
different predicate spellings that cannot coexist in an actual model instance.

Within one transformation, the model can contain:

```text
one source occurrence with unknown continuity
```

and:

```text
another source occurrence with explicit disappearance
```

simultaneously.

## 12. One-to-zero continuity

`ExplicitDisappearanceExists` produced a SAT witness.

Therefore the candidate representation can express:

```text
A -> {}
```

meaning:

```text
continuity is known
and
the complete destination set is empty
```

This is not represented as unknown continuity.

## 13. One-to-one continuity

`UniqueContinuationExists` produced a SAT witness.

Therefore the candidate representation can express:

```text
A -> B
```

with exactly one explicitly declared destination.

This declaration is continuity information.

It does not imply structural equality between `A` and `B`.

## 14. Splits

`SplitExists` produced a SAT witness.

Therefore the candidate representation can express:

```text
A -> {B, C, ...}
```

with more than one explicitly declared destination.

This represents split continuity.

No semantic ordering among split destinations is currently implied.

## 15. Merges

`MergeExists` produced a SAT witness.

Therefore the candidate representation permits:

```text
A -> C
B -> C
```

for distinct source occurrences.

Many-to-one continuity is therefore representable.

The one-claim-per-source rule does not imply one-source-per-destination.

## 16. Independent claims

`IndependentClaimsCanCoexist` produced a SAT witness.

This demonstrates that the representation is not accidentally restricted to a
single continuity assertion per transformation.

Multiple source occurrences may independently carry different continuity
states.

## 17. Equal values without continuity

`EqualValuesWithoutContinuity` produced a SAT witness.

This is an important semantic witness.

Within the selected bounds, structurally equal values may occur across a
transformation while continuity remains unknown.

Therefore the model does not derive:

```text
valueEqual(A, B)
```

into:

```text
A continuesTo B
```

This supports the intended separation:

```text
structural/value equality
```

from:

```text
continuity
```

It does not prove that every future extension of the transformation model will
preserve this independence.

It is current bounded regression evidence.

## 18. Pre-semantic workflow failures

Several workflow runs failed before any transformation command executed.

These failures are part of the research history but are not semantic
counterexamples.

### Run 37161199160

Command discovery failed while type-checking:

```text
formal/transformation.als
```

A local name shadowed the `Transformation.destination` field.

Result classification:

```text
Alloy name-resolution / type error
no semantic result
```

### Run 37161368014

Command discovery again failed in:

```text
formal/transformation.als
```

because local identifiers shadowed transformation-model fields.

Result classification:

```text
Alloy name-resolution / type error
no semantic result
```

### Run 37161496229

The verification entrypoint shadowing issue had been repaired sufficiently for
Alloy to reach:

```text
formal/transformation_model.als
```

The imported model then failed because a parameter named:

```text
transformation
```

shadowed the `ContinuityClaim.transformation` field.

Result classification:

```text
Alloy name-resolution / type error
no semantic result
```

### Run 37161699029

Field shadowing had been repaired.

Command discovery then exposed an invalid use of:

```text
false
```

in the initial uniqueness fact.

Alloy 6.2 did not resolve that expression as intended.

The constraint was rewritten directly as:

```text
distinct claims in the same transformation
must have distinct source occurrences
```

Result classification:

```text
Alloy syntax / name-resolution error
no semantic result
```

These runs are useful evidence about the formalization process, but none should
be described as a failed semantic property.

## 19. Readability convention

Repeated Alloy field-shadowing failures motivated a naming convention for local
parameters.

Preferred local names are:

```text
tx
    Transformation

src
    directional source relation occurrence

dst
    directional destination relation occurrence

occurrence
    neutral relation occurrence

claim
    ContinuityClaim
```

Semantic field names remain descriptive:

```text
transformation
sourceOccurrence
destinations
source
destination
```

The objective is to avoid Alloy name-resolution ambiguity without making the
formal model unreadable.

## 20. Current bounded evidence summary

Current evidence supports:

```text
UnknownIsNotExplicitDisappearance:
    bounded check passed

UnknownAndDisappearanceCanCoexist:
    bounded witness exists

ExplicitDisappearanceExists:
    bounded witness exists

UniqueContinuationExists:
    bounded witness exists

SplitExists:
    bounded witness exists

MergeExists:
    bounded witness exists

ClaimPerSourceIsFunctional:
    bounded model-sanity check passed

ClaimsStayInsideTheirTransformation:
    bounded model-sanity check passed

IndependentClaimsCanCoexist:
    bounded witness exists

EqualValuesWithoutContinuity:
    bounded witness exists
```

Representationally, the current model admits:

```text
unknown
disappearance
unique continuation
split
merge
multiple independent claims
equal values without continuity
```

within the selected bounds.

## 21. What is not established

The current transformation evidence does not establish:

```text
continuity composition

associativity of continuity composition

information refinement semantics for Unknown

transformation composition

transformation application

state construction from transformation definitions

creation semantics

ownership propagation

reference transfer

provenance

interaction with entry/view identity

interaction with structured cyclic values

unbounded algebraic properties
```

The initial suite also does not yet provide substantial structured-value
continuity witnesses.

Most existing witnesses deliberately keep relation structure small to isolate
the continuity representation itself.

## 22. Next semantic target – continuity composition

The next transformation-layer experiment is continuity composition.

For compatible concrete transitions:

```text
A --first--> B --second--> C
```

composition must preserve the distinction among:

```text
known continuation
explicit disappearance
unknown
```

Ordinary relational composition is insufficient because it collapses:

```text
unknown
```

and:

```text
known empty destination set
```

if the information state is not tracked explicitly.

## 23. Initial composition cases

The first composition definition should account for at least the following
cases.

### Known continuation followed by known continuation

```text
A -> B
B -> C
```

candidate result:

```text
A -> C
```

### Known continuation followed by disappearance

```text
A -> B
B -> {}
```

candidate result:

```text
A -> {}
```

### Known continuation followed by unknown

```text
A -> B
B -> Unknown
```

candidate result:

```text
A -> Unknown
```

This case is essential.

An absent second-step claim must not silently become:

```text
identity
```

or:

```text
disappearance
```

### First-step disappearance

```text
A -> {}
```

candidate result through any compatible later transformation:

```text
A -> {}
```

because no intermediate continuation remains.

### First-step unknown

```text
A -> Unknown
```

candidate result:

```text
A -> Unknown
```

unless later semantics introduces information unavailable in ordinary forward
composition.

That possibility has not been accepted.

## 24. Split composition

A complete known split such as:

```text
A -> {B, C}

B -> D
C -> E
```

has the leading candidate result:

```text
A -> {D, E}
```

The more important case is partial downstream knowledge:

```text
A -> {B, C}

B -> D
C -> Unknown
```

The leading conservative interpretation is:

```text
A -> Unknown
```

because the complete final continuation set is no longer known.

This is a semantic hypothesis.

It must be explicitly accepted or falsified rather than emerging accidentally
from the Alloy encoding.

## 25. Information semantics of Unknown

A peer review proposed treating continuity as an information domain with a
possible refinement relation:

```text
Unknown <= Known(S)
```

for every concrete complete destination set `S`.

This is plausible but not established.

In particular, current:

```text
Known(S)
```

means a complete asserted destination set.

It should not automatically be interpreted as merely:

```text
at least these destinations are known
```

Therefore set inclusion alone does not currently establish an information order
among different `Known(S)` values.

Information refinement should be treated as its own semantic experiment.

## 26. Associativity target

Once binary continuity composition is defined, test:

```text
(T1 ; T2) ; T3
```

against:

```text
T1 ; (T2 ; T3)
```

under compatible state boundaries.

Associativity matters because the meaning of a transformation history should
not accidentally depend on grouping.

A bounded counterexample would be valuable research evidence.

If associativity fails, classify the cause before changing the model:

```text
incorrect composition algebra
intentional information loss
insufficient continuity representation
need for additional metadata
Alloy encoding defect
```

Do not automatically repair a counterexample by adding a new semantic
primitive.

## 27. Structured continuity witnesses

After the basic composition algebra is understood, strengthen the continuity
suite with structured values.

Useful cases include:

```text
equal structured values with unknown continuity

unequal structured values with known continuity

continuation across changed atoms

continuation across changed role structure

equal DAG values with different sharing topology

cyclic values with explicit continuity

cyclic values without continuity
```

These should reinforce:

```text
value equality != continuity
```

beyond minimal atomic examples.

## 28. Future dependency order

Current preferred semantic dependency order is:

```text
relation/value semantics
    ->
continuity representation
    ->
continuity composition
    ->
transformation composition
    ->
ownership/reference propagation
```

Ownership should remain deferred while the meaning of:

```text
disappearance
split
merge
unknown continuity
composition
```

is still under active investigation.

This keeps counterexamples easier to localize.

## 29. Immediate transformation-specific work

The next transformation work should be:

```text
define continuity composition independently

add direct witnesses/checks for:
    known -> known
    known -> disappearance
    known -> unknown
    disappearance -> disappearance
    unknown -> unknown
    complete split composition
    partial-known split composition

check composition state containment

check that structural equality does not manufacture composed continuity

test associativity

investigate information refinement / monotonicity
```

Only after that layer is coherent should the experiment attempt:

```text
complete transformation composition
transformation application
ownership propagation
reference transfer
```
