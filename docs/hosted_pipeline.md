# Hosted Bootstrap Pipeline – Task 30

**Status: Provisional Plan contract; D3/D4 Decided.**

Issue #66. Baseline: `main` at `c1a4596`. This specification defines the implementation and acceptance boundary for roadmap Task 30. It does not amend D3 or D4 in `docs/roadmap.md`.

## 1. Goal and invariants

Deliver one hosted path from SHEAR source through semantic construction, SHEAR compilation, authenticated artifact admission and execution.

The path must:

- Preserve the canonical semantic graph and its identities.
- Rebuild the compiler through generations 1, 2 and 3 without replacing its semantic source.
- Execute the declared non-evolution corpus subset through route B.
- Authenticate every executed program-code artifact, including transitive calls.
- Fail closed when compilation, admission or execution is unsupported.
- Retain host lowering as an independent test oracle, never an execution fallback.

D3 selects route B as primary. The SHEAR-written VM remains an alternative and independent correctness reference.

D4 permits explicitly contracted, replaceable Python host services. Hosted bootstrap does not mean Python-independent execution.

## 2. Exact corpus subset

Run every scenario and every step of these 20 existing `shear.examples.EXAMPLES` entries, preserving their expected results, exceptions, cell contents and scenario order.

| Group | Included examples | Required behavior |
| --- | --- | --- |
| Recursion | `factorial`, `fibonacci`, `sum_to_n`, `gcd`, `collatz_step_count`, `deep_loop`, `deep_recursion` | Arithmetic, comparisons, conditionals, direct/indirect calls, tail and non-tail recursion |
| Control | `abs_value`, `max_of_two`, `clamp` | Conditional branches and argument evaluation |
| Side effects | `counter`, `account` | Cell reads/writes, persistence, constraints, rejected writes |
| Data | `insertion_sort`, `let_bindings` | Tuples, indexing, slicing, concatenation, lexical bindings and failures |
| Higher order | `map`, `fold`, `map_long_tuple` | Function references, indirect dispatch, deep traversal |
| Closures | `make_adder`, `compose` | By-value captures, nested closures, indirect application |
| Compiler | `compiler` | Existing compiler outputs and semantic behavior, executed through admitted artifacts |

Ordinary failure-producing steps are mandatory. They must not be removed, replaced with positive-only cases or silently evaluated by the ordinary host execution path.

The exact operation closure for each example must be obtained from the loaded canonical graph, including every transitively reached function and closure body. Acceptance tests compare that inventory with the supported operation contract.

The required executable operation coverage includes:

`lit`, `arg`, `add`, `sub`, `mul`, `lt`, `eq`, `if`, `seq`, `call`, `tuple`, `len`, `item`, `slice`, `concat`, `let`, `ref`, `apply`, `applyv`, `closure`, `read`, `write`, `code`, `linksof`, `catch`, `raise`.

This is a target support inventory, not a claim that every operation appears in each example. `catch` and `raise` additionally require dedicated acceptance witnesses.

`invalid` must fail explicitly under existing language semantics. Input-form `label` must retain its existing transparent lowering behavior.

**Excluded existing corpus examples:**

- Self-modification: `power_compiler`, `checked_compile`, `replace_self`, `sort_swap`, `instrument`.
- Historical wrapper bootstrap: `bootstrap`.
- Dedicated error canaries: `safe_install`, `account_report`, `lookup`.

The exclusions remain part of the existing corpus and must continue passing on their established reference routes. They belong to Task 31's hosted-route completion.

`quote`, `unquote`, `function`, `activate` and `trial` are not required as Task 30 compiler operations unless a concrete dependency demonstrates otherwise. Such a discovery must be reported to Plan before enlarging scope.

## 3. Unified compiler architecture

Use one SHEAR-authored implementation of operation lowering, shared between:

1. Expanded-chunk compilation compatible with existing `lower(e)` behavior and regression tests.
2. Node-aware compilation producing per-node chunks containing explicit child `EntityID` references.

Share actual lowering decisions, instruction construction, operand order and operation dispatch – not merely similar interfaces.

Representation-specific adapters may differ. They must not duplicate the operation-lowering algorithms.

Split the compiler into coherent modules/files where useful. No fixed file structure or artificial line limit is imposed.

Retain existing per-node bytecode as the provisional shared executable IR. Reuse concrete operation metadata from `shear/operations.py` and semantic services from the existing state/runtime implementation.

The host machine and the SHEAR-written VM may retain execution-specific machinery. Full VM parity and a broad VM rewrite are excluded.

### Compiler input boundary

