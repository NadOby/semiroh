# H1 Evaluation – Step 8

Status: evaluation of the semantic-core experiment  
Branch: `research/semantic-core`  
Inputs: `projection_results.md` (runs at `0950761`, `cb74cea`, `6739252`),
charter §3.11 and §3.12, the mechanism inventory in `handoff.md`

This is the step-8 evaluation the plan calls for: each inventoried `main`
mechanism classified for the frozen candidate and for revision 1, the stop
rule applied, the H1 verdict, and what follows for H2, H3 and step 9.

It is a judgement over recorded results. No experiment was re-run for it.
It incorporates the review of the draft by the research session
(2026-10-05).

## 1. Verdict

**The experiment falsifies H1 for the frozen candidate**, within the tested
scope (26 corpus programs, 21 continuity cases, the adversarial cases).
Relations whose targets are only contained occurrences cannot represent
`main`'s references to named entities without losing an intended semantic
distinction: equality conflates distinct referents (4,379 entity pairs in
real programs that `main` keeps apart). The failure is not only a cost:
version identity also propagates to ancestors and callers (129 of 549
entities after one leaf edit in `compiler`, against 2), but the repair that
restores the lost distinction is what reintroduces named identity.

**Revision 1 survives every tested observable, but no longer demonstrates a
smaller basis.** It survives all tested identity, reference, continuity,
state-identity and churn observables, with 10 of 10 predeclared predictions
hit and no unexpected mismatches. H1 is not established universally – it is
worded over every intended state, the evidence is finite – and the arity
distinction remains unresolved (§2.2). More importantly for the hypothesis,
revision 1 achieves this by restoring `main`'s identity architecture: names
in values that refer to them, names in state identity, continuity over
names. Charter §3.8 ("EntityID is not intrinsic") is given up.

**What survives is a representational consolidation, not a semantic
reduction.** `main`'s separate layers for value content, relation records and
relation payloads can be one relational structure with typed atoms, ordered
role sequences and two target kinds. The identity, version, state-identity,
reference and continuity mechanisms are retained.

This is an observation about one implementation layer, kept separate from the
mechanism-count stop rule (§2.1), which revision 1 fails.

The hypothesis the branch set out to test – that SHEAR can be rebuilt from a
smaller explicit basis centred on generalized relations, with identity held
separately – is therefore falsified in its strong form and confirmed only in
the weak form above.

## 2. Mechanism table

Classifications: **E** eliminated · **R** retained unchanged · **U**
represented uniformly by an existing candidate mechanism · **N** requires a new
special case or mechanism · **F** not representable without loss.

| # | `main` mechanism | frozen candidate | revision 1 | evidence |
|---|---|---|---|---|
| 1 | canonical semantic value representation (`Value` + canonical content) | U | U | O0: 3,760 of 3,760 entities round-trip modulo arity in all modes |
| 2 | relation record representation (kind, roles, payload) | U | U | O0, O2; relations project to `symbol:relation:<kind>` with one role per `main` role |
| 3 | `EntityID`-valued relation endpoints | F | N | frozen: O1 4,379 conflated pairs, O5 churn; `REF` keeps them only as atoms. Revision 1: the `Named` target kind |
| 4 | ownership forest | U (edge set only) | U (edge set only) | the edge set is ordinary per-edge `owns` relations; O3 agrees after the projection fix. The forest semantics – one owner, acyclicity, destruction and lifetime, ownership following continuity – are retained as `main`'s rules and do not emerge from generic relations. H2 not established for them |
| 5 | `VersionID` derivation | F | R | frozen: value class churns (22, 202, 129 against 1, 1, 2). Revision 1: value class changes exactly where `VersionID` does |
| 6 | `StateID` derivation | coarser by design | R (semantics) | frozen: §3.11 isomorphism equates renamed states (predicted). Revision 1: the semantic mechanism is retained, the representation differs – `main` hashes entity and version identity plus ownership, revision 1 tests isomorphism with names fixed. They agree on all 228 O3 pairs because revision 1 restores names to state identity |
| 7 | pinned `Reference(StateID, EntityID, VersionID)` | F (not tested) | R (not tested) | no observable. Frozen: occurrences have no identity across states, so a reference has nothing stable to name. Revision 1: maps directly to (state identity, name, value class) |
| 8 | continuity representation | U, with a defect | R | frozen: real chains agree (O4), but continuity over anonymous occurrences depends on the chosen isomorphism in symmetric states. Revision 1: the algebra is unchanged and its domain returns to names, which is `main`'s `compose`; 138 of 138 agree, no isomorphism search. Not an elimination of continuity as a semantic mechanism |

Tally:

| | E | R | U | N | F |
|---|---|---|---|---|---|
| frozen candidate | 0 | 0 | 4 (1, 2, 4, 8) | 0 | 3 (3, 5, 7), plus 6 coarser by design |
| revision 1 | 0 | 4 (5, 6, 7, 8) | 3 (1, 2, 4) | 1 (3) | 0 |

### 2.1 Stop rule

"If the candidate needs new special cases faster than it eliminates existing
mechanisms, H1 stops."

- Frozen candidate: three mechanisms cannot be represented without loss. H1
  stops for it regardless of the rule.
- Revision 1 **fails the strict predeclared rule**: it adds one target
  distinction (named targets with bindings in the state, plus the
  acyclic-containment rule that comes with it) and eliminates no inventoried
  semantic mechanism.
