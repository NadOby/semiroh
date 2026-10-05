# Peer Review – Semantic Core Direction

Received: `2026-10-04T19:47+02:00`  
Reviewer: Claude Opus 5.5, at the project owner's request  
Status: external research review, not yet assessed by the project  
Branch reviewed: `research/semantic-core` at `0f380a4`, compared with `main` at `f101346`

This review is evidence and critique, not normative SHEAR semantics. It was
written from reading the branch, `main`'s normative documents and `main`'s
Python model. No Alloy command was executed for it. Claims about Alloy
behaviour are argued from the model text and marked as such.

The project's assessment of each recommendation belongs in a later section or
a separate entry, as was done for the first review.

## 1. Verdict

The question the branch asks – is there a smaller explicit basis from which
SHEAR can be rebuilt – is legitimate and worth answering.

The branch's discipline is good: falsification framing, H1/H2/H3 kept
separate, precise bounded-result vocabulary, non-vacuity witnesses paired with
checks, explicit expectations enforced by the runner, solver timeouts recorded
as "no result".

The execution so far is mostly a theory exercise. All evidence concerns the
candidate in isolation. No real SHEAR program, state or operation has been
projected into the candidate, so H1 – the hypothesis that decides whether the
rest matters – has not been tested at all. Several findings below suggest
that the first real projection will fail in ways the current Alloy suite
cannot detect.

The recommended change is one of method, not of goal: drive the experiment
from `main`, timebox it, and give it a kill criterion (section 11).

## 2. Is minimization sound here?

### Where it is justified

`main` has two structural systems that overlap:

- `Value(entity, content)`, whose content is an arbitrary canonical host tree;
- `Relation(kind, roles, payload)`, whose payload is another canonical tree.

Code is graph form, but data and payloads are host-shaped trees. Several
boundary failures listed in the charter (§1: host values versus semantic
values, mutable construction versus immutable state) live on that seam.
Collapsing value content, relation records and payloads into one relational
structure is a real simplification and is likely to pay off in less model
code, fewer conversion paths and fewer mutation survivors.

There is a second argument for a small basis that the charter does not make:
SHEAR's compiler and VM are also written in SHEAR. Every primitive case in the
core is a case the self-hosted lowering pass and VM must handle. The size of
`shear/examples/self_hosting.py` and `shear/examples/vm.py` is a concrete,
measurable H2/H3 metric for any candidate basis.

### Where it stops being sound

Uniform representations – cons cells, RDF triples, "everything is an object" –
are excellent for tooling, but the distinctions they erase come back as
conventions, and conventions are not checked.

For most languages that trade is acceptable. For SHEAR it is not, because
SHEAR's distinguishing claim is safe self-modification. Identity, continuity,
ownership and the reference/containment distinction are the safety mechanism.
They belong in the kernel, where violating them is rejected, not in a
convention layered over a uniform core.

The charter already says "smallest sufficient basis, not fewest primitives".
The candidate has crossed that line once (section 3), and nothing in the
current suite would notice a distinction being lost, because nothing compares
the candidate with `main`.

### Why it is premature

The hardest constraints on SHEAR's representation will come from areas the
README lists as not touched yet: systems data (structures, layout, references
between cells), native code, concurrency and modules. A systems language needs
addresses, sizes, aliasing and pinning; a purely relational core with
bisimulation equality is awkward for all of them. A basis chosen before those
requirements are known will likely be reopened when they arrive.

`main` progressed because programs forced decisions (the corpus, the
self-hosted compiler, the VM). The owner's stated rule is to defer decisions
until programs need them. The branch inverts that rule: it formalizes first
and looks for programs later. README §26 itself says formalization should
follow demonstrated semantic stability.

## 3. Finding: one edge kind where `main` has three

`main` distinguishes three kinds of edge:

| edge | where | shape | compared by |
|---|---|---|---|
| value containment | inside canonical content | acyclic tree | content |
| entity reference | `Relation` role endpoint, an `EntityID` | arbitrary, cycles allowed | name |
| ownership | ownership relation | forest | lifetime authority |

`semantic_equal` compares canonical bytes, and those bytes contain endpoint
`EntityID`s. Equality is therefore deep through containment and shallow at
references.

The candidate has one edge kind (role → occurrence) and one equality
(bisimulation through every edge). Consequences:

