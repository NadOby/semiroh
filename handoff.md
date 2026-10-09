# Handoff

Read `CLAUDE.md`, the Workflow and task 29 sections of `docs/roadmap.md`, and `docs/spikes/execution_route.md`. Verify all claims against GitHub; this checkpoint is not independent evidence.

## State

- Task: 29, execution-route spike, issue #65.
- Role: Resolve documentation corrections complete; independent re-review next.
- Branch: `task/29-execution-route`.
- Last verified Resolve head before this handoff: `9508ec1989e3d7296e3f6967bd3b4a2ce85de2bb`.
- Execute handoff commit: `e5e4d7724320e00dcb72615874195ed6488cd662`.
- Protected Plan baseline: `deb03aa3ffc198df8e19fa14da59db904f879a1b`.
- Base `main` at Plan: `dbe92c6e6450db479d22a203011f9c974ba00089`.
- D3 and D4: Open. No permanent execution-route or language decision.
- No PR. No golden changes. No changes to Plan-owned acceptance tests.

The next reviewer must fetch the current branch head rather than assume the recorded head is still current.

## Plan integrity

The protected Plan established the contract in:

- `docs/spikes/execution_route.md` – sections 1–10, predictions and role gates.
- `tests/test_execution_route.py` – 18 behavioral acceptance tests.
- `tests/lanes.py` – registration under `cross-boundary`.
- `tests/mutation_catalog.py` – explicit temporary omission of the spike module.

Execute populated section 11 of the spike specification. Resolve changed only nine lines within section 11 to correct evidence interpretation and limitations.

Sections 1–10 remained byte-for-byte unchanged through Resolve. The acceptance tests, lane registration and mutation-catalog omission remain unchanged from the protected Plan baseline.

No `tests/golden_changes/GH-65.txt` is authorized.

## Implementation

The sole new implementation module is `shear/execution_route_spike.py`.

It provides the provisional API:

    produce(runtime, entity) -> (chunk, evidence)
    admit(state, entity, version, chunk, evidence) -> admitted
    run_admitted(runtime, entry, *args) -> result
    trace(runtime) -> tuple[RouteEvent, ...]
    AdmissionRejected

The node-aware compiler is expressed as SHEAR `Function` data and invoked through the ordinary SHEAR runtime. Python supplies a semantic node descriptor, observes the returned artifact and generically decodes canonical values, including typed identifiers.

Supported kinds are `lit`, `arg`, `add` and `call`. The compiler emits per-node host chunks containing child `EntityID` references.

Host admission uses opaque producer evidence, exact output matching, structural checks, node/version/ownership binding and a runtime-specific admitted-artifact registry. Missing or incompatible artifacts fail without ordinary target-node host-lowering fallback during admitted execution.

The implementation uses temporary process-global machine-method interception guarded by a lock. It is experimental, not a permanent runtime interface or concurrency-safe execution boundary.

The existing route-A compiler and VM are unchanged. The existing GitHub Actions workflow was extended with an opt-in `execution_route_spike` diagnostic input and artifact-upload job.

Resolve did not change implementation, tests or workflow configuration.

## Verified CI evidence

- Implementation revision tested: `6ebbc698c881528b53b37c63b5b090f82eb4a037`.
- Workflow run: https://github.com/NadOby/shear/actions/runs/37981959588
- Tests job: https://github.com/NadOby/shear/actions/runs/37981959588/job/113994433438
- Diagnostic job: https://github.com/NadOby/shear/actions/runs/37981959588/job/113994434005
- Evidence artifact: https://github.com/NadOby/shear/actions/runs/37981959588/artifacts/11641073831
- Runner: `GitHub Actions 1000008691`.
- Python: 3.12.15; Linux 6.17.0-1022-azure, x86-64, glibc 2.39; four reported CPU cores.

Every ordinary test lane passed, including all 18 Plan-owned execution-route tests. Golden comparison: 55 unchanged records, zero failures. The diagnostic job completed and uploaded `execution-route.json`.

