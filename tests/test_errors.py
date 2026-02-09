"""Tests for Ember error reporting — verifying line/column info and messages."""

from __future__ import annotations

import pytest

from ember.errors import EmberError, EmberRuntimeError, EmberSyntaxError, EmberTypeError
from ember.lexer import Lexer
from ember.parser import Parser
from tests.conftest import run_ember


class TestErrorFormatting:
    def test_syntax_error_format(self):
        err = EmberSyntaxError("bad token", 5, 10)
        assert err.format() == "[line 5, col 10] SyntaxError: bad token"

    def test_runtime_error_format(self):
        err = EmberRuntimeError("undefined var", 3, 1)
        assert err.format() == "[line 3, col 1] RuntimeError: undefined var"

    def test_type_error_format(self):
        err = EmberTypeError("expected number", 7, 4)
        assert err.format() == "[line 7, col 4] TypeError: expected number"

    def test_base_error_format(self):
        err = EmberError("generic", 1, 1)
        assert err.format() == "[line 1, col 1] Error: generic"


class TestLexerErrors:
    def test_unexpected_character_location(self):
        with pytest.raises(EmberSyntaxError) as exc_info:
            Lexer().tokenize("let x = @")
        err = exc_info.value
        assert err.line == 1

    def test_unterminated_string_location(self):
        with pytest.raises(EmberSyntaxError) as exc_info:
            Lexer().tokenize('"unterminated')
        err = exc_info.value
        assert "Unterminated" in err.message


class TestParserErrors:
    def test_missing_end_message(self):
        with pytest.raises(EmberSyntaxError) as exc_info:
            tokens = Lexer().tokenize("if true do\n  print(1)")
            Parser().parse(tokens)
        assert "end" in exc_info.value.message.lower()

    def test_missing_do_message(self):
        with pytest.raises(EmberSyntaxError) as exc_info:
            tokens = Lexer().tokenize("if true\n  print(1)\nend")
            Parser().parse(tokens)
        assert "do" in exc_info.value.message.lower()


class TestRuntimeErrors:
    def test_undefined_variable_message(self):
        with pytest.raises(EmberRuntimeError) as exc_info:
            run_ember("print(nonexistent)")
        assert "nonexistent" in exc_info.value.message

    def test_division_by_zero(self):
        with pytest.raises(EmberRuntimeError, match="Division by zero"):
            run_ember("let x = 1 / 0")

    def test_index_out_of_range(self):
        with pytest.raises(EmberRuntimeError, match="out of range"):
            run_ember("let arr = [1]\nprint(arr[5])")

    def test_cannot_call_non_function(self):
        with pytest.raises(EmberRuntimeError, match="Cannot call"):
            run_ember("let x = 5\nx()")


class TestTypeErrors:
    def test_add_string_and_number(self):
        with pytest.raises(EmberTypeError):
            run_ember('print("hello" + 5)')

    def test_negate_string(self):
        with pytest.raises(EmberTypeError):
            run_ember('print(-"hello")')

    def test_index_non_list(self):
        with pytest.raises(EmberTypeError):
            run_ember("let x = 5\nprint(x[0])")
