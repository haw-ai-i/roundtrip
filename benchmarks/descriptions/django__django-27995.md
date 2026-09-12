## django/db/models/query.py
1. **Module-Level Preamble:**
   *   **Imports:**
       *   `import copy`
       *   `import operator`
       *   `import warnings`
       *   `from collections import namedtuple`
       *   `from functools import lru_cache`
       *   `from itertools import chain`
       *   `from django.conf import settings`
       *   `from django.core import exceptions`
       *   `from django.db import DJANGO_VERSION_PICKLE_KEY`
       *   `from django.db import IntegrityError`
       *   `from django.db import connections`
       *   `from django.db import router`
       *   `from django.db import transaction`
       *   `from django.db.models import DateField`
       *   `from django.db.models import DateTimeField`
       *   `from django.db.models import sql`
       *   `from django.db.models.constants import LOOKUP_SEP`
       *   `from django.db.models.deletion import Collector`
       *   `from django.db.models.expressions import Case`
       *   `from django.db.models.expressions import Expression`
       *   `from django.db.models.expressions import F`
       *   `from django.db.models.expressions import Value`
       *   `from django.db.models.expressions import When`
       *   `from django.db.models.fields import AutoField`
       *   `from django.db.models.functions import Cast`
       *   `from django.db.models.functions import Trunc`
       *   `from django.db.models.query_utils import FilteredRelation`
       *   `from django.db.models.query_utils import InvalidQuery`
       *   `from django.db.models.query_utils import Q`
       *   `from django.db.models.sql.constants import CURSOR`
       *   `from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE`
       *   `from django.db.utils import NotSupportedError`
       *   `from django.utils import timezone`
       *   `from django.utils.functional import cached_property`
       *   `from django.utils.functional import partition`
       *   `from django.utils.version import get_version`
   *   **Constants & Globals:**
       *   `MAX_GET_RESULTS = 21`
       *   `REPR_OUTPUT_SIZE = 20`
       *   `EmptyResultSet = sql.EmptyResultSet`

