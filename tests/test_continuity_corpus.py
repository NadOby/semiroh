"""Acceptance tests for the continuity corpus (docs/continuity_corpus.md)."""

import unittest

from semiroh import EntityID
from semiroh.continuity import CASES, GROUPS, Case, Expect, check
from semiroh.lang import define

REQUIRED = {
    # The operations the review named: rename, move, insert, delete,
    # split, merge, fold, activate, upgrade.
    "rename", "extract_function", "insert", "remove", "delete_function",
    "split_cell", "merge_cells", "fold", "activate_define", "upgrade_cell",
    # Inference and competing rewrites.
    "leaf_replace", "wrap", "unwrap", "swap", "redefine_same",
    "shared_subtree", "ambiguous_duplicate", "delete_called",
    "rebase_disjoint", "conflicting_edits", "inline_function",
}


class CorpusShapeTests(unittest.TestCase):
    def test_required_cases_and_groups(self) -> None:
        names = [case.name for case in CASES]
        name_set = set(names)
        case_groups = {case.group for case in CASES}
        expected_groups = set(GROUPS)
        errors = []

        duplicates = sorted(
            name
            for name in name_set
            if names.count(name) > 1
        )
        if duplicates:
            errors.append(
                "duplicate cases: " + ", ".join(duplicates)
            )

        missing = sorted(REQUIRED - name_set)
        if missing:
            errors.append(
                "missing required cases: " + ", ".join(missing)
            )

        missing_groups = sorted(expected_groups - case_groups)
        if missing_groups:
            errors.append(
                "missing groups: " + ", ".join(missing_groups)
            )

        unexpected_groups = sorted(case_groups - expected_groups)
        if unexpected_groups:
            errors.append(
                "unexpected groups: " + ", ".join(unexpected_groups)
            )

        for case in CASES:
            if case.status not in ("holds", "gap"):
                errors.append(
                    f"{case.name}: invalid status {case.status!r}"
                )
            if not case.note:
                errors.append(
                    f"{case.name}: missing note"
                )

        self.assertFalse(
            errors,
            "Continuity corpus shape errors:\n" + "\n".join(errors),
        )


class StatusTests(unittest.TestCase):
    def test_holding_cases_hold(self) -> None:
        for case in CASES:
            if case.status == "holds":
                with self.subTest(case=case.name):
                    self.assertEqual(check(case), ())

    def test_gaps_are_still_gaps(self) -> None:
        # A gap that closes fails here: flip its status to "holds".
        for case in CASES:
            if case.status == "gap":
                with self.subTest(case=case.name):
                    self.assertNotEqual(check(case), ())


class CheckContractTests(unittest.TestCase):
    SOURCE = "fn f(x):\n    label(step, 1) + x\n"

    def edit(self, state):
        return define(state, {(EntityID("f"), "step"): ("lit", 10)})

    def test_a_true_expectation_holds(self) -> None:
        case = Case(
            name="probe", group="inferred", source=self.SOURCE,
            operation=self.edit,
            expect=Expect(changed=("node:f@0",), kept=("node:f@1", "node:f@", "fn:f")),
            status="holds", note="leaf edit",
        )

        self.assertEqual(check(case), ())

    def test_a_false_expectation_is_reported_by_designator(self) -> None:
        case = Case(
            name="probe", group="inferred", source=self.SOURCE,
            operation=self.edit,
            expect=Expect(kept=("node:f@0",)),
            status="holds", note="wrong on purpose",
        )
        mismatches = check(case)

        self.assertTrue(mismatches)
        self.assertTrue(any("node:f@0" in mismatch for mismatch in mismatches))


if __name__ == "__main__":
    unittest.main()
