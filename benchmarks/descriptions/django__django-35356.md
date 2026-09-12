## django/db/models/query_utils.py
**1. Module-Level Preamble**

*   **Imports:**
    *   `import functools`
    *   `import inspect`
    *   `import logging`
    *   `from collections import namedtuple`
    *   `from django.core.exceptions import FieldError`
    *   `from django.db import DEFAULT_DB_ALIAS, DatabaseError, connections`
    *   `from django.db.models.constants import LOOKUP_SEP`
    *   `from django.utils import tree`
    *   `from django.utils.functional import cached_property`
    *   `from django.utils.hashable import make_hashable`
*   **Constants & Globals:**
    *   `logger`: `logging.getLogger("django.db.models")`
    *   `PathInfo`: `namedtuple("PathInfo", "from_opts to_opts target_fields join_field m2m direct filtered_relation")`

**2. Code Objects (Classes and Functions)**

*   **`def subclasses(cls)`**
    *   **Signature:** `def subclasses(cls)`
    *   **Implementation Logic:** Yields `cls`. Then iterates over `cls.__subclasses__()` and yields from `subclasses(subclass)` recursively.

*   **`class Q(tree.Node)`**
    *   **Base Classes:** `tree.Node`
    *   **Attributes:**
        *   `AND`: `"AND"`
        *   `OR`: `"OR"`
        *   `XOR`: `"XOR"`
        *   `default`: `AND`
        *   `conditional`: `True`
    *   **`__init__(self, *args, _connector=None, _negated=False, **kwargs)`**
        *   Calls `super().__init__(children=[*args, *sorted(kwargs.items())], connector=_connector, negated=_negated)`.
    *   **`_combine(self, other, conn)`**
        *   If `getattr(other, "conditional", False)` is `False`, raises `TypeError(other)`.
        *   If `not self`, returns `other.copy()`.
        *   If `not other` and `isinstance(other, Q)`, returns `self.copy()`.
        *   Creates `obj = self.create(connector=conn)`.
        *   Calls `obj.add(self, conn)` and `obj.add(other, conn)`.
        *   Returns `obj`.
    *   **`__or__(self, other)`**
        *   Returns `self._combine(other, self.OR)`.
    *   **`__and__(self, other)`**
        *   Returns `self._combine(other, self.AND)`.
    *   **`__xor__(self, other)`**
        *   Returns `self._combine(other, self.XOR)`.
    *   **`__invert__(self)`**
        *   Creates `obj = self.copy()`, calls `obj.negate()`, and returns `obj`.
    *   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`**
        *   Calls `clause, joins = query._add_q(self, reuse, allow_joins=allow_joins, split_subq=False, check_filterable=False, summarize=summarize)`.
        *   Calls `query.promote_joins(joins)`.
        *   Returns `clause`.
    *   **`flatten(self)`**
        *   Yields `self`.
        *   Iterates over `self.children`. For each `child`:
            *   If `isinstance(child, tuple)`, sets `child = child[1]`.
            *   If `hasattr(child, "flatten")`, yields from `child.flatten()`.
            *   Else, yields `child`.
    *   **`check(self, against, using=DEFAULT_DB_ALIAS)`**
        *   Imports `BooleanField`, `Value` from `django.db.models`, `Coalesce` from `django.db.models.functions`, `Query` from `django.db.models.sql`, and `SINGLE` from `django.db.models.sql.constants`.
        *   Creates `query = Query(None)`.
        *   Iterates over `against.items()` as `name, value`:
            *   If `not hasattr(value, "resolve_expression")`, sets `value = Value(value)`.
            *   Calls `query.add_annotation(value, name, select=False)`.
        *   Calls `query.add_annotation(Value(1), "_check")`.
        *   If `connections[using].features.supports_comparing_boolean_expr` is true, calls `query.add_q(Q(Coalesce(self, True, output_field=BooleanField())))`.
        *   Else, calls `query.add_q(self)`.
        *   Gets `compiler = query.get_compiler(using=using)`.
        *   Tries to return `compiler.execute_sql(SINGLE) is not None`.
        *   Excepts `DatabaseError` as `e`, logs a warning using `logger.warning("Got a database error calling check() on %r: %s", self, e)`, and returns `True`.
    *   **`deconstruct(self)`**
        *   Sets `path = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)`.
        *   If `path.startswith("django.db.models.query_utils")`, replaces it with `"django.db.models"`.
        *   Sets `args = tuple(self.children)` and `kwargs = {}`.
        *   If `self.connector != self.default`, sets `kwargs["_connector"] = self.connector`.
        *   If `self.negated`, sets `kwargs["_negated"] = True`.
        *   Returns `path, args, kwargs`.
    *   **`identity(self)`** (Decorated with `@cached_property`)
        *   Calls `path, args, kwargs = self.deconstruct()`.
        *   Sets `identity = [path, *kwargs.items()]`.
        *   Iterates over `args` as `child`:
            *   If `isinstance(child, tuple)`, unpacks to `arg, value`, sets `value = make_hashable(value)`, and appends `(arg, value)` to `identity`.
            *   Else, appends `child` to `identity`.
        *   Returns `tuple(identity)`.
    *   **`__eq__(self, other)`**
        *   If `not isinstance(other, Q)`, returns `NotImplemented`.
        *   Returns `other.identity == self.identity`.
    *   **`__hash__(self)`**
        *   Returns `hash(self.identity)`.

*   **`class DeferredAttribute`**
    *   **`__init__(self, field)`**
        *   Sets `self.field = field`.
    *   **`__get__(self, instance, cls=None)`**
        *   If `instance is None`, returns `self`.
        *   Sets `data = instance.__dict__` and `field_name = self.field.attname`.
        *   If `field_name not in data`:
            *   Sets `val = self._check_parent_chain(instance)`.
            *   If `val is None`:
                *   If `instance.pk is None` and `self.field.generated`, raises `AttributeError("Cannot read a generated field from an unsaved model.")`.
                *   Calls `instance.refresh_from_db(fields=[field_name])`.
            *   Else, sets `data[field_name] = val`.
        *   Returns `data[field_name]`.
    *   **`_check_parent_chain(self, instance)`**
        *   Sets `opts = instance._meta` and `link_field = opts.get_ancestor_link(self.field.model)`.
        *   If `self.field.primary_key` and `self.field != link_field`, returns `getattr(instance, link_field.attname)`.
        *   Returns `None`.

*   **`class class_or_instance_method`**
    *   **`__init__(self, class_method, instance_method)`**
        *   Sets `self.class_method = class_method` and `self.instance_method = instance_method`.
    *   **`__get__(self, instance, owner)`**
        *   If `instance is None`, returns `functools.partial(self.class_method, owner)`.
        *   Returns `functools.partial(self.instance_method, instance)`.

*   **`class RegisterLookupMixin`**
    *   **`_get_lookup(self, lookup_name)`**
        *   Returns `self.get_lookups().get(lookup_name, None)`.
    *   **`get_class_lookups(cls)`** (Decorated with `@functools.cache` and `classmethod` via assignment)
        *   Sets `class_lookups = [parent.__dict__.get("class_lookups", {}) for parent in inspect.getmro(cls)]`.
        *   Returns `cls.merge_dicts(class_lookups)`.
    *   **`get_instance_lookups(self)`**
        *   Sets `class_lookups = self.get_class_lookups()`.
        *   If `instance_lookups := getattr(self, "instance_lookups", None)` is truthy, returns `{**class_lookups, **instance_lookups}`.
        *   Returns `class_lookups`.
    *   **`get_lookups`**: Assigned `class_or_instance_method(get_class_lookups, get_instance_lookups)`.
    *   **`get_class_lookups`**: Assigned `classmethod(get_class_lookups)`.
    *   **`get_lookup(self, lookup_name)`**
        *   Imports `Lookup` from `django.db.models.lookups`.
        *   Sets `found = self._get_lookup(lookup_name)`.
        *   If `found is None` and `hasattr(self, "output_field")`, returns `self.output_field.get_lookup(lookup_name)`.
        *   If `found is not None` and `not issubclass(found, Lookup)`, returns `None`.
        *   Returns `found`.
    *   **`get_transform(self, lookup_name)`**
        *   Imports `Transform` from `django.db.models.lookups`.
        *   Sets `found = self._get_lookup(lookup_name)`.
        *   If `found is None` and `hasattr(self, "output_field")`, returns `self.output_field.get_transform(lookup_name)`.
        *   If `found is not None` and `not issubclass(found, Transform)`, returns `None`.
        *   Returns `found`.
    *   **`merge_dicts(dicts)`** (Decorated with `@staticmethod`)
        *   Sets `merged = {}`.
        *   Iterates over `reversed(dicts)` as `d`, calls `merged.update(d)`.
        *   Returns `merged`.
    *   **`_clear_cached_class_lookups(cls)`** (Decorated with `@classmethod`)
        *   Iterates over `subclasses(cls)` as `subclass`, calls `subclass.get_class_lookups.cache_clear()`.
    *   **`register_class_lookup(cls, lookup, lookup_name=None)`** (Decorated with `classmethod` via assignment)
        *   If `lookup_name is None`, sets `lookup_name = lookup.lookup_name`.
        *   If `"class_lookups" not in cls.__dict__`, sets `cls.class_lookups = {}`.
        *   Sets `cls.class_lookups[lookup_name] = lookup`.
        *   Calls `cls._clear_cached_class_lookups()`.
        *   Returns `lookup`.
    *   **`register_instance_lookup(self, lookup, lookup_name=None)`**
        *   If `lookup_name is None`, sets `lookup_name = lookup.lookup_name`.
        *   If `"instance_lookups" not in self.__dict__`, sets `self.instance_lookups = {}`.
        *   Sets `self.instance_lookups[lookup_name] = lookup`.
        *   Returns `lookup`.
    *   **`register_lookup`**: Assigned `class_or_instance_method(register_class_lookup, register_instance_lookup)`.
    *   **`register_class_lookup`**: Assigned `classmethod(register_class_lookup)`.
    *   **`_unregister_class_lookup(cls, lookup, lookup_name=None)`** (Decorated with `classmethod` via assignment)
        *   If `lookup_name is None`, sets `lookup_name = lookup.lookup_name`.
        *   Deletes `cls.class_lookups[lookup_name]`.
        *   Calls `cls._clear_cached_class_lookups()`.
    *   **`_unregister_instance_lookup(self, lookup, lookup_name=None)`**
        *   If `lookup_name is None`, sets `lookup_name = lookup.lookup_name`.
        *   Deletes `self.instance_lookups[lookup_name]`.
    *   **`_unregister_lookup`**: Assigned `class_or_instance_method(_unregister_class_lookup, _unregister_instance_lookup)`.
    *   **`_unregister_class_lookup`**: Assigned `classmethod(_unregister_class_lookup)`.

*   **`def select_related_descend(field, restricted, requested, select_mask, reverse=False)`**
    *   **Signature:** `def select_related_descend(field, restricted, requested, select_mask, reverse=False)`
    *   **Implementation Logic:**
        *   If `not field.remote_field`, returns `False`.
        *   If `field.remote_field.parent_link` and `not reverse`, returns `False`.
        *   If `restricted`:
            *   If `reverse` and `field.related_query_name() not in requested`, returns `False`.
            *   If `not reverse` and `field.name not in requested`, returns `False`.
        *   If `not restricted` and `field.null`, returns `False`.
        *   If `restricted` and `select_mask` and `field.name in requested` and `field not in select_mask`, raises `FieldError(f"Field {field.model._meta.object_name}.{field.name} cannot be both deferred and traversed using select_related at the same time.")`.
        *   Returns `True`.

*   **`def refs_expression(lookup_parts, annotations)`**
    *   **Signature:** `def refs_expression(lookup_parts, annotations)`
    *   **Implementation Logic:**
        *   Iterates `n` from `1` to `len(lookup_parts) + 1`:
            *   Sets `level_n_lookup = LOOKUP_SEP.join(lookup_parts[0:n])`.
            *   If `annotations.get(level_n_lookup)` is truthy, returns `level_n_lookup, lookup_parts[n:]`.
        *   Returns `None, ()`.

*   **`def check_rel_lookup_compatibility(model, target_opts, field)`**
    *   **Signature:** `def check_rel_lookup_compatibility(model, target_opts, field)`
    *   **Implementation Logic:**
        *   Defines inner function `check(opts)` which returns `model._meta.concrete_model == opts.concrete_model or opts.concrete_model in model._meta.all_parents or model in opts.all_parents`.
        *   Returns `check(target_opts) or (getattr(field, "primary_key", False) and check(field.model._meta))`.

*   **`class FilteredRelation`**
    *   **`__init__(self, relation_name, *, condition=Q())`**
        *   If `not relation_name`, raises `ValueError("relation_name cannot be empty.")`.
        *   Sets `self.relation_name = relation_name` and `self.alias = None`.
        *   If `not isinstance(condition, Q)`, raises `ValueError("condition argument must be a Q() instance.")`.
        *   Sets `self.condition = condition` and `self.resolved_condition = None`.
    *   **`__eq__(self, other)`**
        *   If `not isinstance(other, self.__class__)`, returns `NotImplemented`.
        *   Returns `self.relation_name == other.relation_name and self.alias == other.alias and self.condition == other.condition`.
    *   **`clone(self)`**
        *   Sets `clone = FilteredRelation(self.relation_name, condition=self.condition)`.
        *   Sets `clone.alias = self.alias`.
        *   If `(resolved_condition := self.resolved_condition) is not None`, sets `clone.resolved_condition = resolved_condition.clone()`.
        *   Returns `clone`.
    *   **`relabeled_clone(self, change_map)`**
        *   Sets `clone = self.clone()`.
        *   If `resolved_condition := clone.resolved_condition` is truthy, sets `clone.resolved_condition = resolved_condition.relabeled_clone(change_map)`.
        *   Returns `clone`.
    *   **`resolve_expression(self, query, reuse, *args, **kwargs)`**
        *   Sets `clone = self.clone()`.
        *   Sets `clone.resolved_condition = query.build_filter(self.condition, can_reuse=reuse, allow_joins=True, split_subq=False, update_join_types=False)[0]`.
        *   Returns `clone`.
    *   **`as_sql(self, compiler, connection)`**
        *   Returns `compiler.compile(self.resolved_condition)`.

## django/db/models/sql/compiler.py
```markdown
# Specification for `django/db/models/sql/compiler.py`

