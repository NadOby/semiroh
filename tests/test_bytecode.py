"""Acceptance and regression tests for bytecode and the VM (docs/bytecode.md).

The chunks and the machine are tested through their contracts: what a node
lowers to, which nodes are lowered again after an edit, that a run needs no
host stack, and that operands are checked and evaluated in the order they
always were. Everything else about running code is covered by the
acceptance suites of the language, which run on the VM unchanged.
"""

import random
import sys
import unittest

from semiroh import (
    CellDeclaration,
    ConstraintResult,
    EntityID,
    EvaluationContext,
    Evaluator,
    External,
    IntRange,
    Runtime,
    State,
    Value,
    relation_of,
    transform_with_mapping,
)
from semiroh.bytecode import chunk_of, disassemble, lower, lowered_count
from semiroh.lang import Function, LanguageError, define, function_at, links, load, run

C = EntityID("c")


def program(
    functions: dict[str, Function],
    linked: dict[str, tuple[str, ...]] | None = None,
) -> State:
    """The cell ``c``, and the functions. A function links the cell as
    ``c`` and the functions ``linked`` names for it: every function unless
    ``linked`` says otherwise.
    """

    entities = {C: CellDeclaration(IntRange(0, 100), 0)}

    for name, function in functions.items():
        entity = EntityID(name)
        names = tuple(functions) if linked is None else linked.get(name, ())
        entities[entity] = function
        entities[EntityID(f"{name}.links")] = links(
            entity, c=C, **{other: EntityID(other) for other in names}
        )

    return State.create({
        entity: Value.create(entity, content)
        for entity, content in entities.items()
    })


def runtime_of(
    functions: dict[str, Function],
    linked: dict[str, tuple[str, ...]] | None = None,
) -> Runtime:
    return Runtime(load(program(functions, linked)))


def forget_chunks(state: State) -> None:
    """Drop every derived chunk, as if no node had been run."""

    for value in state.values.values():
        value.__dict__.pop("_chunk", None)


def stack_depth() -> int:
    depth = 0
    frame = sys._getframe()

    while frame is not None:
        depth += 1
        frame = frame.f_back

    return depth


def lit(value) -> tuple:
    return ("lit", value)


def arg(name: str) -> tuple:
    return ("arg", name)


