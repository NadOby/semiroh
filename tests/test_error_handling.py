"""Acceptance tests for error handling (docs/error_handling.md, roadmap
task 20).

``catch`` turns a failure into ``("ok", value)`` or ``("failed", error)``;
``raise`` fails with a program's own error; an error is
``(origin, kind, detail, where)``. These tests failed before task 20 added
``catch`` and ``raise``. That earlier programs keep their identity, text and
bytecode is the golden check's job (tests/golden.py).
"""

from __future__ import annotations

import unittest
from typing import Any, Mapping

from shear import (
    ActivationRejected,
    CellContentRejected,
    CellDeclaration,
    ConstraintResult,
    EntityID,
    EvaluationContext,
    Evaluator,
    External,
    IntRange,
    RelationConstraintRejected,
    Runtime,
    State,
    Value,
    canonical_serialize,
    canonicalize,
)
from shear import operations
from shear.bytecode import CALL_DEPTH_LIMIT
from shear.examples import EXAMPLES, Example, Raises
from shear.examples._support import program
from shear.lang import (
    CallDepthExceeded,
    Function,
    LanguageError,
    define,
    function_at,
    links,
    load,
    run,
)
from shear.relations import relation_of
from shear.syntax import SourceError, parse, render_program

F = EntityID("f")
G = EntityID("g")
FETCH = EntityID("fetch")
BALANCE = EntityID("balance")
LOG = EntityID("log")
POWER = EntityID("power")
SPIN = EntityID("spin")
DEEP = EntityID("deep")


def same(left: Any, right: Any) -> bool:
    return canonical_serialize(canonicalize(left)) == canonical_serialize(
        canonicalize(right)
    )


def runtime_of(
    entities: Mapping[EntityID, Any],
    context: EvaluationContext | None = None,
) -> Runtime:
    return Runtime(load(program(entities)), context)


def node(runtime: Runtime, function: EntityID, kind: str, **roles: Any) -> EntityID:
    """The one node of ``kind`` in ``function`` whose roles include ``roles``."""

    state = runtime.active.state
    found = []

    for entity in state.owned_subtree(function):
        relation = (
            None if entity == function else relation_of(state.values[entity])
        )

        if (
            relation is not None
            and relation.kind == kind
            and all(relation.roles.get(k) == v for k, v in roles.items())
        ):
            found.append(entity)

    assert len(found) == 1, (function, kind, found)
    return found[0]


def failed(origin: str, kind: str, detail: Any, where: tuple) -> tuple:
    return ("failed", (origin, kind, detail, where))


def out_of_range(index: int, length: int) -> tuple:
    return (("index", index), ("length", length), ("operation", "item"))


