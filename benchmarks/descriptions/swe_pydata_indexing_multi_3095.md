## xarray/core/indexing.py
Now I have read every line of the file (1307 lines). Here is the complete specification:

---

# Module-Level Preamble

## Imports

```python
import functools
import operator
from collections import defaultdict
from contextlib import suppress
from datetime import timedelta
from typing import Sequence

import numpy as np
import pandas as pd

from . import duck_array_ops, nputils, utils
from .pycompat import dask_array_type, integer_types
from .utils import is_dict_like
```

## Constants & Globals

No module-level constants. `integer_types` and `dask_array_type` are imported from `.pycompat`. `is_dict_like`, `NDArrayMixin`, `safe_cast_to_index`, `to_0d_object_array`, `to_0d_array`, `is_valid_numpy_dtype` come from `.utils`.

---

# Code Objects (Functions)

## `expanded_indexer(key, ndim)`

Given a key for indexing an ndarray and the number of dimensions, returns an equivalent tuple-key with length exactly `ndim`. If `key` is not a tuple, wraps it in `(key,)`. Replaces each `Ellipsis` with enough `slice(None)` entries to fill all remaining dimensions (only the first `Ellipsis` triggers expansion; subsequent ones become single `slice(None)`). Pads trailing positions with `slice(None)` if needed. Raises `IndexError('too many indices')` if the expanded key exceeds `ndim`. Returns a tuple of length `ndim`.

## `_expand_slice(slice_, size)`

Returns `np.arange(*slice_.indices(size))`, i.e., expands a slice into an array of integer positions within dimension `size`.

## `_sanitize_slice_element(x)`

Sanitizes individual elements (start/stop/step) of a slice used for xarray indexing. If `x` is a `Variable` or `DataArray`, replaces it with `.values`. If `x` is a 0-d numpy array, extracts the scalar via `[()]`; raises `ValueError` if not 0-d. If `x` is `np.timedelta64`, converts to `pd.Timedelta(x)`. Returns the sanitized value.

## `_asarray_tuplesafe(values)`

Converts `values` into a numpy array of at most 1 dimension while preserving tuples as objects. If `values` is a tuple, calls `utils.to_0d_object_array(values)` and returns it. Otherwise, calls `np.asarray(values)`. If the result has ndim==2, creates an empty object-dtype array of length `len(values)` and assigns each element individually (to prevent numpy from interpreting a list-of-tuples as a 2D numeric array). Returns the result.

## `_is_nested_tuple(possible_tuple)`

Returns `True` if `possible_tuple` is a tuple containing at least one element that is itself a `tuple`, `list`, or `slice`. Otherwise returns `False`.

## `_index_method_kwargs(method, tolerance)`

Returns a kwargs dict for pandas indexing compatibility. If `method` is not None, adds `'method': method`. If `tolerance` is not None, adds `'tolerance': tolerance`. Returns the (possibly empty) dict.

## `get_loc(index, label, method=None, tolerance=None)`

Delegates to `index.get_loc(label, **kwargs)` where kwargs comes from `_index_method_kwargs(method, tolerance)`. Returns whatever pandas returns.

## `get_indexer_nd(index, labels, method=None, tolerance=None)`

Calls `pd.Index.get_indexer` on flattened labels and reshapes the result back to `labels.shape`. Internally: flattens `labels` via `np.ravel`, calls `index.get_indexer(flat_labels, **kwargs)`, reshapes the flat indexer array to `labels.shape`, returns it.

## `convert_label_indexer(index, label, index_name='', method=None, tolerance=None)`

Given a pandas.Index and a label (from xarray `__getitem__`), returns `(indexer, new_index)`. The `indexer` is suitable for indexing an ndarray along that dimension; `new_index` may be a modified pandas Index/MultiIndex.

Logic:
- If `label` is a `slice`: calls `index.slice_indexer()` with sanitized start/stop/step. If the result is not itself a slice, raises `KeyError('cannot represent labeled-based slice indexer…')`. Returns `(indexer, None)`.
- If `label` is dict-like: requires `index` to be a `pd.MultiIndex`, else raises `ValueError`. If `len(label) == index.nlevels` and values are not nested tuples, calls `index.get_loc(tuple(label[k] for k in index.names))`. Otherwise iterates label items; if any value is a non-string Sequence, raises `ValueError('Vectorized selection is not available along level variable: …')`. Calls `index.get_loc_level(tuple(label.values()), level=tuple(label.keys()))` to get `(indexer, new_index)`. If indexer dtype is boolean and sum is 0, raises `KeyError('{} not found'.format(label))`.
- If `label` is a tuple and `index` is a MultiIndex: if nested tuple, calls `index.get_locs(label)`; if length equals nlevels, calls `index.get_loc(label)`; otherwise calls `index.get_loc_level(label, level=list(range(len(label))))`.
- Otherwise (scalar or array label): wraps via `_asarray_tuplesafe` unless ndim > 1. If scalar (`ndim == 0`): for MultiIndex, calls `get_loc_level(label.item(), level=0)`; else calls `get_loc(index, label.item(), method, tolerance)`. If boolean dtype: returns the label directly as indexer. Otherwise (integer array): if MultiIndex and ndim > 1, raises `ValueError('Vectorized selection is not available along MultiIndex variable…')`; calls `get_indexer_nd(index, label, method, tolerance)`; if any result < 0, raises `KeyError('not all values found in index %r' % index_name)`.

Returns `(indexer, new_index)` where `new_index` is None unless a MultiIndex level was dropped.

## `get_dim_indexers(data_obj, indexers)`

Given an xarray data object and label-based indexers dict, returns a mapping of dimension-name → indexer. Validates that all keys exist in `data_obj.dims` or `_level_coords`, else raises `ValueError`. Groups multi-index level indexers into a single dict per dimension under `level_indexers`. If both a direct dimension indexer and level indexers target the same dim, raises `ValueError("cannot combine multi-index level indexers with an indexer for dimension %s" % dim)`. Returns `{dim: label_or_level_dict}`.

## `remap_label_indexers(data_obj, indexers, method=None, tolerance=None)`

Given xarray data object and label-based indexers, returns `(pos_indexers, new_indexes)`. Validates `method` is a string or raises `TypeError`. Calls `get_dim_indexers(data_obj, indexers)`. For each dim: if no pandas index exists for that dim (KeyError), reuses the provided labels as-is; if method/tolerance were supplied without an index, raises `ValueError`. Otherwise calls `convert_label_indexer(index, label, dim, method, tolerance)` and stores results. Returns `(pos_indexers, new_indexes)`.

## `slice_slice(old_slice, applied_slice, size)`

Given two slices and the dimension size, returns a single equivalent slice for sequential application. Computes combined step as product of both steps (treating None as 1). Expands `old_slice` to an array via `_expand_slice`, indexes it with `applied_slice`. If non-empty: start = first element, stop = last + sign(step) (None if < 0). If empty: start=stop=0. Returns the new slice.

