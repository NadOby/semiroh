# Metaprogramming

**Status: implemented.** `semiroh/lang.py` implements the metaprogramming
operations below, and `tests/test_metaprogramming.py` passes; since
roadmap task 4 its programs are loaded into graph form (graph_form.md), with
the behaviour assertions unchanged.

The first program (first_program.md) changes only when the host changes it.
This step lets a running program write code and install it into itself: the
program carries its own compiler, and its self-modification goes through the
same activation, with the same checks, as the host's.

## 1. Scope

**Decided.**

In scope:

- code as data: building expression trees with holes (`quote`);
- function values built at run time (`function`);
- replacing the program's own functions by activation (`activate`), gated by
  an activation capability that the host grants per run;
- what a running frame does after its own program changed.

Out of scope: creating, removing or renaming entities from inside the
language (creation would force ownership_model.md §13's placement
question); changing cells or links relations from inside the language;
reading code back as data and taking tuples apart; trials from inside the
language (activation_model.md §8; language_trials.md); error handling inside the language;
nested quotation; any capability model beyond one per-run grant.

## 2. Code as data

**Decided**, except nesting (**Provisional**).

An expression tree is an ordinary tuple value, and `lit` already returns one
verbatim. `quote` adds holes:

    ("quote", template)    template with every hole filled
    ("unquote", e)         a hole: replaced by the value of e

A hole may appear at any depth of the template, including the template
itself. `e` is evaluated in the scope of the function running the `quote`,
so it can use parameters, reads and calls. Everything that is not a hole is
copied as it is. A tuple whose head is `"unquote"` and that does not have
exactly one operand is a `LanguageError`. `lit` is unchanged and never fills
holes.

Provisional: quotation does not nest. A hole inside a quote inside a
template is still filled by the outer `quote`. To put a literal
`("unquote", ...)` into generated code, unquote a `lit` of it:
`("unquote", ("lit", ("unquote", e)))`.

Example: a compiler that emits the body of `x` to the power `n`.

    emit(n) = ("if", ("eq", ("arg", "n"), ("lit", 0)),
                 ("lit", ("lit", 1)),
                 ("quote", ("mul", ("arg", "x"),
                     ("unquote", ("call", "emit",
                         ("sub", ("arg", "n"), ("lit", 1)))))))

`emit(2)` evaluates to `("mul", ("arg", "x"), ("mul", ("arg", "x"),
("lit", 1)))`.

## 3. Function values

**Decided.**

    ("function", params, body)    a Function value

Both operands are evaluated. `params` must be a tuple of distinct non-empty
strings and `body` a non-empty tuple, as for `Function` itself; anything
else is a `LanguageError`. The body is not checked further: generated code
is checked when it runs, like host-installed code, or by constraints the
program declares on itself (section 4).

A function value is an ordinary value. It can be passed, returned, compared
with `eq`, and stored in a cell whose constraint allows it. `IsKind` knows
only the core kinds, so for now such a constraint is an `External`
evaluator that checks `kind_of(content) == "function"`; whether a layer can
add kinds is open.

## 4. Self-modification

**Decided**, except the representation of the capability (**Provisional**).

    ("activate", link1, f1, ..., linkN, fN)    N >= 1

replaces the functions named by `link1` ... `linkN` with the function values
`f1` ... `fN`, in one activation:

1. Evaluate `f1` ... `fN` in order.
2. Check the operands. They come in link/expression pairs; each link
   resolves through the running function's links, as for `call`, to an
   entity whose value in the active state is a function; no entity is named
   twice; each `fi` is a function value. A failed check is a `LanguageError`.
3. Check the capability (below). Without it: `ActivationRejected`.
4. Build `transform_with_mapping(active_state, {target_i: f_i}, mappings)`,
   where `mappings` declares every entity of the active state continuous
   with itself, and call `runtime.activate` on the result with no
   converters. A rejection propagates unchanged as `ActivationRejected` and
   leaves the program as it was.
5. Return `None`.

Either every change lands, in one new version, or none does. Every entity
stays continuous with itself and only function values change, so cells keep
their content (activation_model.md §4) and links relations are untouched.

