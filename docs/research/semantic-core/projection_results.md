# Projection Results – Steps 5 to 7

Status: first run, re-run after review and revision 1 run, not interpreted for H1  
Branch: `research/semantic-core`  
Run at: `0950761` (first run), `cb74cea` (re-run after review), `6739252` (revision 1 run); `PYTHONPATH=research python3 -m core_projection.run`, about 35 s each for the first two  
Plan: `docs/research/semantic-core/projection_plan.md`; revision 1: `docs/research/semantic-core/revision_plan.md`

## Revision 1 run

Status: run once, predictions checked, not interpreted for H1 (step 8)  
Run at: `6739252` (code identical to the run; the commits after it only add this report, the diary entry and the handoff); `PYTHONPATH=research python3 -m core_projection.run`, about a minute  
Plan: `docs/research/semantic-core/revision_plan.md`; charter §3.12

The single candidate revision (named roots) was run once on the same corpus,
continuity cases and adversarial cases as before, in three modes: `STRUCT` and
`REF` (the frozen candidate, `core.py` untouched) and `NAMED` (the revision,
`named.py`). The predictions of plan §3 were recorded before the run and are
checked verbatim below; nothing in the projection was changed after seeing a
result.

Overall: agree 5947086, predicted mismatch 5488, unexpected mismatch 0, gap 0.

### Predictions

| observable | prediction | result | detail |
|---|---|---|---|
| O0 | round trip exact modulo arity; arity collapse unchanged | hit | modulo arity: 3760 of 3760 agree; exact: 0 unexpected, 316 arity collapses (STRUCT: 316) |
| O1 | agrees with main on every pair, as REF did | hit | 1976135 of 1976135 entity pairs agree |
| O2 | agrees | hit | 132 of 132 link targets agree |
| O3 built twice / literal changed | agrees | hit | 94 of 94 state pairs agree |
| O3 renamed (both orders) | agrees with main: not isomorphic, names are fixed | hit | 134 of 134 renamed state pairs (not isomorphic, as main) agree |
| O4 shared and independent middle states | agrees with main on every real chain | hit | 138 of 138 composed sources (real chains and adversarial 4) agree |
| adversarial 3, differently named | Unknown, as main | hit | 4 of 4 sources agree; 4 are Unknown |
| adversarial 3, symmetric with same naming | agrees with main; no dependence on an isomorphism | hit | 8 of 8 sources agree; 0 vary (no isomorphism is searched) |
| O5, all three scenarios | agrees with main (1, 1, 2) | hit | 3 of 3 scenarios agree; VersionID changes in main: [1, 1, 2] |
| contained cycles in projected states | none | hit | 67 of 67 projected states agree; 0 with a contained cycle |

Hits 10 of 10. No row is a miss and no `NAMED` row is `unexpected` or a `gap`.
The two cases the plan does not list were judged by the rows they fall under
(as decided before the run): adversarial 2 (`factorial`) by "contained cycles:
none" and the O1 and O3 rows for `factorial`, whose self-reference is a `Named`
target to its own name and agrees; adversarial 4 by "O4 agrees", included in the
O4 row above.

### Counts per mode

| mode | agree | predicted mismatch | unexpected mismatch | gap | rows |
|---|---|---|---|---|---|
| `STRUCT` | 1,979,331 | 4,838 | 0 | 0 | 1,984,169 |
| `REF` | 1,983,835 | 334 | 0 | 0 | 1,984,169 |
| `NAMED` | 1,983,920 | 316 | 0 | 0 | 1,984,236 |

`NAMED` has 67 more rows than the others: the C0 observable, one row per
projected state. Its 316 predicted rows are all the arity collapse in O0 (the
same 316 as `STRUCT` and `REF`); every other `NAMED` row agrees with `main`.
The per-observable counts, with the other two modes beside them:

| observable | agree | predicted mismatch | unexpected mismatch | gap | total |
|---|---|---|---|---|---|
| C0/NAMED | 67 | 0 | 0 | 0 | 67 |
| O0/NAMED/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/NAMED/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O0/REF/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/REF/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O0/STRUCT/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/STRUCT/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O1/NAMED | 1976135 | 0 | 0 | 0 | 1976135 |
| O1/REF | 1976135 | 0 | 0 | 0 | 1976135 |
| O1/STRUCT | 1971756 | 4379 | 0 | 0 | 1976135 |
| O2/NAMED | 132 | 0 | 0 | 0 | 132 |
| O2/REF | 132 | 0 | 0 | 0 | 132 |
| O2/STRUCT | 132 | 0 | 0 | 0 | 132 |
| O3/NAMED/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/NAMED/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/NAMED/renamed (order-preserving) | 67 | 0 | 0 | 0 | 67 |
| O3/NAMED/renamed (order-reversing) | 67 | 0 | 0 | 0 | 67 |
| O3/REF/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/REF/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/REF/renamed (order-preserving) | 61 | 6 | 0 | 0 | 67 |
| O3/REF/renamed (order-reversing) | 61 | 6 | 0 | 0 | 67 |
| O3/STRUCT/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/STRUCT/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/STRUCT/renamed (order-preserving) | 0 | 67 | 0 | 0 | 67 |
| O3/STRUCT/renamed (order-reversing) | 0 | 67 | 0 | 0 | 67 |
| O4a/NAMED | 73 | 0 | 0 | 0 | 73 |
| O4a/REF | 73 | 0 | 0 | 0 | 73 |
| O4a/STRUCT | 73 | 0 | 0 | 0 | 73 |
| O4b/NAMED | 77 | 0 | 0 | 0 | 77 |
| O4b/REF | 71 | 6 | 0 | 0 | 77 |
| O4b/STRUCT | 71 | 6 | 0 | 0 | 77 |
| O5/NAMED | 3 | 0 | 0 | 0 | 3 |
| O5/REF | 3 | 0 | 0 | 0 | 3 |
| O5/STRUCT | 0 | 3 | 0 | 0 | 3 |
| adv2/NAMED | 1 | 0 | 0 | 0 | 1 |
| adv2/REF | 1 | 0 | 0 | 0 | 1 |
| adv2/STRUCT | 1 | 0 | 0 | 0 | 1 |

### Unexpected rows

None.

### Reproduction of the frozen candidate

`STRUCT` and `REF` reproduce the `cb74cea` record exactly: every
per-observable, per-classification count in the table of the re-run (full
output at the end of this file) and the wording of the three O5 rows of each
mode. The check is part of the runner (`baseline.py`): it reads the recorded
table from this file and compares it with the run, and the runner exits with
status 2 if the frozen modes differ.

### What the hits are evidence of

Facts about the rows, not a verdict on H1.

- **Equality, links and churn (O1, O2, O5) are informative.** `NAMED` agrees
  with `main` on all 1,976,135 entity pairs, all 132 link targets and the three
  version-churn scenarios (1 of 42, 1 of 402, 2 of 549 value classes change),
  as the `REF` control does, with the names held in `Named` targets and
  bindings and none in atoms. `STRUCT` equates 4,379 pairs that `main` keeps apart and changes 22, 202 and
  129 value classes in the same scenarios.
- **Identity and composition (O3 renamed, O4) hold largely by the definition.**
  Names are fixed in state identity (§3.12 item 5) and continuity composes over
  names (item 6), so a renamed state is not isomorphic and two steps join where
  the first step's destination names are the second step's source names. These
  are the rules `main` has; their agreement restates the revision more than it
  tests it. `NAMED` composition needs no isomorphism search (O4b is 77 of 77
  agree where `STRUCT` and `REF` each have 6 predicted rows), and
  adversarial 3 gives the answer `main` gives (`Unknown` when the middle states
  are named differently).
- **The cost is the one the plan named.** The frozen candidate's O3 renamed rows
  are 134 of 134 predicted mismatches in `STRUCT` (names not in state identity);
  in `NAMED` they are 134 of 134 agreements. That is charter §3.8 given up:
  names are part of values that refer to them and of state identity.
- **No new loss.** The arity collapse is unchanged (the same 316 O0 rows as
  in the frozen modes); nothing else fails to round-trip.

### Choices made in this execution

The plan is silent on these; each was a decision of the execution, listed so
the run can be read against them.

1. **One content table.** `NAMED` reuses `project.py`'s builder (the `REF`
   builder, which already puts a fresh nullary occurrence where content refers
   to an entity) and then replaces each such occurrence by a `Named` target
   (`project_named.py`). Content, handle allocation and gaps follow the same
   code in all three modes.
2. **Bare reference.** An entity whose whole content is a reference projects as
   a relation with atom `symbol:ref` and one role `target` holding a `Named`
   target. The plan names neither the atom nor the role. It decodes back; `STRUCT`
   still cannot project it.
3. **Reuse of `core.py` by encoding.** `named.py` decides equality and identity
   by encoding a state as a `CState`: one nullary leaf per distinct referenced
   name (atom `symbol:name:<n>`, no edge to the bound root, so bisimulation
   cannot look through a name), and one relation per binding (atom
   `symbol:binding:<n>`, role `root`). The encoding is injective; content atoms
   with a reserved prefix are rejected, and the projection treats them (and
   `ref` outside a bare reference) as a gap.