1. **The naive projection loses distinctions.** Two call nodes targeting `f`
   and `g` are unequal in `main`. In the candidate they become equal whenever
   `f` and `g` have bisimilar bodies. Keeping them distinct requires putting
   the `EntityID` into structure, which contradicts "EntityID is not
   intrinsic to relation value".

2. **The cyclic-equality question is a symptom.** `main` answered it
   structurally: containment and ownership are acyclic; cycles pass through
   references, which are compared by name. Once contained and referenced
   targets are distinguished, "self-cycle versus two-node cycle" largely
   disappears: acyclic content needs plain structural equality (hash-consing),
   and cycles never need unfolding.

3. **Incremental identity breaks.** If `VersionID` is derived from the
   candidate's equality, editing a leaf changes the identity of every
   ancestor and, through references, every caller. `graph_ledger.md` reports
   that a leaf edit in a 41- or 401-node function relowers one node, and rates
   incremental compilation "Strong" precisely because the cache key coincides
   with node identity. That measurement is a ready-made projection
   observable.

4. **Ownership cannot be derived from containment.** The candidate
   deliberately permits sharing (`SharingDoesNotForceInequality`), so a
   contained occurrence has no unique structural parent. Ownership is a forest
   in `main`. It therefore needs its own edge kind or its own relation; it is
   not derivable from containment alone.

Recommendation: decide early whether a role target can be either a contained
occurrence or a referenced name. This is a distinction of target kind, not a
new object kind, so it is compatible with "the relation is the only
graph-semantic object".

## 4. Finding: occurrence handles are a hidden identity

The charter states that `RelationRef` "is not persistent semantic identity"
and that `EntityID` lives only in an entry-scoped view. But continuity claims
and `View.entities` are both defined on occurrences.

In Alloy this is invisible, because each `Rel` atom is distinct; Alloy atom
identity silently plays the role of an identity primitive.

Outside Alloy, one of two things must hold:

- **Occurrences are not semantic.** Then the meaning of a state must be
  invariant under renaming of handles. A state containing two disconnected
  `1` occurrences has an automorphism swapping them. The claim "the first
  continues to `y`, the second disappears" is not invariant under that
  automorphism, so it has no handle-independent meaning. Splits and partial
  disappearance among equal values become inexpressible. State identity
  also needs a canonical form up to renaming – polynomial if states are
  quotiented by bisimulation, but then equal occurrences merge and
  occurrence-level continuity disappears entirely.

- **Occurrences are semantic.** Then `RelationRef` is an identity, and the
  candidate has two identity notions (occurrence and `EntityID`) where `main`
  has one.

`main` avoids the dilemma: every entity has an `EntityID`, continuity is
stated over `EntityID`s, and `StateID` hashes `(EntityID, content)` pairs.
Names are part of state content.

A related practical consequence is the frame problem. In `main` an untouched
entity keeps its `EntityID` in the destination state, so a running program's
cell can keep holding a function's `EntityID` (README: function references
held in cells do not follow renames). With state-local occurrences, nothing
links an `S1` occurrence to an `S2` occurrence except an explicit claim. Every
entity anyone may still refer to then needs a claim at every step, and
transformation records grow with the state rather than with the change.

Recommendation: state explicitly which identity the candidate uses for
continuity and state identity, and add a witness that exposes the automorphism
case rather than letting Alloy atom identity answer it.

## 5. Finding: continuity composition already exists in `main`

`docs/transformation_composition.md` and `transforms.compose` define the
rule the branch calls its "leading candidate": Unknown absorbs, explicit
disappearance drops out, split branches are unioned, a partially unknown split
is Unknown. `tests/test_transform_composition.py` already tests associativity
for chains, split/merge and Unknown.

None of the research documents cite this. The handoff describes the rule as a
hypothesis not yet encoded or verified.

This is good news for H1: it is the cheapest available projection. Generate
bounded instances from `transformation_model.als`, translate them to
`TransformationDefinition`s, run `compose`, and compare. Differences worth
classifying include `main`'s third outcome (a source absent from both
`mappings` and `unknown_sources`) and the candidate's state-compatibility
requirement, which `main`'s definitions do not carry.

### The algebra, and a simpler encoding

The rule is Kleisli composition for `Option ∘ Set` with absorbing `None`.
Represent continuity information as a known set `K` and a map `M ⊆ K × Dst`:

```text
compose((K1, M1), (K2, M2)) = (K, K <: M1.M2)
    where K = { s ∈ K1 | M1[s] ⊆ K2 }
```

