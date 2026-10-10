# Execution-route spike – Task 29

**Status: provisional.** Issue #65, roadmap section I, decision D3.

This is the revised Plan contract following two review rounds. It does not decide D3, D4 or permanent language semantics.

## 1. Question

Compare two execution routes for chunks produced by the SHEAR compiler:

- A: execution through the SHEAR-written VM.
- B: host execution of admitted, SHEAR-compiled per-node derived artifacts.

The semantic graph remains canonical. Derived executable artifacts cannot replace semantic definitions.

The existing `swap_all` mechanism is a baseline, not a source-preserving solution: it installs literal-chunk wrappers as active function bodies and retains the originals in separate source twins.

The objective is a bounded, falsifiable comparison for the owner's D3 decision, not a complete hosted-bootstrap implementation.

## 2. Workload and scope

W0 – executable comparison:

- Reproduce the existing route-A compiler rebuild through generations 1, 2 and 3.
- Produce, admit and execute a genuine SHEAR-compiled per-node chunk through route B.
- Use a function with child nodes and a statically linked call as the route-B witness.
- Keep the semantic source and its versions unchanged.
- Attempt compiler rebuilding on route B, recording each achieved generation and its concrete limitations.
- Distinguish program execution from compiler execution, fixed host machinery and fallback.

Only genuinely equivalent executable coverage may be compared quantitatively.

W1 – ordinary corpus coverage inventory:

- Classify the tier-1 and tier-2 operation requirements against Task 28's matrix.
- Identify missing instructions, services, indirect-call requirements and fallbacks.
- Record each gap, its prerequisite and its future owning task.
- No corpus-wide implementation is required.

W2 – live-evolution coverage inventory:

- Assess candidate construction, trial, activation, rejection, continuity, held frames and closures, and retirement.
- Record supported and blocked mechanisms for each route.
- No new live-evolution implementation is required.

Route A additionally requires one bounded wrapper-free execution design or a concrete counterexample. Implementation is not required.

Tasks 30 and 31 own full hosted-pipeline and live-evolution completion.

## 3. Spike modules and interfaces

The entire experimental implementation lives in:

    shear/execution_route_spike.py

This module contains:

- Host-side production observation, structural admission, derived-artifact storage, execution routing and tracing.
- A node-aware compiler expressed as SHEAR `Function` data, invoked through the ordinary SHEAR runtime.
- Private helpers necessary to build a separate compiler runtime and construct the host-provided node descriptor.

No additional Python module is authorized for this spike without returning to Plan.

The SHEAR compiler must actually execute as a SHEAR function. Python may construct the descriptor and observe the compiler's returned value; Python must not implement the lowering operation whose result is attributed to the SHEAR compiler.

At the producer boundary, Python may generically decode the complete canonical compiler result, including typed entity and version identifiers, into host values; decoding must be opcode-independent and must not synthesize or modify instructions.

The compiler runtime may be separate from the target program runtime. Production must not modify the target program's semantic definitions.

Provisional API:

    produce(runtime, entity) -> (chunk, evidence)
    admit(state, entity, version, chunk, evidence) -> admitted
    run_admitted(runtime, entry, *args) -> result
    trace(runtime) -> tuple[RouteEvent, ...]
    AdmissionRejected

`entity` identifies a semantic code node, not its containing function. `version` is that node's `VersionID`.

The descriptor supplied to the compiler contains the node's kind, payload, role-to-child `EntityID` mapping, owner and permitted linked entities. The compiler produces a host-format per-node chunk containing semantic child references, not recursively expanded child chunks.

The mandatory supported node kinds for the executable witness are `lit`, `arg`, `add` and `call`. Further support is optional but must be recorded and differentially tested.

Admitted artifacts and tracing records live outside semantic state. The spike does not change the program-visible `code` operation or expose node identities through it.

### Module lifecycle and mutation policy

`shear/execution_route_spike.py` is temporary experimental machinery, not an accepted permanent runtime interface.

Plan registers it in `tests/mutation_catalog.py` under `OMITTED`, with the reason:

    Experimental Task 29 spike; remove or replace in Task 30, or promote with an explicit mutation-testing decision.

The omission is intentional and temporary. Acceptance and adversarial tests remain mandatory; omission does not excuse functional or security defects.

No new example module is necessary. The existing `shear/examples/self_hosting.py` stays unchanged, avoiding its mutation-survivor source pin.