4. **Containment check on use.** `NState` validates handles, names and bindings
   when built; acyclicity of `Contained` targets is checked by `equal` and
   `isomorphisms` (`ContainmentCycle`), so C0 can count cyclic states instead of
   crashing on them. C0 is counted over the 67 states that `run.state_rows`
   projects (corpus programs and continuity-corpus sources and destinations),
   not over the churn and adversarial states.
5. **NAMED composition does not search isomorphisms**, in either variant;
   isomorphism search is used for O3 only.
6. **Classification rules are mode-aware.** The predictions cited for the frozen
   candidate do not carry over: in `NAMED`, a renamed state that is isomorphic,
   a composition that varies or that joins where `main` cannot, and a version
   churn above `main`'s are `unexpected`; the adversarial 1 label never applies
   to O1. The arity label applies to O0 (and to any O1 row explained only by
   arity).
7. **Existing tests edited.** Two tests asserted the list of modes of a function's
   rows (`test_one_row_per_mode`, `test_rows_for_every_scenario_and_mode`); they
   now expect `NAMED` too. They check what they checked before.
8. **Existing modules touched.** `project.py` gained `Mode.NAMED` and two
   dispatches (`project`, `decode`); its `STRUCT` and `REF` paths are unchanged.
   The observables, `identity.py`, `churn.py`, `composition.py` and
   `adversarial.py` gained `NAMED` branches; `run.py` gained C0, the
   predictions and the reproduction check. `NamedProjection` has no `cstate`, so
   code that reads the candidate state must choose how a `NAMED` state is read.

## Re-run after review

The review of the first run asked for four changes. The projection and
instruments were changed as below and the experiment was run once more at
`cb74cea` (full output at the end of this file). The candidate core was still
not touched. The first run's text and numbers follow unchanged; where this
section corrects them it says so.

Changes:

1. **Ownership projection.** One `owns` relation per ownership edge (atom
   `symbol:owns`, role `owner` to the owner's root, role `owned` to the child's
   root) replaces one relation per owner listing its children. This is a
   projection correction justified by `main`'s semantics, not a result-driven
   tweak: `normalize_ownership` stores children as `sorted(set(...))`, so their
   order is not semantic and a sequence let `EntityID` spelling into the
   projected structure. It supersedes deviation 1 below.
2. **O5 `STRUCT` is a predicted mismatch**, cited as direction review §3.3
   (item 3 of its section 3): version identity derived from candidate equality
   propagates to ancestors and referrers.
3. **A cross-function O5 scenario.** In the `compiler` corpus program, one
   literal leaf of the called function `upper` is edited with `lang.define`;
   the rows compare `main`'s `VersionID` changes with candidate value-class
   changes.
4. **Instrument fixes found on the way.** When an O3 non-isomorphism remains
   under a renaming, the row now names its cause (`spelling_cause`: a map keyed
   by `entity_id`, whose entries `main` lists in key-spelling order).
   `rename_entities` re-sorts map entries as `canonicalize` would; before, it
   kept the old order, which is not a state `main` would build.

Counts, first run against re-run:

| classification | first run | re-run |
|---|---|---|
| agree | 3,963,165 | 3,963,166 |
| predicted mismatch | 5,109 | 5,172 |
| unexpected mismatch | 62 | 0 |
| gap | 0 | 0 |

What moved: the 60 unexpected O3 `STRUCT` order-reversing rows are now
isomorphic and predicted (§3.11), like the order-preserving ones: all 67 of 67
states. No corpus state contains a map keyed by `entity_id`, so no
non-isomorphism remains to attribute; the attribution path is exercised on a
synthetic state in the tests. The 2 unexpected O5 rows are now predicted, and
the new scenario adds 2 rows (`REF` agrees, `STRUCT` predicted). Nothing
else changed.

O5, all three scenarios:

| scenario | `main`: VersionID changes | `STRUCT`: value classes changed | `REF` |
|---|---|---|---|
| leaf edit, 41 nodes | 1 of 42 | 22 of 42 (the leaf, 20 additions and the function) | 1 of 42, agrees |
| leaf edit, 401 nodes | 1 of 402 | 202 of 402 | 1 of 402, agrees |
| `compiler`, leaf in `upper` | 2 of 549 (2 nodes also replaced) | 129 of 549, all 5 functions | 2 of 549, agrees |

In the cross-function scenario `define` replaces the edited literal and its
parent node, so `main` changes the parent's and the function definition's
`VersionID` and creates two nodes. Under `STRUCT` the change reaches every
function, since `lower` and `evals` call each other and the other functions
call them.

Planted-bug checks for the changes (CLAUDE.md): 6 mutants of the ownership,
attribution and renaming code, 6 caught. 6 mutants of the churn code: 5 caught
at first; the survivor (the `main` count forced to zero) exposed a missing
test, which now catches it.

---

The rest of this file is the first run, at `0950761`.

The candidate core was frozen throughout. Mismatches below are results; none
was removed by adjusting the projection. Evaluating H1 (step 8) and the one
candidate revision (step 7) are separate tasks.

## Deviations from plan

The plan was not edited. Where it was silent, wrong or could not be followed
literally, the code does the following.

1. **Ownership order follows spelling.** `State` sorts an owner's children by
   `EntityID`, and the plan says the `owns` relation lists children "in `main`
   order". `owned` therefore depends on `EntityID` spelling, contradicting
   "nothing else may depend on spelling". I followed the plan literally and
   added an order-reversing renaming to O3 to expose it. The alternative, one
   `owns` relation per edge, would be spelling-free but is a change to the
   plan's rule. This is a projection choice, not a candidate change.
2. **Raw tuples and lists inside node payloads** (cell and constraint
   records) are not covered by the plan's table. They project to
   `symbol:raw_tuple` / `symbol:raw_list` with role `items`.
3. **A bare-reference entity** (an entity whose whole content is an
   `entity_id`) has no relation to put the reference in under `STRUCT`; it
   raises `ProjectionGap`. A relation role named `payload` also raises
   `ProjectionGap` (it would collide with the payload role). Neither occurs in
   the corpus.
4. **bytes** node payloads are stored as hex strings in `main`; they project
   to `bytes` atoms from the decoded bytes.
5. **"links relation" is wrong.** The `link:<name>` roles live on the
   `definition` relation of each function; O2 reads them there.
6. **O0 is reported twice**, exact and modulo arity. Single endpoint and
   one-element tuple project alike by the plan's rule, so exact decoding cannot
   recover the distinction. Exact failures explained only by that are labelled
   "predicted mismatch (arity collapse)". The same label applies to any O1
   mismatch caused only by arity, in either mode.
7. **O1 rule.** A `STRUCT` pair that `main` keeps unequal and the candidate
   equates is predicted (adversarial case 1) iff the two contents are equal
   once `entity_id` nodes are masked. Any other disagreement, and every
   disagreement in `REF` beyond arity, is unexpected.
8. **O4 uses real two-step chains**, not the continuity corpus's single
   operations (`CASES` has no chains). Eight chains are built with `main`'s
   own `define` edits and the corpus's operation constructors, so the first
   step's destination is the second step's source in `main`. Each is run
   with (a) one shared projection of the middle state and (b) independent
   projections joined through every isomorphism.
9. **`main`'s third compose outcome.** A source mentioned by neither mapping
   is neither mapped nor unknown. It is reported as "absent" and counted
   separately from "Unknown"; both count as agreeing with the candidate's
   Unknown.
10. **O3 has an extra pair**, the order-reversing renaming (item 1), and
    `rename_entities` in `project.py` to build renamed states.
11. **Adversarial case 3 has a fourth variant**, a symmetric middle state
    with the same naming on both sides, to separate "main cannot join" from
    "the candidate cannot choose".
12. **O5 is rebuilt from the public lang API**, not by calling
    `ledger._leaf_edit_measurement`. Node counts are asserted equal to the
    ledger's (41 and 401); the relowering count is read from
    `ledger.measurements()`.
13. **Rows are aggregated** (`count`, `examples`); equal rows are folded.
    A million entity pairs would otherwise not fit in a report.
14. **Extra modules.** `observables.py` is split into `observables.py` (O0–O2),
    `identity.py` (O3), `composition.py` (O4), `churn.py` (O5) and `rows.py`,
    to keep files near the 500-line threshold. `core.py` (552 lines) was kept
    whole.
15. **Tests live in `research/core_projection/tests/`**, run with
    `python3 -m unittest discover -s research -t research`. The root
    `python3 -m unittest discover` does not collect them (no
    `research/__init__.py`; checked: 1029 root tests, none from the package).

## Summary

67 `main` states were projected in both modes: the 26 corpus programs, the 21
continuity-corpus sources and 20 operation destinations (two cases expect a
rejection and have none; one competing pair has two). No state raised `ProjectionGap`
and no content held a `VersionID` or `StateID`, so there are no gaps.