class CatchTests(unittest.TestCase):
    def assertSame(self, actual: Any, expected: Any) -> None:
        self.assertTrue(same(actual, expected), f"{actual!r} != {expected!r}")

    def test_a_returned_value_is_wrapped_as_ok(self) -> None:
        runtime = runtime_of({F: Function((), ("catch", ("lit", 5)))})

        self.assertSame(run(runtime, F), ("ok", 5))

    def test_a_value_shaped_like_a_failure_stays_wrapped(self) -> None:
        runtime = runtime_of({F: Function((), ("catch", ("lit", ("failed", 1))))})

        self.assertSame(run(runtime, F), ("ok", ("failed", 1)))

    def test_a_broken_language_rule_becomes_a_failed_value(self) -> None:
        runtime = runtime_of({
            FETCH: Function(("t",), ("catch", ("item", ("arg", "t"), ("lit", 3)))),
        })

        self.assertSame(
            run(runtime, FETCH, (1, 2)),
            failed(
                "language",
                "out_of_range",
                out_of_range(3, 2),
                (FETCH, node(runtime, FETCH, "item")),
            ),
        )

    def test_wrong_kind_names_the_kind_it_got_not_the_operand(self) -> None:
        runtime = runtime_of({
            F: Function(("v",), ("catch", ("add", ("lit", 1), ("arg", "v")))),
        })

        self.assertSame(
            run(runtime, F, "x"),
            failed(
                "language",
                "wrong_kind",
                (("expected", "int"), ("got", "str"), ("operation", "add")),
                (F, node(runtime, F, "add")),
            ),
        )

    def test_a_failure_in_a_callee_names_the_callees_node(self) -> None:
        runtime = runtime_of({
            F: Function(("t",), ("catch", ("call", "fetch", ("arg", "t")))),
            EntityID("f.links"): links(F, fetch=FETCH),
            FETCH: Function(("t",), ("item", ("arg", "t"), ("lit", 3))),
        })

        self.assertSame(
            run(runtime, F, (1, 2)),
            failed(
                "language",
                "out_of_range",
                out_of_range(3, 2),
                (FETCH, node(runtime, FETCH, "item")),
            ),
        )

    def test_wrong_arity_is_reported_at_the_call(self) -> None:
        runtime = runtime_of({
            F: Function(("x",), ("catch", ("call", "g", ("arg", "x"), ("arg", "x")))),
            EntityID("f.links"): links(F, g=G),
            G: Function(("y",), ("arg", "y")),
        })

        self.assertSame(
            run(runtime, F, 1),
            failed(
                "language",
                "arity",
                (("expected", 1), ("function", G), ("got", 2)),
                (F, node(runtime, F, "call")),
            ),
        )

    def test_the_filter_catches_a_listed_kind(self) -> None:
        runtime = runtime_of({
            FETCH: Function(
                ("t",),
                (
                    "catch",
                    ("item", ("arg", "t"), ("lit", 3)),
                    ("wrong_kind", "out_of_range"),
                ),
            ),
        })

        self.assertSame(
            run(runtime, FETCH, (1, 2)),
            failed(
                "language",
                "out_of_range",
                out_of_range(3, 2),
                (FETCH, node(runtime, FETCH, "item")),
            ),
        )

    def test_an_unlisted_kind_passes_through_unchanged(self) -> None:
        runtime = runtime_of({
            F: Function(("t",), ("catch", ("call", "fetch", ("arg", "t")))),
            EntityID("f.links"): links(F, fetch=FETCH),
            FETCH: Function(
                ("t",),
                ("catch", ("item", ("arg", "t"), ("lit", 3)), ("wrong_kind",)),
            ),
        })
        error = (
            "language",
            "out_of_range",
            out_of_range(3, 2),
            (FETCH, node(runtime, FETCH, "item")),
        )

        self.assertSame(run(runtime, F, (1, 2)), ("failed", error))

        with self.assertRaises(LanguageError) as raised:
            run(runtime, FETCH, (1, 2))

        self.assertSame(raised.exception.error, error)

    def test_the_filter_matches_a_programs_own_kind(self) -> None:
        runtime = runtime_of({
            F: Function(
                (),
                ("catch", ("raise", ("lit", "missing"), ("lit", 0)), ("missing",)),
            ),
        })

        self.assertSame(
            run(runtime, F),
            failed("program", "missing", 0, (F, node(runtime, F, "raise"))),
        )


class RaiseTests(unittest.TestCase):
    def assertSame(self, actual: Any, expected: Any) -> None:
        self.assertTrue(same(actual, expected), f"{actual!r} != {expected!r}")

    def test_raise_fails_with_a_program_error(self) -> None:
        runtime = runtime_of({
            F: Function(
                ("k",),
                (
                    "catch",
                    (
                        "raise",
                        ("lit", "missing"),
                        ("tuple", ("tuple", ("lit", "key"), ("arg", "k"))),
                    ),
                ),
            ),
        })

        self.assertSame(
            run(runtime, F, "z"),
            failed(
                "program",
                "missing",
                (("key", "z"),),
                (F, node(runtime, F, "raise")),
            ),
        )

    def test_a_program_may_raise_a_kind_of_the_language(self) -> None:
        runtime = runtime_of({
            F: Function(
                (),
                ("catch", ("raise", ("lit", "out_of_range"), ("lit", 7))),
            ),
        })

        self.assertSame(
            run(runtime, F),
            failed("program", "out_of_range", 7, (F, node(runtime, F, "raise"))),
        )

    def test_a_kind_that_is_not_a_string_is_a_language_error(self) -> None:
        runtime = runtime_of({
            F: Function((), ("catch", ("raise", ("lit", 1), ("lit", 0)))),
        })

        self.assertSame(
            run(runtime, F),
            failed(
                "language",
                "wrong_kind",
                (("expected", "str"), ("got", "int"), ("operation", "raise")),
                (F, node(runtime, F, "raise")),
            ),
        )

    def test_an_uncaught_raise_escapes_as_a_language_error(self) -> None:
        runtime = runtime_of({
            F: Function((), ("raise", ("lit", "missing"), ("lit", 0))),
        })

        with self.assertRaises(LanguageError) as raised:
            run(runtime, F)

        self.assertSame(
            raised.exception.error,
            ("program", "missing", 0, (F, node(runtime, F, "raise"))),
        )


