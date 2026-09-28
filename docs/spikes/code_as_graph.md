# Spike: code as a semantic graph

**Status: spike, not adopted.** Branch `spike/code-as-graph`,
`semiroh/graph_code.py`. Tests: `tests/test_graph_code_spike.py` (thin,
end-to-end only). Core modules (`identity`, `canonical`, `values`, `state`,
`relations`, `ownership`, `transforms`, `cells`, `constraints`, `runtime`)
were used unmodified.

Question: does putting the *code itself* in the semantic graph — one entity
per expression node, instead of one opaque tuple tree per function — pay
for itself. Built a second interpreter, `graph_code.py`, alongside
`lang.py`, over the same core, and converted `lang.py`'s own
`test_metaprogramming.py` fixture into it.

Design: a node is a `Relation` whose `kind` is the operation and whose
roles are its operand entities (a literal's value is `payload`; a leaf
node gets a `self` role only to satisfy "a relation needs ≥1 role"). A
function owns all of its nodes directly — a flat set, not a tree shaped
like the expression. `call`/`read`/`write` reference their target through
a role, not a link name.

## What per-node identity bought

**Locality of edits is real and free.** `edit_node` changes one node's
`Relation`; every other node — parent included, since parents hold their
child's `EntityID`, not its content — keeps the same `EntityID` *and*
`VersionID` (`test_editing_one_node_touches_only_that_node`). No cascade.
This is a genuine improvement over Unison's per-*definition* hash, where
editing one subexpression changes the whole definition's hash and every
caller must be repointed to it. Our model separates "what this node is"
(`EntityID`, stable) from "what it currently contains" (`VersionID`,
derived from content) at expression grain, not function grain — which is
what a system whose actual goal is *live* self-modification (not
Unison's offline, content-addressed dedup) needs.

**Renames are the core's `_follow_relation_endpoints`, not a rewrite.**
`rename_function` supplies one continuity mapping; every `call`/`read`
role naming the old entity anywhere in the state is rewritten by the
existing transformation machinery (`test_rename_keeps_callers_working`).
`lang.py`'s `links` relation turns out to be dead weight once code lives
in the graph: a role *is* a tracked reference (relation_model.md §4), so
the extra name-indirection layer `lang.py` needed for raw `EntityID`s
embedded in tuple data is no longer buying anything. `convert_program`
drops every `links` relation it finds.

**Hot-swap granularity did not actually improve at the language level.**
The `activate` op still replaces a function's whole body in one step,
exactly like `lang.py`; `edit_node`'s finer grain is host-only. Getting
language-level value from per-node identity would need a node-targeted
`activate`, which is a natural next step, not built here.

## What it cost

- **Code**: 871 lines vs. `lang.py`'s 732, for the same feature set —
  every node kind now needs a build case, an eval case, and a quote case
  (three dispatch tables instead of one), where `lang.py` needed only eval.
- **Entities per function**: `EMIT` (if/eq/quote/mul/unquote/call) is 13
  node entities. `POWER` after `COMPILE(5)` owns 11 nodes for a five-deep
  multiplication chain. The converted `test_metaprogramming` fixture grows
  from 17 entities to 53, then 63 after one `COMPILE(5)`.
- **Timing** (power example, `POWER(2)`, 20k calls): graph interpretation
  is *faster*, 13µs/call vs. 79µs/call, because `lang.py` re-decodes a
  whole function's nested canonical tuple on every call while the graph
  interpreter reads one small `Relation` per node as it walks. But
  *installing* generated code is slower — `COMPILE(12)` is 5.5ms vs. 2.8ms
  — because `State.__post_init__` re-serializes **every** entity in the
  state to derive `StateID` on every transformation, so a state with 3-5x
  more entities pays that cost on every activation, not just on the edit.
  Locality of identity does not imply locality of activation cost; that
  cost lives in the core state model, not in this design.
- **Friction with the core**: none required a code change, but two things
  are worth flagging. (1) A relation's "≥1 role" rule forced the `self`
  role hack for zero-operand nodes (`lit`, `arg`) — a small wart. (2) A
  content-hashed node id would have bought Unison-style structural
  deduplication for free, and was deliberately rejected: it would collapse
  "entity identity" into "semantic equality", which README invariants
  #4–#5 treat as a hard line. That is a designed trade-off, not an
  oversight — we get none of Unison's automatic dedup as a result.

## ownership_model.md §13 questions this forced

- *How ownership becomes part of the graph*: flat — a function owns all
  of its nodes directly, not a tree shaped like the expression. No change
  to the ownership store was needed.
- *Deletion vs. disappearance*: both are needed, for different callers, as
  ownership_model.md §7 already says. `remove_function` uses recursive
  `State.destroy` (a function no longer wanted at all).
  Whole-body `activate` uses transformation disappearance
  (`old_node → ()`) for a function's superseded nodes, because that is
  what composes inside a `TransformationDefinition`/`Runtime.activate`.
- *Program root*: deferred again, as in `first_program.md` — functions
  stay top-level; none of the four criteria needed one.
- *How creation places a new entity under its owner*: there is no
  automatic "owned by its creator" default. Every install path computes
  and supplies the **full** destination ownership map explicitly
  (ownership_model.md §10 requires this, not a patch). That is real,
  repeated boilerplate `transform_with_mapping` does not currently ease
  for ownership the way `changes` eases it for values — a plausible small
  core improvement, not attempted here.

## Recommendation: hybrid, not a wholesale switch

Adopt per-node graph form as an **explicit expansion**, not the default
representation of every function. The core already has the concept
(README §22, opaque vs. expanded representations); this spike is that
expansion made concrete, and it interoperates with the unmodified core.
Concretely: a function stays an opaque `lang.py`-style tuple body by
default; a tool that needs entity-grain access — a live editor targeting
one function, a metaprogram introspecting one function, a debugger that
wants a subexpression's identity to survive nearby edits — expands it
into graph form (`convert_program`'s per-function logic) and, if it must,
collapses it back (the `_quote_node` walk already does this, short of a
packaged round-trip). Making graph form the *only* representation is not
supported by what was measured: `StateID` recomputation scales with total
entity count, so a whole program in per-node form pays that cost on every
self-modification, for functions nobody is editing. That is a property of
the current core state model, not of per-node identity, so it argues for
selective adoption, not against the idea.
