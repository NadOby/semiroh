# Canary Corpus

**Status: planned.** `semiroh/examples/` does not exist yet; the acceptance
tests in `tests/test_corpus.py` fail until it does.

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
        order against one fresh `Runtime(program, context)`

    Wanted(name, needs)
        a program the language cannot express yet, and the feature it
        needs

    EXAMPLES: tuple[Example, ...]
    MISSING: tuple[Wanted, ...]
    TAGS = frozenset({"recursion", "side effects", "control",
                      "self-modification"})

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

## 4. Wanted programs

**Open.** The list is the input for roadmap.md task 6. Expected entries
include insertion sort, map and fold (taking tuples apart; applying a
function value), local variables, and a loop too deep for recursion in the
reference interpreter. Each entry says which feature it needs.

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
