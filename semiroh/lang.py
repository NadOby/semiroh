"""A tiny language interpreted directly over semantic state (first_program.md).

A **function** is an entity whose value is a :class:`Function`: parameter
names plus a body expression tree of plain tuples. A function never holds
raw ``EntityID``\\ s; it names the functions and cells it uses through link
names, resolved via its own **links relation** (:func:`links`). Running a
function can change program state only through ``activate``, and only when
the run was granted the activation capability.

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
from .runtime import ActivationRejected, CellError, Runtime
from .state import State
from .transforms import transform_with_mapping
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
    """Undo canonicalization of a tuple/list/map-shaped expression tree."""

    if isinstance(node, CanonicalNode):
        kind = node[1]

        if kind == "tuple":
            return tuple(_decode(item) for item in node[2])

        if kind == "list":
            return [_decode(item) for item in node[2]]

        if kind == "map":
            return {_decode(key): _decode(value) for key, value in node[2]}

    return node


def _function_from_canonical(content: Any) -> Function | None:
    """Decode a Function from its own canonical tagged node, if it is one."""

    if isinstance(content, CanonicalNode) and content[1] == "function":
        params, body = content[2]
        return Function(_decode(params), _decode(body))

    return None


def function_of(value: Value) -> Function | None:
    """Return the Function held by a value, or None if it does not hold one."""

    return _function_from_canonical(value.content)


def _function_value(value: Any) -> Function | None:
    """Decode a value that should be a Function value, live or canonical.

    A value built by ``("function", ...)`` in the same evaluation is already
    a live ``Function``. One read from a cell, matched from an ``arg``, or
    embedded as a ``lit`` literal that was canonicalized into state instead
    arrives as its canonical tagged node and must be decoded the same way
    (metaprogramming.md section 8).
    """

    if isinstance(value, Function):
        return value

    return _function_from_canonical(value)


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


@dataclass(frozen=True)
class _RunContext:
    runtime: Runtime
    may_activate: bool


def _eval_int(
    context: _RunContext,
    function_entity: EntityID,
    links_relation: Relation | None,
    bindings: dict[str, Any],
    node: Any,
    op: str,
) -> int:
    value = _eval(
        context,
        function_entity,
        links_relation,
        bindings,
        node,
    )

    if not _is_int(value):
        raise LanguageError(
            f"{function_entity.value}: {op} operands must be int"
        )

    return value


def _quote(
    context: _RunContext,
    function_entity: EntityID,
    links_relation: Relation | None,
    bindings: dict[str, Any],
    template: Any,
) -> Any:
    if not isinstance(template, tuple):
        return template

    if template and template[0] == "unquote":
        if len(template) != 2:
            raise LanguageError(
                f"{function_entity.value}: unquote takes exactly one operand"
            )

        return _eval(
            context,
            function_entity,
            links_relation,
            bindings,
            template[1],
        )

    return tuple(
        _quote(
            context,
            function_entity,
            links_relation,
            bindings,
            item,
        )
        for item in template
    )


def _function(
    context: _RunContext,
    function_entity: EntityID,
    links_relation: Relation | None,
    bindings: dict[str, Any],
    rest: tuple[Any, ...],
) -> Function:
    _arity(function_entity, "function", rest, 2)

    params = _eval(
        context,
        function_entity,
        links_relation,
        bindings,
        rest[0],
    )
    body = _eval(
        context,
        function_entity,
        links_relation,
        bindings,
        rest[1],
    )

    params = _decode(params)
    body = _decode(body)

    if not isinstance(params, tuple):
        raise LanguageError(
            f"{function_entity.value}: function parameters must be a tuple"
        )

    if not isinstance(body, tuple):
        raise LanguageError(
            f"{function_entity.value}: function body must be a tuple"
        )

    try:
        return Function(params, body)
    except (TypeError, ValueError) as exc:
        raise LanguageError(str(exc)) from exc


def _activation_pairs(
    context: _RunContext,
    function_entity: EntityID,
    links_relation: Relation | None,
    bindings: dict[str, Any],
    pairs: tuple[Any, ...],
    op: str,
    *,
    require_pairs: bool = True,
) -> tuple[State, dict[EntityID, Function]]:
    """Evaluate and check ``activate``/``trial``'s link/value pairs.

    Shared by ``activate`` (metaprogramming.md section 4) and ``trial``
    (language_trials.md section 2, whose pairs "are checked as for
    activate"). Evaluates the value expressions first, then reads the
    active state and resolves and checks every pair against it: each link
    resolves through the running function's links to an entity whose value
    in that state is a function, no entity is named twice, and each value
    is a function. Reading the active state only after evaluation matters
    because evaluating a value expression can itself activate
    (language_trials.md section 8).
    """

    if len(pairs) % 2 or (require_pairs and not pairs):
        raise LanguageError(
            f"{function_entity.value}: {op} needs link/value pairs"
        )

    evaluated_values = [
        _eval(
            context,
            function_entity,
            links_relation,
            bindings,
            pairs[index],
        )
        for index in range(1, len(pairs), 2)
    ]

    state = context.runtime.active.state
    targets: list[EntityID] = []

    for index in range(0, len(pairs), 2):
        link_name = pairs[index]
        target = _resolve_link(
            function_entity,
            links_relation,
            link_name,
        )

        if target in targets:
            raise LanguageError(
                f"{function_entity.value}: {op} target appears twice: "
                f"{target.value}"
            )

        if target not in state.values:
            raise LanguageError(
                f"{function_entity.value}: {op} target does not exist: "
                f"{target.value}"
            )

        if function_of(state.values[target]) is None:
            raise LanguageError(
                f"{function_entity.value}: {op} target is not a function: "
                f"{target.value}"
            )

        targets.append(target)

    functions: list[Function] = []

    for value in evaluated_values:
        function = _function_value(value)

        if function is None:
            raise LanguageError(
                f"{function_entity.value}: {op} value is not a function"
            )

        functions.append(function)

    return state, dict(zip(targets, functions))


def _activate(
    context: _RunContext,
    function_entity: EntityID,
    links_relation: Relation | None,
    bindings: dict[str, Any],
    rest: tuple[Any, ...],
) -> None:
    state, changes = _activation_pairs(
        context,
        function_entity,
        links_relation,
        bindings,
        rest,
        "activate",
    )

    if not context.may_activate:
        raise ActivationRejected("activation capability not granted")

    mappings = {
        entity: (entity,)
        for entity in state.values
    }

    result = transform_with_mapping(
        state,
        changes=changes,
        entity_mappings=mappings,
    )

    context.runtime.activate(result)
    return None


def _trial(
    context: _RunContext,
    function_entity: EntityID,
    links_relation: Relation | None,
    bindings: dict[str, Any],
    rest: tuple[Any, ...],
) -> Any:
    """Exercise a candidate in an isolated runtime (language_trials.md).

    The first operand names the call to make against the candidate; the
    rest are link/value pairs checked exactly as ``activate``'s
    (:func:`_activation_pairs`). The call's arguments are evaluated first,
    then the pairs' values, both in the running function's scope and the
    real runtime; only once that is done is the active state read to build
    the transformation and hand it to ``Runtime.trial``. The linked
    function then runs in the isolated runtime, without the activation
    capability, and its result is returned; the real runtime is never
    touched.
    """

    if not rest:
        raise LanguageError(
            f"{function_entity.value}: trial needs a call form"
        )

    call_form, *pairs = rest
    pairs = tuple(pairs)

    if (
        not isinstance(call_form, tuple)
        or len(call_form) < 2
        or call_form[0] != "call"
    ):
        raise LanguageError(
            f"{function_entity.value}: trial's first operand must be a "
            f"call form"
        )

    _, link_name, *arg_exprs = call_form

    args = tuple(
        _eval(
            context,
            function_entity,
            links_relation,
            bindings,
            expr,
        )
        for expr in arg_exprs
    )

    state, changes = _activation_pairs(
        context,
        function_entity,
        links_relation,
        bindings,
        pairs,
        "trial",
        require_pairs=False,
    )

    call_target = _resolve_link(
        function_entity,
        links_relation,
        link_name,
    )

    if not context.may_activate:
        raise ActivationRejected("activation capability not granted")

    mappings = {
        entity: (entity,)
        for entity in state.values
    }

    result = transform_with_mapping(
        state,
        changes=changes,
        entity_mappings=mappings,
    )

    candidate = context.runtime.trial(result)
    candidate_context = _RunContext(runtime=candidate, may_activate=False)

    return _call(candidate_context, call_target, args)


def _eval(
    context: _RunContext,
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
            context,
            function_entity,
            links_relation,
            bindings,
            rest[0],
            op,
        )
        right = _eval_int(
            context,
            function_entity,
            links_relation,
            bindings,
            rest[1],
            op,
        )

        if op == "add":
            return left + right

        if op == "sub":
            return left - right

        return left * right

    if op == "lt":
        _arity(function_entity, op, rest, 2)
        left = _eval_int(
            context,
            function_entity,
            links_relation,
            bindings,
            rest[0],
            op,
        )
        right = _eval_int(
            context,
            function_entity,
            links_relation,
            bindings,
            rest[1],
            op,
        )

        return left < right

    if op == "eq":
        _arity(function_entity, op, rest, 2)
        left = _eval(
            context,
            function_entity,
            links_relation,
            bindings,
            rest[0],
        )
        right = _eval(
            context,
            function_entity,
            links_relation,
            bindings,
            rest[1],
        )

        return _semantically_equal(left, right)

    if op == "if":
        _arity(function_entity, op, rest, 3)
        condition = _eval(
            context,
            function_entity,
            links_relation,
            bindings,
            rest[0],
        )

        if not isinstance(condition, bool):
            raise LanguageError(
                f"{function_entity.value}: if condition must be bool"
            )

        branch = rest[1] if condition else rest[2]

        return _eval(
            context,
            function_entity,
            links_relation,
            bindings,
            branch,
        )

    if op == "seq":
        if not rest:
            raise LanguageError(
                f"{function_entity.value}: seq needs at least one expression"
            )

        result: Any = None

        for expr in rest:
            result = _eval(
                context,
                function_entity,
                links_relation,
                bindings,
                expr,
            )

        return result

    if op == "call":
        if not rest:
            raise LanguageError(f"{function_entity.value}: call needs a link")

        link_name, *arg_exprs = rest
        target = _resolve_link(
            function_entity,
            links_relation,
            link_name,
        )
        args = tuple(
            _eval(
                context,
                function_entity,
                links_relation,
                bindings,
                expr,
            )
            for expr in arg_exprs
        )

        return _call(context, target, args)

    if op == "read":
        _arity(function_entity, op, rest, 1)
        cell = _resolve_link(
            function_entity,
            links_relation,
            rest[0],
        )

        # CellError means the link names something that is not a cell: a
        # language mistake (section 3), not a constraint rejection, so it
        # becomes a LanguageError. CellContentRejected and
        # RelationConstraintRejected are constraint failures and are left to
        # propagate unchanged.
        try:
            return context.runtime.read(cell)
        except CellError as exc:
            raise LanguageError(str(exc)) from exc

    if op == "write":
        _arity(function_entity, op, rest, 2)
        cell = _resolve_link(
            function_entity,
            links_relation,
            rest[0],
        )
        value = _eval(
            context,
            function_entity,
            links_relation,
            bindings,
            rest[1],
        )

        # Same distinction as "read" above.
        try:
            context.runtime.write(cell, value)
        except CellError as exc:
            raise LanguageError(str(exc)) from exc

        return value

    if op == "quote":
        _arity(function_entity, op, rest, 1)

        return _quote(
            context,
            function_entity,
            links_relation,
            bindings,
            rest[0],
        )

    if op == "function":
        return _function(
            context,
            function_entity,
            links_relation,
            bindings,
            tuple(rest),
        )

    if op == "activate":
        _activate(
            context,
            function_entity,
            links_relation,
            bindings,
            tuple(rest),
        )
        return None

    if op == "trial":
        return _trial(
            context,
            function_entity,
            links_relation,
            bindings,
            tuple(rest),
        )

    raise LanguageError(
        f"{function_entity.value}: unknown operation {op!r}"
    )


def _call(
    context: _RunContext,
    function_entity: EntityID,
    args: tuple[Any, ...],
) -> Any:
    """Call a function entity with already-evaluated arguments."""

    runtime = context.runtime
    frame = runtime.enter(function_entity)

    try:
        state = frame.version.state
        function = function_of(state.values[function_entity])

        if function is None:
            raise LanguageError(
                f"{function_entity.value} is not a function"
            )

        if len(args) != len(function.params):
            raise LanguageError(
                f"{function_entity.value} takes {len(function.params)} "
                f"argument(s), got {len(args)}"
            )

        bindings = dict(zip(function.params, args))
        links_relation = _links_of(state, function_entity)

        return _eval(
            context,
            function_entity,
            links_relation,
            bindings,
            function.body,
        )
    finally:
        frame.release()


def run(
    runtime: Runtime,
    entry: EntityID,
    *args: Any,
    may_activate: bool = False,
) -> Any:
    """Evaluate ``entry`` and return its result.

    Arguments are canonicalized before being bound to the entry function's
    parameters. Every call enters and releases a frame, so a finished run
    leaves no holds; a run that raises releases its frames too.

    By default a run cannot activate a new program state. Passing
    ``may_activate=True`` grants the run the provisional activation
    capability described in metaprogramming.md section 4.
    """

    context = _RunContext(
        runtime=runtime,
        may_activate=may_activate,
    )

    return _call(
        context,
        entry,
        tuple(canonicalize(arg) for arg in args),
    )
