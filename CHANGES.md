# Development Changelog

This is a retroactive architectural development log. It records significant
semantic decisions and milestones rather than individual commits.

## 2026-09

### Semantic identity model

- Established the semantic graph as the canonical program representation.
- Defined semantic values as the fundamental meaningful units of the model.
- Separated EntityID, VersionID, StateID, and runtime identity.
- Distinguished identity from semantic equality.
- Made semantic states immutable.
- Defined StateID from exact semantic state content rather than history,
  provenance, or transformation mappings.
- Added canonical serialization as the basis for semantic identity.
- Made references state-relative and version-pinned.
- Added explicit cross-state reference transfer.
- Added explicit entity mappings for identity continuity across transformations.
- Separated transformation mappings and provenance from state identity.
- Distinguished explicit rebinding from identity-preserving reference transfer.

### Semantic transformations

- Established transformations as functions producing new immutable states.
- Allowed explicit identity mappings across transformations.
- Allowed identity continuity to represent renaming and other structural
  transformations without implying semantic equality.
- Established explicit produce-versus-activate semantics as a design direction.

### Immutability

- Made semantic values immutable through canonicalized content.
- Made state value collections immutable.
- Established immutable replacement rather than implicit mutation as the default
  state evolution mechanism.

### Testing and executable model

- Established the Python implementation as the executable semantic reference
  model.
- Added tests for identity, equality, references, state identity,
  transformations, canonical serialization, and immutability.
- Added GitHub Actions validation for the semantic model.

### Ownership

- Began separating ownership from ordinary semantic references.
- Ownership is treated as a semantic state relation.
- Ownership is directional and forms a forest.
- An entity may have at most one owner.
- Ordinary references may form arbitrary cycles independently of ownership.
- Destruction is defined as an immutable state transformation recursively
  removing an owned subtree.

## Future

Architectural decisions will be added here when they become sufficiently
stable to form part of the SEMIROH semantic model.

## 2026-09-20

### Session: Repository refactor

- Refactored the executable test suite from a monolithic test module into
  thematic `unittest` modules under `tests/`.
- Separated tests by semantic concern: identity, canonicalization, references,
  state, ownership, lifecycle, transformations, and continuity.
- Switched the test suite to standard `unittest` discovery.
- Updated GitHub Actions validation to discover tests from the `tests/` package.
- Removed the obsolete root-level test module after its tests were migrated.
- Removed the obsolete `identity_model.py` compatibility facade now that the
  package implementation is the direct semantic reference model.
- Preserved the existing semantic behavior while restructuring the executable
  test architecture.
- Established the development changelog as append-only for subsequent entries.

### Transformation model specification

- Defined transformations as explicit transitions between immutable semantic
  states.
- Defined explicit entity continuity as a zero/one/many relation supporting
  disappearance, creation, split, merge, and many-to-many mappings.
- Distinguished an absent mapping from an explicit mapping to zero
  destinations.
- Defined state-local, one-step reference transfer with validation of
  `StateID`, entity existence, and exact `VersionID`.
- Defined explicit distinction between continuity-preserving reference
  transfer and destination-state rebinding.
- Established that transformation mappings and provenance do not contribute to
  `StateID`.
- Established canonical ordering and validation requirements for transition
  mappings.
- Separated ownership transformation semantics from entity continuity.
- Documented composition and reversibility as distinct concerns rather than
  implicit properties of individual transformations.
- Added `docs/transformation_model.md` as the authoritative specification for
  the current transformation model.
- Marked unresolved transformation semantics explicitly rather than
  prematurely defining them through implementation or tests.

### 2026-09-20 – Transformation composition specification tests

Added `tests/test_transformation_composition.py`.

These tests intentionally document expected composition behavior
without introducing composition implementation.

Covered scenarios:

- continuity chain
- disappearance
- split
- split-merge normalization
- preservation vs continuity
- identity transformation
- associativity

The file acts as an executable specification anchor for future
composition implementation.

### 2026-09-20 – Composition API specification

Added `docs/transformation_composition_api.md`.

Introduced explicit composition result categories:

- Known continuity
- Known disappearance
- Unknown

Unknown represents insufficient continuity information and is distinct
from both continuity and disappearance.

Composition APIs are specified in terms of these three result classes.

## 2026-09-28

### Model/specification divergences fixed

- Transformation application now decides the presence of explicitly mapped
  sources by the mappings alone: a mapped source remains present if and only
  if it is itself a destination of some mapping, and explicit disappearance
  is never overridden. Swap (`A → B`, `B → A`) and shift (`A → B`, `B → C`)
  mappings are now applicable; previously they were rejected.
- Destination validation runs against the resulting destination state, so a
  mapping into an entity that is explicitly mapped to zero destinations is
  rejected as a missing destination.