class LoweringTests(unittest.TestCase):
    def state_of(self, body: tuple, *params: str) -> State:
        return load(program({"f": Function(params, body)}))

    def root_chunk(self, body: tuple, *params: str) -> tuple:
        state = self.state_of(body, *params)
        definition = relation_of(state.values[EntityID("f")])

        return chunk_of(state, definition.roles["body"])

    def test_leaves_are_one_instruction_and_an_end(self) -> None:
        self.assertEqual(self.root_chunk(lit(7)), (("LIT", 7), ("END",)))
        self.assertEqual(
            self.root_chunk(arg("n"), "n"),
            (("ARG", "n"), ("END",)),
        )

    def test_a_chunk_names_its_children_by_entity(self) -> None:
        chunk = self.root_chunk(("add", arg("n"), lit(1)), "n")

        self.assertEqual(
            disassemble(chunk),
            "\n".join([
                "EVAL f/0.1",
                "INT 'add'",
                "EVAL f/0.2",
                "INT 'add'",
                "ADD",
                "END",
            ]),
        )

    def test_operands_are_checked_before_the_next_one_runs(self) -> None:
        # The order every check has always had: the left operand is
        # evaluated and checked before the right one runs.
        for body, kinds in (
            (("lt", lit(1), lit(2)), ["INT", "INT"]),
            (("item", ("tuple", lit(1)), lit(0)), ["TUPLE", "INT"]),
            (("slice", ("tuple", lit(1)), lit(0), lit(1)), ["TUPLE", "INT", "INT"]),
            (("concat", ("tuple",), ("tuple",)), ["TUPLE", "TUPLE"]),
        ):
            with self.subTest(body=body[0]):
                chunk = self.root_chunk(body)
                ops = [instruction[0] for instruction in chunk]
                checks = [op for op in ops if op in ("INT", "TUPLE")]

                self.assertEqual(checks, kinds)
                self.assertEqual(ops[0], "EVAL")
                self.assertEqual(ops[1], kinds[0])

    def test_let_checks_its_name_before_evaluating_the_value(self) -> None:
        chunk = self.root_chunk(("let", "x", lit(1), arg("x")))

        self.assertEqual(
            [instruction[0] for instruction in chunk],
            ["LETCHECK", "EVAL", "LETBIND", "END"],
        )

    def test_control_flow_hands_over_without_returning(self) -> None:
        chunk = self.root_chunk(("if", ("lt", lit(1), lit(2)), lit(3), lit(4)))
        self.assertEqual(
            [instruction[0] for instruction in chunk],
            ["EVAL", "BRANCH", "END"],
        )

        chunk = self.root_chunk(("seq", lit(1), lit(2), lit(3)))
        self.assertEqual(
            [instruction[0] for instruction in chunk],
            ["EVAL", "POP", "EVAL", "POP", "GOTO", "END"],
        )

    def test_a_call_names_its_target_and_argument_count(self) -> None:
        state = load(program({
            "f": Function((), ("call", "g", lit(1), lit(2))),
            "g": Function(("a", "b"), arg("a")),
        }))
        body = relation_of(state.values[EntityID("f")]).roles["body"]
        call = chunk_of(state, body)

        self.assertEqual(call[-2], ("CALL", EntityID("g"), 2))

    def test_lowering_reads_only_the_node(self) -> None:
        # Two functions with the same leaf lower it to equal chunks: no
        # owner, state or position is part of a chunk.
        state = load(program({
            "f": Function((), lit(5)),
            "g": Function((), lit(5)),
        }))

        def root(name: str) -> tuple:
            body = relation_of(state.values[EntityID(name)]).roles["body"]
            return lower(relation_of(state.values[body]))

        self.assertEqual(root("f"), root("g"))

    def test_invalid_code_lowers_to_a_raise_and_fails_when_run(self) -> None:
        chunk = self.root_chunk(("frob", lit(1)))

        self.assertEqual(
            chunk,
            (("RAISE", "unknown operation 'frob'"), ("END",)),
        )

        runtime = runtime_of({"f": Function((), ("frob", lit(1)))})

        with self.assertRaisesRegex(LanguageError, "f: unknown operation"):
            run(runtime, EntityID("f"))

    def test_an_entity_that_is_not_code_cannot_be_lowered(self) -> None:
        state = load(program({"f": Function((), lit(1))}))

        with self.assertRaisesRegex(LanguageError, "^f: c is not a code node"):
            chunk_of(state, C, EntityID("f"))

        with self.assertRaisesRegex(LanguageError, "^f: gone is not a code node"):
            chunk_of(state, EntityID("gone"), EntityID("f"))


