## xarray/core/dataset.py
I see the spec file exists but only covers ~376 lines (~4% of the 8882-line source). I need to read all remaining critical sections and build a comprehensive specification. Let me use parallel reads to cover the remaining sections efficiently.

## xarray/core/variable.py
Now I have read every section of this ~3083-line file. Let me write the complete natural-language specification.

---

# Module-Level Preamble

## Imports (lines 1-78)

```python
from __future__ import annotations
import copy, itertools, math, numbers, warnings
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Callable, Hashable, Iterable, Literal, Mapping, Sequence

import numpy as np
import pandas as pd
from packaging.version import Version
import xarray as xr  # only for Dataset and DataArray

from . import common, dtypes, duck_array_ops, indexing, nputils, ops, utils
from .arithmetic import VariableArithmetic
from .common import AbstractArray
from .indexing import BasicIndexer, OuterIndexer, PandasIndexingAdapter, VectorizedIndexer, as_indexable
from .npcompat import QUANTILE_METHODS, ArrayLike
from .options import OPTIONS, _get_keep_attrs
from .pycompat import DuckArrayModule, cupy_array_type, dask_array_type, integer_types, is_duck_dask_array, sparse_array_type
from .utils import Frozen, NdimSizeLenMixin, OrderedSet, _default, decode_numpy_dict_values, drop_dims_from_indexers, either_dict_or_kwargs, ensure_us_time_resolution, infix_dims, is_duck_array, maybe_coerce_to_str

if TYPE_CHECKING:
    from .types import ErrorOptionsWithWarn, PadModeOptions, PadReflectOptions, T_Variable
```

## Constants & Globals (lines 60-69)

- `NON_NUMPY_SUPPORTED_ARRAY_TYPES`: tuple = `(indexing.ExplicitlyIndexed, pd.Index)` + `dask_array_type` + `cupy_array_type`. Defines array types that are supported but not numpy ndarrays.
- `BASIC_INDEXING_TYPES`: tuple = `integer_types + (slice,)`. Valid basic indexing element types.

## Exception Class (lines 80-85)

- **MissingDimensionsError(ValueError)**: Error raised when a dimension name cannot be safely inferred for a variable. Inherits from ValueError for backward compatibility.

---

# Module-Level Functions

## `as_variable(obj, name=None) -> Variable | IndexVariable` (lines 87-169)

Converts an object into a Variable or IndexVariable.

**Logic:**
1. If `obj` is a `DataArray`, extract its `.variable` attribute.
2. If already a `Variable`, return a shallow copy (`copy(deep=False)`).
3. If `obj` is a tuple, attempt `Variable(*obj)`. On failure, raise the same exception type with a formatted message about the expected `(dims, data[, attrs, encoding])` form. If the second element of the tuple is a `DataArray`, raise `TypeError` immediately (ambiguous).
4. If `obj` is scalar (`utils.is_scalar(obj)`), create `Variable([], obj)`.
5. If `obj` is a `pd.Index` or `IndexVariable` with `.name is not None`, create `Variable(obj.name, obj)`.
6. If `obj` is a `set` or `dict`, raise `TypeError`.
7. If `name is not None`: convert data via `as_compatible_data(obj)`. If the result has ndim != 1, raise `MissingDimensionsError`. Otherwise create `Variable(name, data, fastpath=True)`.
8. Else: raise `TypeError` about missing explicit dimensions.

After conversion, if `name is not None and name in obj.dims`: validate that `obj.ndim == 1`, else raise `MissingDimensionsError`. Convert to IndexVariable via `obj.to_index_variable()`. Return the result.

## `_maybe_wrap_data(data)` (lines 172-182)

Wraps `pd.Index` objects into `PandasIndexingAdapter`. Leaves everything else unchanged. Used for numpy arrays, NumpyArrayAdapter, and LazilyIndexedArray pass through unmodified.

## `_possibly_convert_objects(values)` (lines 185-191)

Converts arrays of `datetime.datetime` / `datetime.timedelta` objects into `datetime64`/`timedelta64` per pandas convention. Flattens via `.ravel()`, converts through `pd.Series`, then reshapes back to original shape via `np.asarray(pd.Series(values.ravel())).reshape(values.shape)`.

## `as_compatible_data(data, fastpath=False)` (lines 194-250)

Prepares and wraps data for a Variable.

