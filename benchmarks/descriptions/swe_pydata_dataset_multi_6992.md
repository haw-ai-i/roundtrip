## xarray/core/dataset.py
The complete specification for `xarray/core/dataset.py` has been written to `/tmp/omp_desc_umg3edzc/xarray/core/dataset_spec.md`. Here's a summary of what it covers:

**Structure:**
1. **Imports** — All imports listed precisely (numpy, pandas, xarray internals, TYPE_CHECKING conditionals)
2. **Constants & Globals** — `_NO_NAN_SCALAR`, `_DEFAULT_NAMES`, `VALID_STRING_TYPES`, `DATASET_FACTORY_LOCK`
3. **Helper Functions** — 10+ module-level utilities (`_get_axis_num`, `_validate_dtype`, `_infer_coords_and_dims`, etc.)
4. **Dataset Class** (§4) with full detail on:
   - **Attributes** (8 core instance attributes with types and initialization points)
   - **Properties** (~25 properties including `dims`, `sizes`, `data_vars`, `coords`, `variables`, `attrs`, `encoding`, `nbytes`, `chunksizes`, `real`, `imag`, `plot`)
   - **Magic Methods** (`__init__`, `__repr__`, `__getitem__`, `__setitem__`, `__delitem__`, `__iter__`, `__len__`, `__contains__`, all comparison operators, all arithmetic operators, `__abs__`, `__array__`, `__array_ufunc__`, pickle methods)
   - **Variable Management** (14 methods: `_replace`, `assign_coords`, `assign`, `rename`/`rename_dims`/`rename_vars`, `swap_dims`, `set_coords`, `reset_coords`, `reset_index`, `set_index`, `drop_vars`/`drop_sel`/`drop_idxr`/`drop_dims`/`drop_isel`)
   - **Selection/Indexing** (8 methods: `sel`, `isel`, `isel_fancy`, `isel_points`, `query`, etc.)
   - **Alignment/Broadcasting** (5 methods)
   - **Merge/Combine** (6 methods)
   - **Math/Stats** (~17 methods including `reduce`, `mean`, `std`, `var`, `median`, `sum`, `prod`, `min`, `max`, `argmin`, `argmax`, `idxmin`, `idxmax`, `count`, `nunique`, `first`, `last`, `quantile`)
   - **Array Manipulation** (7 methods: `stack`, `unstack`, `transpose`, `squeeze`, `expand_dims`, `roll`, `shift`)
   - **Polynomial/Curve Fitting** (`polyfit`, `curvefit` with full implementation logic)
   - **Padding/Differentiate/Integrate/Rank** (6 methods)
   - **Grouping/Rolling/Coarsening/Resampling** (7 methods)
   - **Calendar Conversion** (`convert_calendar`, `interp_calendar`)
   - **Serialization/I/O** (`to_netcdf`, `to_zarr`, `to_dataframe`, `from_dataframe`)
5. **Supporting Classes** — `_Dataset_PlotMethods`
6. **Key Design Patterns** — Immutability, variable-centric storage, index management, duck array support

## xarray/core/indexes.py
Here is the complete natural-language specification of `xarray/core/indexes.py`:

---

## Module-Level Preamble

### Imports

```python
from __future__ import annotations
import collections.abc
import copy
from collections import defaultdict
from typing import (
    TYPE_CHECKING, Any, Dict, Generic, Hashable, Iterable, Iterator,
    Mapping, Sequence, TypeVar, cast,
)
import numpy as np
import pandas as pd

from . import formatting, nputils, utils
from .indexing import IndexSelResult, PandasIndexingAdapter, PandasMultiIndexingAdapter
from .utils import Frozen, get_valid_numpy_dtype, is_dict_like, is_scalar

if TYPE_CHECKING:
    from .types import ErrorOptions, T_Index
    from .variable import Variable
```

### Constants & Type Aliases

- **`IndexVars`** — type alias for `Dict[Any, "Variable"]`. Represents a mapping of coordinate names to `Variable` objects.
- **`T_PandasOrXarrayIndex`** — a `TypeVar` bound to either `Index` or `pd.Index`, used as the generic parameter for the `Indexes` class.

---

## Free Functions

### `_sanitize_slice_element(x)`

