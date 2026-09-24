## django/db/models/query_utils.py
**1. Module-Level Preamble**

**Imports:**
```python
import functools
import inspect
import logging
from collections import namedtuple

from django.core.exceptions import FieldError
from django.db import DEFAULT_DB_ALIAS, DatabaseError
from django.db.models.constants import LOOKUP_SEP
from django.utils import tree
```

**Constants & Globals:**
*   `logger`: `logging.getLogger("django.db.models")`
*   `PathInfo`: `namedtuple("PathInfo", "from_opts to_opts target_fields join_field m2m direct filtered_relation")`

---

**2. Code Objects (Classes and Functions)**

**Function: `subclasses`**
*   **Signature:** `def subclasses(cls)`
*   **Implementation Logic:**
    *   Yields the provided `cls`.
    *   Iterates over `cls.__subclasses__()`.
    *   Recursively yields from `subclasses(subclass)` for each subclass.

**Class: `Q`**
*   **Base Classes:** `tree.Node`
*   **Attributes:**
    *   `AND`: `"AND"`
    *   `OR`: `"OR"`
    *   `XOR`: `"XOR"`
    *   `default`: `AND`
    *   `conditional`: `True`
*   **Method: `__init__`**
    *   **Signature:** `def __init__(self, *args, _connector=None, _negated=False, **kwargs)`
    *   **Implementation Logic:** Calls `super().__init__()` with `children=[*args, *sorted(kwargs.items())]`, `connector=_connector`, and `negated=_negated`.
*   **Method: `_combine`**
    *   **Signature:** `def _combine(self, other, conn)`
    *   **Implementation Logic:**
        *   Raises `TypeError(other)` if `getattr(other, "conditional", False)` is `False`.
        *   If `not self`, returns `other.copy()`.
        *   If `not other` and `isinstance(other, Q)`, returns `self.copy()`.
        *   Creates a new instance `obj = self.create(connector=conn)`.
        *   Calls `obj.add(self, conn)` and `obj.add(other, conn)`.
        *   Returns `obj`.
*   **Method: `__or__`**
    *   **Signature:** `def __or__(self, other)`
    *   **Implementation Logic:** Returns `self._combine(other, self.OR)`.
*   **Method: `__and__`**
    *   **Signature:** `def __and__(self, other)`
    *   **Implementation Logic:** Returns `self._combine(other, self.AND)`.
*   **Method: `__xor__`**
    *   **Signature:** `def __xor__(self, other)`
    *   **Implementation Logic:** Returns `self._combine(other, self.XOR)`.
*   **Method: `__invert__`**
    *   **Signature:** `def __invert__(self)`
    *   **Implementation Logic:** Creates a copy of `self`, calls `negate()` on the copy, and returns it.
*   **Method: `resolve_expression`**
    *   **Signature:** `def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`
    *   **Implementation Logic:**
        *   Calls `query._add_q(self, reuse, allow_joins=allow_joins, split_subq=False, check_filterable=False)` and unpacks into `clause, joins`.
        *   Calls `query.promote_joins(joins)`.
        *   Returns `clause`.
*   **Method: `flatten`**
    *   **Signature:** `def flatten(self)`
    *   **Implementation Logic:**
        *   Yields `self`.
        *   Iterates over `self.children`:
            *   If the child is a tuple, reassigns `child = child[1]`.
            *   If `hasattr(child, "flatten")`, yields from `child.flatten()`.
            *   Otherwise, yields `child`.
*   **Method: `check`**
    *   **Signature:** `def check(self, against, using=DEFAULT_DB_ALIAS)`
    *   **Implementation Logic:**
        *   Imports `Value` from `django.db.models`, `Query` from `django.db.models.sql`, and `SINGLE` from `django.db.models.sql.constants`.
        *   Instantiates `query = Query(None)`.
        *   Iterates over `name, value` in `against.items()`:
            *   If `not hasattr(value, "resolve_expression")`, wraps it as `value = Value(value)`.
            *   Calls `query.add_annotation(value, name, select=False)`.
        *   Calls `query.add_annotation(Value(1), "_check")`.
        *   Calls `query.add_q(self)`.
        *   Gets the compiler via `query.get_compiler(using=using)`.
        *   Tries to return `compiler.execute_sql(SINGLE) is not None`.
        *   Catches `DatabaseError` as `e`, logs a warning `"Got a database error calling check() on %r: %s"` with `self` and `e`, and returns `True`.