**Logic:**
1. If `fastpath=True` and `data.ndim > 0`, return `_maybe_wrap_data(data)`.
2. If `data` is `Variable` or `DataArray`, return `data.data`.
3. If `data` is in `NON_NUMPY_SUPPORTED_ARRAY_TYPES`, return `_maybe_wrap_data(data)`.
4. If `data` is a tuple, convert via `utils.to_0d_object_array(data)`.
5. If `pd.Timestamp`, convert to `np.datetime64(data.value, "ns")`.
6. If `timedelta`, convert to `np.timedelta64(getattr(data, "value", data), "ns")`.
7. If `pd.Series`/`pd.Index`/`pd.DataFrame`, extract `.values`.
8. If `np.ma.MaskedArray`: if any mask values exist, promote dtype via `dtypes.maybe_promote()`, convert to the promoted dtype, and fill masked positions with the promoted fill value; otherwise just `np.asarray(data)`.
9. If data has `__array_function__` or `__array_namespace__` but is not an ndarray, return it as-is (duck array passthrough).
10. Convert via `np.asarray(data)`.
11. If result dtype kind is in `"OMm"` (object, bytes, datetime), apply `_possibly_convert_objects()`.
12. Return `_maybe_wrap_data(data)`.

## `_as_array_or_item(data)` (lines 253-273)

Converts data to numpy array via `np.asarray(data)`. For 0-dimensional arrays with dtype kind `"M"` (datetime64), converts to `np.datetime64(data, "ns")`; for `"m"` (timedelta64), converts to `np.timedelta64(data, "ns")`. This works around numpy issues with 0d datetime/timedelta arrays.

## `_unified_dims(variables)` (lines 2942-2960)

Validates and unifies dimensions across a collection of variables. Iterates each variable's `(dim, size)` pairs into `all_dims` dict. Raises `ValueError` if any dimension has duplicate names within a single variable or if sizes conflict between variables. Returns the unified `dict[Hashable, int]`.

## `_broadcast_compat_variables(*variables) -> tuple[Variable, ...]` (lines 2963-2970)

Creates broadcast-compatible variables with matching dimensions using `_unified_dims()`, then calls `var.set_dims(dims)` for each variable whose dims differ from the unified set. Returns a tuple of adjusted variables.

## `broadcast_variables(*variables: Variable) -> tuple[Variable, ...]` (lines 2973-2987)

Like `_broadcast_compat_variables()` but returns fully broadcasted variables with matching dimensions and data views. Uses `_unified_dims()`, then calls `var.set_dims(dims_map)` for each variable whose dims differ from the unified tuple.

## `_broadcast_compat_data(self, other)` (lines 2990-3002)

Broadcasts two operands together. If `other` has attributes `dims`, `data`, `shape`, `encoding`, uses `_broadcast_compat_variables()` to get compatible variables and returns `(self_data, other_data, dims)`. Otherwise falls back to numpy broadcasting: returns `(self.data, other, self.dims)`.

## `concat(variables, dim="concat_dim", positions=None, shortcut=False, combine_attrs="override")` (lines 3005-3057)

Module-level wrapper that dispatches to either `IndexVariable.concat()` or `Variable.concat()`. If all variables are `IndexVariable`, delegates; otherwise calls `Variable.concat()`.

## `calculate_dimensions(variables: Mapping[Any, Variable]) -> dict[Hashable, int]` (lines 3060-3083)

Computes dimension sizes from a mapping of variable names to Variables. Tracks scalar variables (those with no dims). Raises `ValueError` if a dimension already exists as a scalar variable or if conflicting sizes are found for the same dimension across different variables. Returns `dict[Hashable, int]`.

---

# Variable Class (lines 276-2707)

## Header & Slots

```python
class Variable(AbstractArray, NdimSizeLenMixin, VariableArithmetic):
    __slots__ = ("_dims", "_data", "_attrs", "_encoding")
```

**Inheritance:** `AbstractArray` (provides array protocol), `NdimSizeLenMixin` (provides `ndim`, `size`, `__len__`), `VariableArithmetic` (provides operator overloads).

## Attributes

- `_dims`: tuple of Hashable — dimension names
- `_data`: wrapped data array (numpy, dask, sparse, PandasIndexingAdapter, etc.)
- `_attrs`: dict[Hashable, Any] or None — local attributes
- `_encoding`: dict or None — encoding metadata for serialization

## `__init__(self, dims, data, attrs=None, encoding=None, fastpath=False)` (lines 299-326)

