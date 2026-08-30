## xarray/core/dataset.py
The specification has been written to `/tmp/omp_desc_k8ka4ytr/xarray_spec.md`. It covers all 5085 lines of `xarray/core/dataset.py`, including:

- **All imports** (exact module paths, aliases, TYPE_CHECKING block)
- **Constants & globals** (`_DATETIMEINDEX_COMPONENTS`)
- **6 module-level functions** with full implementation logic (`_get_virtual_variable`, `calculate_dimensions`, `merge_indexes`, `split_indexes`, `_assert_empty`, `as_dataset`)
- **2 helper classes** (`DataVariables`, `_LocIndexer`)
- **The `Dataset` class** — all 80+ methods and properties, including:
  - Initialization and internal construction (`__init__`, `_construct_direct`, `_replace`, etc.)
  - Dask integration (10 dask protocol methods)
  - Indexing (`isel`, `sel`, `head`, `tail`, `thin`)
  - Alignment & reshaping (`reindex`, `interp`, `rename`, `swap_dims`, `stack`/`unstack`, `expand_dims`)
  - Arithmetic operations (unary/binary/inplace ops, `_calculate_binary_op`)
  - Reductions (`reduce`, `apply`, `quantile`, `rank`, `diff`)
  - I/O & serialization (`to_netcdf`, `to_zarr`, `to_dataframe`, `from_dict`, etc.)
  - Coordinate management (`set_coords`, `reset_coords`, `set_index`, `reset_index`)
  - Filtering (`filter_by_attrs`)
- **Module footer** (`ops.inject_all_ops_and_reduce_methods` call)

## xarray/core/variable.py
I've now read all 2246 lines of the file in full. Let me write the complete specification:

---

# Module Specification: `xarray/core/variable.py` (2246 lines)

## 1. Module-Level Preamble

### Imports

```python
import functools
import itertools
from collections import OrderedDict, defaultdict
from datetime import timedelta
from distutils.version import LooseVersion
from typing import Any, Hashable, Mapping, Union

import numpy as np
import pandas as pd
import xarray as xr  # only for Dataset and DataArray

from . import arithmetic, common, dtypes, duck_array_ops, indexing, nputils, ops, utils
from .indexing import (BasicIndexer, OuterIndexer, PandasIndexAdapter, VectorizedIndexer, as_indexable)
from .npcompat import IS_NEP18_ACTIVE
from .options import _get_keep_attrs
from .pycompat import dask_array_type, integer_types
from .utils import (OrderedSet, decode_numpy_dict_values, either_dict_or_kwargs, ensure_us_time_resolution)

try:
    import dask.array as da
except ImportError:
    pass
```

### Constants & Globals

- **`NON_NUMPY_SUPPORTED_ARRAY_TYPES`** — tuple: `(indexing.ExplicitlyIndexed, pd.Index)` concatenated with `dask_array_type`. Defines array types that are natively supported without conversion to numpy.
- **`BASIC_INDEXING_TYPES`** — tuple: `integer_types + (slice,)`. Valid basic indexing element types (integers and slices only).

### Exception Class

- **`MissingDimensionsError(ValueError)`** — inherits from `ValueError` for backward compatibility; raised when dimension names cannot be safely inferred.

---

## 2. Module-Level Functions

### `as_variable(obj, name=None) -> Union[Variable, IndexVariable]`

Converts an object into a Variable or IndexVariable:
1. If `obj` is a `DataArray`, extract its `.variable` attribute.
2. If already a `Variable`, return `obj.copy(deep=False)` (shallow copy).
3. If `obj` is a tuple, attempt `Variable(*obj)`, catching `(TypeError, ValueError)` and re-raising with a descriptive message about the failed conversion.
4. If `utils.is_scalar(obj)`, wrap as `Variable([], obj)`.
5. If `obj` is a `pd.Index` or `IndexVariable` with `obj.name is not None`, create `Variable(obj.name, obj)`.
6. If `obj` is a `set` or `dict`, raise `TypeError`.
7. If `name is not None` and none of the above matched: call `as_compatible_data(obj)`; if result has `ndim != 1`, raise `MissingDimensionsError`; otherwise create `Variable(name, data, fastpath=True)`.
8. If none of the above branches applied, raise `TypeError`.
9. After conversion, if `name is not None` and `name in obj.dims`: validate that `obj.ndim == 1` (else raise `MissingDimensionsError`), then convert via `obj.to_index_variable()`.

