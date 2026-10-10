# Handoff

Read `CLAUDE.md`, `docs/roadmap.md` and the relevant specifications before continuing. Independently verify this checkpoint against GitHub.

## Current state

- Task: 30 – Hosted-bootstrap pipeline.
- Issue: #66.
- Branch: `task/30-hosted-bootstrap`.
- Role: Plan complete; next role is Execute in a fresh chat.
- Main baseline at Plan start: `c1a4596ff555b1f3483b93398a3e8f73fd89bffa`.
- **Protected Plan contract head:** `2f2081b866ca2d686a4cabed3fa4a05a48a31789`.
- The subsequent handoff-only commit does not alter the protected specification or acceptance tests.
- Execute starts from the task branch HEAD, including this handoff.
- GitHub access for the planning assistant was read-only. Owner committed each supplied file through GitHub and each commit was independently checked.

The authoritative Plan specification is `docs/hosted_pipeline.md`. This handoff is a checkpoint, not an independent source of architectural authority.

## Settled architecture

D3 and D4 in `docs/roadmap.md` are Decided and remain authoritative. Issue #66 retains older full-workload assumptions; D4 supersedes them.

Eight Task 30 Plan decisions were settled with the owner:

1. **Unified compiler:** One SHEAR-authored lowering implementation shared by expanded-chunk and node-aware paths. Split across multiple files where useful. No parallel independent compiler algorithms.
2. **Corpus:** All 20 declared non-evolution examples, with every original scenario, expected exception and cell assertion. No positive-only filtering.
3. **Error operations:** Implement `catch` and `raise` on route B in Task 30, while preserving the dedicated error canaries for Task 31.
4. **Generations:** Shared pinned canonical compiler source, separate derived artifact generations. Host orchestration selects generations without replacing source.
5. **Node descriptors:** Host-provided immutable, version-pinned semantic descriptors. No new program-visible node reflection API. This boundary remains replaceable and is technical debt.
6. **Seed:** Closed, finite, deterministic manifest of the host-lowered generation-0 SHEAR compiler and all transitive code dependencies. No implicit expansion.
7. **Invalidation:** Conservative, fail-closed invalidation. Full dependency-safe reuse across live activation belongs to Task 31.
8. **Metaprogramming:** Defer `quote`, `unquote`, `function`, `activate` and `trial` compiler support unless a concrete Task 30 dependency requires it. Return material scope changes to Plan.

D4 permits explicitly contracted, replaceable host semantic services and fixed host execution machinery. It forbids Python from synthesizing instructions attributed to SHEAR compilation, arbitrary program-visible bytecode installation and unobserved host-lowering fallback.

## Protected Plan-owned files

All are present as of the protected Plan contract head:

- `docs/hosted_pipeline.md` – exact workload, compiler architecture, seed, generations, route-B admission, artifact invalidation, diagnostics, exclusions and independent Review criteria.
- `tests/test_hosted_corpus.py` – full existing corpus scenarios, source preservation and admitted execution trace.
- `tests/test_hosted_pipeline.py` – generations 1–3, seed, admission, source-text command and error operators.
- `tests/test_hosted_safety.py` – dependency invalidation, link rebinding, host-cache isolation and failure provenance.
- `tests/lanes.py` – all three modules registered in `cross-boundary`; otherwise restored to the main baseline.

These files are the protected Plan contract. Execute must not weaken their assertions, change expectations to accommodate implementation, silently skip scenarios or amend the specification to rationalize different behavior.

No golden-record changes are declared or expected. Do not create `tests/golden_changes/GH-66.txt` unless a new Plan pass explicitly authorizes particular changed records.

## Test baseline and verification

The Plan tests deliberately import `shear.hosted_bootstrap`, which is absent before implementation. Consequently the branch's ordinary test suite and cross-boundary CI lane are expected to be red until Execute supplies the hosted interface.

Do not treat that absence as a reason to skip the tests, substitute `lang.run`, or make CI report false success.

The provisional test-facing contract includes:

- `HostedSession(runtime)`, `prepare(compiler_generation=...)`, `run`, `trace`, `produce`, `admit`, `rebuild_through`, and `seed_manifest`.
- `AdmissionRejected`.
- Observable generation reports, artifact producer provenance, admitted-execution events and finite seed membership.
- A reproducible source-text command through `python3 -m shear.hosted_bootstrap`.

