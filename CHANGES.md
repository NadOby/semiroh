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
