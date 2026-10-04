# A Bytecode Interpreter in SHEAR

**Status: implemented** (roadmap.md task 10; extended by task 17).
`shear/lang.py` and `shear/bytecode.py` implement the operations below;
`shear/examples/vm.py` holds the interpreter and the program that swaps the
compiler onto it; `tests/test_vm.py` and `tests/test_closure_self_hosting.py`
cover the interpreted path.

Task 8 wrote the compiler in the language and checked its output against the
host's. This step runs that output: an interpreter for the chunks of `lower`,
written in SHEAR, so a program can compile a function of its own, swap in a
function that runs the chunk on the interpreter, and do this to the compiler
itself (self_hosting.md section 5). The host's virtual machine still runs
everything; the interpreter is one more program on it.

Task 17 extended this path with lexical closures. The interpreter therefore
has its own semantic representation of callable values rather than depending
on the host Python `Closure` record.

## 1. Reflection and indirect calls

**Provisional:**

    ("applyv", f, args)     call callable value f with the items of tuple args
    ("linksof", link)       the link table of the linked function, as a tuple
                            of (name, entity) pairs sorted by name

`applyv` is `apply` with the arguments in a tuple, so that an interpreter can
call with a count it only knows at run time. `f` may be either a function
reference or a closure. It evaluates `f`, checks that it is callable,
evaluates `args`, checks that it is a tuple, and then follows the ordinary
call rules.

In graph form `applyv` has `function` and `args` roles and lowers to:

    EVAL
    REFCHECK
    EVAL
    TUPLE
    APPLYV

`linksof` returns the names a function's code may use and the entities they
name, read from the active version, like `code`. It gives the interpreter the
table that resolves names in `CALL` and `REF`. Links that do not name a single
entity are left out.

In graph form `linksof` is a node with a `target` role and the link as payload,
like `code`; it lowers to `LINKS`.

Neither operation reads or writes a cell.

## 2. The interpreter

**Provisional:**

`vm(chunk, params, args, links)` runs a chunk as `lower` emits it
(self_hosting.md section 2): `EVAL`, `GOTO`, `BRANCH`, `LETBIND` and
`CLOSURE` contain the expanded chunk of their child where applicable.

The machine is:

    vm_run(chunk, pc, stack, env, links)

The operand stack is a tuple, the environment a tuple of `(name, value)`
pairs, and the program counter an index.

Helper functions provide:

    vm_lookup      lexical lookup
    vm_has         lexical-name membership
    vm_find        link-table lookup
    vm_bind        parameter binding
    vm_capture     capture selected lexical bindings
    vm_apply       apply a tagged callable
    vm_trap        produce an error by an invalid operation

Every instruction tail-calls `vm_run` with the next program counter where
possible. `EVAL` recursively runs a child; `GOTO`, `BRANCH` and `LETBIND`
tail-call it.

`CALL`, `APPLY` and `APPLYV` are final operations in the chunks emitted by
`lower`, so interpreted tail calls remain tail calls through the interpreter.

The interpreter handles:

    LIT ARG EVAL GOTO BRANCH POP END
    INT TUPLE ADD SUB MUL LT EQ
    LEN ITEM SLICE CONCAT MKTUPLE
    CALL REFCHECK APPLY APPLYV REF CLOSURE
    LETCHECK LETBIND

This is the pure subset of the bytecode instruction set needed by the
self-hosted compiler and closure tests.

## 3. Callable representation

**Decided:**

The interpreter represents callable values as tagged semantic tuples.

A function reference is:

    ("ref", entity)

A closure is:

    ("closure", body, params, captures, links)

where:

- `body` is the expanded bytecode chunk for the closure body;
- `params` is its parameter tuple;
- `captures` is the captured lexical environment as `(name, value)` pairs;
- `links` is the link table of the function in which the closure was created.

This representation is internal to the SHEAR-written VM. It intentionally
does not reuse the host Python `Closure` record.

`CLOSURE` constructs that value by calling `vm_capture` for the declared
capture names. Only explicitly declared names are copied.

`REFCHECK` verifies that the value has either the `ref` or `closure` tag
before later call operands run.

`vm_apply` dispatches by tag:

- `ref` delegates to ordinary `applyv` on the referenced installed function;
- `closure` checks arity, binds parameters over the captured environment, and
  runs the stored body with the closure's stored links;
- anything else traps.

Thus another closure can itself be captured as an ordinary semantic value.

## 4. Where it differs from the host machine

**Provisional:**

Each deviation has tests defining the current behaviour.

- **Errors are made by doing.** The language has no general raise operation,
  so checks use existing failing operations: `INT` adds zero, `TUPLE` takes
  the length, and `vm_trap` indexes an empty tuple. The resulting failure is
  still a `LanguageError`, but its message need not match the host machine's.
- **`REF` does not itself prove that its linked entity is a function.** It
  creates a tagged reference to the resolved entity. Applying it later goes
  through the ordinary host `applyv` semantics, which rejects a non-function.
- **`READ`, `WRITE`, `CODE`, `LINKS` and `RAISE` are not interpreted.**
  Functions containing those instructions can be compiled and their chunks
  passed to the interpreter, but execution traps at the unsupported
  instruction.
- The VM's closure value contains expanded bytecode and a captured link table,
  while the host closure contains semantic graph identities. The two paths are
  required to agree observably over the subset the interpreted VM supports,
  not to share representation.

The old task-10 deviation where `REFCHECK` did nothing is gone: task 17 needed
the interpreter to distinguish tagged function references and closures before
evaluating later arguments.

## 5. Swapping onto the interpreter

**Decided:**

`shear/examples/vm.py` builds `swap_all()`. It reads each function of the
compiler (`upper`, `evals`, `seq_code`, `lower`) with `code` and `linksof`,
compiles it with `lower`, and activates one function per name with the same
parameters and a body equivalent to:

    ("call", "vm", ("lit", chunk), ("lit", params),
     ("tuple", ("arg", p), ...), ("lit", links))

That is one `activate` with four pairs: a run may activate once under the
two-version bound, so they are installed together.

The functions need a `vm` link, which `compiler_entities` takes as an extra.
`swap_upper()` and the other `swap_*` helpers swap one function and return its
chunk.

The interpreter's own functions are not swapped, since the swapped interpreter
would otherwise call itself recursively through the same abstraction layer.

After `swap_all()`, compiler calls pass through the SHEAR-written
interpreter and `lower` produces the same results as before. Compiling its own
source on its own bytecode therefore reaches the same bootstrap fixpoint.

## 6. Checks

The acceptance suites cover:

- `applyv` and `linksof`: values, checks and order, tail calls, graph-form
  round trip and lowering;
- each supported instruction against the host machine;
- seeded random pure programs, including failures;
- interpreted tail recursion under a deliberately low host-machine call limit;
- interpreted non-tail recursion;
- `swap_all` and the individual swap helpers;
- the compiler bootstrap fixpoint;
- activation-capability requirements for swapping;
- the `bootstrap` corpus example;
- `CLOSURE` construction;
- capture of lexical values;
- tagged `REFCHECK`;
- applying tagged references and closures;
- closure arity rejection;
- host compiler versus embedded compiler closure lowering;
- execution of compiled closure code by the SHEAR VM.

Mutation testing of `vm.py` remains part of the broader verification suite.

The SHEAR interpreter is intentionally much slower than the host machine;
performance is not its purpose. It exists as an independent executable path
for compiler output.

## 7. Open

**Open:**

- **Cells from the interpreter.** `READ` and `WRITE` would need a cell chosen
  by value. That makes a value into a read/write capability in a way static
  links currently are not.
- **`CODE` and `LINKS` by reference** for a genuinely meta-circular
  interpreter, and how the regress of an interpreter running itself should
  terminate.
- **General error construction.** A language-level error operation would let
  the interpreted VM reproduce host-machine failures and messages more
  precisely instead of trapping through unrelated invalid operations.
- **Speed.** A tuple program counter and stack copy data per instruction, and
  opcode dispatch is a chain of comparisons. Numeric opcodes or a dispatch
  table could improve this if performance ever matters.
- Whether the host machine should execute an arbitrary chunk constructed by a
  program (self_hosting.md section 5, bytecode.md section 8). The interpreted
  path demonstrates that program-produced bytecode can already be executed
  without granting that capability to the host machine.