The experimental module may merge with Task 29 as explicitly temporary code. Task 30 must remove it, replace it or deliberately promote it with the appropriate mutation-catalog update. A route-A decision does not justify silently retaining the unused host experiment.

Because Plan registers a module that Execute has not created yet, the mutation-catalog inventory is expected to fail until that module exists. Execute must create it before claiming ordinary CI is green.

## 4. Host admission and trust boundary

**Provisional choice: structural admission plus trusted producer evidence.**

Admission establishes:

1. The node exists in the supplied state, is executable, belongs to a valid function and has the claimed version.
2. The chunk contains supported, well-formed instructions, operand types and control-flow structure.
3. Child operands refer only to the node's actual semantic children.
4. Function/entity operands requiring link resolution refer only to entities available through the owner's links.
5. The chunk matches the exact artifact observed at the trusted producer boundary.
6. The producer record binds the actual SHEAR compiler invocation, its compiler version/generation, the target state, node, version and returned artifact.
7. Dependencies and cache identity prevent stale or incorrectly rebound artifacts from executing.
8. Rejected artifacts never enter the executable cache and never trigger host-lowering fallback.

Trusted host machinery observes the SHEAR compiler function actually executing and returning its result. It retains an opaque record and issues an evidence handle.

Neither a tuple built by a SHEAR program nor a copied collection of record fields grants authority. An authentic handle cannot authorize a different chunk or node.

Only internal host machinery invokes admission. No program-visible compilation capability, arbitrary-bytecode installation operation or transferable admission credential is added.

Admission does **not** prove compiler correctness. It does not recompute semantic lowering and never invokes host lowering as its verifier.

Compiler correctness must instead be tested against independent expected behavior and, inside tests only, the existing host lowering as a differential oracle.

An independent semantic verifier would duplicate compiler logic; admission by recomputation would collapse route B into the existing host path. Neither is required or authorized.

## 5. Route tracing

`trace(runtime)` returns a read-only snapshot of host-maintained observations. Each `RouteEvent` exposes at least:

    kind
    route
    entity
    version
    artifact_id

The event kinds are `produce`, `admit` and `execute`.

- Production events identify route `shear-compiler` and expose the actual compiler entity and compiler version.
- Admission events identify route `host-admission`.
- Execution events identify route `admitted-host`.
- `artifact_id` is an exact immutable identity or digest of the produced artifact. Events for the same admitted artifact carry the same identity.
- `entity` and `version` identify the semantic node whose artifact is involved.

Trace data is not program-supplied. Producing an event without actually observing the corresponding operation does not satisfy this contract.

For the executable witness, the trace must identify every target-program node whose admitted artifact executes. Execution using ordinary host lowering or unrecorded chunks must fail the witness.

No claim of system-wide transitive completeness may be made beyond the explicitly traced workload.

## 6. Route A and deferred semantics

Characterize the existing wrapper-based route, including its modification of active semantic source and reliance on installed host functions for some calls.

Describe one design for selecting VM execution through external derived-artifact state without replacing function bodies, or demonstrate a concrete obstacle.

No new language instructions or by-value authority mechanism may be introduced to make route A pass this spike.

`READ`, `WRITE`, `CODE`, `LINKS`, `QUOTE`, `FUNCTION`, `ACTIVATE`, `TRIAL`, `CATCH`, `FAIL` and `RAISE` remain documented VM coverage gaps where unsupported.

Whether cell and reflection targets can be chosen by value is a separate language and capability decision.

## 7. Fixed predictions

P1 – The existing wrapper mechanism changes active semantic function definitions and therefore fails source preservation despite successful observed computation.

P2 – The existing SHEAR compiler emits recursively expanded chunks from collapsed expressions and needs a separate node-aware SHEAR entry to produce per-node host chunks.

P3 – Structural admission and trusted producer evidence can admit a genuine SHEAR-produced per-node artifact while rejecting forged, stale and modified submissions without host lowering.

P4 – For the same cold executable witness, total route-B latency is at most 10 times ordinary host-route latency.

Define P4 precisely:

    T_B = T(produce all required target nodes)
        + T(admit all produced artifacts)
        + T(run_admitted once)

    T_H = T(ordinary host run once, including its lazy lowering)

    P4 holds when median(T_B) / median(T_H) <= 10.

Use fresh, equivalent target runtimes, identical program inputs, identical expected outputs and cold target-node chunk caches for both paths.

Exclude common test-fixture and target-runtime construction from both measurements. Include any route-B-specific compiler-runtime initialization required for production. Exclude only common preparation performed equally for both routes.

