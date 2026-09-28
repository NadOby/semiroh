"""A tiny language whose code lives in the semantic graph (graph_form.md).

Programs are written in the **input format** (first_program.md): a
**function** is an entity whose value is a :class:`Function`, parameter
names plus a body expression tree of plain tuples, and it names the
functions and cells it uses through link names, resolved via its own
**links relation** (:func:`links`).

:func:`load` turns a program into **graph form**, the only form that runs.
Every expression node is a relation entity owned by its function; the
function entity's value is a ``definition`` relation holding its
parameters, the root node of its body and its link table. Calls, reads and
writes name their targets through relation roles, so a rename follows
continuity in the core. :func:`function_at` collapses a function back to
the input format, and :func:`define` replaces whole bodies.

Code as data stays in the input format: ``quote`` builds tuples,
``function`` builds :class:`Function` values, and ``activate`` and
``trial`` install them the way :func:`define` does. Running a function can
change program state only through ``activate``, and only when the run was
granted the activation capability.

This module is a layer on top of the core model, not part of it: it is not
re-exported from ``semiroh/__init__.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .canonical import (
    CanonicalNode,
    SemanticRecord,
    _node,
    canonical_serialize,
    canonicalize,
)
from .identity import EntityID
from .relations import Endpoint, Relation, relation_index, relation_of
from .runtime import ActivationRejected, CellError, Runtime
from .state import State
from .transforms import TransformResult, transform_with_mapping
from .values import Value

# The role a function plays in its own links relation; reserved as a link
# name (first_program.md section 2).
FUNCTION_ROLE = "function"
LINKS_KIND = "links"

# Graph form (graph_form.md section 2): a function entity's value is a
# definition relation; its body root is the "body" role and each link of
# its link table is a "link:<name>" role.
DEFINITION_KIND = "definition"
BODY_ROLE = "body"
LINK_ROLE_PREFIX = "link:"
INVALID_KIND = "invalid"

_BINARY = ("add", "sub", "mul", "lt", "eq")

# Operations with a fixed number of operands.
_ARITY = {
    "lit": 1,
    "arg": 1,
    **dict.fromkeys(_BINARY, 2),
    "if": 3,
    "read": 1,
    "write": 2,
    "quote": 1,
    "function": 2,
}

NODE_KINDS = frozenset({
    "lit",
    "arg",
    *_BINARY,
    "if",
    "seq",
    "call",
    "read",
    "write",
    "quote",
    "unquote",
    "function",
    "activate",
    "trial",
    INVALID_KIND,
})

# What a quote node's template holds in place of each hole; every hole of
# the source template is a tuple headed "unquote", so nothing else is.
_HOLE = ("unquote",)


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

    A ``Function`` is the input format and the form of code as data; a
    loaded program holds its functions in graph form instead
    (graph_form.md).
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
    """Return the Function held by a value, or None if it does not hold one.

    This reads the input format (and function values used as data, such as
    a cell's content); a function of a loaded program is read with
    :func:`function_at`.
    """

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


def _links_of(
    state: State,
    function: EntityID,
    index: Mapping[EntityID, tuple[tuple[EntityID, str], ...]] | None = None,
) -> tuple[EntityID, Relation] | None:
    """Return the links relation entity and record of a function, if any.

    ``index`` is ``relation_index(state)``, passed in by a caller that looks
    up many functions.
    """

    found: list[tuple[EntityID, Relation]] = []

    if index is None:
        index = relation_index(state)

    for relation_entity, role in index.get(function, ()):
        if role != FUNCTION_ROLE:
            continue

        relation = relation_of(state.values[relation_entity])

        if relation is not None and relation.kind == LINKS_KIND:
            found.append((relation_entity, relation))

    if len(found) > 1:
        raise LanguageError(
            f"{function.value} has more than one links relation"
        )

    return found[0] if found else None


# ---------------------------------------------------------------------------
# Graph form: definitions and nodes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Definition:
    """A function entity's value in graph form (graph_form.md section 2).

    ``links`` is the function's link table: the names its code may use,
    which new bodies are resolved against. ``generation`` counts the bodies
    the function has had, so the node entities of a new body never reuse
    the names of an earlier one.
    """

    params: tuple[str, ...]
    body: EntityID
    links: Mapping[str, Endpoint]
    generation: int

    def relation(self) -> Relation:
        roles: dict[str, Endpoint] = {BODY_ROLE: self.body}

        for name, target in self.links.items():
            roles[LINK_ROLE_PREFIX + name] = target

        return Relation(
            DEFINITION_KIND,
            roles,
            {"params": self.params, "generation": self.generation},
        )


def _definition_of(value: Value) -> _Definition | None:
    """Return the definition held by a value, or None if it holds none."""

    node = relation_of(value)

    if node is None or node.kind != DEFINITION_KIND:
        return None

    try:
        payload = _decode(node.payload)
        return _Definition(
            tuple(payload["params"]),
            node.roles[BODY_ROLE],
            {
                role[len(LINK_ROLE_PREFIX):]: endpoint
                for role, endpoint in node.roles.items()
                if role.startswith(LINK_ROLE_PREFIX)
            },
            payload["generation"],
        )
    except (KeyError, TypeError) as exc:
        raise LanguageError(
            f"{value.entity.value} holds a malformed definition"
        ) from exc


def _invalid(problem: str, expr: Any) -> Relation:
    return Relation(INVALID_KIND, {}, (problem, expr))


class _Builder:
    """Builds the graph form of one function body (graph_form.md section 3).

    Node entities are ``<function>/<generation>.<index>``, numbered in
    preorder, so the root is index 0. Building never fails: an expression
    the interpreter would reject becomes an ``invalid`` node that raises
    the same ``LanguageError`` when it runs, so code is still checked when
    it runs (metaprogramming.md section 3).
    """

    def __init__(
        self,
        function: EntityID,
        generation: int,
        scope: Mapping[str, Endpoint],
    ) -> None:
        self.function = function
        self.generation = generation
        self.scope = scope
        self.nodes: dict[EntityID, Relation] = {}
        self._count = 0

    def _allocate(self) -> EntityID:
        entity = EntityID(
            f"{self.function.value}/{self.generation}.{self._count}"
        )
        self._count += 1
        return entity

    def resolve(self, name: Any) -> tuple[EntityID | None, str | None]:
        """Resolve a link name through the function's link table."""

        if (
            not isinstance(name, str)
            or name == FUNCTION_ROLE
            or name not in self.scope
        ):
            return None, f"unknown link {name!r}"

        target = self.scope[name]

        if not isinstance(target, EntityID):
            return None, f"link {name!r} does not name a single entity"

        return target, None

    def links(
        self,
        names: tuple[Any, ...],
    ) -> tuple[tuple[EntityID, ...], tuple[tuple[Any, str | None], ...]]:
        """Resolve the link names of activate or trial pairs.

        Returns the resolved targets, in order, and one ``(name, problem)``
        entry per name; the problem is raised only when the pairs are
        checked, after their values are evaluated.
        """

        targets: list[EntityID] = []
        entries: list[tuple[Any, str | None]] = []

        for name in names:
            target, problem = self.resolve(name)

            if target is not None:
                targets.append(target)

            entries.append((name, problem))

        return tuple(targets), tuple(entries)

    def expr(self, expr: Any) -> EntityID:
        entity = self._allocate()
        self.nodes[entity] = self._relation(expr)
        return entity

    def exprs(self, exprs: tuple[Any, ...]) -> tuple[EntityID, ...]:
        return tuple(self.expr(item) for item in exprs)

    def template(self, template: Any, holes: list[EntityID]) -> Any:
        """Copy a quote template, replacing each hole with ``_HOLE``."""

        if not isinstance(template, tuple) or isinstance(template, CanonicalNode):
            return template

        if template and template[0] == "unquote":
            entity = self._allocate()

            if len(template) != 2:
                self.nodes[entity] = _invalid(
                    "unquote takes exactly one operand",
                    template,
                )
            else:
                self.nodes[entity] = Relation(
                    "unquote",
                    {"expr": self.expr(template[1])},
                )

            holes.append(entity)
            return _HOLE

        return tuple(self.template(item, holes) for item in template)

    def _relation(self, expr: Any) -> Relation:
        if not isinstance(expr, tuple) or not expr or not isinstance(expr[0], str):
            return _invalid(f"not a valid expression: {expr!r}", expr)

        op = expr[0]
        rest = expr[1:]

        if op in _ARITY and len(rest) != _ARITY[op]:
            return _invalid(
                f"{op} takes {_ARITY[op]} operand(s), got {len(rest)}",
                expr,
            )

        if op in ("lit", "arg"):
            return Relation(op, {}, rest[0])

        if op in _BINARY:
            return Relation(
                op,
                {"left": self.expr(rest[0]), "right": self.expr(rest[1])},
            )

        if op == "if":
            return Relation(
                "if",
                {
                    "cond": self.expr(rest[0]),
                    "then": self.expr(rest[1]),
                    "else": self.expr(rest[2]),
                },
            )

        if op == "seq":
            if not rest:
                return _invalid("seq needs at least one expression", expr)

            return Relation("seq", {"items": self.exprs(rest)})

        if op in ("call", "read", "write"):
            if not rest:
                return _invalid("call needs a link", expr)

            target, problem = self.resolve(rest[0])

            if problem is not None:
                return _invalid(problem, expr)

            if op == "call":
                return Relation(
                    "call",
                    {"target": target, "args": self.exprs(rest[1:])},
                    rest[0],
                )

            if op == "read":
                return Relation("read", {"cell": target}, rest[0])

            return Relation(
                "write",
                {"cell": target, "value": self.expr(rest[1])},
                rest[0],
            )

        if op == "quote":
            holes: list[EntityID] = []
            template = self.template(rest[0], holes)
            return Relation("quote", {"holes": tuple(holes)}, template)

        if op == "function":
            return Relation(
                "function",
                {"params": self.expr(rest[0]), "body": self.expr(rest[1])},
            )

        if op == "activate":
            if not rest or len(rest) % 2:
                return _invalid("activate needs link/value pairs", expr)

            values = self.exprs(rest[1::2])
            targets, entries = self.links(rest[0::2])

            return Relation(
                "activate",
                {"targets": targets, "values": values},
                {"links": entries},
            )

        if op == "trial":
            if not rest:
                return _invalid("trial needs a call form", expr)

            call_form = rest[0]

            if (
                not isinstance(call_form, tuple)
                or len(call_form) < 2
                or call_form[0] != "call"
            ):
                return _invalid(
                    "trial's first operand must be a call form",
                    expr,
                )

            pairs = rest[1:]
            roles: dict[str, Endpoint] = {"args": self.exprs(call_form[2:])}
            roles["values"] = self.exprs(pairs[1::2])
            roles["targets"], entries = self.links(pairs[0::2])
            target, problem = self.resolve(call_form[1])

            if target is not None:
                roles["target"] = target

            return Relation(
                "trial",
                roles,
                {"call": (call_form[1], problem), "links": entries},
            )

        return _invalid(f"unknown operation {op!r}", expr)


def _compile(
    entity: EntityID,
    function: Function,
    links_table: Mapping[str, Endpoint],
    generation: int,
    taken: set[EntityID],
) -> tuple[Relation, dict[EntityID, Relation]]:
    """Build a function's definition and nodes; node names avoid ``taken``.

    The first generation whose node names are all free is used, so the
    result depends only on the arguments.
    """

    while True:
        builder = _Builder(entity, generation, links_table)
        root = builder.expr(function.body)

        if taken.isdisjoint(builder.nodes):
            break

        generation += 1

    definition = _Definition(function.params, root, dict(links_table), generation)

    return definition.relation(), builder.nodes


def load(state: State) -> State:
    """Convert a program in the input format into graph form.

    Every entity holding a ``Function`` keeps its ``EntityID`` and holds a
    definition instead; its body becomes nodes it owns, and its links
    relation, which becomes its link table, disappears. Everything else is
    unchanged. The result depends only on ``state``.
    """

    functions = {
        entity: function
        for entity in sorted(state.values)
        if (function := function_of(state.values[entity])) is not None
    }

    if not functions:
        return state

    index = relation_index(state)
    changes: dict[EntityID, Any] = {}
    mappings: dict[EntityID, tuple[EntityID, ...]] = {}
    placements: dict[EntityID, EntityID] = {}
    taken = set(state.values)

    for entity, function in functions.items():
        if state.owned_children(entity):
            raise LanguageError(
                f"{entity.value} already owns entities; a function owns "
                f"only its nodes"
            )

        found = _links_of(state, entity, index)
        links_table: dict[str, Endpoint] = {}

        if found is not None:
            links_entity, links_relation = found
            mappings[links_entity] = ()
            links_table = {
                name: target
                for name, target in links_relation.roles.items()
                if name != FUNCTION_ROLE
            }

        definition, nodes = _compile(entity, function, links_table, 0, taken)
        taken.update(nodes)
        changes[entity] = definition
        changes.update(nodes)
        placements.update(dict.fromkeys(nodes, entity))

    return transform_with_mapping(
        state,
        changes,
        mappings,
        placements=placements,
    ).destination


def define(
    state: State,
    functions: Mapping[EntityID, Function],
) -> TransformResult:
    """Replace the whole bodies of functions in a graph-form state.

    Each new body's link names resolve through its function's link table.
    The function's old nodes disappear, its new nodes are placed under it,
    and every other entity is continuous with itself (graph_form.md
    section 6). The caller activates the result.
    """

    changes: dict[EntityID, Any] = {}
    mappings: dict[EntityID, Any] = {}
    placements: dict[EntityID, EntityID] = {}
    taken = set(state.values)

    for entity in sorted(functions):
        function = functions[entity]

        if not isinstance(function, Function):
            raise TypeError("define takes Function values")

        if entity not in state.values:
            raise LanguageError(f"{entity.value} does not exist")

        current = _definition_of(state.values[entity])

        if current is None:
            raise LanguageError(f"{entity.value} is not a function")

        definition, nodes = _compile(
            entity,
            function,
            current.links,
            current.generation + 1,
            taken,
        )
        taken.update(nodes)

        for old in state.owned_children(entity):
            mappings[old] = ()

        changes[entity] = definition
        changes.update(nodes)
        placements.update(dict.fromkeys(nodes, entity))

    for entity in state.values:
        mappings.setdefault(entity, entity)

    return transform_with_mapping(
        state,
        changes,
        mappings,
        placements=placements,
    )


def _node_at(
    state: State,
    function_entity: EntityID,
    entity: EntityID,
) -> Relation:
    """Return the node relation of ``entity``; its payload stays canonical.

    ``relation_of`` decodes a value once and keeps the record with it, so
    walking the same code again does not decode it again.
    """

    value = state.values.get(entity)
    node = None if value is None else relation_of(value)

    if node is None or node.kind not in NODE_KINDS:
        raise LanguageError(
            f"{function_entity.value}: {entity.value} is not a code node"
        )

    return node


def _pairs(names: tuple[Any, ...], values: tuple[Any, ...]) -> tuple[Any, ...]:
    """Interleave pair names and values; a trailing name stays unpaired."""

    items: list[Any] = []

    for index, name in enumerate(names):
        items.append(name)

        if index < len(values):
            items.append(values[index])

    return tuple(items)


def _fill(template: Any, holes: Any) -> Any:
    """Put each value of the ``holes`` iterator back in place of a hole."""

    if not isinstance(template, tuple) or isinstance(template, CanonicalNode):
        return template

    if template and template[0] == "unquote":
        return next(holes)

    return tuple(_fill(item, holes) for item in template)


def _collapse(state: State, function_entity: EntityID, entity: EntityID) -> Any:
    """Return the input-format expression of a node and its operands."""

    node = _node_at(state, function_entity, entity)
    kind = node.kind
    roles = node.roles

    def collapse(child: EntityID) -> Any:
        return _collapse(state, function_entity, child)

    def collapse_all(children: tuple[EntityID, ...]) -> tuple[Any, ...]:
        return tuple(collapse(child) for child in children)

    if kind == INVALID_KIND:
        return _decode(node.payload)[1]

    if kind in ("lit", "arg"):
        return (kind, _decode(node.payload))

    if kind in _BINARY:
        return (kind, collapse(roles["left"]), collapse(roles["right"]))

    if kind == "if":
        return (
            "if",
            collapse(roles["cond"]),
            collapse(roles["then"]),
            collapse(roles["else"]),
        )

    if kind == "seq":
        return ("seq", *collapse_all(roles["items"]))

    if kind == "call":
        return ("call", _decode(node.payload), *collapse_all(roles["args"]))

    if kind == "read":
        return ("read", _decode(node.payload))

    if kind == "write":
        return ("write", _decode(node.payload), collapse(roles["value"]))

    if kind == "quote":
        holes = iter(collapse_all(roles["holes"]))
        return ("quote", _fill(_decode(node.payload), holes))

    if kind == "unquote":
        return ("unquote", collapse(roles["expr"]))

    if kind == "function":
        return ("function", collapse(roles["params"]), collapse(roles["body"]))

    payload = _decode(node.payload)
    names = tuple(name for name, _ in payload["links"])
    pairs = _pairs(names, collapse_all(roles["values"]))

    if kind == "activate":
        return ("activate", *pairs)

    call = ("call", payload["call"][0], *collapse_all(roles["args"]))
    return ("trial", call, *pairs)


def function_at(state: State, entity: EntityID) -> Function | None:
    """Collapse a function of a graph-form state back to the input format.

    Returns None if ``entity`` is absent or is not a function. Link names
    come back as they were written, so ``function_at(load(s), f)`` equals
    the ``Function`` that ``s`` held.
    """

    value = state.values.get(entity)

    if value is None:
        return None

    definition = _definition_of(value)

    if definition is None:
        return None

    return Function(
        definition.params,
        _collapse(state, entity, definition.body),
    )


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _semantically_equal(left: Any, right: Any) -> bool:
    return canonical_serialize(canonicalize(left)) == canonical_serialize(
        canonicalize(right)
    )


@dataclass(frozen=True)
class _RunContext:
    runtime: Runtime
    may_activate: bool


def _eval_int(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    entity: EntityID,
    op: str,
) -> int:
    value = _eval(context, state, function_entity, bindings, entity)

    if not _is_int(value):
        raise LanguageError(
            f"{function_entity.value}: {op} operands must be int"
        )

    return value


def _quote(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    node: Relation,
) -> Any:
    """Fill a quote's holes, in template order, with their values."""

    def holes() -> Any:
        for hole in node.roles["holes"]:
            hole_node = _node_at(state, function_entity, hole)

            if hole_node.kind == INVALID_KIND:
                problem = _decode(hole_node.payload)[0]
                raise LanguageError(f"{function_entity.value}: {problem}")

            yield _eval(
                context,
                state,
                function_entity,
                bindings,
                hole_node.roles["expr"],
            )

    return _fill(_decode(node.payload), holes())


def _function(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    node: Relation,
) -> Function:
    params = _eval(
        context,
        state,
        function_entity,
        bindings,
        node.roles["params"],
    )
    body = _eval(
        context,
        state,
        function_entity,
        bindings,
        node.roles["body"],
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
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    node: Relation,
    op: str,
) -> tuple[State, dict[EntityID, Function]]:
    """Evaluate and check ``activate``/``trial``'s link/value pairs.

    Shared by ``activate`` (metaprogramming.md section 4) and ``trial``
    (language_trials.md section 2, whose pairs "are checked as for
    activate"). Evaluates the value expressions first, then reads the
    active state and checks every pair against it: each link resolved
    through the running function's link table to an entity whose value in
    that state is a function, no entity is named twice, and each value is
    a function. Reading the active state only after evaluation matters
    because evaluating a value expression can itself activate
    (language_trials.md section 8).
    """

    entries = _decode(node.payload)["links"]
    value_nodes = node.roles["values"]

    if len(entries) != len(value_nodes):
        raise LanguageError(
            f"{function_entity.value}: {op} needs link/value pairs"
        )

    evaluated_values = [
        _eval(context, state, function_entity, bindings, value_node)
        for value_node in value_nodes
    ]

    active = context.runtime.active.state
    resolved = iter(node.roles["targets"])
    targets: list[EntityID] = []

    for _, problem in entries:
        if problem is not None:
            raise LanguageError(f"{function_entity.value}: {problem}")

        target = next(resolved)

        if target in targets:
            raise LanguageError(
                f"{function_entity.value}: {op} target appears twice: "
                f"{target.value}"
            )

        if target not in active.values:
            raise LanguageError(
                f"{function_entity.value}: {op} target does not exist: "
                f"{target.value}"
            )

        if _definition_of(active.values[target]) is None:
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

    return active, dict(zip(targets, functions))


def _activate(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    node: Relation,
) -> None:
    active, functions = _activation_pairs(
        context,
        state,
        function_entity,
        bindings,
        node,
        "activate",
    )

    if not context.may_activate:
        raise ActivationRejected("activation capability not granted")

    context.runtime.activate(define(active, functions))
    return None


def _trial(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    node: Relation,
) -> Any:
    """Exercise a candidate in an isolated runtime (language_trials.md).

    The node names the call to make against the candidate, and its pairs
    are checked exactly as ``activate``'s (:func:`_activation_pairs`). The
    call's arguments are evaluated first, then the pairs' values, both in
    the running function's scope and the real runtime; only once that is
    done is the active state read to build the transformation, as
    :func:`define` does, and hand it to ``Runtime.trial``. The linked
    function then runs in the isolated runtime, without the activation
    capability, and its result is returned; the real runtime is never
    touched.
    """

    args = tuple(
        _eval(context, state, function_entity, bindings, arg)
        for arg in node.roles["args"]
    )

    active, functions = _activation_pairs(
        context,
        state,
        function_entity,
        bindings,
        node,
        "trial",
    )

    _, problem = _decode(node.payload)["call"]

    if problem is not None:
        raise LanguageError(f"{function_entity.value}: {problem}")

    if not context.may_activate:
        raise ActivationRejected("activation capability not granted")

    candidate = context.runtime.trial(define(active, functions))
    candidate_context = _RunContext(runtime=candidate, may_activate=False)

    return _call(candidate_context, node.roles["target"], args)


def _eval(
    context: _RunContext,
    state: State,
    function_entity: EntityID,
    bindings: dict[str, Any],
    entity: EntityID,
) -> Any:
    """Evaluate one expression node of a function body."""

    node = _node_at(state, function_entity, entity)
    op = node.kind
    roles = node.roles

    if op == "lit":
        return _decode(node.payload)

    if op == "arg":
        name = _decode(node.payload)

        if not isinstance(name, str) or name not in bindings:
            raise LanguageError(
                f"{function_entity.value}: unknown parameter {name!r}"
            )

        return bindings[name]

    if op in ("add", "sub", "mul"):
        left = _eval_int(
            context, state, function_entity, bindings, roles["left"], op
        )
        right = _eval_int(
            context, state, function_entity, bindings, roles["right"], op
        )

        if op == "add":
            return left + right

        if op == "sub":
            return left - right

        return left * right

    if op == "lt":
        left = _eval_int(
            context, state, function_entity, bindings, roles["left"], op
        )
        right = _eval_int(
            context, state, function_entity, bindings, roles["right"], op
        )

        return left < right

    if op == "eq":
        left = _eval(context, state, function_entity, bindings, roles["left"])
        right = _eval(context, state, function_entity, bindings, roles["right"])

        return _semantically_equal(left, right)

    if op == "if":
        condition = _eval(
            context, state, function_entity, bindings, roles["cond"]
        )

        if not isinstance(condition, bool):
            raise LanguageError(
                f"{function_entity.value}: if condition must be bool"
            )

        branch = roles["then"] if condition else roles["else"]

        return _eval(context, state, function_entity, bindings, branch)

    if op == "seq":
        result: Any = None

        for item in roles["items"]:
            result = _eval(context, state, function_entity, bindings, item)

        return result

    if op == "call":
        args = tuple(
            _eval(context, state, function_entity, bindings, arg)
            for arg in roles["args"]
        )

        return _call(context, roles["target"], args)

    if op == "read":
        # CellError means the link names something that is not a cell: a
        # language mistake (section 3), not a constraint rejection, so it
        # becomes a LanguageError. CellContentRejected and
        # RelationConstraintRejected are constraint failures and are left to
        # propagate unchanged.
        try:
            return context.runtime.read(roles["cell"])
        except CellError as exc:
            raise LanguageError(str(exc)) from exc

    if op == "write":
        value = _eval(context, state, function_entity, bindings, roles["value"])

        # Same distinction as "read" above.
        try:
            context.runtime.write(roles["cell"], value)
        except CellError as exc:
            raise LanguageError(str(exc)) from exc

        return value

    if op == "quote":
        return _quote(context, state, function_entity, bindings, node)

    if op == "function":
        return _function(context, state, function_entity, bindings, node)

    if op == "activate":
        return _activate(context, state, function_entity, bindings, node)

    if op == "trial":
        return _trial(context, state, function_entity, bindings, node)

    if op == INVALID_KIND:
        problem = _decode(node.payload)[0]
        raise LanguageError(f"{function_entity.value}: {problem}")

    # An unquote node is only ever a quote's hole.
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
        value = state.values[function_entity]
        definition = _definition_of(value)

        if definition is None:
            unloaded = function_of(value) is not None
            raise LanguageError(
                f"{function_entity.value} is not a function"
                + ("; load the program first" if unloaded else "")
            )

        if len(args) != len(definition.params):
            raise LanguageError(
                f"{function_entity.value} takes {len(definition.params)} "
                f"argument(s), got {len(args)}"
            )

        bindings = dict(zip(definition.params, args))

        return _eval(
            context,
            state,
            function_entity,
            bindings,
            definition.body,
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

    The runtime's program must be in graph form (:func:`load`). Arguments
    are canonicalized before being bound to the entry function's
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
