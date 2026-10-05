"""The recorded counts of the frozen candidate (`cb74cea`), read from the results report.

``STRUCT`` and ``REF`` are the record of the frozen candidate: revision 1 must
reproduce their per-observable counts exactly. The record is the "Counts per
observable and classification" table of the "Full report of the re-run
(`cb74cea`)" section of ``projection_results.md``, and the O5 rows of the same
section. Parsing fails closed: a missing section or a malformed row raises.
"""

from __future__ import annotations

from pathlib import Path

from core_projection.rows import CLASSIFICATIONS, Row

REPORT = Path(__file__).resolve().parents[2] / "docs/research/semantic-core/projection_results.md"
SECTION = "## Full report of the re-run (`cb74cea`)"
COUNTS_HEADING = "### Counts per observable and classification"
CHURN_HEADING = "### Version churn (O5)"
FROZEN_MODES = ("STRUCT", "REF")


def _section(text: str, heading: str, start: int = 0) -> str:
    begin = text.find(heading, start)

    if begin < 0:
        raise ValueError(f"results report has no {heading!r}")

    begin += len(heading)
    end = text.find("\n#", begin)

    return text[begin: end if end >= 0 else len(text)]


def _table(block: str) -> list[list[str]]:
    lines = [line for line in block.splitlines() if line.startswith("|")]

    if len(lines) < 3:
        raise ValueError("results report has an empty table")

    return [
        [cell.strip().replace("\\|", "|") for cell in line.strip().strip("|").split(" | ")]
        for line in lines[2:]
    ]


def _recorded(path: Path) -> tuple[str, int]:
    text = path.read_text()
    start = text.find(SECTION)

    if start < 0:
        raise ValueError(f"results report has no {SECTION!r}")

    return text, start


def recorded_counts(path: Path = REPORT) -> dict[tuple[str, str], int]:
    """(observable, classification) -> n for the frozen modes, as recorded."""

    text, start = _recorded(path)
    header = ["observable", *CLASSIFICATIONS, "total"]
    block = _section(text, COUNTS_HEADING, start)
    counts: dict[tuple[str, str], int] = {}

    for cells in _table(block):
        if len(cells) != len(header):
            raise ValueError(f"malformed counts row {cells!r}")

        observable = cells[0]

        if not any(f"/{mode}" in observable for mode in FROZEN_MODES):
            continue

        values = [int(c) for c in cells[1:-1]]

        if sum(values) != int(cells[-1]):
            raise ValueError(f"counts row {observable!r} does not add up")

        counts.update({(observable, c): v for c, v in zip(CLASSIFICATIONS, values) if v})

    if not counts:
        raise ValueError("no frozen-mode counts recorded")

    return counts


def recorded_churn(path: Path = REPORT) -> dict[tuple[str, str], tuple[str, str]]:
    """(case, observable) -> (main, candidate) wording of the O5 rows of the frozen modes."""

    text, start = _recorded(path)
    churn: dict[tuple[str, str], tuple[str, str]] = {}

    for cells in _table(_section(text, CHURN_HEADING, start)):
        case, observable, main, candidate = cells[:4]

        if any(f"/{mode}" in observable for mode in FROZEN_MODES):
            churn[(case, observable)] = (main, candidate)

    if not churn:
        raise ValueError("no O5 rows recorded")

    return churn


def live_counts(rows: list[Row]) -> dict[tuple[str, str], int]:
    """The same counts from a run, frozen modes only."""

    live: dict[tuple[str, str], int] = {}

    for row in rows:
        if any(f"/{mode}" in row.observable for mode in FROZEN_MODES):
            key = (row.observable, row.classification)
            live[key] = live.get(key, 0) + row.count

    return live


def live_churn(rows: list[Row]) -> dict[tuple[str, str], tuple[str, str]]:
    return {
        (row.case, row.observable): (row.main_result, row.candidate_result)
        for row in rows
        if row.observable.startswith("O5/")
        and any(f"/{mode}" in row.observable for mode in FROZEN_MODES)
    }


def differences(rows: list[Row], path: Path = REPORT) -> list[str]:
    """Every way a run's frozen-mode results differ from the record (empty: reproduced)."""

    found: list[str] = []
    recorded, live = recorded_counts(path), live_counts(rows)

    for key in sorted(set(recorded) | set(live)):
        if recorded.get(key, 0) != live.get(key, 0):
            found.append(
                f"{key[0]} / {key[1]}: recorded {recorded.get(key, 0)}, now {live.get(key, 0)}"
            )

    recorded_o5, live_o5 = recorded_churn(path), live_churn(rows)

    for key in sorted(set(recorded_o5) | set(live_o5)):
        if recorded_o5.get(key) != live_o5.get(key):
            found.append(f"{key[1]} ({key[0]}): recorded {recorded_o5.get(key)}, now {live_o5.get(key)}")

    return found
