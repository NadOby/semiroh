"""Acceptance tests for the canary corpus (docs/corpus.md).

The corpus must run under the reference interpreter, and must fail under
deliberately broken ones. The implementation is done when these tests pass
unchanged.
"""

import unittest

from semiroh import (
    CellContentRejected,
    CellDeclaration,
    EntityID,
    IntRange,
    State,
    Value,
)
from semiroh import lang
from semiroh.examples import (
    EXAMPLES,
    MISSING,
    TAGS,
    Example,
    ExampleFailed,
    Raises,
    Step,
    play,
)
from semiroh.lang import Function, links


def off_by_one(runtime, entry, *args, may_activate=False):
    result = lang.run(runtime, entry, *args, may_activate=may_activate)

    if isinstance(result, int) and not isinstance(result, bool):
        return result + 1

    return result


def lost_writes(runtime, entry, *args, may_activate=False):
    before = dict(runtime.active.cells)
    result = lang.run(runtime, entry, *args, may_activate=may_activate)

    for cell, content in before.items():
        if cell in runtime.active.cells:
            runtime.write(cell, content)

    return result


def ignored_grant(runtime, entry, *args, may_activate=False):
    return lang.run(runtime, entry, *args)


def swallowed_errors(runtime, entry, *args, may_activate=False):
    try:
        return lang.run(runtime, entry, *args, may_activate=may_activate)
    except Exception:
        return None


def fails(example: Example, run) -> bool:
    try:
        play(example, run)
    except ExampleFailed:
        return True

    return False


def has_raises_step(example: Example) -> bool:
    return any(
        isinstance(step.expect, Raises)
        for scenario in example.scenarios
        for step in scenario
    )


class CorpusShapeTests(unittest.TestCase):
    def test_tier_one_covers_every_tag(self) -> None:
        self.assertGreaterEqual(len(EXAMPLES), 10)
        self.assertEqual(len({example.name for example in EXAMPLES}), len(EXAMPLES))

        for example in EXAMPLES:
            with self.subTest(example=example.name):
                self.assertTrue(example.tags)
                self.assertLessEqual(set(example.tags), TAGS)
                self.assertTrue(example.scenarios)
                self.assertTrue(all(example.scenarios))

        self.assertEqual(
            set().union(*(example.tags for example in EXAMPLES)),
            set(TAGS),
        )

    def test_wanted_programs_name_their_missing_feature(self) -> None:
        self.assertEqual(len({wanted.name for wanted in MISSING}), len(MISSING))

        for wanted in MISSING:
            with self.subTest(wanted=wanted.name):
                self.assertTrue(wanted.name)
                self.assertTrue(wanted.needs)


class ReferenceInterpreterTests(unittest.TestCase):
    def test_every_example_runs_under_lang(self) -> None:
        for example in EXAMPLES:
            with self.subTest(example=example.name):
                play(example, lang.run)


class CanaryTests(unittest.TestCase):
    """The corpus must notice a broken interpreter."""

    def test_wrong_integer_results_are_caught(self) -> None:
        caught = [example.name for example in EXAMPLES if fails(example, off_by_one)]

        self.assertGreaterEqual(len(caught), 5)

    def test_lost_cell_writes_are_caught(self) -> None:
        for example in EXAMPLES:
            if "side effects" in example.tags:
                with self.subTest(example=example.name):
                    self.assertTrue(fails(example, lost_writes))

    def test_ignored_activation_grant_is_caught(self) -> None:
        for example in EXAMPLES:
            if "self-modification" in example.tags:
                with self.subTest(example=example.name):
                    self.assertTrue(fails(example, ignored_grant))

    def test_swallowed_errors_are_caught(self) -> None:
        expecting_errors = [example for example in EXAMPLES if has_raises_step(example)]
        self.assertTrue(expecting_errors)

        for example in expecting_errors:
            with self.subTest(example=example.name):
                self.assertTrue(fails(example, swallowed_errors))


class PlayTests(unittest.TestCase):
    """The contract of play itself, on a tiny example outside the corpus."""

    COUNTER = EntityID("counter")
    BUMP = EntityID("bump")
    BUMP_LINKS = EntityID("bump.links")
    IS_ONE = EntityID("is_one")

    def example(self, *steps: Step) -> Example:
        program = State.create({
            entity: Value.create(entity, content)
            for entity, content in {
                self.COUNTER: CellDeclaration(IntRange(0, 1), 0),
                self.BUMP: Function(
                    (),
                    ("write", "counter", ("add", ("read", "counter"), ("lit", 1))),
                ),
                self.BUMP_LINKS: links(self.BUMP, counter=self.COUNTER),
                self.IS_ONE: Function(("x",), ("eq", ("arg", "x"), ("lit", 1))),
            }.items()
        })

        return Example(
            name="tiny",
            tags=frozenset({"side effects"}),
            program=program,
            scenarios=(tuple(steps),),
        )

    def test_matching_steps_pass(self) -> None:
        play(
            self.example(
                Step(self.BUMP, (), 1, cells={self.COUNTER: 1}),
                Step(self.BUMP, (), Raises(ValueError)),  # a subclass counts
                Step(self.IS_ONE, (1,), True),
            ),
            lang.run,
        )

    def test_mismatches_fail_and_name_the_example(self) -> None:
        for step in (
            Step(self.BUMP, (), 2),
            Step(self.BUMP, (), 1, cells={self.COUNTER: 0}),
            Step(self.IS_ONE, (1,), 1),  # True is not 1
            Step(self.IS_ONE, (), True),  # raises instead of returning
            Step(self.IS_ONE, (1,), Raises(CellContentRejected)),
        ):
            with self.subTest(step=step):
                with self.assertRaises(ExampleFailed) as caught:
                    play(self.example(step), lang.run)

                self.assertIn("tiny", str(caught.exception))

    def test_each_scenario_starts_from_a_fresh_runtime(self) -> None:
        example = self.example(Step(self.BUMP, (), 1))
        example = Example(
            name=example.name,
            tags=example.tags,
            program=example.program,
            scenarios=(example.scenarios[0], example.scenarios[0]),
        )

        play(example, lang.run)


if __name__ == "__main__":
    unittest.main()