*   **Method: `deconstruct`**
    *   **Signature:** `def deconstruct(self)`
    *   **Implementation Logic:**
        *   Constructs `path = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)`.
        *   If `path` starts with `"django.db.models.query_utils"`, replaces it with `"django.db.models"`.
        *   Sets `args = tuple(self.children)` and `kwargs = {}`.
        *   If `self.connector != self.default`, sets `kwargs["_connector"] = self.connector`.
        *   If `self.negated`, sets `kwargs["_negated"] = True`.
        *   Returns `path, args, kwargs`.

**Class: `DeferredAttribute`**
*   **Method: `__init__`**
    *   **Signature:** `def __init__(self, field)`
    *   **Implementation Logic:** Sets `self.field = field`.
*   **Method: `__get__`**
    *   **Signature:** `def __get__(self, instance, cls=None)`
    *   **Implementation Logic:**
        *   If `instance is None`, returns `self`.
        *   Sets `data = instance.__dict__` and `field_name = self.field.attname`.
        *   If `field_name not in data`:
            *   Calls `self._check_parent_chain(instance)` and assigns to `val`.
            *   If `val is None`, calls `instance.refresh_from_db(fields=[field_name])`.
            *   Else, sets `data[field_name] = val`.
        *   Returns `data[field_name]`.
*   **Method: `_check_parent_chain`**
    *   **Signature:** `def _check_parent_chain(self, instance)`
    *   **Implementation Logic:**
        *   Sets `opts = instance._meta`.
        *   Sets `link_field = opts.get_ancestor_link(self.field.model)`.
        *   If `self.field.primary_key` is true and `self.field != link_field`, returns `getattr(instance, link_field.attname)`.
        *   Returns `None`.

**Class: `RegisterLookupMixin`**
*   **Method: `_get_lookup`** (Class Method)
    *   **Signature:** `def _get_lookup(cls, lookup_name)`
    *   **Implementation Logic:** Returns `cls.get_lookups().get(lookup_name, None)`.
*   **Method: `get_lookups`** (Class Method, decorated with `@functools.lru_cache(maxsize=None)`)
    *   **Signature:** `def get_lookups(cls)`
    *   **Implementation Logic:**
        *   Creates a list `class_lookups` containing `parent.__dict__.get("class_lookups", {})` for each `parent` in `inspect.getmro(cls)`.
        *   Returns `cls.merge_dicts(class_lookups)`.
*   **Method: `get_lookup`**
    *   **Signature:** `def get_lookup(self, lookup_name)`
    *   **Implementation Logic:**
        *   Imports `Lookup` from `django.db.models.lookups`.
        *   Sets `found = self._get_lookup(lookup_name)`.
        *   If `found is None` and `hasattr(self, "output_field")`, returns `self.output_field.get_lookup(lookup_name)`.
        *   If `found is not None` and `not issubclass(found, Lookup)`, returns `None`.
        *   Returns `found`.
*   **Method: `get_transform`**
    *   **Signature:** `def get_transform(self, lookup_name)`
    *   **Implementation Logic:**
        *   Imports `Transform` from `django.db.models.lookups`.
        *   Sets `found = self._get_lookup(lookup_name)`.
        *   If `found is None` and `hasattr(self, "output_field")`, returns `self.output_field.get_transform(lookup_name)`.
        *   If `found is not None` and `not issubclass(found, Transform)`, returns `None`.
        *   Returns `found`.
*   **Method: `merge_dicts`** (Static Method)
    *   **Signature:** `def merge_dicts(dicts)`
    *   **Implementation Logic:**
        *   Initializes `merged = {}`.
        *   Iterates over `d` in `reversed(dicts)` and calls `merged.update(d)`.
        *   Returns `merged`.
*   **Method: `_clear_cached_lookups`** (Class Method)
    *   **Signature:** `def _clear_cached_lookups(cls)`
    *   **Implementation Logic:** Iterates over `subclass` in `subclasses(cls)` and calls `subclass.get_lookups.cache_clear()`.
*   **Method: `register_lookup`** (Class Method)
    *   **Signature:** `def register_lookup(cls, lookup, lookup_name=None)`
    *   **Implementation Logic:**
        *   If `lookup_name is None`, sets it to `lookup.lookup_name`.
        *   If `"class_lookups" not in cls.__dict__`, sets `cls.class_lookups = {}`.
        *   Sets `cls.class_lookups[lookup_name] = lookup`.
        *   Calls `cls._clear_cached_lookups()`.
        *   Returns `lookup`.
