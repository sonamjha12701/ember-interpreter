"""Recursive-descent parser with Pratt expression parsing for Ember.

Converts a token stream into an Abstract Syntax Tree.  Statements are
parsed with straightforward recursive descent; expressions use
top-down operator precedence (Pratt parsing) to handle precedence and
associativity cleanly.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

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
from ember.errors import EmberSyntaxError
from ember.tokens import Token, TokenType


# ------------------------------------------------------------------
# Precedence levels (lowest → highest)
# ------------------------------------------------------------------

PREC_NONE = 0
PREC_OR = 1
PREC_AND = 2
PREC_NOT = 3
PREC_EQUALITY = 4      # == !=
PREC_COMPARISON = 5     # < > <= >=
PREC_ADDITION = 6       # + -
PREC_MULTIPLICATION = 7 # * / %
PREC_UNARY = 8          # - (negation)
PREC_CALL = 9           # () []

# Map token types to their infix precedence.
INFIX_PRECEDENCE: Dict[TokenType, int] = {
    TokenType.OR: PREC_OR,
    TokenType.AND: PREC_AND,
    TokenType.EQUAL_EQUAL: PREC_EQUALITY,
    TokenType.BANG_EQUAL: PREC_EQUALITY,
    TokenType.LESS: PREC_COMPARISON,
    TokenType.GREATER: PREC_COMPARISON,
    TokenType.LESS_EQUAL: PREC_COMPARISON,
    TokenType.GREATER_EQUAL: PREC_COMPARISON,
    TokenType.PLUS: PREC_ADDITION,
    TokenType.MINUS: PREC_ADDITION,
    TokenType.STAR: PREC_MULTIPLICATION,
    TokenType.SLASH: PREC_MULTIPLICATION,
    TokenType.PERCENT: PREC_MULTIPLICATION,
    TokenType.LPAREN: PREC_CALL,
    TokenType.LBRACKET: PREC_CALL,
}


class Parser:
    """Parses a list of tokens into an Ember AST."""

    def __init__(self) -> None:
        self._tokens: List[Token] = []
        self._pos: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, tokens: List[Token]) -> Program:
        """Parse *tokens* and return a :class:`Program` AST node."""
        self._tokens = tokens
        self._pos = 0

        self._skip_newlines()
        statements: List[ASTNode] = []
        while not self._check(TokenType.EOF):
            stmt = self._parse_statement()
            statements.append(stmt)
            self._skip_newlines()

        tok = self._current()
        return Program(line=1, column=1, statements=statements)

    # ------------------------------------------------------------------
    # Statement parsing
    # ------------------------------------------------------------------

    def _parse_statement(self) -> ASTNode:
        """Dispatch to the correct statement parser."""
        if self._check(TokenType.LET):
            return self._parse_let()
        if self._check(TokenType.IF):
            return self._parse_if()
        if self._check(TokenType.WHILE):
            return self._parse_while()
        if self._check(TokenType.FN):
            return self._parse_fn()
        if self._check(TokenType.RETURN):
            return self._parse_return()
        return self._parse_expression_statement()

    def _parse_let(self) -> ASTNode:
        """Parse ``let name = expr`` or ``let obj[index] = expr``."""
        let_tok = self._consume(TokenType.LET, "Expected 'let'")

        # Check for index assignment: let arr[i] = value
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'let'")

        if self._check(TokenType.LBRACKET):
            # Index assignment: let arr[i] = value
            self._advance()  # consume [
            index_expr = self._parse_expression()
            self._consume(TokenType.RBRACKET, "Expected ']' after index")
            self._consume(TokenType.EQUAL, "Expected '=' in assignment")
            value = self._parse_expression()
            self._expect_newline()
            obj = Identifier(line=name_tok.line, column=name_tok.column, name=name_tok.lexeme)
            return IndexAssignment(
                line=let_tok.line, column=let_tok.column,
                obj=obj, index=index_expr, value=value,
            )

        self._consume(TokenType.EQUAL, "Expected '=' after variable name")
        value = self._parse_expression()
        self._expect_newline()
        return LetStatement(
            line=let_tok.line, column=let_tok.column,
            name=name_tok.lexeme, value=value,
        )

    def _parse_if(self) -> IfStatement:
        """Parse ``if cond do ... (elif cond do ...)* (else do ...)? end``."""
        if_tok = self._consume(TokenType.IF, "Expected 'if'")
        condition = self._parse_expression()
        self._consume(TokenType.DO, "Expected 'do' after if condition")
        self._expect_newline()
        then_body = self._parse_block()

        elif_clauses: List[Tuple[ASTNode, List[ASTNode]]] = []
        while self._check(TokenType.ELIF):
            self._advance()
            elif_cond = self._parse_expression()
            self._consume(TokenType.DO, "Expected 'do' after elif condition")
            self._expect_newline()
            elif_body = self._parse_block()
            elif_clauses.append((elif_cond, elif_body))

        else_body: Optional[List[ASTNode]] = None
        if self._check(TokenType.ELSE):
            self._advance()
            self._consume(TokenType.DO, "Expected 'do' after else")
            self._expect_newline()
            else_body = self._parse_block()

        self._consume(TokenType.END, "Expected 'end' to close if block")
        self._expect_newline()
        return IfStatement(
            line=if_tok.line, column=if_tok.column,
            condition=condition,
            then_body=then_body,
            elif_clauses=elif_clauses,
            else_body=else_body,
        )

    def _parse_while(self) -> WhileStatement:
        """Parse ``while cond do ... end``."""
        while_tok = self._consume(TokenType.WHILE, "Expected 'while'")
        condition = self._parse_expression()
        self._consume(TokenType.DO, "Expected 'do' after while condition")
        self._expect_newline()
        body = self._parse_block()
        self._consume(TokenType.END, "Expected 'end' to close while block")
        self._expect_newline()
        return WhileStatement(
            line=while_tok.line, column=while_tok.column,
            condition=condition, body=body,
        )

    def _parse_fn(self) -> FunctionDef:
        """Parse ``fn name(params) do ... end``."""
        fn_tok = self._consume(TokenType.FN, "Expected 'fn'")
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected function name after 'fn'")
        self._consume(TokenType.LPAREN, "Expected '(' after function name")

        params: List[str] = []
        if not self._check(TokenType.RPAREN):
            first = self._consume(TokenType.IDENTIFIER, "Expected parameter name")
            params.append(first.lexeme)
            while self._check(TokenType.COMMA):
                self._advance()
                p = self._consume(TokenType.IDENTIFIER, "Expected parameter name")
                params.append(p.lexeme)

        self._consume(TokenType.RPAREN, "Expected ')' after parameters")
        self._consume(TokenType.DO, "Expected 'do' after function signature")
        self._expect_newline()
        body = self._parse_block()
        self._consume(TokenType.END, "Expected 'end' to close function body")
        self._expect_newline()
        return FunctionDef(
            line=fn_tok.line, column=fn_tok.column,
            name=name_tok.lexeme, params=params, body=body,
        )

    def _parse_return(self) -> ReturnStatement:
        """Parse ``return expr?``."""
        ret_tok = self._consume(TokenType.RETURN, "Expected 'return'")
        value: Optional[ASTNode] = None
        if not self._check(TokenType.NEWLINE) and not self._check(TokenType.EOF):
            value = self._parse_expression()
        self._expect_newline()
        return ReturnStatement(
            line=ret_tok.line, column=ret_tok.column, value=value,
        )

    def _parse_expression_statement(self) -> ExpressionStatement:
        """Parse an expression used as a statement."""
        expr = self._parse_expression()
        self._expect_newline()
        return ExpressionStatement(
            line=expr.line, column=expr.column, expression=expr,
        )

    # ------------------------------------------------------------------
    # Block parsing
    # ------------------------------------------------------------------

    def _parse_block(self) -> List[ASTNode]:
        """Parse statements until we reach ``end``, ``elif``, or ``else``."""
        self._skip_newlines()
        stmts: List[ASTNode] = []
        while not self._check(TokenType.END) and \
              not self._check(TokenType.ELIF) and \
              not self._check(TokenType.ELSE) and \
              not self._check(TokenType.EOF):
            stmts.append(self._parse_statement())
            self._skip_newlines()
        return stmts

    # ------------------------------------------------------------------
    # Pratt expression parser
    # ------------------------------------------------------------------

    def _parse_expression(self, min_prec: int = PREC_NONE) -> ASTNode:
        """Parse an expression using top-down operator precedence."""
        left = self._parse_prefix()

        while True:
            tok = self._current()
            prec = INFIX_PRECEDENCE.get(tok.type, PREC_NONE)
            if prec <= min_prec:
                break
            left = self._parse_infix(left, prec)

        return left

    def _parse_prefix(self) -> ASTNode:
        """Parse a prefix expression (literal, unary, grouping, identifier)."""
        tok = self._current()

        # Number literal
        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumberLiteral(line=tok.line, column=tok.column, value=tok.literal)

        # String literal
        if tok.type == TokenType.STRING:
            self._advance()
            return StringLiteral(line=tok.line, column=tok.column, value=tok.literal)

        # Boolean literals
        if tok.type == TokenType.TRUE:
            self._advance()
            return BoolLiteral(line=tok.line, column=tok.column, value=True)
        if tok.type == TokenType.FALSE:
            self._advance()
            return BoolLiteral(line=tok.line, column=tok.column, value=False)

        # Nil
        if tok.type == TokenType.NIL:
            self._advance()
            return NilLiteral(line=tok.line, column=tok.column)

        # Identifier
        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return Identifier(line=tok.line, column=tok.column, name=tok.lexeme)

        # Grouped expression
        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        # List literal
        if tok.type == TokenType.LBRACKET:
            return self._parse_list_literal()

        # Unary minus
        if tok.type == TokenType.MINUS:
            self._advance()
            operand = self._parse_expression(PREC_UNARY)
            return UnaryOp(
                line=tok.line, column=tok.column,
                operator="-", operand=operand,
            )

        # Unary not
        if tok.type == TokenType.NOT:
            self._advance()
            operand = self._parse_expression(PREC_NOT)
            return UnaryOp(
                line=tok.line, column=tok.column,
                operator="not", operand=operand,
            )

        raise EmberSyntaxError(
            f"Unexpected token '{tok.lexeme}'", tok.line, tok.column,
        )

    def _parse_infix(self, left: ASTNode, prec: int) -> ASTNode:
        """Parse an infix expression (binary op, function call, index)."""
        tok = self._current()

        # Function call
        if tok.type == TokenType.LPAREN:
            self._advance()
            args: List[ASTNode] = []
            if not self._check(TokenType.RPAREN):
                args.append(self._parse_expression())
                while self._check(TokenType.COMMA):
                    self._advance()
                    args.append(self._parse_expression())
            self._consume(TokenType.RPAREN, "Expected ')' after arguments")
            return FunctionCall(
                line=tok.line, column=tok.column,
                callee=left, arguments=args,
            )

        # Index access
        if tok.type == TokenType.LBRACKET:
            self._advance()
            index = self._parse_expression()
            self._consume(TokenType.RBRACKET, "Expected ']' after index")
            return IndexAccess(
                line=tok.line, column=tok.column,
                obj=left, index=index,
            )

        # Binary operators — left-associative
        op_lexeme = tok.lexeme
        self._advance()
        right = self._parse_expression(prec)
        return BinaryOp(
            line=tok.line, column=tok.column,
            left=left, operator=op_lexeme, right=right,
        )

    def _parse_list_literal(self) -> ListLiteral:
        """Parse ``[expr, expr, ...]``."""
        tok = self._consume(TokenType.LBRACKET, "Expected '['")
        elements: List[ASTNode] = []
        if not self._check(TokenType.RBRACKET):
            elements.append(self._parse_expression())
            while self._check(TokenType.COMMA):
                self._advance()
                elements.append(self._parse_expression())
        self._consume(TokenType.RBRACKET, "Expected ']' after list elements")
        return ListLiteral(line=tok.line, column=tok.column, elements=elements)

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    def _current(self) -> Token:
        """Return the token at the current position."""
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        """Consume and return the current token."""
        tok = self._tokens[self._pos]
        if tok.type != TokenType.EOF:
            self._pos += 1
        return tok

    def _check(self, tt: TokenType) -> bool:
        """Check if the current token is of type *tt* without consuming."""
        return self._current().type == tt

    def _consume(self, tt: TokenType, message: str) -> Token:
        """Consume a token of the expected type, or raise an error."""
        tok = self._current()
        if tok.type != tt:
            raise EmberSyntaxError(
                f"{message}, got '{tok.lexeme}'", tok.line, tok.column,
            )
        return self._advance()

    def _skip_newlines(self) -> None:
        """Skip any NEWLINE tokens at the current position."""
        while self._check(TokenType.NEWLINE):
            self._advance()

    def _expect_newline(self) -> None:
        """Expect a NEWLINE or EOF after a statement."""
        if self._check(TokenType.EOF):
            return
        if self._check(TokenType.NEWLINE):
            self._advance()
            return
        # Allow a missing newline before 'end', 'elif', 'else' for flexibility.
        if self._check(TokenType.END) or self._check(TokenType.ELIF) or self._check(TokenType.ELSE):
            return
        tok = self._current()
        raise EmberSyntaxError(
            f"Expected newline after statement, got '{tok.lexeme}'",
            tok.line, tok.column,
        )
