# Text Syntax, Version 0

**Status: implemented** (roadmap.md task 11; extended by task 17) in
`shear/syntax.py`. The acceptance tests are `tests/test_syntax.py`;
`tests/test_syntax_units.py` pins each construct. Section 8 lists what the
implementation had to decide.

Programs have been written as nested tuples. This step adds a human source
view (syntax_notes.md, Direction A): `parse` reads text into the input
format, which `load` turns into graph form, and `render` prints graph form
back as text. The graph stays authoritative; text is a projection.

`parse` itself is import-only: parsing text produces input-format state and
does not infer continuity with an existing graph. Editing an existing program
uses `reconcile(state, text)`, specified in `name_resolution.md`: it resolves
the edited text and expresses the change through `lang.define`, so task 13's
continuity inference applies. Cell declaration edits remain outside the
current reconciler.

## 1. Programs

**Decided:**

A program text is a sequence of declarations:

    cell NAME: TYPE = LITERAL
    cell NAME: int in LO..HI = LITERAL
    fn NAME(PARAM, ...):
        BLOCK

`TYPE` is `int`, `bool`, `str`, `tuple`, `entity` (constraint `IsKind`) or
`int in LO..HI` (`IntRange`). `LITERAL` is a data literal (section 3).
Each declared name is an entity with that `EntityID`. A function's links
relation is created from the global names its body uses; programs never
write links.

Either bound of `int in LO..HI` may be left out for a `None` bound
(`int in 0..`), and `entity` is `IsKind("entity_id")`. The code that
`activate(f = ...)` or `trial(..., f = ...)` installs into a global function
`f` is resolved through the links of `f`, so the global names in the quote or
`fn` body it is built from are also links of `f`. Names that only compute the
code (a call such as `emit(n)`, or the inside of `unquote(...)` and
`literal(...)`) are links of the enclosing function only. A target that only
`base` declares keeps its links.

Indentation is by spaces, consistent within a block; tabs are rejected.
`#` starts a comment to the end of the line.

## 2. Names

**Decided:**

Inside a function, a name is a parameter, a `let` name (section 4), a
declared global, or a name of the `base` state (section 7). A name that is
both local and global is a `SourceError`. Uses:

    counter                 read of a global cell
    counter = e             write of a global cell (a statement)
    f(a, b)                 call of a global function
    g(a, b)                 apply, when g is a parameter or let name
    ref(f)                  a reference to global function f
    code(f), linksof(f)     code and links of global function f

Assigning to a parameter or let name, reading a function as a value
without `ref`, and calling a cell are `SourceError`s. These names are
reserved and cannot be declared bare: `fn cell let if else true false none
quote unquote literal function activate trial label raw ref code linksof
apply len item slice concat closure captures`. In backquotes (`` `len` ``)
they are ordinary names, which a declaration, parameter, `let`, closure
parameter or closure capture may use where it does not clash with a global.

## 3. Expressions

**Decided:**

    1  -1  true  false  none  "text"   literals (strings as JSON strings)
    (a, b)  (a,)  ()                   tuple of values
    a + b  a - b  a * b                add, sub, mul
    a < b  a == b                      lt, eq (no other comparisons)
    x if c else y                      inline if
    len(t) item(t, i) slice(t, a, b) concat(a, b)
    apply(f, args)                     applyv: call f with a tuple of args
    function(params, body)             a function value from computed parts
    fn(x, y): EXPR                     a function value with a literal body
    closure(x, y) captures(a, b): EXPR executable lexical closure
    quote(EXPR)                        code as data, with holes (below)
    label(NAME, EXPR)                  a labelled node (graph_form.md §9)
    activate(TARGET = VALUE, ...)      TARGET is f, or f.label for a node
    trial(f(args), TARGET = VALUE, ...)
    raw(DATA)                          an input-form expression, verbatim

Precedence, lowest first: inline if; `fn` and `closure`; `<` and `==`
(not chained); `+` and `-`; `*`; calls and atoms. Parentheses group.

**Closures.** `closure(PARAM, ...) captures(NAME, ...): EXPR` is the source
form of the canonical input form

    ("closure", (PARAM, ...), (NAME, ...), EXPR)

Captures are explicit: the syntax does not infer free variables. Every
capture must name a parameter or `let` binding in scope where the closure is
created. Parameters and captures are each unique, and the two sets may not
overlap.

Only the declared captures and the closure's parameters are in lexical scope
inside its body. Other locals of the creating function are not visible.
Captures are by value when the closure is created; the caller's scope does
not participate when it is later invoked. See closures.md.

An empty parameter list and an empty capture list are both valid:

    closure() captures(): 1

A closure may itself capture another closure or function reference because
captures are ordinary runtime values.

A closure inside `quote(...)` is not supported by version 0 syntax and must
be represented with `raw(...)`, as for `fn` inside a quote.

**Apply.** A call whose head is a simple local name renders naturally as

    f(a, b)

and parses to variadic `apply`. The general source form

    apply(value, args)

takes the arguments as one tuple and parses to `applyv`.

When rendering a variadic `apply` whose callable is not a simple local name,
the renderer normalizes it to the general form by packing its operands into
a tuple. For example:

    ("apply", ("add", ("arg", "x"), ("arg", "x")), ("lit", 1))

renders as:

    apply(x + x, (1,))

Parsing that text yields `applyv`; rendering it again gives the same text.
The text projection therefore preserves behaviour and reaches a textual
fixpoint without preserving the exact input-form operation.

