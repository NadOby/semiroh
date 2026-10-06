# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. A checkpoint of claims, not evidence: verify against the
repository. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- `main` has task 20, the single test job, the five-role workflow (Review and
  Publish check the Plan-owned files), hosted bootstrap (roadmap section I)
  and the golden check. Work is tracked in GitHub issues; commits start with
  `GH-<n>`; no session links anywhere.
- Current: task 27, issue #63, on `task/27-rebuild`. Plan done; next role is
  **Execute**. Plan head commit: the commit before this handoff, `b2d6eb1`
  (check `git log`).

## Execution contract (Provisional, see docs/vm_in_shear.md section 7)

- Add twin source functions (`vm.source_name(name)`, `"<name>_source"`) to
  `bootstrap_entities`, built from the same body constructors, never swapped.
- `swap_all` and `swap_*` compile `(code <name>_source)`; add the
  `vm.GENERATION` function (`"generation"`) updated by a fifth pair in the
  same activation, record `(n, ((name, chunk), ...))`.
- Make `tests/test_rebuild.py` pass without editing it. The existing
  `BootstrapTests.test_a_run_swaps_once` encodes the old rule (a second swap
  compiled the wrappers): rename it to what it now checks and say so.
- Record time and peak memory per generation in section 7 (the prediction is
  already there; add the measurement and one revision if wrong).
- `programs/bootstrap` is the only golden record declared (`GH-63.txt`); if
  the check shows another record change, return to Plan.
- Execute adds the `CHANGES.md` entry. Do not touch the Plan-owned files.

## Claims for Review

- After generation 1 the host machine never lowers or runs the retained
  source; plant a bug (compile generation 2 with a host-run copy) and the
  test must fail.
- Generations 1 to 3 give the same chunks as the host compiler.
- Decision taken by Plan, not by the owner: twin source functions instead of
  a literal copy of the source in `swap_all` (a copy could drift) or a second
  `rebuild` path (swap_all would keep compiling wrappers).
- `vm.py` is over 1200 lines; moving the bootstrap section out is optional.

## Next

- Execute #63; then Review, Resolve, Publish.
- Independent candidates: task 21 (#58), task 23 (#60), #73.
