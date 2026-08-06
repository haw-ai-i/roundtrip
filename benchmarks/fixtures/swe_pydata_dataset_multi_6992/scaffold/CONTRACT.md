# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `xarray/core/dataset.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DataVariables`
- `Dataset`
- `as_dataset`

## `xarray/core/indexes.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Index`
- `IndexVars`
- `Indexes`
- `PandasIndex`
- `PandasMultiIndex`
- `T_PandasOrXarrayIndex`
- `_asarray_tuplesafe`
- `as_scalar`
- `assert_no_index_corrupted`
- `create_default_index_implicit`
- `default_indexes`
- `filter_indexes_from_coords`
- `get_indexer_nd`
- `indexes_all_equal`
- `indexes_equal`
- `isel_indexes`
- `normalize_label`
- `remove_unused_levels_categories`
- `roll_indexes`

Implement them to satisfy the specification. Do not write tests.
