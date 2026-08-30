## django/db/models/query.py
Now I have the full file content (2764 lines). Let me compile the complete natural-language specification.

---

# Module Specification: `django/db/models/query.py`

## 1. Module-Level Preamble

### Imports

```python
import copy
import operator
import warnings
from itertools import chain, islice

from asgiref.sync import sync_to_async

import django
from django.conf import settings
from django.core import exceptions
from django.db import (
    DJANGO_VERSION_PICKLE_KEY,
    IntegrityError,
    NotSupportedError,
    connections,
    router,
    transaction,
)
from django.db.models import AutoField, DateField, DateTimeField, Field, sql
from django.db.models.constants import LOOKUP_SEP, OnConflict
from django.db.models.deletion import Collector
from django.db.models.expressions import Case, F, Value, When
from django.db.models.functions import Cast, Trunc
from django.db.models.query_utils import FilteredRelation, Q
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE, ROW_COUNT
from django.db.models.utils import (
    AltersData,
    create_namedtuple_class,
    resolve_callables,
)
from django.utils import timezone
from django.utils.deprecation import RemovedInDjango60Warning
from django.utils.functional import cached_property, partition
```

### Constants & Globals

| Name | Value | Description |
|------|-------|-------------|
| `MAX_GET_RESULTS` | `21` | Maximum number of results to fetch in a `get()` query. |
| `REPR_OUTPUT_SIZE` | `20` | Maximum items displayed in `QuerySet.__repr__`. |
| `PROHIBITED_FILTER_KWARGS` | `frozenset(["_connector", "_negated"])` | Forbidden keyword argument names for filter/exclude methods. |

---

## 2. Code Objects

### Class: `BaseIterable`

**Purpose:** Generic base iterable that wraps a QuerySet and provides chunked iteration with async support.

**Attributes (instance, set in `__init__`):**
- `self.queryset` — the QuerySet being iterated.
- `self.chunked_fetch` — boolean; whether to use server-side cursor chunking.
- `self.chunk_size` — integer; number of rows per chunk (defaults to `GET_ITERATOR_CHUNK_SIZE`).

**Methods:**

#### `__init__(self, queryset, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE)`
Stores the three attributes above.

#### `_async_generator(self)` *(async)*
Creates an async generator that yields items from a sync iterator in chunks:
1. Creates `sync_generator = self.__iter__()`.
2. Defines inner function `next_slice(gen)` returning `list(islice(gen, self.chunk_size))`.
3. Loops indefinitely: awaits `sync_to_async(next_slice)(sync_generator)`, yielding each item from the chunk; breaks when a chunk has fewer than `chunk_size` items.

#### `__aiter__(self)`
Returns `self._async_generator()`. A synchronous method returning an async iterator/generator.

---

### Class: `ModelIterable(BaseIterable)`

**Purpose:** Yields model instances for each row from a standard QuerySet query.

**Methods:**

#### `__iter__(self)`
1. Gets `queryset`, `db = queryset.db`.
2. Creates compiler via `queryset.query.get_compiler(using=db)`.
3. Executes SQL: `results = compiler.execute_sql(chunked_fetch=self.chunked_fetch, chunk_size=self.chunk_size)`.
4. Extracts from compiler: `select`, `klass_info`, `annotation_col_map`.
5. Gets `model_cls = klass_info["model"]`, `select_fields = klass_info["select_fields"]`.
6. Computes `model_fields_start` and `model_fields_end` from `select_fields[0]` and `select_fields[-1]+1`.
7. Builds `init_list`: list of field attnames for columns in the model's field range.
8. Calls `get_related_populators(klass_info, select, db)` to get related populator objects.
9. Builds `known_related_objects` from `queryset._known_related_objects`, creating tuples of `(field, related_objs_dict, operator.attrgetter(...))`.
10. For each row in `compiler.results_iter(results)`:
    a. Creates model instance: `model_cls.from_db(db, init_list, row[model_fields_start:model_fields_end])`.
    b. For each rel_populator: calls `rel_populator.populate(row, obj)`.
    c. If `annotation_col_map` exists: sets annotated attributes on the object via `setattr(obj, attr_name, row[col_pos])`.
    d. For each known related object: if field is not already cached on obj, gets rel_obj_id via `rel_getter(obj)`, looks up in `rel_objs[rel_obj_id]`, and sets it as attribute (skipping KeyError).
    e. Yields the constructed model instance.

---

### Class: `RawModelIterable(BaseIterable)`

**Purpose:** Yields model instances for each row from a raw SQL query.

**Methods:**

#### `__iter__(self)`
1. Gets `db`, `query = self.queryset.query`, `connection = connections[db]`.
2. Creates compiler: `connection.ops.compiler("SQLCompiler")(query, connection, db)`.
3. Sets `query_iterator = iter(query)`.
4. In a try/finally block:
   a. Calls `self.queryset.resolve_model_init_order()` to get `(model_init_names, model_init_pos, annotation_fields)`.
   b. Gets `model_cls = self.queryset.model`.
   c. If primary key attname not in `model_init_names`, raises `FieldDoesNotExist("Raw query must include the primary key")`.
   d. Builds `fields` list: `[self.queryset.model_fields.get(c) for c in self.queryset.columns]`.
   e. Builds `cols`: `[f.get_col(f.model._meta.db_table) if f else None for f in fields]`.
   f. Gets converters via `compiler.get_converters(cols)`; applies them to query_iterator if present.
   g. If composite fields exist: transforms rows via `compiler.composite_fields_to_tuples(query_iterator, cols)`.
   h. For each `values` row: builds `model_init_values = [values[pos] for pos in model_init_pos]`, creates instance via `model_cls.from_db(db, model_init_names, model_init_values)`, sets annotation fields if present, yields the instance.
5. In finally block: closes query cursor if it has one and is open.

---

### Class: `ValuesIterable(BaseIterable)`

**Purpose:** Yields a dict for each row (used by `QuerySet.values()`).

**Methods:**

#### `__iter__(self)`
1. Gets `queryset`, `query = queryset.query`.
2. Creates compiler via `query.get_compiler(queryset.db)`.
3. Determines column names: if `query.selected` exists, uses it; otherwise concatenates `[*query.extra_select, *query.values_select, *query.annotation_select]`.
4. For each row from `compiler.results_iter(chunked_fetch=self.chunked_fetch, chunk_size=self.chunk_size)`: yields `{names[i]: row[i] for i in range(len(names))}`.

---

### Class: `ValuesListIterable(BaseIterable)`

**Purpose:** Yields a tuple for each row (used by `QuerySet.values_list(flat=False)`).

**Methods:**

#### `__iter__(self)`
Delegates to `compiler.results_iter(tuple_expected=True, chunked_fetch=self.chunked_fetch, chunk_size=self.chunk_size)`.

---

### Class: `NamedValuesListIterable(ValuesListIterable)`

**Purpose:** Yields a namedtuple for each row (used by `QuerySet.values_list(named=True)`).

**Methods:**

#### `__iter__(self)`
1. Gets field names from `queryset._fields` if set; otherwise from `[*query.extra_select, *query.values_select, *query.annotation_select]`.
2. Creates namedtuple class via `create_namedtuple_class(*names)`.
3. For each row from parent `__iter__()`: yields `tuple.__new__(tuple_class, row)`.

---

### Class: `FlatValuesListIterable(BaseIterable)`

**Purpose:** Yields single scalar values (used by `QuerySet.values_list(flat=True)`).

**Methods:**

#### `__iter__(self)`
For each row from `compiler.results_iter(chunked_fetch=self.chunked_fetch, chunk_size=self.chunk_size)`: yields `row[0]`.

---

### Class: `QuerySet(AltersData)`

**Purpose:** The main ORM query builder and executor. Represents a lazy database lookup for a set of objects. Inherits from `AltersData` (which marks methods that modify the database).

#### Attributes (instance, set in `__init__`):
- `self.model` — the model class this QuerySet operates on.
- `self._db` — database alias; None if using default.
- `self._hints` — dict of hints for routers (default `{}`).
- `self._query` — an `sql.Query` instance (or subclass); created as `sql.Query(self.model)` if not provided.
- `self._result_cache` — cached list of results; None until `_fetch_all()` is called.
- `self._sticky_filter` — boolean; whether the next filter should be treated as sticky.
- `self._for_write` — boolean; True for write operations (affects database routing).
- `self._prefetch_related_lookups` — tuple of prefetch lookup strings.
- `self._prefetch_done` — boolean; whether prefetch has been performed on cached results.
- `self._known_related_objects` — dict mapping `{rel_field: {pk: rel_obj}}`.
- `self._iterable_class` — the iterable class to use (default `ModelIterable`).
- `self._fields` — tuple of field names for values queries; None otherwise.
- `self._defer_next_filter` — boolean; whether next filter should be deferred.
- `self._deferred_filter` — tuple `(negate, args, kwargs)` or None.

#### Class-level attribute:
- `as_manager.queryset_only = True` (set before wrapping with `classmethod`).

---

#### Property: `query` (getter)
If `self._deferred_filter` is set, unpacks it and calls `self._filter_or_exclude_inplace(negate, args, kwargs)`, then clears `_deferred_filter`. Returns `self._query`.

