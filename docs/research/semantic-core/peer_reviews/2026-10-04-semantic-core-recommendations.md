# Peer Review – Semantic Core Recommendations

Received: `2026-10-04T05:42+02:00`  
Status: external research review  
Branch reviewed: `research/semantic-core`

This document records an external review of the semantic-core experiment and the
project's assessment of its recommendations.

The review is evidence and critique, not normative SHEAR semantics.

Reviewer wording may refer to the project by its previous name, SEMIROH. The
current project name is SHEAR.

## Overall assessment

The review is substantively aligned with the current research direction.

Its strongest recommendations concern:

- keeping the research handoff current;
- defining continuity composition before higher transformation semantics;
- checking associativity and partial-information behaviour;
- strengthening equality tests with negative and cyclic cases;
- beginning real projection from the current implementation;
- distinguishing categories of formal evidence;
- hardening CI expectations;
- preserving machine-readable research results;
- keeping H1, H2 and H3 independent.

Most recommendations are accepted.

Several require qualification because they either propose semantics that have
not yet been accepted or use terminology that differs from the current
candidate model.

## Confirmed findings

### Handoff drift

Accepted – immediate.

`handoff.md` is behind the live branch.

In particular, it still describes creation of the initial formal model as a
future step even though the branch now contains:

```text
formal/core_model.als
formal/core.als
formal/transformation_model.als
formal/transformation.als
```

as well as:

```text
instrumented Alloy execution
semantic-core CI
transformation CI
bounded SAT / UNSAT results
non-vacuity witnesses
continuity representation experiments
```

The handoff should again become the compact authoritative continuation point.

It must remain a checkpoint rather than a historical log.

Historical development belongs in the project diary.

### Continuity representation

Accepted as established bounded evidence.

The current candidate distinguishes:

```text
Unknown

Known({})
    explicit disappearance

Known({x, ...})
    explicit continuation
```

The current Alloy representation uses `ContinuityClaim` as scaffolding to
preserve the distinction between:

```text
no claim
```

and:

```text
claim with empty destination set
```

Initial bounded witnesses/checks cover:

```text
unknown versus disappearance
1 -> 0
1 -> 1
1 -> many
many -> 1
multiple independent claims
claim-per-source functionality
state containment
structural equality without continuity
```

This establishes representation behaviour only within the selected bounds.

It does not establish continuity composition.

### Verification CI does not require `expect`

Accepted – real verification-hardening gap.

The current runner enforces a declared expectation when Alloy reports:

```text
expect 0
```

or:

```text
expect 1
```

but an unspecified expectation is currently accepted.

Research verification CI should eventually reject unspecified expectations
unless an explicit exploratory execution mode is requested.

### Entry-scoped identity is not established

Accepted.

The current `View` representation contains:

```text
state
entry
entities
```

and constrains the entry and entity targets to belong to the selected state.

It does not currently derive, constrain or otherwise determine `entities` from
`entry`.

Therefore the current evidence supports:

```text
view-scoped EntityID mapping
```

but not yet:

```text
entry-derived EntityID namespace
```

This distinction should remain explicit.

## P0 recommendations

### Update `handoff.md`

Accepted – immediate.

The updated handoff should contain at least:

#### Established

```text
candidate relation/state/view representation exists
candidate bisimulation-based value equality exists
bounded algebraic checks and non-vacuity witnesses exist
EntityID distinction can coexist with equal values
sharing topology need not determine value equality
explicit continuity representation exists
unknown/disappearance/continuation/split/merge are representable
separate core and transformation verification lanes exist
```

#### Not established

```text
projection of current SHEAR semantics in general
entry-derived identity namespaces
continuity composition
transformation composition
ownership derivation
reference semantics
higher semantic construction
H2 in general
H3 beyond initial formal experiments
```

#### Immediate target

```text
continuity composition
```

### Formalize continuity composition

Accepted – immediate semantic target.

Conceptually:

```text
Continuity<T> =
    Unknown
    | Known(Set<T>)
```

with:

```text
Known({})
```

representing explicit disappearance.

The first composition experiment should remain independent of complete
transformation composition.