The host reference runs the same function and arguments through the ordinary machine, including its ordinary lazy host lowering. It is not warm execution alone.

Measure route-B production, admission and execution separately as well as their total. Measure subsequent warm runs separately, but do not use warm timings to evaluate P4.

If one route cannot execute the same witness without undeclared fallback, P4 is inconclusive rather than confirmed.

P5 – Existing instrumentation is insufficient to establish complete producer and execution provenance; explicit boundary tracing is needed.

The Task 23 diagnostic baseline was approximately 0.037 seconds for native `lower(lower)` against 5.264 seconds under the SHEAR VM, approximately 142:1. It is not the P4 denominator and does not establish admission cost.

Predictions are fixed before Execute starts. One documented experimental revision is permitted after recording a falsifying observation and the reason for revision. Material changes in scope, trust or language semantics return to Plan.

## 8. Plan-owned acceptance tests

`tests/test_execution_route.py` must exercise actual behavior, not merely documentation or report formatting.

Positive tests:

- A genuine SHEAR-produced chunk for the correct node and version is admitted.
- A node with children emits the required per-node `EVAL` references and executes to an independently specified result.
- The SHEAR-produced chunk for each mandatory supported node kind equals `bytecode.lower(relation)` when host lowering is called solely from the test.
- An admitted execution uses the admitted artifacts rather than cached or newly host-lowered code.
- Semantic function definitions and node versions remain unchanged.
- Editing a function invalidates incompatible old artifacts.
- Tracing identifies the genuine producing compiler and matches production, admission and execution of the same artifacts.

Negative tests:

- Arbitrary Python evidence is rejected.
- Evidence-shaped data returned by a SHEAR program is rejected.
- A genuine handle cannot be reused with another producer's chunk.
- A genuine handle attached to the wrong node is rejected.
- A stale version is rejected.
- A modified but structurally valid instruction sequence is rejected.
- Foreign child and unlinked entity operands are rejected.
- Admission does not call host lowering.
- Producing the target artifact does not secretly invoke host lowering for that target.
- Rejected artifacts cannot execute through a fallback.

Tests must use the fixed spike API. They must fail on the Plan baseline because behavior is missing, not because a report heading is missing.

Execute may add tests for implementation details but cannot weaken the Plan-owned cases.

No golden changes are authorized.

## 9. Measurements and evidence

Use `docs/content_baseline.md` section 3.

Mandatory observations:

- Rebuild time for each actually achieved compiler generation on both routes.
- P4 cold production/admission/execution latency and matching cold host reference.
- Separate warm execution latency.
- One small edit through preparation, lowering/admission and activation, with phase and total latency and checked before/after behavior.

For comparable timings, collect at least three untraced observations, their median and range, and record exact commit, CI runner, Python version, workload and cache conditions.

Reuse the Task 23 memory and artifact-size baseline. Extra memory measurements are optional unless the spike reveals a particular cost mechanism.

W1 and W2 coverage inventories must reference the Task 28 matrix and name unsupported capabilities without treating them as passes.

All results and recommendations belong under section 11 of this document, not in a second report in `docs/bootstrap.md`.

### Required costly-to-change analysis

The final recommendation must explicitly analyze these three Provisional interfaces:

1. **Instruction set** – which instructions or operand conventions would become route-specific, and what would be required to migrate the compiler and execution machinery.
2. **The version observed by `code`** – the cost and semantic consequences of choosing active, held/caller or other version views, including continuity and closure behavior. Do not change `code` in this task.
3. **Node identities in compiler output** – whether outputs contain `EntityID`s, opaque references or expanded child chunks; the effects on compiler APIs, invalidation and reproducibility.

For each, record route-A implications, route-B implications, what becomes expensive to reverse, and the outstanding owner decision.

The final report must include the admission rule, observed limitations, recommendation and this analysis. Omitting it fails Task 29's roadmap done-when condition.

## 10. Decision and role gates

G1 – Canonical source: replacing active function definitions with chunk wrappers fails unless the owner changes the anchor.

G2 – Admission: source-bound, authentic artifacts only; rejection must be fail-closed.

G3 – Correctness: admission proves structure and origin, not semantic correctness. Differential and independent behavioral tests are required.

G4 – Scope: W0 is executable; W1 and W2 are inventories. Blocked paths cannot be reported as implemented.

G5 – Cost: use the P4 formula fixed before execution. Compare equivalent work and report other costs separately.

G6 – Owner authority: D3 and D4 and permanent language-shaping choices remain open until explicitly decided.

