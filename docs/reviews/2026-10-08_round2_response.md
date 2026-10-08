# Reply to the second review round, 2026-10-08

Answers [the second-round review](2026-10-08_round2_review.txt). Each of its
points has a row in [the ledger](2026-10-08_ledger.md), S1–S15. The bootstrap
fixes are commit `80bef0d` on `workflow/bootstrap-review` (issue #83).

## Bootstrap points

### S1. A guard on F3

- **Verdict:** accepted.
- **Change:** task 29: if D4 settles on a workload that differs materially
  from the recommended one, the comparison is redone for it before D3 is
  accepted.

### S2. F4

- **Verdict:** agreed; no change.

### S3. Provenance must be unforgeable

- **Verdict:** accepted. "The producer is recorded" says nothing if the
  program that supplies a chunk also supplies the record.
- **Change:** task 29's admission rule now says who may assert that a
  compiler generation produced a chunk for a node version, and why program
  code cannot forge that.
- **A structural answer, for the spike to test:** programs never submit
  chunks. The admission path itself runs the installed compiler on the node
  and records the producer. Replacing the compiler takes the activation
  capability, like any other activation.

### S4. Route (a) and the canonical-source anchor

- **Verdict:** accepted. The wrappers are per-function program code, not
  route machinery, and exempting them hid the anchor violation that round 1
  itself pointed out.
- **Change:** task 29 must establish whether the SHEAR-VM route has a form
  that keeps the source canonical and executable forms derived. If it has
  none, that route stays a candidate only if the owner explicitly changes the
  first acceptance anchor. Task 30 now exempts only the VM's own functions.
- **Correction to round 1 (F5):** dependency freshness is irrelevant only
  for per-node chunks, whose children are referenced by `EntityID`. The SHEAR
  compiler emits expanded chunks, with children inlined (self_hosting §2). A
  source-preserving route (a) that cached such chunks against a function
  would go stale when any node below changes (bytecode §2). It needs either
  per-node chunks or subtree versions. Per-node chunks are the same
  node-identity work route (b) needs, which narrows route (a)'s advantage to
  trust alone.

### S5. Task 28 contradicted itself

- **Verdict:** verified defect.
- **Change:** "for every operation in `shear/operations.py`, a bootstrap
  matrix declares its status". Supported entries are derived from the code,
  only rejected or deferred is declared in the test, and `operations.py`
  keeps shapes.

### S6. `RAISE` missing from task 29's list

- **Verdict:** verified defect, a transcription slip from round 1.
- **Change:** `RAISE` added.

### S7. Scaffolding if route (a) wins

- **Verdict:** accepted.
- **Change:** vm_in_shear §7: if D3 chooses the SHEAR VM, the twins and
  wrappers stay only in a form task 29 shows keeps the source canonical, or
  as an exception to the first anchor that the owner accepts explicitly.

## Design points

- **S8, the independence condition:** accepted in the reviewer's wording, for
  the canaries section and the checklist.
- **S9, canaries as blocked probes:** agreed. The ledger's "program" status
  with a named prerequisite says exactly that.
- **S10, systems identity:** agreed.
- **S11, the new goals:** accepted, with one scope note. Asked which of the
  extrapolated goals he holds, the owner answered "most of it". The rows move
  to "add", Provisional and not scheduled, and a later round may still drop
  one.
- **S12, graph_ledger.md:** agreed.
- **S13, the velocity principles:** accepted as refined.
- **S14, "one revision":**
  - **Verdict:** partly accepted. A broken instrument or a wrongly formulated
    discriminator is a real reason to revise, so the count should not be
    project-wide.
  - **Pushback:** a revision made after seeing results is where goalposts
    move. Proposed edit 10 now generalizes predictions before the run and a
    named falsifier. The count stays per task, and any revision is recorded
    with its reason before the rerun.

## State

- `workflow/bootstrap-review` has no open point from either round. It is
  ready for another review or for the owner to merge.
- `workflow/design-goals` goes to a consolidation round: the ledger's
  proposed edits, applied to the existing documents.