def _cells(log_first: bool) -> dict[EntityID, Any]:
    writes = (
        ("write", "log", ("lit", 1)),
        ("write", "balance", ("lit", -1)),
    )
    return {
        BALANCE: CellDeclaration(IntRange(0, None), 10),
        LOG: CellDeclaration(IntRange(0, None), 0),
        F: Function((), ("catch", ("seq", *writes)) if log_first else writes[1]),
        EntityID("f.links"): links(F, balance=BALANCE, log=LOG),
    }


class RuntimeAndLimitTests(unittest.TestCase):
    def assertSame(self, actual: Any, expected: Any) -> None:
        self.assertTrue(same(actual, expected), f"{actual!r} != {expected!r}")

    def test_a_refused_write_is_a_runtime_error_and_earlier_writes_stay(self) -> None:
        runtime = runtime_of(_cells(log_first=True))

        self.assertSame(
            run(runtime, F),
            failed(
                "runtime",
                "cell_rejected",
                (("cell", BALANCE), ("constraint", "violated"), ("operation", "write")),
                (F, node(runtime, F, "write", cell=BALANCE)),
            ),
        )
        self.assertEqual(runtime.read(LOG), 1)
        self.assertEqual(runtime.read(BALANCE), 10)

    def test_an_unknown_constraint_result_is_reported_as_unknown(self) -> None:
        audited = EntityID("audited")
        context = EvaluationContext(externals={
            "audit": Evaluator(
                lambda value: ConstraintResult.SATISFIED
                if value < 100
                else ConstraintResult.UNKNOWN
            ),
        })
        runtime = runtime_of(
            {
                audited: CellDeclaration(External("audit"), 0),
                F: Function(("v",), ("catch", ("write", "audited", ("arg", "v")))),
                EntityID("f.links"): links(F, audited=audited),
            },
            context,
        )

        self.assertSame(
            run(runtime, F, 500),
            failed(
                "runtime",
                "cell_rejected",
                (("cell", audited), ("constraint", "unknown"), ("operation", "write")),
                (F, node(runtime, F, "write")),
            ),
        )
        self.assertEqual(runtime.read(audited), 0)

    def test_activating_without_the_capability_is_a_runtime_error(self) -> None:
        runtime = runtime_of({
            F: Function(
                (),
                (
                    "catch",
                    (
                        "activate",
                        "g",
                        ("function", ("lit", ()), ("lit", ("lit", 2))),
                    ),
                ),
            ),
            EntityID("f.links"): links(F, g=G),
            G: Function((), ("lit", 1)),
        })

        self.assertSame(
            run(runtime, F),
            failed(
                "runtime",
                "no_capability",
                (("operation", "activate"),),
                (F, node(runtime, F, "activate")),
            ),
        )
        self.assertEqual(run(runtime, G), 1)

    def test_the_depth_limit_is_a_limit_error_and_the_program_goes_on(self) -> None:
        runtime = runtime_of({
            F: Function((), ("catch", ("call", "spin", ("lit", 0)))),
            EntityID("f.links"): links(F, spin=SPIN),
            SPIN: Function(
                ("n",),
                ("add", ("lit", 1), ("call", "spin", ("arg", "n"))),
            ),
            EntityID("spin.links"): links(SPIN, spin=SPIN),
        })

        result = run(runtime, F)

        self.assertSame(
            result,
            failed(
                "limit",
                "depth_limit",
                (("limit", CALL_DEPTH_LIMIT),),
                (SPIN, node(runtime, SPIN, "call")),
            ),
        )
        self.assertEqual(runtime.active.holds, frozenset())
        self.assertSame(run(runtime, F), result)

    def test_a_failure_under_trial_is_caught_and_the_program_is_unchanged(self) -> None:
        runtime = runtime_of({
            POWER: Function(("x",), ("lit", 1)),
            F: Function(
                ("x",),
                (
                    "catch",
                    (
                        "trial",
                        ("call", "power", ("arg", "x")),
                        "power",
                        (
                            "function",
                            ("lit", ("y",)),
                            ("lit", ("item", ("lit", ()), ("arg", "y"))),
                        ),
                    ),
                ),
            ),
            EntityID("f.links"): links(F, power=POWER),
        })
        before = runtime.active.state.id

        result = run(runtime, F, 2, may_activate=True)

        self.assertEqual(result[0], "failed")
        origin, kind, detail, where = result[1]
        self.assertEqual((origin, kind), ("language", "out_of_range"))
        self.assertSame(detail, out_of_range(2, 0))
        self.assertSame(where[0], POWER)
        self.assertEqual(runtime.active.state.id, before)
        self.assertEqual(run(runtime, POWER, 2), 1)


