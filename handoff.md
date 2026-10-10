# Handoff

Read `CLAUDE.md`, `docs/roadmap.md`, and the relevant specifications before continuing. Independently verify this checkpoint against GitHub.

## Current state

- Task: 30 – Hosted-bootstrap pipeline.
- Issue: #66.
- Branch: `task/30-hosted-bootstrap`.
- Role: Revised Plan complete; next role is Execute in a fresh chat.
- Main baseline: `c1a4596ff555b1f3483b93398a3e8f73fd89bffa`.
- Original Plan head: `2f2081b866ca2d686a4cabed3fa4a05a48a31789`.
- **Revised protected Plan head: `94ac037cbcd5e08ed86a3ae6e39c8d20c08f464a`.**
- The subsequent handoff-only commit is not part of the protected specification/test baseline.
- Execute starts from the task branch HEAD, including this handoff.

The authoritative specification is `docs/hosted_pipeline.md`. This handoff records the execution contract; it is not independent architectural authority.

## Settled architecture

D3 and D4 in `docs/roadmap.md` are Decided. The older issue #66 full-workload assumptions are superseded by D4.

The eight owner-approved Task 30 decisions remain unchanged:

1. One SHEAR-authored compiler lowering implementation shared by expanded and node-aware modes.
2. All 20 declared non-evolution corpus examples, including ordinary failures and cell effects.
3. `catch` and `raise` added to Task 30; dedicated error canaries remain Task 31.
4. Three distinct compiler artifact generations, G1–G3, over unchanged canonical compiler source.
5. Immutable, host-provided, version-pinned compiler descriptors; reflection unchanged.
6. Finite, closed, audited G0 compiler seed.
7. Conservative dependency invalidation; cross-activation reuse deferred.
8. `quote`, `unquote`, `function`, `activate` and `trial` lowering deferred unless a concrete Task 30 dependency requires them.

No final textual syntax or filename extension is being selected.

## Independent Plan review and resolution

An independent read-only Plan review at `f220578` reported four P2 acceptance-contract gaps. It accepted the D3/D4 architecture, exact workload, exclusions, unified compiler requirement, admission and invalidation principles, and golden-record policy.

All four findings have been addressed in the revised Plan-owned specification and acceptance tests:

1. **Compiler/target boundary:** The compiler executes from its own pinned canonical compiler source state. Target programs retain separate canonical states and need not contain compiler functions. `compiler_source_state_id` and `target_state_id` have distinct meanings and provenance bindings.
2. **Genuine self-rebuilding:** Acceptance tests independently observe compiler execution through the existing machine boundary, compare G1–G3 artifacts against the host oracle, and invalidate predecessor artifacts to test fail-closed generation dependencies.
3. **Exact seed closure:** Tests independently traverse the compiler source's owned executable nodes and linked compiler functions. Manifest membership must equal that closure; unrelated target nodes and undeclared host lowering are rejected.
4. **Reconciliation command:** An end-to-end edit-mode test checks original and edited source, independent reconciliation, continuity, admitted execution of both states, and preservation of the original active state.

Revision commits:

- `46c8762996d90d76bf00b5db8bfc4c018eb961a3` – specification clarification.
- `94ac037cbcd5e08ed86a3ae6e39c8d20c08f464a` – strengthened acceptance tests.

These are Plan corrections, not production defect fixes. No new owner decision was required.

## Protected Plan-owned files

- `docs/hosted_pipeline.md` – authoritative Task 30 contract, revised after independent review.
- `tests/test_hosted_corpus.py` – entire selected corpus, preserved expectations and admitted execution.
- `tests/test_hosted_pipeline.py` – compiler isolation, exact seed, genuine generation ancestry, admission, error operations and reconciliation command.
- `tests/test_hosted_safety.py` – invalidation, link rebinding, cache isolation and error semantics.
- `tests/lanes.py` – the three modules registered under `cross-boundary`.

