# Verification hardening

**Status: implemented** (roadmap task 18, PR #42).

Task 18 strengthens the evidence that SEMIROH's semantics are correct before
task 19 changes the architecture. It is deliberately separate from the
refactor: this task changes tests, test infrastructure and CI, not production
semantics.

The suite was already broad and contained property, differential, negative,
atomicity, continuity and mutation tests. The problem was uneven strength
rather than absence of serious testing. In particular, interactions across
subsystem boundaries, malformed generated inputs, long stateful sequences and
newer features had less systematic coverage.

Task 18 adds those missing verification layers, makes generated failures
replayable and reducible, broadens mutation testing, and partitions ordinary CI
into semantic lanes.

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

The suite contains:

- small unit tests for local contracts;
- minimized regression tests for discovered bugs;
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

Tests deliberately cross several boundaries in one case when that is where the
semantic contract lives.

Examples already exercised by the suite include:

    text
    → parse
    → graph
    → render
    → parse
    → reconcile

and:

    input form
    → graph form
    → collapse
    → execute malformed code
    → LanguageError

and:

    graph
    → embedded compiler
    → bytecode
    → SEMIROH VM
    ↕
    host execution

and:

    transform
    → trial / activate
    → runtime cell transfer
    → holds and version lifecycle

A subsystem agreeing with itself is weaker evidence than two independently
implemented paths agreeing.

## 4. Differential testing

**Decided:**

Differential tests use independent implementations already present in the
project.

The suite checks, where their domains overlap:

    host lowering == embedded compiler lowering
    host machine behaviour == SEMIROH VM behaviour
    graph execution before transform == graph execution after
        semantics-preserving transform
    trial behaviour == activation behaviour where specified

Comparison includes failures where relevant, not only successful return values.

Task 18 specifically adds generated closure-heavy host/VM differential testing.
Sixty deterministic generated closure programs are each run with two arguments.
The generator exercises direct closure calls, `applyv`, nested closures and
closures capturing other closures. It uses a cached base semantic graph so the
test remains practical in ordinary CI.

Each generated case identifies its seed, and a single failure can be replayed
with:

    SEMIROH_SEED=<seed> \
        python -m unittest tests.test_closure_differential

The generator deliberately stays within the common host/embedded-VM subset.

## 5. Metamorphic testing

**Decided:**

Metamorphic tests check relationships whose expected result is known without a
separate reference interpreter.

Existing tests already cover several such properties, including canonical
mapping order, matching order independence, folding twice, syntax
render/reparse, graph load/collapse and trial/activation agreement.

Task 18 adds generated transformation metamorphisms over independent changes:

- applying independent changes in either order gives the same state;
- batching independent changes agrees with applying them sequentially;
- repeating the same semantic change is idempotent.

The generated cases are deterministic and use the same replay/budget mechanism
as the other Task 18 generators.

The transformations are limited to relations justified by SEMIROH's actual
identity and continuity rules; conventional-language equivalences are not
assumed automatically.

## 6. Negative and malformed generation

**Decided:**

Generated testing includes invalid inputs rather than constructing only valid
programs.

Task 18 adds deterministic malformed-language generation covering families
including:

- unknown operations;
- wrong arity;
- malformed `let` names;
- wrong arithmetic and condition operand kinds;
- malformed tuple operations;
- non-callable values;
- malformed closure parameter/capture containers;
- malformed closure names;
- duplicate closure names;
- overlapping parameter/capture names;
- missing declared captures.

The ordinary budget is 120 seeds.

Each case is first loaded into graph form and collapsed back to input form. The
test requires the malformed body to survive that round trip unchanged rather
than being normalized away. Execution must then fail with `LanguageError`, not
with a leaked host exception.

The runtime state identity is checked before and after the rejected execution,
so rejection alone is not treated as sufficient evidence of atomicity.

A case can be replayed with:

    SEMIROH_SEED=<seed> \
        python -m unittest tests.test_malformed_generation

Existing targeted tests continue to cover malformed semantic records,
ownership, mappings, links, relations and other subsystem-specific invalid
states.

## 7. Stateful semantic simulation

**Decided:**

Task 18 adds deterministic generated operation sequences over a live runtime.

The ordinary campaign runs 120 seeds, each producing 40 operations drawn from:

    write
    rejected write
    enter frame / hold
    keep reference
    release hold
    trial
    activate

These operations deliberately cross state, runtime cell, transformation,
reference and version-lifecycle boundaries.

After every generated operation the harness checks global invariants including:

- the runtime owns an active version;
- the active version is the first loaded version;
- at most two main runtime versions are loaded;
- the active version is not retired;
- the `previous` view agrees with version ownership;
- recorded holds are live and belong to exactly one version;
- runtime cell content belongs only to declared cells;
- runtime cell content satisfies its constraint;
- the harness's live hold handles agree with runtime hold records;
- rejected writes and rejected activations are atomic;
- trials leave the main runtime unchanged.

A failure prints the step, operation and seed.

Replay is:

    SEMIROH_SEED=<seed> \
        python -m unittest tests.test_stateful_sequences

The failing operation sequence is also passed through deterministic
delta-debugging reduction before it is reported.

The harness is intentionally extensible. Later semantic features can add
operations such as reconcile, explicit merge/split/disappearance and
old/new callable invocation without replacing the framework.

## 8. Bounded exhaustive testing

**Decided:**

For small domains, exhaustive enumeration complements random generation.

Task 18 exhaustively checks continuity composition over a two-entity universe.

For each source entity, the first and second relation can independently be:

- absent;
- known disappearance;
- mapped to the first entity;
- mapped to the second entity;
- split to both entities.

That gives 25 complete relation definitions and therefore:

    25 × 25 = 625

two-step compositions.

Both source entities are checked for every composition, giving 1,250
source-level observations.

The implementation is compared against a small independent relational oracle
that distinguishes:

    absent
    known continuation/disappearance
    unknown continuity

This completely covers the tiny domain rather than relying on sampling.

## 9. Failure reproduction and reduction

**Decided:**

Generated failures must be reproducible and reducible before being promoted to
permanent regressions.

`tests/generation.py` provides the common infrastructure.

`SEMIROH_SEED` accepts either one integer or a comma-separated list:

    SEMIROH_SEED=37 python -m unittest tests.test_stateful_sequences

or:

    SEMIROH_SEED=7,11,19 python -m unittest tests.test_metamorphic

`SEMIROH_CASES` changes the deterministic generated-case budget while keeping
the seed sequence anchored at zero:

    SEMIROH_CASES=1000 python -m tests.lanes cross-boundary

An explicit replay seed takes precedence over the case budget.

The helper also provides deterministic sequence delta-debugging. It repeatedly
removes chunks while the supplied failure predicate still fails, producing a
smaller sequence suitable for diagnosis and eventual promotion to a permanent
regression.

The reduction machinery itself has unit tests.

Every real defect discovered by generated testing should become a small,
ordinary deterministic regression test. The original seed may be retained as
provenance, but the regression should not depend on rediscovery.

## 10. Mutation testing

**Decided:**

Mutation testing now covers the semantic implementation substantially more
broadly.

Before Task 18 the campaign targeted eight files:

    semiroh/bytecode.py
    semiroh/lang.py
    semiroh/matching.py
    semiroh/runtime.py
    semiroh/transforms.py
    semiroh/examples/self_hosting.py
    semiroh/fold.py
    semiroh/examples/vm.py

Task 18 expands this to 22 implementation targets, including:

    canonical
    cells
    closures
    constraints
    continuity
    equality
    machine
    ownership
    reconcile
    references
    relations
    state
    syntax
    values

as well as the previous targets and the independent embedded compiler/VM.

`tests/mutation_catalog.py` is the explicit inventory. Every top-level
production Python module and every example module must either be a mutation
target or have a written reason for omission. Tests enforce that accounting so
new semantic modules cannot silently escape the campaign.

Known surviving mutants are classified explicitly as either:

1. `equivalent`, with a written reason; or
2. `unspecified`, where the changed behaviour is outside the semantic
   contract.

A test gap is deliberately not a permitted survivor classification. A semantic
gap receives a regression test and the mutant must then be killed.

The manual validation campaign on 30 September 2026 used:

    SEMIROH_MUTATE=1
    SEMIROH_MUTATE_SEED=1

across all 22 targets. It completed successfully with no unclassified
survivors. The mutation lane took 186.067 seconds, confirming that broad
mutation belongs in the heavy/manual tier rather than ordinary PR latency.

Mutation operators remain intentionally simple. New operators should be added
when a concrete missing fault class justifies them rather than to increase a
nominal mutation score.

## 11. Practices borrowed

**Decided:**

Established practices are used selectively rather than treating any one
project's test architecture as a template.

Relevant influences are:

- LLVM – separation of focused regression tests and whole-program suites;
- Rust – first-class negative testing;
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

The ordinary suite is explicitly partitioned by `tests/lanes.py`.

The lanes are:

    core-model
    language-runtime
    transform-continuity
    syntax-reconcile
    compiler-self-hosting
    vm-bootstrap
    cross-boundary
    mutation

Every `test_*.py` module must belong to exactly one lane. CI fails if a test
module is unassigned, assigned twice, or named by the configuration after the
file disappears.

The partition is semantic rather than equal-size sharding. This makes failures
localize to a meaningful subsystem.

The two slow lanes are intentionally separate:

- `compiler-self-hosting` contains the independent compiler and generated
  closure differential tests;
- `vm-bootstrap` contains embedded VM/bootstrap verification.

The remaining lanes are substantially cheaper.

Mutation testing controls its own internal process concurrency; ordinary CI
does not add another nested mutation-parallelism layer.

The workflow preserves path filtering and manual dispatch support and uses
current Node-24-compatible `actions/checkout@v7` and
`actions/setup-python@v7`.

## 13. CI timing

**Measured:**

The pre-Task-18 baseline is GitHub Actions run `36672073336`, immediately
before the Task 18 branch.

It used one serial test job:

    831 tests
    Python unittest time: 21.464 s
    workflow wall time:   36 s

Task 18 adds generated differential, malformed, metamorphic, bounded-exhaustive,
stateful, lane-infrastructure and mutation-catalog tests, so the post-change
suite is strictly stronger rather than an equal-work benchmark.

A representative split run without significant hosted-runner queueing is
`36679502020`:

    workflow wall time: 25 s

The slowest lanes are the compiler/self-hosting and VM/bootstrap lanes. On
later run `36682239622` their measured Python execution times were:

    compiler-self-hosting: 17.479 s
    vm-bootstrap:          12.623 s

So the deterministic test-execution critical path is below the old 21.464 s
serial suite even after adding the Task 18 verification layers.

GitHub-hosted runner allocation adds external variance. For example, later
ordinary runs took 47–60 seconds end-to-end when one matrix job waited tens of
seconds before receiving a runner. That queue time is not test execution and
is therefore recorded separately rather than hidden.

The relevant conclusion is:

- deterministic execution critical path decreased;
- a no-queue workflow sample improved from 36 s to 25 s;
- hosted-runner queueing can dominate end-to-end latency independently of the
  suite partition.

## 14. CI tiers

**Decided:**

Every push/PR runs:

- the complete ordinary deterministic suite, split into parallel semantic
  lanes;
- cheap generated differential/cross-boundary tests;
- bounded exhaustive continuity composition;
- deterministic stateful/adversarial sequences;
- mutation engine/catalog checks.

The expensive planted-mutant campaign does not run automatically on every PR.

Manual workflow dispatch exposes:

    generated_cases
    mutation_count
    mutation_seed

`generated_cases` raises the deterministic budget of participating generated
families.

`mutation_count` enables the broad mutation campaign and selects the number of
mutants sampled per target.

`mutation_seed` makes that sample reproducible.

This separates normal feedback latency from campaigns that intentionally spend
substantially more compute.

## 15. Implementation summary

**Implemented:**

Task 18 added:

- explicit semantic CI lane partitioning with coverage guards;
- parallel matrix CI;
- current GitHub action versions and restored path/manual triggers;
- generated closure-heavy host-versus-embedded-VM differential tests;
- generated malformed-language rejection and atomicity tests;
- generated metamorphic transformation tests;
- a deterministic stateful runtime sequence harness;
- bounded exhaustive continuity-composition verification;
- common seed replay, case-budget and sequence-reduction infrastructure;
- mutation target accounting and survivor classification;
- mutation coverage expanded from 8 to 22 implementation targets;
- a manual heavy verification tier.

No production semantic behaviour was intentionally changed.

## 16. Acceptance

**Satisfied in PR #42:**

- verification boundaries and their test methods are documented;
- the ordinary suite is split into meaningful parallel CI jobs;
- before/after ordinary-suite timing is recorded;
- independent host/compiler/VM implementations have generated differential
  coverage where their domains overlap;
- malformed generation exercises graph-form and runtime semantic boundaries;
- a deterministic stateful sequence harness checks global invariants after
  every operation;
- bounded exhaustive continuity composition covers a complete small semantic
  domain;
- mutation targets cover the semantic implementation substantially more
  completely and surviving mutants require explicit classification;
- generated failures can be replayed by seed and stateful sequences can be
  reduced;
- real defects discovered by future generated campaigns have a defined path
  into minimized permanent regressions;
- no production semantic behaviour was intentionally changed.

Task 19 can therefore refactor architecture against this stronger verification
baseline.