`s ∈ K` with empty image is explicit disappearance; `s ∉ K` is Unknown.

Associativity, unbounded:

```text
left  K = { s ∈ K1 | M1[s] ⊆ K2  and  M2[M1[s]] ⊆ K3 }
right K = { s ∈ K1 | M1[s] ⊆ { b ∈ K2 | M2[b] ⊆ K3 } }
```

These sets are equal, and both maps are `K <: M1.M2.M3` because relational
join is associative.

Monotonicity under the flat order `Unknown ≤ Known(S)`: refining inputs only
changes Unknown entries to Known ones. A composed result that was Known
depended only on inputs that were already Known, so it cannot change.
Refinement can turn a composed Unknown into Known, never change a Known
result.

In Alloy this encoding removes `ContinuityClaim` and `AtMostOneClaimPerSource`
(functionality becomes automatic). Associativity can then apply the actual
operator to a composed result, instead of comparing two hand-written
expansions as `transformation_associativity.als` currently does.

## 6. Finding: H3 is measured in the wrong place

The first review's recommendation to "treat formal complexity as H3 evidence"
was accepted. Solver time for model-checking the specification is not the
cost of the semantics. H3 asks whether SHEAR can be implemented efficiently;
`CompositionIsBisimulation` taking 3 or 96 minutes says something about the
Alloy encoding, not about SHEAR.

The relevant complexity facts are already known:

- bisimilarity of two roots in a finite deterministic labelled graph:
  near-linear with union-find (Hopcroft–Karp style);
- a canonical form up to bisimilarity: `O(m log n)` partition refinement;
- canonical form up to isomorphism without bisimulation quotienting: graph
  canonization, with no known polynomial algorithm in general.

H3 evidence should come from the implementation side: identity recomputation
per edit, relowering counts, transformation record size per edit, and the size
of the self-hosted compiler and VM.

## 7. Finding: H2 needs a map in the other direction

The commuting square in charter §7.2 uses `π : Current → Core`. That tests
representation (H1). Construction (H2) needs the reverse: an interpretation
`σ : Core → Current` for a fragment, with `σ ∘ π` agreeing with identity on
the chosen observables. Without `σ`, a successful `π` shows only that current
states can be encoded, not that current concepts can be built from the core.

## 8. Verification hygiene

- **Textbook lemmas.** Identity, converse and composition of bisimulations
  are textbook results with short hand proofs. Hours of SAT time and a solver
  study were spent confirming them. Bounded checking is most valuable on
  model-specific claims and on hunting counterexamples.

- **No-soundness is unchecked.** `0f380a4` closes a real hole: before it, an
  unreachable contradictory pair could make `EqualityNo` hold for equal roots.
  The fix came from reasoning; no command would have caught it. Add an
  assertion that `EqualityNo` excludes any bisimulation containing the root
  pair, using a witness signature (as `BisimWitness` does) so the check stays
  first-order.

- **`ClosedBoundedComparisonIsBisimulation`** restates the definition of
  `EqualityYes`. It is a model sanity check and should be classified so.

- **Dead file.** `formal/core_equality_negative.als` is superseded by the
  negative section of `core.als` and is not listed in the workflow. Its
  `run`s place `not valueEqual` (a higher-order universal) inside a `run`,
  which Alloy may refuse to skolemize. Remove it.

- **Silent gaps.** The workflow's explicit model list lets a new `.als` file
  go unrun without notice, which is how the dead file went unnoticed. Mirror
  `tests/lanes.py`: every top-level `formal/*.als` with commands must be
  listed, or marked as a library, or CI fails.

- **Single hand-picked mutant.** `transformation_composition_mutation.als`
  shows that one property kills one mutant chosen to be killed by it.
  Mechanically generated mutants of `transformation_model.als` (drop a
  conjunct, swap `all`/`some`, swap `in`/`not in`) run against the whole
  suite would be cheap and informative, and would reuse the thinking behind
  `main`'s mutation catalog.

- **Budget versus Unknown.** `query_outcomes.als` treats budget exhaustion as
  evaluator status, not semantic Unknown. `constraint_model.md` §5 says
  exhausted budget yields `Unknown`. The research position is arguably
  better, but it is an unrecorded divergence from a normative `main`
  document and should be logged as an H1 mismatch.

- **Structural equality is decidable.** On finite states structural equality
  always has a definite answer. `Unknown` belongs to semantic equivalence
  (for example extensional equality of functions), not to structural
  equality. README §11 should eventually say so.

