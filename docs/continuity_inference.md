# Continuity Inference

**Status: implemented** (roadmap.md task 13). Deterministic rules for the
continuity nobody declares: which nodes an edit by `define` keeps, how a
node moves between functions, and what happens to two transformations of
the same state. Every case of the continuity corpus holds
(continuity_corpus.md §5); `tests/test_continuity_inference.py` is the
acceptance test and `tests/test_matching.py` tests the rules one by one.
The rules live in `shear/matching.py` (`match`, `shapes`), `lang.define`
builds the two sides, and `transforms.rebase` combines two results.

## 1. Terms

**Decided:**

- An edit's **scope** is what one `define` entry replaces. For a
  whole-function entry, the old side is every node of the function and the
  new side is the new body. For a label entry, the old side is the labelled
  node and the nodes below it, and the new side is the new expression.
  Nodes outside every scope are untouched, as today.
- All entries of one `define` form one **pool**: a node may be matched to a
  node of another entry, which is how it moves between functions
  (section 4).
- The **shape** of a subtree is its kind, its payload and its roles, with
  node operands compared by shape, recursively, and every other endpoint
  (a called function, a cell) compared by `EntityID`. Labels are not part
  of the shape; a label only names a node.

## 2. Matching an edit

**Decided:**

Owner, 2026-09-29: identity follows the expression, and the edited position
keeps its identity only as a same-kind fallback.

1. **Unchanged subtrees.** Taking new subtrees from the largest down, a
   new subtree is matched to an old one when its shape occurs exactly once
   among the old subtrees not matched yet and exactly once among the new
   subtrees not matched yet. The whole subtree is matched: each node keeps
   its `EntityID`, and, its content being equal, its `VersionID`.
2. **The edited position.** After rule 1, the root of each entry's new
   side takes the `EntityID` of the old node at that position (the old
   body root, or the labelled node) when neither is matched yet and both
   have the same kind. It takes the new content, so its `VersionID`
   changes. Nothing else is matched by position.
3. **Everything else.** An old node left unmatched disappears (a mapping
   to nothing); a new node left unmatched is created, named and placed as
   today (graph_form.md section 4).

Ambiguity never keeps an identity: a shape with two candidates on either
side keeps neither, and neither does anything below it unless it is unique
on its own. Nothing is matched by similarity. "Not matched yet" matters:
once a larger subtree takes one of two equal copies on each side, the copy
left is unique and is matched on its own.

Consequences:

- **graph_form.md §9 changed.** A labelled node keeps its `EntityID` only
  by rule 1 or rule 2. Wrapping it (`k` becomes `double(x)` where `k` was
  `x`) keeps the old node under the call, and the label then names the new
  call. A label edit that changes the node's kind gives the position a new
  node; the old one disappears. A same-kind edit (`1` to `10`) keeps it, as
  `leaf_replace` pins.
- **An edit that changes nothing changes nothing.** When every node is
  matched and the labels and links are the same, the function's value is
  unchanged and the destination is the source (same `StateID`).
- **Default.** Every `define` infers (owner, 2026-09-29), including the
  transformations `activate` and `trial` build (graph_form.md section 6).
  The existing tests that pinned fresh nodes for an unchanged part were
  renamed to what they now check (CHANGES.md, Continuity inference).

**Provisional:**

Settled by the code, not by the owner:

- Leaves match like any subtree, so a unique literal or argument that
  moves to another position within the scope keeps its identity there.
- Within one size, every candidate is decided against the counts taken
  before any of that size is matched, and matching one never changes the
  count of another shape of the same size, so the result does not depend
  on the order of either side or of the entries (`MatchingProperties` in
  `tests/test_matching.py`).
- A whole-function entry's position is the old body root; a label entry's
  is the labelled node; a created function has none.
- A whole-function edit advances the function's generation only when it
  creates a node; a created function starts at generation 0. A label edit
  never advances it (as before task 13), so its new nodes avoid only the
  names that exist (section 6).

## 3. What `define` records

**Provisional:**

The result stays an ordinary core transformation: kept nodes map to
themselves, disappeared ones to nothing, created ones are placed. A matched
node whose operands changed (rule 2) is a change of an existing entity. The
result states the destination ownership whole (transformation_model.md §13),
so the owner change of a node that moves between functions is explicit,
never implicit. When a label entry's root is a new node, the node outside
the scope that named the old position (or the body root reference in the
definition) is changed to name the new root, and the label names the new
root.

## 4. Moves across functions

**Decided:**

