"""CI-only bootstrap cost measurements for task 23 (issue #60).

Run explicitly with ``python -m tests.content_baseline_measure``.
This module is not an ordinary test or a performance gate.
"""

from __future__ import annotations

import gc
import json
import math
import os
from pathlib import Path
import platform
import statistics
import time
import tracemalloc
from unittest import mock

from shear import EntityID, Runtime, canonical_serialize, canonicalize
from shear import bytecode
from shear.examples import self_hosting, vm
from shear.examples._support import program
from shear.lang import (
    Function,
    NODE_KINDS,
    define,
    function_at,
    load,
    run,
)
from shear.relations import relation_of
from tests.content_baseline import validate_measurement


OBSERVATIONS = 3
EDIT_TARGET = EntityID("content_baseline_edit")


def _encoded(value: object) -> bytes:
    return canonical_serialize(canonicalize(value))


def _hardware() -> dict:
    cpu = platform.processor() or platform.uname().processor

    cpuinfo = Path("/proc/cpuinfo")

    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu = line.partition(":")[2].strip()
                break

    if not cpu:
        raise RuntimeError("CPU model is unavailable")

    affinity = (
        len(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else os.cpu_count() or 1
    )
    cores = affinity
    quota = Path("/sys/fs/cgroup/cpu.max")

    if quota.is_file():
        parts = quota.read_text(encoding="utf-8").split()

        if len(parts) == 2 and parts[0] != "max":
            limit, period = map(int, parts)

            if period > 0:
                cores = min(cores, max(1, math.ceil(limit / period)))

    return {
        "python": platform.python_version(),
        "os": platform.platform(),
        "cpu": cpu,
        "cores": cores,
        "affinity_cores": affinity,
        "core_definition": (
            "CPU affinity count limited by the cgroup v2 CPU quota, "
            "rounded up to a whole core."
        ),
    }


def _provenance() -> tuple[str, str]:
    sha = os.environ.get("GITHUB_SHA", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")

    if (
        len(sha) != 40
        or not all(c in "0123456789abcdef" for c in sha)
        or repository != "NadOby/shear"
        or not run_id.isdecimal()
    ):
        raise RuntimeError(
            "Measurements require GitHub Actions provenance "
            "for NadOby/shear."
        )

    return (
        sha,
        f"https://github.com/{repository}/actions/runs/{run_id}",
    )


def _timings(function) -> list[float]:
    # Warm-up is deliberately excluded from the observations.
    function()
    times = []

    for _ in range(OBSERVATIONS):
        start = time.perf_counter()
        function()
        times.append(time.perf_counter() - start)

    return times


def _peak(function) -> int:
    gc.collect()
    tracemalloc.start()

    try:
        function()
        _, peak = tracemalloc.get_traced_memory()
        return peak
    finally:
        tracemalloc.stop()


def _compiler_routes() -> tuple[dict, object, object]:
    initial = load(program(vm.bootstrap_entities()))
    native = Runtime(initial)
    interpreted = Runtime(initial)

    original = function_at(initial, self_hosting.LOWER)

    if original is None:
        raise AssertionError("the compiler source is missing")

    source = original.body

    # Native means the host machine executes the SHEAR compiler.
    # It does not mean calling the Python bytecode lowering function.
    def native_call():
        return run(native, self_hosting.LOWER, source)

    native_output = native_call()

    # Install generation 1 through the actual bootstrap program.
    run(interpreted, vm.SWAP_ALL, may_activate=True)
    state = interpreted.active.state

    retained = function_at(state, vm.source_name("lower"))
    installed = function_at(state, self_hosting.LOWER)

    if retained != original:
        raise AssertionError("retained compiler source differs")

    if installed is None or installed.body[:2] != ("call", "vm"):
        raise AssertionError("the interpreted compiler was not installed")

    generation = run(interpreted, vm.GENERATION)

    if generation[0] != 1:
        raise AssertionError("unexpected bootstrap generation")

    def interpreted_call():
        return run(interpreted, self_hosting.LOWER, source)

    # Verify the interpreted route without contaminating the timings
    # with mocking or an inspection callback.
    real_chunk_of = bytecode.chunk_of
    source_prefixes = tuple(
        vm.source_name(name).value
        for name in vm.SWAPPED
    )
    requests = []

    def traced_chunk_of(graph, entity, owner=None):
        requests.append(entity)

        if entity.value.startswith(source_prefixes):
            raise AssertionError(
                f"host lowering used retained compiler source: {entity}"
            )

        return real_chunk_of(graph, entity, owner)

    with mock.patch.object(
        bytecode,
        "chunk_of",
        side_effect=traced_chunk_of,
    ):
        interpreted_output = interpreted_call()

    if _encoded(native_output) != _encoded(interpreted_output):
        raise AssertionError("compiler output differs by route")

    native_times = _timings(native_call)
    interpreted_times = _timings(interpreted_call)

    native_peak = _peak(native_call)
    interpreted_peak = _peak(interpreted_call)

    routes = {
        "native": {
            "seconds": native_times,
            "peak_traced_bytes": native_peak,
            "output": native_output,
        },
        "shear_vm": {
            "seconds": interpreted_times,
            "peak_traced_bytes": interpreted_peak,
            "output": interpreted_output,
        },
    }

    evidence = {
        "generation": generation[0],
        "compiler_source_entity": vm.source_name("lower").value,
        "installed_compiler_entity": self_hosting.LOWER.value,
        "installed_body_calls": installed.body[1],
        "host_chunk_requests_inspected": len(requests),
        "retained_source_host_fallback": False,
        "structural_output_equal": True,
    }

    return routes, state, (native_output, evidence)


def _sizes(state, compiler_output) -> dict:
    # Materialize every derivable code-node chunk of the selected
    # post-install graph. This is separate from all timed observations.
    derived = []

    for entity, value in sorted(state.values.items()):
        relation = relation_of(value)

        if relation is None or relation.kind not in NODE_KINDS:
            continue

        derived.append(bytecode.chunk_of(state, entity))

    # The image proxy contains semantic entity content and ownership,
    # not merely cached VersionIDs or an executable machine image.
    content = (
        tuple(
            (entity, state.values[entity].content)
            for entity in sorted(state.values)
        ),
        tuple(
            (owner, state.ownership[owner])
            for owner in sorted(state.ownership)
        ),
    )

    return {
        "compiler_chunk_bytes": len(_encoded(compiler_output)),
        "derived_chunk_count": len(derived),
        "derived_chunk_bytes": sum(len(_encoded(c)) for c in derived),
        "state_content_bytes": len(_encoded(content)),
        "image_exclusions": [
            "Host Python interpreter and runtime implementation",
            "Host services, foreign libraries and operating system",
            "Derived bytecode chunks and their object overhead",
            "Runtime frames, stacks, holds and cell contents",
            "Python object headers, references and allocator overhead",
            "Executable packaging, startup data and image format",
        ],
        "definitions": {
            "compiler_chunk_bytes": (
                "Canonical serialized bytes of the complete output "
                "from lower(lower)."
            ),
            "derived_chunk_count": (
                "One chunk for each code node in the loaded "
                "post-install graph."
            ),
            "derived_chunk_bytes": (
                "Sum of canonical serialized lengths of all derived "
                "node chunks, counting each code-node entity once."
            ),
            "state_content_bytes": (
                "Canonical serialized pair of sorted "
                "(EntityID, Value.content) entries and sorted "
                "(owner, children) entries of the installed state."
            ),
        },
        "program_selection": (
            "Bootstrap graph after installing compiler generation 1."
        ),
    }


def _small_edit() -> dict:
    old_body = (
        "add",
        ("arg", "x"),
        ("lit", 1),
    )
    new_body = (
        "add",
        ("arg", "x"),
        ("lit", 2),
    )

    initial = load(program({
        EDIT_TARGET: Function(("x",), old_body),
    }))
    runtime = Runtime(initial)
    before = run(runtime, EDIT_TARGET, 3)

    if before != 4:
        raise AssertionError("unexpected original function result")

    started = time.perf_counter()
    phase = time.perf_counter()
    candidate = define(
        initial,
        {EDIT_TARGET: Function(("x",), new_body)},
    )
    defined_at = time.perf_counter()
    define_seconds = defined_at - phase

    if runtime.active.state.id != initial.id:
        raise AssertionError("candidate creation activated the edit")

    destination = candidate.destination
    changed_nodes = []

    for entity, value in destination.values.items():
        previous = initial.values.get(entity)

        if (
            previous is not None
            and previous.version_id == value.version_id
        ):
            continue

        relation = relation_of(value)

        if relation is not None and relation.kind in NODE_KINDS:
            changed_nodes.append(entity)

    phase = time.perf_counter()
    lowered_before = bytecode.lowered_count()

    for entity in changed_nodes:
        bytecode.chunk_of(destination, entity, EDIT_TARGET)

    affected_chunks = bytecode.lowered_count() - lowered_before
    lower_seconds = time.perf_counter() - phase

    # Finish the preparation interval before correctness verification.
    # The verification run is not part of edit latency.
    prepared_at = time.perf_counter()

    if run(runtime, EDIT_TARGET, 3) != before:
        raise AssertionError("candidate affected active execution")

    # Activation is measured as a separate interval. Total edit latency
    # combines preparation and activation, excluding the check above.
    activation_started = time.perf_counter()
    runtime.activate(candidate)
    activated_at = time.perf_counter()
    activate_seconds = activated_at - activation_started

    after = run(runtime, EDIT_TARGET, 3)

    if after != 5 or runtime.active.state.id != destination.id:
        raise AssertionError("edit activation result is incorrect")

    return {
        "function": EDIT_TARGET.value,
        "argument": 3,
        "before": before,
        "after": after,
        "phase_seconds": {
            "define": define_seconds,
            "lower": lower_seconds,
            "activate": activate_seconds,
        },
        "total_seconds": (
            (prepared_at - started) + activate_seconds
        ),
        "affected_nodes": len(changed_nodes),
        "affected_chunks": affected_chunks,
        "candidate_state_changed_before_activation": False,
        "activated_state_id_matches_candidate": True,
    }


def collect_measurement() -> dict:
    revision, ci_run_url = _provenance()
    routes, state, compiler = _compiler_routes()
    output, evidence = compiler

    summaries = {}

    for name, route in routes.items():
        seconds = route["seconds"]
        summaries[name] = {
            "median_seconds": statistics.median(seconds),
            "min_seconds": min(seconds),
            "max_seconds": max(seconds),
        }

    report = {
        "workload": "lower(lower)",
        "revision": revision,
        "ci_run_url": ci_run_url,
        "hardware": _hardware(),
        "routes": routes,
        "summaries": summaries,
        "sizes": _sizes(state, output),
        "edit": _small_edit(),
        "provenance_checks": evidence,
        "measurement_scope": {
            "timing": (
                "Python perf_counter; one excluded warm-up then "
                "three untraced calls on each preloaded runtime. "
                "Runtime setup, installation and generation checks "
                "are excluded."
            ),
            "memory": (
                "Peak Python tracemalloc allocations during one "
                "additional warmed call per route; excludes prior "
                "program allocation, process RSS and native memory."
            ),
            "performance_gate": False,
        },
    }

    validate_measurement(report)
    return report


def main() -> int:
    report = collect_measurement()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
