# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. A checkpoint of claims, not evidence: verify against the
repository. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- `main` has task 20, error handling (PR #55), and the single test job
  (PR #48). Task 20's review and mutation evidence is in PR #55 and in the
  history of this file.
- Work is tracked in GitHub issues. Roadmap tasks 21 to 31 are issues #56 to
  #67, labelled `task`; tasks 27 to 31 form the milestone "Hosted
  bootstrap". Open follow-ups are labelled `follow-up`. Commits start with
  the issue key `GH-<n>`.
- Two stacked workflow PRs are published and wait for the owner's merge:
  - PR #70, `workflow/independent-review-resolution` (closes #50): the five
    task roles and issue tracking;
  - PR #71, `workflow/bootstrap` (closes #69), based on #70: roadmap
    section I (hosted bootstrap), pending decisions D3 and D4, task 23's
    bootstrap costs, and the bootstrap delivery review in `docs/reviews/`.

## Next

- The owner merges #70, then #71 once it is retargeted to `main`.
- Then, in any order: #68, the CI-contract change on `workflow/ci-contract`
  (it edits CLAUDE.md, so it starts after these merge or stacks on them);
  task 21 (#58) and task 27 (#63), both independent; task 23 (#60).
