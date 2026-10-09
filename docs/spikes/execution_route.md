# Execution-route spike – Task 29

**Status: provisional.** Issue #65, roadmap section I, decision D3.

Plan revision after independent criticism of the initial Plan head `21d3f153bf8d1c10ae7b1744efb9f9c84bdb3848`. The original Plan was not accepted for Execute. This revision replaces its scope, predictions and acceptance contract.

No D3 or D4 decision is made here.

## 1. Question

Compare:

- A: the SHEAR-written VM executing compiler-produced chunks.
- B: the host machine executing SHEAR-compiled chunks admitted as derived artifacts of identified semantic nodes.

Preserve the semantic graph as canonical, with executable artifacts separate from semantic definitions. Neither route may silently replace unsupported compilation with host lowering.

Task 27's wrapper-based rebuild is a working baseline, not proof of source preservation: its active function bodies become wrappers containing literal chunks, while separate source twins retain the original code.

The spike must produce evidence sufficient for an owner decision, not implement the whole hosted-bootstrap milestone.

## 2. Scope

W0 – executable comparison:

- Run the existing generation-1 through generation-3 rebuild on route A as the baseline.
- Construct a bounded route-B witness in which a compiler written in SHEAR produces an identified node's executable chunk, the host admits it, and execution returns the independently expected result.
- Attempt the same compiler rebuild on route B. Record each achieved generation or the concrete blocker. An incomplete rebuild is not comparable with a complete rebuild.
- Preserve source identities and versions on the route-B witness; demonstrate actual use of the admitted artifact rather than a hidden host-lowered chunk.
- Check the producer and execution route of every chunk within the claimed witness. Do not claim global transitive provenance beyond that boundary.

W1 – ordinary-program coverage inventory only:

- Apply Task 28's matrix to the tier-1 and tier-2 corpora.
- Classify required operations, host services, delegated calls and missing instructions.
- Record the prerequisites and the task owning each gap. No new corpus-wide implementation is required.

W2 – live-evolution coverage inventory only:

- Evaluate candidate creation, trial, activation, rejection, continuity, old frames/closures and retirement against both routes.
- Identify blocked semantics and services. No new live-evolution implementation is required.

W1 and W2 are not executable acceptance workloads for this spike. Tasks 30 and 31 own their completion.

## 3. Provisional spike interfaces

These interfaces are internal experiments, not permanent SHEAR syntax, public operations or language semantics.

Place the bounded experimental API in `shear/execution_route_spike.py`:

    produce(runtime, entity) -> (chunk, evidence)
    admit(state, entity, version, chunk, evidence) -> admitted
    run_admitted(runtime, entry, *args) -> result
    AdmissionRejected

`entity` denotes a semantic code node, not its owning function. `version` is that node's `VersionID`. A runtime-scoped admitted-artifact table remains outside semantic state.

`produce` must invoke a genuine compiler function implemented in SHEAR. The host supplies a node descriptor containing the node's kind, payload, child-role identities, owner and relevant links. That descriptor is input data, not compiler output.

The SHEAR compiler produces one host-format per-node chunk, with child `EntityID` references rather than recursively expanded chunks. The host may construct the descriptor and observe the result, but may not obtain that result by invoking `bytecode.lower` or `bytecode.lower_value`.

This is a spike-only node-aware compiler entry. It does not change the program-visible `code` operation, which continues to return its existing representation. Whether SHEAR programs should later see node identities is an owner decision.

The test suite uses the named interface directly. Execute may choose internal data structures but must not substitute a materially different contract without returning to Plan.

## 4. Route-B admission

**Provisional recommendation: structural admission and trusted producer evidence, with differential compiler-correctness tests.**

Admission checks:

1. The node exists in the supplied state and has the claimed version.
2. The node is executable and belongs to a valid function.
3. The chunk is a well-formed, supported instruction sequence with valid operand types and control flow.
4. Child references in instructions belong to the identified node's semantic children.
5. Function/entity operands requiring link resolution refer only to links available to the node's owner.
6. The chunk is exactly the artifact whose production was observed by the trusted host. A changed chunk, even if structurally valid, is rejected.
7. The producer record binds the compiler function and generation, source state, node identity, version and exact output.
8. Runtime admission binds the artifact to its required state and dependencies. Changes that invalidate the binding cannot reuse the artifact.
9. Rejection never populates the executable cache and never switches to host lowering.

