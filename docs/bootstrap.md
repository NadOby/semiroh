# Hosted Bootstrap Boundary

**Status: provisional.** Roadmap task 28, issue #64. This document
records the current implementation boundary and proposes the hosted
services for decision D4. It does not settle D3 or D4.

Baseline: `main` at `081ba0d0882e9c02906a3f6a4081f77d2907e897`.

## 1. Scope and terminology

The four routes are:

1. Host lowering: graph-form nodes lowered by `shear.bytecode.lower`.
2. Host execution: those chunks executed by `shear.machine`.
3. SHEAR lowering: input-form expressions compiled by the SHEAR
   program `lower` in `shear/examples/self_hosting.py`.
4. SHEAR-VM execution: expanded chunks interpreted by the SHEAR
   program `vm` in `shear/examples/vm.py`.

The fourth route is itself executed by the Python-hosted machine.
"Host execution" and "SHEAR-VM execution" describe which interpreter
implements the program's instructions, not the absence of Python.

**Status definitions:**

- **S – Supported:** the route has an implementation of the operation
  for valid inputs. This does not promise that every other route
  needed to reach it is supported.
- **R – Rejected:** the operation intentionally represents invalid
  code and produces an explicit failure rather than useful execution.
  Lowering may produce a failure instruction instead of raising.
- **D – Deferred:** the route lacks the operation's intended
  semantics. Its current behavior must fail explicitly. An observed
  failure is not evidence of implementation support.

The matrix describes the current implementation, not the intended
post-task-30 subset. It is not a declaration that the complete
hosted-bootstrap pipeline already works.

The host may supply declared runtime primitives and semantic services.
It must not silently replace SHEAR compilation or interpreted execution
of program code with host compilation or execution. An explicitly
declared seed, verifier, or reference oracle is a separate role.

## 2. Operation support matrix

**Provisional:** classification of the current implementation.
Every row corresponds to exactly one operation in
`shear.operations.OPERATIONS`.

| Operation | Host lower | Host run | SHEAR lower | SHEAR VM |
| --- | --- | --- | --- | --- |
| `lit` | S | S | S | S |
| `arg` | S | S | S | S |
| `add` | S | S | S | S |
| `sub` | S | S | S | S |
| `mul` | S | S | S | S |
| `lt` | S | S | S | S |
| `eq` | S | S | S | S |
| `if` | S | S | S | S |
| `seq` | S | S | S | S |
| `call` | S | S | S | S |
| `read` | S | S | S | D |
| `write` | S | S | S | D |
| `quote` | S | S | D | D |
| `unquote` | S | S | D | S |
| `function` | S | S | D | D |
| `closure` | S | S | S | S |
| `activate` | S | S | D | D |
| `trial` | S | S | D | D |
| `tuple` | S | S | S | S |
| `len` | S | S | S | S |
| `item` | S | S | S | S |
| `slice` | S | S | S | S |
| `concat` | S | S | S | S |
| `let` | S | S | S | S |
| `catch` | S | S | D | D |
| `raise` | S | S | D | D |
| `ref` | S | S | S | S |
| `code` | S | S | S | D |
| `linksof` | S | S | S | D |
| `apply` | S | S | S | S |
| `applyv` | S | S | S | S |
| `invalid` | R | R | R | R |

`label` belongs to input syntax, not `OPERATIONS`. SHEAR lowering
recognizes it transparently without introducing a graph operation.

### 2.1 Evidence

Host lowering is implemented by `bytecode.lower`, including its
activation helper. Host execution dispatches in `machine._execute`.
`invalid` lowers to an explicit `RAISE` instruction.

SHEAR lowering's supported subset is
`self_hosting.LOWERED - {"label"}`. Operations outside that subset
currently produce `RAISE "unknown operation"` rather than delegating
to `bytecode.lower`. The diagnostic is generic and does not by itself
distinguish a deferred operation from an unknown spelling.

SHEAR-VM execution is determined by the instruction cases in
`vm._cases` and their dispatch in `vm._run_body`. The interpreter
covers the pure subset, including `CLOSURE`, but not `READ`, `WRITE`,
`CODE`, `LINKS`, `QUOTE`, `FUNCTION`, `ACTIVATE`, `TRIAL`, `CATCH`,
`FAIL`, or `RAISE`. Unsupported instructions reach `vm_trap`.

`unquote` is exceptional: host lowering emits `GOTO`, whose expanded
instruction semantics the SHEAR VM implements. SHEAR lowering does
not independently compile `unquote`, so this does not establish a
complete SHEAR-to-SHEAR-VM route for it.

