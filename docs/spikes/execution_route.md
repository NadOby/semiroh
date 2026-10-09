# Execution-route spike – Task 29

**Status: provisional.** Issue #65, roadmap section I, decision D3.

Plan baseline: `dbe92c6e6450db479d22a203011f9c974ba00089`.

This is a falsifiable comparison contract, not a D3 decision. Execute may implement bounded experimental machinery, but cannot select the permanent execution route or change Decided semantics.

## 1. Question and constraints

Can compiler-produced chunks execute with recorded, non-forgeable provenance while keeping the semantic graph canonical, without accepting arbitrary program-supplied bytecode as host-executable code?

Compare two routes:

- A: execution through the SHEAR-written VM.
- B: execution on the host machine after verification and admission as a derived artifact of a specific semantic node version.

Both routes must preserve the semantic source, candidate/activation separation, continuity, errors, effect order, holds, and version lifetime.

The existing `swap_all` mechanism is not itself an acceptable solution to the canonical-source requirement. It installs wrappers containing literal executable chunks as active function bodies, while retaining separate source twins.

## 2. Evidence before the experiment

The current SHEAR compiler emits expanded chunks from collapsed input-form expressions, not individually identified graph nodes. Host bytecode instead consists of per-node chunks containing semantic child references.

Consequently, route B needs a compiler interface that identifies the compiled node and its version, and an admissible per-node output representation. Merely attaching node metadata to an expanded chunk is insufficient.

The existing SHEAR VM lacks instructions for cells, reflection, activation, trials and error handling. Its `CALL`, `APPLY` and `APPLYV` paths can delegate to installed host-executed functions. Instruction coverage therefore does not establish complete transitive execution coverage.

Task 23 measured `lower(lower)` at approximately 0.037 s through the native host-executed compiler and 5.264 s through the SHEAR VM, with a median ratio of approximately 142:1. These observations are diagnostic baselines, not target budgets.

Task 28's operation matrix and host-service inventory in `docs/bootstrap.md` are the coverage baseline. They do not authorize additional Python services.

## 3. Workload

Use the recommended D4 workload provisionally. D4 remains an owner decision.

W0 – compiler self-rebuild:
- Seed the SHEAR compiler through the Python model.
- Rebuild generations 1, 2 and 3.
- Compare complete compiled outputs, provenance and retained semantic source.
- Identify host lowering, fixed interpreter machinery and program-code execution separately.

W1 – ordinary execution:
- Exercise the tier-1 and tier-2 corpora, including cells, recursion, calls, closures and error cases.
- Record each supported, rejected or deferred operation against Task 28's matrix.
- Compare observable results and errors with the existing reference path.

W2 – live-evolution probe:
- Produce a candidate, trial it, activate a valid change and reject an invalid change.
- Check continuity, live-cell content and an old frame or closure across activation.
- Check repeated updates and retirement under the current lifetime rules.

W0 is mandatory for executable comparison. W1 and W2 must have complete coverage ledgers. Unsupported cases may remain blocked by named prerequisites assigned to Tasks 30 and 31; they cannot be counted as passing or silently delegated to host lowering.

If D4 later chooses a materially different workload or host boundary, rerun the affected comparison before D3 is accepted.

## 4. Route A – SHEAR VM

Evaluate the current wrapper-based route as a baseline and attempt one bounded wrapper-free route.

The wrapper-free candidate must execute compiler-produced chunks through the SHEAR VM while keeping the active semantic definitions and their node versions unchanged. Executable artifacts must be separate derived state.

Specify how calls, indirect calls, recursion and closures select their execution route without replacing semantic function bodies.

Account for every transitive callee and for the currently missing instructions. Host-executed program-code delegation is a fallback, not evidence of complete SHEAR-VM execution.

If no bounded design satisfies the canonical-source requirement, record the counterexample. Do not silently weaken the acceptance anchor.

## 5. Route B – verified host execution

The host must admit artifacts only through a verifier, not through a program-visible arbitrary-chunk installation API.

An admission request must identify:
- The held semantic state and node identity.
- The node's `VersionID`.
- The compiler generation and producing computation.
- The proposed per-node chunk.
- Any semantic dependencies not already captured by the node version.

The verifier must establish:

1. The identified node exists in the claimed state with the claimed version and is executable code.
2. The chunk has valid instruction structure, operands, control flow and references.
3. The chunk implements that node's semantic operation, including child identities, evaluation order and allowed effects. Shape and provenance checks alone are not sufficient.
4. Every dependency necessary for correct execution and invalidation is recorded or resolved through the held semantic state.
5. Producer evidence is created by trusted execution machinery observing a compiler invocation. Program code cannot create, impersonate, transfer as authority, or forge that assertion using ordinary data.
6. Admission and execution preserve the runtime's activation capability, held versions, error provenance and lifetime rules.

A compiler-generation assertion establishes origin, not correctness. Semantic verification remains necessary even for a genuine compiler result.

Host lowering must not be used to generate or admit the production artifact. It remains a differential test oracle. A verifier that delegates equivalence to host lowering fails this boundary.

Rejected artifacts must not enter the executable cache. Cache entries must bind to validated semantic identities and dependencies. A stale artifact must not be silently reused after an incompatible change.

Document the trusted boundary precisely, including who owns admission credentials and which program-visible operations, if any, can request compilation or execution.

## 6. Predictions fixed before execution

P1 – The existing wrapper-based route will fail the canonical-source acceptance condition even when its observable computation is correct.

