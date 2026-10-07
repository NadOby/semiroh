# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. A checkpoint of claims, not evidence: verify against the
repository. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- `main` has task 20, the single test job, the five-role workflow, hosted
  bootstrap (roadmap section I) and the golden check. Work is tracked in
  GitHub issues; commits start with `GH-<n>`.
- Current: task 27, issue #63, on `task/27-rebuild`.
- Plan head: `b2d6eb1`.
- Implementation and adversarial Review are complete. No verified Task 27
  semantic defect remains. Next role is **Publish**.
- Final ordinary CI before this handoff is green on
  `f8796ec97e1a597db4bd0ccab5254c9128699c1c`, run `37687237865`.
- `.github/workflows/semantic-model.yml` has been restored exactly to `main`;
  temporary benchmark instrumentation is gone.

## Implemented

- `bootstrap_entities()` retains exact source twins
  `upper_source`, `evals_source`, `seq_code_source` and `lower_source`.
  Their parameters and bodies are exact twins of the original compiler
  functions and they are never swapped.
- Retained-source links deliberately resolve compiler dependencies to the
  live compiler entities. An earlier version linked source twins to source
  twins and caused a real text/corpus round-trip regression; the current
  live-link design preserves normal semantic resolution.
- `swap_all` and each `swap_*` compile `(code <name>_source)` with the active
  `lower`.
- `swap_all` computes all four chunks before activation, then atomically
  installs the four wrappers plus `generation` as a fifth activation pair.
- `generation` starts at `(0, ())` and records
  `(n, ((name, chunk), ...))` in `SWAPPED` order using the same chunk values
  installed by that activation.
- Generation 1 is compiled by the host-run compiler. Generations 2 and 3 go
  through the installed compiler running on the SHEAR VM.
- `tests/test_vm.py` only received the planned rename/comment change:
  the old second-swap test now states that a second run rebuilds from retained
  source.
- `tests/test_rebuild.py` is unchanged from Plan head.
- `vm.py` was not split.

## Verification

- Adversarial review found no semantic defect:
  retained bodies/parameters are exact twins; generation 2/3 use the installed
  compiler; no hidden host-lowering fallback exists in the current call path;
  all four chunks are computed before activation; installation and generation
  recording use the same chunks.
- The provenance test is architecture-specific: dynamically it excludes host
  execution/lowering of the retained `*_source` functions. Static review of
  the current architecture found no alternative host-compilation path.
- `source_dependencies` manually duplicates the compiler dependency map and
  could drift in a future compiler change; it is correct for the current
  compiler.
- Golden comparison passes with exactly `programs/bootstrap` changed, as
  declared by `tests/golden_changes/GH-63.txt`.
- The six pre-existing classified `vm.py` mutation survivors remain genuinely
  equivalent; their catalog was repinned to the changed source.
- Exhaustive mutation campaign `37673486710` selected 3543 mutants. Fifteen
  of sixteen shards passed. The only failure was one unclassified survivor in
  unchanged `shear/syntax/printer.py`; no Task-27 `vm.py` survivor was found.
- The exact same printer survivor was reproduced on `main` in control run
  `37682687438`, ruling out Task 27 as its cause. Follow-up issue #81 tracks
  that pre-existing rendering/mutation-test question.
- Ordinary CI after all Task 27 code, documentation, changelog and workflow
  cleanup is green: run `37687237865`.

## Measurements

GitHub Actions run `37673221466`, Intel Xeon Platinum 8370C 2.80 GHz,
Linux x86-64, Python 3.12.14; memory is peak traced Python memory:

- generation 1: 1.182 s, 3.906 MiB;
- generation 2: 21.232 s, 4.096 MiB;
- generation 3: 21.271 s, 3.210 MiB;
- total generation time: 43.685 s.

The pre-run prediction was about 8 s and 2 MB per interpreted generation,
about 25 s total. Section 7 of `docs/vm_in_shear.md` records the measurement
and revision.

## Publish

- Re-check the Plan-owned files against Plan head `b2d6eb1`; the intentional
  specification change is the allowed Task 27 section-7 measurement/status
  completion, while `tests/test_rebuild.py`, `tests/golden_changes/GH-63.txt`
  and `docs/roadmap.md` remain Plan-owned.
- Re-check the final branch diff and green ordinary CI.
- Open the Task 27 PR closing #63.
- Do not include #81 in this PR; it is an independent follow-up.
