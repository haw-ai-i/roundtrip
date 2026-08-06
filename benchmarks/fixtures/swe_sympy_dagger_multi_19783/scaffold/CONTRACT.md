# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `sympy/physics/quantum/dagger.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Dagger`

## `sympy/physics/quantum/operator.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DifferentialOperator`
- `HermitianOperator`
- `IdentityOperator`
- `Operator`
- `OuterProduct`
- `UnitaryOperator`

Implement them to satisfy the specification. Do not write tests.
