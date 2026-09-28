# Activation Model

This document describes what happens when a running program activates a new
version of its own program state.

Every SEMIROH program carries its compiler and can modify itself. Program
modification produces a new immutable state (see
[`transformation_model.md`](transformation_model.md)). Activation is the
separate step that makes the running program execute that state.

Each section is marked:

- **Decided**: agreed direction; later changes should be deliberate.
- **Proposed**: recommended direction, not yet agreed.
- **Open**: options are listed; no direction is chosen.

## 1. Program state and runtime state

**Decided.**

A running program has two kinds of state:

    program state
        immutable semantic state identified by StateID:
        values, ownership, and the existence, identity and type of
        mutable cells

    runtime state
        everything produced by execution: stack frames, heap data,
        mutable cell content, execution positions, native code

Runtime state does not contribute to `StateID`.

Activation connects the two. Runtime state produced while `S₀` was active must
become valid, or remain explicitly pinned, when `S₁` becomes active.

## 2. Activation as a transition

**Decided.**

Activation takes:

    active state          S₀
    produced state        S₁
    transformation result S₀ → S₁ with explicit continuity
    state-transfer functions, where required

and makes `S₁` active.

Activation uses the transformation result, not only `S₁`. Continuity is what
tells the runtime how live state in `S₀` corresponds to `S₁`.

Activation is atomic from the program's point of view: either `S₁` becomes
active with every required transfer completed, or `S₀` stays active and
runtime state is unchanged.

Activating a state for which no transformation from the active state
exists gives every live entity unknown continuity. Such an activation is
therefore rejected whenever any mutable cell holds live content (section 4),
and references into `S₀` stay pinned (section 6).

## 3. Validation and authority

**Decided.**

Producing a new state with the embedded compiler and activating a state are
both governed by capabilities. A program without the activation capability
cannot replace its own running version.

Order:

1. produce `S₁`;
2. validate `S₁` (constraints and contracts);
3. run state-transfer functions into staged runtime state;
4. switch atomically;
5. release superseded versions when nothing depends on them (section 7).

Any failure before step 4 leaves `S₀` active and runtime state unchanged.
`Unknown` validation results do not permit activation unless an explicit
policy says otherwise.

## 4. Mutable cell content

**Decided**, except where conversion functions live, which is open.

A mutable cell is versioned program state; its content is runtime state. At
activation, cell content is carried along explicit continuity:

    cell A in S₀ → cell A' in S₁
        content of A is transferred into A'

This corresponds to Erlang's `code_change`: the new version receives the old
state and may convert it.

