# Implementation target
Write the module at `xarray/core/combine.py`.

## `xarray/core/combine.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `_check_shape_tile_ids`
- `_combine_all_along_first_dim`
- `_combine_nd`
- `_infer_concat_order_from_coords`
- `_infer_concat_order_from_positions`
- `_new_tile_id`
- `auto_combine`
- `combine_by_coords`
- `combine_nested`
- `vars_as_keys`

Implement them to satisfy the specification. Do not write tests.