Scope: within one `define`, a node matched to a node of another function
keeps its `EntityID` and changes its owner to the function whose new body
holds it. It keeps its `VersionID` when its content is equal. No compiled
chunk depends on the function a node belongs to (a parameter is an `arg`
node naming the parameter), so a moved node is never changed for that
reason.

**Provisional:**

Operation, implemented as proposed:

- a `Function` for an entity absent from the state creates that function;
- `None` for a function removes it (a mapping to nothing; its unmatched
  nodes go with it);
- a links relation (`lang.links`) as the value of any entity key replaces
  the link table of the function it names, so a new body may call a
  function created in the same `define`, and a removed function is no
  longer linked. A links relation for a removed function, two for one
  function, a label edit of an absent function, and a whole-function and a
  label entry for one function are `LanguageError`s.

`extract_function` and `inline_function` use this shape through a single
`define` call (continuity.py).

## 5. Two transformations of the same state

**Decided:**

Scope: two results built from the same state are combined when the entities
they touch are disjoint, and rejected with their own error when they overlap,
not with the stale-source rejection.

**Provisional:**

Implemented:

    rebase(result, onto) -> TransformResult          (transforms.py)
        result and onto start from the same state, else ValueError.
        Returns result re-based to start from onto.destination.
    touched(result) -> frozenset[EntityID]           (transforms.py)
    TransformationConflict(ValueError)               (transforms.py)
    ActivationConflict(ActivationRejected,
                       TransformationConflict)       (runtime.py)

- The entities a result **touches** are those of its source whose value or
  owner changes, that disappear, or that map to anything but themselves,
  and those it creates. Overlapping touched sets are a
  `TransformationConflict`. An edit that moves a kept node under a new
  parent touches the parent and the function, not the kept node.
- Created node names that collide are renamed deterministically in the
  rebased result: every node the result created in generation `g` of `f`
  moves to the first later generation of `f` whose names are all free.
  Any other created entity whose name is taken (two results creating one
  function) is a conflict.
- The rebased result carries the result's changes (endpoints renamed), its
  non-identity mappings, its conversions and its owner changes over
  `onto`'s destination; what `onto` created maps to itself. A structural
  failure of the combination (an endpoint or an owner that is gone) is a
  conflict. Constraints are checked by activation, as for any result, so
  a combination that violates a constraint is rejected there, not as a
  `TransformationConflict`.
- Disjoint edits that create nothing commute: either order, and one
  `define` of both edits, give the same state.
- **Runtime.** `activate` of a result whose source is a state this runtime
  had active earlier rebases it over each result activated since, in
  order; a conflict raises `ActivationConflict`, which is both
  `ActivationRejected` and `TransformationConflict`, and leaves the runtime
  unchanged. A result from a state the runtime never had active is still
  rejected as stale, and is not a conflict. The runtime remembers every
  result it activated, without bound. `trial` rebases the same way,
  against the main runtime's history; the isolated runtime starts with an
  empty history.

## 6. Open

- A finer merge of two edits that both touch one function's value (its
  label or link table), which section 5 rejects: two label edits of one
  function combine only because a label edit whose root keeps its identity
  leaves the definition unchanged.
- Semantic conflicts outside the touched sets: an edit that relies on a
  callee the other edit changes.
- Moves between functions across two transformations.
- A bound on what the runtime remembers for rebasing.
- Name reuse by label edits: since a label edit leaves the generation as
  it is, a node it creates can take the name of a node an earlier label
  edit made disappear (`f/1.0` created, removed, created again). Advancing
  the generation would change the definition, so two label edits of one
  function that create nodes would then conflict in `rebase`.
- Whether a constraint failure of a combined state should be a
  `TransformationConflict` (section 5 leaves it to activation).
- Similarity matching; a changed subtree keeps its identity only by
  declared continuity, a label edit, or rule 2.

## 7. Acceptance tests

`tests/test_continuity_inference.py`: every corpus case holds; one old
node and two equal new ones keep neither; the largest unique subtree wins;
a changed kind at the root gives a new node; an identical body leaves the
state unchanged; a label wrap moves the node and the label; a label kind
change gives a new node and matches only inside its label; disjoint edits
rebase and commute, in the runtime too; overlapping edits and an edit
inside a removed function conflict; a result from an unknown state is
stale, not a conflict; `rebase` needs a common source.

`tests/test_matching.py`: uniqueness on each side, largest first, rule 2's
kind fallback, order independence and one-rule-per-kept-node as seeded
properties, a move between functions changing the owner, touched sets,
created-name renaming, two results creating one function, a combined state
that fails a check, and disjoint edits commuting as a property.