Required base cases include:

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
A -> {}
=> A -> {}
```

For a split:

```text
A -> {B, C}
B -> D
C -> E
=> A -> {D, E}
```

The important partial-information case is:

```text
A -> {B, C}
B -> D
C -> Unknown
```

The leading candidate interpretation is:

```text
A -> Unknown
```

because the complete destination set is not known.

This remains a semantic hypothesis until explicitly accepted and tested.

### Check associativity

Accepted.

After the binary composition rule is explicit, test:

```text
(T1 ; T2) ; T3
```

against:

```text
T1 ; (T2 ; T3)
```

under compatible state boundaries.

A bounded counterexample would be valuable evidence rather than something to
work around.

Failure should be classified before changing the representation:

```text
incorrect continuity algebra
intentional information loss
insufficient representation
need for additional metadata
encoding defect
```

### Define information semantics of `Unknown`

Accepted with qualification.

The proposed information ordering:

```text
Unknown <= Known(S)
```

is plausible and useful, but it is not yet established SHEAR semantics.

It should be investigated alongside continuity composition rather than silently
assumed.

If adopted, useful properties include monotonicity under increased information.

Different `Known(S)` values should not automatically be ordered by subset
unless such an ordering receives an independent semantic justification.

`Known(S)` currently means a complete asserted destination set, not merely a
lower bound on possible destinations.

### Add negative equality witnesses

Accepted with one correction.

Positive algebraic properties are insufficient to detect an equality predicate
that is systematically too permissive.

Useful negative witnesses include:

```text
DifferentAtomsAreNotEqual
DifferentRoleSetsAreNotEqual
DifferentTargetOrderIsNotEqual
DifferentRoleMultiplicityIsNotEqual
PresentEmptyRoleDiffersFromAbsentRole
```

The review's proposed:

```text
DifferentRoleOrderIsNotEqual
```

must not be adopted literally if it refers to order among distinct role names.

Current candidate semantics do not assign semantic order to role declarations.

Order is semantic inside each role's target sequence.

An additional positive witness may therefore be useful:

```text
RoleDeclarationOrderDoesNotMatter
```

if the Alloy representation ever makes declaration order observable.

### Test cyclic equality explicitly

Accepted – high priority.

The current candidate value equality is bisimulation.

Therefore finite graphs with different cycle topology may denote equal values
when their relational unfoldings are bisimilar.

The canonical experiment is:

```text
A:
    next -> A
```

versus:

```text
B:
    next -> C

C:
    next -> B
```

The experiment must decide whether the intended semantic object is:

```text
finite graph topology
```

or:

```text
relational/coinductive unfolding
```

at the value-equality layer.

Required cases should include:

```text
one-node cycle versus two-node cycle
mutually recursive structures
different atoms inside cycles
different role structure inside cycles
different sharing topology around cycles
```

This is an unresolved semantic question, not merely a test-coverage issue.

## P1 recommendations

### Build the first projection from current SHEAR semantics

Accepted.

This is the first major direct H1 experiment.

Start with a narrow projection:

```text
π : CurrentModel -> CandidateCore
```

covering only a deliberately small slice such as:

```text
atoms
nullary values
ordinary relation values
role target ordering
multiplicity
EntityID distinction
structural/value equality
```

Then compare relevant observables under current and candidate operations.

Mismatch categories should include:

```text
candidate-core defect
current-model defect
projection defect
representational difference
implicit semantic assumption
intentionally unspecified behaviour
```

Neither side should automatically be considered authoritative.

### Add structured continuity witnesses

Accepted.

Atomic continuity witnesses are useful because they isolate continuity
representation.

They should not be the only evidence.

Later witnesses should include:

```text
equal structured values with unknown continuity
unequal structured values with known continuity
continuation across changed atoms
continuation across changed role structure
equal DAG values with different sharing
cyclic values with and without continuity
```

These test the intended independence:

```text
value equality != continuity
```

### Separate formal evidence categories

Accepted.

Green Alloy commands are not epistemically equivalent.

At minimum distinguish:

```text
model sanity check
derived bounded property
SAT witness
negative witness / anti-witness
non-vacuity witness
```

For example, checking a property already imposed directly by a fact primarily
tests the encoding and test harness rather than deriving new semantic
information.

### Standardize bounded-result terminology

Accepted.

Preferred language:

```text
bounded check passed
bounded counterexample found
bounded witness exists
experimentally observed
not established
```

Use `verified` only where its scope is immediately unambiguous.

No Alloy result in this branch should be presented as an unbounded theorem
without an actual proof.

### Require explicit expectations in verification CI

Accepted.

Desired research-CI behaviour:

```text
expect 0 + UNSAT -> pass
expect 1 + SAT   -> pass
expect 0 + SAT   -> fail
expect 1 + UNSAT -> fail
unspecified      -> fail
```

Exploratory runs may eventually provide an explicit mode that permits
unspecified expectations.

### Preserve machine-readable results

Accepted with implementation qualification.

The existing runner already emits structured metric records.

Important formal results should be preserved in a form that remains available
after ordinary CI logs disappear.

Possible persistent representation:

```text
JSON
JSONL
```

Do not assume GitHub Actions artifacts alone are permanent – artifact retention
itself may expire.

A reasonable strategy is:

```text
CI artifacts for complete per-run output
+
small versioned result records for significant research results
```

The exact repository layout remains to be decided.

### Treat formal complexity as H3 evidence

Accepted.

Track:

```text
scope
primary SAT variables
total SAT variables
clauses
translation time
solver time
memory observations
```

Wall-clock observations from shared GitHub runners should be interpreted
cautiously.

Scope staircases may become useful once individual properties are stable
enough that scaling measurements have interpretable meaning.

### Preserve non-vacuity witnesses as a convention

Accepted.

For important implication-shaped properties, prefer:

```text
check Property
```

together with an explicit witness showing that the interesting antecedent can
actually occur.

This should be treated as a research convention rather than a special fix for
the existing bisimulation checks.

### Investigate `Role` as a bootstrap primitive

Accepted as an open research question.

Do not remove `Role` merely to minimize primitive count.

Questions include:

```text
what determines Role equality?
can Role be an Atom or Symbol?
can Role itself be relational?
does relationalizing Role introduce circular meta-role machinery?
what implementation and verification cost does a primitive Role avoid?
```

The objective remains minimum sufficient semantic basis, not minimum primitive
count.

### Investigate entry-scoped EntityID construction

Accepted.

The current model does not yet establish this.

Questions include:

```text
same state + same entry:
    what must be invariant about EntityID bindings?

