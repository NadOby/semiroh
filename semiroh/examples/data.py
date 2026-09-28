"""Data-tagged canary programs (docs/corpus.md section 3, tier 2)."""

from __future__ import annotations

from .. import CellDeclaration, EntityID, IntRange
from ..lang import Function, LanguageError, links
from . import Example, Raises, Step
from ._support import program


def _insertion_sort() -> Example:
    insert = EntityID("insert")
    sort = EntityID("insertion_sort")
    t = ("arg", "t")
    x = ("arg", "x")
    sorted_ = ("arg", "sorted")
    entities = {
        insert: Function(
            ("x", "sorted"),
            (
                "if",
                ("eq", ("len", sorted_), ("lit", 0)),
                ("tuple", x),
                (
                    "if",
                    ("lt", x, ("item", sorted_, ("lit", 0))),
                    ("concat", ("tuple", x), sorted_),
                    (
                        "concat",
                        ("tuple", ("item", sorted_, ("lit", 0))),
                        (
                            "call",
                            "insert",
                            x,
                            ("slice", sorted_, ("lit", 1), ("len", sorted_)),
                        ),
                    ),
                ),
            ),
        ),
        EntityID("insert.links"): links(insert, insert=insert),
        sort: Function(
            ("t",),
            (
                "if",
                ("eq", ("len", t), ("lit", 0)),
                t,
                (
                    "call",
                    "insert",
                    ("item", t, ("lit", 0)),
                    (
                        "call",
                        "insertion_sort",
                        ("slice", t, ("lit", 1), ("len", t)),
                    ),
                ),
            ),
        ),
        EntityID("insertion_sort.links"): links(
            sort,
            insert=insert,
            insertion_sort=sort,
        ),
    }

    return Example(
        name="insertion_sort",
        tags=frozenset({"data"}),
        program=program(entities),
        scenarios=(
            (
                Step(insert, (3, (1, 2, 4, 5)), (1, 2, 3, 4, 5)),
                Step(sort, ((),), ()),
                Step(sort, ((7,),), (7,)),
                Step(sort, ((3, 1, 2),), (1, 2, 3)),
                Step(sort, ((5, 2, 4, 6, 1, 3),), (1, 2, 3, 4, 5, 6)),
                Step(sort, ((4, 3, 2, 1),), (1, 2, 3, 4)),
                Step(sort, ((2, 1, 2, 1, -3, 0),), (-3, 0, 1, 1, 2, 2)),
            ),
        ),
        description=(
            "Insertion sort of a tuple of ints of unknown length: insert "
            "puts one element into a sorted tuple, and the sort inserts the "
            "head into the sorted tail. Walks the data with len, item, "
            "slice and concat."
        ),
    )


def _let_bindings() -> Example:
    counter = EntityID("counter")
    roots = EntityID("real_roots")
    bump_twice = EntityID("bump_twice")
    shadow = EntityID("shadow")
    a, b, c, d = ("arg", "a"), ("arg", "b"), ("arg", "c"), ("arg", "d")
    entities = {
        counter: CellDeclaration(IntRange(0, 100), 0),
        # The number of real roots of a*x^2 + b*x + c: the discriminant is
        # named once and read three times.
        roots: Function(
            ("a", "b", "c"),
            (
                "let",
                "ac",
                ("mul", a, c),
                (
                    "let",
                    "d",
                    (
                        "sub",
                        ("mul", b, b),
                        ("mul", ("lit", 4), ("arg", "ac")),
                    ),
                    (
                        "if",
                        ("lt", d, ("lit", 0)),
                        ("lit", 0),
                        ("if", ("eq", d, ("lit", 0)), ("lit", 1), ("lit", 2)),
                    ),
                ),
            ),
        ),
        # The bound value is evaluated once: the write happens once, and
        # both reads of v see what it returned.
        bump_twice: Function(
            (),
            (
                "let",
                "v",
                ("write", "counter", ("add", ("read", "counter"), ("lit", 1))),
                ("add", ("arg", "v"), ("arg", "v")),
            ),
        ),
        EntityID("bump_twice.links"): links(bump_twice, counter=counter),
        # A name already in scope is an ambiguity, not a shadow.
        shadow: Function(("x",), ("let", "x", ("lit", 1), ("arg", "x"))),
    }

    return Example(
        name="let_bindings",
        tags=frozenset({"data", "side effects"}),
        program=program(entities),
        scenarios=(
            (
                Step(roots, (1, 0, 1), 0),
                Step(roots, (1, 2, 1), 1),
                Step(roots, (1, 3, 2), 2),
                Step(roots, (2, -3, 1), 2),
                Step(bump_twice, (), 2, cells={counter: 1}),
                Step(bump_twice, (), 4, cells={counter: 2}),
                Step(shadow, (5,), Raises(LanguageError)),
            ),
        ),
        description=(
            "let names an intermediate value: the discriminant of a "
            "quadratic is computed once and used three times, and a "
            "side-effecting bound expression runs exactly once. A let that "
            "reuses a parameter's name is rejected."
        ),
    )


EXAMPLES: tuple[Example, ...] = (
    _insertion_sort(),
    _let_bindings(),
)
