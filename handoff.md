# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. A checkpoint of claims, not evidence: verify against the
repository. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- `main` has task 27 (PR #82): the compiler rebuilds from retained source,
  generations 2 and 3 compiled on the SHEAR VM; and the #81 fix (PR #85):
  the printer survivor is classified as unspecified layout. Work is tracked
  in GitHub issues; commits start with `GH-<n>`.
- No roadmap task is in progress.
- `workflow/bootstrap-review` (this change) sharpens roadmap section I after
  the 2026-10-08 peer review: task 29 compares routes on D4's recommended
  workload and states the verifier's admission rule, task 30's provenance
  criterion names program code and exempts the route's machinery, task 31
  builds on task 30's corpus, D4 sets two provisional budgets, task 28 reads
  route support from the code. It also fixes drift found by the review.
  A second review round (input and reply on `workflow/design-goals`, issue
  #84) added: route (a) must show a source-preserving form or the owner
  changes the first anchor; provenance must be unforgeable; the comparison
  is redone if D4 changes the workload. Reviewed as conceptually ready;
  next: the owner merges after green CI.
- Design goals from the same discussion go on a separate branch,
  `workflow/design-goals`, through several review rounds before merging.

## Next

- Roadmap order: task 23 (issue #60) with its bootstrap costs, then tasks 28
  and 29, decisions D3 and D4, tasks 30 and 31. Tasks 21 and 22 are
  independent.
