"""Acceptance tests for metaprogramming (docs/metaprogramming.md).

These tests define how a running program writes code and installs it into
itself. The implementation is done when they pass unchanged.

Programs are written in the input format and loaded into graph form
(graph_form.md).
"""

import unittest

from shear import (
    ActivationRejected,
    CellDeclaration,
    ConstraintResult,
    EntityID,
    EvaluationContext,
    Evaluator,
    External,
    IntRange,
    Relation,
    Role,
    Runtime,
    State,
    Value,
    canonical_serialize,
    canonicalize,
    kind_of,
)
from shear.lang import Function, LanguageError, function_at, links, load, run

COUNTER = EntityID("counter")
STASH = EntityID("stash")
INCREMENT = EntityID("increment")
INCREMENT_LINKS = EntityID("increment.links")
POWER = EntityID("power")
EMIT = EntityID("emit")
EMIT_LINKS = EntityID("emit.links")
COMPILE = EntityID("compile")
COMPILE_LINKS = EntityID("compile.links")
PREPARE = EntityID("prepare")
PREPARE_LINKS = EntityID("prepare.links")
INSTALL = EntityID("install")
INSTALL_LINKS = EntityID("install.links")
BUMP = EntityID("bump")
BUMP_LINKS = EntityID("bump.links")
REPLACE_SELF = EntityID("replace_self")
REPLACE_SELF_LINKS = EntityID("replace_self.links")


def code(params: tuple, body: tuple) -> tuple:
    """An expression that evaluates to Function(params, body)."""

    return ("function", ("lit", params), ("lit", body))


def increment_body(step: int) -> tuple:
    return ("write", "counter", ("add", ("read", "counter"), ("lit", step)))


def power_body(n: int) -> tuple:
    """What emit(n) should generate: x multiplied n times, times 1."""

    if n == 0:
        return ("lit", 1)

    return ("mul", ("arg", "x"), power_body(n - 1))


def mentions(content: object, word: str) -> bool:
    if content == word:
        return True

    if isinstance(content, tuple):
        return any(mentions(item, word) for item in content)

    return False


CONTEXT = EvaluationContext(externals={
    # Code that writes cells is not pure.
    "pure": Evaluator(
        lambda subject: ConstraintResult.VIOLATED
        if mentions(subject, "write")
        else ConstraintResult.SATISFIED
    ),
    # IsKind only knows the core kinds; "function" belongs to the language.
    "code": Evaluator(
        lambda subject: ConstraintResult.SATISFIED
        if kind_of(subject) == "function"
        else ConstraintResult.VIOLATED
    ),
})


def program(extra: dict | None = None) -> State:
    entities = {
        COUNTER: CellDeclaration(IntRange(0, 100), 0),
        STASH: CellDeclaration(External("code"), Function(("x",), ("lit", 1))),
        INCREMENT: Function((), increment_body(1)),
        INCREMENT_LINKS: links(INCREMENT, counter=COUNTER),
        POWER: Function(("x",), ("lit", 1)),
        # A compiler: emit(n) builds the body of x to the power n.
        EMIT: Function(
            ("n",),
            (
                "if",
                ("eq", ("arg", "n"), ("lit", 0)),
                ("lit", ("lit", 1)),
                (
                    "quote",
                    (
                        "mul",
                        ("arg", "x"),
                        (
                            "unquote",
                            ("call", "emit", ("sub", ("arg", "n"), ("lit", 1))),
                        ),
                    ),
                ),
            ),
        ),
        EMIT_LINKS: links(EMIT, emit=EMIT),
        COMPILE: Function(
            ("n",),
            (
                "activate",
                "power",
                ("function", ("lit", ("x",)), ("call", "emit", ("arg", "n"))),
            ),
        ),
        COMPILE_LINKS: links(COMPILE, power=POWER, emit=EMIT),
        PREPARE: Function(
            ("n",),
            (
                "write",
                "stash",
                ("function", ("lit", ("x",)), ("call", "emit", ("arg", "n"))),
            ),
        ),
        PREPARE_LINKS: links(PREPARE, stash=STASH, emit=EMIT),
        INSTALL: Function((), ("activate", "power", ("read", "stash"))),
        INSTALL_LINKS: links(INSTALL, power=POWER, stash=STASH),
        BUMP: Function(
            (),
            (
                "seq",
                ("call", "increment"),
                ("activate", "increment", code((), increment_body(10))),
                ("call", "increment"),
            ),
        ),
        BUMP_LINKS: links(BUMP, increment=INCREMENT),
        REPLACE_SELF: Function(
            (),
            (
                "seq",
                ("activate", "itself", code((), ("lit", "new"))),
                ("lit", "old"),
            ),
        ),
        REPLACE_SELF_LINKS: links(REPLACE_SELF, itself=REPLACE_SELF),
        **(extra or {}),
    }

    return load(State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    }))


