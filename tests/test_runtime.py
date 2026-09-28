"""Tests for runtime state: cell content, versions, and holds."""

import random
import unittest

from semiroh import (
    CellDeclaration,
    CellError,
    CrossStateReference,
    EntityID,
    Reference,
    Runtime,
    StaleReference,
    State,
    StateID,
    Value,
    VersionID,
    canonicalize,
    transform,
)

COUNTER = EntityID("counter")
NAME = EntityID("name")
LIMIT = EntityID("limit")


def program() -> State:
    return State.create({
        COUNTER: Value.create(COUNTER, CellDeclaration("int", 0)),
        NAME: Value.create(NAME, CellDeclaration("str", "")),
        LIMIT: Value.create(LIMIT, 10),
    })


class CellContentTests(unittest.TestCase):
    def test_cells_start_with_their_initial_content(self) -> None:
        runtime = Runtime(program())

        self.assertEqual(runtime.read(COUNTER), 0)
        self.assertEqual(runtime.read(NAME), "")

    def test_writing_a_cell_does_not_change_program_state(self) -> None:
        state = program()
        runtime = Runtime(state)

        runtime.write(COUNTER, 5)

        self.assertEqual(runtime.read(COUNTER), 5)
        self.assertIs(runtime.active.state, state)
        self.assertEqual(runtime.active.id, program().id)

    def test_written_content_is_canonical_and_detached(self) -> None:
        runtime = Runtime(program())
        items = [1, 2]

        runtime.write(NAME, items)
        items.append(3)

        self.assertEqual(runtime.read(NAME), canonicalize([1, 2]))

    def test_runtimes_of_the_same_state_have_independent_content(self) -> None:
        state = program()
        first = Runtime(state)
        second = Runtime(state)

        first.write(COUNTER, 1)

        self.assertEqual(second.read(COUNTER), 0)

    def test_ordinary_values_are_not_writable(self) -> None:
        runtime = Runtime(program())

        with self.assertRaises(CellError):
            runtime.write(LIMIT, 11)

        with self.assertRaises(CellError):
            runtime.read(LIMIT)

    def test_absent_entities_are_rejected(self) -> None:
        runtime = Runtime(program())

        with self.assertRaises(KeyError):
            runtime.write(EntityID("missing"), 1)

    def test_cell_view_is_read_only(self) -> None:
        runtime = Runtime(program())

        with self.assertRaises(TypeError):
            runtime.active.cells[COUNTER] = 1  # type: ignore[index]


class VersionOwnershipTests(unittest.TestCase):
    def test_runtime_root_owns_only_the_active_version_initially(self) -> None:
        runtime = Runtime(program())

        self.assertEqual(runtime.versions, (runtime.active,))


class HoldTests(unittest.TestCase):
    def test_frame_holds_the_active_version_until_released(self) -> None:
        runtime = Runtime(program())

        frame = runtime.enter(LIMIT)

        self.assertIs(frame.version, runtime.active)
        self.assertEqual(frame.entity, LIMIT)
        self.assertEqual(runtime.active.holds, {frame})

        frame.release()

        self.assertTrue(frame.released)
        self.assertEqual(runtime.active.holds, frozenset())

    def test_hold_cannot_be_released_twice(self) -> None:
        frame = Runtime(program()).enter(LIMIT)
        frame.release()

        with self.assertRaises(ValueError):
            frame.release()

    def test_frame_requires_an_entity_of_the_active_state(self) -> None:
        with self.assertRaises(KeyError):
            Runtime(program()).enter(EntityID("missing"))

    def test_kept_reference_holds_its_version(self) -> None:
        state = program()
        runtime = Runtime(state)

        kept = runtime.keep(state.reference(LIMIT))

        self.assertIs(kept.version, runtime.active)
        self.assertIn(kept, runtime.active.holds)

    def test_kept_reference_must_resolve(self) -> None:
        state = program()
        runtime = Runtime(state)
        other = transform(state, {LIMIT: 20})

        with self.assertRaises(CrossStateReference):
            runtime.keep(other.reference(LIMIT))

        with self.assertRaises(StaleReference):
            runtime.keep(
                Reference(state.id, LIMIT, VersionID("stale"))
            )

        with self.assertRaises(CrossStateReference):
            runtime.keep(
                Reference(StateID("elsewhere"), LIMIT, VersionID("x"))
            )


class RuntimeProperties(unittest.TestCase):
    def test_random_runtime_activity_preserves_program_state_and_holds(
        self,
    ) -> None:
        # Cell writes never change program state, and the recorded holds are
        # exactly the holds that have not been released.
        state = program()

        for seed in range(200):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                runtime = Runtime(state)
                live: list = []
                expected = {COUNTER: 0, NAME: ""}

                for _ in range(40):
                    action = rng.randrange(4)

                    if action == 0:
                        cell = rng.choice([COUNTER, NAME])
                        content = rng.choice([0, 1, "x", (1, 2), [3]])
                        runtime.write(cell, content)
                        expected[cell] = canonicalize(content)
                    elif action == 1:
                        live.append(
                            runtime.enter(rng.choice([COUNTER, LIMIT]))
                        )
                    elif action == 2:
                        live.append(runtime.keep(state.reference(LIMIT)))
                    elif live:
                        live.pop(rng.randrange(len(live))).release()

                self.assertEqual(runtime.active.id, state.id)
                self.assertEqual(runtime.active.holds, set(live))
                self.assertEqual(dict(runtime.active.cells), expected)


if __name__ == "__main__":
    unittest.main()