The interpreter's `CALL` can invoke an installed function through
ordinary `applyv`. If the callee is host-compiled program code, that
dependency must be reported; instruction support alone is not proof
of end-to-end bootstrap execution.

### 2.2 Boundary invariants

**Decided (existing semantic constraints):**

- The semantic graph is authoritative; chunks are derived artifacts.
- A compiled chunk does not establish semantic identity or continuity.
- Producing a candidate and activating it remain distinct.
- An activation must pass existing checks and capability rules.
- Runtime cell content does not enter `StateID`.
- Failed or unsupported execution must not activate a candidate.
- Arbitrary program-produced chunks are not directly admitted to
  host execution by the current implementation.

**Provisional (bootstrap enforcement):**

- An unsupported operation must fail on its selected route, without
  calling a different route to implement it.
- The permitted host-service set is explicit and auditable.
- Provenance distinguishes seed compilation, SHEAR compilation,
  fixed interpreter machinery, and executed program code.
- A positive execution result cannot conceal an undeclared host
  compilation or host-executed program-code dependency.

## 3. Host-service inventory

**Provisional:** these are recommended allowances, not an approved D4
boundary. Each entry gives its contract, implementation, proposed
allowance, and existing or planned verification.

"Allow" means Python may implement that service during hosted bootstrap.
"Conditional" means its use or admission rule depends on D3/D4.
"Seed/oracle" means it is not an allowed fallback for compilation of
executed program code.

| Service | Contract | Implementation | Proposed use | Tests |
| --- | --- | --- | --- | --- |
| Lexing and parsing | Convert source text to input semantic declarations; reject malformed text | `syntax/lexer.py`, `syntax/parser.py` | Allow | `test_syntax.py`, `test_syntax_units.py` |
| Graph construction and resolution | Resolve links, validate forms, create owned graph code | `lang.load`, `_Builder`, `relations.py` | Allow | `test_graph_form.py`, `test_lang.py` |
| Definition and edits | Produce transformations from explicit edits without mutating their source | `lang.define`, `transforms.py` | Allow | `test_node_edits.py`, `test_transforms.py` |
| Continuity inference | Preserve only justified identities; report inferred mappings without inventing preservation | `matching.py`, `lang.define` | Allow | `test_continuity_inference.py`, `test_continuity_corpus.py` |
| Semantic state | Store immutable values and ownership; derive state identity from content | `state.py`, `values.py` | Allow | `test_state.py`, `test_state_identity_cost.py` |
| Entity and version identity | Preserve entity identity and derive content-based version identities | `identity.py`, `values.py` | Allow | `test_identity.py` |
| Canonicalization | Produce stable canonical representations and reject unsupported content | `canonical.py`, `relations.py` | Allow | `test_canonical.py`, `test_relations.py` |
| Host lowering and chunk cache | Lower graph nodes into derived, cached chunks | `bytecode.py` | Seed/oracle; not fallback | `test_bytecode.py`, `test_rebuild.py`, new boundary tests |
| SHEAR compiler execution | Run the compiler program and produce expanded chunk data | `examples/self_hosting.py`, `machine.py` | Required; execution engine conditional | `test_self_hosting.py`, `test_rebuild.py` |
| SHEAR-VM interpretation | Execute the supported expanded instruction subset through language operations | `examples/vm.py` | Conditional on D3 | `test_vm.py`, `test_rebuild.py`, new boundary tests |
| Host machine execution | Execute host-derived chunks with explicit frames, stacks, errors and calls | `machine.py` | Fixed seed/runtime service; compiled-artifact admission requires D3 | `test_bytecode.py`, `test_vm.py` |
| Code reflection | Return the active version's function code in input form | `machine.py` (`CODE`), `lang.function_at` | Allow, provisionally | `test_self_hosting.py` |
| Link reflection | Return resolved links of the active function | `machine.py` (`LINKS`), `lang.py` | Allow, provisionally | `test_vm.py` |
| Data operations | Provide arithmetic, tuples, indexing, slicing, comparison and callable dispatch | `machine.py`, `canonical.py` | Allow | `test_data_ops.py`, `test_vm.py` |
| Cells and constraints | Read/write canonicalized cell content, reject unsatisfied constraints without altering semantic state | `runtime.py`, `constraints.py` | Allow | `test_cells.py`, `test_constraints.py` |
| Activation | Stage, validate and atomically select the candidate with declared continuity and authority | `Runtime.activate`, `lang.define`, `machine.py` | Allow, provisionally | `test_activation.py`, `test_metaprogramming.py` |
| Trials | Exercise candidates in isolation without granting activation authority | `Runtime.trial`, `machine.py` | Allow, provisionally | `test_trial_runs.py`, `test_language_trials.py` |
| Version lifetime | Hold running versions and retire superseded versions under current rules | `Runtime`, `Version`, `Frame`, `Hold` | Allow, provisionally | `test_lifecycle.py`, `test_activation.py` |
| Runtime error semantics | Report language, program, runtime and limit failures with existing error values | `machine.py`, `lang.py` | Allow | `test_error_handling.py`, `test_error_values.py` |