- Separately, it exposes a plausible one-layer representational
  consolidation: mechanisms 1 and 2 become one relational-content structure.
  That observation is not counted as an elimination; counting it would
  change the predeclared arithmetic after the fact.

### 2.2 The arity collapse

`main` distinguishes a single endpoint from a one-element tuple in relation
roles (`Endpoint = EntityID | tuple[EntityID, ...]`); the candidate's roles are
sequences, so the two project alike. This affects 316 entities and no equality
result.

Judgement: likely redundant for graph-form code; unresolved for arbitrary and
non-code relations. For code relations, `operations.py` already records fixed
and variable arity, code roles and ordered roles, so the shape is recoverable
from the relation kind. `main`'s generic `Relation` representation still
distinguishes a single endpoint from a one-element tuple, and that has not
been checked for non-code kinds (definitions, cells, constraints). Revision 1
is not declared fully H1-preserving until it is.

## 3. H2 – construction

Positive evidence for the tested data fragment only: `decode` inverts the
projection on content in all three modes (the data-fragment interpretation
σ). H2 as defined covers ownership, lifetime, constraints, closures,
execution, effects, capabilities and provenance; none was derived from the
candidate. H2 is not established.

## 4. H3 – practicality

- **The frozen candidate has an observed, severe locality failure.** Deriving version
  identity from contained-only equality makes a leaf edit touch every
  ancestor and every transitive caller. In `compiler` that is all five
  functions. It removes the incremental-compilation advantage
  `graph_ledger.md` rates as Strong. That alone rejects it as practical.
- **Revision 1 removes the measured churn regression** (1, 1, 2, as
  `main`). With acyclic containment, value equality needs no bisimulation.
  That is all H3 evidence shows for it: graph size, matching cost, compiler
  complexity and implementation complexity were not benchmarked, so H3 is
  not established for revision 1.
- **Alloy solver time is not H3 evidence** about SHEAR; it measured the cost
  of checking the specification.

## 5. Consequences for the branch

- **The bisimulation and cyclic-equality work is moot for revision 1.**
  Containment is acyclic and cycles pass through names, so equality is plain
  structural equality. The Alloy core suite remains a correct record of the
  frozen candidate.
- **Entry-scoped identity and `Role` as a primitive** – both open in the
  handoff – are not needed by any result. Revision 1 puts bindings in the
  state, not in an entry-scoped view.
- **The experiment reached its stopping point** under the structural timebox:
  one projection, the corpus plus adversarial cases, one revision, this
  evaluation. No second redesign cycle.

## 6. What to record in `main`

Four independent semantic relationships must remain distinguishable – not
four primitive edge types:

```text
within a state:
    structural / value containment
    named reference                  to stable entity identity
    ownership                        an edge set with forest constraints

between states:
    continuity                       declared by transformations, over names
```

The experiment showed that conflating containment and named reference is
wrong. It did not show that the graph substrate needs primitive edge
classes. `main` already treats ownership and ordinary references as different
relations.

On identity: **`EntityID` is not continuity; it is the stable vocabulary in
which continuity can be stated.** A stable entity identity is primitive;
cross-state continuity is declared by transformations, and identity does not
determine it – `main` says so explicitly. Path-derived identifiers were
considered after the run: they are useful locators but not sufficient
semantic identity, because an identity derived from the current state alone
can say "same position" or "same content", never "same thing, moved". That
rejects paths as identity, not paths or selectors as part of a reference
anchored at a stable identity, such as `(EntityID(A), field y)`.

The promising simplifications are therefore horizontal – removing duplicate
mechanisms within these axes – not vertical reductions of identity, time or
lifetime into graph topology.

## 7. Recommendation for step 9

Step 9 was defined as "if H1 fails, use the failures to define the smallest
compatibility-boundary refactor into `main`". The failures point at one
candidate change only: unifying `Value` content, relation records and payloads
into a single relational content form with typed atoms and `EntityID`
references as a distinct target kind.

The experiment shows this is representable without loss. It does not show
that `main` becomes simpler, safer or smaller by doing it. That is a separate
claim, and it should be tested as one:

1. Treat step 9 as an ordinary `main` roadmap task with its own plan, not an
   automatic consequence of this branch.
2. Measure the costs it claims to remove soon, as a baseline, before other
   work changes the code: conversion paths between host values and canonical
   content, mutation survivors in `canonical.py`, `values.py` and
   `relations.py`, and the size of the self-hosted compiler and VM where they
   handle content shapes.
3. Decide only later, after the constraints experiment and the layout spike,
   which may change what the right content representation is. Proceed only
   if the costs are material, preserve the existing
   `EntityID`, reference and ownership semantics, and require a concrete
   reduction in production mechanisms or conversion paths. Confirm the arity
   question (§2.2) first.

If those measurements do not show a material cost, the correct result of this
branch is a recorded negative: `main`'s current layering is already close to
the smallest sufficient basis for SHEAR's identity requirements.

## 8. What is not established

- Any unbounded property; any result outside the 26 corpus programs, the 21
  continuity cases and the adversarial cases.
- Ownership lifetime, references (mechanism 7), constraints and runtime
  activation under either candidate.
- That the consolidation in §7 would improve `main`.
- H1 universally, H2, or H3 for revision 1.
