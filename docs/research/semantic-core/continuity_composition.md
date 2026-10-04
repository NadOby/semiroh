# Continuity Composition

Status: active semantic hypothesis  
Branch: `research/semantic-core`

This document defines the current research question around composition of
continuity information.

It is not normative SHEAR semantics.

Established continuity representation and bounded evidence belong in:

```text
docs/research/semantic-core/transformation_verification.md
```

Chronological experiments and corrections belong in:

```text
docs/research/semantic-core/project_diary.md
```

## 1. Existing representation

For one source occurrence, current continuity information can be described as:

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

`Known(S)` currently means that `S` is the complete asserted destination set.

It does not mean merely:

```text
at least the members of S are known
```

## 2. Composition problem

Given compatible transitions:

```text
S0 --T1--> S1 --T2--> S2
```

define continuity from an occurrence in `S0` to occurrences in `S2`.

Composition must preserve the distinction between:

```text
unknown
known disappearance
known nonempty continuation
```

Ordinary relational composition is insufficient because it cannot by itself
distinguish:

```text
unknown
```

from:

```text
known empty result
```

## 3. Candidate composition rule

Let:

```text
compose(c1, next)
```

compose one first-step continuity value `c1` with second-step continuity
information `next` for intermediate occurrences.

Current leading rule:

### First step unknown

```text
compose(Unknown, next)
    = Unknown
```

Later information cannot determine which intermediate occurrences existed if
the first step itself is unknown.

### First step disappearance

```text
compose(Known({}), next)
    = Known({})
```

There are no intermediate occurrences to continue.

### First step has destinations

For:

```text
Known({b1, b2, ...})
```

inspect second-step continuity for every intermediate destination.

If any relevant intermediate occurrence has:

```text
Unknown
```

then the complete final destination set cannot be determined.

Candidate result:

```text
Unknown
```

If every relevant intermediate has known continuity:

```text
b1 -> Known(S1)
b2 -> Known(S2)
...
```

then compose by union:

```text
Known(S1 ∪ S2 ∪ ...)
```

This union may itself be empty, giving explicit disappearance.

## 4. Basic cases

### Transitive continuation

```text
A -> {B}
B -> {C}
```

candidate result:

```text
A -> {C}
```

### Downstream disappearance

```text
A -> {B}
B -> {}
```

candidate result:

```text
A -> {}
```

### Downstream unknown

```text
A -> {B}
B -> Unknown
```

candidate result:

```text
A -> Unknown
```

### First-step disappearance

```text
A -> {}
```

candidate result through any compatible later transition:

```text
A -> {}
```

### First-step unknown

```text
A -> Unknown
```

candidate result:

```text
A -> Unknown
```

## 5. Split cases

### Complete downstream knowledge

```text
A -> {B, C}
B -> {D}
C -> {E}
```

candidate result:

```text
A -> {D, E}
```

### One branch disappears

```text
A -> {B, C}
B -> {D}
C -> {}
```

candidate result:

```text
A -> {D}
```

Disappearance of one branch does not make the complete result unknown when its
disappearance is explicitly known.

### All branches disappear

```text
A -> {B, C}
B -> {}
C -> {}
```

candidate result:

```text
A -> {}
```

### Partial downstream knowledge

```text
A -> {B, C}
B -> {D}
C -> Unknown
```

leading candidate result:

```text
A -> Unknown
```

The known `D` cannot be presented as the complete continuation set while the
continuation of `C` remains unknown.

## 6. Merge cases

Composition may collapse multiple branches onto the same final occurrence:

```text
A -> {B, C}
B -> {D}
C -> {D}
```

candidate result:

```text
A -> {D}
```

Because destination continuity is currently represented as a set, duplicate
paths do not create duplicate semantic destinations.

Whether path multiplicity should ever be semantically observable is not part of
the current continuity model.

## 7. Unknown is information state, not destination

`Unknown` must not be modeled as:

```text
a special Relation
a synthetic destination
an empty set
```

It describes absence of complete continuity information.

This distinction is necessary for:

```text
Unknown != Known({})
```

and for conservative composition.

## 8. Information refinement hypothesis

A peer review proposed an information ordering:

```text
Unknown <= Known(S)
```

for every concrete complete destination set `S`.

This is a plausible interpretation:

```text
Unknown
    less information

Known(S)
    complete information
```

but it is not yet accepted semantics.

Different concrete values:

```text
Known(S1)
Known(S2)
```

are not currently ordered merely because:

```text
S1 subset S2
```

because each claims to be a complete destination set.

This information-refinement hypothesis should be tested separately from the
basic composition rule.

## 9. Associativity target

If composition is valid, an important expected property is:

```text
(T1 ; T2) ; T3
==
T1 ; (T2 ; T3)
```

for compatible state boundaries.

This must be tested rather than assumed.

Potential causes of a counterexample include:

```text
incorrect composition rule
information loss
insufficient continuity representation
unexpected set semantics
formal encoding defect
need for additional semantic information
```

A counterexample is research evidence.

Do not repair it automatically by adding provenance or another primitive.

## 10. Equality independence

Composition must not manufacture continuity from structural equality.

For example:

```text
A -> {B}

valueEqual(B, C)

C -> {D}
```

does not by itself justify treating:

```text
B
```

as if it had the continuity claim of:

```text
C
```

Continuity follows explicit continuity information, not value equality.

This preserves:

```text
value equality != continuity
```

through composition.

## 11. State compatibility

For:

```text
T1:
    source      = S0
    destination = S1

T2:
    source      = S1
    destination = S2
```

composition is straightforwardly state-compatible.

Composition where:

```text
T1.destination != T2.source
```

is currently outside the experiment.

No implicit rebinding, structural matching, or state equivalence should be
introduced merely to make incompatible transformations composable.

## 12. First Alloy experiment

The first formalization should test continuity composition independently of full
transformation composition.

It should avoid introducing:

```text
transformation definitions
state changes
ownership
references
provenance
creation
```

unless one of those proves necessary to express the continuity algebra itself.

Initial checks/witnesses should cover:

```text
known -> known

known -> disappearance

known -> unknown

disappearance -> disappearance

unknown -> unknown

complete split composition

split with one disappearing branch

all split branches disappearing

split with one unknown branch

merge after split

no continuity inferred from value equality

source/destination state containment
```

After these behave as intended:

```text
check associativity
```

with explicit non-vacuity witnesses for the composition scenarios.

## 13. Falsification criteria

The current candidate should be reconsidered if bounded exploration shows that
the proposed representation cannot express or compose intended distinctions
without introducing accidental semantics.

Particularly important failures would include:

```text
Unknown collapsing into disappearance

partial knowledge producing a falsely complete Known result

grouping-dependent composition

structural equality creating continuity

split or merge information becoming ambiguous

composition requiring provenance to recover basic continuity meaning
```

Such failures should be classified before modifying the semantic basis.

## 14. Relationship to higher layers

Continuity composition should stabilize before attempting:

```text
full transformation composition
ownership propagation
reference transfer
lifecycle semantics
```

Those layers depend on the meaning of:

```text
unknown
disappearance
split
merge
composition
```

and would otherwise make failures harder to localize.

## 15. Current status

Established:

```text
continuity representation distinguishes Unknown from Known({})
split and merge are representable
value equality does not force continuity
```

Not established:

```text
the candidate composition rule
associativity
information-refinement semantics
monotonicity
interaction with structured cyclic values
full transformation composition
```

Immediate next experiment:

```text
encode the candidate continuity-composition rule in Alloy
and test the basic cases before adding higher transformation semantics
```
