"""Shared test fixtures and helpers for the Ember test suite."""

from __future__ import annotations

from typing import List

import pytest

from ember.interpreter import Interpreter
from ember.lexer import Lexer
from ember.parser import Parser


@pytest.fixture
def lexer() -> Lexer:
    return Lexer()


@pytest.fixture
def parser() -> Parser:
    return Parser()


def run_ember(source: str) -> List[str]:
    """Run Ember source code and return a list of printed output lines."""
    output: List[str] = []
    interpreter = Interpreter(output_fn=lambda text: output.append(text))
    tokens = Lexer().tokenize(source)
    program = Parser().parse(tokens)
    interpreter.execute(program)
    return output
