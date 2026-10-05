# Projection Plan – Step 5

Status: plan for execution  
Branch: `research/semantic-core`  
Plan steps: 5 and 6 of `handoff.md`

This is the implementation plan for the single `main → candidate → observable`
projection. It is written for an executing session that has not seen the
discussion that produced it. Read `handoff.md` and charter §3.11 first.

The candidate is frozen (handoff, "Candidate core"). Nothing in this plan
changes candidate semantics. If the implementation seems to need a change,
stop and record it as a step-7 revision candidate instead.

## 1. Goal

Project real `main` states into the candidate core and compare observables.
The output is evidence: a classified list of agreements, predicted mismatches,
unexpected mismatches and projection gaps.

The experiment does not have to pass. A mismatch is a result, not a bug to
fix by adjusting the projection until it agrees.

## 2. Isolation

- Code lives in `research/core_projection/`, a package
  (`research/core_projection/__init__.py`). Do **not** add
  `research/__init__.py`: without it, the root
  `python3 -m unittest discover` does not descend into `research/`, so the
  normal suite and `tests/lanes.py` are unaffected. Verify this.
- Standard library only. Python 3.12.
- The candidate side (`core.py`) must not import `shear`. Only `project.py`,
  `observables.py`, `adversarial.py` and `run.py` read `main`.
- The candidate side must not reuse `main` algorithms (canonical equality,
  `compose`, matching). Oracle independence is the point.
- Run tests with:

      python3 -m unittest discover -s research -t research

- Run the experiment with:

      PYTHONPATH=research python3 -m core_projection.run

- Add `.github/workflows/core-projection.yml`: on push to
  `research/semantic-core` and manual dispatch, Python 3.12, run the tests,
  then run the experiment and print the report. The experiment step must not
  fail the job because of mismatches – only because of crashes.

## 3. Modules

Keep each file under about 500 lines.

### 3.1 `core.py` – candidate model (no `shear` import)

- `Atom`: frozen `(tag, value)` with tags `none`, `bool`, `int`, `text`,
  `bytes`, `symbol`. `("bool", True) != ("int", 1)`.
- `CState`: immutable mapping `handle → (atom | None, roles)`, where
  `roles` maps role name → tuple of handles. Handles are ints and carry no
  meaning. Constructor validates that every target exists.
- `bisimilar(left, a, right, b) -> bool`. Role targets are ordered and
  labelled, so successors are deterministic: use a pair worklist with
  union-find. Pop a pair; reject on different atoms, role-name sets or
  sequence lengths; push corresponding child pairs; already-merged pairs are
  skipped. Exact, near-linear, no backtracking.
- `isomorphisms(left, right, limit=None)`: enumerate bijections of handles
  preserving atoms, role names, sequences and targets (charter §3.11). Use
  colour refinement on both graphs (atom, role signature, in-edge
  signature), then backtracking with forward propagation along role
  targets. `isomorphic(left, right)` is `next(..., None) is not None`.
- Continuity: `Continuity = Mapping[int, frozenset[int]]`. A key present is
  `Known(set)`; an absent key is `Unknown`.
  `compose(c1, c2)` implements `(K, K <: M1.M2)` with
  `K = { s ∈ K1 | M1[s] ⊆ K2 }` (direction review §5).
  `transport(c, iso)` renames source or destination handles through an
  isomorphism.

### 3.2 `project.py` – π from `main`

`project(state, mode) -> Projection(cstate, view, ownership_handles)`.

Input states are `main` `State`s in graph form: corpus programs go through
`shear.lang.load` first.

Per entity: project its `Value.content` (already canonical) to a fresh
subtree; `view[entity]` is the root handle. No sharing between entities and
no hash-consing.

Content rules:

| canonical content | candidate relation |
|---|---|
| `None`, `bool`, `int`, `str` | nullary, typed atom |
| node `bytes` | nullary, `bytes` atom |
| node `tuple`, `list` | atom `symbol:tuple` / `symbol:list`, role `items` |
| node `map` | atom `symbol:map`, role `entries`; each entry: atom `symbol:entry`, roles `key`, `value` |
| node `relation` (a `Relation` record) | atom `symbol:relation:<kind>`; one role per `main` role name, targets in order; role `payload` if the payload is not `None` |
| node `entity_id` | depends on mode, below |
| node `version_id`, `state_id` | nullary `symbol` atom; record each occurrence as a gap (identity inside content) |
| any other node `(kind, payload)` | atom `symbol:<kind>`, role `payload` with one target |

Modes for `entity_id`:

- `STRUCT` (charter-faithful, the primary run): the reference becomes a
  direct role target to the referenced entity's root handle. An `entity_id`
  naming an entity absent from the state raises `ProjectionGap`.
- `REF` (control only): the reference becomes a nullary `symbol` atom
  holding the `EntityID` string. This puts `EntityID` into value, which
  charter §3.8 says it is not. Its purpose is to show what `STRUCT` loses.

Wherever a role is a single endpoint in `main`, treat it as a one-element
sequence.

Ownership: for each owner, one relation with atom `symbol:owns`, role
`owner` → `(root of owner)`, role `owned` → roots of children in `main`
order. These live inside the state, so they take part in state identity.

