
# Handoff

Read `CLAUDE.md`, the Workflow and task 29 sections of `docs/roadmap.md`, and `docs/spikes/execution_route.md`. Independently verify repository claims rather than treating this checkpoint as evidence.

## Current state

- Task: 29, execution-route spike, issue #65.
- Role: Publish, following accepted independent Review and the owner's D3 decision.
- Branch: `task/29-execution-route`.
- Last checked branch head: `71e046e2ff2a84b90b503f5957c39b134659a33f`.
- Last checked `main`: `dbe92c6e6450db479d22a203011f9c974ba00089`.
- Branch is ahead of `main`, not behind it.
- Protected Plan baseline: `deb03aa3ffc198df8e19fa14da59db904f879a1b`.
- Tested Execute revision: `6ebbc698c881528b53b37c63b5b090f82eb4a037`.
- Final documentation Resolve commits: `9508ec1989e3d7296e3f6967bd3b4a2ce85de2bb` and `cc4d6df5382d73023e9c37e3496ddc18cce3fb8a`.
- Final pre-Publish handoff commit: `71e046e2ff2a84b90b503f5957c39b134659a33f`.
- The owner reports that the final independent Review accepted the corrected state, with no further Resolve required.
- No PR has been opened for task 29.

## Owner decision – D3

**Decided:** Use a hybrid execution architecture.

1. The primary hosted execution route is B: the existing host machine executes authenticated, SHEAR-compiled per-node derived artifacts with provenance and a fail-closed admission boundary.
2. Retain the SHEAR-written VM as an alternative implementation, independent correctness reference and possible bootstrap component.
3. This selects an architecture, not the experimental route-B implementation or its performance.
4. The semantic hypergraph remains canonical. Executable representations are derived artifacts and never replace the semantic definitions.
5. The current Python executor, bytecode encoding, verifier, artifact cache and hashing algorithms are replaceable implementation choices. Changes must preserve semantics, required integrity properties, identities, provenance, activation and version-lifetime contracts.
6. Preserve the possibility of runtime coexistence and live replacement of implementations. No particular migration mechanism is decided by D3.

**Long-term direction, not task-30 scope:** Native execution on Linux using LLVM as the initial machine-code producer. The SHEAR VM may itself be compiled to native code. A custom MLIR dialect is optional, not selected. Native compilation and removal of Python remain later milestones.

**Open:** D4, the hosted-bootstrap workload and permitted host boundary, must be settled before task 30 planning. Instruction-set/IR conventions, the semantic version observed by `code`, and node identities exposed by compiler output remain provisional or open. No additional language semantics are decided here.

## Verified Task 29 evidence

The Plan contract is `docs/spikes/execution_route.md` sections 1–10, with 18 Plan-owned behavioral acceptance tests in `tests/test_execution_route.py`. The Plan-owned test expectations, lane registration and mutation-catalog omission were preserved through Execute and Resolve.

The complete experimental report and its caveats are in section 11 of the spike specification. Its pre-decision recommendation and the Plan's owner-decision gate are historical evidence, not a reversal of the subsequent owner decision recorded above.

Route A completed compiler rebuild generations 1, 2 and 3, with median swap times of 0.204083 s, 7.415722 s and 7.465605 s. The implemented route still installs literal-chunk wrappers instead of preserving active canonical source. Its wrapper-free alternative was proposed, not implemented. Route A did not execute the route-B linked-call witness.

Route B demonstrated authentic SHEAR compilation, admission and host execution of per-node artifacts for `lit`, `arg`, `add` and `call`. Its linked-call witness returned `7`, as did ordinary host execution. This does not demonstrate full operation coverage or a compiler rebuild: the attempted route-B rebuild stopped at generation 0 on unsupported `swap_all/0.0`.

The prespecified P4 performance prediction failed:

- Cold route B median: 9.873980 ms.
- Cold ordinary host median: 0.055123 ms.
- Cold ratio: 179.126317, against the predicted maximum of 10.
- Warm route B execution median: 0.639887 ms.
- Warm ordinary host execution median: 0.022001 ms.

The dominant measured cold production component includes compiler-runtime initialization and compilation, but the diagnostic did not measure those subcomponents separately. No optimization benefit has yet been demonstrated. The Route A rebuild and Route B linked-call timings are different workloads and are not directly comparable.

A small edit was compiled, admitted and executed in a separate candidate runtime, returning `9`. After activation, the original runtime returned `9` through ordinary host execution, not admitted execution. Cross-activation artifact transfer and unchanged-node reuse were not demonstrated.

## Verification

Evidence from the tested Execute revision:

- CI: https://github.com/NadOby/shear/actions/runs/37981959588
- All ordinary test lanes passed, including the 18 Plan-owned tests.
- Golden comparison: 55 unchanged records, no failures.
- Diagnostic job passed and uploaded `execution-route.json`.
- The mutation campaign was not run; the spike module retains its Plan-authorized temporary catalog omission.

The two Resolve commits changed documentation only, correcting result attribution, cost interpretation, activation attribution, verifier-maintenance caveats and the linked-call comparison wording. No new benchmark result is claimed for Resolve.

Publish must independently recheck the current diff, protected Plan files and applicable CI. The owner's report of independent Review acceptance is a disposition, not a substitute for these checks.

## Remaining limitations and follow-ups

Route B remains a bounded experimental implementation, not a deployable runtime:

- Only four node kinds are supported.
- Compiler rebuilding and the full corpus cannot yet use admitted execution.
- Admission checks origin and structure, not semantic correctness.
- The verifier uses per-kind opcode templates, with a substantial maintenance cost.
- Execution uses temporary process-global method interception, not a concurrency-safe integrated machine boundary.
- The registry is runtime-local and exact-state-bound, preventing reuse across changed states.
- Persistent artifact storage, dependency invalidation, activation transfer, hold-aware retirement and complete transitive provenance remain unresolved.
- P4 failed substantially and must be remeasured after integration without rewriting its original result.

Task 30, issue #66, must remove, replace or explicitly promote `shear/execution_route_spike.py`. In particular, its diagnostic currently imports `tests.test_execution_route`, and the module uses `unittest.mock`; promotion requires eliminating test-infrastructure dependencies and deciding mutation-test coverage explicitly.

Task 30 owns the integrated hosted execution pipeline and workload coverage after D4. Task 31, issue #67, owns the remaining live-evolution acceptance path. These existing task issues cover the identified follow-up work; none of these limitations is represented as already resolved.

## Publish sequence

1. Record D3 in the authoritative roadmap without changing the protected Plan acceptance contract.
2. Preserve the historical Task 29 spike measurements and accepted Review result.
3. Add one accurate Task 29 entry to `CHANGES.md`.
4. Recheck the final branch against `main`, the protected Plan baseline, CI and the accepted Review state.
5. Open a ready PR closing #65, with the measured failure and deferred Task 30–31 work disclosed separately.
6. Mark Task 29 Implemented with its PR number and update this checkpoint.

GitHub access is read-only for the assistant. The owner edits from mobile: one complete file, one commit, followed by independent verification before the next file. Do not claim publication or merge before checking GitHub.
