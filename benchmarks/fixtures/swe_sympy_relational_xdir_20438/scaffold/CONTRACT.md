# Implementation target
Write the following 3 modules. They live in the same package and may import each other.

## `sympy/core/relational.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Eq`
- `Equality`
- `Ge`
- `GreaterThan`
- `Gt`
- `Le`
- `LessThan`
- `Lt`
- `Ne`
- `Rel`
- `Relational`
- `StrictGreaterThan`
- `StrictLessThan`
- `Unequality`
- `_Inequality`
- `_canonical`
- `is_eq`
- `is_ge`
- `is_gt`
- `is_le`
- `is_lt`
- `is_neq`

## `sympy/sets/handlers/comparison.py`
Other modules import these names from it, so they MUST exist with these exact names:

## `sympy/sets/handlers/issubset.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `is_subset_sets`

Implement them to satisfy the specification. Do not write tests.