Plan owns this specification and its acceptance tests. Execute implements the experimental API and collects evidence. If the contract proves materially unsuitable, return to Plan.

Independent Review examines the actual compiler invocation, forged authority, output integrity, source preservation, differential correctness, trace authenticity and measurement provenance against the protected Plan baseline.

Resolve addresses verified defects. Publish follows an accepted independent Review and the owner's D3 decision. No earlier PR.

## 11. Execution results

### 11.1. Provenance and verification

**Status: Execute evidence, pending independent Review.** These observations do not decide D3 or D4.

- Revision: `6ebbc698c881528b53b37c63b5b090f82eb4a037`.
- Branch: `task/29-execution-route`.
- CI: https://github.com/NadOby/shear/actions/runs/37981959588
- Tests job: https://github.com/NadOby/shear/actions/runs/37981959588/job/113994433438
- Diagnostic job: https://github.com/NadOby/shear/actions/runs/37981959588/job/113994434005
- Evidence artifact: https://github.com/NadOby/shear/actions/runs/37981959588/artifacts/11641073831
- Artifact file: `execution-route.json`.
- Runner: `GitHub Actions 1000008691`; Python 3.12.15; Linux 6.17.0-1022-azure, x86-64, glibc 2.39; four reported CPU cores.
- The diagnostic did not record the processor model. Task 23's separately recorded hardware and allocation measurements remain the reference baseline, not measurements from this Task 29 runner.

The manually dispatched workflow passed every ordinary test lane, including the 18 Plan-owned execution-route tests. The golden comparison reported 55 unchanged records and zero failures. The diagnostic job completed and uploaded its JSON artifact. The mutation campaign was not run; the spike module retains the Plan-authorized temporary mutation-catalog omission.

Timings use `time.perf_counter()`, three observations per comparable route, with tracing suppressed during the timed intervals. No performance threshold is enforced by CI. The measurements are single-run, single-runner diagnostic evidence, not performance guarantees.

### 11.2. W0 – executable routes

**Route A – three rebuilding generations achieved.** Starting from a fresh bootstrap runtime, three successive `swap_all` activations reported generations 1, 2 and 3. Each generation used the existing SHEAR compiler/VM rebuilding mechanism. The measured interval for each generation includes its swap operation and activation, but excludes bootstrap runtime construction and the subsequent generation-record verification.

The mechanism is not source-preserving: the active compiler functions become wrappers holding literal chunks and delegating to `vm`. Retained source twins preserve separate copies of the original definitions. Generations 2 and 3 therefore demonstrate the existing rebuilding path, not a compliant wrapper-free route A. The interpreter also delegates some linked and indirect calls to host execution, as recorded in `docs/bootstrap.md` section 2.1.

**Route B – one bounded per-node execution witness achieved.** A SHEAR `Function` constructs chunks for `lit`, `arg`, `add` and `call` using a host-provided descriptor. Python observes one actual SHEAR compiler invocation, generically decodes the canonical result, and records the artifact. Admission binds that artifact to the target state, node, version, owner and compiler identity. The host machine then runs the admitted chunks without using ordinary target-node lowering.

The linked-call witness returned `7` through both admitted route-B execution and ordinary host execution. Route A was evaluated separately through compiler rebuilding; the linked-call witness was not executed through its VM. Every target and caller node required for that execution has an admitted artifact. The Plan tests separately compare all four emitted node kinds with the host lowering oracle, and verify a host-cache poison and lowering-fallback guard. The target's semantic definitions and node versions remain unchanged during production and admitted execution.

**Route-B compiler rebuilding – generation 0 only.** The diagnostic attempted production for the actual bootstrap `swap_all` body. It failed closed on `EntityID('swap_all/0.0')`, which is outside the four supported node kinds. No compiler generation was installed through route B; no route-B rebuild timing exists. This is a coverage blocker, not an execution failure of the supported witness. Supporting the existing compiler and its installation path requires many additional operation kinds, host services and a transitive admitted-execution boundary.

The executable comparison supports route B on the narrow linked-call witness, compared only with ordinary host execution. Route A's compiler-rebuild timing and route B's witness timing are different workloads and must not be compared as if equivalent.

**Wrapper-free route-A design, not implemented.** Preserve semantic function bodies and hold executable VM chunks in external derived-artifact storage, keyed by semantic node versions and the required compiler/VM dependencies. A trusted execution router selects the SHEAR VM entry without installing literal-chunk wrappers. This requires a separate routing boundary, access to the correct held program version and link environment, and transitive VM execution for every reached program function. Existing `CALL`/`APPLY`/`APPLYV` delegation and unsupported VM instructions prevent the current mechanism from meeting that design. No new language instruction or by-value authority rule is implied by this proposal.

