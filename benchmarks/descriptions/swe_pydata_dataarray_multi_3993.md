## xarray/core/dataarray.py
The complete natural-language specification of `xarray/core/dataarray.py` (4294 lines) has been written to `/tmp/omp_desc_hlxbwshk/xarray/core/dataarray_spec.md`. It covers:

1. **All imports** — 70+ import statements with exact module paths and conditional TYPE_CHECKING blocks
2. **Module-level constants** — `_THIS_ARRAY` sentinel
3. **Helper functions** — `_infer_coords_and_dims`, `_check_data_shape`
4. **Helper class** — `_LocIndexer` with `__slots__`, `__getitem__`, `__setitem__`
5. **The `DataArray` class** in full:
   - Slots, class-level attributes (`_groupby_cls`, `_rolling_cls`, etc.), accessor descriptors (`dt`, `plot`, `str`)
   - Constructor with all 7 parameters and fastpath mode
   - All internal helpers (`_replace`, `_replace_maybe_drop_dims`, `_overwrite_indexes`, `_to_temp_dataset`, `_from_temp_dataset`, `_to_dataset_split`, `_to_dataset_whole`)
   - Public conversion methods (`to_dataset`, `to_pandas`, `to_dataframe`, `to_series`, `to_masked_array`, `to_netcdf`, `to_dict`, `from_dict`, `from_series`, `to_cdms2`, `from_cdms2`, `to_iris`, `from_iris`)
   - All indexing methods (`__getitem__`, `__setitem__`, `__delitem__`, `isel`, `sel`, `head`, `tail`, `thin`, `loc`)
   - Broadcasting/reindexing (`broadcast_like`, `reindex`, `reindex_like`)
   - Interpolation (`interp`, `interp_like`)
   - Dimension manipulation (`rename`, `swap_dims`, `expand_dims`, `set_index`, `reset_index`, `reorder_levels`, `stack`, `unstack`, `to_unstacked_dataset`)
   - Transposition, dropping, filling, reduction methods
   - Arithmetic operators via `_unary_op`, `_binary_op`, `_inplace_binary_op` factories
   - Calculus (`differentiate`, `integrate`), sorting, quantile, rank, padding, polynomial fitting
   - Dask integration (all `__dask_*` protocol methods)
   - Comparison methods (`equals`, `broadcast_equals`, `identical`)
   - Index-of-min/max (`idxmin`, `idxmax`, `argmin`, `argmax`)
   - The final `ops.inject_all_ops_and_reduce_methods(DataArray, priority=60)` call

## xarray/core/dataset.py
Now I have read all 7009 lines of the file. Let me compile the complete natural-language specification:

---

# Module Specification: `xarray/core/dataset.py` (7009 lines)

## 1. Imports

```python
import copy, datetime, functools, sys, warnings
from collections import defaultdict
from distutils.version import LooseVersion
from html import escape
from numbers import Number
from operator import methodcaller
from pathlib import Path
from typing import (TYPE_CHECKING, Any, Callable, DefaultDict, Dict, Hashable,
                    Iterable, Iterator, List, Mapping, MutableMapping, Optional,
                    Sequence, Set, Tuple, TypeVar, Union, cast, overload)

import numpy as np
import pandas as pd
import xarray as xr

from ..coding.cftimeindex import _parse_array_of_cftime_strings
from ..plot.dataset_plot import _Dataset_PlotMethods
from . import (alignment, dtypes, duck_array_ops, formatting, formatting_html,
               groupby, ops, resample, rolling, utils, weighted)
from .alignment import (_broadcast_helper, _get_broadcast_dims_map_common_coords, align)
from .common import (DataWithCoords, ImplementsDatasetReduce,
                     _contains_datetime_like_objects)
from .coordinates import (DatasetCoordinates, assert_coordinate_consistent,
                          remap_label_indexers)
from .duck_array_ops import datetime_to_numeric
from .indexes import (Indexes, default_indexes, isel_variable_and_index,
                      propagate_indexes, remove_unused_levels_categories,
                      roll_index)
from .indexing import is_fancy_indexer
from .merge import (dataset_merge_method, dataset_update_method,
                    merge_coordinates_without_align, merge_data_and_coords)
from .missing import get_clean_interp_index
from .options import OPTIONS, _get_keep_attrs
from .pycompat import is_duck_dask_array, sparse_array_type
from .utils import (Default, Frozen, HybridMappingProxy, SortedKeysDict,
                    _default, decode_numpy_dict_values, drop_dims_from_indexers,
                    either_dict_or_kwargs, hashable, infix_dims, is_dict_like,
                    is_scalar, maybe_wrap_array)
from .variable import (IndexVariable, Variable, as_variable,
                       assert_unique_multiindex_level_names, broadcast_variables)

if TYPE_CHECKING:
    from ..backends import AbstractDataStore, ZarrStore
    from .dataarray import DataArray
    from .merge import CoercibleMapping
    T_DSorDA = TypeVar("T_DSorDA", DataArray, "Dataset")
    try:
        from dask.delayed import Delayed
    except ImportError:
        Delayed = None
```

## 2. Module-Level Constants & Functions

### `_DATETIMEINDEX_COMPONENTS` (list)
A list of strings naming attributes of `pd.DatetimeIndex` that are ndarrays of time info:
`["year", "month", "day", "hour", "minute", "second", "microsecond", "nanosecond", "date", "time", "dayofyear", "weekofyear", "dayofweek", "quarter"]`.

