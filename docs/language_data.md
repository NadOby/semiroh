# Data, Local Names and Function References

**Status: implemented** (roadmap.md task 6). `semiroh/lang.py` and
`semiroh/bytecode.py` implement it; `tests/test_data_ops.py` is the acceptance suite, and
`tests/test_data_graph_form.py` covers the graph form and the frames of tail
calls.

The canary corpus (corpus.md section 4) found four programs the language
could not express: insertion sort, map and fold, local variables, and a
loop deeper than the reference interpreter's stack. This step adds what
they need, in input form; graph form gets one node kind per operation
(graph_form.md section 3).

## 1. Tuples

**Decided:**

    ("tuple", e1, ..., en)      a tuple of the values, n >= 0
    ("len", t)                  the length of tuple t
    ("item", t, i)              element i of t, 0 <= i < len(t)
    ("slice", t, start, stop)   t[start:stop], 0 <= start <= stop <= len(t)
    ("concat", t1, t2)          t1 followed by t2

Indices are ints (a bool is not an int). There is no negative indexing and
no clamping: anything outside the stated bounds, or an operand of the wrong
kind, is a `LanguageError`. Tuples read from cells or passed as arguments
are canonical and are accepted like any other tuple.

## 2. Local names

**Decided:**

    ("let", name, e, body)

evaluates `e`, binds `name` to its value for `body`, and returns the value
of `body`. `("arg", name)` reads parameters and let-bound names alike. A
name that is not a non-empty string, or that is already in scope (a
parameter or an enclosing `let`), is a `LanguageError`: shadowing would be
an ambiguity.

## 3. Function references

**Decided:**

Everything in this section except what a reference is and how it survives
renames.

**Provisional:**

What a reference is and how it survives renames.

    ("ref", link)               a reference to the linked function
    ("apply", f, e1, ..., en)   call the function f refers to

A reference is an ordinary value: it can be passed, returned, compared with
`eq` and stored in a cell. Provisionally it is the function's `EntityID`
(kind `entity_id`, so a cell can constrain it with `IsKind("entity_id")`).
`apply` calls it exactly as `call` does: a frame, the arity check, and the
function as it is in the active version. `ref` of a link that does not name
a function, and `apply` of anything that is not a reference to a function in
the active state, are `LanguageError`s.

A reference held in a cell is runtime content, not a relation, so it does
not follow a rename of its function; applying it afterwards is a
`LanguageError`. Tracking references in cell content is open
(activation_model.md section 6).

## 4. Tail calls

**Decided:**

A `call` or `apply` in tail position does not grow the machine's stacks
(bytecode.md section 4).
Tail position is the body root, both branches of an `if` in tail position,
the last item of a `seq` in tail position, and the body of a `let` in tail
position. The caller's frame is released when the callee's frame is entered;
holds, code in flight (metaprogramming.md section 5) and results are
otherwise unchanged.

## 5. Corpus tier 2

**Decided:**

`TAGS` gains `"data"` and `"higher order"`. The corpus gains at least:
insertion sort, map, fold, a program using `let`, a tail-recursive loop
deeper than 1000 calls, and a canary that swaps the ordering a sort uses
(for example by activating a different comparator) between two runs while
the data stays in a cell. The four programs above leave `MISSING`; any new
gap found while writing them is added there.

## 6. Acceptance tests and notes

`tests/test_data_ops.py` pins sections 1 to 5, and `tests/test_corpus.py`
must keep passing. The implementer adds graph-form node kinds and roles to
graph_form.md section 3, keeps `function_at` round-tripping the new
operations, adds a `CHANGES.md` entry, and marks this document's status.
