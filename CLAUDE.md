# CLAUDE.md

Guidance for AI sessions working on SHEAR. Read this first; read the docs it
points to only when the task touches them.

## What this is

SHEAR is the skeleton of a systems programming language whose canonical
program is an immutable semantic graph, and whose programs carry their own
compiler and can modify themselves at runtime (Erlang-style hot loading in
spirit). `shear/` is an executable Python *reference model* of the semantic
rules, not the language implementation. `README.md` is the overview; `docs/`
holds one spec per concept; `CHANGES.md` is the architectural log.

## Vision (guidance, not dogma)

- The semantic graph is the source of truth. It generalizes a hypergraph:
  there are no nodes and edges, only entities; a relation is an entity.
- Semantic state is immutable. Changes produce new states; identity never
  depends on history or provenance.
- Runtime is an interpretation of semantic state. Runtime mutation (cell
  content) never changes semantic identity.
- Transformations are explicit: continuity, disappearance, creation, splits,
  merges, conversions. Ambiguity is rejected, never silently resolved.
- Constraints are semantic values; executable evaluators are separate and
  referenced by name.
- Be pragmatic, not pure: prefer the smallest change that works, defer design
  decisions until a real program needs them, and change the vision where it
  contradicts reality.

## Workflow

- Work follows `docs/roadmap.md`: its task order, and the five task roles
  its Workflow section defines: Plan, Execute, Review, Resolve and Publish.
  "Plan task N", "Execute task N", "Review task N", "Resolve task N" and
  "Publish task N" are sufficient instructions, because the roadmap defines
  each role's contract; read it when given one.
- Plan, Execute and Review normally run in separate fresh chats. The context
  or model that implemented a change is never its sole certifier: Review is
  independent of Execute, and fixes for its findings belong to Resolve, not
  to Review. A different model family can add independence but is optional;
  role separation and fresh context are mandatory.
- No background agents.
- Work is tracked in GitHub issues: every roadmap task and every other change
  has an issue before work starts, and a follow-up found while working becomes
  a `follow-up` issue, not a note in a file or a chat. The roadmap's Workflow
  section says how the roles use them.
- `handoff.md` is a compact checkpoint of state and claims (task, role,
  decisions, next steps), not a log, not an authority and not verification
  evidence: check a claim against the repository before relying on it. It
  names the task's issue. Keep it short and current.
- Review preserves epistemic labels: Decided / Provisional / Open in
  specifications, and verified defect / limitation / hypothesis /
  documentation drift in its findings.
- Docs, tests, and code are three representations of one spec: change them
  together. Mark doc sections Decided / Provisional / Open where a design
  decision actually has that status.
- Check a proposal against the vision first; if existing code conflicts with
  it, say so rather than rationalize it.
- One coherent change per PR. Append an entry to `CHANGES.md` per PR. If two
  open branches both append to `CHANGES.md`, stack the later one on the
  earlier one to avoid conflicts.
- Never edit the owner's tests to fit new code without saying so; if a test
  encodes an old rule, rename it to what it now checks and call it out.
- AI sessions should not limit themselves to the immediate patch when the work
  exposes a concrete architectural or process weakness. Surface the smallest
  justified improvement and explain why it follows from the evidence.
- Distinguish changes required for the current task from useful architectural
  or process follow-ups so scope remains explicit. Non-blocking follow-ups
  stay separate from the current task's defects.

## Conventions

- Commits: one line in smart-commit style: the issue key `GH-<n>` first, then
  a verb (Add / Change / Fix / Remove) and exactly what was done, for example
  `GH-50 Change the workflow to five task roles`. Write `GH-<n>`, not `#<n>`:
  GitHub links both, but git drops a line starting with `#` as a comment
  whenever a message is edited in an editor. No body besides trailers.
- PR descriptions: short, with `Closes #<n>` for each issue the PR completes,
  so that merging closes it. No link to the AI session. If the environment
  appends a session-link footer, remove it by editing the description.
- Prefer extending the existing workflow (a job, step or dispatch input such
  as `mutation_shards`) over adding workflows or throwaway branches. Remove a
  workflow and its runs once its purpose ends.
