# Bytecode and the Virtual Machine

**Status: implemented** (roadmap.md task 7, decision D2; extended by task 17).
`shear/bytecode.py` lowers, caches and disassembles chunks;
`shear/machine.py` executes them. `tests/test_bytecode.py` is the main
acceptance suite, with closure behaviour additionally covered by
`tests/test_closures.py`.

Graph form (graph_form.md) is the only semantic form that runs. Each
expression node lowers to a **chunk** of bytecode, and a virtual machine with
its own explicit stacks runs chunks. Bytecode is a derived artifact, never
part of semantic state: it does not change any `EntityID`, `VersionID` or
`StateID`.

## 1. What changed for the language

**Decided:**

Task 7 changed no observable language semantics except the recursion limit.
A call no longer uses the host's stack, so the number of calls that may wait
on each other moved from about 200 (the host's recursion limit, five Python
frames a call) to `CALL_DEPTH_LIMIT`, 100,000 (section 4).

The corpus programs `map_long_tuple` (a `map` over two thousand elements)
and `deep_recursion` (a sum ten thousand calls deep) run, where the first
failed from about 200 elements (corpus.md section 4). A runaway recursion
stops with `CallDepthExceeded`, a `LanguageError`, after about 1.5 s and
90 MB, where the old interpreter raised the host's `RecursionError`.

Results, exception types and messages, cell content, holds and the order of
effects are otherwise those of the interpreter it replaced, checked against
it before removal (section 6).

Roadmap task 17 extends the language itself with closures; the bytecode layer
represents their construction with `CLOSURE` and uses the existing
`APPLY`/`APPLYV` call machinery for invocation.

## 2. Chunks

**Decided:**

One chunk per node, children by reference.

**Provisional:**

The instruction set.

A chunk is a tuple of instructions ending with `END`. An instruction is a
plain tuple whose first item is its opcode, followed by operands that are
strings, ints, `EntityID`s or tuples of them:

    ("ARG", "x")
    ("MUL",)
    ("CALL", f, 2)
    ("CLOSURE", body, ("x",), ("n",))

`disassemble(chunk)` prints one instruction per line.

A chunk holds the instructions of **one node**. The nodes below it are named
by `EntityID` (`("EVAL", child)`), not inlined, so a chunk is a function of
its node's value alone: no owner, no state, no position, no other node.

The function that owns a node appears only when the machine executes the
chunk; it supplies lexical/runtime context and is used in errors.

    add(arg n, lit 1)       EVAL f/0.1
                            INT 'add'
                            EVAL f/0.2
                            INT 'add'
                            ADD
                            END

Why a chunk per node and not one flat body per function: the function's own
value does not hold its code, so an edit of one node (graph_form.md section
9) leaves the function's `VersionID` alone and a body-level artifact would
have nothing to be keyed by.

A chunk that inlines its children would be invalid whenever any node below it
changes, and every edit would lower all of the node's ancestors. By reference,
an edit gives one node a new value and only that node's chunk is stale
(section 5).

`lower(node)` builds the chunk of a node and never fails merely because code
is semantically invalid. An `invalid` node lowers to `RAISE`, so code remains
checked when it runs.

Two things differ from the removed interpreter for nodes that only a
hand-built state can hold, since `load` and `define` build neither. An
`unquote` node outside a quote, which is only ever a quote's hole, evaluates
its operand instead of raising "unknown operation". A node that lacks a role
raises `KeyError` when lowered, before operands that otherwise would have run.

## 3. Instructions

**Provisional:**

The stack is the operand stack of one run.

    LIT v               push the literal (decoded when it runs)
    ARG name            push a parameter, capture or let-bound name;
                        unknown is an error
    EVAL n              run node n, then continue here; its value is pushed
    GOTO n              continue as node n, in place of this chunk
    BRANCH a b          pop a bool; continue as node a if true, else b
    POP                 discard the top value
    INT op              the top value must be an int (op names the operation)
    TUPLE op            the top value must be a tuple; replace it by its items
    ADD SUB MUL LT      pop two ints, push the result
    EQ                  pop two values, push semantic equality
    LEN ITEM SLICE CONCAT
                        tuple operations on checked operands; bounds are
                        checked here
    MKTUPLE k           pop k values, push the tuple

    CALL f k            pop k arguments, call statically resolved function f
    REFCHECK            top value must be a function reference or closure
    APPLY k             pop k arguments and a callable, then call it
    APPLYV              pop an argument tuple and a callable, then call it

    REF f name          push f, which must name an installed function
    CLOSURE body params captures
                        capture the named lexical values and push a closure
                        whose code root is body

    CODE f name         push the code of function f as (params, body)
                        (self_hosting.md)
    LINKS f name        push the link table of function f as (name, entity)
                        pairs (vm_in_shear.md)

    LETCHECK name       the name must not already be in lexical scope
    LETBIND name n      pop a value, bind name to it, continue as node n

    READ cell           push the cell's content
    WRITE cell          write the top value; it stays on the stack

    QUOTE tmpl k        pop k hole values, push the filled template
    FUNCTION            pop a body and parameters, push a Function value

    ACTIVATE ..         pop the values, check the pairs, activate
    TRIAL ..            pop values and arguments, check, run in a trial

    RAISE message       raise LanguageError for this node
    END                 this chunk is done
    RETURN              (machine only) this call is done