Extracts a scalar value from an element that may be wrapped in a `Variable`, `DataArray`, or `np.ndarray`. If `x` is not a tuple and its numpy shape has non-zero dimensions, raises `ValueError`. Converts `Variable`/`DataArray` to `.values`; converts `np.ndarray` via `x[()]` (0-d view). Returns the scalar.

### `_query_slice(index, label, coord_name="", method=None, tolerance=None)`

Queries a pandas index using a slice object's start/stop/step. Calls `_sanitize_slice_element` on each boundary. Invokes `index.slice_indexer(...)`. If the result is not a `slice` (i.e., pandas converted it to an array indexer), raises `KeyError` with a message about unsorted/non-unique index. Returns the slice indexer. Raises `NotImplementedError` if `method` or `tolerance` is non-None.

### `_asarray_tuplesafe(values)`

Converts values into a numpy array of at most 1-dimension while preserving tuples. If `values` is a tuple, creates a 0-d object array via `utils.to_0d_object_array(values)`. Otherwise calls `np.asarray(values)`; if the result has ndim==2, creates an empty object array of length `len(values)` and assigns `values` into it element-wise. Returns the result.

### `_is_nested_tuple(possible_tuple)`

Returns `True` if `possible_tuple` is a tuple containing at least one element that is itself a `tuple`, `list`, or `slice`.

### `normalize_label(value, dtype=None) -> np.ndarray`

Normalizes a label for index selection. If the value has `ndim <= 1` (or defaults to 1), passes it through `_asarray_tuplesafe`. If `dtype` is provided and its kind is `"f"` (float) while `value.dtype.kind != "b"` (not boolean), casts `value` to `np.asarray(value, dtype=dtype)`. Returns the resulting numpy array.

### `as_scalar(value: np.ndarray)`

Converts a 0-d numpy array to a Python scalar. If `value.dtype.kind` is `"m"` (timedelta64) or `"M"` (datetime64), returns `value[()]`; otherwise returns `value.item()`.

### `get_indexer_nd(index, labels, method=None, tolerance=None)`

Wrapper around `pandas.Index.get_indexer` for n-dimensional label arrays. Flattens `labels` via `np.ravel(labels)`, calls `index.get_indexer(flat_labels, ...)`, then reshapes the result back to `labels.shape`. Returns the reshaped indexer array.

### `_check_dim_compat(variables: Mapping[Any, Variable], all_dims: str = "equal")`

Validates that multi-index variable candidates are 1-dimensional and dimensionally consistent. Raises `ValueError` if any variable has `ndim != 1`. If `all_dims == "equal"`, raises if variables have different dimensions (more than one unique dims tuple). If `all_dims == "different"`, raises if fewer unique dims exist than the number of variables (duplicate dimensions among variables).

### `remove_unused_levels_categories(index: pd.Index) -> pd.Index`

Cleans up a pandas index by removing unused levels/categories. For `pd.MultiIndex`: calls `index.remove_unused_levels()`. If any level is a `CategoricalIndex`, manually rebuilds the level values using `index.codes[i]` to filter each level, then reconstructs via `pd.MultiIndex.from_arrays(levels, names=index.names)`. For `pd.CategoricalIndex`: calls `index.remove_unused_categories()`. Returns the cleaned index.

### `create_default_index_implicit(dim_variable: Variable, all_variables: Mapping | Iterable[Hashable] | None = None) -> tuple[PandasIndex, IndexVars]`

Creates a default index from a dimension variable. If `all_variables` is not a `Mapping`, converts it to `{k: None for k in all_variables}`. Extracts the dimension name as `name = dim_variable.dims[0]`. Gets the underlying array via `getattr(dim_variable._data, "array", None)`.

- If the array is a `pd.MultiIndex`: creates a `PandasMultiIndex(array, name)`, calls `index.create_variables()`, then checks for conflicts between level names and variable names in `all_variables`. If there are fewer duplicate names than total levels (meaning both dimension coordinate and all level coordinates were given), skips the conflict check; otherwise raises `ValueError` if any conflicting variable is not equal to `dim_variable`.
- Otherwise: creates a `PandasIndex.from_variables({name: dim_variable})`, then calls `index.create_variables(dim_var)`.

