# Roadmap

**Status: provisional.** The order of work after the code-as-graph spike
(PR #17, docs/spikes/code_as_graph.md on that branch). Tasks are done in
order unless marked independent; each one is a PR and follows CLAUDE.md.

## Workflow

**Decided.** A semi-automatic loop, driven from one planning chat:

1. **Plan.** The planning chat writes the task's plan and acceptance tests
   on a branch `task/<n>-<name>`. For handoff tasks it checks them against
   a throwaway prototype and a few planted bugs.
2. **Write.** A writer agent (a smaller model, started fresh in its own
   worktree) implements the plan and commits. For one-session tasks a
   larger model designs and implements together.
3. **Review.** A reviewer agent, fresh and not the writer, checks the work
   against the plan and CLAUDE.md, fixes small issues as separate commits,
   and reports anything larger.
4. **Check and publish.** The planning chat checks that the acceptance
   tests are unchanged, runs the suite, pushes, and opens a ready PR with
   anything that needs the owner.
5. **Merge.** The owner merges, or pushes back, and says so. The loop
   continues with the next task.

Tasks are marked **handoff** (the plan and tests are settled before any
code) or **one session** (the design comes out of writing the code). The
planning chat asks the owner only about decisions like D1; any other choice
is made, marked Provisional and named in the PR. Independent tasks may run
in parallel; the planning chat resolves `CHANGES.md` conflicts when
publishing. When the planning chat grows heavy, a new one starts from
CLAUDE.md and this roadmap.

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

## A. Foundations

### 1. Canary corpus, tier 1 (handoff, independent)

A library of small programs with expected results, in
`semiroh/examples/`. Every interpreter and representation must run them
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

Derive `StateID` from each entity's `VersionID` (cached per `Value`) plus
ownership, instead of re-serializing every entity's content. `StateID`
stays derived from content and cannot be supplied; only its hash input
changes.

Done when: equal content gives an equal `StateID` and different content a
different one (seeded property test); the spike's `COMPILE(12)` install on
graph form is no slower than on `lang.py`; the full suite passes.

### 3. Creation places entities under an owner (handoff)

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

`activate` and `trial` can target a single node, so hot swapping at the
language level has the same granularity as identity. This is the piece
the spike did not build.

Done when: a program replaces one subexpression of a running function, and
only that node's version changes.

### 6. Canary corpus, tier 2: data and higher order (handoff)

Add what task 1 found missing, probably: taking tuples apart, local
bindings, and applying a function value. Then add programs for map, fold
and sort, plus a canary that swaps the sort implementation between two
runs while the data stays in a cell.

Done when: the tier 2 programs run, and the list of missing features is
updated.

## C. The payoff

### 7. Incremental compilation (one session)

Lower graph form to an executable form (Python closures are enough). The
result is cached as a derived artifact keyed by node version, so after a
self-modification only changed nodes are lowered again. If this is not
simpler and more precise than re-pointing dependents per function, record
that per-node identity is not paying for itself.

### 8. A compiler pass that keeps continuity (one session)

For example, constant folding written as a graph transformation that
declares its merges. Optimised, hot-swapped code keeps a mapping to its
source nodes, which a test checks.

### 9. Self-hosting milestone (one session)

Write the lowering pass from task 7 in SEMIROH itself. A program then
recompiles and hot swaps part of itself with its own compiler.

## Later

- Text syntax, with a reconciler that turns an edited text into a
  transformation with continuity.
- Systems data: structs, arrays and references between cells, with layout
  changes handled by converters.
- Error handling inside the language, when a corpus program needs it.
- The program root (ownership_model.md §13), when modules or libraries
  need one.