| classification | count |
|---|---|
| agree | 3,963,165 |
| predicted mismatch | 5,109 |
| unexpected mismatch | 62 |
| gap | 0 |

Predicted mismatches, all with the prediction that explains them:

- **O0 exact, 316 per mode:** arity collapse. Modulo arity, every entity
  round-trips (3,760 of 3,760, both modes).
- **O1 `STRUCT`, 4,379 of about 1.98 million pairs:** adversarial case 1,
  distinct referents with equal content. All of them. `REF` has no O1
  mismatch at all.
- **O3 renamed states:** §3.11. `STRUCT` equates 67 of 67 order-preserving
  renamings and 7 of 67 order-reversing ones (in those 7 no owner has more than one
  child, so there is no order to flip). `REF` equates 6 of 67 each, the states with no references, where the
  candidate holds no names at all.
- **O4, 12 rows, all in adversarial case 3:** `main` cannot join middle
  states named differently, and the candidate's result depends on the
  isomorphism in the symmetric case. See below.

**Unexpected mismatches (62):**

1. **O3 `STRUCT`, order-reversing renaming, 60 of 67 states.** The renamed
   state is not isomorphic to the original because ownership order follows
   `EntityID` spelling (deviation 1). The order-preserving renaming does not
   expose it. This is a defect in the plan's projection rule, not in the
   candidate; the `REF` control agrees on all 67 since it keeps names.
2. **O5 `STRUCT`, both scenarios, 2 rows.** After a leaf edit, `main` changes
   the `VersionID` of 1 entity and relowers 1 node; in `STRUCT` the value
   class changes for 22 of 42 entities (20 additions, the edited leaf and the
   function definition) and 202 of 402. The candidate value of an entity
   includes everything it reaches, so a change reaches every referrer through
   role targets. `REF` gives 1 and 1. No prediction was cited for this and the
   row is not tuned away.

Observations:

- **Adversarial 1 holds** as predicted (the 4,379 above), including in real
  programs (for example the nodes `is_even/0.1` and `is_odd/0.1` of `deep_loop`,
  which `main` keeps apart and `STRUCT` equates).