## 9. Documentation and process

- **Volume.** Of about 12.2k added lines, about 6.6k are prose, 4.7k Alloy and
  0.9k CI. Most of the prose describes verification process rather than
  semantics. `handoff.md`, described as compact, is 578 lines with about 320
  lines of content; one-word code blocks inflate every document.

- **Drift.** Nine hours after its refresh, `handoff.md` names two removed
  workflows and lists continuity composition, explicit-expect hardening,
  negative equality and cyclic equality as not done. `transformation_verification.md`
  and the open-target list in `alloy_verification.md` have drifted the same
  way. Every additional document is another place to drift. Command
  inventories, expectations and evidence categories could be generated from
  the `.als` files instead of maintained by hand in four places.

- **Closed over the branch.** The branch's documents, its first review and its
  handoff reference only each other. Neither review compared the candidate
  with `main`. The handoff should list the `main` documents the candidate must
  answer to: `identity_model.md`, `transformation_model.md`,
  `transformation_composition.md`, `reference_model.md`,
  `ownership_model.md`, `constraint_model.md` §5, `activation_model.md` §4
  and `graph_ledger.md`. Future reviews should be asked to compare against
  them.

- **Commit churn.** Six "auto-discovered entrypoints" commits followed by a
  restore and six deletions suggest that the manual file-transfer workflow is
  costing more than it protects. Batching changes, or letting sessions push
  to the research branch, would reduce it.

## 10. What is not established by this review

- No Alloy command was run; section 8's skolemization remark is argued, not
  observed.
- The projection failures in sections 3 and 4 are predicted from the models'
  definitions. They become evidence only when a projection is built and the
  mismatch is observed.
- The proofs in section 5 are hand proofs, not mechanized.

## 11. Recommended plan

Reframe the branch as a refactor-driven experiment on `main`, timeboxed, with
a kill criterion.

1. **Projection first.** Build `π` for a narrow fragment and run every program
   in `shear/examples/` through it. Observables: `semantic_equal`, call
   targets, `StateID` stability under unchanged content, and the ledger's
   relowering count after a leaf edit.
2. **Decide the edge kinds.** Contained occurrence versus referenced name, and
   ownership as its own relation. Decide which identity continuity uses
   (section 4).
3. **Differential composition.** Alloy-generated instances against
   `transforms.compose` (section 5). Re-encode composition as `(K, M)`.
4. **Pick one real seam.** Unify `Value` content, `Relation` payload and
   relation records in `main` behind a compatibility boundary. Measure model
   size, mutation survivors and self-hosted compiler size before and after.
5. **Only then** entry-scoped identity, `Role`, ownership derivation and
   `σ` for H2.

Kill criterion: if the corpus cannot round-trip through `π` with its
observables preserved within a fixed budget (for example two weeks of
sessions), park the branch and record why. Under the charter, a recorded
negative result is a valid outcome.

Taken this way, the branch either delivers a concrete simplification to
`main` or shows cheaply that the current layering is already close to
minimal.

## 12. Project assessment

Assessed: `2026-10-05T09:41+02:00`, in discussion between the project owner,
the research session and the reviewer.

The review is adopted as the working direction, with the corrections below.
Its proposed architecture (sections 3 and 4) is not adopted. Those sections
are treated as predictions to test, not as design conclusions.

### Accepted

- Continuity composition is not a new semantic question. `main` already
  defines the same algebra in `transformation_composition.md` and implements
  it in `transforms.compose`. The next step is a differential comparison
  with `main`, not further invention.
- `main` and the candidate differ in equality around references. `main`
  compares endpoint `EntityID`s shallowly. The candidate bisimulates through
  role targets. A naive projection can make relations that refer to
  different, structurally equal entities equal. This is a real H1 mismatch
  that needs a decision or a failed-projection witness.
- H1 has barely been tested. Current evidence shows internal consistency of
  the candidate, not preservation of existing SHEAR semantics.
- Alloy solver cost is formalization cost, not H3 evidence about
  implementation cost.
- H2 needs more than `π : Current → Core`. Some constructive demonstration
  is required. A literal inverse is stronger than necessary.
- `formal/core_equality_negative.als` is outside CI and must be removed or
  classified as a library. Whether Alloy rejects its higher-order `run`s
  remains unverified.
- `EqualityNo` needs an independent soundness assertion.
- A kill criterion is required.