## `_index_indexer_1d(old_indexer, applied_indexer, size)`

Combines two 1-D indexers. Shortcut: if `applied_indexer` is `slice(None)`, returns `old_indexer`. If both are slices, calls `slice_slice(old_indexer, applied_indexer, size)`. If old is slice and applied is array, expands old then indexes with applied. Otherwise (old is array), directly indexes `old_indexer[applied_indexer]`. Returns the combined indexer.

## `as_integer_or_none(value)`

Returns `None` if value is None; otherwise returns `operator.index(value)`.

## `as_integer_slice(value)`

Converts a slice's start/stop/step via `as_integer_or_none`, returning a new slice with integer (or None) components.

---

# Code Objects (Classes)

## `class ExplicitIndexer`

Base class for explicit indexer objects. Cannot be instantiated directly (`TypeError`). Stores `_key = tuple(key)` in `__init__`. Property `tuple` returns the key. `__repr__` returns `'ClassName(tuple)'`.

### `class BasicIndexer(ExplicitIndexer)`

For basic indexing (int or slice per dimension). Validates each element: int → `int(k)`, slice → `as_integer_slice(k)`, else raises `TypeError`. Passes cleaned tuple to parent.

### `class OuterIndexer(ExplicitIndexer)`

For outer/orthogonal indexing (int, slice, or 1-d integer np.ndarray per dimension). Validates each: int → `int(k)`, slice → `as_integer_slice(k)`, ndarray → must be 1-d with integer dtype, converted to `np.int64`; else raises `TypeError`. Passes cleaned tuple to parent.

### `class VectorizedIndexer(ExplicitIndexer)`

For vectorized indexing (slice or N-d integer np.ndarray per dimension). Validates each: slice → `as_integer_slice(k)`, ndarray → must have integer dtype, all ndarrays must share the same ndim; converted to `np.int64`; else raises `TypeError`/`ValueError`. Passes cleaned tuple to parent.

## `class ExplicitlyIndexed`

Empty mixin class marking support for Indexer subclasses in indexing.

## `class ExplicitlyIndexedNDArrayMixin(utils.NDArrayMixin, ExplicitlyIndexed)`

Provides `__array__(self, dtype=None)`: creates a full-slice `BasicIndexer((slice(None),)*self.ndim)` and returns `np.asarray(self[key], dtype=dtype)`.

## `class ImplicitToExplicitIndexingAdapter(utils.NDArrayMixin)`

Wraps an array, converting tuples into the indicated explicit indexer.
- `__init__(array, indexer_cls=BasicIndexer)`: stores `as_indexable(array)` and `indexer_cls`.
- `__array__(dtype=None)`: returns `np.asarray(self.array, dtype=dtype)`.
- `__getitem__(key)`: expands key via `expanded_indexer(key, self.ndim)`, indexes `self.array[self.indexer_cls(key)]`. If result is `ExplicitlyIndexed`, wraps it in a new adapter of the same type; otherwise returns raw result.

## `class LazilyOuterIndexedArray(ExplicitlyIndexedNDArrayMixin)`

Wraps an array to make basic and outer indexing lazy (defers actual data access).
- `__init__(array, key=None)`: if unwrapping another instance of itself, extracts its key and underlying array. If no key provided, creates full-slice `BasicIndexer`. Stores `as_indexable(array)` and the key.
- `_updated_key(new_key)`: combines current lazy key with a new indexer by iterating dimensions: for integer positions in old key, keeps them; for slices, calls `_index_indexer_1d(old_slice, next_new_key, size)`. Returns `BasicIndexer` if all elements are int/slice, else `OuterIndexer`.
- `shape`: computed from current key — slice dims → length of range, array dims → `.size`.
- `__array__(dtype=None)`: returns `np.asarray(as_indexable(self.array)[self.key], dtype=dtype)` (forces evaluation).
- `transpose(order)`: delegates to `LazilyVectorizedIndexedArray(self.array, self.key).transpose(order)`.
- `__getitem__(indexer)`: if VectorizedIndexer, wraps in `LazilyVectorizedIndexedArray` and indexes; otherwise returns a new `LazilyOuterIndexedArray` with the updated key.
- `__setitem__(key, value)`: if VectorizedIndexer, raises `NotImplementedError`; otherwise computes full key and assigns to underlying array.
- `__repr__`: `'%s(array=%r, key=%r)'`.

## `class LazilyVectorizedIndexedArray(ExplicitlyIndexedNDArrayMixin)`

Wraps an array to make vectorized indexing lazy.
- `__init__(array, key)`: if key is Basic/OuterIndexer, converts via `_outer_to_vectorized_indexer(key, array.shape)`; else uses `_arrayize_vectorized_indexer(key, array.shape)`. Stores `as_indexable(array)`.
- `shape`: returns `np.broadcast(*self.key.tuple).shape`.
- `__array__(dtype=None)`: returns `np.asarray(self.array[self.key], dtype=dtype)`.
- `_updated_key(new_key)`: calls `_combine_indexers(self.key, self.shape, new_key)`.
- `__getitem__(indexer)`: if all indexer elements are integers (scalar result), creates a `LazilyOuterIndexedArray` with per-element indexing into each key array; otherwise returns a new instance of the same class with combined key.
- `transpose(order)`: transposes each ndarray in the key tuple, wraps in new VectorizedIndexer, returns new instance.
- `__setitem__(key, value)`: raises `NotImplementedError`.
- `__repr__`: `'%s(array=%r, key=%r)'`.

## `_wrap_numpy_scalars(array)`

If `np.isscalar(array)`, wraps in `np.array(array)` (0-d array); otherwise returns unchanged.

## `class CopyOnWriteArray(ExplicitlyIndexedNDArrayMixin)`

Copy-on-write wrapper.
- `__init__(array)`: stores `as_indexable(array)`, `_copied = False`.
- `_ensure_copied()`: if not yet copied, replaces array with a fresh copy via `np.array(self.array)`, sets `_copied = True`.
- `__array__(dtype=None)`: returns `np.asarray(self.array, dtype=dtype)` (no copy).
- `__getitem__(key)`: returns new `CopyOnWriteArray(_wrap_numpy_scalars(self.array[key]))` — reads are lazy.
- `transpose(order)`: delegates to `self.array.transpose(order)`.
- `__setitem__(key, value)`: calls `_ensure_copied()` then assigns to underlying array.

## `class MemoryCachedArray(ExplicitlyIndexedNDArrayMixin)`

Caches data as a numpy array after first access.
- `__init__(array)`: stores `_wrap_numpy_scalars(as_indexable(array))`.
- `_ensure_cached()`: if not already a `NumpyIndexingAdapter`, wraps with one via `np.asarray(self.array)`.
- `__array__(dtype=None)`: calls `_ensure_cached()` then returns `np.asarray(self.array, dtype=dtype)`.
- `__getitem__(key)`: returns new `MemoryCachedArray(_wrap_numpy_scalars(self.array[key]))`.
- `transpose(order)`: delegates to `self.array.transpose(order)`.
- `__setitem__(key, value)`: directly assigns to underlying array (no copy-on-write).

