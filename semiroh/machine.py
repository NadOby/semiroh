"""Execution machine for SEMIROH bytecode."""

from __future__ import annotations

from typing import Any, Mapping

from . import bytecode
from .canonical import CanonicalNode, canonical_serialize, canonicalize
from .closures import Closure, closure_value
from .identity import EntityID
from .lang import (
    CallDepthExceeded,
    Function,
    LanguageError,
    _decode,
    _definition_of,
    _fill,
    _function_value,
    define,
    function_at,
    function_of,
)
from .runtime import ActivationRejected, CellError, Runtime
from .values import Value


_RETURN: bytecode.Chunk = (("RETURN",),)


class _Activation:
    """One live call and its hold on a program version."""

    __slots__ = ("entity", "hold", "values")

    def __init__(self, entity: EntityID, hold: Any) -> None:
        self.entity = entity
        self.hold = hold
        self.values: Mapping[EntityID, Value] = {}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


_PRIMITIVES = (str, int, bool, type(None))


def _semantically_equal(left: Any, right: Any) -> bool:
    if type(left) in _PRIMITIVES and type(right) in _PRIMITIVES:
        return type(left) is type(right) and left == right

    return canonical_serialize(canonicalize(left)) == canonical_serialize(
        canonicalize(right)
    )


def _items(value: Any) -> tuple[Any, ...] | None:
    if isinstance(value, CanonicalNode):
        return value[2] if value[1] == "tuple" else None

    if isinstance(value, tuple):
        return value

    return None


def _reference(value: Any) -> EntityID | None:
    if isinstance(value, EntityID):
        return value

    if isinstance(value, CanonicalNode) and value[1] == "entity_id":
        return EntityID(value[2])

    return None


def _callable(value: Any) -> EntityID | Closure | None:
    reference = _reference(value)

    if reference is not None:
        return reference

    return closure_value(value)


def _function(owner: EntityID, params: Any, body: Any) -> Function:
    params = _decode(params)
    body = _decode(body)

    if not isinstance(params, tuple):
        raise LanguageError(
            f"{owner.value}: function parameters must be a tuple"
        )

    if not isinstance(body, tuple):
        raise LanguageError(
            f"{owner.value}: function body must be a tuple"
        )

    try:
        return Function(params, body)
    except (TypeError, ValueError) as exc:
        raise LanguageError(str(exc)) from exc


def _closure(
    owner: EntityID,
    body: EntityID,
    params: Any,
    capture_names: Any,
    env: Mapping[str, Any],
) -> Closure:
    params = _decode(params)
    capture_names = _decode(capture_names)

    if not isinstance(params, tuple):
        raise LanguageError(
            f"{owner.value}: closure parameters must be a tuple"
        )

    if not isinstance(capture_names, tuple):
        raise LanguageError(
            f"{owner.value}: closure captures must be a tuple"
        )

    if not all(
        isinstance(name, str) and name
        for name in capture_names
    ):
        raise LanguageError(
            f"{owner.value}: "
            "closure captures need non-empty string names"
        )

    captures: list[tuple[str, Any]] = []

    for name in capture_names:
        if name not in env:
            raise LanguageError(
                f"{owner.value}: missing closure capture {name!r}"
            )

        captures.append((name, env[name]))

    try:
        return Closure(
            owner,
            body,
            params,
            tuple(captures),
        )
    except (TypeError, ValueError) as exc:
        raise LanguageError(
            f"{owner.value}: {exc}"
        ) from exc


def _activation_pairs(
    runtime: Runtime,
    owner: EntityID,
    entries: tuple[Any, ...],
    targets: tuple[EntityID, ...],
    values: list[Any],
    op: str,
) -> tuple[Any, dict[EntityID | tuple[EntityID, str], Any]]:
    active = runtime.active.state
    resolved = iter(targets)
    seen: set[Any] = set()
    edits: dict[EntityID | tuple[EntityID, str], Any] = {}

    for (name, problem), value in zip(entries, values):
        if problem is not None:
            raise LanguageError(
                f"{owner.value}: {problem}"
            )

        target = next(resolved)
        label = name[1] if isinstance(name, tuple) else None
        key: EntityID | tuple[EntityID, str] = (
            (target, label)
            if label is not None
            else target
        )

        if key in seen:
            raise LanguageError(
                f"{owner.value}: {op} target appears twice: "
                f"{target.value}"
            )

        seen.add(key)

        if target not in active.values:
            raise LanguageError(
                f"{owner.value}: {op} target does not exist: "
                f"{target.value}"
            )

        if _definition_of(active.values[target]) is None:
            raise LanguageError(
                f"{owner.value}: {op} target is not a function: "
                f"{target.value}"
            )

        function = _function_value(value)

        if label is not None:
            if function is not None:
                raise LanguageError(
                    f"{owner.value}: {op} value is not an expression: "
                    f"{target.value}"
                )

            edits[key] = value
        else:
            if function is None:
                raise LanguageError(
                    f"{owner.value}: {op} value is not a function: "
                    f"{target.value}"
                )

            edits[key] = function

    return active, edits


