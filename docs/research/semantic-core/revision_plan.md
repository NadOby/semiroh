# Candidate Revision Plan – Step 7

Status: plan for execution  
Branch: `research/semantic-core`  
Plan steps: 7 of `docs/research/semantic-core/handoff.md`; step 8 follows on Opus

This is the single candidate revision the timebox allows. It is written for an
executing session that has not seen the discussion behind it. Read
`docs/research/semantic-core/handoff.md`, charter §3 and §3.11, and the re-run
section of `projection_results.md` first.

After this revision there is no second redesign cycle. If the revised
candidate also fails, that is the step-8 result.

## 1. Evidence the revision answers

From the re-run at `cb74cea` (0 unexpected, 5,172 predicted, 0 gaps):

- **`STRUCT`, the charter-faithful mode, loses `main` distinctions.**
  - O1: 4,379 entity pairs in real programs that `main` keeps apart are
    equal in the candidate (distinct referents with equal content).
  - O5: a leaf edit changes the value class of 22 of 42, 202 of 402, and in
    `compiler` 129 of 549 entities (all five functions), against 1, 1 and 2
    `VersionID` changes in `main`.
- **`REF`, the control, matches `main` on O1, O2 and O5**, but only by putting
  `EntityID` strings into atoms, which contradicts charter §3.8.
- **Composition (O4)** agrees on every real chain. It depends on the chosen
  isomorphism only in the hand-built symmetric middle state, because
  continuity is stated over anonymous occurrences.
- **O0** round-trips modulo arity; arity collapse is the only loss.

Common cause: the frozen candidate has one kind of role target, a contained
occurrence. `main` has two – contained content, compared structurally, and
references to named entities, compared by name – and continuity and state
identity in `main` are stated over those names.

## 2. The revision: named roots

One idea, applied consistently: entities are named roots inside the state;
everything below a root is anonymous relational content.

1. **Target kinds.** A role target is either `Contained(handle)` or
   `Named(name)`.
2. **Bindings in the state.** A state is `(relations, bindings)`, with
   `bindings : Name ⇀ handle`. Bindings move from the view into the state.
   Every `Named` target must resolve to a binding of the same state.
3. **Acyclic containment.** `Contained` targets form an acyclic graph. Cycles
   pass through `Named` targets only. (`main`'s canonical content is a tree,
   so projected states satisfy this; the projection must check it.)
4. **Value equality.** Bisimulation over `Contained` targets; `Named` targets
   are equal iff their names are equal. On acyclic containment this is plain
   structural equality.
5. **State identity (revises §3.11).** Isomorphism over handles that
   preserves atoms, role names, sequences, `Contained` targets, `Named`
   targets (names are not renamed) and bindings (each name maps to
   corresponding handles).
6. **Continuity over names.** `Continuity` maps source names to `Known(set of
   destination names)`; an absent name is `Unknown`. The composition rule is
   unchanged, `(K, K <: M1.M2)`, over names instead of handles.

What it keeps from the frozen candidate: one relational structure for all
content (no separate value, record and payload layers); typed atoms; ordered
role sequences; the composition algebra.

What it gives up: "EntityID is not intrinsic to relation value" (charter
§3.8). Names become part of values that refer to them and part of state
identity.

### Alternatives considered and rejected

- **Equality that stops at entity roots, without names.** Compare occurrences
  reached through a role target by occurrence identity when they are view
  roots. It works inside one state but has no meaning across states, because
  occurrences have no identity across states. It reduces to named roots as
  soon as two states are compared.
- **Keep occurrence-level continuity alongside named targets.** Leaves the
  symmetric-middle-state dependence in place for no gain: every corpus
  continuity claim is between entities.
- **Encode arity.** Out of scope: the arity question is a step-8 judgement
  about whether `main`'s single-endpoint/one-element-tuple distinction is
  semantic.

## 3. Predictions (recorded before the run)

For a new projection mode `NAMED` that targets the revised candidate:

| observable | prediction |
|---|---|
| O0 | round trip exact modulo arity; arity collapse unchanged |
| O1 | agrees with `main` on every pair, as `REF` did |
| O2 | agrees |
| O3 built twice / literal changed | agrees |
| O3 renamed (both orders) | agrees with `main`: renamed states are not isomorphic, because names are fixed |
| O4 shared and independent middle states | agrees with `main` on every real chain |
| adversarial 3, differently named | `Unknown`, as `main` (names do not match) |
| adversarial 3, symmetric with same naming | agrees with `main`: no dependence on an isomorphism |
| O5, all three scenarios | agrees with `main` (1, 1, 2) |
| contained cycles in projected states | none |

Any `NAMED` result that differs from this table is classified unexpected.

`STRUCT` and `REF` must reproduce the `cb74cea` counts exactly. They are now
the record of the frozen candidate; any change there means the revision
leaked into the frozen code.

## 4. Implementation

### 4.1 Charter

Add `docs/semantic_core_experiment.md` §3.12 "Revision 1: named roots" with
the text of §2 above (definition, what it keeps, what it gives up, rejected
alternatives). Do not edit §3.1–§3.11: they describe the frozen candidate the
first run tested. In §3.11 add one line pointing to §3.12 for the revised
state identity.

### 4.2 Code (`research/core_projection/`)

- **Additive, not in place.** The frozen model in `core.py` stays as it is.
  Put the revised model in a new module, `named.py`: `Name`, target kinds,
  `NState` with bindings, `equal` (structural, with a containment-cycle
  check), `isomorphic`/`isomorphisms` with names fixed, and continuity over
  names reusing the `(K, M)` rule. If code can be shared with `core.py`
  without changing `core.py`'s behaviour, import it; otherwise duplicate.
- **`project.py`:** add `Mode.NAMED`: `entity_id` nodes become
  `Named(EntityID string)`; each entity's root is bound to its name;
  ownership edges become `owns` relations whose `owner` and `owned` targets
  are `Named`. Everything else follows the existing content table. `decode`
  supports `NAMED`.
- **Observables and runner:** run every observable in all three modes. Add
  one observable, **C0 contained cycles**: count projected states whose
  `Contained` graph has a cycle (prediction 0). Add a "Predictions" section
  to the report that checks each row of §3 and lists any miss.
- Keep each file near the 500-line threshold.

### 4.3 Tests (instruments only)

- `named.equal`: the Alloy witness set (different atoms, role sets, order,
  multiplicity, present-empty versus absent role are unequal; equal values
  with different sharing are equal); `Named` targets with different names
  are unequal even when their bound content is equal; a containment cycle
  is rejected.
- `named.isomorphisms`: random state versus a random handle permutation is
  isomorphic; renaming one binding breaks it; a state whose only symmetry is
  between identical anonymous subtrees has the expected automorphism count.
- Continuity over names: versus a naive reference; associativity.
- `project` in `NAMED`: every `Named` target resolves; round trip; the
  bare-reference entity (deviation 3 of the first run) now projects, since a
  root may be a relation with a single `Named` target.
- Plant a plausible bug once per property test and confirm it is caught.

## 5. Deliverables and stopping point

1. Charter §3.12 and the §3.11 pointer.
2. `named.py`, the `NAMED` mode, C0, the predictions check, tests.
3. One run. Add a section "Revision 1 run" at the top of
   `projection_results.md`: the predictions table with hits and misses,
   counts per mode, every unexpected row, and confirmation that `STRUCT` and
   `REF` reproduce `cb74cea`.
4. One diary entry; `handoff.md` step 7 marked done.

Then stop. Step 8 – the H1 evaluation against the mechanism inventory – is an
Opus task.

## 6. Commit plan

None pushed without the owner's go-ahead.

1. `Record candidate revision 1 named roots in the charter`
2. `Add named-roots candidate model`
3. `Add NAMED projection mode and contained-cycle observable`
4. `Record revision 1 projection results`

## 7. What step 8 will do (for orientation, not for this session)

Classify each of the eight inventoried `main` mechanisms as eliminated,
retained unchanged, represented uniformly by an existing candidate
mechanism, or requiring a new special case, for the frozen candidate and for
revision 1; apply the stop rule; give the H1 verdict; record H2 and H3
observations; and state what step 9 – the compatibility-boundary refactor in
`main` – should consolidate.
