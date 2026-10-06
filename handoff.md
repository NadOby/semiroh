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

The issue body is the amended specification (owner's review of the first
version: push baseline, per-issue declarations, namespaced IDs, the guard
test, separate subprocesses, digests, the `*` rule).

- Deleted: `tests/language_golden.json`, `tests/test_language_golden.py`,
  `--record`, and `MainCorpusGuardTests` in `tests/test_error_handling.py`
  (an owner's test: it pinned pre-task-20 digests and would reject intended
  changes). `tests/golden.py` holds the recorder (`observe`, unchanged) and
  the check; `tests/test_golden.py` (lane `cross-boundary`) tests the rules.
  Planting a bug in each rule fails at least one test.
- Base and head record in separate `python -m tests.golden --record`
  subprocesses, each with its tree as working directory and `PYTHONPATH`
  removed. A base without `tests/golden.py` uses the retired module's
  `observe`; that fallback can go once `main` has the new module.
- CI: `fetch-depth: 0`; on a push to `main`, `--base` with
  `github.event.before`; otherwise `--against origin/main` (merge base, which
  is HEAD itself on the ref's tip).
- Declarations: new files in `tests/golden_changes/`; changing or deleting
  an existing one fails. This branch declares `*` in `GH-72.txt` because the
  recorder moved; nothing under `shear/` changes.
- Locally against `main`: 55 unchanged, 0 failures. End to end on a scratch
  branch: an undeclared change to `gcd` fails; declared in a new `GH-99.txt`
  it passes; an explicit `--base` over two commits works; editing
  `GH-72.txt` fails; a clean tip against itself passes.
- Not verified locally: the `push` to `main` path, which only runs after
  merge.

## Next

- Review #72, then Resolve/Publish. After it merges, the rest of #68
  (acceptance contract, task-contract verifier, CLAUDE.md principle and
  trim) remains.
- Independent candidates: task 21 (#58), task 27 (#63); task 23 (#60).
