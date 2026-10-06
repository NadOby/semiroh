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
- Two stacked workflow branches wait for the owner, without PRs yet:
  - `workflow/independent-review-resolution` (#50), rebased on `main`: the
    five task roles and issue tracking;
  - `workflow/bootstrap` (#69), on top of it: roadmap section I (hosted
    bootstrap), pending decisions D3 and D4, task 23's bootstrap costs, and
    the bootstrap delivery review in `docs/reviews/`. It replaces the
    misspelled `wokflow/bootstrap`.

## Next

- The owner reviews the two branches; Publish opens their PRs in order.
- Then, in any order: #68, the CI-contract change on `workflow/ci-contract`
  (it edits CLAUDE.md, so it starts after these merge or stacks on them);
  task 21 (#58) and task 27 (#63), both independent; task 23 (#60).