Returns `(index, index_vars)`.

### `default_indexes(coords: Mapping[Any, Variable], dims: Iterable) -> dict[Hashable, Index]`

Builds default indexes for a Dataset/DataArray. Iterates over `coords.items()`. For each coordinate whose name is in `dims`, calls `create_default_index_implicit(var, coords)`. If all resulting index variable names are subsets of the original coord names, adds `{k: index for k in index_vars}` to the result dict. Returns the indexes dict.

### `indexes_equal(index: Index, other_index: Index, variable: Variable, other_variable: Variable, cache: dict[tuple[int, int], bool | None] = None) -> bool`

Checks if two indexes are equal with optional caching. Uses `(id(index), id(other_index))` as the cache key. If types match and `index.equals(other_index)` succeeds, caches and returns the result. Otherwise falls back to `variable.equals(other_variable)`. Returns a boolean.

### `indexes_all_equal(elements: Sequence[tuple[Index, dict[Hashable, Variable]]]) -> bool`

Checks if all index-element pairs in the sequence are equal. Defines an inner `check_variables()` that compares variables across elements. If all indexes share the same type, tries `indexes[0].equals(other_idx)` for each other; on `NotImplementedError`, falls back to variable comparison. If types differ, directly uses variable comparison. Returns `not not_equal`.

### `_apply_indexes(indexes: Indexes[Index], args: Mapping[Any, Any], func: str) -> tuple[dict[Hashable, Index], dict[Hashable, Variable]]`

Applies a method (`"isel"` or `"roll"`) to all indexes. Copies the input `indexes` dict. For each unique `(index, index_vars)` from `group_by_index()`, collects args for dimensions present in the index variables' dims. Calls `getattr(index, func)(index_args)`. If result is non-None: updates `new_indexes` with `{k: new_index for k in index_vars}` and merges `new_index.create_variables(index_vars)` into `new_index_variables`. If None: removes all keys of that index from `new_indexes`. Returns `(new_indexes, new_index_variables)`.

### `isel_indexes(indexes: Indexes[Index], indexers: Mapping[Any, Any]) -> tuple[dict[Hashable, Index], dict[Hashable, Variable]]`

Shorthand for `_apply_indexes(indexes, indexers, "isel")`. Returns the updated indexes and variables after positional selection.

### `roll_indexes(indexes: Indexes[Index], shifts: Mapping[Any, int]) -> tuple[dict[Hashable, Index], dict[Hashable, Variable]]`

Shorthand for `_apply_indexes(indexes, shifts, "roll")`. Returns the updated indexes and variables after rolling.

### `filter_indexes_from_coords(indexes: Mapping[Any, Index], filtered_coord_names: set) -> dict[Hashable, Index]`

Filters index items given a subset of coordinate names. Builds an `index_coord_names` mapping from `id(idx)` to sets of coordinate names sharing that index. For each group, if the group's coord names are not fully contained in `filtered_coord_names`, deletes all keys for that group from the result. Returns the filtered dict.

### `assert_no_index_corrupted(indexes: Indexes[Index], coord_names: set[Hashable]) -> None`

Asserts that removing specified coordinates will not corrupt indexes. For each `(index, index_coords)` from `group_by_index()`, computes the intersection with `coord_names`. If the intersection is non-empty but does not equal all of `index_coords` (partial overlap), raises `ValueError` listing the conflicting coordinate names and the full set of index coordinates.

---

## Classes

### `class Index`

**Docstring:** Base class inherited by all xarray-compatible indexes.

**Class Methods:**
- **`from_variables(cls, variables: Mapping[Any, Variable]) -> Index`**: Abstract; raises `NotImplementedError`.
- **`concat(cls: type[T_Index], indexes: Sequence[T_Index], dim: Hashable, positions: Iterable[Iterable[int]] = None) -> T_Index`**: Abstract; raises `NotImplementedError`. Concatenates a sequence of same-type indexes along a dimension, optionally reordering via `positions` (a list of position lists forming an inverse permutation).
- **`stack(cls, variables: Mapping[Any, Variable], dim: Hashable) -> Index`**: Abstract default; raises `NotImplementedError` with a message about stacked coordinates.
- **`unstack(self) -> tuple[dict[Hashable, Index], pd.MultiIndex]`**: Abstract; raises `NotImplementedError`.