### 11.3. Compiler-generation timings

All values are seconds. Each row has three untraced observations, a median and the observed range.

| Route and generation | Observations | Median | Min–max |
| --- | --- | ---: | ---: |
| A, generation 1 | 0.204083, 0.199989, 0.224628 | 0.204083 | 0.199989–0.224628 |
| A, generation 2 | 7.408509, 7.415722, 7.423526 | 7.415722 | 7.408509–7.423526 |
| A, generation 3 | 7.465605, 7.441106, 7.474766 | 7.465605 | 7.441106–7.474766 |
| B, rebuilding | Not executable | N/A | Blocked at generation 0 |

The substantial difference between A's first and subsequent generations is consistent with the installed interpreter route. These observations do not isolate compiler lowering, activation and VM execution into separate per-generation phases.

### 11.4. P4 – cold and warm execution

The comparison uses two fresh instances of the same fixture per observation, with identical linked caller, argument `4`, result `7`, and initially cold target-node caches. Fixture construction is excluded from both intervals. Route B's measured production includes initialization of its separate SHEAR compiler runtime; this route-specific cost is not excluded.

For each of three observations:

- `T_B` includes production for every target/caller node, admission for every produced chunk, and one admitted execution.
- `T_H` is one ordinary host execution on the independent reference fixture, including lazy lowering.
- Warm executions are separate measurements after the cold execution.

| Measurement | Observations (ms) | Median (ms) | Range (ms) |
| --- | --- | ---: | ---: |
| B production | 8.434757, 8.048946, 7.856976 | 8.048946 | 7.856976–8.434757 |
| B admission | 1.212718, 1.176401, 1.180669 | 1.180669 | 1.176401–1.212718 |
| B admitted execution | 0.683779, 0.648633, 0.655025 | 0.655025 | 0.648633–0.683779 |
| **B total cold** | **10.331254, 9.873980, 9.692670** | **9.873980** | **9.692670–10.331254** |
| **Host total cold** | **0.055123, 0.056135, 0.052839** | **0.055123** | **0.052839–0.056135** |
| B warm execution | 0.686413, 0.639887, 0.628335 | 0.639887 | 0.628335–0.686413 |
| Host warm execution | 0.022131, 0.022001, 0.021791 | 0.022001 | 0.021791–0.022131 |

The fixed P4 ratio is:

    median(T_B) / median(T_H) = 179.126317

**P4 is falsified** against its prespecified maximum of 10. The dominant measured cold component is production, which includes SHEAR compiler-runtime initialization and compilation of the witness nodes. The diagnostic did not time those two subcomponents separately; a reusable compiler runtime could change the cost distribution, but no such optimization was measured here. Admission and admitted execution also exceed the host reference independently. The warm comparison is reported separately and does not substitute for P4.

These measurements compare the implemented prototype with ordinary host execution, not optimized production implementations. They do not establish the asymptotic cost of a permanent admission cache, shared compiler runtime or machine integration. No post-observation experimental revision was made.

### 11.5. Small edit and activation

The diagnostic edits `target(x)` from `x + 3` to `x + 5` using `define`, prepares a separate candidate runtime, and produces, admits and executes the candidate's target-node chunks there. It then activates the transformation on the original runtime. At `x = 4`, the candidate's admitted execution returns `9`, but the post-activation result of `9` is obtained through ordinary host execution on the original runtime, not through admitted chunks.

| Phase | Elapsed (ms) |
| --- | ---: |
| Candidate preparation through `define` | 13.397810 |
| Candidate compiler production, admission and verification execution | 10.418749 |
| Original runtime `activate` | 1.194154 |
| **Total measured interval** | **25.010713** |

This is one measured edit, not a three-observation latency distribution. The candidate phase includes an admitted verification run, so it is not an isolated compilation-only cost. Candidate construction and execution occur outside the original runtime's active state. The candidate registry is attached to that separate runtime; artifacts are not transferred to the activated original runtime. The Plan test independently verifies rejection of incompatible old artifacts, but the spike does not demonstrate admitted execution following activation or reuse of unchanged-node artifacts.

Task 23's corrected native/VM compiler timing, traced-allocation baseline, derived-artifact sizes and state-content proxy remain in `docs/content_baseline.md` sections 5.7 onward. Their separate revision, workloads and measurement methodology must not be conflated with these Task 29 measurements.

