# Hosted Bootstrap Pipeline – Task 30

**Status: Provisional Plan contract; D3/D4 Decided.**

Issue #66. Baseline: `main` at `c1a4596`. This specification defines the implementation and acceptance boundary for roadmap Task 30. It does not amend D3 or D4 in `docs/roadmap.md`.

The independent Plan review of `f220578` identified four P2 acceptance-contract gaps. Sections 3–5, 8–9 and 12 incorporate their resolution without changing the workload or architectural decisions.

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

### Compiler and target source boundary

**Provisional integration contract: two distinct canonical semantic states.**

- The **compiler source state** contains the SHEAR-authored unified compiler and its semantic dependencies. It remains pinned while compiler executable generations G0–G3 are produced. The host may maintain a separate compiler runtime using this state.
- The **target source state** contains the program being compiled and executed. It may be an ordinary corpus program or a program constructed from source text. It does not need to contain any compiler functions.
- The host orchestrates interactions between the compiler runtime and target runtime and supplies pinned descriptions of target nodes. This interaction is an explicitly permitted D4 host service.
- Compiling a target never injects compiler entities, link relations or wrappers into the target canonical state. Compiler generation changes likewise do not modify either canonical source.
- Compiler and target may happen to have equal state identities in a special case, but their logical roles and provenance must remain distinct.

The term `compiler_source_state_id` means the `StateID` of the pinned canonical compiler source. It is used by the seed manifest and generation reports.

The term `target_state_id` means the `StateID` of the pinned target program whose nodes are being compiled. It is bound to target-artifact provenance and dependency validation.

Neither identity may be substituted for the other. The earlier ambiguous `source_state_id` fields in the Plan test-facing interface are replaced with these explicit names.

The provisional unified node-aware compiler entry is `EntityID("compile_node")`. Its name is an integration identifier, not new language syntax.

### Compiler input boundary

The host prepares immutable, version-pinned descriptors containing:

- Target source `StateID`.
- Node `EntityID` and `VersionID`.
- Owning function identity.
- Node kind and semantic payload.
- Ordered/role-labelled child identities.
- Permitted linked function and cell identities.

Descriptors come from the pinned target state, not mutable program-supplied authority. The SHEAR compiler performs the lowering.

Python may validate descriptor construction and generically decode compiler results. It may not synthesize or repair instructions attributed to SHEAR compilation.

`code` continues to observe the active version when executed as a language operation. Compiler descriptors explicitly select a pinned version; these two rules must not be conflated.

Program-visible node-identity reflection is unchanged. Reconsidering that boundary is deferred.

## 4. Finite bootstrap seed

Generation 0 is a finite, explicitly inventoried host-lowered SHEAR compiler seed, derived only from the pinned compiler source state.

The independent root contract is the following set of compiler functions:

- `lower`
- `upper`
- `evals`
- `seq_code`
- `compile_node`

Additional helpers enter the seed only through the declared semantic dependency closure, not by treating them as arbitrary new roots.

The seed contains every executable relation node owned by those roots and by compiler functions transitively reachable through their semantic links. Include code in closure bodies and other owned executable subtrees. Do not count function-definition relations, links-table relations or unrelated target-program entities as executable seed nodes.

The implementation may use a conservative dependency closure if dynamic callable dispatch makes a particular dependency impossible to determine statically, but any additional member must be specifically justified against the canonical compiler source, reviewed and inventoried. It must not be silently authorized by a runtime lookup.

Execute must produce a checked-in, deterministic seed manifest identifying:

- The pinned `compiler_source_state_id`.
- The fixed, explicit seed roots.
- Every permitted host-lowered executable node, its `EntityID`, `VersionID` and owning compiler function.
- Its transitive compiler-code dependency closure.
- Fixed host machinery and permitted semantic services, listed separately.

A manifest containing only root names, with unconstrained runtime expansion, is insufficient. The actual seed node set must be closed, reproducible and independently checked against the semantic source before execution.

Acceptance tests must independently traverse the compiler source and calculate the expected seed set. Set equality is required, not merely a subset check against observed host-lowering events.

