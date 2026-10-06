"""The golden check's comparison rules (tests/golden.py), on planted records."""

from __future__ import annotations

import unittest

from tests.golden import compare, intended

BASE = {
    "programs": {"fold": {"graph": "g1"}, "gcd": {"graph": "g2"}},
    "continuity": {"fold": {"check": [True]}},
    "api": {"shear.lang": ["define", "load"]},
}


def _with(group: str, name: str, value: object) -> dict:
    head = {g: dict(records) for g, records in BASE.items()}

    if value is None:
        del head[group][name]
    else:
        head[group][name] = value

    return head


def _run(head: dict, intended=(), recorder_changed=False):
    return compare(BASE, head, list(intended), recorder_changed)


class ComparisonTests(unittest.TestCase):
    def test_identical_records_pass(self) -> None:
        report, failures = _run(BASE)

        self.assertEqual(failures, [])
        self.assertTrue(report[0].startswith("4 unchanged, 0 new, 0 changed"))

    def test_a_new_record_passes_and_is_printed_in_full(self) -> None:
        report, failures = _run(_with("programs", "lcm", {"graph": "g9"}))

        self.assertEqual(failures, [])
        self.assertTrue(any("new programs/lcm" in r and '"g9"' in r for r in report))

    def test_a_changed_record_fails_with_old_and_new(self) -> None:
        _, failures = _run(_with("programs", "gcd", {"graph": "g3"}))

        self.assertEqual(len(failures), 1)
        self.assertIn("programs/gcd changed", failures[0])
        self.assertIn('"g2"', failures[0])
        self.assertIn('"g3"', failures[0])

    def test_a_removed_record_fails(self) -> None:
        _, failures = _run(_with("programs", "gcd", None))

        self.assertEqual(len(failures), 1)
        self.assertIn("programs/gcd removed", failures[0])

    def test_an_added_line_makes_the_change_intended(self) -> None:
        head = _with("programs", "gcd", {"graph": "g3"})
        report, failures = _run(head, ["programs/gcd"])

        self.assertEqual(failures, [])
        self.assertTrue(any(r.startswith("intended: programs/gcd changed") for r in report))

    def test_a_line_names_one_group_only(self) -> None:
        head = _with("continuity", "fold", {"check": [False]})
        _, failures = _run(head, ["programs/fold"])

        self.assertTrue(any("continuity/fold changed" in f for f in failures))
        self.assertTrue(any("'programs/fold' is declared" in f for f in failures))

    def test_an_added_line_whose_record_did_not_change_fails(self) -> None:
        _, failures = _run(BASE, ["programs/gcd", "programs/missing"])

        self.assertEqual(len(failures), 2)
        self.assertTrue(all("did not change" in f for f in failures))


class ApiTests(unittest.TestCase):
    def test_new_public_names_pass_and_are_printed(self) -> None:
        head = _with("api", "shear.lang", ["define", "load", "run"])
        report, failures = _run(head)

        self.assertEqual(failures, [])
        self.assertTrue(any("new public names in api/shear.lang: run" in r for r in report))

    def test_a_lost_public_name_fails_unless_intended(self) -> None:
        head = _with("api", "shear.lang", ["load"])

        _, failures = _run(head)
        self.assertEqual(len(failures), 1)
        self.assertIn("lost public names define", failures[0])

        _, failures = _run(head, ["api/shear.lang"])
        self.assertEqual(failures, [])


class RecorderTests(unittest.TestCase):
    def test_a_changed_recorder_fails_without_a_star(self) -> None:
        _, failures = _run(BASE, recorder_changed=True)

        self.assertEqual(len(failures), 1)
        self.assertIn("recorder changed", failures[0])

    def test_a_star_accepts_and_prints_every_difference(self) -> None:
        head = _with("programs", "gcd", {"graph": "g3"})
        head["continuity"] = {}
        report, failures = _run(head, ["*"], recorder_changed=True)

        self.assertEqual(failures, [])
        self.assertTrue(any("intended: programs/gcd changed" in r for r in report))
        self.assertTrue(any("intended: continuity/fold removed" in r for r in report))

    def test_a_group_outside_the_schema_fails_in_base_or_head(self) -> None:
        extra = {**BASE, "effects": {"x": 1}}

        _, failures = compare(BASE, extra, [], False)
        self.assertEqual(len(failures), 1)
        self.assertIn("head recording has groups effects", failures[0])

        _, failures = compare(extra, BASE, [], False)
        self.assertEqual(len(failures), 1)
        self.assertIn("base recording has groups effects", failures[0])

    def test_a_star_does_not_excuse_an_unknown_group(self) -> None:
        _, failures = compare(BASE, {**BASE, "effects": {}}, ["*"], True)

        self.assertEqual(len(failures), 1)
        self.assertIn("effects", failures[0])

    def test_a_star_without_a_recorder_change_fails(self) -> None:
        _, failures = _run(BASE, ["*"])

        self.assertEqual(len(failures), 1)
        self.assertIn("recorder did not change", failures[0])


class DeclarationTests(unittest.TestCase):
    def test_only_files_new_in_the_branch_declare(self) -> None:
        base = {"GH-1.txt": "programs/gcd\n"}
        head = {**base, "GH-2.txt": "# why\n\nprograms/fold\n"}

        self.assertEqual(intended(base, head), (["programs/fold"], []))

    def test_an_earlier_declaration_grants_nothing_but_can_be_declared_again(self) -> None:
        base = {"GH-1.txt": "programs/gcd\n"}
        head = {**base, "GH-2.txt": "programs/gcd\n"}

        self.assertEqual(intended(base, head), (["programs/gcd"], []))
        self.assertEqual(intended(base, base), ([], []))

    def test_changing_or_deleting_history_fails(self) -> None:
        base = {"GH-1.txt": "programs/gcd\n"}

        ids, failures = intended(base, {"GH-1.txt": "programs/gcd\nprograms/fold\n"})
        self.assertEqual(ids, [])
        self.assertIn("is history and was changed", failures[0])

        ids, failures = intended(base, {})
        self.assertEqual(ids, [])
        self.assertIn("is history and was deleted", failures[0])

    def test_a_new_file_not_named_after_an_issue_fails_and_grants_nothing(self) -> None:
        for name in ("notes.txt", "GH-.txt", "GH-7.md", "gh-7.txt", "GH-7.txt.bak", "x/GH-7.txt"):
            with self.subTest(name=name):
                ids, failures = intended({}, {name: "programs/gcd\n"})

                self.assertEqual(ids, [])
                self.assertEqual(len(failures), 1)
                self.assertIn("not named after an issue", failures[0])

    def test_an_issue_named_file_declares(self) -> None:
        self.assertEqual(intended({}, {"GH-123.txt": "programs/gcd\n"}), (["programs/gcd"], []))

    def test_no_declarations_is_empty(self) -> None:
        self.assertEqual(intended({}, {}), ([], []))


if __name__ == "__main__":
    unittest.main()
