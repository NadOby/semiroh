"""A bytecode interpreter written in SEMIROH (docs/vm_in_semiroh.md,
roadmap task 10).

``vm(chunk, params, args, links)`` runs a chunk as ``lower`` in
``self_hosting.py`` emits it: a tuple of instructions in which ``EVAL``,
``GOTO``, ``BRANCH`` and ``LETBIND`` hold the chunk of their child. It runs
the instructions of a pure function: arithmetic, comparison, tuples, ``let``,
``if``, ``seq``, ``call``, ``ref`` and ``apply``. ``links`` is the function's
link table as ``linksof`` returns it, which resolves the names a ``CALL`` or
``REF`` holds; the callee is entered with ``applyv``. An instruction it does
not run (``READ``, ``WRITE``, ``CODE``, ``LINKS``, ``RAISE``) raises.

The machine is ``run(chunk, pc, stack, env, links)``. The operand stack is a
tuple, the environment a tuple of ``(name, value)`` pairs, and the program
counter an index. ``run`` calls itself in tail position for every
instruction, ``EVAL`` calls it for the child, and ``GOTO``, ``BRANCH`` and
``LETBIND`` tail call it, so a tail call of the interpreted function is a
tail call of the machine.

It has no way to raise an error of its own, so a check is made by doing
the operation: ``INT`` adds zero, ``TUPLE`` takes the length, and ``trap``
indexes an empty tuple. The error is a ``LanguageError`` all the same.
"""

from __future__ import annotations

from typing import Any

from .. import ActivationRejected, EntityID
from ..lang import Function, links
from . import Example, Raises, Step
from ._support import program
from .self_hosting import LOWER, UPPER, _arg, _item, _lit

RUN = EntityID("vm_run")
LOOKUP = EntityID("vm_lookup")
HAS = EntityID("vm_has")
FIND = EntityID("vm_find")
BIND = EntityID("vm_bind")
TRAP = EntityID("vm_trap")
VM = EntityID("vm")

_CHUNK, _PC, _STACK, _ENV, _LINKS = (
    _arg("chunk"), _arg("pc"), _arg("stack"), _arg("env"), _arg("links"),
)
_INS, _N = _arg("ins"), ("len", _STACK)


def _sub(left: tuple, right: Any) -> tuple:
    return ("sub", left, _lit(right) if isinstance(right, int) else right)


def _top(depth: int = 1) -> tuple:
    """The value ``depth`` from the top of the stack (1 is the top)."""

    return ("item", _STACK, _sub(_N, depth))


def _drop(count: Any) -> tuple:
    """The stack without its top ``count``."""

    return ("slice", _STACK, _lit(0), _sub(_N, count))


def _push(base: tuple, value: tuple) -> tuple:
    return ("concat", base, ("tuple", value))


def _next(stack: tuple) -> tuple:
    return (
        "call", "vm_run", _CHUNK, ("add", _PC, _lit(1)), stack, _ENV, _LINKS,
    )


def _enter(chunk: tuple, env: tuple = _ENV) -> tuple:
    """Run a child chunk from its start with an empty stack."""

    return ("call", "vm_run", chunk, _lit(0), _lit(()), env, _LINKS)


def _instruction_operand(index: int) -> tuple:
    return _item(_INS, index)


def _binary(operation: str) -> tuple:
    return _next(_push(_drop(2), (operation, _top(2), _top(1))))


