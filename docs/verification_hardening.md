# Verification hardening

**Status: planned** (roadmap task 18).

Task 18 strengthens the evidence that SEMIROH's semantics are correct before
task 19 changes the architecture. It is deliberately separate from the
refactor: this task should change tests, test infrastructure and CI, not
production semantics except for minimal testability hooks where unavoidable.

The current suite is broad and already contains property, differential,
negative, atomicity, continuity and mutation tests. The problem is uneven
strength rather than absence of serious testing. In particular, interactions
across subsystem boundaries, malformed generated inputs, long stateful
sequences and newer features have less systematic coverage.

The ordinary suite currently takes roughly 27–40 seconds in normal development,
so test execution itself also needs structure before substantially heavier
verification is added.

## 1. Goals

**Decided:**

The task has four goals:

1. make important semantic failures harder to hide behind individually correct
   subsystems;
2. discover missing counterexamples and invariants rather than merely increase
   the test count;
3. make generated failures reproducible and reducible to permanent regression
   cases;
4. split and parallelize the test run so stronger verification does not make
   normal development unnecessarily slow.

Task 19, architecture hardening/refactoring, follows this task and is separate.

## 2. Verification layers

**Decided:**

Keep several independent kinds of evidence rather than one universal test
framework.

The suite should contain:

- small unit tests for local contracts;
- minimized regression tests for every discovered bug;
- corpus/whole-program acceptance tests;
- invariant and property tests;
- negative tests generated specifically to violate preconditions;
- differential tests between independent implementations;
- metamorphic tests where semantics-preserving input changes must preserve
  observable behaviour;
- bounded exhaustive tests over small state spaces;
- stateful sequence tests over runtime and transformation operations;
- mutation testing that checks whether the rest of the suite notices planted
  implementation faults.

Coverage and raw test count are diagnostics, not correctness metrics.

## 3. Cross-boundary testing

**Decided:**

Testing subsystem seams is a primary goal.

Important paths include:

    text
      ↕
    input form
      ↕
    semantic graph
      ↕
    bytecode
      ↕
    host machine

and the independent paths:

    semantic graph → embedded compiler → bytecode
    bytecode       → SEMIROH VM

as well as:

    edited text → parse → reconcile → continuity → activation
    transform   → mapping → reference transfer → runtime cells
    activation  → code in flight → version holds → closures

Tests should deliberately cross several boundaries in one case when that is
where the semantic contract lives.

Examples include:

    text
    → parse
    → graph
    → render
    → parse
    → reconcile
    → lower
    → execute
    → compare with the independent execution path

and:

    transform
    → activate
    → transfer runtime content and references
    → execute old and new callable values
    → verify holds, identity and observable behaviour

A subsystem agreeing with itself is weaker evidence than two independently
implemented paths agreeing.

## 4. Differential testing

**Decided:**

Expand existing differential tests around the independent implementations
already present in the project.

Where their domains overlap, generated programs should compare:

    host lowering == embedded compiler lowering
    host machine behaviour == SEMIROH VM behaviour
    graph execution before transform == graph execution after
        semantics-preserving transform
    trial behaviour == activation behaviour where the specification says
        they coincide

Comparison includes failures where relevant, not only successful return values.

The generator must avoid declaring disagreement when the two paths
intentionally have different supported subsets.

## 5. Metamorphic testing

**Decided:**

Add transformations whose expected relationship is known without needing a
separate reference interpreter.

Candidate relations include:

- rebuilding mappings or dictionaries in another insertion order;
- adding or removing semantically irrelevant structure where the language
  permits it;
- alpha-like renaming where identity semantics permit it;
- applying independent transformations in either order;
- folding twice;
- rendering and reparsing a renderable program;
- loading and collapsing graph form;
- changing unreachable or observationally irrelevant code in carefully
  delimited cases.

The exact transformations must be justified by the SEMIROH specification.
Tests must not silently assume conventional-language equivalences that are
false under SEMIROH identity or continuity semantics.

## 6. Negative and malformed generation

**Decided:**

Generated testing must include invalid inputs rather than constructing only
valid programs.

For operation forms this includes, as applicable:

- too few and too many operands;
- wrong operand kinds;
- malformed names;
- duplicate names;
- unknown links;
- dangling entities;
- malformed semantic records;
- invalid nested forms;
- invalid ownership;
- inconsistent transformation mappings;
- invalid closure owner/body/capture combinations.

For every rejection that promises atomicity, the test also checks that all
relevant state remains unchanged.

An exception alone is not sufficient evidence of a correct rejected operation.

## 7. Stateful semantic simulation

**Decided:**

Add deterministic generated sequences of operations, with every sequence
identified by a reproducible seed.

Operations should eventually include appropriate combinations of:

    run
    read/write
    create callable values
    edit
    define
    transform
    trial
    activate
    hold/release
    reconcile
    rebase
    rename
    merge/split/disappear
    call old and new references/closures
    deliberately fail an operation

