# Bootstrap delivery review

**Provisional:**

Contribution dated 2026-10-06, initially reviewed against `main` at `aedc0f9`
and revised after clarifying the intended bootstrap path.

The objective is a working bootstrapped language with acceptable performance,
usable by human and AI programmers, while preserving SHEAR's distinctive
capabilities.

The intended path is to bootstrap SHEAR from the Python implementation.
Python serves as the executable semantic reference and the initial bootstrap
environment. This proposal does not prescribe an intermediate rewrite in
another implementation language.

This is development guidance, not an adopted semantic specification or a
replacement roadmap. Proposed additions and changes remain distinct from
existing commitments.

## 1. Adversarial assessment

Two separate review passes challenged the original discussion: one prioritized
delivery and performance; the other prioritized semantic continuity and design
integrity. Their agreement is an architectural judgement, not independent
experimental evidence. No new runtime or performance results are claimed here.

| Earlier conclusion | Assessment after review |
| --- | --- |
| The basic idea is sound | Coherent enough to implement and test; practical scalability and usability remain unestablished. |
| Graph representation requires graph-expanded data or universal graph rewriting | Incorrect: opaque representations and ordinary computation are already explicit design choices. |
| Continuity, preservation, evidence, and authority need separating | Already distinguished in the specifications; implementations must preserve those distinctions. |
| Add phased review, regression corpora, decision records, and layered verification | Mostly existing practice. Extend the workflow only for a demonstrated gap. |
| Development has become more rigorous | More verification mechanisms are documented. Reduced defect rates or faster delivery were not measured. |
| Comprehensive tooling should come first | Practical commands, inspection, and diagnostics should accompany implementation; complete IDE tooling need not precede bootstrap. |
| Port a vertical slice into another implementation | Premature as a default recommendation. First establish the bootstrap path through Python and SHEAR; replace execution machinery when concrete requirements justify it. |
| Self-hosting will improve performance | Not by itself. Performance depends on the execution engine, generated artifacts, representations, and algorithms. |
| Architectural simplification should drive development | Useful when it removes a concrete cost or obstacle. It must remain connected to delivering the language. |

Two risks remain in tension:

- Improving the reference model indefinitely without completing a usable
  bootstrap.
- Producing a conventional compiler that drops the semantic graph, embedded
  compiler, or live-evolution capabilities to reach an easier milestone.

The delivery plan must address both.

Sources: [project guidance](../../CLAUDE.md),
[semantic graph](../semantic_graph.md),
[relations](../relation_model.md),
[constraints](../constraint_model.md),
[contracts](../contract_model.md), and
[graph ledger](../graph_ledger.md).

## 2. Starting point

The Python implementation is an executable semantic reference model and the
intended starting environment for bootstrap.

[Self-hosting](../self_hosting.md) establishes subset lowering written in
SHEAR and comparison with host-generated output.
The [VM in SHEAR](../vm_in_shear.md) executes that output and supports a
compiler fixpoint. The Python-hosted machine still executes the system;
the embedded interpreter is intentionally slow and supports a restricted
subset.

Task 20 adds SHEAR error handling on the host-machine execution path.
Support for `catch` and `raise` in the embedded compiler and VM remains an
explicit follow-up.

These milestones establish useful executable evidence. They do not yet
establish a complete compiler pipeline, acceptable performance, or removal
of Python runtime dependencies.

The next architectural clarification is the exact boundary of the intended
bootstrap milestone: which components SHEAR must build and execute itself,
and which services may remain supplied by Python.

## 3. What bootstrapping from Python means

Distinguish compiler generations from the runtime executing them.

| Stage | Meaning | Evidence required |
| --- | --- | --- |
| Python seed | The Python implementation loads and executes the compiler written in SHEAR. | The compiler runs on declared inputs and its dependencies are known. |
| Compiler self-rebuild | The SHEAR compiler produces an executable representation of its own required components. That representation performs the next rebuild. | Successive compiler generations actually execute and produce the required artifacts. |
| Useful hosted bootstrap | The rebuilt compiler handles the declared language subset, representative programs, and the selected evolution scenario while using explicitly permitted Python services. | Reproducible build/run path, semantic checks, and development-appropriate time and memory costs. |
| Implementation without Python at runtime | Required execution and runtime services no longer depend on Python. Python may remain the seed and reference oracle. | The resulting system runs under its declared platform dependencies without invoking Python. |

