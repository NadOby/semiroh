# Text Syntax, Version 0

**Status: planned** (roadmap.md task 11). `semiroh/syntax.py` does not exist
yet; the acceptance tests in `tests/test_syntax.py` fail until it does.

Programs have been written as nested tuples. This step adds a human source
view (syntax_notes.md, Direction A): `parse` reads text into the input
format, which `load` turns into graph form, and `render` prints graph form
back as text. The graph stays authoritative; text is a projection.

Version 0 is **import-only**: editing text and parsing it again creates new
nodes. A reconciler that turns an edited text into a transformation with
continuity comes later (roadmap.md, Later).

## 1. Programs

**Decided.**

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

Indentation is by spaces, consistent within a block; tabs are rejected.
`#` starts a comment to the end of the line.

## 2. Names

**Decided.**

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
reserved and cannot be declared: `fn cell let if else true false none quote
unquote literal function activate trial label raw ref code linksof apply
len item slice concat`.

## 3. Expressions

**Decided.**

    1  -1  true  false  none  "text"   literals (strings as JSON strings)
    (a, b)  (a,)  ()                   tuple of values
    a + b  a - b  a * b                add, sub, mul
    a < b  a == b                      lt, eq (no other comparisons)
    x if c else y                      inline if
    len(t) item(t, i) slice(t, a, b) concat(a, b)
    apply(f, args)                     applyv: call f with a tuple of args
    function(params, body)             a function value from computed parts
    fn(x, y): EXPR                     a function value with a literal body
    quote(EXPR)                        code as data, with holes (below)
    label(NAME, EXPR)                  a labelled node (graph_form.md §9)
    activate(TARGET = VALUE, ...)      TARGET is f, or f.label for a node
    trial(f(args), TARGET = VALUE, ...)
    raw(DATA)                          an input-form expression, verbatim

Precedence, lowest first: inline if; `<` and `==` (not chained); `+` and
`-`; `*`; calls and atoms. Parentheses group.

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

**Decided.**

A block is one or more statements, one per line; its value is the value of
the last. Statements are expressions, cell writes, `let` and block `if`:

    let y = e               binds y for the rest of the block
    if c:                   block if; the else part is required
        BLOCK
    else:
        BLOCK

A `let` must be followed by at least one statement. Several statements
make a `seq`; a `let` wraps the rest of its block.

## 5. Rendering

**Decided**, the layout **Provisional**.

`render(state, function)` prints one function of a graph-form state as an
`fn` declaration ending with a newline, and `render_program(state)` prints
every function, in `EntityID` order, separated by one blank line. Bodies
are indented by four spaces. Names are printed as the
current target entity names, so renaming a function shows in the text of
its callers. A name that is not an identifier, or is reserved, is printed
in backquotes, `` `name.x` ``, which the parser accepts anywhere a name is
expected.

Rendering never fails: anything the syntax cannot express, such as an
`invalid` node, a record in a literal, or a quote template that is not
code, is printed as `raw(...)`. Rendering chooses one form where several
parse to the same behaviour: a block `if` for a statement and the last
statement of a block, the inline form elsewhere; `quote(...)` for a literal
whose value is well-formed code.

## 6. Round trip

**Decided.**

Text round-trips by behaviour and by text, not by exact input form (a
tuple of literals and a literal tuple, for example, parse to different
tuples that behave the same):

- every corpus example, with its functions rendered and parsed back, passes
  its scenarios;
- rendering a parsed program gives back the same text;
- corpus examples not tagged `self-modification` render without `raw`.

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

Module `semiroh/syntax.py`, built on `semiroh.lang`.
