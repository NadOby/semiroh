# Constant Folding as a Graph Transformation

**Status: implemented** (roadmap.md task 9). `semiroh/fold.py` implements it
and `tests/test_fold.py` is its acceptance suite.

The first compiler pass that changes code and keeps its identity honest:
folding constants is written as a transformation of a graph-form state that
declares, for every node it changes or removes, where it continues. Nothing
about the pass enters identity; the continuity is metadata of the
`TransformResult` (transformation_model.md sections 5 and 17).

## 1. What it does

**Provisional** (the set of operations).

`fold_constants(state)` returns a `TransformResult` for every function of a
graph-form state. It folds:

- `add`, `sub`, `mul` on two constant ints, and `lt` on two constant ints;
  `eq` on any two constants, by semantic equality (`1` and `True` differ);
- `if` with a constant bool condition: the `if` is replaced by the branch it
  takes;
- a constant is a `lit`, or one of the above over constants; so
  `add(1, mul(2, 3))` and `if(lt(1, 2), 5, x)` fold in one step.

It leaves alone whatever could raise, so that the optimised code raises what
the original raised: an operand that is not an int (a string, a bool, a
tuple), an `if` whose condition is not a bool, and everything that reads a
cell, writes, calls, applies, or takes an argument. Around such a node the
rest of the expression still folds.

## 2. The continuity it declares

**Decided.**

Every entity the pass does not touch maps to itself, so its `EntityID` and
`VersionID` stay.

- **A constant subtree** becomes one `lit`. The subtree's root keeps its
  `EntityID` and takes the literal; every node below it is **merged** into
  it: the mapping sends the root and each node below it to the root (many to
  one, transformation_model.md section 5). The merged nodes are gone. The
  root's parent still names the root, so it is not touched.
- **An `if` with a constant condition** is replaced by the branch it takes.
  The `if` node and the nodes of the condition are merged into that branch's
  root, which keeps its `EntityID` and its content; the other branch
  **disappears** (maps to nothing). The parent of the `if` follows by
  endpoint continuity and gets a new version. If the branch is itself an
  `if` that folds, the mapping goes to the node that finally takes its
  place, never to one that disappears.
- **Labels** (graph_form.md section 9) follow their node: a label inside a
  folded subtree ends up on the subtree's root, and a label on an `if` ends
  up on the branch. A fold that would make a labelled node disappear (it sits
  in the branch not taken) is not done: labels name the nodes a program edits
  and silently dropping one is an ambiguity.

`sources_of(result, node)` gives the nodes of the source state that continue
into a node of the destination: the node itself if it was there, and every
node folded into it. That is the mapping of optimised code to its source
nodes, and it stays in the result for as long as the caller keeps it.

The folded state is the state that loading the folded code would give when
the nodes come out the same: folding `add(x, mul(add(1, 2), 5))` gives
exactly the state `load` gives for `add(x, 15)`. How the code was reached
does not enter its identity.

## 3. Hot swap

**Decided.**

The result is activated like any other (`Runtime.activate`); a running
program swaps to the folded code, and a frame in flight keeps the nodes it
was entered with (metaprogramming.md section 5). After the swap only the
nodes with a new version are lowered again (bytecode.md section 5): folding
`add(x, mul(3, 4))` lowers one node, the new literal.

## 4. Checks

- Curated cases for each operation, for what stays, for labels, and for the
  declared mappings (who merges into whom, who disappears, who is untouched).
- 150 seeded random programs, some of which raise, behave the same before
  and after folding on several arguments, results and exceptions alike, fold
  to a fixed point, and never grow; every source node has a mapping whose
  destinations exist.
- Mutation testing (`SEMIROH_MUTATE`) of `fold.py`: every one of its 64
  sites was tried; the two that survive change nothing (a dataclass flag and
  a return value that is never used).

## 5. Open

- The pass is host code. Writing it in SEMIROH needs a way to build and
  apply a transformation from inside the language (self_hosting.md).
- Further folds: `seq` of constants, `len`/`item` on tuple literals,
  algebraic identities (`x + 0`), inlining a call to a constant function.
  Each is one more case with its own mapping.
- Composing the mapping through later transformations (a fold, then a rename)
  is possible for definitions (transformation_composition.md) but not for
  results; `sources_of` reaches one step back.
- The pass does not run itself. When an optimiser runs, and whether a fold
  is one activation or part of the next, are decisions for a program that
  needs it.