### `_get_virtual_variable(variables, key: Hashable, level_vars: Mapping = None, dim_sizes: Mapping = None) -> Tuple[Hashable, Hashable, Variable]`
Retrieves a virtual variable (e.g., `'time.year'` from a datetime coordinate or a MultiIndex level) from a dict of `Variable` objects.

Logic:
1. If `level_vars`/`dim_sizes` is None, initialize to `{}`.
2. If `key` is in `dim_sizes`, create an `IndexVariable` with `pd.Index(range(dim_sizes[key]), name=key)` and return `(key, key, variable)`.
3. If `key` is not a string, raise `KeyError(key)`.
4. Split `key` on `"."` (max 1 split). If result has length 2: `ref_name`, `var_name = split_key`; if length 1: `ref_name, var_name = key, None`.
5. If `ref_name` is in `level_vars`: get the dimension variable from `variables[level_vars[ref_name]]`, convert to index variable, and retrieve level variable via `.get_level_variable(ref_name)`. Otherwise, look up `ref_var = variables[ref_name]`.
6. If `var_name` is None: `virtual_var = ref_var`, `var_name = key`. Else if `ref_var` contains datetime-like objects: wrap in `xr.DataArray`, get attribute via `.dt.<var_name>`, extract data; otherwise use `getattr(ref_var, var_name).data`. Create `Variable(ref_var.dims, data)`.
7. Return `(ref_name, var_name, virtual_var)`.

### `calculate_dimensions(variables: Mapping[Hashable, Variable]) -> Dict[Hashable, int]`
Calculates dimension sizes from a set of variables. Returns `{dim_name: size}` dict. Raises `ValueError` if any dimension has conflicting sizes across variables or if a dimension name conflicts with a scalar variable name.

Logic:
1. Identify `scalar_vars = {k for k,v in variables.items() if not v.dims}`.
2. Iterate over each `(k, var)`. For each `(dim, size)` in `zip(var.dims, var.shape)`:
   - If `dim` is a scalar variable name: raise `ValueError("dimension %r already exists as a scalar variable" % dim)`.
   - If `dim` not yet in `dims`: record it and set `last_used[dim] = k`.
   - Else if `dims[dim] != size`: raise `ValueError("conflicting sizes for dimension...")`.

### `merge_indexes(indexes, variables, coord_names, append=False) -> Tuple[Dict[Hashable, Variable], Set[Hashable]]`
Merges variables into multi-indexes. Used by `Dataset.set_index`.

Logic:
1. For each `(dim, var_names)` in `indexes`: normalize `var_names` to list if single string/sequence.
2. Validate all variable names exist and have consistent dimension with current index variable (if any).
3. If a current index variable exists and `append=True`, extend names/codes/levels from existing MultiIndex or create categorical from non-MultiIndex.
4. For each var name: get its values, create `pd.Categorical`, extract codes/categories. If single var_name and no existing names: use `pd.Index(values)`. Otherwise build `pd.MultiIndex(levels, codes, names=names)`. Track `dims_to_replace` mapping old dim → new level names for MultiIndex case.
5. Create `IndexVariable(dim, idx)` in `vars_to_replace`, add var_names to `vars_to_remove`.
6. Build `new_variables`: exclude removed vars, update with replaced ones. Update dims of any variable whose dims reference a replaced dimension via `dims_to_replace`.
7. Return `(new_variables, coord_names | set(vars_to_replace) - set(vars_to_remove))`.

### `split_indexes(dims_or_levels, variables, coord_names, level_coords, drop=False) -> Tuple[Dict[Hashable, Variable], Set[Hashable]]`
Extracts (multi-)indexes as separate variables. Used by `Dataset.reset_index`.

Logic:
1. Normalize `dims_or_levels` to list. Separate into dimension names and MultiIndex levels using `level_coords` mapping.
2. For each plain dimension `d`: get its index; if not a MultiIndex, add to `vars_to_remove`; if not `drop`, create variable `str(d)+"_"` from the index values preserving attrs.
3. For each `(d, levs)` in `dim_levels`: get index; if all levels removed (`len(levs) == index.nlevels`), remove dimension var; else replace with `droplevel`. If not `drop`, create variables for each level value.
4. Build new variables dict, update coord_names.

### `_assert_empty(args: tuple, msg="%s") -> None`
Raises `ValueError(msg % args)` if `args` is non-empty.

### `_check_chunks_compatibility(var, chunks, preferred_chunks)`
Warns (via `warnings.warn`) if specified Dask chunks would separate disk chunk shapes for any dimension where both are present and the chunk size is not evenly divisible by the preferred chunk size.

### `_get_chunk(var, chunks) -> Dict[Hashable, Tuple[int, ...]]`
Computes explicit chunk sizes for a variable using dask's `normalize_chunks`, accounting for backend preferred chunking. Returns `{dim: chunk_tuple}` dict. Skips IndexVariables. Handles int/'auto' chunks by broadcasting to all dims.