## `as_indexable(array)`

Ensures the result is an ExplicitlyIndexed subclass: if already one, returns as-is; if `np.ndarray`, wraps in `NumpyIndexingAdapter`; if `pd.Index`, wraps in `PandasIndexAdapter`; if dask array (`dask_array_type`), wraps in `DaskIndexingAdapter`; else raises `TypeError`.

## `_outer_to_vectorized_indexer(key, shape)`

Converts an Outer/Basic indexer into a VectorizedIndexer. Counts non-integer dimensions as `n_dim`. For each dimension: integer → reshaped to `(1,)*n_dim` array; slice → expanded via `np.arange(*k.indices(size))`; ndarray → kept and reshaped with broadcasting shape `(1,...,k.size,...,1)`. Returns `VectorizedIndexer(tuple(new_key))`.

## `_outer_to_numpy_indexer(key, shape)`

Converts an Outer/Basic indexer into a NumPy-compatible tuple. If at most one non-slice element exists in the key, returns `key.tuple` directly (safe for mixed basic/advanced indexing). Otherwise delegates to `_outer_to_vectorized_indexer(key, shape).tuple`.

## `_combine_indexers(old_key, shape, new_key)`

Combines two indexers. If old_key is not VectorizedIndexer, converts via `_outer_to_vectorized_indexer`. If empty old key, returns new_key as-is. Computes `new_shape` from broadcasting old key. Converts new_key to vectorized form (via `_arrayize_vectorized_indexer` or `_outer_to_vectorized_indexer`). Returns `VectorizedIndexer(tuple(o[new_key.tuple] for o in np.broadcast_arrays(*old_key.tuple)))`.

## `class IndexingSupport`

String constants: `'BASIC'`, `'OUTER'`, `'OUTER_1VECTOR'`, `'VECTORIZED'`. Represents the indexing support level of a backend.

## `explicit_indexing_adapter(key, shape, indexing_support, raw_indexing_method)`

Delegates explicit indexing to a raw method. Calls `decompose_indexer(key, shape, indexing_support)` → `(raw_key, numpy_indices)`. Calls `raw_indexing_method(raw_key.tuple)`. If `numpy_indices` is non-empty, indexes the result via `NumpyIndexingAdapter(np.asarray(result))[numpy_indices]`. Returns the final indexed array.

## `decompose_indexer(indexer, shape, indexing_support)`

Dispatches: VectorizedIndexer → `_decompose_vectorized_indexer`; Basic/OuterIndexer → `_decompose_outer_indexer`; else raises `TypeError`.

## `_decompose_slice(key, size)`

Converts a slice to two successive slices where the first always has positive step. Gets `(start, stop, step) = key.indices(size)`. If step > 0: returns `(key, slice(None))`. If step < 0: adjusts stop precisely for step > 1 case (`stop = start + int((stop - start - 1)/step)*step + 1`), then swaps and negates: `return slice(start, stop, -step), slice(None, None, -1)`.

## `_decompose_vectorized_indexer(indexer, shape, indexing_support)`

Decomposes a VectorizedIndexer into `(backend_indexer, np_indexer)`. If VECTORIZED support: returns `(indexer, BasicIndexer(()))`. Otherwise: converts negative indices to positive. For each dimension: slice → `_decompose_slice` for backend + `slice(None)` for in-memory; ndarray → `np.unique(k, return_inverse=True)` gives sorted unique keys for backend and inverse mapping for in-memory. If support is OUTER: returns `(OuterIndexer(backend), VectorizedIndexer(np))`. If BASIC: further decomposes the outer backend indexer via `_decompose_outer_indexer` and combines with np_indexer via `_combine_indexers`.

## `_decompose_outer_indexer(indexer, shape, indexing_support)`

Decomposes an Outer/Basic indexer into `(backend_indexer, np_indexer)`. If VECTORIZED: returns `(indexer, BasicIndexer(()))`. Makes all indices positive. Then branches on support level:
- **OUTER_1VECTOR**: picks the most efficient axis (max gain = range/unique_count). For non-selected ndarray axes, converts to a covering slice for backend and offset array for in-memory. Selected ndarray uses `np.unique` for deduplication. Integers pass through; slices use `_decompose_slice`. Returns `(OuterIndexer, OuterIndexer)`.
- **OUTER**: slices → `_decompose_slice`; integers pass through; sorted ndarrays pass through directly with `slice(None)` in-memory; unsorted ndarrays use `np.unique` for dedup. Returns `(OuterIndexer, OuterIndexer)`.
- **BASIC**: ndarray axes → covering slice + offset array; integers pass through; slices → `_decompose_slice`. Returns `(BasicIndexer, OuterIndexer)`.

## `_arrayize_vectorized_indexer(indexer, shape)`

Replaces slices in a VectorizedIndexer with arrays. If no slices present, returns indexer unchanged. Counts slices and existing ndarrays for dimensionality. For each element: ndarray → reshaped to broadcast with all slice-converted arrays; slice → expanded via `np.arange(*v.indices(size))` and reshaped with proper broadcasting shape `(1,...,-1,...,1)`. Returns new VectorizedIndexer.

## `_dask_array_with_chunks_hint(array, chunks)`

Creates a dask array using chunk hints for dimensions of size > 1 (size-1 dims get single-element chunks). Raises `ValueError` if not enough chunks provided. Calls `da.from_array(array, new_chunks)`.

## `_logical_any(args)`

Returns `functools.reduce(operator.or_, args)`, i.e., element-wise logical OR across all arrays in args.

## `_masked_result_drop_slice(key, chunks_hint=None)`

Filters out slices from key. If `chunks_hint` provided, wraps ndarrays via `_dask_array_with_chunks_hint`. Returns `_logical_any(k == -1 for k in key)`, producing a boolean mask where any indexer element equals -1 (masked).

## `create_mask(indexer, shape, chunks_hint=None)`

Creates a boolean mask for indexing with fill-values (-1 indicates masked locations).
- **OuterIndexer**: converts to vectorized via `_outer_to_vectorized_indexer`, asserts no slices remain, calls `_masked_result_drop_slice`.
- **VectorizedIndexer**: gets base mask from `_masked_result_drop_slice`, computes slice shapes, broadcasts the base mask to include slice dimensions.
- **BasicIndexer**: returns `any(k == -1 for k in indexer.tuple)` (scalar bool).
- Else: raises `TypeError`.

## `_posify_mask_subindexer(index)`

For a 1-d integer ndarray, replaces all `-1` values with the nearest unmasked adjacent value. Uses `np.flatnonzero(~masked)` to find valid positions and `np.searchsorted` for binary search of masked positions among them. If no unmasked positions exist, returns zeros. Returns a copy with -1s replaced.

## `posify_mask_indexer(indexer)`

For each ndarray key in the indexer tuple, applies `_posify_mask_subindexer(k.ravel()).reshape(k.shape)`. Non-ndarray elements pass through unchanged. Returns a new indexer of the same type as input.

