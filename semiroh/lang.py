"""A tiny language interpreted directly over semantic state (first_program.md).

A **function** is an entity whose value is a :class:`Function`: parameter
names plus a body expression tree of plain tuples. A function never holds
raw ``EntityID``\\ s; it names the functions and cells it uses through link
names, resolved via its own **links relation** (:func:`links`). Running a
function never changes program state: :func:`run` only reads and writes
mutable cells through the ``Runtime`` it is given.

This module is a layer on top of the core model, not part of it: it is not
re-exported from ``semiroh/__init__.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import (
    CanonicalNode,
    SemanticRecord,
    _node,
    canonical_serialize,
    canonicalize,
)
from .identity import EntityID
from .relations import Relation, relation_index, relation_of
from .runtime import CellError, Runtime
from .state import State
from .values import Value

# The role a function plays in its own links relation; reserved as a link
# name (first_program.md section 2).
FUNCTION_ROLE = "function"
LINKS_KIND = "links"


class LanguageError(ValueError):
    """The program used the language incorrectly.

    Covers an unknown operation, an unknown link name, a wrong number of
    arguments, calling something that is not a function, reading or writing
    something that is not a cell, and operands of the wrong kind.
    """


@dataclass(frozen=True, eq=False)
class Function(SemanticRecord):
    """Semantic record: a function's parameters and body.

    ``body`` is a plain tuple expression tree (first_program.md section 2).
    Both fields stay ordinary Python data while the record is held live;
    only :meth:`canonical_node` canonicalizes them, so a body read back from
    a ``Value`` arrives as tagged canonical nodes and must be decoded (see
    :func:`function_of`) before it is evaluated.
    """

    params: tuple[str, ...]
    body: tuple

    def __post_init__(self) -> None:
        params = tuple(self.params)

        if not all(isinstance(name, str) and name for name in params):
            raise TypeError("function parameters must be non-empty strings")

        if len(params) != len(set(params)):
            raise TypeError("duplicate function parameter name")

        if not isinstance(self.body, tuple) or not self.body:
            raise TypeError(
                "function body must be a non-empty tuple expression"
            )

        object.__setattr__(self, "params", params)

    def canonical_node(self) -> CanonicalNode:
        return _node(
            "function",
            (canonicalize(self.params), canonicalize(self.body)),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Function):
            return NotImplemented

        return canonical_serialize(self) == canonical_serialize(other)

    def __hash__(self) -> int:
        return hash(canonical_serialize(self))


def _decode(node: Any) -> Any:
    """Undo canonicalization of a tuple/list-shaped expression tree."""

    if isinstance(node, CanonicalNode):
        kind = node[1]

        if kind == "tuple":
            return tuple(_decode(item) for item in node[2])

        if kind == "list":
            return [_decode(item) for item in node[2]]

    return node


def function_of(value: Value) -> Function | None:
    """Return the Function held by a value, or None if it does not hold one."""

    content = value.content

    if isinstance(content, CanonicalNode) and content[1] == "function":
        params, body = content[2]

        return Function(_decode(params), _decode(body))

    return None


def links(function: EntityID, **targets: EntityID) -> Relation:
    """The links relation of a function: link name to target entity.

    ``function`` is the function entity itself, stored under the reserved
    ``function`` role so its links relation can be found from either side
    (section 2). Because that role is also this parameter's name, passing a
    ``function=`` link target raises ``TypeError`` before this body runs;
    nothing here needs to guard against it separately.
    """

    return Relation(LINKS_KIND, {FUNCTION_ROLE: function, **targets})


def _links_of(state: State, function: EntityID) -> Relation | None:
    """Return the links relation for a function entity, if it has one."""

    found: list[Relation] = []

    for relation_entity, role in relation_index(state).get(function, ()):
        if role != FUNCTION_ROLE:
            continue

        relation = relation_of(state.values[relation_entity])

        if relation is not None and relation.kind == LINKS_KIND:
            found.append(relation)

    if len(found) > 1:
        raise LanguageError(
            f"{function.value} has more than one links relation"
        )

    return found[0] if found else None


def _resolve_link(
    function_entity: EntityID,
    links_relation: Relation | None,
    link_name: Any,
) -> EntityID:
    """Resolve a link name used in a function's body to its target entity."""

    if (
        not isinstance(link_name, str)
        or link_name == FUNCTION_ROLE
        or links_relation is None
        or link_name not in links_relation.roles
    ):
        raise LanguageError(
            f"{function_entity.value}: unknown link {link_name!r}"
        )

    target = links_relation.roles[link_name]

    if not isinstance(target, EntityID):
        raise LanguageError(
            f"{function_entity.value}: link {link_name!r} does not name a "
            f"single entity"
        )

    return target


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _semantically_equal(left: Any, right: Any) -> bool:
    return canonical_serialize(canonicalize(left)) == canonical_serialize(
        canonicalize(right)
    )


def _arity(
    function_entity: EntityID,
    op: str,
    rest: tuple[Any, ...],
    expected: int,
) -> None:
    if len(rest) != expected:
        raise LanguageError(
            f"{function_entity.value}: {op} takes {expected} operand(s), "
            f"got {len(rest)}"
        )


