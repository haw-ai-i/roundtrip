# Implementation target
Write the module at `xarray/core/merge.py`.

## `xarray/core/merge.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `MergeElement`
- `MergeError`
- `PANDAS_TYPES`
- `assert_valid_explicit_coords`
- `broadcast_dimension_size`
- `coerce_pandas_values`
- `collect_from_coordinates`
- `collect_variables_and_indexes`
- `dataset_merge_method`
- `dataset_update_method`
- `determine_coords`
- `merge`
- `merge_attrs`
- `merge_collected`
- `merge_coordinates_without_align`
- `merge_coords`
- `merge_core`
- `merge_data_and_coords`
- `unique_variable`

Implement them to satisfy the specification. Do not write tests.