The mutation campaign was not run. The spike retains its Plan-authorized temporary mutation-catalog omission.

The cited diagnostic predates the documentation-only Resolve commit. No new diagnostic or performance measurement is claimed for Resolve.

## Results and predictions

Full workloads, observations, coverage inventories, caveats and recommendation are in `docs/spikes/execution_route.md` section 11.

W0:

- Route A achieved compiler rebuild generations 1, 2 and 3. Median swap times: 0.204083 s, 7.415722 s and 7.465605 s.
- Route A still replaces active compiler definitions with literal-chunk wrappers. Retained source twins do not restore canonical-source preservation.
- Route B produced, admitted and executed authentic per-node artifacts for a bounded linked-call witness without changing semantic source.
- Route B and ordinary host execution both returned `7` for the linked-call witness at `x = 4`. Route A did not execute that witness through its VM.
- The four supported node kinds agreed with the host lowering oracle in differential tests.
- Route-B compiler rebuilding reached generation 0 only. Production stopped on unsupported `swap_all/0.0`. No route-B rebuild timing exists.
- A bounded wrapper-free route-A design was recorded, not implemented.

P1, P2, P3 and P5 were supported within their stated evidence boundaries.

P4 was falsified. For the equivalent cold witness:

    median(T_B) = 9.873980 ms
    median(T_H) = 0.055123 ms
    median(T_B) / median(T_H) = 179.126317

The fixed prediction required a ratio at most 10. No experimental revision was made.

The dominant measured cold component is production, including separate SHEAR compiler-runtime initialization and node compilation. Those subcomponents were not separately timed in the original diagnostic.

Separate median warm execution times were 0.639887 ms for B and 0.022001 ms for the host reference.

The small-edit diagnostic changed `target(x)` from `x + 3` to `x + 5`. Candidate preparation, production/admission/verification and activation totaled 25.010713 ms.

The candidate returned `9` through admitted execution on a separate candidate runtime. After activation, the original runtime returned `9` through ordinary host execution, not admitted execution. The diagnostic does not demonstrate transfer of admitted artifacts across activation.

W1 and W2 are inventories only. They identify unsupported corpus, instruction, indirect-call, reflection, cell, error, activation, continuity, closure and lifetime behavior. No complete corpus execution or live evolution through route B is claimed.

## Independent Review findings

Two independent reviews assessed the Execute implementation at `e5e4d7724320e00dcb72615874195ed6488cd662`.

The first review found one P3 documentation defect and no verified P0–P2 defects. The linked-call result was incorrectly attributed to both execution routes when the diagnostic compared admitted route B with ordinary host execution.

The second review identified:

1. P2 evidence-reporting defect – the post-activation result was obtained through ordinary host execution, not the admitted route.
2. P3 evidence-reporting defect – the runtime-local, exact-state-bound registry does not demonstrate precise invalidation or reuse of unchanged-node artifacts after a state change.
3. P3 cost-interpretation limitation – the original diagnostic includes compiler-runtime initialization in production time but does not separately measure it.
4. P3 architectural limitation – structural validation uses per-kind opcode templates, creating a maintenance cost when the supported vocabulary expands.
5. Task 30 housekeeping – the temporary spike imports test infrastructure, and the route-B rebuild attempt was limited to production on an unsupported node.

The second review also supplied separate local timing observations. Those measurements are not added to the original CI evidence or substituted for the fixed P4 result.

Neither review established a production-ready execution route or completed hosted bootstrap. Both identified the bounded route-B witness as meaningful evidence.

## Resolve changes

Resolve commit:

    9508ec1989e3d7296e3f6967bd3b4a2ce85de2bb

Commit message:

    GH-65 Correct execution-route evidence and limitations

Exactly one file changed: `docs/spikes/execution_route.md`.

Nine lines in section 11 were replaced:

