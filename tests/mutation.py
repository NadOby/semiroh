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
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

# Baseline and mutant subprocesses run the same semantic suite, but source-tree
# integrity checks are test-harness meta-tests rather than mutation kill
# oracles. They use this marker to exclude themselves identically from both
# subprocess kinds while remaining mandatory in the ordinary suite.
MUTATION_SUBPROCESS_ENV = "SEMIROH_MUTATION_SUBPROCESS"

_COMPARE = {
    ast.Lt: ast.GtE,
    ast.LtE: ast.Gt,
    ast.Gt: ast.LtE,
    ast.GtE: ast.Lt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
}
_ARITHMETIC = {
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.Add,
}

# target, qualified named scope, mutation kind, stripped source line,
# occurrence among sites of that kind on that physical line.
#
# The scope and line-local occurrence make classifications stable under
# unrelated insertions elsewhere while deliberately failing closed when an
# indistinguishable duplicate site is introduced in the same scope.
MutationKey = tuple[str, str, str, str, int]


@dataclass(frozen=True)
class Mutant:
    target: str
    index: int
    scope: str
    kind: str
    line: int
    text: str
    occurrence: int

    @property
    def key(self) -> MutationKey:
        """Stable identity used for survivor classification.

        ``index`` and ``line`` remain useful for execution and diagnostics but
        are intentionally not part of the classification key.

        Named scopes distinguish identical source lines in different semantic
        constructs. ``occurrence`` distinguishes multiple mutable nodes of the
        same kind represented on one physical source line.

        If an indistinguishable duplicate line is added to the same scope, the
        duplicate receives the same key. Catalog validation then observes more
        than one matching site and fails closed instead of silently rebinding a
        reviewed classification.
        """

        return (
            self.target,
            self.scope,
            self.kind,
            self.text,
            self.occurrence,
        )


def _sites(tree: ast.AST) -> list[tuple[str, ast.AST]]:
    found: list[tuple[str, ast.AST]] = []

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Compare)
            and type(node.ops[0]) in _COMPARE
        ):
            found.append(("compare", node))
        elif (
            isinstance(node, ast.BinOp)
            and type(node.op) in _ARITHMETIC
        ):
            found.append(("arithmetic", node))
        elif isinstance(node, ast.BoolOp):
            found.append(("boolean", node))
        elif isinstance(node, ast.If):
            found.append(("if", node))
        elif (
            isinstance(node, ast.Constant)
            and type(node.value) in (bool, int)
        ):
            found.append(("constant", node))
        elif (
            isinstance(node, ast.Return)
            and node.value is not None
            and not (
                isinstance(node.value, ast.Constant)
                and node.value.value is None
            )
        ):
            found.append(("return", node))

    return found