### 11.6. P1–P5 outcomes

| Prediction | Outcome | Evidence and boundary |
| --- | --- | --- |
| P1 – wrapper route changes active source | **Supported** | Existing `swap_all` installs executable wrappers; retained source twins are separate |
| P2 – existing compiler needs a per-node entry | **Supported** | Existing compiler emits expanded chunks; spike implements and differentially tests the separate node-aware SHEAR compiler |
| P3 – authentic structural admission can work | **Supported for W0** | Genuine output admitted; forged evidence, wrong node/version, changed instructions, foreign child and unlinked target rejected |
| P4 – cold ratio at most 10 | **Falsified** | Measured ratio 179.126317 on the equivalent executable witness |
| P5 – additional provenance tracing is necessary | **Supported** | Explicit producer, admission and execution boundary events establish the tested witness's artifact identity; existing rebuild instrumentation alone cannot do so |

Admission success is evidence of origin and compatibility, not a proof that arbitrary compiler output implements the intended semantics. Correctness evidence comes from the independent witness result and the four-kind differential comparison. A passing test suite does not imply system-wide producer provenance.

### 11.7. Admission rule and residual trust

The experimental admission rule accepts a chunk only when:

1. Its opaque handle identifies an observed SHEAR compiler result.
2. The supplied chunk matches that observed result exactly under canonical serialization.
3. The target state object, node, version and owning function match the producer record.
4. The node has a supported kind and the expected instruction sequence and arities.
5. Child evaluations name the node's actual owned children; linked calls target a permitted function with the required argument count.
6. An admitted execution resolves its required chunks from the state/version-bound registry and rejects absent or incompatible entries rather than lowering them on demand.

The host records a digest and producer compiler identity/version. Trace events are host-maintained, and the producer event identifies the actual SHEAR compiler function used. Admitted artifacts are not stored in semantic state.

The temporary implementation intercepts machine chunk lookup with process-global Python method patching guarded by a lock. This is an experimental execution boundary, not a deployable isolation or concurrency mechanism. The lock does not serialize unrelated machine executions that do not cooperate with it. Registry lifetimes, compiler invalidation and host-only access to admission need a permanent design.

The validation is bounded to `lit`, `arg`, `add` and `call`. It checks known structures and references but is not a general-purpose instruction verifier. It does not verify arbitrary semantic equivalence, capability safety, control-flow effects or completeness of dependencies outside the witness.

### 11.8. W1 – tier-1 and tier-2 corpus inventory

This inventory uses the operation statuses in `docs/bootstrap.md` section 2. Here, “A” refers to the current SHEAR-written VM and its existing compiler; “B” refers only to the four-kind admitted spike. Task 28's instruction-level `S` status does not establish a complete source-to-execution route.

| Corpus requirement | Route A | Route B | Prerequisite and owner |
| --- | --- | --- | --- |
| Literals, arguments, addition | SHEAR lower S; VM S | Executed and differentially tested | W0 completed for these kinds |
| Other arithmetic and comparisons (`sub`, `mul`, `lt`, `eq`) | SHEAR lower S; VM S | Not implemented | Extend node-aware compiler and admission – Task 30 |
| Conditional/sequence control (`if`, `seq`) | SHEAR lower S; VM S | Not implemented | Branch, jump and child-reference semantics – Task 30 |
| Statically linked calls and recursion | VM supports `CALL` but may delegate through host `applyv` | Direct linked `CALL` executed | Eliminate undeclared transitive host fallback – Task 30 |
| Tuples, indexing, slicing, concatenation and `let` | SHEAR lower S; VM S | Not implemented | Add tuple, lexical-binding and safety checks – Task 30 |
| Function references, `apply`, `applyv` | SHEAR lower S; VM S at instruction level, but references may delegate to host | Not implemented | Indirect dispatch, closures and route provenance – Tasks 30–31 |
| Cells (`read`, `write`) and constraints | SHEAR lowering S; VM D for `READ`/`WRITE` | Not implemented | Runtime cell services and verified execution – Tasks 30–31 |
| Code and link reflection (`code`, `linksof`) | SHEAR lowering S; VM D for `CODE`/`LINKS` | Not implemented | Explicit host reflection boundary and version policy – Task 30, D4 |
| Quote/unquote and code construction | SHEAR lowering D; VM quote D; `GOTO` supports unquote at instruction level only | Not implemented | Whole source-expression semantics, not isolated `GOTO` – Tasks 30–31 |
| `function`, `activate`, `trial` | SHEAR lowering D; VM D | Not implemented | Candidate construction and live-evolution route – Task 31 |
| Closures | SHEAR lowering S; VM S for supported subset | Not implemented | Capture and held-version semantics – Task 31 |
| Catchable and raised errors (`catch`, `raise`) | SHEAR lowering D; VM D for `CATCH`/`FAIL` | Not implemented | Error handlers and preserved error provenance – Tasks 30–31 |
| Invalid code | Rejected on existing paths, with differing diagnostics | Not admitted by the four-kind route | Uniform fail-closed semantics – Task 30 |