Returns the resulting Variable or IndexVariable.

### `_maybe_wrap_data(data)`

Wraps `pd.Index` objects into `PandasIndexAdapter`; returns all other data unchanged.

### `_possibly_convert_objects(values)`

Converts arrays of Python `datetime.datetime` and `datetime.timedelta` objects to numpy datetime64/timedelta64 via: `np.asarray(pd.Series(values.ravel())).reshape(values.shape)`.

### `as_compatible_data(data, fastpath=False)`

Prepares data for storage in a Variable:
1. If `fastpath=True` and `getattr(data, "ndim", 0) > 0`, return `_maybe_wrap_data(data)`.
2. If `data` is a `Variable`, return `data.data`.
3. If `data` is an instance of `NON_NUMPY_SUPPORTED_ARRAY_TYPES`, return `_maybe_wrap_data(data)`.
4. If `data` is a tuple, convert via `utils.to_0d_object_array(data)`.
5. If `data` is a `pd.Timestamp`, convert to `np.datetime64(data.value, "ns")`.
6. If `data` is a `timedelta`, convert to `np.timedelta64(getattr(data, "value", data), "ns")`.
7. Unwrap self-described arrays: `data = getattr(data, "values", data)`.
8. If `data` is a `np.ma.MaskedArray`: if any mask values are True, promote dtype via `dtypes.maybe_promote`, convert to the promoted dtype, and set masked positions to the fill value; otherwise just call `np.asarray(data)`.
9. If not already an ndarray but has `__array_function__` and `IS_NEP18_ACTIVE` is False, raise `TypeError` with instructions about NEP18.
10. Convert via `np.asarray(data)`.
11. If the result is an ndarray: if dtype kind is `"O"`, call `_possibly_convert_objects`; if `"M"` (datetime), convert to `"datetime64[ns]"`; if `"m"` (timedelta), convert to `"timedelta64[ns]"`.
12. Return `_maybe_wrap_data(data)`.

### `_as_array_or_item(data)`

Converts data to numpy array via `np.asarray(data)`. If the result is 0-dimensional and has dtype kind `"M"` or `"m"`, explicitly converts it to nanosecond precision (`np.datetime64(data, "ns")` or `np.timedelta64(data, "ns")`). This works around known numpy bugs with 0D datetime/timedelta arrays.

### `_unified_dims(variables)`

Validates and unifies dimensions across multiple variables:
1. Iterates over each variable; if a variable has duplicate dimension names (len(set) < len), raise `ValueError`.
2. For each `(dim, size)` pair, records the first-seen size for that dimension name. If a later variable has a different size for the same dimension, raise `ValueError` about mismatched broadcast lengths.
3. Returns an `OrderedDict` mapping dimension names to their unified sizes.

### `_broadcast_compat_variables(*variables)`

Creates broadcast-compatible variables with matching dimensions: calls `_unified_dims(variables)` to get unified dims, then returns a tuple where each variable is passed through `var.set_dims(dims)` if its dims differ from the unified dims, otherwise returned unchanged.

### `broadcast_variables(*variables)`

Like `_broadcast_compat_variables` but ensures full broadcast (all dimensions have matching sizes). Returns variables with expanded dimensions via `set_dims`.

### `_broadcast_compat_data(self, other)`

Broadcasts data for binary operations:
1. If `other` has all of `["dims", "data", "shape", "encoding"]`, treat it as a Variable-like object: call `_broadcast_compat_variables(self, other)`, extract `.data` from both, and return `(self_data, other_data, dims)` where `dims = new_self.dims`.
2. Otherwise (numpy array or similar), use raw data (`self.data`, `other`) with `dims = self.dims`.

### `concat(variables, dim="concat_dim", positions=None, shortcut=False)`

Module-level concat dispatcher: converts `variables` to a list; if all are `IndexVariable`, delegates to `IndexVariable.concat`; otherwise delegates to `Variable.concat`.

### `assert_unique_multiindex_level_names(variables)`

