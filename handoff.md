# Handoff

Read `CLAUDE.md` and `docs/roadmap.md` first. Verify every claim in this checkpoint against the repository.

## State

- Task 29, issue #65: Revised Plan prepared following blocking Plan review findings.
- Branch: `task/29-execution-route`.
- Base `main`: `dbe92c6e6450db479d22a203011f9c974ba00089`.
- Revised Plan-owned baseline: `7bda8682af2bfd5fc60e7409b07c9c268ddcd866`.
- This handoff commit follows that baseline. Verify the final branch head before Execute.
- D3 and D4 remain Open. No permanent language or execution-route decision has been made.
- No production-code or golden-record changes. No PR.

## Plan revision

The initial Plan was rejected because it required an independent semantic verifier resembling a second compiler, delegated language-shaping decisions to Execute, tested mostly report formatting and exceeded the scope of a bounded spike.

The revised contract is `docs/spikes/execution_route.md`.

Decisions provisional for this spike only:

- Structural admission plus trusted producer evidence; semantic correctness is assessed by independent expectations and differential tests rather than by recomputing lowering in the verifier.
- A node-aware SHEAR compiler entry producing one per-node chunk, without modifying the existing program-visible `code` operation.
- Producer evidence created and retained by trusted host runtime machinery observing the actual compiler invocation and result.
- No program-visible artifact-admission operation or credential.
- By-value targets for cells and reflection remain blocked. Their capability semantics are not changed.

These provisional experiment interfaces do not resolve D3, D4 or the permanent language-level authority model.

## Protected Plan files

- `docs/spikes/execution_route.md`: revised scope, interfaces, predictions, acceptance tests, measurements and decision gates.
- `tests/test_execution_route.py`: behavioral positive and negative tests against the spike API.
- `tests/lanes.py`: `test_execution_route` registered in `cross-boundary`.
- No golden changes are authorized. No `tests/golden_changes/GH-65.txt` is needed.

Review must compare these files against the revised Plan baseline. The lane-file diff includes the registration and one unrelated blank-line deletion; this is cosmetic, not an intended semantic change.

## Execute scope

The executable comparison is W0:

- Route A: existing SHEAR-VM compiler rebuild across generations 1–3, with its wrapper/source-preservation limitation recorded.
- Route B: a SHEAR-compiled, structurally admitted per-node artifact executed by the host while the semantic source remains unchanged.
- Attempt compiler rebuilding through route B, recording achieved generations and any concrete blocker.
- Prove the actual producer and execution route within the claimed witness. Do not claim complete transitive provenance without tracing it.

W1 (ordinary corpora) and W2 (live evolution) require coverage inventories only. Do not implement their unsupported operations in this task.

For route A, describe one bounded wrapper-free design or give a concrete counterexample. No wrapper-free runtime implementation is required.

## Spike API

Implement the provisional internal module `shear/execution_route_spike.py` with:

    produce(runtime, entity) -> (chunk, evidence)
    admit(state, entity, version, chunk, evidence) -> admitted
    run_admitted(runtime, entry, *args) -> result
    AdmissionRejected

`entity` identifies a semantic code node, and `version` is its `VersionID`. Admitted artifacts stay outside semantic state.

`produce` invokes a genuine SHEAR compiler function consuming a host-provided semantic-node descriptor and emitting a host-format per-node chunk with child `EntityID` references.

Admission must check node existence and version, ownership, supported instruction structure, permitted child/entity references, immutable output binding and authentic host-owned producer evidence. It must reject invalid input without fallback or cache pollution.

Compiler provenance does not prove compiler correctness. The latter remains a differential and behavioral testing obligation.

Do not add an arbitrary program-visible host-bytecode execution primitive. Do not use host lowering to produce or admit the experimental artifact.

## Tests and evidence

The Plan-owned `tests/test_execution_route.py` specifies:

- Genuine per-node production and admission.
- Forged, wrong-node, stale and altered evidence rejection.
- Foreign child and unlinked function operand rejection.
- No host lowering in admission or target production.
- Execution using admitted artifacts instead of host lowering or cached host chunks.
- Preserved active semantic source and node versions.
- Invalidation after an edit.
- No execution fallback after rejection.

The new tests intentionally fail without `shear.execution_route_spike`. Passing CI has not been verified for the revised Plan; the initial red state is expected.

Execute must add implementation-specific tests without weakening the Plan-owned expectations. If the specified API is materially unsuitable, return to Plan.

Evidence and recommendations belong in `docs/spikes/execution_route.md` section 11, not in a duplicate table in `docs/bootstrap.md`.

Use GitHub Actions to verify behavior. Record the exact commit, runner, runtime version, commands, outputs, failures and limitations.

## Predictions and measurements

P1–P5 are fixed in the revised spike specification before execution.

P4 predicts that route B, including admission, stays within 10 times the comparable ordinary host-executed reference time. This is an experimental threshold, not a D4 budget.

Mandatory measurements:

- Rebuild time for each achieved generation.
- Cold production/admission and warm execution timing.
- Small-edit-to-activation latency, separated into phases.

Reuse the corrected Task 23 baseline and measurement methodology. At least three untraced observations are required for comparable timings. Do not compare workloads with different coverage as equivalent.

One recorded experimental revision is allowed. Further material redesign returns to Plan.

## Independent Review

The reviewer must independently verify:

- The accepted Plan baseline and Plan-owned file integrity.
- Genuine SHEAR compiler execution rather than disguised host lowering.
- Structural admission, evidence authenticity and negative witnesses.
- No unauthorized program-visible admission authority.
- Actual use of admitted artifacts without host fallback.
- Source preservation and invalidation.
- Correct characterization of route A and gaps in W1/W2.
- Reproducible measurements, fixed predictions and honest coverage limits.

Classify findings as verified defects, limitations, hypotheses or documentation drift. Resolve verified defects and obtain another independent Review.

## Follow-ups and decisions

Owner decisions remaining Open:

- D3: final compiler-produced-chunk execution route.
- D4: hosted workload, host services and provisional budgets.
- Permanent node-identity exposure, admission authority and by-value capability semantics.

A potential `follow-up` issue is a repository check that prevents unrelated changes to test-lane registration files. No such issue has been created or claimed here.

Tasks 30 and 31 own full hosted-pipeline and live-evolution implementation.

## Publish

Do not open a PR before independent Review accepts the final result and the owner decides D3. Publish must reverify `main`, CI, the accepted Plan baseline and the final diff, then prepare a PR closing #65.

## Next

Start a fresh `Execute task 29` chat after verifying this handoff commit. Use read-only GitHub tools and GitHub Actions; follow the owner's mobile, one-file-per-commit protocol. Do not assume write access or ask the owner to run local commands.
