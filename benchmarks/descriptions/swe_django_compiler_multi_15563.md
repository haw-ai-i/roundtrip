## django/db/models/sql/compiler.py
I've now read all 1899 lines of the file. Here is the complete natural-language specification:

---

# Module Specification: `django/db/models/sql/compiler.py`

## 1. Module-Level Preamble

### Imports

```python
import collections
import json
import re
from functools import partial
from itertools import chain

from django.core.exceptions import EmptyResultSet, FieldError
from django.db import DatabaseError, NotSupportedError
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import F, OrderBy, RawSQL, Ref, Value
from django.db.models.functions import Cast, Random
from django.db.models.query_utils import select_related_descend

from django.db.models.sql.constants import (
    CURSOR,
    GET_ITERATOR_CHUNK_SIZE,
    MULTI,
    NO_RESULTS,
    ORDER_DIR,
    SINGLE,
)
from django.db.models.sql.query import Query, get_order_dir
from django.db.transaction import TransactionManagementError
from django.utils.functional import cached_property
from django.utils.hashable import make_hashable
from django.utils.regex_helper import _lazy_re_compile
```

### Constants & Globals

- **`ordering_parts`**: A compiled regex (`_lazy_re_compile`) matching `r"^(.*)\s(?:ASC|DESC).*"` with flags `re.MULTILINE | re.DOTALL`. Used to strip ordering direction from SQL strings.

---

## 2. Code Objects

### Class: `SQLCompiler`

**Inheritance:** None (base class)

#### Attributes (initialized in `__init__`)

- `query`: A `Query` object — the query being compiled.
- `connection`: The database connection object.
- `using`: Database alias string.
- `elide_empty`: Boolean; if `True`, queries that would return empty result sets are elided (not executed).
- `quote_cache`: Dict, initialized to `{"*": "*"}` — caches quoted names for table/column aliases.
- `select`: Initially `None`; set by `get_select()` as a list of 3-tuples `(expression, (sql, params), alias)`.
- `annotation_col_map`: Initially `None`; set by `get_select()` as a dict mapping annotation names to column positions.
- `klass_info`: Initially `None`; set by `get_select()`, describing model/related-model selection info.
- `_meta_ordering`: Initially `None`; tracks whether ordering came from the model's Meta class.
- `col_count`: Integer; length of `self.select` after setup.

#### Methods

##### `__repr__(self)` → `str`

Returns a formatted string: `<{ClassName} model={model.__qualname__} connection={connection!r} using={using!r}>`.

##### `setup_query(self)`

If all entries in `self.query.alias_refcount` are zero, calls `self.query.get_initial_alias()`. Then calls `self.get_select()` and assigns its three return values to `self.select`, `self.klass_info`, `self.annotation_col_map`. Sets `self.col_count = len(self.select)`.

##### `pre_sql_setup(self)` → `(extra_select, order_by, group_by)`

Calls `setup_query()`. Calls `get_order_by()` and assigns result to `order_by`. Calls `self.query.where.split_having()` and assigns results to `self.where` and `self.having`. Calls `get_extra_select(order_by, self.select)`, sets `self.has_extra_select = bool(extra_select)`. Calls `get_group_by(self.select + extra_select, order_by)` and assigns result to `group_by`. Returns `(extra_select, order_by, group_by)`.

##### `get_group_by(self, select, order_by)` → `list[tuple[str, tuple]]`

Returns a deduplicated list of 2-tuples `(sql, params)` for the GROUP BY clause.