## `class NumpyIndexingAdapter(ExplicitlyIndexedNDArrayMixin)`

Wraps a NumPy array for explicit indexing.
- `__init__(array)`: asserts `isinstance(array, np.ndarray)`, stores it.
- `_indexing_array_and_key(key)`: converts key based on type: OuterIndexer → uses `_outer_to_numpy_indexer`; VectorizedIndexer → wraps array in `nputils.NumpyVIndexAdapter` and uses raw tuple; BasicIndexer → appends `(Ellipsis,)` to tuple for 0d slices. Returns `(array, key)`.
- `transpose(order)`: returns `self.array.transpose(order)`.
- `__getitem__(key)`: calls `_indexing_array_and_key(key)` then indexes.
- `__setitem__(key, value)`: same as getitem; if ValueError and array is read-only/no data, raises a more informative message about `.copy()`.

## `class DaskIndexingAdapter(ExplicitlyIndexedNDArrayMixin)`

Wraps a dask array for explicit indexing.
- `__init__(array)`: stores the dask array.
- `__getitem__(key)`: BasicIndexer → `self.array[key.tuple]`; VectorizedIndexer → `self.array.vindex[key.tuple]`; OuterIndexer → tries `self.array[key]` directly; if NotImplementedError, performs manual orthogonal indexing by iterating axes in reverse: `value = value[(slice(None),)*axis + (subkey,)]`.
- `__setitem__(key, value)`: raises `TypeError` explaining that dask arrays don't support item assignment.
- `transpose(order)`: returns `self.array.transpose(order)`.

## `class PandasIndexAdapter(ExplicitlyIndexedNDArrayMixin)`

Wraps a pandas.Index to preserve dtypes and handle explicit indexing.
- `__init__(array, dtype=None)`: stores `utils.safe_cast_to_index(array)`. Determines `_dtype`: for PeriodIndex → `'O'`; if has `.categories` → categories dtype; if not valid numpy dtype → `'O'`; else uses `array.dtype`.
- `dtype` property: returns `_dtype`.
- `__array__(dtype=None)`: defaults to `self.dtype`. For PeriodIndex, tries `.astype('object')`. Returns `np.asarray(array.values, dtype=dtype)`.
- `shape` property: returns `(len(self.array),)` (workaround for old pandas).
- `__getitem__(indexer)`: unpacks single-element tuple keys. If key ndim > 1, delegates to NumpyIndexingAdapter on raw values. Otherwise indexes the pandas Index directly. If result is pd.Index, wraps in PandasIndexAdapter. For scalars: NaT → `np.datetime64('NaT', 'ns')`; timedelta → `np.timedelta64(value, 'ns')`; Timestamp → `.to_datetime64()`; else casts to self.dtype. Wraps final scalar via `utils.to_0d_array(result)`.
- `transpose(order)`: returns `self.array` (always 1-d).
- `__repr__()`: `'%s(array=%r, dtype=%r)' % (type(self).__name__, self.array, self.dtype)`.

---

## xarray/core/variable.py
Now I have the complete file content (all 2160 lines). Let me write the comprehensive natural-language specification.

---

# Module-Level Preamble

## Imports

```python
import functools
import itertools
from collections import OrderedDict, defaultdict
from datetime import timedelta
from distutils.version import LooseVersion
from typing import Any, Hashable, Mapping, MutableMapping, Union

import numpy as np
import pandas as pd

import xarray as xr  # only for Dataset and DataArray

from . import (arithmetic, common, dtypes, duck_array_ops, indexing, nputils, ops, utils)
from .indexing import (BasicIndexer, OuterIndexer, PandasIndexAdapter, VectorizedIndexer, as_indexable)
from .options import _get_keep_attrs
from .pycompat import dask_array_type, integer_types
from .utils import (OrderedSet, decode_numpy_dict_values, either_dict_or_kwargs, ensure_us_time_resolution)

try:
    import dask.array as da
except ImportError:
    pass
```

## Constants & Globals

- **`NON_NUMPY_SUPPORTED_ARRAY_TYPES`**: Tuple of `(indexing.ExplicitlyIndexed, pd.Index)` concatenated with `dask_array_type`. Used to identify array types that should be wrapped in adapter objects rather than converted to numpy arrays.
- **`BASIC_INDEXING_TYPES`**: Tuple of `integer_types + (slice,)`, used to classify indexing keys as "basic" (integers and slices only).

## Exception Class

### `MissingDimensionsError(ValueError)`
A custom exception inheriting from `ValueError` for backward compatibility. Raised when a variable cannot be safely assigned a dimension name because its data has more than one dimension or conflicts with existing dimensions.

---

# Module-Level Functions

## `as_variable(obj, name=None) -> Union[Variable, IndexVariable]`
Converts an arbitrary object into a `Variable` (or `IndexVariable`). Processing order:
1. If `obj` is a `DataArray`, extract its `.variable` attribute.
2. If already a `Variable`, return a shallow copy (`copy(deep=False)`).
3. If a tuple, attempt to unpack as `(dims, data[, attrs, encoding])` into `Variable(*obj)`. On failure, raise the original error with context.
4. If scalar (per `utils.is_scalar`), create `Variable([], obj)`.
5. If `pd.Index` or `IndexVariable` with a non-None `.name`, create `Variable(obj.name, obj)`.
6. If `set` or `dict`, raise `TypeError`.
7. If `name is not None`, convert data via `as_compatible_data(obj)`; if the result is not 1D, raise `MissingDimensionsError`; otherwise create `Variable(name, data, fastpath=True)`.
8. Otherwise, raise `TypeError` (cannot decode without explicit dimensions).

After conversion: if `name is not None` and `name in obj.dims`, convert to `IndexVariable` via `to_index_variable()`. If the variable has more than 1 dimension with a name matching one of its dims, raise `MissingDimensionsError`.

## `_maybe_wrap_data(data)`
Wraps raw data in adapter objects for proper indexing. If `data` is a `pd.Index`, wraps it in `PandasIndexAdapter`; otherwise returns unchanged (numpy arrays and existing adapters pass through).

## `_possibly_convert_objects(values)`
Converts numpy arrays of Python `datetime.datetime` / `timedelta` objects into `datetime64`/`timedelta64` dtypes per pandas convention. Flattens, converts via `pd.Series`, reshapes back.

## `as_compatible_data(data, fastpath=False) -> array_like`
Prepares and wraps data for storage in a Variable:
1. If `fastpath=True` and `data.ndim > 0`, return `_maybe_wrap_data(data)` (skip conversion for non-scalar arrays).
2. If already a `Variable`, return its `.data`.
3. If instance of `NON_NUMPY_SUPPORTED_ARRAY_TYPES`, wrap via `_maybe_wrap_data`.
4. If tuple, convert via `utils.to_0d_object_array`.
5. If `pd.Timestamp`, convert to `np.datetime64(data.value, 'ns')`.
6. If `timedelta`, convert to `np.timedelta64(getattr(data, 'value', data), 'ns')`.
7. Extract `.values` attribute if present (avoids nested self-described arrays).
8. If `np.ma.MaskedArray`: if any mask values exist, promote dtype and replace masked entries with the fill value; otherwise convert to plain ndarray.
9. Convert via `np.asarray(data)`.
10. For resulting numpy array: if kind `'O'`, apply `_possibly_convert_objects`; if kind `'M'` (datetime64), ensure nanosecond precision; if kind `'m'` (timedelta64), ensure nanosecond precision.
11. Return `_maybe_wrap_data(data)`.