Validates uniqueness of MultiIndex level names across variables (a dict mapping var_name → Variable):
1. For each variable whose `_data` is a `PandasIndexAdapter`, extract its `level_names` via `to_index_variable().level_names`.
2. Collect all level names into a defaultdict list and a flat set.
3. If any level name appears in more than one variable, raise `ValueError` listing the conflicts.
4. Also check for conflicts between level names and dimension names (GH:2299); if any dimension name matches an existing level name across all variables, raise `ValueError`.

---

## 3. Class: `Variable(common.AbstractArray, arithmetic.SupportsArithmetic, utils.NdimSizeLenMixin)`

### Attributes & Slots

- **`__slots__ = ("_dims", "_data", "_attrs", "_encoding")`** — four private instance attributes.
- `_dims`: tuple of dimension name strings (set in `__init__`).
- `_data`: the underlying data array (wrapped via `as_compatible_data`).
- `_attrs`: `OrderedDict[Any, Any]` or `None` (lazily initialized).
- `_encoding`: dict or `None` (lazily initialized to `{}`).

### `__init__(self, dims, data, attrs=None, encoding=None, fastpath=False)`

1. Set `self._data = as_compatible_data(data, fastpath=fastpath)`.
2. Set `self._dims = self._parse_dimensions(dims)`.
3. Initialize `_attrs` and `_encoding` to `None`, then assign them from parameters if not None (using the setters which validate).

### Properties

- **`dtype`** → `self._data.dtype`
- **`shape`** → `self._data.shape`
- **`nbytes`** → `self.size * self.dtype.itemsize`
- **`_in_memory`** → bool: True if `_data` is an instance of `(np.ndarray, np.number, PandasIndexAdapter)` or a `MemoryCachedArray` wrapping a `NumpyIndexingAdapter`.
- **`dims`** (getter) → `self._dims`; (setter) → calls `self._parse_dimensions(value)`.
- **`data`** (getter): if `_data` has `__array_function__` or is a dask array, return `_data` directly; else return `self.values`. (Setter): validate shape match via `as_compatible_data`, then assign.
- **`values`** (getter) → `_as_array_or_item(self._data)`; (setter) → delegates to `self.data = values`.
- **`attrs`** (getter): lazily initializes `_attrs` to `OrderedDict()` if None, returns it; (setter) → `self._attrs = OrderedDict(value)`.
- **`encoding`** (getter): lazily initializes `_encoding` to `{}` if None; (setter) → validates castable to dict.
- **`chunks`** → `getattr(self._data, "chunks", None)` or the dask array's chunk info.
- **`T`** → `self.transpose()` (property alias).

### Instance Methods

#### `_parse_dimensions(dims)`

If `dims` is a string, wrap in tuple `(dims,)`. Validate that `len(dims) == self.ndim`; raise `ValueError` otherwise. Returns the tuple.

#### `_item_key_to_tuple(key)`

If key is dict-like, return `tuple(key.get(dim, slice(None)) for dim in self.dims)`. Otherwise return key as-is.

#### `_broadcast_indexes(key)` → `(dims, indexer, new_order)`

Prepares an indexing key:
1. Convert via `_item_key_to_tuple`, then expand scalars via `indexing.expanded_indexer(key, self.ndim)`.
2. Convert scalar Variables (0-dim) to integers via `.data.item()`, and 0-d numpy arrays via `.item()`.
3. If all elements are `BASIC_INDEXING_TYPES` → delegate to `_broadcast_indexes_basic(key)`.
4. Validate indexers via `_validate_indexers(key)`.
5. If no element is a Variable (all unlabeled), delegate to `_broadcast_indexes_outer(key)`.
6. Check if all Variables in key are 1-dim with unique dimension names and no duplicates → `_broadcast_indexes_outer(key)`.
7. Otherwise, delegate to `_broadcast_indexes_vectorized(key)`.

#### `_validate_indexers(key)`

For each `(dim, k)` pair: if `k` is not a basic indexing type and not a Variable, convert to numpy array; if ndim > 1, raise `IndexError`; for boolean dtype (`"b"`): validate size matches dimension length, ndim == 1, and dims match the target dimension.

#### `_broadcast_indexes_basic(key)` → `(dims, BasicIndexer(key), None)`

