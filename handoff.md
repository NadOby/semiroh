# Semantic Core Research Handoff

Branch: `research/semantic-core`  
Status: active architectural experiment  
Refreshed: `2026-10-05T09:41+02:00`

Compact continuation checkpoint. History belongs in
`docs/research/semantic-core/project_diary.md`; evidence belongs in the
verification documents.

## Working procedure

- Inspect the live branch before judging current state.
- GitHub writes are made by the owner, or by a session when the owner
  permits it. Work one coherent change at a time.
- `project_diary.md` is append-only.
- Alloy runs in GitHub Actions only. Do not run Alloy locally or claim local
  Alloy results.

## Objective

Test whether SHEAR can be rebuilt from a smaller explicit basis centred on
generalized relations, while preserving intended semantics, constructibility,
independent verification and practicality.

- **H1 – representation:** current SHEAR semantics survive projection into
  the candidate without losing intended distinctions.
- **H2 – construction:** current concepts can be built from the candidate.
- **H3 – practicality:** both are implementable at acceptable cost,
  measured on the implementation side, not by Alloy solver time.

The candidate must now explain existing SHEAR, not merely stay internally
consistent.

## Candidate core (frozen for the experiment)

```text
Relation = { atom : Atom?, roles : Role -> Sequence<RelationRef> }
```

- `RelationRef` is a state-local occurrence handle, not persistent identity.
- State: finite relational structure, no universal root.
- View: `state`, `entry`, `entities : EntityID -> occurrence`
  (view-scoped; entry-derived namespaces are not established).
- Value equality: bisimulation.
- Continuity per source occurrence: `Unknown | Known(Set<occurrence>)`;
  `Known({})` is explicit disappearance.
- Composition: Unknown absorbs, disappearance drops out, split branches
  union, a partially unknown split is Unknown. This matches `main`'s
  `transforms.compose`.

`RoleUse`, `Slot`, `BisimWitness`, `CompositionCase`, `ContinuityClaim`,
`Comparison` are Alloy scaffolding, not candidate ontology.

No new candidate semantics are added before step 7 of the plan.

## Established (bounded Alloy evidence)

- Bisimulation identity, reversal, composition, with non-vacuity witnesses.
- Distinct `EntityID`s can name equal values; sharing topology need not
  determine equality.
- Continuity representation: unknown versus disappearance, 1→1, split,
  merge, equal values without continuity.
- Continuity composition cases, associativity and one targeted mutation
  passed in the first consolidated workflow run.

Committed, results to read from the latest CI run before citing: negative
equality checks and the self-cycle witness in `core.als`; everything in
`query_outcomes.als`.

## Not established

H1, H2 and H3 in general; entry-derived identity; candidate `StateID`;
well-defined composition across independently constructed states; ownership
derivation; reference semantics; unbounded results.

## Active execution plan

Adopted from the direction review and its assessment:
`docs/research/semantic-core/peer_reviews/2026-10-04-semantic-core-direction-review.md`
§12.

1. Finish the `query_outcomes.als` soundness cleanup and CI. Remaining:
   an independent soundness assertion for `EqualityNo` (no bisimulation
   containing the root pair exists when it holds), using a witness
   signature so the check stays first-order.
2. Resolve `formal/core_equality_negative.als`: superseded by `core.als`
   and not in the workflow. Remove it, or classify it as a library. Then
   make the workflow fail when a top-level `formal/*.als` with commands is
   not listed.
3. Freeze candidate semantics and the mechanism inventory (below).
4. Record the candidate state-identity hypothesis: `StateID` equality is
   equality up to renaming of occurrence handles. This is a hypothesis
   needed to run the experiment, not settled semantics.
5. Implement one narrow `main → candidate → observable` projection.
6. Run the existing corpus plus the adversarial corpus (below).
7. Allow at most one candidate revision in response to failures.
8. Evaluate H1 from the mechanism table and the round-trip failures.
9. If H1 fails, use the failures to define the smallest
   compatibility-boundary refactor into `main` – likely consolidating
   `Value` content, relation records and payload representation, not
   replacing identity and reference machinery.

