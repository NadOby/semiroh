# Handoff

Read `CLAUDE.md` and `docs/roadmap.md` first. Verify this checkpoint against the repository. It is not verification evidence.

## State

- Task 29, issue #65: Plan complete; Execute next.
- Branch: `task/29-execution-route`.
- Base `main`: `dbe92c6e6450db479d22a203011f9c974ba00089`.
- Plan-owned baseline: `56c4cf8033a43c192bad250748f10990fd01d926`.
- The final Plan handoff commit follows that baseline. Execute must fetch and verify the actual branch head.
- D3 and D4 remain Open. Neither is decided by Plan.
- No production changes, intended golden-record changes or PR.

## Plan-owned files

- `docs/spikes/execution_route.md`: alternatives A and B, workload W0–W2, predictions P1–P5, acceptance criteria A1–A11, decision gates G1–G6, measurement contract and role boundaries.
- `tests/test_execution_route.py`: source-preservation witnesses and evidence-report acceptance checks.
- `tests/lanes.py`: `test_execution_route` registered in `cross-boundary`.
- No `tests/golden_changes/GH-65.txt` is required; no golden changes are authorized.

These files form the protected Plan baseline for independent Review. Any material correction to the specification or its acceptance tests returns to Plan.

## Execution contract

Compare:
- A: SHEAR-VM execution, including a bounded source-preserving alternative to wrappers.
- B: verified host execution of SHEAR-compiled per-node derived artifacts.

Preserve canonical semantic graph code, node/version identity, held-version behavior, candidate/activation separation, existing failure semantics and continuity.

Use the provisional D4 workload:
- W0: compiler generations 1–3.
- W1: ordinary corpus and error behavior.
- W2: live-evolution probe.

Record missing operation and service coverage explicitly. Tasks 30 and 31 own completion of the hosted pipeline and live-evolution milestone.

For B, establish genuine SHEAR compiler origin, trusted non-forgeable producer assertions, structural and semantic admission, correct cache identity and invalidation, and rejection of forged, stale, wrong-node or malformed artifacts. Host lowering is a differential oracle, not an admission mechanism.

For A, demonstrate whether execution can keep active semantic function bodies canonical without relying on wrappers, and identify every transitive host fallback.

Add executable behavioral and adversarial tests for the selected experiments. The Plan-owned evidence-report tests are not substitutes for implementation tests.

Record predictions before running the experiments; only one documented experimental revision is allowed. Escalate architectural changes and Decided-semantics changes rather than deciding them in Execute.

## Evidence and CI

- Append `## 7. Task 29 execution-route evidence` to `docs/bootstrap.md`.
- Record all 22 evidence IDs: A1–A11, P1–P5, A-W0 through A-W2 and B-W0 through B-W2.
- Table columns: ID, Status, Proof, Finding.
- Acceptance/workload statuses: pass, fail, blocked.
- Prediction statuses: confirmed, falsified, inconclusive.
- Each passing acceptance/workload result requires a GitHub Actions run link. Identify concrete blockers.
- At least one route must demonstrate W0.
- Collect timings and memory using `docs/content_baseline.md` section 3; identify runner, commit, inputs and cache conditions.
- Compare only equivalent coverage. Preserve explicit negative results.
- Expected initial red tests: evidence-report checks until Execute records results.
- No successful test run has yet been verified for this Plan.

The report must give a recommendation, not enact D3. If D4 differs materially from the provisional workload, the comparison needs revision before D3 acceptance.

## Independent Review

Review must fetch current git state and compare the implementation head against the protected Plan baseline. Inspect all changes to tests, specifications and golden declarations.

Verify independently:
- Genuine compiler producer provenance and absence of undeclared host lowering.
- Semantic verification, negative admission tests and non-forgeable assertions.
- Source preservation and transitive call coverage.
- Workload parity, blocked paths and behavioral expectations.
- CI evidence, measurement methods and pre-recorded predictions.
- Preservation of Decided semantics.

Classify findings as verified defects, limitations, hypotheses or documentation drift. Review does not modify production code. Resolve handles verified defects, followed by another independent Review.

## Publish boundary

Do not open a PR before Publish and an accepted independent Review. D3 requires the owner's decision. Publish verifies main, final diff, CI and Plan-owned file integrity, then opens a PR closing #65.

Defer nonblocking follow-ups separately, using `follow-up` issues where needed.

## Next

Start `Execute task 29` in a fresh chat after verifying this handoff commit. Use GitHub Actions for execution. Do not assume GitHub write access or ask the owner to run local commands.
