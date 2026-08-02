# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `sympy/matrices/matrices.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DeferredVector`
- `MatrixBase`
- `MatrixCalculus`
- `MatrixDeprecated`
- `MatrixDeterminant`
- `MatrixEigen`
- `MatrixReductions`
- `MatrixSubspaces`
- `_find_reasonable_pivot_naive`
- `a2idx`
- `classof`

## `sympy/utilities/randtest.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `_randint`
- `_randrange`
- `random_complex_number`
- `test_derivative_numerically`
- `verify_numerically`

Implement them to satisfy the specification. Do not write tests.
