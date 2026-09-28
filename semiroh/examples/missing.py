"""Wanted programs the current language cannot express (docs/corpus.md §4).

Each entry names a program tried against ``semiroh.lang`` and the feature
it needs; see docs/corpus.md section 4 for the write-up.
"""

from __future__ import annotations

from . import Wanted

MISSING: tuple[Wanted, ...] = (
    Wanted(
        name="insertion_sort",
        needs=(
            "a way to take a tuple apart at runtime (head/tail or an index "
            "operation) and a length operation, to iterate over a sequence "
            "of unknown length. The language only has fixed-shape literal "
            "tuples and quote/unquote for shaping code, not for walking "
            "runtime data whose length isn't known when the program is "
            "written."
        ),
    ),
    Wanted(
        name="map_and_fold",
        needs=(
            "an `apply` operation that calls a function *value* directly. "
            "`call` only dispatches through a static link name resolved "
            "via the calling function's own links relation, so a function "
            "received as an argument or read from a cell cannot be "
            "invoked -- only functions the definition already names. Also "
            "needs the same tuple decomposition as insertion sort, to walk "
            "the elements being mapped or folded."
        ),
    ),
    Wanted(
        name="local_variables",
        needs=(
            "a `let`/local-binding form to name an intermediate value "
            "within one function body. The only binding mechanism is a "
            "call's parameters, so naming a subexpression's value for "
            "reuse means either re-evaluating it or factoring it into a "
            "separate linked function, which is a different (and heavier) "
            "scope, not a local variable."
        ),
    ),
    Wanted(
        name="deep_loop",
        needs=(
            "tail-call elimination, or an iteration primitive, in the "
            "reference interpreter. The language has no loop construct, "
            "only recursion, and every `call` nests further Python stack "
            "frames in semiroh/lang.py's `_call`/`_eval`; a loop expressed "
            "the only way the language allows -- recursion -- hits "
            "Python's recursion limit (RecursionError) long before any "
            "conceptual program-level limit. Measured against the "
            "`sum_to_n` example here, under the interpreter's default "
            "recursion limit of 1000, `sum_to_n(196)` succeeds and "
            "`sum_to_n(197)` raises RecursionError -- about 5 Python "
            "stack frames per SEMIROH call."
        ),
    ),
)
