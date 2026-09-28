"""Acceptance tests for trials in the language (docs/language_trials.md).

These tests define how a running program exercises candidate code in an
isolated runtime before installing it. The implementation is done when they
pass unchanged.
"""

import unittest

from semiroh import (
    ActivationRejected,
    CellContentRejected,
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
)
from semiroh.lang import Function, LanguageError, links, run

COUNTER = EntityID("counter")
INCREMENT = EntityID("increment")
INCREMENT_LINKS = EntityID("increment.links")
POWER = EntityID("power")
EMIT = EntityID("emit")
EMIT_LINKS = EntityID("emit.links")
COMPILE = EntityID("compile")
COMPILE_LINKS = EntityID("compile.links")
INSTALL_IF = EntityID("install_if")
INSTALL_IF_LINKS = EntityID("install_if.links")
CHECKED_COMPILE = EntityID("checked_compile")
CHECKED_COMPILE_LINKS = EntityID("checked_compile.links")
TRY_INCREMENT = EntityID("try_increment")
TRY_INCREMENT_LINKS = EntityID("try_increment.links")
DRY_INCREMENT = EntityID("dry_increment")
DRY_INCREMENT_LINKS = EntityID("dry_increment.links")


def code(params: tuple, body: tuple) -> tuple:
    """An expression that evaluates to Function(params, body)."""

    return ("function", ("lit", params), ("lit", body))


def square() -> tuple:
    return code(("x",), ("mul", ("arg", "x"), ("arg", "x")))


def cube() -> tuple:
    return code(
        ("x",),
        ("mul", ("arg", "x"), ("mul", ("arg", "x"), ("arg", "x"))),
    )


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
})


