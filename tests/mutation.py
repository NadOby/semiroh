"""Seeded single-site mutants of one source file, run against the suite.

A helper for ``tests/test_mutation.py``, not a test module. A mutant changes
one place in a file (a comparison flipped, ``and`` turned into ``or``, an
``if`` negated, a constant moved by one, a returned value dropped) in a
copy of the repository and runs the suite there. A mutant the suite does not
fail is a *survivor*: either the change does not alter behaviour, or nothing
checks that behaviour.
"""

from __future__ import annotations

import ast
import os
import random
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_COMPARE = {
    ast.Lt: ast.GtE, ast.LtE: ast.Gt, ast.Gt: ast.LtE, ast.GtE: ast.Lt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Is: ast.IsNot,
    ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In,
}
_ARITHMETIC = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add}


@dataclass(frozen=True)
class Mutant:
    target: str
    index: int
    kind: str
    line: int
    text: str   # the source line that was changed, stripped


def _sites(tree: ast.AST) -> list[tuple[str, ast.AST]]:
    found: list[tuple[str, ast.AST]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and type(node.ops[0]) in _COMPARE:
            found.append(("compare", node))
        elif isinstance(node, ast.BinOp) and type(node.op) in _ARITHMETIC:
            found.append(("arithmetic", node))
        elif isinstance(node, ast.BoolOp):
            found.append(("boolean", node))
        elif isinstance(node, ast.If):
            found.append(("if", node))
        elif isinstance(node, ast.Constant) and type(node.value) in (bool, int):
            found.append(("constant", node))
        elif (
            isinstance(node, ast.Return)
            and node.value is not None
            and not (isinstance(node.value, ast.Constant) and node.value.value is None)
        ):
            found.append(("return", node))

    return found


def _change(kind: str, node: ast.AST) -> None:
    if kind == "compare":
        node.ops[0] = _COMPARE[type(node.ops[0])]()
    elif kind == "arithmetic":
        node.op = _ARITHMETIC[type(node.op)]()
    elif kind == "boolean":
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
    elif kind == "if":
        node.test = ast.UnaryOp(ast.Not(), node.test)
    elif kind == "constant":
        value = node.value
        node.value = (not value) if isinstance(value, bool) else value + 1
    else:
        node.value = ast.Constant(None)


def site_count(source: str) -> int:
    return len(_sites(ast.parse(source)))


def mutate(source: str, target: str, index: int) -> tuple[str, Mutant]:
    """The source with site ``index`` changed, and a description of it."""

    tree = ast.parse(source)
    kind, node = _sites(tree)[index]
    line = node.lineno
    text = source.splitlines()[line - 1].strip()
    _change(kind, node)
    ast.fix_missing_locations(tree)

    return ast.unparse(tree), Mutant(target, index, kind, line, text)


def sample(source: str, count: int, seed: int) -> list[int]:
    sites = site_count(source)

    return sorted(random.Random(seed).sample(range(sites), min(count, sites)))


def killed(
    root: Path,
    target: str,
    index: int,
    command: list[str],
    timeout: float = 180,
) -> tuple[Mutant, bool]:
    """Run ``command`` in a copy of ``root`` with one site of ``target``
    changed. True when it fails (or hangs), which is what a mutant should do.
    """

    source = (root / target).read_text()
    mutated, mutant = mutate(source, target, index)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("SEMIROH_MUTATE")}

    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "repo"
        shutil.copytree(
            root, copy,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "docs"),
        )
        (copy / target).write_text(mutated)

        try:
            done = subprocess.run(
                command, cwd=copy, env=env, capture_output=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return mutant, True

    return mutant, done.returncode != 0


def survivors(
    root: Path,
    target: str,
    indexes: list[int],
    command: list[str],
    workers: int | None = None,
) -> list[Mutant]:
    workers = workers or min(8, os.cpu_count() or 1)

    with ThreadPoolExecutor(workers) as pool:
        results = list(pool.map(
            lambda index: killed(root, target, index, command), indexes,
        ))

    return [mutant for mutant, dead in results if not dead]


SUITE = [sys.executable, "-m", "unittest", "discover", "-f", "-q"]
