# Error Handling

**Status: implemented** (roadmap.md task 20). The acceptance tests are
`tests/test_error_handling.py` and the `errors` examples in
`shear/examples/errors.py`.

Until now every failure ends the whole run: a program cannot observe that
something failed, decide, and go on. Three programs need more than that:

- `checked_compile` (self_modification.py) trials a candidate before
  installing it, but a candidate that raises under `trial` stops the program
  that is deciding about it (language_trials.md §4). `trial` protects the
  program from a wrong answer, not from a crash.
- `account` (side_effects.py) can show an overdraft only as the run aborting;
  it cannot report "refused" and continue.
- The interpreter written in SHEAR fakes its own errors by indexing an empty
  tuple (`vm_trap`), and lists general error construction as open
  (vm_in_shear.md section 7).

This task adds two operations: `catch` turns a failure into a value at an
explicit point, and `raise` lets a program fail with an error of its own.

## 1. Scope

**Decided:**

A program can catch every failure the language reports about the program's
own run:

- an error the program raises itself (`raise`, section 3);
- a broken language rule: an operand of the wrong kind, an index out of
  range, a wrong number of arguments, applying something that is not
  callable, naming an absent function or a non-cell, and so on;
- a cell write the runtime refuses because its content is violated or
  unknown under the cell's constraint, or a constraint relation is not
  satisfied;
- an activation the runtime refuses, including a missing activation
  capability, a rejected candidate and a conflict;
- anything raised inside a `trial`, by the candidate or by the trial itself;
- the call-depth limit, as its own `limit` origin: a limit was hit, which is
  not a verdict about the program (section 4).

Not caught:

- a failure of the Python reference model itself: a Python exception that is
  not one of the language's errors (a `KeyError` from a hand-built malformed
  state, an evaluator that raises, the host recursion limit in
  canonicalization). It is a defect of the model, not something the program
  decided, and it ends the run as today;
- non-termination. A tail-call loop that never ends hits no limit, so there
  is nothing to catch; that needs a step budget (bytecode.md section 8).

No rollback: `catch` does not undo what happened inside it before the
failure. A cell written before the failure keeps its new content, and an
activation that succeeded stays active. The failing step itself changed
nothing: a refused write leaves the cell as it was, and a refused activation
leaves the runtime unchanged (activation_model.md §2). Returning to an earlier
program version is a new activation (activation_model.md §9). `trial` remains
the all-or-nothing tool.

## 2. Catch

**Decided:**

    ("catch", e)                    catch every failure of e
    ("catch", e, (k1, ..., kn))     catch only failures of kinds k1 ... kn

`catch` evaluates `e`. If `e` returns `v`, the value of `catch` is
`("ok", v)`. If `e` fails with an error the catch accepts, its value is
`("failed", error)`, with the error value of section 4. The result is always
wrapped, so a normal return can never be mistaken for a failure: an `e` that
returns `("failed", x)` gives `("ok", ("failed", x))`.

The first form accepts every error. The second accepts an error whose kind is
one of the listed kinds, whatever its origin; any other error passes through
the catch unchanged, with its origin, kind, detail and where as they were,
to an enclosing catch or out of the run.

The expression `e` is not in tail position: a call in it keeps its caller's
frame, because the catch must still wrap its result (language_data.md §4).
Tail calls inside the functions `e` calls are unaffected.

A program decides with ordinary operations on the result, for example

    let r = catch(trial(power(x), power = f))
    if item(r, 0) == "ok": ...

**Provisional:**

- The kinds are part of the node, not an evaluated expression: a non-empty
  tuple of distinct non-empty strings. A `catch` whose kinds are anything
  else builds an `invalid` node, which fails with `invalid_code` when it runs.
- An error raised while the catch evaluates `e` is caught; nothing is
  evaluated before `e`.

## 3. Raise

**Decided:**

    ("raise", kind, detail)

evaluates `kind`, then `detail`, and fails with the error
`("program", kind, detail, where)`, where `where` is the `raise` node
(section 4). A program cannot choose the origin: whatever it raises has
origin `program`, so a program cannot make its own failure look like the
language's. It can use any kind name, including one of the language's, so an
interpreter written in SHEAR can reproduce the host machine's failures.

**Provisional:**

- `kind` must be a string; anything else fails with `wrong_kind`
  (operation `raise`), and the empty string fails with `malformed`.
- `detail` may be any value. Programs are encouraged to use `(name, value)`
  pairs as the language does.
- A failure while evaluating `kind` or `detail` is that failure, not the
  raise.

## 4. The error value

**Decided:**

An error is a plain tuple

    (origin, kind, detail, where)

- **origin** says who reported it, and the machine sets it:
  `"program"` (`raise`), `"language"` (a rule of the language was broken),
  `"runtime"` (the runtime refused a write or an activation) or `"limit"`
  (a resource limit was hit). Following the research branch's distinction
  between a semantic result and evaluator status, a `limit` error is a status,
  not a verdict about the program; it is catchable so that a program can
  reject a runaway candidate under trial.
