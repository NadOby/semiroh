# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. A checkpoint of claims, not evidence: verify against the
repository. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- `main` has task 20 (PR #55), the single test job (PR #48), the five-role
  workflow with issue tracking (PR #70) and roadmap section I, hosted
  bootstrap (PR #71).
- Work is tracked in GitHub issues. Roadmap tasks 21 to 31 are issues #56 to
  #67, labelled `task`; tasks 27 to 31 form the milestone "Hosted
  bootstrap". Commits start with the issue key `GH-<n>`.
- Current: #72 on `workflow/golden-check`, a workflow change split out of
  #68 at the owner's request ("as soon as possible"). Implemented; next role
  is **Review**, in a fresh chat.

## #72 claims for Review

- `tests/language_golden.json`, `tests/test_language_golden.py` and
  `--record` are deleted. `tests/golden.py` holds the recorder (`observe`,
  moved unchanged) and the check; `tests/test_golden.py` (lane
  `cross-boundary`) tests the comparison rules on planted records. Each rule
  was confirmed by planting a bug in it: every plant fails at least one test.
- CI: the `tests` job checks out with `fetch-depth: 0` and runs
  `python -m tests.golden --against origin/main` after the lanes.
- Base: merge base of the ref and HEAD; when HEAD is the ref's tip (a push
  to `main`), the previous commit. A base without `tests/golden.py` records
  with the retired `tests.test_language_golden.observe`, so this branch's
  own run works; that fallback can go once `main` has the new module.
- Rules: new records pass and are printed in full; unchanged pass; changed
  or removed fail with old and new. API records fail only when a public name
  disappears. Intended changes are `<group>/<name>` lines the branch adds to
  `tests/golden_changes.txt` (difflib over the base and head file); groups
  are qualified because `fold` is both a program and a continuity case. An
  added line whose record did not change fails. A recorder change needs a
  `*` line, and `*` without a recorder change fails (Provisional: the design
  did not say).
- This branch adds `*`, because the recorder moved. Locally against `main`:
  55 unchanged, 0 failures. End to end on a scratch branch: missing `*`,
  a changed `gcd` without a line, the same with `programs/gcd`, and a padded
  `programs/fold` gave fail, fail, pass and fail.
- `tests/test_error_handling.py` (task 20's guard) now imports `observe`
  from `tests.golden`; only the import and a comment changed.
- Known limit: run locally on `main` itself with uncommitted changes, the
  base is the previous commit, not HEAD.

## Next

- Review #72, then Resolve/Publish. After it merges, the rest of #68
  (acceptance contract, task-contract verifier, CLAUDE.md principle and
  trim) remains.
- Independent candidates: task 21 (#58), task 27 (#63); task 23 (#60).