*   **Method: `_unregister_lookup`** (Class Method)
    *   **Signature:** `def _unregister_lookup(cls, lookup, lookup_name=None)`
    *   **Implementation Logic:**
        *   If `lookup_name is None`, sets it to `lookup.lookup_name`.
        *   Deletes `cls.class_lookups[lookup_name]`.
        *   Calls `cls._clear_cached_lookups()`.

**Function: `select_related_descend`**
*   **Signature:** `def select_related_descend(field, restricted, requested, load_fields, reverse=False)`
*   **Implementation Logic:**
    *   If `not field.remote_field`, returns `False`.
    *   If `field.remote_field.parent_link` and `not reverse`, returns `False`.
    *   If `restricted`:
        *   If `reverse` and `field.related_query_name() not in requested`, returns `False`.
        *   If `not reverse` and `field.name not in requested`, returns `False`.
    *   If `not restricted` and `field.null`, returns `False`.
    *   If `restricted` and `load_fields` and `field.name in requested` and `field.attname not in load_fields`, raises `FieldError` with a message indicating the field cannot be both deferred and traversed.
    *   Returns `True`.

**Function: `refs_expression`**
*   **Signature:** `def refs_expression(lookup_parts, annotations)`
*   **Implementation Logic:**
    *   Iterates `n` from `1` to `len(lookup_parts) + 1`:
        *   Sets `level_n_lookup = LOOKUP_SEP.join(lookup_parts[0:n])`.
        *   If `level_n_lookup in annotations` and `annotations[level_n_lookup]` is truthy, returns `annotations[level_n_lookup], lookup_parts[n:]`.
    *   Returns `False, ()`.

**Function: `check_rel_lookup_compatibility`**
*   **Signature:** `def check_rel_lookup_compatibility(model, target_opts, field)`
*   **Implementation Logic:**
    *   Defines an inner function `check(opts)` that returns `True` if `model._meta.concrete_model == opts.concrete_model`, or `opts.concrete_model in model._meta.get_parent_list()`, or `model in opts.get_parent_list()`.
    *   Returns `check(target_opts) or (getattr(field, "primary_key", False) and check(field.model._meta))`.

**Class: `FilteredRelation`**
*   **Method: `__init__`**
    *   **Signature:** `def __init__(self, relation_name, *, condition=Q())`
    *   **Implementation Logic:**
        *   Raises `ValueError("relation_name cannot be empty.")` if `not relation_name`.
        *   Sets `self.relation_name = relation_name` and `self.alias = None`.
        *   Raises `ValueError("condition argument must be a Q() instance.")` if `not isinstance(condition, Q)`.
        *   Sets `self.condition = condition` and `self.path = []`.
*   **Method: `__eq__`**
    *   **Signature:** `def __eq__(self, other)`
    *   **Implementation Logic:**
        *   If `not isinstance(other, self.__class__)`, returns `NotImplemented`.
        *   Returns `True` if `self.relation_name == other.relation_name`, `self.alias == other.alias`, and `self.condition == other.condition`.
*   **Method: `clone`**
    *   **Signature:** `def clone(self)`
    *   **Implementation Logic:**
        *   Creates `clone = FilteredRelation(self.relation_name, condition=self.condition)`.
        *   Sets `clone.alias = self.alias` and `clone.path = self.path[:]`.
        *   Returns `clone`.
*   **Method: `resolve_expression`**
    *   **Signature:** `def resolve_expression(self, *args, **kwargs)`
    *   **Implementation Logic:** Raises `NotImplementedError("FilteredRelation.resolve_expression() is unused.")`.
*   **Method: `as_sql`**
    *   **Signature:** `def as_sql(self, compiler, connection)`
    *   **Implementation Logic:**
        *   Sets `query = compiler.query`.
        *   Sets `where = query.build_filtered_relation_q(self.condition, reuse=set(self.path))`.
        *   Returns `compiler.compile(where)`.

## django/db/models/sql/compiler.py
I have read the file `django/db/models/sql/compiler.py` and written a complete natural-language specification of it to `/tmp/tmpm9yi7naz.md`.

## django/db/models/sql/query.py
This is a natural-language specification of `django/db/models/sql/query.py`.