def _deep() -> dict[EntityID, Any]:
    """deep(n) fails n calls down; f(n) catches it, then activates g."""

    return {
        DEEP: Function(
            ("n",),
            (
                "if",
                ("eq", ("arg", "n"), ("lit", 0)),
                ("item", ("lit", ()), ("lit", 0)),
                ("add", ("lit", 1), ("call", "deep", ("sub", ("arg", "n"), ("lit", 1)))),
            ),
        ),
        EntityID("deep.links"): links(DEEP, deep=DEEP),
        G: Function((), ("lit", 1)),
        F: Function(
            ("n",),
            (
                "seq",
                ("catch", ("call", "deep", ("arg", "n"))),
                ("activate", "g", ("function", ("lit", ()), ("lit", ("lit", 2)))),
                ("lit", "done"),
            ),
        ),
        EntityID("f.links"): links(F, deep=DEEP, g=G),
    }


class UnwindingTests(unittest.TestCase):
    def test_a_caught_failure_releases_every_call_it_unwinds(self) -> None:
        runtime = runtime_of(_deep())

        self.assertEqual(run(runtime, F, 50, may_activate=True), "done")
        self.assertEqual(runtime.active.holds, frozenset())
        self.assertTrue(all(version.retired for version in runtime.versions[:-1]))

        # A hold leaked by an unwound call would keep the first version alive
        # and reject this second activation (activation_model.md section 7).
        self.assertEqual(run(runtime, F, 50, may_activate=True), "done")
        self.assertEqual(run(runtime, G), 2)

    def test_a_tail_loop_inside_a_caught_call_does_not_grow(self) -> None:
        loop = EntityID("loop")
        runtime = runtime_of({
            loop: Function(
                ("n",),
                (
                    "if",
                    ("eq", ("arg", "n"), ("lit", 0)),
                    ("lit", "end"),
                    ("call", "loop", ("sub", ("arg", "n"), ("lit", 1))),
                ),
            ),
            EntityID("loop.links"): links(loop, loop=loop),
            F: Function(("n",), ("catch", ("call", "loop", ("arg", "n")))),
            EntityID("f.links"): links(F, loop=loop),
        })

        self.assertTrue(same(run(runtime, F, CALL_DEPTH_LIMIT + 10), ("ok", "end")))


class EscapingErrorTests(unittest.TestCase):
    def assertSame(self, actual: Any, expected: Any) -> None:
        self.assertTrue(same(actual, expected), f"{actual!r} != {expected!r}")

    def test_an_escaping_failure_carries_what_catch_would_give(self) -> None:
        entities = {
            FETCH: Function(("t",), ("item", ("arg", "t"), ("lit", 3))),
            F: Function(("t",), ("catch", ("call", "fetch", ("arg", "t")))),
            EntityID("f.links"): links(F, fetch=FETCH),
        }
        runtime = runtime_of(entities)

        with self.assertRaises(LanguageError) as raised:
            run(runtime, FETCH, (1, 2))

        self.assertSame(("failed", raised.exception.error), run(runtime, F, (1, 2)))

    def test_runtime_and_limit_failures_keep_their_classes(self) -> None:
        runtime = runtime_of(_cells(log_first=False))

        with self.assertRaises(CellContentRejected) as rejected:
            run(runtime, F)

        self.assertEqual(rejected.exception.error[:2], ("runtime", "cell_rejected"))

        spinning = runtime_of({
            SPIN: Function(("n",), ("add", ("lit", 1), ("call", "spin", ("arg", "n")))),
            EntityID("spin.links"): links(SPIN, spin=SPIN),
        })

        with self.assertRaises(CallDepthExceeded) as exceeded:
            run(spinning, SPIN, 0)

        self.assertEqual(exceeded.exception.error[:2], ("limit", "depth_limit"))

    def test_describe_renders_an_error_for_people(self) -> None:
        from shear.errors import describe

        runtime = runtime_of({
            FETCH: Function(("t",), ("catch", ("item", ("arg", "t"), ("lit", 3)))),
        })
        text = describe(run(runtime, FETCH, (1, 2))[1])

        self.assertIsInstance(text, str)
        self.assertIn("out_of_range", text)
        self.assertIn("fetch", text)

    def test_the_catalogue_gives_each_kind_its_origin(self) -> None:
        from shear.errors import KINDS

        pinned = {
            "wrong_kind": "language",
            "out_of_range": "language",
            "arity": "language",
            "absent": "language",
            "not_a_function": "language",
            "not_a_cell": "language",
            "name_in_scope": "language",
            "unknown_name": "language",
            "malformed": "language",
            "invalid_code": "language",
            "cell_rejected": "runtime",
            "relation_rejected": "runtime",
            "activation_rejected": "runtime",
            "activation_conflict": "runtime",
            "no_capability": "runtime",
            "depth_limit": "limit",
        }

        self.assertLessEqual(pinned.items(), dict(KINDS).items())
        self.assertLessEqual(set(KINDS.values()), {"language", "runtime", "limit"})