### `_maybe_chunk(name, var, chunks, token=None, lock=False, name_prefix="xarray-", overwrite_encoded_chunks=False)`
Converts or rechunks a variable into dask. If `chunks` is not None and `var.ndim > 0`: tokenize with `(name, token, var._data, chunks)`, create new name `{prefix}{name}-{token}`, call `var.chunk(chunks, name=name2, lock=lock)`. If `overwrite_encoded_chunks` and var has chunks, set `encoding["chunks"] = tuple(x[0] for x in var.chunks)`. Returns the (possibly chunked) variable.

### `as_dataset(obj: Any) -> "Dataset"`
Casts object to Dataset. If obj has `.to_dataset()`, calls it. If not already a Dataset, wraps in `Dataset(obj)`.

## 3. Classes

### `class DataVariables(Mapping[Hashable, "DataArray"])`
A mapping view over data variables (non-coordinate variables) of a Dataset.

**Slots:** `_dataset: Dataset`

**Methods:**
- `__init__(self, dataset: Dataset)` — stores reference.
- `__iter__() -> Iterator[Hashable]` — yields keys from `self._dataset._variables` that are not in `self._dataset._coord_names`.
- `__len__() -> int` — returns `len(self._dataset._variables) - len(self._dataset._coord_names)`.
- `__contains__(key: Hashable) -> bool` — True if key is in `_variables` and not in `_coord_names`.
- `__getitem__(key: Hashable) -> DataArray` — returns `self._dataset[key]` if key not a coord; raises `KeyError` otherwise.
- `__repr__() -> str` — calls `formatting.data_vars_repr(self)`.
- `variables` (property) → `Mapping[Hashable, Variable]` — returns Frozen dict of Variable objects for data vars only.
- `_ipython_key_completions_()` — yields keys from parent completions excluding coord names.

### `class _LocIndexer`
Helper class for `.loc` attribute on Dataset.

**Slots:** `dataset: Dataset`

- `__init__(self, dataset: Dataset)` — stores reference.
- `__getitem__(key: Mapping[Hashable, Any]) -> Dataset` — if key is not dict-like, raises TypeError; otherwise returns `self.dataset.sel(key)`.

### `class Dataset(Mapping, ImplementsDatasetReduce, DataWithCoords)`
A multi-dimensional, in-memory array database resembling an in-memory representation of a NetCDF file. Variables, coordinates, and attributes form a self-describing dataset. One-dimensional variables with name equal to their dimension are index coordinates for label-based indexing.

**Class Attributes:**
- `_groupby_cls = groupby.DatasetGroupBy`
- `_rolling_cls = rolling.DatasetRolling`
- `_coarsen_cls = rolling.DatasetCoarsen`
- `_resample_cls = resample.DatasetResample`
- `_weighted_cls = weighted.DatasetWeighted`

**Slots:** `"_attrs", "_cache", "_coord_names", "_dims", "_encoding", "_close", "_indexes", "_variables", "__weakref__"`

**Attributes (initialized in `__init__` or lazily):**
- `_attrs: Optional[Dict[Hashable, Any]]` — global attributes.
- `_cache: Dict[str, Any]` — cache dict.
- `_coord_names: Set[Hashable]` — set of coordinate variable names.
- `_dims: Dict[Hashable, int]` — dimension name → size mapping.
- `_encoding: Optional[Dict[Hashable, Any]]` — encoding attributes.
- `_close: Optional[Callable[[], None]]` — cleanup callback for file handles.
- `_indexes: Optional[Dict[Hashable, pd.Index]]` — pandas index objects.
- `_variables: Dict[Hashable, Variable]` — all variables (data + coords).

#### `__init__(self, data_vars: Mapping = None, coords: Mapping = None, attrs: Mapping = None)`
1. Default both to `{}` if None.
2. If same key in both `data_vars` and `coords`: raise `ValueError`.
3. If `coords` is a Dataset, extract its `.variables`.
4. Call `merge_data_and_coords(data_vars, coords, compat="broadcast_equals")` → `(variables, coord_names, dims, indexes, _)`.
5. Set all slot attributes from the result; `_close = None`, `_encoding = None`.

#### Class Method: `load_store(cls, store, decoder=None) -> Dataset`
Creates a Dataset from a backend DataStore. Calls `store.load()` → `(variables, attributes)`. If decoder provided, applies it. Creates Dataset with variables and attrs. Sets close callback via `set_close(store.close)`.

#### Properties (Dataset):
- **`variables`** → `Frozen(self._variables)` — all Variable objects including coords.
- **`attrs`** → `Dict[Hashable, Any]` — global attributes; lazily initialized to `{}` if None. Setter: replaces with `dict(value)`.
- **`encoding`** → `Dict` — encoding dict; lazily initialized to `{}`. Setter: replaces with `dict(value)`.
- **`dims`** → `Frozen(SortedKeysDict(self._dims))` — dimension name → size mapping (read-only).
- **`sizes`** → same as `dims` (alias for consistency with DataArray).
- **`indexes`** → `Indexes(self._indexes)` — if `_indexes` is None, computes via `default_indexes(self._variables, self._dims)`.
- **`coords`** → `DatasetCoordinates(self)` — coordinate view.
- **`data_vars`** → `DataVariables(self)` — data variable view.
- **`nbytes`** → `int` — sum of `v.nbytes` for all variables.
- **`chunks`** → `Frozen(SortedKeysDict(chunks))` — block dimensions per dim; raises ValueError if inconsistent chunks across variables.
- **`loc`** → `_LocIndexer(self)` — label-based indexer.

