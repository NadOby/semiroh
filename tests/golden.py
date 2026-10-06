"""Golden check of the language layer: base against head, nothing stored.

The recorder (``observe``) captures what the language layer does: for every
corpus program its StateID, its graph-form StateID, a digest of its rendered
text and of every node's bytecode chunk; for every continuity case its source
StateID and its check result; and the public names of the language modules.

``--against REF`` records the merge base of REF and HEAD (or, when HEAD is
REF's tip, the previous commit) in a temporary worktree with the base's own
recorder, records the working tree with this one, and compares the records:

- a new record passes and is printed in full;
- an unchanged record passes;
- a changed or removed record fails unless the branch intends it, and the
  old and new records are printed. A public API record changes only when a
  name disappears; new names pass and are printed.

Intended changes are lines this branch adds to ``tests/golden_changes.txt``:
one ``<group>/<name>`` per line (``programs/fold``, ``continuity/fold``,
``api/shear.lang``); blank lines and lines starting with ``#`` are ignored.
Lines already in the base are history and grant nothing. An added line whose
record did not change fails. A branch that changes this file's recorder fails
unless it adds a ``*`` line, which accepts and prints every difference; a
``*`` without a recorder change fails.

    python3 -m tests.golden --against main     # the check, as CI runs it
    python3 -m tests.golden --record           # this tree's records as JSON
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGES = "tests/golden_changes.txt"
RECORDER = "tests/golden.py"
GROUPS = ("programs", "continuity", "api")
API_MODULES = ("shear", "shear.lang", "shear.syntax", "shear.bytecode", "shear.machine")

# A base from before this file existed records with the retired module.
LEGACY_RECORDER = (
    "import json, sys\n"
    "from tests.test_language_golden import observe\n"
    "json.dump(observe(), sys.stdout, sort_keys=True)\n"
)


# -- The recorder ------------------------------------------------------------


def _digest(value: object) -> str:
    return hashlib.sha1(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _failure(exc: BaseException) -> str:
    return f"raises {type(exc).__name__}"


def _program(example) -> dict[str, str]:
    from shear import lang, syntax
    from shear.bytecode import chunk_of

    record = {"program": example.program.id.value}

    try:
        state = lang.load(example.program)
    except Exception as exc:  # recorded, so a changed failure shows too
        record["graph"] = _failure(exc)
        return record

    record["graph"] = state.id.value

    try:
        record["text"] = _digest(syntax.render_program(state))
    except Exception as exc:
        record["text"] = _failure(exc)

    chunks = []

    for entity in sorted(state.values, key=lambda e: e.value):
        if "/" in entity.value:
            try:
                chunks.append((entity.value, repr(chunk_of(state, entity))))
            except Exception as exc:
                chunks.append((entity.value, _failure(exc)))

    record["chunks"] = _digest(chunks)
    return record


def _api() -> dict[str, list[str]]:
    """Public names per language module: its ``__all__``, or else the names
    it defines itself (not names it merely imports)."""

    surface = {}

    for name in API_MODULES:
        module = importlib.import_module(name)
        names = getattr(module, "__all__", None)

        if names is None:
            names = [
                attr for attr in dir(module)
                if not attr.startswith("_")
                and not isinstance(getattr(module, attr), type(module))
                and getattr(getattr(module, attr), "__module__", name) == name
            ]

        surface[name] = sorted(names)

    return surface


def observe() -> dict[str, object]:
    from shear import continuity, examples, lang, syntax

    return {
        "programs": {example.name: _program(example) for example in examples.EXAMPLES},
        "continuity": {
            case.name: {
                "source": lang.load(syntax.parse(case.source)).id.value,
                "check": list(continuity.check(case)),
            }
            for case in continuity.CASES
        },
        "api": _api(),
    }


# -- The comparison ----------------------------------------------------------


def added_lines(base_text: str, head_text: str) -> list[str]:
    """Meaningful lines the head adds to the base text of the changes file."""

    old, new = base_text.splitlines(), head_text.splitlines()
    added = []

    for tag, _, _, j1, j2 in difflib.SequenceMatcher(a=old, b=new).get_opcodes():
        if tag in ("insert", "replace"):
            added += new[j1:j2]

    return [
        line.strip() for line in added
        if line.strip() and not line.strip().startswith("#")
    ]


def _show(value: object) -> str:
    return "\n".join(
        "    " + line
        for line in json.dumps(value, sort_keys=True, indent=1).splitlines()
    )


def compare(
    base: dict, head: dict, intended: list[str], recorder_changed: bool,
) -> tuple[list[str], list[str]]:
    """Return (report, failures) for two recordings."""

    star = "*" in intended
    keys = [line for line in intended if line != "*"]
    report: list[str] = []
    failures: list[str] = []
    changed: set[str] = set()
    counts = {"unchanged": 0, "new": 0}

    for group in GROUPS:
        old, new = base.get(group, {}), head.get(group, {})

        for name in sorted(set(old) | set(new)):
            key = f"{group}/{name}"

            if name not in old:
                counts["new"] += 1
                report.append(f"new {key}:\n{_show(new[name])}")
                continue

            if name not in new:
                verdict = "removed"
            elif group == "api":
                gained = sorted(set(new[name]) - set(old[name]))
                lost = sorted(set(old[name]) - set(new[name]))

                if gained:
                    changed.add(key)
                    report.append(f"new public names in {key}: {', '.join(gained)}")

                if not lost:
                    if not gained:
                        counts["unchanged"] += 1
                    continue

                verdict = f"lost public names {', '.join(lost)}"
            elif old[name] == new[name]:
                counts["unchanged"] += 1
                continue
            else:
                verdict = "changed"

            changed.add(key)
            detail = f"{key} {verdict}\n  old:\n{_show(old[name])}"

            if name in new:
                detail += f"\n  new:\n{_show(new[name])}"

            if star or key in keys:
                report.append(f"intended: {detail}")
            else:
                failures.append(f"{detail}\n  (not in lines this branch added to {CHANGES})")

    for key in keys:
        if key not in changed:
            failures.append(f"{CHANGES} adds {key!r}, but that record did not change")

    if recorder_changed and not star:
        failures.append(
            f"recorder changed: {RECORDER} differs from the base; add a '*' line "
            f"to {CHANGES} so that every difference is accepted and printed"
        )

    if star and not recorder_changed:
        failures.append(f"{CHANGES} adds '*', but the recorder did not change")

    summary = (
        f"{counts['unchanged']} unchanged, {counts['new']} new, "
        f"{len(changed)} changed, {len(failures)} failures"
    )

    return [summary, *report], failures


# -- Running it --------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _show_file(commit: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT, capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def base_commit(against: str) -> str:
    head = _git("rev-parse", "HEAD")
    base = _git("merge-base", against, "HEAD")
    return _git("rev-parse", "HEAD^") if base == head else base


def record(tree: Path, legacy: bool = False) -> dict:
    command = (
        [sys.executable, "-c", LEGACY_RECORDER]
        if legacy else [sys.executable, "-m", "tests.golden", "--record"]
    )
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    result = subprocess.run(
        command, cwd=tree, env=env, capture_output=True, text=True,
    )

    if result.returncode != 0:
        raise SystemExit(f"recording {tree} failed:\n{result.stderr}")

    return json.loads(result.stdout)


def check(against: str) -> int:
    base = base_commit(against)
    base_recorder = _show_file(base, RECORDER)
    head_recorder = (ROOT / RECORDER).read_text()
    changes = ROOT / CHANGES
    intended = added_lines(
        _show_file(base, CHANGES) or "",
        changes.read_text() if changes.exists() else "",
    )

    with tempfile.TemporaryDirectory() as scratch:
        tree = Path(scratch) / "base"
        _git("worktree", "add", "--detach", "--quiet", str(tree), base)

        try:
            old = record(tree, legacy=base_recorder is None)
        finally:
            _git("worktree", "remove", "--force", str(tree))

    new = record(ROOT)
    report, failures = compare(old, new, intended, base_recorder != head_recorder)

    print(f"golden check against {base[:12]} ({against})")

    for line in report:
        print(line)

    for line in failures:
        print(f"FAIL: {line}")

    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m tests.golden")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--against", metavar="REF", help="compare with the merge base of REF")
    mode.add_argument("--record", action="store_true", help="print this tree's records")
    args = parser.parse_args(argv)

    if args.record:
        json.dump(observe(), sys.stdout, sort_keys=True)
        return 0

    return check(args.against)


if __name__ == "__main__":
    raise SystemExit(main())