The host prepares immutable, version-pinned descriptors containing:

- Source state identity.
- Node `EntityID` and `VersionID`.
- Owning function identity.
- Node kind and semantic payload.
- Ordered/role-labelled child identities.
- Permitted linked function and cell identities.

Descriptors come from the pinned semantic state, not mutable program-supplied authority. The SHEAR compiler performs the lowering.

Python may validate descriptor construction and generically decode compiler results. It may not synthesize or repair instructions attributed to SHEAR compilation.

`code` continues to observe the active version when executed as a language operation. Compiler descriptors explicitly select a pinned version; these two rules must not be conflated.

Program-visible node-identity reflection is unchanged. Reconsidering that boundary is deferred.

## 4. Finite bootstrap seed

Generation 0 is a finite, explicitly inventoried host-lowered SHEAR compiler seed.

Its roots include the existing compiler functions `lower`, `upper`, `evals`, `seq_code` and the unified compiler's required shared helpers. Only actually necessary additional dependencies may be admitted to the seed.

Execute must produce a checked-in, deterministic seed manifest identifying:

- Every permitted host-lowered program-code node and its version.
- Its owning function and dependency closure.
- The compiler source identity against which the manifest was constructed.
- Any fixed host machinery and permitted semantic services, listed separately.

A manifest containing only root names, with unconstrained runtime expansion, is insufficient. The actual seed node set must be closed, reproducible and checked against the manifest before execution.

Adding an unlisted dependency must fail, not silently enlarge the seed.

No ordinary corpus program, target-program wrapper or newly compiled generation may be treated as seed machinery.

## 5. Compiler generations

Generation 0 executes its declared seed on the hosted machine and invokes the SHEAR compiler.

- **G1:** Produced by an observed G0 SHEAR compiler execution, then admitted.
- **G2:** Produced by execution of admitted G1 compiler artifacts, then admitted.
- **G3:** Produced by execution of admitted G2 compiler artifacts, then admitted.

All generations compile the same pinned canonical compiler source. Generations identify executable artifact sets, not semantic source revisions.

Host orchestration may select an admitted generation without `define` or language-driven activation. It cannot manufacture compiler output, substitute an artifact from an earlier generation, or relabel producer provenance.

For identical deterministic compiler inputs, compare G1, G2 and G3 outputs structurally and against the independent host-lowering oracle. Generation metadata is checked separately and must not be normalized away.

A fixpoint alone is insufficient: each generation must demonstrably execute its predecessor-produced compiler code.

## 6. Route-B admission and provenance

Integrate artifact lookup into an explicit per-run/per-runtime execution boundary. Remove the Task 29 prototype's process-global `mock.patch` interception from the production path.

Host-internal admission requires:

1. An existing executable semantic node with the claimed identity and version.
2. A matching observed SHEAR compiler invocation and returned artifact.
3. A trusted record of producer compiler entity, version and generation.
4. Structurally valid instructions, operands, control flow and child references.
5. Link and owner compatibility with the pinned source.
6. Valid dependency bindings and artifact integrity.
7. No program-visible authority to mint admission evidence or install arbitrary bytecode.

Admission authenticates origin and structure. It does not certify compiler semantic correctness or recompute chunks using host lowering.

The execution resolver must cover root calls, static `CALL`, indirect `APPLY`/`APPLYV`, closures, child-node evaluation and error-handler bodies.

Every executed program-code node has a traceable chain of production, admission and execution. Fixed runtime machinery and the G0 seed are explicitly distinguished from program code.

Missing, malformed, forged, misbound, stale or unsupported artifacts fail closed. Neither lazy host lowering nor a pre-existing host chunk cache may rescue them.

The Task 29 spike must be removed, replaced or explicitly promoted, including a justified mutation-catalog disposition.

## 7. Artifact invalidation

Derived artifacts live outside canonical semantic state.

A usable artifact is bound to its node/version, compiler generation or equivalent producer identity, executable IR contract and all relevant semantic dependencies, including link and owner context.

For Task 30, conservative invalidation is sufficient:

- Reuse compatible artifacts within the same pinned state.
- Invalidate or revalidate when any relevant dependency or compiler implementation changes.
- Permit invalidating all artifacts on a state change.
- Never infer compatibility from `VersionID` alone.
- Rejected/stale artifacts cannot enter or remain usable through an execution cache.
- A failed compilation or admission leaves the semantic state unchanged.

No cross-activation reuse optimization is required. Held frames, closures across activation and retirement-aware reuse are Task 31 tests.

## 8. Documented command path

Provide one reproducible standard-library Python command, provisionally:

`python3 -m shear.hosted_bootstrap --source-file FILE --entry NAME --args-json JSON`

The command must load the source using existing syntax and graph construction, compile through the SHEAR compiler, admit the produced artifacts and execute the named entry.

An explicitly documented edit mode must additionally exercise source reconciliation/`define` before compilation, without silently activating a candidate.

Report results and provenance in a reproducible, inspectable form. Diagnostics must identify failures at the appropriate source node and boundary.

Corpus acceptance may use the equivalent programmatic API for richer semantic arguments, closures and persistent runtime scenarios.

## 9. Plan-owned acceptance tests

Plan establishes tests before Execute changes production implementation. The tests must fail against the unimplemented route rather than treating unavailable behavior as a skip or success.

Minimum independent checks:

1. All 20 selected corpus examples run every existing scenario and step with original expectations.
2. Each executed code node has authentic producer, node, version, generation and admitted-execution evidence, including indirect calls and closures.
3. G0 seed membership is exact and immutable during a run; undeclared host lowering is rejected.
4. G1, G2 and G3 are genuinely produced by their predecessors, without source replacement or cached-generation substitution.
5. Canonical source, identities and source rendering remain unchanged across artifact generation changes.
6. The unified compiler preserves existing expanded-chunk outputs while its node-aware output agrees with the independent host oracle.
7. `catch` and `raise` preserve the language's existing result, filter, error-provenance, unwinding and non-rollback semantics.
8. Forged evidence, incorrect nodes/versions, changed artifacts, foreign child references and missing admitted callees fail closed.
9. A changed node or link dependency invalidates incompatible artifacts without requiring a full live activation scenario.
10. Source text, parsing, reconciliation where applicable, compiler execution and admission form one reproducible command path.
11. Task 29's linked-call witness is reproduced on the integrated route, with the prototype's limitations explicitly distinguished from new evidence.
12. Existing route-A compiler/VM and corpus regressions remain unchanged.

Test oracles must include existing independently specified corpus expectations, host lowering used only in differential tests, and adversarial faults that prove the checks detect missing provenance or incorrect behavior.

No existing golden-record changes are intended. If Execute discovers a necessary golden change, return it to Plan for an explicit declaration before modifying expectations.

New test modules must be registered in `tests/lanes.py`. Test evidence must not depend solely on the same compiler algorithm being tested.

## 10. Diagnostics

Record named hardware, Python version, operating system and source revision.

Measure separately:

- Initialization and seed costs.
- Compiler generations 1, 2 and 3.
- Artifact production and admission.
- Cold and warm execution.
- Independent verification.
- Small-edit preparation, admitted compilation and activation as distinct phases.
- Peak memory, artifact counts and artifact sizes.

Use repeated, untraced observations and report distributions or individual observations with their median. Do not combine dissimilar workloads into a performance ratio.

D4's 10-second rebuild and 50-ms small-edit targets, with 1-second and 10-ms aspirations, are diagnostic only.

Retain Task 23 and Task 29 historical measurements unchanged. A new equivalent-workload route-B measurement must not retroactively reinterpret Task 29's falsified 179.126317-times cold-cost prediction.

## 11. Explicit Task 31 exclusions

Task 30 does not establish:

- Language-driven construction, trial or activation of changed functions.
- Full `quote`, `unquote`, `function`, `activate` or `trial` compiler coverage.
- The three dedicated error canaries on the admitted route.
- A persistent self-modifying hosted image.
- Old frames and closures continuing across activation.
- Cross-activation artifact reuse and retirement.
- Repeated live updates, retained-version bounds or runtime replacement.
- Full SHEAR-VM feature parity.
- Native code generation or removal of Python.

These remain Task 31 or later obligations. Their absence cannot be hidden by successful host-orchestrated compiler generations.

## 12. Execute and Review boundaries

**Execute contract:** Implement the specified route and acceptance tests without weakening Plan-owned expectations. Keep the shared compiler implementation concrete, the bootstrap seed closed and provenance transitive. Document provisional integration choices and update the operation matrix, host-service inventory, diagnostics and `CHANGES.md`. Escalate material architectural changes.

**Independent Review criteria:** Compare Plan-owned files against the recorded Plan head; verify the full corpus and generation claims through code inspection and independent execution evidence. Audit every host-lowering path, artifact lookup boundary, transitive call route, dependency check and negative test. Confirm source preservation, non-self-referential oracles, mutation-catalog treatment, unchanged golden records, ordinary CI and diagnostic provenance.

Classify verified defects, limitations, hypotheses and documentation drift separately. No successful Execute run certifies its own correctness.
