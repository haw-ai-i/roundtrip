# `saferepr` Module

The `saferepr` module provides tools for safely generating string representations of Python objects. It is designed to be resilient to exceptions and to handle objects with long representations gracefully.

## Key Features

- **Robust Exception Handling**: The module catches exceptions that occur within `__repr__` methods, preventing them from crashing the application. Instead of an exception, it returns a formatted string indicating that an error occurred.
- **Output Size Limiting**: Representations are truncated to a specified maximum length, which is crucial for logging and display systems that cannot handle arbitrarily long strings.
- **Safe Pretty-Printing**: A safe version of `pprint.pformat` is included, which also benefits from the same exception-handling mechanism.

## Core Components

### `saferepr(obj: Any, maxsize: int = 240) -> str`

This is the main function of the module. It returns a size-limited, safe representation of the given object.

- **`obj`**: The object to represent.
- **`maxsize`**: The maximum size of the output string.

If the object's `__repr__` method raises an exception, `saferepr` will catch it and return a string with exception information.

**Source Reference**: `src/saferepr.py`

### `safeformat(obj: Any) -> str`

This function provides a "pretty-printed" string representation of an object, similar to `pprint.pformat`. It is also designed to be safe and will not raise exceptions if an object's `__repr__` method fails.

**Source Reference**: `src/saferepr.py`

### `SafeRepr(reprlib.Repr)`

This class is a subclass of `reprlib.Repr` and forms the core of the `saferepr` implementation. It can be instantiated directly for more control over the representation process.

- **`__init__(self, maxsize: int)`**: Initializes the `SafeRepr` instance with a specific `maxsize`.
- **`repr(self, x: Any) -> str`**: The method that performs the safe representation.

**Source Reference**: `src/saferepr.py`

## Usage Examples

### Basic Usage

```python
from saferepr import saferepr

# Simple objects
saferepr(1)  # Returns '1'
saferepr([1, 2, 3])  # Returns '[1, 2, 3]'

# Long strings
long_string = "a" * 1000
saferepr(long_string, maxsize=50)
# Returns a truncated string with ellipsis in the middle
```

### Handling Broken `__repr__`

```python
from saferepr import saferepr

class Broken:
    def __repr__(self):
        raise ValueError("This is a broken repr")

b = Broken()
representation = saferepr(b)
# representation will be a string like:
# '<[ValueError('This is a broken repr') raised in repr()] Broken object at 0x...>'
```

This ensures that even when dealing with potentially unstable objects, the program can continue to operate without interruption.

## Testing

The module's behavior is thoroughly tested in `tests/test_saferepr.py`. The tests cover various scenarios, including:
- Simple data types.
- Size limiting (`maxsize`).
- Various exceptions raised from `__repr__`.
- `BaseException` handling to ensure pytest outcomes are not suppressed.

By examining the tests, you can gain a deeper understanding of the module's capabilities and edge-case handling.
