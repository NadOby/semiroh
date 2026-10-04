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
stable to form part of the SHEAR semantic model.

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

- Stated the motivating goal in the README: every SHEAR program carries its
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

- Added `shear/lang.py`: a tiny expression language interpreted directly
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

- Added `shear/examples/`, implementing the canary corpus (docs/corpus.md):
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

- `shear/lang.py` stores and runs code as graph form (roadmap.md D1, task
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

- `shear/lang.py` implements node-level edits (roadmap.md task 5;
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

- `shear/lang.py` implements docs/language_data.md (roadmap.md task 6):
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

- `shear/bytecode.py` replaces the tree interpreter (roadmap.md task 7,
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
  `SHEAR_MUTATE` set, so `unittest discover` and CI are unchanged. It
  replaces the differential harness of #26, which could not outlive the
  tree interpreter.
- It found two gaps, now tested: nothing checked that a `GOTO`, `BRANCH` or
  `LETBIND` child comes from the chunk cache (a second run of a program
  using `if`, `seq` and `let` lowers nothing), and an edit whose
  replacement repeats the label of the node it replaces had no test. Both
  tests fail with the bug planted. Survivors that change nothing are listed
  with their reason; one is an open gap (equality of `Function` by content
  against by fields).

### Self-hosting: `code` and a compiler in SHEAR

- Added `("code", link)`, which returns `(params, body)` of a function in
  input form, read from the active version (self_hosting.md section 1). In
  graph form it is a node with a `target` role like `ref`; it lowers to
  `CODE`. Reading needs no capability.
- Wrote the lowering pass of bytecode.md in SHEAR
  (`shear/examples/self_hosting.py`): `lower(e)` gives the chunk of an
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
  in SHEAR is roadmap task 10, "probably".
- Extended the mutation targets to `self_hosting.py` (two listed survivors)
  and pinned the message of an unknown `code` link, which a mutant found
  loose. No existing test was edited.

### Constant folding with declared continuity

- Added `shear/fold.py`: `fold_constants(state)` returns a
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

### A bytecode interpreter in SHEAR

- Added `("applyv", f, args)`, which calls a function reference with the
  items of a tuple, and `("linksof", link)`, which returns a function's link
  table as `(name, entity)` pairs. Both are nodes in graph form and lower to
  `APPLYV` and `LINKS` (vm_in_shear.md section 1). The compiler in SHEAR
  covers them.
- Wrote an interpreter for the chunks `lower` emits in SHEAR
  (`shear/examples/vm.py`): `vm(chunk, params, args, links)`, an operand
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

### Checkpoint

- README gained a status section: what the reference model demonstrates
  (the graph is the program, programs modify themselves, programs carry
  their compiler), how the vision changed on contact with code, which
  decisions are still provisional, and what is not touched yet. Sections 24
  and 25 now name the language layer, the canary corpus and the mutation
  tests. Docs were checked for stale statuses and references; none needed
  changes.

### Text syntax, version 0

- Added `shear/syntax.py`: `parse(text, base=None)` reads program text
  (cells, functions, blocks with `let` and `if`, expressions, `quote`,
  `unquote`, `literal`, `fn`, `activate`, `trial`, `label`, `raw`) into the
  input format, with a links relation made from the global names each body
  uses; `render` and `render_program` print graph form back as text, with the
  current target names, and `raw(...)` for what the syntax cannot write.
  Import-only: editing text and parsing it again creates new nodes
  (docs/syntax.md).
- The corpus round-trips by behaviour and by text. Only `instrument` prints
  `raw`, for a cell write inside a quote template.
- Decided on contact with the corpus (syntax.md sections 1, 2, 4 and 8): a
  `let` value may be a cell write; an `IntRange` bound may be left out; the
  names in code installed by `activate` or `trial` into a function are also
  links of that function (the links of a function declared in text come
  only from the text, so a function that a self-modifying one rewrites
  would otherwise lack the links its new code needs); a reserved word in
  backquotes is an ordinary name.
- `render_program` prints cells too, since a printed function is not a
  program without the cells it names. No existing module or test changed.

### Continuity corpus

- Added `shear/continuity.py`: 21 cases of expected continuity (groups
  declared, inferred, competing, moved), each a program in text syntax, an
  operation and an `Expect` over designators (`fn:`, `cell:`,
  `node:NAME@PATH`, `after:NAME@PATH`, a path being the input-form position
  of a node). `check` runs a case and names each mismatch
  (docs/continuity_corpus.md). `Case` gained `writes`, cell content written
  before the activation, so that a transfer differs from a reset.
- 11 cases hold and pin the current rules: declared mappings, cell merge,
  split and upgrade, folding, the label edit. 10 are gaps, the input of
  task 13: a whole-body `define` keeps no node that a tree match would keep
  (`insert`, `remove`, `wrap`, `unwrap`, `swap`, `shared_subtree`,
  `redefine_same`), nothing re-bases a result (`rebase_disjoint`), and no
  operation moves a node between functions (`extract_function`,
  `inline_function`).
- Found on contact: `define` of a body equal to the old one still renews
  every node; `conflicting_edits` holds only because any second result from
  the same source is rejected as stale, which is also why `rebase_disjoint`
  fails; a program loaded again reuses the ids `f/0.n` for other nodes.
  No prediction was wrong. No existing module or test changed.

### Continuity inference

- Added `shear/matching.py`: `match` and `shapes`, the rules of
  docs/continuity_inference.md §2. From the largest size down, a new
  subtree whose shape is unique among the unmatched old and new subtrees
  keeps the old identity whole; then each entry's new root keeps the node
  at its position when the kind is the same. Nothing else is matched.
- `define` infers by default (owner decision: identity follows the
  expression), including the transformations `activate` and `trial`
  build. All entries of one `define` form one pool, so a node can move
  between functions, with its owner change stated in explicit destination
  ownership. `define` also creates a function (a `Function` for an absent
  entity), removes one (None) and replaces a link table (a links relation
  as an entry), so `extract_function` and `inline_function` are one
  `define`. An edit that changes nothing gives the source state.
- Added `transforms.rebase`, `touched` and `TransformationConflict`: two
  results of one state combine when their touched sets are disjoint;
  colliding created node names move to the function's next free
  generation. `Runtime.activate` and `trial` rebase a result from an
  earlier active state over every result activated since;
  `ActivationConflict` is both `ActivationRejected` and
  `TransformationConflict`. A result from a state never active is stale,
  as before.
- All 21 continuity corpus cases hold; the operations of the two moved
  cases changed, not their sources or expectations.
- Decided on contact: a label edit that changes the node's kind now gives
  the position a new node, and the node that named it is changed (graph
  form §9 changed); a whole-function edit advances the generation only
  when it creates a node, and a label edit never does, so it can reuse
  the name of a node an earlier label edit removed (Open); no compiled chunk depends on the owning function,
  so a moved node keeps its `VersionID`; the runtime remembers every
  activated result (unbounded, Open); a combined state's constraints are
  left to activation, not reported as a conflict.
- Existing tests changed, each renamed to what it now checks:
  `test_define_replaces_one_body_and_nothing_else` →
  `test_define_edits_one_body_keeping_what_is_unchanged_and_nothing_else`
  (the unchanged `read` and the root are kept);
  `test_replacing_with_a_larger_expression_and_back` →
  `..._renews_the_position` (a kind change gives a new node);
  `test_define_rejects_what_is_not_a_function` →
  `..._and_creates_an_absent_one` (define may create a function);
  `test_repeated_defines_never_reuse_a_node_entity` →
  `test_repeated_defines_never_create_a_node_under_a_used_name` (kept
  nodes keep their names; created ones still never reuse one);
  `test_load_and_define_round_trip_any_body` →
  `..._keeping_only_what_matches` (it failed on 55 of 300 seeds, each a
  unique unchanged subtree or a same-kind root correctly kept, not a bug).
  The probes of three `CheckTests` in `test_continuity_units.py` now use a
  whole-body edit that keeps no node; `check` did not change.
- Added `tests/test_matching.py` (rules one by one, order independence and
  one-rule-per-kept-node as seeded properties, moves, touched sets,
  renaming, conflicts). `matching.py` and `transforms.py` joined the
  mutation targets.
- Found by review and mutation (seed 13 on the four changed modules):
  tests that rebase skips a name the other result removed, that the
  runtime rebases from the last time the source was active, that three
  disjoint edits of one state activate in turn, that a rebased result
  keeps a cell the other one created, and that a label's matching stays
  inside it. Three equivalent mutants are listed. No model code changed.

### Graph ledger

Added `docs/graph_ledger.md`, an evidence ledger for where graph form earns
its keep relative to an ordinary compiler representation. It covers stable
node identity, hot swap, incremental compilation, fold provenance,
continuity inference, moves, rebasing, relation/ownership updates and
constraints over code, with explicit Strong / Even / Weak verdicts.

Added `shear/examples/ledger.py`, which measures the existing model rather
than estimating results: incremental bytecode lowering counts, continuity
corpus identity claims and constant-fold provenance. Added
`tests/test_ledger.py` to run the measurement script and require every quoted
ledger measurement to match live model output.

### Reconciler

- Added `docs/name_resolution.md`: lexical names resolve through active
  `let` bindings, parameters and then the program-global namespace; version
  0 has one implicit root module and deliberately adds no module syntax.
- Added `shear/reconcile.py`: complete edited source is parsed and compared
  with the authoritative graph, and changed functions are applied through
  `lang.define` so task 13's continuity inference preserves unambiguous
  unchanged code nodes.
- Unchanged functions are left untouched; functions may be added or removed,
  while a bare top-level rename is deliberately remove plus create because
  source spelling alone supplies no declaration-continuity evidence.
- Function link tables are reconciled with their bodies, including removing
  the last link. Cell declaration edits are rejected until cell migration
  semantics are specified.
- Added acceptance coverage for no-op edits, descendant continuity,
  insertion, function creation/removal and rename, changed and removed
  references, untouched-function identity, and rejected cell declaration
  edits.

### Documentation coherence

- Started task 16, a documentation-coherence sweep with no intended semantic
  model changes.
- Normalized standalone `Decided`, `Provisional`, and `Open` markers across
  the specification documents.
- Added `tests/test_docs.py` to detect stale roadmap PR placeholders, broken
  internal Markdown links, invalid numbered section references, missing
  top-level headings, and noncanonical status markers.
- Documentation checks accumulate independent errors so one CI run reports
  the full set of mechanical problems instead of stopping at the first one.
- Applied the same accumulated-diagnostic pattern where useful to graph-ledger
  documentation measurements, continuity designators, and continuity-corpus
  shape checks.
- Extended the semantic-model workflow to run for changes anywhere under
  `docs/` or to `README.md`, so documentation coherence is enforced on
  documentation-only changes.
- Recorded a later cleanup to split CI into independent coherence, semantic
  unit, regression/corpus, property/stress, and expensive mutation jobs.

### Lexical closures

- Added executable lexical closures (roadmap task 17; docs/closures.md) as a
  runtime value distinct from `Function`, which remains code as data for
  construction and activation.
- Added `("closure", params, captures, body)` with explicit by-value lexical
  captures. Closure bodies remain ordinary graph code; graph form stores only
  the body as a code child and keeps parameter and capture-name tuples as node
  data.
- `apply` and `applyv` now accept either installed-function references or
  closures. Closure calls use ordinary arity, active-version and tail-call
  rules, require no activation capability, and do not fall back to the
  caller's lexical scope.
- Existing closures retain their captured values while their semantic
  owner/body identities resolve through the active program version when
  continuity preserves them.
- Added `CLOSURE` bytecode and host-machine support, including tail closure
  calls and the same early callable check used by indirect function calls.
- Extended the compiler written in SHEAR to emit closure bytecode and added
  an independent structural comparison with host lowering.
- Extended the bytecode VM written in SHEAR with tagged callable values:
  `("ref", entity)` and
  `("closure", body, params, captures, links)`. Its `REFCHECK` now validates
  callables before later operands run.
- Added explicit source syntax
  `closure(params) captures(names): expression`; capture inference remains
  deferred source sugar rather than part of the semantic operation.
- Added corpus examples `make_adder` and `compose`. `MISSING` is now empty.
- Added closure acceptance coverage for capture by value, returned closures,
  caller-scope isolation, passing/storing/comparing/capturing closures,
  continuity across activation, error ordering, graph-form round trips,
  tail-call depth, self-hosted lowering and execution on the SHEAR VM.
- Added `docs/verification_hardening.md` for roadmap task 18 and recorded
  language-architecture hardening as task 19.
  
## 2026-09-30

### Verification hardening

- Completed roadmap task 18 without intentional production-semantic changes.
  Verification work is separated from task 19's language-architecture changes.
- Split the ordinary deterministic suite into eight semantic CI lanes:
  `core-model`, `language-runtime`, `transform-continuity`,
  `syntax-reconcile`, `compiler-self-hosting`, `vm-bootstrap`,
  `cross-boundary`, and `mutation`. `tests/lanes.py` requires every ordinary
  `test_*.py` module to belong to exactly one lane.
- Added shared deterministic generation infrastructure with `SHEAR_SEED`
  replay, `SHEAR_CASES` budget control, and deterministic sequence
  reduction.
- Added generated closure-heavy differential tests across host execution and
  the embedded compiler/SHEAR VM path; malformed-language rejection
  generation; stateful runtime sequences with independently tracked semantic
  effects and invariants after every operation; bounded-exhaustive continuity
  composition; and metamorphic tests across both low-level transformations and
  language-level render/reconcile, `function_at`/`define`, and independent
  rebased edits.
- Expanded mutation accounting from 8 to 23 implementation targets. Every
  top-level semantic module and example module is now either a mutation target
  or has an explicit omission reason.
- Survivor site keys use `(target, kind, stripped source line, occurrence among
  matching sites)`. The key identifies a mutation site only within one reviewed
  source version.
- Added conservative source-version pinning for reviewed survivors. Every
  target containing a classified survivor is pinned to the Git blob ID of the
  exact source bytes under which that classification was reviewed. Any edit to
  that target invalidates all of its survivor classifications until they are
  explicitly re-reviewed and repinned.
- Migrated historical survivor knowledge only where the current exact site and
  justification were defensible. Survivor classifications are limited to
  `equivalent` and `unspecified`; a semantic test gap cannot be whitelisted.
  The historical `Function` equality entry was deliberately not migrated
  because its original record described an open test gap rather than an
  equivalent mutant.
- Updated `CLAUDE.md` with semantic-lane requirements, generated-test replay
  controls, mutation campaign controls, and survivor-classification policy.
  `CLAUDE.md` and `CHANGES.md` were also added to the workflow path filters so
  documentation/process-only changes trigger verification.
- Moved one-off run measurements out of `docs/verification_hardening.md`.
  That document records stable verification architecture and policy; concrete
  execution evidence is kept here and in the PR record.

Measured Task 18 evidence that remains valid:

- Pre-Task-18 serial baseline, run `36672073336`: 831 tests, 21.464 s Python
  test time, 36 s workflow wall time.
- Representative split run `36679502020`: 25 s workflow wall time without
  significant hosted-runner queueing.
- Run `36682239622`: `compiler-self-hosting` took 17.479 s and
  `vm-bootstrap` 12.623 s, putting the deterministic critical path below the
  old 21.464 s serial test time despite the stronger suite.
- Generated-case run `36683989602` exercised a 200-case budget successfully.
- Generated stress run `36874845445` exercised `SHEAR_CASES=2000`
  successfully across the split ordinary CI lanes.

Historical mutation executions that are not valid mutation-kill evidence:

- Run `36690295906` sampled one mutant from each of the then-22 targets.
  This run is invalid as mutation-kill evidence because the mutation repository
  copy omitted `docs/`, causing the complete child suite to fail independently
  of the planted mutant.
- Run `36708852109` used `SHEAR_MUTATE=25` and
  `SHEAR_MUTATE_SEED=1` across the then-22 targets. It is invalid for the
  same omitted-`docs/` reason and does not validate the survivor catalog.
- Subsequent corrected mutation discovery and deterministic batches 0–6 are
  also not final mutation-kill evidence. A later review found that mutation
  catalog/source-integrity meta-tests still ran inside mutant subprocesses.
  A mutant, or the whole-file `ast.unparse()` rewrite used to emit it, could
  therefore fail those meta-tests for a nonsemantic source-text reason and be
  falsely counted as killed.
- Exhaustive campaign run `36891181744` was started before that false-kill
  path was fixed. Regardless of its execution result, it is not valid final
  mutation-kill evidence.

### Verification hardening review corrections

Fresh pre-merge reviews found several verification-harness problems. They are
recorded here because historical workflow success must not be mistaken for
valid evidence after the relevant oracle was shown to be unsound.

- The malformed-language generator was initially described as testing blanket
  rejection atomicity. That was incorrect. Mutable cell content is runtime
  state outside `StateID`, and arbitrary `LanguageError` is not transactional:
  effects that precede a later error remain observable according to normal
  effect ordering. Generated malformed tests now check graph-form round-trip
  preservation and rejection with `LanguageError` rather than leaked host
  exceptions. Atomicity is asserted only for operations whose contracts
  promise it, including rejected writes and rejected activations.
- The original mutation harness copied the repository while excluding `docs/`
  but ran the complete `unittest` suite in that copy. `tests/test_docs.py`
  therefore failed independently of planted mutants. The harness now copies
  the complete relevant repository and performs a baseline preflight using the
  same command, copy rules, and environment as mutant execution.
- Review found historical `shear/lang.py` generation mutations incorrectly
  classified as equivalent. Graph-form generation numbers are specified parts
  of node identity: new functions start at generation 0, replacement starts at
  the next generation, and collisions advance to the first free generation.
  Those exemptions were removed and dedicated regressions now pin the rules.
- Review found that mutation catalog and other source-integrity meta-tests ran
  inside mutation child subprocesses. Since mutants are emitted by rewriting
  the target with `ast.unparse()`, those tests could fail because source text
  changed rather than because semantic behaviour changed. Known equivalent
  mutants could therefore be falsely reported as killed.
- Mutation baseline and mutant child suites now run with
  `SHEAR_MUTATION_SUBPROCESS=1`. Mutation-catalog/source-integrity meta-tests
  are excluded identically from both child-suite kinds while remaining
  mandatory in ordinary CI. A regression explicitly verifies that a
  source-sensitive meta-test cannot falsely kill an otherwise surviving
  mutant.
- Review also found that the compact occurrence-based survivor key could
  silently rebind after insertion of another identical mutation site earlier
  in a file. Rather than making the key structurally more complex, reviewed
  survivors are now bound conservatively to exact source versions through
  `SURVIVOR_SOURCE_BLOBS`. Any source edit invalidates that target's reviewed
  survivor classifications, and direct mutation-campaign execution refuses
  stale, missing, or obsolete pins.
- Further review found that survivor identity also depends on the mutation
  engine version. Site traversal and occurrence assignment are defined by
  `tests/mutation.py`, as are the semantics of each mutation kind, so an engine
  edit could reinterpret an unchanged survivor key while all target-source
  pins still matched. `SURVIVOR_ENGINE_BLOB` now pins the exact reviewed
  `tests/mutation.py` Git blob. Ordinary catalog CI verifies that pin, and
  direct mutation campaigns validate it before baseline or mutant execution.
  Any mutation-engine edit therefore requires explicit survivor re-review and
  repinning.
- Exhaustive mutation campaign `36908901083` was started after the false-kill
  and source-version fixes on head `40796cdb53b589cd368895c86fae97709ebe6202`. The later mutation-engine-pin
  correction did not modify `tests/mutation.py` or any mutation target; the
  campaign therefore uses the exact engine and target-source versions now
  reviewed and pinned. If it completes cleanly, its shard logs and exact
  mutation-site counts will provide the final Task 18 mutation-kill evidence.

## 2026-10-04

### Verification hardening final evidence and scope correction

- Corrected the earlier Task 18 scope statement that described the work as
  having no production-semantic changes. Mutation review exposed two real
  production defects and the task includes their fixes:
  - closure capture values are canonicalized when the closure is constructed,
    so later mutation of a host container cannot change the captured semantic
    value;
  - closure capture names are validated as non-empty strings before lookup, so
    malformed names produce `LanguageError` rather than leaking host container
    behaviour.
- Earlier mutation runs remain historical discovery evidence rather than final
  mutation-kill evidence:
  - runs `36690295906` and `36708852109` used an incomplete mutation repository
    copy that omitted `docs/`;
  - the following deterministic batches and exhaustive run `36891181744`
    still allowed source-sensitive mutation-catalog integrity tests to kill
    mutants for nonsemantic reasons;
  - run `36908901083`, after fixing that false-kill path, established a
    3447-site census and exposed 288 survivors for review;
  - run `37065518652` on the reviewed infrastructure contained 3449 sites and
    exposed 62 remaining unclassified survivors, which drove further
    regressions and classifications;
  - attempted exhaustive run `37122470634` exposed the final seven unresolved
    cases: six syntax survivors requiring five regressions plus one
    intentionally unspecified rendering-layout classification, and one
    `fold.py` survivor whose existing equivalent classification had been
    attached to the wrong same-text occurrence. The occurrence key was
    corrected rather than adding another classification.
- Final exhaustive mutation campaign `37140471232` ran on exact head
  `39a20617a32bcb35059d7e99fae2b8f72e6423b7` with
  `SHEAR_MUTATE=10000`, seed `1`, batch `0`, and four deterministic target
  shards.
- The final shard census was:
  - shard 0: 481 / 481 sites;
  - shard 1: 999 / 999 sites;
  - shard 2: 1529 / 1529 sites;
  - shard 3: 440 / 440 sites;
  - total: 3449 mutation sites.
- All four mutation shards passed with zero unclassified survivors. The eight
  ordinary semantic CI lanes also passed on the same workflow run.
- This completes Task 18 verification hardening on that exact tree. The result
  is strong mutation evidence for the reviewed implementation and test suite;
  it is not a formal proof of semantic correctness.

### Verification infrastructure follow-up

- Completed roadmap task 18a as verification infrastructure and CI work only.
  The branch comparison against `main` contains no `shear/` production-file
  changes and no task 19 implementation.
- Replaced target-level mutation sharding with deterministic mutant-level
  sharding. Mutation selection is completed first using the existing target,
  budget, seed and batch semantics; the selected mutants are then shuffled
  deterministically from the seed and distributed round-robin. Changing the
  shard count therefore does not change the selected work set, shards are
  disjoint and exhaustive, and their selected counts differ by at most one.
- Centralized the semantic mutation subprocess oracle in
  `tests/mutation_oracle.py`. Harness-integrity and survivor-catalog tests
  remain mandatory in the ordinary mutation CI lane but are excluded from
  mutation-kill decisions. Regression coverage verifies that baseline and
  mutant subprocesses use the same semantic oracle command.
- Added flushed campaign observability: pinned engine and target-source
  versions, exact campaign inputs and selected keys, periodic progress,
  immediate survivor reports, reconciled completion counts, grouped outcomes,
  and per-target diagnostic timings. A time-based heartbeat continues to emit
  progress while long-running mutants produce no completions.
- Added JSONL evidence from the same campaign event stream and made manual CI
  shards upload that evidence even when unclassified survivors make the shard
  fail.
- Added exact mutation replay under target-source and mutation-engine pins.
  Added `replay-failures` to consume one or more completed shard reports, run
  one semantic baseline, and replay only the recorded unclassified survivors.
  Synthetic regression coverage verifies the filtering, single-baseline
  preflight and fail-closed handling of incomplete reports.
- A 23-mutant smoke campaign, run `37163862758`, exercised the new four-shard
  path as `6 / 6 / 6 / 5`, with 18 killed mutants, 5 classified survivors and
  0 unclassified survivors. All four evidence artifacts uploaded.
- That smoke campaign exposed a real observability defect: progress intervals
  were checked only when a mutant future completed, so a sufficiently slow
  mutant could leave a shard silent beyond the requested heartbeat interval.
  The campaign runner now waits with a timeout for the next completion and
  emits progress even when zero additional mutants finish. Regression coverage
  pins that behaviour.
- Exhaustive validation run `37165355654` ran on head
  `7a2798db465c59de6edcf589e7b4577d29f7a582` with
  `SHEAR_MUTATE=10000`, seed `1`, batch `0`, and four mutant-level shards.
  Its four JSONL reports contain exactly 3449 unique selected mutation keys and
  exactly 3449 unique outcomes, with no omissions or duplicates.
- The exhaustive shard census was:
  - shard 0: 863 mutants;
  - shard 1: 862 mutants;
  - shard 2: 862 mutants;
  - shard 3: 862 mutants.
- Aggregate exhaustive outcomes were 3301 killed mutants, 148 classified
  survivors and 0 unclassified survivors. All four mutation jobs, all four
  evidence uploads and all eight ordinary semantic CI lanes passed.
- Campaign elapsed times were approximately 58.2, 53.0, 52.6 and 58.4 minutes,
  a slowest-to-fastest ratio of about 1.11. For comparison, Task 18's
  target-level exhaustive shards took approximately 40.3, 104.8, 273.4 and
  38.6 minutes, a ratio of about 7.1. On this exhaustive seed-1 workload,
  deterministic mutant shuffling therefore reduced the mutation critical path
  from about 273 minutes to about 58 minutes, roughly a 4.7x reduction.
  Timing remains diagnostic only: this run demonstrates good balancing for
  this workload and does not establish a timing guarantee for every future
  source tree or seed.
- The exhaustive run also exercised the heartbeat throughout roughly
  53–58-minute campaigns, including periods with no completed mutants, so the
  live-progress behaviour is supported by both regression tests and a
  full-scale execution.

### Rename to SHEAR

- The project, the Python package (`semiroh` → `shear`), docs, tests, CI and
  environment variables (`SEMIROH_*` → `SHEAR_*`) are renamed. No semantics
  changed: every corpus program keeps its StateID, rendered text and
  bytecode, and every continuity case its result.
- Mutation survivor pins were moved to the new paths only after checking
  that each pinned file is byte for byte the old one with the name
  substituted, so no classification was re-reviewed.
- A stale `SEMIROH_*` variable now fails the test package instead of being
  ignored. The old name stays only in that guard, its test, this entry and
  the README's closing note.