class CacheTests(unittest.TestCase):
    F = EntityID("wide")
    WIDE = Function(
        ("n",),
        (
            "add",
            ("add", arg("n"), lit(1)),
            ("add", ("label", "edit", lit(2)), ("mul", arg("n"), lit(3))),
        ),
    )

    def runtime(self) -> Runtime:
        return runtime_of({
            "wide": self.WIDE,
            "other": Function(("x",), ("add", arg("x"), arg("x"))),
        })

    def lowered_by(self, action) -> int:
        before = lowered_count()
        action()

        return lowered_count() - before

    def test_a_node_is_lowered_once(self) -> None:
        runtime = self.runtime()

        self.assertEqual(self.lowered_by(lambda: run(runtime, self.F, 4)), 9)
        self.assertEqual(self.lowered_by(lambda: run(runtime, self.F, 5)), 0)

    def test_only_the_nodes_that_ran_are_lowered(self) -> None:
        runtime = runtime_of({
            "pick": Function(
                ("n",),
                ("if", ("lt", arg("n"), lit(1)), lit(10), ("add", lit(1), lit(2))),
            ),
        })
        pick = EntityID("pick")

        # if, lt, arg, lit, lit(10): the else branch has not run.
        self.assertEqual(self.lowered_by(lambda: run(runtime, pick, 0)), 5)
        # The else branch: add and its two operands.
        self.assertEqual(self.lowered_by(lambda: run(runtime, pick, 5)), 3)

    def test_an_edit_lowers_only_the_edited_node(self) -> None:
        runtime = self.runtime()
        self.assertEqual(run(runtime, self.F, 4), 5 + 2 + 12)

        runtime.activate(define(runtime.active.state, {(self.F, "edit"): lit(5)}))

        self.assertEqual(self.lowered_by(lambda: run(runtime, self.F, 4)), 1)
        self.assertEqual(run(runtime, self.F, 4), 5 + 5 + 12)

    def test_a_leaf_edit_lowers_one_node_however_big_the_function(self) -> None:
        # bytecode.md section 7: a function of 41 nodes and one of 401.
        for links_in_chain, nodes in ((20, 41), (200, 401)):
            with self.subTest(nodes=nodes):
                body = ("label", "edit", lit(1))

                for index in range(links_in_chain):
                    body = ("add", body, lit(index))

                runtime = runtime_of({"big": Function((), body)})
                big = EntityID("big")
                expected = 1 + sum(range(links_in_chain))

                self.assertEqual(run(runtime, big), expected)
                self.assertEqual(
                    len(runtime.active.state.owned_subtree(big)),
                    nodes,
                )

                runtime.activate(
                    define(runtime.active.state, {(big, "edit"): lit(5)})
                )

                self.assertEqual(self.lowered_by(lambda: run(runtime, big)), 1)
                self.assertEqual(run(runtime, big), expected + 4)

    def test_an_edit_that_adds_nodes_lowers_those_and_no_others(self) -> None:
        runtime = self.runtime()
        run(runtime, self.F, 4)

        replacement = ("mul", lit(2), ("add", lit(1), lit(1)))
        runtime.activate(define(runtime.active.state, {(self.F, "edit"): replacement}))

        # The labelled node with its new content, and four new nodes.
        self.assertEqual(self.lowered_by(lambda: run(runtime, self.F, 4)), 5)
        self.assertEqual(run(runtime, self.F, 4), 5 + 4 + 12)

    def test_replacing_one_function_lowers_no_other(self) -> None:
        runtime = self.runtime()
        other = EntityID("other")
        run(runtime, self.F, 4)
        run(runtime, other, 3)

        runtime.activate(define(
            runtime.active.state,
            {self.F: Function(("n",), ("mul", arg("n"), arg("n")))},
        ))

        self.assertEqual(self.lowered_by(lambda: run(runtime, other, 3)), 0)
        self.assertEqual(self.lowered_by(lambda: run(runtime, self.F, 4)), 3)
        self.assertEqual(run(runtime, self.F, 4), 16)

    def test_a_rename_lowers_only_the_calls_that_name_it(self) -> None:
        double, twice, quad = EntityID("double"), EntityID("twice"), EntityID("quad")
        runtime = runtime_of(
            {
                "double": Function(("x",), ("add", arg("x"), arg("x"))),
                "quad": Function(
                    ("x",),
                    ("call", "double", ("call", "double", arg("x"))),
                ),
            },
            linked={"quad": ("double",)},
        )
        self.assertEqual(run(runtime, quad, 3), 12)

        source = runtime.active.state
        mappings = {entity: entity for entity in source.values}
        mappings[double] = twice
        runtime.activate(transform_with_mapping(
            source,
            {twice: source.values[double].content},
            mappings,
        ))

        # The two call nodes are new versions (their target moved); the
        # argument node and both nodes of the callee are not.
        self.assertEqual(self.lowered_by(lambda: run(runtime, quad, 3)), 2)
        self.assertEqual(run(runtime, quad, 3), 12)

    def test_a_node_carried_into_a_new_state_keeps_its_chunk(self) -> None:
        runtime = self.runtime()
        run(runtime, self.F, 4)
        before = runtime.active.state
        runtime.activate(define(before, {(self.F, "edit"): lit(5)}))
        after = runtime.active.state
        untouched = sorted(before.owned_subtree(self.F))[1]

        self.assertIs(before.values[untouched], after.values[untouched])
        self.assertIs(
            chunk_of(before, untouched),
            chunk_of(after, untouched),
        )

    def test_running_does_not_change_semantic_identity(self) -> None:
        runtime = self.runtime()
        state = runtime.active.state
        versions = {entity: value.version_id for entity, value in state.values.items()}

        run(runtime, self.F, 4)

        self.assertEqual(runtime.active.state.id, state.id)
        self.assertEqual(
            {entity: value.version_id for entity, value in state.values.items()},
            versions,
        )
        self.assertEqual(
            Value.create(self.F, state.values[self.F].content),
            state.values[self.F],
        )


