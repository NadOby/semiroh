# Semantic Core Research Handoff

Branch: `research/semantic-core`  
Status: active architectural experiment  
Refreshed: `2026-10-05T15:27+02:00`

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

Candidate semantics were frozen until step 7. Step 7 added revision 1, named
roots (charter §3.12, `research/core_projection/named.py`), additively: `core.py`
and the `STRUCT` and `REF` projection modes remain the record of the frozen
candidate. There is no second revision; if revision 1 also fails, that is the
step-8 result.

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

1. Done: `EqualityNo` is checked against an independent bisimulation
   witness (`7f66c36`); that command passed in run `37281614361`. Confirm
   the rest of that run's matrix before citing the whole file as passing.
2. Done: `formal/core_equality_negative.als` deleted (`d07a4dd`); the
   workflow fails when a top-level `formal/*.als` with commands is not a
   listed entrypoint.
3. Done: candidate semantics frozen until step 7; mechanism inventory
   fixed (below).
4. Done: experimental candidate `StateID` hypothesis recorded in
   `docs/semantic_core_experiment.md` §3.11 – isomorphism under bijective
   handle renaming, view `EntityID` bindings excluded, equivalence only, no
   hash specified, unchanged until step 7.
5. Done: one narrow `main → candidate → observable` projection
   (`research/core_projection/`, plan `projection_plan.md`).
6. Done: run on the existing corpus plus the adversarial corpus. First run
   `0950761`, re-run after review `cb74cea` (ownership projection fixed to
   one relation per edge; O5 `STRUCT` predicted; cross-function churn
   scenario added). Results and deviations from the plan:
   `docs/research/semantic-core/projection_results.md` (re-run: 0 unexpected
   mismatches, 5,172 predicted, 0 gaps).
7. Done: the single candidate revision, revision 1 named roots
   (`revision_plan.md`, charter §3.12, `named.py`, projection mode `NAMED`),
   run once with the predictions recorded before the run (run at `6739252`).
   Result: 10 of 10 predictions hit, 0 unexpected mismatches, 0 gaps; `STRUCT`
   and `REF` reproduce the `cb74cea` counts exactly (checked by the runner).
   Cost: names enter values and state identity (charter §3.8 given up). The
   arity collapse is unchanged. Not interpreted for H1; see "Revision 1 run" in
   `projection_results.md`, which also lists the choices the plan left open.
8. Done: H1 evaluation in `h1_evaluation.md`. H1 fails for the frozen
   candidate (named references not representable without loss). Revision 1
   survives every tested observable but fails the strict stop rule and
   restores `main`'s identity architecture, giving up charter §3.8. What
   survives is a possible consolidation of value content, relation records
   and payloads, not a smaller basis.
9. If H1 fails, use the failures to define the smallest
   compatibility-boundary refactor into `main` – likely consolidating
   `Value` content, relation records and payload representation, not
   replacing identity and reference machinery.

Timebox (structural): one projection, the existing corpus plus the
adversarial corpus, one candidate revision, then evaluation. No second
redesign cycle.

Stop rule: if the candidate needs new special cases faster than it
eliminates existing mechanisms, H1 stops.

Next: the experiment is closed. Follow-ups are ordinary `main` roadmap tasks,
agreed with the reviewing session, in this order:

1. Audit endpoint arity: semantic or redundant outside code.
2. Audit `Reference(StateID, EntityID, VersionID)`: can a valid reference
   distinguish anything with `VersionID` that `(StateID, EntityID)` cannot?
   Today `StaleReference` is reachable only after the `StateID` check.
3. Measure duplicated content-handling machinery (conversion sites, mutation
   survivors in `canonical.py`/`values.py`/`relations.py`, compiler content
   handling). No refactor. This is the baseline of what the experiment
   exposed, taken before later tasks change the code.
4. Constraints as ordinary SHEAR functions: a falsification experiment.
5. Layout-changing hot swap with live interior references: the next research
   spike; Alloy returns for the activation and lifetime protocol.
6. Decide whether the content consolidation is still justified, from the
   measurement in 3 plus anything learned in 4 and 5.

Guardrails:

- Audits are audits, not pre-authorised refactors. Each ends as redundant,
  semantically required, or retained deliberately for engineering reasons
  (for `Reference.version`: integrity witness, cache key or offline
  validation). The last outcome is documented as such, not presented as
  minimal.
