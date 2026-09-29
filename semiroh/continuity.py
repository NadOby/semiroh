"""The continuity corpus (docs/continuity_corpus.md).

Each case is a program in text syntax, an operation on its graph form and
the continuity the operation should give: which entities survive, which are
new, which disappear, merge or split, and what activation does to cell
content. ``check`` runs a case and reports where the model differs from the
expectation; a case's ``status`` records whether it does today.

Designators name entities without writing generated ids::

    fn:NAME            a function entity
    cell:NAME          a cell entity
    node:NAME@PATH     the node at PATH in function NAME, before
    after:NAME@PATH    the node at PATH in function NAME, after

A PATH is the input-form position of an expression: ``""`` is the body root
and ``"1.0"`` is operand 0 of operand 1. Link names, parameter names and
labels are not operands (a label costs no node), so a path counts what
``function_at`` would give as operands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .canonical import CanonicalNode, canonicalize
from .cells import CellDeclaration, cell_declaration
from .constraints import EvaluationContext
from .identity import EntityID
from .fold import fold_constants
from .lang import define, function_at, function_of, load
from .relations import DanglingRelation, relation_of
from .runtime import ActivationRejected, Converter, Runtime
from .state import State
from .syntax import parse
from .transforms import TransformResult, transform_with_mapping

GROUPS = ("declared", "inferred", "competing", "moved")

Operation = Callable[[State], "TransformResult | tuple[TransformResult, ...]"]


@dataclass(frozen=True)
class Expect:
    """What an operation should do to identity (continuity_corpus.md §1).

    Every field lists designators. ``at`` maps a designator before to one
    after that must be the same entity; ``merged`` and ``split`` map a source
    to the destination(s) its mapping records; ``rejected`` is the exception
    the operation or the activation raises; ``cells`` maps cell designators
    to their content after activation.
    """

    kept: tuple[str, ...] = ()
    changed: tuple[str, ...] = ()
    gone: tuple[str, ...] = ()
    new: tuple[str, ...] = ()
    at: Mapping[str, str] = field(default_factory=dict)
    merged: Mapping[str, str] = field(default_factory=dict)
    split: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    rejected: type[BaseException] | None = None
    cells: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Case:
    """One continuity case.

    ``operation(state)`` gets the loaded source and returns a
    ``TransformResult``, or a pair of them built from the same state (group
    ``competing``), or raises. ``writes`` is content written into the cells
    of the running program before the result is activated, so that a
    transfer can be told from a reset to the declared initial content (an
    addition to the format of continuity_corpus.md section 1).
    """

    name: str
    group: str
    source: str
    operation: Operation
    expect: Expect
    status: str
    note: str
    converters: Mapping[str, Converter] = field(default_factory=dict)
    context: EvaluationContext | None = None
    writes: Mapping[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Designators
# ---------------------------------------------------------------------------

# The operands of a node in input-form order (graph_form.md section 3): the
# roles that hold code, in the order ``function_at`` writes them. Leaves,
# reads, references and every other role (a call's target, a cell) are not
# operands.
_OPERANDS: dict[str, tuple[str, ...]] = {
    **dict.fromkeys(("add", "sub", "mul", "lt", "eq", "concat"), ("left", "right")),
    "if": ("cond", "then", "else"),
    "seq": ("items",),
    "tuple": ("items",),
    "call": ("args",),
    "write": ("value",),
    "len": ("tuple",),
    "item": ("tuple", "index"),
    "slice": ("tuple", "start", "stop"),
    "let": ("value", "body"),
    "apply": ("function", "args"),
    "applyv": ("function", "args"),
    "quote": ("holes",),
    "unquote": ("expr",),
    "function": ("params", "body"),
    "activate": ("values",),
    "trial": ("args", "values"),
}


class DesignatorError(ValueError):
    """A designator that names nothing in the state it is resolved in."""


def _operands(state: State, entity: EntityID) -> tuple[EntityID, ...]:
    value = state.values.get(entity)
    node = None if value is None else relation_of(value)

    if node is None:
        return ()

    found: list[EntityID] = []

    for role in _OPERANDS.get(node.kind, ()):
        endpoint = node.roles[role]
        found.extend(endpoint if isinstance(endpoint, tuple) else (endpoint,))

    return tuple(found)


def _node_at(state: State, function: EntityID, path: str) -> EntityID:
    value = state.values.get(function)
    definition = None if value is None else relation_of(value)

    if definition is None or definition.kind != "definition":
        raise DesignatorError(f"{function.value} is not a function of the state")

    entity = definition.roles["body"]

    for step in path.split(".") if path else ():
        operands = _operands(state, entity)

        if not step.isdigit() or int(step) >= len(operands):
            raise DesignatorError(
                f"{function.value}@{path}: {entity.value} has "
                f"{len(operands)} operand(s), there is no {step!r}"
            )

        entity = operands[int(step)]

    if entity not in state.owned_children(function):
        raise DesignatorError(
            f"{function.value}@{path}: {entity.value} is not owned by "
            f"{function.value}"
        )

    return entity


def resolve(
    designator: str,
    before: State,
    after: State | None = None,
) -> EntityID:
    """The entity a designator names: ``node:`` in ``before``, ``after:`` in
    ``after``, and ``fn:`` and ``cell:`` by name. Raises ``DesignatorError``
    when it names nothing.
    """

    kind, _, rest = designator.partition(":")

    if kind in ("fn", "cell") and rest:
        return EntityID(rest)

    if kind in ("node", "after"):
        name, at, path = rest.partition("@")

        if name and at:
            state = before if kind == "node" else after

            if state is None:
                raise DesignatorError(f"{designator}: there is no state after")

            return _node_at(state, EntityID(name), path)

    raise DesignatorError(f"{designator!r} is not a designator")


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


def _functions(state: State) -> list[EntityID]:
    return [
        entity
        for entity in sorted(state.values)
        if (node := relation_of(state.values[entity])) is not None
        and node.kind == "definition"
    ]


def _describe(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _runtime(case: Case, source: State) -> Runtime:
    runtime = Runtime(source, case.context)

    for designator, content in case.writes.items():
        runtime.write(resolve(designator, source), content)

    return runtime


def _structure(
    case: Case,
    source: State,
    destination: State,
    record: Callable[[EntityID], Any],
) -> list[str]:
    """The mismatches between two states, and the mapping records ``record``
    gives, and ``case.expect`` (everything but ``rejected`` and ``cells``).
    """

    expect = case.expect
    problems: list[str] = []
    mentioned: set[EntityID] = set()

    def find(field_name: str, designator: str) -> EntityID | None:
        try:
            return resolve(designator, source, destination)
        except DesignatorError as exc:
            problems.append(f"{field_name} {designator}: {exc}")
            return None

    def version(state: State, entity: EntityID) -> Any:
        return state.values[entity].version_id

    for label, designators in (("kept", expect.kept), ("changed", expect.changed)):
        for designator in designators:
            entity = find(label, designator)

            if entity is None:
                continue

            mentioned.add(entity)

            if entity not in source.values or entity not in destination.values:
                side = "before" if entity not in source.values else "after"
                problems.append(f"{label} {designator}: {entity.value} is absent {side}")
            elif (version(source, entity) == version(destination, entity)) != (
                label == "kept"
            ):
                problems.append(
                    f"{label} {designator}: {entity.value} "
                    f"{'has a new version' if label == 'kept' else 'kept its version'}"
                )

    for designator in expect.gone:
        entity = find("gone", designator)

        if entity is None:
            continue

        mentioned.add(entity)
        mapping = record(entity)

        if entity in destination.values:
            problems.append(f"gone {designator}: {entity.value} is still present after")
        elif mapping is None or mapping.destination_entities:
            problems.append(
                f"gone {designator}: {entity.value} is absent after but not "
                f"recorded as a disappearance"
            )

    for designator in expect.new:
        entity = find("new", designator)

        if entity is None:
            continue

        if entity in source.values:
            problems.append(f"new {designator}: {entity.value} was already there before")
        elif entity not in destination.values:
            problems.append(f"new {designator}: {entity.value} is absent after")

    for before, after in expect.at.items():
        first, second = find("at", before), find("at", after)

        if first is None or second is None:
            continue

        mentioned.add(first)

        if first != second:
            problems.append(
                f"at {before}: {first.value} is not at {after} "
                f"(that is {second.value})"
            )

    for designator, target in expect.merged.items():
        entity, destination_entity = find("merged", designator), find("merged", target)

        if entity is None or destination_entity is None:
            continue

        mentioned.add(entity)
        mapping = record(entity)
        found = () if mapping is None else mapping.destination_entities

        if found != (destination_entity,):
            problems.append(
                f"merged {designator}: mapped to "
                f"{[item.value for item in found] or 'nothing'}, "
                f"expected {target} ({destination_entity.value})"
            )

    for designator, targets in expect.split.items():
        entity = find("split", designator)
        wanted = [find("split", target) for target in targets]

        if entity is None or None in wanted:
            continue

        mentioned.add(entity)
        mapping = record(entity)
        found = () if mapping is None else mapping.destination_entities

        if found != tuple(sorted(wanted)):  # type: ignore[type-var]
            problems.append(
                f"split {designator}: mapped to "
                f"{[item.value for item in found] or 'nothing'}, expected "
                f"{[item.value for item in wanted if item is not None]}"
            )

    if case.group == "declared":
        # A declared transformation says what happens to everything it
        # touches; the rest of every function must stay as it was.
        for function in _functions(source):
            for node in source.owned_children(function):
                if node in mentioned:
                    continue

                if node not in destination.values:
                    problems.append(
                        f"unmentioned {node.value} of {function.value} is gone"
                    )
                elif version(source, node) != version(destination, node):
                    problems.append(
                        f"unmentioned {node.value} of {function.value} changed"
                    )

    return problems


def _cells(case: Case, source: State, runtime: Runtime) -> list[str]:
    problems: list[str] = []

    for designator, content in case.expect.cells.items():
        try:
            found = runtime.read(resolve(designator, source))
        except Exception as exc:  # absent or not a cell after activation
            problems.append(f"cells {designator}: {_describe(exc)}")
            continue

        if found != canonicalize(content):
            problems.append(f"cells {designator}: holds {found!r}, expected {content!r}")

    return problems


def _check_one(case: Case, source: State, result: TransformResult) -> list[str]:
    expect = case.expect
    runtime: Runtime | None = None
    problems: list[str] = []

    try:
        runtime = _runtime(case, source)
        runtime.activate(result, case.converters)
    except Exception as exc:
        if expect.rejected is not None and isinstance(exc, expect.rejected):
            return []

        problems.append(f"activation raised {_describe(exc)}")
        runtime = None
    else:
        if expect.rejected is not None:
            return [f"expected {expect.rejected.__name__}, nothing was rejected"]

    problems += _structure(case, source, result.destination, result.mapping_for)

    if expect.cells:
        if runtime is None:
            problems.append("cells: the result could not be activated")
        else:
            problems += _cells(case, source, runtime)

    return problems


def _check_pair(
    case: Case,
    source: State,
    results: tuple[TransformResult, ...],
) -> list[str]:
    """Two transformations built from the same state, activated one after the
    other in either order. ``expect.rejected`` is what the second raises; with
    none, both apply and the final state is checked.
    """

    expect = case.expect
    problems: list[str] = []

    def record(entity: EntityID) -> Any:
        # Every rewrite maps what it does not touch to itself, so the record
        # that says something is the one that does not.
        found = None

        for result in results:
            mapping = result.mapping_for(entity)

            if mapping is not None and mapping.destination_entities != (entity,):
                return mapping

            found = found or mapping

        return found

    for order in ((0, 1), (1, 0)):
        label = f"{'first' if order[0] == 0 else 'second'} edit, then the other"
        runtime = _runtime(case, source)

        try:
            runtime.activate(results[order[0]], case.converters)
        except Exception as exc:
            problems.append(f"{label}: the first activation raised {_describe(exc)}")
            continue

        try:
            runtime.activate(results[order[1]], case.converters)
        except Exception as exc:
            if expect.rejected is None or not isinstance(exc, expect.rejected):
                problems.append(f"{label}: the second activation raised {_describe(exc)}")

            continue

        if expect.rejected is not None:
            problems.append(
                f"{label}: expected {expect.rejected.__name__}, nothing was rejected"
            )
            continue

        problems += [
            f"{label}: {problem}"
            for problem in _structure(case, source, runtime.active.state, record)
        ]

        if expect.cells:
            problems += [f"{label}: {problem}" for problem in _cells(case, source, runtime)]

    return problems


def check(case: Case) -> tuple[str, ...]:
    """The mismatches between what the case's operation does and what it
    expects, each naming the designator involved; empty when it holds.
    """

    source = load(parse(case.source))

    try:
        produced = case.operation(source)
    except Exception as exc:
        rejected = case.expect.rejected

        if rejected is not None and isinstance(exc, rejected):
            return ()

        return (f"the operation raised {_describe(exc)}",)

    if isinstance(produced, tuple):
        return tuple(_check_pair(case, source, produced))

    return tuple(_check_one(case, source, produced))


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def _redefine(name: str, program: str) -> Operation:
    """Replace the whole body of ``name`` by the one ``program`` gives it."""

    def operation(state: State) -> TransformResult:
        function = function_of(parse(program).values[EntityID(name)])
        return define(state, {EntityID(name): function})

    return operation


def _edit(*edits: tuple[str, str, Any]) -> Operation:
    """Replace the labelled nodes ``(function, label, expression)``."""

    def operation(state: State) -> TransformResult:
        return define(
            state,
            {(EntityID(name), label): expr for name, label, expr in edits},
        )

    return operation


def _competing(*edits: tuple[str, str, Any]) -> Operation:
    """One label edit per entry, each built from the same state."""

    def operation(state: State) -> tuple[TransformResult, ...]:
        return tuple(_edit(edit)(state) for edit in edits)

    return operation


def _reimport(program: str) -> Operation:
    """The closest a host gets when no operation expresses an edit: load the
    edited program as it is written (syntax.md: import-only), with no
    continuity declared between the two states.
    """

    def operation(state: State) -> TransformResult:
        return TransformResult(
            source=state,
            destination=load(parse(program)),
            mappings=(),
        )

    return operation


def _rename(old: str, new: str) -> Operation:
    def operation(state: State) -> TransformResult:
        mappings: dict[EntityID, Any] = {entity: entity for entity in state.values}
        mappings[EntityID(old)] = EntityID(new)
        return transform_with_mapping(
            state,
            {EntityID(new): state.values[EntityID(old)].content},
            mappings,
        )

    return operation


def _delete(name: str) -> Operation:
    """Map the function ``name`` to nothing and everything else to itself;
    the function's nodes are left for the owned-subtree cascade.
    """

    def operation(state: State) -> TransformResult:
        function = EntityID(name)
        owned = state.owned_subtree(function) | {function}
        mappings: dict[EntityID, Any] = {
            entity: entity for entity in state.values if entity not in owned
        }
        mappings[function] = ()
        return transform_with_mapping(state, {}, mappings)

    return operation


def _declaration(text: str, name: str) -> CellDeclaration:
    declaration = cell_declaration(parse(text).values[EntityID(name)])
    assert declaration is not None
    return declaration


def _element(content: Any, index: int) -> Any:
    """An item of canonical tuple content."""

    assert isinstance(content, CanonicalNode) and content[1] == "tuple"
    return content[2][index]


def _merge_cells(state: State) -> TransformResult:
    a, b = EntityID("a"), EntityID("b")
    return transform_with_mapping(state, {}, {a: a, b: a}, conversions={a: "sum"})


def _split_cell(state: State) -> TransformResult:
    pair, left, right = EntityID("pair"), EntityID("left"), EntityID("right")
    half = "cell {}: int = 0\n"
    return transform_with_mapping(
        state,
        {
            left: _declaration(half.format("left"), "left"),
            right: _declaration(half.format("right"), "right"),
        },
        {pair: (left, right)},
        conversions={left: "first", right: "second"},
    )


def _upgrade_cell(state: State) -> TransformResult:
    n = EntityID("n")
    return transform_with_mapping(
        state,
        {n: _declaration("cell n: tuple = (0,)\n", "n")},
        {n: n},
        conversions={n: "wrap"},
    )


def _redefine_same(state: State) -> TransformResult:
    f = EntityID("f")
    function = function_at(state, f)
    assert function is not None
    return define(state, {f: function})


# ---------------------------------------------------------------------------
# The corpus
# ---------------------------------------------------------------------------

_DOUBLE = "fn double(x):\n    x * 2\n\n"

CASES: tuple[Case, ...] = (
    # -- declared: a host transformation with explicit mappings -------------
    Case(
        name="rename",
        group="declared",
        source=_DOUBLE + "fn quad(x):\n    double(double(x))\n",
        operation=_rename("double", "twice"),
        expect=Expect(
            kept=("node:double@", "node:double@0", "node:double@1", "node:quad@0.0"),
            changed=("node:quad@", "node:quad@0", "fn:quad"),
            at={"node:double@": "after:twice@"},
            merged={"fn:double": "fn:twice"},
        ),
        status="holds",
        note=(
            "Holds. The mapping `double -> twice` moves the nodes of `double` "
            "to `twice` with their EntityID and VersionID unchanged. `quad`, "
            "its two call nodes and its link follow the rename by endpoint "
            "continuity and get new versions; its `x` does not. `merged` here "
            "only reads the recorded mapping `double -> twice`."
        ),
    ),
    Case(
        name="delete_function",
        group="declared",
        source=(
            "fn used(x):\n    x + 1\n\n"
            "fn unused(x):\n    x * 2 + 1\n\n"
            "fn main(x):\n    used(x)\n"
        ),
        operation=_delete("unused"),
        expect=Expect(
            gone=(
                "fn:unused",
                "node:unused@",
                "node:unused@0",
                "node:unused@0.0",
                "node:unused@0.1",
                "node:unused@1",
            ),
            kept=("fn:used", "fn:main"),
        ),
        status="holds",
        note=(
            "Holds. The function maps to nothing and its five nodes go with it "
            "by the owned-subtree cascade, each recorded as a disappearance; "
            "the other functions keep their versions."
        ),
    ),
    Case(
        name="delete_called",
        group="declared",
        source="fn used(x):\n    x + 1\n\nfn main(x):\n    used(x)\n",
        operation=_delete("used"),
        expect=Expect(rejected=DanglingRelation),
        status="holds",
        note=(
            "Holds. The transformation itself raises DanglingRelation, because "
            "`main` still calls `used`; no activation is reached."
        ),
    ),
    Case(
        name="merge_cells",
        group="declared",
        source="cell a: int = 3\ncell b: int = 4\n",
        operation=_merge_cells,
        expect=Expect(
            merged={"cell:a": "cell:a", "cell:b": "cell:a"},
            kept=("cell:a",),
            cells={"cell:a": 30},
        ),
        converters={"sum": Converter(lambda sources: sum(sources.values()))},
        writes={"cell:a": 10, "cell:b": 20},
        status="holds",
        note=(
            "Holds. `a` and `b` map to `a`, and the converter sees the runtime "
            "content written before the activation (10 and 20), not the "
            "declared initial content. `a` keeps its version; `b` is removed by "
            "the mapping, which is a merge, not a disappearance."
        ),
    ),
    Case(
        name="split_cell",
        group="declared",
        source="cell pair: tuple = (3, 4)\n",
        operation=_split_cell,
        expect=Expect(
            split={"cell:pair": ("cell:left", "cell:right")},
            cells={"cell:left": 10, "cell:right": 20},
        ),
        converters={
            "first": Converter(lambda sources: _element(sources[EntityID("pair")], 0)),
            "second": Converter(lambda sources: _element(sources[EntityID("pair")], 1)),
        },
        writes={"cell:pair": (10, 20)},
        status="holds",
        note=(
            "Holds. `pair` maps to `left` and `right`, and each converter takes "
            "its half of the runtime tuple (10, 20). `pair` is removed as a "
            "mapped source that is not a destination."
        ),
    ),
    Case(
        name="upgrade_cell",
        group="declared",
        source="cell n: int = 7\n",
        operation=_upgrade_cell,
        expect=Expect(changed=("cell:n",), cells={"cell:n": (9,)}),
        converters={"wrap": Converter(lambda sources: (sources[EntityID("n")],))},
        writes={"cell:n": 9},
        status="holds",
        note=(
            "Holds. The cell keeps its EntityID and gets a new declaration, so "
            "a new VersionID; the converter turns the runtime content 9 into "
            "`(9,)`, which the tuple constraint accepts."
        ),
    ),
    Case(
        name="fold",
        group="declared",
        source=(
            "fn plain():\n    1 + 2\n\n"
            "fn nested(x):\n    x + (1 + 2)\n"
        ),
        operation=fold_constants,
        expect=Expect(
            changed=("node:plain@", "node:nested@1"),
            merged={
                "node:plain@": "after:plain@",
                "node:plain@0": "after:plain@",
                "node:plain@1": "after:plain@",
                "node:nested@1": "after:nested@1",
                "node:nested@1.0": "after:nested@1",
                "node:nested@1.1": "after:nested@1",
            },
            kept=("node:nested@", "node:nested@0"),
        ),
        status="holds",
        note=(
            "Holds. The root of a folded subtree keeps its EntityID and takes "
            "the literal, so it is changed; it and both operands are recorded "
            "as merged into it. The parent and `x` stay kept, since the parent "
            "still names the root."
        ),
    ),
    Case(
        name="activate_define",
        group="declared",
        source="cell hits: int = 0\n\nfn bump(x):\n    hits + x\n",
        operation=_redefine(
            "bump", "cell hits: int = 0\n\nfn bump(x):\n    hits + x * 2\n"
        ),
        expect=Expect(
            gone=("node:bump@", "node:bump@0", "node:bump@1"),
            new=(
                "after:bump@",
                "after:bump@0",
                "after:bump@1",
                "after:bump@1.0",
                "after:bump@1.1",
            ),
            changed=("fn:bump",),
            kept=("cell:hits",),
            cells={"cell:hits": 5},
        ),
        writes={"cell:hits": 5},
        status="holds",
        note=(
            "Holds. A whole-body `define` declares every old node of `bump` "
            "gone and creates the new ones (generation 1). The cell maps to "
            "itself and keeps its runtime content (5, written before the "
            "activation) instead of returning to its initial 0."
        ),
    ),
    # -- inferred: an edit that declares no continuity for what it touches --
    Case(
        name="leaf_replace",
        group="inferred",
        source="fn f(x):\n    x + label(one, 1)\n",
        operation=_edit(("f", "one", ("lit", 10))),
        expect=Expect(
            changed=("node:f@1",),
            kept=("node:f@", "node:f@0", "fn:f"),
        ),
        status="holds",
        note=(
            "Holds. A label edit keeps the labelled node's EntityID with new "
            "content; its parent, `x` and the function's own value keep their "
            "versions."
        ),
    ),
    Case(
        name="insert",
        group="inferred",
        source="fn f(a, b, c):\n    a + b\n",
        operation=_redefine("f", "fn f(a, b, c):\n    a + c + b\n"),
        expect=Expect(
            kept=("node:f@0", "node:f@1"),
            at={"node:f@0": "after:f@0.0", "node:f@1": "after:f@1"},
            new=("after:f@0", "after:f@0.1"),
        ),
        status="gap",
        note=(
            "Gap. `define` replaces the whole body: every old node maps to "
            "nothing and the new tree is created as `f/1.n`, so `a` and `b` are "
            "gone and come back as new nodes. Nothing matches the old tree "
            "against the new one. The expected `new` nodes are new only because "
            "everything is."
        ),
    ),
    Case(
        name="remove",
        group="inferred",
        source="fn f(a, b, c):\n    a + c + b\n",
        operation=_redefine("f", "fn f(a, b, c):\n    a + b\n"),
        expect=Expect(
            kept=("node:f@0.0", "node:f@1"),
            at={"node:f@0.0": "after:f@0", "node:f@1": "after:f@1"},
            gone=("node:f@0.1", "node:f@0"),
        ),
        status="gap",
        note=(
            "Gap, as insert: `a` and `b` disappear with the rest of the old "
            "body and the new `a` and `b` are new nodes."
        ),
    ),
    Case(
        name="wrap",
        group="inferred",
        source=_DOUBLE + "fn f(x):\n    x + double(1)\n",
        operation=_redefine("f", _DOUBLE + "fn f(x):\n    double(x) + double(1)\n"),
        expect=Expect(
            kept=("node:f@0",),
            at={"node:f@0": "after:f@0.0"},
            new=("after:f@0",),
        ),
        status="gap",
        note=(
            "Gap, as insert: the old `x` disappears and the `x` under the new "
            "call is a new node. (`f` already calls `double` elsewhere, because "
            "a new body resolves link names through the function's existing "
            "link table.)"
        ),
    ),
    Case(
        name="unwrap",
        group="inferred",
        source=_DOUBLE + "fn f(x):\n    double(x) + double(1)\n",
        operation=_redefine("f", _DOUBLE + "fn f(x):\n    x + double(1)\n"),
        expect=Expect(
            kept=("node:f@0.0",),
            at={"node:f@0.0": "after:f@0"},
            gone=("node:f@0",),
        ),
        status="gap",
        note=(
            "Gap, as insert: the old `x` and the call both disappear and the "
            "`x` left is a new node."
        ),
    ),
    Case(
        name="swap",
        group="inferred",
        source="fn f(a, b):\n    a - b\n",
        operation=_redefine("f", "fn f(a, b):\n    b - a\n"),
        expect=Expect(
            kept=("node:f@0", "node:f@1"),
            at={"node:f@0": "after:f@1", "node:f@1": "after:f@0"},
            changed=("node:f@",),
        ),
        status="gap",
        note=(
            "Gap, as insert: even the root `sub` disappears and comes back new, "
            "so `changed` fails too."
        ),
    ),
    Case(
        name="redefine_same",
        group="inferred",
        source="fn f(x):\n    x + 1\n",
        operation=_redefine_same,
        expect=Expect(kept=("node:f@", "node:f@0", "node:f@1")),
        status="gap",
        note=(
            "Gap. `define` with the function's own body (from `function_at`) "
            "still gives fresh nodes `f/1.n`: every old node disappears and an "
            "equal one is created, so an edit that changes nothing changes "
            "every identity."
        ),
    ),
    Case(
        name="shared_subtree",
        group="inferred",
        source="fn f(x):\n    (x + 1) * 2\n",
        operation=_redefine("f", "fn f(x):\n    (x + 1) * 3\n"),
        expect=Expect(kept=("node:f@0", "node:f@0.0", "node:f@0.1")),
        status="gap",
        note=(
            "Gap, as insert: the unchanged `x + 1` disappears and is created "
            "again."
        ),
    ),
    Case(
        name="ambiguous_duplicate",
        group="inferred",
        source="fn f(x):\n    x + x\n",
        operation=_redefine("f", "fn f(x):\n    x\n"),
        expect=Expect(
            new=("after:f@",),
            gone=("node:f@0", "node:f@1"),
        ),
        status="holds",
        note=(
            "Holds, vacuously: nothing is inferred today, so the remaining `x` "
            "is new because every node of a redefined body is. It must still "
            "hold once inference exists: two old nodes match, so neither may be "
            "kept."
        ),
    ),
    # -- competing: two transformations built from the same state -----------
    Case(
        name="rebase_disjoint",
        group="competing",
        source="fn f(x):\n    label(left, 1) + label(right, 2)\n",
        operation=_competing(
            ("f", "left", ("lit", 10)),
            ("f", "right", ("lit", 20)),
        ),
        expect=Expect(changed=("node:f@0", "node:f@1")),
        status="gap",
        note=(
            "Gap. The second result was built from the initial state, not the "
            "active one, so the runtime rejects it in either order "
            "(ActivationRejected: transformation does not start from the active "
            "state). Nothing re-bases a result onto a later state."
        ),
    ),
    Case(
        name="conflicting_edits",
        group="competing",
        source="fn f(x):\n    label(left, 1) + x\n",
        operation=_competing(
            ("f", "left", ("lit", 10)),
            ("f", "left", ("lit", 20)),
        ),
        expect=Expect(rejected=ActivationRejected),
        status="holds",
        note=(
            "Holds, but by the rule that fails rebase_disjoint: any second "
            "result from the same source is rejected as stale, conflicting or "
            "not. The case says nothing about detecting conflicts; a rebase "
            "that makes rebase_disjoint apply must keep this one rejected, for "
            "the right reason."
        ),
    ),
    # -- moved: a node changes its function ----------------------------------
    Case(
        name="extract_function",
        group="moved",
        source="fn f(x):\n    x * 2 + 1\n",
        operation=_reimport(
            "fn g(x):\n    x * 2\n\nfn f(x):\n    g(x) + 1\n"
        ),
        expect=Expect(
            kept=("node:f@0", "node:f@0.0", "node:f@0.1"),
            at={
                "node:f@0": "after:g@",
                "node:f@0.0": "after:g@0",
                "node:f@0.1": "after:g@1",
            },
            new=("after:f@0",),
        ),
        status="gap",
        note=(
            "Gap. No operation moves a node to another function; the closest is "
            "to import the edited program with no continuity declared. `g` and "
            "the call are new and nothing of `x * 2` is kept: `load` numbers "
            "nodes by function, generation and index, so the ids `f/0.n` come "
            "back on other nodes with new versions."
        ),
    ),
    Case(
        name="inline_function",
        group="moved",
        source="fn g(x):\n    x * 2\n\nfn f(x):\n    g(x) + 1\n",
        operation=_reimport("fn f(x):\n    x * 2 + 1\n"),
        expect=Expect(
            kept=("node:g@", "node:g@0", "node:g@1"),
            at={
                "node:g@": "after:f@0",
                "node:g@0": "after:f@0.0",
                "node:g@1": "after:f@0.1",
            },
            gone=("fn:g",),
        ),
        status="gap",
        note=(
            "Gap, as extract_function: no mapping is declared, so `g` is absent "
            "after without being recorded as a disappearance, and its body "
            "comes back as new nodes `f/0.n`."
        ),
    ),
)
