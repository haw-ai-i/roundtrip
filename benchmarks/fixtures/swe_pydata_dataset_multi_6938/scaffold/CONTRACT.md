# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `xarray/core/dataset.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DataVariables`
- `Dataset`
- `as_dataset`

## `xarray/core/variable.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BASIC_INDEXING_TYPES`
- `Coordinate`
- `IndexVariable`
- `MissingDimensionsError`
- `NON_NUMPY_SUPPORTED_ARRAY_TYPES`
- `Variable`
- `as_compatible_data`
- `as_variable`
- `broadcast_variables`
- `calculate_dimensions`
- `concat`

Implement them to satisfy the specification. Do not write tests.
