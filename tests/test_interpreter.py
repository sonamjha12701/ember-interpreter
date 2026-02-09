"""Tests for the Ember interpreter (tree-walking evaluator)."""

from __future__ import annotations

import pytest

from ember.errors import EmberRuntimeError, EmberTypeError
from tests.conftest import run_ember


class TestArithmetic:
    def test_addition(self):
        assert run_ember("print(1 + 2)") == ["3"]

    def test_subtraction(self):
        assert run_ember("print(10 - 3)") == ["7"]

    def test_multiplication(self):
        assert run_ember("print(4 * 5)") == ["20"]

    def test_division(self):
        assert run_ember("print(10 / 4)") == ["2.5"]

    def test_modulo(self):
        assert run_ember("print(17 % 5)") == ["2"]

    def test_precedence(self):
        assert run_ember("print(2 + 3 * 4)") == ["14"]

    def test_grouped(self):
        assert run_ember("print((2 + 3) * 4)") == ["20"]

    def test_negation(self):
        assert run_ember("print(-5)") == ["-5"]

    def test_division_by_zero(self):
        with pytest.raises(EmberRuntimeError, match="Division by zero"):
            run_ember("print(1 / 0)")

    def test_modulo_by_zero(self):
        with pytest.raises(EmberRuntimeError, match="Modulo by zero"):
            run_ember("print(1 % 0)")


class TestStrings:
    def test_concatenation(self):
        assert run_ember('print("hello" + " " + "world")') == ["hello world"]

    def test_string_type_error(self):
        with pytest.raises(EmberTypeError):
            run_ember('print("hello" + 5)')


class TestComparisons:
    def test_equal(self):
        assert run_ember("print(1 == 1)") == ["true"]
        assert run_ember("print(1 == 2)") == ["false"]

    def test_not_equal(self):
        assert run_ember("print(1 != 2)") == ["true"]

    def test_less(self):
        assert run_ember("print(1 < 2)") == ["true"]
        assert run_ember("print(2 < 1)") == ["false"]

    def test_greater(self):
        assert run_ember("print(2 > 1)") == ["true"]

    def test_less_equal(self):
        assert run_ember("print(1 <= 1)") == ["true"]
        assert run_ember("print(2 <= 1)") == ["false"]

    def test_greater_equal(self):
        assert run_ember("print(1 >= 1)") == ["true"]

    def test_nil_equality(self):
        assert run_ember("print(nil == nil)") == ["true"]
        assert run_ember("print(nil == 0)") == ["false"]

    def test_string_equality(self):
        assert run_ember('print("a" == "a")') == ["true"]
        assert run_ember('print("a" == "b")') == ["false"]


class TestLogicalOperators:
    def test_and(self):
        assert run_ember("print(true and true)") == ["true"]
        assert run_ember("print(true and false)") == ["false"]

    def test_or(self):
        assert run_ember("print(false or true)") == ["true"]
        assert run_ember("print(false or false)") == ["false"]

    def test_not(self):
        assert run_ember("print(not true)") == ["false"]
        assert run_ember("print(not false)") == ["true"]

    def test_short_circuit_and(self):
        # Should not evaluate the second operand
        assert run_ember("print(false and 1/0)") == ["false"]

    def test_short_circuit_or(self):
        assert run_ember("print(true or 1/0)") == ["true"]


class TestVariables:
    def test_define_and_use(self):
        assert run_ember("let x = 10\nprint(x)") == ["10"]

    def test_reassign(self):
        assert run_ember("let x = 1\nlet x = 2\nprint(x)") == ["2"]

    def test_undefined_variable(self):
        with pytest.raises(EmberRuntimeError, match="Undefined variable"):
            run_ember("print(x)")


class TestIfStatements:
    def test_true_branch(self):
        source = 'if true do\n  print("yes")\nend'
        assert run_ember(source) == ["yes"]

    def test_false_branch(self):
        source = 'if false do\n  print("yes")\nelse do\n  print("no")\nend'
        assert run_ember(source) == ["no"]

    def test_elif(self):
        source = """
let x = 2
if x == 1 do
    print("one")
elif x == 2 do
    print("two")
else do
    print("other")
end
"""
        assert run_ember(source) == ["two"]


class TestWhileLoops:
    def test_basic_loop(self):
        source = """
let i = 0
while i < 3 do
    print(i)
    let i = i + 1
end
"""
        assert run_ember(source) == ["0", "1", "2"]

    def test_loop_does_not_execute(self):
        source = """
while false do
    print("nope")
end
print("done")
"""
        assert run_ember(source) == ["done"]


class TestFunctions:
    def test_basic_function(self):
        source = """
fn greet(name) do
    print("Hello, " + name + "!")
end
greet("World")
"""
        assert run_ember(source) == ["Hello, World!"]

    def test_return_value(self):
        source = """
fn add(a, b) do
    return a + b
end
print(add(3, 4))
"""
        assert run_ember(source) == ["7"]

    def test_recursion(self):
        source = """
fn fact(n) do
    if n <= 1 do
        return 1
    end
    return n * fact(n - 1)
end
print(fact(5))
"""
        assert run_ember(source) == ["120"]

    def test_wrong_arity(self):
        source = """
fn f(a, b) do
    return a + b
end
f(1)
"""
        with pytest.raises(EmberRuntimeError, match="expects 2 argument"):
            run_ember(source)

    def test_calling_non_function(self):
        with pytest.raises(EmberRuntimeError, match="Cannot call"):
            run_ember("let x = 5\nx()")


class TestClosures:
    def test_closure_captures_env(self):
        source = """
fn make_adder(x) do
    fn adder(y) do
        return x + y
    end
    return adder
end
let add5 = make_adder(5)
print(add5(3))
"""
        assert run_ember(source) == ["8"]

    def test_counter_closure(self):
        source = """
fn make_counter() do
    let count = 0
    fn next() do
        let count = count + 1
        return count
    end
    return next
end
let c = make_counter()
print(c())
print(c())
print(c())
"""
        assert run_ember(source) == ["1", "2", "3"]


class TestLists:
    def test_create_and_index(self):
        source = """
let arr = [10, 20, 30]
print(arr[0])
print(arr[2])
"""
        assert run_ember(source) == ["10", "30"]

    def test_index_assignment(self):
        source = """
let arr = [1, 2, 3]
let arr[1] = 99
print(arr)
"""
        assert run_ember(source) == ["[1, 99, 3]"]

    def test_index_out_of_range(self):
        with pytest.raises(EmberRuntimeError, match="out of range"):
            run_ember("let arr = [1, 2]\nprint(arr[5])")

    def test_nested_list(self):
        source = """
let m = [[1, 2], [3, 4]]
print(m[0])
print(m[1][1])
"""
        assert run_ember(source) == ["[1, 2]", "4"]


class TestNil:
    def test_nil_value(self):
        assert run_ember("print(nil)") == ["nil"]

    def test_nil_is_falsy(self):
        source = """
if not nil do
    print("nil is falsy")
end
"""
        assert run_ember(source) == ["nil is falsy"]


class TestBooleans:
    def test_bool_display(self):
        assert run_ember("print(true)") == ["true"]
        assert run_ember("print(false)") == ["false"]
