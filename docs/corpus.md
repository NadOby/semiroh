# Canary Corpus

**Status: implemented.** `semiroh/examples/` exists; the acceptance tests in
`tests/test_corpus.py` pass.

A library of small programs with expected results. Every interpreter and
every representation of code must run the whole corpus unchanged. That
turns a change of representation (roadmap.md task 4) into a differential
test, and each program the language cannot express yet names a missing
feature.

## 1. Scope

**Decided.**

In scope: tier 1, programs the current language (`semiroh/lang.py`) can
express; the data format; `play`, which runs an example with a given
interpreter; the list of wanted programs the language cannot express yet.

Out of scope: host-driven transformations (renames and other host edits
stay in the acceptance tests of the language); benchmarks; a standard
library.

## 2. Format

**Decided.**

Module `semiroh/examples/` (a package, so programs can be split across
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
                      "self-modification", "data", "higher order"})

    ExampleFailed(AssertionError)
    play(example, run)
        runs every scenario with the given `run` function and raises
        ExampleFailed, naming the example, scenario and step, at the
        first mismatch; a step expecting a value that raises instead is a
        mismatch too

`run` has the signature of `semiroh.lang.run`; another interpreter passes
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
  through `call`, through `apply` and between two functions;
- self-modification: `sort_swap`, which sorts a tuple in a cell with the
  function `order` refers to, activates a different `order` between two
  runs, and sorts again with the data still in its cell.

## 4. Wanted programs

**Open.** Recorded in `semiroh/examples/missing.py` (`MISSING`). Writing the
tier 2 programs found two gaps:

- `map_long_tuple` needs non-tail recursion deeper than the Python stack.
  Tail calls made loops unbounded, but a call not in tail position still
  nests about 5 Python frames. Under the default recursion limit of 1000
  the `map` example succeeds on a tuple of 190 elements and raises
  `RecursionError` on 200, and `insertion_sort` succeeds on 150 and raises
  on 200. It needs an evaluator whose stack is not the Python stack, or a
  primitive that walks a tuple without recursion.
- `make_adder` needs function values that capture local names, such as
  `make_adder(n)` or `compose(f, g)`. `ref` gives only the identity of a
  function that already exists and `apply` takes only such a reference; a
  function built by `function` is code as data and runs only after
  `activate` installs it under an existing entity. It needs anonymous
  function values with captured bindings, or partial application.

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
  `semiroh/lang.py`'s `_call`/`_eval`. Measured against the `sum_to_n`
  tier-1 example: under the interpreter's default recursion limit of 1000,
  `sum_to_n(197)` succeeds and `sum_to_n(198)` raises `RecursionError` —
  about 5 Python stack frames per SEMIROH call (measured on graph form;
  the tuple-body interpreter stopped one call earlier).

## 5. Acceptance tests

`tests/test_corpus.py` pins the format and the canary property: the corpus
must fail under deliberately broken interpreters (wrong integer results,
lost cell writes, an ignored activation grant, swallowed errors). The
implementation is done when it passes without changes.

## 6. Implementation notes

- Programs are data. Build them with `semiroh.lang` (`Function`, `links`)
  and core constructors only; host code appears only as evaluators in an
  example's `context`.
- Keep each program small and readable; one module per tag is fine.
- When done: add a `CHANGES.md` entry and mark this document's status.