## 1. Module-Level Preamble

### Imports
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
    CURSOR, GET_ITERATOR_CHUNK_SIZE, MULTI, NO_RESULTS, ORDER_DIR, SINGLE
)
from django.db.models.sql.query import Query, get_order_dir
from django.db.models.sql.where import AND
from django.db.transaction import TransactionManagementError
from django.utils.functional import cached_property
from django.utils.hashable import make_hashable
from django.utils.regex_helper import _lazy_re_compile
```

### Constants & Globals
There are no module-level constants or globals defined outside of the classes.

## 2. Code Objects (Classes and Functions)

### `PositionRef(Ref)`
A subclass of `Ref` used to reference a column by its ordinal position in the `SELECT` clause.

*   **`__init__(self, ordinal, refs, source)`**
    *   Initializes the `PositionRef` with an `ordinal` (integer), `refs` (string name), and `source` (expression).
*   **`as_sql(self, compiler, connection)`**
    *   Returns the string representation of the `ordinal` and an empty tuple for parameters.

### `SQLCompiler`
The base class for compiling Django `Query` objects into SQL strings.

*   **Attributes:**
    *   `ordering_parts`: A compiled regular expression `_lazy_re_compile('^(.*)\\s(?:ASC|DESC).*', re.MULTILINE | re.DOTALL)` used to strip ordering directions from SQL clauses.
*   **`__init__(self, query, connection, using, elide_empty=True)`**
    *   Initializes the compiler with the `query`, `connection`, `using` (database alias), and `elide_empty` flag. Sets up internal state variables like `select`, `annotation_col_map`, `klass_info`, and `ordering_parts`.
*   **`setup_query(self, with_col_aliases=False)`**
    *   Prepares the query for compilation by resolving select columns, group by, and order by clauses.
*   **`pre_sql_setup(self, with_col_aliases=False)`**
    *   Calls `setup_query` and handles additional setup like extra selects and annotations.
*   **`get_group_by(self, select, order_by)`**
    *   Returns a list of 2-tuples `(sql, params)` representing the `GROUP BY` clause based on the `select` and `order_by` expressions.
*   **`collapse_group_by(self, expressions, having)`**
    *   Optimizes the `GROUP BY` clause by removing redundant expressions (e.g., if a primary key is included, other fields from the same table can be omitted).
*   **`get_select(self, with_col_aliases=False)`**
    *   Returns a tuple of `(select, klass_info, annotations)`. `select` is a list of `(sql, params)` for the `SELECT` clause.
*   **`get_order_by(self)`**
    *   Returns a list of `(sql, params)` for the `ORDER BY` clause.
*   **`get_extra_select(self, order_by, select)`**
    *   Returns extra select columns needed for ordering.
*   **`quote_name_unless_alias(self, name)`**
    *   Quotes a name unless it is a known alias.
*   **`compile(self, node)`**
    *   Compiles an AST node into SQL by calling its `as_sql` method.
*   **`get_combinator_sql(self, combinator, all)`**
    *   Returns the SQL for combinators like `UNION`, `INTERSECT`, or `EXCEPT`.
*   **`as_sql(self, with_limits=True, with_col_aliases=False)`**
    *   The main method that constructs the full `SELECT` SQL query string and parameters.
*   **`get_default_columns(self, select_mask, start_alias=None, opts=None, from_parent=None)`**
    *   Computes the default columns to select for a given model.
*   **`get_distinct(self)`**
    *   Returns the SQL and parameters for the `DISTINCT` clause.
*   **`get_from_clause(self)`**
    *   Returns a list of strings and parameters for the `FROM` clause, including `JOIN`s.
*   **`get_related_selections(self, select, select_mask, opts=None, root_alias=None, cur_depth=1, requested=None, restricted=None)`**
    *   Recursively adds related fields to the `SELECT` clause for `select_related`.
*   **`get_converters(self, expressions)`**
    *   Returns a list of converter functions for the selected expressions.
*   **`apply_converters(self, rows, converters)`**
    *   Applies the converter functions to the raw database rows.
*   **`results_iter(self, results=None, tuple_expected=False, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE)`**
    *   Returns an iterator over the results, applying converters and resolving related objects.
*   **`execute_sql(self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE)`**
    *   Executes the compiled SQL query and returns the results based on `result_type`.

### `SQLInsertCompiler(SQLCompiler)`
Compiles `INSERT` queries.

*   **Attributes:**
    *   `returning_fields = None`
    *   `returning_params = ()`
*   **`assemble_as_sql(self, fields, value_rows)`**
    *   Constructs the `INSERT` SQL string and parameters for multiple rows.
*   **`as_sql(self)`**
    *   Returns a list of `(sql, params)` tuples for the `INSERT` query.
*   **`execute_sql(self, returning_fields=None)`**
    *   Executes the `INSERT` query and returns the inserted primary keys or returning fields.

### `SQLDeleteCompiler(SQLCompiler)`
Compiles `DELETE` queries.

*   **`as_sql(self)`**
    *   Constructs the `DELETE` SQL string and parameters. Handles self-referential subqueries if necessary.

### `SQLUpdateCompiler(SQLCompiler)`
Compiles `UPDATE` queries.

*   **`as_sql(self)`**
    *   Constructs the `UPDATE` SQL string and parameters.
*   **`execute_sql(self, result_type)`**
    *   Executes the `UPDATE` query and returns the number of affected rows.

### `SQLAggregateCompiler(SQLCompiler)`
Compiles aggregate queries (e.g., `COUNT`, `MAX`).

*   **`as_sql(self)`**
    *   Constructs the SQL string and parameters for the aggregate query, typically wrapping the base query in a subquery.

### `cursor_iter(cursor, sentinel, col_count, itersize)`
*   **Signature:** `cursor_iter(cursor, sentinel, col_count, itersize)`
*   **Implementation Logic:** Yields rows from a database cursor in chunks of `itersize` until the `sentinel` is reached or the cursor is exhausted. Closes the cursor when done.
```

