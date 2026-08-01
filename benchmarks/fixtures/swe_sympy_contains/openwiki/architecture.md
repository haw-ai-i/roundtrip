# Architecture

This document provides a more detailed look at the components of the `swe_sympy_contains` test repository.

## Testing Harness

The testing harness is designed to provide a standardized way to evaluate the implementation of the `Contains` class.

### `run_oracle.py`

This script is the core of the testing process. It is responsible for:

-   **Environment Setup**: It ensures that the testing environment is in a pristine state by copying a clean version of the target file (`sympy/sets/contains.py`) before each run.
-   **Test Execution**: It uses the `subprocess` module to invoke `pytest` on the oracle test file.
-   **Configuration**: It relies on `/oracle_env.json` for paths and `/coundetrip.yaml` for overall test structure.

### `coundetrip.yaml`

This file defines the structure of the test for the Coundetrip benchmark runner. It specifies:

-   `name`: The name of the test.
-   `test_command`: The command to run the test (`python run_oracle.py`).
-   `source_paths`: The path to the source code being tested.
-   `scaffold_paths`: The path to the scaffold files, including the contract.
-   `test_paths`: The paths to the test-related files.

## Source Code: `sympy/sets/contains.py`

The file under test is `/sympy/sets/contains.py`. It defines the `Contains` class, which is a `BooleanFunction` in `sympy`.

### `Contains` Class

The `Contains` class is used to represent the concept of an element belonging to a set in a symbolic way.

-   **`eval(cls, x, s)`**: This class method is the main entry point for evaluation. It checks if `x` is in the set `s` by calling `s.contains(x)`. It can return `True`, `False`, or remain unevaluated if the membership cannot be determined at the time of the call.
-   **`binary_symbols`**: This property is used to extract the binary symbols from the arguments of the `Contains` expression.
-   **`as_set()`**: This method returns the set part of the `Contains` expression.

## Contract: `scaffold/CONTRACT.md`

This file defines the public API that must be implemented in `sympy/sets/contains.py`. For this test, the contract is simple: the module must provide a `Contains` class. This ensures that any generated code adheres to the expected interface.