1. Sets `self._data = as_compatible_data(data, fastpath=fastpath)`.
2. Sets `self._dims = self._parse_dimensions(dims)`.
3. Initializes `_attrs` and `_encoding` to None.
4. If `attrs is not None`, assigns via `self.attrs = attrs` (which copies the dict).
5. If `encoding is not None`, assigns via `self.encoding = encoding`.

## Properties

### `dtype` → dtype (line 328-330)
Returns `self._data.dtype`.

### `shape` → tuple[int, ...] (lines 332-334)
Returns `self._data.shape`.

### `nbytes` → int (lines 336-344)
If `self.data` has `.nbytes`, returns it; otherwise returns `self.size * self.dtype.itemsize`.

### `_in_memory` → bool (lines 346-353)
True if `_data` is an `np.ndarray`, `np.number`, `PandasIndexingAdapter`, or a `MemoryCachedArray` wrapping a `NumpyIndexingAdapter`.

### `data` / `data=` (lines 355-370)
Getter: returns `self._data` if it's a duck array, else returns `self.values`. Setter: converts via `as_compatible_data()`, validates shape matches, assigns to `_data`.

### `values` / `values=` (lines 530-537)
Getter: returns `_as_array_or_item(self._data)` as numpy ndarray. Setter: delegates to `self.data = values`.

### `dims` / `dims=` (lines 572-580)
Getter: returns `self._dims`. Setter: calls `self._parse_dimensions(value)`.

### `attrs` → dict[Hashable, Any] (lines 871-880)
Lazy-initialized dict. Returns `_attrs`, creating `{}` if None. Setter copies the mapping via `dict(value)`.

### `encoding` → dict (lines 882-894)
Lazy-initialized dict. Returns `_encoding`, creating `{}` if None. Setter converts to dict, raising ValueError on failure.

### `chunks` → tuple[tuple[int,...],...] | None (lines 1005-1017)
Returns `getattr(self._data, "chunks", None)`.

### `chunksizes` → Frozen[Hashable, tuple[int,...]] (lines 1019-1038)
If `_data` has chunks, returns a `Frozen` mapping of dimension names to chunk shapes. Otherwise empty dict.

## Methods

### `astype(self: T_Variable, dtype, *, order=None, casting=None, subok=None, copy=None, keep_attrs=True) -> T_Variable` (lines 372-445)
Creates a copy with data cast to the specified type. Filters out None-valued kwargs (`order`, `casting`, `subok`, `copy`). Calls `apply_ufunc(duck_array_ops.astype, self, dtype, kwargs=filtered_kwargs, keep_attrs=keep_attrs, dask="allowed")`.

### `load(self, **kwargs) -> Variable` (lines 447-468)
Triggers loading of deferred data. If `_data` is a duck dask array, computes it via `.compute(**kwargs)` and re-wraps. If not a duck array, converts via `np.asarray()`. Returns self.

### `compute(self, **kwargs) -> Variable` (lines 470-489)
Creates a shallow copy then calls `load(**kwargs)` on it. Original is unaltered.

### Dask integration methods (lines 491-528)
- `__dask_tokenize__()`: returns `normalize_token((type(self), self._dims, self.data, self._attrs))`.
- `__dask_graph__()`: returns `_data.__dask_graph__()` if dask array, else None.
- `__dask_keys__()`: delegates to `_data.__dask_keys__()`.
- `__dask_layers__()`: delegates to `_data.__dask_layers__()`.
- `__dask_optimize__` / `__dask_scheduler__`: property delegations.
- `__dask_postcompute__()`: returns `(self._dask_finalize, (array_func,) + array_args)`.
- `__dask_postpersist__()`: same pattern with postpersist.
- `_dask_finalize(results, array_func, *args, **kwargs)`: creates new Variable from finalized data.

### `to_base_variable(self)` → Variable (lines 539-543)
Returns a base `Variable` with the same dims, data, attrs, and encoding. Alias: `to_variable`.

### `to_index_variable(self)` → IndexVariable (lines 547-551)
Returns an `IndexVariable` with same content. Alias: `to_coord`.

### `to_index(self)` → pd.Index (line 555-557)
Converts to IndexVariable then calls its `.to_index()`.

### `to_dict(self, data=True, encoding=False) -> dict` (lines 559-570)
Returns a dictionary representation: `{"dims": ..., "attrs": ...}`. If `data=True`, adds `"data"` as the list of values with US time resolution; else adds `"dtype"` and `"shape"`. If `encoding=True`, adds `"encoding"`.