#### Dask Integration Methods:
- **`__dask_tokenize__(self)`** — returns `normalize_token((type(self), self._variables, self._coord_names, self._attrs))`.
- **`__dask_graph__(self)`** — merges dask graphs from all variables; returns HighLevelGraph or sharedict.
- **`__dask_keys__()`, `__dask_layers__()`** — aggregate keys/layers from dask-collection variables.
- **`__dask_optimize__`**, **`__dask_scheduler__`** — delegate to `da.Array`.
- **`__dask_postcompute__(self)`** / **`__dask_postpersist__(self)`** — return `(method, args)` tuples for reconstructing Dataset from dask results.
- **`_dask_postcompute(results, info, *args)`** (static) — reconstructs variables from computed results and calls `_construct_direct`.
- **`_dask_postpersist(dsk, info, *args)`** (static) — similar but handles persist mode by filtering dask keys.

#### Core Construction/Replacement Methods:
- **`_construct_direct(cls, variables, coord_names, dims=None, attrs=None, indexes=None, encoding=None, close=None)`** — bypasses `__init__`. If dims is None, computes via `calculate_dimensions`. Uses `object.__new__(cls)` and sets all slots directly.
- **`_replace(self, variables=None, coord_names=None, dims=None, attrs=_default, indexes=_default, encoding=_default, inplace=False) -> Dataset`** — returns new or modified dataset with replaced attributes. If `inplace=True`, mutates self; else copies mutable args and creates via `_construct_direct`.
- **`_replace_with_new_dims(self, variables, coord_names=None, attrs=_default, indexes=_default, inplace=False)`** — recalculates dims from variables then calls `_replace`.
- **`_replace_vars_and_dims(self, variables, coord_names=None, dims=None, attrs=_default, inplace=False)`** (deprecated) — like above but always passes `indexes=None` to force index recalculation.
- **`_overwrite_indexes(self, indexes: Mapping[Any, pd.Index]) -> Dataset`** — updates variable and index dicts with new IndexVariables; renames dims if MultiIndex name differs from dim name.

#### Lifecycle Methods:
- **`load(self, **kwargs) -> Dataset`** — loads lazy dask arrays via `da.compute(*lazy_data.values(), **kwargs)` in-place, then calls `.load()` on non-dask variables. Returns self.
- **`compute(self, **kwargs) -> Dataset`** — shallow copy then load.
- **`persist(self, **kwargs) -> Dataset`** — shallow copy then `_persist_inplace`.
- **`_persist_inplace(self, **kwargs)`** — persists dask arrays via `dask.persist()`, updates in-place. Returns self.
- **`copy(self, deep=False, data=None) -> Dataset`** — if data is None: copies all variables with `deep`; else validates that data keys match original data var keys exactly, then creates new variables using per-variable copy with data override. Deep-copies attrs. Returns via `_replace`.

#### Internal Helpers:
- **`_level_coords`** (property) → `Dict[str, Hashable]` — maps MultiIndex level names to their dimension name.
- **`_copy_listed(self, names: Iterable[Hashable]) -> Dataset`** — creates new Dataset with only listed variables and relevant coordinates. Handles virtual variables via `_get_virtual_variable`. Preserves needed dims and indexes.
- **`_construct_dataarray(self, name: Hashable) -> DataArray`** — constructs a DataArray from internal variable (handling virtual vars), including all coordinate variables whose dims are subset of the target's dims.
- **`__copy__()`, `__deepcopy__(self, memo=None)`** — delegate to `copy(deep=False/True)`.

#### Attribute/Item Access:
- **`_attr_sources`** (property) → yields `_item_sources` then `attrs`.
- **`_item_sources`** (property) → yields `data_vars`, `HybridMappingProxy(coords)`, `HybridMappingProxy(dims, self)` for virtual coords, empty `HybridMappingProxy(level_coords)`.

#### Mapping Protocol:
- **`__contains__(key: object) -> bool`** — checks `key in self._variables`.
- **`__len__() -> int`** — returns `len(self.data_vars)`.
- **`__bool__() -> bool`** — truthiness based on data vars.
- **`__iter__() -> Iterator[Hashable]`** — iterates over data vars.
- **`__array__(self, dtype=None)`** — raises TypeError (datasets cannot be converted to numpy arrays directly).
- **`__getitem__(self, key)`** — overloaded: if dict-like → `self.isel(**key)`; if hashable → `_construct_dataarray(key)`; else → `_copy_listed(np.asarray(key))`.
- **`__setitem__(self, key: Hashable, value) -> None`** — calls `self.update({key: value})`; raises NotImplementedError for dict-like keys.
- **`__delitem__(self, key: Hashable) -> None`** — deletes from `_variables`, removes from `_coord_names`, removes from `_indexes`, recalculates dims.
- **`__hash__ = None`** — unhashable.

#### Comparison Methods:
- **`_all_compat(self, other: Dataset, compat_str: str) -> bool`** — checks coord names match and all variables are compatible via `getattr(var, compat_str)(other_var)`.
- **`broadcast_equals(self, other: Dataset) -> bool`** — calls `_all_compat(other, "broadcast_equals")`; catches TypeError/AttributeError → False.
- **`equals(self, other: Dataset) -> bool`** — calls `_all_compat(other, "equals")`.
- **`identical(self, other: Dataset) -> bool`** — checks `utils.dict_equiv(self.attrs, other.attrs)` and `_all_compat(other, "identical")`.