class GraphFormAndSyntaxTests(unittest.TestCase):
    def test_catch_and_raise_are_operations(self) -> None:
        self.assertEqual(operations.OPERATIONS["catch"].code, ("body",))
        self.assertEqual(operations.OPERATIONS["raise"].code, ("kind", "detail"))
        self.assertTrue(operations.OPERATIONS["raise"].positional)

    def test_catch_and_raise_round_trip_through_graph_form(self) -> None:
        bodies = (
            ("catch", ("item", ("arg", "t"), ("lit", 0))),
            ("catch", ("item", ("arg", "t"), ("lit", 0)), ("wrong_kind", "out_of_range")),
            ("raise", ("lit", "missing"), ("tuple", ("lit", "key"), ("arg", "t"))),
        )

        for body in bodies:
            with self.subTest(body=body):
                state = load(program({F: Function(("t",), body)}))
                kinds = [
                    relation_of(state.values[entity]).kind
                    for entity in state.owned_subtree(F)
                    if entity != F
                ]

                # An unknown operation would load as one invalid node that
                # collapses back to the same input form.
                self.assertIn(body[0], kinds)
                self.assertNotIn("invalid", kinds)
                self.assertEqual(function_at(state, F).body, body)

    def test_a_malformed_catch_fails_closed(self) -> None:
        for kinds in ((), ("a", "a"), (1,), ("",)):
            with self.subTest(kinds=kinds):
                runtime = runtime_of({F: Function((), ("catch", ("lit", 1), kinds))})

                with self.assertRaises(LanguageError) as raised:
                    run(runtime, F)

                self.assertEqual(raised.exception.error[:2], ("language", "invalid_code"))

    def test_catch_and_raise_parse_and_render(self) -> None:
        cases = (
            (
                'fn f(t):\n    catch(item(t, 3))\n',
                ("catch", ("item", ("arg", "t"), ("lit", 3))),
            ),
            (
                'fn f(t):\n    catch(item(t, 3), "wrong_kind", "out_of_range")\n',
                (
                    "catch",
                    ("item", ("arg", "t"), ("lit", 3)),
                    ("wrong_kind", "out_of_range"),
                ),
            ),
            (
                'fn f(k):\n    raise("missing", (("key", k),))\n',
                (
                    "raise",
                    ("lit", "missing"),
                    ("tuple", ("tuple", ("lit", "key"), ("arg", "k"))),
                ),
            ),
        )

        for text, body in cases:
            with self.subTest(text=text):
                state = load(parse(text))
                self.assertEqual(function_at(state, F).body, body)
                self.assertEqual(render_program(state), text)

    def test_catch_and_raise_are_reserved_and_kinds_are_literals(self) -> None:
        for text in (
            "fn catch(x):\n    x\n",
            "fn raise(x):\n    x\n",
            "fn f(t, k):\n    catch(item(t, 0), k)\n",
        ):
            with self.subTest(text=text):
                with self.assertRaises(SourceError):
                    parse(text)

    def test_wrapping_any_corpus_body_in_catch_keeps_every_node(self) -> None:
        for example in EXAMPLES:
            state = load(example.program)

            for entity in sorted(state.values, key=lambda e: e.value):
                relation = relation_of(state.values[entity])

                if relation is None or relation.kind != "definition":
                    continue

                with self.subTest(example=example.name, function=entity.value):
                    function = function_at(state, entity)
                    wrapped = define(
                        state,
                        {entity: Function(function.params, ("catch", function.body))},
                    ).destination
                    old = set(state.owned_subtree(entity)) - {entity}
                    new = set(wrapped.owned_subtree(entity)) - {entity} - old

                    for kept in old:
                        self.assertEqual(wrapped.values.get(kept), state.values[kept])

                    self.assertEqual(
                        [relation_of(wrapped.values[e]).kind for e in new],
                        ["catch"],
                    )