`CLOSURE` does not execute its body. It records the current values of the
explicit capture names and stores the semantic owner/body identities in a
`Closure` value. Missing captures fail at construction.

`EVAL` is the only ordinary expression instruction that suspends the current
cursor. `GOTO`, `BRANCH` and `LETBIND` hand over without suspending the chunk,
and they are the last instruction of theirs: they are how tail position is
preserved (section 4).

## 4. The machine

**Decided:**

A run keeps an operand stack, a control stack of suspended cursors and the
live calls. A cursor is:

    (chunk, pc, tail, env, activation)

It records the chunk being run and where it is, whether its node is in tail
position, the lexical environment and the live activation whose held program
version supplies its nodes.

Nothing recurses in the host for ordinary calls: `EVAL` and non-tail calls
push control state; `END` and `RETURN` restore it.

- **Direct calls.** `CALL` enters the statically resolved function with
  `Runtime.enter`, reads its definition from the held state, checks arity and
  starts its body with parameters as `env`.

- **Indirect calls.** `APPLY` and `APPLYV` accept either an `EntityID`
  function reference or a `Closure`. `REFCHECK` has already rejected all
  other values before later arguments are evaluated.

- **Function-reference application.** The target must still exist in the
  active state. The machine enters it like a direct call and performs the
  ordinary function and arity checks.

- **Closure application.** The machine resolves the closure's owner and body
  in the active program state, enters the owner, then verifies in the held
  version that the owner is still a function, the body exists and still
  belongs to that owner, and the argument count matches the closure's
  parameters. The initial environment is the captured values overlaid with
  the supplied parameter bindings.

- **Code in flight** (metaprogramming.md section 5). Once a call has entered
  a version, its nodes come from that held state even if another version is
  activated while it runs. A later call enters the then-active version.
  Existing closures likewise resolve their semantic owner/body identities
  when called; their captured values are not recomputed.

- **Tail position** (language_data.md section 4) is a property of the cursor.
  The body root is in tail position; `GOTO`, `BRANCH` and `LETBIND` preserve
  it, while `EVAL` clears it. A `CALL`, `APPLY` or `APPLYV` reached in tail
  position reuses the live call: the machine enters the callee's frame and
  releases the caller's. This applies equally to closure calls. A chain of
  tail calls therefore keeps one live call, one frame and one hold.

- **Names.** `env` is copied at a `let`, as the interpreter copied its
  bindings. `LETCHECK` looks in `env` when the `let` runs, because a chunk
  cannot know the lexical scope around it. A closure snapshots only its
  declared names from that same environment.

- **Depth limit** (**Provisional**). A call that is not in tail position
  raises `CallDepthExceeded` when `CALL_DEPTH_LIMIT` calls (100,000, the
  entry among them) are already waiting. A tail call replaces its caller and
  adds no depth. The rule is independent of whether the target is a direct
  function, function reference or closure.

- **Trial.** `TRIAL` runs the linked function on a fresh machine over the
  isolated runtime, without the activation capability
  (language_trials.md). That is the only nested run, one per trial level.

- **Errors and cleanup.** A `LanguageError` names the function whose
  activation owns the executing node. Runtime and cell errors propagate as
  before (`CellError` becomes `LanguageError`, constraint rejections remain
  what they are). On any exception, outstanding holds are released in
  reverse activation order.

## 5. The cache

**Decided:**

A node's chunk is kept with the node's `Value`, like its `VersionID` and its
decoded relation (state_model.md section 4), and is lowered the first time
the node runs.