Returns dimensions for non-integer key elements wrapped in a `BasicIndexer`.

#### `_broadcast_indexes_outer(key)` → `(dims, OuterIndexer(tuple(new_key)), None)`

For each key element: if Variable, extract `.data`; otherwise convert to numpy array. For boolean arrays, replace with `np.nonzero(k)`. Returns dims (from Variable dims or self dims for non-integer keys).

#### `_broadcast_indexes_vectorized(key)` → `(out_dims, VectorizedIndexer(tuple(out_key)), new_order)`

1. Build a list of variables from key elements: slices are kept as-is; Variables stay as-is; others converted via `as_variable(value, name=dim)`. Boolean indices resolved via `_nonzero()`.
2. Collect all variable dims into an OrderedSet for output dimensions.
3. For slice elements where the dimension is shared with a variable, convert to a range Variable; otherwise keep as slices in a separate list `(i, value)`.
4. Broadcast variables together via `_broadcast_compat_variables`; on mismatch, raise `IndexError("Dimensions of indexers mismatch: ...")`.
5. Build output key from variable `.data` values plus slice entries at their original positions.
6. Compute `new_order`: axes to move (those not in slice_positions).

#### `__getitem__(self, key)` → Variable

Calls `_broadcast_indexes(key)`, applies indexer via `as_indexable(self._data)[indexer]`, moves axes if needed via `duck_array_ops.moveaxis`, returns `_finalize_indexing_result(dims, data)`.

#### `_finalize_indexing_result(self, dims, data)` → Variable

Returns `type(self)(dims, data, self._attrs, self._encoding, fastpath=True)`. Overridden by IndexVariable.

#### `_getitem_with_mask(self, key, fill_value=dtypes.NA)` → Variable

Like `__getitem__` but remaps -1 indices to a fill value:
1. Resolve fill_value via `dtypes.get_fill_value(self.dtype)` if NA.
2. Get dims/indexer/new_order from `_broadcast_indexes`.
3. If array has elements: for dask data, use `indexing.posify_mask_indexer(indexer)`; otherwise use indexer as-is. Apply indexer to get data, create mask via `indexing.create_mask(indexer, self.shape, data)`, then apply `duck_array_ops.where(mask, fill_value, data)`.
4. If empty array: create mask directly (no indexing), broadcast fill_value to mask shape.
5. Move axes if needed; return `_finalize_indexing_result`.

#### `__setitem__(self, key, value)`

1. Get dims/indexer/new_order from `_broadcast_indexes`.
2. If value is not a Variable: convert via `as_compatible_data`; validate ndim ≤ len(dims) (else raise `ValueError`); if 0-dim, wrap as `Variable((), value)`; else wrap as `Variable(dims[-value.ndim:], value)`.
3. Broadcast value to target dims via `value.set_dims(dims).data`.
4. If new_order exists: move axes on the value array.
5. Apply assignment: `as_indexable(self._data)[index_tuple] = value`.

#### `copy(self, deep=True, data=None)` → Variable

1. If `data is None`: use `self._data`; if it's a `MemoryCachedArray`, create a new one wrapping the same inner array (don't share cache); if deep and (`__array_function__` or dask), call `.copy()`; else if not PandasIndexAdapter, convert to numpy via `np.array(data)`.
2. If `data is not None`: validate shape match (else raise `ValueError`), then `as_compatible_data(data)`.
3. Return `type(self)(self.dims, data, self._attrs, self._encoding, fastpath=True)`.

#### `__copy__(self)` → `self.copy(deep=False)`
#### `__deepcopy__(self, memo=None)` → `self.copy(deep=True)`
#### `__hash__ = None` (mutable objects are unhashable)

#### `load(self, **kwargs)` → self

If `_data` is a dask array: replace with `as_compatible_data(self._data.compute(**kwargs))`. Else if not having `__array_function__`, convert via `np.asarray(self._data)`. Returns self.

#### `compute(self, **kwargs)` → Variable

Creates shallow copy (`self.copy(deep=False)`) and calls `.load(**kwargs)` on it. Original unchanged.

#### Dask Integration Methods

