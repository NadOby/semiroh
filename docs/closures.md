# Closures

**Status: planned** (roadmap task 17).

The canary corpus has one remaining gap: a function cannot return an
executable value that keeps bindings from the scope in which it was created.
This document adds closures without changing `Function`, activation, or the
graph-as-program rule.

## 1. Scope

**Decided:**

In scope:

- anonymous callable values;
- lexical capture by value;
- passing, returning and applying closures;
- storing closures as ordinary values;
- ordinary arity and tail-call behaviour;
- graph form, bytecode, and the compiler and VM written in SEMIROH;
- `make_adder` and `compose` in the corpus.

Out of scope:

- mutable captured bindings;
- implicit capture inference;
- recursive self-referential closure construction;
- changes to function-reference continuity;
- changes to activation capability semantics;
- a new lifetime or garbage-collection mechanism.

`Function` remains code as data. A value produced by the existing
`function` operation is not directly callable and still needs `activate`
before it becomes installed program code.

## 2. Closure expression

**Provisional:**

The input form is:

    ("closure", (p1, ..., pN), (c1, ..., cM), body)

`p1 ... pN` are the closure's parameters.

`c1 ... cM` are names explicitly captured from the environment in which the
closure expression is evaluated.

`body` is ordinary SEMIROH code. It is part of the semantic graph like every
other expression tree; creating a closure does not turn its body into an
opaque `Function` value.

Parameter and capture names must be non-empty strings and unique within their
respective lists. A name may not occur in both lists.

Every declared capture must exist in the current lexical environment when the
closure is created. Otherwise creation raises `LanguageError`.

Capture names are explicit in this version. Inferring free variables would add
a subtree dependency to closure construction and to lowering; explicit capture
names keep the closure node's semantics local. A future source syntax may
infer them as sugar without changing the semantic operation.

## 3. Captured environment

**Decided:**

Capture is by value when the closure is created.

For:

    ("let", "n", ("lit", 4),
        ("closure", ("x",), ("n",),
            ("add", ("arg", "n"), ("arg", "x"))))

the closure contains the current value of `n`.

Calling the closure does not inspect the caller's lexical environment. Its
environment consists only of:

1. the captured names and values;
2. its parameters and the arguments supplied by the call;
3. names introduced by `let` while its body runs.

An `arg` in the body that is not provided by one of those sources raises
`LanguageError`. There is no dynamic-scope fallback.

Only explicitly declared captures belong to the closure value. Unused names
from the creating frame do not affect the closure's semantic value.

Captured values are ordinary immutable semantic values. Capturing an
`EntityID`, another closure, a tuple, or other value does not give it special
continuity behaviour.

## 4. Closure value

**Provisional:**

A closure is a distinct semantic record, conceptually:

    Closure(
        owner,
        body,
        params,
        captures,
    )

where:

- `owner` is the function entity whose graph contains the closure body;
- `body` is the `EntityID` of the body's graph root;
- `params` is the ordered parameter tuple;
- `captures` is the ordered name/value tuple captured at creation.

The body remains graph code. The closure does not contain a second opaque copy
of that code.

Closures are ordinary values. They may be passed, returned, compared by the
ordinary semantic equality machinery, captured by another closure, and stored
where the containing value is otherwise permitted.

Two closures with the same code identities, parameters and captured semantic
values have the same semantic value. Uncaptured names in their creating frames
are irrelevant.

## 5. Calling

**Decided:**

`apply` and `applyv` accept either:

- the existing reference to an installed function; or
- a closure.

`call` remains a call through a statically resolved function link.

For a closure call:

1. check that the value is callable before evaluating later arguments, as
   `apply` does now;
2. evaluate the arguments in the caller;
3. check the closure's arity;
4. enter the closure's owner in the active program version;
5. execute the closure body with the captured environment plus the supplied
   parameters.

A returned closure therefore remains callable after its creating frame has
finished.

Creating or applying a closure requires no activation capability.

A `Function` value is still not callable. In particular:

    ("apply", ("function", ...), ...)

remains a `LanguageError`.

## 6. Program versions and continuity

**Provisional:**

A closure's `owner` and `body` are semantic entity identities, not a private
copy of a historical program state.

Calling a closure resolves those identities in the active program version,
the same general rule used by current function references.

Therefore:

- if continuity preserves the closure body and its owner across an edit, an
  existing closure invokes their active versions;
- if the required owner or body is absent, applying the closure raises
  `LanguageError`;
- captured values themselves are not recomputed or recaptured after an
  activation.

This task does not solve the existing problem that `EntityID` values held as
runtime data do not automatically follow a rename. Closure code identities
have the same limitation for now.

No additional version-retention or garbage-collection rule is introduced.

## 7. Graph form and bytecode

**Decided:**

`closure` is a graph-form node kind.

Its body is an ordinary child code node. Its parameter and capture-name lists
are node data; evaluating the closure node does not evaluate its body.

`function_at` round-trips the closure expression.

Lowering produces a closure-construction instruction containing enough
information to identify the body, parameters and capture names. The owner is
the function whose frame evaluates that instruction.

Applying a closure creates the same kind of machine call frame as an ordinary
function call, except that its initial environment contains the captured
values in addition to its parameters.

A closure application in tail position replaces its caller exactly as an
ordinary tail `call` or `apply` does. It does not consume another entry of the
machine's call-depth limit.

## 8. Embedded compiler and VM

**Decided:**

Adding closures extends the language carried by a program's compiler; the
self-hosted path must not silently lose the operation.

The lowering pass written in SEMIROH emits the same closure bytecode as the
host lowering pass.

The bytecode interpreter written in SEMIROH executes closure construction and
closure application for the pure-code subset it already supports.

The compiler bootstrap fixpoint and the existing self-hosting acceptance tests
continue to hold.

The internal representation used by the SEMIROH-written VM need not be the
host Python `Closure` record, provided its observable behaviour is the same.

## 9. Corpus

**Decided:**

The corpus gains at least:

- `make_adder`: `make_adder(n)` returns a closure that adds the captured `n`
  to its argument;
- `compose`: returns a closure that applies captured callable values in
  composition.

These programs use no activation capability.

After they are added, `semiroh.examples.MISSING` is empty.

## 10. Acceptance

**Decided:**

`tests/test_closures.py` pins the behaviour above.

It covers at least:

- `make_adder`;
- `compose`;
- a closure returned from a function and called after that function's frame
  has finished;
- explicit capture by value and independence from the caller's scope;
- passing and returning closures as ordinary values;
- closure arity errors;
- invalid and duplicate parameter/capture names;
- a missing declared capture;
- an undeclared free `arg` failing rather than resolving dynamically;
- `apply` and `applyv` accepting closures;
- `apply` of a `Function` value remaining invalid;
- closure calls requiring no activation grant;
- a deep chain of tail closure applications not growing the call stack;
- graph-form round-trip;
- host and SEMIROH lowering agreeing for closure code;
- the SEMIROH VM running the closure corpus cases it covers;
- `MISSING` becoming empty.

The existing suite remains unchanged except where an old test explicitly says
that only an `EntityID` can be applied; such a test is renamed to state the
remaining rule rather than deleted.

## 11. Deferred questions

**Open:**

- Whether source syntax should infer captures while keeping explicit captures
  in the semantic form.
- Whether closures eventually use fully state/version-pinned semantic
  references rather than the language layer's current active-version
  `EntityID` behaviour.
- How closure values containing code identities migrate when runtime values
  acquire general reference-continuity support.
- Recursive closure construction and mutually recursive anonymous functions.
- Mutable lexical bindings, if the language ever adds them.
