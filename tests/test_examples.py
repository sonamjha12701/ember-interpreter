"""Integration tests that run example Ember programs.

Ensures the example programs execute without errors and produce
expected output.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ember.interpreter import Interpreter
from ember.lexer import Lexer
from ember.parser import Parser

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def run_example(filename: str) -> list:
    """Run an example file and return captured output lines."""
    filepath = EXAMPLES_DIR / filename
    source = filepath.read_text(encoding="utf-8")
    output = []
    interpreter = Interpreter(output_fn=lambda text: output.append(text))
    tokens = Lexer().tokenize(source)
    program = Parser().parse(tokens)
    interpreter.execute(program)
    return output


class TestHello:
    def test_runs_without_error(self):
        output = run_example("hello.ember")
        assert len(output) >= 1
        assert "Hello" in output[0]


class TestFibonacci:
    def test_produces_output(self):
        output = run_example("fibonacci.ember")
        assert len(output) == 15
        assert "fib(0) = 0" in output[0]
        assert "fib(1) = 1" in output[1]
        # fib(10) = 55
        assert "55" in output[10]


class TestFizzbuzz:
    def test_produces_correct_output(self):
        output = run_example("fizzbuzz.ember")
        assert len(output) == 30
        assert output[0] == "1"
        assert output[1] == "2"
        assert output[2] == "Fizz"
        assert output[3] == "4"
        assert output[4] == "Buzz"
        assert output[14] == "FizzBuzz"


class TestSorting:
    def test_sorts_correctly(self):
        output = run_example("sorting.ember")
        assert len(output) == 2
        assert "Before:" in output[0]
        assert "After:" in output[1]
        assert "[11, 12, 22, 25, 34, 64, 90]" in output[1]


class TestClosures:
    def test_closures_work(self):
        output = run_example("closures.ember")
        assert "add5(3) = 8" in output[0]
        assert "add10(3) = 13" in output[1]
        assert "counter() = 1" in output[2]
        assert "counter() = 2" in output[3]
        assert "counter() = 3" in output[4]


class TestAllExamplesExist:
    """Verify all expected example files are present."""

    @pytest.mark.parametrize("filename", [
        "hello.ember",
        "fibonacci.ember",
        "fizzbuzz.ember",
        "sorting.ember",
        "closures.ember",
        "guessing_game.ember",
    ])
    def test_example_exists(self, filename):
        assert (EXAMPLES_DIR / filename).exists()