#### Coordinate Management:
- **`set_coords(self, names) -> Dataset`** — converts existing variables to coordinates. Validates all names exist in dataset (via `_assert_all_in_dataset`). Returns copy with updated `_coord_names`.
- **`reset_coords(self, names=None, drop=False) -> Dataset`** — converts coords back to data vars or drops them. Default: reset all non-dimension coords. If `drop=True`, removes from `_variables`. Validates dimension coordinates cannot be removed.

#### I/O Methods:
- **`dump_to_store(self, store, **kwargs)`** — delegates to `backends.api.dump_to_store`.
- **`to_netcdf(self, path=None, mode="w", format=None, group=None, engine=None, encoding={}, unlimited_dims=None, compute=True, invalid_netcdf=False) -> Union[bytes, Delayed, None]`** — delegates to `backends.api.to_netcdf`.
- **`to_zarr(self, store=None, chunk_store=None, mode=None, synchronizer=None, group=None, encoding={}, compute=True, consolidated=False, append_dim=None, region=None) -> ZarrStore`** — delegates to `backends.api.to_zarr`.

#### Display Methods:
- **`__repr__() -> str`** — calls `formatting.dataset_repr(self)`.
- **`_repr_html_(self)`** — returns HTML representation or escaped text based on `OPTIONS["display_style"]`.
- **`info(self, buf=None)`** — writes netCDF-style summary to buffer (dimensions, variables with dtype/dims/attrs, global attributes).

#### Indexing Methods:
- **`_validate_indexers(self, indexers, missing_dims="raise") -> Iterator[Tuple[Hashable, ...]]`** — validates and normalizes indexer dict. Drops dims not in dataset per `missing_dims`. Yields `(key, normalized_value)` for each indexer. Handles int/slice/Variable/DataArray/tuple/Dataset (raises TypeError)/empty-sequence → empty array/string arrays with datetime conversion.
- **`_validate_interp_indexers(self, indexers) -> Iterator[Tuple[Hashable, Variable]]`** — variant for interpolation; converts to IndexVariable where appropriate.
- **`_get_indexers_coords_and_indexes(self, indexers)`** — extracts coordinates from DataArray indexers (excluding those already in self). Returns `(attached_coords, attached_indexes)`.

- **`isel(self, indexers=None, drop=False, missing_dims="raise", **indexers_kwargs) -> Dataset`** — integer-based indexing. If any fancy indexer: delegates to `_isel_fancy`. Otherwise fast path: for each variable, apply relevant indexers via `var.isel(var_indexers)`. Updates coord_names if dropped scalar coords. Updates indexes for 1D coordinate vars. Returns via `_construct_direct`.

- **`_isel_fancy(self, indexers, *, drop, missing_dims="raise") -> Dataset`** — fancy/boolean indexing path. For each variable: handles MultiIndex variables via `isel_variable_and_index`; drops if in indexers and drop=True; otherwise applies `var.isel()`. Extracts coordinates from indexers and merges.

- **`sel(self, indexers=None, method=None, tolerance=None, drop=False, **indexers_kwargs) -> Dataset`** — label-based indexing. Calls `remap_label_indexers()` to get position indexers, then calls `isel(pos_indexers, drop=drop)` and `_overwrite_indexes(new_indexes)`.

- **`head(self, indexers=None, **kwargs)`, `tail(self, indexers=None, **kwargs)`, `thin(self, indexers=None, **kwargs)`** — convenience methods wrapping `isel` with slice(indexers), slice(-val,None), or slice(None,None,val). Default n=5.

- **`broadcast_like(self, other: Union[Dataset, DataArray], exclude=None) -> Dataset`** — broadcasts self against another object using `align()` and `_broadcast_helper()`.

- **`reindex_like(self, other, method=None, tolerance=None, copy=True, fill_value=dtypes.NA) -> Dataset`** — conforms to other's indexes. Calls `alignment.reindex_like_indexers()` then `self.reindex(...)`.

- **`reindex(self, indexers=None, method=None, tolerance=None, copy=True, fill_value=dtypes.NA, **kwargs)`** — delegates to `_reindex()`.

- **`_reindex(self, indexers=None, method=None, tolerance=None, copy=True, fill_value=dtypes.NA, sparse=False, **kwargs) -> Dataset`** — validates dims, calls `alignment.reindex_variables()` → `(variables, indexes)`, updates coord_names with indexer keys.

- **`interp(self, coords=None, method="linear", assume_sorted=False, kwargs=None, **coords_kwargs) -> Dataset`** — multidimensional interpolation via scipy. Validates indexers, computes shared dims, optionally sorts by `sortby()`. For each variable (skipping indexed coords): if dtype is numeric and has indexer dims, calls `missing.interp(var, var_indexers, method, **kwargs)`. Attaches new coordinate variables and their indexes. Extracts coordinates from original coords.

- **`interp_like(self, other, method="linear", assume_sorted=False, kwargs=None) -> Dataset`** — interpolates onto another object's coordinates. Separates numeric vs object coords; reindexes on object coords then interpolates on numeric ones.

