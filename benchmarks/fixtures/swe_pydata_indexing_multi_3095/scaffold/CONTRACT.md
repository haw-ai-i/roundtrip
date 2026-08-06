# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `xarray/core/indexing.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BasicIndexer`
- `CopyOnWriteArray`
- `DaskIndexingAdapter`
- `ExplicitIndexer`
- `ExplicitlyIndexed`
- `ExplicitlyIndexedNDArrayMixin`
- `ImplicitToExplicitIndexingAdapter`
- `IndexingSupport`
- `LazilyOuterIndexedArray`
- `LazilyVectorizedIndexedArray`
- `MemoryCachedArray`
- `NumpyIndexingAdapter`
- `OuterIndexer`
- `PandasIndexAdapter`
- `VectorizedIndexer`
- `as_indexable`
- `as_integer_or_none`
- `as_integer_slice`
- `convert_label_indexer`
- `create_mask`
- `decompose_indexer`
- `expanded_indexer`
- `explicit_indexing_adapter`
- `get_dim_indexers`
- `get_indexer_nd`
- `get_loc`
- `posify_mask_indexer`
- `remap_label_indexers`
- `slice_slice`

## `xarray/core/variable.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BASIC_INDEXING_TYPES`
- `Coordinate`
- `IndexVariable`
- `MissingDimensionsError`
- `NON_NUMPY_SUPPORTED_ARRAY_TYPES`
- `Variable`
- `as_compatible_data`
- `as_variable`
- `assert_unique_multiindex_level_names`
- `broadcast_variables`
- `concat`

Implement them to satisfy the specification. Do not write tests.
