"""Result rows shared by the observables (plan section 3.3).

A ``Row`` records one comparison of a ``main`` result with the candidate's.
Observables emit one row per compared item and ``aggregate`` folds identical
rows into one with a count and a few examples, so a report stays readable
when a state has a million entity pairs. The count and examples are an
addition to the plan's row shape.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

AGREE = "agree"
PREDICTED = "predicted mismatch"
UNEXPECTED = "unexpected mismatch"
GAP = "gap"

CLASSIFICATIONS = (AGREE, PREDICTED, UNEXPECTED, GAP)

MAX_EXAMPLES = 3


@dataclass(frozen=True)
class Row:
    """One compared item (or, after ``aggregate``, ``count`` identical ones)."""

    case: str
    observable: str
    main_result: str
    candidate_result: str
    classification: str
    note: str = ""
    count: int = 1
    examples: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.classification not in CLASSIFICATIONS:
            raise ValueError(f"unknown classification {self.classification!r}")

        if self.count < 1:
            raise ValueError("a row stands for at least one item")

    @property
    def key(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.case,
            self.observable,
            self.main_result,
            self.candidate_result,
            self.classification,
            self.note,
        )


def aggregate(rows: Iterable[Row], max_examples: int = MAX_EXAMPLES) -> list[Row]:
    """Fold rows with the same key into one, keeping first-seen order."""

    folded: dict[tuple[str, ...], Row] = {}

    for row in rows:
        previous = folded.get(row.key)

        if previous is None:
            folded[row.key] = replace(row, examples=row.examples[:max_examples])
            continue

        room = max_examples - len(previous.examples)
        folded[row.key] = replace(
            previous,
            count=previous.count + row.count,
            examples=previous.examples + row.examples[: max(room, 0)],
        )

    return list(folded.values())


def counts(rows: Iterable[Row]) -> dict[tuple[str, str], int]:
    """Items per (observable, classification)."""

    result: dict[tuple[str, str], int] = {}

    for row in rows:
        key = (row.observable, row.classification)
        result[key] = result.get(key, 0) + row.count

    return result