- Documented that a value change for a source removed by the mappings has no
  effect, generalizing the existing disappearance-precedence rule. The rule
  is marked provisional: rejecting such contradictory definitions is the
  expected future direction.
- Transformations without explicit destination ownership now remove only
  ownership edges involving entities absent from the destination. Explicitly
  mapped entities that remain present (such as `A → A`) keep their ownership,
  as the transformation and ownership models already required.
- Canonicalization is idempotent. Already-canonical content is recognised
  and not wrapped again, so rebuilding a value from existing content (for
  example through `with_changes` or `dataclasses.replace`) no longer changes
  its identity. Canonical serializations, and therefore all existing
  `VersionID` and `StateID` values, are unchanged.
- `Value` equality, hashing and `semantic_equal` use canonical serialization,
  so `True` and `1` are distinct values, consistent with their distinct
  `VersionID`s.
- Owners listed with no children no longer affect state identity; absent
  entities are still rejected.
- Ownership cycle detection is iterative and supports deep ownership chains.
- `make_reference` rejects a value belonging to a different entity.

### Testing

- Added regression tests for each fix in the thematic test modules.
- Added seeded property tests (`tests/test_properties.py`) for
  canonicalization, ownership normalization, application rules, associativity
  of composition, and agreement between chained reference transfer and
  continuity composition.

### Self-modification direction

- Stated the motivating goal in the README: every SEMIROH program carries its
  own compiler and retains the ability to modify itself by producing,
  validating, and activating a new version of its program state.
- Made the embedded compiler part of every program image and added it to the
  high-value invariants.
- Established that a mutable cell is versioned semantic state while its
  current content is runtime state that does not contribute to `StateID`.
- Adopted Erlang-style hot code loading, in spirit, as the direction for
  runtime activation: live state, including mutable cell content, is carried
  across activation along explicit continuity mappings, optionally through a
  conversion function.
- Recorded runtime activation, embedded compiler footprint, and platforms
  that restrict runtime code generation as open design areas.

### Activation model

- Added `docs/activation_model.md`, separating decided, proposed, and open
  parts of runtime activation: program versus runtime state, atomic
  activation from a transformation result, capability-governed activation,
  Erlang-style transfer of mutable cell content along continuity, handling
  of code in flight and of references, and lifetime of superseded versions.
- Added runtime self-modification prior art to `priors.md`.
- Accepted the proposed activation rules: cardinality-based state transfer,
  rejection of live cells without declared continuity, pinning of
  untransferable references by default, validation before an atomic switch,
  and rollback as a new activation.
- Decided to retire superseded versions through the ownership model: a
  version owns its code and untransferred resources and is destroyed once
  nothing holds it. Holds are coarse, runtime-internal, per-version records,
  deliberately not a general borrowing system.
- Decided on a bound of two running versions per runtime (active and previous),
  with speculative candidates exercised in isolated runtimes rather than as
  additional running versions.
- Decided that a new activation is rejected by default while the previous
  version is still held; waiting or terminating the holders are explicit
  alternatives.

### Review follow-ups

- `State` derives `StateID` during construction; an identity can no longer
  be supplied by the caller, and direct construction performs the same
  validation as `State.create()`.
- `compose()` rejects inputs other than transformation definitions and
  composition results, as the composition API specifies.
- `rebind_reference()` documents that the original reference is neither
  validated nor consulted, and delegates to `State.reference()`.
- Removed the placeholder composition specification tests, superseded by
  the implemented composition tests.
- Updated the constraint model's implementation status.

### Executable activation model, stage 1

- Added `CellDeclaration`: a mutable cell's type and initializer are values
  in program state and contribute to `StateID`.
- Added `SemanticRecord`, a base for model records that define their own
  tagged canonical node.
- Added `Runtime`: the runtime root owns loaded versions, each `Version` owns
  its cell content, and cell reads and writes never change program state.
- Added runtime-internal holds on versions from simulated frames and kept
  references.

### Semantic constraints

- Specified three-valued composition as strong Kleene logic in the
  constraint model.
- Added semantic constraints with canonical identity: `IsKind`, `IntRange`,
  `Length`, `OneOf`, `AllOf`, `AnyOf`, `Not`, and `External`. Constraints can
  appear in program state.
- Kept the executable predicate wrapper as an evaluator that `External`
  constraints reference by name; a missing evaluator yields `Unknown`.
- Added a computation-step budget; exhausting it yields `Unknown`.
- Decided that a cell write whose constraint evaluates to `Unknown` is
  rejected, like activation; this applies once cells declare constraints.
- Made executable evaluators always receive canonical content, whether they
  are called directly or through `External`.
