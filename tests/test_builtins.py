"""Tests for Ember built-in functions."""

from __future__ import annotations

import pytest

from ember.errors import EmberRuntimeError, EmberTypeError
from tests.conftest import run_ember


class TestPrint:
    def test_single_value(self):
        assert run_ember("print(42)") == ["42"]

    def test_multiple_values(self):
        assert run_ember('print("x =", 10)') == ["x = 10"]

    def test_no_args(self):
        assert run_ember("print()") == [""]


class TestLen:
    def test_string_length(self):
        assert run_ember('print(len("hello"))') == ["5"]

    def test_list_length(self):
        assert run_ember("print(len([1, 2, 3]))") == ["3"]

    def test_empty_list(self):
        assert run_ember("print(len([]))") == ["0"]

    def test_wrong_type(self):
        with pytest.raises(EmberRuntimeError, match="len\\(\\)"):
            run_ember("len(42)")


class TestAppend:
    def test_append_to_list(self):
        source = """
let arr = [1, 2]
append(arr, 3)
print(arr)
"""
        assert run_ember(source) == ["[1, 2, 3]"]

    def test_append_non_list(self):
        with pytest.raises(EmberRuntimeError, match="append\\(\\)"):
            run_ember('append("hello", 1)')


class TestType:
    def test_number(self):
        assert run_ember("print(type(42))") == ["number"]

    def test_string(self):
        assert run_ember('print(type("hi"))') == ["string"]

    def test_bool(self):
        assert run_ember("print(type(true))") == ["bool"]

    def test_nil(self):
        assert run_ember("print(type(nil))") == ["nil"]

    def test_list(self):
        assert run_ember("print(type([1]))") == ["list"]

    def test_function(self):
        source = """
fn f() do
    return 1
end
print(type(f))
"""
        assert run_ember(source) == ["function"]

    def test_builtin(self):
        assert run_ember("print(type(print))") == ["function"]


class TestStr:
    def test_number_to_string(self):
        assert run_ember("print(str(42))") == ["42"]

    def test_bool_to_string(self):
        assert run_ember("print(str(true))") == ["true"]

    def test_nil_to_string(self):
        assert run_ember("print(str(nil))") == ["nil"]


class TestNum:
    def test_string_to_number(self):
        assert run_ember('print(num("42") + 1)') == ["43"]

    def test_invalid_conversion(self):
        with pytest.raises(EmberRuntimeError, match="num\\(\\)"):
            run_ember('num("hello")')


class TestArity:
    def test_len_wrong_arity(self):
        with pytest.raises(EmberRuntimeError, match="expects 1 argument"):
            run_ember("len(1, 2)")

    def test_append_wrong_arity(self):
        with pytest.raises(EmberRuntimeError, match="expects 2 argument"):
            run_ember("append([1])")