## `_as_array_or_item(data)`
Converts data to numpy array via `np.asarray`, then handles 0-dimensional datetime64/timedelta64 arrays by extracting the scalar value (workaround for broken 0d datetime64/timedelta64 behavior in numpy). Returns a plain Python scalar for 0d datetime/timedelta, otherwise returns the ndarray.

## `_unified_dims(variables) -> OrderedDict`
Validates and unifies dimensions across multiple variables:
- Iterates each variable's dims/shapes; rejects duplicate dimension names within a single variable.
- Builds an `OrderedDict` mapping dim name → size. Rejects mismatched sizes for the same dimension across variables.
- Returns the unified dimension order dict.

## `_broadcast_compat_variables(*variables) -> tuple[Variable]`
Creates broadcast-compatible variables with matching dimensions. Calls `_unified_dims(variables)` to get unified dims, then calls `var.set_dims(dims)` on each variable that doesn't already have those dims. Some variables may retain size-1 dimensions instead of being fully expanded.

## `broadcast_variables(*variables) -> tuple[Variable]`
Like `_broadcast_compat_variables`, but returns variables with fully broadcast data (dimensions are reordered and inserted so all arrays share the same dimension order). Dimensions sorted by first appearance across input variables.

## `_broadcast_compat_data(self, other) -> Tuple[array_like, array_like, tuple[str]]`
Broadcasts `self` against `other` for arithmetic operations:
- If `other` has attributes `dims`, `data`, `shape`, `encoding` (i.e., is Variable-like), use `_broadcast_compat_variables` to align them; return `(new_self.data, new_other.data, new_self.dims)`.
- Otherwise, fall back to numpy broadcasting rules: return `(self.data, other, self.dims)`.

## `concat(variables, dim='concat_dim', positions=None, shortcut=False) -> Variable`
Module-level concatenation dispatcher. Converts variables to list; if all are `IndexVariable`, delegates to `IndexVariable.concat`; otherwise delegates to `Variable.concat`.

## `assert_unique_multiindex_level_names(variables: Mapping[Hashable, Variable])`
Validates uniqueness of MultiIndex level names across a mapping of variable name → Variable:
- For each variable whose `_data` is a `PandasIndexAdapter`, extracts its `level_names`.
- Tracks which variables own each level name.
- If any level name appears in multiple variables, raises `ValueError` with details.
- Also checks that no dimension name conflicts with any MultiIndex level name (GH:2299).

---

# Class: Variable

**Inheritance:** `common.AbstractArray`, `arithmetic.SupportsArithmetic`, `utils.NdimSizeLenMixin`

A netCDF-like variable consisting of dimensions, data, and attributes. Implements array broadcasting by dimension name for arithmetic operations.

## Attributes (instance)

| Attribute | Type | Description |
|-----------|------|-------------|
| `_data` | array_like | The underlying data (numpy array, dask array, PandasIndexAdapter, etc.), set via `as_compatible_data`. |
| `_dims` | tuple[str] | Dimension names, validated by `_parse_dimensions`. |
| `_attrs` | OrderedDict or None | Local attributes; lazily initialized to empty `OrderedDict()`. |
| `_encoding` | dict or None | Encoding metadata for serialization (e.g., netCDF); lazily initialized to `{}`. |

## Constructor: `__init__(self, dims, data, attrs=None, encoding=None, fastpath=False)`
- Sets `_data = as_compatible_data(data, fastpath=fastpath)`.
- Sets `_dims = self._parse_dimensions(dims)`.
- Initializes `_attrs = None`, `_encoding = None`; if `attrs` is not None, assigns via the `attrs` setter; same for `encoding`.

## Properties & Setters

### `dtype` → `np.dtype`
Returns `self._data.dtype`.

### `shape` → tuple[int]
Returns `self._data.shape`.

### `nbytes` → int
Returns `self.size * self.dtype.itemsize`.

### `_in_memory` → bool
True if data is in memory: instance of `np.ndarray`, `np.number`, `PandasIndexAdapter`, or a `MemoryCachedArray` wrapping a `NumpyIndexingAdapter`.

### `data` → array_like / setter
- **Getter**: If `_data` is dask, return it directly; otherwise return `self.values` (numpy).
- **Setter**: Converts via `as_compatible_data`; validates shape matches; assigns to `_data`.

### `values` → numpy.ndarray / setter
- **Getter**: Returns `_as_array_or_item(self._data)` — the data as a plain numpy array, with 0d datetime/timedelta scalar extraction.
- **Setter**: Delegates to `self.data = values`.

### `dims` → tuple[str] / setter
- **Getter**: Returns `self._dims`.
- **Setter**: Validates via `_parse_dimensions(value)`.

### `chunks` → tuple or None
Returns `getattr(self._data, 'chunks', None)` — block dimensions for dask arrays.

### `T` → Variable
Returns `self.transpose()`.

## Methods

### `_parse_dimensions(dims) -> tuple[str]`
Normalizes dims: if string, wraps in tuple; validates length matches `self.ndim`; raises `ValueError` on mismatch.

### `_item_key_to_tuple(key)`
Converts dict-like keys (e.g., `{'dim': 0}`) to a full-size tuple of indexers using `self.dims` as the key order, defaulting missing dims to `slice(None)`. Otherwise returns key unchanged.

### `_broadcast_indexes(key) -> Tuple[tuple[str], Indexer, Optional[list[int]]]`
Prepares an indexing key for xarray-style orthogonal indexing:
1. Convert via `_item_key_to_tuple`; expand via `indexing.expanded_indexer(key, self.ndim)` to full size.
2. Convert 0d Variable keys to integers via `.data.item()`; convert 0d numpy arrays to integers via `.item()`.
3. If all key elements are `BASIC_INDEXING_TYPES`, delegate to `_broadcast_indexes_basic`.
4. Validate indexers via `_validate_indexers`.
5. If no key element is a Variable, delegate to `_broadcast_indexes_outer`.
6. If all Variable keys are 1D with unique dimension names, delegate to `_broadcast_indexes_outer`.
7. Otherwise, delegate to `_broadcast_indexes_vectorized`.

### `_broadcast_indexes_basic(key) -> Tuple[tuple[str], BasicIndexer, None]`
For basic indexing only (integers and slices). Returns dims for non-integer key elements, wrapped in `BasicIndexer`, with no axis reordering.