### `_parse_dimensions(dims)` → tuple[Hashable,...] (lines 581-590)
Converts string dims to single-element tuple. Validates length matches `self.ndim`. Raises ValueError on mismatch.

### `_item_key_to_tuple(key)` (lines 592-596)
If key is dict-like, converts to a tuple of `(key.get(dim, slice(None)) for dim in self.dims)`. Otherwise returns key as-is.

### `_broadcast_indexes(key)` → (dims, indexer, new_order) (lines 598-654)
Prepares an indexing key:
1. Converts via `_item_key_to_tuple()`, then `indexing.expanded_indexer(key, self.ndim)`.
2. Converts 0-d Variable keys to integers via `.data.item()`.
3. Converts 0-d numpy arrays to integers via `.item()`.
4. If all elements are `BASIC_INDEXING_TYPES`: delegates to `_broadcast_indexes_basic()`.
5. Validates indexers via `_validate_indexers()`.
6. If no key is a Variable: delegates to `_broadcast_indexes_outer()`.
7. Checks if all Variable keys are 1-d with unique dimension names; if so, uses `_broadcast_indexes_outer()`.
8. Otherwise delegates to `_broadcast_indexes_vectorized()`.

### `_broadcast_indexes_basic(key)` → (dims, BasicIndexer, None) (lines 656-660)
Dims = non-integer elements of key mapped to corresponding dimension names. Returns `(dims, BasicIndexer(key), None)`.

### `_validate_indexers(key)` (lines 662-691)
For each (dim, k): if not a basic type and not a Variable, convert to numpy array. Raises `IndexError` if: multi-dimensional unlabeled arrays; boolean array size doesn't match dimension length; boolean indexing is >1-d; boolean indexer dims don't match target dimension.

### `_broadcast_indexes_outer(key)` → (dims, OuterIndexer, None) (lines 693-713)
Dims extracted from Variable keys' first dim or original dims for non-integer entries. Converts Variable keys to `.data`, converts non-basic types to numpy arrays (empty arrays cast to int, boolean arrays converted via `np.nonzero()`). Returns `(dims, OuterIndexer(tuple(new_key)), None)`.

### `_nonzero(self)` → tuple[Variable,...] (lines 715-720)
Equivalent of `np.nonzero(self.data)`, returns a tuple of Variables, one per dimension.

### `_broadcast_indexes_vectorized(key)` → (out_dims, VectorizedIndexer, new_order) (lines 722-776)
Complex vectorized indexing:
1. Iterates key elements; slices add their dim to `out_dims_set`. Non-slice values become Variables via `as_variable(value, name=dim)`, with boolean keys converted via `_nonzero()`.
2. Tracks which dims appear in variable indexers (`variable_dims`).
3. For slice entries where the dim is shared with a variable indexer, converts the slice to an arange Variable; otherwise records as `(position, slice)` tuple.
4. Broadcasts all variables together via `_broadcast_compat_variables()`. On mismatch, raises `IndexError`.
5. Builds output key from variable data, tracks slice positions and new axis order.
6. Returns `(out_dims, VectorizedIndexer(tuple(out_key)), new_order)`.

### `__getitem__(self: T_Variable, key) -> T_Variable` (lines 778-795)
xarray-style orthogonal indexing. Gets `(dims, indexer, new_order)` from `_broadcast_indexes()`, applies to `as_indexable(self._data)[indexer]`, applies `np.moveaxis()` if `new_order` is set, then calls `_finalize_indexing_result(dims, data)`.

### `_finalize_indexing_result(self: T_Variable, dims, data) -> T_Variable` (lines 797-799)
Returns `self._replace(dims=dims, data=data)`. Overridden in IndexVariable.

### `_getitem_with_mask(self, key, fill_value=dtypes.NA)` (lines 801-839)
Indexes with -1 remapped to fill value. For dask arrays, uses `posify_mask_indexer()`. Creates mask via `indexing.create_mask()`, then applies `duck_array_ops.where(np.logical_not(mask), data, fill_value)`. Handles empty array case by building mask directly. Applies moveaxis if needed.

### `__setitem__(self, key, value)` (lines 841-869)
xarray-style orthogonal setitem. Broadcasts key via `_broadcast_indexes()`. If value is not Variable, converts to compatible data and wraps as Variable with appropriate dims. Broadcasts value to target dims via `.set_dims(dims).data`. Applies moveaxis if `new_order` set. Assigns to `as_indexable(self._data)[index_tuple] = value`.