**Instance Methods:**
- **`create_variables(self, variables: Mapping[Any, Variable] | None = None) -> IndexVars`**: If `variables` is not None, returns a shallow copy via `dict(**variables)`; otherwise returns `{}`.
- **`to_pandas_index(self) -> pd.Index`**: Raises `TypeError` by default (overridden in subclasses).
- **`isel(self, indexers: Mapping[Any, int | slice | np.ndarray | Variable]) -> Index | None`**: Returns `None` by default.
- **`sel(self, labels: dict[Any, Any]) -> IndexSelResult`**: Abstract; raises `NotImplementedError`.
- **`join(self: T_Index, other: T_Index, how: str = "inner") -> T_Index`**: Abstract default; raises `NotImplementedError`.
- **`reindex_like(self: T_Index, other: T_Index) -> dict[Hashable, Any]`**: Abstract default; raises `NotImplementedError`.
- **`equals(self, other)`**: Abstract; raises `NotImplementedError`.
- **`roll(self, shifts: Mapping[Any, int]) -> Index | None`**: Returns `None` by default.
- **`rename(self, name_dict: Mapping[Any, Hashable], dims_dict: Mapping[Any, Hashable]) -> Index`**: Returns `self` (identity) by default.
- **`__copy__(self) -> Index`**: Calls `self.copy(deep=False)`.
- **`__deepcopy__(self, memo=None) -> Index`**: Calls `self.copy(deep=True)`; `memo` is accepted for API compatibility but ignored.
- **`copy(self, deep: bool = True) -> Index`**: Creates a new instance via `cls.__new__(cls)`. If `deep`, deep-copies all attributes from `__dict__`; otherwise shallow-copies via `__dict__.update()`. Returns the copy.
- **`__getitem__(self, indexer: Any)`**: Abstract; raises `NotImplementedError`.

---

### `class PandasIndex(Index)`

**Docstring:** Wrap a pandas.Index as an xarray compatible index.

**Slots:** `("index", "dim", "coord_dtype")`

**Attributes (set in `__init__`):**
- **`index: pd.Index`** — the wrapped pandas Index.
- **`dim: Hashable`** — the dimension name.
- **`coord_dtype: Any`** — numpy dtype for coordinate data; defaults to `get_valid_numpy_dtype(index)`.

**`__init__(self, array: Any, dim: Hashable, coord_dtype: Any = None)`**

Converts `array` via `utils.safe_cast_to_index(array).copy()`. If the index name is None, sets it to `dim`. Stores `index`, `dim`, and `coord_dtype`.

**`_replace(self, index, dim=None, coord_dtype=None) -> PandasIndex`**

Creates a new instance of the same type with optional overrides for `dim` (defaults to `self.dim`) and `coord_dtype` (defaults to `self.coord_dtype`).

**`from_variables(cls, variables: Mapping[Any, Variable]) -> PandasIndex`**

Validates exactly one variable is provided and it has `ndim == 1`. Extracts the dimension from `var.dims[0]`. Gets underlying data via `getattr(var._data, "array", var.data)`. If `var._data` is a `PandasMultiIndexingAdapter`, retrieves level values via `var._data.array.get_level_values(level)` where `level = var._data.level`. Creates the index with `cls(data, dim, coord_dtype=var.dtype)`, asserts it's not a `pd.MultiIndex`, sets `obj.index.name = name`, and returns.

**`_concat_indexes(indexes, dim, positions=None) -> pd.Index` (static method)**

Concatenates pandas indexes along a dimension. If no indexes, returns `pd.Index([])`. Otherwise validates all have matching `dim`, appends the list of `idx.index` objects via `pd.Index.append()`. If `positions` is provided, computes an inverse permutation via `nputils.inverse_permutation(np.concatenate(positions))` and applies it with `.take(indices)`. Returns the new pandas Index.

**`concat(cls, indexes: Sequence[PandasIndex], dim: Hashable, positions: Iterable[Iterable[int]] = None) -> PandasIndex`**

Calls `_concat_indexes(indexes, dim, positions)` to get `new_pd_index`. If no indexes, sets `coord_dtype = None`; otherwise computes `np.result_type(*[idx.coord_dtype for idx in indexes])`. Returns `cls(new_pd_index, dim=dim, coord_dtype=coord_dtype)`.