- Python, standard library only. Frozen dataclasses for semantic records.
- Around 500 lines is a review threshold for source, test, and configuration
  files, not a hard limit. When a file approaches or exceeds it, consider
  splitting by coherent responsibility or subdomain. Keep it monolithic when
  that is clearer; do not split mechanically just to satisfy a line count.
- Large declarative catalogs should normally separate executable loading and
  validation logic from serialized review data when that reduces churn and
  makes review boundaries clearer. Prefer standard-library-readable formats
  and keep validation fail-closed.

## Testing

- Run the complete local suite with:

      python3 -m unittest discover

- The deterministic test modules are partitioned into semantic lanes defined
  by `tests/lanes.py`. Run one lane with:

      python3 -m tests.lanes <lane>

  CI runs every lane in one job on Python 3.12, each lane as its own process,
  as many at a time as the runner has CPUs, and prints a per-lane result and
  timing table:

      python3 -m tests.lanes --all

- Every ordinary `tests/test_*.py` module must appear in exactly one lane in
  `tests/lanes.py`. Adding a test module without assigning it to a lane, listing
  it twice, or leaving a stale lane entry makes CI fail.
- Every test module ends with `if __name__ == "__main__": unittest.main()`,
  so `python3 -m tests.test_x` runs one module.
- Generated/property tests use deterministic seeds. Shared generated-test
  infrastructure lives in `tests/generation.py`.
- `SHEAR_SEED=<seed>` replays a generated case. A comma-separated list
  replays several explicit seeds. An explicit seed overrides the generated
  case budget.
- `SHEAR_CASES=<n>` changes the deterministic generated-case budget for
  participating tests. Unset, empty, or `0` means use each test's ordinary
  default budget; a positive integer selects the heavy budget.
- Property tests use `random.Random(seed)` with `subTest(seed=...)`, so
  failures are reproducible. No third-party test libraries.
- A new regression test must fail on the old code. For a property test,
  plant a plausible bug and confirm the property catches it.
- Test semantic contracts, not incidental implementation details.
- CI compares the language layer's golden records (corpus programs,
  continuity cases, public names) with the merge base; nothing is stored or
  re-recorded. `python3 -m tests.golden --against main` runs the same check
  locally. A record may change only through a `<group>/<name>` line the
  branch adds to `tests/golden_changes.txt`, written by Plan; a change to the
  recorder in `tests/golden.py` needs a `*` line instead.
- Mutation target policy and explicit omissions live in
  `tests/mutation_catalog.py`. Reviewed survivor classifications and exact
  target-source pins live in per-target TOML files under
  `tests/mutation_catalog_data/`; its manifest pins the mutation-engine version
  and inventories every target with classified survivors. The Python loader
  validates that serialized catalog fail-closed.
- A survivor classification is valid only for the exact pinned target-source
  version and pinned mutation-engine version under which it was reviewed. Any
  edit to a target file invalidates all survivor classifications for that file
  until explicit re-review and repinning; any edit to `tests/mutation.py`
  invalidates the survivor catalog as a whole until explicit re-review and
  repinning.
- Run a seeded mutation sample with, for example:

      SHEAR_MUTATE=1 SHEAR_MUTATE_SEED=1 \
          python3 -m tests.test_mutation

  `SHEAR_MUTATE` is the number of mutants sampled per target. A survivor may
  be catalogued only when it is reviewed as semantically equivalent or
  intentionally unspecified, with a reason. A semantic test gap receives a
  regression test and must not be whitelisted as a survivor.
- Mutation work is selected before sharding. The complete selected set is
  deterministically shuffled from `SHEAR_MUTATE_SEED`, then individual
  mutants are distributed round-robin across `SHEAR_MUTATE_SHARDS`.
  Changing the shard count must not change the selected mutation set, and shard
  sizes differ by at most one mutant.
- The mutation subprocess semantic oracle is centralized in
  `tests/mutation_oracle.py`. The ordinary `mutation` lane contains harness,
  catalog and infrastructure checks and remains mandatory CI, but it is
  excluded from mutation-kill decisions. Baseline and mutant subprocesses must
  use the same semantic oracle command.
- Mutation campaigns emit flushed human progress plus JSONL evidence. Set
  `SHEAR_MUTATION_REPORT=<path>` to choose the report path. Each report pins
  the mutation engine and target sources, records campaign inputs and exact
  selected keys, records every mutant outcome, and ends with reconciled counts
  and diagnostic timing summaries.