Timebox (structural): one projection, the existing corpus plus the
adversarial corpus, one candidate revision, then evaluation. No second
redesign cycle.

Stop rule: if the candidate needs new special cases faster than it
eliminates existing mechanisms, H1 stops.

## Projection observables

- `semantic_equal` on projected values;
- call and link targets;
- `StateID` stability for unchanged content;
- continuity results of `transforms.compose`;
- the ledger's relowering count after a leaf edit (`graph_ledger.md`).

## Adversarial corpus

1. **Reference target identity versus structural equality.** Two relations
   referring to different entities with bisimilar content must stay unequal
   if `main` keeps them unequal.
2. **Recursive self-reference.** A recursive corpus program such as
   factorial, whose `links` relation points back to its own entity. Record
   which representation the projection chose, as an experimental result:
   - structural edge → a cycle; cyclic equality becomes urgent;
   - reference-bearing form → the target-kind distinction under another
     name; if it carries `EntityID` as content, it conflicts with
     "EntityID is not intrinsic".
   Record the consequences for equality and identity.
3. **Independently constructed middle states.**

   ```text
   T1 : S0 -> M1
   T2 : M2 -> S2
   StateID(M1) == StateID(M2), built independently
   ```

   - symmetric: `M` has two structurally equal, otherwise symmetric
     occurrences;
   - asymmetric control: `M` has no automorphism.

   Question: does the candidate determine a unique composition without an
   externally chosen isomorphism `M1 ↔ M2`? A failure only in the symmetric
   case is an observed H1 failure caused by symmetry.
4. **Continuity composition** with split, merge, disappearance and Unknown,
   compared case by case with `transforms.compose`.

## Mechanism inventory (draft – freeze at step 3)

Mechanisms of `main` the candidate claims to replace or represent:

```text
Value(entity, content) and canonical content trees
Relation records (kind, roles, payload)
Relation payload trees
EntityID endpoints in relation roles
Ownership forest
VersionID derivation
StateID derivation
TransformationMapping / CompositionResult (mappings, unknown_sources)
```

After the experiment, classify each as:

```text
eliminated by the candidate
retained unchanged
represented uniformly by an existing candidate mechanism
requiring a new special case or mechanism
```

## `main` documents the candidate must answer to

`identity_model.md`, `transformation_model.md`,
`transformation_composition.md`, `reference_model.md`,
`ownership_model.md`, `constraint_model.md` §5, `activation_model.md` §4,
`graph_ledger.md`, README §11.

## Open boundary question

Budget exhaustion: `main`'s constraint model maps it to `Unknown`; README
§11 does not specify it for equality. `query_outcomes.als` (since `7b7dd31`)
returns no semantic result on exhaustion and reports only evaluator status.
This is a semantic boundary question, not yet a decided divergence.

## Files

```text
formal/core_model.als                 candidate core
formal/core.als                       core checks and witnesses
formal/query_outcomes.als             bounded equality outcomes
formal/transformation_model.als       continuity and composition
formal/transformation*.als            transformation entrypoints
formal/core_equality_negative.als     orphan, see plan step 2
.github/scripts/AlloyRunner.java      instrumented runner
.github/workflows/alloy-verification.yml   all Alloy commands, lingeling.parallel
.github/workflows/semantic-model.yml  Python model tests

docs/semantic_core_experiment.md                    charter
docs/research/semantic-core/alloy_verification.md   verification policy
docs/research/semantic-core/core_verification.md    core evidence
docs/research/semantic-core/transformation_verification.md
docs/research/semantic-core/continuity_composition.md
docs/research/semantic-core/alloy_api_reference.md
docs/research/semantic-core/project_diary.md        append-only log
docs/research/semantic-core/peer_reviews/
```

`transformation_verification.md`, `continuity_composition.md` and the
open-target list in `alloy_verification.md` predate the composition and
equality work and still describe it as future work.

## Verification language

Use: bounded check passed, bounded counterexample found, bounded witness
exists, no result, not established. Never present bounded UNSAT as a
theorem. Pair important implication checks with non-vacuity witnesses.