- **kind** names what happened: one of the catalogue of section 6, or a name
  the program chose.
- **detail** holds the facts as data. For errors the language reports it is a
  tuple of `(name, value)` pairs, the way `linksof` returns a function's
  links. It names the kind of an offending operand rather than holding the
  operand itself.
- **where** is `(function, node)`: the function and the graph-form node that
  failed. A node identity follows edits by continuity, unlike a line number,
  and the printer can show its source.

An error is an ordinary value: it can be compared with `eq`, taken apart with
`item`, stored in a cell and passed on.

A human-readable message is not part of the value. Tooling derives it from
the value (section 7), so improving a message never changes what a program
observes.

**Provisional:**

- Detail pairs are sorted by name, each name appearing once.
- Detail values are ints, strings, entity ids and canonical kind names.
  Constraint results appear as `"violated"` or `"unknown"`.
- `where` names the node whose instruction failed. A failure on entering a
  callee (wrong arity, an absent target) is the call node in the caller;
  a depth-limit failure is the call that would exceed the limit. Inside a
  trial, `where` names the candidate's function and node.

## 5. Origins of host failures

**Provisional:**

The machine maps the reference model's exceptions to origins:

    LanguageError (but not CallDepthExceeded)    language
    a program's raise                             program
    CellContentRejected, RelationConstraintRejected,
    ActivationRejected (with ActivationConflict)  runtime
    CallDepthExceeded                             limit

Any other exception escaping an operation is a failure of the model (section
1) and is neither caught nor given an error value. If such an exception turns
out to be reachable from a well-formed program's own request (for example
from `define` inside `activate`), it is reported to the owner, not silently
mapped.

## 6. Kind catalogue

**Provisional:**

The kinds the language and the runtime report. `operation` is the
graph-form operation kind that failed (`add`, `item`, `if`, `apply`,
`write`, `raise`, ...).

| kind | origin | detail fields | when |
| --- | --- | --- | --- |
| `wrong_kind` | language | `expected`, `got`, `operation` | an operand has the wrong kind; `got` is its canonical kind (`constraints.kind_of`), `expected` is `int`, `bool`, `tuple`, `str` or `callable` |
| `out_of_range` | language | `index`, `length`, `operation` (`item`); `length`, `operation`, `start`, `stop` (`slice`) | an index or slice is outside a tuple |
| `arity` | language | `expected`, `function`, `got` | a call or application passes the wrong number of arguments; `function` is the callee, or a closure's owner |
| `absent` | language | `entity`, `operation` | a callable's target, or a closure's owner or body, is not in the active version |
| `not_a_function` | language | `entity`, `operation` | an operation needs a function and the entity is not one |
| `not_a_cell` | language | `entity`, `operation` | `read` or `write` names an entity that is not a cell |
| `name_in_scope` | language | `name` | a `let` name is already in scope |
| `unknown_name` | language | `name` | a name read with `arg` is not in scope |
| `malformed` | language | `operation`, `problem` | a value built at run time is not well formed: a function, closure or quote, activation or trial pairs, an edit `define` rejects, a raise with an empty kind |
| `invalid_code` | language | `problem` | the node is `invalid` or is not a code node |
| `cell_rejected` | runtime | `cell`, `constraint`, `operation` | a write's content is violated or unknown under the cell's constraint |
| `relation_rejected` | runtime | `constraint`, `operation`, `relation` | a write leaves a constraint relation violated or unknown |
| `activation_rejected` | runtime | `reason`, and `cell`, `constraint`, `relation` when the runtime names them | the runtime rejects an activation or a trial candidate |
| `activation_conflict` | runtime | `reason` | an activation conflicts with one made since its source state |
| `no_capability` | runtime | `operation` | `activate` or `trial` runs without the activation capability, including in code under trial |
| `depth_limit` | limit | `limit` | a call would exceed `CALL_DEPTH_LIMIT` |

`problem` and `reason` are text taken from today's messages; they are the only
free text in a detail.

The acceptance tests pin the kinds and details they use. Adding a kind is
allowed and is named in the PR; renaming or removing one is the owner's
decision.

## 7. Host interface

**Provisional:**

- `shear.errors` holds the catalogue as `KINDS` (kind to origin) and
  `describe(error)`, which renders an error value as text for people: its
  kind, its detail and the function and node it names. It does not take part
  in execution.
- An exception that escapes a run keeps its class (`LanguageError`,
  `CellContentRejected`, `ActivationRejected`, `CallDepthExceeded`, ...) and
  carries the error value as `.error`, equal to what `catch` would have
  produced. It is set where the failure happened and is not replaced by
  outer frames or by an enclosing run of a trial.
- A language failure stays an instance of exactly `LanguageError` with
  today's message: existing tests compare class names between the host
  machine and the interpreter written in SHEAR, and match message prefixes
  such as `inner: add operands`. Kind and detail are attached to the
  exception, not expressed as subclasses.