- Replay one reported mutation directly from its key and pins:

      python3 -m tests.mutation_campaign replay \
          --key-json '["shear/example.py","constant","value = False",0]' \
          --source-blob <source-blob> \
          --engine-blob <engine-blob>

- After a large failed campaign, replay only the previously unclassified
  survivors from one or more downloaded shard reports:

      python3 -m tests.mutation_campaign replay-failures \
          mutation-report-*.jsonl

  Report-driven replay validates completed reports and their recorded pins,
  runs the semantic baseline once, and then executes only the recorded
  unclassified survivors. It does not reconstruct their original seed, batch,
  or shard.
- Larger generated and mutation campaigns are available through manual
  workflow dispatch; ordinary PR CI keeps the deterministic default budgets.
  Mutation campaign shards publish their JSONL evidence as workflow artifacts,
  including when a shard fails after finding unclassified survivors.

## Model map

- `canonical.py`: canonical content and serialization; identity is derived
  from canonical bytes. `SemanticRecord` lets model records be values.
- `values.py`, `state.py`: `Value`, immutable `State` (values + ownership);
  `StateID` is derived from content and cannot be supplied.
- `transforms.py`: `TransformationDefinition` (changes, mappings, named
  conversions) → `TransformResult`. Mapped sources are removed unless they
  are mapping destinations; changing a removed entity is rejected; relation
  endpoints and ownership follow declared continuity. `rebase` combines
  two results of one state when their `touched` sets are disjoint, else
  `TransformationConflict`.
- `matching.py`: continuity inference for `define` (`match`, `shapes`):
  unique unchanged subtrees keep their identity, largest first, then the
  edited position by kind (docs/continuity_inference.md).
- `relations.py`: `Relation(kind, roles, payload)` entities; endpoints must
  exist; a constraint payload makes a constraint relation. Kinds have no
  core meaning.
- `constraints.py`: three-valued semantic constraints (strong Kleene),
  `Evaluator` behind `External(name)`, step budgets.
- `operations.py`: the one table of operation shapes (arity, code roles,
  ordered roles, positional build); `lang`, `continuity` and `syntax` derive
  from it, and `tests/test_operations.py` checks every implementation agrees.
- `lang.py`, `bytecode.py`, `machine.py`: the language layer. `lang.py` keeps
  code as graph form (`load`, `define`, `function_at`; `define` infers what an
  edit keeps and can create, remove and relink functions); `bytecode.py` lowers
  each node to a chunk, kept with the node's `Value`; `machine.py` runs chunks
  with explicit stacks. Dependencies point one way: machine → bytecode →
  lang, with `lang.run` the one lazy call into the machine.
- `fold.py`: constant folding as a graph transformation that declares its
  merges (`fold_constants`, `sources_of`).
- `continuity.py`: the continuity corpus: cases with expected continuity
  per operation (`CASES`, `check`); a `gap` case would record inference
  still missing; all 21 hold (docs/continuity_corpus.md).
- `examples/ledger.py`: executable measurements for the graph ledger:
  incremental lowering counts, continuity-corpus identity claims and fold
  provenance (`docs/graph_ledger.md`).
- `syntax/`: text syntax version 0 over `lang.py`, split into `lexer`,
  `parser`, `printer` and shared `forms`: `parse` (text to the
  input format, over an optional base), `render` and `render_program` (graph
  form to text, `raw(...)` for what the syntax cannot write). Import-only.
- `reconcile.py`: edited complete source to a graph transformation
  (`reconcile`): parses and resolves the edited program, preserves
  top-level identity for declarations that keep their name, delegates
  code-node continuity to `lang.define`, treats a bare top-level rename as
  remove plus create, and rejects cell declaration edits until migration
  semantics are specified (`docs/name_resolution.md`).
- `cells.py`, `runtime.py`: `CellDeclaration(constraint, initial)`;
  `Runtime` holds cell content outside `StateID`, checks constraints
  (anything but Satisfied rejects), activates transformation results
  atomically (two-version bound, holds, retirement), rebases a result
  from an earlier active state over those activated since, and runs trials.