Implementation may split these responsibilities internally, but it must satisfy the behavioral and observable contract. Any genuine contradiction in Plan-owned tests must return to Plan rather than be silently edited by Execute.

No local implementation tests or successful CI runs are claimed for the unimplemented pipeline.

## Execute contract

Implement in this order where practical:

1. Unify actual SHEAR compiler lowering for expanded output and per-node IR, preserving existing `lower(e)` behavior.
2. Supply pinned compiler descriptors and the deterministic finite G0 seed inventory.
3. Integrate per-runtime route-B production, admission and artifact lookup without Task 29's process-global interception.
4. Enforce provenance transitively through static calls, indirect calls, closures and child evaluation. Missing or incompatible artifacts must fail closed.
5. Build and execute genuine compiler generations G1, G2 and G3, each produced by its predecessor, against unchanged canonical source.
6. Implement the required non-evolution operations, including `catch` and `raise`; run all 20 selected corpus examples through the admitted route.
7. Implement conservative dependency-safe invalidation and the documented text-to-execution command, including a reconciliation/edit path.
8. Validate all Plan-owned tests and existing reference-route tests; provide operation/service inventories, independent comparison evidence, performance diagnostics and the mutation-catalog disposition.
9. Append the Task 30 architectural entry to `CHANGES.md`. Keep historical Task 23/29 evidence unchanged.

The production integration must remove, replace or explicitly promote `shear/execution_route_spike.py`, including its experimental test dependencies and temporary mutation-catalog omission.

Host lowering is permitted for the manifest-closed seed and as an independent test oracle. It must not be a hidden fallback or part of route-B admission.

The compiler generations must be observed executions, not merely structurally identical artifacts with changed labels or reused producer evidence.

## Performance evidence

D4's provisional targets are diagnostic, not acceptance gates:

- At most 10 seconds per compiler generation, aspiration 1 second.
- At most 50 ms from small edit through preparation, admitted compilation and activation, aspiration 10 ms.

Measure named hardware, initialization, production, admission, execution, verification, cold/warm conditions and repeated untraced observations separately.

Preserve Task 29's falsified 179.126317-times cold-cost observation. Revalidate route B on Task 30's actual workload before making performance or architecture claims. Different route-A and route-B workloads must not be compared as equivalent.

## Task 31 exclusions

Issue #67 retains program-driven code construction, trial and activation; remaining metaprogramming operators; self-modification and dedicated error canaries; sustained live updates; held frames or closures across activation; cross-activation artifact reuse; and version retirement.

Host-orchestrated G1–G3 generation changes do not establish live evolution.

No full SHEAR-written VM parity, native execution or Python removal is required by Task 30.

## Independent Review contract

Review Task 30 in a fresh context, separate from Execute.

1. Fetch current main and task branch and verify the recorded protected Plan head.
2. Diff Execute HEAD against `2f2081b866ca2d686a4cabed3fa4a05a48a31789` over all Plan-owned specification and test files and golden declarations. Explain every change; unexplained weakening is blocking.
3. Independently verify exact corpus coverage, expected failures and cell behavior, compiler-generation ancestry, unchanged canonical source and complete transitively observed artifact provenance.
4. Audit every path able to perform host lowering or retrieve an executable chunk, especially indirect calls, closures, error handlers and caches.
5. Verify finite seed closure, adversarial admission tests, dependency invalidation, absence of process-global runtime interception and the independent correctness oracle.
6. Check the command path, operation and service inventories, actual measurements, mutation-catalog treatment, golden records, full ordinary tests and CI.
7. Distinguish verified defects from limitations, hypotheses and documentation drift; classify defect severity.

Execute cannot independently certify its own implementation. Resolve handles Review findings; Publish follows only after independent Review acceptance.

## Next action

Start a fresh chat with **Execute Task 30 (#66)**.

Fetch current main and this task branch. Read `CLAUDE.md`, `docs/roadmap.md`, `docs/hosted_pipeline.md`, the protected acceptance tests, `handoff.md`, D3/D4 and the relevant historical evidence.

Use the protected Plan head above. Implement without changing settled semantics or weakening tests. If a material Plan assumption fails, return to Plan.

For mobile, read-only GitHub work: provide complete file replacements, clickable GitHub edit links and copyable `GH-66` commit messages, one commit at a time. Verify every user-made commit before continuing.