- An uncaught `raise` escapes as `Raised`, a subclass of `LanguageError`.
  The implementation keeps that subclass private to `machine.py` while
  setting its class name and qualified name to `Raised`; no new Python
  constructor or public import is added.

## 8. Graph form, bytecode and machine

**Provisional:**

- `operations.py` gains `catch` (code role `body`, variable arity: one or two
  input operands, the kinds as payload, built and collapsed by its own case
  like `let`) and `raise` (positional, code roles `kind` and `detail`).
  Continuity, lowering and syntax derive from the table as for every
  operation (`tests/test_operations.py`).
- Lowering: `catch` becomes one instruction that enters `body` under a
  handler, for example `CATCH body kinds`; `raise` evaluates its operands and
  ends with an instruction that fails, for example `FAIL`. `RAISE` keeps its
  meaning for invalid nodes.
- A handler records the control-stack depth, the operand-stack height and the
  number of live calls when it is entered. A failure unwinds to the nearest
  handler that accepts it, releases the holds of every call above it, drops
  the operand stack to the recorded height, pushes `("failed", error)` and
  continues after the catch. With no accepting handler the failure leaves the
  run as an exception, releasing every hold as today.
- A failure inside `trial` leaves the nested run of the candidate as an
  exception carrying its error (the candidate runtime is discarded as today),
  and the enclosing run treats it like any other failure of the `trial`
  instruction.
- A handler accepts only a failure whose error value the machine set during
  the same run. Each `run` gets a fresh private run mark, the nested run of a
  `trial` shares it, and the machine stamps it on every error value it sets.
  A host exception that carries an `.error` of its own, or an exception
  escaping an independent `run` started by host code (an evaluator that calls
  `run`), is not this run's failure and is not caught (section 1). The mark
  is not part of the error value and not a public interface.
- Holds, code in flight and the two-version bound follow from releasing the
  unwound calls; nothing else about versions changes.
- Existing nodes lower exactly as before: every corpus program of main keeps
  its StateID, rendered text and bytecode.

## 9. Syntax

**Provisional:**

    catch(EXPR)
    catch(EXPR, "kind", ...)
    raise(EXPR, EXPR)

The kinds of `catch` are string literals. `catch` and `raise` become reserved
names (syntax.md §2); in backquotes they stay ordinary names.

## 10. Embedded compiler and VM

**Provisional:**

The compiler written in SHEAR does not lower `catch` or `raise`; it stays
within what it covers (`self_hosting.LOWERED`), and the interpreter written in
SHEAR keeps `vm_trap`. Both are follow-ups (section 13).

## 11. Corpus

**Decided:**

The `errors` tag and three examples (`shear/examples/errors.py`):

- `safe_install` trials each candidate under `catch` and installs it only if
  it returns the expected value. A candidate that indexes an empty tuple and
  one that recurses without end are reported by kind and never installed.
- `account_report` withdraws under `catch(..., "cell_rejected")`: an
  overdraft is reported as `("refused", "violated")`, the attempt counter it
  wrote first keeps its count (no rollback), and a withdrawal of a string
  passes through as the language error it is.
- `lookup` raises its own `missing` error, catches it selectively to fall back
  to a default, lets a malformed table's language error through, and reads
  the origin, kind and detail of both.

## 12. Acceptance

`tests/test_error_handling.py` pins:

- `catch` results, wrapping and the filter, including a pass-through error
  keeping its origin, kind, detail and where;
- the error value of `raise` and of language, runtime and limit failures,
  with exact detail for the kinds it uses;
- errors from a callee and from code under trial, and released holds;
- no rollback;
- `.error` on escaping exceptions and `describe`;
- graph form, syntax and continuity of the new operations, and that a
  malformed `catch` fails closed;
- the corpus through the new layer: every step of every canary corpus program
  called through `catch` gives `("ok", expected)` or a failure of the expected
  origin, with the same cells and later steps; a filter that matches nothing
  changes nothing; wrapping any corpus function's body in `catch` keeps the
  identity of every node it had;
- that every program of main keeps its StateID, text and bytecode.

## 13. Open

**Open:**

- Re-raising a caught error unchanged. Not needed while filters choose what a
  catch handles; revisit if a program needs to inspect an error before
  deciding to pass it on.
- Declared error kinds: program entities, like cells, naming a kind and
  constraining its detail, so renames follow continuity and tooling can list a
  program's errors (roadmap.md "Later").
- Contracts that state which kinds a function may raise. Raising is an
  effect, and contract_model.md §18 forbids inventing effect semantics
  through contract fields before an effect model exists.
- A step budget, so that a non-terminating candidate can be stopped and
  reported as a `limit` error (bytecode.md section 8).
- Reason codes for rejected activations instead of text.
- A cause chain for an error raised while handling another.
- Lowering `catch` and `raise` in the compiler written in SHEAR, running them
  in the interpreter written in SHEAR, and replacing its `vm_trap`.
- Rollback of cell writes on failure: not wanted for now.
