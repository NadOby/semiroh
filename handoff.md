
# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. A checkpoint of claims, not evidence: verify against the
repository. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- Task 23, issue #60, is in Plan → Execute handoff.
- Base: `main` at `a4998b0` (PR #87 merged).
- Branch: `task/23-content-baseline`.
- Plan-owned contract frozen at `c4a4bcc`:
  `docs/content_baseline.md`, `tests/test_content_baseline.py`,
  and registration in `tests/lanes.py`.
- No production implementation or measurements have been completed.
- CI execution only. The acceptance tests currently import the absent
  `tests.content_baseline` module, so failure is expected until Execute
  implements it. No test result is claimed here.

## Execute contract

- Implement `tests/content_baseline.py` against the Plan-owned acceptance
  tests and measurement protocol. Keep the diagnostic separate from
  ordinary test execution.
- Inventory content conversion sites, representations, mutation survivors
  and compiler/VM representation boundaries using current source evidence.
- Measure identical `lower(lower)` workloads through host execution of the
  SHEAR compiler and the installed SHEAR-VM compiler route. Verify
  structural equality and provenance independently of timing.
- Record warm-up, at least three untraced timing observations per route,
  separately traced peak allocations, byte-size definitions, chunk counts,
  and one verified `define` → lower → activation edit.
- Extend the existing GitHub Actions workflow with an explicitly
  dispatched diagnostic mode. Do not make ordinary CI benchmark timings
  or enforce performance thresholds.
- Record CI provenance, raw observations, hardware, limitations and
  results in the specification's append-only results section.
- Do not refactor semantic content, change public semantics, rewrite
  Plan acceptance tests, or change golden records.
- Append the PR's architectural-log entry to `CHANGES.md`.

## Review contract

Independently verify conversion counts and classifications against source,
mutation catalog pins, runtime-route equivalence and absence of host
lowering fallback, measurement provenance, units, workload definitions,
and the program-image proxy's exclusions.

Keep findings classified as verified defects, limitations, hypotheses
or documentation drift. Material changes to Plan-owned expectations return
to Plan rather than being absorbed by Execute.

## Next

Start a fresh Execute task 23 context from the frozen Plan contract.
After Execute, independently Review, Resolve if needed, and Publish.
Roadmap order thereafter: tasks 28 and 29, decisions D3 and D4, then
tasks 30 and 31. Tasks 21 and 22 are independent.
