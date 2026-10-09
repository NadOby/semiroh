# Handoff

Compact checkpoint for the next chat. Verify claims against the
repository. Read `CLAUDE.md` and `docs/roadmap.md` first.

## State

- Task 28, issue #64: Plan recorded; CI verification pending.
- Branch: `task/28-bootstrap-boundary`.
- Base `main`: `081ba0d0882e9c02906a3f6a4081f77d2907e897`.
- Plan-owned specification and test baseline:
  `265bb6cdfac988d0363fffcadf572ce2558ad13c`.
- Subsequent handoff commits change only this checkpoint.
- No production code or golden-record changes.
- No CI success is claimed.

## Plan contract

`docs/bootstrap.md` defines the four-route support matrix and the
proposed host-service inventory. `tests/test_bootstrap_boundary.py`
contains the Plan-owned acceptance tests, registered in the
`cross-boundary` lane by `tests/lanes.py`.

The matrix distinguishes supported, rejected and deferred operations.
Supported routes are grounded in implementation dispatch. Deferred
routes must fail explicitly rather than silently use host compilation
or execution.

The `unquote` exception matters: its host-lowered `GOTO` instruction
is understood by the SHEAR VM, but the SHEAR compiler does not lower
`unquote`. Interpreter `CALL` may delegate to host-compiled linked
functions. Neither property proves an end-to-end host-independent
pipeline.

The host inventory separates existing services from prospective
task-30 needs, and permitted runtime services from compiler fallback.
Python remains the hosted execution substrate.

## Execution boundaries

- Validate the acceptance tests through GitHub CI. Do not claim
  validation from source inspection alone.
- If an acceptance test is incorrect or contradicts the implementation,
  return the discrepancy to Plan before changing that test.
- Preserve the existing semantic graph, identity, continuity,
  activation, runtime-cell and derived-bytecode contracts.
- Retain explicit failures for deferred operations and for interpreter
  instructions outside its supported subset.
- Ensure unsupported routes never silently invoke a host implementation.
- Preserve task-27 rebuild provenance checks for compiler source twins
  in generations 2 and 3.
- Do not change golden records or production semantics for task 28.
- Do not implement task 29, task 30 or task 31 in this change.

## Open decisions

- D3: execution by the SHEAR VM versus verified host execution of
  compiler-produced chunks. Task 29 must supply evidence and define
  any non-forgeable admission rule.
- D4: final bootstrap workload, permitted host services and measured
  budget. Owner approval is required before fixing this boundary.
- Whether VM support means an individual instruction or complete
  transitive execution must remain explicit; this Plan uses the
  instruction-level meaning.
- Generic `RAISE "unknown operation"` for deferred SHEAR lowering is
  recorded current behavior, not an approved final diagnostic design.

## Review targets

Independently verify every matrix row against implementation, the
status of `invalid`, the `unquote` exception, the unsupported-opcode
trap, and whether `CALL` introduces undeclared host execution.

Check that host-fallback guards are sensitive to a plausible
regression and that the service inventory distinguishes observed
calls, proposed allowances and verification evidence.

For Plan-owned specifications and tests, compare Execute's head with
the Plan baseline `265bb6cdfac988d0363fffcadf572ce2558ad13c`.
Any later change requires explicit justification and Plan approval
where it changes acceptance semantics.

## Next

Start Execute task 28 in a separate fresh chat, using this branch
and the recorded Plan baseline.

Verify the implementation through CI. Open the PR against `main`
after Execute is complete. Independent Review follows the
implementation and CI verification.

Do not claim Task 28 implemented or issue #64 complete on the basis
of this Plan alone.