#### Property: `query` (setter)
If `value.values_select` is truthy, sets `self._iterable_class = ValuesIterable`. Sets `self._query = value`.

---

#### `as_manager(cls)` *(classmethod)*
Creates a `Manager.from_queryset(cls)()` instance, sets `_built_with_as_manager = True`, returns it. Used to create manager objects from QuerySet subclasses.

---

### Python Magic Methods

#### `__deepcopy__(self, memo)`
Creates a new empty QuerySet via `self.__class__()`. Deep-copies all attributes except `_result_cache` (set to None). Returns the copy.

#### `__getstate__(self)`
Calls `self._fetch_all()` to populate cache. Returns `{**self.__dict__, DJANGO_VERSION_PICKLE_KEY: django.__version__}`.

#### `__setstate__(self, state)`
If `DJANGO_VERSION_PICKLE_KEY` is in state and differs from current `django.__version__`, emits a `RuntimeWarning`. If key is missing, emits a different `RuntimeWarning`. Updates `self.__dict__.update(state)`.

#### `__repr__(self)`
Fetches up to `REPR_OUTPUT_SIZE + 1` items. If more than `REPR_OUTPUT_SIZE`, replaces last item with `"...(remaining elements truncated)..."`. Returns `"<%s %r>" % (self.__class__.__name__, data)`.

#### `__len__(self)`
Calls `_fetch_all()`. Returns `len(self._result_cache)`.

#### `__iter__(self)`
Calls `_fetch_all()`. Returns `iter(self._result_cache)`.

#### `__aiter__(self)`
Defines inner async generator that awaits `sync_to_async(self._fetch_all)()` then yields each item from cache. Returns the generator function (not coroutine).

#### `__bool__(self)`
Calls `_fetch_all()`. Returns `bool(self._result_cache)`.

#### `__getitem__(self, k)`
Validates `k` is int or slice; raises `TypeError` otherwise. Rejects negative indices (int or slice components); raises `ValueError`. If cache exists, returns `self._result_cache[k]`. For slices: creates chain clone, sets limits via `qs.query.set_limits(start, stop)`, returns `list(qs)[::k.step]` if step is set, else `qs`. For int: creates chain clone, sets limit to 1 (`set_limits(k, k+1)`), fetches all, returns `_result_cache[0]`.

#### `__class_getitem__(cls, *args, **kwargs)`
Returns `cls` (for PEP 585 type hint support).

#### `__and__(self, other)`
Checks both are QuerySets via `_check_operator_queryset`; sanity-checks merge compatibility. If either is `EmptyQuerySet`, returns the other. Creates chain clone, merges known related objects, combines queries with `sql.AND`. Returns combined.

#### `__or__(self, other)`
Similar to `__and__` but uses `sql.OR`. Handles non-filterable querysets by wrapping in `pk__in` subqueries.

#### `__xor__(self, other)`
Similar to `__or__` but uses `sql.XOR`.

---

### Database Query Methods

#### `_iterator(self, use_chunked_fetch, chunk_size)` *(generator)*
1. Creates iterable instance of `self._iterable_class(self, chunked_fetch=use_chunked_fetch, chunk_size=chunk_size or 2000)`.
2. If no prefetch lookups or `chunk_size is None`: yields from iterable directly.
3. Otherwise: iterates in chunks of `chunk_size`, calling `prefetch_related_objects(results, *self._prefetch_related_lookups)` between each chunk yield.

#### `iterator(self, chunk_size=None)` *(generator)*
Validates chunk_size (required if prefetch lookups exist; must be positive). Determines `use_chunked_fetch` from connection settings (`DISABLE_SERVER_SIDE_CURSORS`). Returns `_iterator(use_chunked_fetch, chunk_size)`.

#### `aiterator(self, chunk_size=2000)` *(async generator)*
Validates chunk_size > 0. Gets `use_chunked_fetch`. Creates iterable. If prefetch lookups exist: collects items in batches of `chunk_size`, calls `aprefetch_related_objects` between batches, yields each batch. Otherwise: yields directly from async iterable.

#### `aggregate(self, *args, **kwargs)`
Raises `NotImplementedError` if `query.distinct_fields` is set. Validates values are expressions via `_validate_values_are_expressions`. For positional args: extracts `default_alias`, raises `TypeError` for complex aggregates without alias; adds to kwargs with that alias. Returns `self.query.chain().get_aggregation(self.db, kwargs)`.

#### `aaggregate(self, *args, **kwargs)` *(async)*
Returns `await sync_to_async(self.aggregate)(*args, **kwargs)`.

#### `count(self)`
If cache exists, returns `len(self._result_cache)`. Otherwise returns `self.query.get_count(using=self.db)`.

#### `acount(self)` *(async)*
Returns `await sync_to_async(self.count)()`.

#### `get(self, *args, **kwargs)`
Raises `NotSupportedError` if query has a combinator and filter args/kwargs are provided. Clones with `_chain()` if combinator; otherwise calls `filter(*args, **kwargs)`. If can filter and no distinct fields: clears ordering via `order_by()`. Sets limit to `MAX_GET_RESULTS` unless `select_for_update` is set without the database supporting it with limit. Gets `num = len(clone)`. Returns single result if num==1; raises `DoesNotExist` if num==0; raises `MultipleObjectsReturned` otherwise (with count info).

#### `aget(self, *args, **kwargs)` *(async)*
Returns `await sync_to_async(self.get)(*args, **kwargs)`.

#### `create(self, **kwargs)`
Checks for reverse one-to-one fields in kwargs; raises `ValueError` if found. Creates model instance with kwargs. Sets `_for_write = True`. Saves with `force_insert=True, using=self.db`. Returns the object.

**Attribute:** `create.alters_data = True`

#### `acreate(self, **kwargs)` *(async)*
Returns `await sync_to_async(self.create)(**kwargs)`.

**Attribute:** `acreate.alters_data = True`

---

### Bulk Operations

#### `_prepare_for_bulk_create(self, objs)`
For each obj: if PK not set, populates it via `obj._meta.pk.get_pk_value_on_save(obj)`. If DB doesn't support DEFAULT keyword in bulk insert and field is not generated: checks for `DatabaseDefault` values and replaces with `field.db_default`. Calls `obj._prepare_related_fields_for_save(operation_name="bulk_create")`.

#### `_check_bulk_create_options(self, ignore_conflicts, update_conflicts, update_fields, unique_fields)`
Validates mutual exclusivity of `ignore_conflicts`/`update_conflicts`. Checks DB feature support for each option. For `update_conflicts`: validates `update_fields` and `unique_fields` are provided; checks fields are concrete (not M2M); rejects PKs in update_fields. Returns `OnConflict.IGNORE`, `OnConflict.UPDATE`, or `None`.

#### `bulk_create(self, objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, update_fields=None, unique_fields=None)`
Validates batch_size > 0. Checks multi-table inheritance is not used (all parents share same concrete model). If empty objs: returns them. Converts `unique_fields`/`update_fields` from names to field objects. Calls `_check_bulk_create_options`. Sets `_for_write = True`. Gets concrete non-generated fields. Prepares objs via `_prepare_for_bulk_create`. In a transaction:
1. Partitions objs into those with PK set and without.
2. For objs_with_pk: calls `_batched_insert`, sets returned columns on objects, marks state as not adding.
3. For objs_without_pk: removes AutoField from fields list, calls `_batched_insert`, handles returning rows if supported, marks state.
Returns `objs`.

**Attribute:** `bulk_create.alters_data = True`

#### `abulk_create(self, ...)` *(async)*
Delegates to sync version via `sync_to_async`.

**Attribute:** `abulk_create.alters_data = True`

#### `bulk_update(self, objs, fields, batch_size=None)`
Validates batch_size > 0 and fields non-empty. All objs must have PK set. Converts field names to Field objects; rejects non-concrete or M2M fields. Rejects PK fields in update list. For each obj: calls `_prepare_related_fields_for_save`. Computes `max_batch_size` from connection ops. Builds batches. For each batch: builds CASE/WHEN statements for each field, wraps with Cast if required by DB feature. Executes updates via `queryset.filter(pk__in=pks).update(**update_kwargs)` within a transaction. Returns total rows updated.

**Attribute:** `bulk_update.alters_data = True`

#### `abulk_update(self, ...)` *(async)*
Delegates to sync version.

**Attribute:** `abulk_update.alters_data = True`

---

### Get-or-Create / Update-or-Create

#### `get_or_create(self, defaults=None, **kwargs)`
Sets `_for_write = True`. Tries `self.get(**kwargs)`, returns `(obj, False)` on success. On `DoesNotExist`: builds params via `_extract_model_params(defaults, **kwargs)`. In a transaction: resolves callables in params, calls `create(**params)`, returns `(obj, True)`. On `IntegrityError`: retries `get(**kwargs)`, re-raises if still missing.

**Attribute:** `get_or_create.alters_data = True`

#### `aget_or_create(self, ...)` *(async)*
Delegates to sync version.

**Attribute:** `aget_or_create.alters_data = True`

