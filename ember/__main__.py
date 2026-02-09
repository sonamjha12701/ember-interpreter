"""Entry point for ``python -m ember`` and the ``ember`` CLI command.

Usage:
    ember                     Start the interactive REPL
    ember <file.ember>        Execute an Ember source file
    ember --tokens <file>     Print the token stream (debug mode)
    ember --ast <file>        Print the AST (debug mode)
"""

from __future__ import annotations

import argparse
import sys

from ember.lexer import Lexer
from ember.parser import Parser


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="ember",
        description="Ember — a small programming language interpreter",
    )
    ap.add_argument("file", nargs="?", help="Ember source file to execute")
    ap.add_argument("--tokens", action="store_true", help="Print token stream and exit")
    ap.add_argument("--ast", action="store_true", help="Print AST and exit")
    args = ap.parse_args()

    # No file → start REPL
    if args.file is None:
        from ember.repl import start_repl
        start_repl()
        return

    # Read source file
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        sys.exit(1)

    # --tokens mode
    if args.tokens:
        tokens = Lexer().tokenize(source)
        for tok in tokens:
            print(tok)
        return

    # --ast mode
    if args.ast:
        tokens = Lexer().tokenize(source)
        program = Parser().parse(tokens)
        _print_ast(program, indent=0)
        return

    # Normal execution
    from ember.runner import run_file
    run_file(args.file)


def _print_ast(node: object, indent: int = 0) -> None:
    """Pretty-print an AST node tree."""
    prefix = "  " * indent
    if isinstance(node, list):
        for item in node:
            _print_ast(item, indent)
        return

    name = type(node).__name__
    # Collect fields (skip line/column for cleaner output)
    if hasattr(node, "__dataclass_fields__"):
        fields = {
            k: v
            for k, v in node.__dict__.items()
            if k not in ("line", "column")
        }
        simple_fields = {}
        complex_fields = {}
        for k, v in fields.items():
            if isinstance(v, list) or (hasattr(v, "__dataclass_fields__")):
                complex_fields[k] = v
            else:
                simple_fields[k] = v

        parts = ", ".join(f"{k}={v!r}" for k, v in simple_fields.items())
        print(f"{prefix}{name}({parts})")
        for k, v in complex_fields.items():
            print(f"{prefix}  {k}:")
            if isinstance(v, list):
                for item in v:
                    _print_ast(item, indent + 2)
            else:
                _print_ast(v, indent + 2)
    else:
        print(f"{prefix}{node!r}")


if __name__ == "__main__":
    main()
