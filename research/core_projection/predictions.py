"""The predictions of revision plan section 3, checked against a run.

The table was recorded before the run and is not edited to fit it. Each claim
is a function of the run's rows; a claim that does not hold is reported as a
miss, and the rows that break it carry their own ``unexpected`` classification
(so every miss is also listed among the unexpected rows).

Adversarial cases 2 and 4 have no row of their own in the plan; they are
judged by the rows they fall under: case 2 by "contained cycles: none" and the
O1/O3 rows for ``factorial``, case 4 by "O4 agrees".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable

from core_projection.rows import AGREE, PREDICTED, UNEXPECTED, Row

NAMED = "NAMED"


@dataclass(frozen=True)
class Claim:
    observable: str
    prediction: str
    check: Callable[[list[Row]], tuple[bool, str]]


@dataclass(frozen=True)
class Verdict:
    observable: str
    prediction: str
    hit: bool
    detail: str


def _total(rows: Iterable[Row]) -> int:
    return sum(row.count for row in rows)


def _by_class(rows: Iterable[Row], classification: str) -> list[Row]:
    return [row for row in rows if row.classification == classification]


def _select(rows: list[Row], prefix: str, case: Callable[[str], bool] = lambda _: True) -> list[Row]:
    return [r for r in rows if r.observable.startswith(prefix) and case(r.case)]


def _all_agree(rows: list[Row], what: str) -> tuple[bool, str]:
    total = _total(rows)
    agree = _total(_by_class(rows, AGREE))

    if total == 0:
        return False, f"{what}: no rows (the claim was not exercised)"

    return agree == total, f"{agree} of {total} {what} agree"


def check_o0(rows: list[Row]) -> tuple[bool, str]:
    exact = _select(rows, f"O0/{NAMED}/exact")
    modulo = _select(rows, f"O0/{NAMED}/modulo-arity")
    struct = _select(rows, "O0/STRUCT/exact")
    arity_named = _total(_by_class(exact, PREDICTED))
    arity_struct = _total(_by_class(struct, PREDICTED))
    ok = (
        _total(_by_class(modulo, AGREE)) == _total(modulo) > 0
        and not _by_class(exact, UNEXPECTED)
        and arity_named == arity_struct
    )

    return ok, (
        f"modulo arity: {_total(_by_class(modulo, AGREE))} of {_total(modulo)} agree; "
        f"exact: {_total(_by_class(exact, UNEXPECTED))} unexpected, {arity_named} arity collapses "
        f"(STRUCT: {arity_struct})"
    )


def check_o1(rows: list[Row]) -> tuple[bool, str]:
    return _all_agree(_select(rows, f"O1/{NAMED}"), "entity pairs")


def check_o2(rows: list[Row]) -> tuple[bool, str]:
    return _all_agree(_select(rows, f"O2/{NAMED}"), "link targets")


def check_o3_same(rows: list[Row]) -> tuple[bool, str]:
    selected = _select(rows, f"O3/{NAMED}/built twice") + _select(rows, f"O3/{NAMED}/one literal changed")

    return _all_agree(selected, "state pairs")


def check_o3_renamed(rows: list[Row]) -> tuple[bool, str]:
    return _all_agree(_select(rows, f"O3/{NAMED}/renamed"), "renamed state pairs (not isomorphic, as main)")


def check_o4_chains(rows: list[Row]) -> tuple[bool, str]:
    selected = [
        r for r in _select(rows, "O4")
        if f"/{NAMED}" in r.observable and (r.case.startswith("chain:") or r.case.startswith("adversarial 4:"))
    ]

    return _all_agree(selected, "composed sources (real chains and adversarial 4)")


def _adversarial_3(rows: list[Row], marker: str) -> list[Row]:
    return [
        r for r in _select(rows, "O4") if f"/{NAMED}" in r.observable
        and r.case.startswith("adversarial 3:") and marker in r.case
    ]


def check_adv3_different(rows: list[Row]) -> tuple[bool, str]:
    selected = _adversarial_3(rows, "differently named")
    unknown = [r for r in selected if r.candidate_result == "Unknown"]
    ok, detail = _all_agree(selected, "sources")

    return ok and _total(unknown) == _total(selected), f"{detail}; {_total(unknown)} are Unknown"


def check_adv3_same(rows: list[Row]) -> tuple[bool, str]:
    selected = _adversarial_3(rows, "same naming")
    ok, detail = _all_agree(selected, "sources")
    varies = [r for r in selected if "varies" in r.candidate_result]

    return ok and not varies, f"{detail}; {_total(varies)} vary (no isomorphism is searched)"


def check_o5(rows: list[Row]) -> tuple[bool, str]:
    selected = _select(rows, f"O5/{NAMED}")
    counts = [
        int(re.match(r"(\d+) of", r.main_result).group(1)) for r in selected  # type: ignore[union-attr]
    ]
    ok, detail = _all_agree(selected, "scenarios")

    return ok and counts == [1, 1, 2], f"{detail}; VersionID changes in main: {counts}"


def check_c0(rows: list[Row]) -> tuple[bool, str]:
    selected = _select(rows, "C0/NAMED")
    cyclic = _total(_by_class(selected, UNEXPECTED))
    ok, detail = _all_agree(selected, "projected states")

    return ok and cyclic == 0, f"{detail}; {cyclic} with a contained cycle"


CLAIMS = (
    Claim("O0", "round trip exact modulo arity; arity collapse unchanged", check_o0),
    Claim("O1", "agrees with main on every pair, as REF did", check_o1),
    Claim("O2", "agrees", check_o2),
    Claim("O3 built twice / literal changed", "agrees", check_o3_same),
    Claim("O3 renamed (both orders)", "agrees with main: not isomorphic, names are fixed", check_o3_renamed),
    Claim("O4 shared and independent middle states", "agrees with main on every real chain", check_o4_chains),
    Claim("adversarial 3, differently named", "Unknown, as main", check_adv3_different),
    Claim("adversarial 3, symmetric with same naming", "agrees with main; no dependence on an isomorphism", check_adv3_same),
    Claim("O5, all three scenarios", "agrees with main (1, 1, 2)", check_o5),
    Claim("contained cycles in projected states", "none", check_c0),
)


def verdicts(rows: list[Row]) -> list[Verdict]:
    return [Verdict(c.observable, c.prediction, *c.check(rows)) for c in CLAIMS]