Determinism: handle allocation may follow sorted `EntityID` order. Nothing
else may depend on `EntityID` spelling.

`decode(projection) -> dict[EntityID, canonical content]`: the inverse on
content, using `view` to turn root targets back into `EntityID`s in
`STRUCT` mode. This is the data-fragment interpretation σ for H2.

### 3.3 `observables.py`

Each observable returns rows `(case, observable, main_result,
candidate_result, classification, note)`. Classifications:

```text
agree
predicted mismatch      (prediction cited: §3.11 or adversarial case number)
unexpected mismatch
gap                     (projection could not represent the input)
```

- **O0 round trip:** `decode(project(S)) == {e: S.values[e].content}`.
- **O1 equality:** for every pair of entities in a state, `main`
  `semantic_equal` versus candidate `bisimilar` on their roots. Run in both
  modes.
- **O2 link targets:** for each `links` relation of each function, the
  `main` target `EntityID` versus the entity recovered from the candidate
  target through `view` inverse.
- **O3 state identity, both directions:** for pairs of `main` states,
  `StateID` equality versus candidate `isomorphic`. Pairs: the same program
  loaded twice; the program with every `EntityID` consistently renamed; the
  program with one literal changed.
- **O4 composition:** for continuity-corpus transformations
  (`shear.continuity.CASES`) and adversarial case 4, `main`
  `transforms.compose` versus candidate `compose` on projected handles. If
  the intermediate states were built independently, compose through every
  isomorphism and report whether the result is the same for all of them.
  `compose` rejects `TransformResult`s; a `TransformResult` carries its
  `source`, `destination` and `mappings`, so build the `main` side from
  those mappings and the candidate side from projected `source` and
  `destination`.
- **O5 version churn:** for the leaf-edit scenarios in
  `shear/examples/ledger.py` (`_leaf_edit_measurement(20)` and the 401-node
  variant used by `measurements()`), count entities
  whose `main` `VersionID` changed, versus entities whose candidate value
  class changed (root not bisimilar to its old root). `main` relowers one
  node; record the candidate count in both modes.

### 3.4 `adversarial.py`

Build these as `main` states or transformations:

1. Two relations referring to two different entities whose content is
   equal. Prediction: `STRUCT` makes them equal, `main` does not.
2. `factorial` from the corpus. Record which representation each mode
   produces: `STRUCT` yields a cycle; `REF` yields an `EntityID` atom.
   Report the O1 and O3 consequences.
3. Independently built middle states (charter §3.11):
   - symmetric: two equal, unconnected values; built twice with different
     `EntityID` naming;
   - asymmetric control: the same, but the two values differ.
   Prediction: the control composes uniquely; the symmetric case may
   depend on the isomorphism.
4. Composition cases: chain, disappearance, unknown, split, split with
   disappearing branch, split with unknown branch, merge after split.

### 3.5 `run.py`

Runs every corpus program (`shear.examples.EXAMPLES`), the continuity corpus
and the adversarial cases through all observables in both modes. Prints a
Markdown report:

- counts per observable and classification;
- every non-`agree` row;
- the recursion result for adversarial case 2;
- the O5 numbers.

## 4. Tests (machinery only)

Tests check that the instruments work. They do not assert experimental
outcomes – those belong in the report.

- `bisimilar`: the Alloy witness set – different atoms, role sets, target
  order, multiplicity, present-empty versus absent role are unequal; equal
  values with different sharing are equal; self-cycle equals two-node cycle.
- `bisimilar` versus a separate naive reference (greatest fixpoint over all
  pairs) on random small states, seeded `random.Random(seed)` with
  `subTest(seed=...)`.
- `isomorphisms`: random state versus a random handle permutation of itself
  is isomorphic; a single atom change breaks it; the symmetric state of
  adversarial case 3 has exactly two automorphisms, the control exactly one.
- `compose`: versus a naive reference written directly from
  `Unknown | Known(set)` case analysis, on random inputs; associativity on
  random triples; Unknown never becomes `Known({})`.
- `project`: every target exists; `("bool", True)` and `("int", 1)` stay
  distinct; projecting the same state twice with shuffled construction
  order gives isomorphic results; `decode` round trip on synthetic states
  in both modes; `STRUCT` raises `ProjectionGap` on a dangling reference.
- Per CLAUDE.md, for each property test plant a plausible bug once and
  confirm the test catches it; mention this in the commit or PR.

## 5. Deliverables and stopping point

1. Code and tests as above, plus the workflow.
2. One run of `run.py`, with its report saved as
   `docs/research/semantic-core/projection_results.md`, preceded by a short
   summary that states each classification count and every unexpected
   mismatch.
3. One appended diary entry.
4. `handoff.md`: mark steps 5 and 6 done.

Then stop. Steps 7 and 8 – the one candidate revision and the H1 evaluation
against the mechanism inventory – are separate tasks with their own plan
and review.

## 6. Commit plan

Small coherent commits, one-line smart-commit messages, none pushed without
the owner's go-ahead:

1. `Add candidate core model for projection experiment` (`core.py`, tests)
2. `Add main to candidate projection` (`project.py`, tests)
3. `Add projection observables and adversarial cases`
4. `Add projection experiment runner and workflow`
5. `Record first projection results` (results, diary, handoff)