These are distinct milestones. A hosted bootstrap is meaningful even when
Python still provides execution or runtime services. It must not be described
as Python-independent.

Conversely, removing Python does not require rewriting operating-system
services, an external backend, or every platform primitive in SHEAR.
The permitted external boundary must be explicit.

Successive compiler generations should normally execute on the same declared
runtime rather than adding another interpreter layer on every rebuild.
A fixed interpreted path can be useful initially; an increasing interpretation
depth is not a sustainable bootstrap strategy.

The current interpreted compiler fixpoint remains valuable evidence.
A practical bootstrap must additionally show that the produced compiler
artifact, rather than an unnoticed fallback to the seed compiler, performs
the next compilation.

## 4. Preserve the project idea through executable acceptance

Use the existing specifications as authority. The following are acceptance
anchors, not a new immutable constitution:

- The semantic graph remains canonical. Source and executable forms are
  representations or derived products, not competing authorities.
- Program images retain their semantic program and the compiler/transformation
  machinery needed to regenerate execution.
- Immutable semantic state, runtime mutation, entity identity, value equality,
  ownership, and declared continuity retain their specified distinctions.
- Producing a candidate transformation remains distinct from activating it.
- Continuity alone does not establish behavioral preservation; descriptions
  do not grant authority.
- Opaque values, external resources, and efficient derived representations
  remain possible.
- Lifetime and retirement follow declared rules rather than depending
  accidentally on Python object reachability.

Do not freeze Python containers, current bytecode shape, cache layout,
the provisional version limit, or unfinished lifetime mechanisms as part of
these commitments.

Host garbage collection can support the seed implementation. It does not
establish that the eventual lifetime design has been implemented.

A necessary semantic change must name the affected rule, the motivating
program, and the consequences. Update specifications and acceptance evidence
explicitly rather than silently changing expected outputs.

SHEAR supplies a substrate and language. Learning, autonomous improvement,
fixed objectives, and application-governance mechanisms are not bootstrap
requirements unless a concrete program independently needs them.

## 5. Bootstrap dependency inventory

Before expanding implementation scope, inventory the services used by the
compiler workload.

| Area | Questions to answer |
| --- | --- |
| Input | Is the compiler consuming text, serialized semantic state, or another explicit representation? Who parses or loads it? |
| Semantic construction | Who creates entities, resolves names, validates structures, and constructs immutable states? |
| Identity | Who performs canonicalization, derives identities, and checks references? |
| Compilation | Which passes execute in SHEAR, and which still invoke Python implementations? |
| Execution | What executes emitted artifacts? Which validation and authority checks apply? |
| Data operations | Which collection, string, lookup, and graph operations are host services? |
| Runtime | Who manages cells, closures, holds, activation, migration, and retirement? |
| Platform | Which allocation, file, process, timing, and other external services are required? |

For each actual dependency, record:

- The operation and its contract.
- The current implementation.
- Whether it remains an allowed host service for the milestone.
- What must replace it if it blocks that milestone.
- The acceptance case covering the boundary.

Keep this inventory in the existing bootstrap plan; do not create another
general tracking system.

The bootstrap subset must be closed over the actual compiler workload and its
declared dependencies. This does not require supporting every planned language
feature before bootstrap.

Use the compiler's real algorithms to expose missing data capabilities.
Do not introduce a complete systems-data model merely because compilers
eventually need efficient storage. Equally, do not hide an essential collection
or lifetime problem behind increasingly expensive tuple manipulations.

## 6. Proposed bootstrap milestone

Deliver the milestone through small, dependency-ordered changes scheduled
through the current roadmap.

### 6.1 Define the workload and boundary

Choose a compiler workload large enough to exercise the intended pipeline.
Name its required language subset, supported input, runtime services,
and expected output.

