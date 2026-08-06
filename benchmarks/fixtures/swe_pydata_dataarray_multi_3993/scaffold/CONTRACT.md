# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `xarray/core/dataarray.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DataArray`

## `xarray/core/dataset.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DataVariables`
- `Dataset`
- `as_dataset`
- `calculate_dimensions`
- `merge_indexes`
- `split_indexes`

Implement them to satisfy the specification. Do not write tests.
