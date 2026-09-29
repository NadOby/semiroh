"""Unit tests for the continuity corpus machinery (docs/continuity_corpus.md):
how designators resolve, and what `check` reports for each kind of expectation.
"""

import unittest
from dataclasses import replace
from typing import Iterator

from semiroh import DanglingRelation, EntityID, State
from semiroh.continuity import (
    CASES,
    Case,
    DesignatorError,
    Expect,
    check,
    resolve,
)
from semiroh.examples import EXAMPLES
from semiroh.lang import Function, define, load
from semiroh.relations import relation_of
from semiroh.runtime import ActivationRejected
from semiroh.syntax import parse
from semiroh.transforms import TransformResult, transform_with_mapping

F = EntityID("f")


def state_of(text: str) -> State:
    return load(parse(text))


def kind_of(state: State, designator: str) -> str:
    node = relation_of(state.values[resolve(designator, state, state)])
    assert node is not None
    return node.kind


def by_name(name: str) -> Case:
    return next(case for case in CASES if case.name == name)


ORDER = """\
cell c: int = 0

fn g(a):
    a

fn f(x):
    let y = g(x)
    c = y
    if y < 1:
        g(y)
    else:
        x
"""


class PathTests(unittest.TestCase):
    def test_a_path_counts_input_form_operands_from_the_body_root(self) -> None:
        state = state_of("fn f(x):\n    (x + 1) * 2\n")

        kinds = {
            "": "mul",
            "0": "add",
            "0.0": "arg",
            "0.1": "lit",
            "1": "lit",
        }

        for path, kind in kinds.items():
            with self.subTest(path=path):
                self.assertEqual(kind_of(state, f"node:f@{path}"), kind)

        # Numbered in preorder, so the path order is the id order.
        self.assertEqual(resolve("node:f@", state), EntityID("f/0.0"))
        self.assertEqual(resolve("node:f@0.1", state), EntityID("f/0.3"))
        self.assertEqual(resolve("node:f@1", state), EntityID("f/0.4"))

    def test_operands_skip_link_names_targets_and_cells(self) -> None:
        state = state_of(ORDER)

        kinds = {
            "": "let",
            "0": "call",  # let: value, then body
            "0.0": "arg",  # a call's operands are its arguments only
            "1": "seq",
            "1.0": "write",  # a write's operand is its value, not the cell
            "1.0.0": "arg",
            "1.1": "if",
            "1.1.0": "lt",  # if: cond, then, else
            "1.1.0.0": "arg",
            "1.1.0.1": "lit",
            "1.1.1": "call",
            "1.1.1.0": "arg",
            "1.1.2": "arg",
        }

        for path, kind in kinds.items():
            with self.subTest(path=path):
                self.assertEqual(kind_of(state, f"node:f@{path}"), kind)

        with self.assertRaises(DesignatorError):
            resolve("node:f@0.1", state)

    def test_a_label_is_transparent(self) -> None:
        plain = state_of("fn f(x):\n    (x + 1) * 2\n")
        labelled = state_of(
            "fn f(x):\n    label(top, label(sum, x + 1) * label(two, 2))\n"
        )
        definition = relation_of(labelled.values[F])
        assert definition is not None

        for path in ("", "0", "0.0", "0.1", "1"):
            with self.subTest(path=path):
                self.assertEqual(
                    resolve(f"node:f@{path}", labelled),
                    resolve(f"node:f@{path}", plain),
                )

        self.assertEqual(resolve("node:f@", labelled), definition.roles["label:top"])
        self.assertEqual(resolve("node:f@0", labelled), definition.roles["label:sum"])
        self.assertEqual(resolve("node:f@1", labelled), definition.roles["label:two"])

    def test_fn_and_cell_designators_name_an_entity_by_string(self) -> None:
        state = state_of(ORDER)

        self.assertEqual(resolve("fn:f", state), F)
        self.assertEqual(resolve("cell:c", state), EntityID("c"))
        # Naming is not looking up: whether it is there is for `check`.
        self.assertEqual(resolve("fn:absent", state), EntityID("absent"))

    def test_before_and_after_designators_resolve_in_their_own_state(self) -> None:
        before = state_of("fn f(x):\n    x + label(one, 1)\n")

        whole = define(before, {F: Function(("x",), ("lit", 0))}).destination
        leaf = define(before, {(F, "one"): ("lit", 10)}).destination

        old, new = resolve("node:f@", before, whole), resolve("after:f@", before, whole)
        self.assertNotEqual(old, new)
        self.assertIn(old, before.values)
        self.assertNotIn(old, whole.values)
        self.assertIn(new, whole.values)
        self.assertNotIn(new, before.values)

        # A label edit keeps the labelled node: the same entity at both.
        self.assertEqual(
            resolve("node:f@1", before, leaf), resolve("after:f@1", before, leaf)
        )

    def test_a_node_is_at_a_path_only_under_its_owner(self) -> None:
        # "Now owned by g" (extract_function) is part of what a designator
        # says: the node at f's path must be one that f owns.
        state = state_of("fn f(x):\n    x + 1\n\nfn g(x):\n    x\n")
        root = resolve("node:f@", state)
        ownership = {
            owner: list(state.owned_children(owner))
            for owner in state.values
            if state.owned_children(owner)
        }
        ownership[F].remove(root)
        ownership[EntityID("g")].append(root)
        moved = transform_with_mapping(
            state,
            {},
            {entity: entity for entity in state.values},
            ownership=ownership,
        ).destination

        self.assertEqual(resolve("node:g@", moved), EntityID("g/0.0"))

        with self.assertRaises(DesignatorError):
            resolve("node:f@", moved)

    def test_a_designator_that_names_nothing_is_an_error(self) -> None:
        state = state_of("cell c: int = 0\n\nfn f(x):\n    (x + 1) * c\n")
        bad = [
            "", "f", "fn", "fn:", "cell:", "node:f", "node:@", "node:@0",
            "after:f", "thing:f@",
            "node:nope@",      # no such function
            "node:c@",         # a cell is not a function
            "node:f@9",        # past the operands
            "node:f@1.0",      # a leaf has no operands
            "node:f@a",        # not a position
            "node:f@-1",
            "node:f@0..1",
        ]

        for designator in bad:
            with self.subTest(designator=designator):
                with self.assertRaises(DesignatorError):
                    resolve(designator, state, state)

        with self.assertRaises(DesignatorError):
            resolve("after:f@", state)  # there is no state after

    def test_paths_reach_every_owned_node_once(self) -> None:
        # The operand table must agree with graph form (graph_form.md
        # section 3): walking it from the body root reaches exactly the
        # nodes the function owns, each by one path.
        def reached(state: State, name: str) -> list[EntityID]:
            found: list[EntityID] = []
            pending = [""]

            while pending:
                path = pending.pop()
                found.append(resolve(f"node:{name}@{path}", state))

                for index in range(10_000):
                    child = f"{path}.{index}" if path else str(index)

                    try:
                        resolve(f"node:{name}@{child}", state)
                    except DesignatorError:
                        break

                    pending.append(child)

            return found

        for example in EXAMPLES:
            state = load(example.program)

            for entity in sorted(state.values):
                node = relation_of(state.values[entity])

                if node is None or node.kind != "definition":
                    continue

                with self.subTest(example=example.name, function=entity.value):
                    found = reached(state, entity.value)

                    self.assertEqual(len(found), len(set(found)))
                    self.assertEqual(set(found), set(state.owned_children(entity)))


