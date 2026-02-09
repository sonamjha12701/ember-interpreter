"""Error types for the Ember language interpreter.

All errors carry source location information (line and column) for
clear, actionable error messages.
"""

from __future__ import annotations


class EmberError(Exception):
    """Base class for all Ember language errors."""

    def __init__(self, message: str, line: int, column: int) -> None:
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.format())

    def format(self) -> str:
        return f"[line {self.line}, col {self.column}] Error: {self.message}"


class EmberSyntaxError(EmberError):
    """Raised for lexer and parser errors (malformed source code)."""

    def format(self) -> str:
        return f"[line {self.line}, col {self.column}] SyntaxError: {self.message}"


class EmberRuntimeError(EmberError):
    """Raised for errors during program execution."""

    def format(self) -> str:
        return f"[line {self.line}, col {self.column}] RuntimeError: {self.message}"


class EmberTypeError(EmberError):
    """Raised for type mismatch errors during execution."""

    def format(self) -> str:
        return f"[line {self.line}, col {self.column}] TypeError: {self.message}"