def _scope_names(tree: ast.AST) -> dict[int, str]:
    """Map every AST node to its nearest qualified named scope."""

    scopes: dict[int, str] = {}

    def visit(
        node: ast.AST,
        names: tuple[str, ...],
    ) -> None:
        if isinstance(
            node,
            (
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            names = (*names, node.name)

        scopes[id(node)] = (
            ".".join(names)
            if names
            else "<module>"
        )

        for child in ast.iter_child_nodes(node):
            visit(child, names)

    visit(tree, ())
    return scopes


def _descriptions(
    source: str,
    target: str,
    tree: ast.AST,
    sites: list[tuple[str, ast.AST]],
) -> tuple[Mutant, ...]:
    lines = source.splitlines()
    scopes = _scope_names(tree)

    # Occurrence is intentionally local to one physical line. Identical lines
    # elsewhere therefore do not renumber this site. If such a line is added
    # in the same named scope, both sites instead receive the same key and the
    # catalog's uniqueness check fails closed.
    seen: dict[tuple[str, str, int], int] = defaultdict(int)
    descriptions = []

    for index, (kind, node) in enumerate(sites):
        line = node.lineno
        text = lines[line - 1].strip()
        scope = scopes[id(node)]
        group = (scope, kind, line)
        occurrence = seen[group]
        seen[group] += 1

        descriptions.append(
            Mutant(
                target=target,
                index=index,
                scope=scope,
                kind=kind,
                line=line,
                text=text,
                occurrence=occurrence,
            )
        )

    return tuple(descriptions)


def site_descriptions(
    source: str,
    target: str,
) -> tuple[Mutant, ...]:
    """Describe every mutation site without changing the source."""

    tree = ast.parse(source)
    sites = _sites(tree)

    return _descriptions(
        source,
        target,
        tree,
        sites,
    )


def _change(kind: str, node: ast.AST) -> None:
    if kind == "compare":
        node.ops[0] = _COMPARE[type(node.ops[0])]()
    elif kind == "arithmetic":
        node.op = _ARITHMETIC[type(node.op)]()
    elif kind == "boolean":
        node.op = (
            ast.Or()
            if isinstance(node.op, ast.And)
            else ast.And()
        )
    elif kind == "if":
        node.test = ast.UnaryOp(
            ast.Not(),
            node.test,
        )
    elif kind == "constant":
        value = node.value
        node.value = (
            not value
            if isinstance(value, bool)
            else value + 1
        )
    else:
        node.value = ast.Constant(None)


def site_count(source: str) -> int:
    return len(_sites(ast.parse(source)))


def mutate(
    source: str,
    target: str,
    index: int,
) -> tuple[str, Mutant]:
    """The source with site ``index`` changed and its exact description."""

    tree = ast.parse(source)
    sites = _sites(tree)
    kind, node = sites[index]
    mutant = _descriptions(
        source,
        target,
        tree,
        sites,
    )[index]

    _change(kind, node)
    ast.fix_missing_locations(tree)

    return ast.unparse(tree), mutant


def sample(
    source: str,
    count: int,
    seed: int,
    batch: int = 0,
) -> list[int]:
    """Return one deterministic, non-overlapping mutation batch.

    For a fixed ``source``, ``count`` and ``seed``, batches partition the
    shuffled mutation sites into consecutive slices. Therefore batch N never
    repeats a site from an earlier batch, and running all batches eventually
    covers every site exactly once.
    """

    if count < 1:
        raise ValueError("mutation sample count must be positive")

    if batch < 0:
        raise ValueError("mutation batch must be non-negative")

    indexes = list(range(site_count(source)))
    random.Random(seed).shuffle(indexes)

    start = batch * count
    stop = start + count

    return sorted(indexes[start:stop])


def _suite_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if (
            not key.startswith("SEMIROH_MUTATE")
            and key != MUTATION_SUBPROCESS_ENV
        )
    }
    environment[MUTATION_SUBPROCESS_ENV] = "1"

    return environment


def in_mutation_subprocess() -> bool:
    """Whether this process is the suite run for a mutation campaign."""

    return os.environ.get(MUTATION_SUBPROCESS_ENV) == "1"


def _copy_repository(
    root: Path,
    destination: Path,
) -> None:
    """Copy exactly the repository content needed by the mutation suite."""

    shutil.copytree(
        root,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
        ),
    )


def baseline(
    root: Path,
    command: list[str],
    timeout: float = 180,
) -> subprocess.CompletedProcess[bytes]:
    """Run the mutation suite against an unmodified repository copy.

    This uses the same copy and environment rules as mutant execution. Mutation
    testing is only meaningful when this baseline succeeds.
    """

    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "repo"
        _copy_repository(root, copy)

        return subprocess.run(
            command,
            cwd=copy,
            env=_suite_environment(),
            capture_output=True,
            timeout=timeout,
        )


def killed(
    root: Path,
    target: str,
    index: int,
    command: list[str],
    timeout: float = 180,
) -> tuple[Mutant, bool]:
    """Run ``command`` against one mutant.

    ``True`` means the suite failed or timed out, so the mutant was killed.
    """

    source = (root / target).read_text()
    mutated, mutant = mutate(
        source,
        target,
        index,
    )

    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "repo"
        _copy_repository(root, copy)
        (copy / target).write_text(mutated)

        try:
            done = subprocess.run(
                command,
                cwd=copy,
                env=_suite_environment(),
                capture_output=True,
                timeout=timeout,
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
    workers = workers or min(
        8,
        os.cpu_count() or 1,
    )

    with ThreadPoolExecutor(workers) as pool:
        results = list(
            pool.map(
                lambda index: killed(
                    root,
                    target,
                    index,
                    command,
                ),
                indexes,
            )
        )

    return [
        mutant
        for mutant, dead in results
        if not dead
    ]


SUITE = [
    sys.executable,
    "-m",
    "unittest",
    "discover",
    "-f",
    "-q",
]