SOURCE = "fn f(x):\n    label(step, 1) + x\n"


def probe(expect: Expect, operation, group: str = "inferred", **extra) -> Case:
    return Case(
        name="probe", group=group, source=SOURCE, operation=operation,
        expect=expect, status="holds", note="probe", **extra,
    )


def leaf_edit(state: State) -> TransformResult:
    return define(state, {(F, "step"): ("lit", 10)})


def unrelated_edit(state: State) -> TransformResult:
    """A whole-body edit that shares no subtree with the old body and
    changes the root's kind, so inference keeps no node: every old node
    disappears and every new one is created (continuity_inference.md §2).
    """

    return define(state, {F: Function(("x",), ("lit", 2))})


def forgotten(state: State) -> TransformResult:
    """The edited program with no continuity declared at all."""

    return TransformResult(
        source=state, destination=state_of("fn f(x):\n    x\n"), mappings=()
    )


class CheckTests(unittest.TestCase):
    def mismatches(self, expect: Expect, operation, **extra) -> tuple[str, ...]:
        return check(probe(expect, operation, **extra))

    def test_kept_and_changed_are_told_apart_by_version(self) -> None:
        self.assertEqual(
            self.mismatches(
                Expect(changed=("node:f@0",), kept=("node:f@1", "node:f@")), leaf_edit
            ),
            (),
        )

        wrong = self.mismatches(
            Expect(kept=("node:f@0",), changed=("node:f@1",)), leaf_edit
        )

        self.assertEqual(len(wrong), 2)
        self.assertIn("kept node:f@0", wrong[0])
        self.assertIn("changed node:f@1", wrong[1])

    def test_a_node_that_is_absent_after_is_not_kept_or_changed(self) -> None:
        wrong = self.mismatches(
            Expect(kept=("node:f@1",), changed=("node:f@",)), unrelated_edit
        )

        self.assertEqual(len(wrong), 2)
        self.assertTrue(all("absent after" in mismatch for mismatch in wrong))

    def test_gone_needs_a_recorded_disappearance(self) -> None:
        self.assertEqual(self.mismatches(Expect(gone=("node:f@1",)), unrelated_edit), ())

        unrecorded = self.mismatches(Expect(gone=("node:f@1",)), forgotten)
        self.assertEqual(len(unrecorded), 1)
        self.assertIn("gone node:f@1", unrecorded[0])
        self.assertIn("not recorded as a disappearance", unrecorded[0])

        present = self.mismatches(Expect(gone=("node:f@1",)), leaf_edit)
        self.assertIn("still present", present[0])

    def test_new_means_absent_before_and_present_after(self) -> None:
        self.assertEqual(self.mismatches(Expect(new=("after:f@",)), unrelated_edit), ())

        wrong = self.mismatches(Expect(new=("after:f@1",)), leaf_edit)
        self.assertEqual(len(wrong), 1)
        self.assertIn("new after:f@1", wrong[0])
        self.assertIn("already there", wrong[0])

    def test_at_needs_the_same_entity_at_both_designators(self) -> None:
        self.assertEqual(
            self.mismatches(Expect(at={"node:f@0": "after:f@0"}), leaf_edit), ()
        )

        wrong = self.mismatches(Expect(at={"node:f@0": "after:f@1"}), leaf_edit)
        self.assertEqual(len(wrong), 1)
        self.assertIn("at node:f@0", wrong[0])
        self.assertIn("after:f@1", wrong[0])

    def test_a_designator_that_resolves_to_nothing_is_a_mismatch(self) -> None:
        wrong = self.mismatches(Expect(kept=("node:f@7",)), leaf_edit)

        self.assertEqual(len(wrong), 1)
        self.assertIn("kept node:f@7", wrong[0])

    def test_merged_and_split_read_the_recorded_mapping(self) -> None:
        merge, split = by_name("merge_cells"), by_name("split_cell")

        self.assertEqual(check(merge), ())
        self.assertEqual(check(split), ())

        wrong_merge = check(
            replace(merge, expect=Expect(merged={"cell:b": "cell:b"}))
        )
        self.assertEqual(len(wrong_merge), 1)
        self.assertIn("merged cell:b", wrong_merge[0])

        wrong_split = check(
            replace(split, expect=Expect(split={"cell:pair": ("cell:left",)}))
        )
        self.assertEqual(len(wrong_split), 1)
        self.assertIn("split cell:pair", wrong_split[0])

    def test_rejected_is_the_exception_of_the_operation_or_the_activation(self) -> None:
        called = by_name("delete_called")

        # The transformation itself raises: no activation is reached.
        with self.assertRaises(DanglingRelation):
            called.operation(state_of(called.source))

        self.assertEqual(check(called), ())
        # A subclass counts; a different exception does not.
        self.assertEqual(check(replace(called, expect=Expect(rejected=ValueError))), ())
        wrong = check(replace(called, expect=Expect(rejected=KeyError)))
        self.assertEqual(len(wrong), 1)
        self.assertIn("DanglingRelation", wrong[0])

        # An operation that goes through is not a rejection.
        accepted = self.mismatches(Expect(rejected=ActivationRejected), leaf_edit)
        self.assertEqual(len(accepted), 1)
        self.assertIn("nothing was rejected", accepted[0])

        # An operation that raises without a rejection expected is a mismatch.
        unexpected = check(replace(called, expect=Expect(kept=("fn:main",))))
        self.assertEqual(len(unexpected), 1)
        self.assertIn("the operation raised", unexpected[0])

    def test_cells_tell_a_transfer_from_a_reset(self) -> None:
        case = by_name("activate_define")  # writes 5 into a cell that starts at 0

        self.assertEqual(check(case), ())

        reset = check(
            replace(case, group="inferred", expect=Expect(cells={"cell:hits": 0}))
        )
        self.assertEqual(len(reset), 1)
        self.assertIn("cells cell:hits", reset[0])
        self.assertIn("holds 5", reset[0])

        untouched = check(replace(case, writes={}))
        self.assertEqual(len(untouched), 1)
        self.assertIn("holds 0", untouched[0])

    def test_the_declared_group_wants_everything_unmentioned_kept(self) -> None:
        rename = by_name("rename")
        only_the_mapping = Expect(merged={"fn:double": "fn:twice"})

        wrong = check(replace(rename, expect=only_the_mapping))

        self.assertEqual(len(wrong), 2)
        self.assertTrue(all("unmentioned quad/0." in mismatch for mismatch in wrong))
        self.assertTrue(all("changed" in mismatch for mismatch in wrong))

        # No such rule outside the declared group.
        self.assertEqual(check(replace(rename, group="inferred", expect=only_the_mapping)), ())

    def test_a_pair_is_activated_in_both_orders(self) -> None:
        def chained(state: State) -> tuple[TransformResult, ...]:
            first = define(state, {(F, "step"): ("lit", 10)})
            second = define(first.destination, {(F, "step"): ("lit", 20)})
            return first, second

        wrong = self.mismatches(Expect(changed=("node:f@0",)), chained, group="competing")

        # Built one on the other, they apply in one order only.
        self.assertEqual(len(wrong), 1)
        self.assertTrue(wrong[0].startswith("second edit, then the other"))
        self.assertIn("ActivationRejected", wrong[0])

        # The second of two rewrites of one state is rejected, in either order.
        conflicting = check(by_name("conflicting_edits"))
        self.assertEqual(conflicting, ())
        accepted = check(replace(by_name("conflicting_edits"), expect=Expect()))
        self.assertEqual(len(accepted), 2)