- Made `IsKind` accept every kind the model produces, including `cell` and
  `constraint`.
- Renamed the executable predicate wrapper `Constraint` to `Evaluator` and
  `SemanticConstraint` to `Constraint`, matching the specification's use of
  the term.
- Documented that the step budget does not bound evaluators and that an
  evaluator failure propagates rather than becoming `Unknown`.

### Cell constraints

- A `CellDeclaration` declares a constraint instead of a type name; the
  constraint is the cell's type.
- Program state stays pure data: declaring a cell does not evaluate its
  constraint. A runtime checks each cell's initial content when it loads a
  version, and checks every write, using its evaluation context.
- Only `Satisfied` content is accepted; `Violated` and `Unknown` are both
  rejected with `CellContentRejected`, and a rejected write leaves the cell
  unchanged.

### Executable activation

- Transformation definitions and results carry named conversions, keyed by
  destination cell (provisional). Executable `Converter`s are supplied at
  activation, like evaluators for External constraints.
- Added `Runtime.activate`: staged and atomic. Cell content crosses along
  declared continuity; one-to-one content transfers unchanged when it
  satisfies the destination cell's constraint, and otherwise needs a
  conversion (provisional rule). Splits and merges always need conversions.
  Every content reaching a cell is checked, and anything but `Satisfied`
  rejects the activation.
- A cell without declared continuity, or continuing as a non-cell, rejects
  the activation. A bare state has unknown continuity.
- Kept references transfer along unique continuations or stay pinned to the
  previous version; a strict policy rejects instead.
- Activation is rejected while the previous version is held. A superseded
  version is retired, destroying its cell content, when its last hold is
  released.

### Trial runs

- Recorded as decided: a cell continuing as a non-cell rejects activation; a
  cell fed only by non-cells starts from its initializer and a conversion
  for it is rejected; a declared one-to-one conversion is always used; a
  frame keeps executing in the version it started in.
- Added `Runtime.trial`: a candidate runs in an isolated runtime with its own
  root. Cell content is staged exactly as activation would stage it, with
  the same converters and checks, so a trial is rejected whenever the
  activation would be. The main runtime is unchanged and its two-version
  bound does not apply; holds are not copied.

### Relation model

- Added `docs/relation_model.md` proposing the first concrete graph
  structure: relations are entities whose values are relation records with
  a kind, named roles, and an optional payload. Endpoints must be present in
  the same state.
- Decided that raw `EntityID`s in ordinary values are untracked data; that
  relations follow declared continuity across transformations and are never
  removed implicitly; and that constraint relations are evaluated over a
  role map in the runtime, starting with `Role` and `External`.

### Relations, stage 1

- Recorded the remaining relation model proposals as decided, and clarified
  that every mapped endpoint follows its mapping, even when its entity is
  still present, so relations stay correct across swaps and shifts.
- Added `Relation` records with endpoint integrity in state construction:
  a relation with an absent endpoint cannot exist, and `destroy` fails when a
  relation outside the destroyed subtree points into it.
- Applying a transformation rewrites mapped endpoints of unchanged
  relations, and rejects endpoints that disappear or split unless the
  relation is changed or removed explicitly. Following an endpoint does not
  declare the relation's own continuity.
- Added `relation_index`, a derived index from entity to relation and role.

### Constraint relations

- Added `Role(name, constraint)`, projecting into the role map that is the
  subject of a constraint relation.
- A relation whose payload is a constraint is a constraint relation; its kind
  keeps no built-in meaning.
- A runtime evaluates constraint relations when a version loads, when a
  write changes one of their endpoint cells, and against the staged content
  of activation and trial runs. Anything but `Satisfied` rejects, and the
  runtime stays unchanged.

### Vision conflict fixes

- A definition that changes an entity and also removes it through its
  mappings is contradictory and is rejected when created. The earlier rule,
  that the change was silently dropped, is reversed.
- Ownership edges follow declared continuity when a transformation does not
  supply destination ownership: renamed, merged, swapped, or shifted owners
  and children keep their place in the forest. No remaining entity changes
  owner implicitly: an owner disappearing or splitting while its child
  remains, or a child splitting, is rejected. This reverses the rule that
  continuity mappings never modify ownership, which silently orphaned the
  children of a renamed owner.
- Transformation results list every relation whose endpoints followed
  continuity (`RelationRewrite`), checked against the source and destination
  states.
- Stated that the semantic graph generalizes a hypergraph: there are no
  nodes and edges, only entities, and a relation is itself an entity.
- Deferred until the first program implementations need them: how ownership
  becomes part of the graph, whether deletion and disappearance are one
  operation, the root of the ownership forest, and how creation places an
  entity under its owner.

### First program

