# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. A checkpoint of claims, not evidence: verify against the
repository. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- `main` has task 20, the single test job, the five-role workflow, hosted
  bootstrap (roadmap section I), the golden check (#72, PR #75) and the
  no-write-assumption rule (#74, PR #76).
- Work is tracked in GitHub issues; commits start with `GH-<n>`.
- Current: #77 on `workflow/task-contract`. The owner dropped the task-contract
  verifier (blob pins, amendments, commit isolation, base-side checker) as
  more infrastructure than the problem needs: the Review and Publish roles
  now carry the check. The golden base-vs-head check stays. Mechanical
  enforcement returns only if repeated Review failures show a need.
- #77 changes `docs/roadmap.md` (Plan records its head commit; Review diffs
  the Plan-owned files; Publish re-checks them) and `CHANGES.md`. Next role:
  Review, then Publish. #78 (CLAUDE.md principle and trim) stays; its
  principle should say mechanical checks are added when Review repeatedly
  misses something, not by default.

## Next

- Review and Publish #77, then #78.
- Independent candidates: task 21 (#58), task 27 (#63), task 23 (#60), #73.