#### Renaming Methods:
- **`_rename_vars(self, name_dict, dims_dict)`** → `(variables, coord_names)` — renames variables and their dims per dicts. Raises ValueError if new name conflicts.
- **`_rename_dims(self, name_dict)`** → dict of renamed dims.
- **`_rename_indexes(self, name_dict, dims_set)`** → renamed indexes (handles MultiIndex renaming).
- **`_rename_all(self, name_dict, dims_dict)`** — combines all three rename helpers.

- **`rename(self, name_dict=None, **names) -> Dataset`** — renames both variables and dimensions simultaneously. Validates keys exist in dataset or dims. Calls `_rename_all(name_dict=name_dict, dims_dict=name_dict)`. Asserts unique MultiIndex level names.
- **`rename_dims(self, dims_dict=None, **dims) -> Dataset`** — renames only dimensions. Validates new name doesn't conflict with existing dim/variable.
- **`rename_vars(self, name_dict=None, **names) -> Dataset`** — renames only variables (including coords).

- **`swap_dims(self, dims_dict=None, **dims_kwargs) -> Dataset`** — swaps dimension names using a coordinate variable as the new dimension. Validates old dim exists and new dim is either a 1D coord along old dim or not yet present. Converts relevant vars to IndexVariable with updated index; others to base Variable.

#### Dimension Expansion/Stacking:
- **`expand_dims(self, dim=None, axis=None, **dim_kwargs) -> Dataset`** — inserts new axes of size 1 (or with coordinates). Handles dim as single hashable, sequence, or mapping. Validates no duplicate dims, no conflicts with existing variables. For each variable: if in `dim`, promotes to index var; else inserts new dimensions at specified axis positions using `set_dims()`.

- **`set_index(self, indexes=None, append=False, **indexes_kwargs) -> Dataset`** — creates MultiIndex from existing variables. Calls `merge_indexes()` then `_replace_vars_and_dims()`.

- **`reset_index(self, dims_or_levels, drop=False) -> Dataset`** — extracts MultiIndex levels as separate variables. Calls `split_indexes()` then `_replace_vars_and_dims()`.

- **`reorder_levels(self, dim_order=None, **dim_order_kwargs) -> Dataset`** — reorders levels of a MultiIndex dimension. Validates MultiIndex exists, creates new IndexVariable and index with reordered levels.

- **`_stack_once(self, dims, new_dim)`** — stacks dimensions into one (called by `stack`). Handles ellipsis via `infix_dims()`. For each variable: expands missing dims, calls `.stack()`. Creates MultiIndex from product of level indices.

- **`stack(self, dimensions=None, **dimensions_kwargs) -> Dataset`** — stacks multiple dimension pairs sequentially via `_stack_once()`. Ellipsis replaces unlisted dims.

- **`to_stacked_array(self, new_dim, sample_dims, variable_dim="variable", name=None) -> DataArray`** — combines variables of differing dimensionality into a single DataArray without broadcasting. Validates all vars share `sample_dims`. For each var: assigns coords, expands missing stacking dims + variable_dim, stacks. Concatenates along new_dim. Coerces MultiIndex level dtypes to match input dimensions.

- **`_unstack_once(self, dim, fill_value) -> Dataset`** — fast unstack for numpy arrays with MultiIndex. For each var: if has `dim`, calls `var._unstack_once(index, dim, fill_value_)`. Creates IndexVariables from index levels.

- **`_unstack_full_reindex(self, dim, fill_value, sparse) -> Dataset`** — full reindex-based unstack (for dask/sparse/non-numpy). Reindexes to full MultiIndex product if needed, then unstacks.

- **`unstack(self, dim=None, fill_value=dtypes.NA, sparse=False) -> Dataset`** — unstacks MultiIndexes into new dimensions. Default: all MultiIndex dims. Selects `_unstack_once` or `_unstack_full_reindex` based on array type (dask/sparse/non-numpy/old numpy → full reindex).

#### Mutation Methods:
- **`update(self, other: CoercibleMapping) -> Dataset`** — merges `other` into self in-place via `dataset_update_method()`, then `_replace(inplace=True, ...)`. Raises ValueError on dimension size conflicts.

- **`merge(self, other, overwrite_vars=frozenset(), compat="no_conflicts", join="outer", fill_value=dtypes.NA) -> Dataset`** — merges two datasets. Converts DataArray to Dataset if needed. Calls `dataset_merge_method()` with all parameters. Returns via `_replace(**result._asdict())`.

- **`_assert_all_in_dataset(self, names, virtual_okay=False)`** — validates all names exist in dataset (optionally including virtual variables). Raises ValueError otherwise.

- **`drop_vars(self, names, errors="raise") -> Dataset`** — drops named variables and their indexes. Filters `_variables`, `_coord_names`, and `indexes`. Recalculates dims via `_replace_with_new_dims()`.

- **`drop(self, labels=None, dim=None, errors="raise", **labels_kwargs)`** — backward-compatible wrapper routing to `drop_vars`, `drop_sel`, or deprecated paths with appropriate warnings.

- **`drop_sel(self, labels=None, errors="raise", **labels_kwargs) -> Dataset`** — drops index labels by dimension. For each dim: gets index, calls `index.drop(labels_for_dim, errors=errors)`, then uses `.loc[{dim: new_index}]`.

