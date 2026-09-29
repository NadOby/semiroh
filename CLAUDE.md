# CLAUDE.md

Guidance for AI sessions working on SEMIROH. Read this first; read the docs it
points to only when the task touches them.

## What this is

SEMIROH is the skeleton of a systems programming language whose canonical
program is an immutable semantic graph, and whose programs carry their own
compiler and can modify themselves at runtime (Erlang-style hot loading in
spirit). `semiroh/` is an executable Python *reference model* of the semantic
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

- Work follows `docs/roadmap.md`: its task order and its plan, write,
  review, publish loop.
- Docs, tests, and code are three representations of one spec: change them
  together. Mark doc sections Decided / Provisional / Open.
- Check a proposal against the vision first; if existing code conflicts with
  it, say so rather than rationalize it.
- One coherent change per PR. Append an entry to `CHANGES.md` per PR. If two
  open branches both append to `CHANGES.md`, stack the later one on the
  earlier one to avoid conflicts.
- Never edit the owner's tests to fit new code without saying so; if a test
  encodes an old rule, rename it to what it now checks and call it out.

## Conventions

- Commits: one line, smart-commit style: starts with Add / Change / Fix /
  Remove and says exactly what was done. No body besides trailers.
- PR descriptions: short. No link to the AI session. If the environment
  appends a session-link footer, remove it by editing the description.
- Python, standard library only. Frozen dataclasses for semantic records.

## Testing

- Run: `python3 -m unittest discover` (CI runs the same on Python 3.12).
- Every test module ends with `if __name__ == "__main__": unittest.main()`,
  so `python3 -m tests.test_x` runs one module.
- Property tests use seeded `random.Random(seed)` with `subTest(seed=...)`, so
  failures are reproducible. No third-party test libraries.
- A new regression test must fail on the old code. For a property test,
  plant a plausible bug and confirm the property catches it.
- Test semantic contracts, not incidental implementation details.
- `SEMIROH_MUTATE=1 python3 -m tests.test_mutation` plants seeded bugs in
  the model and runs the suite on each (a few minutes); a survivor is a gap
  in the tests or a listed equivalent (`EQUIVALENT` in that module).

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
- `lang.py`, `bytecode.py`: the language layer. `lang.py` keeps code as
  graph form (`load`, `define`, `function_at`; `define` infers what an
  edit keeps and can create, remove and relink functions); `bytecode.py` lowers each
  node to a chunk, kept with the node's `Value`, and runs chunks on a
  virtual machine with explicit stacks. `lang.run` calls it.
- `fold.py`: constant folding as a graph transformation that declares its
  merges (`fold_constants`, `sources_of`).
- `continuity.py`: the continuity corpus: cases with expected continuity
  per operation (`CASES`, `check`); a `gap` case would record inference
  still missing; all 21 hold (docs/continuity_corpus.md).
- `examples/ledger.py`: executable measurements for the graph ledger:
  incremental lowering counts, continuity-corpus identity claims and fold
  provenance (`docs/graph_ledger.md`).
- `syntax.py`: text syntax version 0 over `lang.py`: `parse` (text to the
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