- **`__dask_graph__(self)`** → returns `_data.__dask_graph__()` if dask array, else `None`.
- **`__dask_keys__(self)`** → delegates to `_data.__dask_keys__()`.
- **`__dask_layers__(self)`** → delegates to `_data.__dask_layers__()`.
- **`__dask_optimize__`** (property) → delegates to `_data.__dask_optimize__`.
- **`__dask_scheduler__`** (property) → delegates to `_data.__dask_scheduler__`.
- **`__dask_postcompute__(self)`** → returns `(self._dask_finalize, (array_func, array_args, self._dims, self._attrs, self._encoding))` where `array_func, array_args = _data.__dask_postcompute__()`.
- **`__dask_postpersist__(self)`** → same structure with `_data.__dask_postpersist__()`.
- **`_dask_finalize(results, array_func, array_args, dims, attrs, encoding)`** (static): if results is dict (persist case), filter to only keys matching `array_args[0]`; call `array_func(results, *array_args)`; return `Variable(dims, data, attrs=attrs, encoding=encoding)`.

#### `to_base_variable(self)` → Variable

Returns `Variable(self.dims, self._data, self._attrs, encoding=self._encoding, fastpath=True)`. Aliased as `to_variable`.

#### `to_index_variable(self)` → IndexVariable

Returns `IndexVariable(self.dims, self._data, self._attrs, encoding=self._encoding, fastpath=True)`. Aliased as `to_coord`.

#### `to_index(self)` → pd.Index

Calls `self.to_index_variable().to_index()`.

#### `to_dict(self, data=True)` → dict

Returns `{"dims": self.dims, "attrs": decode_numpy_dict_values(self.attrs)}`. If `data=True`, adds `"data"` key with `ensure_us_time_resolution(self.values).tolist()`; else adds `"dtype"` (str of dtype) and `"shape"`.

#### `chunk(self, chunks=None, name=None, lock=False)` → Variable

Converts data to dask array:
1. If `chunks` is dict-like, convert dimension names to axis indices.
2. If `chunks is None`, use existing chunks or full shape.
3. If `_data` is already a dask array: call `.rechunk(chunks)`.
4. Else if `_data` is `ExplicitlyIndex`: wrap in `ImplicitToExplicitIndexingAdapter(data, OuterIndexer)`; for dask ≥ 2.0.0, pass `meta=np.ndarray`; else empty kwargs.
5. If chunks is dict-like, convert to tuple of chunk sizes.
6. Call `da.from_array(data, chunks, name=name, lock=lock, **kwargs)`.
7. Return new Variable with dask data.

#### `isel(self, indexers=None, drop=False, **indexers_kwargs)` → Variable

1. Normalize via `either_dict_or_kwargs(indexers, indexers_kwargs, "isel")`.
2. Validate all indexer keys exist in `self.dims` (else raise `ValueError`).
3. Build full slice key: `[slice(None)] * self.ndim`, replacing entries for indexed dimensions.
4. Return `self[tuple(key)]`.

#### `squeeze(self, dim=None)` → Variable

Calls `common.get_squeeze_dims(self, dim)`, then `self.isel({d: 0 for d in dims})`.

#### `_shift_one_dim(self, dim, count, fill_value=dtypes.NA)` → Variable

1. Get axis via `get_axis_num(dim)`.
2. Compute keep slice: positive count → `slice(None, -count)`, negative → `slice(-count, None)`, zero → `slice(None)`.
3. Trim data along axis using the keep slice.
4. Resolve fill_value: if NA, promote dtype via `dtypes.maybe_promote(self.dtype)`; else use self.dtype.
5. Compute filler shape: copy of self.shape with axis dimension set to `min(abs(count), shape[axis])`.
6. Create filler array: for dask, use `da.full` with matching chunks; else `np.full`.
7. Concatenate `[filler, trimmed]` (positive count) or `[trimmed, filler]` (negative).
8. For dask data, rechunk to match original chunk sizes.
9. Return new Variable.

#### `shift(self, shifts=None, fill_value=dtypes.NA, **shifts_kwargs)` → Variable

Normalizes via `either_dict_or_kwargs`, then iteratively applies `_shift_one_dim` for each `(dim, count)`.

#### `pad_with_fill_value(self, pad_widths=None, fill_value=dtypes.NA, **pad_widths_kwargs)` → Variable

