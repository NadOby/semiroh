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
(``shear/bytecode.py``, docs/bytecode.md).

This module is a layer on top of the core model, not part of it: it is not
re-exported from ``shear/__init__.py``.
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
from .matching import match
from .operations import ARITY, BINARY, INVALID, OPERATIONS
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
INVALID_KIND = INVALID

_BINARY = BINARY
_ARITY = ARITY
NODE_KINDS = frozenset(OPERATIONS)

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
    (``shear.bytecode.CALL_DEPTH_LIMIT``, bytecode.md section 4).
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
    ) -> None:
        self.function = function
        self.generation = generation
        self.scope = scope
        self.nodes: dict[EntityID, Relation] = {}
        self.labels: dict[str, EntityID] = {}
        self.root: EntityID | None = None
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
                name[0]
                if isinstance(name, tuple) and len(name) == 2
                else name
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

        if (
            not isinstance(template, tuple)
            or isinstance(template, CanonicalNode)
        ):
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
        if (
            not isinstance(expr, tuple)
            or not expr
            or not isinstance(expr[0], str)
        ):
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

        shape = OPERATIONS.get(op)

        if shape is not None and shape.positional:
            if len(rest) < shape.minimum:
                return _invalid(shape.too_few, expr)

            roles: dict[str, Any] = {}

            for index, role in enumerate(shape.code):
                if role in shape.ordered:
                    roles[role] = self.exprs(rest[index:])
                else:
                    roles[role] = self.expr(rest[index])

            return Relation(op, roles)




        if op in ("call", "read", "write"):
            if not rest:
                return _invalid("call needs a link", expr)

            target, problem = self.resolve(rest[0])

            if problem is not None:
                return _invalid(problem, expr)

            if op == "call":
                return Relation(
                    "call",
                    {
                        "target": target,
                        "args": self.exprs(rest[1:]),
                    },
                    rest[0],
                )

            if op == "read":
                return Relation("read", {"cell": target}, rest[0])

            return Relation(
                "write",
                {
                    "cell": target,
                    "value": self.expr(rest[1]),
                },
                rest[0],
            )

        if op == "quote":
            holes: list[EntityID] = []
            template = self.template(rest[0], holes)
            return Relation("quote", {"holes": tuple(holes)}, template)


        if op == "closure":
            return Relation(
                "closure",
                {"body": self.expr(rest[2])},
                {
                    "params": rest[0],
                    "captures": rest[1],
                },
            )






        if op == "let":
            if not isinstance(rest[0], str) or not rest[0]:
                return _invalid(
                    f"let name must be a non-empty string, got {rest[0]!r}",
                    expr,
                )

            return Relation(
                "let",
                {
                    "value": self.expr(rest[1]),
                    "body": self.expr(rest[2]),
                },
                rest[0],
            )

        if op == "ref":
            target, problem = self.resolve(rest[0])

            if problem is not None:
                return _invalid(problem, expr)

            return Relation("ref", {"target": target}, rest[0])

        if op in ("code", "linksof"):
            target, problem = self.resolve(rest[0])

            if problem is not None:
                return _invalid(problem, expr)

            return Relation(op, {"target": target}, rest[0])



        if op == "activate":
            if not rest or len(rest) % 2:
                return _invalid("activate needs link/value pairs", expr)

            values = self.exprs(rest[1::2])
            targets, entries = self.links(rest[0::2])

            return Relation(
                "activate",
                {
                    "targets": targets,
                    "values": values,
                },
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
            roles: dict[str, Endpoint] = {
                "args": self.exprs(call_form[2:])
            }
            roles["values"] = self.exprs(pairs[1::2])
            roles["targets"], entries = self.links(pairs[0::2])
            target, problem = self.resolve(call_form[1])

            if target is not None:
                roles["target"] = target

            return Relation(
                "trial",
                roles,
                {
                    "call": (call_form[1], problem),
                    "links": entries,
                },
            )

        return _invalid(f"unknown operation {op!r}", expr)


def _compile(
    entity: EntityID,
    expr: Any,
    links_table: Mapping[str, Endpoint],
    generation: int,
    taken: set[EntityID],
) -> _Builder:
    """Build the nodes of one expression of ``entity``; node names avoid
    ``taken``.

    The first generation whose node names are all free is used, so the
    result depends only on the arguments.
    """

    while True:
        builder = _Builder(entity, generation, links_table)
        builder.root = builder.expr(expr)

        if taken.isdisjoint(builder.nodes):
            return builder

        generation += 1


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
                found |= _subtree(
                    state,
                    function_entity,
                    owned,
                    child,
                )

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

        builder = _compile(
            entity,
            function.body,
            links_table,
            0,
            taken,
        )
        nodes = builder.nodes
        taken.update(nodes)
        changes[entity] = _Definition(
            function.params,
            builder.root,
            dict(links_table),
            dict(builder.labels),
            builder.generation,
        ).relation()
        changes.update(nodes)
        placements.update(dict.fromkeys(nodes, entity))

    return transform_with_mapping(
        state,
        changes,
        mappings,
        placements=placements,
    ).destination


@dataclass(frozen=True)
class _Entry:
    """One side-by-side of an edit (continuity_inference.md §1): the old
    nodes an entry of ``define`` replaces and the builder of the new side.
    ``position`` is the old node at the new root's position, if any.
    """

    function: EntityID
    old: dict[EntityID, Relation]
    builder: _Builder | None
    position: EntityID | None
    label: str | None = None


def _edits_of(
    state: State,
    edits: Mapping[EntityID | tuple[EntityID, str], Any],
) -> tuple[
    dict[EntityID, Function | None],
    dict[EntityID, dict[str, Any]],
    dict[EntityID, dict[str, Endpoint]],
]:
    """Sort the entries of ``define`` into whole functions (a ``Function``,
    or None to remove one), label edits and link tables.
    """

    whole: dict[EntityID, Function | None] = {}
    labelled: dict[EntityID, dict[str, Any]] = {}
    tables: dict[EntityID, dict[str, Endpoint]] = {}

    for key, value in edits.items():
        if isinstance(key, EntityID):
            if isinstance(value, Relation) and value.kind == LINKS_KIND:
                function = value.roles.get(FUNCTION_ROLE)

                if (
                    not isinstance(function, EntityID)
                    or function in tables
                ):
                    raise LanguageError(
                        f"{key.value}: a links relation needs one function, "
                        f"and a function one links relation"
                    )

                tables[function] = {
                    name: target
                    for name, target in value.roles.items()
                    if name != FUNCTION_ROLE
                }
                continue

            if value is not None and not isinstance(value, Function):
                raise LanguageError(
                    f"{key.value}: define needs a Function, None or a links "
                    f"relation for a whole function, not an expression"
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

            labelled.setdefault(key[0], {})[key[1]] = value
            continue

        raise LanguageError(f"not a define target: {key!r}")

    for entity in sorted({*whole, *labelled, *tables}):
        value = state.values.get(entity)
        current = None if value is None else _definition_of(value)
        created = value is None and whole.get(entity) is not None

        if value is not None and current is None:
            raise LanguageError(f"{entity.value} is not a function")

        if current is None and not created:
            raise LanguageError(f"{entity.value} does not exist")

        if entity in labelled and entity in whole:
            raise LanguageError(
                f"{entity.value}: define replaces a whole function or its "
                f"labelled nodes, not both"
            )

        if entity in tables and whole.get(entity, entity) is None:
            raise LanguageError(
                f"{entity.value}: a removed function has no links"
            )

    return whole, labelled, tables


def _old_side(
    state: State,
    function: EntityID,
    nodes: Any,
) -> dict[EntityID, Relation]:
    return {
        node: _node_at(state, function, node)
        for node in nodes
    }


def define(
    state: State,
    edits: Mapping[EntityID | tuple[EntityID, str], Any],
) -> TransformResult:
    """Edit functions of a graph-form state, inferring what the edit keeps
    (graph_form.md sections 5 and 9, continuity_inference.md).

    A key is a function entity or a ``(function, label)`` pair. A function
    entity takes a ``Function`` (its new body; a function absent from the
    state is created) or None (the function is removed). Any entity key
    may instead take a links relation (:func:`links`), which replaces the
    link table of the function it names; new bodies resolve link names
    through the new table. A ``(function, label)`` pair takes an expression
    (code as data) that replaces the labelled node and the nodes below it.

    Every entry's old nodes and new nodes form one pool, which
    :func:`shear.matching.match` matches: a matched node keeps its
    EntityID (and its VersionID when its content is equal), moving to the
    function whose new side holds it; an unmatched old node disappears; an
    unmatched new node is created, named ``<function>/<generation>.<index>``
    (graph_form.md section 4). Ownership of the result is stated whole, so
    a moved node's owner change is explicit. Every other entity is
    continuous with itself. The caller activates the result.
    """

    whole, labelled, tables = _edits_of(state, edits)
    taken = set(state.values)
    entries: list[_Entry] = []

    def compile_entry(
        function: EntityID,
        expr: Any,
        generation: int,
    ) -> _Builder:
        table = tables.get(function)

        if table is None:
            value = state.values.get(function)
            table = (
                {}
                if value is None
                else _definition_of(value).links
            )

        builder = _compile(
            function,
            expr,
            table,
            generation,
            taken,
        )
        taken.update(builder.nodes)
        return builder

    for entity in sorted(whole):
        function = whole[entity]
        current = (
            _definition_of(state.values[entity])
            if entity in state.values
            else None
        )
        old = (
            {}
            if current is None
            else _old_side(
                state,
                entity,
                state.owned_children(entity),
            )
        )
        builder = (
            None
            if function is None
            else compile_entry(
                entity,
                function.body,
                0 if current is None else current.generation + 1,
            )
        )
        entries.append(
            _Entry(
                entity,
                old,
                builder,
                None if current is None else current.body,
            )
        )

    for entity in sorted(labelled):
        current = _definition_of(state.values[entity])
        owned = set(state.owned_children(entity))
        scopes: dict[str, set[EntityID]] = {}

        for label in sorted(labelled[entity]):
            root = current.labels.get(label)

            if root is None:
                raise LanguageError(
                    f"{entity.value}: unknown label {label!r}"
                )

            scopes[label] = _subtree(
                state,
                entity,
                owned,
                root,
            )

        for label, scope in scopes.items():
            for other, inner in scopes.items():
                if (
                    other != label
                    and current.labels[label] in inner
                ):
                    raise LanguageError(
                        f"{entity.value}: node edits {label!r} and "
                        f"{other!r} overlap"
                    )

            builder = compile_entry(
                entity,
                labelled[entity][label],
                current.generation + 1,
            )
            entries.append(
                _Entry(
                    entity,
                    _old_side(state, entity, scope),
                    builder,
                    current.labels[label],
                    label,
                )
            )

    old: dict[EntityID, Relation] = {}
    new: dict[EntityID, Relation] = {}

    for entry in entries:
        old.update(entry.old)

        if entry.builder is not None:
            new.update(entry.builder.nodes)

    kept = match(
        old,
        new,
        [
            (entry.builder.root, entry.position)
            for entry in entries
            if entry.builder is not None
        ],
    )
    final = {
        node: kept.get(node, node)
        for node in new
    }
    changes: dict[EntityID, Any] = {}
    owners: dict[EntityID, EntityID] = {}
    relink: dict[EntityID, dict[EntityID, EntityID]] = {}
    labels: dict[EntityID, dict[str, EntityID]] = {}
    fresh: set[EntityID] = set()

    def change(entity: EntityID, content: Relation) -> None:
        value = state.values.get(entity)

        if value is None or Value(entity, content) != value:
            changes[entity] = content

    for entry in entries:
        builder = entry.builder

        if builder is None:
            continue

        for node, relation in builder.nodes.items():
            owners[final[node]] = entry.function
            change(
                final[node],
                relation.with_endpoints(final),
            )

            if node not in kept:
                fresh.add(entry.function)

        introduced = {
            name: final[node]
            for name, node in builder.labels.items()
        }
        root = final[builder.root]

        if entry.label is None:
            labels[entry.function] = introduced
            continue

        table = labels.setdefault(entry.function, {})

        for name, node in introduced.items():
            if (
                name in table
                or (name == entry.label and node != root)
            ):
                raise LanguageError(
                    f"{entry.function.value}: label {name!r} is already "
                    f"used elsewhere in the function"
                )

            table[name] = node

        if (
            entry.label in table
            and table[entry.label] != root
        ):
            raise LanguageError(
                f"{entry.function.value}: label {entry.label!r} is already "
                f"used elsewhere in the function"
            )

        table[entry.label] = root

        if root != entry.position:
            relink.setdefault(
                entry.function,
                {},
            )[entry.position] = root

    scoped = set(old)
    removed = {
        entity
        for entity, function in whole.items()
        if function is None
    }

    for entity in sorted(
        {*whole, *labelled, *tables} - removed
    ):
        value = state.values.get(entity)
        current = (
            None
            if value is None
            else _definition_of(value)
        )
        replaced = relink.get(entity, {})
        function = whole.get(entity)
        entry_table = labels.get(entity, {})

        if function is None:
            for node in state.owned_children(entity):
                if node not in scoped:
                    relation = _node_at(
                        state,
                        entity,
                        node,
                    )

                    if relation.endpoints & replaced.keys():
                        change(
                            node,
                            relation.with_endpoints(replaced),
                        )

            outside = {
                name: node
                for name, node in current.labels.items()
                if node not in scoped
            }

            for name in entry_table:
                if name in outside:
                    raise LanguageError(
                        f"{entity.value}: label {name!r} is already used "
                        f"elsewhere in the function"
                    )

            params = current.params
            body = replaced.get(
                current.body,
                current.body,
            )
            entry_table = {
                **outside,
                **entry_table,
            }
        else:
            params = function.params
            body = next(
                final[entry.builder.root]
                for entry in entries
                if (
                    entry.function == entity
                    and entry.builder is not None
                )
            )

        generation = (
            next(
                entry.builder.generation
                for entry in entries
                if (
                    entry.function == entity
                    and entry.builder is not None
                )
            )
            if (
                function is not None
                and (entity in fresh or current is None)
            )
            else current.generation
        )
        change(
            entity,
            _Definition(
                params,
                body,
                tables.get(
                    entity,
                    current.links if current else {},
                ),
                entry_table,
                generation,
            ).relation(),
        )

    mappings: dict[EntityID, Any] = {
        entity: (
            ()
            if entity in removed or entity in scoped
            else entity
        )
        for entity in state.values
    }

    for node in kept.values():
        mappings[node] = node

    ownership: dict[EntityID, list[EntityID]] = {
        owner: [
            child
            for child in children
            if child not in scoped and child not in removed
        ]
        for owner, children in state.ownership.items()
        if owner not in removed
    }

    for node, owner in owners.items():
        ownership.setdefault(owner, []).append(node)

    return transform_with_mapping(
        state,
        changes,
        mappings,
        ownership=ownership,
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


def _pairs(
    names: tuple[Any, ...],
    values: tuple[Any, ...],
) -> tuple[Any, ...]:
    """Interleave pair names and values; a trailing name stays unpaired."""

    items: list[Any] = []

    for index, name in enumerate(names):
        items.append(name)

        if index < len(values):
            items.append(values[index])

    return tuple(items)


def _fill(template: Any, holes: Any) -> Any:
    """Put each value of the ``holes`` iterator back in place of a hole."""

    if (
        not isinstance(template, tuple)
        or isinstance(template, CanonicalNode)
    ):
        return template

    if template and template[0] == "unquote":
        return next(holes)

    return tuple(
        _fill(item, holes)
        for item in template
    )


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
        definition = (
            _definition_of(value)
            if value is not None
            else None
        )
        labels = (
            {
                target: name
                for name, target in definition.labels.items()
            }
            if definition is not None
            else {}
        )

    node = _node_at(
        state,
        function_entity,
        entity,
    )
    kind = node.kind
    roles = node.roles

    def collapse(child: EntityID) -> Any:
        return _collapse(
            state,
            function_entity,
            child,
            labels,
        )

    def collapse_all(
        children: tuple[EntityID, ...],
    ) -> tuple[Any, ...]:
        return tuple(
            collapse(child)
            for child in children
        )

    if kind == INVALID_KIND:
        expr = _decode(node.payload)[1]
    elif kind in ("lit", "arg"):
        expr = (kind, _decode(node.payload))
    elif kind in OPERATIONS and OPERATIONS[kind].positional:
        shape = OPERATIONS[kind]
        operands: list[Any] = []

        for role in shape.code:
            if role in shape.ordered:
                operands.extend(collapse_all(roles[role]))
            else:
                operands.append(collapse(roles[role]))

        expr = (kind, *operands)
    elif kind == "call":
        expr = (
            "call",
            _decode(node.payload),
            *collapse_all(roles["args"]),
        )
    elif kind == "closure":
        payload = _decode(node.payload)
        expr = (
            "closure",
            payload["params"],
            payload["captures"],
            collapse(roles["body"]),
        )
    elif kind == "let":
        expr = (
            "let",
            _decode(node.payload),
            collapse(roles["value"]),
            collapse(roles["body"]),
        )
    elif kind == "ref":
        expr = (
            "ref",
            _decode(node.payload),
        )
    elif kind in ("code", "linksof"):
        expr = (
            kind,
            _decode(node.payload),
        )
    elif kind == "read":
        expr = (
            "read",
            _decode(node.payload),
        )
    elif kind == "write":
        expr = (
            "write",
            _decode(node.payload),
            collapse(roles["value"]),
        )
    elif kind == "quote":
        holes = iter(
            collapse_all(roles["holes"])
        )
        expr = (
            "quote",
            _fill(
                _decode(node.payload),
                holes,
            ),
        )
    elif kind == "unquote":
        expr = (
            "unquote",
            collapse(roles["expr"]),
        )
    else:
        payload = _decode(node.payload)
        names = tuple(
            name
            for name, _ in payload["links"]
        )
        pairs = _pairs(
            names,
            collapse_all(roles["values"]),
        )

        if kind == "activate":
            expr = (
                "activate",
                *pairs,
            )
        else:
            call = (
                "call",
                payload["call"][0],
                *collapse_all(roles["args"]),
            )
            expr = (
                "trial",
                call,
                *pairs,
            )

    name = labels.get(entity)
    return (
        ("label", name, expr)
        if name is not None
        else expr
    )


def function_at(
    state: State,
    entity: EntityID,
) -> Function | None:
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
        _collapse(
            state,
            entity,
            definition.body,
        ),
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
    :func:`shear.bytecode.run`, which this calls, for the details of a
    run.

    Arguments are canonicalized before being bound to the entry function's
    parameters. Every call enters and releases a frame, so a finished run
    leaves no holds; a run that raises releases its frames too.

    By default a run cannot activate a new program state. Passing
    ``may_activate=True`` grants the run the provisional activation
    capability described in metaprogramming.md section 4.
    """

    from .bytecode import run as run_bytecode

    return run_bytecode(
        runtime,
        entry,
        *args,
        may_activate=may_activate,
    )