def designators(expect: Expect) -> Iterator[str]:
    yield from expect.kept
    yield from expect.changed
    yield from expect.gone
    yield from expect.new
    yield from expect.at
    yield from expect.at.values()
    yield from expect.merged
    yield from expect.merged.values()
    yield from expect.split
    yield from (target for targets in expect.split.values() for target in targets)
    yield from expect.cells


class CorpusTests(unittest.TestCase):
    def test_every_designator_of_every_case_resolves(self) -> None:
        """A gap must fail on its expectation, not on a bad designator."""
        for case in CASES:
            if case.expect.rejected is not None:
                continue

            with self.subTest(case=case.name):
                source = state_of(case.source)
                produced = case.operation(source)
                result = produced[0] if isinstance(produced, tuple) else produced
                errors = []

                for designator in designators(case.expect):
                    try:
                        resolve(designator, source, result.destination)
                    except DesignatorError as exc:
                        errors.append(f"{designator}: {exc}")

                self.assertFalse(
                    errors,
                    "Unresolvable continuity designators:\n" + "\n".join(errors),
                )

    def test_a_gap_fails_on_its_expectation_not_on_a_crash(self) -> None:
        for case in CASES:
            if case.status == "gap" and case.group != "competing":
                with self.subTest(case=case.name):
                    for mismatch in check(case):
                        self.assertNotIn("raised", mismatch)

    def test_the_note_starts_with_the_status(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                word = "Holds" if case.status == "holds" else "Gap"

                self.assertTrue(case.note.startswith(word), case.note)

    def test_sources_and_operations_are_deterministic(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                self.assertEqual(check(case), check(case))


if __name__ == "__main__":
    unittest.main()