**`create_variables(self, variables: Mapping[Any, Variable] | None = None) -> IndexVars`**

Imports `IndexVariable`. Gets the index name. If `variables` is provided and contains the name, extracts `attrs` and `encoding`; otherwise both are `None`. Creates a `PandasIndexingAdapter(self.index, dtype=self.coord_dtype)` as data, wraps it in an `IndexVariable(self.dim, ...)`, returns `{name: var}`.

**`to_pandas_index(self) -> pd.Index`**

Returns `self.index`.

**`isel(self, indexers: Mapping[Any, int | slice | np.ndarray | Variable]) -> PandasIndex | None`**

Extracts the indexer for `self.dim`. If it's a `Variable`, checks that its dims equal `(self.dim,)`; if not, returns `None` (new dimensions would be introduced). Otherwise uses `indxr.data`. If the result is scalar or not a slice, returns `None` (scalar selection drops index). Otherwise returns `self._replace(self.index[indxr])`.

**`sel(self, labels: dict[Any, Any], method=None, tolerance=None) -> IndexSelResult`**

Validates `method` is None or a string. Asserts exactly one label entry; extracts `coord_name, label`.

- If `label` is a `slice`: calls `_query_slice(...)`, returns `IndexSelResult({self.dim: indexer})`.
- If `label` is dict-like: raises `ValueError` (no MultiIndex support).
- Otherwise: normalizes the label via `normalize_label(label, dtype=self.coord_dtype)`.
  - **0-d array:** extracts scalar value. If index is `CategoricalIndex`, raises if `method`/`tolerance` provided; otherwise uses `self.index.get_loc(label_value)`. Else: if `method` is set, calls `get_indexer_nd(...)` and raises `KeyError` on any `-1`; else tries `self.index.get_loc(label_value)`, catching `KeyError` to provide a helpful message.
  - **Boolean dtype:** uses the label array directly as indexer.
  - **Other multi-element:** calls `get_indexer_nd(...)`, raises `KeyError` if any `-1`.

After indexing, if the original `label` was a `Variable`, wraps the indexer in `Variable(label.dims, indexer)`. If it was a `DataArray`, wraps in `DataArray(indexer, coords=label._coords, dims=label.dims)`. Returns `IndexSelResult({self.dim: indexer})`.

**`equals(self, other: Index)`**

Returns `False` if `other` is not a `PandasIndex`; otherwise returns `self.index.equals(other.index) and self.dim == other.dim`.

**`join(self: PandasIndex, other: PandasIndex, how: str = "inner") -> PandasIndex`**

If `how == "outer"`, calls `self.index.union(other.index)`; else uses `intersection()`. Computes `coord_dtype = np.result_type(self.coord_dtype, other.coord_dtype)`. Returns a new instance with the joined index.

**`reindex_like(self, other: PandasIndex, method=None, tolerance=None) -> dict[Hashable, Any]`**

Raises `ValueError` if `self.index.is_unique` is False. Returns `{self.dim: get_indexer_nd(self.index, other.index, method, tolerance)}`.

**`roll(self, shifts: Mapping[Any, int]) -> PandasIndex`**

Computes `shift = shifts[self.dim] % self.index.shape[0]`. If non-zero, creates a new index via `self.index[-shift:].append(self.index[:-shift])`; else copies the index. Returns `self._replace(new_pd_idx)`.

**`rename(self, name_dict, dims_dict)`**

If neither `self.index.name` nor `self.dim` appear in the respective dicts, returns `self`. Otherwise gets new names (falling back to originals), renames the pandas index, and calls `_replace(index, dim=new_dim)`.

**`copy(self, deep=True)`**

If `deep`, copies the underlying pandas index via `self.index.copy(deep=True)`; else uses it directly. Calls `_replace(index)`.

**`__getitem__(self, indexer: Any)`**

Returns `self._replace(self.index[indexer])`.

---

### `class PandasMultiIndex(PandasIndex)`

**Docstring:** Wrap a pandas.MultiIndex as an xarray compatible index.

**Slots:** `("index", "dim", "coord_dtype", "level_coords_dtype")`

