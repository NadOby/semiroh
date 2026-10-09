# Handoff

Read `CLAUDE.md`, the Workflow and task 29 sections of `docs/roadmap.md`, and the task specification. Verify this checkpoint against GitHub; it is not evidence by itself.

## State

- Task: 29, execution-route spike, issue #65.
- Role: Plan – final revised contract; Execute next.
- Branch: `task/29-execution-route`.
- Base `main`: `dbe92c6e6450db479d22a203011f9c974ba00089`.
- Protected Plan baseline: `bd114538782c7816f84464430c56a2d1be9046ce`.
- This handoff commit follows that baseline. Execute must verify the final branch head and ancestry.
- D3 and D4: Open. No permanent execution-route or language decision.
- No production changes, golden changes or PR.

## Protected Plan contract

Read `docs/spikes/execution_route.md` in full. It is the authoritative experimental contract.

Protected files:

- `docs/spikes/execution_route.md` – scope, experimental interfaces, admission and trace rules, predictions, measurements, acceptance and decision gates.
- `tests/test_execution_route.py` – 18 behavioral acceptance tests.
- `tests/lanes.py` – one added registration in `cross-boundary`, with no unrelated differences from `main`.
- `tests/mutation_catalog.py` – one temporary omission for the experimental module.

No `tests/golden_changes/GH-65.txt` is needed or authorized.

Execute must not weaken the acceptance tests, change the spec to match an implementation or silently decide a language-level question. A material contract defect returns to Plan.

## Experimental implementation

The sole authorized new Python implementation module is:

    shear/execution_route_spike.py

It contains the experimental host boundary and the node-aware compiler expressed as SHEAR `Function` data.

The SHEAR compiler must genuinely execute. Python may construct descriptors and observe the returned result, but must not perform lowering attributed to the SHEAR compiler.

Provisional API:

    produce(runtime, entity) -> (chunk, evidence)
    admit(state, entity, version, chunk, evidence) -> admitted
    run_admitted(runtime, entry, *args) -> result
    trace(runtime) -> tuple[RouteEvent, ...]
    AdmissionRejected

Compiler output is a per-node host chunk with semantic child `EntityID` references. The mandatory node kinds are `lit`, `arg`, `add` and `call`.

Admission is structural plus trusted host-observed producer evidence. It binds node, version, ownership, permitted references, producer invocation and exact output. No semantic second compiler, recomputation through host lowering or program-visible admission authority is allowed.

Trace events must identify the actual producer, admission and executed artifacts. A claimed route without observed execution does not pass.

The experimental module is registered under `OMITTED` in the mutation catalog. It remains subject to behavioral and adversarial testing. Task 30 must remove, replace or explicitly promote it, including reconsideration of mutation coverage.

## Scope

W0 is executable:

- Route A: reproduce the existing SHEAR-VM compiler rebuild through generations 1–3, documenting the wrapper/source-preservation limitation.
- Route B: produce, admit and execute per-node artifacts without modifying canonical semantic definitions.
- Exercise child nodes and a linked call; attempt compiler rebuilding and record achieved generations and blockers.
- Give a bounded wrapper-free route-A design or a concrete counterexample; implementation is not required.

W1 and W2 are coverage inventories only. Record ordinary-corpus and live-evolution gaps against the Task 28 matrix. Do not implement missing capabilities for these workloads in Task 29.

Keep D3, D4, by-value capability semantics and permanent compiler identity exposure unresolved.

## Acceptance and testing

The 18 Plan-owned tests cover:

- Genuine SHEAR-produced chunks and successful admission.
- Per-node lowering for all four mandatory node kinds, differentially checked against host lowering used only inside tests.
- Rejection of arbitrary evidence, SHEAR-program-generated forgery, genuine-handle misuse, wrong node, stale version, modified instructions, foreign child and unlinked function operands.
- Absence of host lowering during admission and target production.
- Admitted execution without ordinary host-cache or lowering fallback.
- Transitive execution through an admitted linked callee.
- Production/admission/execution trace identity and compiler attribution.
- Semantic source preservation and post-edit invalidation.

These tests are intentionally red until Execute implements the missing experimental module.

The mutation-catalog inventory is also expected to fail while its registered experimental module does not exist.

No green CI run has been verified for this Plan. Use GitHub Actions and report actual results, including failures.

## Predictions and evidence

P1–P5 are fixed in the spike specification before Execute. Only one documented experimental revision is allowed; material redesign returns to Plan.

P4 uses the defined cold comparison:

    T_B = production + admission + admitted execution
    T_H = ordinary host execution including lazy lowering

The predicted median ratio is `T_B / T_H <= 10`, using identical executable witnesses and matched cold-cache conditions. Route-B-specific compiler initialization is included; common fixture preparation is excluded.

Mandatory evidence:

- Compiler rebuild timings for every achieved generation.
- Cold production, admission and execution timings, plus the comparable host reference.
- Warm execution timing separately.
- Small-edit-to-activation phase timings.
- At least three untraced observations for comparable timings, including runner, commit, input and cache conditions.
- W1/W2 inventories with explicit blockers.
- Genuine producer, admission and execution trace evidence.
- Differential correctness and negative admission evidence.

Write results in `docs/spikes/execution_route.md` section 11, not a parallel report in `docs/bootstrap.md`.

The final recommendation must assess the Provisional interfaces made expensive to change by each route:

1. Instruction set and operand conventions.
2. Which semantic version `code` observes.
3. Node identities and references in compiler output.

For each, compare both routes, reversibility costs and unresolved owner choices.

## Independent Review

Review is a separate, read-only role. It must fetch the implementation head and compare all Plan-owned files against `bd114538782c7816f84464430c56a2d1be9046ce`.

Independently examine:

- Genuine SHEAR compiler execution rather than disguised host lowering.
- Structural admission and non-forgeable producer evidence.
- Differential correctness and adversarial rejection.
- Actual admitted execution without untraced host fallback.
- Semantic-source preservation, version binding and invalidation.
- Trace completeness for the claimed witness.
- W0 results, W1/W2 limits, timings, predictions and reproducibility.
- Mutation-catalog handling and absence of unrelated changes.

Classify findings as verified defects, limitations, hypotheses or documentation drift. Resolve verified defects and obtain another independent Review.

## Decision and Publish boundary

The result supplies evidence and a recommendation, not an automatic D3 decision. D3 remains with the owner; D4 must also be settled before Task 30 planning.

Do not open a PR before accepted independent Review and the necessary owner decision. Publish rechecks `main`, CI, Plan integrity and the final diff, and prepares the PR closing #65.

## Next

Start `Execute task 29` in a fresh chat after verifying this handoff commit.

Follow the owner's mobile GitHub editing protocol: read-only tools, complete copyable file content, one file and commit at a time, confirmation by `Done`, and independent verification after each commit. No terminal dependency.