- **`drop_isel(self, indexers=None, **indexers_kwargs)`** — drops by integer position. Uses `index.delete(pos_for_dim)` for each dimension, then `.loc[dimension_index]`.

- **`drop_dims(self, drop_dims, errors="raise") -> Dataset`** — drops all variables containing specified dimensions. Collects variable names whose dims intersect with `drop_dims`, calls `drop_vars()`.

#### Transformation Methods:
- **`transpose(self, *dims) -> Dataset`** — reorders dimensions on each variable. Validates dim args match dataset dims (allowing `...`). Copies self then transposes each variable's dims.

- **`diff(self, dim, n=1, label="upper")`** — computes n-th order discrete difference. For data vars: `var.isel(end) - var.isel(start)`; for coords: uses appropriate slice. Recursively applies if n > 1. Updates index with new coordinate.

- **`shift(self, shifts=None, fill_value=dtypes.NA, **shifts_kwargs) -> Dataset`** — shifts data variables by offsets along dimensions. Coordinates stay in place. Per-variable shift with per-var fill values from dict.

- **`roll(self, shifts=None, roll_coords=None, **shifts_kwargs) -> Dataset`** — rolls (circularly shifts) variables and optionally coordinates. Warns about `roll_coords` default deprecation. Updates indexes via `roll_index()` if rolling coords.

- **`sortby(self, variables, ascending=True)`** — sorts dataset by labels/values of 1D DataArrays or variable names. Aligns with left join. Uses `np.lexsort()` for multiple keys per dimension (first key = primary). Returns `aligned_self.isel(**indices)`.

#### Reduction/Aggregation Methods:
- **`reduce(self, func, dim=None, keep_attrs=None, keepdims=False, numeric_only=False, **kwargs) -> Dataset`** — applies reduction function along dimensions. For each variable: if coord and no reduce dims → keep; else if numeric (or `not numeric_only`) → apply `var.reduce()`. Unpacks single-dim tuples for functions like argmin. Returns via `_replace_with_new_dims()`.

- **`map(self, func, keep_attrs=None, args=(), **kwargs) -> Dataset`** — applies function to each data variable. Uses `maybe_wrap_array()` on result. Copies attrs if `keep_attrs`. Creates new Dataset with results.

- **`apply(self, func, keep_attrs=None, args=(), **kwargs)`** — deprecated alias for `map()`, emits PendingDeprecationWarning.

- **`assign(self, variables=None, **variables_kwargs) -> Dataset`** — assigns new data vars (supporting callables). Computes all results first via `_calc_assign_results()`, then calls `update(results)`. Returns copy with additions.

#### Conversion Methods:
- **`to_array(self, dim="variable", name=None)`** — converts dataset to DataArray by stacking all data variables along a new dimension. Broadcasts vars, stacks `.data`, adds variable names as coordinate.

- **`_normalize_dim_order(self, dim_order=None) -> Dict[Hashable, int]`** — validates and returns ordered dims mapping (alphabetical if None).

- **`_to_dataframe(self, ordered_dims)`** — converts to pandas DataFrame: columns are non-dim vars flattened; index is Cartesian product of coords.

- **`to_dataframe(self, dim_order=None) -> pd.DataFrame`** — public wrapper for `_to_dataframe()`.

- **`_set_sparse_data_from_dataframe(self, idx, arrays, dims)`** / **`_set_numpy_data_from_dataframe(self, idx, arrays, dims)`** — internal helpers for `from_dataframe()` to populate data from DataFrame columns.

- **`from_dataframe(cls, dataframe: pd.DataFrame, sparse=False) -> Dataset`** — class method converting pandas DataFrame to Dataset. Validates unique columns and unique MultiIndex. Creates dimension variables from index levels. Populates data vars via sparse or numpy path.

- **`to_dask_dataframe(self, dim_order=None, set_index=False)`** — converts to dask.dataframe. Builds series for each column (dims + coords + data_vars), concatenates along axis=1. Optionally sets index.

- **`to_dict(self, data=True) -> dict`** — converts dataset to nested dict with `coords`, `data_vars`, `attrs`, `dims`. Uses `decode_numpy_dict_values()` on attrs and `variable.to_dict()` per var.

- **`from_dict(cls, d)` → Dataset** — class method reconstructing Dataset from dict format. Handles both flat `{name: {dims, data}}` and structured `{coords, data_vars, dims, attrs}` formats. Sets coords via `set_coords()`.

#### Arithmetic Operator Helpers (static methods):
- **`_unary_op(f)`** → decorator — wraps unary function to apply over non-coordinate variables only. Preserves attrs based on `keep_attrs` kwarg (default True). Returns `_replace_with_new_dims(variables, attrs=attrs)`.
- **`_binary_op(f, reflexive=False, join=None)`** → decorator — wraps binary operation. Aligns self and other if both are DataArray/Dataset using `OPTIONS["arithmetic_join"]` or explicit join. Calls `_calculate_binary_op()`.
- **`_inplace_binary_op(f)`** → decorator — wraps in-place operations (e.g., `__iadd__`). Reindexes other to self, converts op via `ops.inplace_to_noninplace_op`, calls `_calculate_binary_op(inplace=True)`, then replaces self's vars/indexes.

