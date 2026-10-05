"""Adversarial cases (plan section 3.4) and the real two-step chains of O4.

Cases 1 and 2 are states run through the ordinary observables; case 3 and
case 4 are ``composition.Link``s. The chains are built with ``main``'s own
machinery (``lang.define`` edits and the continuity corpus's operations), so
the first step's destination is the second step's source in ``main``.
"""

from __future__ import annotations

from typing import Any, Callable

from shear.continuity import CASES, _DOUBLE, _delete, _edit, _redefine, _rename, _restate
from shear.fold import fold_constants
from shear.identity import EntityID
from shear.lang import load
from shear.relations import Relation
from shear.state import State
from shear.syntax import parse
from shear.transforms import TransformResult, transform_with_mapping
from shear.values import Value

from core_projection import observables
from core_projection.composition import Link, composition_rows, link_from_results
from core_projection.core import Atom
from core_projection.named import Name, Named
from core_projection.project import Mode, project
from core_projection.rows import AGREE, UNEXPECTED, Row

ADVERSARIAL_3 = (
    "adversarial 3 (main cannot join independently named middle states; "
    "the candidate joins them by isomorphism)"
)


def _state(contents: dict[str, Any]) -> State:
    return State.create({
        EntityID(name): Value.create(EntityID(name), content)
        for name, content in contents.items()
    })


def _mapping(spec: dict[str, tuple[str, ...]]) -> dict[EntityID, tuple[EntityID, ...]]:
    return {
        EntityID(source): tuple(EntityID(d) for d in destinations)
        for source, destinations in spec.items()
    }


# ---------------------------------------------------------------------------
# case 1: distinct referents with equal content
# ---------------------------------------------------------------------------


def two_referents_state() -> State:
    """``r1`` refers to ``x``, ``r2`` to ``y``; ``x`` and ``y`` have equal content."""

    x, y = EntityID("x"), EntityID("y")

    return State.create({
        x: Value.create(x, 5),
        y: Value.create(y, 5),
        EntityID("r1"): Value.create(EntityID("r1"), Relation("wraps", {"of": x})),
        EntityID("r2"): Value.create(EntityID("r2"), Relation("wraps", {"of": y})),
    })


def case_1_rows() -> list[Row]:
    state = two_referents_state()
    case = "adversarial 1: two referents with equal content"

    return observables.equality_rows(case, state) + observables.roundtrip_rows(case, state)


# ---------------------------------------------------------------------------
# case 2: recursion
# ---------------------------------------------------------------------------


def recursion_rows() -> list[Row]:
    """What each mode makes of a function that links to itself (``factorial``).

    The prediction is a cycle under ``STRUCT`` (the function's root occurrence
    is the target of its own ``link`` role), an ``EntityID`` atom under
    ``REF`` and, under ``NAMED``, a ``Named`` target to its own name with
    acyclic containment (plan section 3, "contained cycles: none"). The O1
    and O3 consequences are the ordinary rows for the same program.
    """

    from shear.examples import EXAMPLES

    program = load(next(e.program for e in EXAMPLES if e.name == "factorial"))
    case = "adversarial 2: factorial"
    function = EntityID("factorial")
    rows: list[Row] = []

    for mode in Mode:
        projection = project(program, mode)
        root = projection.view[function]

        if mode is Mode.NAMED:
            target = projection.nstate.roles(root)[f"link:{function.value}"][0]
            acyclic = projection.nstate.containment_cycle() is None
            predicted = acyclic and target == Named(Name(function.value))
            rows.append(Row(
                case, f"adv2/{mode.name}", "function links to itself by EntityID",
                f"{'Named' if isinstance(target, Named) else 'contained'} target "
                f"{target.name.value if isinstance(target, Named) else target.handle!r}; "
                f"containment {'acyclic' if acyclic else 'cyclic'}",
                AGREE if predicted else UNEXPECTED,
                "self-reference is a Named target to the function's own name, not a contained cycle"
                if predicted else "not a Named self-reference with acyclic containment",
            ))
            continue

        target = projection.cstate.roles(root)[f"link:{function.value}"][0]

        if mode is Mode.STRUCT:
            cycle = target == root
            word = f"self-loop: the link role of handle {root} targets handle {target}"
        else:
            atom = projection.cstate.atom(target)
            cycle = False
            word = f"nullary atom {atom.tag}:{atom.value!r}"

        predicted = cycle if mode is Mode.STRUCT else (
            projection.cstate.atom(target) == Atom("symbol", function.value)
        )
        rows.append(Row(
            case, f"adv2/{mode.name}", "function links to itself by EntityID", word,
            AGREE if predicted else UNEXPECTED,
            "matches the predicted representation" if predicted else "not the predicted representation",
        ))

    return rows


# ---------------------------------------------------------------------------
# case 3: independently built middle states
# ---------------------------------------------------------------------------


def case_3_links() -> list[Link]:
    start = _state({"p": 1, "q": 2})
    end = _state({"x": 3, "y": 4})
    first = _mapping({"p": ("a",), "q": ("b",)})
    symmetric = _state({"a": 7, "b": 7})
    symmetric_renamed = _state({"c": 7, "d": 7})
    control = _state({"a": 7, "b": 8})
    control_renamed = _state({"c": 7, "d": 8})
    through_cd = _mapping({"c": ("x",), "d": ("y",)})
    through_ab = _mapping({"a": ("x",), "b": ("y",)})

    return [
        Link(
            "adversarial 3: symmetric, differently named", start, symmetric,
            symmetric_renamed, end, first, through_cd, ADVERSARIAL_3,
        ),
        Link(
            "adversarial 3: asymmetric control, differently named", start, control,
            control_renamed, end, first, through_cd, ADVERSARIAL_3,
        ),
        Link(
            "adversarial 3: symmetric, same naming", start, symmetric,
            symmetric, end, first, through_ab,
        ),
        Link(
            "adversarial 3: asymmetric control, same naming", start, control,
            control, end, first, through_ab,
        ),
    ]