### `_validate_indexers(key)`
Sanity checks on indexers:
- For each dim/key pair: if not a basic type, convert to numpy array; reject multi-dimensional unlabeled arrays (`IndexError`).
- For boolean keys: validate size matches the target dimension length; reject >1D boolean indexing; require unlabeled or matching dimension.

### `_broadcast_indexes_outer(key) -> Tuple[tuple[str], OuterIndexer, None]`
For outer (orthogonal) indexing. Extracts dims from Variable keys or original dims for non-integer elements. Converts Variable keys to `.data`; converts non-basic types to numpy arrays; converts boolean arrays via `np.nonzero`. Returns wrapped in `OuterIndexer`.

### `_broadcast_indexes_vectorized(key) -> Tuple[tuple[str], VectorizedIndexer, Optional[list[int]]]`
For vectorized (advanced) indexing where indexers share dimensions:
1. For each dim/key pair: if slice, add to output dims; else convert key to Variable via `as_variable(value, name=dim)`; for boolean keys, call `_nonzero()`. Collect all variable dims into an `OrderedSet`.
2. Convert slices that share a dimension with at least one other variable into 1D Variable arrays (via `np.arange`); keep independent slices as-is.
3. Broadcast variables together via `_broadcast_compat_variables`; on mismatch, raise `IndexError`.
4. Build output key from `.data` of each variable; collect slice positions and compute axis reordering (`new_order`) to move sliced axes to correct positions.
5. Return `(out_dims, VectorizedIndexer(out_key), new_order)`.

### `_nonzero() -> tuple[Variable, ...]`
Equivalent to `np.nonzero(self.data)` but returns a tuple of 1D Variables (one per dimension).

### `__getitem__(self, key) -> Variable`
xarray-style indexing: calls `_broadcast_indexes(key)` to get dims/indexer/new_order; applies indexer to `as_indexable(self._data)`; if new_order is set, moves axes via `duck_array_ops.moveaxis`; returns `_finalize_indexing_result(dims, data)`.

### `_finalize_indexing_result(dims, data) -> Variable`
Creates a new Variable of the same type with `(dims, data, self._attrs, self._encoding, fastpath=True)`. Overridden by `IndexVariable`.

### `__setitem__(self, key, value)`
xarray-style in-place assignment:
1. Broadcast key via `_broadcast_indexes` to get dims/indexer/new_order.
2. If value is not a Variable, convert via `as_compatible_data`; validate ndim ≤ len(dims); wrap 0d or multi-dim values as Variables with appropriate dims.
3. Broadcast value to target dims via `.set_dims(dims).data`.
4. If new_order is set, prepend leading newaxis axes and move axes accordingly.
5. Assign `indexable[index_tuple] = value` where `indexable = as_indexable(self._data)`.

