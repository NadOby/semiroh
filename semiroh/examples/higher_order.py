"""Higher-order canary programs (docs/corpus.md section 3, tier 2).

A function is passed as a reference, ``("ref", link)``, an ``EntityID`` that
``("apply", f, ...)`` calls (language_data.md section 3). A step may pass one
as an argument.
"""

from __future__ import annotations

from .. import CellDeclaration, EntityID, IsKind
from ..lang import Function, LanguageError, links
from . import Example, Raises, Step
from ._support import program


def _map() -> Example:
    map_ = EntityID("map")
    double = EntityID("double")
    square = EntityID("square")
    size = EntityID("size")
    f, t = ("arg", "f"), ("arg", "t")
    entities = {
        map_: Function(
            ("f", "t"),
            (
                "if",
                ("eq", ("len", t), ("lit", 0)),
                t,
                (
                    "concat",
                    ("tuple", ("apply", f, ("item", t, ("lit", 0)))),
                    (
                        "call",
                        "map",
                        f,
                        ("slice", t, ("lit", 1), ("len", t)),
                    ),
                ),
            ),
        ),
        EntityID("map.links"): links(map_, map=map_),
        double: Function(("x",), ("add", ("arg", "x"), ("arg", "x"))),
        square: Function(("x",), ("mul", ("arg", "x"), ("arg", "x"))),
        size: Function(("x",), ("len", ("arg", "x"))),
    }

    return Example(
        name="map",
        tags=frozenset({"data", "higher order"}),
        program=program(entities),
        scenarios=(
            (
                Step(map_, (double, (1, 2, 3)), (2, 4, 6)),
                Step(map_, (square, (1, 2, 3, 4)), (1, 4, 9, 16)),
                Step(map_, (size, ((1, 2), (), (3,))), (2, 0, 1)),
                Step(map_, (double, ()), ()),
                Step(map_, (5, (1,)), Raises(LanguageError)),
            ),
        ),
        description=(
            "map(f, t) applies the function f refers to to every element "
            "of t; the step passes double, square and size as references. "
            "Applying something that is not a function reference raises."
        ),
    )


def _fold() -> Example:
    fold = EntityID("fold")
    plus = EntityID("plus")
    times = EntityID("times")
    minus = EntityID("minus")
    f, acc, t = ("arg", "f"), ("arg", "acc"), ("arg", "t")
    a, b = ("arg", "a"), ("arg", "b")
    entities = {
        # A left fold, and a tail call: the accumulator carries the result.
        fold: Function(
            ("f", "acc", "t"),
            (
                "if",
                ("eq", ("len", t), ("lit", 0)),
                acc,
                (
                    "call",
                    "fold",
                    f,
                    ("apply", f, acc, ("item", t, ("lit", 0))),
                    ("slice", t, ("lit", 1), ("len", t)),
                ),
            ),
        ),
        EntityID("fold.links"): links(fold, fold=fold),
        plus: Function(("a", "b"), ("add", a, b)),
        times: Function(("a", "b"), ("mul", a, b)),
        minus: Function(("a", "b"), ("sub", a, b)),
    }

    return Example(
        name="fold",
        tags=frozenset({"data", "higher order"}),
        program=program(entities),
        scenarios=(
            (
                Step(fold, (plus, 0, (1, 2, 3, 4)), 10),
                Step(fold, (times, 1, (1, 2, 3, 4, 5)), 120),
                Step(fold, (minus, 0, (1, 2, 3)), -6),
                Step(fold, (plus, 7, ()), 7),
                Step(fold, (plus, 0, tuple(range(1500))), 1124250),
            ),
        ),
        description=(
            "fold(f, acc, t) combines the elements of t into acc from the "
            "left. minus shows the order: ((0 - 1) - 2) - 3. The last step "
            "folds 1500 elements, deeper than the interpreter's stack "
            "allows without tail calls."
        ),
    )


def _sort_swap() -> Example:
    data = EntityID("data")
    order = EntityID("order")
    insert_by = EntityID("insert_by")
    sort_by = EntityID("sort_by")
    sort_data = EntityID("sort_data")
    swap_order = EntityID("swap_order")
    before, x, s = ("arg", "before"), ("arg", "x"), ("arg", "s")
    t, rest = ("arg", "t"), ("arg", "rest")
    entities = {
        data: CellDeclaration(IsKind("tuple"), (3, 1, 4, 1, 5, 9, 2, 6)),
        # The ordering the sort uses; swap_order installs another.
        order: Function(("a", "b"), ("lt", ("arg", "a"), ("arg", "b"))),
        insert_by: Function(
            ("before", "x", "s"),
            (
                "if",
                ("eq", ("len", s), ("lit", 0)),
                ("tuple", x),
                (
                    "if",
                    ("apply", before, x, ("item", s, ("lit", 0))),
                    ("concat", ("tuple", x), s),
                    (
                        "concat",
                        ("tuple", ("item", s, ("lit", 0))),
                        (
                            "call",
                            "insert_by",
                            before,
                            x,
                            ("slice", s, ("lit", 1), ("len", s)),
                        ),
                    ),
                ),
            ),
        ),
        EntityID("insert_by.links"): links(insert_by, insert_by=insert_by),
        sort_by: Function(
            ("before", "t"),
            (
                "if",
                ("eq", ("len", t), ("lit", 0)),
                t,
                (
                    "let",
                    "rest",
                    ("slice", t, ("lit", 1), ("len", t)),
                    (
                        "call",
                        "insert_by",
                        before,
                        ("item", t, ("lit", 0)),
                        ("call", "sort_by", before, rest),
                    ),
                ),
            ),
        ),
        EntityID("sort_by.links"): links(
            sort_by,
            insert_by=insert_by,
            sort_by=sort_by,
        ),
        sort_data: Function(
            (),
            (
                "write",
                "data",
                ("call", "sort_by", ("ref", "order"), ("read", "data")),
            ),
        ),
        EntityID("sort_data.links"): links(
            sort_data,
            data=data,
            order=order,
            sort_by=sort_by,
        ),
        swap_order: Function(
            (),
            (
                "activate",
                "order",
                (
                    "function",
                    ("lit", ("a", "b")),
                    ("lit", ("lt", ("arg", "b"), ("arg", "a"))),
                ),
            ),
        ),
        EntityID("swap_order.links"): links(swap_order, order=order),
    }
    ascending = (1, 1, 2, 3, 4, 5, 6, 9)
    descending = (9, 6, 5, 4, 3, 2, 1, 1)

    return Example(
        name="sort_swap",
        tags=frozenset({"data", "higher order", "self-modification"}),
        program=program(entities),
        scenarios=(
            (
                Step(sort_data, (), ascending, cells={data: ascending}),
                Step(swap_order, (), None, may_activate=True, cells={data: ascending}),
                Step(sort_data, (), descending, cells={data: descending}),
            ),
        ),
        description=(
            "sort_data sorts the tuple in a cell with the function that "
            "order refers to. swap_order activates a different order "
            "between two runs; the data stays in its cell, and the next "
            "sort_data uses the new ordering."
        ),
    )


EXAMPLES: tuple[Example, ...] = (
    _map(),
    _fold(),
    _sort_swap(),
)