An unrelated compiler-source function, an ordinary corpus node, a target-program node or a per-function wrapper must not enter the seed merely because it appears in a state or happens to be callable.

Every actual host-lowering request must be checked against the sealed manifest. An undeclared dependency must fail before host lowering occurs. The manifest cannot expand during execution. A changed compiler source or dependency graph requires a separately validated manifest; an existing manifest cannot silently authorize the change.

No ordinary corpus program, target-program wrapper or newly compiled generation may be treated as seed machinery.

## 5. Compiler generations

Generation 0 executes its declared seed on the hosted machine and invokes the SHEAR compiler.

- **G1:** Produced by observed G0 SHEAR compiler execution, then admitted.
- **G2:** Produced by actual execution of admitted G1 compiler artifacts, then admitted.
- **G3:** Produced by actual execution of admitted G2 compiler artifacts, then admitted.

All generations compile the same pinned canonical compiler source. The source is identified by `compiler_source_state_id`; generations identify derived executable artifact sets, not source revisions.

Host orchestration may select an admitted generation without `define` or language-driven activation. It cannot manufacture compiler output, substitute an artifact from an earlier generation, or relabel producer provenance.

### Independent generation verification

Generation reports and implementation-emitted events are necessary evidence but are not sufficient on their own.

Acceptance must also:

1. Observe real entry into the existing host machine's SHEAR execution mechanism for successive compiler-generation invocations, independently of the pipeline's own provenance events.
2. Check the actual admitted compiler artifact sets for G1, G2 and G3, including generation-specific identity, semantic node/version binding and structural output.
3. Compare all three generations' compiler-node chunks against each other and the independent host-lowering oracle on the same pinned compiler source nodes. Compare artifact generation metadata separately.
4. Demonstrate causality by withholding or invalidating G1's admitted compiler artifacts before attempting G2, and separately G2's artifacts before attempting G3. Each attempt must fail closed rather than produce a successor through host lowering, stale chunks, relabelled artifacts or another generation.
5. Confirm the compiler source and target source are unchanged across the rebuild.

The test-facing host registry may expose a read-only artifact snapshot and an explicit host-only invalidation hook for this verification. Neither is program-visible authority to install code.

A structural fixpoint, plausible ancestry labels, disjoint artifact IDs or self-reported production events alone are insufficient to establish self-rebuilding.

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

Compiler artifact provenance refers to the pinned compiler source state. Target-artifact provenance additionally binds the target `StateID`, node and version. Execution under a compiler generation must never confuse these provenance domains.

Admission authenticates origin and structure. It does not certify compiler semantic correctness or recompute chunks using host lowering.

The execution resolver must cover root calls, static `CALL`, indirect `APPLY`/`APPLYV`, closures, child-node evaluation and error-handler bodies.

Every executed program-code node has a traceable chain of production, admission and execution. Fixed runtime machinery and the G0 seed are explicitly distinguished from program code.

Missing, malformed, forged, misbound, stale or unsupported artifacts fail closed. Neither lazy host lowering nor a pre-existing host chunk cache may rescue them.

The Task 29 spike must be removed, replaced or explicitly promoted, including a justified mutation-catalog disposition.

## 7. Artifact invalidation

Derived artifacts live outside canonical semantic state.

A usable artifact is bound to its target source state, node/version, compiler generation or equivalent producer identity, executable IR contract and all relevant semantic dependencies, including link and owner context.

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

The command loads target source using existing syntax and graph construction, obtains the separate pinned compiler source, compiles through the SHEAR compiler, admits the produced artifacts and executes the named target entry. Target text does not need to declare the compiler.

A provisional edit mode uses:

`python3 -m shear.hosted_bootstrap --source-file ORIGINAL --edited-source-file EDITED --edit-mode prepare --entry NAME --args-json JSON`

The edit mode must:

1. Parse and load the original source into canonical target graph form.
2. Run the original entry through admitted route B.
3. Reconcile the edited source against the original canonical state using `reconcile`/`define`, obtaining a candidate state and continuity mapping.
4. Compile the candidate's nodes through the same SHEAR compiler and admit them against the candidate target state, without altering the original active state.
5. Execute the candidate entry on a separate candidate runtime or equivalent isolated staged context. This is host-orchestrated diagnostic execution, not program-driven `trial` or activation.
6. Report the original and candidate results, their source-state identities, the retained entry identity and the fact that the original active state was not switched.