**Attributes (set in `__init__`):**
- **`level_coords_dtype: dict[str, Any]`** — maps level names to their numpy dtypes.

**`__init__(self, array: Any, dim: Hashable, level_coords_dtype: Any = None)`**

Calls `super().__init__(array, dim)`. Sets default index level names: for each level, uses `idx.name or f"{dim}_level_{i}"`; raises `ValueError` if a name equals `dim`. Assigns the names to `self.index.names`. If `level_coords_dtype` is None, builds `{idx.name: get_valid_numpy_dtype(idx) for idx in self.index.levels}`. Stores it.

**`_replace(self, index, dim=None, level_coords_dtype=None) -> PandasMultiIndex`**

Sets `index.name = dim`. Defaults `dim` to `self.dim`, `level_coords_dtype` to `self.level_coords_dtype`. Returns `type(self)(index, dim, level_coords_dtype)`.

**`from_variables(cls, variables: Mapping[Any, Variable]) -> PandasMultiIndex`**

Calls `_check_dim_compat(variables)` (default `"equal"`). Gets dimension from the first variable's dims. Creates a `pd.MultiIndex.from_arrays([var.values for var in variables.values()], names=variables.keys())`, sets its name to `dim`. Builds `level_coords_dtype = {name: var.dtype for name, var in variables.items()}`. Returns `cls(index, dim, level_coords_dtype=...)`.

**`concat(cls, indexes: Sequence[PandasMultiIndex], dim: Hashable, positions=None) -> PandasMultiIndex`**

Calls `_concat_indexes(...)`. If no indexes, sets `level_coords_dtype = None`; otherwise for each level name in the first index's dtype dict, computes `np.result_type(*[idx.level_coords_dtype[name] for idx in indexes])`. Returns `cls(new_pd_index, dim=dim, level_coords_dtype=...)`.

**`stack(cls, variables: Mapping[Any, Variable], dim: Hashable) -> PandasMultiIndex`**

Calls `_check_dim_compat(variables, all_dims="different")`. Converts each variable to a pandas index via `utils.safe_cast_to_index(var)`; raises if any is already a `pd.MultiIndex`. Factorizes each level index (`lev.factorize()`), gets split labels and levels. Creates an n-dimensional meshgrid with `np.meshgrid(*split_labels, indexing="ij")`, raveling each to get `labels`. Builds `pd.MultiIndex(levels, labels, sortorder=0, names=variables.keys())`. Returns a new instance with `level_coords_dtype = {k: var.dtype for k, var in variables.items()}`.

**`unstack(self) -> tuple[dict[Hashable, Index], pd.MultiIndex]`**

Cleans the index via `remove_unused_levels_categories(self.index)`. For each `(name, lev)` pair from `clean_index.names/levels`, creates a `PandasIndex(lev.copy(), name, coord_dtype=self.level_coords_dtype[name])` and stores it in `new_indexes`. Returns `(new_indexes, clean_index)`.

**`from_variables_maybe_expand(cls, dim: Hashable, current_variables: Mapping[Any, Variable], variables: Mapping[Any, Variable]) -> tuple[PandasMultiIndex, IndexVars]`**

Creates or expands a multi-index. Initializes lists for `names`, `codes`, `levels`, and dict for `level_variables`. Calls `_check_dim_compat({**current_variables, **variables})`.

- If `len(current_variables) > 1`: extracts the existing `PandasMultiIndexingAdapter` from the first variable's data, gets its array (the MultiIndex), extends names/codes/levels from it, and copies level variables.
- If `len(current_variables) == 1`: creates a new level name `{dim}_level_0`, factorizes the single variable via `pd.Categorical(var.values, ordered=True)`, appends codes/categories.

For each new `(name, var)` in `variables`: creates a categorical, appends to names/codes/levels, stores the variable. Builds `pd.MultiIndex(levels, codes, names=names)`. Creates level_coords_dtype and returns `(cls(index, dim, ...), obj.create_variables(level_variables))`.

**`keep_levels(self, level_variables: Mapping[Any, Variable]) -> PandasMultiIndex | PandasIndex`**

