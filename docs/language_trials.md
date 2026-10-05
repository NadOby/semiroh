# Trials in the Language

**Status: implemented.** `shear/lang.py` and `shear/bytecode.py`
implement the `trial` operation below, and `tests/test_language_trials.py` passes; since roadmap task 4 its
programs are loaded into graph form (graph_form.md), with the behaviour
assertions unchanged. Roadmap task 20 adds catchable failures around trials
without changing the trial operation itself.

metaprogramming.md lets a program install code it wrote. This step lets it
exercise that code first: the program runs a call against a candidate
version in an isolated runtime (activation_model.md §8), looks at the
result, and only then decides whether to `activate`.

## 1. Scope

**Decided:**

In scope: one operation, `trial`, over the same changes `activate` accepts,
using `Runtime.trial` as it is.

The original trial task did not add error handling to the language. Roadmap
task 20 later adds `catch` and `raise` independently: `trial` still
propagates a candidate failure, but an enclosing `catch` can now turn that
failure into a value (section 4).

Still out of scope: observing the candidate's cells after the trial; keeping
or reusing a candidate across operations; converters; any change to the core
model.

## 2. The operation

**Decided:**

    ("trial", ("call", link, e1, ..., eK), link1, f1, ..., linkN, fN)
        N >= 0

The first operand is a call form, written exactly as a `call`. The rest are
link/function pairs, exactly as for `activate`. The value of `trial` is the
value the call returns when it runs against the program with the pairs'
changes applied.

1. Evaluate the call's arguments `e1` ... `eK`, then `f1` ... `fN`, in order,
   in the running function's scope and the real runtime.
2. Check the operands. The first operand must be a call form whose link
   resolves through the running function's links; the pairs are checked as
   for `activate` (metaprogramming.md §4). A failed check is a
   `LanguageError`.
3. Check the capability (section 3). Without it: `ActivationRejected`.
4. Build the transformation exactly as `activate` would, from the active
   state as it is once the operands have been evaluated, and call
   `runtime.trial` on it. A rejection propagates unchanged as
   `ActivationRejected`. In graph form that is `define` (graph_form.md §6).
5. Call the linked function with the evaluated arguments in the isolated
   runtime, without the activation capability, and return its result.

With `N = 0` there are no changes: the call runs against the current program
in isolation, so its cell writes do not reach the real runtime.

The isolated runtime is discarded when `trial` returns or raises. The real
runtime is never changed by a trial: not its program state, not its cells,
not its holds.

## 3. Capability

**Provisional:**

Until capabilities are modelled.

A trial produces a candidate state, and activation_model.md §3 governs
producing states with the embedded compiler as well as activating them. A
trial is the first half of an activation, so it takes the same grant:
`trial` needs `may_activate=True`, like `activate`.

The candidate receives only what the trial grants (activation_model.md §8).
It runs without the activation capability, so code under trial cannot
`activate` or `trial`: either raises `ActivationRejected`. Its constraints
are evaluated in the main runtime's context, which is `Runtime.trial`'s
default.

## 4. Failures

**Decided:**

`trial` does not convert a candidate failure into its own result. A successful
candidate returns its ordinary value; a failure propagates out of the
isolated run:

- a candidate the runtime rejects raises `ActivationRejected`, as activating
  it would; the program's own constraints (metaprogramming.md §4) therefore
  reject a candidate before any of its code runs;
- anything the call raises in the candidate (`LanguageError`,
  `CellContentRejected`, `ActivationRejected`, `CallDepthExceeded`, or a
  program `raise`) propagates from the trial with its task-20 error value
  unchanged;
- a failure of the Python reference model that is not a SHEAR-reported
  failure remains a model failure and is not converted into a catchable
  language error.

The isolated runtime is discarded on all of these paths, so its cell writes
and candidate program state never reach the real runtime.

Without an enclosing `catch`, the propagated failure stops the outer run
before any later `activate`, as before task 20. With `catch`, the caller can
inspect the failure and decide whether to continue, for example:

    ("catch", ("trial", ...))

returns `("ok", value)` when the candidate returns normally, or
`("failed", error)` when the candidate reports a catchable failure.

A filtered catch can select only particular candidate failures:

    ("catch", ("trial", ...), ("out_of_range", "depth_limit"))

A non-matching failure passes through unchanged. Its origin, kind, detail and
`where` continue to identify the failure inside the candidate rather than
the enclosing `trial` node.

This makes the intended test-before-install pattern explicit:

    let r = catch(trial(power(x), power = candidate))
    if item(r, 0) == "ok":
        activate(power = candidate)
    else:
        ...

`trial` remains the isolation boundary for state; `catch` is only the failure
observation boundary. Catching a trial failure does not commit any effects
from the isolated runtime.

## 5. Trials and the two-version bound

**Decided:**

Following activation_model.md §8.

The isolated runtime has its own root, so trials do not count against the
main runtime's two-version bound. A run may make any number of trials,
before or after its one activation.

## 6. API

Addition to `shear/lang.py`:

    ("trial", ("call", link, e, ...), link, f, ...)
        the call's result against the candidate; the real runtime unchanged

No new Python API: `trial` uses the existing `may_activate` grant of `run`.

## 7. Acceptance tests

`tests/test_language_trials.py` pins the behaviour above. It fails until
`shear/lang.py` implements it; the implementation is done when it passes
without changes, together with the rest of the suite. The implementer adds
unit tests for each `LanguageError` case of `trial` (first operand not a
call form, unknown call link, the pair errors), for the order of checks
(operand errors before the capability), for `N = 0`, and for a trial whose
operands activate: the transformation starts from the active state after
evaluation, so that trial still runs.

Roadmap task 20 additionally pins trial failures through `catch` in
`tests/test_error_handling.py`: failures from candidate code keep their error
value and candidate location, while the isolated runtime remains discarded.

## 8. Implementation notes

- Share the pair checks and the transformation with `activate`: one helper
  that checks the pairs and builds the `TransformResult` from the active
  state read after the operands are evaluated. Move `activate`'s read of
  the active state after its operand evaluation too.
- Run the call in the isolated runtime on a fresh run of the machine
  (bytecode.md section 4), whose runtime is the isolated one and whose
  `may_activate` is false.
- Use `Runtime.trial` and `transform_with_mapping` as they are. No core
  change should be needed; if one is, stop and say why in the PR.
- Keep the diff small: add code rather than reformat existing code, and
  leave existing comments and docstrings in place.
- When done: add a `CHANGES.md` entry, mark this document's status, update
  activation_model.md §12, and fill in section 9.

## 9. Deferred questions this program needed

- activation_model.md §13, capability isolation for trials: answered
  provisionally (section 3): code under trial runs with `may_activate=False`
  regardless of the outer run's grant, so it cannot `activate` or `trial`
  itself.
- ownership_model.md §13: none. `trial` creates no entities, removes no
  entities, and changes no ownership; it only stages and discards an
  isolated candidate.
