# Implementation target
Write the module at `xarray/core/common.py`.

## `xarray/core/common.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ALL_DIMS`
- `AbstractArray`
- `AttrAccessMixin`
- `C`
- `DTypeMaybeMapping`
- `DataWithCoords`
- `ImplementsArrayReduce`
- `ImplementsDatasetReduce`
- `T`
- `contains_cftime_datetimes`
- `full_like`
- `get_chunksizes`
- `get_squeeze_dims`
- `is_np_datetime_like`
- `is_np_timedelta_like`
- `ones_like`
- `zeros_like`

Implement them to satisfy the specification. Do not write tests.