Rules by mapping cardinality:

    A → A' (same representation)
        content transferred unchanged

    A → A' (changed type or representation)
        an explicit conversion function is required;
        without one, activation is rejected

    A → ∅
        content is discarded; resources it owns stay owned by the
        old version and are destroyed when that version is retired
        (section 7)

    A → (A', A'')
        an explicit transfer function must produce each destination's
        content; content is never duplicated implicitly

    (A, B) → C
        an explicit merge function is required

    A with no declared continuity
        activation is rejected if A holds live content

The last rule follows the transformation model: preservation is not
continuity. Tools that produce transformations, including the embedded
compiler, are expected to declare identity mappings (`A → A`) for cells they
leave untouched, so this rule costs nothing in the common case.

A cell new in `S₁` (no incoming mapping) is initialized by its own
initializer.

Where conversion functions live is open. One option is to make them a third
component of the transformation definition, next to changes and mappings.

## 5. Code in flight

**Open.**

Some threads may be executing code of entities that the transformation
changed or removed. Options:

    version coexistence
        running frames continue in the old version; new calls enter the
        new version. Erlang switches at fully qualified calls; local calls
        stay in the version already running.

    explicit update points
        the program declares where activation may take effect; activation
        waits until every thread reaches one (Kitsune for C).

    quiescence
        activation waits until no thread executes changed code.

    on-stack replacement
        live frames are rewritten into frames of the new version. This
        requires continuity for locals and execution positions and is the
        most general and the most complex option.

These can be combined per thread: each thread switches when it reaches a safe
point, as Linux kernel livepatch does per task.

A reasonable starting point is version coexistence with switching at call
boundaries or explicit update points. On-stack replacement can come later.

## 6. References across activation

**Decided.**

References are state-pinned. Activation is exactly the one step through which
runtime-held references into `S₀` are transferred:

    unique continuation
        reference is transferred to S₁ (transfer_reference)

    disappearance, ambiguity, or unknown continuity
        reference stays pinned to S₀

A pinned reference keeps the old version alive (section 7). It is never
silently rebound to an unrelated entity in `S₁`.

Pinning is the default. A program may opt into a stricter policy that
rejects activation when any live reference cannot be transferred.

## 7. Retiring superseded versions

**Proposed** (ownership, runtime holds, two-version bound). **Open**
(activation while the previous version is still held).

Retirement of old versions uses the ownership model rather than a separate
lifetime mechanism. The same rules apply to runtime state as to program
state: one owner per entity, no cycles, and recursive destruction of an owned
subtree.

    runtime root
        owns the active version
        owns superseded versions that are still in use

    version
        owns its native code
        owns cells and resources that did not transfer at activation

Retiring a version destroys its owned subtree. Resources of cells that
disappeared at activation (`A → ∅`, section 4) remain owned by the old version
and are destroyed with it.

Ownership alone cannot say when retirement is allowed. Many threads, frames
and pinned references can depend on the same old version, and ownership
permits only one owner. These dependencies are therefore recorded as holds on
the version:

    frame executing old code             holds its version
    reference pinned to S₀ (section 6)   holds the version of S₀
    function pointer, return address     holds the version it points into

A superseded version is retired when nothing holds it any more.

A hold is deliberately much narrower than a borrow:

- it is coarse: it applies to a whole version, not to individual objects;
- it is dynamic: the runtime tracks it, for example with an epoch or
  RCU-style grace period, or a count per version;
- it is internal: it does not appear in types, has no lifetimes or aliasing
  rules, and user code never creates or checks one.

SEMIROH does not introduce a general borrowing system to retire versions.

At most two versions run in one runtime: the active version and the previous
one, as in Erlang. Two is the minimum compatible with pinned references
(section 6) and with activation that does not stop every thread. A
single-version bound would require every activation to wait until no thread
runs old code, and to reject every reference it cannot transfer.

Open: what happens when a new activation arrives while the previous version
is still held. The options are to wait (possibly with a timeout), to reject
the activation, or to terminate the holders, as Erlang terminates processes
still running purged code. Terminating a thread would itself be destruction of
what that thread owns.

## 8. Rollback

**Decided.**

`S₀` remains an immutable, valid state after activation. Returning to it is a
new activation `S₁ → S₀` with its own continuity mappings and conversion
functions.

Runtime state transferred during the first activation is not automatically
restored. Consistent with the transformation model, reversibility is not
implied by the existence of a forward transformation.

## 9. Native code

**Open.**

The embedded compiler regenerates the executable representation of `S₁`.
Native code can be cached by `VersionID`, so entities whose version is
unchanged reuse existing code.

Installing new native code interacts with W^X memory policies, code signing,
and platforms that forbid runtime code generation. These are listed as open
areas in the README.

## 10. Relation to other models

- **Transformation model**: supplies `S₁` and the continuity mappings.
  Activation adds no continuity of its own.
- **Reference model**: activation is the one-step transfer for runtime-held
  references.
- **Ownership model**: retirement of superseded versions is recursive
  destruction of an owned subtree, gated by runtime holds (section 7). No
  general borrowing system is introduced.
- **Constraint and contract models**: supply the validation performed before
  activation.
- **State model**: activation selects a state; it does not mutate any state.

## 11. Current implementation status

The Python reference model does not yet implement activation, runtime state,
or mutable cells.

A first executable model could consist of a small interpreter holding live
references and mutable cells for an active state, a metaprogram producing
`S₁`, activation that transfers cell content and references along the
transformation result, and release of `S₀` once nothing is pinned to it.

## 12. Unresolved areas

- switching strategy for code in flight (section 5);
- where conversion and transfer functions live (section 4);
- how the runtime tracks holds on versions (section 7);
- activation while the previous version is still held (section 7);
- concurrency: per-thread switching and its memory model;
- native code installation under platform restrictions.

## 13. Design principle

Activation is an explicit, atomic transition of the running program from one
immutable program state to another.

Live runtime state crosses that transition only along declared continuity,
with explicit conversion where its shape changes. Anything that cannot cross
stays pinned to the version it belongs to, or the activation is rejected.