Tier-1 side effects and self-modification, and tier-2 higher-order composition, are therefore **not covered end-to-end** by the spike. A successful route-A bootstrap or route-B linked call cannot be generalized to these canaries.

Additional gaps include VM interpretation of `READ`, `WRITE`, `CODE`, `LINKS`, `QUOTE`, `FUNCTION`, `ACTIVATE`, `TRIAL`, `CATCH`, `FAIL` and `RAISE`; fixed host services for reflection, cells, activation, trials and errors; and transitive `CALL`/`APPLY`/`APPLYV` dispatch without unrecorded host-compiled program code. Task 30 owns complete execution-route provenance and operation coverage for the selected hosted workload; Task 31 owns full live-evolution coverage.

### 11.9. W2 – live-evolution inventory

| Mechanism | Route A today | Route B today | Blocker / owner |
| --- | --- | --- | --- |
| Candidate construction | Host `define` and existing graph construction; not SHEAR-VM-complete | Host `define` demonstrated for one edit | Integrated compiler/candidate pipeline – Tasks 30–31 |
| Trial and isolated candidate execution | Host trial service exists; VM `TRIAL` missing | Candidate admitted execution demonstrated, not `trial` semantics | Trial isolation, effects and rejection – Task 31 |
| Activation | `swap_all` uses host activation and replaces semantic function definitions | Host activation demonstrated externally; the post-activation result uses ordinary host execution, not admitted artifacts | Transfer/admission of artifacts across activation – Task 31 |
| Rejection and errors | Host guards and exceptions; VM lacks catchable-error instructions | Rejects invalid admission and missing artifacts; no general language error route | Complete failure categories and handler behavior – Task 31 |
| Continuity across edits | Host transformation/matching services exist | Registry is runtime-local, keyed by state ID, node and version, and checks exact state-object identity; changed state cannot reuse even unchanged-node entries | Per-node reuse, continuity mapping and dependency invalidation – Task 31 |
| Held frames and in-flight code | Host machine holds versions; VM source/version correspondence is not fully verified | Uses held machine state for chunk lookup; no concurrent activation witness | Prove old/new frame behavior and routing – Task 31 |
| Closures | VM closure subset implemented, with representation distinct from host closures | No admitted closure execution | Capture, application and retirement semantics – Task 31 |
| Retirement and lifetime | Host runtime retires versions; wrapper/VM artifact lifetime is not integrated | No artifact-retirement or registry cleanup protocol | Hold-aware artifact lifecycle – Task 31 |

Only the stated narrow behaviors were exercised in Task 29. The table is an inventory, not an assertion that any route supports live evolution end-to-end.

### 11.10. Costly-to-change provisional interfaces

**Instruction set and operand conventions.**

- **Route A:** Depends on the SHEAR interpreter's expanded instruction format and its partial operation table. Adding full instruction support means changing the embedded compiler and interpreter, including stack, error, effect and tail-position handling. Its use of host `applyv` for references also requires deliberate transitive routing changes.
- **Route B:** Depends directly on host per-node chunks, `EVAL` child `EntityID`s, typed operands, instruction ordering, and the machine's cursor conventions. Admission currently validates a hardcoded opcode-sequence template for each supported node kind, including type guards. Extending the supported vocabulary therefore duplicates part of lowering's instruction structure in the verifier and requires coordinated changes to the SHEAR compiler, validation templates and host machine. This maintenance burden becomes significant beyond the four-kind witness.
- **Reversal cost:** Once large programs compile against either format, migration affects compiler output, verifier/admission behavior, executable caches, runtime dispatch and regression fixtures. Route B makes the host chunk ABI a particularly important compatibility surface; route A makes the interpreted instruction vocabulary important.
- **Open owner decision:** Whether the provisional host instruction set is the durable common IR or whether a versioned, route-independent executable IR should precede Task 30. No new instruction semantics are decided here.

