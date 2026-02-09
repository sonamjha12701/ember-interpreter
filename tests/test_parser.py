"""Tests for the Ember parser."""

from __future__ import annotations

import pytest

from ember.ast_nodes import (
    BinaryOp,
    BoolLiteral,
    ExpressionStatement,
    FunctionCall,
    FunctionDef,
    Identifier,
    IfStatement,
    IndexAccess,
    LetStatement,
    ListLiteral,
    NilLiteral,
    NumberLiteral,
    Program,
    ReturnStatement,
    StringLiteral,
    UnaryOp,
    WhileStatement,
)
from ember.errors import EmberSyntaxError
from ember.lexer import Lexer
from ember.parser import Parser


def parse(source: str) -> Program:
    tokens = Lexer().tokenize(source)
    return Parser().parse(tokens)


def parse_expr(source: str):
    """Parse a single expression and return the expression node."""
    program = parse(source)
    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, ExpressionStatement)
    return stmt.expression


class TestLiterals:
    def test_number(self):
        expr = parse_expr("42")
        assert isinstance(expr, NumberLiteral)
        assert expr.value == 42.0

    def test_string(self):
        expr = parse_expr('"hello"')
        assert isinstance(expr, StringLiteral)
        assert expr.value == "hello"

    def test_true(self):
        expr = parse_expr("true")
        assert isinstance(expr, BoolLiteral)
        assert expr.value is True

    def test_false(self):
        expr = parse_expr("false")
        assert isinstance(expr, BoolLiteral)
        assert expr.value is False

    def test_nil(self):
        expr = parse_expr("nil")
        assert isinstance(expr, NilLiteral)

    def test_list(self):
        expr = parse_expr("[1, 2, 3]")
        assert isinstance(expr, ListLiteral)
        assert len(expr.elements) == 3


class TestOperatorPrecedence:
    def test_addition_and_multiplication(self):
        # 1 + 2 * 3 should parse as 1 + (2 * 3)
        expr = parse_expr("1 + 2 * 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "+"
        assert isinstance(expr.left, NumberLiteral)
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == "*"

    def test_grouped_expression(self):
        # (1 + 2) * 3
        expr = parse_expr("(1 + 2) * 3")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "*"
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == "+"

    def test_comparison(self):
        expr = parse_expr("a < b")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "<"

    def test_equality(self):
        expr = parse_expr("a == b")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "=="

    def test_logical_and_or(self):
        # a and b or c => (a and b) or c
        expr = parse_expr("a and b or c")
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "or"
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == "and"


class TestUnaryOperators:
    def test_negation(self):
        expr = parse_expr("-5")
        assert isinstance(expr, UnaryOp)
        assert expr.operator == "-"
        assert isinstance(expr.operand, NumberLiteral)

    def test_not(self):
        expr = parse_expr("not true")
        assert isinstance(expr, UnaryOp)
        assert expr.operator == "not"


class TestFunctionCall:
    def test_no_args(self):
        expr = parse_expr("foo()")
        assert isinstance(expr, FunctionCall)
        assert isinstance(expr.callee, Identifier)
        assert len(expr.arguments) == 0

    def test_with_args(self):
        expr = parse_expr("add(1, 2)")
        assert isinstance(expr, FunctionCall)
        assert len(expr.arguments) == 2

    def test_nested_call(self):
        expr = parse_expr("f(g(x))")
        assert isinstance(expr, FunctionCall)
        assert isinstance(expr.arguments[0], FunctionCall)


class TestIndexAccess:
    def test_simple_index(self):
        expr = parse_expr("arr[0]")
        assert isinstance(expr, IndexAccess)
        assert isinstance(expr.obj, Identifier)
        assert isinstance(expr.index, NumberLiteral)


class TestStatements:
    def test_let_statement(self):
        program = parse("let x = 5")
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, LetStatement)
        assert stmt.name == "x"
        assert isinstance(stmt.value, NumberLiteral)

    def test_if_statement(self):
        program = parse("if true do\n  print(1)\nend")
        stmt = program.statements[0]
        assert isinstance(stmt, IfStatement)
        assert len(stmt.then_body) == 1

    def test_if_elif_else(self):
        source = "if x do\n  1\nelif y do\n  2\nelse do\n  3\nend"
        program = parse(source)
        stmt = program.statements[0]
        assert isinstance(stmt, IfStatement)
        assert len(stmt.elif_clauses) == 1
        assert stmt.else_body is not None

    def test_while_statement(self):
        program = parse("while true do\n  print(1)\nend")
        stmt = program.statements[0]
        assert isinstance(stmt, WhileStatement)

    def test_function_def(self):
        program = parse("fn add(a, b) do\n  return a + b\nend")
        stmt = program.statements[0]
        assert isinstance(stmt, FunctionDef)
        assert stmt.name == "add"
        assert stmt.params == ["a", "b"]
        assert len(stmt.body) == 1

    def test_return_with_value(self):
        program = parse("fn f() do\n  return 42\nend")
        fn = program.statements[0]
        assert isinstance(fn, FunctionDef)
        ret = fn.body[0]
        assert isinstance(ret, ReturnStatement)
        assert isinstance(ret.value, NumberLiteral)

    def test_return_without_value(self):
        program = parse("fn f() do\n  return\nend")
        fn = program.statements[0]
        ret = fn.body[0]
        assert isinstance(ret, ReturnStatement)
        assert ret.value is None


class TestErrors:
    def test_missing_end(self):
        with pytest.raises(EmberSyntaxError, match="Expected 'end'"):
            parse("if true do\n  print(1)")

    def test_missing_do(self):
        with pytest.raises(EmberSyntaxError, match="Expected 'do'"):
            parse("if true\n  print(1)\nend")

    def test_unexpected_token(self):
        with pytest.raises(EmberSyntaxError):
            parse(")")