#### `update_or_create(self, defaults=None, create_defaults=None, **kwargs)`
Sets `update_defaults = defaults or {}`. If `create_defaults is None`, uses `update_defaults`. In a transaction: calls `self.select_for_update().get_or_create(create_defaults, **kwargs)`. If created: returns `(obj, True)`. Otherwise: sets each resolved callable from update_defaults on obj. Builds `update_fields` set; if it's a subset of concrete non-PK fields, adds auto_now fields and saves with `update_fields`; otherwise saves without field restriction. Returns `(obj, False)`.

**Attribute:** `update_or_create.alters_data = True`

#### `aupdate_or_create(self, ...)` *(async)*
Delegates to sync version.

**Attribute:** `aupdate_or_create.alters_data = True`

---

### Helper Methods for Create Operations

#### `_extract_model_params(self, defaults, **kwargs)`
Filters kwargs to exclude lookup-separator keys (e.g., `__gt`). Merges with defaults. Validates each param against model fields; allows properties with setters. Raises `FieldError` for invalid params. Returns merged params dict.

---

### First/Latest/Earliest Methods

#### `_earliest(self, *fields)`
If fields given: uses them as ordering. Otherwise uses `model._meta.get_latest_by`. If neither available: raises `ValueError`. Creates chain clone, sets limit to 1, clears ordering, adds the field(s) to ordering, calls `.get()`.

#### `earliest(self, *fields)`
Raises `TypeError` if query is sliced. Returns `_earliest(*fields)`.

#### `aearliest(self, *fields)` *(async)*
Delegates to sync version.

#### `latest(self, *fields)`
Raises `TypeError` if query is sliced. Calls `self.reverse()._earliest(*fields)`.

#### `alatest(self, *fields)` *(async)*
Delegates to sync version.

#### `first(self)`
If already ordered: uses self; else checks ordering/aggregation compatibility and orders by `"pk"`. Returns first item from `queryset[:1]` or None.

#### `afirst(self)` *(async)*
Delegates to sync version.

#### `last(self)`
If ordered: reverses; else checks compatibility and orders by `"-pk"`. Returns first item from reversed queryset[:1] or None.

#### `alast(self)` *(async)*
Delegates to sync version.

---

### Bulk/Collection Methods

#### `in_bulk(self, id_list=None, *, field_name="pk")`
Raises `TypeError` if sliced or not using ModelIterable. Validates `field_name` uniqueness (checks total unique constraints). If `id_list is None`: iterates all objects. If empty list: returns `{}`. Handles DB parameter limits by batching the filter query with unions. Returns dict mapping `{getattr(obj, field_name): obj for obj in qs}`.

#### `ain_bulk(self, ...)` *(async)*
Delegates to sync version.

---

### Delete / Update Methods

#### `delete(self)`
Raises errors if combined queries, sliced, distinct fields set, or values/values_list used. Creates chain clone with `_for_write = True`. Disables `select_for_update` and `select_related`, clears ordering. Uses `Collector(using=del_query.db, origin=self)` to collect and delete related objects. Returns `(num_deleted, num_deleted_per_model)`. Clears result cache.

**Attribute:** `delete.alters_data = True; delete.queryset_only = True`

#### `adelete(self)` *(async)*
Delegates to sync version.

**Attribute:** `adelete.alters_data = True; adelete.queryset_only = True`

#### `_raw_delete(self, using)`
Clones query, replaces class with `sql.DeleteQuery`, executes via compiler returning row count.

**Attribute:** `_raw_delete.alters_data = True`

#### `update(self, **kwargs)`
Raises errors for combined queries or sliced queries. Sets `_for_write = True`. Creates chain as UpdateQuery, adds update values. Inlines annotations in ordering (validating no aggregates). Clears SELECT clause. Executes within `mark_for_rollback_on_error` context. Returns rows updated.

**Attribute:** `update.alters_data = True`

#### `aupdate(self, **kwargs)` *(async)*
Delegates to sync version.

**Attribute:** `aupdate.alters_data = True`

#### `_update(self, values)`
Version accepting field objects instead of names (used by model save). Raises if sliced. Creates UpdateQuery chain, adds update fields, clears annotations, returns row count.

**Attribute:** `_update.alters_data = True; _update.queryset_only = False`

---

### Existence / Containment Methods

#### `exists(self)`
If cache is None: calls `self.query.has_results(using=self.db)`. Otherwise returns `bool(self._result_cache)`.

#### `aexists(self)` *(async)*
Delegates to sync version.

#### `contains(self, obj)`
Raises errors for combined queries or values/values_list. Validates obj is model instance of same concrete model with PK set. If cache exists: checks membership directly. Otherwise calls `self.filter(pk=obj.pk).exists()`.

#### `acontains(self, obj)` *(async)*
Delegates to sync version.

---

### Explain Method

#### `explain(self, *, format=None, **options)`
Returns `self.query.explain(using=self.db, format=format, **options)`.

#### `aexplain(self, ...)` *(async)*
Delegates to sync version.

---

### Methods Returning a QuerySet Subclass (RawQuerySet)

#### `raw(self, raw_query, params=(), translations=None, using=None)`
Creates and returns a `RawQuerySet(raw_query, model=self.model, params=params, translations=translations, using=using or self.db)`, copying `_prefetch_related_lookups`.

---

### Values / Values List / Dates Methods

#### `_values(self, *fields, **expressions)`
Creates chain clone. If expressions: annotates with them. Sets `clone._fields = fields`. Calls `clone.query.set_values(fields)`. Returns clone.

#### `values(self, *fields, **expressions)`
Concatenates expression names to fields. Calls `_values(*fields, **expressions)`, sets `_iterable_class = ValuesIterable`, returns clone.

#### `values_list(self, *fields, flat=False, named=False)`
Raises errors if both flat and named, or flat with >1 field. Processes each field: expressions get aliases (prefixed with counter for backward compat); duplicate names get suffixed counters. Creates chain via `_values`. Sets iterable class to `NamedValuesListIterable` if named, `FlatValuesListIterable` if flat, else `ValuesListIterable`. Returns clone.

#### `dates(self, field_name, kind, order="ASC")`
Validates kind in `("year", "month", "week", "day")`, order in `("ASC", "DESC")`. Annotates with `Trunc(field_name, kind, output_field=DateField())` and `F(field_name)`. Values list on datefield flat=True. Distinct. Filters non-null plain_field. Orders by datefield (reversed if DESC).

#### `datetimes(self, field_name, kind, order="ASC", tzinfo=None)`
Validates kind in `("year", "month", "week", "day", "hour", "minute", "second")`, order in `("ASC", "DESC")`. If USE_TZ: defaults tzinfo to current timezone; else None. Similar to `dates` but uses `DateTimeField` and `Trunc(..., tzinfo=tzinfo)`.

#### `none(self)`
Creates chain clone, calls `clone.query.set_empty()`, returns it.

---

### Filter / Exclude Methods

#### `all(self)`
Returns `self._chain()` (a copy).

#### `filter(self, *args, **kwargs)`
Raises for combined queries. Returns `_filter_or_exclude(False, args, kwargs)`.

#### `exclude(self, *args, **kwargs)`
Raises for combined queries. Returns `_filter_or_exclude(True, args, kwargs)`.

#### `_filter_or_exclude(self, negate, args, kwargs)`
Raises if sliced and has filter args/kwargs. Creates chain clone. If `_defer_next_filter` is set: clears it, stores `(negate, args, kwargs)` in `clone._deferred_filter`, returns clone (lazy evaluation). Otherwise calls `_filter_or_exclude_inplace(negate, args, kwargs)`.

#### `_filter_or_exclude_inplace(self, negate, args, kwargs)`
Validates no prohibited kwargs. If negate: adds `~Q(*args, **kwargs)` to query; else adds `Q(*args, **kwargs)`.

#### `complex_filter(self, filter_obj)`
If `filter_obj` is Q object: creates chain clone, adds Q to query. Else: calls `_filter_or_exclude(False, args=(), kwargs=filter_obj)`.

---

### Combinator Methods (Union / Intersection / Difference)

#### `_combinator_query(self, combinator, *other_qs, all=False)`
Creates chain clone. Clears ordering and limits. Sets `combined_queries` to `(self.query,) + tuple(qs.query for qs in other_qs)`. Sets `combinator`, `combinator_all = all`. Returns clone.

#### `union(self, *other_qs, all=False)`
If self is EmptyQuerySet: combines non-empty querysets (returns first if only one). If no other_qs: returns self. Otherwise calls `_combinator_query("union", ...)`.

#### `intersection(self, *other_qs)`
Returns self if empty; returns any empty queryset encountered in others. Otherwise calls `_combinator_query("intersection", ...)`.

#### `difference(self, *other_qs)`
Returns self if empty. Otherwise calls `_combinator_query("difference", ...)`.

---

### Selection / Prefetch Methods

#### `select_for_update(self, nowait=False, skip_locked=False, of=(), no_key=False)`
Raises if both nowait and skip_locked. Creates chain clone, sets `_for_write = True`, sets all four query flags (`select_for_update`, `select_for_update_nowait`, `select_for_update_skip_locked`, `select_for_no_key_update`). Returns clone.