**The semantic version observed by `code`.**

- **Route A:** The existing wrapper path reflects active compiler wrappers while source twins carry the original program. A wrapper-free route needs a clear rule for whether reflection uses active state or the version held by the calling frame; otherwise a compiler may inspect a different definition from the one executing.
- **Route B:** Admission and execution are bound to the held node's version, but `code` itself remains the existing host operation. Reflection and compilation could disagree if `code` reads active definitions while an in-flight call continues on a held version.
- **Reversal cost:** Changing active versus held/caller-version semantics later alters compiler dependencies, cache invalidation, continuity following, closure behavior, recursive compilation and observable results under activation.
- **Open owner decision:** Keep today's active-version `code` view, adopt a held/caller-version view, or introduce an explicit version-selection facility. Task 29 changes none of them; D4 and subsequent language review must settle the policy before depending on it.

**Node identities in compiler output.**

- **Route A:** Existing recursively expanded chunks do not preserve the same per-node execution boundaries as the canonical graph. Making this route source-preserving requires an identity/dependency map outside expanded bytecode, or a revised interpreter representation retaining node references.
- **Route B:** The tested per-node chunks contain actual child and linked-function `EntityID`s, enabling trace correlation without replacing semantic definitions. However, the current admitted registry is attached to one runtime, indexed by `(StateID, EntityID, VersionID)`, and also checks exact state-object identity. A state change consequently prevents reuse of every previously admitted entry, including unchanged nodes. Precise per-node invalidation or transfer to an activated state is a possible future design, not a demonstrated property of this spike.
- **Reversal cost:** Moving between expanded children, semantic `EntityID`s and opaque execution references changes compiler APIs, dependency tracking, artifact identity, caching, continuity transfer and reproducibility. Per-function expansion would also widen invalidation after node edits.
- **Open owner decision:** Retain explicit semantic node IDs in derived chunks, adopt opaque version-pinned references, or use expanded child chunks with a separately maintained provenance map. No new program-visible node-identity exposure is authorized by this spike.

### 11.11. Recommendation and remaining decisions

**Recommendation to the owner – conditional preference for route B as the Task 30 architecture, not a D3 decision.**

Route B has a demonstrated narrow trust and source-preservation boundary, precise per-node output and an explicit admitted-execution trace. It avoids route A's current source-wrapper violation and better matches the existing per-node identity model. However, it **failed P4 by a large margin**, cannot yet rebuild the compiler, and relies on temporary global machine interception. Its performance and completeness do not justify accepting it as production machinery now.

Route A demonstrates three actual compiler rebuild generations but continues to replace active semantic source and contains host-delegated execution paths. Its wrapper-free form is a proposed design rather than observed behavior. It remains useful as a separate compiler/VM correctness reference and a competing D3 option.

For a route-B Task 30 plan, prioritize a reusable compiler runtime, persistent admission with deliberate unchanged-node reuse across states and activation, full operation coverage, maintainable structural validation, and an integrated machine routing boundary. Measure cold and warm costs again without changing the fixed Task 29 P4 result. For route A, require a concrete source-preserving dispatcher and transitive VM-only execution account before it can satisfy the canonical-source gate.

The owner must still decide D3 (execution route), D4 (hosted workload and permitted host boundary), the provisional budgets, and the costly-to-change language/IR interfaces above. The present spike supplies evidence for those decisions but makes none of them.

Task 30 must also remove, replace or explicitly promote `shear/execution_route_spike.py`, including an explicit mutation-testing decision. Task 31 remains responsible for the live-evolution mechanisms identified in W2. Independent Review must verify the implementation, trust assumptions, trace coverage, timings, Plan-file integrity and scope boundaries before Publish.


### 11.12. Subsequent owner decision (2026-10-10)

**D3 – Decided** after this report (roadmap.md, PR #91): adopt the hybrid
architecture, with authenticated host execution of SHEAR-compiled per-node
artifacts as the primary hosted route and the SHEAR-written VM retained as
an alternative and independent correctness reference. Shared compiler/IR
and runtime implementation are preferred where practical, without
compromising independent behavioral oracles or requiring VM feature parity.

D4 remains open before Task 30 planning. If its workload differs materially
from the recommended one, renewed route validation is required; D3 is
revisited only if the new evidence undermines the selected architecture.

This postscript records the owner's decision, not a revised experimental
result. Sections 1–11.11, including the original predictions, measured P4
failure, coverage limitations and recommendation, remain historical evidence.
