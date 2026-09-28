# Graph Form

**Status: implemented.** `semiroh/lang.py` stores code in graph form and
`semiroh/bytecode.py` runs it (roadmap.md D1, tasks 4 and 7).
`tests/test_graph_form.py` is the acceptance suite; the unit tests are at the
end of `tests/test_lang.py`.

Code is stored as graph form: every expression node is a relation entity
owned by its function. Tuple bodies with links relations (first_program.md)
remain the input format and the form of code as data. One virtual machine
runs graph form, after lowering each node to bytecode (bytecode.md).

## 1. Two forms

**Decided** (D1).

    input format      Function(params, body) values and links relations
                      (first_program.md §2); what programs are written in,
                      what quote and function produce, what define takes
    graph form        a definition relation per function and one relation
                      entity per expression node; the only form that runs

`load(state)` converts the input format into graph form and
`function_at(state, f)` collapses one function back. `run` on a program
that was not loaded raises `LanguageError` saying so.

## 2. What a function entity holds

**Provisional.**

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

**Decided** (kinds and roles), **Provisional** (payload shapes).

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
    apply               function, args (ordered)           -
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

**Data, let, references** (language_data.md). `ref` names its function by
the `target` role, like `call`, so a rename of the function follows
continuity; the value it produces, an `EntityID`, is runtime data and does
not. A `let` whose name is not a non-empty string is an `invalid` node.
That the name is not already in scope is checked when the `let` runs,
because a node edit (section 9) replaces a node without seeing the `let`s
around it. Tail position (language_data.md section 4) is a property of where
a node sits, not a node kind: the machine finds it while running
(bytecode.md section 4).

**Quote.** The template stays data: only tuples headed `"unquote"` are
holes, lists, maps and records inside it are copied as they are, and holes
are filled in template order. Records inside a template are atoms. (The
tuple interpreter walked into their canonical encoding; no program in the
corpus or the suites depended on that.)

## 4. Node identity and ownership

**Provisional.**

A node's `EntityID` is `<function>/<generation>.<index>`, numbered in
preorder, so the root is index 0. Names are derived from the owning
function and the state being changed only, so `load` and `define` are
deterministic. A new body uses the function's next generation; if any of
its names is already taken by an entity of the state, the next free
generation is used instead. A node name is therefore never reused while
its function's definition records the generation, and never collides with
an existing entity.

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

## 5. load, define, function_at

**Decided.**

    load(state) -> State
        every entity holding a Function keeps its EntityID and gets a
        definition; its body becomes nodes placed under it; its links
        relation becomes its link table and disappears; everything else is
        unchanged. More than one links relation for a function is a
        LanguageError. A graph-form state loads to itself.

    define(state, {f: Function}) -> TransformResult
        replaces whole bodies. Link names in each new body resolve through
        f's link table. f's old nodes map to () and disappear, the new
        nodes are created under f with placements (ownership_model.md
        §10), f gets a new definition, and every other entity maps to
        itself. The caller activates the result. A target that is absent
        or not a function is a LanguageError.

    function_at(state, f) -> Function | None
        collapses f back to the input format; None when f is absent or not
        a function. function_at(load(s), f) equals the Function s held.

Host edits that are not whole-body replacements (rename, removal) are
plain core transformations.

## 6. How activate and trial build their transformation

**Decided.**

`activate` and `trial` keep their semantics (metaprogramming.md §4,
language_trials.md §2): values are evaluated first, then the active state is
read and the pairs are checked against it (each target a function, none
twice, each value a Function). The transformation is then
`define(active_state, {target: function, ...})`, which `Runtime.activate`
or `Runtime.trial` receives. A running frame keeps evaluating the nodes of
the version it started in, so code in flight is unchanged
(metaprogramming.md §5).

## 7. Constraints over code

**Provisional.**

A function's value holds only its definition, so a constraint relation over
a function would no longer see its code. The core now gives an owner
endpoint's owned subtree to constraint relations (relation_model.md §7):
the function contributes `{"value": <definition>, "owned": {node: ...}}`.
Program constraints over code (metaprogramming.md §4, language_trials.md
§4) keep working on graph form this way.

## 8. Open

- Whether a function should own its nodes as a tree shaped like the
  expression, which would let a subexpression be removed with its operands
  by one disappearance.
- Whether invalid code should be rejected at `load`/`define` instead, once
  the language has error handling.
- Whether the link table should be editable from the language.

## 9. Node edits

**Status: implemented** (roadmap.md task 5). **Provisional** as a whole.

A program replaces one subexpression of a function without replacing the
function, so hot swapping has the granularity of node identity.

- **Labels.** `("label", name, e)` marks the node of `e` with a name unique
  within its function. It is transparent when run (it evaluates `e`), and
  `function_at` keeps it. A duplicate label in one function, or a name that
  is not a non-empty string, is a `LanguageError`.
- **Host.** `define` also accepts `(function, label): expression` entries,
  mixed with whole-function entries in one transformation. The labelled
  node keeps its `EntityID` and takes the new expression's root content;
  the nodes below it are replaced, the old ones disappearing and the new
  ones placed under the function. Every other node, and the function's own
  value unless its labels change, keeps its `EntityID` and `VersionID`.
- **Language.** In `activate` and `trial`, a pair's target may be
  `(link, label)`, with an expression (code as data) as its value instead
  of a function value. Capability, checks, code in flight and atomicity
  are as for whole functions.
- **Errors** (`LanguageError`): an unknown label; a value that is not an
  expression (for example a function value) for a node target, or an
  expression for a function target; a replacement that introduces a label
  already used elsewhere in the function.
