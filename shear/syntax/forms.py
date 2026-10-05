"""Input-form helpers that both the parser and the printer use."""

from __future__ import annotations

from typing import Any, Callable

from ..canonical import CanonicalNode
from ..constraints import IsKind
from ..lang import NODE_KINDS


# Cell type names other than ``int``, and the ``IsKind`` kind each stands for.
_TYPE_KINDS = {"bool": "bool", "str": "str", "tuple": "tuple", "entity": "entity_id"}


def _tup(value: Any) -> bool:
    """A plain tuple, not a canonical tagged node (which subclasses tuple)."""

    return isinstance(value, tuple) and not isinstance(value, CanonicalNode)


def _map_links(expr: Any, f: Callable[[str], str]) -> Any:
    """Rewrite every link name of an input-form expression with ``f``.

    Follows the shape of the operations that carry link names (``call``,
    ``read``, ``write``, ``ref``, ``code``, ``linksof``, and the targets of
    ``activate`` and ``trial``), and leaves literals and anything it does not
    recognize alone.
    """

    if not _tup(expr) or not expr or not isinstance(expr[0], str):
        return expr

    op, rest = expr[0], expr[1:]

    def sub(child: Any) -> Any:
        return _map_links(child, f)

    def target(name: Any) -> Any:
        if isinstance(name, str):
            return f(name)

        if _tup(name) and len(name) == 2 and isinstance(name[0], str):
            return (f(name[0]), name[1])

        return name

    if op in ("lit", "arg") or op not in NODE_KINDS and op != "label":
        return expr

    if op in ("call", "read", "write", "ref", "code", "linksof"):
        if rest and isinstance(rest[0], str):
            return (op, f(rest[0]), *(sub(child) for child in rest[1:]))

        return expr

    if op == "activate":
        return (
            op,
            *(
                target(child) if index % 2 == 0 else sub(child)
                for index, child in enumerate(rest)
            ),
        )

    if op == "trial":
        if not rest:
            return expr

        return (
            op,
            sub(rest[0]),
            *(
                target(child) if index % 2 == 0 else sub(child)
                for index, child in enumerate(rest[1:])
            ),
        )

    if op == "let" and len(rest) == 3:
        return (op, rest[0], sub(rest[1]), sub(rest[2]))

    if op == "label" and len(rest) == 2:
        return (op, rest[0], sub(rest[1]))

    if op == "closure" and len(rest) == 3:
        return (
            op,
            rest[0],
            rest[1],
            sub(rest[2]),
        )

    return (op, *(sub(child) for child in rest))
