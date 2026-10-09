# Handoff

Compact checkpoint for the next chat. Claims are not evidence: verify
against the repository. Read `CLAUDE.md` and `docs/roadmap.md` first.

## State

- Task 23, issue #60, has completed Resolve and awaits fresh
  independent Review.
- Branch: `task/23-content-baseline`.
- Original Plan baseline: `c4a4bcc`.
- Revised Plan baseline: `564203e`.
- Previous reviewed implementation: `d138aa3`.
- Latest Resolve documentation commit: `fff6d07`.
- No task PR has been opened.

## Review findings and disposition

The previous independent Review reported four P2 findings.

- F1 – Incomplete conversion inventory. Addressed by adding
  `tests/content_baseline_evidence.py` and integrating its
  source-anchored mechanisms into `tests/content_baseline.py`.
  The original helper-call count remains separate.
- F2 – Unsupported duplication classifications. Addressed with
  named mechanism relationships, source-linked call-site evidence,
  explicit uncertainty statuses and exclusions. No site is declared
  redundant merely because its mechanism overlaps another.
- F3 – Edit-latency measurement included verification execution.
  Corrected the timer boundaries in
  `tests/content_baseline_measure.py`, retaining the correctness
  assertion and regenerating the measurements.
- F4 – Missing independent acceptance tests for measurement
  correctness. Resolved through Plan amendment `564203e`.
  Six deterministic negative and control tests use mocked runtimes
  without running benchmarks in ordinary CI.

These are Resolve dispositions, not independent Review acceptance.
No production semantic code or golden records were changed.

## Verified CI evidence

- Revised Plan CI:
  https://github.com/NadOby/shear/actions/runs/37902162561
- Resolve diagnostic revision:
  `375076fa6da98656efbd0fe0179a312e8fb981d0`
- Dispatched diagnostic:
  https://github.com/NadOby/shear/actions/runs/37912552583
- Diagnostic artifact ID: `11606884068`.
- Latest documentation CI:
  https://github.com/NadOby/shear/actions/runs/37916798393

All listed runs passed. The diagnostic artifact contains
`content-inventory.json` and `content-baseline.json`.

The updated inventory contains:

- 140 static helper-call sites: 127 direct, 13 recursive.
- 22 separately recorded conversion mechanisms.
- 12 named mechanism relationships and five exclusions.
- 38 source-linked call sites; 102 with unresolved overlap.
- 20 source-supported semantic-necessity classifications;
  120 unresolved.
- 2 source-supported retained results, 17 conditional cache
  cases, 53 potential reconstructions and 68 unresolved.

These are source-level classifications, not measured numbers of
redundant conversions.

The corrected diagnostic reports:

- Native `lower(lower)` median: 0.037135609 seconds.
- SHEAR-VM median: 5.263811208 seconds.
- Complete compiler outputs structurally equal.
- Traced allocation peaks: 212,392 and 1,355,751 bytes.
- Compiler output: 123,643 canonical serialized bytes.
- Host-derived graph-node chunks: 1,858, totaling 915,986
  serialized bytes.
- State-content proxy: 988,970 bytes.
- Corrected small-edit total: 0.000510425 seconds.
- Before/after edit results: 4 and 5, with separate activation.

Full raw observations, hardware, definitions and limitations are
in `docs/content_baseline.md` sections 5.7–5.11. Sections 5.1–5.6
preserve the original diagnostic evidence.

## Independent Review requirements

Start Review from current `main`, the task branch, the issue and the
amended Plan baseline. Independently verify:

- Completeness and accuracy of the bounded mechanism inventory.
- AST source anchors, call-site classifications and specific
  mechanism-pair evidence.
- That uncertain relationships remain explicitly unresolved.
- Preservation of revised Plan acceptance tests.
- Corrected edit timing boundaries and retained assertions.
- Artifact provenance, measurement definitions and reported numbers.
- Absence of production semantic changes and golden-record changes.

Prior non-blocking limitations remain: diagnostic size, bounded
inventory coverage, limited fallback instrumentation, host-derived
chunk terminology and single-environment measurements.

Classify any new observations as verified defects, limitations,
hypotheses or documentation drift. Resolve fixes require another
independent Review.

## Next

Start a fresh **Review task 23** context.

Publish remains blocked until independent Review accepts the
implementation. After acceptance, Publish verifies current `main`,
the final diff and CI, then prepares a PR with `Closes #60`.
