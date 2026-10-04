"""Golden behaviour of the language layer (roadmap task 19).

Task 19 restructures the language implementation without changing what it
does. ``tests/language_golden.json`` was recorded on main before the
restructuring: for every corpus program, its StateID, its graph-form
StateID, a digest of its rendered text and of every node's bytecode chunk;
for every continuity case, its source StateID and its check result; and the
public names of the language modules. A change to any of these is a change
of language behaviour, not a refactor.

Regenerate only for an intended behaviour change:

    python3 -m tests.test_language_golden --record
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
import unittest
from pathlib import Path

from shear import continuity, examples, lang, syntax
from shear.bytecode import chunk_of

GOLDEN = Path(__file__).with_name("language_golden.json")
API_MODULES = ("shear", "shear.lang", "shear.syntax", "shear.bytecode", "shear.machine")

# Public names removed on purpose, each with its reason.
REMOVED = {
    ("shear.bytecode", "run"):
        "task 19: bytecode no longer imports the machine; lang.run, the "
        "language's entry point, calls shear.machine.run directly",
}


def _digest(value: object) -> str:
    return hashlib.sha1(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _failure(exc: BaseException) -> str:
    return f"raises {type(exc).__name__}"


def _program(example: examples.Example) -> dict[str, str]:
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


class LanguageGoldenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.golden = json.loads(GOLDEN.read_text())
        self.observed = observe()

    def test_corpus_programs_keep_identity_text_and_bytecode(self) -> None:
        self.assertEqual(self.observed["programs"], self.golden["programs"])

    def test_continuity_cases_keep_their_sources_and_results(self) -> None:
        self.assertEqual(self.observed["continuity"], self.golden["continuity"])

    def test_no_public_name_of_a_language_module_disappears(self) -> None:
        for module, names in self.golden["api"].items():
            with self.subTest(module=module):
                missing = set(names) - set(self.observed["api"][module])
                missing -= {name for owner, name in REMOVED if owner == module}
                self.assertEqual(missing, set())


if __name__ == "__main__":
    if sys.argv[1:] == ["--record"]:
        GOLDEN.write_text(json.dumps(observe(), sort_keys=True, indent=1) + "\n")
    else:
        unittest.main()