## Module-Level Preamble

### Imports
The module imports standard library modules (`copy`, `difflib`, `functools`, `sys`, `collections`, `collections.abc`, `itertools`, `string`), Django exceptions (`FieldDoesNotExist`, `FieldError`), database utilities (`DEFAULT_DB_ALIAS`, `NotSupportedError`, `connections`), model aggregates (`Count`), constants (`LOOKUP_SEP`), expressions (`BaseExpression`, `Col`, `Exists`, `F`, `OuterRef`, `Ref`, `ResolvedOuterRef`, `Value`), fields (`Field`), related lookups (`MultiColSource`), lookups (`Lookup`), query utilities (`Q`, `check_rel_lookup_compatibility`, `refs_expression`), SQL constants (`INNER`, `LOUTER`, `ORDER_DIR`, `SINGLE`), SQL datastructures (`BaseTable`, `Empty`, `Join`, `MultiJoin`), SQL where nodes (`AND`, `OR`, `ExtraWhere`, `NothingNode`, `WhereNode`), functional utilities (`cached_property`), regex helpers (`_lazy_re_compile`), and tree nodes (`Node`).

### Constants & Globals
*   `__all__`: `["Query", "RawQuery"]`
*   `FORBIDDEN_ALIAS_PATTERN`: A compiled regex matching forbidden characters in column aliases (`['`"\]\[;\s]|--|/\*|\*/`).
*   `EXPLAIN_OPTIONS_PATTERN`: A compiled regex matching valid EXPLAIN options (`[\w\-]+`).
*   `JoinInfo`: A `namedtuple` with fields `("final_field", "targets", "opts", "joins", "path", "transform_function")`.
*   `ExplainInfo`: A `namedtuple` with fields `("format", "options")`.

## Code Objects

### `get_field_names_from_opts(opts)`
*   **Signature:** `def get_field_names_from_opts(opts):`
*   **Logic:** Returns a set of field names and attnames from the given model options (`opts`). If `opts` is `None`, returns an empty set.

### `get_children_from_q(q)`
*   **Signature:** `def get_children_from_q(q):`
*   **Logic:** A generator that yields all non-`Node` children from a `Q` object recursively.

### `RawQuery`
*   **Signature:** `class RawQuery:`
*   **Attributes:** `params`, `sql`, `using`, `cursor`, `low_mark`, `high_mark`, `extra_select`, `annotation_select`.
*   **Logic:** Represents a raw SQL query. Provides methods like `chain`, `clone`, `get_columns`, `get_compiler`, `get_meta`, and `_execute_query` to execute the raw SQL and fetch results.

### `Query`
*   **Signature:** `class Query(BaseExpression):`
*   **Logic:** The core class representing a single SQL query. It encapsulates all SQL construction logic for QuerySets.
    *   It manages the `select`, `where`, `order_by`, `group_by`, `having`, and `limit`/`offset` clauses.
    *   It handles joins (`alias_map`, `alias_refcount`) and table aliases.
    *   It provides methods for cloning (`clone`), combining (`combine`), and resolving expressions (`resolve_expression`).
    *   It includes complex logic for building filter conditions (`build_filter`), adding joins (`setup_joins`, `join`), and handling annotations and aggregations.
    *   It manages the query state (e.g., `is_sliced`, `has_select_fields`, `distinct`).

### `get_order_dir(field, default="ASC")`
*   **Signature:** `def get_order_dir(field, default="ASC"):`
*   **Logic:** Parses an order specification (e.g., `'-foo'`) and returns a tuple of the field name and direction (`('foo', 'DESC')`).

### `add_to_dict(data, key, value)`
*   **Signature:** `def add_to_dict(data, key, value):`
*   **Logic:** Adds `value` to a set stored at `data[key]`. If `key` doesn't exist, it creates a new set.

### `is_reverse_o2o(field)`
*   **Signature:** `def is_reverse_o2o(field):`
*   **Logic:** Checks if a field is a reverse one-to-one relation (`field.is_relation and field.one_to_one and not field.concrete`).

### `JoinPromoter`
*   **Signature:** `class JoinPromoter:`
*   **Logic:** Abstracts away join promotion problems for complex filter conditions. It tracks joins added to a query and determines which ones need to be promoted to `LEFT OUTER JOIN` based on the logical structure of the `WHERE` clause (e.g., when joins are used within an `OR` condition).