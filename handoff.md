# Handoff

Read `CLAUDE.md`, `docs/roadmap.md`, and the relevant specifications
before continuing. Independently verify this checkpoint against GitHub.

## Current state

- Task 29 – Execution route for compiler-produced chunks.
- Issue: #65.
- PR: #91, https://github.com/NadOby/shear/pull/91
- Branch: `task/29-execution-route`.
- Pre-handoff branch head: `cf2b34e3e7630d451a2138790a136a583d12f3c4`.
- Checked `main` before reconciliation: `dbe92c6e6450db479d22a203011f9c974ba00089`.
- Role: Resolve of pre-merge documentation review, awaiting fresh
  independent Review before owner merge.
- Task 29 is marked Implemented (PR #91).
- The original implementation and final Resolve state passed independent
  Review. Two subsequent pre-merge reviews found P2 documentation
  inconsistencies and P3 documentation drift.
- Those findings have been addressed by documentation-only commits.
  Their resolution is not yet independently accepted.
- Ordinary CI passed on preceding reconciliation commits. CI for
  `cf2b34e` was in progress at this checkpoint.
- `CHANGES.md` contains the original Task 29 entry and an append-only
  pre-merge documentation reconciliation entry.

## D3 – Decided

Adopt a hybrid execution architecture.

- Route B is the primary hosted execution path: authenticated,
  SHEAR-compiler-produced per-node artifacts executed by the existing
  host machine with structural, fail-closed admission and provenance.
- Admission is host-internal, bound to semantic node and version, and
  requires observed compiler provenance. Arbitrary program-supplied
  bytecode cannot be installed or executed directly by the host.
- Retain the SHEAR-written VM (route A) as an alternative implementation,
  independent correctness reference and possible bootstrap component.
- Share semantic contracts, operation metadata, compiler pipeline,
  compatible executable IR and runtime services where practical.
- Task 30 Plan must identify concrete shared implementation components,
  not merely compatible interface descriptions.
- Keep execution-specific machinery separate. Do not build two complete
  production executors in parallel or require immediate VM feature parity.
- Shared implementation must not make correctness checks self-referential.
  Keep independent behavioral oracles.
- The canonical program remains the semantic hypergraph. Executable
  representations are derived artifacts.
- Python, current bytecode encoding, admission implementation, hashes
  and caches are replaceable, subject to preserving the relevant semantic,
  identity, integrity, provenance, activation and lifetime guarantees.
- Exact shared IR and adapter boundaries remain provisional.
  Task 30 does not require a broad rewrite of the existing SHEAR VM.

Task 27's source twins, literal-chunk wrappers, generation record and
dependency map remain historical/reference-route test scaffolding.
They are not part of the primary hosted execution path. Wrappers
are program code, not exempt fixed interpreter machinery. They
must not displace canonical source in the hosted-bootstrap pipeline.
Existing reference-route regression tests remain valid.

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
with live evolution.

The original Task 29 Plan required redoing the route comparison before
D3 acceptance if D4 selected a materially different workload. The
owner subsequently accepted D3 as an architectural principle before
D4, superseding the timing gate but not workload validation.

If D4 materially departs from the recommended workload, Task 30
planning must require renewed route validation. Revisit D3 only if
that evidence undermines the selected architecture. The performance
and canonical-source acceptance anchors remain in force.

Instruction-set/IR conventions, the version observed by `code`,
and node identities exposed through compiler output retain their
existing provisional or open status.

## Task 29 evidence

Protected Plan baseline:
`deb03aa3ffc198df8e19fa14da59db904f879a1b`

Tested Execute revision:
`6ebbc698c881528b53b37c63b5b090f82eb4a037`

Final original Resolve revisions:
`9508ec1989e3d7296e3f6967bd3b4a2ce85de2bb`
`cc4d6df5382d73023e9c37e3496ddc18cce3fb8a`

Specification and complete experimental report:
`docs/spikes/execution_route.md`

Original CI evidence:
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
- Admission proves observed artifact origin and structural compatibility,
  not semantic correctness of arbitrary compiler output.

## Pre-merge review resolution

Two independent pre-merge reviews of PR #91, at commit `a8e687e`,
identified overlapping documentation defects.

P2 – D3/D4 comparison gate:

- `docs/roadmap.md` now records that the owner accepted D3 as an
  architecture principle, explicitly superseding the Plan's
  before-D3 timing gate.
- A materially different D4 workload still requires renewed validation.
  D3 is reconsidered if that evidence undermines the architecture.
- Task 29's actual bounded W0 comparison is distinguished from the
  originally proposed complete workload comparison.

P2 – Host execution admission:

- `docs/bytecode.md` section 8 now permits authenticated
  SHEAR-compiler-produced per-node artifacts through host-internal
  admission, bound to semantic node and version with observed producer
  provenance.
- The prohibition on arbitrary program-visible bytecode installation
  remains in force.
- `docs/self_hosting.md` distinguishes historical host-only lowering
  from D3's permitted authenticated artifact route.

P2/P3 – Hybrid VM scaffolding and Task 30:

- `docs/vm_in_shear.md` now classifies Task 27's swap wrappers and source
  twins as historical/reference-route test scaffolding.
- `docs/roadmap.md` clarifies Task 30's non-exempt program-code wrappers
  and requires concrete shared compiler/IR and runtime components
  alongside independent behavioral oracles.

P3 – Historical and normative references:

- `docs/bootstrap.md` distinguishes decided D3 from open D4,
  without changing the Task 28 operation matrix or measurements.
- `docs/corpus.md` preserves the dated canary table and adds a
  post-D3 clarification for canaries 11 and 12.
- `docs/spikes/execution_route.md` appends a subsequent-owner-decision
  postscript; the original Plan contract, experimental results,
  predictions and recommendation are unchanged.

The documentation reconciliation starts after `a8e687e` and ends,
before this handoff commit, at `cf2b34e`. It changes:

- `docs/bytecode.md`
- `docs/roadmap.md`
- `docs/vm_in_shear.md`
- `docs/bootstrap.md`
- `docs/self_hosting.md`
- `docs/corpus.md`
- `docs/spikes/execution_route.md`
- `CHANGES.md` (append-only)

No production implementation, tests, golden records or experimental
measurements were intentionally changed in this reconciliation.
Independent Review must verify that claim from the repository diff.

## Deferred work

Task 30 – issue #66:

- Integrate the hosted execution path without the experimental
  process-global interception mechanism.
- Extend the SHEAR compiler to the D4 workload.
- Provide complete provenance for executed program-code artifacts,
  with no hidden host-lowering fallback.
- Address artifact lifecycle, verifier maintenance, dependency tracking,
  cross-state reuse and compiler rebuilding.
- Reassess performance on comparable workloads, including any
  materially different D4 workload.
- Remove, replace or explicitly promote
  `shear/execution_route_spike.py`, including its test-infrastructure
  dependencies and mutation-catalog treatment.
- Identify shared compiler/IR and runtime implementation components
  without requiring VM feature parity or weakening independent tests.
- Preserve canonical source; reference-route wrappers do not count
  as hosted-bootstrap implementation.

Task 31 – issue #67:

- Execute live evolution through the hosted bootstrap path.
- Demonstrate candidate construction, trial, activation, rejection,
  held frames and closures, continuity and retirement.

Neither task's deferred work is claimed completed by Task 29.

## Next action

1. Fetch the current PR #91 head, current `main`, `CLAUDE.md`,
   roadmap and this handoff. Independently review the documentation
   reconciliation against both pre-merge reviews.
2. Check every P2/P3 finding, the D3/D4 decision boundaries, the
   Task 30 wrapper policy, and whether shared implementation is
   sufficiently specified without requiring premature VM refactoring.
3. Verify original Plan-owned acceptance tests and specifications,
   production implementation, golden records and measurements remain
   intact. Confirm final diff and CI.
4. If Review accepts the final state, the owner may merge PR #91.
   Otherwise perform another bounded Resolve and fresh Review.
5. Settle D4 before starting Plan Task 30 in a separate fresh context.

GitHub access for the assistant is read-only. The owner works from
mobile with complete-file, one-commit-at-a-time editing and independent
verification after each commit. Present edits in this order:
commit message, clickable GitHub edit link, complete inline file.
`CHANGES.md` and historical postscript updates are append-only.
