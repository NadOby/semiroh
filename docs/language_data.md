# Data, Local Names and Callable Values

**Status: implemented** (roadmap.md task 6; extended by tasks 10 and 17).
`shear/lang.py` and `shear/bytecode.py` implement it;
`tests/test_data_ops.py` is the main acceptance suite, and
`tests/test_data_graph_form.py` covers graph form and the frames of tail calls.
Closures are specified in closures.md and tested in `tests/test_closures.py`.

The canary corpus (corpus.md section 4) originally found four programs the
language could not express: insertion sort, map and fold, local variables,
and a loop deeper than the reference interpreter's stack. Task 6 added what
they needed. Later tasks extended callable values with tuple-argument
application and lexical closures.

## 1. Tuples

**Decided:**

    ("tuple", e1, ..., en)      a tuple of the values, n >= 0
    ("len", t)                  the length of tuple t
    ("item", t, i)              element i of t, 0 <= i < len(t)
    ("slice", t, start, stop)   t[start:stop], 0 <= start <= stop <= len(t)
    ("concat", t1, t2)          t1 followed by t2

Indices are ints (a bool is not an int). There is no negative indexing and
no clamping: anything outside the stated bounds, or an operand of the wrong
kind, is a `LanguageError`. Tuples read from cells or passed as arguments
are canonical and are accepted like any other tuple.

## 2. Local names

**Decided:**

    ("let", name, e, body)

evaluates `e`, binds `name` to its value for `body`, and returns the value
of `body`. `("arg", name)` reads parameters, closure captures and let-bound
names alike.

A `let` name that is not a non-empty string, or that is already in scope
(a parameter, closure capture or enclosing `let`), is a `LanguageError`:
shadowing would be ambiguous.

Closure construction may explicitly capture parameters and enclosing
`let` names. Capture is by value; see closures.md.

## 3. Callable values

**Decided:**

Function references, indirect application, and lexical closures.

**Provisional:**

The representation and continuity of function references.

    ("ref", link)               a reference to the linked function
    ("apply", f, e1, ..., en)   call callable value f with n arguments
    ("applyv", f, args)         call callable value f with tuple args

A function reference is an ordinary value: it can be passed, returned,
compared with `eq`, captured by a closure and stored in a cell.
Provisionally it is the function's `EntityID` (kind `entity_id`, so a cell
can constrain it with `IsKind("entity_id")`).

A closure is a distinct ordinary callable value containing semantic
owner/body identities, parameters and explicitly captured lexical values.
Its representation and continuity rules are specified in closures.md.

`apply` and `applyv` accept either:

- a function reference; or
- a closure.

A `Function` value produced by the `function` operation remains code as data
and is not callable directly. It must be installed with `activate` before a
function reference can call it.

`apply` evaluates and validates its callable before evaluating later
arguments. `applyv` likewise validates the callable before evaluating its
argument tuple, then requires that value to be a tuple.

For a function reference, application enters the referenced function as it
exists in the active version and performs the ordinary arity check.

For a closure, application resolves its owner and body in the active program
version, performs the closure arity check, and starts the body with its
captured environment plus parameter bindings. The caller's lexical scope is
not consulted.

`ref` of a link that does not name a function is a `LanguageError`.
Application of anything that is neither a valid function reference nor a
closure is also a `LanguageError`.

A function reference held in runtime data is not a relation endpoint, so it
does not automatically follow a rename of its function; applying it
afterwards fails if the old `EntityID` is absent from the active state.
General continuity for references stored as data remains open
(activation_model.md section 6).

Closure code identities currently have the corresponding active-version
`EntityID` limitation, while captured values are never recomputed after an
activation.

## 4. Tail calls

**Decided:**

A `call`, `apply` or `applyv` in tail position does not grow the machine's
call stack (bytecode.md section 4), whether the indirect target is a function
reference or a closure.

Tail position is:

- the body root;
- both branches of an `if` in tail position;
- the last item of a `seq` in tail position;
- the body of a `let` in tail position.

The body of `catch` is never in tail position. The catch must retain its
caller frame so that a successful result can still be wrapped as
`("ok", value)`, or a caught failure as `("failed", error)`. Tail calls
inside functions called by the caught expression are unaffected.

The caller's frame is released when the callee's frame is entered. Holds,
code in flight (metaprogramming.md section 5), results and ordinary error
ordering are otherwise unchanged.

A tail closure application obeys the same rule: it replaces its caller
rather than consuming another entry of `CALL_DEPTH_LIMIT`.

## 5. Corpus

**Decided:**

Task 6 added the `data` and `higher order` tags and the tier-2 examples:

- insertion sort;
- map;
- fold;
- local bindings;
- deep tail recursion;
- sorting through a function reference that can be changed between runs.

Task 7 later removed the remaining host-stack limit for non-tail recursion.

Task 17 added closure examples `make_adder` and `compose`, closing the final
corpus gap. `shear.examples.MISSING` is currently empty.

## 6. Acceptance tests and notes

`tests/test_data_ops.py` pins tuple operations, local names, function
references and task-6 tail calls.

`tests/test_data_graph_form.py` pins their graph representation and call-frame
behaviour.

`tests/test_closures.py` extends the callable-value rules with:

- closure application through `apply` and `applyv`;
- capture by value;
- passing, returning, storing and comparing closures;
- capture of another callable;
- closure arity and invalid-target errors;
- error ordering;
- tail closure calls;
- continuity across activation.

Graph-form roles are documented in graph_form.md section 3 and bytecode
execution in bytecode.md.
