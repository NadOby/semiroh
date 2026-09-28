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
