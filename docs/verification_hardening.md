# Verification hardening

**Status: implemented** (roadmap task 18, PR #42).

Task 18 strengthens the evidence that SEMIROH's semantics are correct before
task 19 changes the architecture. It is deliberately separate from that
refactor: this task changes tests, test infrastructure, documentation and CI,
not production semantics.

This document records the resulting verification architecture and policies.
One-off CI timings, workflow run IDs and campaign measurements are historical
evidence and belong in `CHANGES.md` and the PR record rather than in this
document.

## 1. Goals

Task 18 has four goals:

1. make cross-subsystem semantic failures harder to hide behind individually
   correct components;
2. discover counterexamples and missing invariants rather than merely increase
   the test count;
3. make generated failures reproducible and reducible into permanent
   regressions;
4. keep normal feedback practical while allowing substantially heavier
   verification campaigns when needed.

Task 19 can therefore change architecture against a stronger baseline without
mixing verification work into the refactor itself.

## 2. Verification layers

**Decided:**

SEMIROH uses several independent kinds of evidence rather than one universal
test framework:

- focused unit tests for local contracts;
- minimized deterministic regressions for discovered defects;
- corpus and whole-program acceptance tests;
- invariant and generated property tests;
- generated malformed and negative inputs;
- differential tests between independent implementations;
- metamorphic tests for semantics-preserving relationships;
- bounded exhaustive checks over small complete state spaces;
- deterministic stateful operation sequences;
- mutation testing that checks whether the rest of the suite notices planted
  implementation faults.

Coverage and raw test count are diagnostics, not correctness metrics.

## 3. Cross-boundary testing

**Decided:**

Subsystem seams are first-class verification targets.

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

Examples include:

    text
    → parse
    → graph
    → render
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

A subsystem agreeing with itself is weaker evidence than independent semantic
paths agreeing.

## 4. Differential testing

**Decided:**

Differential tests use independently implemented paths already present in the
project.

Where their domains overlap, the suite checks relationships including:

    host lowering == embedded compiler lowering
    host machine behaviour == SEMIROH VM behaviour
    graph execution before transform == graph execution after
        semantics-preserving transform
    trial behaviour == activation behaviour where specified

Failures are compared where relevant, not only successful return values.

Task 18 adds deterministic closure-heavy differential generation across host
execution and the embedded compiler/VM path. Cases exercise:

- direct closure calls;
- `applyv`;
- nested closures;
- closures capturing ordinary values;
- closures capturing other closures.

The generator stays within the common host/embedded-VM subset.

Generated cases identify their seed and can be replayed with:

    SEMIROH_SEED=<seed> \
        python -m unittest tests.test_closure_differential

Larger generated budgets belong to the manual/heavy verification tier.

## 5. Metamorphic testing

**Decided:**

Metamorphic tests check relationships whose expected result is known without a
separate reference interpreter.

Task 18 checks low-level transformation relationships including:

- independent value changes commute;
- batching independent changes agrees with applying them sequentially;
- repeating the same semantic change is idempotent.

It also checks language-level relationships that exercise substantially more of
SEMIROH:

- rendering an authoritative graph-form program and reconciling that rendered
  source back into the same program is a no-op;
- projecting a loaded function through `function_at` and defining that same
  function again is a no-op;
- rebasing two independent function definitions produces the same language
  projection and observable execution as defining both edits together.

The last relation deliberately does not require exact `StateID` equality.
Independent and batched edits may allocate graph nodes through different
histories even when their source projection and observable language semantics
agree. Metamorphic tests must assert the semantic contract, not accidental
allocation history.

Existing tests independently cover other metamorphic relationships such as
canonical mapping order, matching order independence, folding twice,
render/reparse and trial/activation agreement.

Generated metamorphic cases use the common deterministic replay mechanism.

## 6. Negative and malformed generation

**Decided:**

Generated verification includes invalid inputs rather than constructing only
valid programs.

Task 18 generates malformed language cases including:

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

Each malformed case is loaded into graph form and collapsed back to input form.
The malformed body must survive that round trip rather than being normalized
away.

Execution must then fail with `LanguageError`, not a leaked host exception.

These tests do not impose transactional rollback on arbitrary language errors.
Effects that occur before a later error remain governed by the language's
normal effect-ordering semantics. Atomicity is asserted separately only for
operations whose contracts promise it, such as rejected writes and rejected
activations.

Replay is:

    SEMIROH_SEED=<seed> \
        python -m unittest tests.test_malformed_generation

Existing targeted tests continue to cover malformed semantic records,
ownership, mappings, links, relations and other subsystem-specific invalid
states.

## 7. Stateful semantic simulation

**Decided:**

Task 18 adds deterministic generated operation sequences over a live runtime.

Operations include:

    write
    rejected write
    enter frame / hold
    keep reference
    release hold
    trial
    activate

These deliberately cross state, runtime-cell, transformation, reference and
version-lifecycle boundaries.

After every generated operation the harness checks global invariants including:

- the runtime owns an active version;
- at most two main runtime versions are loaded;
- the active version is not retired;
- the `previous` view agrees with version ownership;
- recorded holds are live and belong to exactly one version;
- runtime cell content belongs only to declared cells;
- runtime cell content satisfies its constraint;
- the harness's live hold handles agree with runtime hold records;
- rejected writes and rejected activations are atomic;
- trials leave the main runtime unchanged.

Failures report the operation step and seed.

Replay is:

    SEMIROH_SEED=<seed> \
        python -m unittest tests.test_stateful_sequences

A failing sequence is passed through deterministic delta-debugging reduction
before it is reported.

The harness is intentionally extensible. Future semantic features can add
operations such as reconcile, explicit merge/split/disappearance and old/new
callable invocation without replacing the framework.

## 8. Bounded exhaustive testing

**Decided:**

Small semantic domains are checked exhaustively where practical.

Task 18 exhaustively checks continuity composition over a two-entity universe.

For each source entity, each relation can independently be:

- absent;
- known disappearance;
- mapped to the first entity;
- mapped to the second entity;
- split to both entities.

This produces a complete finite set of two-step relation compositions.

The implementation is compared against a small independent relational oracle
that distinguishes:

    absent
    known continuation/disappearance
    unknown continuity

This complements generated testing by completely covering a small semantic
domain rather than sampling it.

## 9. Failure reproduction and reduction

**Decided:**

Generated failures must be reproducible and reducible before being promoted to
permanent regressions.

`tests/generation.py` provides shared infrastructure.

`SEMIROH_SEED` accepts one integer or a comma-separated list:

    SEMIROH_SEED=37 \
        python -m unittest tests.test_stateful_sequences

or:

    SEMIROH_SEED=7,11,19 \
        python -m unittest tests.test_metamorphic

`SEMIROH_CASES` changes the deterministic generated-case budget:

    SEMIROH_CASES=1000 \
        python -m tests.lanes cross-boundary

Unset, empty, or `0` means that each test uses its ordinary default budget.

An explicit replay seed takes precedence over the case budget.

The shared helper also implements deterministic sequence delta-debugging. It
repeatedly removes chunks while the supplied failure predicate still fails,
producing a smaller sequence suitable for diagnosis.

Every real defect discovered by generated verification should become a small,
ordinary deterministic regression. A seed may remain as provenance, but the
regression should not depend on rediscovery.

## 10. Mutation testing

**Decided:**

Mutation testing covers the semantic implementation broadly enough that new
model modules cannot silently disappear from the campaign.

Before Task 18 the mutation campaign targeted eight implementation files.
Task 18 expands this to 22 targets, including the independent embedded compiler
and SEMIROH VM.

`tests/mutation_catalog.py` is the explicit inventory.

Every top-level production Python module and every example module must either:

- be a mutation target; or
- appear in `OMITTED` with a written reason.

Ordinary tests enforce this accounting.

The mutation engine uses Python's standard `ast` module to mutate the Python
reference implementation. That AST is test-tool implementation machinery only;
it is not a SEMIROH program representation or compiler IR.

Before planting mutants, a campaign runs the exact mutation test command
against an unmodified repository copy made with the same copy and environment
rules used for mutant execution. A failing baseline aborts the campaign rather
than allowing unrelated infrastructure failures to count as killed mutants.

### Survivor identity

A reviewed survivor is keyed by:

    target file
    mutation kind
    complete stripped source line
    occurrence among sites with the same kind and source line

The occurrence distinguishes multiple mutable constructs represented by the
same line, including nested constructs.

Global mutation-site index and source line number are deliberately excluded
from persistent identity. Therefore inserting unrelated code elsewhere in a
file does not invalidate reviewed survivor classifications.

Catalog tests require each survivor key to identify exactly one current
mutation site. If the relevant source expression itself changes, the key no
longer resolves and the catalog fails closed.

### Survivor classification

The useful historical survivor knowledge from the earlier mutation campaign
was migrated to exact current keys where the reason remained defensible.

Historical entries are not copied blindly:

- semantically equivalent mutations are classified `equivalent`;
- behaviour deliberately outside the semantic contract may be classified
  `unspecified`;
- a known semantic test gap is never classified as a permitted survivor;
- an old entry that cannot be mapped confidently to one current mutation site
  remains unclassified until a campaign rediscovers an exact survivor.

In particular, the historical `Function` equality survivor was documented as
an open test gap, not an equivalence, so it is not whitelisted.

Generation-allocation mutations are likewise not whitelisted: graph-form
generation numbers are part of node identity, so changing initial generation,
next-generation allocation or collision advancement changes specified semantic
identity and must be killed by regression tests.

Every survivor classification carries a written reason.

A new unclassified survivor therefore means one of three things must happen:

1. prove it equivalent and record the reason;
2. establish that the changed behaviour is intentionally unspecified and
   record the reason;
3. treat it as a test gap, add a regression, and kill the mutant.

A test gap is never resolved by adding it to the survivor catalog.

Mutation operators remain intentionally simple. New operators should be added
when a concrete missing fault class justifies them rather than to increase a
nominal mutation score.

## 11. Practices borrowed

Established verification practices are used selectively rather than treating
another project's test architecture as a template.

Relevant influences include:

- LLVM – separation of focused regressions and whole-program suites;
- Rust – first-class negative testing;
- Csmith – valid-program differential generation;
- EMI – equivalence-modulo-inputs compiler testing;
- Alive2 – validating transformations against semantic contracts;
- SQLite – independent harnesses, malformed inputs and boundary testing;
- Hypothesis/QuickCheck-style systems – generation, state machines and
  shrinking;
- deterministic simulation used in complex stateful systems – long,
  reproducible operation sequences with invariant checking.

SEMIROH's own graph identity and continuity rules take precedence over
assumptions from conventional languages.

## 12. CI structure

**Decided:**

The ordinary deterministic suite is explicitly partitioned by
`tests/lanes.py`.

The lanes are:

    core-model
    language-runtime
    transform-continuity
    syntax-reconcile
    compiler-self-hosting
    vm-bootstrap
    cross-boundary
    mutation

Every ordinary `test_*.py` module must belong to exactly one lane.

CI fails if a test module is:

- unassigned;
- assigned more than once; or
- still named by the configuration after its file disappears.

The partition is semantic rather than equal-size sharding so a failing lane
identifies a meaningful subsystem boundary.

The slower independent implementations are separated from the cheaper model
lanes.

Mutation testing controls its own process concurrency; ordinary lane
parallelism does not add another nested mutation-parallelism layer.

The workflow retains manual dispatch for heavier generated and mutation
campaigns.

## 13. Measurement policy

**Decided:**

Verification-performance measurements are evidence about a particular run, not
part of the permanent verification specification.

For Task 18:

- compare the pre-change serial workflow with a representative split workflow;
- distinguish Python test-execution time from hosted-runner allocation and
  queue delay;
- record heavy generated and mutation campaign sizes and elapsed times;
- keep those concrete run IDs and measurements in `CHANGES.md` and the PR
  record.

The stable requirement is that ordinary feedback remains practical while the
heavier tier can spend substantially more compute.

Future changes may produce different timings without making this document
stale.

## 14. CI tiers

**Decided:**

Every ordinary push/PR run includes:

- the complete deterministic suite split into semantic lanes;
- cheap generated differential and cross-boundary cases;
- bounded exhaustive continuity composition;
- deterministic stateful/adversarial sequences;
- mutation engine and catalog validation.

The broad planted-mutant campaign is intentionally not part of every PR run.

Manual workflow dispatch exposes:

    generated_cases
    mutation_count
    mutation_seed

`generated_cases` raises participating generated-test budgets.

`mutation_count` selects how many mutants are sampled per mutation target.

`mutation_seed` makes the sample reproducible.

This separates ordinary feedback latency from campaigns that intentionally use
substantially more compute.

## 15. Implementation summary

**Implemented:**

Task 18 added:

- explicit semantic CI lanes with partition coverage guards;
- parallel matrix CI;
- generated closure-heavy host-versus-embedded-VM differential testing;
- generated malformed-language round-trip and rejection testing;
- generated low-level and language-level metamorphic testing;
- a deterministic stateful runtime sequence harness;
- bounded exhaustive continuity-composition verification;
- common seed replay, case-budget and sequence-reduction infrastructure;
- explicit mutation target accounting;
- stable exact survivor identities;
- mutation baseline preflight against an unmodified repository copy;
- graph-generation identity regressions for specified allocation semantics;
- migration of defensible historical survivor classifications;
- mutation coverage expanded from 8 to 22 implementation targets;
- manual heavy generated and mutation verification tiers;
- updated repository guidance for lanes, generated replay and mutation
  classification.

No production semantic behaviour is intentionally changed by Task 18.

## 16. Acceptance

**Satisfied in PR #42:**

- verification boundaries and their test methods are documented;
- every ordinary test module belongs to exactly one semantic CI lane;
- the ordinary suite runs in parallel semantic jobs;
- before/after timing evidence is recorded outside this stable specification;
- independent host/compiler/VM implementations have generated differential
  coverage where their domains overlap;
- malformed generation exercises graph-form collapse and specified runtime
  rejection without assuming generic rollback semantics;
- language-level metamorphic relations exercise render/reconcile,
  `function_at`/`define`, and independent rebased definitions;
- a deterministic stateful sequence harness checks global invariants after
  every operation;
- bounded exhaustive continuity composition covers a complete small domain;
- generated failures can be replayed by seed;
- failing stateful sequences can be reduced;
- mutation targets account for the semantic implementation explicitly;
- mutation campaigns validate an unmodified copy before planting mutants;
- survivor identities remain stable under unrelated edits elsewhere in a file;
- historical reviewed survivor knowledge is preserved where defensible;
- semantic test gaps cannot be whitelisted as accepted survivors;
- specified graph-generation identity changes are covered by regressions rather
  than survivor exemptions;
- manual generated and mutation campaign paths exist for heavier validation;
- real defects discovered by future generated campaigns have a defined path
  into minimized permanent regressions;
- no production semantic behaviour is intentionally changed.

Task 19 can therefore refactor architecture against this stronger verification
baseline.
