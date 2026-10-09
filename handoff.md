# Handoff

Read `CLAUDE.md`, the Workflow and task 29 sections of `docs/roadmap.md`, and `docs/spikes/execution_route.md`. Verify all claims against GitHub; this checkpoint is not evidence by itself.

## State

- Task: 29, execution-route spike, issue #65.
- Role: Execute complete; independent Review next.
- Branch: `task/29-execution-route`.
- Last verified implementation/evidence head: `9754d9a820dd7d1c0c4a6f4f6507991ff3aeacf0`. Fetch the current branch head before Review.
- Base `main` at Plan: `dbe92c6e6450db479d22a203011f9c974ba00089`.
- Protected Plan baseline: `deb03aa3ffc198df8e19fa14da59db904f879a1b`.
- D3 and D4: Open. No permanent execution-route or language decision.
- No PR. No golden changes. No changes to Plan-owned acceptance tests.

## Plan integrity

The protected Plan established the contract in:

- `docs/spikes/execution_route.md` – sections 1–10, predictions and role gates.
- `tests/test_execution_route.py` – 18 behavioral acceptance tests.
- `tests/lanes.py` – registration under `cross-boundary`.
- `tests/mutation_catalog.py` – explicit temporary omission of the spike module.

Execute changed only section 11 of the spike specification. The acceptance tests, lane assignment and mutation-catalog omission remain unchanged from the protected Plan baseline.

The current branch also includes the final Plan-to-Execute handoff commit following that baseline. Review must compare the Plan-owned files against the protected commit, not assume that every post-Plan change is an implementation change.

No `tests/golden_changes/GH-65.txt` is authorized.

## Implementation

The sole new implementation module is `shear/execution_route_spike.py`.

It provides the provisional API:

    produce(runtime, entity) -> (chunk, evidence)
    admit(state, entity, version, chunk, evidence) -> admitted
    run_admitted(runtime, entry, *args) -> result
    trace(runtime) -> tuple[RouteEvent, ...]
    AdmissionRejected

The node-aware compiler is expressed as SHEAR `Function` data, invoked through the ordinary SHEAR runtime. Python supplies a semantic node descriptor, observes the returned artifact and generically decodes canonical values, including typed identifiers.

The supported kinds are `lit`, `arg`, `add` and `call`. The compiler emits per-node host chunks containing child `EntityID` references.

Host admission uses opaque producer evidence, exact output matching, structural checks, node/version/ownership binding and a separate admitted-artifact registry. Execution uses admitted chunks through the existing machine. Missing or invalid artifacts fail without ordinary target-node lowering fallback.

The implementation is experimental. It uses temporary process-global machine-method interception and a lock. It is not a permanent runtime interface or concurrency-safe execution boundary.

The existing route-A compiler and VM are unchanged. The existing GitHub Actions workflow was extended with a manual `execution_route_spike` diagnostic input and artifact-upload job.

## Verified CI evidence

- Revision tested: `6ebbc698c881528b53b37c63b5b090f82eb4a037`.
- Workflow run: https://github.com/NadOby/shear/actions/runs/37981959588
- Tests job: https://github.com/NadOby/shear/actions/runs/37981959588/job/113994433438
- Diagnostic job: https://github.com/NadOby/shear/actions/runs/37981959588/job/113994434005
- Evidence artifact: https://github.com/NadOby/shear/actions/runs/37981959588/artifacts/11641073831
- Runner: `GitHub Actions 1000008691`.
- Python: 3.12.15; Linux 6.17.0-1022-azure, x86-64, glibc 2.39; four reported CPU cores.

Every ordinary test lane passed, including all 18 Plan-owned execution-route tests. Golden comparison: 55 unchanged records, zero failures. The explicitly dispatched diagnostic completed and uploaded `execution-route.json`.

The mutation campaign was not run. The spike retains its Plan-authorized temporary mutation-catalog omission.

The results document was committed after this CI run; no separate post-documentation CI run is claimed.

## Results and predictions

Full results, workloads, observations, inventories, caveats and recommendation are in `docs/spikes/execution_route.md` section 11.

W0:

- Route A reproduced compiler rebuild generations 1, 2 and 3. Median swap times: 0.204083 s, 7.415722 s and 7.465605 s.
- Route A still replaces active compiler definitions with literal-chunk wrappers; retained source twins do not repair canonical-source preservation.
- Route B produced, admitted and executed authentic per-node artifacts, including a linked caller and callee, without changing semantic source.
- The route-B linked-call witness returned `7` for `x = 4`. Its chunks agreed with the independent host lowering oracle for all four supported node kinds.
- Route-B compiler rebuilding reached generation 0 only. Its attempt stopped on unsupported `swap_all/0.0`. No route-B rebuild timing exists.
- A bounded wrapper-free route-A design was recorded, not implemented.

P1, P2, P3 and P5 were supported within their stated evidence boundaries.

P4 was falsified. For the equivalent cold witness:

    median(T_B) = 9.873980 ms
    median(T_H) = 0.055123 ms
    median(T_B) / median(T_H) = 179.126317

The fixed prediction required a ratio at most 10. No experimental revision was made to the prediction or workload.

Separate median warm execution times were 0.639887 ms for B and 0.022001 ms for the host reference.

One small edit changed `target(x)` from `x + 3` to `x + 5`. Preparation, candidate production/admission/verification and activation totaled 25.010713 ms; the result changed from `7` to `9`. This is one observation and includes candidate verification execution.

W1 and W2 are inventories only. They identify corpus, instruction, indirect-call, reflection, cell, error, activation, continuity, closure and lifetime gaps. No complete corpus execution or live evolution through route B is claimed.

## Known limitations

- Route B covers four node kinds and one narrow linked-call workload, not the complete compiler or corpus.
- Admission establishes origin and structural compatibility, not semantic correctness for arbitrary programs.
- Trace completeness is demonstrated for the tested witness, not the entire transitive hosted pipeline.
- The experimental registry, compiler lifetime, dependency invalidation and process-global machine interception require replacement or redesign.
- Performance is materially worse than the fixed P4 bound, particularly because cold production initializes a separate SHEAR compiler runtime.
- The route-A wrapper-free alternative has not been executed or measured.
- The Task 29 diagnostic did not record a processor model; Task 23's separate hardware baseline must not be silently substituted.
- The temporary spike module is intentionally omitted from mutation campaigns. Task 30 must remove, replace or explicitly promote it with an accompanying mutation-testing decision.

These limitations are disclosed results, not declarations that independent Review must accept them.

## Independent Review

Review must be performed in a fresh, separate context with read-only access. Fetch the actual branch head, inspect the implementation and compare protected Plan files against `deb03aa3ffc198df8e19fa14da59db904f879a1b`.

Independently verify:

1. The compiler genuinely executes as SHEAR code and Python does not synthesize target instructions.
2. Evidence cannot be forged through SHEAR data or ordinary Python values, and authentic evidence cannot authorize an altered or foreign artifact.
3. Structural admission validates ownership, references, opcode shapes and state/version binding without secretly invoking host lowering.
4. The linked call executes every required admitted node without ordinary cached-chunk or lowering fallback.
5. Source preservation, invalidation and held-version behavior are supported only to the extent claimed.
6. Production, admission and execution traces correspond to actual operations and match artifact identities.
7. Differential correctness, negative admission tests and mutation-catalog handling satisfy the protected Plan.
8. W0, W1, W2, P1–P5, timings, workload equivalence, CI provenance and costly-to-change analysis are reported accurately.
9. No Plan-owned tests were weakened, no unapproved golden change occurred and no unrelated repository behavior was modified.

Classify findings as verified defects (P0–P3), limitations, hypotheses or documentation drift. Resolve verified defects in a separate Resolve role; rerun independent Review afterward.

## Decision and Publish boundary

The recorded recommendation conditionally favors route B for Task 30 because of source preservation, per-node identity and authenticated execution. It does not disregard the P4 failure, incomplete compiler coverage or temporary host interception.

This is a recommendation, not the owner's D3 decision. D3 and D4 remain Open. The instruction set, the semantic version observed by `code` and the representation of node identities in compiler output remain Provisional.

No PR is authorized before accepted independent Review and the necessary owner decision. Publish must recheck current `main`, the final diff, Plan integrity, CI and any Review findings. It then prepares the PR closing #65 and records any required follow-up issues.

## Next

Start `Review task 29` in a fresh chat.

Follow the owner's mobile GitHub protocol for any later editing: read-only GitHub access for the assistant, one complete file per commit, copyable commit messages, clickable branch-specific edit links, manual owner commits, `Done` confirmation and independent verification. No terminal dependency.
