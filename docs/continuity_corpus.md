# Continuity Corpus

**Status: implemented** (roadmap.md task 12). `semiroh/continuity.py` holds
the format, the 21 cases and `check`; `tests/test_continuity_corpus.py` is
the acceptance suite and `tests/test_continuity_units.py` pins designator
resolution and what `check` reports. Section 5 lists which cases hold.

The canary corpus (corpus.md) checks what programs compute. This corpus
checks what a transformation does to identity: for each operation, which
entities survive, which are new, which disappear, merge or split, and what
activation does to cell content. The expected outcome of every case is
normative. Its status says whether the model meets it today.

## 1. Format

**Decided.**

Module `semiroh/continuity.py`:

    Expect(kept=(), changed=(), gone=(), new=(), at={}, merged={},
           split={}, rejected=None, cells={})
    Case(name, group, source, operation, expect, status, note,
         converters={}, context=None, writes={})
    CASES: tuple[Case, ...]
    GROUPS = ("declared", "inferred", "competing", "moved")
    check(case) -> tuple[str, ...]

`source` is a program in text syntax (syntax.md), loaded into graph form.
`operation(state)` returns a `TransformResult` (or a pair of them, for the
competing group), or raises. `check` returns the mismatches between what
happened and `expect`, each naming the designator involved; an empty result
means the expectation holds. `status` is `"holds"` or `"gap"`.

`writes` maps cell designators to content written into the running program
before the result is activated, so that a transfer can be told from a reset
to the declared initial content. `check` activates every result it gets; an
activation that raises is a mismatch unless `rejected` names it. For a pair
of results (group `competing`), `check` activates them one after the other
in both orders on one runtime: `rejected` is what the second raises, and
with none both must apply and the expectations are read on the final state,
against the mapping records of both results. `resolve(designator, before,
after=None)` gives the entity a designator names and raises `DesignatorError`
when it names nothing, and a node designator also requires the node to be
owned by its function.

**Designators** name entities without writing generated ids:

    fn:NAME            a function entity
    cell:NAME          a cell entity
    node:NAME@PATH     the node at PATH in function NAME, before
    after:NAME@PATH    the node at PATH in function NAME, after

A PATH is the input-form position of an expression: `""` is the body root,
and `"1.0"` is operand 0 of operand 1. Operands are counted in input form,
excluding link names, parameter names and labels (a label is transparent).
`before` designators resolve in the source state, `after` designators in
the destination state.

**Expectations**, each over designators:

- `kept`: present before and after, same `EntityID` and same `VersionID`;
- `changed`: present before and after, same `EntityID`, new `VersionID`;
- `gone`: absent after, and recorded in the result as a disappearance;
- `new`: absent before;
- `at`: `{before: after}`, the same `EntityID` at both positions (a node
  that survived and moved);
- `merged`, `split`: `{source: destination(s)}` as recorded in the
  result's mappings;
- `rejected`: the exception type the operation or the activation raises;
- `cells`: cell contents after activating the result, with `converters`.

Anything a case does not mention is not checked, except in the `declared`
group, where every function's nodes not mentioned must be `kept`.

## 2. Cases

**Decided** (expected outcomes), **Provisional** (the statuses, which
record the model today). Each is one `Case`. Programs are sketched here;
the module holds them in full.

Declared continuity (group `declared`): a host transformation with
explicit mappings. These pin the current rules.

| name | program and operation | expected |
| --- | --- | --- |
| `rename` | `double`, `quad` calling it; rename `double` to `twice` | `double`'s nodes kept, owned by `twice`; `quad`'s call nodes changed |
| `delete_function` | an unused function mapped to `()` | the function and all its nodes gone |
| `delete_called` | a called function mapped to `()` | rejected, `DanglingRelation` |
| `merge_cells` | cells `a`, `b` mapped into `a`, converter sums | merged; after activation `a` holds the sum |
| `split_cell` | a pair cell split into `left`, `right` | split; each holds its half |
| `upgrade_cell` | an `int` cell redeclared as a tuple, converted | changed; content converted |
| `fold` | `1 + 2` folded (constant_folding.md) | the root survives as the literal `3`; its operands as recorded by the fold |
| `activate_define` | a body replaced with `define` in a program with a cell | the cell's content transferred |

