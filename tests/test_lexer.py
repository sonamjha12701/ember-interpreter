"""Tests for the Ember lexer (tokenizer)."""

from __future__ import annotations

import pytest

from ember.errors import EmberSyntaxError
from ember.lexer import Lexer
from ember.tokens import TokenType


@pytest.fixture
def lex():
    """Helper that returns just the non-NEWLINE, non-EOF tokens."""
    lexer = Lexer()

    def _lex(source: str):
        tokens = lexer.tokenize(source)
        return [t for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]

    return _lex


class TestNumbers:
    def test_integer(self, lex):
        tokens = lex("42")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].literal == 42.0

    def test_float(self, lex):
        tokens = lex("3.14")
        assert len(tokens) == 1
        assert tokens[0].literal == 3.14

    def test_multiple_numbers(self, lex):
        tokens = lex("1 2 3")
        assert len(tokens) == 3
        assert all(t.type == TokenType.NUMBER for t in tokens)


class TestStrings:
    def test_simple_string(self, lex):
        tokens = lex('"hello"')
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].literal == "hello"

    def test_escape_sequences(self, lex):
        tokens = lex(r'"line\none"')
        assert tokens[0].literal == "line\none"

    def test_escaped_quote(self, lex):
        tokens = lex(r'"say \"hi\""')
        assert tokens[0].literal == 'say "hi"'

    def test_unterminated_string(self):
        lexer = Lexer()
        with pytest.raises(EmberSyntaxError, match="Unterminated string"):
            lexer.tokenize('"hello')


class TestOperators:
    def test_single_char_operators(self, lex):
        tokens = lex("+ - * / % = < >")
        types = [t.type for t in tokens]
        assert types == [
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
            TokenType.SLASH, TokenType.PERCENT, TokenType.EQUAL,
            TokenType.LESS, TokenType.GREATER,
        ]

    def test_two_char_operators(self, lex):
        tokens = lex("== != <= >=")
        types = [t.type for t in tokens]
        assert types == [
            TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL,
            TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL,
        ]

    def test_delimiters(self, lex):
        tokens = lex("( ) [ ] ,")
        types = [t.type for t in tokens]
        assert types == [
            TokenType.LPAREN, TokenType.RPAREN,
            TokenType.LBRACKET, TokenType.RBRACKET,
            TokenType.COMMA,
        ]


class TestKeywords:
    def test_all_keywords(self, lex):
        tokens = lex("let fn if elif else while do end return and or not true false nil")
        types = [t.type for t in tokens]
        assert types == [
            TokenType.LET, TokenType.FN, TokenType.IF,
            TokenType.ELIF, TokenType.ELSE, TokenType.WHILE,
            TokenType.DO, TokenType.END, TokenType.RETURN,
            TokenType.AND, TokenType.OR, TokenType.NOT,
            TokenType.TRUE, TokenType.FALSE, TokenType.NIL,
        ]

    def test_true_false_literals(self, lex):
        tokens = lex("true false")
        assert tokens[0].literal is True
        assert tokens[1].literal is False


class TestIdentifiers:
    def test_simple(self, lex):
        tokens = lex("foo bar")
        assert all(t.type == TokenType.IDENTIFIER for t in tokens)
        assert tokens[0].lexeme == "foo"

    def test_with_underscores(self, lex):
        tokens = lex("my_var _private")
        assert all(t.type == TokenType.IDENTIFIER for t in tokens)

    def test_with_numbers(self, lex):
        tokens = lex("var1 item2")
        assert all(t.type == TokenType.IDENTIFIER for t in tokens)


class TestNewlinesAndComments:
    def test_newlines_collapse(self):
        lexer = Lexer()
        tokens = lexer.tokenize("a\n\n\nb")
        newlines = [t for t in tokens if t.type == TokenType.NEWLINE]
        # One collapsed newline between 'a' and 'b', plus trailing newline before EOF
        assert len(newlines) == 2

    def test_consecutive_newlines_between_tokens(self):
        lexer = Lexer()
        # The three newlines between a and b should collapse to exactly one
        tokens = lexer.tokenize("a\n\n\nb")
        types = [t.type for t in tokens]
        assert types == [
            TokenType.IDENTIFIER, TokenType.NEWLINE,
            TokenType.IDENTIFIER, TokenType.NEWLINE,
            TokenType.EOF,
        ]

    def test_comments_ignored(self, lex):
        tokens = lex("x # this is a comment")
        assert len(tokens) == 1
        assert tokens[0].lexeme == "x"

    def test_comment_only_line(self, lex):
        tokens = lex("# just a comment")
        assert len(tokens) == 0


class TestErrors:
    def test_unexpected_character(self):
        lexer = Lexer()
        with pytest.raises(EmberSyntaxError, match="Unexpected character"):
            lexer.tokenize("@")

    def test_line_tracking(self):
        lexer = Lexer()
        tokens = lexer.tokenize("a\nb\nc")
        # Find 'c' token
        c_tok = [t for t in tokens if t.lexeme == "c"][0]
        assert c_tok.line == 3
