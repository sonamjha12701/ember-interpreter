"""Lexical scoping via chained environments for the Ember interpreter.

Each :class:`Environment` holds a mapping of variable names to values
and an optional reference to a parent (enclosing) scope.  Variable
look-ups walk the chain until a binding is found or the global scope
is exhausted.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class Environment:
    """A single scope level in the Ember variable environment."""

    def __init__(self, parent: Optional[Environment] = None) -> None:
        self._values: Dict[str, Any] = {}
        self._parent = parent

    def define(self, name: str, value: Any) -> None:
        """Bind *name* to *value* in the current scope."""
        self._values[name] = value

    def get(self, name: str) -> Any:
        """Look up *name*, walking up the scope chain.

        Raises ``KeyError`` if the variable is not defined in any
        enclosing scope (the caller wraps this in an ``EmberRuntimeError``).
        """
        if name in self._values:
            return self._values[name]
        if self._parent is not None:
            return self._parent.get(name)
        raise KeyError(name)

    def set(self, name: str, value: Any) -> None:
        """Update *name* in the nearest enclosing scope that contains it.

        Raises ``KeyError`` if the variable is not defined anywhere.
        """
        if name in self._values:
            self._values[name] = value
            return
        if self._parent is not None:
            self._parent.set(name, value)
            return
        raise KeyError(name)

    def has(self, name: str) -> bool:
        """Return ``True`` if *name* is defined in this scope or any parent."""
        if name in self._values:
            return True
        if self._parent is not None:
            return self._parent.has(name)
        return False