### 3.1 Actual workload versus prospective pipeline

The existing self-rebuild workload uses constructed compiler graph code,
input-form expressions, host runtime services, and the SHEAR compiler/VM.
It does not prove that source-text parsing is part of that rebuild.

Parsing, source reconciliation and the complete corpus-to-execution
pipeline are prospective task-30 dependencies. They remain inventory
entries, but must not be described as observed self-rebuild calls.

Python allocation, hashing, memory management and operating-system
services remain implementation dependencies of the hosted model.
This inventory does not claim independence from Python, a complete
foreign-service ABI, or a non-Python lifetime implementation.

The corrected task-23 evidence is in `docs/content_baseline.md`.
It measures selected routes and a finite inventory, not universal
absence of host fallback.

## 4. Acceptance contract for task 28

**Provisional Plan-owned tests:** `tests/test_bootstrap_boundary.py`,
registered in `tests/lanes.py`.

1. Matrix completeness: exactly one entry per operation in
   `OPERATIONS`; no additional graph operations or omitted `invalid`.
2. Supported host-lowering cases are derived from the actual lowering
   dispatch and checked with representative graph nodes.
3. SHEAR-lowering coverage agrees with `self_hosting.LOWERED`,
   excluding input-only `label`. Covered operations are checked
   structurally against expanded host chunks where appropriate.
4. Interpreter support is derived from actual instruction dispatch;
   supported instruction cases have execution witnesses.
5. Deferred SHEAR-lowering cases emit the declared explicit failure,
   rather than invoking host lowering.
6. Deferred interpreter instructions reach an intentional trap,
   rather than being dispatched to host instruction execution.
7. Negative witnesses distinguish intentional rejection from errors
   arising incidentally in operands or malformed test fixtures.
8. A guarded rebuild checks forbidden host-lowering requests for
   retained compiler source in generations 2 and 3, retaining the
   existing test-27 provenance guarantee.
9. Tests explicitly classify native `CALL` delegation. They cannot
   treat a call into host-compiled program code as independent
   interpreted execution.
10. The inventory's implementation and test references are checked
    against repository files; unsupported service claims are not
    silently promoted to verified coverage.

Preserve the existing compiler, VM, corpus, continuity and golden
records. No golden-record changes are intended for issue #64.

Existing tests relevant to independent review include
`test_operations.py`, `test_self_hosting.py`, `test_vm.py`,
`test_rebuild.py`, and `test_content_baseline.py`.

New regression tests must expose a plausible boundary violation:
for example, a deferred compilation case secretly using
`bytecode.lower`, or an unsupported interpreter instruction being
executed through the host instead of trapping. A test that only checks
a shared table against itself is not sufficient.

## 5. Scope and decision gates

Task 28 creates the boundary specification, tests and inventory.
It does not implement new language instructions, choose the execution
engine, create a generic capability system, replace Python services,
or prove a complete host-free bootstrap.

**Open – D3:** Task 29 compares execution on the SHEAR VM with
verified host execution of compiler-produced derived chunks.
Host execution must have a non-forgeable admission rule linking
each chunk to a semantic node, its version, and its producer.

**Open – D4:** The owner chooses the final workload and permitted
host boundary before task 30. Recommended workload: compiler
self-rebuild, the canary corpus, and live evolution. Python parsing,
semantic construction, identity, continuity and activation are
recommended permitted services. Runtime budgets need the recorded
task-23 measurements and a named environment.

**Open:** Whether `code` reads the active or another version in
future implementations, whether reflection accepts references
rather than static links, and how interpreted cells are selected
without accidental authority escalation. Existing behavior must
not be changed by Task 28.

If implementation reveals materially different support, Plan
must be revised before Execute changes acceptance expectations.

## 6. Independent review targets

Review must verify the matrix against implementation, not just the
table test; the distinction between unsupported and invalid forms;
the `unquote` exception; positive witnesses and fail-closed negative
witnesses; interpreter `CALL` delegation; provenance guards across
rebuilds; and the inventory's allowed-versus-observed distinction.

Review must also compare Plan-owned specifications and acceptance
tests at the Plan head against Execute's head. An unapproved change
to their meaning is a blocking Plan-contract deviation.

The resulting matrix and inventory are inputs to D4 and task 29,
not evidence that the hosted-bootstrap milestone is complete.