In graph form (graph_form.md §6) step 4 is `define(active_state, {target_i:
f_i})`: the targets' old nodes disappear, their new nodes are placed under
them, every other entity is continuous with itself, and each `f_i`'s link
names resolve through its target's link table, which replaces the links
relation.

**Capability.** activation_model.md §3 decided that a program without the
activation capability cannot replace its own running version. Capabilities
are not modelled yet, so the grant is minimal:

    run(runtime, entry, *args, may_activate=False)

A run without the grant raises `ActivationRejected` at `activate`, after the
operand checks. `quote` and `function` need no capability: they produce
values, not program states. How capabilities are represented stays
provisional until capabilities are modelled.

**The program's own constraints.** Activation checks every constraint
relation against the new state, including relations whose endpoints are
functions: an endpoint that is not a cell contributes its value
(relation_model.md §7). A program can therefore declare what its code must
satisfy, for example with an `External` evaluator over a function's value,
and a self-modification that breaks it is rejected like any other
activation. In graph form a function's value is its definition and its code
is the nodes it owns; a function endpoint contributes both, as its owned
subtree (relation_model.md §7, graph_form.md §7).

## 5. Code in flight

**Provisional.**

activation_model.md §5 decided that a frame executing when an activation
happens keeps executing in the version it started in and holds that version.
The language uses version coexistence with switching at call boundaries:

- the frame that ran `activate`, and every caller still waiting on it,
  finishes the body it started with;
- every call made after the activation, from any frame, enters the function
  as it is in the active version. Every call in this language goes through
  a link, like an Erlang fully qualified call; there are no local calls;
- `read` and `write` always use the active version's cells. `activate`
  never changes cells and cells transfer by identity, so their content is
  continuous.

`activate` keeps every entity and every links relation, so links a frame
resolved before the activation still name the same entities after it. In
graph form a frame evaluates the nodes of the version it started in, and
the nodes name their targets directly (graph_form.md §6).

**At most one activation per run.** The run's frames hold the previous
version until they return, so a second `activate` in the same run is
rejected by the two-version bound (activation_model.md §7) with
`ActivationRejected`; the first activation stays. When the run ends,
returning or raising, its frames release the previous version and it
retires.

## 6. API

Additions to `semiroh/lang.py`:

    ("quote", template)               code as data with ("unquote", e) holes
    ("function", params, body)        a Function value
    ("activate", link, f, ...)        replace linked functions, one activation
    run(runtime, entry, *args, may_activate=False)

A run without `may_activate` behaves exactly as before and never changes
program state.

## 7. Acceptance tests

`tests/test_metaprogramming.py` pins the behaviour above. It passes unchanged,
together with `tests/test_first_program.py`. The implementation also has
unit tests for each new operation and each `LanguageError` case, for `lit`
versus `quote`, and for the order of checks in `activate` (operand errors
before the capability), plus a seeded property test where a `quote` without
holes equals `lit`.

## 8. Implementation notes

- The evaluator uses run-scoped context containing the runtime and
  `may_activate`.
- Values read from cells or passed as arguments are canonical: a tuple
  arrives as a tagged node. `params` and `body` are decoded before building a
  `Function`, and canonical function values are accepted by `activate`.
- `transform_with_mapping` and `Runtime.activate` are used unchanged.
- No core semantic model changes were required.
- The implementation keeps the evaluator small and leaves capability
  representation provisional.
- The module docstring now states that activation can change program state
  when the run has been granted the capability.
- `activation_model.md` §5 records that this language uses version
  coexistence with switching at every call.
- Section 9 records the deferred questions resolved by this program.

## 9. Deferred questions this program needed

- ownership_model.md §13: none. The language creates no entities, removes no
  entities, and changes no ownership.
- activation_model.md §5, code in flight: answered provisionally for this
  language. Frames continue in their starting version; calls after activation
  enter the active version.
- activation_model.md §3, capabilities: answered provisionally with the
  minimal per-run `may_activate=True` grant.
- evaluator references by name (`External`) work unchanged.