A value carried unchanged into a new state keeps its chunk. A `define` that
replaces one node gives that node a new value and lowers it again; its
siblings, its parents (which name it by `EntityID`) and every other function
keep theirs.

A rename rewrites the call nodes that name the function by endpoint
continuity, so those nodes, and only those, are new versions.

Nothing invalidates anything: a chunk is valid for as long as its value
exists, and a garbage-collected value takes its chunk with it. A function's
definition is kept with its value in the same way.

A closure does not cache a private copy of the body's chunk. It keeps the
body's semantic `EntityID`; when called, the active/held state supplies the
corresponding value and therefore that value's cached chunk.

`lowered_count()` counts the nodes lowered so far; the tests compare it before
and after an edit.

## 6. Order of effects

**Decided:**

Every check that could fail keeps its place relative to side effects before
or after it, because a write that already happened remains observable after
the error.

Thus:

- `INT` and `TUPLE` follow the operand they check and precede later operands;
- an `if` checks its condition before either branch runs;
- a `let` checks its name before its value runs;
- `apply`/`applyv` check that their target is a callable reference or closure
  before later arguments run;
- the active-state existence of the referenced function or closure
  owner/body is checked after those arguments have run;
- closure arity is checked when the closure call is opened;
- `trial` evaluates its call arguments before checking its edit pairs.

`tests/test_bytecode.py` and `tests/test_closures.py` pin these orderings,
including failures next to observable effects.

Differential checking before the tree interpreter was removed used 4000
seeded random programs (about 20,000 steps, a third succeeding, with
activations, node edits and trials). They ran on the interpreter of `main`
and on the bytecode machine with the same results, exception types and
messages, cell contents, collapsed functions, versions and holds.

One program differed only because the old interpreter reached Python's
recursion limit; with that limit raised it agreed. The harness was not kept
because there is no longer a second host interpreter to compare against.

Roadmap task 18 added broader differential, metamorphic and stateful testing,
including the independent self-hosted compiler and SHEAR VM paths.

## 7. Is per-node identity paying for itself?

**Provisional:**

On these measurements. The roadmap asked for a record if caching per node
version were not simpler and more precise than re-pointing dependents per
function.

It is simpler. The cache is the chunk kept on the value: no key, no
dependents index and no invalidation rule, and nothing to keep in step with
activation, trial or retirement. Re-pointing dependents per function would
need an index of which functions call which, updated at every activation.

It is more precise where the language now has the granularity, on node edits
(`tests/test_bytecode.py`, `CacheTests`):

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
small next to activation, which builds every node of a swapped body: an edit
of one leaf followed by a run took 1.1 ms against 2.0 ms for a whole-body
swap at 41 nodes, and 8.5 ms against 18.9 ms at 401.

The count is what per-node identity buys: in every row it is at most what
per-function lowering would give, and it costs no explicit dependency index.
Its value grows with the work attached to each node, for example compiler
passes such as roadmap task 9. Per-node identity is paying for itself,
modestly.

## 8. Derived bytecode and open limits

**Decided:**

Bytecode remains derived from semantic graph nodes. A program cannot install
a chunk as the executable definition of a host function.

Roadmap task 8 resolved the original self-hosting question by having the
compiler written in SHEAR emit bytecode as ordinary tuple data. Roadmap
task 10 then added an interpreter written in SHEAR that executes those
tuples. Task 17 extends both paths with closure bytecode.

Thus a program can produce and execute bytecode without making bytecode part
of semantic state or granting arbitrary emitted chunks directly to the host
machine.

**Open:**

- **Core canonicalization still uses the host stack.** A value nested a few
  hundred levels deep (measured: a function body nested about 244 levels, or
  a result built by recursion into a deeply nested tuple) exceeds the host
  recursion limit in `canonical_serialize`, where the machine itself cannot.
  This is a core limit, outside the machine.

- **Leaf inlining.** A chunk per leaf costs a push and a pop to run. Folding
  leaves into their parent would give up per-node precision for them; not
  done, since nothing needs it.

- **The depth limit** is one constant for every run, and counts calls, not
  memory. A run whose calls hold large values can use more than a run of the
  same depth with small ones. Whether it should be an option of `run`, or a
  budget like a constraint's (constraint_model.md), is open.

- **Chunk lifetime is the value's.** Nothing bounds the number of chunks
  alive at once except the values themselves.

- **Host execution of program-produced chunks.** The SHEAR-written VM
  demonstrates that such chunks can be run as data. Whether the host machine
  should ever accept one directly remains separate from the derived-bytecode
  model.
