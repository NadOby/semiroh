# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. A checkpoint of claims, not evidence: verify against the
repository. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- `main` has task 20, the single test job, the five-role workflow, hosted
  bootstrap (roadmap section I), the golden check (#72, PR #75) and the
  no-write-assumption rule (#74, PR #76).
- Work is tracked in GitHub issues; commits start with `GH-<n>`.
- Current: Plan for #68, on `workflow/task-contract`: `docs/task_contract.md`
  (Provisional). Split into #77 (contract and verifier) and #78 (CLAUDE.md
  principle and trim). Waiting for the owner's decisions D-A, D-B, D-C
  (section 5 of that doc). Next role: **Execute #77**, then #78.

## Claims for Review of this plan

- The contract needs no GitHub state: it is files plus git history.
- Running the checker from the merge base is what stops a branch from
  weakening its own checker; the first merge is the only exception.
- Splitting `tests/golden_check.py` from the recorder removes the shared-file
  limitation recorded in Review of #72.

## Next

- Owner answers D-A to D-C; then Execute #77 and #78.
- Independent candidates: task 21 (#58), task 27 (#63), task 23 (#60), #73.
