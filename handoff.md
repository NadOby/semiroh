# Handoff

Read `CLAUDE.md` and `docs/roadmap.md` first. Verify this checkpoint
against the repository; it is not independent verification evidence.

## State

- Task 28, issue #64: Plan deliverables complete; independent Review pending.
- Branch: `task/28-bootstrap-boundary`.
- Base `main`: `081ba0d0882e9c02906a3f6a4081f77d2907e897`.
- Revised Plan baseline:
  `1f328747069891407668434728c5436d421faa17`.
- No production or golden-record changes.
- No PR opened. Publication follows independent Review.

## Deliverables

- `docs/bootstrap.md`: four-route operation matrix, semantics of the
  statuses, host-service inventory and reproducible trace description.
- `tests/test_bootstrap_boundary.py`: matrix, lowering, rejection,
  interpreter-trap and inventory acceptance tests.
- `tests/lanes.py`: one added `cross-boundary` test registration.
- `CHANGES.md`: Plan and review-correction history.

Task 28's deliverables require no production implementation.

## Verified CI

The revised Plan passed the ordinary CI suite and golden comparison:

https://github.com/NadOby/shear/actions/runs/37936673375

This run tested baseline `1f328747`. The full deterministic suite
can also run locally as documented in `CLAUDE.md`; mutation campaigns
have separate CI execution requirements.

## Boundary and limitations

The SHEAR VM's operation classification is instruction-level.
`unquote` is S there because its host-lowered `GOTO` instruction is
implemented, not because complete quote/unquote execution works.

SHEAR lowering explicitly fails for its deferred operations.
Its generic error chunk does not distinguish deferred operations
from `invalid`.

The VM's `CALL`, and `APPLY`/`APPLYV` on references, can delegate
to installed host-executed code. Existing rebuilds also involve
host-lowered program wrappers. Complete transitive execution
provenance remains a task-30 requirement.

The host inventory distinguishes proposed D4 allowances from a
reviewer's reported observations of two rebuild generations.
The trace recorded 16 host-lowered `code` nodes and four `linksof`
nodes. `docs/bootstrap.md` explains how to reproduce the lowering
trace; the observations are not a committed trace artifact.

D3 and D4 remain open. `docs/roadmap.md`, under "Pending decisions",
is authoritative.

## Remaining nonblocking review observations

- The declared missing-instruction set is checked for disjointness
  and subset membership, but not exact equality against host-lowered
  instructions outside `vm._ORDER`.
- Test chunk expansion duplicates existing expansion logic, limiting
  its independence as an oracle.
- The changelog contains intermediate Plan-review narrative and an
  overbroad historical host-fallback claim. Publish should consolidate
  it into one accurate task-result entry.

These are recorded limitations, not claims of completed corrections.

## Next

Conduct independent Review against Plan baseline `1f328747`.
Verify the matrix, inventory, CI evidence, review corrections and
accepted limitations.

Return any newly verified Plan-owned defect to Plan or Resolve.
After acceptance, Publish consolidates `CHANGES.md`, opens the PR
against `main`, and handles issue #64 closure through merging.

Do not begin task 29 or change D3/D4 within task 28.