## django/db/models/sql/query.py
This is a natural-language specification of the `django/db/models/sql/query.py` file.

## 1. Module-Level Preamble

### Imports
```python
import copy
import difflib
import functools
import sys
from collections import Counter, namedtuple
from collections.abc import Iterator, Mapping
from itertools import chain, count, product
from string import ascii_uppercase

from django.core.exceptions import FieldDoesNotExist, FieldError
from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections
from django.db.models.aggregates import Count
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import (
    BaseExpression, Col, Exists, F, OuterRef, Ref, ResolvedOuterRef, Value,
)
from django.db.models.fields import Field
from django.db.models.fields.related_lookups import MultiColSource
from django.db.models.lookups import Lookup
from django.db.models.query_utils import Q, check_rel_lookup_compatibility, refs_expression
from django.db.models.sql.constants import INNER, LOUTER, ORDER_DIR, SINGLE
from django.db.models.sql.datastructures import BaseTable, Empty, Join, MultiJoin
from django.db.models.sql.where import AND, OR, ExtraWhere, NothingNode, WhereNode
from django.utils.functional import cached_property
from django.utils.regex_helper import _lazy_re_compile
from django.utils.tree import Node
```

### Constants & Globals
*   `__all__ = ["Query", "RawQuery"]`
*   `FORBIDDEN_ALIAS_PATTERN = _lazy_re_compile(r"['`\"\]\[;\s]|--|/\*|\*/")`
*   `EXPLAIN_OPTIONS_PATTERN = _lazy_re_compile(r"[\w-]+")`
*   `JoinInfo = namedtuple("JoinInfo", ("final_field", "targets", "opts", "joins", "path", "transform_function"))`
*   `ExplainInfo = namedtuple("ExplainInfo", ("format", "options"))`

## 2. Code Objects (Classes and Functions)

### `get_field_names_from_opts(opts)`
*   **Signature:** `def get_field_names_from_opts(opts):`
*   **Logic:** Returns an empty set if `opts` is `None`. Otherwise, returns a set of field names and attnames (if concrete) from `opts.get_fields()`.

### `get_paths_from_expression(expr)`
*   **Signature:** `def get_paths_from_expression(expr):`
*   **Logic:** A generator that yields field names from an expression. If `expr` is an `F` object, yields its `name`. If it has a `flatten` method, iterates over its children, yielding `name` for `F` objects and delegating to `get_children_from_q` for `Q` objects.

### `get_children_from_q(q)`
*   **Signature:** `def get_children_from_q(q):`
*   **Logic:** A generator that yields paths from a `Q` object's children. Recursively yields from `Node` children. For tuple children `(lhs, rhs)`, yields `lhs` and delegates `rhs` to `get_paths_from_expression` if it has `resolve_expression`. For other children with `resolve_expression`, delegates to `get_paths_from_expression`.

### `get_child_with_renamed_prefix(prefix, replacement, child)`
*   **Signature:** `def get_child_with_renamed_prefix(prefix, replacement, child):`
*   **Logic:** Renames a prefix in a child expression. If `child` is a `Node`, delegates to `rename_prefix_from_q`. If a tuple `(lhs, rhs)`, replaces `prefix` with `replacement` in `lhs` (if it starts with `prefix + LOOKUP_SEP`) and recursively processes `rhs`. If an `F` object, copies it and replaces the prefix in its name. If a `QuerySet`, raises `ValueError`. Otherwise, if it has `resolve_expression`, copies it and recursively processes its source expressions.

### `rename_prefix_from_q(prefix, replacement, q)`
*   **Signature:** `def rename_prefix_from_q(prefix, replacement, q):`
*   **Logic:** Returns a new `Q` object created by applying `get_child_with_renamed_prefix` to all children of `q`, preserving its connector and negated state.

### `RawQuery`
*   **Header:** `class RawQuery:`
*   **Implementation Logic:** Represents a raw SQL query.
    *   `__init__(self, sql, using, params=())`: Initializes `sql`, `using`, `params`, `cursor` (None), `low_mark` (0), `high_mark` (None), `extra_select` ({}), and `annotation_select` ({}).
    *   `chain(self, using)`: Returns `self.clone(using)`.
    *   `clone(self, using)`: Returns a new `RawQuery` with the same `sql`, `using`, and `params`.
    *   `get_columns(self)`: Executes the query if `cursor` is None, then returns the column names from `cursor.description` converted by the connection's identifier converter.
    *   `__iter__(self)`: Executes the query. If the database doesn't support chunked reads, evaluates the entire cursor into a list. Returns an iterator over the result.
    *   `__repr__(self)`: Returns a string representation.
    *   `params_type(self)` (property): Returns `dict` if `params` is a mapping, `tuple` if not None, else `None`.
    *   `__str__(self)`: Returns the SQL string, substituting parameters if present.
    *   `_execute_query(self)`: Adapts parameters using the connection's `adapt_unknown_value`, creates a cursor, and executes the SQL.

### `Query`
*   **Header:** `class Query(BaseExpression):`
*   **Implementation Logic:** Represents a single SQL query. Handles SQL construction, joins, aliases, and filtering.
    *   **Attributes:** Defines numerous class-level attributes for SQL clauses (e.g., `select`, `group_by`, `order_by`, `where`, `annotations`, `extra`, `alias_map`, `alias_refcount`).
    *   `__init__(self, model, alias_cols=True)`: Initializes instance attributes.
    *   `output_field(self)` (property): Returns the output field if there's exactly one select or annotation.
    *   `base_table(self)` (cached_property): Returns the first alias in `alias_map`.
    *   `sql_with_params(self)`: Returns the SQL string and parameters using the compiler for `DEFAULT_DB_ALIAS`.
    *   `clone(self)`: Returns a lightweight copy of the query, deepcopying necessary structures like `alias_map` and `where`.
    *   `get_aggregation(self, using, aggregate_exprs)`: Resolves and computes aggregations. Uses a subquery if the query has limits, distinct, grouping, or set operations.
    *   `get_count(self, using)`: Performs a `COUNT(*)` aggregation.
    *   `exists(self, limit=True)`: Modifies the query to check for existence (clears select, adds `Value(1)`, sets limit to 1).
    *   `combine(self, rhs, connector)`: Merges `rhs` into `self` using `connector` (AND/OR). Relabels aliases to avoid conflicts and promotes joins appropriately.
    *   `table_alias(self, table_name, create=False, filtered_relation=None)`: Returns an alias for a table, creating a new one if `create` is True or reusing an existing one.
    *   `promote_joins(self, aliases)` / `demote_joins(self, aliases)`: Adjusts join types (INNER/LOUTER) for the given aliases and their children to maintain correct semantics.
    *   `change_aliases(self, change_map)`: Updates aliases in the query based on `change_map`.
    *   `bump_prefix(self, other_query, exclude=None)`: Changes the alias prefix to avoid conflicts with `other_query`.
    *   `join(self, join, reuse=None)`: Adds a join to the query, reusing an existing alias if possible, and returns the alias.
    *   `setup_joins(self, names, opts, alias, can_reuse=None, allow_many=True)`: Computes necessary table joins for a field path (`names`). Returns a `JoinInfo` namedtuple.
    *   `trim_joins(self, targets, joins, path)`: Trims unnecessary direct joins from the end of a join chain.
    *   `resolve_ref(self, name, allow_joins=True, reuse=None, summarize=False)`: Resolves a reference name to an annotation or a field transform.
    *   `split_exclude(self, filter_expr, can_reuse, names_with_path)`: Constructs a nested `EXISTS` subquery for excluding against N-to-many relations.
    *   `build_filter(self, filter_expr, ...)`: Builds a `WhereNode` for a single filter clause. Handles `Q` objects, conditional expressions, and standard lookups.
    *   `add_q(self, q_object)`: Adds a `Q` object to the query's `where` clause and performs final join promotion/demotion.
    *   `set_limits(self, low=None, high=None)`: Adjusts the offset and limit of the query.
    *   `add_fields(self, field_names, allow_m2m=True)`: Adds model fields to the select set.
    *   `add_ordering(self, *ordering)`: Adds items to the `order_by` clause.
    *   `set_group_by(self, allow_aliases=True)`: Expands the `GROUP BY` clause based on selected fields and annotations.

### `get_order_dir(field, default="ASC")`
*   **Signature:** `def get_order_dir(field, default="ASC"):`
*   **Logic:** Returns a tuple `(field_name, direction)` for an order specification (e.g., `'-foo'` -> `('foo', 'DESC')`).

### `JoinPromoter`
*   **Header:** `class JoinPromoter:`
*   **Implementation Logic:** Abstracts join promotion logic for complex filter conditions (AND/OR).
    *   `__init__(self, connector, num_children, negated)`: Initializes the promoter with the connector, number of children, and negation state. Calculates the `effective_connector`.
    *   `add_votes(self, votes)`: Adds votes for tables that require INNER joins.
    *   `update_join_types(self, query)`: Determines which joins should be promoted to LOUTER or demoted to INNER based on the votes and effective connector, and applies these changes to the `query`. Returns the set of demoted aliases.