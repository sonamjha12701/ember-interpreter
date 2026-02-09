"""Built-in functions for the Ember language.

Each built-in is wrapped in an :class:`EmberBuiltin` instance that the
interpreter can call exactly like a user-defined function.
"""

from __future__ import annotations

from typing import Any, Callable, List

from ember.environment import Environment
from ember.errors import EmberRuntimeError


class EmberBuiltin:
    """A built-in function callable by the Ember interpreter."""

    def __init__(self, name: str, arity: int, fn: Callable[..., Any]) -> None:
        self.name = name
        self.arity = arity  # -1 means variadic
        self.fn = fn

    def __repr__(self) -> str:
        return f"<builtin {self.name}>"


def _builtin_len(args: List[Any], line: int, col: int) -> Any:
    if isinstance(args[0], str):
        return float(len(args[0]))
    if isinstance(args[0], list):
        return float(len(args[0]))
    raise EmberRuntimeError(
        f"len() expects a string or list, got {_type_name(args[0])}", line, col,
    )


def _builtin_append(args: List[Any], line: int, col: int) -> Any:
    if not isinstance(args[0], list):
        raise EmberRuntimeError(
            f"append() expects a list as first argument, got {_type_name(args[0])}",
            line, col,
        )
    args[0].append(args[1])
    return None


def _builtin_type(args: List[Any], line: int, col: int) -> Any:
    return _type_name(args[0])


def _builtin_str(args: List[Any], line: int, col: int) -> Any:
    return _format_value(args[0])


def _builtin_num(args: List[Any], line: int, col: int) -> Any:
    try:
        return float(args[0])
    except (ValueError, TypeError):
        raise EmberRuntimeError(
            f"num() cannot convert {_format_value(args[0])!r} to a number",
            line, col,
        )


def _builtin_input(args: List[Any], line: int, col: int) -> Any:
    prompt = _format_value(args[0]) if args else ""
    return input(prompt)


def _type_name(value: Any) -> str:
    """Return the Ember type name for a Python value."""
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
    if isinstance(value, EmberBuiltin):
        return "function"
    # EmberFunction is checked by name to avoid circular imports.
    type_name = type(value).__name__
    if type_name == "EmberFunction":
        return "function"
    return "unknown"


def _format_value(value: Any) -> str:
    """Format an Ember value for display."""
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        items = ", ".join(_format_value(v) for v in value)
        return f"[{items}]"
    return str(value)


def register_builtins(env: Environment, output_fn: Callable[..., Any] = print) -> None:
    """Register all built-in functions into *env*."""

    def _builtin_print(args: List[Any], line: int, col: int) -> Any:
        output_fn(" ".join(_format_value(a) for a in args))
        return None

    builtins = [
        EmberBuiltin("print", -1, _builtin_print),
        EmberBuiltin("len", 1, _builtin_len),
        EmberBuiltin("append", 2, _builtin_append),
        EmberBuiltin("type", 1, _builtin_type),
        EmberBuiltin("str", 1, _builtin_str),
        EmberBuiltin("num", 1, _builtin_num),
        EmberBuiltin("input", -1, _builtin_input),
    ]
    for b in builtins:
        env.define(b.name, b)