def _pop_n(
    stack: list[Any],
    count: int,
) -> list[Any]:
    start = len(stack) - count
    values = stack[start:]
    del stack[start:]

    return values


def _open(
    activation: _Activation,
    args: list[Any],
) -> tuple[bytecode.Chunk, dict[str, Any]]:
    entity = activation.entity
    state = activation.hold.version.state
    activation.values = state.values
    value = state.values[entity]
    definition = _definition_of(value)

    if definition is None:
        unloaded = function_of(value) is not None
        raise LanguageError(
            f"{entity.value} is not a function"
            + (
                "; load the program first"
                if unloaded
                else ""
            )
        )

    if len(args) != len(definition.params):
        raise LanguageError(
            f"{entity.value} takes "
            f"{len(definition.params)} argument(s), "
            f"got {len(args)}"
        )

    return (
        bytecode.chunk_of(
            state,
            definition.body,
            entity,
        ),
        dict(zip(definition.params, args)),
    )


def _open_closure(
    activation: _Activation,
    closure: Closure,
    args: list[Any],
) -> tuple[bytecode.Chunk, dict[str, Any]]:
    state = activation.hold.version.state
    activation.values = state.values

    owner_value = state.values.get(closure.owner)

    if (
        owner_value is None
        or _definition_of(owner_value) is None
    ):
        raise LanguageError(
            f"{closure.owner.value}: closure owner is not "
            f"a function in the active version"
        )

    if closure.body not in state.values:
        raise LanguageError(
            f"{closure.owner.value}: closure body "
            f"{closure.body.value} is absent from the active version"
        )

    if state.owner_of(closure.body) != closure.owner:
        raise LanguageError(
            f"{closure.owner.value}: closure body "
            f"{closure.body.value} no longer belongs to its owner"
        )

    if len(args) != len(closure.params):
        raise LanguageError(
            f"{closure.owner.value} closure takes "
            f"{len(closure.params)} argument(s), "
            f"got {len(args)}"
        )

    env = dict(closure.captures)
    env.update(zip(closure.params, args))

    return (
        bytecode.chunk_of(
            state,
            closure.body,
            closure.owner,
        ),
        env,
    )


def _resolved_call(
    runtime: Runtime,
    owner: EntityID,
    target: EntityID | Closure,
) -> tuple[EntityID, Closure | None]:
    active = runtime.active.state

    if isinstance(target, Closure):
        if not active.contains(target.owner):
            raise LanguageError(
                f"{owner.value}: apply of closure whose owner "
                f"{target.owner.value} is not in the active state"
            )

        if not active.contains(target.body):
            raise LanguageError(
                f"{owner.value}: apply of closure whose body "
                f"{target.body.value} is not in the active state"
            )

        return target.owner, target

    if not active.contains(target):
        raise LanguageError(
            f"{owner.value}: apply of {target.value}, "
            f"which is not in the active state"
        )

    return target, None


