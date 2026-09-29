"""Text syntax, version 0 (docs/syntax.md): a source view of programs.

``parse`` reads program text into the input format (first_program.md), which
``semiroh.lang.load`` turns into graph form; ``render`` and
``render_program`` print graph form back as text. The graph stays
authoritative and text is a projection: parsing edited text creates new
nodes (version 0 is import-only).

This module is a layer on top of ``semiroh.lang``, not part of the core
model, and is not re-exported from ``semiroh/__init__.py``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from .canonical import CanonicalNode
from .cells import CellDeclaration, cell_declaration
from .constraints import IntRange, IsKind
from .identity import EntityID
from .lang import (
    _ARITY,
    FUNCTION_ROLE,
    LINKS_KIND,
    NODE_KINDS,
    Function,
    _decode,
    _definition_of,
    function_at,
    function_of,
)
from .relations import Relation, relation_of
from .state import State
from .values import Value

__all__ = ["SourceError", "parse", "render", "render_program"]

RESERVED = frozenset(
    "fn cell let if else true false none quote unquote literal function "
    "activate trial label raw ref code linksof apply len item slice "
    "concat".split()
)

# Cell type names other than ``int``, and the ``IsKind`` kind each stands for.
_TYPE_KINDS = {"bool": "bool", "str": "str", "tuple": "tuple", "entity": "entity_id"}


class SourceError(ValueError):
    """The text is not a valid program; ``line`` and ``column`` are 1-based."""

    def __init__(self, message: str, line: int = 1, column: int = 1) -> None:
        super().__init__(f"line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Token:
    """One token. ``kind`` is name, int, string, op, newline, indent, dedent
    or eof; a backquoted name has ``quoted`` set and is never a keyword.
    """

    kind: str
    value: Any
    line: int
    column: int
    quoted: bool = False


_NAME = re.compile(r"[^\W\d]\w*")
_INT = re.compile(r"\d+")
_STRING = re.compile(r'"(?:[^"\\\x00-\x1f]|\\.)*"')
_OPS = ("==", "..", "(", ")", ",", ":", "=", "+", "-", "*", "<", ".")
_NAME_ESCAPES = {"\\": "\\", "`": "`", "n": "\n", "r": "\r", "t": "\t"}


def _scan_name(line: str, start: int, number: int) -> tuple[str, int]:
    """Read a backquoted name starting at ``line[start]``."""

    out: list[str] = []
    i = start + 1

    while i < len(line):
        char = line[i]

        if char == "`":
            if not out:
                raise SourceError("empty name", number, start + 1)

            return "".join(out), i + 1

        if char == "\\":
            i += 1
            escape = line[i] if i < len(line) else ""

            if escape in _NAME_ESCAPES:
                out.append(_NAME_ESCAPES[escape])
            elif escape == "u" and re.fullmatch(r"[0-9a-fA-F]{4}", line[i + 1:i + 5]):
                out.append(chr(int(line[i + 1:i + 5], 16)))
                i += 4
            else:
                raise SourceError("invalid escape in name", number, i + 1)
        else:
            out.append(char)

        i += 1

    raise SourceError("unterminated name", number, start + 1)


def tokenize(text: str) -> list[Token]:
    """Split program text into tokens, with INDENT and DEDENT for blocks."""

    tokens: list[Token] = []
    indents = [0]
    lines = text.split("\n")

    for number, raw_line in enumerate(lines, 1):
        line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        body = line.lstrip(" ")
        indent = len(line) - len(body)

        if not body.strip() or body.lstrip("\t ").startswith("#"):
            continue

        if body.startswith("\t"):
            raise SourceError("tabs are not allowed in indentation", number, indent + 1)

        if indent > indents[-1]:
            indents.append(indent)
            tokens.append(Token("indent", None, number, indent + 1))
        else:
            while indent < indents[-1]:
                indents.pop()
                tokens.append(Token("dedent", None, number, indent + 1))

            if indent != indents[-1]:
                raise SourceError("inconsistent indentation", number, indent + 1)

        pos = indent

        while pos < len(line):
            char = line[pos]
            column = pos + 1

            if char == " ":
                pos += 1
            elif char == "\t":
                raise SourceError("tabs are not allowed", number, column)
            elif char == "#":
                break
            elif char == '"':
                match = _STRING.match(line, pos)

                if match is None:
                    raise SourceError("unterminated or invalid string", number, column)

                try:
                    value = json.loads(match.group())
                except ValueError:
                    raise SourceError("invalid escape in string", number, column) from None

                tokens.append(Token("string", value, number, column))
                pos = match.end()
            elif char == "`":
                name, pos = _scan_name(line, pos, number)
                tokens.append(Token("name", name, number, column, quoted=True))
            elif (match := _NAME.match(line, pos)) is not None:
                tokens.append(Token("name", match.group(), number, column))
                pos = match.end()
            elif (match := _INT.match(line, pos)) is not None:
                pos = match.end()

                if pos < len(line) and (line[pos].isalnum() or line[pos] == "_"):
                    raise SourceError("invalid number", number, column)

                tokens.append(Token("int", int(match.group()), number, column))
            else:
                for op in _OPS:
                    if line.startswith(op, pos):
                        tokens.append(Token("op", op, number, column))
                        pos += len(op)
                        break
                else:
                    raise SourceError(f"unexpected character {char!r}", number, column)

        tokens.append(Token("newline", None, number, len(line) + 1))

    last = len(lines)

    for _ in indents[1:]:
        tokens.append(Token("dedent", None, last, 1))

    tokens.append(Token("eof", None, last, 1))
    return tokens


# ---------------------------------------------------------------------------
# Input-form helpers
# ---------------------------------------------------------------------------


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
        return (op, *(
            target(child) if index % 2 == 0 else sub(child)
            for index, child in enumerate(rest)
        ))

    if op == "trial":
        if not rest:
            return expr

        return (op, sub(rest[0]), *(
            target(child) if index % 2 == 0 else sub(child)
            for index, child in enumerate(rest[1:])
        ))

    if op == "let" and len(rest) == 3:
        return (op, rest[0], sub(rest[1]), sub(rest[2]))

    if op == "label" and len(rest) == 2:
        return (op, rest[0], sub(rest[1]))

    return (op, *(sub(child) for child in rest))


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_ORDINARY, _HOLES = 0, 1


def _base_kinds(base: State | None) -> dict[str, str]:
    kinds: dict[str, str] = {}

    if base is not None:
        for entity, value in base.values.items():
            if cell_declaration(value) is not None:
                kinds[entity.value] = "cell"
            elif function_of(value) is not None or _definition_of(value) is not None:
                kinds[entity.value] = "fn"

    return kinds


class _Parser:
    def __init__(self, tokens: list[Token], base: State | None) -> None:
        self.tokens = tokens
        self.pos = 0
        self.kinds = _base_kinds(base)
        self.declared: dict[str, str] = {}
        self.mode = _ORDINARY
        self.locals: list[str] = []
        self.used: dict[str, None] = {}
        self.collectors: list[dict[str, None]] = []
        self.extra: dict[str, dict[str, None]] = {}
        self._prescan()

    # -- token access ------------------------------------------------------

    def peek(self, ahead: int = 0) -> Token:
        return self.tokens[min(self.pos + ahead, len(self.tokens) - 1)]

    def next(self) -> Token:
        token = self.peek()

        if token.kind != "eof":
            self.pos += 1

        return token

    def error(self, message: str, token: Token | None = None) -> SourceError:
        token = token or self.peek()
        return SourceError(message, token.line, token.column)

    def is_op(self, value: str, ahead: int = 0) -> bool:
        token = self.peek(ahead)
        return token.kind == "op" and token.value == value

    def is_word(self, value: str, ahead: int = 0) -> bool:
        token = self.peek(ahead)
        return token.kind == "name" and not token.quoted and token.value == value

    def accept_op(self, value: str) -> bool:
        if self.is_op(value):
            self.next()
            return True

        return False

    def expect_op(self, value: str) -> Token:
        if not self.is_op(value):
            raise self.error(f"expected {value!r}")

        return self.next()

    def expect_int(self) -> int:
        token = self.next()

        if token.kind != "int":
            raise self.error("expected a number", token)

        return token.value

    def end_of_statement(self) -> None:
        token = self.peek()

        if token.kind != "newline":
            raise self.error("unexpected " + _describe(token))

        self.next()

    def _prescan(self) -> None:
        """Register every declared name first, so uses may come before it."""

        depth = 0
        at_start = True
        tokens = self.tokens

        for index, token in enumerate(tokens):
            if token.kind == "indent":
                depth += 1
            elif token.kind == "dedent":
                depth -= 1
            elif token.kind == "newline":
                at_start = True
            else:
                if (
                    at_start
                    and depth == 0
                    and token.kind == "name"
                    and not token.quoted
                    and token.value in ("cell", "fn")
                    and tokens[index + 1].kind == "name"
                ):
                    self.kinds[tokens[index + 1].value] = token.value

                at_start = False

    # -- declarations ------------------------------------------------------

    def run(self, base: State | None) -> State:
        entities: dict[EntityID, Any] = {}
        used_by: dict[str, dict[str, None]] = {}

        while True:
            token = self.peek()

            if token.kind == "eof":
                break

            if token.kind == "indent":
                raise self.error("unexpected indent")

            if self.is_word("cell"):
                name, content = self.cell()
                entities[EntityID(name)] = content
            elif self.is_word("fn"):
                name, content, used = self.function()
                entities[EntityID(name)] = content
                used_by[name] = used
            else:
                raise self.error("expected a 'cell' or 'fn' declaration, found " + _describe(token))

        for name, used in used_by.items():
            used.update(self.extra.get(name, {}))

        return _merge(base, entities, used_by, self.declared)

    def declaration_name(self, kind: str) -> Token:
        token = self.next()

        if token.kind != "name":
            raise self.error("expected a name", token)

        if not token.quoted and token.value in RESERVED:
            raise self.error(
                f"{token.value!r} is reserved and cannot be declared "
                f"(write it in backquotes to use it as a name)",
                token,
            )

        if token.value in self.declared:
            raise self.error(f"{token.value!r} is already declared", token)

        self.declared[token.value] = kind
        return token

    def cell(self) -> tuple[str, CellDeclaration]:
        self.next()
        name = self.declaration_name("cell")
        self.expect_op(":")
        type_token = self.next()

        if type_token.kind != "name" or type_token.quoted:
            raise self.error("expected a cell type", type_token)

        constraint: IntRange | IsKind

        if type_token.value == "int":
            if self.is_word("in"):
                self.next()
                low = self.optional_int()
                self.expect_op("..")
                high = self.optional_int()

                try:
                    constraint = IntRange(low, high)
                except ValueError as exc:
                    raise self.error(str(exc), type_token) from None
            else:
                constraint = IsKind("int")
        elif type_token.value in _TYPE_KINDS:
            constraint = IsKind(_TYPE_KINDS[type_token.value])
        else:
            raise self.error(f"unknown cell type {type_token.value!r}", type_token)

        self.expect_op("=")
        initial = self.data()
        self.end_of_statement()
        return name.value, CellDeclaration(constraint, initial)

    def optional_int(self) -> int | None:
        if self.accept_op("-"):
            return -self.expect_int()

        if self.peek().kind == "int":
            return self.next().value

        return None

    def function(self) -> tuple[str, Function, dict[str, None]]:
        self.next()
        name = self.declaration_name("fn")
        self.expect_op("(")
        params = self.params()
        self.expect_op(":")
        self.locals = list(params)
        self.used = {}
        self.mode = _ORDINARY
        body = self.suite()

        try:
            function = Function(tuple(params), body)
        except TypeError as exc:
            raise self.error(str(exc), name) from None

        return name.value, function, self.used

    def params(self) -> list[str]:
        """Read parameter names up to and including the closing ``)``."""

        names: list[str] = []

        if self.accept_op(")"):
            return names

        while True:
            token = self.next()
            self.check_local(token)

            if token.value in names:
                raise self.error(f"duplicate parameter {token.value!r}", token)

            names.append(token.value)

            if self.accept_op(","):
                continue

            self.expect_op(")")
            return names

    def check_local(self, token: Token) -> None:
        if token.kind != "name":
            raise self.error("expected a name", token)

        if not token.quoted and token.value in RESERVED:
            raise self.error(
                f"{token.value!r} is reserved (write it in backquotes to use it as a name)",
                token,
            )

        if token.value in self.kinds:
            raise self.error(
                f"{token.value!r} is both a local and a global name",
                token,
            )

    # -- blocks and statements ---------------------------------------------

    def suite(self) -> Any:
        if self.peek().kind != "newline":
            raise self.error("expected the end of the line after ':'")

        self.next()

        if self.peek().kind != "indent":
            raise self.error("expected an indented block")

        self.next()
        return self.block()

    def block(self) -> Any:
        mark = len(self.locals)
        items: list[tuple] = []

        while self.peek().kind not in ("dedent", "eof"):
            items.append(self.statement())

        if self.peek().kind == "dedent":
            self.next()

        del self.locals[mark:]
        return self.fold(items)

    def fold(self, items: list[tuple]) -> Any:
        nodes: list[Any] = []

        for index, item in enumerate(items):
            if item[0] == "let":
                _, name, value, token = item

                if index == len(items) - 1:
                    raise self.error("a let must be followed by a statement", token)

                nodes.append(("let", name, value, self.fold(items[index + 1:])))
                break

            nodes.append(item[1])

        return nodes[0] if len(nodes) == 1 else ("seq", *nodes)

    def statement(self) -> tuple:
        token = self.peek()

        if token.kind == "indent":
            raise self.error("unexpected indent")

        if self.is_word("let"):
            return self.let_statement()

        if self.is_word("if"):
            return self.if_statement()

        if self.is_word("else"):
            raise self.error("else without if")

        if token.kind == "name" and self.is_op("=", 1):
            return ("expr", self.assignment())

        node = self.expr()
        self.end_of_statement()
        return ("expr", node)

    def let_statement(self) -> tuple:
        token = self.next()
        name = self.next()
        self.check_local(name)
        self.expect_op("=")
        value = self.write() if self.peek().kind == "name" and self.is_op("=", 1) else self.expr()
        self.end_of_statement()
        self.locals.append(name.value)
        return ("let", name.value, value, token)

    def if_statement(self) -> tuple:
        token = self.next()
        condition = self.expr()
        self.expect_op(":")
        then = self.suite()

        if not self.is_word("else"):
            raise self.error("an if needs an else part", token)

        self.next()
        self.expect_op(":")
        other = self.suite()
        return ("expr", ("if", condition, then, other))

    def assignment(self) -> Any:
        node = self.write()
        self.end_of_statement()
        return node

    def write(self) -> Any:
        """``NAME = EXPR``: a write of a global cell, without its newline."""

        name = self.next()
        self.next()

        if name.value in self.locals:
            raise self.error(
                f"cannot assign to {name.value!r}: only global cells can be assigned",
                name,
            )

        if self.kinds.get(name.value) != "cell":
            raise self.error(f"cannot assign to {name.value!r}: it is not a cell", name)

        value = self.expr()
        self.use(name)
        return ("write", name.value, value)

    def use(self, token: Token) -> None:
        if token.value == FUNCTION_ROLE:
            raise self.error("'function' cannot be used as a global name", token)

        self.record(token.value)

    def record(self, name: str) -> None:
        self.used[name] = None

        # A name in a hole, or in a call that computes the code, belongs to
        # the enclosing function only; a name in the code being built (a
        # quote or an fn body) is also a name of the target it is installed in.
        if self.mode == _HOLES:
            for collector in self.collectors:
                collector[name] = None

    # -- expressions -------------------------------------------------------

    def expr(self) -> Any:
        node = self.comparison()

        if self.is_word("if"):
            self.next()
            condition = self.comparison()

            if not self.is_word("else"):
                raise self.error("expected 'else'")

            self.next()
            return ("if", condition, node, self.expr())

        return node

    def comparison(self) -> Any:
        left = self.additive()
        token = self.peek()

        if token.kind == "op" and token.value in ("<", "=="):
            self.next()
            node = ("lt" if token.value == "<" else "eq", left, self.additive())
            follow = self.peek()

            if follow.kind == "op" and follow.value in ("<", "=="):
                raise self.error("comparisons cannot be chained", follow)

            return node

        return left

    def additive(self) -> Any:
        node = self.multiplicative()

        while self.peek().kind == "op" and self.peek().value in ("+", "-"):
            op = "add" if self.next().value == "+" else "sub"
            node = (op, node, self.multiplicative())

        return node

    def multiplicative(self) -> Any:
        node = self.atom()

        while self.is_op("*"):
            self.next()
            node = ("mul", node, self.atom())

        return node

    def atom(self) -> Any:
        token = self.peek()

        if token.kind in ("int", "string"):
            self.next()
            return ("lit", token.value)

        if token.kind == "op":
            if token.value == "-":
                self.next()
                return ("lit", -self.expect_int())

            if token.value == "(":
                self.next()
                return self.parenthesized(self.expr, lambda items: ("tuple", *items))

            raise self.error("unexpected " + _describe(token))

        if token.kind == "name":
            if not token.quoted and token.value in RESERVED:
                return self.builtin(token)

            return self.name_use(token)

        raise self.error("unexpected " + _describe(token))

    def parenthesized(self, element: Callable[[], Any], build: Callable[[list], Any]) -> Any:
        """Read what follows ``(``: a group, or a tuple; consumes the ``)``."""

        if self.accept_op(")"):
            return build([])

        first = element()

        if self.accept_op(")"):
            return first

        items = [first]

        while self.accept_op(","):
            if self.accept_op(")"):
                return build(items)

            items.append(element())

            if self.accept_op(")"):
                return build(items)

        self.expect_op(")")
        raise AssertionError("unreachable")

    def call_args(self) -> list[Any]:
        self.expect_op("(")
        args: list[Any] = []

        if self.accept_op(")"):
            return args

        while True:
            args.append(self.expr())

            if self.accept_op(","):
                continue

            self.expect_op(")")
            return args

    def in_mode(self, mode: int, parse: Callable[[], Any]) -> Any:
        saved = self.mode
        self.mode = mode

        try:
            return parse()
        finally:
            self.mode = saved

    def name_use(self, token: Token) -> Any:
        self.next()
        name = token.value
        kind = self.kinds.get(name)
        call = self.is_op("(")

        if self.mode == _ORDINARY and name in self.locals:
            if call:
                return ("apply", ("arg", name), *self.call_args())

            return ("arg", name)

        if kind == "cell":
            if call:
                raise self.error(f"{name!r} is a cell and cannot be called", token)

            self.use(token)
            return ("read", name)

        if kind == "fn":
            if not call:
                raise self.error(
                    f"{name!r} is a function; write ref({name}) to use it as a value",
                    token,
                )

            self.use(token)
            return ("call", name, *self.call_args())

        if self.mode == _HOLES:
            if call:
                return ("apply", ("arg", name), *self.call_args())

            return ("arg", name)

        raise self.error(f"unknown name {name!r}", token)

    def global_function(self, token: Token) -> str:
        if token.kind != "name":
            raise self.error("expected a function name", token)

        if self.kinds.get(token.value) != "fn":
            raise self.error(f"{token.value!r} is not a declared function", token)

        self.use(token)
        return token.value

    def fixed_args(self, token: Token, count: int) -> list[Any]:
        args = self.call_args()

        if len(args) != count:
            raise self.error(f"{token.value} takes {count} argument(s), got {len(args)}", token)

        return args

    def builtin(self, token: Token) -> Any:
        name = token.value
        self.next()

        if name in ("true", "false", "none"):
            return ("lit", {"true": True, "false": False, "none": None}[name])

        if name in ("len", "item", "slice", "concat"):
            arity = {"len": 1, "item": 2, "slice": 3, "concat": 2}[name]
            return (name, *self.fixed_args(token, arity))

        if name == "apply":
            return ("applyv", *self.fixed_args(token, 2))

        if name == "function":
            return ("function", *self.fixed_args(token, 2))

        if name in ("ref", "code", "linksof"):
            self.expect_op("(")
            target = self.global_function(self.next())
            self.expect_op(")")
            return (name, target)

        if name == "fn":
            return self.fn_value(token)

        if name == "quote":
            if self.mode == _HOLES:
                raise self.error("quote inside quote is not supported; use raw", token)

            self.expect_op("(")
            template = self.in_mode(_HOLES, self.expr)
            self.expect_op(")")
            return ("quote", template)

        if name in ("unquote", "literal"):
            if self.mode != _HOLES:
                raise self.error(f"{name} outside quote", token)

            self.expect_op("(")
            inner = self.in_mode(_ORDINARY, self.expr)
            self.expect_op(")")
            return ("unquote", inner) if name == "unquote" else ("lit", ("unquote", inner))

        if name == "label":
            self.expect_op("(")
            label = self.next()

            if label.kind != "name" or (not label.quoted and label.value in RESERVED):
                raise self.error("expected a label name", label)

            self.expect_op(",")
            inner = self.expr()
            self.expect_op(")")
            return ("label", label.value, inner)

        if name == "activate":
            self.expect_op("(")
            return ("activate", *self.pairs(self.target_pair))

        if name == "trial":
            return self.trial(token)

        if name == "raw":
            self.expect_op("(")
            data = self.data()
            self.expect_op(")")
            # Raw data is code as data: its names are names of the code built.
            return self.in_mode(_HOLES, lambda: _map_links(data, self.use_raw))

        raise self.error(f"unexpected {name!r}", token)

    def use_raw(self, name: str) -> str:
        if name in self.kinds and name != FUNCTION_ROLE:
            self.record(name)

        return name

    def fn_value(self, token: Token) -> Any:
        if self.mode == _HOLES:
            raise self.error("fn inside quote is not supported; use raw", token)

        self.expect_op("(")
        params = self.params()
        self.expect_op(":")
        body = self.in_mode(_HOLES, self.expr)
        return ("function", ("lit", tuple(params)), ("quote", body))

    def target_pair(self) -> list[Any]:
        """One ``TARGET = VALUE`` pair of activate or trial."""

        token = self.next()
        target: Any = self.global_function(token)

        if self.accept_op("."):
            label = self.next()

            if label.kind != "name":
                raise self.error("expected a label name", label)

            target = (target, label.value)

        self.expect_op("=")
        installed: dict[str, None] = {}
        self.collectors.append(installed)

        try:
            value = self.expr()
        finally:
            self.collectors.pop()

        # The code installed into a function is resolved through that
        # function's links, so the names it uses are links of the target too.
        self.extra.setdefault(token.value, {}).update(installed)
        return [target, value]

    def pairs(self, pair: Callable[[], list[Any]], first: bool = True) -> list[Any]:
        """Read ``pair`` items separated by commas, up to and including ``)``."""

        items: list[Any] = []

        if first and self.is_op(")"):
            raise self.error("expected at least one TARGET = VALUE")

        while True:
            items.extend(pair())

            if self.accept_op(","):
                continue

            self.expect_op(")")
            return items

    def trial(self, token: Token) -> Any:
        self.expect_op("(")
        callee = self.global_function(self.next())
        call = ("call", callee, *self.call_args())
        items: list[Any] = []

        while self.accept_op(","):
            items.extend(self.target_pair())

        self.expect_op(")")
        return ("trial", call, *items)

    # -- data literals -----------------------------------------------------

    def data(self) -> Any:
        token = self.next()

        if token.kind in ("int", "string"):
            return token.value

        if token.kind == "op" and token.value == "-":
            return -self.expect_int()

        if token.kind == "op" and token.value == "(":
            return self.parenthesized(self.data, tuple)

        if token.kind == "name" and not token.quoted and token.value in ("true", "false", "none"):
            return {"true": True, "false": False, "none": None}[token.value]

        raise self.error("expected a data literal", token)


def _describe(token: Token) -> str:
    if token.kind == "eof":
        return "end of text"

    if token.kind in ("newline", "indent", "dedent"):
        return token.kind

    return repr(token.value)


def _merge(
    base: State | None,
    entities: dict[EntityID, Any],
    used_by: dict[str, dict[str, None]],
    declared: dict[str, str],
) -> State:
    """The state for the declarations, over ``base`` if there is one."""

    declared_ids = {EntityID(name) for name in declared}
    functions = {EntityID(name) for name, kind in declared.items() if kind == "fn"}
    values: dict[EntityID, Value] = {}

    if base is not None:
        stale = {
            entity
            for entity, value in base.values.items()
            if (relation := relation_of(value)) is not None
            and relation.kind == LINKS_KIND
            and relation.roles.get(FUNCTION_ROLE) in functions
        }

        for entity, value in base.values.items():
            if entity not in declared_ids and entity not in stale:
                values[entity] = value

    taken = set(values) | declared_ids

    for entity, content in entities.items():
        values[entity] = Value.create(entity, content)

    for name, used in used_by.items():
        if not used:
            continue

        links_id = EntityID(f"{name}.links")
        suffix = 0

        while links_id in taken:
            suffix += 1
            links_id = EntityID(f"{name}.links.{suffix}")

        taken.add(links_id)
        relation = Relation(
            LINKS_KIND,
            {FUNCTION_ROLE: EntityID(name), **{target: EntityID(target) for target in used}},
        )
        values[links_id] = Value.create(links_id, relation)

    ownership = {}

    if base is not None:
        ownership = {
            owner: tuple(child for child in children if child in values)
            for owner, children in base.ownership.items()
            if owner in values
        }

    return State.create(values, ownership)


def parse(text: str, base: State | None = None) -> State:
    """Read program text into an input-format state.

    The state holds the declared cells and functions, and a links relation
    for each function that uses global names. With ``base`` (an input-format
    state), it also holds every entity of ``base`` that the text does not
    declare, except the links relations of functions the text declares, and
    names resolve against ``base`` too. Raises ``SourceError``.
    """

    return _Parser(tokenize(text), base).run(base)


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

_IDENTIFIER = re.compile(r"[^\W\d]\w*")


class _NoSyntax(Exception):
    """A piece of input form the syntax cannot express (rendered as raw)."""


def _name(name: str) -> str:
    """A name as text: bare if it is an identifier, backquoted otherwise."""

    if _IDENTIFIER.fullmatch(name) and name not in RESERVED:
        return name

    out: list[str] = []

    for char in name:
        code = ord(char)

        if char in "\\`":
            out.append("\\" + char)
        elif char == "\n":
            out.append("\\n")
        elif char == "\r":
            out.append("\\r")
        elif char == "\t":
            out.append("\\t")
        elif code < 0x20 or code == 0x7F or 0xD800 <= code <= 0xDFFF:
            out.append(f"\\u{code:04x}")
        else:
            out.append(char)

    return "`" + "".join(out) + "`"


def _scalar(value: Any) -> bool:
    return value is None or isinstance(value, (bool, int, str))


def _data_text(value: Any) -> str:
    """A data literal as text; raises ``_NoSyntax`` for anything else."""

    if value is True:
        return "true"

    if value is False:
        return "false"

    if value is None:
        return "none"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)

    if _tup(value):
        items = [_data_text(item) for item in value]

        if len(items) == 1:
            return f"({items[0]},)"

        return "(" + ", ".join(items) + ")"

    raise _NoSyntax


def _raw_text(value: Any) -> str:
    """Data as text for ``raw``; a leaf the syntax cannot write is shown in
    angle brackets, which the parser rejects.
    """

    if _tup(value):
        items = [_raw_text(item) for item in value]
        return "(" + ", ".join(items) + ("," if len(items) == 1 else "") + ")"

    try:
        return _data_text(value)
    except _NoSyntax:
        return f"<{value!r}>"


# operation: (symbol, own precedence, left operand needs, right operand needs)
_INFIX = {
    "add": ("+", 2, 2, 3),
    "sub": ("-", 2, 2, 3),
    "mul": ("*", 3, 3, 4),
    "lt": ("<", 1, 2, 2),
    "eq": ("==", 1, 2, 2),
}
_PLAIN = {"len", "item", "slice", "concat"}


class _Renderer:
    """Prints the input form of one function as text.

    ``names`` maps the function's link names to the names of their current
    target entities; ``known`` is every global name. Precedence levels: 0
    inline if and ``fn``, 1 comparison, 2 addition, 3 multiplication, 4
    atoms. ``mode`` is 0 in ordinary code, 1 in a quote template (holes
    allowed) and 2 in a template that is a literal's value (no holes).
    """

    def __init__(self, names: dict[str, str], known: frozenset[str]) -> None:
        self.names = names
        self.known = known

    def raw(self, node: Any) -> str:
        mapped = _map_links(node, lambda name: self.names.get(name, name))
        return "raw(" + _raw_text(mapped) + ")"

    # -- blocks ------------------------------------------------------------

    def block(self, node: Any, locs: frozenset[str], depth: int, tail: bool = True) -> list[str]:
        if _tup(node) and len(node) > 1 and node[0] == "seq":
            items = node[1:]
            lines: list[str] = []

            for index, item in enumerate(items):
                lines += self.statement(item, locs, depth, tail and index == len(items) - 1)

            return lines

        return self.statement(node, locs, depth, tail)

    def statement(self, node: Any, locs: frozenset[str], depth: int, tail: bool) -> list[str]:
        pad = "    " * depth

        try:
            if _tup(node) and node and isinstance(node[0], str):
                op, rest = node[0], node[1:]

                if op == "seq" and len(rest) > 0:
                    return self.block(node, locs, depth, tail)

                if op == "let" and len(rest) == 3 and tail:
                    name = rest[0]

                    if not isinstance(name, str) or not name or name in self.known:
                        raise _NoSyntax

                    value = self.let_value(rest[1], locs)
                    return [
                        f"{pad}let {_name(name)} = {value}",
                        *self.block(rest[2], locs | {name}, depth, True),
                    ]

                if op == "if" and len(rest) == 3:
                    condition = self.operand(rest[0], locs, 0, False, 0)
                    return [
                        f"{pad}if {condition}:",
                        *self.block(rest[1], locs, depth + 1, True),
                        f"{pad}else:",
                        *self.block(rest[2], locs, depth + 1, True),
                    ]

                if op == "write" and len(rest) == 2:
                    target = self.link(rest[0], 0)

                    if target in locs:
                        raise _NoSyntax

                    value = self.operand(rest[1], locs, 0, False, 0)
                    return [f"{pad}{_name(target)} = {value}"]

            return [pad + self.expr(node, locs)[0]]
        except _NoSyntax:
            return [pad + self.raw(node)]

    def let_value(self, node: Any, locs: frozenset[str]) -> str:
        """The value of a let: an expression, or a cell write."""

        if _tup(node) and len(node) == 3 and node[0] == "write":
            try:
                target = self.link(node[1], 0)

                if target not in locs:
                    return f"{_name(target)} = {self.operand(node[2], locs, 0, False, 0)}"
            except _NoSyntax:
                pass

        return self.operand(node, locs, 0, False, 0)

    # -- expressions -------------------------------------------------------

    def expr(self, node: Any, locs: frozenset[str], mode: int = 0, strict: bool = False) -> tuple[str, int]:
        try:
            return self._expr(node, locs, mode, strict)
        except _NoSyntax:
            if strict:
                raise

            return self.raw(node), 4

    def operand(self, node: Any, locs: frozenset[str], mode: int, strict: bool, need: int) -> str:
        text, prec = self.expr(node, locs, mode, strict)
        return text if prec >= need else "(" + text + ")"

    def link(self, link: Any, mode: int) -> str:
        """The global name for a link name: the current target entity's name
        in code; in a template the link name itself, which the code built
        from the template resolves through its own function's links.
        """

        if not isinstance(link, str):
            raise _NoSyntax

        target = self.names.get(link) if mode == 0 else (link if link in self.known else None)

        if target is None:
            raise _NoSyntax

        return target

    def _expr(self, node: Any, locs: frozenset[str], mode: int, strict: bool) -> tuple[str, int]:
        if not _tup(node) or not node or not isinstance(node[0], str):
            raise _NoSyntax

        op, rest = node[0], node[1:]

        if op in _ARITY and len(rest) != _ARITY[op]:
            raise _NoSyntax

        def operand(child: Any, need: int = 0) -> str:
            return self.operand(child, locs, mode, strict, need)

        if op == "lit":
            return self.literal(rest[0], locs, mode), 4

        if op == "arg":
            name = rest[0]

            if not isinstance(name, str) or not name or name in self.known:
                raise _NoSyntax

            if mode == 0 and name not in locs:
                raise _NoSyntax

            return _name(name), 4

        if op in _INFIX:
            symbol, prec, left, right = _INFIX[op]
            return f"{operand(rest[0], left)} {symbol} {operand(rest[1], right)}", prec

        if op == "if":
            return f"{operand(rest[1], 1)} if {operand(rest[0], 1)} else {operand(rest[2])}", 0

        if op in ("call", "read", "ref", "code", "linksof"):
            if not rest:
                raise _NoSyntax

            name = self.link(rest[0], mode)

            if mode == 0 and name in locs:
                raise _NoSyntax

            if op == "read":
                return _name(name), 4

            if op == "call":
                return f"{_name(name)}({', '.join(operand(arg) for arg in rest[1:])})", 4

            return f"{op}({_name(name)})", 4

        if op == "apply":
            head = rest[0] if rest else None

            if not (_tup(head) and len(head) == 2 and head[0] == "arg" and isinstance(head[1], str)):
                raise _NoSyntax

            name = head[1]

            if not name or name in self.known or (mode == 0 and name not in locs):
                raise _NoSyntax

            return f"{_name(name)}({', '.join(operand(arg) for arg in rest[1:])})", 4

        if op == "applyv":
            return f"apply({operand(rest[0])}, {operand(rest[1])})", 4

        if op == "tuple":
            items = [operand(item) for item in rest]

            if len(items) == 1:
                return f"({items[0]},)", 4

            return "(" + ", ".join(items) + ")", 4

        if op in _PLAIN:
            return f"{op}({', '.join(operand(arg) for arg in rest)})", 4

        if op == "quote":
            if mode != 0:
                raise _NoSyntax

            return "quote(" + self.expr(rest[0], locs, 1, True)[0] + ")", 4

        if op == "unquote":
            if mode != 1 or len(rest) != 1:
                raise _NoSyntax

            return "unquote(" + self.expr(rest[0], locs, 0, False)[0] + ")", 4

        if op == "function":
            if mode == 0:
                text = self.fn_form(rest, locs)

                if text is not None:
                    return text, 0

            return f"function({operand(rest[0])}, {operand(rest[1])})", 4

        if op == "label":
            if len(rest) != 2 or not isinstance(rest[0], str) or not rest[0]:
                raise _NoSyntax

            return f"label({_name(rest[0])}, {operand(rest[1])})", 4

        if op == "activate":
            if not rest or len(rest) % 2:
                raise _NoSyntax

            return "activate(" + ", ".join(self.pairs(rest, locs, mode, strict)) + ")", 4

        if op == "trial":
            call = rest[0] if rest else None

            if not (_tup(call) and len(call) >= 2 and call[0] == "call") or len(rest) % 2 == 0:
                raise _NoSyntax

            name = self.link(call[1], mode)

            if mode == 0 and name in locs:
                raise _NoSyntax

            head = f"{_name(name)}({', '.join(operand(arg) for arg in call[2:])})"
            return "trial(" + ", ".join([head, *self.pairs(rest[1:], locs, mode, strict)]) + ")", 4

        raise _NoSyntax

    def pairs(self, items: tuple, locs: frozenset[str], mode: int, strict: bool) -> list[str]:
        """``TARGET = VALUE`` texts for the interleaved targets and values."""

        if len(items) % 2:
            raise _NoSyntax

        texts = []

        for target, value in zip(items[0::2], items[1::2]):
            if _tup(target) and len(target) == 2 and isinstance(target[1], str) and target[1]:
                name, suffix = self.link(target[0], mode), "." + _name(target[1])
            else:
                name, suffix = self.link(target, mode), ""

            if mode == 0 and name in locs:
                raise _NoSyntax

            texts.append(f"{_name(name)}{suffix} = {self.operand(value, locs, mode, strict, 0)}")

        return texts

    def literal(self, value: Any, locs: frozenset[str], mode: int) -> str:
        if mode == 0:
            if _scalar(value):
                return _data_text(value)

            if _tup(value):
                # Code as data reads as a quote; anything else as a tuple.
                try:
                    return "quote(" + self.expr(value, locs, 2, True)[0] + ")"
                except _NoSyntax:
                    return _data_text(value)

            raise _NoSyntax

        if _scalar(value):
            return _data_text(value)

        if mode == 1 and _tup(value) and len(value) == 2 and value[0] == "unquote":
            return "literal(" + self.expr(value[1], locs, 0, False)[0] + ")"

        raise _NoSyntax

    def fn_form(self, rest: tuple, locs: frozenset[str]) -> str | None:
        """``fn(params): body`` for a function value with a literal body."""

        params, body = rest

        if not (
            _tup(params)
            and len(params) == 2
            and params[0] == "lit"
            and _tup(params[1])
            and all(isinstance(name, str) and name for name in params[1])
            and len(set(params[1])) == len(params[1])
            and not any(name in self.known for name in params[1])
        ):
            return None

        if _tup(body) and len(body) == 2 and body[0] == "quote":
            mode, template = 1, body[1]
        elif _tup(body) and len(body) == 2 and body[0] == "lit" and _tup(body[1]):
            mode, template = 2, body[1]
        else:
            return None

        try:
            text = self.expr(template, locs, mode, True)[0]
        except _NoSyntax:
            return None

        return "fn(" + ", ".join(_name(name) for name in params[1]) + "): " + text


def _global_names(state: State) -> frozenset[str]:
    return frozenset(
        entity.value
        for entity, value in state.values.items()
        if _definition_of(value) is not None or cell_declaration(value) is not None
    )


def _render(state: State, function: EntityID, known: frozenset[str]) -> str:
    value = state.values.get(function)
    definition = None if value is None else _definition_of(value)
    code = function_at(state, function)

    if definition is None or code is None:
        raise ValueError(f"{function.value} is not a function of the state")

    names = {
        link: target.value
        for link, target in definition.links.items()
        if isinstance(target, EntityID)
    }
    renderer = _Renderer(names, known | frozenset(names.values()))
    params = ", ".join(_name(param) for param in code.params)
    lines = [
        f"fn {_name(function.value)}({params}):",
        *renderer.block(code.body, frozenset(code.params), 1),
    ]
    return "\n".join(lines) + "\n"


def render(state: State, function: EntityID) -> str:
    """Print one function of a graph-form state as an ``fn`` declaration.

    Names are the current target entity names, so a rename shows in the
    text of the callers. Anything the syntax cannot express prints as
    ``raw(...)``.
    """

    return _render(state, function, _global_names(state))


def _cell_text(entity: EntityID, declaration: CellDeclaration) -> str:
    name = _name(entity.value)
    constraint = declaration.constraint

    try:
        if isinstance(constraint, IntRange):
            low = "" if constraint.min is None else str(constraint.min)
            high = "" if constraint.max is None else str(constraint.max)
            kind = f"int in {low}..{high}"
        elif isinstance(constraint, IsKind) and constraint.kind == "int":
            kind = "int"
        elif isinstance(constraint, IsKind) and constraint.kind in _TYPE_KINDS.values():
            kind = next(text for text, k in _TYPE_KINDS.items() if k == constraint.kind)
        else:
            raise _NoSyntax

        return f"cell {name}: {kind} = {_data_text(_decode(declaration.initial))}"
    except _NoSyntax:
        return f"# cell {name}: not expressible in the syntax"


def render_program(state: State) -> str:
    """Print every cell, then every function, of a graph-form state.

    Cells come first, then functions in ``EntityID`` order, separated by
    one blank line.
    """

    known = _global_names(state)
    cells: list[str] = []
    parts: list[str] = []

    for entity in sorted(state.values):
        value = state.values[entity]
        declaration = cell_declaration(value)

        if declaration is not None:
            cells.append(_cell_text(entity, declaration))
        elif _definition_of(value) is not None:
            parts.append(_render(state, entity, known))

    if cells:
        parts.insert(0, "\n".join(cells) + "\n")

    return "\n".join(parts)
