# Name Resolution

This specifies the name-resolution rules used by text syntax and the
reconciler. It does not introduce new syntax.

## 1. Lexical names

**Provisional.**

A function has one lexical namespace.

Resolution of an ordinary name in a function body is:

1. the innermost active `let` binding;
2. a function parameter;
3. a program declaration.

A `let` is visible only in the remainder of the block it wraps. A parameter
is visible throughout its function.

A local name and a program declaration may not have the same name in one
function. Version 0 rejects that case rather than choosing one interpretation.
This preserves the existing `SourceError` rule in `syntax.md`.

Inside `quote(...)`, the quote has its own code namespace. A name that is not
a program declaration denotes an argument of the code being constructed.
Lexical names of the enclosing function are not captured. The expression
inside `unquote(...)` or `literal(...)` returns to the enclosing lexical
scope.

Backquoted names obey exactly the same resolution rules as ordinary names.
Backquotes only allow spelling a name that would otherwise be reserved or
lexically invalid.

## 2. Program names

**Provisional.**

Version 0 has one program-global namespace. Cells and functions occupy that
same namespace and declaration names are unique.

A global source name resolves to the `EntityID` of the declaration with that
name. Function code records the result through its definition's link
endpoints. The spelling in source is therefore not the semantic reference:
after resolution, relation endpoints identify the target.

This is why a target rename can change rendered source without rewriting the
call node itself.

Declarations may be used before their textual declaration. Resolution is
therefore against the complete declaration set, not declaration order.

## 3. Modules

**Provisional.**

There is one implicit root module: the program itself.

Task 15 does not add module declarations, imports, qualified names, module
entities or a program-root entity. Those require syntax and ownership choices
that the current language has deliberately deferred.

For the reconciler, "module resolution" therefore means resolution in the
single program-global namespace described above.

When explicit modules are added, this section must be replaced by rules for
module ownership, qualification, imports and ambiguity. The lexical rules in
section 1 need not change.

## 4. Reconciliation

**Provisional.**

The graph state is authoritative. Edited text is a proposed new source view
of that state, not a second authoritative representation.

Reconciliation performs these stages:

1. parse the complete edited text;
2. resolve lexical names by section 1;
3. resolve program names by section 2;
4. compare its declarations with the current graph state;
5. express changed function definitions through `lang.define`;
6. let continuity inference match old and new graph nodes;
7. return one `TransformResult`.

An unchanged source declaration is not rebuilt merely because the file was
parsed again. Its existing graph entities remain untouched.

A changed function keeps its function `EntityID`. Its old and new body nodes
are passed through continuity inference. Unambiguous unchanged descendants
therefore keep identity; ambiguous matches receive new identity.

Adding or removing a function is an ordinary `define` creation or removal.

## 5. Renames

**Provisional.**

A bare textual declaration rename is not enough evidence that two differently
named top-level declarations are the same entity.

For example, changing:

    fn old():
        1

to:

    fn new():
        1

is interpreted as removing `old` and creating `new`, unless some future
source-level mechanism explicitly supplies continuity.

This follows the task-13 rule: ambiguity receives new identity rather than a
guess.

References in the edited source resolve to whichever declaration their new
spelling names.

## 6. Cells

**Provisional.**

Task 15 preserves existing cell declarations and their identity when their
source declaration is unchanged.

Changing, adding or removing a cell declaration is outside the first
reconciler slice. Cell declaration changes interact with runtime cell content,
constraints and conversion semantics, so they require an explicit policy
rather than treating a source edit as a value replacement.

The reconciler rejects such edits instead of silently rebuilding cells.

Function edits may freely change which existing cells they reference.

## 7. Errors

**Provisional.**

Syntax and name-resolution failures remain `SourceError`s with source
positions.

A source edit that is syntactically valid but outside the supported
reconciliation rules raises `ReconcileError`.

No failed reconciliation changes the source graph state.

## 8. Open

**Open.**

The following are deliberately not decided by task 15:

- explicit program-root representation;
- module entities and ownership;
- import and export syntax;
- qualified names;
- cross-module ambiguity;
- source syntax for declaring top-level continuity, including renames;
- cell migration and conversion syntax.
- - `lang.define` input representation for multiple edits targeting one entity;
  reconciliation currently uses collision-free temporary `EntityID` keys for
  relation edits because `define` accepts a mapping with one value per key.