Inferred continuity (group `inferred`): an edit that declares no
continuity for the nodes it touches, made with `define`, whole-body or by
label. The expected outcome is the one inference should give.

| name | edit | expected |
| --- | --- | --- |
| `leaf_replace` | labelled `1` becomes `10` | the leaf changed, everything else kept |
| `insert` | `a + b` becomes `a + c + b` | `a`, `b` kept and `at` their new paths; the new `add` and `c` new |
| `remove` | `a + c + b` becomes `a + b` | `a`, `b` kept; `c` and the inner `add` gone |
| `wrap` | `x` becomes `double(x)` | `x` kept `at` the call's operand; the call new |
| `unwrap` | `double(x)` becomes `x` | `x` kept `at` the call's old position; the call gone |
| `swap` | `a - b` becomes `b - a` | `a`, `b` kept `at` swapped paths; the `sub` changed |
| `redefine_same` | `define` a function with its own body | every node kept |
| `shared_subtree` | `(x + 1) * 2` becomes `(x + 1) * 3` | `x + 1` kept |
| `ambiguous_duplicate` | `x + x` becomes `x` | the remaining `x` new (two candidates: never guessed) |

Competing rewrites (group `competing`): two transformations built from the
same state.

| name | rewrites | expected |
| --- | --- | --- |
| `rebase_disjoint` | edits of two different labels | both apply, in either order |
| `conflicting_edits` | two edits of the same label | the second rejected |

Moves across functions (group `moved`):

| name | edit | expected |
| --- | --- | --- |
| `extract_function` | `f(x): x * 2 + 1` becomes `g(x): x * 2` and `f(x): g(x) + 1` | the nodes of `x * 2` kept, now owned by `g`; the call new |
| `inline_function` | the reverse | `g`'s body nodes kept, now owned by `f`; `g` gone |

## 3. Acceptance tests

`tests/test_continuity_corpus.py` pins the format, the groups and the
required cases, runs `check` on every case, and checks the status: a
`holds` case must hold, and a `gap` case must still fail. A gap that
closes fails the test until its status is flipped, which is the point.

## 4. Implementation notes

- Operations use the model as it is: `transform_with_mapping`, `define`
  (whole body, or `(function, label)` entries), `fold_constants`,
  `Runtime.activate`. Where no operation can express a case yet (a move
  across functions, a rebase), the operation does the closest thing the
  model allows, and the case is a gap.
- Resolving a PATH needs the input-form position of each graph node. Build
  it from the function's graph (graph_form.md section 3) in `continuity.py`;
  do not change `lang.py` for it.
- The statuses in section 2 are predictions. Record what the model does;
  if a prediction is wrong, say so in the case's note and in the report.
- The moved cases and the inferred ones cannot be written with an operation
  that infers anything, so they use the closest thing there is: `define`
  of the whole body, or (across functions) loading the edited program with
  no continuity declared.

## 5. What holds today

**Provisional**, since it records the model as it is; task 13 flips gaps.
No prediction of sections 2 and 4 was wrong. Each case's `note` says what
the model does.

Holds (11): `rename`, `delete_function`, `delete_called`, `merge_cells`,
`split_cell`, `upgrade_cell`, `fold`, `activate_define`, `leaf_replace`,
`ambiguous_duplicate`, `conflicting_edits`. Declared continuity and the
label edit behave as specified. Two of them hold weakly:

- `ambiguous_duplicate` holds because nothing is inferred, so the remaining
  `x` is new like everything else; it must keep holding when inference
  exists.
- `conflicting_edits` holds because the runtime rejects any second result
  from the same source as stale, whether or not it conflicts.

Gaps (10), in three kinds:

- Whole-body `define` declares that every old node disappears and the new
  ones are created (`f/1.n`), so nothing is kept that a tree match would
  keep: `insert`, `remove`, `wrap`, `unwrap`, `swap`, `shared_subtree`, and
  `redefine_same`, where a body equal to the old one still renews every
  node.
- Nothing re-bases a result onto a later state: `rebase_disjoint` (two
  edits of different labels) is rejected as stale in either order.
- No operation moves a node to another function: `extract_function` and
  `inline_function`. Loading the edited program declares no continuity, and
  because `load` names nodes by function, generation and index, the ids
  `f/0.n` come back on other nodes.
