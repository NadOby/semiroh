# A Bytecode Interpreter in SEMIROH

**Status: implemented** (roadmap.md task 10). `semiroh/lang.py` and
`semiroh/bytecode.py` implement the two operations below;
`semiroh/examples/vm.py` holds the interpreter and the program that swaps the
compiler onto it; `tests/test_vm.py` is the acceptance suite.

Task 8 wrote the compiler in the language and checked its output against the
host's. This step runs that output: an interpreter for the chunks of
`lower`, written in SEMIROH, so a program can compile a function of its own,
swap in a function that runs the chunk on the interpreter, and do this to the
compiler itself (self_hosting.md section 5). The host's virtual machine still
runs everything; the interpreter is one more program on it.

## 1. Two operations

**Provisional.**

    ("applyv", f, args)     call the function f refers to with the items of
                            the tuple args
    ("linksof", link)       the link table of the linked function, as a tuple
                            of (name, entity) pairs sorted by name

`applyv` is `apply` with the arguments in a tuple, so that an interpreter can
call with a count it only knows at run time. It evaluates `f`, checks that it
is a reference, evaluates `args`, checks that it is a tuple, and then behaves
exactly as `apply` (frame, arity check, tail position, active state). It is
a node like `apply`: `function` and `args` roles, lowering to
`EVAL, REFCHECK, EVAL, TUPLE, APPLYV`.

`linksof` returns the names a function's code may use and the entities they
name, read from the active version, like `code`. It gives the interpreter the
table that resolves the name in a `CALL` or `REF` to a reference; links that
do not name a single entity are left out. A link that names a cell comes back
as an entity too, and `applyv` of it is the same error as `apply` of it.
In graph form `linksof` is a node with a `target` role and the link as payload,
like `code`; it lowers to `LINKS`.

Both are reflection, in the sense of self_hosting.md: a program can find out
what a function links and call what it finds. Neither reads or writes a cell.

## 2. The interpreter

**Provisional.**

`vm(chunk, params, args, links)` runs a chunk as `lower` emits it
(self_hosting.md section 2): `EVAL`, `GOTO`, `BRANCH` and `LETBIND` hold the
chunk of their child. The machine is `vm_run(chunk, pc, stack, env, links)`:
the operand stack is a tuple, the environment a tuple of `(name, value)`
pairs, and the program counter an index. Five small functions carry the rest:
`vm_lookup`, `vm_has`, `vm_find` (a name in the link table), `vm_bind`
(parameters to arguments) and `vm_trap`.

- Every instruction is a tail call of `vm_run` with the next `pc`, so a
  chunk runs in constant space.
- `EVAL` calls `vm_run` on the child and pushes the result; `GOTO`, `BRANCH`
  and `LETBIND` tail call it. `END` returns the top of the stack.
- `CALL`, `APPLY` and `APPLYV` are the last instruction before `END` in every
  chunk `lower` emits, so the call is the value of the chunk and is a tail
  call of the machine. An interpreted tail call is therefore a tail call all
  the way down, and interpreted non-tail recursion nests only as deep as the
  program does: a sum 30,000 calls deep runs (about four machine calls to
  an interpreted call, against `CALL_DEPTH_LIMIT` of 100,000).
- The dispatch is a chain of `if`s on the opcode name, the most frequent
  first.

It runs: `LIT ARG EVAL GOTO BRANCH POP END INT TUPLE ADD SUB MUL LT EQ LEN
ITEM SLICE CONCAT MKTUPLE CALL REFCHECK APPLY APPLYV REF LETCHECK LETBIND`,
which is every operation of the language that does not touch a cell or code
as data.

## 3. Where it differs from the machine

**Provisional.** Each is a deviation for which a test says what happens.

- **Errors are made by doing.** The language has no way to raise, so a check
  is the operation itself: `INT` adds zero, `TUPLE` takes the length, an
  unknown name or an unknown opcode indexes an empty tuple. The error is a
  `LanguageError` all the same, with another message.
- **`REFCHECK` does nothing.** The host checks that the function is a
  reference before it evaluates the arguments; the interpreter has no test
  for it and the check happens at the call, after the arguments ran. It
  shows only in side effects of the arguments of a call that was going to
  fail.
- **`REF` does not check that its link names a function.**
- **`READ`, `WRITE`, `CODE`, `LINKS` and `RAISE` raise.** Naming a cell or
  reading a function by name from the interpreter needs a way to reach them
  by value; a cell reached that way is a capability question the language
  has not had to answer (section 6). A function that uses them can be
  compiled, and its chunk can be handed to the interpreter; running it
  raises where the machine would have run it.

## 4. Swapping onto the interpreter

**Decided.**

`semiroh/examples/vm.py` builds `swap_all()`. It reads each function of the
compiler (`upper`, `evals`, `seq_code`, `lower`) with `code` and `linksof`,
compiles it with `lower`, and activates one function per name that has the
same parameters and the body

    ("call", "vm", ("lit", chunk), ("lit", params),
     ("tuple", ("arg", p), ...), ("lit", links))

That is one `activate` with four pairs: a run may activate once (the
two-version bound), so they go together. The functions need a `vm` link,
which `compiler_entities` takes as an extra. `swap_upper()` and the other
`swap_*` swap one function and return its chunk. The interpreter's own
functions are not swapped, since the swapped function would call itself.

After `swap_all()` every call of the compiler goes through the interpreter,
and `lower` gives what it gave: on the tests' expressions and on its own
source. Compiling its own source on its own bytecode gives the chunk it gave
before the swap, the fixpoint of a bootstrap.

## 5. Checks

- `applyv` and `linksof`: their values, the checks and their order, tail
  calls through `applyv`, graph form round trip and lowering.
- Each instruction the interpreter runs, and the errors it makes, against the
  machine on the same function; 60 seeded random programs, some that raise,
  compile with `lower` and run on the interpreter as they run on the machine.
- Interpreted tail recursion under a lowered call limit (500 deep against
  a limit of 60) and interpreted non-tail recursion 300 deep.
- `swap_all` and `swap_upper`: same results before and after, the functions
  replaced, the fixpoint, the capability needed, and the corpus example
  `bootstrap`.
- Mutation testing (`SEMIROH_MUTATE`) of `vm.py`: 88 of its 90 sites are
  caught; the two others change no behaviour. It found that the results of
  `CALL` never need to be pushed, which is why they are not.
- Speed: the interpreter is about 90 times slower than the machine on the
  same work (the compiler compiling its own source: 57 ms, 5.1 s). The tests
  that use it take about 15 s together.

## 6. Open

- **Cells from the interpreter.** `READ` and `WRITE` need a cell chosen by
  value. That makes every reference a capability to read and write, which the
  static links never were. Whether references to cells exist, and how a
  program is granted one, is a design question for a program that needs it.
- **A check for a reference** (`REFCHECK`), or a way to raise from the
  language, so that the interpreter's errors match the machine's and the
  order of effects too.
- **`CODE` and `LINKS` by reference** for the interpreter to run itself
  (a meta-circular interpreter), and the regress that swapping the interpreter
  for a version that runs on itself would need to end.
- **Speed.** A `pc` and a stack as tuples cost a copy per instruction;
  a chunk is a tree, so dispatching on an opcode name is a chain of
  comparisons. A numbering of opcodes, or a table lookup, would help; neither
  has been needed.
- Whether the host machine should run a chunk a program made (self_hosting.md
  section 5, bytecode.md section 8): the interpreter shows that a program can
  run its own chunk without that.
