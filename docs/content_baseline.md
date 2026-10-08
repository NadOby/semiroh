# Content duplication and bootstrap baseline

**Status: Provisional (Plan, roadmap task 23, issue #60).**

This is a measurement task, not a refactor. Its purpose is to provide
evidence for task 26's consolidation decision and task 29's execution-route
comparison. No result from this task changes the semantic model.

## 1. Scope

Measure two independent groups of evidence:

1. Semantic-content machinery: host-to-canonical conversions, the
   representations held by `Value` and `Relation`, mutation survivors,
   and content handling in the SHEAR compiler and VM.
2. Hosted-bootstrap costs: compiler execution time and peak memory,
   compiler-produced chunks, program-image size proxies, and a small
   edit through `define`, lowering and activation.

Keep duplication counts and runtime costs separate. Report actual
measurements rather than extrapolating one from the other.

## 2. Content inventory

Use the checked-out source revision as the inventory boundary.

Enumerate conversion sites in `shear/`, including canonicalization,
serialization, reconstruction of semantic records, relation decoding,
graph-form construction and collapse, and conversions at the embedded
compiler and SHEAR-VM boundaries.

For each site record:

- module and function;
- source and destination representations;
- whether the conversion is required by semantics or by the current
  implementation;
- whether the result is retained or reconstructed;
- whether another mechanism performs substantially the same conversion.

Count distinct call sites, not runtime invocations. Separate direct
conversions from recursive calls and representation-preserving operations.
Publish the inventory so that the counts can be independently checked.

Classify the current representation of relation content, roles and payloads
against `Value.content`. Distinguish copies from alternative views and
cached decoded records. Do not count a cache as an independent semantic
representation without evidence.

For `canonical.py`, `values.py` and `relations.py`, report mutation
survivors by classification, using the pinned catalog and reviewed source.
Separate equivalent and intentionally unspecified survivors from test
gaps. Do not infer mutation coverage from survivor counts alone.

Identify the tuple and canonical-content conversion boundaries in
`shear/examples/self_hosting.py` and `shear/examples/vm.py`, including
host services still used by their execution.

## 3. Bootstrap measurements

Run the diagnostic on CI, outside the ordinary test suite. Use Python
3.12 and standard-library instrumentation. Record the exact commit,
workflow-run URL, Python version, OS, CPU model and available cores.

Compare the same `lower(lower)` workload on two routes:

- Native route: the host machine executes the compiler written in SHEAR.
- Interpreted route: the SHEAR VM executes the installed compiler chunk.

"Native" here does not mean native machine-code generation or direct use
of the Python lowering function.

Use identical compiler source and input on both routes. Compare their
complete outputs structurally before reporting relative performance.
Preserve the existing generation/provenance checks from task 27.

After a warm-up, take at least three untraced timing observations per
route with `time.perf_counter()`. Report the median and range. Measure
peak traced Python allocations separately with `tracemalloc`, naming
what the measurement includes and excludes. Do not conflate traced
allocations with process RSS.

Report:

- compiler self-compilation time by route;
- peak traced memory by route;
- canonical serialized size of the compiler-produced chunk;
- total count and serialized size of derived chunks for the selected
  loaded program;
- canonical state-content byte size as a program-image proxy.

The reference model has no final deployable image format. Label the
last measurement as a proxy and enumerate excluded runtime machinery
and serialization components. Do not call it an executable-image size.

Measure one small, explicitly named function edit with `define`, lowering
and `Runtime.activate`. Record phase times, overall elapsed time,
affected node/chunk counts, and the verified before/after result.
Candidate production must remain separate from activation.

All measured sizes have byte units and an exact definition.

## 4. Implementation and acceptance contract

Plan owns this protocol and the acceptance tests. Execute may append
measurement results but must not silently change the protocol.

The diagnostic should provide a deterministic inventory mode and a
separately requested timing mode. Use one small diagnostic module, not a
general benchmark framework. A dedicated `workflow_dispatch` input may
invoke timing through the existing CI workflow. Ordinary CI must not run
performance measurements or enforce timing thresholds.

Acceptance tests verify the inventory structure and classification,
measurement-result structure, the selected semantic workload and its
correctness checks. They do not assert machine-specific elapsed times.

No production semantics, public language APIs or golden records should
change. The existing corpus, rebuild, identity and activation tests
remain applicable. Any changed mutation target requires the established
catalog/source-pin procedure.

Review must independently check the inventory counts, measurement units,
workload equivalence, the absence of host-lowering fallback on the
interpreted route, and whether the claimed image size is only a proxy.

The task is complete only when both evidence groups are recorded with
reproducible CI provenance. A missing measurement is reported as missing,
not estimated. Any proposed consolidation or execution-route change is
deferred to its respective roadmap task.

## 5. Results

To be appended by Execute after the CI measurements. Include the
inventory and classifications, raw observations, summaries, hardware
and revision, CI run references, and limitations. Do not revise sections
1–4 to accommodate unexpected measurements without returning to Plan.

### 5.1. Evidence and provenance – 2026-10-08

- Revision: `9b5f9225636a4ac8ff3b21c5eb32ebd6668084ff`.
- CI run: https://github.com/NadOby/shear/actions/runs/37763237141
- Artifact: `content-baseline-9b5f9225636a4ac8ff3b21c5eb32ebd6668084ff`.
- Artifact files: `content-inventory.json` and `content-baseline.json`.
- Result: ordinary test lanes, golden checks, deterministic inventory and manually dispatched measurements succeeded.
- Python: 3.12.15.
- OS: Linux 6.17.0-1022-azure, x86-64, glibc 2.39.
- CPU: Intel Xeon Platinum 8573C; 4 available CPU cores as reported by CPU affinity and cgroup-quota inspection.

The artifact contains the complete per-site inventory and raw measurement report. Both are reproducible from the pinned revision using the `content_baseline` workflow-dispatch input. Performance measurements are not part of ordinary CI and enforce no thresholds.

### 5.2. Semantic-content inventory

The deterministic AST inventory enumerated 140 static call sites across `shear/`: 127 direct and 13 recursive. These are counts of syntactic calls to the selected conversion helpers, not dynamic execution frequencies or independently established duplication.

| Conversion helper | Static sites |
|---|---:|
| `canonical_serialize` | 41 |
| `canonicalize` | 29 |
| `_decode` | 36 |
| `relation_of` | 17 |
| `function_of` | 6 |
| `function_at` | 4 |
| `_compile` | 2 |
| `_collapse` | 2 |
| `_function_from_canonical` | 2 |
| `_decode_endpoint` | 1 |
| **Total** | **140** |

The preliminary call-site classifier labels 18 sites semantic and 122 implementation-dependent. Retention labels are 18 retained, 53 reconstructed and 69 neither. These labels are heuristic classifications requiring independent source review; they are not a measured count of avoidable conversions.

Representation distinctions:

- `Value.content` holds canonical semantic content. Its `VersionID` is a derived identity cache.
- `Relation.roles` is a normalized endpoint view, not automatically an independent copy of semantic state.
- `Relation.payload` is canonicalized and incorporated into the stored relation content.
- `relation_of` caches a decoded `Relation` on an immutable `Value`. This is a derived record cache rather than separately authoritative semantic state.

Named compiler and VM boundaries include `compiler_entities` and `_lower_body` in `shear/examples/self_hosting.py`, and `_compiled`, `_swapped_function` and `bootstrap_entities` in `shear/examples/vm.py`. Python still constructs the compiler and VM seed, supplies the runtime and implements operations such as code inspection, function construction and activation. The detailed source/destination and host-service descriptions are in `content-inventory.json`.

The reviewed survivor catalog contains six survivors for the three selected mutation targets: three equivalent and three intentionally unspecified, with no catalogued test gaps inferred. The catalog's Git blob pins are:

- `shear/canonical.py`: `6ef26cdc8ea29df65f2cd902341aee9b4b27b014` – one equivalent, one unspecified.
- `shear/values.py`: `4d23855227d1aaf0638a13e93bb357744ee019b1` – one equivalent, one unspecified.
- `shear/relations.py`: `951bb7fee26632461e079dd7c0f12164335a907c` – one equivalent, one unspecified.

These survivor counts do not establish overall mutation coverage or absence of other testing gaps.

### 5.3. Bootstrap execution and memory

Workload: `lower(lower)` using the same retained compiler source expression as input on both routes. The native route executes the SHEAR compiler on the host machine; the interpreted route executes the generation-1 installed compiler through the SHEAR VM. The complete results were canonically serialized and compared before timing; they agreed.

Each route was warmed once, then executed three times without tracing. Times below are seconds from `time.perf_counter()`.

| Observation | Native | SHEAR VM |
|---|---:|---:|
| 1 | 0.036499594 | 5.095818614 |
| 2 | 0.036181738 | 5.126153965 |
| 3 | 0.036189932 | 5.239161373 |
| Median | 0.036189932 | 5.126153965 |

The ratio of route medians is approximately 142:1. It is an observed workload ratio on this runner, not a general performance prediction.

Separate warmed executions under `tracemalloc` reported peak traced allocations of 212,392 bytes (native) and 1,355,751 bytes (SHEAR VM). These values exclude allocations made before tracing, untraced native allocations and process RSS.

The installed compiler's body calls `vm`; its retained source matched the original compiler definition. The generation record was 1. Instrumentation observed 115,233 `bytecode.chunk_of` requests during an interpreted execution and rejected any request naming retained compiler-source entities. None triggered that rejection. This check supports the exercised route but is not a universal proof against every possible host fallback.

### 5.4. Derived chunks and state-content proxy

The selected program is the bootstrap graph after installation of compiler generation 1.

| Quantity | Recorded result |
|---|---:|
| Complete `lower(lower)` output, canonical serialized | 123,643 bytes |
| Derived code-node chunks | 1,858 |
| Sum of canonical serialized derived chunks | 915,986 bytes |
| Canonical state-content proxy | 988,970 bytes |

The chunk sum counts each code-node entity once. The state-content proxy serializes sorted `(EntityID, Value.content)` entries and sorted ownership entries.

The proxy excludes Python interpreter/runtime implementation and host services, derived chunks and their Python object overhead, execution frames and stacks, holds, runtime cell contents, Python allocator overhead, executable packaging and startup data. It is **not** a deployable executable-image size. The quantities should not be added together as though they describe disjoint physical memory.

### 5.5. Small edit through activation

The measured function was `content_baseline_edit(x)`, changed from `x + 1` to `x + 2`, evaluated with `x = 3`. The active result was 4 before activation and 5 afterward. Candidate construction did not change the active state; the activated state ID matched the candidate.

| Phase | Elapsed seconds |
|---|---:|
| `define` | 0.000480012 |
| Lower changed code nodes | 0.000008594 |
| `Runtime.activate` | 0.000029744 |
| Total measured edit interval | 0.000552658 |

Two changed code nodes and two newly lowered chunks were recorded. The total interval also includes small amounts of orchestration between the individually measured phases; result verification after activation is separate.

### 5.6. Limitations

This is a single CI environment and one three-observation timing sample per execution route. Timing values are diagnostics, not stable performance guarantees.

The AST inventory records named helper calls, not arbitrary conversions hidden inside other operations. Necessity, retention and overlap classifications are provisional. The full inventory, rather than only the aggregate counts above, must be checked during independent Review.

The source-equivalence and instrumented host-fallback checks apply to the tested route and revision. They do not establish execution-route equivalence for every possible program.

GitHub Actions artifacts may expire. The checked-in diagnostic and pinned commit provide the regeneration procedure; the reported measurements remain observations of the cited run.

No semantic-content refactor or consolidation decision is made by these results. Those decisions remain with the later roadmap tasks.