### `copy(self, deep=True, data=None) -> Variable` (lines 896-974)
If `data is None`: uses `_data`, handling `MemoryCachedArray` specially (creates new wrapper). If `deep=True`, applies `copy.deepcopy()`. If `data` provided: converts via `as_compatible_data()`, validates shape match. Returns `self._replace(data=data)`.

### `__copy__(self)` → Variable (line 993-994)
Returns `self.copy(deep=False)`.

### `__deepcopy__(self, memo=None)` → Variable (lines 996-999)
Returns `self.copy(deep=True)`.

### `__hash__ = None` (line 1003)
Variables are not hashable.

### `chunk(self, chunks={}, name=None, lock=False, inline_array=False, **chunks_kwargs) -> Variable` (lines 1042-1143)
Coerces data to dask array with given chunks. Handles None warning for deprecated chunks value. Normalizes via `either_dict_or_kwargs()`. Converts dimension-name keys to axis numbers. If already dask: calls `.rechunk(chunks)`. If not dask and is ExplicitlyIndexed, wraps in `ImplicitToExplicitIndexingAdapter` with `OuterIndexer`, sets `meta=np.ndarray`. Converts dict chunks to tuple form. Calls `da.from_array(data, chunks, ...)`. Returns `_replace(data=data)`.

### `to_numpy(self) -> np.ndarray` (lines 1145-1163)
Coerces data: if dask → `.compute()`, if cupy → `.get()`, if pint → `.magnitude`, if sparse → `.todense()`, then `np.asarray(data)`.

### `as_numpy(self: T_Variable) -> T_Variable` (line 1165-1167)
Returns `_replace(data=self.to_numpy())`.

### `_as_sparse(self, sparse_format=_default, fill_value=dtypes.NA)` → Variable (lines 1169-1189)
Converts to sparse array backend. Determines dtype/fill_value via `dtypes.maybe_promote()`. Looks up `sparse.as_{format}` function. Calls it on `self.data.astype(dtype)`, returns `_replace(data=data)`.

### `_to_dense(self)` → Variable (lines 1191-1197)
If `_data` has `.todense()`, returns `_replace(data=_data.todense())`; else shallow copy.

### `isel(self: T_Variable, indexers=None, missing_dims="raise", **indexers_kwargs) -> T_Variable` (lines 1199-1232)
Dimension-based integer/slice/array indexing. Normalizes via `either_dict_or_kwargs()`, drops unknown dims per `missing_dims`, builds tuple key `(indexers.get(dim, slice(None)) for dim in self.dims)`, returns `self[key]`.

### `squeeze(self, dim=None)` → Variable (lines 1234-1255)
Gets squeeze dims via `common.get_squeeze_dims(self, dim)`, returns `self.isel({d: 0 for d in dims})`.

### `_shift_one_dim(self, dim, count, fill_value=dtypes.NA)` → Variable (lines 1257-1291)
Shifts one dimension. Computes keep slice based on sign of count. Trims data, determines dtype/fill via `maybe_promote()`, computes pad widths, applies `np.pad(..., mode="constant")`. Rechunks dask output to match original chunks. Returns `_replace(data=data)`.

### `shift(self, shifts=None, fill_value=dtypes.NA, **shifts_kwargs)` → Variable (lines 1293-1318)
Iterates over shift dict, applying `_shift_one_dim()` sequentially for each dimension.

### `_pad_options_dim_to_index(pad_option, fill_with_shape=False)` (lines 1320-1330)
Helper: if `fill_with_shape`, returns `(n,n)` for missing dims; else `(0,0)`. For present dims, uses the provided value.

### `pad(self, pad_width=None, mode="constant", stat_length=None, constant_values=None, end_values=None, reflect_type=None, **pad_width_kwargs)` → Variable (lines 1332-1429)
Pads data via `np.pad()`. Default for "constant" mode uses `maybe_promote()` dtype/fill_value. Normalizes stat_length/constant_values/end_values from dict to index form. Handles dask stat_length bug workaround. Converts integer pad_widths to `(v,v)` tuples. Builds kwargs dict with only non-None values. Calls `np.pad(self.data.astype(dtype, copy=False), ...)`. Returns `type(self)(self.dims, array)`.

### `_roll_one_dim(self, dim, count)` → Variable (lines 1431-1450)
Rolls one dimension by slicing at `-count` and concatenating. Rechunks dask output to match original chunks. Returns `_replace(data=data)`.