2. **Code Objects (Classes and Functions):**
   *   **Class:** `BaseIterable`
       *   **Bases:** 
       *   **Method:** `__init__`
           *   **Signature:** `self, queryset, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE`
           *   **Implementation Logic:**
               *   Initializes the iterable with the given queryset, chunked_fetch flag, and chunk_size.
   *   **Class:** `ModelIterable`
       *   **Bases:** BaseIterable
       *   **Method:** `__iter__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Yields model instances for each row returned by the database compiler. Handles related object population if `select_related` is used.
   *   **Class:** `ValuesIterable`
       *   **Bases:** BaseIterable
       *   **Method:** `__iter__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Yields dictionaries mapping field names to values for each row.
   *   **Class:** `ValuesListIterable`
       *   **Bases:** BaseIterable
       *   **Method:** `__iter__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Yields tuples of values for each row.
   *   **Class:** `NamedValuesListIterable`
       *   **Bases:** ValuesListIterable
       *   **Method:** `create_namedtuple_class`
           *   **Signature:** `*names`
           *   **Implementation Logic:**
               *   Creates and caches a `namedtuple` class for the given field names.
       *   **Method:** `__iter__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Yields namedtuples of values for each row.
   *   **Class:** `FlatValuesListIterable`
       *   **Bases:** BaseIterable
       *   **Method:** `__iter__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Yields the first value of each row directly (flat list).
   *   **Class:** `QuerySet`
       *   **Bases:** 
       *   **Method:** `__init__`
           *   **Signature:** `self, model=None, query=None, using=None, hints=None`
           *   **Implementation Logic:**
               *   Initializes the QuerySet with a model, an optional SQL query object, database alias, and hints.
       *   **Method:** `as_manager`
           *   **Signature:** `cls`
           *   **Implementation Logic:**
               *   Returns a Manager instance with methods from this QuerySet class.
       *   **Method:** `__deepcopy__`
           *   **Signature:** `self, memo`
           *   **Implementation Logic:**
               *   Creates a deep copy of the QuerySet, ensuring the result cache is not shared.
       *   **Method:** `__getstate__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Forces evaluation of the QuerySet and returns its state for pickling.
       *   **Method:** `__setstate__`
           *   **Signature:** `self, state`
           *   **Implementation Logic:**
               *   Restores the QuerySet state from a pickle.
       *   **Method:** `__repr__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns a string representation of the QuerySet, evaluating it up to `REPR_OUTPUT_SIZE + 1` elements.
       *   **Method:** `__len__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns the number of elements in the evaluated QuerySet.
       *   **Method:** `__iter__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Evaluates the QuerySet and returns an iterator over its results.
       *   **Method:** `__bool__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns True if the QuerySet contains any results, False otherwise.
       *   **Method:** `__getitem__`
           *   **Signature:** `self, k`
           *   **Implementation Logic:**
               *   Supports slicing and indexing of the QuerySet, modifying the underlying SQL query accordingly.
       *   **Method:** `__and__`
           *   **Signature:** `self, other`
           *   **Implementation Logic:**
               *   Combines two QuerySets using SQL AND.
       *   **Method:** `__or__`
           *   **Signature:** `self, other`
           *   **Implementation Logic:**
               *   Combines two QuerySets using SQL OR.
       *   **Method:** `_iterator`
           *   **Signature:** `self, use_chunked_fetch, chunk_size`
           *   **Implementation Logic:**
               *   Internal method to yield results from the database using the appropriate iterable class.
       *   **Method:** `iterator`
           *   **Signature:** `self, chunk_size=2000`
           *   **Implementation Logic:**
               *   Returns an iterator that fetches results in chunks, avoiding loading all results into memory at once.
       *   **Method:** `aggregate`
           *   **Signature:** `self, *args, **kwargs`
           *   **Implementation Logic:**
               *   Computes and returns a dictionary of aggregate values (e.g., Count, Sum) over the QuerySet.
       *   **Method:** `count`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns the total number of objects matching the QuerySet, using a SQL COUNT query if not already evaluated.
       *   **Method:** `get`
           *   **Signature:** `self, *args, **kwargs`
           *   **Implementation Logic:**
               *   Returns a single object matching the given lookups. Raises `DoesNotExist` if none found, or `MultipleObjectsReturned` if more than one found.
       *   **Method:** `create`
           *   **Signature:** `self, **kwargs`
           *   **Implementation Logic:**
               *   Creates and saves a new object with the given kwargs, returning the instance.
       *   **Method:** `_populate_pk_values`
           *   **Signature:** `self, objs`
           *   **Implementation Logic:**
               *   Populates primary key values on objects before bulk insertion if the database supports it.
       *   **Method:** `bulk_create`
           *   **Signature:** `self, objs, batch_size=None, ignore_conflicts=False`
           *   **Implementation Logic:**
               *   Inserts a list of objects into the database in an efficient manner.
       *   **Method:** `bulk_update`
           *   **Signature:** `self, objs, fields, batch_size=None`
           *   **Implementation Logic:**
               *   Updates specific fields on a list of objects in the database efficiently.
       *   **Method:** `get_or_create`
           *   **Signature:** `self, defaults=None, **kwargs`
           *   **Implementation Logic:**
               *   Looks up an object with the given kwargs, creating one if it doesn't exist. Returns a tuple of `(object, created)`.
       *   **Method:** `update_or_create`
           *   **Signature:** `self, defaults=None, **kwargs`
           *   **Implementation Logic:**
               *   Looks up an object with the given kwargs, updating it with `defaults` if it exists, or creating it otherwise. Returns `(object, created)`.
       *   **Method:** `_create_object_from_params`
           *   **Signature:** `self, lookup, params, lock=False`
           *   **Implementation Logic:**
               *   Helper method for `get_or_create` and `update_or_create` to instantiate and save the object.
       *   **Method:** `_extract_model_params`
           *   **Signature:** `self, defaults, **kwargs`
           *   **Implementation Logic:**
               *   Extracts parameters for model instantiation from lookups and defaults.
       *   **Method:** `_earliest`
           *   **Signature:** `self, *fields`
           *   **Implementation Logic:**
               *   Helper method to return the earliest or latest object based on the given fields.
       *   **Method:** `earliest`
           *   **Signature:** `self, *fields`
           *   **Implementation Logic:**
               *   Returns the earliest object according to the given fields or the model's `get_latest_by` option.
       *   **Method:** `latest`
           *   **Signature:** `self, *fields`
           *   **Implementation Logic:**
               *   Returns the latest object according to the given fields or the model's `get_latest_by` option.
       *   **Method:** `first`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns the first object of a query, or None if no match is found.
       *   **Method:** `last`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns the last object of a query, or None if no match is found.
       *   **Method:** `in_bulk`
           *   **Signature:** `self, id_list=None, *, field_name='pk'`
           *   **Implementation Logic:**
               *   Returns a dictionary mapping each of the given IDs to the object with that ID.
       *   **Method:** `delete`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Deletes the records in the current QuerySet and returns a dictionary with the number of objects deleted per model.
       *   **Method:** `_raw_delete`
           *   **Signature:** `self, using`
           *   **Implementation Logic:**
               *   Executes a fast SQL DELETE without fetching objects into memory or calling `delete()` methods.
       *   **Method:** `update`
           *   **Signature:** `self, **kwargs`
           *   **Implementation Logic:**
               *   Updates all elements in the current QuerySet with the given kwargs. Returns the number of rows matched.
       *   **Method:** `_update`
           *   **Signature:** `self, values`
           *   **Implementation Logic:**
               *   Internal method to execute the SQL UPDATE query.
       *   **Method:** `exists`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns True if the QuerySet contains any results, False otherwise, using an optimized SQL EXISTS query.
       *   **Method:** `_prefetch_related_objects`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Populates prefetched object caches for the evaluated QuerySet.
       *   **Method:** `explain`
           *   **Signature:** `self, *, format=None, **options`
           *   **Implementation Logic:**
               *   Returns the query execution plan from the database.
       *   **Method:** `raw`
           *   **Signature:** `self, raw_query, params=None, translations=None, using=None`
           *   **Implementation Logic:**
               *   Returns a `RawQuerySet` for executing raw SQL queries.
       *   **Method:** `_values`
           *   **Signature:** `self, *fields, **expressions`
           *   **Implementation Logic:**
               *   Internal method to configure the QuerySet to return dictionaries or tuples instead of model instances.
       *   **Method:** `values`
           *   **Signature:** `self, *fields, **expressions`
           *   **Implementation Logic:**
               *   Returns a QuerySet that yields dictionaries instead of model instances.
       *   **Method:** `values_list`
           *   **Signature:** `self, *fields, flat=False, named=False`
           *   **Implementation Logic:**
               *   Returns a QuerySet that yields tuples instead of model instances.
       *   **Method:** `dates`
           *   **Signature:** `self, field_name, kind, order='ASC'`
           *   **Implementation Logic:**
               *   Returns a QuerySet that evaluates to a list of datetime.date objects representing all available dates of a given kind.
       *   **Method:** `datetimes`
           *   **Signature:** `self, field_name, kind, order='ASC', tzinfo=None`
           *   **Implementation Logic:**
               *   Returns a QuerySet that evaluates to a list of datetime.datetime objects representing all available datetimes of a given kind.
       *   **Method:** `none`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns an `EmptyQuerySet` that will always evaluate to an empty list.
       *   **Method:** `all`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns a new QuerySet that is a copy of the current one.
       *   **Method:** `filter`
           *   **Signature:** `self, *args, **kwargs`
           *   **Implementation Logic:**
               *   Returns a new QuerySet containing objects that match the given lookup parameters.
       *   **Method:** `exclude`
           *   **Signature:** `self, *args, **kwargs`
           *   **Implementation Logic:**
               *   Returns a new QuerySet containing objects that do not match the given lookup parameters.
       *   **Method:** `_filter_or_exclude`
           *   **Signature:** `self, negate, *args, **kwargs`
           *   **Implementation Logic:**
               *   Internal method to apply filters or exclusions to the query.
       *   **Method:** `complex_filter`
           *   **Signature:** `self, filter_obj`
           *   **Implementation Logic:**
               *   Returns a new QuerySet with the given complex filter object (e.g., a Q object) applied.
       *   **Method:** `_combinator_query`
           *   **Signature:** `self, combinator, *other_qs, all=False`
           *   **Implementation Logic:**
               *   Internal method to combine multiple QuerySets using SQL set operations (UNION, INTERSECT, EXCEPT).
       *   **Method:** `union`
           *   **Signature:** `self, *other_qs, all=False`
           *   **Implementation Logic:**
               *   Returns a new QuerySet representing the SQL UNION of this QuerySet and others.
       *   **Method:** `intersection`
           *   **Signature:** `self, *other_qs`
           *   **Implementation Logic:**
               *   Returns a new QuerySet representing the SQL INTERSECT of this QuerySet and others.
       *   **Method:** `difference`
           *   **Signature:** `self, *other_qs`
           *   **Implementation Logic:**
               *   Returns a new QuerySet representing the SQL EXCEPT of this QuerySet and others.
       *   **Method:** `select_for_update`
           *   **Signature:** `self, nowait=False, skip_locked=False, of=()`
           *   **Implementation Logic:**
               *   Returns a new QuerySet that will lock rows until the end of the transaction.
       *   **Method:** `select_related`
           *   **Signature:** `self, *fields`
           *   **Implementation Logic:**
               *   Returns a new QuerySet that will "follow" foreign-key relationships, selecting additional related-object data when it executes its query.
       *   **Method:** `prefetch_related`
           *   **Signature:** `self, *lookups`
           *   **Implementation Logic:**
               *   Returns a new QuerySet that will automatically retrieve, in a single batch, related objects for each of the specified lookups.
       *   **Method:** `annotate`
           *   **Signature:** `self, *args, **kwargs`
           *   **Implementation Logic:**
               *   Returns a new QuerySet with the given annotations added to each object.
       *   **Method:** `order_by`
           *   **Signature:** `self, *field_names`
           *   **Implementation Logic:**
               *   Returns a new QuerySet ordered by the given field names.
       *   **Method:** `distinct`
           *   **Signature:** `self, *field_names`
           *   **Implementation Logic:**
               *   Returns a new QuerySet that uses SELECT DISTINCT in its SQL query.
       *   **Method:** `extra`
           *   **Signature:** `self, select=None, where=None, params=None, tables=None, order_by=None, select_params=None`
           *   **Implementation Logic:**
               *   Adds extra SQL fragments to the query.
       *   **Method:** `reverse`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Reverses the ordering of the QuerySet.
       *   **Method:** `defer`
           *   **Signature:** `self, *fields`
           *   **Implementation Logic:**
               *   Defers the loading of the specified fields until they are accessed.
       *   **Method:** `only`
           *   **Signature:** `self, *fields`
           *   **Implementation Logic:**
               *   Restricts the loaded fields to only the specified ones (and the primary key).
       *   **Method:** `using`
           *   **Signature:** `self, alias`
           *   **Implementation Logic:**
               *   Selects which database this QuerySet should execute against.
       *   **Method:** `ordered`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns True if the QuerySet is ordered, False otherwise.
       *   **Method:** `db`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns the database alias that will be used if this query is executed now.
       *   **Method:** `_insert`
           *   **Signature:** `self, objs, fields, return_id=False, raw=False, using=None, ignore_conflicts=False`
           *   **Implementation Logic:**
               *   Internal method to execute an SQL INSERT query.
       *   **Method:** `_batched_insert`
           *   **Signature:** `self, objs, fields, batch_size, ignore_conflicts=False`
           *   **Implementation Logic:**
               *   Internal method to insert objects in batches.
       *   **Method:** `_chain`
           *   **Signature:** `self, **kwargs`
           *   **Implementation Logic:**
               *   Returns a copy of the current QuerySet, updating its properties with the given kwargs.
       *   **Method:** `_clone`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns a copy of the current QuerySet.
       *   **Method:** `_fetch_all`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Evaluates the QuerySet and populates the result cache.
       *   **Method:** `_next_is_sticky`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Indicates that the next filter call should be applied to the same table alias.
       *   **Method:** `_merge_sanity_check`
           *   **Signature:** `self, other`
           *   **Implementation Logic:**
               *   Checks if two QuerySets can be merged (e.g., they must be of the same model).
       *   **Method:** `_merge_known_related_objects`
           *   **Signature:** `self, other`
           *   **Implementation Logic:**
               *   Merges known related objects from another QuerySet into this one.
       *   **Method:** `resolve_expression`
           *   **Signature:** `self, *args, **kwargs`
           *   **Implementation Logic:**
               *   Resolves the QuerySet as an expression (e.g., a subquery).
       *   **Method:** `_add_hints`
           *   **Signature:** `self, **hints`
           *   **Implementation Logic:**
               *   Adds hints to the QuerySet for database routers.
       *   **Method:** `_has_filters`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns True if the QuerySet has any filters applied.
       *   **Method:** `_validate_values_are_expressions`
           *   **Signature:** `values, method_name`
           *   **Implementation Logic:**
               *   Validates that the given values are valid expressions for methods like `annotate`.
   *   **Class:** `InstanceCheckMeta`
       *   **Bases:** type
       *   **Method:** `__instancecheck__`
           *   **Signature:** `self, instance`
           *   **Implementation Logic:**
               *   Custom `isinstance` check for `EmptyQuerySet`.
   *   **Class:** `EmptyQuerySet`
       *   **Bases:** 
       *   **Method:** `__init__`
           *   **Signature:** `self, *args, **kwargs`
           *   **Implementation Logic:**
               *   Raises a TypeError, as `EmptyQuerySet` cannot be instantiated directly.
   *   **Class:** `RawQuerySet`
       *   **Bases:** 
       *   **Method:** `__init__`
           *   **Signature:** `self, raw_query, model=None, query=None, params=None, translations=None, using=None, hints=None`
           *   **Implementation Logic:**
               *   Initializes a RawQuerySet with a raw SQL query and parameters.
       *   **Method:** `resolve_model_init_order`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Resolves the order in which model fields should be initialized from the raw query columns.
       *   **Method:** `prefetch_related`
           *   **Signature:** `self, *lookups`
           *   **Implementation Logic:**
               *   Adds prefetch lookups to the RawQuerySet.
       *   **Method:** `_prefetch_related_objects`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Populates prefetched object caches for the evaluated RawQuerySet.
       *   **Method:** `_clone`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns a copy of the RawQuerySet.
       *   **Method:** `_fetch_all`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Evaluates the RawQuerySet and populates the result cache.
       *   **Method:** `__len__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns the number of elements in the evaluated RawQuerySet.
       *   **Method:** `__bool__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns True if the RawQuerySet contains any results.
       *   **Method:** `__iter__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Evaluates the RawQuerySet and returns an iterator over its results.
       *   **Method:** `iterator`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns an iterator over the raw query results, instantiating models.
       *   **Method:** `__repr__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns a string representation of the RawQuerySet.
       *   **Method:** `__getitem__`
           *   **Signature:** `self, k`
           *   **Implementation Logic:**
               *   Supports slicing and indexing of the RawQuerySet.
       *   **Method:** `db`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns the database alias that will be used.
       *   **Method:** `using`
           *   **Signature:** `self, alias`
           *   **Implementation Logic:**
               *   Selects which database this RawQuerySet should execute against.
       *   **Method:** `columns`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns a list of column names from the raw query.
       *   **Method:** `model_fields`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns a dictionary mapping column names to model fields.
   *   **Class:** `Prefetch`
       *   **Bases:** 
       *   **Method:** `__init__`
           *   **Signature:** `self, lookup, queryset=None, to_attr=None`
           *   **Implementation Logic:**
               *   Initializes a Prefetch object with a lookup string, an optional custom queryset, and an optional destination attribute name.
       *   **Method:** `__getstate__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns the state of the Prefetch object for pickling.
       *   **Method:** `add_prefix`
           *   **Signature:** `self, prefix`
           *   **Implementation Logic:**
               *   Adds a prefix to the prefetch lookup.
       *   **Method:** `get_current_prefetch_to`
           *   **Signature:** `self, level`
           *   **Implementation Logic:**
               *   Returns the prefetch path up to the given level.
       *   **Method:** `get_current_to_attr`
           *   **Signature:** `self, level`
           *   **Implementation Logic:**
               *   Returns the destination attribute name for the given level.
       *   **Method:** `get_current_queryset`
           *   **Signature:** `self, level`
           *   **Implementation Logic:**
               *   Returns the custom queryset for the given level, if any.
       *   **Method:** `__eq__`
           *   **Signature:** `self, other`
           *   **Implementation Logic:**
               *   Checks equality based on the prefetch destination.
       *   **Method:** `__hash__`
           *   **Signature:** `self`
           *   **Implementation Logic:**
               *   Returns a hash based on the prefetch destination.
   *   **Function:** `normalize_prefetch_lookups`
       *   **Signature:** `lookups, prefix=None`
       *   **Implementation Logic:**
           *   Converts a list of string lookups or Prefetch objects into a list of Prefetch objects, optionally adding a prefix.
   *   **Function:** `prefetch_related_objects`
       *   **Signature:** `model_instances, *related_lookups`
       *   **Implementation Logic:**
           *   Populates prefetched object caches for a list of model instances based on the given lookups.
   *   **Function:** `get_prefetcher`
       *   **Signature:** `instance, through_attr, to_attr`
       *   **Implementation Logic:**
           *   Finds the object responsible for prefetching a specific attribute on a model instance.
   *   **Function:** `prefetch_one_level`
       *   **Signature:** `instances, prefetcher, lookup, level`
       *   **Implementation Logic:**
           *   Executes a single level of prefetching for a list of instances using the given prefetcher.
   *   **Class:** `RelatedPopulator`
       *   **Bases:** 
       *   **Method:** `__init__`
           *   **Signature:** `self, klass_info, select, db`
           *   **Implementation Logic:**
               *   Initializes the populator with information about the related class and the columns to select.
       *   **Method:** `populate`
           *   **Signature:** `self, row, from_obj`
           *   **Implementation Logic:**
               *   Instantiates a related object from a database row and assigns it to the parent object.
   *   **Function:** `get_related_populators`
       *   **Signature:** `klass_info, select, db`
       *   **Implementation Logic:**
           *   Returns a list of `RelatedPopulator` instances for a given class info dictionary.