The verifier does not recompute semantic lowering. Structural validation does not prove that an arbitrary admitted chunk implements the correct program. Genuine compiler output can still contain a compiler bug.

Compiler correctness is checked independently through deterministic expected results and differential comparison with host lowering as a test oracle. That oracle must not participate in production or admission.

An independent semantic verifier would duplicate substantial compiler logic. Admission by host recomputation would collapse route B into the existing host-lowering path. Neither is included in this spike.

### Trusted producer boundary

Trusted Python runtime machinery observes the SHEAR compiler invocation and its returned chunk. The observation records the actual executed compiler identity, generation, input identity and version, and returned artifact.

An opaque evidence handle refers to this host-owned record. Program data, user-supplied generation numbers and copied or fabricated records do not grant admission authority.

Only internal host machinery can call `admit`. This spike adds no program-visible admission operation, compiler capability or mechanism for directly installing arbitrary executable chunks.

Evidence establishes origin and output integrity, not compiler correctness.

The implementation must demonstrate that evidence cannot be forged using ordinary program data. If the current host runtime cannot establish an authentic producer boundary without broader changes, record the blocker rather than weakening it.

## 5. Route A and open language choices

Evaluate the existing SHEAR-VM route, including its wrapper-based source-preservation failure.

Provide one bounded design for wrapper-free execution, or a concrete counterexample showing why that design cannot work with the current semantics.

No wrapper-free runtime implementation is required in Task 29. Specify how a proposed route would select derived artifacts without rewriting the active function definitions, and identify its call and closure consequences.

`READ`, `WRITE`, `CODE`, `LINKS`, `ACTIVATE` and other currently missing VM instructions remain coverage gaps. In particular, allowing by-value targets for cells or code reflection changes authority and capability semantics. This spike does not introduce those operations.

Owner decisions remaining open:

- D3 – permanent execution route.
- D4 – hosted workload, permitted host boundary and budgets.
- Whether structural admission plus differential correctness evidence is an acceptable trust model.
- Whether and how semantic node identities become visible to SHEAR programs.
- Whether program-visible compilation or artifact admission receives a capability.
- Whether by-value cell and reflection targets are allowed, and under what authority.

The provisional interfaces in section 3 do not decide these permanent questions.

## 6. Predictions before execution

P1 – The existing wrapper-based SHEAR-VM rebuild changes active semantic function bodies while preserving source twins. A wrapper-free design needs an execution-selection mechanism outside those bodies.

P2 – The current embedded compiler cannot directly supply host-format per-node chunks because it consumes collapsed expressions and emits expanded child chunks. The node-aware spike requires a distinct SHEAR-implemented entry.

P3 – Structural admission with trusted producer evidence can accept a genuinely SHEAR-produced per-node chunk and reject forged, stale or altered submissions without executing host lowering. If this requires a second semantic compiler, the proposed boundary fails.

P4 – For an equivalent executable witness, route B including artifact admission has median elapsed time at most 10 times the ordinary host-executed reference path. This is an experimental discriminator, not an accepted D4 performance budget. Report cold admission and warm execution separately. If equivalent coverage is unavailable, report P4 inconclusive.

P5 – The existing Task 27 host-lowering spy is insufficient to prove transitive producer provenance. A route-specific observer must identify produced and executed artifacts at the claimed boundary.

The task-23 baseline is approximately 0.037 s native and 5.264 s interpreted for `lower(lower)`, a ratio of approximately 142:1. These measurements do not predict admission overhead.

Execute receives one documented experimental revision after recording the falsifying observation and rationale. A material change in language semantics, admission policy or workload returns to Plan.

## 7. Plan-owned acceptance tests

Use `tests/test_execution_route.py`. Tests must exercise the actual spike interface; a formatted report is not acceptance evidence.

Required negative tests:

- Forged or program-supplied producer evidence is rejected.
- A valid producer handle attached to another node is rejected.
- A stale node version is rejected.
- An artifact modified after production is rejected, including a structurally valid modification.
- An `EVAL` referencing a non-child node is rejected.
- An instruction referencing an entity outside the owner's permitted links is rejected.
- Admission cannot call host lowering; a spy fails the test if it does.
- Rejected artifacts do not enter the admitted cache or execute through fallback.

Required positive tests:

- A genuine SHEAR-produced chunk is admitted for its exact node and version.
- The admitted chunk executes to an independently expected result.
- The active function body and semantic node versions remain unchanged.
- A demonstrated edit invalidates a stale admitted artifact.
- Host lowering of the target code nodes is not invoked during admitted execution.
- Producer observation and executed-artifact tracing identify the route actually used.

Tests may inspect the experimental API directly. They must fail on the original branch without the implementation for a behavioral reason, not because an evidence table or documentation heading is missing.

Tests of source-preserving wrappers may remain as characterization, but do not substitute for the new red tests.

Only the Plan role changes the acceptance contract. Execute adds further implementation tests without weakening Plan-owned cases.

No golden-record changes are intended.

## 8. Measurements

Use the corrected methodology in `docs/content_baseline.md` section 3.

Mandatory:
- Rebuild time by achieved generation, identifying which route and compiler produced each result.
- Cold producer/admission time and warm execution time, compared with equivalent host execution.
- One small edit through preparation, lowering/admission and activation, with phase and total latency and independently checked before/after behavior.

Use at least three untraced repetitions with median and range for comparable timed workloads. Record exact commit, runner, Python version, input and cache conditions.

Reuse Task 23's memory and artifact-size baseline. New memory, image-size and allocation measurements are optional unless a concrete route-specific mechanism creates an identified concern.

Do not compare timings for workloads with unequal functionality. Report blocked measurements as blocked, not as inferred values.

If a new machine boundary makes a run-context extraction necessary, identify the minimal responsibility and justify it before implementation. No general machine refactor is authorized.

## 9. Evidence and decision gates

Record the spike's observations, tests, coverage ledger, measurements and recommendation in this document, under `## 11. Execution results`. Keep `docs/bootstrap.md` as the Task 28 boundary inventory. No duplicate result table is required.

G1 – Source preservation: wrappers that replace canonical function bodies fail this condition.

G2 – Admission: only authentic, node/version-bound artifacts enter the host execution path. Wrong inputs fail closed.

G3 – Compiler correctness: structural admission is not a proof of semantic correctness. Require independent expected results and differential evidence, and report the residual trust assumption.

G4 – Workload: W0 executable evidence is the target; W1/W2 are coverage inventories. Incomplete work cannot be called implemented.

G5 – Cost: compare admission and execution against the matching host reference, using the fixed prediction rather than retrospective thresholds.

G6 – Owner authority: present results, alternatives, open risks and a recommendation. Do not decide D3, D4 or permanent authority semantics in Execute.

A successful narrow spike establishes feasibility, not the hosted-bootstrap milestone. A blocked or falsified candidate remains a legitimate experimental result but cannot be presented as an implemented route.

## 10. Role contract

Plan owns this specification, behavioral acceptance tests and lane registration. The accepted Plan head is recorded in `handoff.md` after revision.

Execute implements the bounded experimental API and witnesses, collects CI evidence and records the results in section 11. It does not decide the permanent execution route or rewrite acceptance expectations.

Independent Review compares Plan-owned files with the accepted Plan head, tests forged evidence and fallback paths adversarially, verifies actual producer attribution, checks scope and measurements, and identifies any change to Decided semantics.

Resolve handles verified Review defects. Publish follows accepted independent Review and the owner's D3 decision. No PR opens earlier.

Separate nonblocking improvements, including lane-edit process protection, remain follow-ups rather than additional production work in Task 29.

Task 30 owns the full hosted pipeline. Task 31 owns complete live evolution.

## 11. Execution results

**Open.** Execute records results here. No spike execution or result is claimed by this Plan.
