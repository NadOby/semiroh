"""Error values and human-readable descriptions (error_handling.md).

Execution constructs plain error tuples. This module only publishes the
catalogue of host-reported kinds and renders those values for people.
"""

from __future__ import annotations

from typing import Any


KINDS: dict[str, str] = {
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


def _display(value: Any) -> str:
    """Prefer the readable value of identity records."""

    name = getattr(value, "value", None)
    return name if isinstance(name, str) else repr(value)


def describe(error: tuple) -> str:
    """Render a SHEAR error value for a person.

    Error values remain plain ``(origin, kind, detail, where)`` tuples;
    this text is deliberately not part of their semantics.
    """

    try:
        origin, kind, detail, where = error
        function, node = where
    except (TypeError, ValueError):
        return f"malformed error value: {error!r}"

    return (
        f"{kind} ({origin}): {detail!r} "
        f"at {_display(function)} / {_display(node)}"
    )
