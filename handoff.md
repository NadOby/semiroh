# Handoff

Read `CLAUDE.md` and `docs/roadmap.md` first. Verify this checkpoint
against repository state before relying on it.

## State

- Task 28, issue #64: Published as open PR #90, awaiting owner merge.
- Branch: `task/28-bootstrap-boundary`.
- PR: https://github.com/NadOby/shear/pull/90
- Independent Review: accepted, no blocking findings.
- Accepted Plan baseline:
  `1f328747069891407668434728c5436d421faa17`.
- Final substantive Publish update:
  `fbeaa8e3769fbc96cb2230318a490670fa5c175b`.
- Roadmap: Implemented (PR #90).
- PR includes `Closes #64`.
- No production semantics or golden records changed.

## Delivered

- `docs/bootstrap.md`: four-route operation support matrix, host-service
  inventory, reported rebuild observations and reproduction method.
- `tests/test_bootstrap_boundary.py`: acceptance tests for current
  lowering, interpreter dispatch, failure behavior and inventory.
- `tests/lanes.py`: one `cross-boundary` registration.
- `CHANGES.md`: consolidated Task 28 result.
- `docs/roadmap.md`: Task 28 marked Implemented (PR #90).

D3 and D4 remain open for subsequent tasks.

## Verification

- Plan baseline CI passed:
  https://github.com/NadOby/shear/actions/runs/37936673375
- Consolidated Publish CI passed:
  https://github.com/NadOby/shear/actions/runs/37940961244
- Roadmap-update push CI passed:
  https://github.com/NadOby/shear/actions/runs/37942586287

Confirm PR checks for the latest head before merging.
The Plan-owned specification and acceptance tests remained unchanged
during Publish.

## Accepted limitations

- The missing-instruction test checks disjointness and subset membership,
  not exact equality with host-lowered instructions outside the VM.
- The test chunk expander duplicates existing expansion logic.
- The reviewer confirmed two `Runtime.activate` calls, but the documented
  lowering trace alone does not reproduce that activation count.
- Complete transitive execution provenance and prevention of undeclared
  host fallback remain requirements of tasks 29 and 30.
- Rebuild service observations are reviewer-reported evidence, not a
  committed execution trace.

These are nonblocking limitations, not unresolved verified defects.

## Follow-up

Issue #89, labelled `follow-up`, covers the workflow exception for
specification-and-test-only tasks:
https://github.com/NadOby/shear/issues/89

## Next

The owner verifies the latest PR checks, reviews and merges PR #90, or
requests changes.

After merging, verify that PR #90 is merged, issue #64 is closed and
`main` contains the delivered changes. Then select the next roadmap task.

Do not reopen Task 28 without new verified evidence.
