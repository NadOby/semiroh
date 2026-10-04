"""Text syntax, version 0 (docs/syntax.md): a source view of programs.

``parse`` reads program text into the input format (first_program.md), which
``shear.lang.load`` turns into graph form; ``render`` and
``render_program`` print graph form back as text. The graph stays
authoritative and text is a projection: parsing edited text creates new
nodes (version 0 is import-only).

This module is a layer on top of ``shear.lang``, not part of the core
model, and is not re-exported from ``shear/__init__.py``.

The package splits into ``lexer`` (tokens), ``parser`` (text to the input
format), ``printer`` (graph form to text) and ``forms`` (input-form helpers
both sides use).
"""

from .lexer import SourceError, tokenize
from .parser import parse
from .printer import render, render_program

__all__ = ["SourceError", "parse", "render", "render_program"]
