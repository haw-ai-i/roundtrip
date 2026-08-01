# Implementation target
Write the module at `xarray/core/indexing.py`.
Other modules import these names from it, so they MUST exist with these exact names:
- `ArrayApiIndexingAdapter`
- `BasicIndexer`
- `CopyOnWriteArray`
- `DaskIndexingAdapter`
- `ExplicitIndexer`
- `ExplicitlyIndexed`
- `ExplicitlyIndexedNDArrayMixin`
- `ImplicitToExplicitIndexingAdapter`
- `IndexSelResult`
- `IndexingSupport`
- `LazilyIndexedArray`
- `LazilyOuterIndexedArray`
- `LazilyVectorizedIndexedArray`
- `MemoryCachedArray`
- `NdArrayLikeIndexingAdapter`
- `NumpyIndexingAdapter`
- `OuterIndexer`
- `PandasIndexingAdapter`
- `PandasMultiIndexingAdapter`
- `VectorizedIndexer`
- `as_indexable`
- `as_integer_or_none`
- `as_integer_slice`
- `create_mask`
- `decompose_indexer`
- `expanded_indexer`
- `explicit_indexing_adapter`
- `group_indexers_by_index`
- `is_fancy_indexer`
- `map_index_queries`
- `merge_sel_results`
- `posify_mask_indexer`
- `slice_slice`
Implement them to satisfy the specification. Do not write tests.
