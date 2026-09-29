"""Cheap checks that documentation does not drift mechanically."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ROADMAP = DOCS / "roadmap.md"

MARKERS = {"Decided", "Provisional", "Open"}


def _markdown_files() -> list[Path]:
    return [ROOT / "README.md", *sorted(DOCS.glob("*.md"))]


def _slug(heading: str) -> str:
    """Approximate GitHub's heading anchor for the headings used here."""
    heading = re.sub(r"[^\w\s-]", "", heading.lower())
    return re.sub(r"[\s-]+", "-", heading).strip("-")


def _headings(path: Path) -> set[str]:
    headings = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.add(_slug(match.group(1)))
    return headings


class DocumentationCoherenceTests(unittest.TestCase):
    def test_no_merged_task_is_left_pr_pending(self):
        text = ROADMAP.read_text(encoding="utf-8")
        self.assertNotIn("#PR pending", text)

    def test_markdown_links_resolve(self):
        link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        errors = []

        for source in _markdown_files():
            text = source.read_text(encoding="utf-8")
            for raw_target in link_re.findall(text):
                if raw_target.startswith(
                    ("http://", "https://", "mailto:")
                ):
                    continue

                target, _, fragment = raw_target.partition("#")
                destination = (
                    source if not target else (source.parent / target).resolve()
                )

                if not destination.exists():
                    errors.append(
                        f"{source.relative_to(ROOT)}: missing {raw_target}"
                    )
                    continue

                if (
                    fragment
                    and destination.suffix == ".md"
                    and fragment not in _headings(destination)
                ):
                    errors.append(
                        f"{source.relative_to(ROOT)}: "
                        f"missing heading {raw_target}"
                    )

        self.assertFalse(
            errors,
            "Markdown link errors:\n" + "\n".join(errors),
        )

    def test_section_references_resolve(self):
        reference_re = re.compile(
            r"(?P<file>[A-Za-z0-9_./-]+\.md)\s+"
            r"(?:§|section\s+)(?P<section>\d+(?:\.\d+)*)",
            flags=re.IGNORECASE,
        )
        errors = []

        for source in _markdown_files():
            text = source.read_text(encoding="utf-8")
            for match in reference_re.finditer(text):
                target = (source.parent / match.group("file")).resolve()
                section = match.group("section")

                if not target.exists():
                    errors.append(
                        f"{source.relative_to(ROOT)}: "
                        f"missing {match.group('file')}"
                    )
                    continue

                headings = _headings(target)
                if not any(
                    heading == section
                    or heading.startswith(section + "-")
                    for heading in headings
                ):
                    errors.append(
                        f"{source.relative_to(ROOT)}: "
                        f"missing section {match.group(0)}"
                    )

        self.assertFalse(
            errors,
            "Section reference errors:\n" + "\n".join(errors),
        )

    def test_spec_documents_have_heading_and_section_markers(self):
        exempt = {
            "corpus.md",
            "continuity_corpus.md",
            "roadmap.md",
            "syntax_notes.md",
        }
        errors = []

        for path in sorted(DOCS.glob("*.md")):
            if path.name in exempt:
                continue

            lines = path.read_text(encoding="utf-8").splitlines()

            if not lines or not lines[0].startswith("# "):
                errors.append(f"{path.name}: missing top-level heading")

            section_indexes = [
                index
                for index, line in enumerate(lines)
                if re.match(r"^##\s+", line)
            ]

            for position, index in enumerate(section_indexes):
                next_section = (
                    section_indexes[position + 1]
                    if position + 1 < len(section_indexes)
                    else len(lines)
                )
                section = lines[index + 1 : next_section]
                markers = {
                    match.group(1)
                    for line in section
                    if (
                        match := re.fullmatch(
                            r"\*\*(Decided|Provisional|Open):\*\*",
                            line.strip(),
                        )
                    )
                }

                if not markers & MARKERS:
                    errors.append(
                        f"{path.name}: section {lines[index]!r} "
                        "has no Decided/Provisional/Open marker"
                    )

        self.assertFalse(
            errors,
            "Documentation coherence errors:\n" + "\n".join(errors),
        )


if __name__ == "__main__":
    unittest.main()