- If `self.query.group_by is None`, returns `[]`.
- Otherwise builds an `expressions` list:
  - If `self.query.group_by` is not `True` (i.e., it's a list), iterates over each element; if it lacks `as_sql`, resolves via `self.query.resolve_ref(expr)`, else appends directly.
  - Iterates over `select`: for each expression, skips those in `ref_sources` (expressions whose source is a `Ref`). Otherwise calls `expr.get_group_by_cols()` and extends `expressions`.
  - If not `self._meta_ordering`, iterates over `order_by`; for non-ref entries, extends with `expr.get_group_by_cols()`.
  - Extends with `self.having.get_group_by_cols()` if `self.having` is set.
- Calls `collapse_group_by(expressions, having)` to potentially simplify the GROUP BY.
- Iterates over expressions: compiles each via `self.compile(expr)`, formats via `expr.select_format(self, sql, params)`. Deduplicates by `(sql, make_hashable(params))` and returns unique tuples.

##### `collapse_group_by(self, expressions, having)` → `list`

Optimizes GROUP BY based on database features:

- If `self.connection.features.allows_group_by_pk`:
  - Searches for an expression whose `target == self.query.model._meta.pk` and `alias == self.query.base_table`.
  - If found (`pk`), collects aliases of all expressions with a primary-key target into `pk_aliases`. Returns `[pk] + [expr for expr in expressions if expr is in having or (has alias and alias not in pk_aliases)]`.
- Else if `self.connection.features.allows_group_by_selected_pks`:
  - Collects PK expressions from models that support this feature (excluding unmanaged models).
  - Returns only those PK expressions plus non-PK expressions whose alias is not among the PK aliases.
- Otherwise returns `expressions` unchanged.

##### `get_select(self)` → `(ret, klass_info, annotations)`

Returns three values: a list of 3-tuples `(expression, (sql, params), alias)`, a `klass_info` dict, and an `annotations` dict.

- Initializes `select = []`, `klass_info = None`, `annotations = {}`, `select_idx = 0`.
- Iterates over `self.query.extra_select.items()`: for each `(alias, (sql, params))`, sets `annotations[alias] = select_idx`, appends `(RawSQL(sql, params), alias)` to `select`, increments `select_idx`.
- Asserts not both `self.query.select` and `self.query.default_cols`. If `self.query.default_cols`, calls `get_default_columns()`; else uses `self.query.select`. For each column in `cols`: appends `select_idx` to `select_list`, appends `(col, None)` to `select`, increments `select_idx`. Sets `klass_info = {"model": self.query.model, "select_fields": select_list}`.
- Iterates over `self.query.annotation_select.items()`: sets `annotations[alias] = select_idx`, appends `(annotation, alias)` to `select`, increments `select_idx`.
- If `self.query.select_related` is truthy: calls `get_related_selections(select)`, assigns result to `klass_info["related_klass_infos"]`. Defines and runs nested function `get_select_from_parent(klass_info)` that propagates parent select fields to children where `from_parent` is True.
- For each `(col, alias)` in `select`: tries `self.compile(col)`. On `EmptyResultSet`, checks `col.empty_result_set_value`; if `NotImplemented`, uses `"0", ()`; else compiles `Value(empty_result_set_value)`. Otherwise formats via `col.select_format(self, sql, params)`. Appends `(col, (sql, params), alias)` to `ret`.
- Returns `(ret, klass_info, annotations)`.

##### `_order_by_pairs(self)` → generator of `(expr, is_ref)`

Yields `(OrderBy expression, False/True)` tuples for ORDER BY:

- Determines ordering source: if `self.query.extra_order_by` exists, uses it; else if not `self.query.default_ordering`, uses `self.query.order_by`; else if `self.query.order_by` is set, uses it; else if model Meta has ordering, uses that (and sets `self._meta_ordering = True`); else empty list.
- Determines default direction from `ORDER_DIR["ASC"]` or `ORDER_DIR["DESC"]` based on `self.query.standard_ordering`.
- For each field in ordering:
  - If it has `resolve_expression`: if `Value`, casts via `Cast(field, field.output_field)`. If not already `OrderBy`, calls `.asc()`. If not standard ordering, copies and reverses. Yields `(field, False)`. Continues.
  - If field is `"?"`: yields `(OrderBy(Random()), False)`.
  - Otherwise: splits on `LOOKUP_SEP` to get `col, order`; determines `descending = (order == "DESC")`.
    - If `col in self.query.annotation_select`: yields `(OrderBy(Ref(col, annotation), descending=descending), True)`.
    - If `"." in col`: splits into table/col, yields `(OrderBy(RawSQL("%s.%s" % (quoted_table, col)), []), False)`.
    - If `self.query.extra` and `col in self.query.extra_select`: yields `(OrderBy(Ref(col, RawSQL(*extra[col])), True), True)`.
    - Else if `col in self.query.extra`: yields `(OrderBy(RawSQL(*extra[col]), False), False)`.
    - Else: if combinator with existing select and col is an F expression matching alias, yields `(OrderBy(F(col), descending=descending), False)`; else calls `find_ordering_name(field, opts, default_order)` which yields more pairs.

##### `get_order_by(self)` → `list[tuple[ResolvedExpr, tuple[str, tuple, bool]]]`

Returns a deduplicated list of 2-tuples `(resolved_expr, (sql, params, is_ref))`.

- Initializes empty `result`, `seen = set()`.
- For each `(expr, is_ref)` from `_order_by_pairs()`: resolves via `expr.resolve_expression(self.query, allow_joins=True, reuse=None)`.
  - If combinator with existing select: finds matching source in self.select; if match found by alias or column name, replaces source expression with `RawSQL("%d" % (idx+1), ())`; else raises `DatabaseError` if no alias match. Otherwise adds a new annotation column to all combined queries and the main query, sets resolved source to `RawSQL(f"{order_by_idx}", ())`.
- Compiles resolved expr: strips ordering direction via `ordering_parts.search(sql)[1]`, deduplicates by `(without_ordering, make_hashable(params))`. Appends unique entries to result. Returns result.

##### `get_extra_select(self, order_by, select)` → `list`

Returns extra select columns needed for grammatical correctness when `self.query.distinct` is True and not using `distinct_fields`. For each non-ref order-by expression whose SQL (stripped of direction) is not already in the select clause, appends `(expr, (sql, params), None)` to result. Returns result.

##### `quote_name_unless_alias(self, name)` → `str`

Returns a quoted table name unless it's an alias. Checks `self.quote_cache` first. If name is in `alias_map` but not `table_map`, or in `extra_select`, or in `external_aliases` and not in `table_map`, returns unquoted. Otherwise calls `connection.ops.quote_name(name)` and caches.

##### `compile(self, node)` → `(str, tuple)`

Tries to find a vendor-specific implementation: `getattr(node, "as_" + self.connection.vendor, None)`. If found, calls it with `(self, connection)`. Else calls `node.as_sql(self, connection)`. Returns `(sql, params)`.

##### `get_combinator_sql(self, combinator, all)` → `(str, tuple)`

Generates SQL for UNION/DIFFERENCE/INTERSECT compound queries.

- Creates compilers for each non-empty combined query via `query.get_compiler(...)`.
- If backend doesn't support slicing/ordering in compounds, checks that no subquery has LIMIT/OFFSET or ORDER BY; raises `DatabaseError` if so.
- For each compiler: if the main query has `values_select` but this one doesn't, clones and sets values on it. Calls `compiler.as_sql()`. If the compiler's query is itself a combinator: wraps in subquery if parentheses not supported; adds parentheses if needed.
- On `EmptyResultSet`: skips for UNION or DIFFERENCE (if parts already exist); re-raises otherwise.
- If no parts remain, raises `EmptyResultSet`.
- Builds combined SQL using `connection.ops.set_operators[combinator]`, appending `" ALL"` if `all` and combinator is "union". Wraps in braces `{}` or `({})` based on subquery status and feature support. Returns `(result, params)`.

##### `as_sql(self, with_limits=True, with_col_aliases=False)` → `(str, tuple)`

Creates the full SQL string for this query.

- Saves `refcounts_before = self.query.alias_refcount.copy()`.
- Calls `pre_sql_setup()` to get `extra_select`, `order_by`, `group_by`.
- Determines `with_limit_offset` from `self.query.high_mark`/`low_mark`.
- If `combinator` is set: checks feature support, calls `get_combinator_sql(combinator, all)`. Otherwise:
  - Calls `get_distinct()` for DISTINCT fields.
  - Calls `get_from_clause()`.
  - Compiles `self.where` (or uses `"0 = 1"` if elide_empty is False and EmptyResultSet).
  - Compiles `self.having`.
  - Builds result list starting with `"SELECT"`.
  - If distinct: calls `connection.ops.distinct_sql(distinct_fields, distinct_params)`.
  - For each select column (including extra_select): adds AS alias if present, or auto-alias (`col%d`) if `with_col_aliases`. Collects SQL fragments and params.
  - Appends joined select columns, FROM clause.
  - If subquery with extra_select: builds a wrapping subquery selecting only the needed columns from an inner SELECT of the full result.
  - Adds WHERE, GROUP BY (raises `NotImplementedError` if both distinct_fields and group_by), HAVING clauses.
  - If `explain_info`: prepends explain query prefix.
  - Appends ORDER BY clause.
  - Appends LIMIT/OFFSET via `connection.ops.limit_offset_sql(low_mark, high_mark)`.
  - Handles `select_for_update`: checks autocommit, feature support for NOWAIT/SKIP LOCKED/OF/NO KEY UPDATE; calls `get_select_for_update_of_arguments()` and `connection.ops.for_update_sql()`. Appends FOR UPDATE part at the correct position (after FROM or before depending on `for_update_after_from` feature).
- Returns `" ".join(result), tuple(params)`.
- In `finally`: resets refcounts via `self.query.reset_refcounts(refcounts_before)`.

##### `get_default_columns(self, start_alias=None, opts=None, from_parent=None)` → `list[Column]`

Returns a list of Column expressions for every field in the base model.

- If `opts is None`, gets it from `self.query.get_meta()`; returns `[]` if None.
- Calls `deferred_to_columns()` to get `only_load`.
- Starts at `start_alias or self.query.get_initial_alias()`. Builds `seen_models = {None: start_alias}`.
- For each concrete field in `opts.concrete_fields`: determines the model; skips if it's a parent already loaded via `from_parent`; skips if deferred. Calls `query.join_parent_model(opts, model, start_alias, seen_models)` to get alias. Creates column via `field.get_col(alias)`. Appends to result. Returns result.

##### `get_distinct(self)` → `(list[str], list)`

Returns quoted field names for DISTINCT ON.

- Iterates over `self.query.distinct_fields`: splits on `LOOKUP_SEP`, calls `_setup_joins()`, trims joins via `query.trim_joins()`. For each target: if in annotation_select, appends the quoted name; else compiles the transformed column and appends SQL/params. Returns `(result, params)`.

##### `find_ordering_name(self, name, opts, alias=None, default_order="ASC", already_seen=None)` → `list[tuple[OrderBy, bool]]`

Resolves a field path (e.g., `"field1__field2"`) to ORDER BY expressions.

- Splits name into direction and pieces via `get_order_dir()`.
- Calls `_setup_joins(pieces, opts, alias)`.
- If the resolved field is a relation with model ordering: checks for infinite loops via `already_seen` set of join tuples; if loop detected, raises `FieldError("Infinite loop caused by ordering.")`. Otherwise iterates over `opts.ordering`, resolving each item similarly and extending results.
- Trims joins via `query.trim_joins()`. Returns list of `(OrderBy(transform_function(t, alias), descending=descending), False)` for each target.

##### `_setup_joins(self, pieces, opts, alias)` → `(field, targets, alias, joins, path, opts, transform_function)`

Helper that calls `self.query.setup_joins(pieces, opts, alias)`, returns the last join as alias along with field, targets, opts, joins, path, and transform_function.

##### `get_from_clause(self)` → `(list[str], list)`

Returns strings to join after FROM plus params.

- Iterates over `self.query.alias_map`: skips zero-refcount aliases. Compiles each from-clause entry via `compile()`.
- For each table in `self.query.extra_tables`: if alias not already in map or refcount is 1, appends `, {quoted_alias}`. Returns `(result, params)`.

##### `get_related_selections(self, select, opts=None, root_alias=None, cur_depth=1, requested=None, restricted=None)` → `list[dict]`

Fills in select-related information for nested model loading.

- Defines `_get_field_choices()` yielding direct relations, reverse unique relations, and filtered relation names.
- If not restricted and depth exceeds `max_depth`, returns `[]`.
- Gets opts from query Meta if needed; gets `only_load` via `deferred_to_columns()`.
- For each field in `opts.fields`: determines concrete model; skips parent fields already loaded. Checks validity of non-relation fields in restricted mode. Calls `select_related_descend(f, restricted, requested, only_load.get(field_model))`; if False, continues. Builds `klass_info` dict with model, field, reverse=False, setters, from_parent. Gets default columns for the related model; appends to select and records indices in `select_fields`. Recursively calls `get_related_selections()` for next depth.
- For reverse relations (unique FKs): similar process but with `reverse=True`, different setter logic. Checks `select_related_descend` with `reverse=True`. Builds klass_info, gets columns, recurses.
- If restricted: validates that all requested fields were found; raises `FieldError` listing invalid field names and available choices. Returns the list of related_klass_infos.

##### `get_select_for_update_of_arguments(self)` → `list[str]`

Returns quoted arguments for SELECT FOR UPDATE OF clause.

- Defines `_get_parent_klass_info(klass_info)` yielding parent klass_info dicts with select_fields from parent model columns.
- Defines `_get_first_selected_col_from_model(klass_info)` finding the first selected column matching a model's concrete model.
- Defines `_get_field_choices()` doing BFS over klass_info tree to yield all field path strings.
- If no `klass_info`, returns `[]`.
- For each name in `self.query.select_for_update_of`: resolves through klass_info tree; gets the first selected column; if feature supports column-level FOR UPDATE OF, compiles and appends SQL; else appends quoted alias.
- On invalid names: raises `FieldError` with available choices. Returns result list.

##### `deferred_to_columns(self)` → `dict[str, dict]`

Calls `self.query.deferred_to_data(columns)` to convert deferred loading data into a mapping of table names to sets of column names. Returns the columns dict.

##### `get_converters(self, expressions)` → `dict[int, tuple[list, Expression]]`

For each expression at position i: collects backend converters (`connection.ops.get_db_converters(expression)`) and field converters (`expression.get_db_converters(connection)`). If any exist, stores `(converters_list, expression)` in dict keyed by position. Returns the dict.

##### `apply_converters(self, rows, converters)` → generator of lists

For each row (converted to list): for each converter position, applies each converter function sequentially to the value at that position. Yields the modified row as a list.

##### `results_iter(self, results=None, tuple_expected=False, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE)` → generator

Returns an iterator over query results.

- If `results is None`, calls `execute_sql(MULTI, chunked_fetch, chunk_size)`.
- Gets field expressions from first `col_count` entries of `self.select`.
- Gets converters via `get_converters(fields)`.
- Flattens results via `chain.from_iterable()`. If converters exist, applies them; if tuple_expected, maps to tuples. Returns the generator.

##### `has_results(self)` → `bool`

Calls `execute_sql(SINGLE)` and returns `bool()` of the result.

##### `execute_sql(self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE)` → varies

Runs the query against the database.

- Sets `result_type = NO_RESULTS` if falsy.
- Calls `as_sql()`. If no SQL and result_type is MULTI, returns empty iterator; else returns None.
- Opens cursor (chunked or regular). Executes SQL with params. On exception, closes cursor and re-raises.
- If `result_type == CURSOR`: returns the cursor for caller to use/close.
- If `result_type == SINGLE`: fetchone, returns first `col_count` elements or None; closes cursor in finally.
- If `result_type == NO_RESULTS`: closes cursor, returns None.
- Otherwise: creates a `cursor_iter` with sentinel from connection features. If not chunked_fetch or backend doesn't support it, converts to list. Returns the iterator/list.

##### `as_subquery_condition(self, alias, columns, compiler)` → `(str, tuple)`

Adds this query's select columns as equality conditions against the given alias/columns in the WHERE clause (using RawSQL). Then calls `self.as_sql()` and returns `"EXISTS (%s)" % sql, params`.

##### `explain_query(self)` → generator of str

Executes the query via `execute_sql()`, then yields each row's content as a string. If explain format is JSON, uses `json.dumps`; otherwise uses `str`. For non-string tuple elements, joins with spaces after formatting.

---

### Class: `SQLInsertCompiler(SQLCompiler)`

#### Attributes (class-level)

- `returning_fields`: Initially `None`.
- `returning_params`: Tuple, initialized to `()`.

#### Methods

##### `field_as_sql(self, field, val)` → `(str, tuple)`

Returns placeholder SQL and params for a single field value:

- If `field is None`: treats value as raw; returns `(val, [])`.
- If `val` has `as_sql`: compiles via `self.compile(val)`.
- Else if `field` has `get_placeholder`: calls `field.get_placeholder(val, self, connection)` and returns `(placeholder, [val])`.
- Else: returns `("%s", [val])`.
- Calls `connection.ops.modify_insert_params(sql, params)` for backend-specific param adjustment. Returns `(sql, params)`.

##### `prepare_value(self, field, value)` → `value`

Prepares a value for insertion:

- If value has `resolve_expression`: resolves it; raises `ValueError` if the result contains column references (F() can't be used in INSERT); raises `FieldError` if it contains aggregates or window expressions.
- Else: calls `field.get_db_prep_save(value, connection=self.connection)`. Returns the prepared value.

##### `pre_save_val(self, field, obj)` → `value`

Gets a field's pre-save value from an object:

- If `self.query.raw`: returns `getattr(obj, field.attname)`.
- Else: calls `field.pre_save(obj, add=True)`. Returns the value.

##### `assemble_as_sql(self, fields, value_rows)` → `(placeholder_rows, param_rows)`

Generates placeholder SQL and params for bulk or single inserts.

- If no value rows, returns `([], [])`.
- For each row of (field, value) pairs: calls `field_as_sql(field, v)` to get `(sql, [params])`.
- Separates into `placeholder_rows` (list of placeholder strings per row) and `param_rows` (list of param lists per row). Flattens inner param lists. Returns `(placeholder_rows, param_rows)`.

##### `as_sql(self)` → `list[tuple[str, tuple]]`

Returns a list of `(sql_string, params_tuple)` for INSERT statements.

- Gets insert statement via `connection.ops.insert_statement(on_conflict=self.query.on_conflict)`.
- Builds: `"INSERT {statement} {table} ({columns})"`.
- If fields are set: builds value rows from objects; else uses default PK values and `[None]` as fields.
- Determines if bulk insert is possible (`not returning_fields and has_bulk_insert`).
- Calls `assemble_as_sql(fields, value_rows)` to get placeholders and params.
- Gets on-conflict suffix via `connection.ops.on_conflict_suffix_sql(...)`.
- If returning fields and backend supports return columns:
  - For bulk with can_return_rows_from_bulk_insert: calls `ops.return_insert_columns(returning_fields)`, appends result SQL, adds to params. Returns single combined statement.
  - Else for non-bulk: same as above but returns a single-row statement.
- If bulk possible: returns one statement with bulk insert SQL and all params flattened.
- Else (non-bulk): returns one statement per row: `"INSERT ... VALUES ({placeholders})"`.

##### `execute_sql(self, returning_fields=None)` → `list[tuple]`

Executes the INSERT and optionally returns inserted data.

- Asserts that returning fields with multiple objects requires `can_return_rows_from_bulk_insert`.
- Sets `self.returning_fields = returning_fields`.
- Iterates over `as_sql()` results, executing each via cursor.
- If no returning fields: returns `[]`.
- If bulk insert with return rows support and multiple objects: calls `ops.fetch_returned_insert_rows(cursor)`.
- Else if single object with column return support: calls `ops.fetch_returned_insert_columns(cursor, self.returning_params)`, wraps in list.
- Else: gets last insert ID via `ops.last_insert_id(cursor, table, pk_column)`, wraps as `(id,)`.
- Builds column expressions from returning fields; gets converters; applies them if present. Returns rows list.

---

### Class: `SQLDeleteCompiler(SQLCompiler)`

#### Attributes (cached properties)

- `single_alias`: True if the base table is the only table with a non-zero refcount in `alias_map`. Ensures initial alias first.
- `contains_self_reference_subquery`: True if any annotation or WHERE child expression references the base model via `_expr_refs_base_model()`.

#### Class Methods

##### `_expr_refs_base_model(cls, expr, base_model)` → `bool`

Recursively checks if an expression references a given base model:

- If `expr` is a `Query`: returns `expr.model == base_model`.
- Else if no `get_source_expressions`: returns `False`.
- Else: returns True if any source expression recursively refs the base model.

#### Methods

##### `_as_sql(self, query)` → `(str, tuple)`

Returns `"DELETE FROM {quoted_table}"` optionally with `"WHERE {compiled_where}"`. Compiles WHERE via `self.compile(query.where)`. Returns `(sql, params)`.

##### `as_sql(self)` → `(str, tuple)`

- If single alias and no self-reference subquery: returns `_as_sql(self.query)`.
- Otherwise: clones the query into an inner Query; clears select clause; selects only the PK column. Creates an outer Query; if backend doesn't support update-can-self-select, materializes the inner query as a `RawSQL` subquery. Adds `"pk__in"` filter with the inner query to the outer. Returns `_as_sql(outerq)`.

---

### Class: `SQLUpdateCompiler(SQLCompiler)`

#### Methods

##### `as_sql(self)` → `(str, tuple)`

Returns UPDATE SQL.

- Calls `pre_sql_setup()`. If no values, returns `("", ())`.
- For each `(field, model, val)` in `query.values`: resolves expressions; raises `FieldError` for aggregates or window expressions. Handles model instances via `prepare_database_save()` (raises `TypeError` if not a remote field). Calls `field.get_db_prep_save()`. Gets placeholder (custom or `%s`). Builds `"column = value"` or `"column = NULL"`.
- Returns `"UPDATE {table} SET {values} WHERE {where}"` with combined params.

##### `execute_sql(self, result_type)` → `int`

Executes the UPDATE and returns rows affected.

- Calls parent `execute_sql(result_type)`. Gets rowcount from cursor (0 if None).
- For each related update query: executes it via its own compiler; if this was empty but an aux query returned rows, uses that count. Returns total rows affected. Closes cursor in finally.

##### `pre_sql_setup(self)` → None

Adjusts WHERE conditions for updates involving other tables.

- Saves refcounts; ensures initial alias.
- If only one active table and no related updates: returns early.
- Chains a new Query selecting only the PK; clears ordering, extra, select; sets `select_related = False`. Calls parent `pre_sql_setup()`.
- If must pre-select (multiple tables or backend doesn't support self-select): executes the chain query to collect ID values, then filters main query by `"pk__in", idents`. Stores in `self.query.related_ids`.
- Else: fast path — adds subquery filter `"pk__in", query` directly.
- Resets refcounts.

---

### Class: `SQLAggregateCompiler(SQLCompiler)`

#### Methods

##### `as_sql(self)` → `(str, tuple)`

Returns SQL for aggregate queries.

- For each annotation in `self.query.annotation_select.values()`: compiles it; formats via `annotation.select_format(...)`. Collects SQL and params.
- Sets `col_count = len(annotation_select)`.
- Gets inner query compiler from `self.query.inner_query`, calls `as_sql(with_col_aliases=True)`.
- Returns `"SELECT {annotations} FROM ({inner_sql}) subquery"` with combined params.

---

### Function: `cursor_iter(cursor, sentinel, col_count, itersize)` → generator of lists

Yields blocks of rows from a cursor until the sentinel value is reached (using `iter(callable, sentinel)` pattern). Each row is sliced to `col_count` elements if `col_count` is not None. Ensures the cursor is closed in a `finally` block regardless of how iteration ends.

## django/db/models/sql/subqueries.py
Here is the complete natural-language specification of `django/db/models/sql/subqueries.py`:

---

## Module-Level Preamble

### Imports

```python
from django.core.exceptions import FieldError
from django.db.models.sql.constants import CURSOR, GET_ITERATOR_CHUNK_SIZE, NO_RESULTS
from django.db.models.sql.query import Query
```

### Constants & Globals

- `__all__` — a list of four class names exported by this module: `["DeleteQuery", "UpdateQuery", "InsertQuery", "AggregateQuery"]`.

---

## Code Objects

### Class `DeleteQuery(Query)`

**Inheritance:** Subclass of `Query`.

**Class attribute:**
- `compiler` — the string `"SQLDeleteCompiler"`, identifying the SQL compiler class used to compile and execute DELETE statements.

#### Method `do_query(self, table, where, using)`

Executes a single DELETE statement against one table.

1. Replaces `self.alias_map` with a dict containing only the entry for the given `table`: `{table: self.alias_map[table]}`.
2. Assigns the passed `where` argument to `self.where`.
3. Obtains an SQL compiler via `self.get_compiler(using)` and calls its `execute_sql(CURSOR)` method, which returns a database cursor (or `None`).
4. If the cursor is truthy: enters the cursor as a context manager (`with cursor:`) and returns `cursor.rowcount` (the number of rows deleted).
5. If the cursor is falsy: returns `0`.

**Return:** An integer — the number of rows affected by the DELETE, or `0` if no cursor was returned.

#### Method `delete_batch(self, pk_list, using)`

Performs batched DELETE operations for a list of primary-key values, chunking to avoid overly large SQL statements.

1. Initializes `num_deleted = 0`.
2. Retrieves the model's primary key field via `self.get_meta().pk` and stores it in `field`.
3. Iterates over `pk_list` in chunks of size `GET_ITERATOR_CHUNK_SIZE`: for each chunk, computes the slice `pk_list[offset : offset + GET_ITERATOR_CHUNK_SIZE]`.
4. For each chunk:
   a. Clears any existing WHERE clause via `self.clear_where()`.
   b. Adds an `"in"` filter on the primary key field's attname: `f"{field.attname}__in"`, with the current chunk as the value, via `self.add_filter(...)`.
   c. Calls `self.do_query(self.get_meta().db_table, self.where, using=using)` and adds the returned rowcount to `num_deleted`.
5. Returns `num_deleted` — the total number of rows deleted across all chunks.

**Return:** An integer — the cumulative count of deleted objects.

---

### Class `UpdateQuery(Query)`

**Inheritance:** Subclass of `Query`.

**Class attribute:**
- `compiler` — the string `"SQLUpdateCompiler"`.

#### Instance attributes (initialized in `_setup_query`)

- `values` — a list, initially empty; stores tuples of `(field, model, value)` representing columns to update.
- `related_ids` — set to `None`; holds primary-key values for related-update filtering when needed.
- `related_updates` — an empty dict `{}`; maps ancestor models (as keys) to lists of `(field, None, value)` triples describing updates that must be applied to those ancestor tables.

#### Method `__init__(self, *args, **kwargs)`

1. Calls the parent `Query.__init__(*args, **kwargs)`.
2. Calls `self._setup_query()`.

#### Method `_setup_query(self)`

Initializes instance attributes: sets `self.values = []`, `self.related_ids = None`, and `self.related_updates = {}`. Called both from `__init__` and at the end of chaining operations.

#### Method `clone(self)`

1. Calls `super().clone()` to create a shallow copy of the Query base state.
2. Copies `self.related_updates` into the cloned object via `.copy()`, assigning it to `obj.related_updates`.
3. Returns the cloned object.

**Return:** A new `UpdateQuery` instance with copied base state and a deep-enough copy of `related_updates`.

#### Method `update_batch(self, pk_list, values, using)`

Performs batched UPDATE operations across chunks of primary-key values.

1. Calls `self.add_update_values(values)` to populate the update fields/values from the provided dictionary mapping field names to values.
2. Iterates over `pk_list` in chunks of size `GET_ITERATOR_CHUNK_SIZE`.
3. For each chunk:
   a. Clears any existing WHERE clause via `self.clear_where()`.
   b. Adds an `"in"` filter on `"pk__in"` with the current chunk as the value, via `self.add_filter(...)`.
   c. Obtains the SQL compiler via `self.get_compiler(using)` and calls its `execute_sql(NO_RESULTS)` method to execute the UPDATE (no result is expected).

**Return:** None.

#### Method `add_update_values(self, values)`

Converts a dictionary of `{field_name: value}` mappings into update targets. This is the entry point for public queryset `.update()` calls.

1. Initializes an empty list `values_seq`.
2. Iterates over each `(name, val)` pair in `values.items()`:
   a. Retrieves the Django field object via `self.get_meta().get_field(name)`.
   b. Determines whether the field is "direct" (i.e., can be updated directly): `direct = not ((field.auto_created and not field.concrete) or not field.concrete)`. This evaluates to `True` for concrete, non-auto-created fields; `False` otherwise.
   c. Computes `model = field.model._meta.concrete_model`.
   d. If the field is not direct **or** it is a relation that is many-to-many (`field.is_relation and field.many_to_many`): raises `FieldError` with the message `"Cannot update model field %r (only non-relations and foreign keys permitted)." % field`.
   e. If `model` differs from `self.get_meta().concrete_model`: calls `self.add_related_update(model, field, val)` to defer the update to an ancestor table, then `continue`s to the next iteration.
   f. Otherwise: appends `(field, model, val)` to `values_seq`.
3. Calls and returns `self.add_update_fields(values_seq)`.

**Return:** The return value of `add_update_fields` (which is `None`).

#### Method `add_update_fields(self, values_seq)`

Appends field/value triples to the internal update list, resolving any expression objects along the way.

1. Iterates over each `(field, model, val)` triple in `values_seq`:
   a. If `val` has an attribute `"resolve_expression"` (i.e., it is a Django expression object): resolves it by calling `val.resolve_expression(self, allow_joins=False, for_save=True)`, storing the resolved value back into `val`.
   b. Appends `(field, model, val)` to `self.values`.

**Return:** None.

#### Method `add_related_update(self, model, field, value)`

Registers an update that must be applied to an ancestor (parent) model's table rather than the current model's table.

1. Calls `self.related_updates.setdefault(model, [])` and appends `(field, None, value)` to the resulting list. The `None` placeholder is for a column name that is not used in this context.

**Return:** None.

#### Method `get_related_updates(self)`

Produces a list of independent `UpdateQuery` objects — one per ancestor model that needs updating — each carrying the same filtering conditions as the current query but targeting only its own table.

1. If `self.related_updates` is empty: returns an empty list `[]`.
2. Otherwise, initializes an empty list `result`.
3. For each `(model, values)` pair in `self.related_updates.items()`:
   a. Creates a new `UpdateQuery(model)`.
   b. Assigns the accumulated `values` to `query.values`.
   c. If `self.related_ids is not None`: adds an `"in"` filter on `"pk__in"` with `self.related_ids` as the value, via `query.add_filter(...)`.
   d. Appends `query` to `result`.
4. Returns `result`.

**Return:** A list of `UpdateQuery` instances (one per ancestor model needing an update), or an empty list if there are no related updates.

---

### Class `InsertQuery(Query)`

**Inheritance:** Subclass of `Query`.

**Class attribute:**
- `compiler` — the string `"SQLInsertCompiler"`.

#### Instance attributes (initialized in `__init__`)

- `fields` — a list, initially empty; stores field objects to be inserted.
- `objs` — a list, initially empty; stores the object/value rows to insert.
- `on_conflict` — set from constructor argument or `None`; specifies conflict-handling behavior (e.g., `"UPDATE"` for upserts).
- `update_fields` — a list, initialized from the `update_fields` constructor argument or `[]` if falsy; names of fields to update on conflict.
- `unique_fields` — a list, initialized from the `unique_fields` constructor argument or `[]` if falsy; names of unique columns that define conflict targets.

#### Method `__init__(self, *args, on_conflict=None, update_fields=None, unique_fields=None, **kwargs)`

1. Calls the parent `Query.__init__(*args, **kwargs)`.
2. Sets `self.fields = []`, `self.objs = []`.
3. Stores `on_conflict` from the argument (or `None`).
4. Stores `update_fields` from the argument or defaults to `[]`.
5. Stores `unique_fields` from the argument or defaults to `[]`.

#### Method `insert_values(self, fields, objs, raw=False)`

Sets the field and object lists for a single insert operation.

1. Assigns `fields` to `self.fields`.
2. Assigns `objs` to `self.objs`.
3. Stores `raw` (a boolean) in `self.raw`, indicating whether the values are raw SQL fragments rather than parameterized Python objects.

**Return:** None.

---

### Class `AggregateQuery(Query)`

**Inheritance:** Subclass of `Query`.

**Class attribute:**
- `compiler` — the string `"SQLAggregateCompiler"`.

#### Instance attributes (initialized in `__init__`)

- `inner_query` — set from constructor argument; a `Query` instance that serves as the inner subquery placed in the FROM clause.

#### Method `__init__(self, model, inner_query)`

1. Stores `inner_query` in `self.inner_query`.
2. Calls the parent `Query.__init__(model)`, passing only the model argument to initialize the base Query state with the target model.

**Purpose:** This query type wraps another query as a subquery in its FROM clause and selects only the elements specified by its own field list, effectively projecting/limiting columns from an inner query result.