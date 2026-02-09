# Ember

A tree-walking interpreter for a small programming language, built entirely from scratch in Python. No external libraries, no parser generators — just fundamental computer science.

Ember demonstrates core concepts from programming language theory: **lexical analysis**, **recursive-descent parsing** (with Pratt operator precedence), **abstract syntax trees**, **tree-walking interpretation**, **lexical scoping**, and **closures**.

## Quick Start

```bash
# Clone and install
git clone https://github.com/sonamjha12701/ember-interpreter.git
cd ember-interpreter
pip install -e .

# Run the interactive REPL
ember

# Execute a program
ember examples/fibonacci.ember

# Debug modes
ember --tokens examples/hello.ember   # Print token stream
ember --ast examples/hello.ember       # Print abstract syntax tree
```

Or run without installing:

```bash
python -m ember examples/fibonacci.ember
```

## Language Tour

### Variables and Types

```ember
let name = "Ember"
let version = 1.0
let is_cool = true
let nothing = nil
let numbers = [1, 2, 3, 4, 5]
```

Ember has five types: **number** (64-bit float), **string**, **bool**, **list**, and **nil**.

### Arithmetic and Operators

```ember
let result = (10 + 5) * 3 - 2 / 1    # => 43
let remainder = 17 % 5                 # => 2
let greeting = "Hello, " + name + "!"  # String concatenation

# Comparison: ==, !=, <, >, <=, >=
# Logical: and, or, not
let can_vote = age >= 18 and is_citizen
```

### Control Flow

```ember
if temperature > 100 do
    print("Too hot!")
elif temperature < 0 do
    print("Freezing!")
else do
    print("Just right.")
end

let i = 0
while i < 10 do
    print(i)
    let i = i + 1
end
```

### Functions

```ember
fn fibonacci(n) do
    if n <= 1 do
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end

print(fibonacci(10))  # => 55
```

### Closures and First-Class Functions

Functions are first-class values. They can be passed as arguments, returned from other functions, and capture their enclosing scope:

```ember
fn make_counter() do
    let count = 0
    fn next() do
        let count = count + 1
        return count
    end
    return next
end

let counter = make_counter()
print(counter())  # => 1
print(counter())  # => 2
print(counter())  # => 3
```

### Lists

```ember
let items = [10, 20, 30]
print(items[0])           # => 10
let items[1] = 99          # Index assignment
append(items, 40)          # Mutate
print(len(items))          # => 4
```

### Built-in Functions

| Function | Description |
|---|---|
| `print(args...)` | Print values separated by spaces |
| `len(x)` | Length of a string or list |
| `append(list, val)` | Append a value to a list |
| `type(x)` | Return the type as a string |
| `str(x)` | Convert any value to a string |
| `num(x)` | Convert a string to a number |
| `input(prompt?)` | Read a line from standard input |

## Architecture

```
Source Code
    |
    v
 [Lexer]  ──>  Token Stream
    |
    v
 [Parser]  ──>  Abstract Syntax Tree
    |
    v
[Interpreter]  ──>  Output
```

The interpreter follows a classic three-stage pipeline:

1. **Lexer** (`ember/lexer.py`): Scans source text character by character, producing a stream of tokens. Tracks line and column numbers for error reporting.

2. **Parser** (`ember/parser.py`): Consumes tokens and builds an AST. Uses **recursive descent** for statements and **Pratt parsing** (top-down operator precedence) for expressions — an elegant technique that handles operator precedence without deep nesting.

3. **Interpreter** (`ember/interpreter.py`): Walks the AST recursively, evaluating each node. Uses **environment chaining** for lexical scoping: each scope holds a reference to its parent, enabling closures and proper variable resolution.

## Project Structure

```
ember/
├── tokens.py          # Token types and Token dataclass
├── lexer.py           # Source code → token stream
├── ast_nodes.py       # AST node definitions
├── parser.py          # Token stream → AST (Pratt parsing)
├── interpreter.py     # AST → execution
├── environment.py     # Lexical scoping via environment chaining
├── builtins.py        # Built-in function implementations
├── errors.py          # Error types with source location
├── repl.py            # Interactive REPL
├── runner.py          # File execution
└── __main__.py        # CLI entry point
```

## Running Tests

```bash
pip install pytest
pytest
```

The test suite covers the lexer, parser, interpreter, built-in functions, error reporting, and all example programs.

## Design Decisions

- **Pratt parsing** for expressions: handles operator precedence elegantly without deeply nested grammar rules. Each precedence level is a number, and adding new operators requires only a table entry.

- **`do`/`end` blocks**: avoids brace fatigue (C-style) and the complexity of indentation-sensitive parsing (Python-style). Inspired by Ruby and Lua.

- **`let` for all variable operations**: simplifies the language by using a single keyword for both declaration and reassignment, with scope determined by environment chaining.

- **`ReturnSignal` exception**: a standard technique in tree-walking interpreters (used in *Crafting Interpreters*). Avoids threading return state through every recursive call.

- **Output function injection**: the `Interpreter` accepts an `output_fn` parameter, enabling tests to capture printed output without patching `sys.stdout`.

## Language Grammar

```
program     → statement* EOF
statement   → let_stmt | if_stmt | while_stmt | fn_stmt | return_stmt | expr_stmt
let_stmt    → "let" IDENTIFIER "=" expression NEWLINE
            | "let" IDENTIFIER "[" expression "]" "=" expression NEWLINE
if_stmt     → "if" expression "do" block ("elif" expression "do" block)* ("else" "do" block)? "end"
while_stmt  → "while" expression "do" block "end"
fn_stmt     → "fn" IDENTIFIER "(" params? ")" "do" block "end"
return_stmt → "return" expression? NEWLINE
expr_stmt   → expression NEWLINE
block       → statement*
expression  → (Pratt-parsed with precedence climbing)
```

## References

- [Crafting Interpreters](https://craftinginterpreters.com/) by Robert Nystrom
- [Pratt Parsing](https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html) by matklad
- [Structure and Interpretation of Computer Programs](https://mitpress.mit.edu/sites/default/files/sicp/index.html)