After every step, check global invariants rather than only the final result.

Important invariants include:

- relation endpoints exist;
- ownership is valid and acyclic;
- an entity has at most one owner;
- transformation mappings name valid sources and destinations;
- disappearance and continuation records agree with state presence;
- runtime cell content satisfies its required constraints;
- rejected atomic operations leave the runtime unchanged;
- holds correspond to live versions;
- semantic identity remains deterministic.

Failures must print enough information to reproduce the sequence from its seed.

## 8. Bounded exhaustive testing

**Decided:**

For small domains, exhaustive enumeration complements random generation.

Useful candidates are tiny expression trees, tiny ownership graphs, small
continuity mappings and short transformation compositions.

The purpose is complete coverage of small combinatorial corners that random
sampling can repeatedly miss.

Bounds must remain small enough for deterministic CI execution.

## 9. Failure reduction

**Decided:**

Generated failures should be minimized before becoming permanent tests.

Prefer a framework with shrinking where it fits. If a custom generator is
kept, provide structural reduction for the important generated objects and
operation sequences.

Every real discovered defect becomes a small deterministic regression test.
The random seed may remain as provenance, but the regression test should not
depend on rediscovering the original large case.

## 10. Mutation testing

**Decided:**

Expand mutation testing beyond its current production targets.

Semantic modules should either be mutation targets or have an explicit reason
why mutation testing is not useful for them. In particular, newer boundaries
such as the machine, syntax, closures and continuity should not be omitted
accidentally.

Mutation operators should also grow beyond simple arithmetic/comparison/
constant changes where experience shows useful missing fault classes.

A surviving mutant is classified as one of:

1. genuinely equivalent, with a written reason;
2. intentionally unspecified behaviour;
3. a test gap, which receives a regression test.

The goal is not a nominal 100% mutation score. Equivalent and irrelevant
mutants should not cause tests to encode meaningless implementation details.

## 11. Practices to borrow

**Provisional:**

Use established practices selectively rather than cargo-culting one project's
test architecture.

Relevant sources of techniques include:

- LLVM – separation of focused regression tests and whole-program suites;
- Rust – first-class negative/UI testing;
- Csmith – valid-program differential generation;
- EMI – equivalence-modulo-inputs compiler testing;
- Alive2 – validating transformations against semantic contracts;
- SQLite – independent harnesses, malformed inputs and boundary testing;
- Hypothesis/QuickCheck-style systems – generation, state machines and
  shrinking;
- deterministic simulation used in complex stateful systems – long,
  reproducible operation sequences with invariant checking.

SEMIROH's graph identity and continuity rules take precedence over assumptions
from conventional languages.

## 12. CI structure

**Decided:**

Split the ordinary suite into semantically meaningful jobs and run independent
jobs in parallel.

Initial lanes should be approximately:

    core-model
    language-runtime
    transform-continuity
    syntax-reconcile
    compiler-self-hosting
    vm-bootstrap
    cross-boundary

The exact file assignment is determined from measured runtime and dependency
boundaries during the task.

Prefer semantic partitioning over arbitrary equal-size sharding because it
gives useful failure localization. If one semantic lane remains substantially
slower than the others, shard that lane internally.

Do not create nested uncontrolled parallelism. In particular, mutation testing
already launches test processes and should control concurrency at one level.

Measure wall-clock time before and after the split. The purpose of
parallelization is lower development/PR latency while preserving deterministic
results, not merely more simultaneous processes.

## 13. CI tiers

**Decided:**

Use different budgets for different feedback loops.

Every PR runs:

- the complete ordinary deterministic suite, split into parallel lanes;
- cheap deterministic differential/cross-boundary properties;
- bounded small exhaustive cases;
- a small deterministic stateful/adversarial budget;
- a small deterministic mutation sample where runtime permits.

Larger scheduled or manually triggered verification runs:

- substantially larger stateful/random campaigns;
- broader bounded exploration where feasible;
- broad mutation sweeps;
- multiple random seeds or larger generated-program populations.

A failure in a heavy run must be reproducible locally from recorded inputs or
a seed.

## 14. Acceptance

**Decided:**

Task 18 is done when:

- the verification boundaries and their test methods are documented;
- the ordinary suite is split into meaningful parallel CI jobs;
- before/after ordinary-suite wall time is recorded;
- important independent implementations have differential coverage over
  generated cases where their domains overlap;
- malformed generation exercises important semantic boundaries;
- a deterministic stateful sequence harness checks global invariants;
- at least one bounded-exhaustive test family covers a small semantic domain;
- mutation targets cover the semantic implementation substantially more
  completely, with survivors classified;
- generated failures can be reproduced and reduced;
- discovered real defects are preserved as minimized regression tests;
- no production semantic behaviour is intentionally changed.

Task 19 may then refactor architecture against this stronger verification
baseline.
