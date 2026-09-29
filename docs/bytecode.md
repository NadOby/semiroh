# Bytecode and the Virtual Machine

**Status: implemented** (roadmap.md task 7, decision D2). `semiroh/bytecode.py`
implements it and `tests/test_bytecode.py` is its acceptance suite. The
corpus and every language suite run on it unchanged; one interpreter
remains, and it is this machine.

Graph form (graph_form.md) is the only form that runs. Each expression node
lowers to a **chunk** of bytecode, and a virtual machine with its own
explicit stacks runs chunks. Bytecode is a derived artifact, never part of
semantic state: it does not change any `EntityID`, `VersionID` or `StateID`.

## 1. What changed for the language

**Decided:**

Nothing observable, except the limit on recursion. A call no longer uses
the host's stack, so the number of calls that may wait on each other moved
from about 200 (the host's recursion limit, five Python frames a call) to
`CALL_DEPTH_LIMIT`, 100,000 (section 4). The corpus programs
`map_long_tuple` (a `map` over two thousand elements) and `deep_recursion`
(a sum ten thousand calls deep) run, where the first failed from about 200
elements (corpus.md section 4). A runaway recursion stops with
`CallDepthExceeded`, a `LanguageError`, after about 1.5 s and 90 MB, where
the interpreter raised the host's `RecursionError` at once. Results,
exception types and messages, cell content, holds and the order of effects
are otherwise those of the interpreter it replaces, checked against it
(section 6).

## 2. Chunks

**Decided:**

One chunk per node, children by reference.

**Provisional:**

The instruction set.

A chunk is a tuple of instructions ending with `END`. An instruction is a
plain tuple whose first item is its opcode, followed by operands that are
strings, ints, `EntityID`s or tuples of them: `("ARG", "x")`, `("MUL",)`,
`("CALL", f, 2)`. `disassemble(chunk)` prints one instruction per line.

A chunk holds the instructions of **one node**. The nodes below it are named
by `EntityID` (`("EVAL", child)`), not inlined, so a chunk is a function of
its node's value alone: no owner, no state, no position, no other node. The
function that owns a node appears only in error messages, and the machine
adds it when it raises.

    add(arg n, lit 1)       EVAL f/0.1          the left operand, a node of f
                            INT 'add'           check it, before the right runs
                            EVAL f/0.2
                            INT 'add'
                            ADD
                            END

Why a chunk per node and not one flat body per function: the function's own
value does not hold its code, so an edit of one node (graph_form.md section
9) leaves the function's `VersionID` alone and a body-level artifact would
have nothing to be keyed by. A chunk that inlines its children would be
invalid whenever any node below it changes, and every edit would lower all
of the node's ancestors. By reference, an edit gives one node a new value
and only that node's chunk is stale (section 5).

`lower(node)` builds the chunk of a node and never fails on code. An
`invalid` node lowers to `RAISE`, so code is still checked when it runs.

Two things differ from the interpreter for nodes that only a hand-built
state can hold, since `load` and `define` build neither. An `unquote` node
outside a quote, which is only ever a quote's hole, evaluates its operand
instead of raising "unknown operation". A node that lacks a role raises
`KeyError` when it is lowered, before the operands that would have run first,
where the interpreter raised it when the node was reached.

## 3. Instructions

**Provisional:**

The stack is the operand stack of one run.

    LIT v               push the literal (decoded when it runs)
    ARG name            push a parameter or let-bound name; unknown is an error
    EVAL n              run node n, then continue here; its value is pushed
    GOTO n              continue as node n, in place of this chunk
    BRANCH a b          pop a bool; continue as node a if true, else b
    POP                 discard the top value
    INT op              the top value must be an int (op names the operation)
    TUPLE op            the top value must be a tuple; replace it by its items
    ADD SUB MUL LT      pop two ints, push the result
    EQ                  pop two values, push semantic equality
    LEN ITEM SLICE CONCAT   tuple operations on the checked operands;
                        bounds are checked here
    MKTUPLE k           pop k values, push the tuple
    CALL f k            pop k arguments, call the function entity f
    REFCHECK, APPLY k   the reference to a function, then a call of it
    REF f name          push f, which must be a function (a reference)
    CODE f name         push the code of function f as (params, body)
                        (self_hosting.md)
    LINKS f name        push the link table of function f as (name, entity)
                        pairs (vm_in_semiroh.md)
    APPLYV              like APPLY, with the arguments in one tuple
    LETCHECK name       the name must not be in scope
    LETBIND name n      pop a value, bind name to it, continue as node n
    READ cell           push the cell's content
    WRITE cell          write the top value; it stays on the stack
    QUOTE tmpl k        pop k hole values, push the filled template
    FUNCTION            pop a body and parameters, push a Function value
    ACTIVATE ..         pop the values, check the pairs, activate
    TRIAL ..            pop the values and arguments, check, run in a trial
    RAISE message       raise LanguageError for this node
    END                 this chunk is done
    RETURN              (machine only) this call is done

`EVAL` is the only instruction that nests. `GOTO`, `BRANCH` and `LETBIND`
hand over without suspending the chunk, and they are the last instruction of
theirs: they are how tail position is found (section 4).

## 4. The machine

**Decided:**

A run keeps an operand stack, a control stack of suspended cursors and the
live calls. A cursor is `(chunk, pc, tail, env, call)`: the chunk being run
and where it is, whether its node is in tail position, the names in scope,
and the call it belongs to. Nothing recurses in the host: `EVAL` and `CALL`
push a cursor and `END` and `RETURN` pop one.

- **Calls.** `CALL` and `APPLY` enter a frame in the runtime
  (`Runtime.enter`), read the function's definition from the state the frame
  is on, check the arity and start its body with its parameters as `env`.
  The frame is released by `RETURN`, so every run leaves no holds and a run
  that raises releases all its frames, innermost first.
- **Code in flight** (metaprogramming.md section 5). A call reads its nodes
  from the state its frame was entered in, whatever is activated while it
  runs. The next `CALL` enters the new active version.
- **Tail position** (language_data.md section 4) is a property of the cursor:
  the body root is in tail position, and `GOTO`, `BRANCH` and `LETBIND` keep
  it, while `EVAL` clears it. A node in tail position was reached without
  suspending anything, so the cursor below it is its call's `RETURN`, and a
  `CALL` there reuses the call: it enters the callee's frame, then releases
  the caller's. A chain of tail calls keeps one call, one frame and one hold.
- **Names.** `env` is copied at a `let`, as the interpreter copied its
  bindings. `LETCHECK` looks in `env` when the `let` runs, since a chunk
  cannot know the scope around it and a node edit does not see it either
  (graph_form.md section 3).
- **Depth limit** (**Provisional**). A `CALL` that is not in tail position
  raises `CallDepthExceeded` when `CALL_DEPTH_LIMIT` calls (100,000, the
  entry among them) are already waiting in the run; a call in tail position
  replaces its caller and is never one more. The stacks are not the host's,
  so without a limit a runaway recursion would use all the memory there is;
  100,000 calls take about 90 MB and 1.5 s. It is a safety fuse of the
  reference model, a constant that tests may patch, not a rule of the
  language. A trial runs on its own machine, with its own count.
- **Trial.** `TRIAL` runs the linked function on a fresh machine over the
  isolated runtime, without the activation capability
  (language_trials.md). That is the only nested run, one per trial level.
- **Errors.** A `LanguageError` names the function whose node raised it:
  after a tail call, the callee. Errors of the runtime and of cells
  propagate as they did (`CellError` becomes `LanguageError`, constraint
  rejections stay what they are).

## 5. The cache

**Decided:**

A node's chunk is kept with the node's `Value`, like its `VersionID` and its
decoded relation (state_model.md section 4), and is lowered the first time
the node runs. A value carried unchanged into a new state keeps its chunk. A
`define` that replaces one node gives that node a new value and lowers it
again; its siblings, its parents (which name it by `EntityID`) and every
other function keep theirs. A rename rewrites the call nodes that name the
function by endpoint continuity, so those nodes, and only those, are new
versions. Nothing invalidates anything: a chunk is valid for as long as its
value exists, and a garbage-collected value takes its chunk with it.
A function's definition is kept with its value in the same way.

`lowered_count()` counts the nodes lowered so far; the tests compare it
before and after an edit.

## 6. Order of effects

**Decided:**

Every check that could fail keeps its place relative to side effects that
come before or after it, as the interpreter had it, because a write that
already happened is observable after the error. So `INT` and `TUPLE` follow
each operand and precede the next one, an `if` checks its condition before
a branch runs, a `let` checks its name before its value runs, `apply` checks
that its function is a reference before it evaluates the arguments and that
the entity exists after, and `trial` evaluates its call's arguments before
it checks its pairs. `tests/test_bytecode.py` plants a write next to each.

Differential check before the tree interpreter was removed: 4000 seeded
random programs (about 20,000 steps, a third succeeding, with activations,
node edits and trials) run on the interpreter of `main` and on the machine
gave the same results, exception types and messages, cell contents,
collapsed functions, versions and holds. One program differed: the
interpreter reached its Python recursion limit; with the limit raised it
agreed. The harness was not kept, since there is no second interpreter to
run it against.

## 7. Is per-node identity paying for itself?

**Provisional:**

On these measurements. The roadmap asked for a record if caching per node
version were not simpler and more precise than re-pointing dependents per
function.

It is simpler. The cache is the chunk kept on the value: no key, no
dependents index and no invalidation rule, and nothing to keep in step with
activation, trial or retirement. Re-pointing dependents per function would
need an index of which functions call which, updated at every activation.

It is more precise where the language now has the granularity, on node
edits (`tests/test_bytecode.py`, `CacheTests`):

| change | nodes lowered again |
| --- | --- |
| a leaf of a function of 41 nodes replaced | 1 |
| a leaf of a function of 401 nodes replaced | 1 |
| a leaf replaced by an expression of 5 nodes | 5 |
| one function replaced whole (3 new nodes) | 3, and none of any other function |
| a callee renamed, two calls to it | 2, the call nodes |

Lowering per function would lower the whole function each time: 41, 401, 13
(the function of the third row, after the replacement) and the three nodes of
the caller in the last row. For a whole-body replacement it is the same, all
its nodes being new.

Lowering itself is cheap, about 0.8 µs a node (a function of 401 nodes runs
in 428 µs with its chunks and 752 µs without them), so the time saved is
small next to the activation, which builds every node of a swapped body: an
edit of one leaf followed by a run took 1.1 ms against 2.0 ms for a
whole-body swap at 41 nodes, and 8.5 ms against 18.9 ms at 401. The count is
what per-node identity buys: in every row it is at most what per function
would give, and it costs nothing. Its value will grow with the cost of
lowering, for instance if a compiler pass runs on every node (roadmap.md
task 9). Per-node identity is paying for itself, modestly.

## 8. Open

- **Emitting bytecode.** The self-hosting milestone (roadmap.md task 8)
  needs a program to produce bytecode as data. A chunk is a tuple of
  instructions, so that is expressible, but a chunk only means something
  next to the nodes it names, and there is no way to install one: chunks
  are derived from nodes, never given. Whether bytecode becomes a semantic
  value, a function whose code is a chunk graph, or stays derived and the
  compiler in SEMIROH produces graph form, is task 8's decision.
- **Core canonicalization still uses the host stack.** A value nested a few
  hundred levels deep (measured: a function body nested about 244 levels,
  or a result built by recursion into a deeply nested tuple) exceeds the
  host recursion limit in `canonical_serialize`, where the machine itself
  cannot. This is a core limit, outside the machine.
- **Leaf inlining.** A chunk per leaf costs a push and a pop to run. Folding
  leaves into their parent would give up per-node precision for them; not
  done, since nothing needs it.
- **The depth limit** is one constant for every run, and counts calls, not
  memory: a run whose calls hold large values can use more than a run of
  the same depth with small ones. Whether it should be an option of `run`,
  or a budget like a constraint's (constraint_model.md), is open.
- **Chunk lifetime is the value's.** Nothing bounds the number of chunks
  alive at once but the values themselves.