- Added `semiroh/lang.py`: a tiny expression language interpreted directly
  over semantic state (docs/first_program.md), as a layer on top of the core
  model rather than part of it. `Function(params, body)` is a semantic
  record whose body is a plain tuple expression tree; functions name the
  functions and cells they use through link names resolved via their own
  `links` relation, never through raw `EntityID`s, so renaming a linked
  function or cell follows declared continuity instead of changing the
  function's body.
- `run(runtime, entry, *args)` evaluates a function under a `Runtime`: every
  call, including the entry, holds a frame for its duration and releases it
  on return or failure, `read`/`write` go through the runtime so cell and
  relation constraints apply and their errors (`CellContentRejected`, and
  so on) propagate unchanged, and running itself never changes program state
  or `StateID`. `LanguageError` covers the language's own mistakes: unknown
  operations and link names, wrong argument counts, calling a non-function,
  reading or writing a non-cell, and operands of the wrong kind (`bool` is
  never `int`).
- Self-modification stays entirely host-driven, as scoped: the host produces
  a new program state with an ordinary transformation and activates it: the
  acceptance tests cover a behaviour change, a rename that keeps callers
  working through their links relation, and a rejected activation that
  leaves the running program alone.
- Ownership turned out to be unnecessary for this program, exactly as
  section 2 anticipated: none of ownership_model.md §13's deferred questions
  needed an answer (first_program.md section 8).

### Metaprogramming

- Implemented `quote` and `unquote` for constructing expression trees with
  evaluated holes.
- Implemented `function`, which builds `Function` values at run time; they
  pass through ordinary values and cells.
- Implemented `activate` as capability-gated self-modification through the
  existing transformation and atomic runtime activation machinery.
- Kept the semantic core unchanged: self-modification declares identity
  continuity for every existing entity and changes only the selected
  function values.
- Provisionally, the language uses version coexistence: the frame running
  an activation continues in its starting version, while subsequent linked
  calls enter the active version. A second activation in the same run is
  rejected by the two-version bound.
- Added unit coverage for all new operations, malformed operands, activation
  check ordering, atomicity, canonical function values, cell-content
  preservation, and a seeded quotation property.

### Trials in the language

- Implemented `trial`, which exercises a candidate against a call in an
  isolated runtime (`Runtime.trial`) before a program decides whether to
  `activate` it; the real runtime's state, cells and holds are never
  touched.
- Shared the link/value pair checks and the identity-mapped transformation
  between `activate` and `trial` in one helper, and moved the active-state
  read after operand evaluation for both, so a pair value that itself
  activates is trialled or activated against the active state after
  evaluation, not a stale one.
- Code running under trial gets no activation capability, so it cannot
  `activate` or `trial` itself; a rejected candidate or a failure in the
  call propagates unchanged and leaves the real program alone.
- Trials are not limited by the two-version bound: a run may trial any
  number of candidates, before or after its one activation.
- Added unit coverage for `trial`'s `LanguageError` cases, the order of
  checks before the capability, a zero-pair trial run in isolation, and a
  trial whose own pair value activates, confirming the transformation
  starts from the active state after evaluation.

### Roadmap

- Added `docs/roadmap.md`: the order of work after the code-as-graph spike,
  as tasks, and the semi-automatic workflow (plan, writer agent, reviewer
  agent, check, merge) that carries them out.
- Decided D1: graph form is canonical; tuple bodies with links become an
  input format. The spike's hybrid recommendation rested on a `StateID`
  cost that task 2 removes.
- Tasks: a canary corpus of small programs, a `StateID` derived from cached
  `VersionID`s, and creation that places entities under an owner; then
  adopting graph form, node-level self-modification, a second corpus tier,
  incremental compilation, a compiler pass that keeps continuity, and
  self-hosting.

### Cheap StateID

- Changed `StateID` derivation to hash each entity's `VersionID` together
  with the ownership relation, instead of re-serializing every entity's
  content on every state construction (docs/state_model.md section 4).
- Cached `VersionID` on `Value` itself, derived once on first use and kept
  with the value; since a fresh `Value` never starts with a cached
  identity, an entity a transformation carries forward unchanged reuses
  its cached `VersionID` for free, while a changed entity gets a fresh
  one from its new content.
- The cost of deriving a new state's identity no longer depends on the
  size of content a transformation leaves unchanged, only on the number
  of entities.

### Canary corpus

- Added `semiroh/examples/`, implementing the canary corpus (docs/corpus.md):
  `Raises`, `Step`, `Example`, `Wanted`, `ExampleFailed`, and `play`, plus
  thirteen tier-1 programs across recursion, control, side effects, and
  self-modification, one module per tag.
- `gcd` uses subtraction-based Euclid and the Collatz example builds its own
  recursive even/odd test and halving, since the language has only `add`,
  `sub` and `mul` and no modulo or division operator.
