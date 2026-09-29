Graph Ledger

Status: implemented (roadmap.md task 14). This ledger asks where graph
form provides leverage over a conventional compiler representation rather
than merely expressing the same information differently.

Measurements come from "semiroh/examples/ledger.py", which runs the existing
model. "tests/test_ledger.py" checks both that the script runs and that every
measurement quoted here matches its output.

1. Verdicts

Decided.

- Strong – graph form removes or materially simplifies bookkeeping that a
  conventional representation would otherwise need.
- Even – graph form gives the capability directly, but an AST with the
  usual compiler indexes can provide substantially the same result.
- Weak – graph form is not buying much here; an AST, especially one with
  stable node ids, would do as well.

These verdicts concern the present model, not what a future compiler might
make possible.

2. Ledger

Provisional. The capabilities and measurements are implemented; the
comparative verdicts are architectural judgements and may change as the
language grows.

Node identity across edits

Graph form: every expression is an entity. "lang.define" and
"matching.match" preserve an unchanged node's "EntityID" and, when its value
is unchanged, its "VersionID". Shown by "tests/test_continuity_inference.py"
and "tests/test_matching.py".

Ordinary compiler: an AST needs stable node ids plus an edit/reconciliation
algorithm that transfers those ids between old and new trees. A plain rebuilt
AST has no continuity.

Measurement: all 21 continuity cases hold; individual identity claims are
recorded below.

Verdict: Even. Stable AST node ids plus the same matcher can provide this.
The graph makes identity fundamental rather than an auxiliary annotation, but
does not eliminate the matching problem.

Hot swap of one labelled node

Graph form: a labelled expression is one graph entity. "lang.define" changes
that entity or replaces the local subtree; "Runtime.activate" installs the
resulting state. Shown by "tests/test_node_edits.py".

Ordinary compiler: an AST needs a stable node id or source anchor, a way to
rebuild the containing AST/function, and runtime version bookkeeping so code
already executing stays on the old version.

Measurement: a one-leaf edit of a 41-node and a 401-node function causes one
node to be relowered in either case.

Verdict: Even. Stable AST ids plus versioned functions can provide the same
externally visible operation.

Incremental compilation

Graph form: "bytecode.chunk_of" caches one chunk on each node "Value";
unchanged values carry the cache into the next state. There is no invalidation
walk. Shown by "tests/test_bytecode.py", "CacheTests".

Ordinary compiler: an AST needs stable node identity or content keys, a
derived-artifact cache, and either a dependency index/invalidation graph or
equally fine-grained per-node cache keys.

Measurement: a 41-node leaf edit relowers 1 node; a 401-node leaf edit also
relowers 1; replacing one leaf with five nodes relowers 5.

Verdict: Strong against function-level invalidation, but Even against
an AST with stable ids and a per-node artifact cache. The graph's gain is that
the cache key and dependency boundary already coincide with semantic node
identity.

A fold that declares its merges

Graph form: "fold.fold_constants" returns an ordinary "TransformResult";
folded-away source nodes explicitly map into the surviving node, and
"sources_of" reads that record. Shown by "tests/test_fold.py".

Ordinary compiler: an AST optimiser normally rewrites a tree and separately
needs origin/provenance metadata – source-node sets, debug-location unions, or
an optimisation provenance table – if later tooling must know which nodes
became which.

Measurement: the corpus fold changes 2 nodes and records 6 source identities,
3 for each folded node.

Verdict: Strong. The transformation relation used for program evolution is
also the optimiser's provenance record; no second provenance mechanism is
required.

Continuity inference for ordinary edits

Graph form: "matching.match" compares old and new graph subtrees – unique
unchanged subtrees first, then same-kind edited positions; ambiguity gets a
new identity. "lang.define" records the result as an ordinary transformation.
Shown by "tests/test_continuity_inference.py".

Ordinary compiler: an AST with stable ids needs essentially the same
tree-diff/reconciliation pass. A symbol table is additionally needed where
names resolve outside the tree.

Measurement: 21 of 21 corpus cases hold. Insert keeps 2 explicitly checked
identities; remove 2; wrap 1; unwrap 1; swap 3; shared subtree 3; ambiguous
duplicate 0.

Verdict: Weak. The graph supplies the identities to preserve, but not the
inference algorithm. A stable-id AST with the same matcher does just as well.

Moves between functions

Graph form: all entries of one "define" form one matching pool. A matched node
can keep its "EntityID" and "VersionID" while destination ownership changes to
another function. Shown by "tests/test_matching.py", "MoveTests", and the
"extract_function" / "inline_function" corpus cases.

Ordinary compiler: an AST needs stable node ids across different function
trees, a cross-tree matcher, updates to parent/function ownership, symbol-table
scopes, and any dependency indexes keyed by containing function.

Measurement: "extract_function" checks 3 retained identities;
"inline_function" checks 3. Both corpus cases hold.

Verdict: Even. The graph avoids treating containment as identity, but an
AST with detachable stable nodes and explicit ownership can represent the
same move.

Rebase of two edits of one state

Graph form: "transforms.touched" identifies affected entities and "rebase"
combines transformations with disjoint touched sets. "Runtime.activate" can
rebase a result produced from an earlier active state. Shown by
"tests/test_continuity_inference.py" and "tests/test_matching.py".

Ordinary compiler: a compiler/editor stack needs versioned AST snapshots,
stable ids, edit sets or structural diffs, conflict detection, and merge
logic. Dependency or symbol changes may require additional semantic conflict
checks.

Measurement: "rebase_disjoint" holds and checks 2 preserved identities;
"conflicting_edits" holds by rejecting the second transformation.

