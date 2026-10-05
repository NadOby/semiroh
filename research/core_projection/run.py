"""Run the projection experiment and print a Markdown report (plan section 3.5).

    PYTHONPATH=research python3 -m core_projection.run

Every corpus program, every continuity-corpus case (its source and the
destination of its operation) and the adversarial cases go through the
observables in both modes. Mismatches are results: the exit status is zero
unless the run crashes.
"""

from __future__ import annotations

import sys
from collections import Counter
from typing import Iterable

from shear.continuity import CASES
from shear.examples import EXAMPLES
from shear.lang import load
from shear.state import State
from shear.syntax import parse

from core_projection import adversarial, churn, identity, observables
from core_projection.rows import AGREE, CLASSIFICATIONS, Row, aggregate, counts


def state_rows(case: str, state: State, twin: State | None = None) -> list[Row]:
    """O0 to O3 for one state."""

    return aggregate(
        observables.roundtrip_rows(case, state)
        + observables.equality_rows(case, state)
        + observables.link_rows(case, state)
        + identity.identity_rows(case, state, twin)
    )


def collect(limit: int | None = None) -> list[Row]:
    """All rows. ``limit`` keeps only the first programs and cases (for tests)."""

    rows: list[Row] = []

    for example in EXAMPLES[:limit]:
        rows += state_rows(
            f"corpus: {example.name}", load(example.program), load(example.program)
        )

    for case in CASES[:limit]:
        source = load(parse(case.source))
        rows += state_rows(f"continuity: {case.name} (source)", source, load(parse(case.source)))

        if case.expect.rejected is not None:
            continue  # the operation or its activation raises: no destination to project

        result = case.operation(source)

        results = result if isinstance(result, tuple) else (result,)

        for index, item in enumerate(results):
            suffix = f" {index + 1}" if len(results) > 1 else ""
            rows += state_rows(f"continuity: {case.name} (destination{suffix})", item.destination)

    rows += aggregate(adversarial.all_rows())
    rows += churn.churn_rows()

    return rows


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _table(header: tuple[str, ...], body: Iterable[tuple[str, ...]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(_cell(str(c)) for c in row) + " |" for row in body]

    return lines


def _row_cells(row: Row) -> tuple[str, ...]:
    return (
        row.case, row.observable, row.main_result, row.candidate_result,
        row.classification, str(row.count), row.note, "; ".join(row.examples),
    )


ROW_HEADER = ("case", "observable", "main", "candidate", "classification", "n", "note", "examples")


def render(rows: list[Row]) -> str:
    """The report: counts, every non-agree row, case 2, case 3 and O5."""

    totals = counts(rows)
    observable_names = sorted({name for name, _ in totals})
    lines = ["# Projection experiment report", "", "## Counts per observable and classification", ""]
    lines += _table(
        ("observable", *CLASSIFICATIONS, "total"),
        (
            (
                name,
                *(str(totals.get((name, c), 0)) for c in CLASSIFICATIONS),
                str(sum(totals.get((name, c), 0) for c in CLASSIFICATIONS)),
            )
            for name in observable_names
        ),
    )
    overall = Counter()

    for (_, classification), n in totals.items():
        overall[classification] += n

    lines += ["", "Overall: " + ", ".join(f"{c} {overall[c]}" for c in CLASSIFICATIONS), ""]

    lines += ["## Every row that is not agree", ""]
    lines += _table(ROW_HEADER, (_row_cells(r) for r in rows if r.classification != AGREE))

    lines += ["", "## Adversarial case 2: recursion (factorial)", ""]
    lines += _table(ROW_HEADER, (_row_cells(r) for r in rows if r.case == "adversarial 2: factorial"))
    lines += ["", "Consequences for equality (O1) and identity (O3), counted over the factorial program:", ""]
    factorial = [r for r in rows if r.case == "corpus: factorial" and r.observable[:2] in ("O1", "O3")]
    lines += _table(
        ("observable", "classification", "n"),
        sorted((name, c, str(n)) for (name, c), n in counts(factorial).items()),
    )

    lines += ["", "## Composition (O4): outcomes by kind", ""]
    kinds = Counter()

    for r in rows:
        if r.observable.startswith("O4"):
            kinds[(r.observable[:3], r.main_result, r.candidate_result, r.classification)] += r.count

    lines += _table(
        ("variant", "main", "candidate", "classification", "n"),
        ((v, m, c, k, str(n)) for (v, m, c, k), n in sorted(kinds.items())),
    )

    lines += ["", "## Version churn (O5)", ""]
    lines += _table(ROW_HEADER, (_row_cells(r) for r in rows if r.observable.startswith("O5")))
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    print(render(collect()))

    return 0


if __name__ == "__main__":
    sys.exit(main())
