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