- **`_calculate_binary_op(self, f, other, join="inner", inplace=False)`** — core binary operation logic. If other is dict-like (not Dataset): applies over data vars directly. Otherwise: merges coords via `self.coords.merge(other_coords)`. For Dataset other: calls `apply_over_both()` on variables; for non-Dataset: broadcasts scalar against each data var. Updates `_variables` and recalculates dims.

- **`_copy_attrs_from(self, other)`** — copies attrs from other dataset to self (global + per-variable).

#### Missing Value Methods:
- **`dropna(self, dim, how="any", thresh=None, subset=None)`** — drops labels with missing values along dimension. Counts non-NA values per label across subset variables. Creates mask based on `how`/`thresh`, applies via `isel()`.

- **`fillna(self, value) -> Dataset`** — fills missing values using `ops.fillna()`. Validates dict-like value keys are in data vars.

- **`interpolate_na(self, dim=None, method="linear", limit=None, use_coordinate=True, max_gap=None, **kwargs)`** — fills NaNs via interpolation. Delegates to `_apply_over_vars_with_dim(interp_na, ...)`.

- **`ffill(self, dim, limit=None) -> Dataset`** / **`bfill(self, dim, limit=None) -> Dataset`** — forward/backward fill along dimension. Delegates to `missing._apply_over_vars_with_dim()`.

- **`combine_first(self, other: Dataset) -> Dataset`** — combines self with other, filling NaNs from other. Calls `ops.fillna(self, other, join="outer", dataset_join="outer")`.

#### Statistical Methods:
- **`quantile(self, q, dim=None, interpolation="linear", numeric_only=False, keep_attrs=None, skipna=True)`** — computes quantiles per variable. Adds a `"quantile"` coordinate with the quantile values. Handles both scalar and array `q`.

- **`rank(self, dim, pct=False, keep_attrs=None)`** — ranks data along dimension using bottleneck. Equal values get average rank. NaNs stay as NaN.

- **`differentiate(self, coord, edge_order=1, datetime_unit=None)`** — numerical differentiation via central differences. Converts datetime coords to numeric if needed. Applies `duck_array_ops.gradient()` per data variable.

- **`integrate(self, coord, datetime_unit=None) -> Dataset`** / **`_integrate_one(self, coord, datetime_unit=None)`** — trapezoidal integration along coordinate(s). Calls `_integrate_one()` for each coord in sequence. Converts datetime to numeric if needed. Applies `duck_array_ops.trapz()`.

#### Properties:
- **`real`** → `self.map(lambda x: x.real, keep_attrs=True)`
- **`imag`** → `self.map(lambda x: x.imag, keep_attrs=True)`
- **`plot`** → `utils.UncachedAccessor(_Dataset_PlotMethods)`

#### Filtering/Chunking:
- **`filter_by_attrs(self, **kwargs) -> Dataset`** — returns subset of variables matching attribute criteria. Each kwarg is `(attr_name, pattern)` where pattern can be a value or callable returning bool. Returns `self[selection]`.

- **`unify_chunks(self) -> Dataset`** — ensures all dask-array variables have consistent chunk sizes along shared dimensions using `dask.array.core.unify_chunks()`. Quick-exits if no dask arrays or already aligned.

- **`map_blocks(self, func, args=(), kwargs=None, template=None) -> T_DSorDA`** — applies function to each block of the dataset. Delegates to `parallel.map_blocks()`.

#### Fitting:
- **`polyfit(self, dim, deg, skipna=None, rcond=None, w=None, full=False, cov=False)`** — least-squares polynomial fit replicating numpy.polyfit with NaN skipping. Builds Vandermonde matrix from coordinate index. Handles weights, scaling, rank computation. For each data variable along `dim`: stacks other dims, computes coefficients via `duck_array_ops.least_squares()`, returns Dataset with `[var]_polyfit_coefficients`, optionally residuals/singular values/rank/covariance.

#### Padding:
- **`pad(self, pad_width=None, mode="constant", stat_length=None, constant_values=0, end_values=0, reflect_type=None, **pad_width_kwargs) -> Dataset`** — pads variables along dimensions. Data vars use specified `mode`; coords use `"edge"/"reflect"/"symmetric"/"wrap"` modes or `"constant"` with NA fill_value.

#### Index Methods:
- **`idxmin(self, dim=None, skipna=None, fill_value=dtypes.NA, keep_attrs=None)`** — returns coordinate labels of minimum values per variable. Delegates via `map(methodcaller("idxmin", ...))`.

- **`idxmax(self, dim=None, skipna=None, fill_value=dtypes.NA, keep_attrs=None)`** — same for maximum values.

- **`argmin(self, dim=None, axis=None, **kwargs) -> Dataset`** / **`argmax(self, dim=None, axis=None, **kwargs) -> Dataset`** — returns indices of min/max per variable. Warns about deprecation when called with no args. Single-dim case uses `reduce()`; multi-dim sequence raises ValueError (dict return cannot be stored in Dataset).

## 4. Module-Level Side Effect

```python
ops.inject_all_ops_and_reduce_methods(Dataset, array_only=False)
```
This call injects all arithmetic (`__add__`, `__sub__`, etc.), comparison (`__lt__`, `__eq__`, etc.), and reduction methods onto the `Dataset` class at module import time. The `array_only=False` parameter means these operators work on both array-like and scalar operands, delegating to `_binary_op`/`_unary_op` helpers as described above.