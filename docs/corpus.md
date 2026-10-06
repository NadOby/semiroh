# Canary Corpus

**Status: implemented.** `shear/examples/` exists; the acceptance tests in
`tests/test_corpus.py` pass.

A library of small programs with expected results. Every interpreter and
every representation of code must run the whole corpus unchanged. That
turns a change of representation (roadmap.md task 4) into a differential
test, and each program the language cannot express yet names a missing
feature.

## 1. Scope

**Decided.**

In scope: tier 1, programs the current language (`shear/lang.py`) can
express; the data format; `play`, which runs an example with a given
interpreter; the list of wanted programs the language cannot express yet.

Out of scope: host-driven transformations (renames and other host edits
stay in the acceptance tests of the language); benchmarks; a standard
library.

## 2. Format

**Decided.**

Module `shear/examples/` (a package, so programs can be split across
files):

    Raises(error)
        expected outcome of a step that must raise `error` (a subclass
        counts)

    Step(entry, args, expect, may_activate=False, cells={})
        one run: `run(runtime, entry, *args, may_activate=...)` must
        return a value semantically equal to `expect` (compared by
        canonical serialization, so True != 1), or raise as `Raises`
        says; afterwards each cell in `cells` must hold that content

    Example(name, tags, program, scenarios, context=None, description="")
        `program` is a State in the input format (tuple Function bodies
        and links relations); each scenario is a tuple of Steps run in
        order against one fresh `Runtime(load(program), context)`, the
        program loaded into graph form (graph_form.md)

    Wanted(name, needs)
        a program the language cannot express yet, and the feature it
        needs

    EXAMPLES: tuple[Example, ...]
    MISSING: tuple[Wanted, ...]
    TAGS = frozenset({"recursion", "side effects", "control",
                      "self-modification", "data", "higher order",
                      "errors"})

    ExampleFailed(AssertionError)
    play(example, run)
        runs every scenario with the given `run` function and raises
        ExampleFailed, naming the example, scenario and step, at the
        first mismatch; a step expecting a value that raises instead is a
        mismatch too

`run` has the signature of `shear.lang.run`; another interpreter passes
its own.

## 3. Tier 1 programs

**Decided**, the list itself is open-ended.

At least ten programs, covering every tag:

- recursion: factorial, fibonacci, gcd, sum to n, Collatz step count;
- control: absolute value, max, clamp or sign;
- side effects: a counter, an account whose balance cell rejects an
  overdraft (a step that raises `CellContentRejected` and a later step
  showing the balance unchanged);
- self-modification: the power compiler that compiles and activates, a
  compile that installs only after a `trial`, a function that replaces
  itself.

A side-effect example must check cells, or have a later step whose result
depends on an earlier write. A self-modification example must have a step
whose result shows the new code, run with `may_activate=True` where it
activates.

Tier 2 (roadmap.md task 6, language_data.md section 5) adds:

- data: `insertion_sort`, and `let_bindings` (a discriminant named once, a
  side-effecting bound expression that runs once, a `let` that reuses a
  parameter's name and raises);
- higher order: `map` and `fold`, run with function references passed as
  arguments;
- recursion: `deep_loop`, tail-recursive loops thousands of calls deep,
  through `call`, through `apply` and between two functions; and, after
  roadmap.md task 7, `deep_recursion`, a sum by recursion that is not a
  tail call, ten thousand calls deep;
- higher order and recursion: `map_long_tuple`, `map` over tuples of a
  thousand and two thousand elements;
- self-hosting (roadmap.md task 8): `compiler`, `lower` written in SHEAR,
  and `instrument`, a program that reads its own function, swaps in a
  version that counts its calls and compiles what it installed
  (self_hosting.md);
- self-hosting (roadmap.md task 10): `bootstrap`, the compiler swapped for
  functions that run their own chunks on an interpreter written in SHEAR,
  then compiling again (vm_in_shear.md);
- self-modification: `sort_swap`, which sorts a tuple in a cell with the
  function `order` refers to, activates a different `order` between two
  runs, and sorts again with the data still in its cell;
- closures (roadmap.md task 17): `make_adder`, which returns a closure
  capturing its argument by value, and `compose`, which returns a closure
  capturing callable values and applying them in composition;
- errors (roadmap.md task 20): `safe_install`, `account_report` and
  `lookup`, covering catchable failures, selective filters, program-raised
  errors and failure values.

The task-20 error examples exercise distinct boundaries:

- `safe_install` trials candidate implementations of `power` under `catch`.
  A candidate that indexes an empty tuple reports `out_of_range`, and a
  runaway recursive candidate reports `depth_limit`; neither is installed.
  A candidate that merely returns the wrong value is rejected normally, and
  only the correct candidate is activated.
- `account_report` increments an attempt counter before writing a constrained
  balance. It catches only `cell_rejected`, so an overdraft becomes
  `("refused", "violated")` while the earlier attempt write remains visible:
  `catch` does not roll back effects. Passing a string instead of an integer
  produces a language error that is not accepted by the filter and therefore
  still escapes.
- `lookup` uses `raise("missing", ...)` for an absent key. `find_or` catches
  only that program error and returns a default, while malformed table data
  still produces the language's `wrong_kind`. `why` catches both and exposes
  their origin, kind and detail as ordinary values.

## 4. Wanted programs

**Open.** Recorded in `shear/examples/missing.py` (`MISSING`).

`MISSING` is currently empty. The gaps discovered while extending the corpus
have all been closed by implemented roadmap tasks.

**Closed** by roadmap.md task 17: `make_adder`, the last remaining gap.
It needed an executable anonymous callable that captures bindings from its
creating lexical environment. `ref` names an already-installed function,
while `function` remains code as data that must be installed with `activate`.
Closures add the missing distinction: an executable value with explicit,
by-value lexical captures. `make_adder` and `compose` are now corpus examples.

**Closed** by roadmap.md task 7: `map_long_tuple`, which needed non-tail
recursion deeper than the Python stack. Tail calls (task 6) made loops
unbounded, but a call that was not in tail position still nested about 5
Python frames, so `map` failed from a tuple of 200 elements and
`insertion_sort` from 200. The bytecode machine keeps its calls on its own
stack (bytecode.md), and the examples `map_long_tuple` (a thousand and two
thousand elements) and `deep_recursion` (a sum ten thousand calls deep) are
tier 2.

**Closed** by roadmap.md task 6: the four programs this list first
recorded, now tier 2 examples. What each needed, as first written:

- `insertion_sort` needs a way to take a tuple apart at runtime (head/tail
  or an index operation) and a length operation, to iterate over a sequence
  of unknown length. The language only has fixed-shape literal tuples and
  `quote`/`unquote` for shaping code, not for walking runtime data whose
  length isn't known when the program is written.
- `map_and_fold` needs an `apply` operation that calls a function *value*
  directly: `call` only dispatches through a static link name resolved via
  the calling function's own links relation, so a function received as an
  argument or read from a cell cannot be invoked. It also needs the same
  tuple decomposition as insertion sort.
- `local_variables` needs a `let`/local-binding form to name an
  intermediate value within one function body; the only binding mechanism
  is a call's parameters.
- `deep_loop` needs tail-call elimination, or an iteration primitive, in
  the reference interpreter. The language has no loop construct, only
  recursion, and every `call` nests further Python stack frames in
  `shear/lang.py`'s `_call`/`_eval`. Measured against the `sum_to_n`
  tier-1 example: under the interpreter's default recursion limit of 1000,
  `sum_to_n(197)` succeeds and `sum_to_n(198)` raises `RecursionError` -
  about 5 Python stack frames per SHEAR call (measured on graph form;
  the tuple-body interpreter stopped one call earlier).

## 5. Acceptance tests

`tests/test_corpus.py` pins the format and the canary property: the corpus
must fail under deliberately broken interpreters (wrong integer results,
lost cell writes, an ignored activation grant, swallowed errors). The
implementation is done when it passes without changes.

Task 20 additionally uses the three `errors` examples as cross-boundary
canaries. They must run under the ordinary language path, round-trip through
text syntax, and add golden records without changing the golden records of
any pre-existing program (`tests/golden.py`).

## 6. Implementation notes

- Programs are data. Build them with `shear.lang` (`Function`, `links`)
  and core constructors only; host code appears only as evaluators in an
  example's `context`.
- Keep each program small and readable; one module per tag is fine.
- When done: add a `CHANGES.md` entry and mark this document's status.
