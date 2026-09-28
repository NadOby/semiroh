"""Tests for activation: cell transfer, references, and version lifecycle."""

import random
import unittest
from typing import Any

from semiroh import (
    ActivationRejected,
    CellDeclaration,
    CellError,
    ConstraintResult,
    Converter,
    EntityID,
    EvaluationContext,
    Evaluator,
    External,
    IntRange,
    IsKind,
    Runtime,
    State,
    Value,
    transform_with_mapping,
)

A = EntityID("a")
B = EntityID("b")
C = EntityID("c")
X = EntityID("x")

SAT = ConstraintResult.SATISFIED
VIO = ConstraintResult.VIOLATED
UNK = ConstraintResult.UNKNOWN


def cell(constraint: Any = None, initial: Any = 0) -> CellDeclaration:
    return CellDeclaration(constraint or IsKind("int"), initial)


def state(**entities: Any) -> State:
    return State.create({
        EntityID(name): Value.create(EntityID(name), content)
        for name, content in entities.items()
    })


def snapshot(runtime: Runtime) -> tuple:
    return (
        runtime.active,
        runtime.versions,
        tuple(
            (version.id, dict(version.cells), version.holds, version.retired)
            for version in runtime.versions
        ),
    )


CONVERTERS = {
    "zero": Converter(lambda _: 0),
    "sum": Converter(lambda sources: sum(sources.values())),
    "huge": Converter(lambda _: 10**6),
}


def random_activation_case(
    rng: random.Random,
) -> tuple[Runtime, Any] | None:
    """A runtime with live content and a random result starting from it.

    Returns None when the random definition itself is invalid.
    """

    names = [EntityID(f"c{index}") for index in range(4)]
    constraints = [IsKind("int"), IntRange(0, 5), IntRange(3, 9)]

    source = State.create({
        name: Value.create(name, cell(IsKind("int"), 0))
        for name in names
    })
    runtime = Runtime(source)

    for name in names:
        runtime.write(name, rng.randrange(-2, 12))

    if rng.random() < 0.3:
        runtime.keep(source.reference(names[0]))

    changes = {
        name: cell(rng.choice(constraints), rng.randrange(0, 4))
        for name in names
        if rng.random() < 0.5
    }
    mappings = {}

    for name in names:
        roll = rng.random()

        if roll < 0.05:
            continue  # no declared continuity

        if roll < 0.2:
            mappings[name] = ()
        elif roll < 0.65:
            mappings[name] = (name,)
        else:
            mappings[name] = tuple(rng.sample(names, rng.choice([1, 1, 2])))

    destinations = {
        destination
        for targets in mappings.values()
        for destination in targets
    }
    conversions = {
        destination: rng.choice(sorted(CONVERTERS))
        for destination in destinations
        if rng.random() < 0.5
    }

    try:
        result = transform_with_mapping(
            source,
            changes,
            mappings,
            conversions=conversions,
        )
    except KeyError:
        return None

    return runtime, result