Use provisional syntax or serialized semantic input where appropriate.
Final syntax design is not a prerequisite.

State whether the milestone is a useful hosted bootstrap or requires removal
of Python at runtime.

### 6.2 Establish an executable artifact path

Use Python to execute the compiler written in SHEAR.

Specify how the compiler's output becomes executable on the declared runtime.
The current interpreted path may remain useful, but extending it is not
automatically the best delivery route.

Executing compiler-produced artifacts must respect the existing distinction
between the semantic program and derived executable code. Direct host execution
of arbitrary supplied bytecode must not be introduced as an unnoticed shortcut.

If a new execution path is needed, test it with a narrow spike before committing
to a backend. Compare alternatives only where a concrete uncertainty warrants
the work.

### 6.3 Close the declared pipeline

Provide one documented command path from input through validation, semantic
construction, compilation, and execution.

Host services may remain where the milestone explicitly permits them.
Unsupported operations must fail explicitly rather than silently falling back
to an undeclared implementation.

Maintain an executable support matrix for the relevant operations across:

- Host lowering.
- Host execution.
- SHEAR-written lowering.
- Execution of the SHEAR compiler's output.

The matrix should distinguish supported behavior, explicit rejection, and
deliberately deferred behavior.

### 6.4 Rebuild with the produced compiler

The Python seed loads and runs the initial SHEAR compiler.
That compiler produces the next compiler artifact.
The produced artifact executes and rebuilds the compiler again.

Record the provenance and execution route of each stage so that host fallback
cannot masquerade as self-rebuilding.

Compare deterministic artifacts where appropriate, and compare observable
behavior against the reference model and independent acceptance expectations.

Where identities or artifact metadata are intentionally nondeterministic,
specify the comparison relation. Do not normalize away semantically meaningful
differences merely to obtain agreement.

A compiler fixpoint is useful evidence, not a complete correctness proof.

### 6.5 Exercise live evolution on the same route

The delivered path must eventually demonstrate a running image that:

- Reads and changes its semantic program.
- Compiles the candidate through its retained compiler machinery.
- Trials and activates a valid change.
- Preserves the explicitly expected continuity and live data.
- Handles a rejected candidate according to the specified failure semantics.
- Exercises an old frame or closure across the change.
- Repeats updates and retires versions according to the declared lifetime policy.

These cases can be introduced incrementally, but they belong to the milestone's
acceptance criteria. A batch-only compiler is insufficient evidence for the
complete SHEAR delivery goal.

Do not promise rollback of effects where the specification provides none.

### 6.6 Make the result usable

Provide build/run commands, inspectable semantic changes, and diagnostics
locating failures. Reuse structured results for human and AI clients.

Full IDE integration, graphical debugging, package distribution, and syntax
polishing can develop incrementally. They are not prerequisites for the first
useful bootstrap.

## 7. Performance: separate seed cost from delivered-system cost

Python can be slow without invalidating the bootstrap path.
Its initial requirement is to make development and rebuilding tolerable.

The eventual language implementation has a different requirement:
acceptable performance for its intended programs and live evolution.

Self-hosting alone provides no speedup. Faster execution requires improved
algorithms, representations, generated code, or execution machinery.

Measure these costs separately:

| Workload | Measurements needed |
| --- | --- |
| Seed loading and initial compilation | Elapsed time, peak memory, host services used |
| Successive compiler rebuilds | Time and memory per generation, artifact size, execution route |
| Representative ordinary programs | Throughput or latency, allocations or peak memory, input size, relevant baseline |
| Small edits in increasingly large programs | Matching, state construction, identity derivation, validation, lowering, migration, activation, and total latency |
| Repeated valid and rejected updates | Latency distribution, retained states and artifacts, retirement and reclamation behavior |
| Startup and compiler availability | Startup time and full image footprint, including semantic graph and compiler |

Record initial baselines on named hardware, then choose numeric acceptance
budgets appropriate to the milestone before accepting the implementation route.
Do not invent thresholds without workload evidence.

Pin workload inputs, implementation revision, machine/runtime configuration,
cache conditions, and repetition count. Report variability and use several input
sizes to expose scaling.