def _execute(
    runtime: Runtime,
    may_activate: bool,
    entry: EntityID,
    args: list[Any],
) -> Any:
    stack: list[Any] = []
    control: list[tuple] = []
    live: list[_Activation] = []

    try:
        hold = runtime.enter(entry)
        activation = _Activation(entry, hold)
        live.append(activation)
        chunk, env = _open(activation, args)
        pc = 0
        tail = True
        control.append(
            (_RETURN, 0, False, None, activation)
        )

        while True:
            instr = chunk[pc]
            pc += 1
            op = instr[0]

            if op == "EVAL":
                value = activation.values.get(instr[1])
                child = (
                    None
                    if value is None
                    else value.__dict__.get("_chunk")
                )

                if child is None:
                    child = bytecode._lower_value(
                        value,
                        instr[1],
                        activation.entity,
                    )

                control.append(
                    (chunk, pc, tail, env, activation)
                )
                chunk = child
                pc = 0
                tail = False

            elif op == "ARG":
                name = instr[1]

                if (
                    not isinstance(name, str)
                    or name not in env
                ):
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"unknown parameter {name!r}"
                    )

                stack.append(env[name])

            elif op == "LIT":
                stack.append(_decode(instr[1]))

            elif op == "END":
                (
                    chunk,
                    pc,
                    tail,
                    env,
                    activation,
                ) = control.pop()

            elif op == "INT":
                if not _is_int(stack[-1]):
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"{instr[1]} operands must be int"
                    )

            elif op == "ADD":
                right = stack.pop()
                stack[-1] += right

            elif op == "SUB":
                right = stack.pop()
                stack[-1] -= right

            elif op == "MUL":
                right = stack.pop()
                stack[-1] *= right

            elif op == "LT":
                right = stack.pop()
                stack[-1] = stack[-1] < right

            elif op == "EQ":
                right = stack.pop()
                stack[-1] = _semantically_equal(
                    stack[-1],
                    right,
                )

            elif op == "BRANCH":
                condition = stack.pop()

                if not isinstance(condition, bool):
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"if condition must be bool"
                    )

                entity = (
                    instr[1]
                    if condition
                    else instr[2]
                )
                value = activation.values.get(entity)
                child = (
                    None
                    if value is None
                    else value.__dict__.get("_chunk")
                )

                if child is None:
                    child = bytecode._lower_value(
                        value,
                        entity,
                        activation.entity,
                    )

                chunk = child
                pc = 0

            elif op == "GOTO":
                value = activation.values.get(instr[1])
                child = (
                    None
                    if value is None
                    else value.__dict__.get("_chunk")
                )

                if child is None:
                    child = bytecode._lower_value(
                        value,
                        instr[1],
                        activation.entity,
                    )

                chunk = child
                pc = 0

            elif op == "POP":
                stack.pop()

            elif op in ("CALL", "APPLY", "APPLYV"):
                closure: Closure | None = None

                if op == "CALL":
                    target_entity = instr[1]
                    arguments = _pop_n(
                        stack,
                        instr[2],
                    )
                else:
                    if op == "APPLY":
                        arguments = _pop_n(
                            stack,
                            instr[1],
                        )
                    else:
                        arguments = list(stack.pop())

                    target = stack.pop()
                    target_entity, closure = _resolved_call(
                        runtime,
                        activation.entity,
                        target,
                    )

                if (
                    not tail
                    and len(live)
                    >= bytecode.CALL_DEPTH_LIMIT
                ):
                    raise CallDepthExceeded(
                        f"{activation.entity.value}: "
                        f"more than "
                        f"{bytecode.CALL_DEPTH_LIMIT} "
                        f"calls waiting on each other"
                    )

                hold = runtime.enter(target_entity)

                if tail:
                    released = activation.hold
                    activation.entity = target_entity
                    activation.hold = hold
                    released.release()
                else:
                    control.append(
                        (
                            chunk,
                            pc,
                            tail,
                            env,
                            activation,
                        )
                    )
                    activation = _Activation(
                        target_entity,
                        hold,
                    )
                    live.append(activation)
                    control.append(
                        (
                            _RETURN,
                            0,
                            False,
                            None,
                            activation,
                        )
                    )

                if closure is None:
                    chunk, env = _open(
                        activation,
                        arguments,
                    )
                else:
                    chunk, env = _open_closure(
                        activation,
                        closure,
                        arguments,
                    )

                pc = 0
                tail = True

            elif op == "RETURN":
                live.pop()
                activation.hold.release()

                if not control:
                    return stack.pop()

                (
                    chunk,
                    pc,
                    tail,
                    env,
                    activation,
                ) = control.pop()

            elif op == "LETCHECK":
                if instr[1] in env:
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"let name {instr[1]!r} "
                        f"is already in scope"
                    )

            elif op == "LETBIND":
                env = {
                    **env,
                    instr[1]: stack.pop(),
                }
                value = activation.values.get(instr[2])
                child = (
                    None
                    if value is None
                    else value.__dict__.get("_chunk")
                )

                if child is None:
                    child = bytecode._lower_value(
                        value,
                        instr[2],
                        activation.entity,
                    )

                chunk = child
                pc = 0

            elif op == "MKTUPLE":
                stack.append(
                    tuple(
                        _pop_n(
                            stack,
                            instr[1],
                        )
                    )
                )

            elif op == "TUPLE":
                items = _items(stack.pop())

                if items is None:
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"{instr[1]} operands must be tuples"
                    )

                stack.append(items)

            elif op == "LEN":
                stack.append(
                    len(stack.pop())
                )

            elif op == "ITEM":
                index = stack.pop()
                items = stack.pop()

                if not 0 <= index < len(items):
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"item index {index} is outside "
                        f"a tuple of {len(items)}"
                    )

                stack.append(items[index])

            elif op == "SLICE":
                stop = stack.pop()
                start = stack.pop()
                items = stack.pop()

                if not 0 <= start <= stop <= len(items):
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"slice {start}:{stop} is outside "
                        f"a tuple of {len(items)}"
                    )

                stack.append(
                    items[start:stop]
                )

            elif op == "CONCAT":
                right = stack.pop()
                stack[-1] = (
                    stack[-1] + right
                )

            elif op == "REF":
                held = activation.values.get(
                    instr[1]
                )

                if (
                    held is None
                    or _definition_of(held) is None
                ):
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"ref {instr[2]!r} does not "
                        f"name a function"
                    )

                stack.append(instr[1])

            elif op == "CODE":
                function = function_at(
                    runtime.active.state,
                    instr[1],
                )

                if function is None:
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"code {instr[2]!r} does not "
                        f"name a function"
                    )

                stack.append(
                    (
                        function.params,
                        function.body,
                    )
                )

            elif op == "LINKS":
                held = runtime.active.state.values.get(
                    instr[1]
                )
                definition = (
                    None
                    if held is None
                    else _definition_of(held)
                )

                if definition is None:
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"linksof {instr[2]!r} does not "
                        f"name a function"
                    )

                stack.append(tuple(
                    (
                        name,
                        target,
                    )
                    for name, target in sorted(
                        definition.links.items()
                    )
                    if isinstance(
                        target,
                        EntityID,
                    )
                ))

            elif op == "REFCHECK":
                target = _callable(
                    stack.pop()
                )

                if target is None:
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"apply needs a function "
                        f"reference or closure"
                    )

                stack.append(target)

            elif op == "CLOSURE":
                stack.append(
                    _closure(
                        activation.entity,
                        instr[1],
                        instr[2],
                        instr[3],
                        env,
                    )
                )

            elif op == "READ":
                try:
                    stack.append(
                        runtime.read(instr[1])
                    )
                except CellError as exc:
                    raise LanguageError(
                        str(exc)
                    ) from exc

            elif op == "WRITE":
                try:
                    runtime.write(
                        instr[1],
                        stack[-1],
                    )
                except CellError as exc:
                    raise LanguageError(
                        str(exc)
                    ) from exc

            elif op == "QUOTE":
                holes = iter(
                    _pop_n(
                        stack,
                        instr[2],
                    )
                )
                stack.append(
                    _fill(
                        _decode(instr[1]),
                        holes,
                    )
                )

            elif op == "FUNCTION":
                body = stack.pop()
                params = stack.pop()
                stack.append(
                    _function(
                        activation.entity,
                        params,
                        body,
                    )
                )

            elif op == "ACTIVATE":
                values = _pop_n(
                    stack,
                    len(instr[1]),
                )
                active, edits = _activation_pairs(
                    runtime,
                    activation.entity,
                    instr[1],
                    instr[2],
                    values,
                    "activate",
                )

                if not may_activate:
                    raise ActivationRejected(
                        "activation capability not granted"
                    )

                runtime.activate(
                    define(active, edits)
                )
                stack.append(None)

            elif op == "TRIAL":
                (
                    _,
                    entries,
                    targets,
                    problem,
                    target,
                    arg_count,
                ) = instr
                values = _pop_n(
                    stack,
                    len(entries),
                )
                arguments = _pop_n(
                    stack,
                    arg_count,
                )
                active, edits = _activation_pairs(
                    runtime,
                    activation.entity,
                    entries,
                    targets,
                    values,
                    "trial",
                )

                if problem is not None:
                    raise LanguageError(
                        f"{activation.entity.value}: "
                        f"{problem}"
                    )

                if not may_activate:
                    raise ActivationRejected(
                        "activation capability not granted"
                    )

                candidate = runtime.trial(
                    define(active, edits)
                )
                stack.append(
                    _execute(
                        candidate,
                        False,
                        target,
                        arguments,
                    )
                )

            elif op == "RAISE":
                raise LanguageError(
                    f"{activation.entity.value}: "
                    f"{instr[1]}"
                )

            else:
                raise LanguageError(
                    f"{activation.entity.value}: "
                    f"unknown instruction {op!r}"
                )

    except BaseException:
        for pending in reversed(live):
            if not pending.hold.released:
                pending.hold.release()

        raise


def run(
    runtime: Runtime,
    entry: EntityID,
    *args: Any,
    may_activate: bool = False,
) -> Any:
    """Evaluate one graph-form function."""

    return _execute(
        runtime,
        may_activate,
        entry,
        [
            canonicalize(arg)
            for arg in args
        ],
    )