1. Normalize via `either_dict_or_kwargs`; resolve dtype/fill_value as in shift.
2. For dask data: for each dimension with padding, create before/after filler arrays with matching chunks; concatenate `[before, original, after]` (skipping zero-width fillers).
3. For numpy: use `np.pad(self.data.astype(dtype, copy=False), pads, mode="constant", constant_values=fill_value)`.
4. Return new Variable.

#### `_roll_one_dim(self, dim, count)` → Variable

1. Get axis; normalize count modulo dimension size.
2. If count == 0: single slice `[slice(None)]`; else two slices `[-count:, : -count]`.
3. Index data for each slice, concatenate along axis via `duck_array_ops.concatenate`.
4. Rechunk dask data to original chunks.
5. Return new Variable.

#### `roll(self, shifts=None, **shifts_kwargs)` → Variable

Normalizes via `either_dict_or_kwargs`, iteratively applies `_roll_one_dim` for each dimension.

#### `transpose(self, *dims) -> Variable`

If no dims provided, reverse: `self.dims[::-1]`. Get axis indices via `get_axis_num(dims)`. If fewer than 2 dims, return shallow copy. Otherwise call `as_indexable(self._data).transpose(axes)` and return new Variable with reordered dims/attrs/encoding.

#### `set_dims(self, dims, shape=None)` → Variable

1. Normalize string to list; if dict-like dims and no shape provided, use `dims.values()` as shape.
2. Validate that existing dims are a subset of new dims (else raise `ValueError`).
3. Build expanded dims: new dims first, then original dims.
4. If dims unchanged: use raw data. If shape provided: broadcast via `duck_array_ops.broadcast_to(self.data, tmp_shape)`. Else: add leading axes via `(None,) * delta` indexing.
5. Create Variable with expanded dims/data/attrs/encoding; transpose to requested order.

#### `_stack_once(self, dims, new_dim)` → Variable

1. Validate all `dims` are in `self.dims`; validate `new_dim` not already a dimension name; if no dims to stack, return shallow copy.
2. Compute dim order: non-stacked dims + stacked dims. Transpose to that order.
3. Reshape data: original shape up to non-stacked count + `(-1,)`. New dims: same prefix + `(new_dim,)`.
4. Return new Variable.

#### `stack(self, dimensions=None, **dimensions_kwargs)` → Variable

Normalizes via `either_dict_or_kwargs`, iteratively applies `_stack_once` for each `(new_dim, dims)`.

#### `_unstack_once(self, dims, old_dim)` → Variable

1. Extract new dim names and sizes; validate `old_dim` exists; validate no name collision with existing dims; validate product of new sizes equals old dimension size (else raise `ValueError`).
2. Transpose: non-old dims + `[old_dim]`. Reshape data to `(non_old_count, ...) + new_sizes`. New dims: same prefix + new names.
3. Return new Variable.

#### `unstack(self, dimensions=None, **dimensions_kwargs)` → Variable

Normalizes via `either_dict_or_kwargs`, iteratively applies `_unstack_once` for each `(old_dim, dims)`.

#### `fillna(self, value)` → Variable

Delegates to `ops.fillna(self, value)`.

#### `where(self, cond, other=dtypes.NA)` → Variable

Delegates to `ops.where_method(self, cond, other)`.

#### `reduce(self, func, dim=None, axis=None, keep_attrs=None, keepdims=False, allow_lazy=False, **kwargs)` → Variable

1. If `dim is common.ALL_DIMS`, set `dim = None`. Validate not both `dim` and `axis` provided (else raise `ValueError`).
2. Convert `dim` to axis via `get_axis_num(dim)`. Select input data: `self.data` if lazy, else `self.values`.
3. Apply func with or without axis argument.
4. Determine output dims: if result shape equals self.shape, keep all dims; else compute removed axes and either keep them as size-1 (via `np.newaxis` slicing) when `keepdims=True`, or filter them out.
5. Resolve `keep_attrs` via `_get_keep_attrs(default=False)`; set attrs accordingly.
6. Return new Variable with computed dims/data/attrs.

#### `concat(cls, variables, dim="concat_dim", positions=None, shortcut=False)` → Variable (classmethod)