def _cases() -> list[tuple[str, tuple]]:
    k = _instruction_operand
    name = k(1)

    def call(function: tuple, arguments: tuple) -> tuple:
        """The call is the last instruction before END in every chunk
        ``lower`` emits, so its result is the value of the chunk: a tail
        call of the machine, and the interpreted function's tail calls stay
        tail calls. (Nothing is left on the stack below the arguments.)
        """

        return ("applyv", function, arguments)

    return [
        ("LIT", _next(_push(_STACK, k(1)))),
        ("ARG", _next(_push(_STACK, ("call", "vm_lookup", _ENV, name, _lit(0))))),
        ("EVAL", _next(_push(_STACK, _enter(k(1))))),
        ("END", _top()),
        ("GOTO", _enter(k(1))),
        ("BRANCH", ("if", _top(), _enter(k(1)), _enter(k(2)))),
        ("POP", _next(_drop(1))),
        ("INT", ("seq", ("add", _top(), _lit(0)), _next(_STACK))),
        ("TUPLE", ("seq", ("len", _top()), _next(_STACK))),
        ("ADD", _binary("add")),
        ("SUB", _binary("sub")),
        ("MUL", _binary("mul")),
        ("LT", _binary("lt")),
        ("EQ", _binary("eq")),
        ("LEN", _next(_push(_drop(1), ("len", _top())))),
        ("ITEM", _next(_push(_drop(2), ("item", _top(2), _top(1))))),
        ("SLICE", _next(_push(_drop(3), ("slice", _top(3), _top(2), _top(1))))),
        ("CONCAT", _next(_push(_drop(2), ("concat", _top(2), _top(1))))),
        (
            "MKTUPLE",
            _next(_push(
                _drop(k(1)),
                ("slice", _STACK, _sub(_N, k(1)), _N),
            )),
        ),
        (
            "CALL",
            call(
                ("call", "vm_find", _LINKS, name, _lit(0)),
                ("slice", _STACK, _sub(_N, k(2)), _N),
            ),
        ),
        ("REFCHECK", _next(_STACK)),
        (
            "APPLY",
            call(
                ("item", _STACK, _sub(_N, ("add", k(1), _lit(1)))),
                ("slice", _STACK, _sub(_N, k(1)), _N),
            ),
        ),
        ("APPLYV", call(_top(2), _top(1))),
        ("REF", _next(_push(_STACK, ("call", "vm_find", _LINKS, name, _lit(0))))),
        (
            "LETCHECK",
            ("if", ("call", "vm_has", _ENV, name, _lit(0)), ("call", "vm_trap"), _next(_STACK)),
        ),
        (
            "LETBIND",
            _enter(
                k(2),
                ("concat", _ENV, ("tuple", ("tuple", name, _top()))),
            ),
        ),
    ]


# Most frequent first (in the compiler's own chunk): every instruction costs a
# comparison for each opcode before it.
_ORDER = (
    "END", "EVAL", "LIT", "MKTUPLE", "TUPLE", "ARG", "INT", "ITEM", "CALL",
    "CONCAT", "EQ", "BRANCH", "GOTO", "POP", "LEN", "ADD", "SUB", "MUL", "LT",
    "SLICE", "LETCHECK", "LETBIND", "REF", "APPLY", "APPLYV", "REFCHECK",
)


def _run_body() -> tuple:
    chain: tuple = ("call", "vm_trap")

    cases = dict(_cases())

    for op in reversed(_ORDER):
        body = cases[op]
        chain = ("if", ("eq", _arg("op"), _lit(op)), body, chain)

    return (
        "let", "ins", ("item", _CHUNK, _PC),
        ("let", "op", _item(_INS, 0), chain),
    )


def _lookup_body() -> tuple:
    env, name, i = _arg("env"), _arg("name"), _arg("i")
    pair = ("item", env, i)

    return (
        "if",
        ("lt", i, ("len", env)),
        (
            "if",
            ("eq", ("item", pair, _lit(0)), name),
            ("item", pair, _lit(1)),
            ("call", "vm_lookup", env, name, ("add", i, _lit(1))),
        ),
        ("call", "vm_trap"),
    )


def _has_body() -> tuple:
    env, name, i = _arg("env"), _arg("name"), _arg("i")

    return (
        "if",
        ("lt", i, ("len", env)),
        (
            "if",
            ("eq", ("item", ("item", env, i), _lit(0)), name),
            _lit(True),
            ("call", "vm_has", env, name, ("add", i, _lit(1))),
        ),
        _lit(False),
    )