# ---------------------------------------------------------------------------
# case 4: composition cases
# ---------------------------------------------------------------------------


def _link(
    name: str,
    start: dict[str, int],
    middle: dict[str, int],
    end: dict[str, int],
    first: dict[str, tuple[str, ...]],
    second: dict[str, tuple[str, ...]],
) -> Link:
    middle_state = _state(middle)

    return Link(
        f"adversarial 4: {name}", _state(start), middle_state, middle_state,
        _state(end), _mapping(first), _mapping(second),
    )


def case_4_links() -> list[Link]:
    return [
        _link("chain", {"a": 1}, {"b": 2}, {"c": 3}, {"a": ("b",)}, {"b": ("c",)}),
        _link("disappearance", {"a": 1}, {"b": 2}, {"c": 3}, {"a": ()}, {"b": ("c",)}),
        _link(
            "unknown", {"a": 1, "z": 9}, {"b": 2, "z": 9}, {"c": 3, "z": 9},
            {"a": ("b",)}, {},
        ),
        _link(
            "split", {"a": 1}, {"b": 2, "c": 3}, {"d": 4, "e": 5},
            {"a": ("b", "c")}, {"b": ("d",), "c": ("e",)},
        ),
        _link(
            "split, one branch disappears", {"a": 1}, {"b": 2, "c": 3}, {"e": 5},
            {"a": ("b", "c")}, {"b": (), "c": ("e",)},
        ),
        _link(
            "split, one branch unknown", {"a": 1}, {"b": 2, "c": 3}, {"e": 5},
            {"a": ("b", "c")}, {"c": ("e",)},
        ),
        _link(
            "merge after split", {"a": 1}, {"b": 2, "c": 3}, {"d": 4},
            {"a": ("b", "c")}, {"b": ("d",), "c": ("d",)},
        ),
        _link(
            "merge", {"a": 1, "b": 2}, {"c": 3}, {"d": 4},
            {"a": ("c",), "b": ("c",)}, {"c": ("d",)},
        ),
    ]


# ---------------------------------------------------------------------------
# real chains
# ---------------------------------------------------------------------------

_USED = "fn used(x):\n    x + 1\n\n"
_UNUSED = "fn unused(x):\n    x * 2 + 1\n\n"
_MAIN = "fn main(x):\n    used(x)\n"


def _merge_halves(state: State) -> TransformResult:
    left, right = EntityID("left"), EntityID("right")

    return transform_with_mapping(state, {}, {left: left, right: left}, conversions={left: "sum"})


def _case(name: str) -> Callable[[State], Any]:
    return next(case for case in CASES if case.name == name).operation


# name -> (source program, first operation, second operation). The second is
# applied to the first's destination.
CHAIN_SPECS: dict[str, tuple[str, Callable[[State], Any], Callable[[State], Any]]] = {
    "rename, then rename": (
        _DOUBLE + "fn quad(x):\n    double(double(x))\n",
        _rename("double", "twice"),
        _rename("quad", "quad2"),
    ),
    "delete, then rename": (
        _USED + _UNUSED + _MAIN,
        _delete("unused"),
        _rename("main", "entry"),
    ),
    "delete, then redefine": (
        _USED + _UNUSED + _MAIN,
        _delete("unused"),
        _redefine("main", _USED + "fn main(x):\n    used(x) + 1\n"),
    ),
    "edit, then edit": (
        "fn f(x):\n    x + label(one, 1)\n",
        _edit(("f", "one", ("lit", 2))),
        _edit(("f", "one", ("add", ("lit", 1), ("lit", 1)))),
    ),
    "insert, then remove": (
        "fn f(a, b, c):\n    a + b\n",
        _redefine("f", "fn f(a, b, c):\n    a + b + c\n"),
        _redefine("f", "fn f(a, b, c):\n    a + c\n"),
    ),
    "fold, then rename": (
        "fn plain():\n    1 + 2\n\nfn nested(x):\n    x + (1 + 2)\n",
        fold_constants,
        _rename("nested", "nest"),
    ),
    "split a cell, then merge the halves": (
        "cell pair: tuple = (3, 4)\n",
        _case("split_cell"),
        _merge_halves,
    ),
    "extract a function, then inline it": (
        "fn f(x):\n    x * 2 + 1\n",
        _restate("fn g(x):\n    x * 2\n\nfn f(x):\n    g(x) + 1\n"),
        _restate("fn f(x):\n    x * 2 + 1\n", "g"),
    ),
}


def chain_links() -> list[Link]:
    links = []

    for name, (source, first, second) in CHAIN_SPECS.items():
        result = first(load(parse(source)))
        links.append(link_from_results(f"chain: {name}", result, second(result.destination)))

    return links


def composition_case_rows() -> list[Row]:
    rows: list[Row] = []

    for link in case_3_links() + case_4_links() + chain_links():
        rows += composition_rows(link, seed=sum(map(ord, link.name)))

    return rows


def all_rows() -> list[Row]:
    """Everything the adversarial cases produce, except the ordinary
    observables the runner applies to the corpus (and so to ``factorial``)."""

    return case_1_rows() + recursion_rows() + composition_case_rows()