1. If `dim` is not a string, extract its single dimension name: `dim, = dim.dims`.
2. Convert to list; get first variable.
3. Extract arrays `[v.data for v in variables]`.
4. If `dim in first_var.dims`: concatenate along that axis via `duck_array_ops.concatenate`; if positions provided, apply inverse permutation via `nputils.inverse_permutation(np.concatenate(positions))` and take along axis.
5. Else: stack along new axis 0 via `duck_array_ops.stack`.
6. Copy attrs/encoding from first variable; if not shortcut, validate all variables have same dims (else raise `ValueError`) and remove incompatible attribute items.
7. Return `cls(dims, data, attrs, encoding)`.

#### `equals(self, other, equiv=duck_array_ops.array_equiv)` → bool

Get `other.variable` if available; compare dims; check identity (`self._data is other._data`) or equivalence via `equiv(self.data, other.data)`. Catch `(TypeError, AttributeError)` → False.

#### `broadcast_equals(self, other, equiv=duck_array_ops.array_equiv)` → bool

Broadcast both variables together; call `self.equals(other, equiv=equiv)`. On error, return False.

#### `identical(self, other)` → bool

Check `utils.dict_equiv(self.attrs, other.attrs)` and `self.equals(other)`. Catch errors → False.

#### `no_conflicts(self, other)` → bool

Calls `broadcast_equals` with `equiv=duck_array_ops.array_notnull_equiv`.

#### `quantile(self, q, dim=None, interpolation="linear")` → Variable

1. If data is dask array, raise `TypeError`.
2. Convert `q` to float64 numpy array.
3. Compute output dims: start with self.dims; remove specified dims (scalar or list); if no dim specified, result has no dims; if q is multi-element, prepend `"quantile"` dimension.
4. Call `np.nanpercentile(self.data, q * 100.0, axis=axis, interpolation=interpolation)`.
5. Return new Variable with computed dims and data.

#### `rank(self, dim, pct=False)` → Variable

1. Import bottleneck; if dask array, raise `TypeError`; if not numpy ndarray, raise `TypeError`.
2. Get axis; select func: `bn.nanrankdata` for float dtype, else `bn.rankdata`.
3. Apply func along axis; if pct, divide by count of non-NaN values per element.
4. Return new Variable with same dims and ranked data.

#### `rolling_window(self, dim, window, window_dim, center=False, fill_value=dtypes.NA)` → Variable

1. Resolve dtype/fill_value as needed; cast array if promoted.
2. New dims: `self.dims + (window_dim,)`.
3. Call `duck_array_ops.rolling_window(array, axis=self.get_axis_num(dim), window=window, center=center, fill_value=fill_value)`.
4. Return new Variable with new dims and result data.

#### `coarsen(self, windows, func, boundary="exact", side="left")` → Variable

1. Filter windows to only those in self.dims; if empty, return copy.
2. Call `_coarsen_reshape(windows, boundary, side)` to get reshaped data and axis tuple.
3. If func is a string, resolve via `getattr(duck_array_ops, name)`, else raise `NameError`.
4. Apply func on reshaped data along computed axes; return new Variable with original dims and result data.

#### `_coarsen_reshape(self, windows, boundary, side)` → `(reshaped_data, tuple_axes)`

1. Normalize boundary/side to dicts keyed by dimension names.
2. Filter to only dimensions in windows.
3. For each (dim, window): validate `window > 0`; handle boundary: `"exact"` raises if size not divisible; `"trim"` slices from left or right; `"pad"` calls `pad_with_fill_value`.
4. Build new shape: for coarsened dims, split into `(size // window, window)`; for others, keep original size. Track axes for the reshape.
5. Return `variable.data.reshape(shape), tuple(axes)`.

#### `_to_numeric(self, offset=None, datetime_unit=None, dtype=float)` → Variable

Calls `duck_array_ops.datetime_to_numeric(self.data, offset, datetime_unit, dtype)`; returns new Variable with same dims and attrs.

### Properties (continued)

- **`real`** → `type(self)(self.dims, self.data.real, self._attrs)`
- **`imag`** → `type(self)(self.dims, self.data.imag, self._attrs)`
- **`__array_wrap__(self, obj, context=None)`** → `Variable(self.dims, obj)`

### Static Operation Helpers (injected by ops module)

