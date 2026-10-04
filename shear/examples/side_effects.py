"""Side-effect-tagged canary programs (docs/corpus.md section 3)."""

from __future__ import annotations

from .. import CellContentRejected, CellDeclaration, EntityID, IntRange
from ..lang import Function, links
from . import Example, Raises, Step
from ._support import program


def _counter() -> Example:
    cell = EntityID("counter.cell")
    increment = EntityID("counter.increment")
    entities = {
        cell: CellDeclaration(IntRange(0, None), 0),
        increment: Function(
            (),
            ("write", "counter", ("add", ("read", "counter"), ("lit", 1))),
        ),
        EntityID("counter.increment.links"): links(increment, counter=cell),
    }

    return Example(
        name="counter",
        tags=frozenset({"side effects"}),
        program=program(entities),
        scenarios=(
            (
                Step(increment, (), 1, cells={cell: 1}),
                Step(increment, (), 2, cells={cell: 2}),
                Step(increment, (), 3, cells={cell: 3}),
            ),
        ),
        description="A cell that accumulates across calls.",
    )


def _account() -> Example:
    balance = EntityID("account.balance")
    deposit = EntityID("account.deposit")
    withdraw = EntityID("account.withdraw")
    balance_of = EntityID("account.balance_of")
    entities = {
        balance: CellDeclaration(IntRange(0, None), 0),
        deposit: Function(
            ("amount",),
            ("write", "balance", ("add", ("read", "balance"), ("arg", "amount"))),
        ),
        EntityID("account.deposit.links"): links(deposit, balance=balance),
        withdraw: Function(
            ("amount",),
            ("write", "balance", ("sub", ("read", "balance"), ("arg", "amount"))),
        ),
        EntityID("account.withdraw.links"): links(withdraw, balance=balance),
        balance_of: Function((), ("read", "balance")),
        EntityID("account.balance_of.links"): links(balance_of, balance=balance),
    }

    return Example(
        name="account",
        tags=frozenset({"side effects"}),
        program=program(entities),
        scenarios=(
            (
                Step(deposit, (100,), 100, cells={balance: 100}),
                Step(withdraw, (30,), 70, cells={balance: 70}),
                Step(withdraw, (1000,), Raises(CellContentRejected)),
                Step(balance_of, (), 70, cells={balance: 70}),
            ),
        ),
        description=(
            "A balance cell whose IntRange(0, None) constraint rejects an "
            "overdraft; the rejected withdrawal leaves the balance "
            "unchanged."
        ),
    )


EXAMPLES: tuple[Example, ...] = (
    _counter(),
    _account(),
)