def _eval_int(
    runtime: Runtime,
    function_entity: EntityID,
    links_relation: Relation | None,
    bindings: dict[str, Any],
    node: Any,
    op: str,
) -> int:
    value = _eval(runtime, function_entity, links_relation, bindings, node)

    if not _is_int(value):
        raise LanguageError(
            f"{function_entity.value}: {op} operands must be int"
        )

    return value


def _eval(
    runtime: Runtime,
    function_entity: EntityID,
    links_relation: Relation | None,
    bindings: dict[str, Any],
    node: Any,
) -> Any:
    """Evaluate one expression node of a function body."""

    if not isinstance(node, tuple) or not node or not isinstance(node[0], str):
        raise LanguageError(
            f"{function_entity.value}: not a valid expression: {node!r}"
        )

    op, *rest = node

    if op == "lit":
        _arity(function_entity, op, rest, 1)

        return rest[0]

    if op == "arg":
        _arity(function_entity, op, rest, 1)
        name = rest[0]

        if not isinstance(name, str) or name not in bindings:
            raise LanguageError(
                f"{function_entity.value}: unknown parameter {name!r}"
            )

        return bindings[name]

    if op in ("add", "sub", "mul"):
        _arity(function_entity, op, rest, 2)
        left = _eval_int(
            runtime, function_entity, links_relation, bindings, rest[0], op
        )
        right = _eval_int(
            runtime, function_entity, links_relation, bindings, rest[1], op
        )

        if op == "add":
            return left + right

        if op == "sub":
            return left - right

        return left * right

    if op == "lt":
        _arity(function_entity, op, rest, 2)
        left = _eval_int(
            runtime, function_entity, links_relation, bindings, rest[0], op
        )
        right = _eval_int(
            runtime, function_entity, links_relation, bindings, rest[1], op
        )

        return left < right

    if op == "eq":
        _arity(function_entity, op, rest, 2)
        left = _eval(runtime, function_entity, links_relation, bindings, rest[0])
        right = _eval(
            runtime, function_entity, links_relation, bindings, rest[1]
        )

        return _semantically_equal(left, right)

    if op == "if":
        _arity(function_entity, op, rest, 3)
        condition = _eval(
            runtime, function_entity, links_relation, bindings, rest[0]
        )

        if not isinstance(condition, bool):
            raise LanguageError(
                f"{function_entity.value}: if condition must be bool"
            )

        branch = rest[1] if condition else rest[2]

        return _eval(runtime, function_entity, links_relation, bindings, branch)

    if op == "seq":
        if not rest:
            raise LanguageError(
                f"{function_entity.value}: seq needs at least one expression"
            )

        result: Any = None

        for expr in rest:
            result = _eval(
                runtime, function_entity, links_relation, bindings, expr
            )

        return result

    if op == "call":
        if not rest:
            raise LanguageError(f"{function_entity.value}: call needs a link")

        link_name, *arg_exprs = rest
        target = _resolve_link(function_entity, links_relation, link_name)
        args = tuple(
            _eval(runtime, function_entity, links_relation, bindings, expr)
            for expr in arg_exprs
        )

        return _call(runtime, target, args)

    if op == "read":
        _arity(function_entity, op, rest, 1)
        cell = _resolve_link(function_entity, links_relation, rest[0])

        # CellError means the link names something that is not a cell: a
        # language mistake (section 3), not a constraint rejection, so it
        # becomes a LanguageError. CellContentRejected and
        # RelationConstraintRejected are constraint failures and are left to
        # propagate unchanged.
        try:
            return runtime.read(cell)
        except CellError as exc:
            raise LanguageError(str(exc)) from exc

    if op == "write":
        _arity(function_entity, op, rest, 2)
        cell = _resolve_link(function_entity, links_relation, rest[0])
        value = _eval(
            runtime, function_entity, links_relation, bindings, rest[1]
        )

        # Same distinction as "read" above.
        try:
            runtime.write(cell, value)
        except CellError as exc:
            raise LanguageError(str(exc)) from exc

        return value

    raise LanguageError(f"{function_entity.value}: unknown operation {op!r}")


def _call(runtime: Runtime, function_entity: EntityID, args: tuple[Any, ...]) -> Any:
    """Call a function entity with already-evaluated arguments."""

    frame = runtime.enter(function_entity)

    try:
        state = runtime.active.state
        function = function_of(state.values[function_entity])

        if function is None:
            raise LanguageError(f"{function_entity.value} is not a function")

        if len(args) != len(function.params):
            raise LanguageError(
                f"{function_entity.value} takes {len(function.params)} "
                f"argument(s), got {len(args)}"
            )

        bindings = dict(zip(function.params, args))
        links_relation = _links_of(state, function_entity)

        return _eval(
            runtime, function_entity, links_relation, bindings, function.body
        )
    finally:
        frame.release()


def run(runtime: Runtime, entry: EntityID, *args: Any) -> Any:
    """Evaluate ``entry`` in ``runtime.active`` and return the result.

    Arguments are canonicalized before being bound to the entry function's
    parameters. Every call, including the entry, enters and releases a
    frame, so a finished run leaves no holds; a run that raises releases its
    frames too. Running never changes program state or ``StateID``.
    """

    return _call(runtime, entry, tuple(canonicalize(arg) for arg in args))