The latter three files, other than `test_hosted_pipeline.py`, were unchanged during Plan revision.

No golden-record changes are intended or declared.

Execute must preserve these files and their assertions. A material Plan error must return to Plan rather than be silently absorbed into implementation.

## Test-facing contract

The provisional host-only interface is recorded at the top of `tests/test_hosted_pipeline.py` and in `docs/hosted_pipeline.md`.

It includes:

- `HostedSession(runtime)` and `compiler_source_state`.
- `seed_manifest`, including pinned compiler source identity, roots, executable members and fixed services.
- `rebuild_through(3)` and generation reports.
- `compiler_artifacts(generation)` and a host-only generation invalidation hook.
- `attempt_seed_lower(node)` for negative verification.
- `prepare`, `produce`, `admit`, `run`, and `trace`.
- `AdmissionRejected` and authentic production/admission/execution evidence.
- The normal source-text command and explicitly specified reconciliation edit mode.

Host-only verification mechanisms must not create program-visible authority to install arbitrary executable artifacts.

The new tests intentionally fail before implementation because `shear.hosted_bootstrap` does not exist. No successful CI run or implementation-level validation is claimed.

## Execute requirements

Implement the revised specification, including:

1. The unified SHEAR lowering algorithm and pinned compiler-node descriptors.
2. Distinct compiler and target canonical states.
3. The independently verifiable finite G0 seed.
4. Real G1–G3 compiler self-rebuilding through predecessor-produced admitted code.
5. Per-runtime route-B execution, admission, provenance and transitive artifact resolution, without process-global interception.
6. Complete selected corpus execution, including ordinary failures and `catch`/`raise`.
7. Conservative invalidation for changed code and link dependencies.
8. Source-text execution and candidate reconciliation without unintended activation.
9. Independent correctness comparisons, diagnostics and performance measurements.
10. Task 29 prototype and mutation-catalog disposition, existing regression coverage, and an appended `CHANGES.md` entry.

Host lowering is allowed for the sealed G0 seed and as an independent test oracle. It is not a fallback for ordinary route-B execution or part of admission.

D4's performance targets are diagnostic, not acceptance gates. Preserve the historical Task 29 performance evidence.

## Task 31 exclusions

Task 31 retains language-driven trial and activation, remaining metaprogramming operations, dedicated error canaries, sustained self-modification, held frames and closures across activation, cross-activation artifact reuse and retirement.

Host-orchestrated generation changes do not establish live evolution.

Native compilation, final human-facing syntax, Python removal and full SHEAR-VM parity are not Task 30 requirements.

## Independent Review requirements

Review in a fresh context after Execute:

1. Fetch current main and the task branch.
2. Diff all Plan-owned specification, acceptance-test and golden-declaration files against `94ac037cbcd5e08ed86a3ae6e39c8d20c08f464a`.
3. Independently verify compiler/target separation, canonical source preservation and exact G0 closure.
4. Verify that G2 and G3 genuinely execute predecessor-produced compiler artifacts, rather than relying on reports or labels.
5. Audit all host-lowering paths, artifact resolvers, transitive calls, closures, caches and invalidation paths.
6. Verify the complete corpus, ordinary error behavior and source-edit command, including continuity and absence of unintended activation.
7. Check independent behavioral oracles, the mutation catalog, golden records, ordinary CI and diagnostics.
8. Classify findings as verified defects, limitations, hypotheses or documentation drift.

Execute does not certify its own implementation.

## Next action

Begin **Execute Task 30 (#66)** in a fresh chat.

Read `CLAUDE.md`, `docs/roadmap.md`, `docs/hosted_pipeline.md`, all three Plan-owned acceptance-test modules, this handoff and the relevant D3/D4 specifications.

Use the revised protected Plan head. Do not weaken tests or silently modify settled requirements.

The owner works from mobile with read-only assistant GitHub access. Provide complete file replacements, clickable GitHub edit links and copyable `GH-66` commit messages, one commit at a time. Verify each commit before continuing.
