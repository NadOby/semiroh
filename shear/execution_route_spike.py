
"""Temporary Task 29 route comparison; not a permanent execution API.

The compiler is SHEAR Function data. Its host boundary observes one real
SHEAR invocation; authorization and admitted artifacts are outside State.
The temporary machine interception is serialized but process-global: callers
must not run unrelated machine executions concurrently with run_admitted.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from hashlib import sha256
from threading import RLock
from time import perf_counter
from typing import Any
from unittest import mock
from weakref import WeakKeyDictionary

from . import bytecode, machine
from .canonical import CanonicalNode, canonical_serialize, canonicalize
from .identity import EntityID, StateID, VersionID
from .lang import Function, _definition_of, links, load, run
from .relations import Relation, relation_of
from .runtime import Runtime
from .state import State
from .examples._support import program


class AdmissionRejected(ValueError):
    """No authorized executable artifact is available for this request."""


@dataclass(frozen=True)
class RouteEvent:
    kind: str
    route: str
    entity: EntityID
    version: VersionID
    artifact_id: str
    compiler_entity: EntityID | None = None
    compiler_version: VersionID | None = None


@dataclass(frozen=True)
class _Production:
    state: State
    entity: EntityID
    version: VersionID
    owner: EntityID
    chunk: tuple
    artifact_id: str
    compiler_entity: EntityID
    compiler_version: VersionID


@dataclass
class _Registry:
    compiler: Runtime | None = None
    produced: dict[object, _Production] = field(default_factory=dict)
    admitted: dict[tuple[StateID, EntityID, VersionID], _Production] = field(
        default_factory=dict
    )
    events: list[RouteEvent] = field(default_factory=list)


class _Evidence:
    """Opaque identity; no user value can manufacture a registered handle."""


_ROUTES: WeakKeyDictionary[Runtime, _Registry] = WeakKeyDictionary()
_ISSUERS: WeakKeyDictionary[_Evidence, _Registry] = WeakKeyDictionary()
_MACHINE_LOCK = RLock()
_SUPPRESS_TRACE: ContextVar[bool] = ContextVar("route_spike_no_trace", default=False)
_COMPILER = EntityID("route_compile_node")
_EVALS = EntityID("route_compile_args")
_SUPPORTED = frozenset({"lit", "arg", "add", "call"})


def _lit(value: Any) -> tuple:
    return ("lit", value)


def _arg(name: str) -> tuple:
    return ("arg", name)


def _item(value: tuple, index: int) -> tuple:
    return ("item", value, _lit(index))


def _instruction(op: str, *operands: tuple) -> tuple:
    return ("tuple", _lit(op), *operands)


def _chunk(*instructions: tuple) -> tuple:
    return ("tuple", *instructions, _instruction("END"))


def _compiler_entities() -> dict[EntityID, Any]:
    """Construct source expressions, never target host instructions."""
    descriptor = _arg("descriptor")
    kind = _item(descriptor, 0)
    payload = _item(descriptor, 1)
    roles = _item(descriptor, 2)
    left = _item(_item(roles, 0), 1)
    right = _item(_item(roles, 1), 1)
    args = _item(_item(roles, 0), 1)
    target = _item(_item(roles, 1), 1)
    cases = (
        "if", ("eq", kind, _lit("lit")),
        _chunk(_instruction("LIT", payload)),
        (
            "if", ("eq", kind, _lit("arg")),
            _chunk(_instruction("ARG", payload)),
            (
                "if", ("eq", kind, _lit("add")),
                _chunk(
                    _instruction("EVAL", left),
                    _instruction("INT", _lit("add")),
                    _instruction("EVAL", right),
                    _instruction("INT", _lit("add")),
                    _instruction("ADD"),
                ),
                (
                    "concat",
                    ("call", "evals", args, _lit(0)),
                    ("tuple", _instruction("CALL", target, ("len", args)),
                     _instruction("END")),
                ),
            ),
        ),
    )
    xs, i = _arg("xs"), _arg("i")
    evals = (
        "if", ("lt", i, ("len", xs)),
        (
            "concat",
            ("tuple", _instruction("EVAL", ("item", xs, i))),
            ("call", "evals", xs, ("add", i, _lit(1))),
        ),
        _lit(()),
    )
    return {
        _COMPILER: Function(("descriptor",), cases),
        EntityID("route_compile_node.links"): links(_COMPILER, evals=_EVALS),
        _EVALS: Function(("xs", "i"), evals),
        EntityID("route_compile_args.links"): links(_EVALS, evals=_EVALS),
    }


def _decode_result(value: Any) -> Any:
    """Generic canonical boundary decoder; no opcode or position branches."""
    if isinstance(value, CanonicalNode):
        tag, payload = value[1], value[2]
        if tag == "entity_id":
            return EntityID(payload)
        if tag == "version_id":
            return VersionID(payload)
        if tag == "state_id":
            return StateID(payload)
        if tag == "bytes":
            return bytes.fromhex(payload)
        if tag == "tuple":
            return tuple(_decode_result(item) for item in payload)
        if tag == "list":
            return [_decode_result(item) for item in payload]
        if tag == "map":
            return {
                _decode_result(key): _decode_result(item)
                for key, item in payload
            }
        return value
    if isinstance(value, tuple):
        return tuple(_decode_result(item) for item in value)
    if isinstance(value, list):
        return [_decode_result(item) for item in value]
    if isinstance(value, dict):
        return {
            _decode_result(key): _decode_result(item)
            for key, item in value.items()
        }
    return value


def _event(registry: _Registry, kind: str, record: _Production) -> None:
    if not _SUPPRESS_TRACE.get():
        registry.events.append(RouteEvent(
            kind, {"produce": "shear-compiler", "admit": "host-admission",
                   "execute": "admitted-host"}[kind],
            record.entity, record.version, record.artifact_id,
            record.compiler_entity if kind == "produce" else None,
            record.compiler_version if kind == "produce" else None,
        ))


def _node(state: State, entity: EntityID) -> tuple[Relation, EntityID, Any]:
    value = state.values.get(entity)
    relation = None if value is None else relation_of(value)
    owner = state.owner_of(entity)
    definition = (
        None if owner is None or owner not in state.values
        else _definition_of(state.values[owner])
    )
    if (relation is None or relation.kind not in _SUPPORTED or
            definition is None or entity not in state.owned_subtree(owner)):
        raise AdmissionRejected(f"unsupported or unowned code node {entity!r}")
    return relation, owner, definition


def _descriptor(relation: Relation, owner: EntityID, definition: Any) -> tuple:
    return (
        relation.kind,
        relation.payload,
        tuple(relation.roles.items()),
        owner,
        tuple(sorted(
            (name, entity) for name, entity in definition.links.items()
            if isinstance(entity, EntityID)
        )),
    )


def produce(runtime: Runtime, entity: EntityID) -> tuple[tuple, object]:
    """Observe one real SHEAR compiler call and issue one opaque handle."""
    state = runtime.active.state
    relation, owner, definition = _node(state, entity)
    registry = _ROUTES.setdefault(runtime, _Registry())
    if registry.compiler is None:
        registry.compiler = Runtime(load(program(_compiler_entities())))
    compiler = registry.compiler
    compiler_state = compiler.active.state
    version = state.values[entity].version_id
    compiler_version = compiler_state.values[_COMPILER].version_id
    # Ordinary SHEAR execution, not Python lowering or host bytecode creation.
    returned = run(compiler, _COMPILER, _descriptor(relation, owner, definition))
    chunk = _decode_result(returned)
    if runtime.active.state is not state or compiler.active.state is not compiler_state:
        raise AdmissionRejected("state changed during compiler invocation")
    if not isinstance(chunk, tuple):
        raise AdmissionRejected("compiler did not return a chunk")
    try:
        artifact_id = sha256(canonical_serialize(canonicalize(chunk))).hexdigest()
    except (TypeError, ValueError) as exc:
        raise AdmissionRejected("noncanonical compiler output") from exc
    record = _Production(state, entity, version, owner, chunk, artifact_id,
                         _COMPILER, compiler_version)
    evidence = _Evidence()
    registry.produced[evidence] = record
    _ISSUERS[evidence] = registry
    _event(registry, "produce", record)
    return chunk, evidence


def _validate(state: State, record: _Production) -> None:
    """Check structure and permitted references; do not recompile semantics."""
    relation, owner, definition = _node(state, record.entity)
    chunk = record.chunk
    kind = relation.kind
    if owner != record.owner or not chunk or chunk[-1] != ("END",):
        raise AdmissionRejected("owner or terminator mismatch")
    expected_tags = {
        "lit": ("LIT", "END"),
        "arg": ("ARG", "END"),
        "add": ("EVAL", "INT", "EVAL", "INT", "ADD", "END"),
    }
    if kind == "call":
        expected_tags[kind] = (
            *("EVAL" for _ in relation.roles["args"]), "CALL", "END"
        )
    try:
        if tuple(ins[0] for ins in chunk) != expected_tags[kind]:
            raise AdmissionRejected("unsupported control flow or opcode sequence")
        if not all(isinstance(ins, tuple) and ins and isinstance(ins[0], str)
                   for ins in chunk):
            raise AdmissionRejected("malformed instruction")
        for ins in chunk:
            op = ins[0]
            if op in ("END", "ADD") and len(ins) != 1:
                raise AdmissionRejected("nullary instruction has operands")
            if op in ("LIT", "ARG", "EVAL", "INT") and len(ins) != 2:
                raise AdmissionRejected("wrong instruction arity")
            if op == "EVAL":
                child = ins[1]
                if (not isinstance(child, EntityID) or
                        child not in relation.endpoints or
                        state.owner_of(child) != owner or
                        child not in state.values or
                        relation_of(state.values[child]) is None):
                    raise AdmissionRejected("foreign or non-code child")
            if op == "INT" and ins[1] != "add":
                raise AdmissionRejected("unsupported integer guard")
            if op == "ARG" and not isinstance(ins[1], str):
                raise AdmissionRejected("argument is not a name")
            if op == "CALL":
                target, count = ins[1:]
                if (len(ins) != 3 or not isinstance(target, EntityID) or
                        target != relation.roles["target"] or
                        target not in definition.links.values() or
                        type(count) is not int or count != len(relation.roles["args"])):
                    raise AdmissionRejected("unlinked call or invalid arity")
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, AdmissionRejected):
            raise
        raise AdmissionRejected("malformed chunk structure") from exc


def admit(
    state: State, entity: EntityID, version: VersionID,
    chunk: tuple, evidence: object,
) -> _Production:
    """Store an authenticated, structural, state-bound derived artifact."""
    try:
        registry = _ISSUERS[evidence]
        record = registry.produced[evidence]
    except (KeyError, TypeError):
        raise AdmissionRejected("unrecognized producer evidence") from None
    if (state is not record.state or entity != record.entity or
            version != record.version or
            state.values.get(entity) is None or
            state.values[entity].version_id != version):
        raise AdmissionRejected("wrong node, state or version")
    try:
        same = canonical_serialize(canonicalize(chunk)) == canonical_serialize(
            canonicalize(record.chunk)
        )
    except (TypeError, ValueError):
        same = False
    if not same or sha256(canonical_serialize(canonicalize(record.chunk))).hexdigest() != record.artifact_id:
        raise AdmissionRejected("output does not match observed compiler result")
    _validate(state, record)
    registry.admitted[(state.id, entity, version)] = record
    _event(registry, "admit", record)
    return record


def trace(runtime: Runtime) -> tuple[RouteEvent, ...]:
    """Immutable snapshot of genuine host-side boundary events."""
    registry = _ROUTES.get(runtime)
    return () if registry is None else tuple(registry.events)


def run_admitted(runtime: Runtime, entry: EntityID, *args: Any) -> Any:
    """Execute only admitted chunks on the existing host machine.

    This bounded shim intercepts the machine's two chunk lookup boundaries.
    Any ordinary lowering/cache lookup is an error, never a fallback.
    """
    registry = _ROUTES.get(runtime)
    if registry is None:
        raise AdmissionRejected("no admitted artifacts for this runtime")

    def lookup(activation: Any, entity: EntityID, owner: EntityID) -> tuple:
        state = activation.hold.version.state
        value = state.values.get(entity)
        version = None if value is None else value.version_id
        record = registry.admitted.get((state.id, entity, version))
        if (record is None or state is not record.state or
                state.owner_of(entity) != owner or
                sha256(canonical_serialize(canonicalize(record.chunk))).hexdigest()
                != record.artifact_id):
            raise AdmissionRejected(f"no compatible admitted chunk: {entity!r}")
        _event(registry, "execute", record)
        return record.chunk

    def open_function(activation: Any, arguments: list,
                      where: Any = None, operation: str = "call") -> tuple:
        state = activation.hold.version.state
        value = state.values.get(activation.entity)
        definition = None if value is None else _definition_of(value)
        if definition is None or len(definition.params) != len(arguments):
            raise AdmissionRejected("absent function or wrong argument count")
        activation.values = state.values
        body = definition.body
        return lookup(activation, body, activation.entity), dict(
            zip(definition.params, arguments)
        ), body

    def child_chunk(activation: Any, entity: EntityID,
                    function: EntityID) -> tuple:
        return lookup(activation, entity, function)

    def no_fallback(*_args: Any, **_kw: Any) -> Any:
        raise AdmissionRejected("ordinary host lowering/cache fallback")

    with _MACHINE_LOCK:
        with (
            mock.patch.object(machine, "_open", open_function),
            mock.patch.object(machine, "_child_chunk", child_chunk),
            mock.patch.object(bytecode, "chunk_of", no_fallback),
            mock.patch.object(bytecode, "lower_value", no_fallback),
        ):
            return machine.run(runtime, entry, *args)


def _diagnostic() -> dict[str, Any]:
    """Explicit CI-only observations. No timing threshold is enforced."""
    import os
    import platform
    import statistics

    from .examples import vm
    from .lang import define
    from tests.test_execution_route import CALLER, TARGET, fixture

    def summary(values: list[float]) -> dict[str, Any]:
        return {"observations_s": values, "median_s": statistics.median(values),
                "min_s": min(values), "max_s": max(values)}

    generations: dict[int, list[float]] = {1: [], 2: [], 3: []}
    for _ in range(3):
        host_vm = Runtime(load(program(vm.bootstrap_entities())))
        for generation in (1, 2, 3):
            start = perf_counter()
            run(host_vm, vm.SWAP_ALL, may_activate=True)
            elapsed = perf_counter() - start
            actual = run(host_vm, vm.GENERATION)[0]
            if actual != generation:
                raise AssertionError((actual, generation))
            generations[generation].append(elapsed)

    samples: dict[str, list[float]] = {
        name: [] for name in ("production", "admission", "execution", "total",
                               "host_cold", "b_warm", "host_warm")
    }
    for _ in range(3):
        runtime = fixture()
        reference = fixture()
        nodes = sorted(runtime.active.state.owned_subtree(CALLER) |
                       runtime.active.state.owned_subtree(TARGET))
        token = _SUPPRESS_TRACE.set(True)
        try:
            begin = perf_counter()
            produced = [(node, *produce(runtime, node)) for node in nodes]
            mid1 = perf_counter()
            for node, chunk, evidence in produced:
                admit(runtime.active.state, node,
                      runtime.active.state.values[node].version_id, chunk, evidence)
            mid2 = perf_counter()
            result = run_admitted(runtime, CALLER, 4)
            mid3 = perf_counter()
            warm_start = perf_counter()
            warm = run_admitted(runtime, CALLER, 4)
            warm_elapsed = perf_counter() - warm_start
        finally:
            _SUPPRESS_TRACE.reset(token)
        host_start = perf_counter()
        actual = run(reference, CALLER, 4)
        host_elapsed = perf_counter() - host_start
        host_warm_start = perf_counter()
        host_warm = run(reference, CALLER, 4)
        host_warm_elapsed = perf_counter() - host_warm_start
        if (result, warm, actual, host_warm) != (7, 7, 7, 7):
            raise AssertionError("routes disagree on witness")
        for key, seconds in (
            ("production", mid1 - begin), ("admission", mid2 - mid1),
            ("execution", mid3 - mid2), ("total", mid3 - begin),
            ("host_cold", host_elapsed), ("b_warm", warm_elapsed),
            ("host_warm", host_warm_elapsed),
        ):
            samples[key].append(seconds)

    route_b_blocker = ""
    bootstrap = Runtime(load(program(vm.bootstrap_entities())))
    try:
        body = _definition_of(bootstrap.active.state.values[vm.SWAP_ALL]).body
        produce(bootstrap, body)
    except AdmissionRejected as exc:
        route_b_blocker = str(exc)
    else:
        raise AssertionError("bootstrap's unsupported nodes were accepted")

    edited = fixture()
    before = run(edited, TARGET, 4)
    start = perf_counter()
    result = define(edited.active.state, {
        TARGET: Function(("x",), ("add", ("arg", "x"), ("lit", 5))),
    })
    prep = perf_counter()
    candidate = Runtime(result.destination)
    for node in sorted(candidate.active.state.owned_subtree(TARGET)):
        chunk, evidence = produce(candidate, node)
        admit(candidate.active.state, node,
              candidate.active.state.values[node].version_id, chunk, evidence)
    if run_admitted(candidate, TARGET, 4) != 9:
        raise AssertionError("candidate behavior incorrect")
    lowered = perf_counter()
    edited.activate(result)
    activated = perf_counter()
    after = run(edited, TARGET, 4)
    if (before, after) != (7, 9):
        raise AssertionError("activation behavior incorrect")

    return {
        "revision": os.getenv("GITHUB_SHA", "unavailable"),
        "runner": os.getenv("RUNNER_NAME", "unavailable"),
        "python": platform.python_version(), "os": platform.platform(),
        "cpu_count": os.cpu_count(),
        "witness": "linked caller(x=4) -> target(x)+3, six or fewer nodes per function",
        "cache": "fresh separate runtimes per observation; cold target caches",
        "route_a_generation_s": {str(k): summary(v) for k, v in generations.items()},
        "route_b_generation": {"achieved": 0, "blocker": route_b_blocker},
        "p4_s": {name: summary(values) for name, values in samples.items()},
        "p4_median_ratio": (statistics.median(samples["total"]) /
                            statistics.median(samples["host_cold"])),
        "edit_s": {"prepare": prep-start, "candidate_compile_admit_run": lowered-prep,
                   "activate": activated-lowered, "total": activated-start,
                   "before": before, "after": after},
    }


if __name__ == "__main__":
    import json
    print(json.dumps(_diagnostic(), indent=2, sort_keys=True))