- **`_unary_op(f)`**: wraps a numpy ufunc; calls it on `self.data`; returns `self.__array_wrap__(result)` with numpy errstate suppressed.
- **`_binary_op(f, reflexive=False, **ignored_kwargs)`**: handles broadcasting between self and other (Variable-like or array); applies f (or reversed for reflexive); returns new Variable with broadcast dims and attrs.
- **`_inplace_binary_op(f)`**: like binary but mutates `self.values`; validates dims unchanged; raises TypeError for Dataset operands.

After class definition: `ops.inject_all_ops_and_reduce_methods(Variable)` injects arithmetic operators (`__add__`, `__sub__`, etc.) and reduction methods (`sum`, `mean`, `min`, `max`, etc.).

---

## 4. Class: `IndexVariable(Variable)`

### Attributes & Slots

- **`__slots__ = ()`** — no additional slots; inherits Variable's four slots.
- Always 1-dimensional (enforced in `__init__`).
- `_data` is always a `PandasIndexAdapter`.

### `__init__(self, dims, data, attrs=None, encoding=None, fastpath=False)`

Calls `super().__init__()`. Validates `ndim == 1` (else raise `ValueError`). If `_data` is not already a `PandasIndexAdapter`, wraps it: `self._data = PandasIndexAdapter(self._data)`.

### Instance Methods

#### `load(self)` → self

No-op; data is always loaded. Returns self.

#### `data` (setter, decorated with `@Variable.data.setter`)

Calls parent setter, then ensures `_data` is a `PandasIndexAdapter`.

#### `chunk(self, chunks=None, name=None, lock=False)` → Variable

Dummy: returns `self.copy(deep=False)`. Does not actually chunk.

#### `_finalize_indexing_result(self, dims, data)` → Union[Variable, IndexVariable]

If result is 1-dim, return `type(self)(dims, data, self._attrs, self._encoding, fastpath=True)`; else fall back to plain `Variable`.

#### `__setitem__(self, key, value)` → raises TypeError

Always raises `TypeError("%s values cannot be modified" % type(self).__name__)`.

#### `concat(cls, variables, dim="concat_dim", positions=None, shortcut=False)` → IndexVariable (classmethod)

1. Normalize dim; convert to list.
2. Validate all inputs are IndexVariable (else raise TypeError).
3. Extract pandas indexes: `[v._data.array for v in variables]`.
4. If empty, data = `[]`; else call `indexes[0].append(indexes[1:])` and apply inverse permutation if positions provided.
5. Copy attrs from first variable; validate dims consistency (if not shortcut); remove incompatible items.
6. Return `cls(first_var.dims, data, attrs)`.

#### `copy(self, deep=True, data=None)` → IndexVariable

If `data is None`: use `self._data.copy(deep=deep)` (PandasIndexAdapter's copy). If `data` provided: validate shape, convert via `as_compatible_data`. Return new IndexVariable.

#### `equals(self, other, equiv=None)` → bool

If `equiv is not None`, delegate to parent. Else: compare dims and call `_data_equals(other)`. Catch errors → False.

#### `_data_equals(self, other)` → bool

Calls `self.to_index().equals(other.to_index())` (native pandas Index equality).

#### `to_index_variable(self)` → self

Returns self (already an IndexVariable). Aliased as `to_coord`.

#### `to_index(self)` → pd.Index

1. Assert 1-dim.
2. Extract underlying index: `self._data.array`.
3. If MultiIndex: set default names for unnamed levels (`"{dim}_level_{i}"`); else set name to `self.name`.
4. Return the named pandas Index.

#### `level_names` (property) → tuple or None

Returns `self.to_index().names` if MultiIndex, else `None`.

#### `get_level_variable(self, level)` → IndexVariable

If no MultiIndex, raise ValueError; else return new IndexVariable with `index.get_level_values(level)`.

### Properties

- **`name`** (getter) → `self.dims[0]`; (setter) → raises `AttributeError("cannot modify name of IndexVariable in-place")`.

---

## 5. Backwards Compatibility Alias

```python
Coordinate = utils.alias(IndexVariable, "Coordinate")
```

Creates an alias `Coordinate` pointing to `IndexVariable`, with the string `"Coordinate"` as the display name.