Drops levels not in `level_variables` via `self.index.droplevel([...])`. If result is still a MultiIndex, returns `_replace(index, level_coords_dtype={k: self.level_coords_dtype[k] for k in index.names})`; else returns a new `PandasIndex(index, self.dim, coord_dtype=self.level_coords_dtype[index.name])`.

**`reorder_levels(self, level_variables: Mapping[Any, Variable]) -> PandasMultiIndex`**

Reorders via `self.index.reorder_levels(level_variables.keys())`. Builds new `level_coords_dtype` from the reordered names. Returns `_replace(index, level_coords_dtype=...)`.

**`create_variables(self, variables: Mapping[Any, Variable] | None = None) -> IndexVars`**

Imports `IndexVariable`. Defaults `variables` to `{}`. Iterates over `(self.dim,) + self.index.names`. For the dimension name (`name == self.dim`): sets `level=None, dtype=None`; for level names: sets `level=name, dtype=self.level_coords_dtype[name]`. Gets attrs/encoding from the variable if present (defaults to `{}`). Creates a `PandasMultiIndexingAdapter(self.index, dtype=dtype, level=level)`, wraps in an `IndexVariable` with `fastpath=True`. Returns the dict of index variables.

**`sel(self, labels, method=None, tolerance=None) -> IndexSelResult`**

Raises if `method` or `tolerance` is set. Initializes `new_index = None`, `scalar_coord_values = {}`.

- **Case 1: all label keys are in `self.index.names` (level-based selection):** Normalizes each label, converts to scalar via `as_scalar()` (raises ValueError if not scalar). Checks for slices. If the number of labels equals `index.nlevels` and no slice: calls `self.index.get_loc(tuple(...))`. Otherwise calls `self.index.get_loc_level(tuple(values), level=tuple(keys))`, storing scalar values. Raises `KeyError` if boolean indexer sums to 0.
- **Case 2: label keys are for the multi-index array (dimension-level selection):** If more than one label and not all in index names, raises `ValueError`. Gets `(coord_name, label)`.
  - If dict-like: validates level names; recursively calls `self.sel(label)`.
  - If slice: calls `_query_slice(...)`.
  - If tuple: if nested, uses `get_locs()`; if length equals nlevels, uses `get_loc()`; else uses `get_loc_level()`, storing scalar values.
  - Otherwise: normalizes label. If 0-d: uses `get_loc_level(label_value, level=0)`. If boolean dtype: uses directly. Else if ndim > 1: raises ValueError; otherwise calls `get_indexer_nd(...)`, raising on `-1`. Wraps indexer in Variable/DataArray as appropriate (filtering out conflicting level names for DataArray coords).

If `new_index is not None`:
- If it's a MultiIndex: builds new `level_coords_dtype`, creates `_replace(...)`, sets `dims_dict = {}` and `drop_coords = []`.
- Else: wraps in `PandasIndex(new_index, new_index.name, ...)`, sets `dims_dict = {self.dim: new_index.index.name}` and `drop_coords = [self.dim]`.

Creates variables from the new index. Adds scalar variables for each dropped level (`Variable([], val)`). Returns `IndexSelResult({self.dim: indexer}, indexes=indexes, variables=variables, drop_indexes=list(scalar_coord_values), drop_coords=drop_coords, rename_dims=dims_dict)`.

Else returns `IndexSelResult({self.dim: indexer})`.

**`join(self, other, how: str = "inner")`**

If `how == "outer"`: copies `other.index`, sets its name to None (pandas bug workaround), calls `.union()`; else uses `.intersection()`. Sets the result's name to `self.dim`. Computes new `level_coords_dtype` via `np.result_type(lvl_dtype, other.level_coords_dtype[k])` for each level. Returns a new instance.

**`rename(self, name_dict, dims_dict)`**

If no overlap between index names and name_dict keys and dim not in dims_dict, returns `self`. Builds new names list via `name_dict.get(k, k)`, renames the pandas index. Gets new dim. Rebuilds `level_coords_dtype` by zipping new_names with old values. Returns `_replace(index, dim=new_dim, level_coords_dtype=...)`.

---

### `class Indexes(collections.abc.Mapping, Generic[T_PandasOrXarrayIndex])`

**Docstring:** Immutable proxy for Dataset or DataArray indexes. Keys are coordinate names; values may be pandas or xarray indexes.