### `roll(self, shifts=None, **shifts_kwargs)` → Variable (lines 1452-1476)
Iterates over shift dict, applying `_roll_one_dim()` sequentially.

### `transpose(self, *dims, missing_dims="raise") -> Variable` (lines 1478-1524)
Reverses dims if none given; otherwise uses `infix_dims()`. Returns shallow copy if <2 dims or no change. Otherwise gets axis numbers via `get_axis_num(dims)`, transposes data, returns `_replace(dims=dims, data=data)`.

### `T` → Variable (lines 1526-1528)
Returns `self.transpose()`.

### `set_dims(self, dims, shape=None)` → Variable (lines 1530-1577)
Adds new dimensions. Validates superset constraint. Computes expanded dims order. If no expansion needed, uses data as-is; if shape provided, broadcasts to target shape; else prepends None axes. Creates new Variable then transposes to requested dim order.

### `_stack_once(self, dims, new_dim)` → Variable (lines 1579-1601)
Stacks multiple dimensions into one. Validates inputs. Transposes so stacked dims are last. Reshapes data with `-1` for the new dimension. Returns new Variable.

### `stack(self, dimensions=None, **dimensions_kwargs)` → Variable (lines 1603-1633)
Iterates over dimension mappings, applying `_stack_once()` sequentially.

### `_unstack_once_full(self, dims: Mapping[Any,int], old_dim)` → Variable (lines 1635-1670)
Unstacks one dimension into multiple new dimensions given a mapping of `{new_name: size}`. Validates product of sizes equals old dim size. Transposes, reshapes, returns new Variable.

### `_unstack_once(self, index: pd.MultiIndex, dim, fill_value=dtypes.NA, sparse=False)` → Variable (lines 1672-1738)
Unstacks using a pandas MultiIndex. Transposes to put target dim last. For sparse mode, creates COO array from index codes; for dense mode, creates full array and assigns via fancy indexing with `indexer`. Returns `_replace(dims=new_dims, data=data)`.

### `unstack(self, dimensions=None, **dimensions_kwargs)` → Variable (lines 1740-1776)
Iterates over dimension mappings, applying `_unstack_once_full()` sequentially.

### `fillna(self, value)` → Variable (line 1778-1779)
Delegates to `ops.fillna(self, value)`.

### `where(self, cond, other=dtypes.NA)` → Variable (lines 1781-1782)
Delegates to `ops.where_method(self, cond, other)`.

### `clip(self, min=None, max=None)` → Variable (lines 1784-1797)
Calls `apply_ufunc(np.clip, self, min, max, dask="allowed")`.

### `reduce(self, func, dim=None, axis=None, keep_attrs=None, keepdims=False, **kwargs) -> Variable` (lines 1799-1885)
Reduces by applying `func` along dimension(s). Validates mutual exclusivity of `dim` and `axis`. Converts `dim` to axis numbers. Suppresses "Mean of empty slice" warning. Calls `func(self.data, axis=axis, **kwargs)` or `func(self.data, **kwargs)`. Computes output dims based on whether result shape matches input (no reduction). Handles keepdims by inserting newaxes. Applies attrs per `keep_attrs` / `_get_keep_attrs()`.

### `concat(cls, variables, dim="concat_dim", positions=None, shortcut=False, combine_attrs="override") -> Variable` (lines 1887-1974)
Class method. Converts non-string dim to its single dimension name. Iterates variables list. If `dim in first_var.dims`: concatenates along that axis; else stacks at axis=0 with new dim prepended. Handles positions via inverse permutation reordering. Merges attrs, copies encoding from first variable. Validates dimension consistency unless shortcut=True.

### `equals(self, other, equiv=duck_array_ops.array_equiv)` → bool (lines 1976-1992)
Compares dims and data. Extracts `.variable` from DataArray/Dataset if needed. Checks identity of `_data` or element-wise equivalence via `equiv()`. Catches TypeError/AttributeError, returns False.

### `broadcast_equals(self, other, equiv=duck_array_ops.array_equiv)` → bool (lines 1994-2005)
Broadcasts both variables together, then calls `equals()`. Returns False on ValueError/AttributeError.

### `identical(self, other, equiv=duck_array_ops.array_equiv)` → bool (lines 2007-2014)
Like equals but also checks attribute equality via `utils.dict_equiv()`. Catches TypeError/AttributeError.