- Section 11.2 correctly distinguishes route-B admitted execution from the ordinary host comparison and route-A rebuilding.
- Section 11.4 distinguishes measured aggregate production time from unmeasured compiler initialization and node-compilation subcomponents.
- Section 11.5 identifies admitted candidate execution separately from ordinary post-activation host execution and explicitly states that admitted artifacts were not transferred.
- Section 11.9 corrects the Activation and Continuity across edits inventory rows.
- Section 11.10 documents per-kind verifier templates and removes the unsupported claim of demonstrated precise invalidation.
- Section 11.11 identifies reusable compiler lifetime, cross-state artifact reuse, maintainable validation and integrated routing as future design requirements.

The branch diff against the preceding Execute head contains nine changed lines, nine deletions and nine additions. The file retains 481 lines.

Sections 1–10, implementation, tests, workflow, numerical observations and fixed predictions were unchanged by Resolve.

## Remaining limitations

- Route B covers four node kinds and one narrow linked-call witness, not the complete compiler or corpus.
- Route B cannot yet rebuild the compiler.
- Route B's admitted artifacts are tied to their runtime and exact state object. Cross-state reuse and post-activation admitted execution are unimplemented.
- Admission establishes origin and structural compatibility, not arbitrary semantic correctness.
- The verifier duplicates selected instruction structure using per-kind templates.
- Complete transitive provenance is established only for the bounded witness.
- Process-global machine interception is not safe for unrelated concurrent executions.
- Artifact lifecycle, dependency invalidation, persistent admission and integrated machine routing remain unresolved.
- P4 failed substantially; route-A and route-B compiler rebuilding cannot yet be compared on equivalent workloads.
- Route A's wrapper-free alternative was neither implemented nor measured.
- The temporary spike module remains outside mutation campaigns under the Plan-authorized omission.
- Task 30 must remove, replace or explicitly promote the experimental module and make an explicit mutation-testing decision.

These are disclosed limitations and future design requirements, not claims of production readiness.

## Independent re-review

Start a fresh, read-only `Review task 29` context.

Fetch the current branch head, `CLAUDE.md`, `docs/roadmap.md`, this handoff and the protected Plan baseline.

The re-review should:

1. Verify that Resolve changed only the intended evidence-reporting lines in section 11.
2. Verify sections 1–10 and the Plan-owned tests, lane registration and mutation catalog remain unchanged from `deb03aa3`.
3. Confirm the corrected linked-call attribution against the actual diagnostic.
4. Confirm the candidate-runtime and original-runtime execution paths in the edit/activation diagnostic.
5. Confirm the exact-state-bound registry prevents reuse of admitted artifacts across changed states.
6. Confirm that the discussion of compiler-runtime initialization makes no unsupported quantitative claim.
7. Confirm the verifier-maintenance limitation reflects the implementation.
8. Reassess whether all verified P2/P3 findings from both reviews are resolved without creating new contradictions.
9. Report any new verified defects separately from acknowledged limitations or future Task 30–31 work.

Review must not modify files. Verified defects return to Resolve, followed by another independent Review. Do not reopen already settled implementation questions without new evidence.

## Decision and Publish boundary

The spike conditionally favors route B for Task 30 because of canonical-source preservation, per-node identities, trusted admission and explicit execution provenance on the supported witness.

This remains an evidence-based recommendation, not the owner's D3 decision. P4 failure, incomplete compiler coverage, missing cross-activation continuity, per-kind verifier maintenance and temporary global machine interception are material qualifications.

D3 and D4 remain Open. Instruction-set conventions, the semantic version observed by `code`, and node identities in compiler output remain Provisional.

No PR is authorized before accepted independent re-review and the necessary owner decision.

Publish must recheck current `main`, the protected Plan, CI, final diff, Review disposition, outstanding decisions and required follow-up issues. It then prepares the PR closing #65 if authorized.

## Next

Start `Review task 29` in a fresh chat, explicitly focusing on the combined Resolve corrections.

Follow the owner's mobile GitHub protocol for subsequent changes: read-only assistant GitHub access, one complete file per commit, copyable commit messages, clickable branch-specific edit links, manual owner commits, `Done` confirmation and independent verification. No terminal dependency.
