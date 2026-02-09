"""Tree-walking interpreter for the Ember language.

Walks the AST produced by the parser and evaluates each node.
Uses :class:`Environment` for lexical scoping and supports closures,
recursion, and first-class functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from ember.ast_nodes import (
    ASTNode,
    BinaryOp,
    BoolLiteral,
    ExpressionStatement,
    FunctionCall,
    FunctionDef,
    Identifier,
    IfStatement,
    IndexAccess,
    IndexAssignment,
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
from ember.builtins import EmberBuiltin, _format_value, register_builtins
from ember.environment import Environment
from ember.errors import EmberRuntimeError, EmberTypeError


# ------------------------------------------------------------------
# Callable representation for user-defined functions
# ------------------------------------------------------------------

@dataclass
class EmberFunction:
    """A user-defined Ember function (captures its closure environment)."""
    name: str
    params: List[str]
    body: List[ASTNode]
    closure: Environment

    def __repr__(self) -> str:
        return f"<fn {self.name}>"


class ReturnSignal(Exception):
    """Control-flow exception used to unwind the call stack on ``return``."""

    def __init__(self, value: Any) -> None:
        self.value = value


# ------------------------------------------------------------------
# Interpreter
# ------------------------------------------------------------------

MAX_CALL_DEPTH = 1000


class Interpreter:
    """Evaluates an Ember AST by walking the tree recursively."""

    def __init__(self, output_fn: Callable[..., Any] = print) -> None:
        self.output_fn = output_fn
        self.globals = Environment()
        register_builtins(self.globals, output_fn)
        self._call_depth = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, program: Program) -> None:
        """Execute a complete Ember program."""
        for stmt in program.statements:
            self._exec_stmt(stmt, self.globals)

    # ------------------------------------------------------------------
    # Statement execution
    # ------------------------------------------------------------------

    def _exec_stmt(self, stmt: ASTNode, env: Environment) -> None:
        if isinstance(stmt, LetStatement):
            self._exec_let(stmt, env)
        elif isinstance(stmt, IndexAssignment):
            self._exec_index_assign(stmt, env)
        elif isinstance(stmt, IfStatement):
            self._exec_if(stmt, env)
        elif isinstance(stmt, WhileStatement):
            self._exec_while(stmt, env)
        elif isinstance(stmt, FunctionDef):
            self._exec_fn_def(stmt, env)
        elif isinstance(stmt, ReturnStatement):
            self._exec_return(stmt, env)
        elif isinstance(stmt, ExpressionStatement):
            self._eval(stmt.expression, env)
        else:
            raise EmberRuntimeError(
                f"Unknown statement type: {type(stmt).__name__}",
                stmt.line, stmt.column,
            )

    def _exec_let(self, stmt: LetStatement, env: Environment) -> None:
        value = self._eval(stmt.value, env)
        # If the variable already exists in an enclosing scope, update it.
        # Otherwise define it in the current scope.
        if env.has(stmt.name):
            env.set(stmt.name, value)
        else:
            env.define(stmt.name, value)

    def _exec_index_assign(self, stmt: IndexAssignment, env: Environment) -> None:
        obj = self._eval(stmt.obj, env)
        index = self._eval(stmt.index, env)
        value = self._eval(stmt.value, env)

        if not isinstance(obj, list):
            raise EmberTypeError(
                f"Cannot index into {_format_value(obj)} (type {type(obj).__name__})",
                stmt.line, stmt.column,
            )
        if not isinstance(index, float):
            raise EmberTypeError(
                "List index must be a number", stmt.line, stmt.column,
            )
        idx = int(index)
        if idx < 0 or idx >= len(obj):
            raise EmberRuntimeError(
                f"Index {idx} out of range for list of length {len(obj)}",
                stmt.line, stmt.column,
            )
        obj[idx] = value

    def _exec_if(self, stmt: IfStatement, env: Environment) -> None:
        if self._is_truthy(self._eval(stmt.condition, env)):
            self._exec_block(stmt.then_body, env)
            return

        for elif_cond, elif_body in stmt.elif_clauses:
            if self._is_truthy(self._eval(elif_cond, env)):
                self._exec_block(elif_body, env)
                return

        if stmt.else_body is not None:
            self._exec_block(stmt.else_body, env)

    def _exec_while(self, stmt: WhileStatement, env: Environment) -> None:
        while self._is_truthy(self._eval(stmt.condition, env)):
            self._exec_block(stmt.body, env)

    def _exec_fn_def(self, stmt: FunctionDef, env: Environment) -> None:
        fn = EmberFunction(
            name=stmt.name,
            params=stmt.params,
            body=stmt.body,
            closure=env,
        )
        env.define(stmt.name, fn)

    def _exec_return(self, stmt: ReturnStatement, env: Environment) -> None:
        value = None
        if stmt.value is not None:
            value = self._eval(stmt.value, env)
        raise ReturnSignal(value)

    def _exec_block(self, stmts: List[ASTNode], env: Environment) -> None:
        child_env = Environment(parent=env)
        for s in stmts:
            self._exec_stmt(s, child_env)

    # ------------------------------------------------------------------
    # Expression evaluation
    # ------------------------------------------------------------------

    def _eval(self, expr: ASTNode, env: Environment) -> Any:
        if isinstance(expr, NumberLiteral):
            return expr.value
        if isinstance(expr, StringLiteral):
            return expr.value
        if isinstance(expr, BoolLiteral):
            return expr.value
        if isinstance(expr, NilLiteral):
            return None
        if isinstance(expr, ListLiteral):
            return [self._eval(e, env) for e in expr.elements]
        if isinstance(expr, Identifier):
            return self._eval_identifier(expr, env)
        if isinstance(expr, UnaryOp):
            return self._eval_unary(expr, env)
        if isinstance(expr, BinaryOp):
            return self._eval_binary(expr, env)
        if isinstance(expr, FunctionCall):
            return self._eval_call(expr, env)
        if isinstance(expr, IndexAccess):
            return self._eval_index(expr, env)

        raise EmberRuntimeError(
            f"Unknown expression type: {type(expr).__name__}",
            expr.line, expr.column,
        )

    def _eval_identifier(self, expr: Identifier, env: Environment) -> Any:
        try:
            return env.get(expr.name)
        except KeyError:
            raise EmberRuntimeError(
                f"Undefined variable '{expr.name}'", expr.line, expr.column,
            )

    def _eval_unary(self, expr: UnaryOp, env: Environment) -> Any:
        operand = self._eval(expr.operand, env)

        if expr.operator == "-":
            if not isinstance(operand, float):
                raise EmberTypeError(
                    f"Cannot negate {_format_value(operand)} (type {type(operand).__name__})",
                    expr.line, expr.column,
                )
            return -operand

        if expr.operator == "not":
            return not self._is_truthy(operand)

        raise EmberRuntimeError(
            f"Unknown unary operator '{expr.operator}'", expr.line, expr.column,
        )

    def _eval_binary(self, expr: BinaryOp, env: Environment) -> Any:
        # Short-circuit logical operators
        if expr.operator == "and":
            left = self._eval(expr.left, env)
            if not self._is_truthy(left):
                return left
            return self._eval(expr.right, env)

        if expr.operator == "or":
            left = self._eval(expr.left, env)
            if self._is_truthy(left):
                return left
            return self._eval(expr.right, env)

        left = self._eval(expr.left, env)
        right = self._eval(expr.right, env)

        # Equality (works on all types)
        if expr.operator == "==":
            return self._ember_equal(left, right)
        if expr.operator == "!=":
            return not self._ember_equal(left, right)

        # String concatenation
        if expr.operator == "+" and isinstance(left, str) and isinstance(right, str):
            return left + right

        # Arithmetic and comparison (numbers only)
        if isinstance(left, float) and isinstance(right, float):
            return self._eval_numeric_binary(expr.operator, left, right, expr)

        # Type error for incompatible operands
        raise EmberTypeError(
            f"Cannot apply '{expr.operator}' to "
            f"{_format_value(left)} ({self._type_name(left)}) and "
            f"{_format_value(right)} ({self._type_name(right)})",
            expr.line, expr.column,
        )

    def _eval_numeric_binary(
        self, op: str, left: float, right: float, expr: BinaryOp,
    ) -> Any:
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise EmberRuntimeError(
                    "Division by zero", expr.line, expr.column,
                )
            return left / right
        if op == "%":
            if right == 0:
                raise EmberRuntimeError(
                    "Modulo by zero", expr.line, expr.column,
                )
            return left % right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right

        raise EmberRuntimeError(
            f"Unknown operator '{op}'", expr.line, expr.column,
        )

    def _eval_call(self, expr: FunctionCall, env: Environment) -> Any:
        callee = self._eval(expr.callee, env)
        args = [self._eval(a, env) for a in expr.arguments]

        # Built-in function
        if isinstance(callee, EmberBuiltin):
            if callee.arity != -1 and len(args) != callee.arity:
                raise EmberRuntimeError(
                    f"{callee.name}() expects {callee.arity} argument(s), "
                    f"got {len(args)}",
                    expr.line, expr.column,
                )
            return callee.fn(args, expr.line, expr.column)

        # User-defined function
        if isinstance(callee, EmberFunction):
            if len(args) != len(callee.params):
                raise EmberRuntimeError(
                    f"{callee.name}() expects {len(callee.params)} argument(s), "
                    f"got {len(args)}",
                    expr.line, expr.column,
                )
            self._call_depth += 1
            if self._call_depth > MAX_CALL_DEPTH:
                self._call_depth = 0
                raise EmberRuntimeError(
                    f"Maximum recursion depth exceeded ({MAX_CALL_DEPTH})",
                    expr.line, expr.column,
                )
            try:
                call_env = Environment(parent=callee.closure)
                for name, value in zip(callee.params, args):
                    call_env.define(name, value)
                for stmt in callee.body:
                    self._exec_stmt(stmt, call_env)
            except ReturnSignal as ret:
                return ret.value
            finally:
                self._call_depth -= 1
            return None

        raise EmberRuntimeError(
            f"Cannot call {_format_value(callee)} (type {self._type_name(callee)})",
            expr.line, expr.column,
        )

    def _eval_index(self, expr: IndexAccess, env: Environment) -> Any:
        obj = self._eval(expr.obj, env)
        index = self._eval(expr.index, env)

        if isinstance(obj, list):
            if not isinstance(index, float):
                raise EmberTypeError(
                    "List index must be a number", expr.line, expr.column,
                )
            idx = int(index)
            if idx < 0 or idx >= len(obj):
                raise EmberRuntimeError(
                    f"Index {idx} out of range for list of length {len(obj)}",
                    expr.line, expr.column,
                )
            return obj[idx]

        if isinstance(obj, str):
            if not isinstance(index, float):
                raise EmberTypeError(
                    "String index must be a number", expr.line, expr.column,
                )
            idx = int(index)
            if idx < 0 or idx >= len(obj):
                raise EmberRuntimeError(
                    f"Index {idx} out of range for string of length {len(obj)}",
                    expr.line, expr.column,
                )
            return obj[idx]

        raise EmberTypeError(
            f"Cannot index into {_format_value(obj)} (type {self._type_name(obj)})",
            expr.line, expr.column,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        """Ember truthiness: nil and false are falsy, everything else is truthy."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True

    @staticmethod
    def _ember_equal(a: Any, b: Any) -> bool:
        """Ember equality comparison."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return a == b

    @staticmethod
    def _type_name(value: Any) -> str:
        """Return the Ember type name for a value."""
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, (EmberBuiltin, EmberFunction)):
            return "function"
        return "unknown"
