# Implementation target
Write the module at `xarray/core/variable.py`.

## `xarray/core/variable.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BASIC_INDEXING_TYPES`
- `Coordinate`
- `IndexVariable`
- `MissingDimensionsError`
- `NON_NUMPY_SUPPORTED_ARRAY_TYPES`
- `Variable`
- `VariableType`
- `as_compatible_data`
- `as_variable`
- `assert_unique_multiindex_level_names`
- `broadcast_variables`
- `concat`

Implement them to satisfy the specification. Do not write tests.