### `_getitem_with_mask(self, key, fill_value=dtypes.NA)`
Index with -1 remapped to fill_value (for reindex-style operations):
1. Resolve fill_value via `dtypes.get_fill_value(self.dtype)` if NA.
2. Broadcast key; for dask data, use `posify_mask_indexer` (dask doesn't support negative indices in vindex).
3. Index the data; create mask via `indexing.create_mask(indexer, self.shape, chunks_hint)`.
4. Apply `duck_array_ops.where(mask, fill_value, data)` to replace masked positions.
5. For empty arrays, build mask directly and broadcast fill_value.
6. Reorder axes if needed; return `_finalize_indexing_result`.

### `attrs` → OrderedDict / setter
- **Getter**: Lazily initializes `_attrs` to `OrderedDict()` if None.
- **Setter**: Converts value to `OrderedDict`.

### `encoding` → dict / setter
- **Getter**: Lazily initializes `_encoding` to `{}` if None.
- **Setter**: Converts via `dict(value)`; raises `ValueError` on failure.

### `copy(self, deep=True, data=None) -> Variable`
Returns a copy:
- If `data is None`: use `self._data`; for `MemoryCachedArray`, create a new wrapper (don't share cache); if `deep=True` and not dask/PandasIndexAdapter, convert to numpy array via `np.array(data)`; if dask, call `.copy()`.
- If `data is not None`: convert via `as_compatible_data`; validate shape matches.
- Return `type(self)(self.dims, data, self._attrs, self._encoding, fastpath=True)`.

### `__copy__() -> Variable`
Returns `self.copy(deep=False)`.

### `__deepcopy__(self, memo=None) -> Variable`
Returns `self.copy(deep=True)`.

### `__hash__ = None`
Variables are unhashable (mutable).

### `chunk(self, chunks=None, name=None, lock=False) -> Variable`
Coerces data to a dask array with given chunk sizes:
- If `chunks` is dict-like, convert dim names to axis numbers.
- If `chunks is None`, use existing chunks or full shape.
- If already dask: call `.rechunk(chunks)`.
- Otherwise: wrap in `ImplicitToExplicitIndexingAdapter(data, OuterIndexer)`; create dask array via `da.from_array` (with `meta=np.ndarray` for dask > 1.2.2).
- Return new Variable with dims/attrs/encoding preserved.

### `load(self, **kwargs) -> Variable`
Triggers loading of deferred data: if dask, compute and re-wrap; otherwise convert to numpy via `np.asarray`. Returns self (in-place).

### `compute(self, **kwargs) -> Variable`
Returns a new Variable with loaded data (`self.copy(deep=False)` then `.load(**kwargs)`).

### Dask Integration Methods
- `__dask_graph__()`: Returns `self._data.__dask_graph__()` if dask, else None.
- `__dask_keys__()`: Delegates to `self._data`.
- `__dask_layers__()`: Delegates to `self._data`.
- `__dask_optimize__` / `__dask_scheduler__`: Property delegates to `self._data`.
- `__dask_postcompute__()`: Returns `(self._dask_finalize, (array_func, array_args, self._dims, self._attrs, self._encoding))`.
- `__dask_postpersist__()`: Same pattern with `_dask_finalize`.
- `_dask_finalize(results, array_func, array_args, dims, attrs, encoding)`: For persist case, filters results dict by name; reconstructs Variable from finalized data.

### `to_base_variable() -> Variable` (alias: `to_variable`)
Returns a base `Variable` with same dims/data/attrs/encoding (`fastpath=True`).

### `to_index_variable() -> IndexVariable` (alias: `to_coord`)
Returns an `IndexVariable` with same dims/data/attrs/encoding.

### `to_index() -> pd.Index`
Converts via `self.to_index_variable().to_index()` (delegates to IndexVariable).

### `to_dict(self, data=True) -> dict`
Dictionary representation: always includes `'dims'` and `'attrs'` (decoded); if `data=True`, includes `'data'` as a list (with time resolution normalization); else includes `'dtype'` and `'shape'`.

### `isel(self, indexers=None, drop=False, **indexers_kwargs) -> Variable`
Integer-based indexing by dimension name: validates all indexer keys exist in dims; builds full-size key tuple with `slice(None)` for unindexed dims; delegates to `self[key]`. (The `drop` parameter is accepted but not used in this implementation.)

### `squeeze(self, dim=None) -> Variable`
Removes length-1 dimensions. Gets squeeze dims via `common.get_squeeze_dims(self, dim)`; returns `self.isel({d: 0 for d in dims})`.

### `_shift_one_dim(self, dim, count, fill_value=dtypes.NA) -> Variable`
Shifts one dimension by `count` (positive = right, negative = left):
1. Determine keep slice: if count > 0, `slice(None, -count)`; if < 0, `slice(-count, None)`; else full slice.
2. Extract trimmed data via indexing.
3. If fill_value is NA, promote dtype and get fill value via `dtypes.maybe_promote`.
4. Build filler array of appropriate shape/dtype (dask-aware with matching chunks).
5. Concatenate `[filler, trimmed]` (count > 0) or `[trimmed, filler]` (count < 0).
6. For dask: rechunk to match original chunks.

### `shift(self, shifts=None, fill_value=dtypes.NA, **shifts_kwargs) -> Variable`
Shifts data along specified dimensions. Normalizes shifts via `either_dict_or_kwargs`; applies `_shift_one_dim` sequentially for each dimension; returns result.

### `pad_with_fill_value(self, pad_widths=None, fill_value=dtypes.NA, **pad_widths_kwargs)`
Pads a variable with fill values:
1. Normalize widths via `either_dict_or_kwargs`; resolve fill_value/dtype if NA.
2. For dask data: manually implement padding (dask doesn't support it natively per the code). For each dimension, create filler arrays via `da.full` and concatenate before/after the original array.
3. For numpy: use `np.pad(self.data.astype(dtype), pads, mode='constant', constant_values=fill_value)`.
4. Return new Variable (note: does not preserve attrs/encoding).

### `_roll_one_dim(self, dim, count) -> Variable`
Rolls one dimension by `count`: normalizes via modulo; splits array at `-count` and `slice(None, -count)`; concatenates in swapped order; rechunks dask to match original.

### `roll(self, shifts=None, **shifts_kwargs) -> Variable`
Rolls data along specified dimensions. Normalizes via `either_dict_or_kwargs`; applies `_roll_one_dim` sequentially per dimension.

### `transpose(self, *dims) -> Variable`
Reorders dimensions: if no args, reverses dims; otherwise uses provided order. Gets axis numbers via `get_axis_num(dims)`; if < 2 dims, returns shallow copy; else transposes data via `as_indexable(self._data).transpose(axes)` and returns new Variable with reordered dims/attrs/encoding.

### `set_dims(self, dims, shape=None) -> Variable`
Attaches new dimensions (or expands existing):
1. Normalize dims to list; if dict-like, extract shape from values.
2. Validate: new dims must be a superset of existing dims.
3. Build expanded dim order: new dims first, then existing dims.
4. If dims unchanged, use `self.data` directly (writeable).
5. If shape provided, broadcast via `duck_array_ops.broadcast_to(self.data, tmp_shape)`.
6. Otherwise, prepend `None` axes: `self.data[(None,) * delta + (Ellipsis,)]`.
7. Create Variable and transpose to requested order.

### `_stack_once(self, dims, new_dim) -> Variable`
Stacks multiple existing dimensions into one:
1. Validate all dims exist; reject duplicate names; if no dims to stack, return shallow copy.
2. Transpose so stacked dims come last.
3. Reshape data with `-1` for the new dimension size.
4. Return new Variable with reordered dims/attrs/encoding.

### `stack(self, dimensions=None, **dimensions_kwargs) -> Variable`
Stacks multiple dimension pairs sequentially via `_stack_once`. Normalizes input via `either_dict_or_kwargs`.

### `_unstack_once(self, dims, old_dim) -> Variable`
Unstacks one existing dimension into multiple:
1. Validate old_dim exists; reject name collisions with existing dims; validate product of new sizes equals old size.
2. Transpose so other dims come first, then old_dim last.
3. Reshape data to `(other_dims..., *new_sizes)`.
4. Return new Variable with combined dim names/attrs/encoding.

### `unstack(self, dimensions=None, **dimensions_kwargs) -> Variable`
Unstacks multiple dimension mappings sequentially via `_unstack_once`.

### `concat(cls, variables, dim='concat_dim', positions=None, shortcut=False) -> Variable` (classmethod)
Class-level concatenation:
1. If `dim` is not a string, extract from its dims.
2. Convert to list; get first variable's data as reference.
3. Extract `.data` arrays from all variables.
4. If `dim in first_var.dims`: concatenate along that axis via `duck_array_ops.concatenate`; if positions provided, apply inverse permutation reordering.
5. Else: stack at axis 0 via `duck_array_ops.stack`; prepend dim to dims tuple.
6. Merge attrs/encoding from first variable; on non-shortcut mode, validate consistent dimensions and remove incompatible attribute items across all variables.
7. Return `cls(dims, data, attrs, encoding)`.

### `equals(self, other, equiv=duck_array_ops.array_equiv) -> bool`
True if dims match AND (data is same object OR element-wise equivalent). Catches TypeError/AttributeError → False. NaN values in same locations count as equal.

### `broadcast_equals(self, other, equiv=duck_array_ops.array_equiv) -> bool`
Broadcasts both variables to matching dimensions then calls `equals`. On failure, returns False.

### `identical(self, other) -> bool`
Like `equals`, but also checks attribute equality via `utils.dict_equiv(self.attrs, other.attrs)`.

### `no_conflicts(self, other) -> bool`
True if the intersection of non-null data is equal (NaN positions don't matter). Uses `duck_array_ops.array_notnull_equiv` as the equivalence function.

### `reduce(self, func, dim=None, axis=None, keep_attrs=None, keepdims=False, allow_lazy=False, **kwargs) -> Variable`
Applies a reduction function along dimension(s):
1. If `dim is common.ALL_DIMS`, treat as None (full reduction).
2. Reject both `dim` and `axis` supplied simultaneously.
3. Convert dim to axis via `get_axis_num`.
4. Use `.data` if `allow_lazy=True`, else `.values`.
5. Call `func(input_data, axis=axis, **kwargs)` or `func(input_data, **kwargs)`.
6. If output shape equals input shape (no reduction), keep all dims; otherwise compute removed axes and either keepdims (insert np.newaxis slices) or drop them from dim list.
7. Handle scalar results: if data has no `.shape`, wrap in array with proper slicing for keepdims.
8. Merge attrs based on `keep_attrs` (default False, controlled by `_get_keep_attrs`).

### `fillna(self, value) -> Variable`
Delegates to `ops.fillna(self, value)`.

### `where(self, cond, other=dtypes.NA) -> Variable`
Delegates to `ops.where_method(self, cond, other)`.

### `quantile(self, q, dim=None, interpolation='linear') -> Variable`
Computes quantiles via `np.nanpercentile`:
- Rejects dask arrays (raises TypeError).
- Converts q to float64 array.
- Computes output dims: removes reduced dims; prepends `'quantile'` if q is multi-valued.
- Calls `np.nanpercentile(self.data, q * 100., axis=axis, interpolation=interpolation)`.

### `rank(self, dim, pct=False) -> Variable`
Ranks data along a dimension using the bottleneck library:
- Rejects dask arrays (raises TypeError).
- Uses `bn.nanrankdata` for float dtypes, `bn.rankdata` otherwise.
- If `pct=True`, divides by count of non-NaN values per axis.

### `rolling_window(self, dim, window, window_dim, center=False, fill_value=dtypes.NA) -> Variable`
Creates a rolling window view along one dimension with a new trailing dimension:
1. Resolve dtype/fill_value if NA; convert data to appropriate dtype.
2. Calls `duck_array_ops.rolling_window(array, axis, window, center, fill_value)`.
3. Returns new Variable with dims = original + `(window_dim,)`.

### `coarsen(self, windows, func, boundary='exact', side='left') -> Variable`
Applies a function over coarsened (binned) windows:
1. Filter windows to only those dimensions present in self; if none, return copy.
2. Calls `_coarsen_reshape(windows, boundary, side)` to get reshaped data and axis tuple.
3. If func is string, resolve via `duck_array_ops`; raise NameError if not found.
4. Apply func over the computed axes; return new Variable with attrs preserved.

### `_coarsen_reshape(self, windows, boundary, side) -> Tuple[numpy.ndarray, tuple[int]]`
Reshapes data for coarsening:
1. Normalize boundary/side to dicts (one entry per window dim).
2. Validate window sizes > 0; validate boundary values are 'exact', 'trim', or 'pad'.
3. For each dimension: if 'exact', verify size is divisible by window; if 'trim', slice off excess (left or right based on side); if 'pad', pad with fill_value to reach next multiple of window.
4. Compute new shape: for coarsened dims, split into `(size/window, window)` pairs; for others, keep original size.
5. Return `variable.data.reshape(shape), tuple(axes)`.

### `real` → Variable
Returns a Variable with `.data.real`, preserving dims/attrs.

### `imag` → Variable
Returns a Variable with `.data.imag`, preserving dims/attrs.

### `_to_numeric(self, offset=None, datetime_unit=None, dtype=float) -> Variable`
Converts datetime arrays to numeric via `duck_array_ops.datetime_to_numeric`; returns new Variable.

## Array Wrapping & Arithmetic (injected by ops module)

After class definition, `ops.inject_all_ops_and_reduce_methods(Variable)` injects:
- All numpy ufuncs as unary/binary operations (`_unary_op`, `_binary_op`).
- In-place binary operators (`_inplace_binary_op`).
- Reduction methods like `sum`, `mean`, `min`, `max`, etc.

### `_unary_op(f)` (static method factory)
Wraps a numpy ufunc: calls `f(self.data, *args, **kwargs)` with error state suppressed; wraps result in Variable via `__array_wrap__`.

### `_binary_op(f, reflexive=False, **ignored_kwargs)` (static method factory)
Binary arithmetic between Variables or scalar/array-like:
1. If other is DataArray/Dataset, return NotImplemented.
2. Broadcast self and other via `_broadcast_compat_data` to get aligned data + dims.
3. Apply `f(self_data, other_data)` (or reflexive swap); suppress numpy errors.
4. Return new Variable with result data and merged attrs (per `_get_keep_attrs`).

### `_inplace_binary_op(f)` (static method factory)
In-place operations (`__iadd__`, etc.): validates dims unchanged; broadcasts via `_broadcast_compat_data`; assigns `self.values = f(self_data, other_data)`. Raises TypeError for Dataset.

### `__array_wrap__(self, obj, context=None)`
Wraps numpy array result as `Variable(self.dims, obj)`.

---

# Class: IndexVariable(Variable)

**Inheritance:** `Variable`

A specialized Variable that stores data as a `pandas.Index` (immutable, always 1D). Used for coordinate/index variables.

## Constructor: `__init__(self, dims, data, attrs=None, encoding=None, fastpath=False)`
- Calls `super().__init__()`.
- Validates `ndim == 1`; raises `ValueError` otherwise.
- If `_data` is not already a `PandasIndexAdapter`, wraps it: `self._data = PandasIndexAdapter(self._data)`.

## Methods & Overrides

### `load() -> IndexVariable`
No-op; data is always in memory. Returns self.

### `data` setter (overridden)
Calls parent's setter, then ensures `_data` is wrapped in `PandasIndexAdapter`.

### `chunk(self, chunks=None, name=None, lock=False) -> IndexVariable`
Dummy: returns shallow copy (`self.copy(deep=False)`). IndexVariables cannot be chunked.

### `_finalize_indexing_result(dims, data) -> Variable | IndexVariable`
If result is 1D, return `IndexVariable`; otherwise fall back to base `Variable`.

### `__setitem__(self, key, value)`
Always raises `TypeError` (values are immutable).

### `concat(cls, variables, dim='concat_dim', positions=None, shortcut=False) -> IndexVariable` (classmethod)
Specialized for IndexVariables: preserves pandas.Index objects without converting to numpy.
1. Validate all inputs are IndexVariable; raise TypeError otherwise.
2. Extract underlying indexes via `.data.array`; append them together (`indexes[0].append(indexes[1:])`).
3. If positions provided, apply inverse permutation reordering.
4. Merge attrs (validate dims consistency on non-shortcut).
5. Return `cls(first_var.dims, data, attrs)`.

### `copy(self, deep=True, data=None) -> IndexVariable`
- If `data is None`: for deep copy, create new `PandasIndexAdapter(self._data.array.copy(deep=True))`; for shallow, share `_data`.
- If `data is not None`: convert via `as_compatible_data`; validate shape.
- Return new IndexVariable with same dims/attrs/encoding.

### `equals(self, other, equiv=None) -> bool`
If `equiv is not None`, delegate to parent; otherwise use native pandas index equality: compares dims and calls `_data_equals(other)` (which converts both to pandas.Index and uses `.equals()`).

### `_data_equals(self, other) -> bool`
Converts both to pandas.Index via `.to_index()` and calls `.equals()`.

### `to_index_variable() -> IndexVariable` / `to_coord`
Returns self (already an IndexVariable).

### `to_index() -> pd.Index`
Extracts the underlying pandas index from `_data.array`; for MultiIndex, sets default names for unnamed levels; otherwise sets name to `self.name`.

### `level_names` → tuple or None
Returns `index.names` if the underlying index is a `pd.MultiIndex`, else None.

### `get_level_variable(self, level) -> IndexVariable`
Returns a new IndexVariable from a given MultiIndex level value. Raises ValueError if not a MultiIndex.

### `name` → Hashable / setter
- **Getter**: Returns `self.dims[0]` (the sole dimension name).
- **Setter**: Always raises `AttributeError`.

---

# Module-Level Backwards Compatibility Alias

### `Coordinate = utils.alias(IndexVariable, 'Coordinate')`
Creates an alias for `IndexVariable` named `'Coordinate'` for backwards compatibility.