**Quote.** Inside `quote(...)` and the body of `fn(...):`, code is data.
`unquote(e)` is a hole filled with the code `e` evaluates to, and
`literal(e)` is a literal node whose value is what `e` evaluates to
(`("lit", ("unquote", e))`). Outside a quote, both are `SourceError`s.
Inside a quote, a declared global cell or function resolves as outside
(read, write, call), and any other name is a parameter of the code being
built (`arg`); local names of the enclosing function are not visible.
The expression inside `unquote(...)` or `literal(...)` is back in the
enclosing function, so its parameters and let names are visible there.

**Data literals** (cell initial values, and the argument of `raw`) are
ints, `true`, `false`, `none`, strings and tuples of data literals.

## 4. Blocks

**Decided:**

A block is one or more statements, one per line; its value is the value of
the last. Statements are expressions, cell writes, `let` and block `if`:

    let y = e               binds y for the rest of the block
    let y = counter = e     the value may be a cell write, a statement too
    if c:                   block if; the else part is required
        BLOCK
    else:
        BLOCK

A `let` must be followed by at least one statement. Several statements
make a `seq`; a `let` wraps the rest of its block.

A closure may capture a parameter or any `let` name already in scope at its
creation point. A later `let` is not visible to an earlier closure.

## 5. Rendering

**Decided:**

Rendering semantics.

**Provisional:**

Layout.

`render(state, function)` prints one function of a graph-form state as an
`fn` declaration ending with a newline, and `render_program(state)` prints
every cell as a `cell` declaration, one per line, then every function, both
in `EntityID` order, separated by one blank line (a cell whose constraint or
initial value the syntax cannot write is a comment). Bodies are indented by
four spaces. Names are printed as the current target entity names, so
renaming a function shows in the text of its callers. A name that is not an
identifier, or is reserved, is printed in backquotes, `` `name.x` ``, which
the parser accepts anywhere a name is expected.

Rendering never fails: anything the syntax cannot express, such as an
`invalid` node, a record in a literal, or a quote template that is not code,
is printed as `raw(...)`. Rendering chooses one form where several parse to
the same behaviour: a block `if` for a statement and the last statement of a
block, the inline form elsewhere; `quote(...)` for a literal whose value is
well-formed code; and the general `apply(value, tuple)` form where a
variadic `apply` cannot be printed as a local call.

A well-formed closure renders as

    closure(PARAM, ...) captures(NAME, ...): EXPR

when all captures are in the enclosing lexical scope and the body can be
represented by version 0 syntax. Otherwise the smallest enclosing
unrepresentable expression falls back to `raw(...)`.

## 6. Round trip

**Decided:**

Text round-trips by behaviour and by text, not by exact input form (a
tuple of literals and a literal tuple, for example, parse to different
tuples that behave the same):

- every corpus example, with its functions rendered and parsed back, passes
  its scenarios;
- rendering a parsed program gives back the same text;
- corpus examples not tagged `self-modification` render without `raw`;
- the closure corpus examples `make_adder` and `compose` render and parse
  without losing their explicit captures;
- a general variadic `apply` may normalize to `applyv`, but its rendered text
  is then a fixpoint.

## 7. API

    parse(text, base=None) -> State
        the input-format state for the declarations in text; with base (an
        input-format state), also every entity of base that text does not
        declare, except the links relations of functions text declares, and
        names resolve against base too (so functions can be replaced)
    render(state, function) -> str
    render_program(state) -> str
    SourceError(ValueError)
        with .line and .column (1-based)

Module `shear/syntax.py`, built on `shear.lang`.

## 8. Implementation notes

**Decided:**

Found while making the corpus round-trip and adding closures.

- One statement per line; there are no continuation lines. A tab anywhere
  outside a string or comment is a `SourceError`.
- `raw(DATA)` is verbatim: in code it is the expression, in a quote it is a
  piece of the template. The link names inside it are registered as links of
  the function, and `render` prints them as the current target names. A leaf
  the syntax cannot write, such as an entity or a function value, is printed
  in angle brackets, which the parser rejects, so it is visible, never
  silently changed.
- Rendering replaces the smallest piece that cannot be written by `raw`: a
  `let` or `seq` in expression position, a cell write anywhere but a
  statement or a `let` value, a `let` that is not last in its block, an
  unknown link, and a name that is both local and global. Inside a quote the
  whole `quote(...)` becomes `raw`, since a template is one piece of data.
- In a quote template, link names are printed as they are (the code built
  from the template resolves them through its own function) and must be
  names of the program. A quote inside a quote, `fn` inside a quote and
  `closure` inside a quote are not in version 0: the parser rejects them and
  the renderer prints `raw`.
- A literal that holds code prints as `quote(...)`, one that holds a tuple of
  data as a tuple, so `("lit", ("lit", 1))` and `quote(1)` are one text.
- `fn(params): body` is printed for a function value whose parameters are a
  literal tuple of names and whose body is a quote (or a literal of code);
  every other function value prints as `function(params, body)`.
- Closure syntax keeps capture declaration explicit rather than inferring
  free variables. This mirrors the canonical semantic form and prevents the
  source projection from introducing an independent capture-inference rule.
- A variadic `apply` with a simple local head prints as ordinary call syntax.
  Any other callable head is normalized to `apply(value, tuple)`, which
  parses as `applyv`; this intentionally preserves semantic/textual
  round-trip rather than exact input-form identity.
- Corpus: every example renders without `raw` except `instrument`, whose
  template writes a cell (`("write", "hits", ...)`), which the syntax has no
  form for inside a quote.
