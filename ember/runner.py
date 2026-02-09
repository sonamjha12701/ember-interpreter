"""File execution mode for the Ember interpreter.

Reads an ``.ember`` source file, tokenizes, parses, and interprets it,
printing formatted errors with source context when something goes wrong.
"""

from __future__ import annotations

import sys
from typing import Optional

from ember.errors import EmberError
from ember.interpreter import Interpreter
from ember.lexer import Lexer
from ember.parser import Parser


def run_source(
    source: str,
    interpreter: Optional[Interpreter] = None,
) -> None:
    """Lex, parse, and execute *source* code."""
    if interpreter is None:
        interpreter = Interpreter()

    tokens = Lexer().tokenize(source)
    program = Parser().parse(tokens)
    interpreter.execute(program)


def run_file(path: str) -> None:
    """Read and execute an Ember source file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        run_source(source)
    except EmberError as err:
        _print_error(err, source)
        sys.exit(1)


def _print_error(err: EmberError, source: str) -> None:
    """Print a formatted error with the offending source line."""
    lines = source.splitlines()
    print(err.format(), file=sys.stderr)
    if 1 <= err.line <= len(lines):
        line_text = lines[err.line - 1]
        print(f"  {err.line} | {line_text}", file=sys.stderr)
        # Point to the column
        padding = len(str(err.line)) + 3 + max(0, err.column - 1)
        print(" " * padding + "^", file=sys.stderr)