### `no_conflicts(self, other, equiv=duck_array_ops.array_notnull_equiv)` → bool (line 2016-2023)
Broadcast-equals with NaN-tolerant equivalence function.

### `quantile(self, q, dim=None, method="linear", keep_attrs=None, skipna=None, interpolation=None) -> Variable` (lines 2025-2163)
Computes quantiles along dimension(s). Handles deprecated `interpolation` parameter rename with warning and validation. Chooses `np.nanquantile` or `np.quantile` based on skipna/dtype. Wraps function to move quantile axis to end for apply_ufunc. Calls `apply_ufunc()` with appropriate output sizes. Transposes result, squeezes scalar q dimension if needed, restores attrs if keep_attrs.

### `rank(self, dim, pct=False)` → Variable (lines 2165-2216)
Ranks data along a dimension using bottleneck library. Requires `OPTIONS["use_bottleneck"]`. Raises TypeError for dask or non-numpy arrays. Uses `bn.nanrankdata` for float dtypes, `bn.rankdata` otherwise. If pct=True, divides by count of non-NaN values per axis.

### `rolling_window(self, dim, window, window_dim, center=False, fill_value=dtypes.NA)` → Variable (lines 2218-2328)
Creates rolling windows along dimension(s). Handles scalar/multi-dim cases with validation. Computes pad widths based on center flag. Pads data via `.pad()`, then applies `duck_array_ops.sliding_window_view()` to create the windowed output with new dimension appended.

### `coarsen(self, windows, func, boundary="exact", side="left", keep_attrs=None, **kwargs)` → Variable (lines 2330-2356)
Applies reduction over coarsened windows. Filters windows to present dims. Calls `coarsen_reshape()` for reshaping, then applies the function over the resulting axes.

### `coarsen_reshape(self, windows, boundary, side)` → (reshaped_data, axes) (lines 2358-2423)
Trims/pads variables to window boundaries ("exact", "trim", or "pad" modes). Reshapes data by splitting each coarsened dimension into `(size/window, window)` pairs. Returns reshaped array and axis tuple for reduction.

### `isnull(self, keep_attrs=None)` → Variable (lines 2425-2457)
Element-wise null check via `apply_ufunc(duck_array_ops.isnull, self, ...)`.

### `notnull(self, keep_attrs=None)` → Variable (lines 2459-2491)
Element-wise non-null check via `apply_ufunc(duck_array_ops.notnull, self, ...)`.

### `real` / `imag` properties (lines 2493-2499)
Return `_replace(data=self.data.real)` and `_replace(data=self.data.imag)` respectively.

### `__array_wrap__(self, obj, context=None)` → Variable (line 2501-2502)
Wraps numpy array result: returns `Variable(self.dims, obj)`.

### `_unary_op(self, f, *args, **kwargs)` (lines 2504-2512)
Applies unary function to data. Gets keep_attrs from kwargs or `_get_keep_attrs(default=True)`. Suppresses numpy errors via `np.errstate(all="ignore")`. Wraps result and restores attrs if needed.

### `_binary_op(self, other, f, reflexive=False)` (lines 2514-2528)
Binary operation with broadcasting. Returns NotImplemented for DataArray/Dataset. Uses `_broadcast_compat_data()` to get broadcasted data and dims. Applies function `f` (or reversed if reflexive). Creates new Variable with result and attrs per `_get_keep_attrs(default=False)`.

### `_inplace_binary_op(self, other, f)` (lines 2530-2538)
In-place binary operation. Validates dims don't change for in-place ops. Broadcasts data, applies `f`, assigns to `self.values`. Returns self.

### `_to_numeric(self, offset=None, datetime_unit=None, dtype=float)` → Variable (lines 2540-2547)
Converts datetime arrays to numeric via `duck_array_ops.datetime_to_numeric()`. Returns new Variable with same dims and attrs.

### `_unravel_argminmax(self, argminmax, dim, axis, keep_attrs, skipna)` → Variable | dict[Hashable, Variable] (lines 2549-2617)
Handles argmin/argmax over one or more dimensions. Warns on deprecated no-dim/no-axis usage. For single dimension: calls `reduce()` with the argmin/argmax function. For multiple dimensions: stacks into a new dim, reduces along last axis, unravels indices via `duck_array_ops.unravel_index()`, returns dict of Variables keyed by original dimension names.

