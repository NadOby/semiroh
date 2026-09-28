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
the input format, and :func:`define` replaces whole bodies or single
labelled nodes (graph_form.md section 9).

Code as data stays in the input format: ``quote`` builds tuples,
``function`` builds :class:`Function` values, and ``activate`` and
``trial`` install them the way :func:`define` does. Running a function can
change program state only through ``activate``, and only when the run was
granted the activation capability.

:func:`run` lowers each node to bytecode and runs it on a virtual machine
(``semiroh/bytecode.py``, docs/bytecode.md).

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
from .runtime import Runtime
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
LABEL_ROLE_PREFIX = "label:"
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
    "len": 1,
    "item": 2,
    "slice": 3,
    "concat": 2,
    "let": 3,
    "ref": 1,
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
    "tuple",
    "len",
    "item",
    "slice",
    "concat",
    "let",
    "ref",
    "apply",
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


class CallDepthExceeded(LanguageError):
    """A run has more calls waiting on each other than the machine allows
    (``semiroh.bytecode.CALL_DEPTH_LIMIT``, bytecode.md section 4).
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
    which new bodies are resolved against. ``labels`` is the function's
    label table: each label name of its body to the node entity it marks
    (graph_form.md section 9), stored as roles the same way as ``links`` so
    a labelled node's rename or disappearance follows endpoint continuity.
    ``generation`` counts the bodies the function has had, so the node
    entities of a new body never reuse the names of an earlier one.
    """

    params: tuple[str, ...]
    body: EntityID
    links: Mapping[str, Endpoint]
    labels: Mapping[str, EntityID]
    generation: int

    def relation(self) -> Relation:
        roles: dict[str, Endpoint] = {BODY_ROLE: self.body}

        for name, target in self.links.items():
            roles[LINK_ROLE_PREFIX + name] = target

        for name, target in self.labels.items():
            roles[LABEL_ROLE_PREFIX + name] = target

        return Relation(
            DEFINITION_KIND,
            roles,
            {"params": self.params, "generation": self.generation},
        )


_UNREAD = object()


def _definition_of(value: Value) -> _Definition | None:
    """Return the definition held by a value, or None if it holds none.

    Every call reads its function's definition, so the record is kept with
    the value, like the decoded relation (relations.relation_of). Values
    are immutable, so it can never disagree with the content.
    """

    cached = value.__dict__.get("_definition", _UNREAD)

    if cached is not _UNREAD:
        return cached

    definition = _read_definition(value)
    object.__setattr__(value, "_definition", definition)

    return definition