- Recorded four wanted programs the language cannot express yet: insertion
  sort and map/fold need runtime tuple decomposition and, for map/fold, a
  way to call a function value directly rather than through a static link
  name; local variables need a `let`/local-binding form; and a loop
  expressed as recursion hits the reference interpreter's Python recursion
  limit long before any conceptual program-level limit (measured: the
  `sum_to_n` example succeeds up to `n = 196` and raises `RecursionError`
  at `n = 197`, under the default limit of 1000).

### Placements and ended subtrees

- `TransformationDefinition.create` and `transform_with_mapping` take
  `placements`, `created entity -> owner`, stored canonically like
  `conversions` (ownership_model.md section 10). A placed entity must not
  be a mapping destination (rejected at `create`); `apply` rejects one that
  exists in the source state, is absent from the destination, or whose
  owner is absent from the destination, all with `OwnershipError`.
  Placements and explicit `ownership=` are mutually exclusive
  (`ValueError`); placed edges are appended after the owner's existing
  children, and a placement cycle is caught by the usual forest check.
- Mapping an owner to `()` now ends its owned subtree (ownership_model.md
  section 7): every entity in it, computed from the source ownership, that
  the definition does not name as a mapping source or destination
  disappears too, recursively, stopping at a named entity. `apply` records
  each cascaded entity in the result as a mapping to nothing, drops its
  ownership edge, and rejects a `changes` entry for it with `ValueError`.
  The cascade runs whether or not explicit ownership is supplied.
- Updated the property-test oracles in `tests/test_properties.py`
  (`followed_ownership`, `test_apply_follows_the_presence_and_validity_rules`,
  `apply_stating_ownership`) to compute the cascaded set independently from
  source ownership and the definition's mappings, since they encoded the
  older rule that an owner's disappearance left unnamed children in place.
- Renamed `tests/test_transform_mapping.py`'s
  `test_owner_disappearing_while_children_remain_is_rejected` to
  `test_named_children_of_a_disappearing_owner_need_explicit_ownership` and
  named its previously-unnamed `child`/`sibling` in the mapping: unnamed
  children now disappear with their owner instead of being rejected, so the
  case that rule now checks is a named, kept child changing owner.

### Graph form

- `semiroh/lang.py` stores and runs code as graph form (roadmap.md D1, task
  4; docs/graph_form.md). A function keeps its `EntityID` and holds a
  `definition` relation: its body root (`body`), its link table (one
  `link:<name>` role per link) and `{"params", "generation"}`. Each
  expression node is a relation owned directly by its function, named
  `<function>/<generation>.<index>` in preorder, never reusing an existing
  name. Calls, reads and writes name targets by role; malformed code becomes
  an `invalid` node that raises the same `LanguageError` when run.
- `load` converts the input format (links relations disappear),
  `function_at` collapses a function back, and `define` replaces whole
  bodies with placements and old nodes mapped to `()`. `activate` and
  `trial` build their transformation with `define`. `play` loads corpus
  programs, which stay in the input format.
- Differential check before removing the tuple-body interpreter: the corpus
  (41 steps) and 4000 seeded random programs (16,000 steps, about 3,100
  succeeding) gave the same results, exception types and messages, cells
  and collapsed functions on both; main's acceptance suites passed on the
  old interpreter and the edited ones on graph form. Deviations: records
  inside a `quote` template are copied as atoms (the old interpreter walked
  their canonical encoding), and `sum_to_n` recurses one call deeper
  (`docs/corpus.md`, `missing.py`).
- Core: a relation may have no roles (relation_model.md §2), for leaf
  nodes. `tests/test_relations.py`'s `test_invalid_records_are_rejected`
  loses its `("r", {})` case, which encoded the old rule, and gains a
  non-mapping case.
- Core, **Provisional**: a constraint relation endpoint that owns entities
  contributes `{"value": ..., "owned": {child: ...}}`, and a cell write
  re-evaluates relations over the cell's owners (relation_model.md §7). A
  function's value no longer holds its code, and without this the program
  guards in `test_program_constraints_guard_self_modification` and
  `test_program_constraints_reject_a_candidate` stop rejecting anything.
  New coverage in `tests/test_constraint_relations.py`'s
  `OwnedSubtreeTests` (additions only; no existing assertion changed).
- Core, performance: `check_relation_endpoints` looks endpoints up instead
  of hashing every entity once per relation (it was quadratic), and
  `relation_of` keeps the decoded record with the value. COMPILE(12)
  install: 2.26 ms on main, 4.25 ms on graph form before these two, 2.55
  ms after; corpus 28.4 ms on main, 25.0 ms here; `power(2)` after it 108
  vs 31 µs per call.