Relowering one node is not a measurement of total update cost.
A speedup over Python alone is not proof that a delivered system is adequate.

Separate intentionally retained history, caches, and live holds from memory
that should have been released. Require bounded retention only where the
scenario's lifetime and history policy implies it.

Use existing measurement infrastructure where possible. Timing gates belong
on sufficiently controlled runners; deterministic correctness checks remain
in ordinary CI.

Optimize Python code when it blocks practical iteration or exposes a cost
that will survive bootstrap. Avoid extensive optimization of machinery that
the chosen bootstrap path will soon replace.

Per-node semantic identity does not require per-node execution dispatch.
Larger chunks, inlining, conventional backends, and opaque storage may preserve
the semantic model while changing execution costs.

Derived artifacts must track all dependencies needed for correct recompilation
and activation. The current cache strategy is an implementation choice, not the
project's defining idea.

## 8. Concrete implementation priorities

These recommendations require task-specific verification. They are not a claim
that every listed area currently contains a defect.

### Execution context and failure provenance

Before substantially extending execution boundaries, consider extracting one
explicit run-context component from `shear/machine.py`.

It should centralize the state needed for error provenance and host-callback
boundaries while preserving the distinction between an independent run and
a trial within its enclosing run.

Extract a demonstrated responsibility, not arbitrary sections of a large
dispatch loop. Preserve existing behavior and adversarial regressions.

### Converter effects during activation

Reproduce and classify the previously observed case in which a converter
modifies a live cell and then raises.

Determine precisely which effects activation atomicity covers and which
effects, if any, remain outside it. Then choose the smallest justified response:
restrict converter access, isolate permitted changes, reject reentrant mutation,
or explicitly document the applicable effect boundary.

Do not describe activation as globally transactional if callbacks can produce
irreversible external effects. Add regression evidence for the chosen contract.

### Compiler and execution coverage

Make gaps such as embedded `catch` and `raise` visible in the support matrix.

Extend the selected bootstrap path according to its workload. Do not
automatically reproduce every new host feature in the experimental interpreter,
but do not count host-only features as implemented on the bootstrap path.

### Retention and retirement

Exercise repeated updates while creating and releasing frames, closures,
references, and explicit holds.

Measure what remains reachable after retirement and distinguish required state,
optional history, caches, and incidental references. Use the result to guide
version-retention changes.

### References held as data

Follow task 22 before changing the reference contract.

When implementing the planned distinct reference values, cover nested data,
captured environments, disappearance, transfer, and retirement together.
Ordinary entity IDs must remain ordinary data unless the semantics explicitly
say otherwise.

## 9. Keep development fast without losing commitments

Keep the existing plan/execute/review loop, deterministic PR suite, semantic
corpora, and reproducible counterexamples.

This proposal introduces no new CI workflow, standing review phase,
parallel-agent requirement, or second decision ledger. The split review used
for this contribution was a requested assessment.

For each delivery task, record in its existing plan:

- The working program or bootstrap dependency it enables.
- The semantic boundaries it changes.
- The acceptance evidence and relevant cost measurements.
- What remains deliberately unsupported.

Test changed interactions and preserve substantive counterexamples.
Do not require exhaustive testing of every possible feature combination.

Retain the Python model as an oracle where it remains independently useful.
Share mechanical metadata where appropriate, but avoid sharing the algorithms
under comparison merely to force agreement. Agreement between implementations
that contain the same mistake is weak evidence.

Code should expose costs and falsify design assumptions.
Existing behavior does not automatically become intended semantics.
Classify mismatches before deciding whether code, tests, or specifications
must change.

Keep simplification experiments bounded by a named cost, prediction, and stop
criterion. Evaluate total implementation, runtime, and verification cost,
not only primitive count.

Consolidate duplicated rules when they create demonstrated friction.
Do not add interfaces around every hypothetical future replacement or make
broad cleanup a prerequisite for every feature.

Growing change radius and repeated boundary failures are investigation
triggers, not automatic proof that the architecture requires replacement.