class DeepRecursionTests(unittest.TestCase):
    DEEP = Function(
        ("n",),
        (
            "if",
            ("lt", arg("n"), lit(1)),
            lit(0),
            ("add", arg("n"), ("call", "deep", ("sub", arg("n"), lit(1)))),
        ),
    )

    def test_recursion_is_not_bounded_by_the_host_stack(self) -> None:
        runtime = runtime_of({"deep": self.DEEP})
        limit = sys.getrecursionlimit()

        try:
            # Far too little for a host frame per call: 5000 calls would
            # need thousands of frames.
            sys.setrecursionlimit(stack_depth() + 80)
            result = run(runtime, EntityID("deep"), 5000)
        finally:
            sys.setrecursionlimit(limit)

        self.assertEqual(result, 5000 * 5001 // 2)
        self.assertEqual(runtime.active.holds, frozenset())

    def test_an_error_at_the_bottom_releases_every_frame(self) -> None:
        runtime = runtime_of({
            "bottom": Function(
                ("n",),
                (
                    "if",
                    ("lt", arg("n"), lit(1)),
                    ("add", lit(1), lit("x")),
                    ("add", lit(1), ("call", "bottom", ("sub", arg("n"), lit(1)))),
                ),
            ),
        })

        with self.assertRaisesRegex(LanguageError, "bottom: add operands"):
            run(runtime, EntityID("bottom"), 300)

        self.assertEqual(runtime.active.holds, frozenset())

    def test_an_error_names_the_function_that_raised_it(self) -> None:
        runtime = runtime_of({
            "outer": Function((), ("add", lit(1), ("call", "inner"))),
            "inner": Function((), arg("missing")),
        })

        with self.assertRaisesRegex(LanguageError, "^inner: unknown parameter"):
            run(runtime, EntityID("outer"))

        self.assertEqual(runtime.active.holds, frozenset())

    def test_an_invalid_node_names_the_function_it_is_in(self) -> None:
        runtime = runtime_of({
            "outer": Function((), ("add", lit(1), ("call", "inner"))),
            "inner": Function((), ("frob", lit(1))),
        })

        with self.assertRaisesRegex(LanguageError, "^inner: unknown operation"):
            run(runtime, EntityID("outer"))

        self.assertEqual(runtime.active.holds, frozenset())

    def test_a_tail_call_names_the_callee_in_its_errors(self) -> None:
        runtime = runtime_of({
            "outer": Function((), ("call", "inner")),
            "inner": Function((), ("add", lit("a"), lit(1))),
        })

        with self.assertRaisesRegex(LanguageError, "^inner: add operands"):
            run(runtime, EntityID("outer"))

    def watched(self, functions: dict[str, Function]) -> tuple[Runtime, list]:
        """A runtime whose cell ``w`` records the holds on the active
        version each time it is written."""

        w = EntityID("w")
        seen: list = []
        box: list = []

        def record(content) -> ConstraintResult:
            if box:
                seen.append(len(box[0].active.holds))

            return ConstraintResult.SATISFIED

        entities = {w: CellDeclaration(External("watch"), 0)}

        for name, function in functions.items():
            entity = EntityID(name)
            entities[entity] = function
            entities[EntityID(f"{name}.links")] = links(
                entity, w=w, **{other: EntityID(other) for other in functions}
            )

        runtime = Runtime(
            load(State.create({
                entity: Value.create(entity, content)
                for entity, content in entities.items()
            })),
            EvaluationContext({"watch": Evaluator(record)}),
        )
        box.append(runtime)

        return runtime, seen

    def test_a_chain_of_tail_calls_keeps_one_hold(self) -> None:
        runtime, seen = self.watched({
            "spin": Function(
                ("n",),
                (
                    "if",
                    ("lt", arg("n"), lit(1)),
                    lit(0),
                    (
                        "seq",
                        ("write", "w", arg("n")),
                        ("call", "spin", ("sub", arg("n"), lit(1))),
                    ),
                ),
            ),
        })

        self.assertEqual(run(runtime, EntityID("spin"), 300), 0)
        self.assertEqual(set(seen), {1})
        self.assertEqual(len(seen), 300)

    def test_a_tail_call_in_a_let_body_keeps_one_hold(self) -> None:
        runtime, seen = self.watched({
            "spin": Function(
                ("n",),
                (
                    "if",
                    ("lt", arg("n"), lit(1)),
                    lit(0),
                    (
                        "let",
                        "k",
                        ("sub", arg("n"), lit(1)),
                        (
                            "seq",
                            ("write", "w", arg("n")),
                            ("call", "spin", arg("k")),
                        ),
                    ),
                ),
            ),
        })

        self.assertEqual(run(runtime, EntityID("spin"), 300), 0)
        self.assertEqual(set(seen), {1})
        self.assertEqual(len(seen), 300)

    def test_a_call_that_waits_for_its_result_holds_one_more(self) -> None:
        runtime, seen = self.watched({
            "wait": Function(
                ("n",),
                (
                    "if",
                    ("lt", arg("n"), lit(1)),
                    lit(0),
                    (
                        "seq",
                        ("write", "w", arg("n")),
                        ("add", lit(1), ("call", "wait", ("sub", arg("n"), lit(1)))),
                    ),
                ),
            ),
        })

        self.assertEqual(run(runtime, EntityID("wait"), 50), 50)
        self.assertEqual(seen, list(range(1, 51)))
        self.assertEqual(runtime.active.holds, frozenset())

    def test_a_finished_run_leaves_no_holds(self) -> None:
        runtime = runtime_of({
            "tail": Function(
                ("n",),
                ("if", ("lt", arg("n"), lit(1)), ("read", "c"), ("call", "tail", ("sub", arg("n"), lit(1)))),
            ),
            "wait": Function(("n",), ("add", lit(1), ("call", "tail", arg("n")))),
        })
        self.assertEqual(run(runtime, EntityID("tail"), 500), 0)
        self.assertEqual(run(runtime, EntityID("wait"), 500), 1)
        self.assertEqual(runtime.active.holds, frozenset())


class OrderOfEffectsTests(unittest.TestCase):
    """Each test plants a write where a check must already have failed."""

    def cell_after(self, body: tuple, *args, params: tuple = ()) -> int:
        runtime = runtime_of({"f": Function(params, body)})

        with self.assertRaises(LanguageError):
            run(runtime, EntityID("f"), *args)

        return runtime.read(C)

    def touch(self) -> tuple:
        return ("write", "c", lit(5))

    def test_the_left_operand_is_checked_before_the_right_one_runs(self) -> None:
        for op in ("add", "sub", "mul", "lt"):
            with self.subTest(op=op):
                self.assertEqual(
                    self.cell_after((op, lit("a"), self.touch())),
                    0,
                )

    def test_a_tuple_operand_is_checked_before_the_index_runs(self) -> None:
        self.assertEqual(self.cell_after(("item", lit(3), self.touch())), 0)
        self.assertEqual(self.cell_after(("slice", lit(3), self.touch(), lit(1))), 0)
        self.assertEqual(self.cell_after(("concat", lit(3), self.touch())), 0)

    def test_the_start_of_a_slice_is_checked_before_the_stop_runs(self) -> None:
        body = ("slice", ("tuple", lit(1)), lit("x"), self.touch())

        self.assertEqual(self.cell_after(body), 0)

    def test_the_condition_is_checked_before_a_branch_runs(self) -> None:
        self.assertEqual(self.cell_after(("if", lit(1), self.touch(), lit(0))), 0)

    def test_a_let_name_is_checked_before_its_value_runs(self) -> None:
        body = ("let", "x", self.touch(), lit(0))

        self.assertEqual(self.cell_after(body, 1, params=("x",)), 0)

    def test_a_reference_is_checked_before_the_arguments_run(self) -> None:
        self.assertEqual(self.cell_after(("apply", lit(3), self.touch())), 0)

    def test_the_target_of_an_apply_is_checked_after_the_arguments_ran(self) -> None:
        body = ("apply", lit(EntityID("gone")), self.touch())

        self.assertEqual(self.cell_after(body), 5)

    def test_a_trial_evaluates_its_call_before_it_checks_its_pairs(self) -> None:
        body = ("trial", ("call", "f", self.touch()), "f")

        self.assertEqual(self.cell_after(body), 5)

    def test_values_are_written_and_read_in_order(self) -> None:
        runtime = runtime_of({
            "f": Function(
                (),
                (
                    "seq",
                    ("write", "c", lit(1)),
                    ("write", "c", ("add", ("read", "c"), lit(10))),
                    ("read", "c"),
                ),
            ),
        })

        self.assertEqual(run(runtime, EntityID("f")), 11)


class CodeInFlightTests(unittest.TestCase):
    def check(self, body: tuple) -> None:
        f = EntityID("f")
        runtime = runtime_of({
            "f": Function((), body),
            "swap": Function(
                (),
                ("activate", ("f", "step"), ("quote", lit(2))),
            ),
        })

        # swap replaces f's node while the frame of f that will reach it
        # is running: that frame still sees the old node.
        self.assertEqual(run(runtime, f, may_activate=True), 1)
        self.assertEqual(run(runtime, f, may_activate=True), 2)
        self.assertEqual(runtime.active.holds, frozenset())

    def test_a_frame_keeps_running_the_nodes_it_started_in(self) -> None:
        # The node is reached as an operand.
        self.check(
            ("add", ("seq", ("call", "swap"), lit(0)), ("label", "step", lit(1)))
        )

    def test_a_node_reached_by_a_hand_over_is_the_old_one_too(self) -> None:
        # The node is reached in tail position, as the end of a seq.
        self.check(("seq", ("call", "swap"), ("label", "step", lit(1))))

    def test_a_branch_taken_after_the_swap_is_the_old_one_too(self) -> None:
        self.check(
            ("if", ("lt", ("seq", ("call", "swap"), lit(0)), lit(1)), ("label", "step", lit(1)), lit(9))
        )


class Oracle:
    """A tiny evaluator of integer expressions, independent of the VM."""

    def __call__(self, expr: tuple, env: dict) -> int:
        op = expr[0]

        if op == "lit":
            return expr[1]

        if op == "arg":
            return env[expr[1]]

        if op == "label":
            return self(expr[2], env)

        if op in ("add", "sub", "mul"):
            left, right = self(expr[1], env), self(expr[2], env)

            return {"add": left + right, "sub": left - right, "mul": left * right}[op]

        if op == "if":
            branch = expr[2] if self(expr[1][1], env) < self(expr[1][2], env) else expr[3]

            return self(branch, env)

        if op == "let":
            return self(expr[3], {**env, expr[1]: self(expr[2], env)})

        raise AssertionError(op)


class CacheIsTransparentTests(unittest.TestCase):
    """Warm chunks, cold chunks and an independent oracle agree, through
    random edits of labelled nodes."""

    NAMES = ("p", "q", "r")

    def expr(
        self,
        rng: random.Random,
        depth: int,
        names: tuple,
        labels: list | None,
    ) -> tuple:
        """Labels and lets appear only when ``labels`` is given: a
        replacement has none of either, since it cannot see the ``let``s
        around the node it replaces (graph_form.md section 3)."""

        choice = rng.random()

        if depth <= 0 or choice < 0.25:
            leaf = rng.choice([lit(rng.randint(-3, 9)), arg("n")] + [arg(name) for name in names])

            if labels is not None and leaf[0] == "lit" and rng.random() < 0.6:
                labels.append(f"L{len(labels)}")
                return ("label", labels[-1], leaf)

            return leaf

        if choice < 0.6:
            op = rng.choice(["add", "sub", "mul"])

            return (op, self.expr(rng, depth - 1, names, labels), self.expr(rng, depth - 1, names, labels))

        if choice < 0.8:
            return (
                "if",
                (
                    "lt",
                    self.expr(rng, depth - 1, names, labels),
                    self.expr(rng, depth - 1, names, labels),
                ),
                self.expr(rng, depth - 1, names, labels),
                self.expr(rng, depth - 1, names, labels),
            )

        name = self.NAMES[len(names)] if len(names) < len(self.NAMES) else None

        if name is None or labels is None:
            return self.expr(rng, depth - 1, names, labels)

        return (
            "let",
            name,
            self.expr(rng, depth - 1, names, labels),
            self.expr(rng, depth - 1, (*names, name), labels),
        )

    def test_edits_never_leave_a_stale_chunk(self) -> None:
        oracle = Oracle()
        f = EntityID("f")

        for seed in range(60):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                labels: list = []
                body = self.expr(rng, 4, (), labels)
                runtime = runtime_of({"f": Function(("n",), body)})

                for _ in range(6):
                    n = rng.randint(0, 6)
                    state = runtime.active.state
                    expected = oracle(function_at(state, f).body, {"n": n})

                    warm = run(runtime, f, n)
                    forget_chunks(state)
                    cold = run(runtime, f, n)

                    self.assertEqual((warm, cold), (expected, expected))

                    live = sorted(relation_of(state.values[f]).roles)
                    labelled = [
                        role[len("label:"):]
                        for role in live
                        if role.startswith("label:")
                    ]

                    if not labelled:
                        break

                    label = rng.choice(labelled)
                    replacement = self.expr(rng, 2, (), None)
                    runtime.activate(define(state, {(f, label): replacement}))


if __name__ == "__main__":
    unittest.main()
