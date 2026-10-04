# Graph Form

**Status: implemented.** `shear/lang.py` stores code in graph form and
`shear/bytecode.py` runs it (roadmap.md D1, tasks 4, 7 and 17).
`tests/test_graph_form.py` is the acceptance suite; the unit tests are at the
end of `tests/test_lang.py`, with closure graph-form behaviour additionally
covered by `tests/test_closures.py`.

Code is stored as graph form: every expression node is a relation entity
owned by its function. Tuple bodies with links relations (first_program.md)
remain the input format and the form of code as data. One virtual machine
runs graph form, after lowering each node to bytecode (bytecode.md).

## 1. Two forms

**Decided:**

D1.

    input format      Function(params, body) values and links relations
                      (first_program.md §2); what programs are written in,
                      what quote and function produce, what define takes
    graph form        a definition relation per function and one relation
                      entity per expression node; the only form that runs

`load(state)` converts the input format into graph form and
`function_at(state, f)` collapses one function back. `run` on a program
that was not loaded raises `LanguageError` saying so.

## 2. What a function entity holds

**Provisional:**

A function keeps its `EntityID`; its value becomes a `definition` relation:

    Relation("definition",
             {"body": <root node>, "link:<name>": <target>, ...},
             payload={"params": (...), "generation": g})

- `body` is the root node of the body.
- The **link table** is one `link:<name>` role per link of the input
  format's links relation. It is the scope that link names in new code
  resolve through (section 5). The links relation itself disappears.
  Link targets are roles, so a rename or disappearance of a target follows
  continuity like any endpoint (relation_model.md §5).
- `generation` counts the bodies the function has had; node names use it
  (section 4).

Keeping the link table matters because code as data still names targets by
link name: a body generated at run time and activated into `f` calls what
`f`'s links name, as before, including links `f`'s old body never used.

## 3. Node kinds and roles

**Decided:**

Kinds and roles.

**Provisional:**

Payload shapes.

