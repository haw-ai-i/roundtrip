# Implementation target
Write three modules in `sympy/sets/`. Other modules import these public names, so they
MUST exist with these exact names:

- `contains.py` must define the public class `Contains`.
- `setexpr.py` must define the public class `SetExpr` and the public functions
  `set_function`, `set_div`, and `set_mul`.
- `powerset.py` must define the public class `PowerSet`.

Implement them to satisfy the specification. Do not write tests.