**Slots:** `("_indexes", "_variables", "_dims", "__coord_name_id", "__id_index", "__id_coord_names")`

**Attributes (set in `__init__`):**
- **`_indexes: dict[Any, T_PandasOrXarrayIndex]`** — mapping of coordinate names to indexes.
- **`_variables: dict[Any, Variable]`** — indexed coordinate variables.
- **`_dims: Mapping[Hashable, int] | None`** — lazy cache for dimension sizes.
- **`__coord_name_id: dict[Any, int] | None`** — lazy cache mapping coord name → `id(index)`.
- **`__id_index: dict[int, T_PandasOrXarrayIndex] | None`** — lazy cache mapping index id → unique index objects.
- **`__id_coord_names: dict[int, tuple[Hashable, ...]] | None`** — lazy cache mapping index id → tuple of coord names sharing that index.

**`__init__(self, indexes: dict[Any, T_PandasOrXarrayIndex], variables: dict[Any, Variable])`**

Stores `indexes` and `variables`; initializes all lazy caches to `None`.

**Properties (lazy):**
- **`_coord_name_id`**: Builds `{k: id(idx) for k, idx in self._indexes.items()}` on first access.
- **`_id_index`**: Builds `{id(idx): idx for idx in self.get_unique()}` on first access.
- **`_id_coord_names`**: Groups coord names by index id using `_coord_name_id`, returns `{k: tuple(v) for k, v in ...}`.

**Properties (computed):**
- **`variables`**: Returns `Frozen(self._variables)`.
- **`dims`**: If `_dims` is None, calls `calculate_dimensions(self._variables)` and caches; returns `Frozen(self._dims)`.

**Methods:**
- **`copy()`**: Returns a new `Indexes` instance with shallow copies of both dicts.
- **`get_unique() -> list[T_PandasOrXarrayIndex]`**: Iterates over `_indexes.values()`, collects unique indexes by `id(index)` preserving order, returns the list.
- **`is_multi(key: Hashable) -> bool`**: Returns `True` if more than one coordinate name maps to the same index as `key`.
- **`get_all_coords(self, key: Hashable, errors: ErrorOptions = "raise") -> dict[Hashable, Variable]`**: Validates `errors` is `"raise"` or `"ignore"`. If `key` not in `_indexes`, raises (or returns `{}` if ignore). Otherwise returns `{k: self._variables[k] for k in all_coord_names}` where `all_coord_names = self._id_coord_names[self._coord_name_id[key]]`.
- **`get_all_dims(self, key: Hashable, errors: ErrorOptions = "raise") -> Mapping[Hashable, int]`**: Calls `calculate_dimensions(self.get_all_coords(key, errors=errors))`.
- **`group_by_index() -> list[tuple[T_PandasOrXarrayIndex, dict[Hashable, Variable]]]`**: For each index id in `_id_index`, gets the index and its coord variables (from `_id_coord_names[id]`), appends `(index, coords)` to a list. Returns it.
- **`to_pandas_indexes(self) -> Indexes[pd.Index]`**: Builds a new dict where each value is either the raw `pd.Index` or obtained via `idx.to_pandas_index()`. Returns `Indexes(indexes, self._variables)`.
- **`copy_indexes(self, deep: bool = True) -> tuple[dict[Hashable, T_PandasOrXarrayIndex], dict[Hashable, Variable]]`**: For each `(idx, coords)` from `group_by_index()`: if `idx` is a raw `pd.Index`, converts to the appropriate xarray Index class (`PandasMultiIndex` or `PandasIndex`). Copies it via `idx.copy(deep=deep)`. Creates variables via `idx.create_variables(coords)`. If originally converted from a pandas index, extracts `.index` back. Updates result dicts with `{k: new_idx for k in coords}` and the created vars. Returns `(new_indexes, new_index_vars)`.

**Mapping protocol:**
- **`__iter__(self)`**: `iter(self._indexes)`.
- **`__len__(self)`**: `len(self._indexes)`.
- **`__contains__(self, key)`**: `key in self._indexes`.
- **`__getitem__(self, key)`**: `self._indexes[key]`.
- **`__repr__(self)`**: Calls `formatting.indexes_repr(self)`.