- Constraints experiment kill criterion: it succeeds only if the total
  mechanism count drops. Cost side: new VM operations, new runtime-only
  semantic cases, special Unknown machinery, special budget machinery,
  constraint-only environment interfaces. Removed side: the constraint
  evaluator, constraint node semantics, constraint-specific recursion and
  control logic, the duplicate External execution path. One generic-looking
  opcode that hides special machinery counts as its machinery. Success means
  most constraint behaviour through existing computation, with at most one
  generic boundary for external authority and one generic execution budget;
  strong-Kleene behaviour emerges from functions and data.
- Layout spike, first scenario: S0 has object A `{x, y}`, reference R to
  `A.y`, and a running old-version frame holding R; activation continues A to
  A' with layout `{x, z, y}` and a converter for runtime content; in S1 new
  code reads `A'.y`, the old frame continues under S0, and R has an
  explicitly defined fate. Then vary one dimension at a time: moved field,
  deleted field, split object, ownership change, old-version retirement.
  Alloy models the activation and lifetime protocol and its interleavings;
  Python handles representation, layout and differential behaviour.
  The central question is the status of `A.y`, with three outcomes to
  discriminate, not presuppose: `A.y` has its own semantic identity (a
  reference names the field); `A.y` has none (a reference is A plus a
  selector); or the reference is to a logical property, with physical layout
  and semantic access path fully separate. `(EntityID(A), field y)` is a
  selector anchored at a stable identity, categorically different from a
  path used as identity.
- Method: a simplification names the concrete mechanism it intends to delete;
  a research spike names the concrete requirement that could falsify the
  current architecture. Predictions are recorded before runs; one revision
  per experiment.
- `ContentID = H(content)` with version `(EntityID, ContentID)` is recorded as
  a possible identity-model cleanup, not a task: large blast radius, no
  demonstrated problem.

CI: `.github/workflows/core-projection.yml` runs the
research tests and the experiment on every push to `research/semantic-core`.

## Projection observables

- `semantic_equal` on projected values;
- call and link targets;
- `StateID` equality in both directions (charter §3.11 predicts which
  direction fails and where);
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

   In `main`, `StateID` hashes every `(EntityID, VersionID)` pair plus the
   ownership relation, and `VersionID` derives from `EntityID` and semantic
   content. Equal `StateID`s therefore already imply the same entity naming
   and ownership structure, so `main` has nothing to choose.

   - symmetric: `M` has two structurally equal, otherwise symmetric
     occurrences;
   - asymmetric control: `M` has no automorphism.

   Question: does the candidate determine a unique composition without an
   externally chosen isomorphism `M1 ↔ M2`? Composition is well defined iff
   its result is the same for every isomorphism `M1 → M2` (charter §3.11).
   A failure only in the symmetric case is an observed H1 failure caused by
   symmetry.
4. **Continuity composition** with split, merge, disappearance and Unknown,
   compared case by case with `transforms.compose`.

## Mechanism inventory (freeze at step 3)

Mechanisms of `main` the candidate claims to replace or represent:

```text
canonical semantic value representation (Value + canonical content)
relation record representation (kind, roles, payload)
EntityID-valued relation endpoints
ownership forest
VersionID derivation
StateID derivation
pinned Reference (StateID, EntityID, VersionID)
continuity representation (TransformationMapping / CompositionResult)
```

Relation payload is not counted separately: it is a position holding
canonical semantic content, not an independent identity or continuity
mechanism, and counting it twice would bias the tally.

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
.github/scripts/AlloyRunner.java      instrumented runner
.github/workflows/alloy-verification.yml   all Alloy commands, lingeling.parallel
.github/workflows/semantic-model.yml  Python model tests

docs/semantic_core_experiment.md                    charter
docs/research/semantic-core/alloy_verification.md   verification policy
docs/research/semantic-core/core_verification.md    core evidence
docs/research/semantic-core/transformation_verification.md
docs/research/semantic-core/continuity_composition.md
docs/research/semantic-core/alloy_api_reference.md
docs/research/semantic-core/handoff.md              this file (main keeps its own handoff.md at the root)
docs/research/semantic-core/project_diary.md        append-only log
docs/research/semantic-core/projection_plan.md      step 5 plan
docs/research/semantic-core/revision_plan.md        step 7 plan
docs/research/semantic-core/projection_results.md   steps 5 to 7 results
research/core_projection/                           projection, observables, tests
docs/research/semantic-core/peer_reviews/
```

`transformation_verification.md`, `continuity_composition.md` and the
open-target list in `alloy_verification.md` predate the composition and
equality work and still describe it as future work.

## Verification language

Use: bounded check passed, bounded counterexample found, bounded witness
exists, no result, not established. Never present bounded UNSAT as a
theorem. Pair important implication checks with non-vacuity witnesses.