#### `select_related(self, *fields)`
Raises for combined queries or after values/values_list. Creates chain clone. If `(None,)`: disables select_related. If fields: calls `query.add_select_fields(fields)`. Else: enables unbounded select_related. Returns clone.

#### `prefetch_related(self, *lookups)`
Raises for combined queries. Creates chain clone. If `(None,)`: clears lookups. Otherwise validates no FilteredRelation conflicts; extracts top-level lookup names for validation. Appends lookups to existing tuple. Returns clone.

---

### Annotation Methods

#### `annotate(self, *args, **kwargs)`
Raises for combined queries. Validates expressions. Calls `_annotate(args, kwargs, select=True)`.

#### `alias(self, *args, **kwargs)`
Raises for combined queries. Calls `_annotate(args, kwargs, select=False)`.

#### `_annotate(self, args, kwargs, select=True)`
Validates all values are expressions. For positional args: extracts default_alias (validating no conflicts with kwargs). Merges into annotations dict. Creates chain clone. Determines field names set (from `self._fields` or all model fields). Validates annotation aliases don't conflict with model fields. For FilteredRelation annotations: calls `query.add_filtered_relation(annotation, alias)`. Otherwise: calls `query.add_annotation(annotation, alias, select=select)`. If any new annotation is aggregate and not using field selection: sets `query.group_by = True` (or `set_group_by()` if `_fields` is set). Returns clone.

---

### Ordering / Distinct / Extra Methods

#### `order_by(self, *field_names)`
Raises if sliced. Creates chain clone, clears ordering (preserving defaults), adds new ordering fields. Returns clone.

#### `distinct(self, *field_names)`
Raises for combined queries or if sliced. Creates chain clone, calls `query.add_distinct_fields(*field_names)`. Returns clone.

#### `extra(self, select=None, where=None, params=None, tables=None, order_by=None, select_params=None)`
Raises for combined queries or if sliced. Creates chain clone, calls `query.add_extra(select, select_params, where, params, tables, order_by)`. Returns clone.

#### `reverse(self)`
Raises if sliced. Creates chain clone, toggles `standard_ordering` flag. Returns clone.

---

### Field Loading Methods (Defer / Only)

#### `defer(self, *fields)`
Raises for combined queries or after values/values_list. Creates chain clone. If `(None,)`: clears deferred loading. Else: calls `query.add_deferred_loading(fields)`. Returns clone.

#### `only(self, *fields)`
Raises for combined queries or after values/values_list. Rejects `(None,)` argument. Validates no FilteredRelation conflicts (top-level lookup names). Creates chain clone, calls `query.add_immediate_loading(fields)`. Returns clone.

---

### Database Selection

#### `using(self, alias)`
Creates chain clone, sets `clone._db = alias`, returns it.

---

### Introspection Properties

#### `ordered` *(property)*
Returns True if: EmptyQuerySet; has extra_order_by or order_by; or has default ordering and get_meta().ordering is set and no group_by. Otherwise False.

#### `db` *(property)*
If `_for_write`: returns `_db or router.db_for_write(self.model, **self._hints)`. Else: returns `_db or router.db_for_read(self.model, **self._hints)`.

---

### Private Insert Methods

#### `_insert(self, objs, fields, returning_fields=None, raw=False, using=None, on_conflict=None, update_fields=None, unique_fields=None)`
Sets `_for_write = True`. Uses `using or self.db` as database. Creates `sql.InsertQuery(self.model, ...)`, inserts values via `query.insert_values(fields, objs, raw=raw)`, executes and returns results from compiler.

**Attribute:** `_insert.alters_data = True; _insert.queryset_only = False`

#### `_batched_insert(self, objs, fields, batch_size, on_conflict=None, update_fields=None, unique_fields=None)`
Computes max_batch_size. Splits objs into batches. For each batch: if DB supports returning rows and no conflict handling or UPDATE mode: calls `_insert` with `returning_fields=self.model._meta.db_returning_fields`; else calls without. Returns list of inserted row results.

---

### Chain / Clone Methods

#### `_chain(self)`
Creates clone via `_clone()`. If `_sticky_filter`: sets `obj.query.filter_is_sticky = True`, clears flag. Returns obj.

#### `_clone(self)`
Creates new QuerySet with `model=self.model, query=self.query.chain(), using=self._db, hints=self._hints`. Copies: `_sticky_filter`, `_for_write`, `_prefetch_related_lookups[:]`, `_known_related_objects` (shared reference), `_iterable_class`, `_fields`. Returns clone.

#### `_fetch_all(self)`
If cache is None: populates with `list(self._iterable_class(self))`. If prefetch lookups exist and not done: calls `_prefetch_related_objects()`.

---

### Internal Helper Methods

#### `_next_is_sticky(self)`
Sets `_sticky_filter = True`, returns self. Used internally before a filter call.

#### `_merge_sanity_check(self, other)`
If both have field selections (`_fields is not None`), validates that values_select, extra_select, and annotation_select sets match. Raises `TypeError` if mismatched.

#### `_merge_known_related_objects(self, other)`
Merges `other._known_related_objects` into self's dict (deep merge per field).

#### `resolve_expression(self, *args, **kwargs)`
Calls `self.query.resolve_expression(*args, **kwargs)`, sets `query._db = self._db`. Returns query.

**Attribute:** `resolve_expression.queryset_only = True`

#### `_add_hints(self, **hints)`
Updates `self._hints` with provided hints.

#### `_has_filters(self)`
Returns `self.query.has_filters()`.

#### `_validate_values_are_expressions(self, values, method_name)` *(staticmethod)*
Collects string representations of non-expression args. If any: raises `TypeError("QuerySet.%s() received non-expression(s): %s." % (method_name, ...))`.

#### `_not_support_combined_queries(self, operation_name)`
Raises `NotSupportedError` if query has a combinator.

#### `_check_operator_queryset(self, other, operator_)`
Raises `TypeError` if either queryset has a combinator.

#### `_check_ordering_first_last_queryset_aggregation(self, method)`
If group_by is tuple and PK fields not in group_by: raises `TypeError`.

---

### Class: `InstanceCheckMeta(type)`

**Metaclass for EmptyQuerySet.**

#### `__instancecheck__(self, instance)`
Returns `isinstance(instance, QuerySet) and instance.query.is_empty()`. Enables `isinstance(qs.none(), EmptyQuerySet)` to return True.

---

### Class: `EmptyQuerySet(metaclass=InstanceCheckMeta)`

**Purpose:** Marker class for empty querysets returned by `.none()`. Cannot be instantiated.

#### `__init__(self, *args, **kwargs)`
Always raises `TypeError("EmptyQuerySet can't be instantiated")`.

---

### Class: `RawQuerySet`

**Purpose:** Provides an iterator that converts raw SQL query results into annotated model instances.

#### Attributes (instance, set in `__init__`):
- `self.raw_query` — the raw SQL string.
- `self.model` — target model class.
- `self._db` — database alias.
- `self._hints` — router hints dict.
- `self.query` — an `sql.RawQuery` instance wrapping the raw SQL.
- `self.params` — query parameters tuple.
- `self.translations` — column name translations dict.
- `self._result_cache` — cached results list; None until fetched.
- `self._prefetch_related_lookups` — tuple of prefetch lookups.
- `self._prefetch_done` — boolean.

---

#### `resolve_model_init_order(self)`
Gets identifier converter from connection. Builds `model_init_fields` (fields whose column names appear in columns). Builds `annotation_fields` (columns not matching model fields, with positions). Returns `(model_init_names, model_init_order, annotation_fields)`.

#### `prefetch_related(self, *lookups)`
Creates clone via `_clone()`. If `(None,)`: clears lookups. Else: appends to existing tuple. Returns clone.

#### `_prefetch_related_objects(self)`
Calls `prefetch_related_objects(self._result_cache, *self._prefetch_related_lookups)`, sets `_prefetch_done = True`.

#### `_clone(self)`
Creates new RawQuerySet with same raw_query, model, query (shared), params, translations, using=_db, hints. Copies prefetch lookups list. Returns clone.

#### `_fetch_all(self)`
If cache is None: populates via `list(self.iterator())`. If prefetch lookups exist and not done: calls `_prefetch_related_objects()`.

#### Python Magic Methods (similar to QuerySet):
- `__len__(self)`: fetches all, returns len of cache.
- `__bool__(self)`: fetches all, returns bool of cache.
- `__iter__(self)`: fetches all, returns iter of cache.
- `__aiter__(self)`: async generator that awaits fetch_all then yields from cache.
- `__repr__(self)`: `"<%s: %s>" % (self.__class__.__name__, self.query)`.
- `__getitem__(self, k)`: returns `list(self)[k]`.

#### `iterator(self)` *(generator)*
Yields from `RawModelIterable(self)`.

#### Property: `db`
Returns `_db or router.db_for_read(self.model, **self._hints)`.

#### `using(self, alias)`
Returns new RawQuerySet with cloned query using the given alias.

#### Property: `columns` *(cached_property)*
Gets columns from `query.get_columns()`. Applies translations dict to rename column names. Returns list.

#### Property: `model_fields` *(cached_property)*
Builds `{converter(field.column): field for field in model._meta.fields}` using connection's identifier converter.

---

### Class: `Prefetch`