The kind of a node is its operation. Operands that are code are nodes
referenced by roles; values that are not code are the payload. Calls, reads
and writes name their targets by role and keep the link name in the payload,
so `function_at` gives back the link names as written.

    kind                roles                              payload
    lit                 -                                  the literal
    arg                 -                                  parameter name
    add sub mul lt eq   left, right                        -
    if                  cond, then, else                   -
    seq                 items (ordered)                    -
    call                target, args (ordered)             link name
    read                cell                               link name
    write               cell, value                        link name
    tuple               items (ordered)                    -
    len                 tuple                              -
    item                tuple, index                       -
    slice               tuple, start, stop                 -
    concat              left, right                        -
    let                 value, body                        name
    ref                 target                             link name
    code                target                             link name
    linksof             target                             link name
    apply               function, args (ordered)           -
    applyv              function, args (one tuple)         -
    closure             body                               {"params": (...),
                                                           "captures": (...)}
    quote               holes (ordered)                    template, each
                                                           hole replaced
                                                           by ("unquote",)
    unquote             expr (only as a quote's hole)      -
    function            params, body                       -
    activate            targets, values (ordered)          {"links": ((name,
                                                           problem), ...)}
    trial               target, args, targets, values      {"call": (name,
                                                           problem), "links":
                                                           ...}
    invalid             -                                  (problem, original
                                                           expression)

**Leaves.** `lit`, `arg` and `invalid` relate nothing. They are relations
with no roles: the core now allows a nullary relation (relation_model.md
§2). The spike instead gave every node a `self` role pointing at itself; a
role that relates nothing to anything was a workaround, and the old rule
never guaranteed a relation relates something anyway, since a role may hold
an empty tuple. The alternative, leaves that are not relations, would make
a function own entities of two shapes and break "each expression node is a
relation entity".

**Checked when it runs.** Loading never fails on a body: an expression the
interpreter would reject (unknown operation, wrong arity, unknown link, a
malformed `unquote`, a `trial` whose first operand is not a call form)
becomes an `invalid` node that raises the same `LanguageError` when it is
evaluated, at the point the tuple interpreter raised it. Generated code
stays "checked when it runs" (metaprogramming.md §3), and `function_at`
returns the original expression.

For `activate` and `trial`, a link that does not resolve is recorded as a
`(name, problem)` entry and raised only when the pairs are checked, after
their values are evaluated (metaprogramming.md §4, language_trials.md §2).

**Data, let, references and closures.** `ref` and `code`
(self_hosting.md) name their function by the `target` role, like `call`, so
a rename of the function follows continuity; the value produced by `ref`, an
`EntityID`, is runtime data and does not automatically follow later renames.

A `closure` has exactly one code child, `body`. Its parameter and capture-name
tuples are payload, not child expressions. Evaluating the closure node captures
the named values from the current lexical environment and produces a runtime
`Closure` value referring to the owner function and body node. The body is
not evaluated during closure construction. `function_at` reconstructs:

    ("closure", params, captures, body)

with the body collapsed from its graph node.

A `let` whose name is not a non-empty string is an `invalid` node. That the
name is not already in scope is checked when the `let` runs, because a node
edit (section 9) replaces a node without seeing the `let`s around it. Closure
capture availability is likewise checked when the closure runs, against the
current lexical environment.

Tail position (language_data.md section 4) is a property of where a node sits,
not a node kind: the machine finds it while running (bytecode.md section 4).
Closure calls through `apply` or `applyv` follow the same rule.

**Quote.** The template stays data: only tuples headed `"unquote"` are
holes, lists, maps and records inside it are copied as they are, and holes
are filled in template order. Records inside a template are atoms. (The
tuple interpreter walked into their canonical encoding; no program in the
corpus or the suites depended on that.)

## 4. Node identity and ownership

**Provisional:**

A node's `EntityID` is `<function>/<generation>.<index>`, numbered in
preorder, so the root is index 0. Names are derived from the owning
function and the state being changed only, so `load` and `define` are
deterministic. A new body uses the function's next generation; if any of
its names is already taken by an entity of the state, the next free
generation is used instead, and a whole-function edit that creates a node
records the generation it used in the definition. No edit creates a node
under the name of an entity that exists, and a whole-function edit never
takes a name of a generation the definition has recorded. A label edit
leaves the recorded generation as it is (as before task 13), so a node a
later edit creates can take the name of a node that an earlier label edit
created and that has disappeared since (continuity_inference.md §6, Open).

Nodes are not content-addressed: equal subexpressions in two places are two
entities (identity_model.md; content-hashed ids would merge identity with
semantic equality).

A function owns all of its nodes directly, a flat set rather than a tree
shaped like the expression, and owns nothing else; `load` rejects an input
function that already owns entities. Removing a function (mapping it to
`()`) removes its nodes through the owned-subtree cascade
(ownership_model.md §7). Renaming one is an ordinary continuity mapping:
its nodes follow ownership continuity and keep their `EntityID` and
`VersionID`, and every call node naming it is rewritten by endpoint
continuity.

A closure value does not own its body node. The function already owns that
node. The closure retains only the semantic identities needed to find its
owner and body again in an active program version.

## 5. load, define, function_at

**Decided:**

`load`, `define`, and `function_at` as described below.

**Provisional:**

The `define` entries that create, remove and relink functions
(continuity_inference.md §4).

    load(state) -> State
        every entity holding a Function keeps its EntityID and gets a
        definition; its body becomes nodes placed under it; its links
        relation becomes its link table and disappears; everything else is
        unchanged. More than one links relation for a function is a
        LanguageError. A graph-form state loads to itself.

    define(state, edits) -> TransformResult
        edits functions, inferring what each edit keeps
        (continuity_inference.md). An entry is one of:
          f: Function        a new body for f; an f absent from the state
                             is created (generation 0)
          f: None            removes f and its nodes
          e: links(f, ...)   replaces f's link table (e is any key)
          (f, label): expr   replaces the labelled node (section 9)
        Link names in a new body resolve through f's new link table if the
        edit gives one, else its current one. All entries form one pool:
        an old node matched by continuity_inference.md §2 keeps its
        EntityID (and its VersionID when its content is equal), moving to
        the function whose new body holds it; an unmatched old node maps
        to () and disappears; an unmatched new node is created under its
        function (section 4). The result states destination ownership
        whole, so a move's owner change is explicit. Every other entity
        maps to itself. An edit that changes nothing gives the source
        state. The caller activates the result. A target that is not a
        function, an absent target that is not created, a links relation
        for a removed function, and a whole and a label entry for one
        function are LanguageErrors.

    function_at(state, f) -> Function | None
        collapses f back to the input format; None when f is absent or not
        a function. function_at(load(s), f) equals the Function s held.

`function_at` traverses closure bodies like any other code child. The closure
payload retains its parameter and explicit capture-name tuples unchanged
through load/collapse round trips.

Renaming a function stays a plain core transformation. Creating,
removing and relinking functions are `define` entries since task 13, so
that one `define` can move nodes between functions (extract, inline);
removal by a plain transformation still works. Every `define` infers,
including the one `activate` and `trial` build (section 6), so a
whole-function `activate` of an unchanged body leaves the state as it is.

## 6. How activate and trial build their transformation

**Decided:**

`activate` and `trial` keep their semantics (metaprogramming.md §4,
language_trials.md §2): values are evaluated first, then the active state is
read and the pairs are checked against it (each target a function, none
twice, each value a Function). The transformation is then
`define(active_state, {target: function, ...})`, which `Runtime.activate`
or `Runtime.trial` receives. A running frame keeps evaluating the nodes of
the version it started in, so code in flight is unchanged
(metaprogramming.md §5).

Closures do not change activation capability semantics. Creating or applying
one requires no activation grant. If activation preserves a closure's owner
and body identities, an already-created closure resolves those identities in
the active version when it is next applied; its captured values are not
recomputed.

## 7. Constraints over code

**Decided:**

A function's value holds only its definition, so a constraint relation over
a function would no longer see its code. The core now gives an owner
endpoint's owned subtree to constraint relations (relation_model.md §7):
the function contributes `{"value": <definition>, "owned": {node: ...}}`.
Program constraints over code (metaprogramming.md §4, language_trials.md
§4) keep working on graph form this way.

A closure body remains part of that owned subtree exactly like any other
expression child, so constraints over a function's code see closure code
without any closure-specific mechanism.

## 8. Open

- Whether a function should own its nodes as a tree shaped like the
  expression, which would let a subexpression be removed with its operands
  by one disappearance.
- Whether invalid code should be rejected at `load`/`define` instead, once
  the language has error handling.
- Whether the link table should be editable from the language.

## 9. Node edits

**Status: implemented** (roadmap.md task 5).

**Provisional:**

The node-edit design as a whole.

A program replaces one subexpression of a function without replacing the
function, so hot swapping has the granularity of node identity.

- **Labels.** `("label", name, e)` marks the node of `e` with a name unique
  within its function. It is transparent when run (it evaluates `e`), and
  `function_at` keeps it. A duplicate label in one function, or a name that
  is not a non-empty string, is a `LanguageError`.
- **Host.** `define` also accepts `(function, label): expression` entries,
  mixed with whole-function entries for other functions in one
  transformation. The labelled node and the nodes below it are the old
  side, the new expression the new side, and identity follows the
  expression (continuity_inference.md §2, which replaced the earlier rule
  that the labelled node always kept its `EntityID`): an unchanged unique
  subtree keeps its nodes (rule 1); the labelled node keeps its `EntityID`
  with the new root content only when the kind is the same (rule 2), so
  `1` to `10` keeps it and `1` to `2 + 3` gives a new node while the old
  one disappears; wrapping (`k` was `x`, now `double(x)`) keeps `x` under
  a new call. When the position gets a new node, the node that named the
  old one (or the definition, for the body root) changes to name it, and
  the label names it. Every node outside the label, and the function's own
  value unless its labels or body root change, keeps its `EntityID` and
  `VersionID`.
- **Language.** In `activate` and `trial`, a pair's target may be
  `(link, label)`, with an expression (code as data) as its value instead
  of a function value. Capability, checks, code in flight and atomicity
  are as for whole functions.
- **Closures.** Because a closure stores semantic owner/body identities
  rather than copying code, continuity of a closure body through a node edit
  determines whether an existing closure follows that edit. If continuity
  preserves the body identity, the closure invokes the active version of
  that body. If the identity disappears, applying the closure fails.
- **Errors** (`LanguageError`): an unknown label; a value that is not an
  expression (for example a function value) for a node target, or an
  expression for a function target; a replacement that introduces a label
  already used elsewhere in the function.