- Edited existing tests, program construction and representation only:
  `test_first_program.py` (`program`, `test_language_errors` load;
  `test_program_changes_behaviour_by_activation` uses `define`;
  `test_renamed_function_keeps_callers_working` copies `double`'s
  definition and checks `quad`'s call nodes instead of its links relation),
  `test_metaprogramming.py` (`program` loads, `installed` uses
  `function_at`), `test_language_trials.py` (`program` loads),
  `test_lang.py` (`make_state` loads; `test_activate_changes_code_atomically`
  and `test_canonical_function_argument_can_activate` use `function_at`).
  No test was renamed; `test_graph_form.py` and `test_corpus.py` are
  unchanged.

### Test module entry points

- Added `if __name__ == "__main__": unittest.main()` to the 12 test modules
  that lacked it, so every module runs alone with `python3 -m tests.test_x`;
  CLAUDE.md now asks for it in new test modules.

### Node edits

- `semiroh/lang.py` implements node-level edits (roadmap.md task 5;
  docs/graph_form.md §9). `("label", name, e)` marks `e`'s node with a
  unique, transparent name, kept in a function's definition (a `label:`
  role per name, alongside its `link:` roles) and restored by
  `function_at`. `define` also takes `(function, label)` keys, with an
  expression value: the labelled node keeps its `EntityID` and takes the
  new content, the nodes below it disappear, and any nodes the
  replacement needs are placed under the function. In `activate` and
  `trial`, a pair's target may be `(link, label)`, with an expression
  (code as data) instead of a function value; capability, checks, code in
  flight and atomicity are unchanged.

### Data, let, references and tail calls

- `semiroh/lang.py` implements docs/language_data.md (roadmap.md task 6):
  `tuple`, `len`, `item`, `slice` and `concat` (int indices, no negative
  indexing and no clamping; anything out of bounds is a `LanguageError`);
  `("let", name, e, body)`, which `("arg", name)` reads like a parameter, a
  name already in scope being rejected when the `let` runs; `("ref", link)`,
  an `EntityID` value, and `("apply", f, ...)`, which calls it as `call`
  does. Each is a graph-form node kind (docs/graph_form.md section 3) and
  `function_at` round-trips it.
- Tail calls: `_eval` knows tail position, where a `call` or `apply`
  returns a `_TailCall` to a loop in `_call`. The loop enters the callee's
  frame and then releases the caller's, so a chain of tail calls keeps one
  frame and one interpreter level, and no hold survives a call that raises.
  Calls not in tail position are unchanged (about 5 Python frames each).
- Corpus tier 2: `TAGS` gains `data` and `higher order`; new examples
  `insertion_sort`, `let_bindings`, `map`, `fold`, `deep_loop` and the
  `sort_swap` canary (higher order and self-modification: `order` is
  activated between two sorts while the data stays in a cell). The four
  closed entries left `MISSING`; two gaps found while writing them were
  added: `map_long_tuple` (non-tail recursion is still bounded by the Python
  stack, `map` fails from about 200 elements) and `make_adder` (no function
  values that capture names).
- New `tests/test_data_graph_form.py` (roles, round trip, holds after a
  raising tail call, `apply` of an absent entity) and
  `tests/test_data_regressions.py` (a `slice` stop below the length, wrong
  argument counts that an unbound parameter would hide, `let` scope, tail
  calls in the then-branch of an `if` and before the last item of a `seq`;
  each fails on a planted bug the acceptance suite let through).
  `tests/test_data_ops.py` and `tests/test_corpus.py` are unchanged; no
  existing test was edited.
- Provisional: a reference is the function's `EntityID`; held in cell
  content it does not follow a rename (docs/language_data.md section 3).

### Roadmap update

- Marked tasks 1 to 6 done. Decided D2: task 7 compiles graph form to a
  bytecode run by a VM with an explicit stack, instead of Python closures,
  so the self-hosting milestone can emit it and deep recursion stops
  depending on Python's stack. Swapped tasks 8 and 9, so self-hosting comes
  first, and gave it a prerequisite: an operation that reads code as data.
  Recorded the pending decision on owned-subtree constraint subjects, and
  added the new corpus gaps and the syntax notes to Later.


### Bytecode and the VM

- `semiroh/bytecode.py` replaces the tree interpreter (roadmap.md task 7,
  D2; docs/bytecode.md). Each graph-form node lowers to a chunk, a tuple of
  plain-tuple instructions (`("ARG", "x")`, `("MUL",)`, `("CALL", f, 2)`)
  that names the nodes below it by `EntityID`, so it depends on its node's
  value alone. It is kept with the node's `Value`, like its `VersionID`,
  and lowered the first time the node runs. `lang.run` calls the machine;
  `_eval`, `_call` and their helpers are gone from `lang.py`, which keeps
  the graph form (`load`, `define`, `function_at`). One interpreter
  remains.