**Purpose:** Represents a prefetch lookup with optional custom queryset and to_attr destination.

#### Attributes (instance, set in `__init__`):
- `self.prefetch_through` — traversal path for the prefetch (defaults to lookup string).
- `self.prefetch_to` — destination attribute path (defaults to lookup; modified if to_attr given).
- `self.queryset` — optional custom QuerySet.
- `self.to_attr` — optional attribute name override.

#### `__init__(self, lookup, queryset=None, to_attr=None)`
Sets `prefetch_through = prefetch_to = lookup`. Validates queryset is not RawQuerySet or non-ModelIterable. If `to_attr`: modifies `prefetch_to` by replacing last path segment with to_attr. Sets `queryset` and `to_attr`.

#### `__getstate__(self)`
Clones queryset (clearing result cache, setting prefetch_done=True) if present. Returns copy of `__dict__`.

#### `add_prefix(self, prefix)`
Prepends prefix + LOOKUP_SEP to both `prefetch_through` and `prefetch_to`.

#### `get_current_prefetch_to(self, level)`
Returns first `level+1` segments of `prefetch_to` split by LOOKUP_SEP.

#### `get_current_to_attr(self, level)`
Returns `(parts[level], as_attr)` where `as_attr` is True only if at the last segment and to_attr was set.

#### `get_current_queryset(self, level)` *(deprecated)*
Warns about deprecation. Returns first queryset from `get_current_querysets(level)`.

#### `get_current_querysets(self, level)`
If current prefetch_to equals full prefetch_to and queryset is set: returns `[self.queryset]`. Else returns None.

#### `__eq__(self, other)`
Returns NotImplemented if not Prefetch; else compares `prefetch_to`.

#### `__hash__(self)`
Hashes `(self.__class__, self.prefetch_to)`.

---

### Function: `normalize_prefetch_lookups(lookups, prefix=None)`
Converts non-Prefetch lookups to Prefetch objects. If prefix given: calls `add_prefix(prefix)` on each. Returns list of Prefetch objects.

---

### Function: `prefetch_related_objects(model_instances, *related_lookups)`

Populates prefetched object caches for a list of model instances based on lookup/Prefetch strings.

**Algorithm:**
1. If no instances: return immediately.
2. Initializes `done_queries = {}` (tracks completed prefetch paths), `auto_lookups = set()`, `followed_descriptors = set()` (recursion protection).
3. Normalizes lookups in reverse order via `normalize_prefetch_lookups`.
4. While lookups remain: pops one lookup. If already done and has no custom queryset: continues.
5. Sets `obj_list = model_instances` as starting point.
6. Splits `prefetch_through` into path segments (`through_attrs`). Iterates each level:
   a. Gets `prefetch_to` for current level. If already in `done_queries`: sets obj_list to cached results and continues.
   b. Initializes `_prefetched_objects_cache = {}` on all objects (skips immutable/non-model instances).
   c. Calls `get_prefetcher(first_obj, through_attr, to_attr)` to find prefetcher/descriptor/fetch-status.
   d. Raises `AttributeError` if attribute not found; raises `ValueError` if last level has no prefetcher.
   e. If prefetcher exists: collects unfetched objects, calls `prefetch_one_level(instances, prefetcher, lookup, level)`. Records results in `done_queries`, normalizes additional lookups from the returned queryset's `_prefetch_related_lookups`, adds to work queue. Adds descriptor to `followed_descriptors` (unless already seen on an auto-lookup).
   f. If no prefetcher: traverses into related objects via getattr, handling None values and list extensions (for reverse relations), skipping ObjectDoesNotExist exceptions. Updates obj_list for next level.

---

### Function: `aprefetch_related_objects(model_instances, *related_lookups)` *(async)*
Returns `await sync_to_async(prefetch_related_objects)(model_instances, *related_lookups)`.

---

### Function: `get_prefetcher(instance, through_attr, to_attr)`

Finds a prefetcher object for the given attribute on an instance. Returns 4-tuple: `(prefetcher, rel_obj_descriptor, attr_found, is_fetched)`.

**Algorithm:**
1. Defines `is_to_attr_fetched(model, to_attr)`: handles cached_property special case (checks `__dict__`), otherwise uses `hasattr(instance, to_attr)`.
2. Gets class-level descriptor via `getattr(instance.__class__, through_attr, None)`.
3. If no descriptor: sets `attr_found = hasattr(instance, through_attr)`.
4. If descriptor exists: checks for `get_prefetch_querysets()` (or deprecated `get_prefetch_queryset()`). If found: sets prefetcher to descriptor; if `through_attr == to_attr`: uses descriptor's `is_cached` as is_fetched.
5. If descriptor doesn't support prefetching: gets attribute on instance, checks if result has prefetch method; if so, sets prefetcher and defines `in_prefetched_cache` check.

---

### Function: `prefetch_one_level(instances, prefetcher, lookup, level)`

Runs a single-level prefetch for the given instances using the prefetcher. Returns `(all_related_objects, additional_lookups)`.

**Algorithm:**
1. Calls `prefetcher.get_prefetch_querysets(instances, lookup.get_current_querysets(level))` (or deprecated method with warning). Gets: `rel_qs`, `rel_obj_attr`, `instance_attr`, `single`, `cache_name`, `is_descriptor`.
2. Copies `_prefetch_related_lookups` from returned queryset as additional lookups; clears them on the queryset.
3. Evaluates all related objects: `all_related_objects = list(rel_qs)`.
4. Groups by rel_obj_attr into `rel_obj_cache` dict.
5. Validates `to_attr` doesn't conflict with model fields (if as_attr and instances exist).
6. Determines if this is the leaf level of the prefetch path.
7. For each instance: gets related values from cache via instance_attr. If single: sets value on object (via setattr for to_attr, or field cache). If not single: populates manager's result cache with prefetched values, stores in `_prefetched_objects_cache`.

---

### Class: `RelatedPopulator`

**Purpose:** Used by `select_related()` to instantiate related model objects from SQL query rows. Each select_related model gets its own RelatedPopulator instance.

#### Attributes (instance, set in `__init__`):
- `self.db` — database alias.
- `self.cols_start`, `self.cols_end` — column index range for this model's fields in the row.
- `self.init_list` — list of field attnames for model initialization.
- `self.reorder_for_init` — callable (operator.itemgetter) to reorder columns if parent data needs reordering; None otherwise.
- `self.model_cls` — the model class to instantiate.
- `self.pk_idx` — index of primary key in init_list.
- `self.related_populators` — list of child RelatedPopulator instances for nested select_related.
- `self.local_setter`, `self.remote_setter` — field setter methods for linking objects.

#### `__init__(self, klass_info, select, db)`
Extracts `select_fields = klass_info["select_fields"]`, `from_parent = klass_info["from_parent"]`. If not from parent: sets cols_start/cols_end directly and init_list from select columns. If from parent: builds attname index map, reorders model_init_attnames to match DB column order, creates reorder_for_init itemgetter. Sets model_cls, pk_idx (index of PK in init_list), related_populators via `get_related_populators(klass_info, select, db)`, local_setter and remote_setter from klass_info.

#### `populate(self, row, from_obj)`
1. Gets obj_data: either reordered via `reorder_for_init(row)` or sliced as `row[cols_start:cols_end]`.
2. If `obj_data[pk_idx] is None`: sets `obj = None`; else creates instance via `model_cls.from_db(self.db, self.init_list, obj_data)`, recursively populates related objects.
3. Calls `self.local_setter(from_obj, obj)` to link the object.
4. If obj is not None: calls `self.remote_setter(obj, from_obj)` for reverse linking.

---

### Function: `get_related_populators(klass_info, select, db)`
Iterates over `klass_info.get("related_klass_infos", [])`, creates a `RelatedPopulator` for each, returns list.

## django/db/models/sql/compiler.py
Now I have the complete file content. Let me write the comprehensive natural-language specification:

---

# Module Specification: `django/db/models/sql/compiler.py`

## 1. Imports

```python
import collections
import json
import re
from functools import partial
from itertools import chain

from django.core.exceptions import EmptyResultSet, FieldError, FullResultSet
from django.db import DatabaseError, NotSupportedError
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import F, OrderBy, RawSQL, Ref, Value
from django.db.models.functions import Cast, Random
from django.db.models.lookups import Lookup
from django.db.models.query_utils import select_related_descend
from django.db.models.sql.constants import (
    CURSOR, GET_ITERATOR_CHUNK_SIZE, MULTI, NO_RESULTS, ORDER_DIR, SINGLE,
)
from django.db.models.sql.query import Query, get_order_dir
from django.db.models.sql.where import AND
from django.db.transaction import TransactionManagementError
from django.utils.functional import cached_property
from django.utils.hashable import make_hashable
from django.utils.regex_helper import _lazy_re_compile
```

## 2. Constants & Globals

- **`SQLCompiler.ordering_parts`**: A compiled regex (`_lazy_re_compile`) matching `r"^(.*)\s(?:ASC|DESC).*"` with flags `re.MULTILINE | re.DOTALL`. Used to strip ordering direction suffixes from SQL fragments for deduplication in `get_order_by()`.

## 3. Code Objects

### Class: `SQLCompiler`