def runtime_for(extra: dict | None = None) -> Runtime:
    return Runtime(program(extra), CONTEXT)


def installed(runtime: Runtime, entity: EntityID) -> Function | None:
    return function_at(runtime.active.state, entity)


class CodeAsDataTests(unittest.TestCase):
    def assertSameValue(self, actual: object, expected: object) -> None:
        self.assertEqual(
            canonical_serialize(canonicalize(actual)),
            canonical_serialize(canonicalize(expected)),
        )

    def test_quote_fills_holes(self) -> None:
        runtime = runtime_for()

        self.assertSameValue(run(runtime, EMIT, 0), power_body(0))
        self.assertSameValue(run(runtime, EMIT, 3), power_body(3))

    def test_function_builds_a_function_value(self) -> None:
        make = EntityID("make")
        runtime = runtime_for({
            make: Function(
                ("k",),
                (
                    "function",
                    ("lit", ("x",)),
                    (
                        "quote",
                        ("mul", ("arg", "x"), ("lit", ("unquote", ("arg", "k")))),
                    ),
                ),
            ),
        })

        self.assertSameValue(
            run(runtime, make, 3),
            Function(("x",), ("mul", ("arg", "x"), ("lit", 3))),
        )

    def test_building_code_does_not_change_the_program(self) -> None:
        runtime = runtime_for()
        state = runtime.active.state

        run(runtime, EMIT, 2)
        run(runtime, PREPARE, 2)

        self.assertEqual(runtime.active.id, state.id)


