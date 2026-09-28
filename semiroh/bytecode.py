"""Bytecode and a virtual machine for graph-form code (docs/bytecode.md).

Every expression node of a loaded program (lang.py) lowers to a **chunk**:
a tuple of instructions, each a plain tuple such as ``("ARG", "x")``,
``("MUL",)`` or ``("CALL", f, 2)``. A chunk holds the instructions of one
node only. It names the nodes below it by ``EntityID`` (``("EVAL", child)``),
so it depends on nothing but the node's own value. The chunk is derived data,
kept with the node's ``Value`` like its ``VersionID``: a node carried
unchanged into a new state keeps its chunk, and an edit that gives one node
a new value lowers that node again and nothing else.

:func:`run` executes a function on a machine with an explicit operand stack
and an explicit control stack. It reads nodes from the state a frame was
entered in, so code in flight keeps running the version it started in
(metaprogramming.md section 5). No Python recursion is involved in a call,
so the depth of non-tail recursion is bounded by ``CALL_DEPTH_LIMIT``, a
constant of the machine, not by ``sys.getrecursionlimit()``.

This module is a layer on top of :mod:`semiroh.lang`, which keeps the graph
form itself (``load``, ``define``, ``function_at``).
"""

from __future__ import annotations

from typing import Any, Mapping