The command's JSON output must contain `result`, `candidate_result`, `base_state_id`, `candidate_state_id`, `active_state_id`, `continuity`, `route` and `executed_artifacts`. `continuity` must identify the retained entry entity and the relevant original and candidate body-node identities and versions. A normal, non-edit invocation does not require candidate fields.

The independent acceptance test calculates the expected candidate and continuity from the public parser/reconciler, rather than trusting only values echoed by the command.

No particular filename extension or final human-facing syntax is decided here. Text syntax v0 remains the provisional input format.

Report results and provenance in a reproducible, inspectable form. Diagnostics must identify failures at the appropriate source node and boundary.

Corpus acceptance may use the equivalent programmatic API for richer semantic arguments, closures and persistent runtime scenarios.

## 9. Plan-owned acceptance tests

Plan establishes tests before Execute changes production implementation. The tests must fail against the unimplemented route rather than treating unavailable behavior as a skip or success.

Minimum independent checks:

1. All 20 selected corpus examples run every existing scenario and step with original expectations.
2. Compiler-free target programs compile and execute through a separate pinned compiler state, without compiler-entity injection or changes to target canonical identity.
3. Each executed code node has authentic producer, node, version, compiler generation and target-state admission evidence, including indirect calls and closures.
4. G0 seed membership exactly equals the independently derived, permitted executable dependency closure; no extra target or unrelated compiler code is admitted, and undeclared seed expansion fails.
5. G1, G2 and G3 execute their predecessor-produced admitted compiler code. Independent host-machine observation and missing-predecessor interventions accompany provenance reports.
6. Canonical compiler and target source, their identities and source rendering remain unchanged across artifact generation changes.
7. Expanded-chunk compiler outputs remain compatible, while each generation's node-aware output agrees structurally with the independent host oracle and the other generations.
8. `catch` and `raise` preserve the language's existing result, filter, error-provenance, unwinding and non-rollback semantics.
9. Forged evidence, incorrect nodes/versions, changed artifacts, foreign child references and missing admitted callees fail closed.
10. A changed node or link dependency invalidates incompatible artifacts without requiring a full live activation scenario.
11. Source text, parsing, reconciliation/`define`, original and candidate admitted execution, continuity and non-activation form a reproducible command path.
12. Task 29's linked-call witness is reproduced on the integrated route, with the prototype's limitations explicitly distinguished from new evidence.
13. Existing route-A compiler/VM and corpus regressions remain unchanged.

Test oracles must include existing independently specified corpus expectations, host lowering used only in differential tests, semantic-graph traversal performed independently of the production seed builder, and adversarial faults that prove checks detect missing provenance or incorrect behavior.

No existing golden-record changes are intended. If Execute discovers a necessary golden change, return it to Plan for an explicit declaration before modifying expectations.

New test modules must be registered in `tests/lanes.py`. Existing registered modules may be extended without changing that file. Test evidence must not depend solely on the same compiler algorithm being tested.

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

**Execute contract:** Implement the specified route and acceptance tests without weakening Plan-owned expectations. Keep the shared compiler implementation concrete, the bootstrap seed closed and provenance transitive. Use separate compiler/target canonical states and explicit provenance namespaces. Prove each successor compiler generation depends on admitted execution of its predecessor. Document provisional integration choices and update the operation matrix, host-service inventory, diagnostics and `CHANGES.md`. Escalate material architectural changes.

**Independent Review criteria:** Compare Plan-owned files against the revised protected Plan head; verify the full corpus, compiler-free target support, exact seed closure and generation causality through code inspection and independent execution evidence. Audit every host-lowering path, artifact lookup boundary, transitive call route, dependency check and negative test. Confirm the reconciliation command's continuity and no-activation guarantees, source preservation, non-self-referential oracles, mutation-catalog treatment, unchanged golden records, ordinary CI and diagnostic provenance.

Classify verified defects, limitations, hypotheses and documentation drift separately. No successful Execute run certifies its own correctness.
