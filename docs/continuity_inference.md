# Continuity Inference

**Status: planned** (roadmap.md task 13). Deterministic rules for the
continuity nobody declares: which nodes an edit by `define` keeps, how a
node moves between functions, and what happens to two transformations of
the same state. Done when every case of the continuity corpus holds
(continuity_corpus.md) and `tests/test_continuity_inference.py` passes.

## 1. Terms

**Decided.**

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

**Decided** (owner, 2026-09-29: identity follows the expression, and the
edited position keeps its identity only as a same-kind fallback).

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
on its own. Nothing is matched by similarity.

Consequences:

- **graph_form.md §9 changes.** A labelled node keeps its `EntityID` only
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
  An existing test that pins fresh nodes for an unchanged part is renamed
  to what it now checks, and listed in the PR.

**Provisional.**

- Leaves match like any subtree, so a unique literal or argument that
  moves to another position within the scope keeps its identity there.
- The order among equal-sized new subtrees is preorder of the new side,
  entries in `define`'s sorted order; with rule 1 as stated the result
  does not depend on it, and a test should say so.
- A function's generation advances only when the edit creates a node.

## 3. What `define` records

**Provisional.** The result stays an ordinary core transformation: kept
nodes map to themselves, disappeared ones to nothing, created ones are
placed. A matched node whose operands changed (rule 2) is a change of an
existing entity. Ownership of a node that moves between functions is
stated as explicit destination ownership (transformation_model.md §13),
never left to change implicitly.

## 4. Moves across functions

**Decided** (scope): within one `define`, a node matched to a node of
another function keeps its `EntityID` and changes its owner to the function
whose new body holds it. It keeps its `VersionID` when its content is
equal; if a compiled chunk depends on the function (say, a parameter's
position), it is changed instead, and the PR says so.

**Provisional** (operation): the moved cases need one `define` that
creates, removes and relinks functions. Preferred shape, closest to the
input format `parse` gives:

- a `Function` for an entity absent from the state creates that function;
- `None` for a function removes it (a mapping to nothing; its unmatched
  nodes go with it);
- a links relation for a function (`lang.links`) replaces its link table,
  so a new body may call a function created in the same `define`, and a
  removed function is no longer linked.

Whatever shape is chosen, `extract_function` and `inline_function` use it
through a single `define` call, and the PR names it.

## 5. Two transformations of the same state

**Decided** (scope): two results built from the same state are combined
when the entities they touch are disjoint, and rejected with their own
error when they overlap, not with the stale-source rejection.

**Provisional:**

    rebase(result, onto) -> TransformResult          (transforms.py)
        result and onto start from the same state, else ValueError.
        Returns result re-based to start from onto.destination.
    TransformationConflict(ValueError)               (transforms.py)

- The entities a result **touches** are those of its source whose value or
  owner changes, that disappear, or that map to anything but themselves,
  and those it creates. Overlapping touched sets are a
  `TransformationConflict`.
- Created node names that collide are renamed deterministically in the
  rebased result (the function's next free generation); any other created
  entity whose name is taken is a conflict.
- The combined state passes the usual checks (endpoints exist, ownership
  is a forest, constraints). A failure there is a conflict too, since each
  result was valid alone.
- Disjoint edits that create nothing commute: either order, and one
  `define` of both edits, give the same state.
- **Runtime.** `activate` of a result whose source is a state this runtime
  had active earlier rebases it over each result activated since, in
  order; a conflict raises an error that is both `ActivationRejected` and
  `TransformationConflict`. A result from a state the runtime never had
  active is still rejected as stale, and is not a conflict. The runtime
  remembers the results it activated.

## 6. Open

- A finer merge of two edits that both touch one function's value (its
  label or link table), which section 5 rejects.
- Semantic conflicts outside the touched sets: an edit that relies on a
  callee the other edit changes.
- Moves between functions across two transformations.
- A bound on what the runtime remembers for rebasing.
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

## 8. Implementation notes

- The corpus: flip the ten gaps to `holds`. Sources and expectations are
  normative; only operations (the moved cases), statuses and notes change.
  Record in each note what the model now does.
- Keep matching in one place that `define` calls (a new module is fine);
  add it to the mutation targets and the model map.
- Update graph_form.md §§5, 9, the runtime's activation doc, the corpus
  doc's section 5, CHANGES.md, the roadmap (task 13 done) and the model map.
- Unit tests for the rules beyond the acceptance tests, including the
  order-independence of rule 1.