# -- The canary corpus through catch ---------------------------------------

_ORIGINS: tuple[tuple[type[BaseException], frozenset[str]], ...] = (
    (CallDepthExceeded, frozenset({"limit"})),
    (LanguageError, frozenset({"language", "program"})),
    (CellContentRejected, frozenset({"runtime"})),
    (RelationConstraintRejected, frozenset({"runtime"})),
    (ActivationRejected, frozenset({"runtime"})),
)


def _origins(error: type[BaseException]) -> frozenset[str]:
    for cls, origins in _ORIGINS:
        if issubclass(error, cls):
            return origins

    raise AssertionError(f"no origin for {error.__name__}")


def _probe(entry: EntityID, arity: int) -> EntityID:
    return EntityID(f"probe.{entry.value}.{arity}")


def _probed(example: Example, kinds: tuple[str, ...] | None) -> State:
    """The example's program plus, per entry and arity a step uses, a probe
    function that calls the entry under ``catch`` (with ``kinds`` if given)."""

    values = dict(example.program.values)

    for scenario in example.scenarios:
        for step in scenario:
            probe = _probe(step.entry, len(step.args))

            if probe in values:
                continue

            params = tuple(f"a{index}" for index in range(len(step.args)))
            call = ("call", "target", *(("arg", name) for name in params))
            body = ("catch", call) if kinds is None else ("catch", call, kinds)
            probe_links = EntityID(f"{probe.value}.links")
            values[probe] = Value.create(probe, Function(params, body))
            values[probe_links] = Value.create(
                probe_links,
                links(probe, target=step.entry),
            )

    return State.create(values)


class CorpusThroughCatchTests(unittest.TestCase):
    """Every step of every canary corpus program, called through ``catch``."""

    def play(self, kinds: tuple[str, ...] | None) -> None:
        from shear.errors import KINDS

        for example in EXAMPLES:
            program_state = load(_probed(example, kinds))

            for index, scenario in enumerate(example.scenarios):
                runtime = Runtime(program_state, example.context)

                for number, step in enumerate(scenario):
                    label = f"{example.name}: scenario {index}, step {number}"
                    probe = _probe(step.entry, len(step.args))

                    with self.subTest(step=label):
                        try:
                            result = run(
                                runtime,
                                probe,
                                *step.args,
                                may_activate=step.may_activate,
                            )
                        except Exception as exc:
                            # Only a filter that matches nothing lets one out.
                            self.assertIsNotNone(kinds, f"{label}: raised {exc!r}")
                            self.assertIsInstance(step.expect, Raises)
                            self.assertIsInstance(exc, step.expect.error)
                            self.assertIn(exc.error[0], _origins(type(exc)))
                        else:
                            if isinstance(step.expect, Raises):
                                self.assertIsNone(kinds, f"{label}: caught")
                                self.assertEqual(result[0], "failed", label)
                                origin, kind, _, where = result[1]
                                self.assertIn(origin, _origins(step.expect.error))

                                if origin != "program":
                                    self.assertEqual(KINDS[kind], origin)

                                self.assertEqual(len(where), 2)
                            else:
                                self.assertTrue(
                                    same(result, ("ok", step.expect)),
                                    f"{label}: {result!r}",
                                )

                        for cell, expected in step.cells.items():
                            self.assertTrue(
                                same(runtime.read(cell), expected),
                                f"{label}: cell {cell.value}",
                            )

    def test_every_step_through_catch_gives_ok_or_the_expected_failure(self) -> None:
        self.play(None)

    def test_a_filter_that_matches_nothing_changes_nothing(self) -> None:
        self.play(("no_such_kind",))


if __name__ == "__main__":
    unittest.main()
