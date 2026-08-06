# Implementation target
Write the module at `django/db/models/query.py`.

## `django/db/models/query.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseIterable`
- `EmptyQuerySet`
- `FlatValuesListIterable`
- `InstanceCheckMeta`
- `MAX_GET_RESULTS`
- `ModelIterable`
- `NamedValuesListIterable`
- `Prefetch`
- `QuerySet`
- `REPR_OUTPUT_SIZE`
- `RawQuerySet`
- `RelatedPopulator`
- `ValuesIterable`
- `ValuesListIterable`
- `get_prefetcher`
- `get_related_populators`
- `normalize_prefetch_lookups`
- `prefetch_one_level`
- `prefetch_related_objects`

Implement them to satisfy the specification. Do not write tests.
