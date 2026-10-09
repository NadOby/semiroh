# Handoff

Compact checkpoint for the next chat. Verify claims against the
repository. Read `CLAUDE.md` and `docs/roadmap.md` first.

## State

- Task 28, issue #64: revised Plan complete; CI verification pending.
- Branch: `task/28-bootstrap-boundary`.
- Base `main`: `081ba0d0882e9c02906a3f6a4081f77d2907e897`.
- Revised Plan baseline:
  `6cb59dd1565f58aaad5f182d98475385fced6579`.
- Original Plan baseline: `265bb6c`; superseded after review.
- No production-code or golden-record changes.
- No PR opened. No green CI result independently verified.

## Deliverables

- `docs/bootstrap.md`: operation support matrix across host lowering,
  host execution, SHEAR lowering and SHEAR-VM execution.
- `docs/bootstrap.md`: host-service inventory with contracts,
  implementations, proposed allowances, reported rebuild observations
  and existing verification references.
- `tests/test_bootstrap_boundary.py`: Plan-owned acceptance tests.
- `tests/lanes.py`: registration in the `cross-boundary` lane.
- `CHANGES.md`: initial Plan entry and review corrections.

Task 28's specified deliverables are documentation and acceptance
tests. No production implementation is required to complete this task.

## Plan review and corrections

An external review of the original Plan found:

- P1: noncanonical status markers failed `test_docs`.
- P2: acceptance criteria claimed checks the tests did not perform.
- P3: a host-lowering mock was not an effective provenance guard.
- P3: `unquote` support needed an explicit instruction-level definition.
- D4 limitation: observed and proposed host services were conflated;
  ownership and host-lowered program wrappers needed recording.
- P3: D3/D4 were restated inconsistently with the roadmap.
- P3: an unrelated variable-name change entered `tests/lanes.py`.

The revised Plan addresses these findings in its specification,
tests, lane registration and changelog. Those changes have been
committed but not independently certified by CI or final Review.

## Accepted scope and limitations

The matrix distinguishes supported, rejected and deferred operations.
Supported entries follow the current dispatch implementations.

SHEAR lowering cannot compile `quote`, `unquote`, `function`,
`activate`, `trial`, `catch` or `raise`. Deferred lowering currently
produces a generic explicit failure.

The SHEAR VM understands the `GOTO` instruction produced by host
lowering of `unquote`, but cannot execute a complete valid
quote/unquote expression. Its support classification is at the
instruction level.

Interpreter `CALL`, and `APPLY`/`APPLYV` on references, can invoke
installed host-executed functions. The current rebuild also involves
host-lowered program wrappers. Task 28 does not prove an entirely
SHEAR-compiled execution path.

The tests check matrix completeness, dispatch and lowering behavior,
explicit failure results, VM traps, specific invalid-code diagnostics,
and inventory structure. They do not verify complete transitive
producer provenance or every implementation reference.

The existing task-27 tests provide a narrower provenance check for
retained compiler source twins. Task 30 owns full pipeline provenance.

## Decisions

- D3 remains open: execution route for compiler-produced chunks,
  addressed by task 29.
- D4 remains open: hosted-bootstrap workload, host-service boundary,
  and rebuild-time and edit-to-activation budgets.
- `docs/roadmap.md` is authoritative for both decisions.
- Task 28 does not change language semantics, golden records,
  bytecode admission, or permitted runtime authority.

## Verification and Review

CI is the only execution platform for this workflow. Confirm that the
current branch's checks pass before treating the Plan as validated.
The earlier review reported ten passing new tests but a failing
`cross-boundary` lane on the original specification; those results
do not establish that the revised Plan passes.

An independent Review should:

- Recheck every matrix row against implementation behavior.
- Verify the status-marker fix and all CI results.
- Check the revised tests against the exact claims in section 4.
- Inspect the `invalid` and `unquote` exceptions.
- Confirm that host-execution delegation is documented accurately.
- Check the observed-versus-proposed host-service distinction.
- Ensure `tests/lanes.py` changes only lane membership.
- Verify no production or golden-record changes were introduced.

Use `6cb59dd1565f58aaad5f182d98475385fced6579`
as the revised Plan baseline. This handoff update changes only
the checkpoint and does not supersede that baseline.

## Next

Verify CI for the current branch. Start independent Review task 28
in a fresh chat, using the revised Plan baseline.

If Review finds a Plan-owned defect, return it to Plan rather than
silently changing acceptance criteria.

After acceptance, Publish can open the PR against `main`.
Do not open a PR solely to start an unnecessary Execute phase.

Issue #64 remains open until publication is completed.
