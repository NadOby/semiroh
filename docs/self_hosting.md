# Reading Code, and a Compiler in SEMIROH

**Status: implemented** (roadmap.md task 8). `semiroh/lang.py` and
`semiroh/bytecode.py` implement `code`; `semiroh/examples/self_hosting.py`
holds the compiler and the self-rewriting program; `tests/test_self_hosting.py`
is the acceptance suite.

Two pieces: an operation with which a program reads the code of a function
as data, and the lowering pass of bytecode.md written in the language,
checked against the host's. The owner chose the scope: the compiler emits
bytecode as data and is checked against the host; bytecode stays derived and
the host still runs what it lowers itself. Running what the compiler emits
is a later step (section 5).

## 1. `code`

**Decided:**

The `code` operation, except which version it reads.

**Provisional:**

Which version `code` reads.

    ("code", link)      (params, body) of the linked function, in input form

`params` is the tuple of parameter names and `body` the expression tree that
`function_at` returns and that `load` accepts: link names as written, labels
as `("label", name, e)`. It is the same data `quote` builds, so a program
can take it apart with `item`, `slice` and `len`, rewrite it and hand it to
`function`. In graph form `code` is a node with a `target` role and the link
name as payload, exactly like `ref`, so a rename of the function follows by
continuity. It lowers to one instruction, `CODE f name`.

- It reads the function from the **active** version, not from the version
  the running frame was entered in. **Provisional.** After an `activate` in
  the same run, `code` shows the code the next call would run. Reading needs
  no activation capability.
- A link that does not resolve is an `invalid` node, and a link that names
  something that is not a function is a `LanguageError`, both when the node
  runs.
- Tuples in the result that come from a canonical value read at run time
  may be canonical nodes, as for any tuple the language takes apart. They
  compare equal to plain tuples by `eq` and by canonical serialization, not
  by Python `==`.
- Installing a function's own code back with `activate` and `function`
  gives the same input form and a new version: a whole-function swap builds
  new nodes (graph_form.md section 9). Keeping node identity through a swap
  is roadmap.md task 9.

## 2. The compiler

**Provisional:**

The shape of the output and what is covered.

`lower(e)`, in `semiroh/examples/self_hosting.py`, takes an expression in
input form and returns its chunk. The host's chunk names its children by
`EntityID` (bytecode.md section 2); a program has no entities for the
expression it is holding, so the chunk it produces holds each child's chunk
in place of a reference. Called the *expansion* of a node:

- `EVAL c`, `GOTO c`, `BRANCH a b`, `LETBIND name c` hold chunks;
- an operand that is an entity (`CALL f k`, `REF`, `CODE`, `READ`, `WRITE`)
  is the link name, and `REF f name` is `REF name`;
- `LIT v` holds the value.

`tests/test_self_hosting.py` computes the expansion of the host's chunk of
the same expression and compares it with `lower`'s output.

Covered: every operation of the language except `quote`, `unquote`,
`function`, `activate` and `trial`; `label` costs nothing, as in graph form.
Anything else lowers to `RAISE "unknown operation"`. It assumes a
well-formed expression: it does not check arities, link names or `let`
names, which the host's `load` turns into an `invalid` node that raises when
it runs. An empty `seq` is the one shape it does check, as it is the one the
host also reports as a node.

The compiler is written in the language it covers: `lower`, `upper`
(opcode names), `evals` and `seq_code` (the variable-length operand lists)
use only covered operations. `self_lower()` compiles `lower` by reading it
with `code`, and the test compares that with the host's chunk of `lower`.

## 3. Checks

**Decided:**

- Every operation it covers, in a curated list; 60 seeded random
  expressions over them.
- Each function of the compiler, lowered by the compiler, against the host.
- `self_lower`, the program that reads and compiles its own `lower`.
- Its uncovered operations lower to a `RAISE`.
- Mutation testing (`SEMIROH_MUTATE`, testing docs in CLAUDE.md) of the
  compiler's source: 43 of 45 seeded mutants of `self_hosting.py` fail the
  suite; the two others change no behaviour (a cell bound, an unused
  quote).

## 4. A program that rewrites itself

**Decided:**

The corpus example `instrument` has a cell `hits`, a function `work(x)` and
a function `instrument()`. `instrument` reads `work` with `code`, builds a
function whose body is `work`'s body behind a write that adds one to `hits`,
activates it, and then compiles the code now installed with `lower`, which
sees the new version. Its result is the chunk of what it installed. The
test compares that with the host's expansion of the installed nodes; the
scenario checks that `work` counts, that the swap needs the activation
capability, and that no function but `work` changes version.

## 5. What this is not

- The compiler's output is not run by the host. Bytecode stays derived from
  the graph (bytecode.md section 8), and the host lowers what its VM runs. So
  the swap in section 4 installs input form, and the self-hosted compiler
  reports on it; it does not produce the code that runs.
- **Done in roadmap.md task 10** (vm_in_semiroh.md): a bytecode interpreter
  written in SEMIROH runs the chunks the compiler emits, so a program
  compiles a function of its own and swaps in one that runs its own chunk,
  the compiler included. It needed `applyv` and `linksof`, not `code` by
  reference.

## 6. Open

- Whether `code` should take a function reference (`ref`) instead of a link,
  so a program can read a function it only holds a reference to. The
  interpreter in section 5 needs some such way.
- Whether reading a function's nodes should keep their identity (return
  entities), which a continuity-keeping pass (roadmap.md task 9) needs.
- Covering `quote`, `function`, `activate` and `trial` in the compiler.
- Values taken apart at run time may be canonical nodes; whether a run
  should hand back plain tuples is open.