- **Adversarial 2, `factorial`:** `STRUCT` produces a one-node cycle (the
  `link:factorial` role of the function's root targets itself); `REF` an
  `EntityID` atom. Consequence for equality: all 66 pairs agree in both modes,
  so bisimulation decides pairs on cyclic graphs without special handling.
  Identity rows for `factorial` are the same as for any other program.
- **Adversarial 3:** with the symmetric middle state (two equal unconnected
  values) the independent composition depends on the isomorphism chosen
  (2 isomorphisms, results differ); the asymmetric control composes uniquely
  (1 isomorphism). With different naming, `main` has no result (Unknown) where
  the candidate has one. The symmetric dependence never appeared in a real
  chain: the eight chains agree with `main` in every row, in both variants and
  both modes. One chain (split a cell, then merge the halves) has a middle
  state with 2 isomorphisms, but both give the same result.
- **O2:** all 132 link targets agree in both modes.
- **O4 variant a:** 73 rows per mode, all agree (1 of them "absent" against
  Unknown). Variant b: 71 agree, 6 predicted.

Step-7 revision candidates (reported, not acted on): none are changes to the
candidate. The two groups of unexpected results are a projection rule
(ownership order, deviation 1) and a consequence of `STRUCT` (value
propagation to referrers), which belongs in the step-8 evaluation of H1.

Planted-bug checks (CLAUDE.md): every property test had a plausible bug planted
once and caught. `core.py` and its tests: earlier survivors led to the
connected-symmetry tests and the mixed-components regression test; one planted
bug (colours ignoring sequence lengths) is equivalent. `project.py`: 16
mutants, 16 caught. Observables, composition, identity, rows and churn: 14
mutants, 14 caught. `run.py`: 2 of 2 caught. Alloy and mutation campaigns were
not run.

## Full report

The run's output, with headings demoted one level.


### Counts per observable and classification

| observable | agree | predicted mismatch | unexpected mismatch | gap | total |
|---|---|---|---|---|---|
| O0/REF/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/REF/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O0/STRUCT/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/STRUCT/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O1/REF | 1976135 | 0 | 0 | 0 | 1976135 |
| O1/STRUCT | 1971756 | 4379 | 0 | 0 | 1976135 |
| O2/REF | 132 | 0 | 0 | 0 | 132 |
| O2/STRUCT | 132 | 0 | 0 | 0 | 132 |
| O3/REF/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/REF/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/REF/renamed (order-preserving) | 61 | 6 | 0 | 0 | 67 |
| O3/REF/renamed (order-reversing) | 61 | 6 | 0 | 0 | 67 |
| O3/STRUCT/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/STRUCT/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/STRUCT/renamed (order-preserving) | 0 | 67 | 0 | 0 | 67 |
| O3/STRUCT/renamed (order-reversing) | 0 | 7 | 60 | 0 | 67 |
| O4a/REF | 73 | 0 | 0 | 0 | 73 |
| O4a/STRUCT | 73 | 0 | 0 | 0 | 73 |
| O4b/REF | 71 | 6 | 0 | 0 | 77 |
| O4b/STRUCT | 71 | 6 | 0 | 0 | 77 |
| O5/REF | 2 | 0 | 0 | 0 | 2 |
| O5/STRUCT | 0 | 0 | 2 | 0 | 2 |
| adv2/REF | 1 | 0 | 0 | 0 | 1 |
| adv2/STRUCT | 1 | 0 | 0 | 0 | 1 |

Overall: agree 3963165, predicted mismatch 5109, unexpected mismatch 62, gap 0

### Every row that is not agree

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| corpus: factorial | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | factorial/0.7 |
| corpus: factorial | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | factorial/0.7 |
| corpus: factorial | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: factorial | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: fibonacci | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | fibonacci/0.10; fibonacci/0.6 |
| corpus: fibonacci | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | fibonacci/0.10; fibonacci/0.6 |
| corpus: fibonacci | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fibonacci | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: sum_to_n | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | sum_to_n/0.7 |
| corpus: sum_to_n | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | sum_to_n/0.7 |
| corpus: sum_to_n | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sum_to_n | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: gcd | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: gcd | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: collatz_step_count | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | collatz_half/0.7; collatz_is_even/0.10; collatz_step_count_from/0.6 |
| corpus: collatz_step_count | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | collatz_half/0.7; collatz_is_even/0.10; collatz_step_count_from/0.6 |
| corpus: collatz_step_count | O1/STRUCT | unequal | equal | predicted mismatch | 4 | predicted: adversarial 1 (distinct referents with equal content) | collatz_half/0.1 ~ collatz_is_even/0.1; collatz_half/0.8 ~ collatz_is_even/0.11; collatz_is_even/0.6 ~ collatz_step_count_from/0.1 |
| corpus: collatz_step_count | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: collatz_step_count | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: deep_loop | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | is_even/0.5; is_odd/0.5 |
| corpus: deep_loop | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | is_even/0.5; is_odd/0.5 |
| corpus: deep_loop | O1/STRUCT | unequal | equal | predicted mismatch | 13 | predicted: adversarial 1 (distinct referents with equal content) | is_even/0.1 ~ is_odd/0.1; is_even/0.1 ~ sum_apply/0.1; is_even/0.1 ~ sum_loop/0.1 |
| corpus: deep_loop | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_loop | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: deep_recursion | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | deep_sum/0.7 |
| corpus: deep_recursion | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | deep_sum/0.7 |
| corpus: deep_recursion | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_recursion | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: abs_value | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: abs_value | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: max_of_two | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: max_of_two | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: clamp | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: clamp | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: counter | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: counter | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: account | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: account | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: power_compiler | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compile/0.0; compile/0.3; emit/0.5 |
| corpus: power_compiler | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compile/0.0; compile/0.3; emit/0.5 |
| corpus: power_compiler | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: power_compiler | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: checked_compile | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 5 | predicted: arity collapse (single endpoint and one-element tuple project alike) | checked_compile/0.3; emit/0.5; emit/0.7 |
| corpus: checked_compile | O0/REF/exact | content | decoded differs | predicted mismatch | 5 | predicted: arity collapse (single endpoint and one-element tuple project alike) | checked_compile/0.3; emit/0.5; emit/0.7 |
| corpus: checked_compile | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: checked_compile | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: replace_self | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | replace_self/0.1 |
| corpus: replace_self | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | replace_self/0.1 |
| corpus: replace_self | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: replace_self | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: insertion_sort | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert/0.14; insert/0.18; insert/0.5 |
| corpus: insertion_sort | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert/0.14; insert/0.18; insert/0.5 |
| corpus: insertion_sort | O1/STRUCT | unequal | equal | predicted mismatch | 4 | predicted: adversarial 1 (distinct referents with equal content) | insert/0.10 ~ insert/0.19; insert/0.14 ~ insert/0.5; insert/0.2 ~ insert/0.27 |
| corpus: insertion_sort | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: insertion_sort | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: let_bindings | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: let_bindings | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: map | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | map/0.18 ~ map/0.2 |
| corpus: map | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: fold | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | fold/0.17 ~ fold/0.2 |
| corpus: fold | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fold | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: sort_swap | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert_by/0.15; insert_by/0.19; insert_by/0.5 |
| corpus: sort_swap | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert_by/0.15; insert_by/0.19; insert_by/0.5 |
| corpus: sort_swap | O1/STRUCT | unequal | equal | predicted mismatch | 4 | predicted: adversarial 1 (distinct referents with equal content) | insert_by/0.11 ~ insert_by/0.20; insert_by/0.15 ~ insert_by/0.5; insert_by/0.2 ~ insert_by/0.29 |
| corpus: sort_swap | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sort_swap | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: map_long_tuple | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map_long_tuple | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map_long_tuple | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | map/0.18 ~ map/0.2 |
| corpus: map_long_tuple | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map_long_tuple | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: make_adder | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | apply_adder/0.0; apply_adder/0.1 |
| corpus: make_adder | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | apply_adder/0.0; apply_adder/0.1 |
| corpus: make_adder | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: make_adder | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: compose | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 7 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compose/0.1; compose/0.3; run_compose/0.1 |
| corpus: compose | O0/REF/exact | content | decoded differs | predicted mismatch | 7 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compose/0.1; compose/0.3; run_compose/0.1 |
| corpus: compose | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | run_compose/0.7 ~ run_two_closures/0.10 |
| corpus: compose | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compose | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: compiler | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 75 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; lower/0.103 |
| corpus: compiler | O0/REF/exact | content | decoded differs | predicted mismatch | 75 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; lower/0.103 |
| corpus: compiler | O1/STRUCT | unequal | equal | predicted mismatch | 685 | predicted: adversarial 1 (distinct referents with equal content) | evals/0.13 ~ seq_code/0.16; evals/0.15 ~ seq_code/0.10; evals/0.15 ~ seq_code/0.18 |
| corpus: compiler | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compiler | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: instrument | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 78 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; instrument/0.1 |
| corpus: instrument | O0/REF/exact | content | decoded differs | predicted mismatch | 78 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; instrument/0.1 |
| corpus: instrument | O1/STRUCT | unequal | equal | predicted mismatch | 686 | predicted: adversarial 1 (distinct referents with equal content) | evals/0.13 ~ seq_code/0.16; evals/0.15 ~ seq_code/0.10; evals/0.15 ~ seq_code/0.18 |
| corpus: instrument | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: instrument | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| corpus: bootstrap | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 106 | predicted: arity collapse (single endpoint and one-element tuple project alike) | arg_exprs/0.6; evals/0.12; evals/0.15 |
| corpus: bootstrap | O0/REF/exact | content | decoded differs | predicted mismatch | 106 | predicted: arity collapse (single endpoint and one-element tuple project alike) | arg_exprs/0.6; evals/0.12; evals/0.15 |
| corpus: bootstrap | O1/STRUCT | unequal | equal | predicted mismatch | 2977 | predicted: adversarial 1 (distinct referents with equal content) | arg_exprs/0.1 ~ vm_bind/0.1; arg_exprs/0.14 ~ evals/0.7; arg_exprs/0.14 ~ seq_code/0.26 |
| corpus: bootstrap | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: bootstrap | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: rename (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: rename (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: delete_function (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: delete_function (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: delete_called (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_called (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_called (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_called (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: merge_cells (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (source) | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | nested/0.2 ~ plain/0.0 |
| continuity: fold (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: fold (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: activate_define (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: activate_define (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: leaf_replace (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: leaf_replace (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: insert (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: insert (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: remove (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: remove (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: wrap (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2 |
| continuity: wrap (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2 |
| continuity: wrap (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: wrap (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2; f/1.1 |
| continuity: wrap (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2; f/1.1 |
| continuity: wrap (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: unwrap (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1; f/0.3 |
| continuity: unwrap (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1; f/0.3 |
| continuity: unwrap (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: unwrap (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.3 |
| continuity: unwrap (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.3 |
| continuity: unwrap (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: swap (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: swap (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: redefine_same (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: redefine_same (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: shared_subtree (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: shared_subtree (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: ambiguous_duplicate (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: ambiguous_duplicate (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: rebase_disjoint (destination 1) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 1) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: rebase_disjoint (destination 2) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 2) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: conflicting_edits (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: conflicting_edits (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: extract_function (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: extract_function (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/1.1 |
| continuity: extract_function (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/1.1 |
| continuity: extract_function (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: inline_function (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1 |
| continuity: inline_function (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1 |
| continuity: inline_function (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (source) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| continuity: inline_function (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | not isomorphic | unexpected mismatch | 1 | renaming changed the projected structure; ownership order follows EntityID spelling (plan gap) |  |
| adversarial 1: two referents with equal content | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | r1 ~ r2 |
| adversarial 3: symmetric, differently named | O4b/STRUCT | Unknown | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| adversarial 3: symmetric, differently named | O4b/REF | Unknown | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| adversarial 3: asymmetric control, differently named | O4b/STRUCT | Unknown | Known(1) | predicted mismatch | 2 | predicted: adversarial 3 (main cannot join independently named middle states; the candidate joins them by isomorphism); isomorphisms joining the middle states: 1 | p; q |
| adversarial 3: asymmetric control, differently named | O4b/REF | Unknown | Known(1) | predicted mismatch | 2 | predicted: adversarial 3 (main cannot join independently named middle states; the candidate joins them by isomorphism); isomorphisms joining the middle states: 1 | p; q |
| adversarial 3: symmetric, same naming | O4b/STRUCT | Known(1) | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| adversarial 3: symmetric, same naming | O4b/REF | Known(1) | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| leaf_edit_41 | O5/STRUCT | 1 of 42 entities change VersionID; 1 relowered | 22 of 42 entities change value class | unexpected mismatch | 1 | no cited prediction; the candidate value of an entity includes everything it reaches, so a change propagates to its referrers |  |
| leaf_edit_401 | O5/STRUCT | 1 of 402 entities change VersionID; 1 relowered | 202 of 402 entities change value class | unexpected mismatch | 1 | no cited prediction; the candidate value of an entity includes everything it reaches, so a change propagates to its referrers |  |

### Adversarial case 2: recursion (factorial)

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| adversarial 2: factorial | adv2/STRUCT | function links to itself by EntityID | self-loop: the link role of handle 0 targets handle 0 | agree | 1 | matches the predicted representation |  |
| adversarial 2: factorial | adv2/REF | function links to itself by EntityID | nullary atom symbol:'factorial' | agree | 1 | matches the predicted representation |  |

Consequences for equality (O1) and identity (O3), counted over the factorial program:

| observable | classification | n |
|---|---|---|
| O1/REF | agree | 66 |
| O1/STRUCT | agree | 66 |
| O3/REF/built twice | agree | 1 |
| O3/REF/one literal changed | agree | 1 |
| O3/REF/renamed (order-preserving) | agree | 1 |
| O3/REF/renamed (order-reversing) | agree | 1 |
| O3/STRUCT/built twice | agree | 1 |
| O3/STRUCT/one literal changed | agree | 1 |
| O3/STRUCT/renamed (order-preserving) | predicted mismatch | 1 |
| O3/STRUCT/renamed (order-reversing) | unexpected mismatch | 1 |

### Composition (O4): outcomes by kind

| variant | main | candidate | classification | n |
|---|---|---|---|---|
| O4a | Known(0) | Known(0) | agree | 32 |
| O4a | Known(1) | Known(1) | agree | 106 |
| O4a | Known(2) | Known(2) | agree | 2 |
| O4a | Unknown | Unknown | agree | 4 |
| O4a | absent (not mapped) | Unknown | agree | 2 |
| O4b | Known(0) | Known(0) | agree | 32 |
| O4b | Known(1) | Known(1) | agree | 102 |
| O4b | Known(1) | varies across isomorphisms | predicted mismatch | 4 |
| O4b | Known(2) | Known(2) | agree | 2 |
| O4b | Unknown | Known(1) | predicted mismatch | 4 |
| O4b | Unknown | Unknown | agree | 4 |
| O4b | Unknown | varies across isomorphisms | predicted mismatch | 4 |
| O4b | absent (not mapped) | Unknown | agree | 2 |

### Version churn (O5)

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| leaf_edit_41 | O5/STRUCT | 1 of 42 entities change VersionID; 1 relowered | 22 of 42 entities change value class | unexpected mismatch | 1 | no cited prediction; the candidate value of an entity includes everything it reaches, so a change propagates to its referrers |  |
| leaf_edit_41 | O5/REF | 1 of 42 entities change VersionID; 1 relowered | 1 of 42 entities change value class | agree | 1 |  |  |
| leaf_edit_401 | O5/STRUCT | 1 of 402 entities change VersionID; 1 relowered | 202 of 402 entities change value class | unexpected mismatch | 1 | no cited prediction; the candidate value of an entity includes everything it reaches, so a change propagates to its referrers |  |
| leaf_edit_401 | O5/REF | 1 of 402 entities change VersionID; 1 relowered | 1 of 402 entities change value class | agree | 1 |  |  |

## Full report of the re-run (`cb74cea`)

The run's output, with headings demoted one level.

### Counts per observable and classification

| observable | agree | predicted mismatch | unexpected mismatch | gap | total |
|---|---|---|---|---|---|
| O0/REF/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/REF/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O0/STRUCT/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/STRUCT/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O1/REF | 1976135 | 0 | 0 | 0 | 1976135 |
| O1/STRUCT | 1971756 | 4379 | 0 | 0 | 1976135 |
| O2/REF | 132 | 0 | 0 | 0 | 132 |
| O2/STRUCT | 132 | 0 | 0 | 0 | 132 |
| O3/REF/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/REF/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/REF/renamed (order-preserving) | 61 | 6 | 0 | 0 | 67 |
| O3/REF/renamed (order-reversing) | 61 | 6 | 0 | 0 | 67 |
| O3/STRUCT/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/STRUCT/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/STRUCT/renamed (order-preserving) | 0 | 67 | 0 | 0 | 67 |
| O3/STRUCT/renamed (order-reversing) | 0 | 67 | 0 | 0 | 67 |
| O4a/REF | 73 | 0 | 0 | 0 | 73 |
| O4a/STRUCT | 73 | 0 | 0 | 0 | 73 |
| O4b/REF | 71 | 6 | 0 | 0 | 77 |
| O4b/STRUCT | 71 | 6 | 0 | 0 | 77 |
| O5/REF | 3 | 0 | 0 | 0 | 3 |
| O5/STRUCT | 0 | 3 | 0 | 0 | 3 |
| adv2/REF | 1 | 0 | 0 | 0 | 1 |
| adv2/STRUCT | 1 | 0 | 0 | 0 | 1 |

Overall: agree 3963166, predicted mismatch 5172, unexpected mismatch 0, gap 0

### Every row that is not agree

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| corpus: factorial | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | factorial/0.7 |
| corpus: factorial | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | factorial/0.7 |
| corpus: factorial | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: factorial | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fibonacci | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | fibonacci/0.10; fibonacci/0.6 |
| corpus: fibonacci | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | fibonacci/0.10; fibonacci/0.6 |
| corpus: fibonacci | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fibonacci | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sum_to_n | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | sum_to_n/0.7 |
| corpus: sum_to_n | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | sum_to_n/0.7 |
| corpus: sum_to_n | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sum_to_n | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: gcd | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: gcd | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: collatz_step_count | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | collatz_half/0.7; collatz_is_even/0.10; collatz_step_count_from/0.6 |
| corpus: collatz_step_count | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | collatz_half/0.7; collatz_is_even/0.10; collatz_step_count_from/0.6 |
| corpus: collatz_step_count | O1/STRUCT | unequal | equal | predicted mismatch | 4 | predicted: adversarial 1 (distinct referents with equal content) | collatz_half/0.1 ~ collatz_is_even/0.1; collatz_half/0.8 ~ collatz_is_even/0.11; collatz_is_even/0.6 ~ collatz_step_count_from/0.1 |
| corpus: collatz_step_count | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: collatz_step_count | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_loop | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | is_even/0.5; is_odd/0.5 |
| corpus: deep_loop | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | is_even/0.5; is_odd/0.5 |
| corpus: deep_loop | O1/STRUCT | unequal | equal | predicted mismatch | 13 | predicted: adversarial 1 (distinct referents with equal content) | is_even/0.1 ~ is_odd/0.1; is_even/0.1 ~ sum_apply/0.1; is_even/0.1 ~ sum_loop/0.1 |
| corpus: deep_loop | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_loop | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_recursion | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | deep_sum/0.7 |
| corpus: deep_recursion | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | deep_sum/0.7 |
| corpus: deep_recursion | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_recursion | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: abs_value | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: abs_value | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: max_of_two | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: max_of_two | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: clamp | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: clamp | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: counter | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: counter | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: account | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: account | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: power_compiler | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compile/0.0; compile/0.3; emit/0.5 |
| corpus: power_compiler | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compile/0.0; compile/0.3; emit/0.5 |
| corpus: power_compiler | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: power_compiler | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: checked_compile | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 5 | predicted: arity collapse (single endpoint and one-element tuple project alike) | checked_compile/0.3; emit/0.5; emit/0.7 |
| corpus: checked_compile | O0/REF/exact | content | decoded differs | predicted mismatch | 5 | predicted: arity collapse (single endpoint and one-element tuple project alike) | checked_compile/0.3; emit/0.5; emit/0.7 |
| corpus: checked_compile | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: checked_compile | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: replace_self | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | replace_self/0.1 |
| corpus: replace_self | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | replace_self/0.1 |
| corpus: replace_self | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: replace_self | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: insertion_sort | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert/0.14; insert/0.18; insert/0.5 |
| corpus: insertion_sort | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert/0.14; insert/0.18; insert/0.5 |
| corpus: insertion_sort | O1/STRUCT | unequal | equal | predicted mismatch | 4 | predicted: adversarial 1 (distinct referents with equal content) | insert/0.10 ~ insert/0.19; insert/0.14 ~ insert/0.5; insert/0.2 ~ insert/0.27 |
| corpus: insertion_sort | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: insertion_sort | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: let_bindings | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: let_bindings | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | map/0.18 ~ map/0.2 |
| corpus: map | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fold | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | fold/0.17 ~ fold/0.2 |
| corpus: fold | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fold | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sort_swap | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert_by/0.15; insert_by/0.19; insert_by/0.5 |
| corpus: sort_swap | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert_by/0.15; insert_by/0.19; insert_by/0.5 |
| corpus: sort_swap | O1/STRUCT | unequal | equal | predicted mismatch | 4 | predicted: adversarial 1 (distinct referents with equal content) | insert_by/0.11 ~ insert_by/0.20; insert_by/0.15 ~ insert_by/0.5; insert_by/0.2 ~ insert_by/0.29 |
| corpus: sort_swap | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sort_swap | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map_long_tuple | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map_long_tuple | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map_long_tuple | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | map/0.18 ~ map/0.2 |
| corpus: map_long_tuple | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map_long_tuple | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: make_adder | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | apply_adder/0.0; apply_adder/0.1 |
| corpus: make_adder | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | apply_adder/0.0; apply_adder/0.1 |
| corpus: make_adder | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: make_adder | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compose | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 7 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compose/0.1; compose/0.3; run_compose/0.1 |
| corpus: compose | O0/REF/exact | content | decoded differs | predicted mismatch | 7 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compose/0.1; compose/0.3; run_compose/0.1 |
| corpus: compose | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | run_compose/0.7 ~ run_two_closures/0.10 |
| corpus: compose | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compose | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compiler | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 75 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; lower/0.103 |
| corpus: compiler | O0/REF/exact | content | decoded differs | predicted mismatch | 75 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; lower/0.103 |
| corpus: compiler | O1/STRUCT | unequal | equal | predicted mismatch | 685 | predicted: adversarial 1 (distinct referents with equal content) | evals/0.13 ~ seq_code/0.16; evals/0.15 ~ seq_code/0.10; evals/0.15 ~ seq_code/0.18 |
| corpus: compiler | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compiler | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: instrument | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 78 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; instrument/0.1 |
| corpus: instrument | O0/REF/exact | content | decoded differs | predicted mismatch | 78 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; instrument/0.1 |
| corpus: instrument | O1/STRUCT | unequal | equal | predicted mismatch | 686 | predicted: adversarial 1 (distinct referents with equal content) | evals/0.13 ~ seq_code/0.16; evals/0.15 ~ seq_code/0.10; evals/0.15 ~ seq_code/0.18 |
| corpus: instrument | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: instrument | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: bootstrap | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 106 | predicted: arity collapse (single endpoint and one-element tuple project alike) | arg_exprs/0.6; evals/0.12; evals/0.15 |
| corpus: bootstrap | O0/REF/exact | content | decoded differs | predicted mismatch | 106 | predicted: arity collapse (single endpoint and one-element tuple project alike) | arg_exprs/0.6; evals/0.12; evals/0.15 |
| corpus: bootstrap | O1/STRUCT | unequal | equal | predicted mismatch | 2977 | predicted: adversarial 1 (distinct referents with equal content) | arg_exprs/0.1 ~ vm_bind/0.1; arg_exprs/0.14 ~ evals/0.7; arg_exprs/0.14 ~ seq_code/0.26 |
| corpus: bootstrap | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: bootstrap | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_called (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_called (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_called (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_called (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (source) | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | nested/0.2 ~ plain/0.0 |
| continuity: fold (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2 |
| continuity: wrap (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2 |
| continuity: wrap (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2; f/1.1 |
| continuity: wrap (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2; f/1.1 |
| continuity: wrap (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1; f/0.3 |
| continuity: unwrap (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1; f/0.3 |
| continuity: unwrap (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.3 |
| continuity: unwrap (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.3 |
| continuity: unwrap (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 1) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 1) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 2) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 2) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: conflicting_edits (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: conflicting_edits (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/1.1 |
| continuity: extract_function (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/1.1 |
| continuity: extract_function (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1 |
| continuity: inline_function (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1 |
| continuity: inline_function (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| adversarial 1: two referents with equal content | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | r1 ~ r2 |
| adversarial 3: symmetric, differently named | O4b/STRUCT | Unknown | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| adversarial 3: symmetric, differently named | O4b/REF | Unknown | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| adversarial 3: asymmetric control, differently named | O4b/STRUCT | Unknown | Known(1) | predicted mismatch | 2 | predicted: adversarial 3 (main cannot join independently named middle states; the candidate joins them by isomorphism); isomorphisms joining the middle states: 1 | p; q |
| adversarial 3: asymmetric control, differently named | O4b/REF | Unknown | Known(1) | predicted mismatch | 2 | predicted: adversarial 3 (main cannot join independently named middle states; the candidate joins them by isomorphism); isomorphisms joining the middle states: 1 | p; q |
| adversarial 3: symmetric, same naming | O4b/STRUCT | Known(1) | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| adversarial 3: symmetric, same naming | O4b/REF | Known(1) | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| leaf_edit_41 | O5/STRUCT | 1 of 42 entities change VersionID; 1 relowered | 22 of 42 entities change value class (1 of 1 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| leaf_edit_401 | O5/STRUCT | 1 of 402 entities change VersionID; 1 relowered | 202 of 402 entities change value class (1 of 1 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| cross-function: compiler, edit in upper | O5/STRUCT | 2 of 549 entities change VersionID; 2 removed, 2 created | 129 of 549 entities change value class (5 of 5 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |

### Adversarial case 2: recursion (factorial)

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| adversarial 2: factorial | adv2/STRUCT | function links to itself by EntityID | self-loop: the link role of handle 0 targets handle 0 | agree | 1 | matches the predicted representation |  |
| adversarial 2: factorial | adv2/REF | function links to itself by EntityID | nullary atom symbol:'factorial' | agree | 1 | matches the predicted representation |  |

Consequences for equality (O1) and identity (O3), counted over the factorial program:

| observable | classification | n |
|---|---|---|
| O1/REF | agree | 66 |
| O1/STRUCT | agree | 66 |
| O3/REF/built twice | agree | 1 |
| O3/REF/one literal changed | agree | 1 |
| O3/REF/renamed (order-preserving) | agree | 1 |
| O3/REF/renamed (order-reversing) | agree | 1 |
| O3/STRUCT/built twice | agree | 1 |
| O3/STRUCT/one literal changed | agree | 1 |
| O3/STRUCT/renamed (order-preserving) | predicted mismatch | 1 |
| O3/STRUCT/renamed (order-reversing) | predicted mismatch | 1 |

### Composition (O4): outcomes by kind

| variant | main | candidate | classification | n |
|---|---|---|---|---|
| O4a | Known(0) | Known(0) | agree | 32 |
| O4a | Known(1) | Known(1) | agree | 106 |
| O4a | Known(2) | Known(2) | agree | 2 |
| O4a | Unknown | Unknown | agree | 4 |
| O4a | absent (not mapped) | Unknown | agree | 2 |
| O4b | Known(0) | Known(0) | agree | 32 |
| O4b | Known(1) | Known(1) | agree | 102 |
| O4b | Known(1) | varies across isomorphisms | predicted mismatch | 4 |
| O4b | Known(2) | Known(2) | agree | 2 |
| O4b | Unknown | Known(1) | predicted mismatch | 4 |
| O4b | Unknown | Unknown | agree | 4 |
| O4b | Unknown | varies across isomorphisms | predicted mismatch | 4 |
| O4b | absent (not mapped) | Unknown | agree | 2 |

### Version churn (O5)

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| leaf_edit_41 | O5/STRUCT | 1 of 42 entities change VersionID; 1 relowered | 22 of 42 entities change value class (1 of 1 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| leaf_edit_41 | O5/REF | 1 of 42 entities change VersionID; 1 relowered | 1 of 42 entities change value class (0 of 1 functions) | agree | 1 |  |  |
| leaf_edit_401 | O5/STRUCT | 1 of 402 entities change VersionID; 1 relowered | 202 of 402 entities change value class (1 of 1 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| leaf_edit_401 | O5/REF | 1 of 402 entities change VersionID; 1 relowered | 1 of 402 entities change value class (0 of 1 functions) | agree | 1 |  |  |
| cross-function: compiler, edit in upper | O5/STRUCT | 2 of 549 entities change VersionID; 2 removed, 2 created | 129 of 549 entities change value class (5 of 5 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| cross-function: compiler, edit in upper | O5/REF | 2 of 549 entities change VersionID; 2 removed, 2 created | 2 of 549 entities change value class (1 of 5 functions) | agree | 1 |  |  |

## Full report of the revision 1 run (`6739252`)

The run's output, with headings demoted one level.

### Counts per observable and classification

| observable | agree | predicted mismatch | unexpected mismatch | gap | total |
|---|---|---|---|---|---|
| C0/NAMED | 67 | 0 | 0 | 0 | 67 |
| O0/NAMED/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/NAMED/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O0/REF/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/REF/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O0/STRUCT/exact | 3444 | 316 | 0 | 0 | 3760 |
| O0/STRUCT/modulo-arity | 3760 | 0 | 0 | 0 | 3760 |
| O1/NAMED | 1976135 | 0 | 0 | 0 | 1976135 |
| O1/REF | 1976135 | 0 | 0 | 0 | 1976135 |
| O1/STRUCT | 1971756 | 4379 | 0 | 0 | 1976135 |
| O2/NAMED | 132 | 0 | 0 | 0 | 132 |
| O2/REF | 132 | 0 | 0 | 0 | 132 |
| O2/STRUCT | 132 | 0 | 0 | 0 | 132 |
| O3/NAMED/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/NAMED/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/NAMED/renamed (order-preserving) | 67 | 0 | 0 | 0 | 67 |
| O3/NAMED/renamed (order-reversing) | 67 | 0 | 0 | 0 | 67 |
| O3/REF/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/REF/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/REF/renamed (order-preserving) | 61 | 6 | 0 | 0 | 67 |
| O3/REF/renamed (order-reversing) | 61 | 6 | 0 | 0 | 67 |
| O3/STRUCT/built twice | 47 | 0 | 0 | 0 | 47 |
| O3/STRUCT/one literal changed | 47 | 0 | 0 | 0 | 47 |
| O3/STRUCT/renamed (order-preserving) | 0 | 67 | 0 | 0 | 67 |
| O3/STRUCT/renamed (order-reversing) | 0 | 67 | 0 | 0 | 67 |
| O4a/NAMED | 73 | 0 | 0 | 0 | 73 |
| O4a/REF | 73 | 0 | 0 | 0 | 73 |
| O4a/STRUCT | 73 | 0 | 0 | 0 | 73 |
| O4b/NAMED | 77 | 0 | 0 | 0 | 77 |
| O4b/REF | 71 | 6 | 0 | 0 | 77 |
| O4b/STRUCT | 71 | 6 | 0 | 0 | 77 |
| O5/NAMED | 3 | 0 | 0 | 0 | 3 |
| O5/REF | 3 | 0 | 0 | 0 | 3 |
| O5/STRUCT | 0 | 3 | 0 | 0 | 3 |
| adv2/NAMED | 1 | 0 | 0 | 0 | 1 |
| adv2/REF | 1 | 0 | 0 | 0 | 1 |
| adv2/STRUCT | 1 | 0 | 0 | 0 | 1 |

Overall: agree 5947086, predicted mismatch 5488, unexpected mismatch 0, gap 0

### Every row that is not agree

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| corpus: factorial | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | factorial/0.7 |
| corpus: factorial | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | factorial/0.7 |
| corpus: factorial | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | factorial/0.7 |
| corpus: factorial | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: factorial | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fibonacci | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | fibonacci/0.10; fibonacci/0.6 |
| corpus: fibonacci | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | fibonacci/0.10; fibonacci/0.6 |
| corpus: fibonacci | O0/NAMED/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | fibonacci/0.10; fibonacci/0.6 |
| corpus: fibonacci | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fibonacci | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sum_to_n | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | sum_to_n/0.7 |
| corpus: sum_to_n | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | sum_to_n/0.7 |
| corpus: sum_to_n | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | sum_to_n/0.7 |
| corpus: sum_to_n | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sum_to_n | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: gcd | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: gcd | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: collatz_step_count | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | collatz_half/0.7; collatz_is_even/0.10; collatz_step_count_from/0.6 |
| corpus: collatz_step_count | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | collatz_half/0.7; collatz_is_even/0.10; collatz_step_count_from/0.6 |
| corpus: collatz_step_count | O0/NAMED/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | collatz_half/0.7; collatz_is_even/0.10; collatz_step_count_from/0.6 |
| corpus: collatz_step_count | O1/STRUCT | unequal | equal | predicted mismatch | 4 | predicted: adversarial 1 (distinct referents with equal content) | collatz_half/0.1 ~ collatz_is_even/0.1; collatz_half/0.8 ~ collatz_is_even/0.11; collatz_is_even/0.6 ~ collatz_step_count_from/0.1 |
| corpus: collatz_step_count | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: collatz_step_count | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_loop | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | is_even/0.5; is_odd/0.5 |
| corpus: deep_loop | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | is_even/0.5; is_odd/0.5 |
| corpus: deep_loop | O0/NAMED/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | is_even/0.5; is_odd/0.5 |
| corpus: deep_loop | O1/STRUCT | unequal | equal | predicted mismatch | 13 | predicted: adversarial 1 (distinct referents with equal content) | is_even/0.1 ~ is_odd/0.1; is_even/0.1 ~ sum_apply/0.1; is_even/0.1 ~ sum_loop/0.1 |
| corpus: deep_loop | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_loop | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_recursion | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | deep_sum/0.7 |
| corpus: deep_recursion | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | deep_sum/0.7 |
| corpus: deep_recursion | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | deep_sum/0.7 |
| corpus: deep_recursion | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: deep_recursion | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: abs_value | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: abs_value | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: max_of_two | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: max_of_two | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: clamp | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: clamp | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: counter | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: counter | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: account | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: account | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: power_compiler | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compile/0.0; compile/0.3; emit/0.5 |
| corpus: power_compiler | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compile/0.0; compile/0.3; emit/0.5 |
| corpus: power_compiler | O0/NAMED/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compile/0.0; compile/0.3; emit/0.5 |
| corpus: power_compiler | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: power_compiler | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: checked_compile | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 5 | predicted: arity collapse (single endpoint and one-element tuple project alike) | checked_compile/0.3; emit/0.5; emit/0.7 |
| corpus: checked_compile | O0/REF/exact | content | decoded differs | predicted mismatch | 5 | predicted: arity collapse (single endpoint and one-element tuple project alike) | checked_compile/0.3; emit/0.5; emit/0.7 |
| corpus: checked_compile | O0/NAMED/exact | content | decoded differs | predicted mismatch | 5 | predicted: arity collapse (single endpoint and one-element tuple project alike) | checked_compile/0.3; emit/0.5; emit/0.7 |
| corpus: checked_compile | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: checked_compile | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: replace_self | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | replace_self/0.1 |
| corpus: replace_self | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | replace_self/0.1 |
| corpus: replace_self | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | replace_self/0.1 |
| corpus: replace_self | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: replace_self | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: insertion_sort | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert/0.14; insert/0.18; insert/0.5 |
| corpus: insertion_sort | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert/0.14; insert/0.18; insert/0.5 |
| corpus: insertion_sort | O0/NAMED/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert/0.14; insert/0.18; insert/0.5 |
| corpus: insertion_sort | O1/STRUCT | unequal | equal | predicted mismatch | 4 | predicted: adversarial 1 (distinct referents with equal content) | insert/0.10 ~ insert/0.19; insert/0.14 ~ insert/0.5; insert/0.2 ~ insert/0.27 |
| corpus: insertion_sort | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: insertion_sort | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: let_bindings | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: let_bindings | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map | O0/NAMED/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | map/0.18 ~ map/0.2 |
| corpus: map | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fold | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | fold/0.17 ~ fold/0.2 |
| corpus: fold | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: fold | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sort_swap | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert_by/0.15; insert_by/0.19; insert_by/0.5 |
| corpus: sort_swap | O0/REF/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert_by/0.15; insert_by/0.19; insert_by/0.5 |
| corpus: sort_swap | O0/NAMED/exact | content | decoded differs | predicted mismatch | 4 | predicted: arity collapse (single endpoint and one-element tuple project alike) | insert_by/0.15; insert_by/0.19; insert_by/0.5 |
| corpus: sort_swap | O1/STRUCT | unequal | equal | predicted mismatch | 4 | predicted: adversarial 1 (distinct referents with equal content) | insert_by/0.11 ~ insert_by/0.20; insert_by/0.15 ~ insert_by/0.5; insert_by/0.2 ~ insert_by/0.29 |
| corpus: sort_swap | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: sort_swap | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map_long_tuple | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map_long_tuple | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map_long_tuple | O0/NAMED/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | map/0.7; map/0.8 |
| corpus: map_long_tuple | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | map/0.18 ~ map/0.2 |
| corpus: map_long_tuple | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: map_long_tuple | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: make_adder | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | apply_adder/0.0; apply_adder/0.1 |
| corpus: make_adder | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | apply_adder/0.0; apply_adder/0.1 |
| corpus: make_adder | O0/NAMED/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | apply_adder/0.0; apply_adder/0.1 |
| corpus: make_adder | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: make_adder | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compose | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 7 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compose/0.1; compose/0.3; run_compose/0.1 |
| corpus: compose | O0/REF/exact | content | decoded differs | predicted mismatch | 7 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compose/0.1; compose/0.3; run_compose/0.1 |
| corpus: compose | O0/NAMED/exact | content | decoded differs | predicted mismatch | 7 | predicted: arity collapse (single endpoint and one-element tuple project alike) | compose/0.1; compose/0.3; run_compose/0.1 |
| corpus: compose | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | run_compose/0.7 ~ run_two_closures/0.10 |
| corpus: compose | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compose | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compiler | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 75 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; lower/0.103 |
| corpus: compiler | O0/REF/exact | content | decoded differs | predicted mismatch | 75 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; lower/0.103 |
| corpus: compiler | O0/NAMED/exact | content | decoded differs | predicted mismatch | 75 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; lower/0.103 |
| corpus: compiler | O1/STRUCT | unequal | equal | predicted mismatch | 685 | predicted: adversarial 1 (distinct referents with equal content) | evals/0.13 ~ seq_code/0.16; evals/0.15 ~ seq_code/0.10; evals/0.15 ~ seq_code/0.18 |
| corpus: compiler | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: compiler | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: instrument | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 78 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; instrument/0.1 |
| corpus: instrument | O0/REF/exact | content | decoded differs | predicted mismatch | 78 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; instrument/0.1 |
| corpus: instrument | O0/NAMED/exact | content | decoded differs | predicted mismatch | 78 | predicted: arity collapse (single endpoint and one-element tuple project alike) | evals/0.12; evals/0.15; instrument/0.1 |
| corpus: instrument | O1/STRUCT | unequal | equal | predicted mismatch | 686 | predicted: adversarial 1 (distinct referents with equal content) | evals/0.13 ~ seq_code/0.16; evals/0.15 ~ seq_code/0.10; evals/0.15 ~ seq_code/0.18 |
| corpus: instrument | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: instrument | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: bootstrap | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 106 | predicted: arity collapse (single endpoint and one-element tuple project alike) | arg_exprs/0.6; evals/0.12; evals/0.15 |
| corpus: bootstrap | O0/REF/exact | content | decoded differs | predicted mismatch | 106 | predicted: arity collapse (single endpoint and one-element tuple project alike) | arg_exprs/0.6; evals/0.12; evals/0.15 |
| corpus: bootstrap | O0/NAMED/exact | content | decoded differs | predicted mismatch | 106 | predicted: arity collapse (single endpoint and one-element tuple project alike) | arg_exprs/0.6; evals/0.12; evals/0.15 |
| corpus: bootstrap | O1/STRUCT | unequal | equal | predicted mismatch | 2977 | predicted: adversarial 1 (distinct referents with equal content) | arg_exprs/0.1 ~ vm_bind/0.1; arg_exprs/0.14 ~ evals/0.7; arg_exprs/0.14 ~ seq_code/0.26 |
| corpus: bootstrap | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| corpus: bootstrap | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (source) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (destination) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | quad/0.0; quad/0.1 |
| continuity: rename (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rename (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (source) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (destination) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_function (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_function (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_called (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_called (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_called (source) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | main/0.0 |
| continuity: delete_called (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: delete_called (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (source) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: merge_cells (destination) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (source) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: split_cell (destination) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (source) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/REF/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: upgrade_cell (destination) | O3/REF/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (source) | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | nested/0.2 ~ plain/0.0 |
| continuity: fold (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: fold (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: activate_define (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: leaf_replace (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: insert (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: remove (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2 |
| continuity: wrap (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2 |
| continuity: wrap (source) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2 |
| continuity: wrap (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2; f/1.1 |
| continuity: wrap (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2; f/1.1 |
| continuity: wrap (destination) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.2; f/1.1 |
| continuity: wrap (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: wrap (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1; f/0.3 |
| continuity: unwrap (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1; f/0.3 |
| continuity: unwrap (source) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 2 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1; f/0.3 |
| continuity: unwrap (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.3 |
| continuity: unwrap (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.3 |
| continuity: unwrap (destination) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.3 |
| continuity: unwrap (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: unwrap (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: swap (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: redefine_same (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: shared_subtree (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: ambiguous_duplicate (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 1) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 1) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 2) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: rebase_disjoint (destination 2) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: conflicting_edits (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: conflicting_edits (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (destination) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/1.1 |
| continuity: extract_function (destination) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/1.1 |
| continuity: extract_function (destination) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/1.1 |
| continuity: extract_function (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: extract_function (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (source) | O0/STRUCT/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1 |
| continuity: inline_function (source) | O0/REF/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1 |
| continuity: inline_function (source) | O0/NAMED/exact | content | decoded differs | predicted mismatch | 1 | predicted: arity collapse (single endpoint and one-element tuple project alike) | f/0.1 |
| continuity: inline_function (source) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (source) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (destination) | O3/STRUCT/renamed (order-preserving) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| continuity: inline_function (destination) | O3/STRUCT/renamed (order-reversing) | different StateID | isomorphic | predicted mismatch | 1 | predicted: section 3.11 (EntityID is not part of state identity) |  |
| adversarial 1: two referents with equal content | O1/STRUCT | unequal | equal | predicted mismatch | 1 | predicted: adversarial 1 (distinct referents with equal content) | r1 ~ r2 |
| adversarial 3: symmetric, differently named | O4b/STRUCT | Unknown | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| adversarial 3: symmetric, differently named | O4b/REF | Unknown | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| adversarial 3: asymmetric control, differently named | O4b/STRUCT | Unknown | Known(1) | predicted mismatch | 2 | predicted: adversarial 3 (main cannot join independently named middle states; the candidate joins them by isomorphism); isomorphisms joining the middle states: 1 | p; q |
| adversarial 3: asymmetric control, differently named | O4b/REF | Unknown | Known(1) | predicted mismatch | 2 | predicted: adversarial 3 (main cannot join independently named middle states; the candidate joins them by isomorphism); isomorphisms joining the middle states: 1 | p; q |
| adversarial 3: symmetric, same naming | O4b/STRUCT | Known(1) | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| adversarial 3: symmetric, same naming | O4b/REF | Known(1) | varies across isomorphisms | predicted mismatch | 2 | predicted: section 3.11 (the result depends on which isomorphism joins the steps); isomorphisms joining the middle states: 2 | p; q |
| leaf_edit_41 | O5/STRUCT | 1 of 42 entities change VersionID; 1 relowered | 22 of 42 entities change value class (1 of 1 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| leaf_edit_401 | O5/STRUCT | 1 of 402 entities change VersionID; 1 relowered | 202 of 402 entities change value class (1 of 1 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| cross-function: compiler, edit in upper | O5/STRUCT | 2 of 549 entities change VersionID; 2 removed, 2 created | 129 of 549 entities change value class (5 of 5 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |

### Adversarial case 2: recursion (factorial)

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| adversarial 2: factorial | adv2/STRUCT | function links to itself by EntityID | self-loop: the link role of handle 0 targets handle 0 | agree | 1 | matches the predicted representation |  |
| adversarial 2: factorial | adv2/REF | function links to itself by EntityID | nullary atom symbol:'factorial' | agree | 1 | matches the predicted representation |  |
| adversarial 2: factorial | adv2/NAMED | function links to itself by EntityID | Named target 'factorial'; containment acyclic | agree | 1 | self-reference is a Named target to the function's own name, not a contained cycle |  |

Consequences for equality (O1) and identity (O3), counted over the factorial program:

| observable | classification | n |
|---|---|---|
| O1/NAMED | agree | 66 |
| O1/REF | agree | 66 |
| O1/STRUCT | agree | 66 |
| O3/NAMED/built twice | agree | 1 |
| O3/NAMED/one literal changed | agree | 1 |
| O3/NAMED/renamed (order-preserving) | agree | 1 |
| O3/NAMED/renamed (order-reversing) | agree | 1 |
| O3/REF/built twice | agree | 1 |
| O3/REF/one literal changed | agree | 1 |
| O3/REF/renamed (order-preserving) | agree | 1 |
| O3/REF/renamed (order-reversing) | agree | 1 |
| O3/STRUCT/built twice | agree | 1 |
| O3/STRUCT/one literal changed | agree | 1 |
| O3/STRUCT/renamed (order-preserving) | predicted mismatch | 1 |
| O3/STRUCT/renamed (order-reversing) | predicted mismatch | 1 |

### Composition (O4): outcomes by kind

| variant | main | candidate | classification | n |
|---|---|---|---|---|
| O4a | Known(0) | Known(0) | agree | 48 |
| O4a | Known(1) | Known(1) | agree | 159 |
| O4a | Known(2) | Known(2) | agree | 3 |
| O4a | Unknown | Unknown | agree | 6 |
| O4a | absent (not mapped) | Unknown | agree | 3 |
| O4b | Known(0) | Known(0) | agree | 48 |
| O4b | Known(1) | Known(1) | agree | 155 |
| O4b | Known(1) | varies across isomorphisms | predicted mismatch | 4 |
| O4b | Known(2) | Known(2) | agree | 3 |
| O4b | Unknown | Known(1) | predicted mismatch | 4 |
| O4b | Unknown | Unknown | agree | 10 |
| O4b | Unknown | varies across isomorphisms | predicted mismatch | 4 |
| O4b | absent (not mapped) | Unknown | agree | 3 |

### Version churn (O5)

| case | observable | main | candidate | classification | n | note | examples |
|---|---|---|---|---|---|---|---|
| leaf_edit_41 | O5/STRUCT | 1 of 42 entities change VersionID; 1 relowered | 22 of 42 entities change value class (1 of 1 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| leaf_edit_41 | O5/REF | 1 of 42 entities change VersionID; 1 relowered | 1 of 42 entities change value class (0 of 1 functions) | agree | 1 |  |  |
| leaf_edit_41 | O5/NAMED | 1 of 42 entities change VersionID; 1 relowered | 1 of 42 entities change value class (0 of 1 functions) | agree | 1 |  |  |
| leaf_edit_401 | O5/STRUCT | 1 of 402 entities change VersionID; 1 relowered | 202 of 402 entities change value class (1 of 1 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| leaf_edit_401 | O5/REF | 1 of 402 entities change VersionID; 1 relowered | 1 of 402 entities change value class (0 of 1 functions) | agree | 1 |  |  |
| leaf_edit_401 | O5/NAMED | 1 of 402 entities change VersionID; 1 relowered | 1 of 402 entities change value class (0 of 1 functions) | agree | 1 |  |  |
| cross-function: compiler, edit in upper | O5/STRUCT | 2 of 549 entities change VersionID; 2 removed, 2 created | 129 of 549 entities change value class (5 of 5 functions) | predicted mismatch | 1 | predicted: direction review section 3.3 (version identity derived from candidate equality propagates to ancestors and referrers) |  |
| cross-function: compiler, edit in upper | O5/REF | 2 of 549 entities change VersionID; 2 removed, 2 created | 2 of 549 entities change value class (1 of 5 functions) | agree | 1 |  |  |
| cross-function: compiler, edit in upper | O5/NAMED | 2 of 549 entities change VersionID; 2 removed, 2 created | 2 of 549 entities change value class (1 of 5 functions) | agree | 1 |  |  |

### Predictions (revision plan section 3)

| observable | prediction | result | detail |
|---|---|---|---|
| O0 | round trip exact modulo arity; arity collapse unchanged | hit | modulo arity: 3760 of 3760 agree; exact: 0 unexpected, 316 arity collapses (STRUCT: 316) |
| O1 | agrees with main on every pair, as REF did | hit | 1976135 of 1976135 entity pairs agree |
| O2 | agrees | hit | 132 of 132 link targets agree |
| O3 built twice / literal changed | agrees | hit | 94 of 94 state pairs agree |
| O3 renamed (both orders) | agrees with main: not isomorphic, names are fixed | hit | 134 of 134 renamed state pairs (not isomorphic, as main) agree |
| O4 shared and independent middle states | agrees with main on every real chain | hit | 138 of 138 composed sources (real chains and adversarial 4) agree |
| adversarial 3, differently named | Unknown, as main | hit | 4 of 4 sources agree; 4 are Unknown |
| adversarial 3, symmetric with same naming | agrees with main; no dependence on an isomorphism | hit | 8 of 8 sources agree; 0 vary (no isomorphism is searched) |
| O5, all three scenarios | agrees with main (1, 1, 2) | hit | 3 of 3 scenarios agree; VersionID changes in main: [1, 1, 2] |
| contained cycles in projected states | none | hit | 67 of 67 projected states agree; 0 with a contained cycle |

Hits 10 of 10.

### Reproduction of the frozen candidate (`cb74cea`)

STRUCT and REF reproduce the recorded per-observable counts and O5 rows exactly.
