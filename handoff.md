# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. A checkpoint of claims, not evidence: verify against the
repository. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- Task 20, error handling, on `task/20-error-handling` (no PR). The
  implementation is complete, subject to review. Spec:
  `docs/error_handling.md`.
- The branch is based on current `main` (`27990e2`).
- `research/semantic-core` is a separate experiment with its own
  `handoff.md`. Do not change it from main-line work.

## Phase

**Resolve** is done for the first review. Next: a fresh **Review task 20**.
No PR yet.

## P1 finding and fix

Finding: the catch handler accepted any exception carrying a plausible
4-tuple `.error`, so a host exception with a forged `.error`, or a SHEAR
error escaping an independent `run` started by an external evaluator, was
caught by the outer program. That broke Decided §1 (an evaluator that raises
is not caught).

Fix (`shear/machine.py`): the boundary is "originated in this same run".

- `run()` creates a fresh private token (`object()`) per top-level run and
  passes it to `_execute(..., run_token)`.
- `_execute` publishes the token in a private `ContextVar` (`_RUN`) for its
  dynamic extent and resets it in `finally`. The nested `_execute` of
  `trial` receives the same token; an independent `run()` gets a new one.
- `_attach` stamps the token as `exc._shear_run` only when it creates the
  error value; an existing `.error` keeps its original stamp.
- The handler accepts an exception only if its stamp `is` the current run
  token. Classes, messages and `.error` values of escaping exceptions are
  unchanged; the token is not part of the error value or public API.
- A context variable rather than an explicit parameter on `_attach`: about
  20 helpers outside `_execute` create errors, and threading the token
  through all of them would churn most of the file.

Regression tests (`tests/test_error_provenance.py`, lane
`language-runtime`): forged `.error`; an independent failing `run` inside an
`External` evaluator escapes `catch(write(...))`; a runtime rejection
escaping an inner run escapes too; an inner run still catches its own
errors; the outer run still catches its own errors after an inner run (token
reset); a `raise` under `trial` is caught by the enclosing filtered catch.
The first three fail on the pre-fix code; planted bugs (no reset, a fresh
token for trial) are each caught. Docs: Provisional §8 bullet in
`docs/error_handling.md`; one line in the `CHANGES.md` entry.

## Mutation evidence

- `shear/machine.py` repinned under the task 19 rule: the three
  `_semantically_equal` survivors carry (definition AST-identical); the
  `run()` `may_activate: bool = False,` constant survivor is dropped because
  `run` changed. It is restored only if the campaign reproduces it.
- Campaign on `d05193b` (`SHEAR_MUTATE=10000`, seed 1, batch 0): run
  37411182531 (eight shards, branch `experiment/mutation-8-shards` = same
  code plus a survivor-annotation step) found 69 unclassified survivors.
  The four-shard run 37411180181 selects the same set. Earlier runs were
  cancelled during GitHub's runner-assignment incident of 2026-10-05.
- 23 were real gaps, now killed by `tests/test_error_values.py` (each
  mutant checked locally): `relation_rejected` and `activation_rejected`
  values; `code`, `ref`, `linksof` of a cell; `apply`/`applyv` operation
  names (stale closure, non-callable); malformed `catch` loading as an
  `invalid` node; a directly caught call still taking a call level (the
  catch body is not in tail position); renderer output for hand-built
  malformed catches and non-ASCII kinds.
- 46 classified. 37 re-reviewed carries of main's classifications that
  Execute had dropped (parser 9, printer 25, lang 1, machine 2, including
  `may_activate`), each matched by enclosing statement, not ordinal. 9
  new: two printer atom precedences (a new `4,` and `catch(...)`); machine
  base and catch
  continuation tail flags, the handler-stack invariant guard, the
  unreachable `activation_conflict` mapping, two `return exc` whose results
  callers discard; `errors.describe` on a malformed value (unspecified).
- Review's prediction (three parser, one printer) was low: Execute dropped
  far more than it expected and no campaign had run on the branch.