def _find_body() -> tuple:
    table, name, i = _arg("table"), _arg("name"), _arg("i")
    pair = ("item", table, i)

    return (
        "if",
        ("lt", i, ("len", table)),
        (
            "if",
            ("eq", ("item", pair, _lit(0)), name),
            ("item", pair, _lit(1)),
            ("call", "vm_find", table, name, ("add", i, _lit(1))),
        ),
        ("call", "vm_trap"),
    )


def _bind_body() -> tuple:
    params, args, i, env = _arg("params"), _arg("args"), _arg("i"), _arg("env")

    return (
        "if",
        ("lt", i, ("len", params)),
        (
            "call", "vm_bind", params, args, ("add", i, _lit(1)),
            (
                "concat", env,
                ("tuple", ("tuple", ("item", params, i), ("item", args, i))),
            ),
        ),
        env,
    )


def vm_entities() -> dict[EntityID, Any]:
    """The interpreter's functions and their links."""

    return {
        RUN: Function(
            ("chunk", "pc", "stack", "env", "links"),
            _run_body(),
        ),
        EntityID("vm_run.links"): links(
            RUN, vm_run=RUN, vm_lookup=LOOKUP, vm_has=HAS, vm_find=FIND,
            vm_trap=TRAP,
        ),
        LOOKUP: Function(("env", "name", "i"), _lookup_body()),
        EntityID("vm_lookup.links"): links(LOOKUP, vm_lookup=LOOKUP, vm_trap=TRAP),
        HAS: Function(("env", "name", "i"), _has_body()),
        EntityID("vm_has.links"): links(HAS, vm_has=HAS),
        FIND: Function(("table", "name", "i"), _find_body()),
        EntityID("vm_find.links"): links(FIND, vm_find=FIND, vm_trap=TRAP),
        BIND: Function(("params", "args", "i", "env"), _bind_body()),
        EntityID("vm_bind.links"): links(BIND, vm_bind=BIND),
        TRAP: Function((), ("item", ("tuple",), _lit(0))),
        VM: Function(
            ("chunk", "params", "args", "links"),
            (
                "call", "vm_run", _arg("chunk"), _lit(0), _lit(()),
                (
                    "call", "vm_bind", _arg("params"), _arg("args"),
                    _lit(0), _lit(()),
                ),
                _arg("links"),
            ),
        ),
        EntityID("vm.links"): links(VM, vm_run=RUN, vm_bind=BIND),
    }


# ---------------------------------------------------------------------------
# A program that runs its own compiler on its own bytecode
# ---------------------------------------------------------------------------

ARG_EXPRS = EntityID("arg_exprs")
SWAP_ALL = EntityID("swap_all")
SWAPPED = ("upper", "evals", "seq_code", "lower")


def _swap_name(target: str) -> EntityID:
    return EntityID(f"swap_{target}")


def _arg_exprs_body() -> tuple:
    params, i = _arg("params"), _arg("i")

    return (
        "if",
        ("lt", i, ("len", params)),
        (
            "concat",
            ("tuple", ("tuple", _lit("arg"), ("item", params, i))),
            ("call", "arg_exprs", params, ("add", i, _lit(1))),
        ),
        _lit(()),
    )


def _swapped_function(target: str, chunk: tuple) -> tuple:
    """The value that replaces ``target``: a function with its parameters
    whose body hands ``chunk``, its arguments and its link table to ``vm``.
    """

    params = _item(("code", target), 0)

    return (
        "function",
        params,
        (
            "quote",
            (
                "call", "vm",
                ("lit", ("unquote", chunk)),
                ("lit", ("unquote", params)),
                (
                    "unquote",
                    (
                        "concat",
                        _lit(("tuple",)),
                        ("call", "arg_exprs", params, _lit(0)),
                    ),
                ),
                ("lit", ("unquote", ("linksof", target))),
            ),
        ),
    )