same state + different entry:
    may the same EntityID denote different occurrences?

is the mapping external View scaffolding,
or eventually relational structure reachable from entry?
```

Until resolved, documentation should say:

```text
view-scoped identity mapping
```

rather than claiming entry-derived identity.

## P2 recommendations

### Add deep formal verification workflow

Accepted – deferred until there are stable expensive properties worth
re-running.

Normal CI should remain suitable for regression feedback.

A separate manual or scheduled lane may later explore:

```text
larger scopes
multiple solvers
symmetry settings
decomposition
scope staircases
```

### Run selected properties under multiple solvers

Accepted as supplementary evidence.

Classify outcomes independently:

```text
SAT
UNSAT
timeout
cancelled
runner failure
solver unavailable
```

Failure to terminate is not a semantic counterexample.

### Verify Alloy artifact cryptographically

Accepted as research hygiene, not semantic priority.

Pinning Alloy `6.2.0` is already useful.

Later reproducibility hardening may include:

```text
artifact SHA-256 verification
recorded Java runtime
immutable GitHub Action SHAs
```

### Keep semantic primitives separate from Alloy scaffolding

Accepted and already an explicit project discipline.

Every new Alloy signature should continue to answer:

```text
candidate semantic object?
```

or:

```text
formal / verification scaffolding?
```

Convenient Alloy representation must not silently enlarge the candidate
ontology.

### Add formal mutation experiments

Accepted – useful after the initial suite becomes broader.

High-value mutations include weakening:

```text
atom equality
role-name equality
target ordering
multiplicity
present-empty role distinction
state locality
continuity functionality
```

The purpose is to determine whether the suite detects important semantic
weakening.

This need not initially become a large automatic mutation framework.

### Record failed experiments

Accepted.

The append-only project diary is the natural place for chronological failed
experiments and decisions.

Recommended entry structure:

```text
timestamp
hypothesis
experiment
observation
interpretation
decision / next step
```

Historical entries should not be rewritten.

Later corrections should be appended as new timestamped entries.

### Classify bottlenecks before optimization

Accepted and already supported by the instrumented runner.

Continue distinguishing:

```text
parse
translation
CNF construction
SAT search
```

and distinguish changes to:

```text
semantics
bounded problem
verification scaffolding
search strategy
```

Representational equivalence must not be claimed mechanically proved when it
has only been argued.

## P3 recommendations

### Delay ownership

Accepted.

Dependency order should remain approximately:

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

### Delay universal rewrite machinery

Accepted.

Matcher/binding/guard/rewrite machinery remains a possible derived mechanism,
not an accepted semantic kernel.

Do not adopt it merely because it simplifies construction experiments.

### Keep H1, H2 and H3 independent

Accepted and fundamental.

Possible outcomes include:

```text
H1 pass
H2 fail
H3 fail
```

or:

```text
H1 pass
H2 pass
H3 fail
```

Evidence for one hypothesis must not be silently promoted into evidence for
another.

## Adjusted immediate execution order

Combining the review with the current state of the branch gives the following
working order:

1. update `handoff.md`;
2. finish the documentation split and establish the append-only project diary;
3. define continuity composition;
4. add base unknown/disappearance/continuation/split/merge composition cases;
5. test continuity-composition associativity;
6. investigate information refinement and monotonicity;
7. add negative equality witnesses;
8. add explicit cyclic-equality experiments;
9. harden verification CI to require `expect`;
10. preserve significant machine-readable Alloy results;
11. add structured-value continuity witnesses;
12. build the first narrow projection from current SHEAR semantics;
13. begin commuting-diagram differential experiments;
14. investigate entry-scoped identity construction;
15. investigate the semantic status of `Role`;
16. only then proceed toward complete transformation composition,
    ownership and reference propagation.

This order is provisional.

A counterexample or newly discovered semantic dependency may legitimately
change it.

## Additional project observations

The review exposed one documentation drift not explicitly called out by the
reviewer.

The handoff currently describes continuity conceptually using an ordered
sequence of destinations.

The current candidate transformation model uses a set of destinations because
destination ordering is treated as deterministic representation rather than
additional continuity semantics.

The handoff should be corrected when updated.

## Conclusion

The review is accepted as useful research input.

Its most important contribution is not a proposal for additional ontology.

It identifies places where the existing candidate semantics can be made more
falsifiable:

```text
composition
associativity
partial-information semantics
negative equality cases
cyclic equality
real-model projection
formal-suite mutation
```

That is aligned with the purpose of `research/semantic-core`.

The next semantic milestone remains continuity composition, but documentation
state should be repaired first so that later work has an accurate continuation
point and research record.
