"""Self-modification-tagged canary programs (docs/corpus.md section 3)."""

from __future__ import annotations

from .. import EntityID
from ..lang import Function, links
from . import Example, Step
from ._support import program


def _power_compiler() -> Example:
    power = EntityID("power")
    emit = EntityID("emit")
    compile_ = EntityID("compile")
    entities = {
        power: Function(("x",), ("lit", 1)),
        emit: Function(
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
        EntityID("emit.links"): links(emit, emit=emit),
        compile_: Function(
            ("n",),
            (
                "activate",
                "power",
                ("function", ("lit", ("x",)), ("call", "emit", ("arg", "n"))),
            ),
        ),
        EntityID("compile.links"): links(compile_, power=power, emit=emit),
    }

    return Example(
        name="power_compiler",
        tags=frozenset({"self-modification"}),
        program=program(entities),
        scenarios=(
            (
                Step(power, (3,), 1),
                Step(compile_, (3,), None, may_activate=True),
                Step(power, (3,), 27),
            ),
        ),
        description=(
            "compile(n) generates x^n by quote/unquote and installs it as "
            "power by activation; the later power(3) call shows the new "
            "code."
        ),
    )


def _checked_compile() -> Example:
    power = EntityID("power")
    emit = EntityID("emit")
    install_if = EntityID("install_if")
    checked_compile = EntityID("checked_compile")
    entities = {
        power: Function(("x",), ("lit", 1)),
        emit: Function(
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
        EntityID("emit.links"): links(emit, emit=emit),
        install_if: Function(
            ("f", "x", "expected"),
            (
                "if",
                (
                    "eq",
                    (
                        "trial",
                        ("call", "power", ("arg", "x")),
                        "power",
                        ("arg", "f"),
                    ),
                    ("arg", "expected"),
                ),
                ("seq", ("activate", "power", ("arg", "f")), ("lit", True)),
                ("lit", False),
            ),
        ),
        EntityID("install_if.links"): links(install_if, power=power),
        checked_compile: Function(
            ("n", "x", "expected"),
            (
                "call",
                "install_if",
                ("function", ("lit", ("x",)), ("call", "emit", ("arg", "n"))),
                ("arg", "x"),
                ("arg", "expected"),
            ),
        ),
        EntityID("checked_compile.links"): links(
            checked_compile,
            install_if=install_if,
            emit=emit,
        ),
    }

    return Example(
        name="checked_compile",
        tags=frozenset({"self-modification"}),
        program=program(entities),
        scenarios=(
            (
                Step(checked_compile, (3, 2, 8), True, may_activate=True),
                Step(power, (3,), 27),
                Step(checked_compile, (2, 2, 5), False, may_activate=True),
                Step(power, (3,), 27),
            ),
        ),
        description=(
            "checked_compile trials a candidate against an expected value "
            "before installing it; a candidate that fails the trial (2^2 "
            "is not 5) is never activated, and power(3) still shows the "
            "earlier install."
        ),
    )


def _replace_self() -> Example:
    replace_self = EntityID("replace_self")
    entities = {
        replace_self: Function(
            (),
            (
                "seq",
                (
                    "activate",
                    "itself",
                    ("function", ("lit", ()), ("lit", ("lit", "new"))),
                ),
                ("lit", "old"),
            ),
        ),
        EntityID("replace_self.links"): links(replace_self, itself=replace_self),
    }

    return Example(
        name="replace_self",
        tags=frozenset({"self-modification"}),
        program=program(entities),
        scenarios=(
            (
                Step(replace_self, (), "old", may_activate=True),
                Step(replace_self, (), "new"),
            ),
        ),
        description=(
            "A function that installs a new version of itself but "
            "finishes its own running call with the old body; the next "
            "call runs and returns from the new code."
        ),
    )


EXAMPLES: tuple[Example, ...] = (
    _power_compiler(),
    _checked_compile(),
    _replace_self(),
)
