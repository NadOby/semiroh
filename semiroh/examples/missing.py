"""Wanted programs the current language cannot express (docs/corpus.md §4).

Each entry names a program tried against ``semiroh.lang`` and the feature
it needs; see docs/corpus.md section 4 for the write-up.
"""

from __future__ import annotations

from . import Wanted

MISSING: tuple[Wanted, ...] = (
    Wanted(
        name="map_long_tuple",
        needs=(
            "non-tail recursion deeper than the Python stack. Tail calls "
            "(language_data.md section 4) made loops unbounded, but a call "
            "that is not in tail position still nests interpreter frames "
            "in semiroh/lang.py's `_call`/`_eval`, about 5 Python frames "
            "per call. Measured under the default recursion limit of "
            "1000: the `map` example succeeds on a tuple of 190 elements "
            "and raises RecursionError on 200, and `insertion_sort` "
            "succeeds on 150 elements and raises on 200. Needs an "
            "evaluator whose stack is not the Python stack (an explicit "
            "continuation stack), or a structural primitive that walks a "
            "tuple without recursion."
        ),
    ),
    Wanted(
        name="make_adder",
        needs=(
            "function values that capture local names: make_adder(n) "
            "returning a function that adds n, or compose(f, g) returning "
            "f after g. `ref` yields only the identity of a function that "
            "already exists, and `apply` accepts only such a reference: "
            "`apply` of a `function` value raises LanguageError. A "
            "function built at run time is code as data and can be run "
            "only after `activate` installs it under an existing entity, "
            "which needs the activation capability and a name to replace. "
            "Needs anonymous function values with captured bindings "
            "(closures), or partial application."
        ),
    ),
)