class SelfModificationTests(unittest.TestCase):
    def test_program_compiles_and_installs_its_own_code(self) -> None:
        runtime = runtime_for()
        old = runtime.active
        run(runtime, INCREMENT)
        self.assertEqual(run(runtime, POWER, 2), 1)

        self.assertIsNone(run(runtime, COMPILE, 3, may_activate=True))

        self.assertEqual(run(runtime, POWER, 2), 8)
        self.assertEqual(installed(runtime, POWER), Function(("x",), power_body(3)))
        self.assertNotEqual(runtime.active.id, old.id)
        self.assertEqual(runtime.read(COUNTER), 1)
        self.assertTrue(old.retired)
        self.assertIsNone(runtime.previous)
        self.assertEqual(runtime.active.holds, frozenset())

    def test_activation_needs_the_capability(self) -> None:
        runtime = runtime_for()
        state = runtime.active.state

        with self.assertRaises(ActivationRejected):
            run(runtime, COMPILE, 3)

        self.assertEqual(runtime.active.id, state.id)
        self.assertEqual(run(runtime, POWER, 2), 1)
        self.assertEqual(runtime.active.holds, frozenset())

    def test_function_values_survive_a_cell(self) -> None:
        runtime = runtime_for()

        run(runtime, PREPARE, 2)
        run(runtime, INSTALL, may_activate=True)

        self.assertEqual(run(runtime, POWER, 3), 9)

    def test_program_constraints_guard_self_modification(self) -> None:
        guard = EntityID("power.guard")
        sabotage = EntityID("sabotage")
        sabotage_links = EntityID("sabotage.links")
        runtime = runtime_for({
            guard: Relation("guard", {"code": POWER}, Role("code", External("pure"))),
            # Changes two functions at once; the second breaks the guard.
            sabotage: Function(
                (),
                (
                    "activate",
                    "increment",
                    code((), increment_body(10)),
                    "power",
                    code(("x",), ("write", "counter", ("arg", "x"))),
                ),
            ),
            sabotage_links: links(sabotage, increment=INCREMENT, power=POWER),
        })
        state = runtime.active.state

        with self.assertRaises(ActivationRejected):
            run(runtime, sabotage, may_activate=True)

        # Nothing landed, not even the change the guard does not cover.
        self.assertEqual(runtime.active.id, state.id)
        self.assertEqual(run(runtime, INCREMENT), 1)

        run(runtime, COMPILE, 2, may_activate=True)

        self.assertEqual(run(runtime, POWER, 3), 9)

    def test_language_errors_leave_the_program_unchanged(self) -> None:
        broken = EntityID("broken")
        broken_links = EntityID("broken.links")
        one = code(("x",), ("lit", 1))
        two = code(("x",), ("lit", 2))

        for body in (
            ("activate",),
            ("activate", "power"),
            ("activate", "missing", one),
            ("activate", "counter", code((), ("lit", 1))),  # a cell
            ("activate", "power", ("lit", 5)),  # not a function value
            ("activate", "power", one, "power", two),  # named twice
            ("function", ("lit", (1,)), ("lit", ("lit", 1))),
            ("function", ("lit", ("x", "x")), ("lit", ("lit", 1))),
            ("function", ("lit", ()), ("lit", ())),
            ("quote", ("unquote",)),
            ("quote", ("add", ("unquote", ("lit", 1), ("lit", 2)), ("lit", 3))),
        ):
            with self.subTest(body=body):
                runtime = runtime_for({
                    broken: Function((), body),
                    broken_links: links(broken, counter=COUNTER, power=POWER),
                })
                state = runtime.active.state

                with self.assertRaises(LanguageError):
                    run(runtime, broken, may_activate=True)

                self.assertEqual(runtime.active.id, state.id)
                self.assertEqual(runtime.active.holds, frozenset())


class CodeInFlightTests(unittest.TestCase):
    def test_next_call_enters_the_new_code(self) -> None:
        runtime = runtime_for()
        old = runtime.active

        # +1 in the old code, then +10 in the new code, in one run.
        self.assertEqual(run(runtime, BUMP, may_activate=True), 11)
        self.assertEqual(runtime.read(COUNTER), 11)
        self.assertTrue(old.retired)
        self.assertIsNone(runtime.previous)
        self.assertEqual(runtime.active.holds, frozenset())

    def test_running_function_finishes_its_old_body(self) -> None:
        runtime = runtime_for()

        self.assertEqual(run(runtime, REPLACE_SELF, may_activate=True), "old")
        self.assertEqual(run(runtime, REPLACE_SELF), "new")

    def test_second_activation_in_one_run_is_rejected(self) -> None:
        twice = EntityID("twice")
        twice_links = EntityID("twice.links")
        runtime = runtime_for({
            twice: Function(
                (),
                (
                    "seq",
                    ("activate", "power", code(("x",), ("lit", 2))),
                    ("activate", "power", code(("x",), ("lit", 3))),
                ),
            ),
            twice_links: links(twice, power=POWER),
        })
        old = runtime.active

        # The run's frames still hold the previous version.
        with self.assertRaises(ActivationRejected):
            run(runtime, twice, may_activate=True)

        self.assertEqual(run(runtime, POWER, 5), 2)
        self.assertTrue(old.retired)
        self.assertIsNone(runtime.previous)
        self.assertEqual(runtime.active.holds, frozenset())


if __name__ == "__main__":
    unittest.main()
