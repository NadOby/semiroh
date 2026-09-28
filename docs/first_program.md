# First Program

**Status: done.** `semiroh/lang.py` implements this document; the acceptance
tests in `tests/test_first_program.py` pass unchanged, and no design question
deferred by ownership_model.md §13 turned out to be needed (section 8).

## 1. Scope

In scope:

- a tiny expression language, interpreted directly over semantic state;
- functions, links between them, and mutable cells;
- running under `Runtime`, so cell and relation constraints apply;
- self-modification driven by the host (Python): produce a new program state
  with a transformation, then `Runtime.activate` it.

Out of scope: source syntax and parsing, compilation and native code,
metaprogramming from inside the language (a program producing its own
transformation; the natural next step), types beyond cell constraints,
concurrency, and switching code in flight.

## 2. Program representation

A **function** is an entity whose value is `Function(params, body)`, a
semantic record. `params` is a tuple of parameter names; `body` is an
expression tree of plain tuples:

    ("lit", value)              a literal
    ("arg", name)               a parameter
    ("add"|"sub"|"mul", a, b)   integer arithmetic (bool is not int)
    ("lt"|"eq", a, b)           comparison, returns bool (lt on ints only)
    ("if", cond, then, else)    cond must evaluate to a bool
    ("seq", e1, ..., en)        evaluates in order, returns the last value
    ("call", link, e1, ...)     calls the function the link names
    ("read", link)              current content of the linked cell
    ("write", link, e)          writes the linked cell, returns the value

A body never contains raw `EntityID`s. A function refers to other functions
and cells by **link names**, resolved through a **links relation** stored in
its own entity:

    links(f, double=DOUBLE, counter=COUNTER)
        == Relation("links", {"function": f, "double": DOUBLE,
                              "counter": COUNTER})

Because links are relations, renaming a function or cell follows declared
continuity (relation_model.md §5) and function bodies never change. A
function with no links relation has no links; more than one is an error. The
role name `function` is reserved.

**Cells** are ordinary `CellDeclaration`s. The **entry point** is simply the
function entity the host passes to `run`. **Ownership** is not used.

Deferred questions (ownership_model.md §13) stay deferred unless the
implementation actually hits them; report which ones it did.

## 3. Running

`run(runtime, entry, *args)` evaluates `entry` in `runtime.active` with its
parameters bound to the canonicalized arguments, and returns the result.

- Every function call, including the entry, enters a frame with
  `runtime.enter(function)` and releases it on return and on failure, so a
  finished run leaves no holds.
- `read` and `write` go through `runtime.read` and `runtime.write`, so cell
  constraints and constraint relations are enforced; their errors propagate
  unchanged (for example `CellContentRejected`).
- Running never changes program state or `StateID`.
- `LanguageError` (a `ValueError`) covers: an unknown operation, an unknown
  link name, a wrong number of arguments, calling something that is not a
  function, reading or writing something that is not a cell, and operands of
  the wrong kind.

## 4. Self-modification

The host changes the program with ordinary transformations of
`runtime.active.state` and activates the result. Every cell needs declared
continuity at activation (activation_model.md §4), so host code maps each
entity to itself unless it means otherwise. The acceptance tests show a
behaviour change, a rename that keeps callers working, and a rejected
activation that leaves the old program running.

## 5. API

Module `semiroh/lang.py`, a layer on top of the core (not re-exported from
`semiroh/__init__.py`):

    Function(params, body)      semantic record; body stored canonicalized
    function_of(value)          Function held by a Value, or None
    links(function, **targets)  the links Relation
    run(runtime, entry, *args)  evaluate, return the result
    LanguageError               ValueError subclass

## 6. Acceptance tests

`tests/test_first_program.py` pins the behaviour above. It fails until
`semiroh/lang.py` exists; the implementation is done when it passes without
changes. The implementer adds unit tests for the interpreter itself
(each operation, each `LanguageError` case) and a seeded property test where
it fits.

## 7. Implementation notes

- Values are canonical: a `Function` body read back from a `Value` contains
  tagged tuple nodes (`("__type__", "tuple", items)`); decode them before
  evaluating.
- Find a function's links with `relation_index(state)[f]`: the relation
  entities where `f` plays the role `function` and whose kind is `links`.
- Keep it small: one module of a few hundred lines at most.
- When done: add a `CHANGES.md` entry, mark this document's status, and
  list which deferred questions the implementation needed, with the
  simplest answer it used.

## 8. Deferred questions this program needed

None of ownership_model.md §13's unresolved areas or deferred items came up.
Section 2 already decided ownership is not used by this program: functions
and cells sit in `State.values` with an empty ownership relation, entity
continuity for activation is declared through `transform_with_mapping`'s
`entity_mappings` alone (`identity()` in the tests), and nothing in
`semiroh/lang.py` reads or writes ownership. A future program that needs a
module or program root, explicit ownership transfer, or creation placing a
new entity under an owner would be the first to force an answer there.