P2 – A wrapper-free SHEAR-VM route will require new execution dispatch or an equivalent explicit boundary, plus closure of workload-dependent instruction and indirect-call gaps. The existing VM alone will not meet the complete workload.

P3 – A verified host route can execute at least one genuinely SHEAR-compiled per-node artifact while retaining the original semantic function definition. If no verifier can establish the node's semantics without host lowering, this prediction is false.

P4 – Verified host execution will have lower median `lower(lower)` execution latency than the wrapper-based SHEAR-VM route when compared on the same runner with the same workload and equivalent coverage. Verification and cache costs must be included wherever incurred.

P5 – Existing instrumentation will be insufficient to prove transitive compiler provenance across all calls, wrappers and closures. Additional tracing or an equivalent proof mechanism will be necessary.

Test these predictions, including negative evidence. Execute gets one documented revision of an experimental design or prediction, with its falsifying observation and reason recorded before the rerun. Further material redesign returns to Plan.

## 7. Falsifiable acceptance criteria

A1. The two routes receive the same declared semantic workload and comparable inputs. Full deterministic outputs agree with independently specified expected results, not only with each other.

A2. The route reports the semantic function and node versions before and after execution. A successful source-preserving route shows no replacement of active semantic definitions by literal-chunk wrappers.

A3. A host-admitted chunk is demonstrably produced by the SHEAR compiler, with its node and version established independently of a program-provided claim.

A4. Forged producer records, stale versions, wrong-node chunks, modified instructions, invalid child references and semantically incorrect but structurally valid chunks are rejected before host execution. Each rejection has an observable witness.

A5. A program cannot bypass admission by directly supplying an arbitrary executable chunk or forged authorization value.

A6. The verifier does not invoke host lowering as part of admission. Instrument the boundary so that this assertion is falsifiable.

A7. Trace executed program chunks transitively through direct and indirect calls, recursion and closures. Distinguish fixed interpreter machinery, seed compilation, legitimate host services and unintended host-lowered program code. Any untraced or fallback call invalidates a claim of complete route coverage.

A8. Candidate construction does not activate a change. Existing activation, trial, failure, continuity and held-version behavior must remain unchanged in the cases actually exercised.

A9. Missing instructions and services are enumerated against Task 28's matrix. Deferred paths fail explicitly; a blocked case is never reported as successful.

A10. Produce reproducible correctness and security tests in ordinary CI. The baseline must fail at least one new acceptance test before implementation. Do not weaken these tests during Execute without returning to Plan.

A11. The experimental evidence contains an explicit pass, fail or blocked status for every criterion. A blocked criterion prevents claiming full acceptance, but may still support a documented comparison and recommendation.

## 8. Measurement contract

Reuse `docs/content_baseline.md` section 3 and its corrected results.

Use named CI hardware, Python/runtime versions, exact commit, fixed source/input, identical cache conditions and separate warm-up. Record at least three untraced timings per comparable route, median and range.

Measure separately:
- Seed and compiler rebuild time per generation.
- Compiler execution and artifact admission/verification time.
- Peak traced Python memory, explicitly distinguished from RSS.
- Produced artifact bytes, number of chunks and retained derived artifacts.
- Semantic-state-content size as an image proxy, not an executable image.
- A small `define` → lowering/admission → `Runtime.activate` edit with phase and total latency, affected identities, and before/after results.
- Transitive host lowering, host execution, SHEAR compilation and SHEAR-VM execution counts.

Do not compare incomplete workloads as if coverage were equivalent. Report unmatched work and costs explicitly. Do not impose a new numeric performance budget before D4 is decided.

If extending the host machine requires another execution boundary, consider extracting a single demonstrated run-context responsibility first, as recommended in `reviews/bootstrap_delivery.md` section 8. Do not refactor the full dispatcher as a speculative prerequisite.

## 9. Decision gates

G1 – Canonical representation: a route that replaces semantic definitions with executable wrappers is not acceptable unless the owner explicitly revises the anchor.

G2 – Provenance and verifier: no direct host route is acceptable without a non-forgeable producer boundary, semantic verification and negative admission tests.

G3 – Functional coverage: compare only matching completed workloads; record everything else as blocked or unsupported.

G4 – Cost: compare execution speed together with verification complexity, rebuild latency, edit latency, memory, added trusted mechanisms and maintenance burden.

G5 – D4 dependency: record the provisional workload and permitted host services. Material changes to either require revisiting the comparison.

G6 – Owner decision: present route A, route B, their evidence, unresolved risks and a recommendation. Only the owner decides D3 and authorizes changes to Decided rules.

The instruction set, the version observed by `code`, and node identities in compiler output are Provisional where not already Decided. A recommended route must identify which choices become expensive to change.

## 10. Role boundaries and outputs

Plan owns this specification, the acceptance tests and any intended golden declarations. No production-code change or golden-record change is authorized by Plan.

Execute implements bounded route experiments and gathers evidence using GitHub Actions. Record results, failed predictions, coverage, admission behavior and a recommendation in `docs/bootstrap.md`. Do not rewrite the Plan's criteria to fit the observed outcome.

Independent Review must verify the production/compiler origin, host-lowering exclusion, negative admission tests, source preservation, workload parity and measurement provenance. Compare all Plan-owned files against the Plan head commit.

Resolve handles verified findings. Publish occurs only after independent Review accepts the resulting evidence and D3 has been decided by the owner. The task's final record must distinguish the selected route from the other route's observed limitations.

Task 30 owns full hosted-pipeline implementation and Task 31 owns complete live-evolution coverage. Neither may use Task 29's partial spike results as proof of those later milestones.
