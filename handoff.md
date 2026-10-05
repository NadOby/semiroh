# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- Tasks up to 19 are merged.
- The semantic-core experiment is closed and archived at tag
  `semantic-core-experiment-2026-10`; its outcome is
  `docs/identity_model.md` §10. Do not reopen it: follow-ups are ordinary
  tasks.
- Next: task 20 (endpoint arity audit), then 21 to 25 in order
  (`docs/roadmap.md` section G).

## Phase

None open. A new task starts with **Plan** (Opus).

## Working procedure

- One phase per chat (roadmap Workflow): Plan on Opus, Execute on Sonnet,
  Review and publish on Opus. End each phase by updating this file and
  asking the owner to switch model. No background agents.
- Commit after every coherent step; run `git status` before any reset or
  delete.
- Run `python3 -m unittest discover` before publishing. Do not run mutation
  campaigns in a chat; they run in CI (manual workflow dispatch).
- Open PRs with the GitHub REST API (`gh api` or curl), `"draft": false`.
  PATCH the body once to drop the session link.
- `tests/test_docs.py` rejects "#PR pending": open the PR first, then name
  its number in the roadmap entry.

## Rules learned the hard way

- A refactor keeps `tests/test_language_golden.py` green: corpus StateIDs,
  rendered text, bytecode, continuity results and public names. Re-record it
  only for an intended behaviour change, and say so.
- An operation added in one place fails `tests/test_operations.py`; add it
  to `shear/operations.py` and to every implementation.
- Editing a mutation target invalidates its survivor classifications. Carry
  one over only when its enclosing top-level definition is AST-identical
  (owner's rule, task 19); drop the rest and list them in the PR.
- After restoring a file you planted a bug in, delete every `__pycache__`:
  a same-size restore can reuse the mutant's stale `.pyc`.
- A new layer gets one acceptance test that runs the existing corpora
  through it; the reconciler's first bug showed only that way.
- Environment variables are `SHEAR_*`; a stale `SEMIROH_*` fails the tests
  on purpose.