def program(extra: dict | None = None) -> State:
    entities = {
        COUNTER: CellDeclaration(IntRange(0, 100), 0),
        INCREMENT: Function(
            (),
            ("write", "counter", ("add", ("read", "counter"), ("lit", 1))),
        ),
        INCREMENT_LINKS: links(INCREMENT, counter=COUNTER),
        POWER: Function(("x",), ("lit", 1)),
        # emit(n) builds the body of x to the power n (metaprogramming.md).
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
        # Install f as power only if power(x) gives the expected value.
        INSTALL_IF: Function(
            ("f", "x", "expected"),
            (
                "if",
                (
                    "eq",
                    ("trial", ("call", "power", ("arg", "x")), "power", ("arg", "f")),
                    ("arg", "expected"),
                ),
                ("seq", ("activate", "power", ("arg", "f")), ("lit", True)),
                ("lit", False),
            ),
        ),
        INSTALL_IF_LINKS: links(INSTALL_IF, power=POWER),
        CHECKED_COMPILE: Function(
            ("n", "x", "expected"),
            (
                "call",
                "install_if",
                ("function", ("lit", ("x",)), ("call", "emit", ("arg", "n"))),
                ("arg", "x"),
                ("arg", "expected"),
            ),
        ),
        CHECKED_COMPILE_LINKS: links(
            CHECKED_COMPILE,
            install_if=INSTALL_IF,
            emit=EMIT,
        ),
        TRY_INCREMENT: Function(
            ("step",),
            (
                "trial",
                ("call", "increment"),
                "increment",
                (
                    "function",
                    ("lit", ()),
                    (
                        "quote",
                        (
                            "write",
                            "counter",
                            (
                                "add",
                                ("read", "counter"),
                                ("lit", ("unquote", ("arg", "step"))),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        TRY_INCREMENT_LINKS: links(TRY_INCREMENT, increment=INCREMENT),
        DRY_INCREMENT: Function((), ("trial", ("call", "increment"))),
        DRY_INCREMENT_LINKS: links(DRY_INCREMENT, increment=INCREMENT),
        **(extra or {}),
    }

    return State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    })


def runtime_for(extra: dict | None = None) -> Runtime:
    return Runtime(program(extra), CONTEXT)


def with_function(name: str, body: tuple, **targets: EntityID) -> dict:
    """Extra entities: a function with no parameters and its links."""

    entity = EntityID(name)

    return {
        entity: Function((), body),
        EntityID(f"{name}.links"): links(entity, **targets),
    }


class TrialTests(unittest.TestCase):
    def assertUntouched(self, runtime: Runtime, state: State) -> None:
        self.assertEqual(runtime.active.id, state.id)
        self.assertEqual(runtime.versions, (runtime.active,))
        self.assertEqual(runtime.active.holds, frozenset())

    def test_program_tests_code_before_installing_it(self) -> None:
        runtime = runtime_for()

        self.assertIs(run(runtime, CHECKED_COMPILE, 3, 2, 8, may_activate=True), True)
        self.assertEqual(run(runtime, POWER, 3), 27)

        state = runtime.active.state

        # Square of 2 is not 5: the candidate is tried and not installed.
        self.assertIs(run(runtime, CHECKED_COMPILE, 2, 2, 5, may_activate=True), False)
        self.assertEqual(run(runtime, POWER, 3), 27)
        self.assertUntouched(runtime, state)

    def test_trial_does_not_touch_the_real_runtime(self) -> None:
        runtime = runtime_for()
        run(runtime, INCREMENT)
        state = runtime.active.state
        active = runtime.active

        # The candidate starts from a copy of the counter and adds 10.
        self.assertEqual(run(runtime, TRY_INCREMENT, 10, may_activate=True), 11)

        self.assertEqual(runtime.read(COUNTER), 1)
        self.assertIs(runtime.active, active)
        self.assertUntouched(runtime, state)
        self.assertEqual(run(runtime, INCREMENT), 2)

    def test_trial_without_changes_runs_in_isolation(self) -> None:
        runtime = runtime_for()
        state = runtime.active.state

        self.assertEqual(run(runtime, DRY_INCREMENT, may_activate=True), 1)

        self.assertEqual(runtime.read(COUNTER), 0)
        self.assertUntouched(runtime, state)

    def test_trial_needs_the_capability(self) -> None:
        runtime = runtime_for()
        state = runtime.active.state

        for entry, args in ((TRY_INCREMENT, (10,)), (DRY_INCREMENT, ())):
            with self.subTest(entry=entry):
                with self.assertRaises(ActivationRejected):
                    run(runtime, entry, *args)

                self.assertEqual(runtime.read(COUNTER), 0)
                self.assertUntouched(runtime, state)

    def test_code_under_trial_gets_no_activation_capability(self) -> None:
        runtime = runtime_for(with_function(
            "nested",
            ("trial", ("call", "compile", ("lit", 2))),
            compile=COMPILE,
        ))
        state = runtime.active.state

        with self.assertRaises(ActivationRejected):
            run(runtime, EntityID("nested"), may_activate=True)

        self.assertEqual(run(runtime, POWER, 3), 1)
        self.assertUntouched(runtime, state)

    def test_trials_are_not_limited_by_the_two_version_bound(self) -> None:
        runtime = runtime_for(with_function(
            "many",
            (
                "seq",
                ("trial", ("call", "power", ("lit", 3)), "power", cube()),
                ("activate", "power", square()),
                ("trial", ("call", "power", ("lit", 3)), "power", cube()),
            ),
            power=POWER,
        ))

        self.assertEqual(run(runtime, EntityID("many"), may_activate=True), 27)
        self.assertEqual(run(runtime, POWER, 3), 9)
        self.assertEqual(runtime.versions, (runtime.active,))

    def test_program_constraints_reject_a_candidate(self) -> None:
        extra = {
            EntityID("power.guard"): Relation(
                "guard",
                {"code": POWER},
                Role("code", External("pure")),
            ),
            **with_function(
                "impure",
                (
                    "trial",
                    ("call", "power", ("lit", 2)),
                    "power",
                    code(("x",), ("write", "counter", ("arg", "x"))),
                ),
                power=POWER,
            ),
        }
        runtime = runtime_for(extra)
        state = runtime.active.state

        with self.assertRaises(ActivationRejected):
            run(runtime, EntityID("impure"), may_activate=True)

        self.assertEqual(runtime.read(COUNTER), 0)
        self.assertUntouched(runtime, state)

    def test_failure_in_the_candidate_stops_the_run(self) -> None:
        for error, trial in (
            (
                LanguageError,
                (
                    "trial",
                    ("call", "power", ("lit", 2)),
                    "power",
                    code(("x",), ("frobnicate",)),
                ),
            ),
            (
                CellContentRejected,
                (
                    "trial",
                    ("call", "increment"),
                    "increment",
                    code(
                        (),
                        ("write", "counter", ("add", ("read", "counter"), ("lit", 500))),
                    ),
                ),
            ),
        ):
            with self.subTest(error=error.__name__):
                runtime = runtime_for(with_function(
                    "careful",
                    ("seq", trial, ("activate", "power", square())),
                    increment=INCREMENT,
                    power=POWER,
                ))
                state = runtime.active.state

                with self.assertRaises(error):
                    run(runtime, EntityID("careful"), may_activate=True)

                # The activation after the trial never ran.
                self.assertEqual(run(runtime, POWER, 3), 1)
                self.assertEqual(runtime.read(COUNTER), 0)
                self.assertUntouched(runtime, state)

    def test_language_errors(self) -> None:
        for body in (
            ("trial",),
            ("trial", ("lit", 1)),  # not a call form
            ("trial", ("call", "missing")),
            ("trial", ("call", "power", ("lit", 1)), "power"),
            ("trial", ("call", "power", ("lit", 1)), "counter", code((), ("lit", 1))),
            ("trial", ("call", "power", ("lit", 1)), "power", ("lit", 5)),
        ):
            with self.subTest(body=body):
                runtime = runtime_for(with_function(
                    "broken",
                    body,
                    counter=COUNTER,
                    power=POWER,
                ))
                state = runtime.active.state

                with self.assertRaises(LanguageError):
                    run(runtime, EntityID("broken"), may_activate=True)

                self.assertUntouched(runtime, state)


if __name__ == "__main__":
    unittest.main()
