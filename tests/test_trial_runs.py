"""Tests for trial runs of candidate versions in isolated runtimes."""

import random
import unittest

from shear import (
    ActivationRejected,
    ConstraintResult,
    Converter,
    EvaluationContext,
    Evaluator,
    External,
    IntRange,
    Runtime,
    transform_with_mapping,
)
from tests.test_activation import (
    A,
    CONVERTERS,
    X,
    cell,
    random_activation_case,
    snapshot,
    state,
)

SAT = ConstraintResult.SATISFIED
VIO = ConstraintResult.VIOLATED
UNK = ConstraintResult.UNKNOWN


class TrialRunTests(unittest.TestCase):
    def test_trial_stages_content_into_an_isolated_runtime(self) -> None:
        source = state(a=cell(), x=1)
        runtime = Runtime(source)
        runtime.write(A, 7)
        before = snapshot(runtime)

        result = transform_with_mapping(source, {X: 2}, {A: A})
        trial = runtime.trial(result)

        self.assertEqual(trial.read(A), 7)
        self.assertEqual(trial.active.state, result.destination)
        self.assertEqual(trial.versions, (trial.active,))
        self.assertEqual(snapshot(runtime), before)

    def test_trial_and_main_runtime_are_independent(self) -> None:
        source = state(a=cell())
        runtime = Runtime(source)
        trial = runtime.trial(transform_with_mapping(source, {X: 1}, {A: A}))

        trial.write(A, 1)
        runtime.write(A, 2)

        self.assertEqual((runtime.read(A), trial.read(A)), (2, 1))

    def test_trial_is_rejected_like_activation(self) -> None:
        source = state(a=cell(IntRange(0, 100)))
        runtime = Runtime(source)
        runtime.write(A, 50)
        before = snapshot(runtime)
        narrowed = transform_with_mapping(
            source,
            {A: cell(IntRange(0, 10))},
            {A: A},
        )

        with self.assertRaises(ActivationRejected) as raised:
            runtime.trial(narrowed)

        self.assertEqual(raised.exception.cell, A)
        self.assertIs(raised.exception.result, VIO)
        self.assertEqual(snapshot(runtime), before)

    def test_trial_runs_the_same_conversions(self) -> None:
        source = state(a=cell(IntRange(0, 100)))
        runtime = Runtime(source)
        runtime.write(A, 50)

        trial = runtime.trial(
            transform_with_mapping(
                source,
                {A: cell(IntRange(0, 10))},
                {A: A},
                conversions={A: "clamp"},
            ),
            {"clamp": Converter(lambda sources: min(sources[A], 10))},
        )

        self.assertEqual(trial.read(A), 10)
        self.assertEqual(runtime.read(A), 50)

    def test_trial_is_not_limited_by_the_two_version_bound(self) -> None:
        first = state(x=1)
        runtime = Runtime(first)
        frame = runtime.enter(X)

        second = runtime.activate(
            transform_with_mapping(first, {X: 2}, {X: X})
        ).state
        third = transform_with_mapping(second, {X: 3}, {X: X})

        with self.assertRaises(ActivationRejected):
            runtime.activate(third)

        trial = runtime.trial(third)

        self.assertEqual(trial.active.state, third.destination)
        self.assertEqual(len(runtime.versions), 2)
        frame.release()

    def test_trial_uses_the_main_context_unless_narrowed(self) -> None:
        source = state(a=cell())
        runtime = Runtime(
            source,
            EvaluationContext({"ok": Evaluator(lambda _: SAT)}),
        )
        result = transform_with_mapping(
            source,
            {A: cell(External("ok"))},
            {A: A},
        )

        self.assertIs(runtime.trial(result).context, runtime.context)

        with self.assertRaises(ActivationRejected) as raised:
            runtime.trial(result, context=EvaluationContext())

        self.assertIs(raised.exception.result, UNK)

    def test_trial_does_not_copy_holds(self) -> None:
        source = state(a=cell(), x=1)
        runtime = Runtime(source)
        frame = runtime.enter(A)
        kept = runtime.keep(source.reference(X))

        trial = runtime.trial(transform_with_mapping(source, {}, {A: A, X: X}))

        self.assertEqual(trial.active.holds, frozenset())
        self.assertEqual(runtime.active.holds, {frame, kept})

    def test_trial_must_start_from_the_active_state(self) -> None:
        runtime = Runtime(state(x=1))

        with self.assertRaises(ActivationRejected):
            runtime.trial(transform_with_mapping(state(x=2), {}, {X: X}))

    def test_candidate_becomes_a_main_version_only_by_activation(
        self,
    ) -> None:
        source = state(a=cell())
        runtime = Runtime(source)
        runtime.write(A, 7)
        old = runtime.active
        result = transform_with_mapping(source, {X: 1}, {A: A})

        trial = runtime.trial(result)

        self.assertIs(runtime.active, old)

        new = runtime.activate(result)

        self.assertEqual(new.state, trial.active.state)
        self.assertEqual(dict(new.cells), dict(trial.active.cells))


class TrialRunProperties(unittest.TestCase):
    def test_trial_and_activation_agree(self) -> None:
        # A trial succeeds exactly when the activation would, with the same
        # cell content, and is rejected for the same cell and result.
        outcomes = {"accepted": 0, "rejected": 0}

        for seed in range(500):
            with self.subTest(seed=seed):
                case = random_activation_case(random.Random(seed))

                if case is None:
                    continue

                runtime, result = case
                before = snapshot(runtime)

                try:
                    trial = runtime.trial(result, CONVERTERS)
                except ActivationRejected as rejected:
                    self.assertEqual(snapshot(runtime), before)

                    with self.assertRaises(ActivationRejected) as raised:
                        runtime.activate(result, CONVERTERS)

                    self.assertEqual(raised.exception.cell, rejected.cell)
                    self.assertIs(raised.exception.result, rejected.result)
                    outcomes["rejected"] += 1
                    continue

                self.assertEqual(snapshot(runtime), before)

                new = runtime.activate(result, CONVERTERS)

                self.assertEqual(dict(trial.active.cells), dict(new.cells))
                outcomes["accepted"] += 1

        self.assertGreater(outcomes["accepted"], 50)
        self.assertGreater(outcomes["rejected"], 50)


if __name__ == "__main__":
    unittest.main()
