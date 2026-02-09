"""Token types and Token dataclass for the Ember lexer.

Defines every token the lexer can produce, along with the keyword
lookup table used during identifier classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    """All token types recognized by the Ember lexer."""

    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()

    # Keywords
    LET = auto()
    FN = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    DO = auto()
    END = auto()
    RETURN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()

    # Special
    NEWLINE = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    """An immutable token produced by the lexer."""

    type: TokenType
    lexeme: str
    literal: Any
    line: int
    column: int

    def __repr__(self) -> str:
        if self.literal is not None:
            return f"Token({self.type.name}, {self.lexeme!r}, {self.literal!r})"
        return f"Token({self.type.name}, {self.lexeme!r})"


KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "fn": TokenType.FN,
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "do": TokenType.DO,
    "end": TokenType.END,
    "return": TokenType.RETURN,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "nil": TokenType.NIL,
}
