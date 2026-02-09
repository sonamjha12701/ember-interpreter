"""Abstract Syntax Tree node definitions for the Ember language.

Every node carries *line* and *column* fields so the interpreter can
produce error messages that point back to the source code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


# =====================================================================
# Base
# =====================================================================

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int
    column: int


# =====================================================================
# Expressions — nodes that produce a value
# =====================================================================

@dataclass
class NumberLiteral(ASTNode):
    value: float


@dataclass
class StringLiteral(ASTNode):
    value: str


@dataclass
class BoolLiteral(ASTNode):
    value: bool


@dataclass
class NilLiteral(ASTNode):
    pass


@dataclass
class ListLiteral(ASTNode):
    elements: List[ASTNode]


@dataclass
class Identifier(ASTNode):
    name: str


@dataclass
class UnaryOp(ASTNode):
    operator: str
    operand: ASTNode


@dataclass
class BinaryOp(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode


@dataclass
class FunctionCall(ASTNode):
    callee: ASTNode
    arguments: List[ASTNode]


@dataclass
class IndexAccess(ASTNode):
    obj: ASTNode
    index: ASTNode


# =====================================================================
# Statements — nodes that perform actions
# =====================================================================

@dataclass
class LetStatement(ASTNode):
    name: str
    value: ASTNode


@dataclass
class IndexAssignment(ASTNode):
    obj: ASTNode
    index: ASTNode
    value: ASTNode


@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_body: List[ASTNode]
    elif_clauses: List[Tuple[ASTNode, List[ASTNode]]]
    else_body: Optional[List[ASTNode]]


@dataclass
class WhileStatement(ASTNode):
    condition: ASTNode
    body: List[ASTNode]


@dataclass
class FunctionDef(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]


@dataclass
class ReturnStatement(ASTNode):
    value: Optional[ASTNode]


@dataclass
class ExpressionStatement(ASTNode):
    expression: ASTNode


# =====================================================================
# Top-level
# =====================================================================

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]