def _read_definition(value: Value) -> _Definition | None:
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
            {
                role[len(LABEL_ROLE_PREFIX):]: endpoint
                for role, endpoint in node.roles.items()
                if role.startswith(LABEL_ROLE_PREFIX)
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
        root: EntityID | None = None,
    ) -> None:
        self.function = function
        self.generation = generation
        self.scope = scope
        self.nodes: dict[EntityID, Relation] = {}
        self.labels: dict[str, EntityID] = {}
        self._count = 0
        # A node edit (graph_form.md section 9) reuses the labelled node's
        # own EntityID for the root of its replacement instead of
        # allocating a fresh one; every other allocation is as usual.
        self._root = root

    def _allocate(self) -> EntityID:
        if self._count == 0 and self._root is not None:
            entity = self._root
        else:
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

        A name is either a link name (a whole-function target) or a
        ``(link, label)`` pair naming one node of that function
        (graph_form.md section 9); only the link part is resolved here; a
        node target's label is checked against the target's live labels
        when the pair is checked (:func:`_activation_pairs`). Returns the
        resolved targets, in order, and one ``(name, problem)`` entry per
        name; the problem is raised only when the pairs are checked, after
        their values are evaluated.
        """

        targets: list[EntityID] = []
        entries: list[tuple[Any, str | None]] = []

        for name in names:
            link_name = (
                name[0] if isinstance(name, tuple) and len(name) == 2 else name
            )
            target, problem = self.resolve(link_name)

            if target is not None:
                targets.append(target)

            entries.append((name, problem))

        return tuple(targets), tuple(entries)

    def expr(self, expr: Any) -> EntityID:
        if isinstance(expr, tuple) and len(expr) == 3 and expr[0] == "label":
            return self._label(expr[1], expr[2])

        entity = self._allocate()
        self.nodes[entity] = self._relation(expr)
        return entity

    def _label(self, name: Any, inner: Any) -> EntityID:
        """Compile a ``("label", name, inner)`` form (graph_form.md section
        9): transparent at run time, so it costs no node of its own; the
        entity ``inner`` compiles to is simply also recorded under
        ``name``.
        """

        if not isinstance(name, str) or not name:
            raise LanguageError(
                f"{self.function.value}: label name must be a non-empty "
                f"string, got {name!r}"
            )

        if name in self.labels:
            raise LanguageError(
                f"{self.function.value}: duplicate label {name!r}"
            )

        entity = self.expr(inner)
        self.labels[name] = entity
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

        if op == "tuple":
            return Relation("tuple", {"items": self.exprs(rest)})

        if op == "len":
            return Relation("len", {"tuple": self.expr(rest[0])})

        if op == "item":
            return Relation(
                "item",
                {"tuple": self.expr(rest[0]), "index": self.expr(rest[1])},
            )

        if op == "slice":
            return Relation(
                "slice",
                {
                    "tuple": self.expr(rest[0]),
                    "start": self.expr(rest[1]),
                    "stop": self.expr(rest[2]),
                },
            )

        if op == "concat":
            return Relation(
                "concat",
                {"left": self.expr(rest[0]), "right": self.expr(rest[1])},
            )

        if op == "let":
            if not isinstance(rest[0], str) or not rest[0]:
                return _invalid(
                    f"let name must be a non-empty string, got {rest[0]!r}",
                    expr,
                )

            return Relation(
                "let",
                {"value": self.expr(rest[1]), "body": self.expr(rest[2])},
                rest[0],
            )

        if op == "ref":
            target, problem = self.resolve(rest[0])

            if problem is not None:
                return _invalid(problem, expr)

            return Relation("ref", {"target": target}, rest[0])

        if op == "apply":
            if not rest:
                return _invalid("apply needs a function", expr)

            return Relation(
                "apply",
                {"function": self.expr(rest[0]), "args": self.exprs(rest[1:])},
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

    definition = _Definition(
        function.params, root, dict(links_table), dict(builder.labels), generation
    )

    return definition.relation(), builder.nodes


def _compile_node(
    entity: EntityID,
    root: EntityID,
    expr: Any,
    links_table: Mapping[str, Endpoint],
    generation: int,
    taken: set[EntityID],
) -> tuple[dict[EntityID, Relation], dict[str, EntityID]]:
    """Build the replacement for one labelled node (graph_form.md section
    9). ``root``, the labelled node, keeps its EntityID and takes ``expr``'s
    compiled root content; any deeper nodes ``expr`` needs are fresh,
    retried at a later generation if their names collide with ``taken``.
    """

    while True:
        builder = _Builder(entity, generation, links_table, root=root)
        builder.expr(expr)
        fresh = set(builder.nodes) - {root}

        if taken.isdisjoint(fresh):
            break

        generation += 1

    return builder.nodes, builder.labels


def _subtree(
    state: State,
    function_entity: EntityID,
    owned: set[EntityID],
    entity: EntityID,
) -> set[EntityID]:
    """The nodes of ``function_entity`` structurally below ``entity``
    (itself included). Ownership is flat (section 4), so the old nodes a
    node edit must remove are found by walking roles, not ownership.
    """

    found = {entity}
    node = _node_at(state, function_entity, entity)

    for value in node.roles.values():
        children = value if isinstance(value, tuple) else (value,)

        for child in children:
            if child in owned and child not in found:
                found |= _subtree(state, function_entity, owned, child)

    return found


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
    edits: Mapping[EntityID | tuple[EntityID, str], Any],
) -> TransformResult:
    """Replace whole function bodies, or single labelled nodes, in a
    graph-form state (graph_form.md sections 5 and 9).

    A key is either a function entity, with a ``Function`` value, or a
    ``(function, label)`` pair, with an expression (code as data) value.
    Whole-function entries replace whole bodies: each new body's link
    names resolve through its function's link table, the function's old
    nodes disappear, its new nodes are placed under it, and it gets a new
    definition. Node entries replace one labelled node: it keeps its
    EntityID and takes the new expression's root content, the nodes below
    it disappear, and any nodes the new expression needs are placed under
    the function; the function's own value changes only if the edit adds a
    label. Every other entity is continuous with itself (graph_form.md
    section 6). The caller activates the result.
    """

    changes: dict[EntityID, Any] = {}
    mappings: dict[EntityID, Any] = {}
    placements: dict[EntityID, EntityID] = {}
    taken = set(state.values)

    whole: dict[EntityID, Function] = {}
    node_edits: dict[EntityID, dict[str, Any]] = {}

    for key, value in edits.items():
        if isinstance(key, EntityID):
            if not isinstance(value, Function):
                raise LanguageError(
                    f"{key.value}: define needs a Function for a whole "
                    f"function, not an expression"
                )

            whole[key] = value
            continue

        if (
            isinstance(key, tuple)
            and len(key) == 2
            and isinstance(key[0], EntityID)
            and isinstance(key[1], str)
        ):
            if isinstance(value, Function):
                raise LanguageError(
                    f"{key[0].value}: define needs an expression for node "
                    f"{key[1]!r}, not a Function"
                )

            node_edits.setdefault(key[0], {})[key[1]] = value
            continue

        raise LanguageError(f"not a define target: {key!r}")

    for entity in sorted(whole):
        function = whole[entity]

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

    for entity in sorted(node_edits):
        if entity not in state.values:
            raise LanguageError(f"{entity.value} does not exist")

        current = _definition_of(state.values[entity])

        if current is None:
            raise LanguageError(f"{entity.value} is not a function")

        owned = set(state.owned_children(entity))
        new_labels: dict[str, EntityID] = {}

        for label in sorted(node_edits[entity]):
            root = current.labels.get(label)

            if root is None:
                raise LanguageError(f"{entity.value}: unknown label {label!r}")

            nodes, introduced = _compile_node(
                entity,
                root,
                node_edits[entity][label],
                current.links,
                current.generation + 1,
                taken,
            )

            for name, target in introduced.items():
                if name == label and target == root:
                    continue

                if name in current.labels or name in new_labels:
                    raise LanguageError(
                        f"{entity.value}: label {name!r} is already used "
                        f"elsewhere in the function"
                    )

                new_labels[name] = target

            taken.update(set(nodes) - {root})

            for old in _subtree(state, entity, owned, root) - {root}:
                mappings[old] = ()

            changes.update(nodes)
            placements.update(dict.fromkeys(set(nodes) - {root}, entity))

        if new_labels:
            updated = _Definition(
                current.params,
                current.body,
                current.links,
                {**current.labels, **new_labels},
                current.generation,
            )
            changes[entity] = updated.relation()

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


def _collapse(
    state: State,
    function_entity: EntityID,
    entity: EntityID,
    labels: Mapping[EntityID, str] | None = None,
) -> Any:
    """Return the input-format expression of a node and its operands.

    ``labels`` maps a node entity to the label name that marks it
    (graph_form.md section 9); when omitted (the top-level call), it is
    read from ``function_entity``'s own definition. A labelled node
    collapses back under a ``("label", name, ...)`` wrapper, since the
    label costs no node of its own (:meth:`_Builder._label`).
    """

    if labels is None:
        value = state.values.get(function_entity)
        definition = _definition_of(value) if value is not None else None
        labels = (
            {target: name for name, target in definition.labels.items()}
            if definition is not None
            else {}
        )

    node = _node_at(state, function_entity, entity)
    kind = node.kind
    roles = node.roles

    def collapse(child: EntityID) -> Any:
        return _collapse(state, function_entity, child, labels)

    def collapse_all(children: tuple[EntityID, ...]) -> tuple[Any, ...]:
        return tuple(collapse(child) for child in children)

    if kind == INVALID_KIND:
        expr = _decode(node.payload)[1]
    elif kind in ("lit", "arg"):
        expr = (kind, _decode(node.payload))
    elif kind in _BINARY:
        expr = (kind, collapse(roles["left"]), collapse(roles["right"]))
    elif kind == "if":
        expr = (
            "if",
            collapse(roles["cond"]),
            collapse(roles["then"]),
            collapse(roles["else"]),
        )
    elif kind == "seq":
        expr = ("seq", *collapse_all(roles["items"]))
    elif kind == "call":
        expr = ("call", _decode(node.payload), *collapse_all(roles["args"]))
    elif kind == "tuple":
        expr = ("tuple", *collapse_all(roles["items"]))
    elif kind == "len":
        expr = ("len", collapse(roles["tuple"]))
    elif kind == "item":
        expr = ("item", collapse(roles["tuple"]), collapse(roles["index"]))
    elif kind == "slice":
        expr = (
            "slice",
            collapse(roles["tuple"]),
            collapse(roles["start"]),
            collapse(roles["stop"]),
        )
    elif kind == "concat":
        expr = ("concat", collapse(roles["left"]), collapse(roles["right"]))
    elif kind == "let":
        expr = (
            "let",
            _decode(node.payload),
            collapse(roles["value"]),
            collapse(roles["body"]),
        )
    elif kind == "ref":
        expr = ("ref", _decode(node.payload))
    elif kind == "apply":
        expr = (
            "apply",
            collapse(roles["function"]),
            *collapse_all(roles["args"]),
        )
    elif kind == "read":
        expr = ("read", _decode(node.payload))
    elif kind == "write":
        expr = ("write", _decode(node.payload), collapse(roles["value"]))
    elif kind == "quote":
        holes = iter(collapse_all(roles["holes"]))
        expr = ("quote", _fill(_decode(node.payload), holes))
    elif kind == "unquote":
        expr = ("unquote", collapse(roles["expr"]))
    elif kind == "function":
        expr = ("function", collapse(roles["params"]), collapse(roles["body"]))
    else:
        payload = _decode(node.payload)
        names = tuple(name for name, _ in payload["links"])
        pairs = _pairs(names, collapse_all(roles["values"]))

        if kind == "activate":
            expr = ("activate", *pairs)
        else:
            call = ("call", payload["call"][0], *collapse_all(roles["args"]))
            expr = ("trial", call, *pairs)

    name = labels.get(entity)
    return ("label", name, expr) if name is not None else expr


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
# Running
# ---------------------------------------------------------------------------


def run(
    runtime: Runtime,
    entry: EntityID,
    *args: Any,
    may_activate: bool = False,
) -> Any:
    """Evaluate ``entry`` and return its result.

    The runtime's program must be in graph form (:func:`load`). Nodes lower
    to bytecode that a virtual machine runs (bytecode.md); see
    :func:`semiroh.bytecode.run`, which this calls, for the details of a
    run.

    Arguments are canonicalized before being bound to the entry function's
    parameters. Every call enters and releases a frame, so a finished run
    leaves no holds; a run that raises releases its frames too.

    By default a run cannot activate a new program state. Passing
    ``may_activate=True`` grants the run the provisional activation
    capability described in metaprogramming.md section 4.
    """

    from .bytecode import run as run_bytecode

    return run_bytecode(runtime, entry, *args, may_activate=may_activate)
