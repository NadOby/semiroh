# Roadmap

**Status: provisional.** The order of work after the code-as-graph spike
(PR #17, docs/spikes/code_as_graph.md on that branch). Tasks are done in
order unless marked independent; each one has a GitHub issue, is a PR and
follows CLAUDE.md.

## Workflow

**Decided.** Each task passes through five roles: Plan, Execute, Review,
Resolve and Publish, each normally in its own fresh chat, with no background
agents. The owner starts a role with "Plan task N", "Execute task N",
"Review task N", "Resolve task N" or "Publish task N"; the contracts below
make that instruction sufficient. Every role starts by fetching the
repository and reading CLAUDE.md, this section, the task's roadmap entry and
`handoff.md`, and ends by recording its state in `handoff.md` and stopping.
`handoff.md` is a checkpoint of claims, not evidence that they hold.

**Decided.** Work is tracked in GitHub issues. Each roadmap task not yet
done has an issue labelled `task`, named in its entry's status line; any
other change gets an issue before work starts, and a follow-up found during
a task becomes an issue labelled `follow-up`. An issue holds the goal, the status and the
discussion. This roadmap remains the order and the task definitions, the
specifications the design, `CHANGES.md` the log and `handoff.md` the
checkpoint between chats. Commits and PRs name their issue as CLAUDE.md
describes.

1. **Plan** (`Plan task N`). A fresh context, preferably with the strongest
   reasoning model available. No production changes.
   - Inspect the current repository rather than relying on earlier context;
     read the roadmap task, the relevant specifications, CLAUDE.md and
     `handoff.md`.
   - Treat the roadmap entry as a goal to validate, not a recipe to obey:
     check that its assumptions still hold, and find contradictions,
     underspecified semantics, scope hazards and decisions that need the
     owner. Bring every decision that shapes the language to the owner,
     like D1, with options and a recommendation; make every other choice
     and mark it Provisional.
   - Establish the intended semantics, the exact scope, an implementation
     order where useful, falsifiable acceptance criteria where practical,
     the tests and invariants that must not change, and the decisions
     Execute must not make alone. A new layer gets an acceptance test that
     runs the existing corpora through it.
   - Name the important claims Review must verify independently, and keep
     required work apart from useful follow-ups.
   - Find the task's issue, or create it with the `task` label and name it
     in the roadmap entry.
   - Write the spec and acceptance tests on a branch `task/<n>-<name>`, and
     turn `handoff.md` into the execution contract.
2. **Execute** (`Execute task N`). A separate implementation context with
   write access.
   - Implement the Plan contract, committing coherent steps, preserving
     settled semantics and the acceptance tests.
   - Make provisional choices only where the plan permits them. If the work
     shows the plan is materially wrong, do not redesign around it: return
     the decision to the owner or to a new Plan pass.
   - Record in `handoff.md` the implementation state, provisional choices,
     verification performed, known limitations, mutation-survivor decisions
     and the claims Review must verify.
   - Execute does not certify its own implementation as correct.
3. **Review** (`Review task N`). A fresh context separate from Execute;
   a different model when useful. Adversarial, and read-only for the
   implementation.
   - Fetch the current repository before judging anything. Read
     `handoff.md` as claims to check, not as evidence.
   - Verify the important claims independently against code, tests, docs,
     git history and diff, and CI, and check conformance with the Plan
     contract.
   - Look actively for false confidence: weakened or changed acceptance
     tests; test gaming or task-specific special cases in production code;
     self-referential or non-independent oracles; stale or over-recorded
     goldens; incorrect mutation-survivor carry-over; CI gaps; accidental
     semantic or public-API changes; replay or reduction mistakes;
     documentation drift.
   - Classify each observation as a verified defect, a limitation, a
     hypothesis or documentation drift. Give each verified defect a severity
     from P0 to P3, its exact location, why it is a defect, a concrete
     failure mode or counterexample, and the smallest valid fix. Do not turn
     suspicion into a defect, and do not re-raise historical issues that the
     current code has fixed.
   - Do not repair production code, tests or specifications; record the
     findings in `handoff.md` if needed.
4. **Resolve** (`Resolve task N`). An execution-capable context.
   - Handle the findings one by one: fix a verified defect with the smallest
     valid change, or rebut it with concrete repository evidence.
   - Do not change Decided semantics, acceptance expectations or
     specifications to make a finding disappear; escalate such decisions to
     the owner.
   - Record fixes, rebuttals and unresolved findings in `handoff.md`.
   - A fresh Review pass follows every Resolve. Review and Resolve repeat
     until Review has no unresolved blocking finding.
5. **Publish** (`Publish task N`). Only after an independent Review has
   accepted the final implementation state.
   - Fetch current `main` and rebase the task branch if needed; re-check
     that the acceptance tests are unchanged; verify the final diff and CI;
     check that every finding is resolved or explicitly accepted as a
     non-blocking limitation.
   - Open a ready PR whose description closes the task's issue
     (`Closes #<n>`), then mark the roadmap entry Implemented with the PR's
     number. The PR states intentionally deferred limitations and follow-ups
     separately from defects; each deferred follow-up gets a `follow-up`
     issue named in the PR.

The owner merges, or pushes back, and says so.

A chat whose context grows heavy ends by updating `handoff.md`; the next
chat in the same role starts from CLAUDE.md, this section and `handoff.md`.
Mutation campaigns run in CI, not in a chat.

## Decision D1: graph form is canonical

**Decided.** Code is stored as graph form: each expression node is a
relation entity owned by its function. Tuple bodies with links remain an
input format that converts into it.

The spike showed that code as graph works over the unchanged core. Editing
one node leaves every other node's `EntityID` and `VersionID` alone.
Renames come free from relation endpoint continuity, and the links relation
becomes redundant. The spike recommended a hybrid because installing code
was slower in a state with 3-5x more entities. That cost comes from `State`
re-serializing every entity's content to derive `StateID`, a core scaling
problem task 2 fixes. A hybrid would have meant two representations, two
interpreters and conversions in both directions, against a vision whose
first line is that the graph is the source of truth.

## Decision D2: compile to bytecode

**Decided.** Task 7 lowers graph form to a small bytecode, plain tuples of
instructions such as `ARG x`, `MUL`, `CALL f`, run by a VM with its own
explicit stack, rather than to Python closures. A SHEAR program can emit
bytecode as data, which the self-hosting milestone (task 8) needs; it
cannot emit Python closures. An explicit stack also removes the recursion
limit the corpus found (about 200 levels of non-tail recursion). The
bytecode is the executable IR layer of the syntax notes and the shape an
MLIR dialect could later map from.

## Pending decisions

Both belong to section I, hosted bootstrap.

- **D3: where compiler-produced chunks run.** Open; task 29 brings options
  and a recommendation. Either the SHEAR VM (no change in what the host
  trusts, about 150x the host machine per layer), or the host machine running
  the SHEAR compiler's chunks as derived artifacts of the nodes they compile,
  with recorded provenance and behind a verifier. The second narrows
  bytecode.md section 8 without letting a program run arbitrary bytecode.
- **D4: the hosted-bootstrap workload and boundary.** Open; settled before
  task 30 is planned, with task 28's inventory. Recommended: the workload is
  the SHEAR compiler rebuilding itself plus the corpus, live evolution
  included; Python stays permitted for parsing, `define` and continuity
  inference, state and identity derivation, canonicalization and activation;
  the result is called hosted, never Python-independent.

Decided since: constraint relations see an owner endpoint with its owned
subtree (relation_model.md §7).

## A. Foundations

### 1. Canary corpus, tier 1 (handoff, independent)

**Done** (#20).

A library of small programs with expected results, in
`shear/examples/`. Every interpreter and representation must run them
unchanged, so the corpus gives differential tests when there are two.
Each program is data: a program state, an entry, and cases
`(args, expected result, expected cells)`. A self-modifying program may
also carry a scenario of runs and checks.

Tier 1 is what the current language can express: arithmetic and recursion
(factorial, fibonacci, gcd), side effects (a counter, an accumulator with a
constrained cell), control (if, seq, early rejection by a cell
constraint), and self-modification (compile and activate, trial before
activate, rename under continuity).

Programs the language cannot express yet are listed with the feature they
need. That list is the input for task 6.

Done when: the corpus runs under `lang.py` in one test module, with at
least 10 programs and a list of the missing features.

### 2. Cheap StateID (handoff)

**Done** (#19).

Derive `StateID` from each entity's `VersionID` (cached per `Value`) plus
ownership, instead of re-serializing every entity's content. `StateID`
stays derived from content and cannot be supplied; only its hash input
changes.

Done when: equal content gives an equal `StateID` and different content a
different one (seeded property test); the spike's `COMPILE(12)` install on
graph form is no slower than on `lang.py`; the full suite passes.

### 3. Creation places entities under an owner (handoff)

**Done** (#21).

Answers ownership_model.md §13, "how creation places a new entity under its
owner". The owner leans towards a guarantee of the transformation. A
transformation declares placements (new entity → owner) instead of
restating the whole destination ownership map, and removing an owner
removes what it owns. The spike needed this for every install.

Done when: `ownership_model.md` §13 marks the answer Decided, and
transformations can create and delete owned groups without supplying the
full ownership map.

## B. Code as graph

### 4. Adopt graph form (one session)

**Done** (#22).

Code is stored as graph form (D1). Tuple bodies with links become the input format
that converts into it, so `test_first_program.py`,
`test_metaprogramming.py` and `test_language_trials.py` keep running,
through the converter. The spike's leaf-node `self` role is replaced by
something the core supports directly. Operations on tuple values stay
available, while operations on code move to nodes. One interpreter
remains.

Done when: one interpreter runs the three acceptance suites and the tier 1
corpus; PR #17 is closed in favour of this task.

### 5. Node-level self-modification (handoff)

**Done** (#24).

`activate` and `trial` can target a single node, so hot swapping at the
language level has the same granularity as identity. This is the piece
the spike did not build.

Done when: a program replaces one subexpression of a running function, and
only that node's version changes.

### 6. Canary corpus, tier 2: data and higher order (handoff)

**Done** (#25).

Add what task 1 found missing, probably: taking tuples apart, local
bindings, and applying a function value. Then add programs for map, fold
and sort, plus a canary that swaps the sort implementation between two
runs while the data stays in a cell.

Done when: the tier 2 programs run, and the list of missing features is
updated.

## C. The payoff

### 7. Incremental compilation to bytecode (one session)

**Done** (#26). The design is in bytecode.md, which also records the answer to
the last question below: per-node caching is simpler than re-pointing
dependents and more precise, so per-node identity is paying for itself.

Lower graph form to bytecode (D2) and run it on a VM with an explicit
stack. The bytecode is cached as a derived artifact keyed by node version,
so after a self-modification only changed nodes are lowered again. The
corpus and the acceptance suites run unchanged on the VM, and the
non-tail recursion entry leaves `MISSING`. If caching per node version is
not simpler and more precise than re-pointing dependents per function,
record that per-node identity is not paying for itself.

### 8. Self-hosting milestone (one session)

**Done** (#30). The design is in self_hosting.md. The owner chose the scope:
the compiler emits bytecode as data and is checked against the host's;
what it emits is not run yet (task 10).

First, an operation that reads a function's code as data (input form or
nodes), so a program can see the code it compiles; today only the host has
`function_at`. Then write the lowering pass from task 7 in SHEAR itself:
a program recompiles and hot swaps part of itself with its own compiler.

### 9. A compiler pass that keeps continuity (one session)

**Done** (#31). The design is in constant_folding.md.

For example, constant folding written as a graph transformation that
declares its merges. Optimised, hot-swapped code keeps a mapping to its
source nodes, which a test checks. Independent of task 8.

### 10. A bytecode interpreter in SHEAR (one session)

**Done** (#32). The design is in vm_in_shear.md.

Owner's direction after task 8: "probably". A small VM written in the
language runs the chunks the compiler of task 8 emits, so a program compiles
itself and swaps in a function that runs its own emitted chunk. Needs a way
to call a function chosen at run time and to read a function by reference
(self_hosting.md sections 5 and 6).

## D. Human source

### 11. Text syntax, version 0 (handoff)

**Done** (#34). The design is in syntax.md.

A parser from text (syntax_notes.md, Direction A) into the input format and
a printer from graph form, import-only (syntax.md). Done when the corpus
round-trips through text by behaviour and by text, and the examples not
tagged self-modification render without `raw`.

## E. Continuity

After an outside review (owner-relayed): the project's distinctive claim is
semantic continuity, and continuity is specified where a transformation
declares it but not where it must be inferred, as in ordinary edits. So
the next wave makes continuity explicit before the reconciler.

### 12. Continuity corpus (handoff)

**Done** (#35). The design is in continuity_corpus.md; 11 cases
hold and 10 are gaps.

Cases with expected continuity for rename, move, insert, delete, split,
merge, fold, activate and upgrade (continuity_corpus.md). Cases that hold
today pin the current rules; cases that do not are recorded as gaps, and
become the input of task 13.

### 13. Continuity inference (one session)

**Done** (#36). The design is in continuity_inference.md; all 21
corpus cases hold.

Deterministic rules for continuity nobody declares: keeping unchanged
descendants in an edit, matching a new tree against an old one (an
ambiguous match gets a new identity, never a guess), moves across
functions, and merging or rejecting two transformations of the same state.
Done when the gaps of task 12 hold.

### 14. Where the graph earns its keep (one session)

**Done** (#37).

A short ledger comparing each capability of graph form with what an AST,
a symbol table and a dependency index would need, with the measurements
of tasks 7, 9, 12 and 13. Weak rows are recorded as such.

### 15. Reconciler (one session)

**Done** (#38). The name-resolution rules are in
name_resolution.md.

Text edits become transformations with continuity (task 13's rules), so
editing text keeps the identity of everything the edit does not touch.
Lexical and module name resolution are specified first.

### 16. Documentation coherence (one session)

**Done** (#40).

Correct mechanical documentation drift without changing semantics. Normalize
standalone `Decided`, `Provisional`, and `Open` status markers; check internal
Markdown links and numbered section references; and catch stale roadmap PR
markers. Documentation-only changes run the coherence checks in CI.

Substantive documentation/code mismatches are reported rather than silently
resolved.

Done when: the coherence tests pass, affected status markers are normalized,
and `CHANGES.md` records the sweep.

### 17. Closures (handoff)

**Implemented** (PR #41). The design is in closures.md.

Close the last remaining corpus gap: anonymous callable values with lexical
captures.

Keep `Function` as code-as-data for program construction and activation.
Introduce a distinct executable closure value containing code and its captured
lexical environment. `apply` and `applyv` accept closures as well as existing
function references.

Captures are by value when the closure is created and do not depend on the
caller's scope. A returned closure remains callable after its creating frame
has finished. Creating or calling a closure requires no activation capability.

`make_adder` and `compose` are corpus examples; closures can be passed,
returned, stored and captured as ordinary values; closure calls obey ordinary
arity and tail-call rules; continuity keeps closure code identities meaningful
across activation; the host and self-hosted compilers agree on closure
lowering; the SHEAR VM runs the emitted closure bytecode; and `MISSING` is
empty.

## F. Verification and architecture

### 18. Verification hardening (handoff)

**Implemented** (PR #42). The verification design and policy are in
verification_hardening.md; execution evidence is recorded in `CHANGES.md`
and the PR.

Strengthen the evidence that the semantic model is correct before changing
its architecture. This is broader than adversarial testing: combine
cross-boundary, differential, malformed-input, metamorphic, stateful,
bounded-exhaustive and mutation testing, with failure reduction into permanent
regressions.

Split the ordinary test suite, currently about 27–40 seconds, into meaningful
parallel CI lanes. Keep the full deterministic suite on every PR; give heavier
stateful, fuzzing and mutation campaigns separate budgets while keeping every
failure reproducible.

Done when: the verification boundaries are documented and exercised,
important independent implementations are differentially checked over
generated cases, malformed and stateful testing attack semantic boundaries,
at least one small domain is exhaustively explored, mutation coverage is
substantially broader with survivors classified, generated failures can be
reproduced and minimized, and ordinary CI is split and parallelized with its
before/after wall time recorded.

### 18a. Verification infrastructure follow-up (one session)

**Implemented.**

Improve the verification harness itself before task 19 changes the language
architecture. This task changes test infrastructure and CI only, not production
semantics or the verification policy established by task 18.

Mutation work is now sharded at the individual-mutant level. The complete work
set selected by the existing per-target budget, seed and batch semantics is
built first and deterministically shuffled from the seed. Individual mutants
are then distributed round-robin across shards, so shard count does not change
selection, the shard union is exactly the unsharded work set with no
duplicates, and shard sizes differ by at most one mutant. Timing measurements
remain diagnostic only and do not affect assignment.

Mutation campaigns are observable while they run. The start event records the
mutation-engine version, target-source versions, campaign inputs and selected
mutation keys. Flushed progress reports completed and total mutants, killed
mutants, classified and unclassified survivors, elapsed time and a current
target; a time-based heartbeat continues even when no mutant finishes.
Survivors are reported immediately, while ordinary killed mutants remain
suppressed from the human log.

Completion reports are grouped by target and mutation kind and include elapsed
time and per-target timing statistics. The same event source is written as
JSONL machine-readable evidence containing exact selected keys and every
outcome. Manual mutation shards publish these reports as CI artifacts even when
the shard fails because an unclassified survivor was found.

An exact reported mutation can be replayed directly under its recorded
target-source and mutation-engine pins without reconstructing its seed, batch or
shard. Completed shard reports can also be supplied to `replay-failures`, which
runs one semantic baseline and then replays only their recorded unclassified
survivors.

The mutation subprocess semantic oracle is centralized in
`tests/mutation_oracle.py`. Harness-integrity and survivor-catalog checks remain
mandatory in the ordinary mutation CI lane but cannot become mutation-kill
oracles. Regression tests pin that baseline and mutant subprocesses use the same
semantic oracle.

Done when: for a fixed source tree, budget, seed and batch, mutant-level shards
are deterministic, disjoint and exhaustive and differ in selected mutant count
by at most one; campaigns provide useful live progress and immediate survivor
reporting; machine-readable results are emitted even on failure; any reported
mutation key can be replayed directly and failed reports can replay only their
unclassified survivors; mutation-oracle selection is centralized and
regression-tested; and no production file or intended semantic behaviour
changes.

### 19. Language architecture hardening (handoff)

**Implemented** (PR #45).

Refactor the language implementation against the stronger verification
baseline from task 18, without intentionally changing semantics.

The immediate targets are the accidental duplication and weak boundaries
exposed by task 17: operation structure is described independently in several
tables and switch statements; `syntax.py` and `lang.py` have accumulated
multiple responsibilities; and bytecode lowering and machine execution still
have an avoidable dependency seam.

Prefer one declarative source for mechanical operation shape – arity, code
children and structural roles – while keeping genuinely different semantics
explicit in the parser, runtime, compiler and self-hosted implementations.
Split large modules only where those boundaries are demonstrated by the code
and tests, not merely because a file is large.

Done when: mechanical operation metadata has one authoritative definition,
syntax responsibilities are separated behind the existing public API,
bytecode/machine dependency direction is clean, remaining `lang.py` boundaries
are made explicit where justified, and the task changes no intended language
behaviour.

## G. Errors

### 20. Error handling (handoff)

**Implemented** (PR #55). The design is in error_handling.md.

Today every failure ends the whole run. A candidate that crashes under
`trial` stops the program deciding about it, `account` cannot report a
refused withdrawal, and the interpreter written in SHEAR fakes its own errors
by indexing an empty tuple. Add `catch`, which turns a failure into
`("ok", value)` or `("failed", error)` and can accept only listed kinds, and
`raise`, which fails with a program's own error. An error is
`(origin, kind, detail, where)`; the scope is every failure the language
reports, including the call-depth limit; nothing is rolled back.

Done when: `tests/test_error_handling.py` passes unchanged; the `errors`
examples run in the corpus and round-trip through text; every program of
main keeps its StateID, text and bytecode, so `tests/language_golden.json`
is re-recorded only to add entries; existing failures keep their classes and
messages; the language docs name the new operations; and survivors of edited
mutation targets are carried or dropped by the task 19 rule.

## Later

- Systems data: structs, arrays and references between cells, with layout
  changes handled by converters. Postponed by the owner; records would come
  first.
- References held as data follow continuity (language_data.md §3).
  Owner's direction from task 20 planning: `ref` makes a distinct reference
  value, so only references follow declared continuity at activation and
  plain entity ids stay data; a reference whose target disappears pins the
  old version, which needs the two-version bound to become a setting rather
  than a rule.
- Declared error kinds: program entities, like cells, naming a kind and
  constraining its detail (error_handling.md section 13).
- Syntax and tooling notes (syntax_notes.md): graph and IR views next to
  the source view of task 11.
- The program root and modules (ownership_model.md §13), when explicit
  modules or libraries need them.
- No Python at runtime: the milestone after section I. It lists the runtime
  services that are still Python's and the evidence needed to replace each.
  Self-hosting does not imply it, and it does not require rewriting platform
  services in SHEAR.

## H. After the semantic-core experiment

The experiment (identity_model.md §10) killed one simplification strategy
and left narrower ones. Two rules apply to this section: a simplification
names the concrete mechanism it intends to delete, and a research task names
the concrete requirement that could falsify the current architecture.
Predictions are recorded before a run; an experiment gets one revision.

These tasks follow task 20 (error handling, `task/20-error-handling`).
Task 21 is independent of it; tasks 23 and 24 should start only after task
20 is merged, because it changes the machine substantially.

### 21. Endpoint arity audit (one session)

**Planned.** Independent. Issue #58.

`Relation` distinguishes a single endpoint from a one-element tuple. For
code relations `shear/operations.py` already determines which roles hold
ordered tuples. Check every relation kind, code and non-code, for anything
that observes the distinction.

Done when: the distinction is classified as redundant, semantically
required, or retained deliberately for engineering reasons, with the
evidence. No refactor in this task.

### 22. Reference version audit (one session)

**Planned.** Issue #59.

`Reference(StateID, EntityID, VersionID)`: `State.resolve` and reference
transfer check `StateID` first, so `StaleReference` is reachable only for a
malformed or forged reference. Determine whether a valid reference can
distinguish anything with `VersionID` that `(StateID, EntityID)` cannot.

Take the planned `ref` values into account (the "references held as data
follow continuity" item under Later): a reference that pins an old version
when its target disappears, and transfer that need not preserve the source
version, may give `VersionID` a role today's code does not show. Run this
audit before or as part of planning that item, not after it.

Done when: `VersionID` in `Reference` is classified as redundant,
semantically required, or retained deliberately (integrity witness, cache
key, offline validation), and the reason is documented in
reference_model.md. No refactor in this task.

### 23. Content duplication baseline (one session)

**Planned.** After task 20. Issue #60.

Measure the machinery that handles semantic content in several forms:
conversion sites between host values and canonical content, `Value` content
versus `Relation` records and payloads, mutation survivors in
`canonical.py`, `values.py` and `relations.py`, and content handling in the
self-hosted compiler and VM. Taken after task 20, which changes the machine,
and before tasks 24 and 25 change the code again.

Section I adds bootstrap costs to the same pass, kept apart from the
duplication counts: on named hardware, native and SHEAR-VM time for the
compiler compiling itself, peak memory, chunk and image sizes, and one small
edit end to end through `define`, lowering and activation. No benchmark
framework; timings stay diagnostic and outside ordinary CI.

Done when: the measurements, bootstrap costs included, are recorded. No
refactor.

### 24. Constraints as functions (handoff)

**Planned.** After task 20. Issue #56.

Falsification experiment: can the constraint algebra (`constraints.py`, its
own evaluator, budget and three-valued result) be expressed through the
existing computation model with fewer total mechanisms? Task 20's `catch`
and its `limit` errors are the natural candidates for the one generic budget
and the failure boundary; using them is part of the experiment, not
assumed.

Kill criterion: it succeeds only if the mechanism count drops. Cost side:
new VM operations, runtime-only semantic cases, special Unknown or budget
machinery, constraint-only environment interfaces. Removed side: the
constraint evaluator, constraint node semantics, constraint-specific
recursion and control, the duplicate `External` path. Success allows at most
one generic boundary for external authority and one generic execution
budget; strong-Kleene behaviour comes from functions and data.

Done when: the experiment is run against recorded predictions and the
result – adopt or kill – is recorded.

### 25. Field identity under layout change (handoff)

**Planned.** Issue #61. Research input to records; the owner has postponed systems
data until records exist (Later).

When records are planned, first run this spike. Scenario: record A `{x, y}`,
a reference R to `A.y`, and a running old-version frame holding R;
activation continues A to A' with layout `{x, z, y}` and a converter; new
code reads `A'.y`, the old frame continues under the old state, and R has an
explicitly defined fate. Then vary one dimension at a time: moved field,
deleted field, split record, ownership change, old-version retirement.

The central question is the status of `A.y`, to be discriminated rather than
presupposed: its own semantic identity; no identity (A plus a selector); or
a logical property with layout and access path separate. It interacts with
the planned `ref` values. The activation and lifetime protocol is modelled
in Alloy (the runner from the archived experiment returns here);
representation and layout are tested in Python.

Done when: the scenario and its variations are run against recorded
predictions and the result names which `A.y` outcome holds and what records
need from it.

### 26. Content consolidation decision (one session)

**Planned.** Issue #62.

Decide from task 23's baseline and what tasks 24 and 25 taught whether
unifying `Value` content, relation records and payloads into one relational
content form is still justified. It must preserve `EntityID`, reference and
ownership semantics and show a concrete reduction in production mechanisms
or conversion paths.

Done when: the decision is recorded; if positive, the refactor becomes its
own task.

## I. Hosted bootstrap

**Provisional.** Adopted from the bootstrap delivery review
([reviews/bootstrap_delivery.md](reviews/bootstrap_delivery.md)), which stays
as the dated input for this section. Issue #69; the tasks are grouped in the
GitHub milestone "Hosted bootstrap".

The destination of the work after task 20 is SHEAR bootstrapped from the
Python model, with its distinctive capability on the same path. Four stages
are kept apart:

1. **Python seed.** The Python model runs the compiler written in SHEAR.
   Done by tasks 8 and 10.
2. **Self-rebuild.** The compiler's own output compiles the next generation
   of the compiler, and the record shows that no host fallback did.
3. **Hosted bootstrap**, this section's milestone. The rebuilt compiler
   handles a declared subset, the corpus and live evolution, using explicitly
   permitted Python services at a recorded cost.
4. **No Python at runtime.** A later, separate milestone (Later).

Tasks 8 and 10 reached stage 1 and a fixpoint check: `swap_all` replaces
each compiler function with a call to the SHEAR VM holding a chunk that the
host-run compiler produced, and the swapped compiler compiles `lower` to the
same chunk. Three facts shape this section:

- No chunk the swapped compiler produced is ever run. The swap also replaces
  the compiler's source in the active state with wrappers whose literal
  chunks become its code, so the executable form displaces the semantic one,
  against the first point of the vision.
- The SHEAR compiler does not cover `quote`, `unquote`, `function`,
  `activate`, `trial`, `catch` or `raise` (self_hosting.md section 2,
  vm_in_shear.md). These are mostly the live-evolution operations, so the
  bootstrap route cannot compile a self-modifying program yet.
- Program-produced chunks run only on the SHEAR VM (bytecode.md section 8),
  at about 150x the host machine for one layer: `lower(lower)` takes 0.04 s
  natively and 5.9 s on the SHEAR VM (2 cores, best of 3).

The acceptance anchors are the review's section 4: the semantic graph stays
canonical and executable forms stay derived; an image keeps the compiler
machinery that regenerates its execution; producing a candidate stays
distinct from activating it; continuity alone does not establish
preservation. A task here that would trade one of them for speed brings the
trade to the owner.

Order: task 27 is independent and can start now; then task 23 with its
bootstrap costs, tasks 28 and 29, decisions D3 and D4, and tasks 30 and 31.
Tasks 21 and 22 are independent of this section, and tasks 24 to 26 keep
their own conditions; neither side waits for the other.

### 27. Rebuild the compiler with its own output (one session)

**Planned.** Independent. Issue #63.

Keep the compiler's source as data across swaps. Generation 1 is today's
`swap_all`; generation 2 is compiled by the swapped generation-1 compiler on
the SHEAR VM and installed; generation 3 compiles again. Record which
generation produced each installed chunk.

Done when: generations 2 and 3 agree with generation 1 and with the host
expansion over the compiler and the curated expressions; a test fails if a
generation-2 chunk came from the host-run compiler or from host lowering;
time and peak memory per generation are recorded.

### 28. Bootstrap boundary (one session)

**Planned.** Issue #64.

Every operation in `shear/operations.py` declares its status on four routes,
host lowering, host execution, SHEAR lowering and SHEAR-VM execution, as
supported, explicitly rejected or deferred. A test checks each declaration
against behaviour: a deferred operation fails explicitly, never by falling
back to the host. A new `docs/bootstrap.md` inventories the host services the
compiler workload uses (parsing, `define` and continuity inference, state and
identity derivation, canonicalization, activation, reflection, data
operations), each with its contract, implementation, whether the hosted
bootstrap permits it, and the test that covers it.

Done when: the matrix test passes and the inventory is written, as input to
D4.

### 29. Execution route for compiler-produced chunks (one session)

**Planned.** Issue #65. A spike for D3.

Compare the SHEAR VM with host execution of the SHEAR compiler's chunks as
derived artifacts of the nodes they compile, behind a verifier and with
recorded provenance. The second needs the compiler to see node identities
(self_hosting.md section 6) and keeps the source canonical, which the swap of
task 27 does not. Predictions are recorded before the run; one revision;
costs by task 23's method. If the route adds a machine boundary, weigh
extracting one run-context component from `machine.py` first (review
section 8).

Done when: the results and a recommendation are recorded and the owner
decides D3.

### 30. Hosted-bootstrap pipeline (handoff)

**Planned.** Issue #66. After D3 and D4.

Extend the SHEAR compiler to the subset D4 names, including the operations
above where the workload needs them; embedded `catch` and `raise` close the
follow-up of error_handling.md. One documented command runs source text
through host parsing and `define`, SHEAR lowering, and execution on D3's
route; an unsupported operation fails explicitly.

Done when: task 27's rebuild and the corpus run on this path, provenance
shows no host lowering for executed code, task 28's matrix is updated and
the costs are recorded.

### 31. Live evolution on the bootstrap route (handoff)

**Planned.** Issue #67. After task 30.

With every executed chunk produced by the SHEAR compiler: the
self-modification and error canaries of the corpus; a running image that
changes its program, compiles the candidate with its retained compiler,
trials and activates it with declared continuity and live data, and rejects
a bad candidate by the failure semantics; an old frame or closure across a
change; repeated updates with retirement under the declared lifetime policy.

Done when: these pass and update latency and retained states are recorded.
The hosted-bootstrap milestone is then met.