class CellTransferTests(unittest.TestCase):
    def test_one_to_one_transfers_content_unchanged(self) -> None:
        source = state(a=cell(), x=1)
        runtime = Runtime(source)
        runtime.write(A, 7)

        result = transform_with_mapping(source, {X: 2}, {A: A})
        new = runtime.activate(result)

        self.assertIs(runtime.active, new)
        self.assertEqual(new.state, result.destination)
        self.assertEqual(runtime.read(A), 7)

    def test_rename_transfers_content(self) -> None:
        source = state(a=cell())
        runtime = Runtime(source)
        runtime.write(A, 7)

        runtime.activate(transform_with_mapping(source, {B: cell()}, {A: B}))

        self.assertEqual(runtime.read(B), 7)

        with self.assertRaises(KeyError):
            runtime.read(A)

    def test_widened_constraint_needs_no_conversion(self) -> None:
        source = state(a=cell(IntRange(0, 10)))
        runtime = Runtime(source)
        runtime.write(A, 7)

        runtime.activate(
            transform_with_mapping(source, {A: cell(IntRange(0, 100))}, {A: A})
        )

        self.assertEqual(runtime.read(A), 7)

    def test_failing_content_requires_a_conversion(self) -> None:
        source = state(a=cell(IntRange(0, 100)))
        narrowed = {A: cell(IntRange(0, 10))}

        runtime = Runtime(source)
        runtime.write(A, 50)

        with self.assertRaises(ActivationRejected) as raised:
            runtime.activate(transform_with_mapping(source, narrowed, {A: A}))

        self.assertEqual(raised.exception.cell, A)
        self.assertIs(raised.exception.result, VIO)

        runtime.activate(
            transform_with_mapping(
                source,
                narrowed,
                {A: A},
                conversions={A: "clamp"},
            ),
            {"clamp": Converter(lambda sources: min(sources[A], 10))},
        )

        self.assertEqual(runtime.read(A), 10)

    def test_conversion_output_is_checked(self) -> None:
        source = state(a=cell())
        runtime = Runtime(source)

        with self.assertRaises(ActivationRejected) as raised:
            runtime.activate(
                transform_with_mapping(
                    source,
                    {A: cell(IntRange(0, 10))},
                    {A: A},
                    conversions={A: "big"},
                ),
                {"big": Converter(lambda _: 1000)},
            )

        self.assertIs(raised.exception.result, VIO)

    def test_unknown_under_the_new_constraint_is_rejected(self) -> None:
        source = state(a=cell())
        runtime = Runtime(source)

        with self.assertRaises(ActivationRejected) as raised:
            runtime.activate(
                transform_with_mapping(source, {A: cell(External("ok"))}, {A: A})
            )

        self.assertIs(raised.exception.result, UNK)

    def test_new_constraint_is_evaluated_in_the_runtime_context(self) -> None:
        source = state(a=cell())
        runtime = Runtime(
            source,
            EvaluationContext({"ok": Evaluator(lambda _: SAT)}),
        )

        runtime.activate(
            transform_with_mapping(source, {A: cell(External("ok"))}, {A: A})
        )

        self.assertEqual(runtime.read(A), 0)

    def test_disappearing_cell_discards_its_content(self) -> None:
        source = state(a=cell(), x=1)
        runtime = Runtime(source)
        old = runtime.active

        new = runtime.activate(transform_with_mapping(source, {}, {A: ()}))

        self.assertNotIn(A, new.cells)
        self.assertTrue(old.retired)
        self.assertEqual(dict(old.cells), {})

    def test_split_requires_a_conversion_per_destination(self) -> None:
        source = state(a=cell())
        changes = {B: cell(), C: cell()}
        runtime = Runtime(source)
        runtime.write(A, 7)

        with self.assertRaises(ActivationRejected):
            runtime.activate(
                transform_with_mapping(source, changes, {A: (B, C)})
            )

        runtime.activate(
            transform_with_mapping(
                source,
                changes,
                {A: (B, C)},
                conversions={B: "half", C: "rest"},
            ),
            {
                "half": Converter(lambda sources: sources[A] // 2),
                "rest": Converter(lambda sources: sources[A] - sources[A] // 2),
            },
        )

        self.assertEqual((runtime.read(B), runtime.read(C)), (3, 4))

    def test_merge_requires_a_conversion(self) -> None:
        source = state(a=cell(), b=cell())
        runtime = Runtime(source)
        runtime.write(A, 3)
        runtime.write(B, 4)

        with self.assertRaises(ActivationRejected):
            runtime.activate(
                transform_with_mapping(source, {C: cell()}, {A: C, B: C})
            )

        runtime.activate(
            transform_with_mapping(
                source,
                {C: cell()},
                {A: C, B: C},
                conversions={C: "sum"},
            ),
            {"sum": Converter(lambda sources: sum(sources.values()))},
        )

        self.assertEqual(runtime.read(C), 7)

    def test_cell_without_declared_continuity_is_rejected(self) -> None:
        source = state(a=cell(), x=1)
        runtime = Runtime(source)

        with self.assertRaises(ActivationRejected) as raised:
            runtime.activate(transform_with_mapping(source, {X: 2}, {}))

        self.assertEqual(raised.exception.cell, A)

    def test_bare_state_is_rejected_while_cells_hold_content(self) -> None:
        runtime = Runtime(state(a=cell()))

        with self.assertRaises(ActivationRejected):
            runtime.activate(state(a=cell(), x=1))

    def test_bare_state_activates_when_no_cells_hold_content(self) -> None:
        runtime = Runtime(state(x=1))
        target = state(x=2, a=cell(initial=5))

        runtime.activate(target)

        self.assertEqual(runtime.active.state, target)
        self.assertEqual(runtime.read(A), 5)

    def test_cell_continuing_as_a_non_cell_is_rejected(self) -> None:
        source = state(a=cell(), x=1)
        runtime = Runtime(source)

        with self.assertRaises(ActivationRejected):
            runtime.activate(transform_with_mapping(source, {}, {A: X}))

    def test_new_cell_starts_from_its_initializer(self) -> None:
        source = state(x=1)
        runtime = Runtime(source)

        runtime.activate(
            transform_with_mapping(source, {B: cell(initial=3)}, {X: X})
        )

        self.assertEqual(runtime.read(B), 3)

    def test_new_cell_with_invalid_initializer_is_rejected(self) -> None:
        source = state(x=1)
        runtime = Runtime(source)

        with self.assertRaises(ActivationRejected):
            runtime.activate(
                transform_with_mapping(
                    source,
                    {B: cell(initial="not an int")},
                    {X: X},
                )
            )

    def test_missing_converter_is_rejected(self) -> None:
        source = state(a=cell())
        runtime = Runtime(source)

        with self.assertRaises(ActivationRejected):
            runtime.activate(
                transform_with_mapping(
                    source,
                    {},
                    {A: A},
                    conversions={A: "absent"},
                )
            )

    def test_conversion_needs_source_cells(self) -> None:
        source = state(x=1)
        runtime = Runtime(source)

        with self.assertRaises(ActivationRejected):
            runtime.activate(
                transform_with_mapping(
                    source,
                    {B: cell()},
                    {X: B},
                    conversions={B: "f"},
                ),
                {"f": Converter(lambda _: 0)},
            )

    def test_activation_must_start_from_the_active_state(self) -> None:
        other = state(x=2)
        runtime = Runtime(state(x=1))

        with self.assertRaises(ActivationRejected):
            runtime.activate(transform_with_mapping(other, {}, {X: X}))

    def test_converters_must_be_converters(self) -> None:
        source = state(a=cell())
        runtime = Runtime(source)

        with self.assertRaises(TypeError):
            runtime.activate(
                transform_with_mapping(source, {}, {A: A}),
                {"f": lambda _: 0},  # type: ignore[dict-item]
            )


class ReferenceActivationTests(unittest.TestCase):
    def test_reference_with_unique_continuation_is_transferred(self) -> None:
        source = state(x=1)
        runtime = Runtime(source)
        old = runtime.active
        kept = runtime.keep(source.reference(X))

        result = transform_with_mapping(source, {X: 2}, {X: X})
        new = runtime.activate(result)

        self.assertIs(kept.version, new)
        self.assertEqual(kept.reference, result.destination.reference(X))
        self.assertTrue(old.retired)
        self.assertEqual(runtime.versions, (new,))

    def test_untransferable_reference_is_pinned(self) -> None:
        source = state(x=1)
        runtime = Runtime(source)
        old = runtime.active
        kept = runtime.keep(source.reference(X))

        new = runtime.activate(transform_with_mapping(source, {X: 2}, {}))

        self.assertIs(kept.version, old)
        self.assertEqual(kept.reference, source.reference(X))
        self.assertIs(runtime.previous, old)
        self.assertEqual(runtime.versions, (new, old))

        kept.release()

        self.assertTrue(old.retired)
        self.assertEqual(runtime.versions, (new,))

    def test_strict_policy_rejects_untransferable_references(self) -> None:
        source = state(x=1)
        runtime = Runtime(source)
        runtime.keep(source.reference(X))
        before = snapshot(runtime)

        with self.assertRaises(ActivationRejected):
            runtime.activate(
                transform_with_mapping(source, {X: 2}, {}),
                reject_untransferable_references=True,
            )

        self.assertEqual(snapshot(runtime), before)


class VersionLifecycleTests(unittest.TestCase):
    def test_frame_keeps_the_previous_version_alive(self) -> None:
        source = state(a=cell())
        runtime = Runtime(source)
        runtime.write(A, 7)
        old = runtime.active
        frame = runtime.enter(A)

        runtime.activate(transform_with_mapping(source, {X: 1}, {A: A}))

        self.assertIs(frame.version, old)
        self.assertIs(runtime.previous, old)
        self.assertEqual(old.cells[A], 7)

        frame.release()

        self.assertTrue(old.retired)
        self.assertIsNone(runtime.previous)
        self.assertEqual(dict(old.cells), {})

    def test_activation_is_rejected_while_the_previous_version_is_held(
        self,
    ) -> None:
        first = state(x=1)
        runtime = Runtime(first)
        frame = runtime.enter(X)

        second = runtime.activate(
            transform_with_mapping(first, {X: 2}, {X: X})
        ).state
        third = transform_with_mapping(second, {X: 3}, {X: X})

        with self.assertRaises(ActivationRejected):
            runtime.activate(third)

        frame.release()
        runtime.activate(third)

        self.assertEqual(runtime.active.state, third.destination)

    def test_writes_go_to_the_active_version_only(self) -> None:
        source = state(a=cell())
        runtime = Runtime(source)
        old = runtime.active
        frame = runtime.enter(A)

        runtime.activate(transform_with_mapping(source, {X: 1}, {A: A}))
        runtime.write(A, 9)

        self.assertEqual(old.cells[A], 0)
        self.assertEqual(runtime.read(A), 9)
        frame.release()


class ActivationAtomicityTests(unittest.TestCase):
    def test_converter_failure_leaves_the_runtime_unchanged(self) -> None:
        source = state(a=cell())
        runtime = Runtime(source)
        runtime.write(A, 7)
        before = snapshot(runtime)

        def fail(_: Any) -> Any:
            raise RuntimeError("converter failed")

        with self.assertRaises(RuntimeError):
            runtime.activate(
                transform_with_mapping(
                    source,
                    {},
                    {A: A},
                    conversions={A: "fail"},
                ),
                {"fail": Converter(fail)},
            )

        self.assertEqual(snapshot(runtime), before)

    def test_random_activations_are_atomic_and_keep_constraints(self) -> None:
        # Either an activation succeeds, and every cell of the new version
        # satisfies its constraint, or it is rejected and nothing changes.
        outcomes = {"accepted": 0, "rejected": 0}

        for seed in range(500):
            with self.subTest(seed=seed):
                case = random_activation_case(random.Random(seed))

                if case is None:
                    continue

                runtime, result = case
                before = snapshot(runtime)

                try:
                    new = runtime.activate(result, CONVERTERS)
                except ActivationRejected:
                    outcomes["rejected"] += 1
                    self.assertEqual(snapshot(runtime), before)
                    continue

                outcomes["accepted"] += 1
                self.assertIs(runtime.active, new)

                for name, declaration in new._declarations.items():
                    self.assertIs(
                        declaration.constraint.evaluate(new.cells[name]),
                        SAT,
                    )

        self.assertGreater(outcomes["accepted"], 50)
        self.assertGreater(outcomes["rejected"], 50)


if __name__ == "__main__":
    unittest.main()
