# Implementation target
Write the module at `xarray/core/computation.py`.

## `xarray/core/computation.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `SLICE_NONE`
- `_UFuncSignature`
- `apply_array_ufunc`
- `apply_dataarray_vfunc`
- `apply_dataset_vfunc`
- `apply_dict_of_variables_vfunc`
- `apply_groupby_func`
- `apply_ufunc`
- `apply_variable_ufunc`
- `assert_and_return_exact_match`
- `broadcast_compat_data`
- `build_output_coords_and_indexes`
- `collect_dict_values`
- `corr`
- `cov`
- `cross`
- `dot`
- `join_dict_keys`
- `ordered_set_intersection`
- `ordered_set_union`
- `polyval`
- `result_name`
- `unified_dim_sizes`
- `unify_chunks`
- `where`

Implement them to satisfy the specification. Do not write tests.
