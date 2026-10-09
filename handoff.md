# Handoff

Compact current state for the next chat. This is a checkpoint of claims,
not evidence: verify against the repository. Read `CLAUDE.md` and
`docs/roadmap.md` first.

## State

- Task 23, issue #60, is awaiting Resolve after independent Review.
- Branch: `task/23-content-baseline`.
- Original Plan baseline: `c4a4bcc`.
- Execute head reviewed: `e680a17`.
- Revised Plan acceptance-test baseline: `564203e`.
- No task PR has been opened.

## Independent Review

Review of `e680a17` requested changes: four P2 findings.

- F1 – Incomplete inventory. The 140-site helper-call inventory omits
  direct mechanisms including `lang._Builder._relation` and
  `Relation.canonical_node`. Preserve the helper count and inventory
  the additional mechanisms with explicit exclusions.
- F2 – Duplication relationships are insufficiently evidenced.
  Generic overlap text and name-based classifications cannot establish
  whether sites duplicate content, reconstruct a representation, or
  reuse a cache. Ground mechanism-pair classifications in source and
  explicitly mark unresolved relationships.
- F3 – Small-edit latency includes a pre-activation correctness run.
  Move this check outside the measured interval, preserve the assertion,
  and rerun CI diagnostics.
- F4 – Plan acceptance tests lacked independent negative checks of the
  measurement runner's correctness guards. Return to Plan.

Non-blocking limitations: diagnostic size, host-derived chunk terminology,
limited host-fallback provenance, and single-environment evidence.

## Plan amendment for F4

Commit `564203e` extends the Plan-owned
`tests/test_content_baseline.py` with deterministic negative tests for:

- Both routes using the same compiler source.
- Retained compiler-source agreement.
- Installation of the VM compiler wrapper.
- Generation-1 provenance.
- Structural output equality.
- Rejection of host lowering of retained compiler source.

Tests use mocked runtimes and do not run performance measurements.

CI: https://github.com/NadOby/shear/actions/runs/37902162561

The original five acceptance tests remain. F4's acceptance-contract gap
is addressed; the revised Plan baseline is now `564203e`. The
implementation must preserve these tests during Resolve.

## Prior Execute evidence

- Diagnostic revision: `9b5f922`.
- Diagnostic run:
  https://github.com/NadOby/shear/actions/runs/37763237141
- Results recorded in `docs/content_baseline.md` section 5.
- Original measured `lower(lower)` medians: 0.03619 s native,
  5.12615 s through the SHEAR VM.
- Structural output equality, traced allocation peaks, chunk counts,
  state-content proxy and small edit were recorded.
- No production semantic code or golden records changed.

These observations are not substitutes for independently resolving
the Review findings.

## Resolve contract

Resolve F1–F3 individually, using the smallest valid changes.

- Do not change production semantics or weaken Plan acceptance tests.
- Keep the original 140 helper-call sites distinguishable from newly
  inventoried conversion mechanisms.
- Record concrete representation relationships and unresolved cases.
- Correct the edit-latency measurement boundary without removing
  correctness assertions.
- Update affected results and limitations in section 5 of the spec.
  Preserve the original run as historical evidence.
- Run ordinary CI and dispatch a fresh diagnostic after the fixes.
- Record fixes, rebuttals and unresolved findings here.

## Next

Start a fresh Resolve task 23 context, reading the independent Review,
current source, revised Plan tests, and original measurements.

After Resolve, conduct another independent Review. Publish remains
blocked until that Review accepts the final implementation.
