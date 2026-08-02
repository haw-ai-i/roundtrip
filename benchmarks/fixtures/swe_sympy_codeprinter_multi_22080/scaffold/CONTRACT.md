# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `sympy/printing/codeprinter.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AssignmentError`
- `CodePrinter`
- `ccode`
- `cxxcode`
- `fcode`
- `print_ccode`
- `print_fcode`
- `requires`

## `sympy/printing/precedence.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `PRECEDENCE`
- `PRECEDENCE_FUNCTIONS`
- `PRECEDENCE_TRADITIONAL`
- `PRECEDENCE_VALUES`
- `precedence`
- `precedence_Float`
- `precedence_FracElement`
- `precedence_Integer`
- `precedence_Mul`
- `precedence_PolyElement`
- `precedence_Rational`
- `precedence_UnevaluatedExpr`
- `precedence_traditional`

Implement them to satisfy the specification. Do not write tests.