from .canonical import CanonicalNode, canonical_serialize, canonicalize
from .identity import EntityID
from .lang import (
    INVALID_KIND,
    NODE_KINDS,
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
from .relations import Relation, relation_of
from .runtime import ActivationRejected, CellError, Runtime
from .values import Value

Instruction = tuple
Chunk = tuple

# Provisional (bytecode.md section 4): the most calls that may wait on each
# other in one run. The machine's stacks are not the host's, so without a
# limit a runaway recursion would use all the memory there is. A call in tail
# position replaces its caller and does not count.
CALL_DEPTH_LIMIT = 100_000

_END: Instruction = ("END",)
_RETURN: Chunk = (("RETURN",),)

# How many nodes have been lowered since the process started. Tests compare
# it before and after an edit to see which nodes were lowered again.
_lowered = 0


def lowered_count() -> int:
    """The number of nodes lowered so far (not the number of chunks kept)."""

    return _lowered


# ---------------------------------------------------------------------------
# Lowering
# ---------------------------------------------------------------------------


def _eval_all(entities: tuple[EntityID, ...]) -> list[Instruction]:
    return [("EVAL", entity) for entity in entities]


def lower(node: Relation) -> Chunk:
    """Lower one node to its chunk (docs/bytecode.md section 3).

    The chunk depends only on ``node``. Lowering never fails on code: an
    ``invalid`` node lowers to a ``RAISE`` that fails when the node is
    evaluated, at the point the expression would have failed. Instructions
    that check an operand come right after the operand's evaluation, before
    the next operand runs, so side effects happen or not in the order they
    always did.
    """

    kind = node.kind
    roles = node.roles
    code: list[Instruction]

    if kind == INVALID_KIND:
        code = [("RAISE", _decode(node.payload)[0])]
    elif kind == "lit":
        code = [("LIT", node.payload)]
    elif kind == "arg":
        code = [("ARG", _decode(node.payload))]
    elif kind in ("add", "sub", "mul", "lt"):
        code = [
            ("EVAL", roles["left"]),
            ("INT", kind),
            ("EVAL", roles["right"]),
            ("INT", kind),
            (kind.upper(),),
        ]
    elif kind == "eq":
        code = [("EVAL", roles["left"]), ("EVAL", roles["right"]), ("EQ",)]
    elif kind == "if":
        code = [
            ("EVAL", roles["cond"]),
            ("BRANCH", roles["then"], roles["else"]),
        ]
    elif kind == "seq":
        items = roles["items"]
        code = []

        for item in items[:-1]:
            code += [("EVAL", item), ("POP",)]

        code.append(("GOTO", items[-1]) if items else ("LIT", None))
    elif kind == "call":
        args = roles["args"]
        code = [*_eval_all(args), ("CALL", roles["target"], len(args))]
    elif kind == "tuple":
        items = roles["items"]
        code = [*_eval_all(items), ("MKTUPLE", len(items))]
    elif kind == "len":
        code = [("EVAL", roles["tuple"]), ("TUPLE", kind), ("LEN",)]
    elif kind == "item":
        code = [
            ("EVAL", roles["tuple"]),
            ("TUPLE", kind),
            ("EVAL", roles["index"]),
            ("INT", kind),
            ("ITEM",),
        ]
    elif kind == "slice":
        code = [
            ("EVAL", roles["tuple"]),
            ("TUPLE", kind),
            ("EVAL", roles["start"]),
            ("INT", kind),
            ("EVAL", roles["stop"]),
            ("INT", kind),
            ("SLICE",),
        ]
    elif kind == "concat":
        code = [
            ("EVAL", roles["left"]),
            ("TUPLE", kind),
            ("EVAL", roles["right"]),
            ("TUPLE", kind),
            ("CONCAT",),
        ]
    elif kind == "let":
        name = _decode(node.payload)
        code = [
            ("LETCHECK", name),
            ("EVAL", roles["value"]),
            ("LETBIND", name, roles["body"]),
        ]
    elif kind == "ref":
        code = [("REF", roles["target"], _decode(node.payload))]
    elif kind == "code":
        code = [("CODE", roles["target"], _decode(node.payload))]
    elif kind == "apply":
        args = roles["args"]
        code = [
            ("EVAL", roles["function"]),
            ("REFCHECK",),
            *_eval_all(args),
            ("APPLY", len(args)),
        ]
    elif kind == "read":
        code = [("READ", roles["cell"])]
    elif kind == "write":
        code = [("EVAL", roles["value"]), ("WRITE", roles["cell"])]
    elif kind == "quote":
        holes = roles["holes"]
        code = [*_eval_all(holes), ("QUOTE", node.payload, len(holes))]
    elif kind == "unquote":
        code = [("GOTO", roles["expr"])]
    elif kind == "function":
        code = [
            ("EVAL", roles["params"]),
            ("EVAL", roles["body"]),
            ("FUNCTION",),
        ]
    elif kind in ("activate", "trial"):
        code = _lower_activation(node)
    else:
        code = [("RAISE", f"unknown operation {kind!r}")]

    return (*code, _END)


def _lower_activation(node: Relation) -> list[Instruction]:
    """The chunk of an ``activate`` or ``trial`` node.

    A trial evaluates its call's arguments first. Both then check that
    every link has a value, before any value is evaluated, evaluate the
    values, and only then read the active state and check the pairs
    (metaprogramming.md section 4, language_trials.md section 2).
    """

    roles = node.roles
    payload = _decode(node.payload)
    entries = tuple(payload["links"])
    values = roles["values"]
    code: list[Instruction] = []

    if node.kind == "trial":
        code += _eval_all(roles["args"])

    if len(entries) != len(values):
        code.append(("RAISE", f"{node.kind} needs link/value pairs"))
        return code

    code += _eval_all(values)

    if node.kind == "activate":
        code.append(("ACTIVATE", entries, roles["targets"]))
    else:
        problem = payload["call"][1]
        code.append((
            "TRIAL",
            entries,
            roles["targets"],
            problem,
            roles.get("target"),
            len(roles["args"]),
        ))

    return code


def chunk_of(state: Any, entity: EntityID, owner: EntityID | None = None) -> Chunk:
    """The chunk of a node of ``state``, lowered now if it has none yet.

    ``owner`` names the function the node is run for, for the error of an
    entity that is not a code node.
    """

    value = state.values.get(entity)

    if value is not None:
        chunk = value.__dict__.get("_chunk")

        if chunk is not None:
            return chunk

    return _lower_value(value, entity, owner)


def _lower_value(value: Value | None, entity: EntityID, owner: EntityID | None) -> Chunk:
    global _lowered

    node = None if value is None else relation_of(value)

    if node is None or node.kind not in NODE_KINDS:
        where = owner.value if owner is not None else entity.value
        raise LanguageError(f"{where}: {entity.value} is not a code node")

    chunk = lower(node)
    object.__setattr__(value, "_chunk", chunk)
    _lowered += 1

    return chunk


def disassemble(chunk: Chunk) -> str:
    """One instruction per line, for reading and for tests."""

    def show(operand: Any) -> str:
        if isinstance(operand, EntityID):
            return operand.value

        if isinstance(operand, tuple):
            return "(" + ", ".join(show(item) for item in operand) + ")"

        return repr(operand)

    return "\n".join(
        " ".join([instruction[0], *(show(op) for op in instruction[1:])])
        for instruction in chunk
    )


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------


class _Activation:
    """One live call: the entity it runs, its hold on a version, and the
    state its nodes are read from. A tail call reuses the record for the
    callee, so a chain of tail calls keeps one activation.
    """

    __slots__ = ("entity", "hold", "values")

    def __init__(self, entity: EntityID, hold: Any) -> None:
        self.entity = entity
        self.hold = hold
        self.values: Mapping[EntityID, Value] = {}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _semantically_equal(left: Any, right: Any) -> bool:
    return canonical_serialize(canonicalize(left)) == canonical_serialize(
        canonicalize(right)
    )


def _items(value: Any) -> tuple[Any, ...] | None:
    """The items of a tuple value, live or canonical; None if not a tuple."""

    if isinstance(value, CanonicalNode):
        return value[2] if value[1] == "tuple" else None

    if isinstance(value, tuple):
        return value

    return None


def _reference(value: Any) -> EntityID | None:
    """The entity a function reference value names, live or canonical."""

    if isinstance(value, EntityID):
        return value

    if isinstance(value, CanonicalNode) and value[1] == "entity_id":
        return EntityID(value[2])

    return None


def _function(owner: EntityID, params: Any, body: Any) -> Function:
    params = _decode(params)
    body = _decode(body)

    if not isinstance(params, tuple):
        raise LanguageError(
            f"{owner.value}: function parameters must be a tuple"
        )

    if not isinstance(body, tuple):
        raise LanguageError(f"{owner.value}: function body must be a tuple")

    try:
        return Function(params, body)
    except (TypeError, ValueError) as exc:
        raise LanguageError(str(exc)) from exc


def _activation_pairs(
    runtime: Runtime,
    owner: EntityID,
    entries: tuple[Any, ...],
    targets: tuple[EntityID, ...],
    values: list[Any],
    op: str,
) -> tuple[Any, dict[EntityID | tuple[EntityID, str], Any]]:
    """Check the evaluated link/value pairs of ``activate`` or ``trial``.

    Shared by both (language_trials.md section 2: the pairs "are checked as
    for activate"). The active state is read here, after the values were
    evaluated, because evaluating a value can itself activate
    (language_trials.md section 8). Each link must resolve to an entity
    whose value in that state is a function, no target may appear twice, and
    a value is a Function for a whole-function target or an expression (code
    as data, not a Function value) for a ``(link, label)`` node target
    (graph_form.md section 9). Returns the active state and the edits to
    hand to :func:`semiroh.lang.define`.
    """

    active = runtime.active.state
    resolved = iter(targets)
    seen: set[Any] = set()
    edits: dict[EntityID | tuple[EntityID, str], Any] = {}

    for (name, problem), value in zip(entries, values):
        if problem is not None:
            raise LanguageError(f"{owner.value}: {problem}")

        target = next(resolved)
        label = name[1] if isinstance(name, tuple) else None
        key: EntityID | tuple[EntityID, str] = (
            (target, label) if label is not None else target
        )

        if key in seen:
            raise LanguageError(
                f"{owner.value}: {op} target appears twice: {target.value}"
            )

        seen.add(key)

        if target not in active.values:
            raise LanguageError(
                f"{owner.value}: {op} target does not exist: {target.value}"
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


def _pop_n(stack: list[Any], count: int) -> list[Any]:
    start = len(stack) - count
    values = stack[start:]
    del stack[start:]

    return values


def _open(
    activation: _Activation,
    args: list[Any],
) -> tuple[Chunk, dict[str, Any]]:
    """Read the callee's definition from the state its hold is on, and
    return the chunk of its body with the environment of its parameters.
    """

    entity = activation.entity
    state = activation.hold.version.state
    activation.values = state.values
    value = state.values[entity]
    definition = _definition_of(value)

    if definition is None:
        unloaded = function_of(value) is not None
        raise LanguageError(
            f"{entity.value} is not a function"
            + ("; load the program first" if unloaded else "")
        )

    if len(args) != len(definition.params):
        raise LanguageError(
            f"{entity.value} takes {len(definition.params)} argument(s), "
            f"got {len(args)}"
        )

    return (
        chunk_of(state, definition.body, entity),
        dict(zip(definition.params, args)),
    )


def _execute(
    runtime: Runtime,
    may_activate: bool,
    entry: EntityID,
    args: list[Any],
) -> Any:
    """Run ``entry`` on a fresh machine and return its result.

    The machine keeps a stack of operands and a stack of suspended
    cursors, ``(chunk, pc, tail, env, activation)``. ``tail`` says whether
    the node being run is in tail position of its function
    (language_data.md section 4). A node in tail position is reached only
    through ``GOTO``, ``BRANCH`` and ``LETBIND``, which do not suspend the
    cursor, so the cursor below it is always the call's ``RETURN``, and a
    call there reuses the activation instead of nesting another one.
    """

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
        control.append((_RETURN, 0, False, None, activation))

        while True:
            instr = chunk[pc]
            pc += 1
            op = instr[0]

            if op == "EVAL":
                value = activation.values.get(instr[1])
                child = None if value is None else value.__dict__.get("_chunk")

                if child is None:
                    child = _lower_value(value, instr[1], activation.entity)

                control.append((chunk, pc, tail, env, activation))
                chunk = child
                pc = 0
                tail = False
            elif op == "ARG":
                name = instr[1]

                if not isinstance(name, str) or name not in env:
                    raise LanguageError(
                        f"{activation.entity.value}: unknown parameter "
                        f"{name!r}"
                    )

                stack.append(env[name])
            elif op == "LIT":
                stack.append(_decode(instr[1]))
            elif op == "END":
                chunk, pc, tail, env, activation = control.pop()
            elif op == "INT":
                if not _is_int(stack[-1]):
                    raise LanguageError(
                        f"{activation.entity.value}: {instr[1]} operands "
                        f"must be int"
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
                stack[-1] = _semantically_equal(stack[-1], right)
            elif op == "BRANCH":
                condition = stack.pop()

                if not isinstance(condition, bool):
                    raise LanguageError(
                        f"{activation.entity.value}: if condition must be "
                        f"bool"
                    )

                entity = instr[1] if condition else instr[2]
                value = activation.values.get(entity)
                child = None if value is None else value.__dict__.get("_chunk")

                if child is None:
                    child = _lower_value(value, entity, activation.entity)

                chunk = child
                pc = 0
            elif op == "GOTO":
                value = activation.values.get(instr[1])
                child = None if value is None else value.__dict__.get("_chunk")

                if child is None:
                    child = _lower_value(value, instr[1], activation.entity)

                chunk = child
                pc = 0
            elif op == "POP":
                stack.pop()
            elif op == "CALL" or op == "APPLY":
                if op == "CALL":
                    target = instr[1]
                    arguments = _pop_n(stack, instr[2])
                else:
                    arguments = _pop_n(stack, instr[1])
                    target = stack.pop()

                    # A reference is an EntityID, so it does not follow a
                    # rename (language_data.md section 3); the check is
                    # against the active state, as `call` enters its target
                    # there.
                    if not runtime.active.state.contains(target):
                        raise LanguageError(
                            f"{activation.entity.value}: apply of "
                            f"{target.value}, which is not in the active "
                            f"state"
                        )

                if not tail and len(live) >= CALL_DEPTH_LIMIT:
                    raise CallDepthExceeded(
                        f"{activation.entity.value}: more than "
                        f"{CALL_DEPTH_LIMIT} calls waiting on each other"
                    )

                hold = runtime.enter(target)

                if tail:
                    released = activation.hold
                    activation.entity = target
                    activation.hold = hold
                    released.release()
                else:
                    control.append((chunk, pc, tail, env, activation))
                    activation = _Activation(target, hold)
                    live.append(activation)
                    control.append((_RETURN, 0, False, None, activation))

                chunk, env = _open(activation, arguments)
                pc = 0
                tail = True
            elif op == "RETURN":
                live.pop()
                activation.hold.release()

                if not control:
                    return stack.pop()

                chunk, pc, tail, env, activation = control.pop()
            elif op == "LETCHECK":
                if instr[1] in env:
                    raise LanguageError(
                        f"{activation.entity.value}: let name {instr[1]!r} "
                        f"is already in scope"
                    )
            elif op == "LETBIND":
                env = {**env, instr[1]: stack.pop()}
                value = activation.values.get(instr[2])
                child = None if value is None else value.__dict__.get("_chunk")

                if child is None:
                    child = _lower_value(value, instr[2], activation.entity)

                chunk = child
                pc = 0
            elif op == "MKTUPLE":
                stack.append(tuple(_pop_n(stack, instr[1])))
            elif op == "TUPLE":
                items = _items(stack.pop())

                if items is None:
                    raise LanguageError(
                        f"{activation.entity.value}: {instr[1]} operands "
                        f"must be tuples"
                    )

                stack.append(items)
            elif op == "LEN":
                stack.append(len(stack.pop()))
            elif op == "ITEM":
                index = stack.pop()
                items = stack.pop()

                if not 0 <= index < len(items):
                    raise LanguageError(
                        f"{activation.entity.value}: item index {index} is "
                        f"outside a tuple of {len(items)}"
                    )

                stack.append(items[index])
            elif op == "SLICE":
                stop = stack.pop()
                start = stack.pop()
                items = stack.pop()

                if not 0 <= start <= stop <= len(items):
                    raise LanguageError(
                        f"{activation.entity.value}: slice {start}:{stop} "
                        f"is outside a tuple of {len(items)}"
                    )

                stack.append(items[start:stop])
            elif op == "CONCAT":
                right = stack.pop()
                stack[-1] = stack[-1] + right
            elif op == "REF":
                held = activation.values.get(instr[1])

                if held is None or _definition_of(held) is None:
                    raise LanguageError(
                        f"{activation.entity.value}: ref {instr[2]!r} does "
                        f"not name a function"
                    )

                stack.append(instr[1])
            elif op == "CODE":
                function = function_at(runtime.active.state, instr[1])

                if function is None:
                    raise LanguageError(
                        f"{activation.entity.value}: code {instr[2]!r} does "
                        f"not name a function"
                    )

                stack.append((function.params, function.body))
            elif op == "REFCHECK":
                target = _reference(stack.pop())

                if target is None:
                    raise LanguageError(
                        f"{activation.entity.value}: apply needs a "
                        f"reference to a function"
                    )

                stack.append(target)
            elif op == "READ":
                # CellError means the link names something that is not a
                # cell: a language mistake (graph_form.md section 3), not a
                # constraint rejection, so it becomes a LanguageError.
                # CellContentRejected and RelationConstraintRejected are
                # constraint failures and are left to propagate unchanged.
                try:
                    stack.append(runtime.read(instr[1]))
                except CellError as exc:
                    raise LanguageError(str(exc)) from exc
            elif op == "WRITE":
                try:
                    runtime.write(instr[1], stack[-1])
                except CellError as exc:
                    raise LanguageError(str(exc)) from exc
            elif op == "QUOTE":
                holes = iter(_pop_n(stack, instr[2]))
                stack.append(_fill(_decode(instr[1]), holes))
            elif op == "FUNCTION":
                body = stack.pop()
                params = stack.pop()
                stack.append(_function(activation.entity, params, body))
            elif op == "ACTIVATE":
                values = _pop_n(stack, len(instr[1]))
                active, edits = _activation_pairs(
                    runtime,
                    activation.entity,
                    instr[1],
                    instr[2],
                    values,
                    "activate",
                )

                if not may_activate:
                    raise ActivationRejected("activation capability not granted")

                runtime.activate(define(active, edits))
                stack.append(None)
            elif op == "TRIAL":
                _, entries, targets, problem, target, arg_count = instr
                values = _pop_n(stack, len(entries))
                arguments = _pop_n(stack, arg_count)
                active, edits = _activation_pairs(
                    runtime,
                    activation.entity,
                    entries,
                    targets,
                    values,
                    "trial",
                )

                if problem is not None:
                    raise LanguageError(f"{activation.entity.value}: {problem}")

                if not may_activate:
                    raise ActivationRejected("activation capability not granted")

                # The linked function runs in the isolated runtime, without
                # the activation capability; the real runtime is never
                # touched (language_trials.md).
                candidate = runtime.trial(define(active, edits))
                stack.append(_execute(candidate, False, target, arguments))
            elif op == "RAISE":
                raise LanguageError(f"{activation.entity.value}: {instr[1]}")
            else:
                raise LanguageError(
                    f"{activation.entity.value}: unknown instruction {op!r}"
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
    """Evaluate ``entry`` and return its result (lang.run).

    The runtime's program must be in graph form (:func:`semiroh.lang.load`).
    Arguments are canonicalized before being bound to the entry function's
    parameters. Every call enters and releases a frame, so a finished run
    leaves no holds; a run that raises releases its frames too.

    By default a run cannot activate a new program state. Passing
    ``may_activate=True`` grants the run the provisional activation
    capability described in metaprogramming.md section 4.
    """

    return _execute(
        runtime,
        may_activate,
        entry,
        [canonicalize(arg) for arg in args],
    )
