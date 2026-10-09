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

**Open.** Execute will record:

- Achieved W0 results and precise blockers for each route.
- W1/W2 coverage inventories.
- P1–P5 outcomes and any authorized experimental revision.
- Admission and tracing evidence with CI links.
- Differential correctness evidence.
- Timing measurements and limitations.
- Admission rule and residual trust assumptions.
- Costly-to-change analysis for the instruction set, the version seen by `code`, and node identities in compiler output.
- A recommendation for D3, explicitly distinguished from the owner's decision.

A successful narrow spike establishes feasibility, not completion of Tasks 30 or 31.