Use existing specifications and the changelog to preserve decisions and
rejected alternatives. Keep the handoff a short checkpoint linking to them.

Delivery progress is a reproducible working capability within the agreed
budget, not the number of mechanisms, documents, or passing tests.

## 10. Relationship to the current development path

The [roadmap](../roadmap.md) remains the scheduling authority.
This proposal interprets and extends that path rather than silently replacing it.

Task 20 supplies the error-handling foundation.
Tasks 21–26 retain their existing acceptance criteria, stop rules,
and conditional scheduling unless an explicit change is adopted.

| Existing task | Contribution to the bootstrap objective |
| --- | --- |
| 21. Endpoint arity audit | Establish which endpoint distinctions the compiler and semantic representation must preserve. Retain its independent scheduling and no-refactor scope. |
| 22. Reference version audit | Clarify the reference contract before or during planning references held as data. Avoid losing version semantics during implementation changes. |
| 23. Content duplication baseline | Measure costs before changing content machinery. Preserve its position before tasks 24 and 25 alter the baseline. |
| 24. Constraints as functions | Test whether existing computation and error mechanisms can remove duplicated machinery. Keep its declared kill criterion; rejection of the hypothesis is a valid result. |
| 25. Field identity under layout change | Establish what records and references require across activation and retirement. Keep its trigger when records are planned; do not pull systems data forward by implication. |
| 26. Content consolidation decision | Use the baseline and experiment results to decide whether consolidation earns a separate implementation task. Do not presume a refactor. |

References held as data, records before systems data, and syntax/tooling remain
under their existing roadmap directions.

Bootstrapping from Python is the delivery destination for this work.
It does not require an intermediate wholesale rewrite of the Python model.

The roadmap's conditional dependencies should remain explicit.
Not every open language question must be resolved before a useful hosted
bootstrap, and not every successful experiment requires immediate adoption.

Changes to ordering or scope are welcome when supported by a concrete
dependency, defect, or measured cost. Record them as proposals until adopted.

## 11. Proposed additions to the path

### Extend task 23 with practical measurements

Reuse its measurement pass to record compiler execution time, peak memory,
representation size, and complete small-edit cost on named workloads.

Keep these measurements separate from content-duplication counts.
This gives tasks 24–26 a practical reference without creating a benchmark
framework or treating the slow embedded interpreter as the eventual engine.

### Add a bootstrap dependency inventory

Inventory the actual Python services required by the SHEAR compiler workload.

Classify which remain permitted for hosted bootstrap and which must move into
SHEAR or another explicitly chosen runtime component.

This identifies concrete missing capabilities without requiring speculative
completion of the entire language.

### Add an explicit hosted-bootstrap milestone

Use section 6 as its acceptance outline.

Name the workload, compiler coverage, executable artifact path, host boundary,
and development budgets before committing to implementation.

Schedule its constituent changes through the existing roadmap.
Do not automatically wait for every item under Later or treat all research
results as mandatory redesigns.

### Define removal of Python separately

If the intended delivery requires no Python at runtime, make that an explicit
subsequent milestone or an explicit extension of the bootstrap milestone.

List the runtime services that remain and the evidence needed to replace them.
Do not conflate compiler self-hosting with completion of memory management,
platform integration, or native execution.

### Preserve the distinctive capability on the delivery path

Require live compilation and activation on the same path used for ordinary
programs and compiler rebuilding.

This prevents performance work from delivering a fast execution mode that
cannot support the project's central evolution model.

## 12. Decisions still required

**Open:**

- The compiler workload and supported subset for the first useful hosted
  bootstrap.
- The Python services permitted to remain in that milestone.
- The input and artifact formats used by successive compiler generations.
- The execution route for compiler-produced artifacts and its validation
  boundary.
- The first supported platform and measurement hardware.
- Numeric rebuild, execution, memory, update-latency, and image-size budgets.
- Which runtime dependencies must eventually be removed, and when.
- Where the proposed additions fit into the current task sequence.

Python as the initial bootstrap environment is the stated direction.
These open decisions concern the scope and implementation of that path,
not whether an unrelated language implementation must be built first.