**Inheritance:** None (base class)
**Metaclass:** Default

#### Attributes

| Attribute | Type / Description | Initialization |
|---|---|---|
| `ordering_parts` | Compiled regex pattern | Class-level constant |
| `query` | `Query` object | `__init__` parameter |
| `connection` | Database connection | `__init__` parameter |
| `using` | Database alias string | `__init__` parameter |
| `elide_empty` | `bool` (default `True`) | `__init__` parameter; controls whether queries that would return empty sets are skipped |
| `quote_cache` | `dict[str, str]`, initially `{"*": "*"}` | `__init__`; caches quoted table/column names |
| `select` | `list[tuple[expr, (sql, params), alias]]` or `None` | Set as side-effect of `setup_query()` / `as_sql()` |
| `annotation_col_map` | `dict` or `None` | Set as side-effect of `setup_query()` |
| `klass_info` | `dict` or `None` | Set as side-effect of `setup_query()` |
| `_meta_ordering` | `list` or `None` | Set in `_order_by_pairs()` when meta ordering is used |
| `col_count` | `int` | Set in `setup_query()` as `len(self.select)` |

#### Methods

##### `__init__(self, query, connection, using, elide_empty=True)`
Initializes the compiler with a `Query`, database `connection`, database alias string `using`, and an optional `elide_empty` flag. Sets up instance attributes (see table above). Initializes `quote_cache = {"*": "*"}`.

##### `__repr__(self) → str`
Returns a formatted string: `<ClassName model=Model.__qualname__ connection=<conn> using=<using>>`.

##### `setup_query(self, with_col_aliases=False)`
Prepares the query for SQL generation. If all aliases in `query.alias_map` have refcount 0, calls `query.get_initial_alias()`. Calls `get_select(with_col_aliases=with_col_aliases)`, unpacking into `self.select`, `self.klass_info`, and `self.annotation_col_map`. Sets `self.col_count = len(self.select)`.

##### `pre_sql_setup(self, with_col_aliases=False)`
Performs the full pre-SQL setup. Calls `setup_query(with_col_aliases)`. Calls `get_order_by()` to get `order_by`. Splits `query.where` via `where.split_having_qualify(must_group_by=query.group_by is not None)` into `self.where`, `self.having`, and `self.qualify`. Calls `get_extra_select(order_by, self.select)`, storing result in `extra_select` and setting `self.has_extra_select = bool(extra_select)`. Calls `get_group_by(self.select + extra_select, order_by)` to get `group_by`. Returns `(extra_select, order_by, group_by)`.