Verdict: Even. Immutable graph states and explicit transformations make
the inputs clean, but the conflict algorithm is still explicit machinery.
Current touched-set rebasing is intentionally coarse.

Relation endpoints and ownership follow renames

Graph form: core transformation application rewrites relation endpoints and
ownership through declared continuity. Calls, links, constraints and
ownership therefore follow the same rename mechanism. Implemented in
"transforms.py" and "relations.py"; shown by "tests/test_relations.py",
"tests/test_transforms.py", and continuity case "rename".

Ordinary compiler: an AST compiler needs a symbol table to distinguish
references from textual names, plus use/def or reference indexes to update
resolved references. Ownership/containment metadata needs its own update
rules.

Measurement: "rename" holds and the corpus checks 7 retained identities while
dependent relation values change where their endpoints move.

Verdict: Strong. One general endpoint-continuity rule replaces several
feature-specific rename/update paths.

Constraints over code

Graph form: code nodes are ordinary owned semantic entities. A constraint
relation whose endpoint is a function receives its definition plus owned node
subtree. Implemented in "constraints.py", "relations.py" and "runtime.py";
shown by "tests/test_constraint_relations.py".

Ordinary compiler: an AST compiler needs a constraint representation plus an
adapter exposing AST structure to it, dependency tracking for which
constraints depend on which declarations/nodes, and hooks to rerun affected
checks after edits.

Measurement: no scalar ledger measurement exists yet; the acceptance tests
exercise loading, writes and activation against owned subtrees.

Verdict: Strong structurally, Provisional empirically. The same
relation/ownership machinery used elsewhere exposes code to constraints
without a separate code-query representation, but there is no comparative
cost measurement yet.

3. Measurements

Decided. These comments are machine-checked by
"tests/test_ledger.py". Changing a quoted value without changing the model
makes that test fail.

Incremental compilation

A labelled leaf in a 41-node function relowers 1 node.

<!-- measurement:leaf_edit_41.nodes=41 --><!-- measurement:leaf_edit_41.re_lowered=1 -->The same edit in a 401-node function also relowers 1 node.

<!-- measurement:leaf_edit_401.nodes=401 --><!-- measurement:leaf_edit_401.re_lowered=1 -->Replacing one leaf with a five-node expression relowers exactly 5 nodes.

<!-- measurement:five_node_replacement.replacement_nodes=5 --><!-- measurement:five_node_replacement.re_lowered=5 -->Continuity corpus

The corpus contains 21 cases and 21 currently hold.

<!-- measurement:continuity.cases=21 --><!-- measurement:continuity.holding=21 -->The number below is the count of distinct source entities that each case
explicitly claims retain their identity through "kept", "changed", or "at".
It is not a count of every unchanged entity in the state.

<!-- measurement:continuity.activate_define.same_identity_claims=3 --><!-- measurement:continuity.ambiguous_duplicate.same_identity_claims=0 --><!-- measurement:continuity.conflicting_edits.same_identity_claims=0 --><!-- measurement:continuity.delete_called.same_identity_claims=0 --><!-- measurement:continuity.delete_function.same_identity_claims=2 --><!-- measurement:continuity.extract_function.same_identity_claims=3 --><!-- measurement:continuity.fold.same_identity_claims=4 --><!-- measurement:continuity.inline_function.same_identity_claims=3 --><!-- measurement:continuity.insert.same_identity_claims=2 --><!-- measurement:continuity.leaf_replace.same_identity_claims=4 --><!-- measurement:continuity.merge_cells.same_identity_claims=1 --><!-- measurement:continuity.rebase_disjoint.same_identity_claims=2 --><!-- measurement:continuity.redefine_same.same_identity_claims=3 --><!-- measurement:continuity.remove.same_identity_claims=2 --><!-- measurement:continuity.rename.same_identity_claims=7 --><!-- measurement:continuity.shared_subtree.same_identity_claims=3 --><!-- measurement:continuity.split_cell.same_identity_claims=0 --><!-- measurement:continuity.swap.same_identity_claims=3 --><!-- measurement:continuity.unwrap.same_identity_claims=1 --><!-- measurement:continuity.upgrade_cell.same_identity_claims=1 --><!-- measurement:continuity.wrap.same_identity_claims=1 -->Constant folding

The corpus fold contains 2 folded roots and their mappings record 6
source identities in total. Each surviving folded root has 3 recorded
sources.

<!-- measurement:fold.folded_nodes=2 --><!-- measurement:fold.recorded_sources=6 --><!-- measurement:fold.node:nested@1.sources=3 --><!-- measurement:fold.node:plain@.sources=3 -->4. What the graph is actually buying

Provisional.

The strongest current result is not that graphs can do things trees cannot.
Most rows can be reproduced with an AST once stable node ids, symbol tables,
dependency indexes and provenance records are added.

The graph earns its keep where those mechanisms collapse into the same
semantic machinery:

1. identity is already the unit on which derived bytecode is cached;
2. transformation mappings are also optimisation provenance;
3. relation endpoints and ownership use the same continuity rule for renames,
   merges and moves;
4. constraints can address code through the same entities and ownership used
   by execution and transformation.

Continuity inference itself is not a graph advantage. It remains a matching
problem, and the present rules would work over a stable-id AST.

5. Open

Open.

- Measure constraints over code against a conventional dependency-indexed
  implementation if constraint checking becomes expensive enough to matter.
- Revisit the rebase verdict when semantic conflicts beyond overlapping
  "touched" sets are implemented.
- Revisit the moves verdict once lexical/module scope exists; scope repair may
  expose a larger difference between graph ownership and AST containment.
- If a future implementation uses an AST with stable node ids underneath,
  compare its total bookkeeping directly with the semantic graph rather than
  treating “AST” as necessarily ephemeral.
