"""Spike: code as a semantic graph (docs/spikes/code_as_graph.md).

``semiroh/lang.py`` stops at the function boundary: a ``Function`` entity
holds an opaque tuple tree, so identity, continuity, relations and
ownership do not reach into a function's body. This module tests the
alternative: every expression node is its own entity.

A node is an entity whose value is a :class:`~semiroh.relations.Relation`:
the ``kind`` is the operation, and every operand that is itself code is an
entity referenced through a role (never a raw ``EntityID`` embedded in
ordinary data). A literal or a parameter name, which is not code, is the
relation's ``payload``. Every node also carries a ``self`` role pointing at
itself, which is the cheapest way to satisfy the core rule that a relation
needs at least one role even for a leaf node with no operand entities
(``lit``, ``arg``).

A function entity's own value is a ``function_decl`` relation: ``payload``
is the parameter tuple, and role ``body`` names the root node entity. A
function owns every node of its body directly (a flat ownership set, not a
tree shaped like the expression), so removing a function removes its nodes
in one step and installing new code is placing new entities under the same
owner (ownership_model.md §13).

Calls, reads and writes reference their target directly through a role
(``call``'s ``target``, ``read``/``write``'s ``cell``) instead of through
the link-name indirection ``semiroh/lang.py`` needs because raw
``EntityID``\\ s embedded in an ordinary tuple body are untracked data
(relation_model.md §4). A role is a tracked reference: renaming the target
of a role is an ordinary continuity mapping, and every relation that
mentions the renamed entity is rewritten for free by
``TransformationDefinition`` (relation_model.md §5). ``lang.py``'s
``links`` relation exists only to give a tracked path from a tuple body to
another entity; once the body itself is entities-with-roles, nothing here
uses ``links``, and :func:`convert_program` drops it.

Quotation stays close to ``lang.py``: ``quote``'s operand is a normal
subgraph (built the same way as any other expression, so ``unquote`` nodes
sit inside it like any other node) and evaluating it walks that subgraph,
substituting each ``unquote`` hole with the result of evaluating its
(ordinary, graph) expression, and returns an ordinary portable tuple value
in ``lang.py``'s own tuple-tree shape (with ``call``/``read``/``write``
targets as raw ``EntityID``\\ s instead of link names, since that value is
inert data until it is installed). ``function`` builds such a value at run
time; ``activate`` takes one or more of those values and installs them as
fresh graph nodes, owned by the target function, discarding the function's
previous nodes.

Two extra, host-driven operations exist only as plain Python functions,
because the language itself does not create, remove or rename entities
(out of scope, like metaprogramming.md section 1): :func:`install_function`
and :func:`remove_function` place a function's nodes under it and remove
them again, and :func:`rename_function` and :func:`edit_node` show that a
rename or a single-node edit needs nothing beyond the core transformation
machinery.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .canonical import CanonicalNode, canonicalize
from .cells import cells_of
from .identity import EntityID
from .lang import Function as TupleFunction
from .lang import (
    FUNCTION_ROLE,
    LINKS_KIND,
    LanguageError,
    _decode,
    _links_of,
    _resolve_link,
    function_of as tuple_function_of,
)
from .ownership import follow_ownership
from .relations import Relation, relation_of
from .runtime import ActivationRejected, CellError, Runtime
from .state import State
from .transforms import TransformResult, transform_with_mapping

Resolver = Callable[[Any], EntityID]


# ---------------------------------------------------------------------------
# Node construction
# ---------------------------------------------------------------------------

# Node entity ids only need to be fresh, never equal to any existing entity
# (identity is conceptual, not derived from content or position, per
# identity_model.md). A single process-wide counter guarantees that,
# including across repeated installs into the same function, where a
# per-call counter would repeat "n0", "n1", ... and collide with the very
# nodes being replaced.
_NODE_SERIAL: "itertools.count[int]" = itertools.count()


def _mk(kind: str, self_id: EntityID, *, payload: Any = None, **roles: Any) -> Relation:
    return Relation(kind, {"self": self_id, **roles}, payload)


def _check_arity(op: str, rest: tuple[Any, ...], expected: int) -> None:
    if len(rest) != expected:
        raise LanguageError(
            f"{op} takes {expected} operand(s), got {len(rest)}"
        )


def _target_entity(spec: Any, resolve: Resolver | None) -> EntityID:
    if isinstance(spec, EntityID):
        return spec

    if resolve is None or not isinstance(spec, str):
        raise LanguageError(f"not a valid target: {spec!r}")

    return resolve(spec)


def _build_nodes(
    function_entity: EntityID,
    body: Any,
    resolve: Resolver | None,
    values: dict[EntityID, Any],
    serial: "itertools.count[int]",
) -> EntityID:
    """Recursively convert one portable tuple expression into graph nodes.

    Every new node gets a fresh entity, appended into ``values``. Returns
    the root node's entity. ``resolve`` turns a link-name operand (used only
    by the one-time conversion from ``lang.py`` bodies) into a target
    entity; generated code already carries direct ``EntityID`` targets and
    needs no resolver. The same recursion builds ``quote`` templates: an
    ``unquote`` inside one is just another node kind, not a special mode.
    """

    if not isinstance(body, tuple) or not body or not isinstance(body[0], str):
        raise LanguageError(f"not a valid expression: {body!r}")

    op, *rest = body
    node_id = EntityID(f"{function_entity.value}/n{next(serial)}")

    if op == "lit":
        _check_arity(op, rest, 1)
        values[node_id] = _mk("lit", node_id, payload=rest[0])
        return node_id

    if op == "arg":
        _check_arity(op, rest, 1)
        name = rest[0]

        if not isinstance(name, str) or not name:
            raise LanguageError("arg name must be a non-empty string")

        values[node_id] = _mk("arg", node_id, payload=name)
        return node_id

    if op in ("add", "sub", "mul", "lt", "eq"):
        _check_arity(op, rest, 2)
        left = _build_nodes(function_entity, rest[0], resolve, values, serial)
        right = _build_nodes(function_entity, rest[1], resolve, values, serial)
        values[node_id] = _mk(op, node_id, left=left, right=right)
        return node_id

    if op == "if":
        _check_arity(op, rest, 3)
        cond = _build_nodes(function_entity, rest[0], resolve, values, serial)
        then_ = _build_nodes(function_entity, rest[1], resolve, values, serial)
        else_ = _build_nodes(function_entity, rest[2], resolve, values, serial)
        values[node_id] = _mk(
            "if", node_id, cond=cond, then=then_, **{"else": else_}
        )
        return node_id

    if op == "seq":
        if not rest:
            raise LanguageError("seq needs at least one expression")

        items = tuple(
            _build_nodes(function_entity, item, resolve, values, serial)
            for item in rest
        )
        values[node_id] = _mk("seq", node_id, items=items)
        return node_id

    if op == "call":
        if not rest:
            raise LanguageError("call needs a target")

        target = _target_entity(rest[0], resolve)
        args = tuple(
            _build_nodes(function_entity, expr, resolve, values, serial)
            for expr in rest[1:]
        )
        values[node_id] = _mk("call", node_id, target=target, args=args)
        return node_id

    if op == "read":
        _check_arity(op, rest, 1)
        cell = _target_entity(rest[0], resolve)
        values[node_id] = _mk("read", node_id, cell=cell)
        return node_id

    if op == "write":
        _check_arity(op, rest, 2)
        cell = _target_entity(rest[0], resolve)
        value_node = _build_nodes(function_entity, rest[1], resolve, values, serial)
        values[node_id] = _mk("write", node_id, cell=cell, value=value_node)
        return node_id

    if op == "quote":
        _check_arity(op, rest, 1)
        template = _build_nodes(function_entity, rest[0], resolve, values, serial)
        values[node_id] = _mk("quote", node_id, template=template)
        return node_id

    if op == "unquote":
        _check_arity(op, rest, 1)
        expr = _build_nodes(function_entity, rest[0], resolve, values, serial)
        values[node_id] = _mk("unquote", node_id, expr=expr)
        return node_id

    if op == "function":
        _check_arity(op, rest, 2)
        params = _build_nodes(function_entity, rest[0], resolve, values, serial)
        fbody = _build_nodes(function_entity, rest[1], resolve, values, serial)
        values[node_id] = _mk("function", node_id, params=params, body=fbody)
        return node_id

    if op == "activate":
        if not rest or len(rest) % 2:
            raise LanguageError("activate needs target/value pairs")

        targets = tuple(
            _target_entity(rest[index], resolve)
            for index in range(0, len(rest), 2)
        )
        value_nodes = tuple(
            _build_nodes(function_entity, rest[index], resolve, values, serial)
            for index in range(1, len(rest), 2)
        )
        values[node_id] = _mk(
            "activate", node_id, targets=targets, values=value_nodes
        )
        return node_id

    raise LanguageError(f"unknown operation {op!r}")


# ---------------------------------------------------------------------------
# Function declarations
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Decl:
    params: tuple[str, ...]
    body: EntityID


def _function_decl_of(state: State, entity: EntityID) -> _Decl | None:
    value = state.values.get(entity)

    if value is None:
        return None

    rel = relation_of(value)

    if rel is None or rel.kind != "function_decl":
        return None

    return _Decl(tuple(_decode(rel.payload)), rel.roles["body"])


def _decl_relation(entity: EntityID, params: tuple[str, ...], body: EntityID) -> Relation:
    return _mk("function_decl", entity, payload=tuple(params), body=body)


# ---------------------------------------------------------------------------
# Host-driven graph edits
# ---------------------------------------------------------------------------


def _cell_identity_mappings(state: State) -> dict[EntityID, tuple[EntityID, ...]]:
    return {cell: (cell,) for cell in cells_of(state)}


def install_function(
    state: State,
    function_entity: EntityID,
    params: tuple[str, ...],
    body: tuple,
    *,
    resolve_link: Resolver | None = None,
) -> TransformResult:
    """Host-driven: add a new function entity, owned by its fresh nodes.

    ``function_entity`` must not already exist. This is the host side of
    program modification (first_program.md-style): it produces a
    transformation result; the caller activates it.
    """

    if function_entity in state.values:
        raise ValueError(f"{function_entity.value} already exists")

    node_values: dict[EntityID, Any] = {}
    serial = _NODE_SERIAL
    body_root = _build_nodes(function_entity, body, resolve_link, node_values, serial)

    changes: dict[EntityID, Any] = dict(node_values)
    changes[function_entity] = _decl_relation(function_entity, params, body_root)

    ownership = {owner: list(children) for owner, children in state.ownership.items()}
    ownership[function_entity] = sorted(node_values, key=lambda e: e.value)

    return transform_with_mapping(
        state,
        changes=changes,
        entity_mappings=_cell_identity_mappings(state),
        ownership=ownership,
    )


def remove_function(state: State, function_entity: EntityID) -> State:
    """Host-driven: destroy a function and its owned nodes; no orphans.

    Recursive destruction (ownership_model.md §6) already does exactly
    this; a function's nodes need no special-casing. Fails with
    ``DanglingRelation`` if another entity still calls it.
    """

    return state.destroy(function_entity)


def rename_function(
    state: State,
    old_entity: EntityID,
    new_entity: EntityID,
) -> TransformResult:
    """Host-driven rename: ``new_entity`` continues ``old_entity``.

    The function's nodes keep their own entities and simply change owner,
    following continuity (ownership_model.md §8). Every node elsewhere
    whose ``call``/``read``/``write`` role names ``old_entity`` is rewritten
    to ``new_entity`` by the core transformation machinery
    (relation_model.md §5): no link table to update, because the reference
    was a role, not a name.
    """

    if new_entity in state.values:
        raise ValueError(f"{new_entity.value} already exists")

    old_value = state.values[old_entity]
    old_rel = relation_of(old_value)
    # The copied content's own ``self`` role still names old_entity; rewrite
    # it like any other endpoint, or the destination state would carry a
    # relation pointing at an entity that no longer exists.
    new_content = (
        old_rel.with_endpoints({old_entity: new_entity})
        if old_rel is not None
        else old_value.content
    )
    mappings: dict[EntityID, tuple[EntityID, ...]] = {old_entity: (new_entity,)}
    mappings.update(_cell_identity_mappings(state))

    return transform_with_mapping(
        state,
        changes={new_entity: new_content},
        entity_mappings=mappings,
    )


def edit_node(
    state: State,
    node_entity: EntityID,
    *,
    kind: str | None = None,
    payload: Any = None,
    roles: Mapping[str, Any] | None = None,
) -> TransformResult:
    """Host-driven: replace one node's content; nothing else moves.

    Every entity not named here keeps both its ``EntityID`` and its
    ``VersionID``: the transformation's only change is this node, so the
    edit is exactly as local as the piece of code it touches.
    """

    current = relation_of(state.values[node_entity])

    if current is None:
        raise ValueError(f"{node_entity.value} is not a code node")

    new_relation = Relation(
        kind if kind is not None else current.kind,
        {**current.roles, **(roles or {})},
        current.payload if payload is None else payload,
    )

    return transform_with_mapping(
        state,
        changes={node_entity: new_relation},
        entity_mappings=_cell_identity_mappings(state),
    )


# ---------------------------------------------------------------------------
# Conversion from lang.py
# ---------------------------------------------------------------------------


def convert_program(state: State) -> State:
    """Convert every ``lang.py``-style ``Function`` entity into graph form.

    Cells and any other entity are left untouched. Each function's body is
    rebuilt as owned graph nodes, its link names resolved through its
    existing ``links`` relation (reusing ``lang.py``'s own resolution) into
    direct role references. The ``links`` relations themselves are dropped:
    nothing in the graph form reads them.
    """

    to_convert: dict[EntityID, tuple[TupleFunction, Relation | None]] = {}

    for entity, value in state.values.items():
        func = tuple_function_of(value)

        if func is not None:
            to_convert[entity] = (func, _links_of(state, entity))

    changes: dict[EntityID, Any] = {}
    ownership = {owner: list(children) for owner, children in state.ownership.items()}

    for entity, (func, links_rel) in to_convert.items():
        def resolve(name: Any, _entity: EntityID = entity, _links: Relation | None = links_rel) -> EntityID:
            return _resolve_link(_entity, _links, name)

        node_values: dict[EntityID, Any] = {}
        serial = _NODE_SERIAL
        body_root = _build_nodes(entity, func.body, resolve, node_values, serial)

        changes.update(node_values)
        changes[entity] = _decl_relation(entity, func.params, body_root)
        ownership[entity] = sorted(node_values, key=lambda e: e.value)

    mappings: dict[EntityID, tuple[EntityID, ...]] = {}

    for candidate, value in state.values.items():
        rel = relation_of(value)

        if (
            rel is not None
            and rel.kind == LINKS_KIND
            and rel.roles.get(FUNCTION_ROLE) in to_convert
        ):
            mappings[candidate] = ()

    mappings.update(_cell_identity_mappings(state))

    return transform_with_mapping(
        state,
        changes=changes,
        entity_mappings=mappings,
        ownership=ownership,
    ).destination


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _semantically_equal(left: Any, right: Any) -> bool:
    from .canonical import canonical_serialize

    return canonical_serialize(canonicalize(left)) == canonical_serialize(
        canonicalize(right)
    )


@dataclass(frozen=True)
class _RunContext:
    runtime: Runtime
    may_activate: bool


def _node_relation(state: State, function_entity: EntityID, node_entity: EntityID) -> Relation:
    value = state.values.get(node_entity)

    if value is None:
        raise LanguageError(
            f"{function_entity.value}: node {node_entity.value} does not exist"
        )

    rel = relation_of(value)

    if rel is None:
        raise LanguageError(f"{node_entity.value} is not a code node")

    return rel


def _eval_int(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    node_entity: EntityID,
    op: str,
) -> int:
    value = _eval_node(context, state, function_entity, bindings, node_entity)

    if not _is_int(value):
        raise LanguageError(f"{function_entity.value}: {op} operands must be int")

    return value


def _quote_node(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    node_entity: EntityID,
) -> Any:
    rel = _node_relation(state, function_entity, node_entity)
    op = rel.kind

    if op == "unquote":
        return _eval_node(context, state, function_entity, bindings, rel.roles["expr"])

    if op == "lit":
        return ("lit", _decode(rel.payload))

    if op == "arg":
        return ("arg", _decode(rel.payload))

    if op in ("add", "sub", "mul", "lt", "eq"):
        return (
            op,
            _quote_node(context, state, function_entity, bindings, rel.roles["left"]),
            _quote_node(context, state, function_entity, bindings, rel.roles["right"]),
        )

    if op == "if":
        return (
            "if",
            _quote_node(context, state, function_entity, bindings, rel.roles["cond"]),
            _quote_node(context, state, function_entity, bindings, rel.roles["then"]),
            _quote_node(context, state, function_entity, bindings, rel.roles["else"]),
        )

    if op == "seq":
        return ("seq",) + tuple(
            _quote_node(context, state, function_entity, bindings, item)
            for item in rel.roles["items"]
        )

    if op == "call":
        return ("call", rel.roles["target"]) + tuple(
            _quote_node(context, state, function_entity, bindings, item)
            for item in rel.roles.get("args", ())
        )

    if op == "read":
        return ("read", rel.roles["cell"])

    if op == "write":
        return (
            "write",
            rel.roles["cell"],
            _quote_node(context, state, function_entity, bindings, rel.roles["value"]),
        )

    if op == "function":
        return (
            "function",
            _quote_node(context, state, function_entity, bindings, rel.roles["params"]),
            _quote_node(context, state, function_entity, bindings, rel.roles["body"]),
        )

    if op == "activate":
        parts: list[Any] = ["activate"]

        for target, value_node in zip(rel.roles["targets"], rel.roles["values"]):
            parts.append(target)
            parts.append(
                _quote_node(context, state, function_entity, bindings, value_node)
            )

        return tuple(parts)

    raise LanguageError(
        f"{function_entity.value}: cannot quote node kind {op!r} (nested quote "
        f"is not supported)"
    )


def _function_node(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    rel: Relation,
) -> TupleFunction:
    params = _decode(
        _eval_node(context, state, function_entity, bindings, rel.roles["params"])
    )
    fbody = _decode(
        _eval_node(context, state, function_entity, bindings, rel.roles["body"])
    )

    if not isinstance(params, tuple):
        raise LanguageError(
            f"{function_entity.value}: function parameters must be a tuple"
        )

    if not isinstance(fbody, tuple):
        raise LanguageError(f"{function_entity.value}: function body must be a tuple")

    try:
        return TupleFunction(params, fbody)
    except (TypeError, ValueError) as exc:
        raise LanguageError(str(exc)) from exc


def _install(state: State, replacements: Mapping[EntityID, TupleFunction]) -> TransformResult:
    changes: dict[EntityID, Any] = {}
    mappings: dict[EntityID, tuple[EntityID, ...]] = {}
    new_owned: dict[EntityID, tuple[EntityID, ...]] = {}

    for target, candidate in replacements.items():
        for child in state.owned_children(target):
            mappings[child] = ()

        node_values: dict[EntityID, Any] = {}
        serial = _NODE_SERIAL
        body_root = _build_nodes(target, candidate.body, None, node_values, serial)

        changes.update(node_values)
        changes[target] = _decl_relation(target, candidate.params, body_root)
        new_owned[target] = tuple(sorted(node_values, key=lambda e: e.value))

    mappings.update(_cell_identity_mappings(state))

    ownership = follow_ownership(state.ownership, mappings)

    for target, node_ids in new_owned.items():
        ownership[target] = list(node_ids)

    return transform_with_mapping(
        state,
        changes=changes,
        entity_mappings=mappings,
        ownership=ownership,
    )


def _activate_node(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    rel: Relation,
) -> None:
    target_specs = rel.roles.get("targets", ())
    value_specs = rel.roles.get("values", ())

    if not target_specs or len(target_specs) != len(value_specs):
        raise LanguageError(f"{function_entity.value}: activate needs target/value pairs")

    evaluated = [
        _eval_node(context, state, function_entity, bindings, node_entity)
        for node_entity in value_specs
    ]

    targets: list[EntityID] = []

    for target in target_specs:
        if target in targets:
            raise LanguageError(
                f"{function_entity.value}: activation target appears twice: "
                f"{target.value}"
            )

        if target not in state.values:
            raise LanguageError(
                f"{function_entity.value}: activation target does not exist: "
                f"{target.value}"
            )

        if _function_decl_of(state, target) is None:
            raise LanguageError(
                f"{function_entity.value}: activation target is not a function: "
                f"{target.value}"
            )

        targets.append(target)

    candidates: list[TupleFunction] = []

    for value in evaluated:
        if not isinstance(value, TupleFunction):
            raise LanguageError(
                f"{function_entity.value}: activation value is not a function"
            )

        candidates.append(value)

    if not context.may_activate:
        raise ActivationRejected("activation capability not granted")

    result = _install(state, dict(zip(targets, candidates)))
    context.runtime.activate(result)


def _eval_node(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    node_entity: EntityID,
) -> Any:
    rel = _node_relation(state, function_entity, node_entity)
    op = rel.kind

    if op == "lit":
        return _decode(rel.payload)

    if op == "arg":
        name = _decode(rel.payload)

        if name not in bindings:
            raise LanguageError(f"{function_entity.value}: unknown parameter {name!r}")

        return bindings[name]

    if op in ("add", "sub", "mul"):
        left = _eval_int(context, state, function_entity, bindings, rel.roles["left"], op)
        right = _eval_int(context, state, function_entity, bindings, rel.roles["right"], op)

        if op == "add":
            return left + right

        if op == "sub":
            return left - right

        return left * right

    if op == "lt":
        left = _eval_int(context, state, function_entity, bindings, rel.roles["left"], op)
        right = _eval_int(context, state, function_entity, bindings, rel.roles["right"], op)
        return left < right

    if op == "eq":
        left = _eval_node(context, state, function_entity, bindings, rel.roles["left"])
        right = _eval_node(context, state, function_entity, bindings, rel.roles["right"])
        return _semantically_equal(left, right)

    if op == "if":
        condition = _eval_node(context, state, function_entity, bindings, rel.roles["cond"])

        if not isinstance(condition, bool):
            raise LanguageError(f"{function_entity.value}: if condition must be bool")

        branch = rel.roles["then"] if condition else rel.roles["else"]
        return _eval_node(context, state, function_entity, bindings, branch)

    if op == "seq":
        items = rel.roles.get("items", ())

        if not items:
            raise LanguageError(f"{function_entity.value}: seq needs at least one expression")

        result: Any = None

        for item in items:
            result = _eval_node(context, state, function_entity, bindings, item)

        return result

    if op == "call":
        target = rel.roles["target"]

        if not isinstance(target, EntityID):
            raise LanguageError(f"{function_entity.value}: call target must be an entity")

        args = tuple(
            _eval_node(context, state, function_entity, bindings, expr)
            for expr in rel.roles.get("args", ())
        )
        return _call_node(context, target, args)

    if op == "read":
        cell = rel.roles["cell"]

        try:
            return context.runtime.read(cell)
        except CellError as exc:
            raise LanguageError(str(exc)) from exc

    if op == "write":
        cell = rel.roles["cell"]
        value = _eval_node(context, state, function_entity, bindings, rel.roles["value"])

        try:
            context.runtime.write(cell, value)
        except CellError as exc:
            raise LanguageError(str(exc)) from exc

        return value

    if op == "quote":
        return _quote_node(context, state, function_entity, bindings, rel.roles["template"])

    if op == "unquote":
        raise LanguageError(f"{function_entity.value}: unquote outside quote")

    if op == "function":
        return _function_node(context, state, function_entity, bindings, rel)

    if op == "activate":
        _activate_node(context, state, function_entity, bindings, rel)
        return None

    raise LanguageError(f"{function_entity.value}: unknown operation {op!r}")


def _call_node(
    context: _RunContext,
    function_entity: EntityID,
    args: tuple[Any, ...],
) -> Any:
    runtime = context.runtime
    frame = runtime.enter(function_entity)

    try:
        state = frame.version.state
        decl = _function_decl_of(state, function_entity)

        if decl is None:
            raise LanguageError(f"{function_entity.value} is not a function")

        if len(args) != len(decl.params):
            raise LanguageError(
                f"{function_entity.value} takes {len(decl.params)} argument(s), "
                f"got {len(args)}"
            )

        bindings = dict(zip(decl.params, args))
        return _eval_node(context, state, function_entity, bindings, decl.body)
    finally:
        frame.release()


def run_node(
    runtime: Runtime,
    entry: EntityID,
    *args: Any,
    may_activate: bool = False,
) -> Any:
    """Evaluate ``entry`` over graph-form code and return its result.

    Mirrors ``lang.run``: every call holds and releases a frame, cell
    access goes through the runtime, and a run cannot activate a new
    program state unless ``may_activate`` is granted.
    """

    context = _RunContext(runtime=runtime, may_activate=may_activate)
    return _call_node(context, entry, tuple(canonicalize(arg) for arg in args))