### Corrected

- **Occurrence handles (section 4).** Within one transformation, taken as a
  whole structure up to isomorphism, "one of two equal occurrences continues,
  the other disappears" is well defined. "Inexpressible" overstated it, and it
  is not shown that `RelationRef` must become semantic identity. The open
  question is what makes occurrence reference well defined outside Alloy, and
  under which renamings semantics must be invariant.
- **Where the handle problem appears.** It appears in composition.
  `transformationsCompatible` requires the middle states to be the same Alloy
  `State` atom, which presupposes a shared handle universe. `main` composes
  over stable `EntityID` mappings and needs no such universe. The
  falsification case is:

  ```text
  T1 : S0 -> M1
  T2 : M2 -> S2

  StateID(M1) == StateID(M2)
  M1 and M2 independently constructed
  M contains two structurally equal, otherwise symmetric occurrences
  ```

  Does the candidate determine a unique composition without an externally
  chosen isomorphism `M1 ↔ M2`? A control case with no automorphism in `M`
  isolates symmetry as the cause.
- **State identity.** The test needs a candidate definition of `StateID`.
  "Equal up to renaming of occurrence handles" is recorded as the explicit
  candidate hypothesis needed to run the experiment, not as settled
  semantics.
- **`StateID` definition (section 4).** `main`'s `StateID` hashes each
  `(EntityID, VersionID)` pair and the ownership relation, not
  `(EntityID, content)` pairs. Because `VersionID` derives from `EntityID`
  and semantic content, the argument is unchanged: equal `StateID`s already
  imply the same entity naming and ownership structure.
- **Mechanism inventory (section 11, step 4 and handoff).** The pinned
  `Reference(StateID, EntityID, VersionID)` is counted as its own mechanism.
  Relation payload is merged into the value-content and relation-record
  entries rather than counted separately.
- **Cyclic equality (section 3, point 2).** "Largely disappears" assumes the
  containment/reference distinction survives. That is what the branch tests.
  It is a projection prediction.
- **Recursion.** `main`'s recursive corpus programs contain self-reference
  through explicit `EntityID` links. A cycle appears in the candidate only if
  the projection turns references into structural edges. Recursion is
  therefore the case that forces the projection to reveal its choice: a
  structural edge (a cycle, making cyclic equality urgent) or a
  reference-bearing form (the target-kind distinction under another name; if
  it carries `EntityID` as content, it conflicts with "EntityID is not
  intrinsic"). The choice and its consequences for equality and identity are
  recorded as an experimental result.
- **Budget exhaustion (section 8).** This is a semantic boundary question,
  not simply an H1 mismatch: constraint evaluation and structural equality
  are different operations. README §11 defines equality results as
  `Equal / NotEqual / Unknown` and ties equality to potentially expensive
  reasoning, but does not specify `BudgetExhausted → Unknown`. That mapping
  is an interpretation to test. `7b7dd31` makes exhausted equality return no
  semantic result.
- **Decidability (section 8).** True for the finite structural model. It
  does not settle the project-wide meaning of semantic equality.

### Adopted execution plan

1. Finish the `query_outcomes.als` soundness cleanup and CI.
2. Resolve the orphan `core_equality_negative.als`.
3. Freeze candidate semantics and the mechanism inventory.
4. Record the candidate `StateID`/equivalence hypothesis.
5. Implement one narrow `main → candidate → observable` projection.
6. Run the existing corpus plus a small adversarial corpus:
   reference target identity versus structural equality; recursive
   self-reference; symmetric and asymmetric independently constructed middle
   states; continuity composition with split, merge, disappearance and
   Unknown.
7. Allow at most one candidate revision in response to failures.
8. Evaluate H1 from the predeclared mechanism table and round-trip failures.
9. If H1 fails, use those failures to define the smallest
   compatibility-boundary refactor back into `main` – likely consolidating
   `Value` content, relation records and payload representation rather than
   replacing the identity and reference machinery.

The timebox is structural, not calendar-based: one projection, the existing
corpus plus the adversarial corpus, one candidate revision, then evaluation.
No second redesign cycle.

Each inventoried mechanism of `main` is classified after the experiment as:

```text
eliminated by the candidate
retained unchanged
represented uniformly by an existing candidate mechanism
requiring a new special case or mechanism
```

If the candidate needs new special cases faster than it eliminates existing
mechanisms, H1 stops.