### `argmin(self, dim=None, axis=None, keep_attrs=None, skipna=None)` → Variable | dict[Hashable, Variable] (lines 2619-2662)
Delegates to `_unravel_argminmax("argmin", ...)`.

### `argmax(self, dim=None, axis=None, keep_attrs=None, skipna=None)` → Variable | dict[Hashable, Variable] (lines 2664-2707)
Delegates to `_unravel_argminmax("argmax", ...)`.

---

# IndexVariable Class (lines 2710-2935)

## Header & Slots

```python
class IndexVariable(Variable):
    __slots__ = ()
```

**Inheritance:** `Variable` — a specialized Variable that wraps pandas.Index data. Always 1-dimensional, immutable data stored as PandasIndexingAdapter.

## Attributes (inherited from Variable)

Same `_dims`, `_data`, `_attrs`, `_encoding` slots but with stricter constraints: always 1-d, data is always `PandasIndexingAdapter`.

## `__init__(self, dims, data, attrs=None, encoding=None, fastpath=False)` (lines 2723-2730)
Calls super().__init__(). Validates ndim == 1. Wraps `_data` in `PandasIndexingAdapter` if not already one.

## `__dask_tokenize__(self)` (lines 2732-2736)
Uses `normalize_token((type(self), self._dims, self._data.array, self._attrs))` — accesses the underlying pandas Index directly without converting to numpy.

## `load(self)` → Variable (line 2738-2740)
No-op: data is already loaded. Returns self.

## `data` / `values=` setters (lines 2743-2755)
Both raise ValueError — IndexVariable data is immutable. Directs user to use DataArray/Dataset assign_coords methods.

## `chunk(self, chunks={}, name=None, lock=False, inline_array=False)` → Variable (lines 2757-2759)
No-op: returns shallow copy. Chunking doesn't apply to index variables.

## `_as_sparse()` / `_to_dense()` (lines 2761-2767)
Both no-ops returning `self.copy(deep=False)`.

## `_finalize_indexing_result(self, dims, data)` → Variable (lines 2769-2774)
If result is multi-dimensional (`ndim != 1`), returns a base `Variable`; otherwise returns via `_replace()`. This ensures IndexVariable stays 1-d.

## `__setitem__(self, key, value)` (line 2776-2777)
Always raises TypeError — values cannot be modified.

## `concat(cls, variables, dim="concat_dim", positions=None, shortcut=False, combine_attrs="override")` → IndexVariable (lines 2779-2829)
Specialized for IndexVariable: validates all inputs are IndexVariable. Extracts underlying pandas Index objects via `.data.array`, appends them together. Handles positions reordering. Applies `maybe_coerce_to_str()`. Merges attrs, returns new IndexVariable.

## `copy(self, deep=True, data=None)` → Variable (lines 2831-2865)
If data is None: copies `_data` via `.copy(deep=deep)` (deep parameter ignored since pandas.Index is immutable). If data provided: validates shape, converts via `as_compatible_data()`. Returns `_replace(data=data)`.

## `equals(self, other, equiv=None)` → bool (lines 2867-2877)
If equiv is specified, delegates to super(). Otherwise uses native pandas Index equality via `_data_equals(other)`, which calls `self.to_index().equals(other.to_index())`.

## `_data_equals(self, other)` → bool (line 2879-2880)
Compares via `self.to_index().equals(other.to_index())`.

## `to_index_variable(self)` / `to_coord` (lines 2882-2886)
Returns self. Alias: `to_coord = utils.alias(to_index_variable, "to_coord")`.

## `to_index(self)` → pd.Index (lines 2888-2904)
Extracts the underlying pandas Index from `_data.array`. For MultiIndex, sets default level names (`{dim}_level_{i}`). Sets name via `.set_names(self.name)`. Returns the index.

## `level_names` property → list[str] | None (lines 2906-2915)
Returns `index.names` if MultiIndex, else None.

## `get_level_variable(self, level)` → IndexVariable (lines 2917-2922)
Raises ValueError if no MultiIndex. Returns new IndexVariable from `index.get_level_values(level)`.

## `name` / `name=` properties (lines 2924-2930)
Getter returns `self.dims[0]`. Setter raises AttributeError — name is immutable in-place.

## `_inplace_binary_op(self, other, f)` (lines 2932-2935)
Raises TypeError — IndexVariable values are immutable and cannot be modified in place.

---

# Backwards Compatibility Alias (line 2939)

`Coordinate = utils.alias(IndexVariable, "Coordinate")` — alias for the deprecated `Coordinate` name.