##### `get_group_by(self, select, order_by) → list[tuple[str, tuple]]`
Returns a deduplicated list of 2-tuples `(sql, params)` for the GROUP BY clause. Logic:
- If `query.group_by is None`, returns `[]`.
- Initializes an empty `expressions` list.
- If `query.group_by is not True` (i.e., it's a list), iterates over each expression in `query.group_by`: converts string references to expressions via `query.resolve_ref()`, replaces `Ref` with its source if the database doesn't support group-by refs, appends to `expressions`.
- Collects `ref_sources = {expr.source for expr in expressions if isinstance(expr, Ref)}` and builds `aliased_exprs = {expr: alias}` from select entries that have aliases.
- Iterates over `(expr, _, alias)` in `select`: skips if `expr` is a ref_source; otherwise collects aliased expressions and appends each column from `expr.get_group_by_cols()` to `expressions`.
- If not `_meta_ordering`, iterates over `(expr, (sql, params, is_ref))` in `order_by`: skips refs; extends `expressions` with `expr.get_group_by_cols()`.
- Appends group-by columns from `self.having.get_group_by_cols()` if `self.having` exists.
- Calls `collapse_group_by(expressions, having_group_by)` to optionally reduce the set.
- Deduplicates: iterates over reduced expressions; if database supports refs and alias exists, wraps in `Ref(alias, expr)`. Compiles each expression via `self.compile(expr)`, catching `EmptyResultSet`/`FullResultSet` (skips). Calls `expr.select_format(self, sql, params)`. Hashes params with `make_hashable(params)` and deduplicates by `(sql, params_hash)`.
- Returns list of unique `(sql, params)` tuples.

##### `collapse_group_by(self, expressions, having) → list`
If database feature `allows_group_by_selected_pks` is True: identifies primary key expressions in `expressions` (those with `.target.primary_key == True` and the model passes `allows_group_by_selected_pks_on_model`). Collects their aliases. Filters `expressions` to keep only: PK expressions, expressions in `having`, or expressions whose alias is not among the PK table aliases. Returns filtered list. Otherwise returns `expressions` unchanged.

##### `get_select(self, with_col_aliases=False) → tuple[list[tuple[expr, (sql, params), alias]], dict|None, dict]`
Returns three values: a select list of 3-tuples `(expression, (sql, params), alias)`, a `klass_info` dict or `None`, and an annotations dict. Logic:
- Initializes `select = []`, `klass_info = None`, `annotations = {}`, `select_idx = 0`.
- For each `(alias, (sql, params))` in `query.extra_select`: records `annotations[alias] = select_idx`, appends `(RawSQL(sql, params), alias)` to `select`, increments `select_idx`.
- Asserts not both `query.select` and `query.default_cols`. Gets `select_mask = query.get_select_mask()`.
- If `query.default_cols`: calls `get_default_columns(select_mask)`. Else: uses `cols = query.select`.
- If `cols` is non-empty: iterates over cols, appends each to `select`, records indices in `select_list`, creates `klass_info = {"model": query.model, "select_fields": select_list}`.
- For each `(alias, annotation)` in `query.annotation_select`: records `annotations[alias] = select_idx`, appends `(annotation, alias)` to `select`, increments `select_idx`.
- If `query.select_related` is truthy: calls `get_related_selections(select, select_mask)`, stores result as `klass_info["related_klass_infos"]`. Then runs a nested function `get_select_from_parent(klass_info)` that propagates parent `select_fields` to children where `from_parent` is True.
- Builds final return list: for each `(col, alias)` in `select`: compiles via `self.compile(col)`, catching `EmptyResultSet` (uses `"0"` or `Value(empty_result_set_value)`), catching `FullResultSet` (uses `Value(True)`). Otherwise calls `col.select_format(self, sql, params)`. If `alias is None and with_col_aliases`, generates alias as `f"col{col_idx}"`. Appends `(col, (sql, params), alias)` to result.
- Returns `(ret, klass_info, annotations)`.

##### `_order_by_pairs(self) → generator[tuple[OrderBy|expr, bool]]`
Yields pairs of `(expression, is_ref)` for ORDER BY processing. Logic:
- Determines `ordering`: priority is `query.extra_orderby`, then `query.order_by` (if not default ordering), then `query.order_by` if set, else meta ordering (`meta.ordering`), else `[]`. If meta ordering used, sets `self._meta_ordering = ordering`.
- Sets `default_order` from `ORDER_DIR["ASC"]` or `ORDER_DIR["DESC"]` based on `query.standard_ordering`.
- For each field in `ordering`:
  - If field has `resolve_expression`: if it's a `Value`, wraps in `Cast(field, field.output_field)`. If not already an `OrderBy`, calls `.asc()`. If not standard ordering, copies and reverses. If expression is an `F` referencing an annotation name found in `query.annotation_select`, replaces with `Ref(name, annotation)`. Yields `(field, isinstance(field.expression, Ref))`.
  - If field == `"?"`: yields `(OrderBy(Random()), False)`.
  - Otherwise: parses direction via `get_order_dir(field, default_order)`. If column is in `query.annotation_select`, yields an `OrderBy(Ref(col, annotation), descending)` with `is_ref=True`. If column is in `query.annotations` (masked expression): if combinator and select exist, uses `F(col)`; else resolves the annotation (casting `Value` expressions). Yields `(OrderBy(expr, descending), False)`.
  - If field contains `"."`: splits into table/col, yields `(OrderBy(RawSQL("%s.%s" % (quoted_table, col), []), descending), False)`.
  - If column is in `query.extra`: if in `extra_select`, yields `(OrderBy(Ref(col, RawSQL(*extra[col])), descending), True)`; else yields `(OrderBy(RawSQL(*extra[col]), descending), False)`.
  - Otherwise: if combinator and select exist, uses `F(col)`; else calls `find_ordering_name(field, meta, default_order)` which yields multiple pairs.

##### `get_order_by(self) → list[tuple[expr, tuple[str, tuple, bool]]]`
Returns a deduplicated list of 2-tuples `(resolved_expr, (sql, params, is_ref))`. Iterates over `_order_by_pairs()`: resolves each expression via `expr.resolve_expression(query, allow_joins=True, reuse=None)`. If not a ref and combinator with select exists: checks if the source matches any selected column; if so, sets source to a `Ref` using the column alias. Otherwise, adds the column as a new annotation (`__orderbycolN`) to all combined queries (raising `DatabaseError` if they have explicit select fields), then wraps in `Ref`. Compiles via `self.compile(resolved)`. Strips ordering direction from SQL for deduplication using `ordering_parts.search(sql)[1]`. Deduplicates by `(without_ordering, make_hashable(params))`. Returns list.

##### `get_extra_select(self, order_by, select) → list[tuple[expr, tuple[str, tuple], None]]`
If `query.distinct` and not `query.distinct_fields`: iterates over `order_by`, strips ordering direction from SQL; if not a ref and `(without_ordering, params)` is not already in the select SQL set, appends `(expr, (without_ordering, params), None)`. Returns list.

##### `quote_name_unless_alias(self, name) → str`
Wraps `connection.ops.quote_name`, but skips quoting for table aliases. Checks `quote_cache` first. If name is in `query.alias_map` and not in `query.table_map`, or in `extra_select`, or in `external_aliases` and not in `table_map`: stores unquoted name in cache, returns it. Otherwise quotes via `connection.ops.quote_name(name)`, caches, returns.

##### `compile(self, node) → tuple[str, tuple]`
Attempts vendor-specific implementation: checks for `node.as_<vendor>(self, connection)` method; if found, calls it. Otherwise calls `node.as_sql(self, connection)`. Returns `(sql, params)`.

##### `get_combinator_sql(self, combinator, all) → tuple[list[str], list]`
Generates SQL for compound queries (UNION/INTERSECT/EXCEPT). Creates compilers for each combined query. Validates: if database doesn't support the combinator type, raises `NotSupportedError`. If sliced and not supported, raises `DatabaseError` about LIMIT/OFFED in subqueries. If sliced with UNION and supported, sets `elide_empty = False` on all compilers and copies limits to unsliced ones. Iterates over compilers: if `values_select` is set but compiler doesn't have it, clones the compiler's query and sets values via `set_values()`. Calls `compiler.as_sql(with_col_aliases=True)`. If compiler has its own combinator: wraps in subquery if no parentheses support; adds parentheses if subquery or no slicing/ordering support. Otherwise wraps in parentheses if subquery and slicing supported. Catches `EmptyResultSet`: omits with UNION (or DIFFERENCE after first non-empty); re-raises otherwise. If no parts remain, raises `EmptyResultSet`. Builds combinator SQL using `connection.ops.set_operators[combinator]`, appending `" ALL"` for UNION+all. Wraps in parentheses if not subquery and slicing/ordering supported. Returns `(result, params)`.

##### `get_qualify_sql(self) → tuple[list[str], list]`
Generates SQL for FILTER/WINDOW QUALIFY clauses. Builds inner query by cloning self.query, setting `subquery = True`, wrapping `where + having` in a new AND node. Collects select expressions and aliases from `get_select(with_col_aliases=True)`. Defines nested `collect_replacements(expressions)` that walks expression leaves: if already replaced, skips; if found in select dict, records alias; if Lookup, recurses into source expressions; if Ref not in select aliases, recurses; otherwise creates a new qual alias (`qualN`), adds as annotation to inner query, records replacement. Collects replacements from `self.qualify.leaves()`. Replaces expressions in `self.qualify` with `Ref(alias, expr)`. Similarly processes order_by expressions. Creates inner compiler, calls `as_sql(with_limits=False, with_col_aliases=True)`. Compiles the qualify expression. Builds result: `"SELECT * FROM (inner_sql) qualify WHERE qualify_sql"`. If qual aliases were added, wraps again to mask them back: `"SELECT quoted_aliases FROM (...) qualify_mask"`. Appends ORDER BY if present. Returns `(result, params)`.

##### `as_sql(self, with_limits=True, with_col_aliases=False) → tuple[str, tuple]`
Main method that generates the complete SQL query string and parameters. Saves `query.alias_refcopy` for cleanup. Calls `pre_sql_setup(with_col_aliases or bool(combinator))` to get `(extra_select, order_by, group_by)`. Determines if LIMIT/OFFSET needed: `with_limits and query.is_sliced`. Gets database features.

- **If combinator exists**: validates support, calls `get_combinator_sql()`, sets result/params.
- **Else if qualify exists**: calls `get_qualify_sql()`, sets `order_by = None`.
- **Otherwise** (standard SELECT): gets `distinct_fields` from `get_distinct()`. Gets `from_` clause via `get_from_clause()`. Compiles `self.where` (catching `EmptyResultSet`: if elide_empty, re-raise; else uses `"0 = 1"`; catching `FullResultSet`: uses empty string). Compiles `self.having` similarly. Builds result list starting with `"SELECT"`.
  - If `query.distinct`: calls `connection.ops.distinct_sql(distinct_fields, distinct_params)`, appends to result and params.
  - Builds output columns: for each `(sql, params)` in `select + extra_select`, if alias exists, formats as `"%s AS quoted_alias"`. Appends joined select list.
  - Appends FROM clause if present; else uses `bare_select_suffix` feature.
  - If `query.select_for_update`: validates transaction context (raises `TransactionManagementError` if autocommit and transactions supported). Validates LIMIT compatibility, NOWAIT/SKIP LOCKED/OF/NO KEY support. Calls `connection.ops.for_update_sql()` with arguments from `get_select_for_update_of_arguments()`.
  - Appends WHERE clause if present.
  - Builds GROUP BY: validates that distinct_fields + group_by is not used together (raises `NotImplementedError`). If no ordering, uses `force_no_ordering()`. Appends `"GROUP BY ..."` and clears `_meta_ordering` flag.
  - Appends HAVING clause if present.
  - If `explain_info`: inserts EXPLAIN prefix at position 0.
  - Appends ORDER BY clause (using compound subquery wrapper if required by feature).
  - Appends LIMIT/OFFSET via `connection.ops.limit_offset_sql(low_mark, high_mark)`.
  - Positions FOR UPDATE part based on `for_update_after_from` feature.
  - If used as subquery with extra_select: wraps in outer SELECT to exclude extraneous columns (selects only the original select columns by alias or recompiled expression).
- Finally, resets refcounts via `query.reset_refcounts(refcounts_before)`. Returns `" ".join(result), tuple(params)`.

##### `get_default_columns(self, select_mask, start_alias=None, opts=None, from_parent=None) → list`
Computes default columns for selecting every field in the base model. If `opts is None`, gets it from `query.get_meta()` (returns empty if None). Uses `start_alias = query.get_initial_alias()`. Tracks `seen_models = {None: start_alias}`. For each concrete field in opts: determines the model; skips if already loaded via parent (`from_parent` check); skips if not in `select_mask`; joins parent model and appends `field.get_col(alias)` to result. Returns list of column expressions.

##### `get_distinct(self) → tuple[list[str], list[tuple]]`
Returns quoted fields for DISTINCT ON. Iterates over `query.distinct_fields`: splits on LOOKUP_SEP, runs `_setup_joins()`, trims joins via `query.trim_joins()`. For each target: if column is in `annotation_select`, uses the name as-is (quoted); else compiles `transform_function(target, alias)`. Returns `(result, params)`.

##### `find_ordering_name(self, name, opts, alias=None, default_order="ASC", already_seen=None) → list[tuple[OrderBy, bool]]`
Resolves a field path like `"field1__field2"` to ordering expressions. Parses direction via `get_order_dir()`. Runs `_setup_joins()` on the pieces. If the resolved field is a relation and opts has ordering (and not pk shortcut/attribute name/no transforms): checks for infinite loops via join tuple tracking; recursively resolves each meta ordering item, prefixing references with `"name__"`. Returns results list. Otherwise trims joins and returns `[OrderBy(transform_function(t, alias), descending=False) for t in targets]`.

##### `_setup_joins(self, pieces, opts, alias)`
Helper that calls `query.setup_joins(pieces, opts, alias)`, extracts the last join as the new alias, and returns `(field, targets, alias, joins, path, opts, transform_function)`.

##### `get_from_clause(self) → tuple[list[str], list]`
Returns FROM clause parts. Iterates over `query.alias_map`: skips zero-refcount aliases; compiles each from-clause entry via `self.compile()`, appending SQL and params. For each table in `query.extra_tables`: creates alias, appends as `, quoted_alias` if not already in map or refcount is 1. Returns `(result, params)`.

##### `get_related_selections(self, select, select_mask, opts=None, root_alias=None, cur_depth=1, requested=None, restricted=None) → list[dict]`
Recursively builds `related_klass_infos` for `select_related()`. If depth exceeds `max_depth`, returns empty. Gets opts/alias from query if not provided. Determines if selection is restricted (dict-based). For each field in opts.fields: checks restrictions; validates non-relation fields aren't used as relations; calls `select_related_descend()` to decide inclusion. Creates `klass_info` dict with model, field, setters, etc. Calls `get_default_columns()` for related model, appending columns to select and recording indices. Recursively calls itself for nested relations. For restricted mode: handles reverse relations (unique FKs), filtered relations (`_filtered_relations`). Validates all requested fields are found; raises `FieldError` if not. Returns list of klass_info dicts.

##### `get_select_for_update_of_arguments(self) → list[str]`
Returns quoted column/table references for SELECT FOR UPDATE OF. If no `klass_info`, returns `[]`. Iterates over `query.select_for_update_of`: for `"self"`, gets first selected col from root model; otherwise traverses the klass_info tree following field path parts, collecting parent klass_infos at each level. Gets first selected column from final klass_info. Uses full compiled SQL if feature supports column references; else uses quoted alias. Collects invalid names and raises `FieldError` with allowed choices if any. Returns list of quoted references.

##### `get_converters(self, expressions) → dict[int, tuple[list, expr]]`
For each expression at position i: collects backend converters (`connection.ops.get_db_converters(expression)`) and field converters (`expression.get_db_converters(connection)`). If either is non-empty, stores `(backend + field converters, expression)` in dict keyed by column index.

##### `apply_converters(self, rows, converters) → generator[list]`
For each row (converted to list): for each position with converters, applies each converter function sequentially to the value at that position. Yields modified rows.

##### `results_iter(self, results=None, tuple_expected=False, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE) → generator`
Returns an iterator over query results. If no results provided, calls `execute_sql(MULTI, ...)`. Extracts select fields from first `col_count` entries. Gets converters for those fields. Chains all result rows. Applies converters if present; converts to tuples if `tuple_expected`. Yields rows.

##### `has_results(self) → bool`
Returns `bool(self.execute_sql(SINGLE))`. Can be overridden by backends for optimization.

##### `execute_sql(self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE)`
Executes the query and returns results. Tries to generate SQL via `as_sql()`, raising `EmptyResultSet` if empty: returns empty iterator (MULTI) or None (other). Uses chunked cursor if requested and supported. Executes SQL with params. Returns based on result_type: CURSOR → raw cursor; SINGLE → first row truncated to col_count (or None); NO_RESULTS → closes cursor, returns None; MULTI → yields from `cursor_iter()` helper, materializing into list if not using chunked reads.

##### `as_subquery_condition(self, alias, columns, compiler) → tuple[str, tuple]`
For each column in `query.select`: compiles the select expression, adds a RawSQL equality condition (`lhs = alias.column`) to `query.where` with AND. Calls `as_sql()`, returns `"EXISTS (%s)" % sql, params`.

##### `explain_query(self) → generator[str]`
Executes query via `execute_sql()`. For each row in result[0]: if not a string, joins JSON-formatted or string-converted elements; yields the formatted string.

---

### Class: `SQLInsertCompiler(SQLCompiler)`

#### Attributes (inherited + new)

| Attribute | Type / Default | Description |
|---|---|---|
| `returning_fields` | `None` | Fields to return after insert |
| `returning_params` | `()` | Parameters for the RETURNING clause |

#### Methods

##### `field_as_sql(self, field, val) → tuple[str, tuple]`
Generates placeholder SQL and params for a single field value. If `field is None`: treats `val` as raw SQL, returns `(val, [])`. If `val` has `as_sql`: compiles via `self.compile(val)`. If `field` has `get_placeholder`: calls it with `(val, self, connection)` and wraps val in `[val]`. Else: returns `("%s", [val])`. Calls `connection.ops.modify_insert_params(sql, params)` for Oracle Spatial hook. Returns `(sql, params)`.

##### `prepare_value(self, field, value) → expr`
Prepares a value for insertion. If value has `resolve_expression`: resolves it (no joins, for_save=True). Raises `ValueError` if the resolved expression contains column references (F() can't be used in INSERT). Raises `FieldError` if aggregates or window expressions present. Else: calls `field.get_db_prep_save(value, connection)`. Returns prepared value.

##### `pre_save_val(self, field, obj)`
Gets a field's pre-save value from an object instance. If `query.raw`, returns `getattr(obj, field.attname)`. Otherwise returns `field.pre_save(obj, add=True)`.

##### `assemble_as_sql(self, fields, value_rows) → tuple[list[str], list[list]]`
Takes N fields and M value rows; generates placeholder SQL and params. For each row: zips `(field, value)` pairs through `field_as_sql()`, transposes to separate SQL/param lists, flattens param sublists. Returns `(placeholder_rows, param_rows)`.

##### `as_sql(self) → list[tuple[str, tuple]]`
Generates INSERT statement(s). Gets table name from meta, determines insert statement via `connection.ops.insert_statement(on_conflict=query.on_conflict)`. Builds column list: uses `query.fields` or `[opts.pk]`. For value rows: if fields specified, prepares each value via `prepare_value(pre_save_val(field, obj))`; else generates PK default values. Determines bulk capability: `not returning_fields and has_bulk_insert feature`. Calls `assemble_as_sql()`. Gets on-conflict suffix SQL. If returning fields and can return columns:
  - If bulk insert supported: uses `bulk_insert_sql()` for all rows, params as list of lists.
  - Else: generates single VALUES clause, params as `[param_rows[0]]`.
  Appends RETURNING columns SQL if available. Returns `[(full_sql, flat_params)]` (one tuple).
If bulk capable: returns single INSERT with bulk values and flattened params.
Else: returns list of `(INSERT ... VALUES (...), params)` tuples, one per row.

##### `execute_sql(self, returning_fields=None) → list[tuple]`
Executes the insert. Asserts constraints on returning fields + bulk. Sets `returning_fields`. Opens cursor. Iterates over SQL from `as_sql()`, executing each. If no returning fields: returns `[]`. Otherwise fetches returned data based on feature capabilities (bulk fetch, column fetch, or last_insert_id). Applies converters to rows. Returns list of row tuples.

---

### Class: `SQLDeleteCompiler(SQLCompiler)`

#### Methods

##### `single_alias` (`@cached_property`)
Ensures base table is in aliases via `get_initial_alias()`. Returns `True` if exactly one alias has refcount > 0 in `alias_map`.

##### `_expr_refs_base_model(cls, expr, base_model) → bool` (classmethod)
Recursively checks if an expression references the base model. If it's a Query: compares `.model == base_model`. If no `get_source_expressions`: returns False. Otherwise recurses into all source expressions.

##### `contains_self_reference_subquery` (`@cached_property`)
Returns True if any annotation or WHERE child expression references the base model (via `_expr_refs_base_model`).

##### `_as_sql(self, query) → tuple[str, tuple]`
Generates a simple DELETE statement: `"DELETE FROM quoted_table"`. Compiles WHERE clause; if FullResultSet, returns just the delete with empty params. Otherwise appends `WHERE where_clause`. Returns `(sql, params)`.

##### `as_sql(self) → tuple[str, tuple]`
If single alias and no self-reference subquery: calls `_as_sql(self.query)` directly. Otherwise: clones query into inner query (clearing select), selects only the PK column. Creates outer query; if backend doesn't support self-select, materializes inner as `RawSQL("SELECT * FROM (...) subquery")`. Adds `pk__in` filter with inner query to outer. Calls `_as_sql(outerq)`.

---

### Class: `SQLUpdateCompiler(SQLCompiler)`

#### Methods

##### `as_sql(self) → tuple[str, tuple]`
Generates UPDATE statement. Calls `pre_sql_setup()`. If no values: returns `("", ())`. For each `(field, model, val)` in `query.values`: resolves expressions (no joins, for_save=True), raises `FieldError` for aggregates/window expressions. Handles model instances with `prepare_database_save` (requires remote_field). Otherwise calls `field.get_db_prep_save()`. Gets placeholder via `field.get_placeholder(val, self, connection)` or `"%s"`. If val has `as_sql`: compiles and formats as `"column = sql_expr"`. Else if not None: formats as `"column = %s"` with value param. Else: `"column = NULL"`. Builds result: `"UPDATE quoted_table SET col1=val1, col2=val2"`. Compiles WHERE; if FullResultSet, no WHERE clause. Returns `(sql, params)`.

##### `execute_sql(self, result_type) → int`
Executes the update. Calls parent `execute_sql(result_type)` to get cursor. Extracts `cursor.rowcount` (0 if None). Closes cursor. Iterates over `query.get_related_updates()`: executes each related update via its compiler, tracking first non-empty row count as primary result. Returns total rows affected by primary query.

##### `pre_sql_setup(self)`
Adjusts WHERE conditions for cross-table updates. Gets initial alias. Counts active tables. If no related updates and only one table: returns early. Chains a new Query to collect PK IDs. Clears ordering, extra, select. Adds PK fields (and ancestor PKs if needed). Calls parent `pre_sql_setup()`. If multiple tables or backend doesn't support self-select: executes the ID-collection query, gathers IDs into list and per-parent dicts. Sets `query.add_filter("pk__in", idents)` and `query.related_ids = related_ids`. Else (fast path): sets `query.add_filter("pk__in", subquery)`. Resets refcounts.

---

### Class: `SQLAggregateCompiler(SQLCompiler)`

#### Methods

##### `as_sql(self) → tuple[str, tuple]`
Generates SQL for aggregate-only queries. Iterates over `query.annotation_select.values()`: compiles each annotation, applies `select_format()`, collects SQL and params. Sets `col_count = len(query.annotation_select)`. Joins annotations with `, `. Gets inner query compiler (from `query.inner_query`), calls `as_sql(with_col_aliases=True)`. Returns `"SELECT ann1, ann2 FROM (inner_sql) subquery", combined_params`.

---

### Function: `cursor_iter(cursor, sentinel, col_count, itersize)`
Generator that yields blocks of rows from a cursor. Uses `iter(lambda: cursor.fetchmany(itersize), sentinel)` to fetch in chunks. For each batch of rows: if `col_count is None`, yields as-is; else slices each row to `[:col_count]`. Ensures `cursor.close()` in finally block.