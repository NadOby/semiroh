# Handoff

Compact current state for the next chat. Not a log: replace what is stale,
keep it short. Read CLAUDE.md and `docs/roadmap.md` first.

## State

- Task 20, error handling, is planned on branch `task/20-error-handling`
  (pushed, no PR). The spec is `docs/error_handling.md`; the roadmap entry
  is **Planned.**
- `research/semantic-core` is a separate experiment with its own
  `handoff.md`. Do not change it from main-line work.

## Phase

**Execute** (Sonnet). Then Review and publish (Opus).

## Decided with the owner

Do not change these; they shape the language.

- `catch(e)` gives `("ok", v)` or `("failed", error)`. `catch(e, kinds)`
  accepts only listed kinds; any other error passes through unchanged.
- `raise(kind, detail)` fails with a program error.
- An error is the plain tuple `(origin, kind, detail, where)`. Origin is
  `program`, `language`, `runtime` or `limit`, set by the machine. Detail is
  `(name, value)` pairs for errors the language reports. Where is
  `(function, node)`. Messages come from tooling (`describe`) and are not part
  of the value.
- Scope: every failure the language reports, including the call-depth limit
  as origin `limit`. Failures of the Python model are not caught.
- No rollback.
- Later, not this task: references held as data follow continuity (marked
  `ref` values, pinning, a flexible version bound); records; declared error
  kinds.

## Plan

Commit after each step.

1. `operations.py`: add `catch` (code role `body`, one or two input
   operands, kinds as payload) and `raise` (positional `kind`, `detail`).
2. `lang.py`: build and collapse `catch`. Malformed kinds (empty, not
   strings, empty string, duplicates) build an `invalid` node. `raise` goes
   through the generic positional path.
3. New `shear/errors.py`: `KINDS`, the catalogue of spec §6 mapping kind to
   origin, and `describe(error)`. Add it to `TARGETS` in
   `tests/mutation_catalog.py`.
4. `bytecode.py`: lower `catch` to one instruction that enters `body` under
   a handler, and `raise` to EVAL kind, EVAL detail, then a failing
   instruction. `RAISE` keeps its meaning for invalid nodes.
5. `machine.py`:
   - track the current node and the function it belongs to;
   - keep a handler stack and unwind to the nearest accepting handler;
   - give every raise site its error value (spec §5–6) and set `.error` on
     escaping exceptions;
   - add `Raised(LanguageError)` for uncaught program raises.
6. Syntax: `catch(EXPR)`, `catch(EXPR, "k", ...)` and `raise(EXPR, EXPR)`.
   `catch` and `raise` become reserved. Catch kinds are string literals only.
7. Docs:
   - language_data.md §4: the body of a catch is not in tail position;
   - bytecode.md §3: the new instructions;
   - syntax.md §2–3: the forms and reserved names;
   - language_trials.md §4: trial failures can now be caught;
   - vm_in_shear.md §7: errors can now be constructed;
   - corpus.md: the `errors` tag and examples;
   - graph_form.md §3: the new node roles;
   - error_handling.md: status changes from planned to implemented;
   - a `CHANGES.md` entry.
8. Re-record `tests/language_golden.json`. `git diff main --
   tests/language_golden.json` must only add the three new programs.
9. Mutation catalog: carry survivors only where their enclosing top-level
   definition is AST-identical; drop the rest and list them for the PR.
10. Run `python3 -m unittest discover`.

## Acceptance tests that must not change

- `tests/test_error_handling.py`, the whole file, including the digests in
  `MainCorpusGuardTests`.
- `shear/examples/errors.py`: its expected results are acceptance data.
- The Decided sections of `docs/error_handling.md`.

These fail before execution:
- `test_error_handling`, every test except the guard;
- in `test_corpus`, `test_syntax` (round trip) and `test_language_golden`
  (programs), the subtests for the three new examples.

Everything else passes on the branch. The tests were checked against a
throwaway prototype, not on the branch: all of them pass once `catch`,
`raise` and the syntax exist.

## Do not decide alone

Stop and ask the owner before:
- changing any acceptance test or example expectation. If one looks wrong,
  stop and report it;
- renaming or removing a catalogue kind, or changing the detail layout, the
  origins or the catch results (adding a kind is fine; name it in the PR);
- making a non-SHEAR exception catchable (`KeyError`, `TypeError`,
  `RecursionError`, an evaluator's own exception). Also report any model
  exception that a well-formed program can reach and the spec does not map;
- changing the class or message of an existing failure, the bytecode of
  existing nodes, or the golden entries of existing programs;
- starting anything §13 lists as Open: re-raise, rollback, a step budget,
  declared kinds, or `catch`/`raise` in the self-hosted compiler and VM.

## Hints from the prototype

- Language failures must stay exactly `LanguageError` with today's messages.
  `test_vm` compares `type(exc).__name__` and `test_bytecode` matches
  prefixes such as `inner: add operands`. Attach kind and detail; do not
  subclass.
- Where for a failure while entering a callee (wrong arity, absent target) is
  the call node in the caller. A tail call swaps `activation.entity` before
  opening the callee, so track the node's function separately.
- A handler records the control depth, the accepted kinds, the operand-stack
  height and the number of live calls. Unwinding releases the holds of the
  calls above it.
- `TRIAL` runs the candidate in a nested `_execute`, whose exception already
  carries `.error`; never overwrite it.
- Each depth-limit case takes about 0.7 s; the new module runs in about 9 s.

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
- Names inside quoted code are data. In a corpus program, a link name used
  in a quote must equal its entity's name, or the text round trip prints
  `raw`. Write the empty tuple there as `("tuple",)`, not `("lit", ())`.