- The machine keeps an operand stack and a control stack of cursors, so a
  call does not use the host stack: recursion that is not a tail call is
  bounded by `CALL_DEPTH_LIMIT`, not by the recursion limit. Tail position is a flag of
  the cursor, and a call there reuses its activation (frame entered, then
  the caller's released), so a chain of tail calls keeps one hold. Frames
  are still entered and released per call, code in flight still runs the
  state its frame was entered in, and a run that raises releases every
  frame.
- Differential check before removing the tree interpreter: 4000 seeded
  random programs (19,764 steps, 35% succeeding; activations, node edits and
  trials among them) gave the same results, exception types and messages,
  cells, collapsed functions, versions and holds on `main` and here. One
  program differed, where the old interpreter reached its Python recursion
  limit; with the limit raised it agreed. The harness is not kept.
- Speed on the same machine, old interpreter to VM: `fact(15)` 326 to 183
  µs, a tail loop of 3000 calls 54.5 to 41.5 ms, `map` over 100 elements
  5.6 to 3.5 ms, the whole corpus 847 to 615 ms.
- Corpus: `map_long_tuple` leaves `MISSING` (docs/corpus.md section 4) and
  becomes a tier 2 example, with `deep_recursion`; each fails on the old
  interpreter (`RecursionError`). `make_adder` remains. `tests/test_corpus.py`
  is unchanged.
- Per-node caching against re-pointing dependents per function (bytecode.md
  section 7): a leaf edit lowers 1 node where a function-level artifact
  lowers the whole function (41, 401), a replaced function lowers its new
  nodes and no other function's, a rename lowers the call nodes that name
  it. It is simpler, since a chunk is valid as long as its value exists and
  nothing is invalidated. Lowering costs about 0.8 µs a node, so the time
  saved is small next to the activation; per-node identity pays for itself,
  modestly.
- **Provisional:** the instruction set and the chunk per node (bytecode.md
  sections 2 and 3). An `unquote` node evaluates its operand; only a quote
  reaches it. `_definition_of` keeps the definition with the function's
  value, since every call read it.
- New `tests/test_bytecode.py`: exact chunks, the order of checks and
  effects (a write planted beside each check), which nodes are lowered
  again after a leaf edit, a bigger edit, a whole-body swap and a rename,
  recursion 5000 calls deep under a recursion limit far too low for the
  old interpreter, holds during a tail chain and a waiting chain (through
  a cell evaluator), error names, code in flight through three ways a node
  is reached, and a seeded property test that warm chunks, cold chunks and
  an independent evaluator agree through random node edits. Eighteen
  planted bugs (a check moved, a cache keyed by entity, no cache, a
  frame reading the active state, a tail call that nests, frames not
  released, the wrong function in an error, and others) each fail at
  least one test. No existing test was edited.
- **Provisional**, added after review: `CALL_DEPTH_LIMIT`, 100,000 calls
  waiting on each other in one run (tail calls do not count), raises
  `CallDepthExceeded`, a new `LanguageError`. Without it a runaway
  recursion, which raised `RecursionError` at once, used all the memory
  there was (31 s to a `MemoryError` under 1.5 GB, an OOM kill without a
  limit, and holds left unreleased). 100,000 calls take about 90 MB and 1.5 s.
  Also from review: an empty `seq` node lowers to `None` as it evaluated;
  four docs whose status line still said `lang.py` runs the code name
  `bytecode.py`; and the test list above gained the limit's boundary, tail
  calls at the limit, a tail call in a `let` body and an invalid node's
  function name. Two deviations for hand-built nodes remain, in
  bytecode.md section 2.
- Known limit, not the machine's: `canonical_serialize` still recurses on
  the host stack, so a function body nested about 244 levels or a value
  nested as deep fails to load or to write (bytecode.md section 8).

### Decide owned-subtree constraint subjects

- Decided what task 4 left Provisional: a constraint relation sees an owner
  endpoint as `{"value": ..., "owned": {...}}` and any other endpoint as its
  plain content (relation_model.md section 7, graph_form.md section 7). It
  is kept because a constraint over a function's code has to keep holding
  while nodes are edited or swapped, and naming each node would not.
  Recorded the cost: the shape depends on whether the endpoint owns
  anything, which has not mattered since only functions own structure. An
  opt-in for the subtree was considered and not taken. Removed the pending
  decision from the roadmap. Docs only; `OwnedSubtreeTests` already pin the
  behaviour.

### Mutation tests

- Added `tests/mutation.py` and `tests/test_mutation.py`: seeded single-site
  bugs (a comparison flipped, `and` turned into `or`, an `if` negated, a
  constant moved by one, a returned value dropped) planted in a copy of
  `bytecode.py`, `lang.py` and `runtime.py`, with the whole suite run on each.
  A mutant the suite does not fail is a survivor. The machinery is tested in
  the normal run on a tiny package (planted change killed, a change with no
  effect surviving, a hang counted as killed, the sample repeating); running
  it on the model takes about a minute and only happens with
  `SEMIROH_MUTATE` set, so `unittest discover` and CI are unchanged. It
  replaces the differential harness of #26, which could not outlive the
  tree interpreter.
- It found two gaps, now tested: nothing checked that a `GOTO`, `BRANCH` or
  `LETBIND` child comes from the chunk cache (a second run of a program
  using `if`, `seq` and `let` lowers nothing), and an edit whose
  replacement repeats the label of the node it replaces had no test. Both
  tests fail with the bug planted. Survivors that change nothing are listed
  with their reason; one is an open gap (equality of `Function` by content
  against by fields).

### Self-hosting: `code` and a compiler in SEMIROH

- Added `("code", link)`, which returns `(params, body)` of a function in
  input form, read from the active version (self_hosting.md section 1). In
  graph form it is a node with a `target` role like `ref`; it lowers to
  `CODE`. Reading needs no capability.
- Wrote the lowering pass of bytecode.md in SEMIROH
  (`semiroh/examples/self_hosting.py`): `lower(e)` gives the chunk of an
  expression with each child's chunk in place of its reference and link names
  in place of entities. It covers every operation but `quote`, `unquote`,
  `function`, `activate` and `trial`, and is written in what it covers.
  Tests compare it with the host's chunks on a curated list, 60 seeded
  random expressions, each function of the compiler, and `self_lower`, which
  reads and compiles its own `lower`.
- Added the corpus examples `compiler` and `instrument`: a program reads its
  own function, swaps in a version that counts its calls and compiles what
  it installed. Provisional, at the owner's choice of scope: the compiler's
  output is checked against the host's and not run; a bytecode interpreter
  in SEMIROH is roadmap task 10, "probably".
- Extended the mutation targets to `self_hosting.py` (two listed survivors)
  and pinned the message of an unknown `code` link, which a mutant found
  loose. No existing test was edited.

### Constant folding with declared continuity

- Added `semiroh/fold.py`: `fold_constants(state)` returns a
  `TransformResult` that folds constant `add`, `sub`, `mul`, `lt`, `eq` and
  `if` on a constant bool, in every function of a graph-form state. A
  constant subtree becomes one literal at its root's `EntityID`, with every
  node below it merged into the root; an `if` merges itself and its
  condition into the branch it takes, and the other branch disappears.
  `sources_of(result, node)` reads the mapping back. Anything that could
  raise is left alone, so optimised code raises what the original raised,
  and a fold that would drop a labelled node is not done (constant_folding.md).
- Findings from the tests: folding to a literal leaves the parent untouched
  (the root keeps its `EntityID`), a swap lowers one node, and the folded
  state equals the state `load` gives for the folded code. Chained `if`s
  needed the mapping to point at the node that finally takes the place, not
  at one that disappears.
- Added `fold.py` to the mutation targets (two listed survivors).

### A bytecode interpreter in SEMIROH

- Added `("applyv", f, args)`, which calls a function reference with the
  items of a tuple, and `("linksof", link)`, which returns a function's link
  table as `(name, entity)` pairs. Both are nodes in graph form and lower to
  `APPLYV` and `LINKS` (vm_in_semiroh.md section 1). The compiler in SEMIROH
  covers them.
- Wrote an interpreter for the chunks `lower` emits in SEMIROH
  (`semiroh/examples/vm.py`): `vm(chunk, params, args, links)`, an operand
  stack and an environment as tuples, tail calls kept tail. It runs every
  operation that does not touch a cell or code as data; `READ`, `WRITE`,
  `CODE`, `LINKS` and `RAISE` raise, `REFCHECK` does nothing, and its errors
  are made by doing the operation (Provisional, section 3 of the doc).
- `swap_all()` replaces the compiler's functions, in one activation, by
  functions that hand their own chunk to the interpreter, and the compiler
  then gives the same results running on it, including for its own source: a
  bootstrap fixpoint. About 90 times slower than the machine. Corpus example
  `bootstrap`.
- Found by mutation testing: a call is always the last instruction before
  `END`, so the interpreter never pushes its result. Sped `eq` up for
  primitives in the machine, with a test that keeps kinds apart (`1` is not
  `True`). `vm.py` is a mutation target (two listed survivors, and the fast
  path of `eq`). No existing test was edited.

