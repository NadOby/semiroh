# Handoff

Read `CLAUDE.md`, `docs/roadmap.md`, and the relevant specifications
before continuing. Independently verify this checkpoint against GitHub.

## Current state

- Task 29 – Execution route for compiler-produced chunks.
- Issue: #65.
- PR: #91, https://github.com/NadOby/shear/pull/91
- Branch: `task/29-execution-route`.
- Pre-handoff branch head: `ac1942f766acda6d1efaf233d271e9340da313e4`.
- Checked `main`: `dbe92c6e6450db479d22a203011f9c974ba00089`.
- Role: Publish, awaiting owner merge.
- Independent Review accepted the final Resolve state.
- The latest checked branch CI completed successfully.
- Task 29 is marked Implemented (PR #91) in the roadmap.
- `CHANGES.md` has one append-only Task 29 entry.

## D3 – Decided

Adopt a hybrid execution architecture.

- Route B is the primary hosted execution path: authenticated,
  SHEAR-compiler-produced per-node artifacts executed by the existing
  host machine with structural, fail-closed admission and provenance.
- Retain the SHEAR-written VM (route A) as an alternative implementation,
  independent correctness reference and possible bootstrap component.
- Share semantic contracts, operation metadata, compiler pipeline,
  executable IR and runtime services where practical.
- Keep execution-specific machinery separate. Do not build two complete
  production executors in parallel or require immediate VM feature parity.
- Shared implementation must not make correctness checks self-referential.
  Keep independent behavioral oracles.
- The canonical program remains the semantic hypergraph. Executable
  representations are derived artifacts.
- Python, current bytecode encoding, admission implementation, hashes
  and caches are replaceable, subject to preserving the relevant semantic,
  identity, integrity, provenance, activation and lifetime guarantees.
- The exact shared IR and adapter boundaries remain provisional.
  Task 30 does not require a broad rewrite of the existing SHEAR VM.

Long-term direction: native Linux execution with LLVM as the first
machine-code producer. Compiling the SHEAR VM itself remains possible.
A custom MLIR dialect is optional, not selected. Native execution
and removal of Python are later milestones, not Task 30 requirements.

## D4 – Open

Before planning Task 30, the owner must settle:

- The hosted-bootstrap workload, using Task 28's operation and service
  inventories.
- Exactly which Python host services remain permitted.
- Provisional compiler rebuild and small-edit-to-activation budgets,
  using Task 23's measured baseline.

Recommended workload: compiler rebuilding itself and the corpus,
with live evolution. D3 does not decide D4.

Instruction-set/IR conventions, the version observed by `code`,
and node identities exposed through compiler output retain their
existing provisional or open status.

## Task 29 evidence

Protected Plan baseline:
`deb03aa3ffc198df8e19fa14da59db904f879a1b`

Tested Execute revision:
`6ebbc698c881528b53b37c63b5b090f82eb4a037`

Final Resolve revisions:
`9508ec1989e3d7296e3f6967bd3b4a2ce85de2bb`
`cc4d6df5382d73023e9c37e3496ddc18cce3fb8a`

Specification and complete experimental report:
`docs/spikes/execution_route.md`

CI evidence:
https://github.com/NadOby/shear/actions/runs/37981959588

- Route A rebuilt generations 1, 2 and 3, but installed
  literal-chunk wrappers instead of preserving active canonical source.
- Route B demonstrated SHEAR-produced artifacts for `lit`, `arg`,
  `add` and `call`, authenticated admission and a linked-call witness.
- Route B could not rebuild the compiler: generation 0 only.
- The original P4 performance prediction failed. Route B cold median:
  9.873980 ms; ordinary host median: 0.055123 ms; ratio: 179.126317,
  against the predicted maximum of 10.
- Route B warm execution median: 0.639887 ms; ordinary host warm
  execution median: 0.022001 ms.
- Route A rebuild and Route B witness measurements are not directly
  comparable workloads. Neither route is established as sufficiently
  fast for the final workload.
- The activation witness did not establish admitted execution after
  activation or cross-activation artifact reuse.
- All ordinary test lanes passed on the tested Execute revision,
  including 18 Plan-owned tests. Golden records: 55 unchanged.
- Mutation testing was not run for Task 29; the experimental module
  retains its explicitly authorized temporary catalog omission.
- The protected Plan tests and specifications were preserved.
  Subsequent Publish changes were confined to roadmap, changelog
  and handoff documentation.

## Deferred work

Task 30 – issue #66:

- Integrate the hosted execution path without the experimental
  process-global interception mechanism.
- Extend the SHEAR compiler to the D4 workload.
- Provide complete provenance for executed program-code artifacts,
  with no hidden host-lowering fallback.
- Address artifact lifecycle, verifier maintenance, dependency tracking,
  cross-state reuse and compiler rebuilding.
- Reassess performance on comparable workloads.
- Remove, replace or explicitly promote
  `shear/execution_route_spike.py`, including its test-infrastructure
  dependencies and mutation-catalog treatment.
- Reuse shared compiler/IR and runtime machinery where useful without
  forcing VM feature parity or weakening independent tests.

Task 31 – issue #67:

- Execute live evolution through the hosted bootstrap path.
- Demonstrate candidate construction, trial, activation, rejection,
  held frames and closures, continuity and retirement.

Neither task's deferred work is claimed completed by Task 29.

## Next action

1. Verify the final PR #91 diff and CI after this handoff commit.
2. Owner reviews and merges PR #91, or requests further changes.
3. Settle D4 before starting Plan Task 30.
4. Start Task 30 in a separate fresh Plan context.

GitHub access for the assistant is read-only. The owner works from
mobile with complete-file, one-commit-at-a-time editing and independent
verification after each commit. Present edits in this order:
commit message, clickable GitHub edit link, complete inline file.
`CHANGES.md` is append-only.
