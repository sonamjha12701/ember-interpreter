"""Lexer (tokenizer) for the Ember programming language.

Performs a single-pass scan over source text, producing a list of tokens.
Tracks line and column numbers for error reporting.
"""

from __future__ import annotations

from ember.errors import EmberSyntaxError
from ember.tokens import KEYWORDS, Token, TokenType


class Lexer:
    """Converts Ember source code into a sequence of tokens."""

    def __init__(self) -> None:
        self._source: str = ""
        self._tokens: list[Token] = []
        self._pos: int = 0
        self._line: int = 1
        self._column: int = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tokenize(self, source: str) -> list[Token]:
        """Tokenize *source* and return the token list (ending with EOF)."""
        self._source = source
        self._tokens = []
        self._pos = 0
        self._line = 1
        self._column = 1

        while not self._at_end():
            self._scan_token()

        # Ensure the stream ends with a NEWLINE before EOF so the parser
        # can always expect newline-terminated statements.
        if self._tokens and self._tokens[-1].type not in (
            TokenType.NEWLINE,
            TokenType.EOF,
        ):
            self._tokens.append(
                Token(TokenType.NEWLINE, "\\n", None, self._line, self._column)
            )

        self._tokens.append(
            Token(TokenType.EOF, "", None, self._line, self._column)
        )
        return self._tokens

    # ------------------------------------------------------------------
    # Scanning helpers
    # ------------------------------------------------------------------

    def _scan_token(self) -> None:
        ch = self._advance()

        # Whitespace (not newlines)
        if ch in (" ", "\t", "\r"):
            return

        # Newlines — collapse consecutive newlines into one token.
        if ch == "\n":
            self._emit_newline()
            return

        # Comments
        if ch == "#":
            while not self._at_end() and self._peek() != "\n":
                self._advance()
            return

        # Strings
        if ch == '"':
            self._read_string()
            return

        # Numbers
        if ch.isdigit():
            self._read_number(ch)
            return

        # Identifiers and keywords
        if ch.isalpha() or ch == "_":
            self._read_identifier(ch)
            return

        # Two-character operators
        if ch == "=" and self._match("="):
            self._add_token(TokenType.EQUAL_EQUAL, "==")
            return
        if ch == "!" and self._match("="):
            self._add_token(TokenType.BANG_EQUAL, "!=")
            return
        if ch == "<" and self._match("="):
            self._add_token(TokenType.LESS_EQUAL, "<=")
            return
        if ch == ">" and self._match("="):
            self._add_token(TokenType.GREATER_EQUAL, ">=")
            return

        # Single-character tokens
        single: dict[str, TokenType] = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "=": TokenType.EQUAL,
            "<": TokenType.LESS,
            ">": TokenType.GREATER,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ",": TokenType.COMMA,
        }

        if ch in single:
            self._add_token(single[ch], ch)
            return

        raise EmberSyntaxError(
            f"Unexpected character '{ch}'", self._line, self._column - 1
        )

    # ------------------------------------------------------------------
    # Character-level helpers
    # ------------------------------------------------------------------

    def _at_end(self) -> bool:
        return self._pos >= len(self._source)

    def _advance(self) -> str:
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return ch

    def _peek(self) -> str:
        if self._at_end():
            return "\0"
        return self._source[self._pos]

    def _peek_next(self) -> str:
        if self._pos + 1 >= len(self._source):
            return "\0"
        return self._source[self._pos + 1]

    def _match(self, expected: str) -> bool:
        if self._at_end() or self._source[self._pos] != expected:
            return False
        self._advance()
        return True

    # ------------------------------------------------------------------
    # Token construction
    # ------------------------------------------------------------------

    def _add_token(
        self,
        token_type: TokenType,
        lexeme: str,
        literal: object = None,
    ) -> None:
        col = self._column - len(lexeme)
        self._tokens.append(Token(token_type, lexeme, literal, self._line, col))

    def _emit_newline(self) -> None:
        # Collapse consecutive newlines into a single NEWLINE token.
        if not self._tokens or self._tokens[-1].type == TokenType.NEWLINE:
            return
        self._tokens.append(
            Token(TokenType.NEWLINE, "\\n", None, self._line - 1, self._column)
        )

    # ------------------------------------------------------------------
    # Multi-character token readers
    # ------------------------------------------------------------------

    def _read_string(self) -> None:
        start_line = self._line
        start_col = self._column - 1  # The opening quote
        value: list[str] = []

        while not self._at_end() and self._peek() != '"':
            ch = self._advance()
            if ch == "\n":
                # Allow multi-line strings.
                value.append("\n")
                continue
            if ch == "\\":
                esc = self._advance() if not self._at_end() else ""
                escape_map = {"n": "\n", "t": "\t", "\\": "\\", '"': '"'}
                if esc in escape_map:
                    value.append(escape_map[esc])
                else:
                    value.append("\\" + esc)
                continue
            value.append(ch)

        if self._at_end():
            raise EmberSyntaxError(
                "Unterminated string", start_line, start_col
            )

        self._advance()  # Consume closing "
        text = "".join(value)
        lexeme = '"' + text + '"'
        self._add_token(TokenType.STRING, lexeme, text)

    def _read_number(self, first: str) -> None:
        start_col = self._column - 1
        chars = [first]

        while not self._at_end() and self._peek().isdigit():
            chars.append(self._advance())

        # Fractional part
        if not self._at_end() and self._peek() == "." and self._peek_next().isdigit():
            chars.append(self._advance())  # The '.'
            while not self._at_end() and self._peek().isdigit():
                chars.append(self._advance())

        lexeme = "".join(chars)
        value = float(lexeme)
        # Store as int if there's no fractional part for cleaner display.
        if value == int(value) and "." not in lexeme:
            value = float(int(value))
        self._tokens.append(
            Token(TokenType.NUMBER, lexeme, value, self._line, start_col)
        )

    def _read_identifier(self, first: str) -> None:
        chars = [first]
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            chars.append(self._advance())

        lexeme = "".join(chars)
        token_type = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)

        literal = None
        if token_type == TokenType.TRUE:
            literal = True
        elif token_type == TokenType.FALSE:
            literal = False

        self._add_token(token_type, lexeme, literal)