def _compiled(target: str) -> tuple:
    """The chunk of ``target``, compiled now by ``lower``."""

    return ("call", "lower", _item(("code", target), 1))


def _swap_body(target: str) -> tuple:
    """Replace one function; the value is the chunk installed."""

    return (
        "let", "chunk", _compiled(target),
        (
            "seq",
            ("activate", target, _swapped_function(target, _arg("chunk"))),
            _arg("chunk"),
        ),
    )


def _swap_all_body() -> tuple:
    """Replace every function of the compiler in one activation, each by a
    function that runs its own chunk. A run may activate once (two-version
    bound), so the pairs go together.
    """

    pairs: list[tuple] = []

    for target in SWAPPED:
        pairs += [target, _swapped_function(target, _compiled(target))]

    return ("seq", ("activate", *pairs), _lit(True))


def bootstrap_entities() -> dict[EntityID, Any]:
    """The compiler, the interpreter, and the program that swaps each
    function of the compiler for one that runs on the interpreter.

    ``swap_all()`` swaps them all in one activation; ``swap_lower()`` and the
    others swap one and return the chunk it installed.
    """

    from .self_hosting import compiler_entities

    entities: dict[EntityID, Any] = {
        **compiler_entities({"vm": VM}),
        **vm_entities(),
        ARG_EXPRS: Function(("params", "i"), _arg_exprs_body()),
        EntityID("arg_exprs.links"): links(ARG_EXPRS, arg_exprs=ARG_EXPRS),
    }

    for target in SWAPPED:
        entity = _swap_name(target)
        entities[entity] = Function((), _swap_body(target))
        entities[EntityID(f"swap_{target}.links")] = links(
            entity,
            **{
                target: EntityID(target),
                "lower": EntityID("lower"),
                "arg_exprs": ARG_EXPRS,
            },
        )

    entities[SWAP_ALL] = Function((), _swap_all_body())
    entities[EntityID("swap_all.links")] = links(
        SWAP_ALL,
        **{target: EntityID(target) for target in SWAPPED},
        arg_exprs=ARG_EXPRS,
    )

    return entities


def _bootstrap() -> Example:
    end = ("END",)
    one = (("LIT", 1), end)
    x = (("ARG", "x"), end)
    add = (
        ("EVAL", x), ("INT", "add"), ("EVAL", one), ("INT", "add"),
        ("ADD",), end,
    )
    branch = (
        ("EVAL", (
            ("EVAL", x), ("INT", "lt"), ("EVAL", one), ("INT", "lt"),
            ("LT",), end,
        )),
        ("BRANCH", one, x),
        end,
    )
    expression = ("if", ("lt", ("arg", "x"), ("lit", 1)), ("lit", 1), ("arg", "x"))
    return Example(
        name="bootstrap",
        tags=frozenset({"self-modification", "recursion", "data"}),
        program=program(bootstrap_entities()),
        scenarios=(
            (
                Step(LOWER, (("add", ("arg", "x"), ("lit", 1)),), add),
                Step(SWAP_ALL, (), Raises(ActivationRejected)),
                Step(SWAP_ALL, (), True, may_activate=True),
                Step(LOWER, (("add", ("arg", "x"), ("lit", 1)),), add),
                Step(LOWER, (expression,), branch),
                Step(UPPER, ("mul",), "MUL"),
                Step(UPPER, ("frobnicate",), None),
            ),
        ),
        description=(
            "The compiler of self_hosting.py swaps each of its functions "
            "for one that hands its own chunk to the interpreter written in "
            "SEMIROH, then compiles again, on that bytecode, with the same "
            "results (vm_in_semiroh.md section 5)."
        ),
    )


EXAMPLES: tuple[Example, ...] = (_bootstrap(),)
