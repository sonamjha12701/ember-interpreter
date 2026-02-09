"""Interactive REPL (Read-Eval-Print Loop) for Ember.

Supports multi-line input for blocks: when a line ends with ``do``, the
REPL continues reading until a matching ``end`` is found.
"""

from __future__ import annotations

import sys

from ember.errors import EmberError
from ember.interpreter import Interpreter
from ember.lexer import Lexer
from ember.parser import Parser


def start_repl() -> None:
    """Start the Ember interactive REPL."""
    interpreter = Interpreter()
    lexer = Lexer()
    parser = Parser()

    print("Ember 1.0.0 — Interactive Shell")
    print('Type expressions or statements. Press Ctrl+D to exit.\n')

    while True:
        try:
            source = _read_input()
        except EOFError:
            print("\nGoodbye!")
            break
        except KeyboardInterrupt:
            print()
            continue

        if not source.strip():
            continue

        try:
            tokens = lexer.tokenize(source)
            program = parser.parse(tokens)
            interpreter.execute(program)
        except EmberError as err:
            print(err.format(), file=sys.stderr)


def _read_input() -> str:
    """Read a (possibly multi-line) input from the user.

    If the line contains an unmatched ``do``, keep reading until
    ``end`` balances it out.
    """
    line = input("ember> ")
    lines = [line]

    # Track nesting depth: each 'do' increments, each 'end' decrements.
    depth = _nesting_depth(line)
    while depth > 0:
        try:
            continuation = input("  ...> ")
        except EOFError:
            break
        lines.append(continuation)
        depth += _nesting_depth(continuation)

    return "\n".join(lines)


def _nesting_depth(line: str) -> int:
    """Return the net nesting change for a line of Ember code.

    Counts ``do`` as +1 and ``end`` as -1, ignoring occurrences
    inside strings or after ``#`` comments.
    """
    # Strip comments
    comment_pos = line.find("#")
    if comment_pos >= 0:
        line = line[:comment_pos]

    # Simple word-based scan (good enough for the REPL).
    words = line.split()
    depth = 0
    for word in words:
        if word == "do":
            depth += 1
        elif word == "end":
            depth -= 1
    return depth
