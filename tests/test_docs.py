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

                with self.subTest(
                    source=source.relative_to(ROOT),
                    target=raw_target,
                ):
                    self.assertTrue(
                        destination.exists(),
                        f"{source.relative_to(ROOT)}: missing {raw_target}",
                    )
                    if fragment and destination.suffix == ".md":
                        self.assertIn(
                            fragment,
                            _headings(destination),
                            f"{source.relative_to(ROOT)}: "
                            f"missing heading {raw_target}",
                        )

    def test_section_references_resolve(self):
        reference_re = re.compile(
            r"(?P<file>[A-Za-z0-9_./-]+\.md)\s+"
            r"(?:§|section\s+)(?P<section>\d+(?:\.\d+)*)",
            flags=re.IGNORECASE,
        )

        for source in _markdown_files():
            text = source.read_text(encoding="utf-8")
            for match in reference_re.finditer(text):
                target = (source.parent / match.group("file")).resolve()
                section = match.group("section")

                with self.subTest(
                    source=source.relative_to(ROOT),
                    reference=match.group(0),
                ):
                    self.assertTrue(
                        target.exists(),
                        f"{source.relative_to(ROOT)}: "
                        f"missing {match.group('file')}",
                    )
                    headings = _headings(target)
                    self.assertTrue(
                        any(
                            heading == section
                            or heading.startswith(section + "-")
                            for heading in headings
                        ),
                        f"{source.relative_to(ROOT)}: "
                        f"missing section {match.group(0)}",
                    )

    def test_spec_documents_have_heading_and_section_markers(self):
        exempt = {
            "corpus.md",
            "continuity_corpus.md",
            "roadmap.md",
            "syntax_notes.md",
        }

        for path in sorted(DOCS.glob("*.md")):
            if path.name in exempt:
                continue

            lines = path.read_text(encoding="utf-8").splitlines()
            with self.subTest(path=path.name):
                self.assertTrue(
                    lines and lines[0].startswith("# "),
                    f"{path.name}: missing top-level heading",
                )

            section_indexes = [
                index
                for index, line in enumerate(lines)
                if re.match(r"^##+\s+", line)
            ]
            for index in section_indexes:
                next_section = next(
                    (
                        candidate
                        for candidate in section_indexes
                        if candidate > index
                    ),
                    len(lines),
                )
                section = lines[index + 1 : next_section]
                markers = {
                    match.group(1)
                    for line in section
                    if (
                        match := re.fullmatch(
                            r"\*\*(Decided|Provisional|Open)\.?\*\*",
                            line.strip(),
                        )
                    )
                }
                self.assertTrue(
                    markers & MARKERS,
                    f"{path.name}: section {lines[index]!r} "
                    "has no Decided/Provisional/Open marker",
                )


if __name__ == "__main__":
    unittest.main()