- Confirming campaign on the current head `e4d2061` (10000, seed 1, batch
  0): run 37416039828, sixteen shards, every shard green, so no unclassified
  survivors remain; its eight CI lanes passed too. Its head `5931a59` is
  `e4d2061` plus workflow-only commits (shard count, survivor annotations):
  `git diff e4d2061 5931a59` touches only the workflow file. The shard count
  does not change the selected set (`test_shard_count_does_not_change_selected_work`),
  so this covers exactly the four-shard configuration's 3,528 mutants. The
  four-shard run on the task branch was cancelled after 1 h 45 min to free
  runners; the experiment branches are to be deleted.

## Process change removed from task 20

Commit `98c3831` ("Change workflow to independent planning review and
resolution") is no longer in this branch. Preserved, rebased onto `main`, as
branch `workflow/independent-review-resolution` for its own PR. Task 20 no
longer touches CLAUDE.md, the roadmap Workflow section or a process
`CHANGES.md` entry.

History rewrite (trees unchanged, boundaries kept): the four `Reconcile ...`
and one `Carry ...` subjects now start with Remove / Change; the empty
duplicate commit "Change tail-position rules for catch" (`781a026`, no tree
change) was dropped; a stray `.` body was removed.

## Verified at this state

- Head `e4d2061` plus this handoff commit, based on `main` `27990e2`.
- `python3 -m unittest discover` and every lane in `tests/lanes.py` pass
  locally; all eight CI lanes passed on `e4d2061` (run 37416039828).
- No existing exception class or message changed; `CLAUDE.md` and the
  roadmap Workflow section are untouched by this branch.
- `tests/test_error_handling.py` and `shear/examples/errors.py` are
  unchanged since the Plan anchor `6746afc`.
- `git diff main -- tests/language_golden.json` only adds `safe_install`,
  `account_report` and `lookup`; `MainCorpusGuardTests` passes.

## Provisional choices still in `docs/error_handling.md`

§2 catch kinds are node payload; malformed kinds build `invalid`. §3 `raise`
kind must be a non-empty string; detail is any value. §4 detail pairs sorted
and unique; detail value types; `where` rules (call node on entry, the
candidate's node inside a trial). §5 mapping of host exceptions to origins.
§6 kind catalogue. §7 host interface (`describe`, `.error`, exact
`LanguageError`, private `Raised`). §8 graph form, lowering, handler
unwinding, run provenance. §9 syntax. §10 compiler and VM deferral.

## Limitations (not task 20 defects)

- The private `_Raised` class renames itself `Raised`, which breaks ordinary
  pickling. Picklability is unspecified and the private host-interface
  choice is Provisional (§7).
- `shear/machine.py` is far over the 500-line review threshold; no split in
  this task.
- `CATCH`/`FAIL` in the self-hosted compiler and VM stay deliberately
  deferred (§10, §13).
- `activation_conflict` (§6) cannot be produced by a running program:
  program activations always start from the active state.
- `catch` around deep recursion can end in the host `RecursionError` while
  nesting results, which §1 already lists as an uncaught model failure.
- Actions artifacts and job logs cannot be downloaded from this workspace;
  survivor keys were read from job annotations instead.

## Hypothesis only

- `lang._definition_of()` may fail on a malformed hand-built state with a
  model exception. Do not "fix" it unless a well-formed program can reach it.

## Rules learned the hard way

- Editing a mutation target invalidates its survivor classifications. Carry
  one only when its enclosing top-level definition is AST-identical; drop
  the rest. Mutation campaigns run in CI (manual dispatch), not in a chat.
- After restoring a file you planted a bug in, delete every `__pycache__`.
- Language failures stay exactly `LanguageError` with today's messages;
  `test_vm` compares class names and `test_bytecode` message prefixes.
- A refactor keeps `tests/test_language_golden.py` green; re-record only for
  an intended behaviour change, and say so.
- In a corpus program, a link name used in a quote must equal its entity's
  name, or the round trip prints `raw`.
