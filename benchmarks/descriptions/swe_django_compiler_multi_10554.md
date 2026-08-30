## django/db/models/sql/compiler.py
Now I have read the entire file (1517 lines). Here is the complete specification:

---

# Module Specification: `django/db/models/sql/compiler.py`

## 1. Imports

```python
import collections          # deque for BFS traversal in get_select_for_update_of_arguments
import re                   # regex compilation for ordering_parts pattern
import warnings             # deprecation warning emission
from itertools import chain # chaining iterables (results_iter, _get_field_choices)

from django.core.exceptions import EmptyResultSet, FieldError
from django.db.models.constants import LOOKUP_SEP  # '__' separator string
from django.db.models.expressions import OrderBy, Random, RawSQL, Ref, Value
from django.db.models.functions import Cast
from django.db.models.query_utils import QueryWrapper, select_related_descend
from django.db.models.sql.constants import (
    CURSOR, GET_ITERATOR_CHUNK_SIZE, MULTI, NO_RESULTS, ORDER_DIR, SINGLE,
)
from django.db.models.sql.query import Query, get_order_dir
from django.db.transaction import TransactionManagementError
from django.db.utils import DatabaseError, NotSupportedError
from django.utils.deprecation import RemovedInDjango31Warning
from django.utils.hashable import make_hashable
```

## 2. Constants & Globals

- **`FORCE = object()`** — Sentinel value used as the `select_format` argument to `compile()` to force select-format output regardless of whether the query is a subquery.

## 3. Code Objects

### 3.1 Class `SQLCompiler`

**Inheritance:** None (base class)

**Attributes initialized in `__init__(self, query, connection, using)`:**
- `self.query` — A `Query` object representing the SQL query to compile.
- `self.connection` — The database connection object.
- `self.using` — The database alias string.
- `self.quote_cache: dict[str, str]` — Cached quoted names; initialized as `{'*': '*'}`.
- `self.select: list | None` — Set as a side-effect of `setup_query()` via `get_select()`. List of 3-tuples `(expression, (sql, params), alias)`.
- `self.annotation_col_map: dict | None` — Set by `get_select()`. Dictionary mapping annotation names to column positions.
- `self.klass_info: dict | None` — Set by `get_select()`. Structure describing model/class info for result instantiation.
- `self.ordering_parts: re.Pattern` — Compiled regex `r'^(.*)\s(ASC|DESC)(.*)'` with flags `re.MULTILINE | re.DOTALL`, used to strip ordering direction from SQL strings.
- `self._meta_ordering: list | None` — Stores the Meta.ordering value when it is applied; used for deprecation warning emission.

**Attributes set by other methods:**
- `self.col_count: int` — Length of `self.select`, set in `setup_query()`.
- `self.where, self.having` — Split from `self.query.where.split_having()` in `pre_sql_setup()`.

---

#### `setup_query(self)`

Ensures the query has an initial alias (calls `get_initial_alias()` if all `alias_refcount` values are zero). Then calls `get_select()` to populate `self.select`, `self.klass_info`, and `self.annotation_col_map`. Sets `self.col_count = len(self.select)`.

---

#### `pre_sql_setup(self)` → `(extra_select, order_by, group_by)`

Performs full class setup prior to SQL generation:
1. Calls `setup_query()`.
2. Calls `get_order_by()` to populate ordering.
3. Splits `self.query.where` into `self.where` and `self.having` via `split_having()`.
4. Calls `get_extra_select(order_by, self.select)` to get extra columns needed for DISTINCT + ORDER BY; sets `self.has_extra_select = bool(extra_select)`.
5. Calls `get_group_by(self.select + extra_select, order_by)` to compute GROUP BY clause.
6. Returns `(extra_select, order_by, group_by)`.

---

#### `get_group_by(self, select, order_by)` → `list[tuple[str, tuple]]`

Returns a list of 2-tuples `(sql, params)` for the GROUP BY clause. Logic:
- If `self.query.group_by is None`, returns `[]`.
- Builds an `expressions` list:
  - If `self.query.group_by` is not `True` (i.e., it's a list from `.values()`), iterates over each item; if the item lacks `as_sql` (a string reference), resolves it via `self.query.resolve_ref(expr)`; otherwise appends directly.
- For every `(expr, _, _)` in `select`, calls `expr.get_group_by_cols()` and extends `expressions`.
- For every `(expr, (sql, params, is_ref))` in `order_by`: if the expression has no aggregate and `is_ref` is False, extends with `expr.get_source_expressions()`.
- If `self.having` exists, calls `self.having.get_group_by_cols()` and appends each.
- Calls `self.collapse_group_by(expressions, having_group_by)` to apply database-specific optimizations (GROUP BY primary key shortcuts).
- Deduplicates by compiling each expression via `self.compile(expr)`, hashing params with `make_hashable()`, and tracking seen `(sql, params_hash)` pairs. Returns the deduplicated list of `(sql, params)` tuples.

---

#### `collapse_group_by(self, expressions, having)` → `list`

Optimizes GROUP BY based on database features:
- If `self.connection.features.allows_group_by_pk`: Finds the main model's primary key expression in `expressions`. If found, filters to only `(pk) + (having expressions) + (expressions from tables without a PK in grouped columns)`.
- Else if `self.connection.features.allows_group_by_selected_pks`: Filters out non-PK columns for any table whose PK is already present. Excludes unmanaged models.
- Returns the filtered expression list.

---

#### `get_select(self)` → `(select, klass_info, annotations)`

Returns three values:
1. **`select`** — List of 3-tuples `(expression, (sql, params), alias)`.
2. **`klass_info`** — Dict with `'model'`, `'select_fields'`, and optionally `'related_klass_infos'`.
3. **`annotations`** — Dict mapping annotation names to select column indices.

Logic:
- Initializes `select = []`, `klass_info = None`, `annotations = {}`, `select_idx = 0`.
- For each `(alias, (sql, params))` in `self.query.extra_select`: records index in `annotations`, appends `(RawSQL(sql, params), alias)` to select, increments `select_idx`.
- Asserts that `self.query.select` and `self.query.default_cols` are not both set. If `self.query.default_cols` is True, calls `get_default_columns()`; otherwise uses `self.query.select`.
- For each column in `cols`: appends its index to `select_list`, appends `(col, None)` to select, increments `select_idx`. Sets `klass_info = {'model': self.query.model, 'select_fields': select_list}`.
- For each `(alias, annotation)` in `self.query.annotation_select`: records index in `annotations`, appends `(annotation, alias)` to select, increments `select_idx`.
- If `self.query.select_related` is truthy: calls `get_related_selections(select)` to populate related klass infos; sets `klass_info['related_klass_infos']`. Then recursively propagates parent select_fields to children where `'from_parent'` is True.
- For each `(col, alias)` in the assembled select list: tries `self.compile(col, select_format=True)`. If it raises `EmptyResultSet`, uses `('0', ())`. Appends `(col, (sql, params), alias)` to result.
- Returns `(ret, klass_info, annotations)`.

---

#### `get_order_by(self)` → `list[tuple[OrderBy, tuple]]`

Returns a list of 2-tuples `(resolved_expr, (sql, params, is_ref))` for the ORDER BY clause. Logic:
1. Determines ordering source: `self.query.extra_order_by`, or `self.query.order_by` if set and not default ordering, or `self.query.get_meta().ordering` (stored in `self._meta_ordering`). Defaults to `[]`.
2. Sets `asc, desc` from `ORDER_DIR` based on `self.query.standard_ordering`.
3. For each field in the ordering:
   - If it has `resolve_expression`: if it's a `Value`, wraps with `Cast(field, field.output_field)`. If not an `OrderBy`, calls `.asc()`. If `standard_ordering` is False, copies and reverses. Appends `(field, False)`.
   - If field is `'?'`: appends `(OrderBy(Random()), False)` for random ordering.
   - Otherwise: parses direction via `get_order_dir(field, asc)`. Then checks:
     - If `col` in `self.query.annotation_select`: creates `OrderBy(Ref(col, annotation_expr), descending)`, marks as ref (`True`).
     - Else if `col` in `self.query.annotations`: resolves the expression (casting `Value` if needed), appends with `is_ref=False`.
     - Else if `'.'` in field: splits into table.column, creates `OrderBy(RawSQL('%s.%s' % (quoted_table, col), []), descending)`, `is_ref=False`.
     - Else if no extra or col not in `self.query.extra`: calls `find_ordering_name(field, opts, default_order=asc)` and extends.
     - Else: if col is in `extra_select`, uses `OrderBy(RawSQL(*extra[col]), descending)`, else uses `OrderBy(Ref(col, RawSQL(...)), descending)` with `is_ref=True`.
4. Deduplicates: iterates over `(expr, is_ref)`, resolves each via `expr.resolve_expression(self.query, allow_joins=True, reuse=None)`. If `self.query.combinator` exists, relabels to numeric column indices (`RawSQL('%d' % (idx + 1), ())`). Strips ordering direction from SQL using `ordering_parts.search(sql).group(1)`, hashes params, deduplicates by `(without_ordering, params_hash)`.
5. Returns list of `(resolved, (sql, params, is_ref))` tuples.

---

#### `get_extra_select(self, order_by, select)` → `list[tuple[expr, tuple, None]]`

Returns extra columns needed when `self.query.distinct` is True and `distinct_fields` is empty:
- For each `(expr, (sql, params, is_ref))` in `order_by`: if not a ref and the SQL+params pair is not already in select SQLs, appends `(expr, (without_ordering_sql, params), None)`.

---

#### `quote_name_unless_alias(self, name)` → `str`

Returns a quoted table/column name. Checks `self.quote_cache` first. If the name is an alias (in `alias_map` but not in `table_map`, or in `extra_select`, or in `external_aliases`), returns it unquoted. Otherwise calls `self.connection.ops.quote_name(name)` and caches.

---

#### `compile(self, node, select_format=False)` → `(str, tuple)`

Compiles an expression node to SQL:
1. Looks for a vendor-specific implementation: `node.as_<vendor>(self, self.connection)`. Falls back to `node.as_sql(self, self.connection)`.
2. If `select_format` is `FORCE` or (`select_format` is truthy and the query is not a subquery), applies `node.output_field.select_format(self, sql, params)` for backend-specific formatting (e.g., PostgreSQL).
3. Returns `(sql, params)`.

---

#### `get_combinator_sql(self, combinator, all)` → `(list[str], list)`

Generates SQL for compound queries (UNION, INTERSECT, DIFFERENCE):
1. Creates compilers for each combined query that is not empty.
2. If the backend doesn't support LIMIT/OFFSET in compounds, raises `DatabaseError` if any subquery has limits or ordering.
3. For each compiler: if `values_select` is set but the sub-query doesn't have it, clones and sets values from the main query. Calls `compiler.as_sql()`. If the sub-query itself is a combinator and the backend doesn't support parentheses in compounds, wraps as `SELECT * FROM (...)`.
4. Omits empty resultsets with UNION (always) or DIFFERENCE (only if not first). Re-raises `EmptyResultSet` for other cases.
5. Builds combinator SQL using `self.connection.ops.set_operators[combinator]`, appending `' ALL'` if `all` and combinator is `'union'`.
6. Wraps each part in braces based on backend support, joins with the combinator operator. Returns `(result_list, params_list)`.

---

#### `as_sql(self, with_limits=True, with_col_aliases=False)` → `(str, tuple)`

Main method: generates the full SQL query string and parameter tuple.

Logic (inside try/finally block):
1. Calls `pre_sql_setup()` to get `(extra_select, order_by, group_by)`. Saves `refcounts_before = self.query.alias_refcount.copy()`.
2. If `self.query.combinator` exists: checks backend support; calls `get_combinator_sql(combinator, combinator_all)` for `(result, params)`.
3. Else (simple query):
   - Calls `get_distinct()` to get distinct fields/params.
   - Calls `get_from_clause()` for FROM clause.
   - Compiles `self.where` and `self.having` if present.
   - Builds `result = ['SELECT']`.
   - If `self.query.distinct`: calls `connection.ops.distinct_sql(distinct_fields, distinct_params)`, appends to result.
   - Builds column list: for each `(s_sql, s_params), alias` in `select + extra_select`: if alias exists, formats as `sql AS quoted_alias`; else if `with_col_aliases`, formats as `sql AS ColN`. Extends params. Joins with `, `.
   - Appends columns, `'FROM'`, from-clause to result.
   - If `self.query.select_for_update` and backend supports it: checks autocommit (raises `TransactionManagementError` if on), checks LIMIT compatibility, validates NOWAIT/SKIP_LOCKED/OF support, calls `connection.ops.for_update_sql(nowait, skip_locked, of=...)`. Sets `for_update_part`.
   - If `for_update_part` and backend puts FOR UPDATE after FROM: appends it.
   - If where exists: appends `'WHERE ' + where`.
   - Builds grouping SQL; if grouping and distinct_fields exist, raises `NotImplementedError`. If meta-ordering was used, emits deprecation warning. Appends `'GROUP BY ...'` if grouping present.
   - If having exists: appends `'HAVING ' + having`.
4. If `self.query.explain_query`: inserts explain prefix at position 0.
5. If order_by exists: builds ORDER BY clause, appends.
6. If `with_limit_offset`: appends limit/offset SQL via `connection.ops.limit_offset_sql(low_mark, high_mark)`.
7. If `for_update_part` and backend puts FOR UPDATE before FROM: appends it.
8. **Subquery wrapping:** If `self.query.subquery` and `extra_select` exists: builds a wrapper query selecting only the original columns from `(original_sql) subquery`, to exclude extra selects. Returns wrapped SQL.
9. Returns `' '.join(result), tuple(params)`.

**Finally block:** Calls `self.query.reset_refcounts(refcounts_before)` to clean up joins.

---

#### `get_default_columns(self, start_alias=None, opts=None, from_parent=None)` → `list`

Returns a list of column expressions for selecting every field in the base model:
- If `opts is None`, gets it from `self.query.get_meta()`.
- Calls `deferred_to_columns()` to get deferred field mapping.
- Gets initial alias; builds `seen_models = {None: start_alias}`.
- For each concrete field in opts: determines the model (None if local). Skips if already loaded from a parent via `from_parent`. Skips if field is deferred. Joins parent model, gets column via `field.get_col(alias)`, appends to result.
- Returns list of column expressions.

---

#### `get_distinct(self)` → `(list[str], list[tuple])`

Returns quoted fields for DISTINCT ON:
- For each name in `self.query.distinct_fields`: splits by `LOOKUP_SEP`, calls `_setup_joins()` to get targets/alias/joins/path/transform_function. Trims joins. If the name is an annotation, appends the name; otherwise compiles `transform_function(target, alias)` and collects SQL+params.
- Returns `(result, params)`.

---

#### `find_ordering_name(self, name, opts, alias=None, default_order='ASC', already_seen=None)` → `list[tuple[OrderBy, bool]]`

Resolves a field path (e.g., `'field1__field2'`) to ordering expressions:
- Parses direction via `get_order_dir()`. Splits by `LOOKUP_SEP`, calls `_setup_joins()`.
- If the resolved field is a relation and opts has ordering, and the attribute name differs from the field name: checks for infinite loops (join tuple in `already_seen`), adds to seen set, recursively resolves each ordering item. Returns results.
- Otherwise: trims joins, returns list of `(OrderBy(transform_function(target, alias), descending=descending), False)` for each target.

---

#### `_setup_joins(self, pieces, opts, alias)` → `tuple`

Helper that calls `self.query.setup_joins(pieces, opts, alias)`, extracts the last join as alias, returns `(field, targets, alias, joins, path, opts, transform_function)`.

---

#### `get_from_clause(self)` → `(list[str], list[tuple])`

Returns FROM clause components:
- For each alias in `self.query.alias_map`: if refcount is zero, skips. Gets the from-clause expression; compiles it. Appends SQL and params.
- For each table in `self.query.extra_tables`: gets/creates an alias via `table_alias()`. If not already in alias_map or refcount is 1, appends `, quoted_alias`.
- Returns `(result_list, params_list)`.

---

#### `get_related_selections(self, select, opts=None, root_alias=None, cur_depth=1, requested=None, restricted=None)` → `list[dict]`

Recursively builds `related_klass_infos` for `select_related()` queries:
- Inner function `_get_field_choices()`: yields direct relation field names, reverse relation query names (unique only), and filtered relation names.
- If not restricted and depth exceeds `self.query.max_depth`, returns empty list.
- Sets up opts from meta if needed; gets loaded field names.
- Determines `restricted` mode (dict-based select_related).
- For each field in opts.fields: tracks in `fields_found`. In restricted mode, validates non-relation fields raise `FieldError`. Calls `select_related_descend()` to decide whether to descend. Builds a klass_info dict with model, field, reverse=False, local_setter/remote_setter callbacks, from_parent=False. Appends select columns for the related model's default columns (recording indices in `select_fields`). Recursively calls itself for nested relations.
- In restricted mode: handles reverse relations (unique, non-M2M), filtered relations (top-level only). For each, builds klass_info with appropriate setters and from_parent flag, adds select columns, recurses. Validates all requested fields were found; raises `FieldError` if not.
- Returns the list of related_klass_infos dicts.

---

#### `get_select_for_update_of_arguments(self)` → `list[str]`

Returns quoted column/table references for SELECT FOR UPDATE OF:
- Inner `_get_field_choices()`: BFS traversal of klass_info tree, yielding `'self'` for root and field paths for children.
- For each name in `self.query.select_for_update_of`: splits by `LOOKUP_SEP` (empty list for `'self'`). Traverses the klass_info tree matching field names. If not found, marks as invalid. If found, gets the first select index from `select_fields`, compiles that column; if backend supports column-level FOR UPDATE OF, uses compiled SQL; otherwise uses quoted alias name.
- Raises `FieldError` if any invalid names remain. Returns list of SQL fragments.

---

#### `deferred_to_columns(self)` → `dict`

Converts deferred loading data to a mapping of table names to sets of column names. Calls `self.query.deferred_to_data(columns, self.query.get_loaded_field_names_cb)`.

---

#### `get_converters(self, expressions)` → `dict[int, tuple]`

For each expression in the select list: collects backend converters (`connection.ops.get_db_converters(expression)`) and field converters (`expression.get_db_converters(self.connection)`). If either is non-empty, stores `(backend_converters + field_converters, expression)` at index position. Returns dict of `{index: (converters_list, expression)}`.

---

#### `apply_converters(self, rows, converters)` → generator[list]

Yields rows with type conversion applied: for each row, iterates over converter positions; applies each converter function to the value at that position in sequence. Yields converted rows as lists (or tuples if mapped).

---

#### `results_iter(self, results=None, tuple_expected=False, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE)` → generator

Returns an iterator over query results:
- If `results` is None, calls `execute_sql(MULTI, chunked_fetch, chunk_size)`.
- Extracts field expressions from `self.select[:self.col_count]`.
- Gets converters for those fields.
- Chains all result rows together; applies converters if present; optionally maps to tuples.
- Returns the generator.

---

#### `has_results(self)` → `bool`

Checks whether the query returns any results (optimized for NoSQL backends): adds a dummy extra select, executes with `SINGLE`, returns bool of result.

---

#### `execute_sql(self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE)` → varies

Executes the SQL query against the database:
1. Calls `as_sql()` to get `(sql, params)`. If no SQL, raises `EmptyResultSet`; if MULTI, returns empty iterator; else returns None.
2. Opens cursor (chunked or regular based on flag/backend support).
3. Executes with `cursor.execute(sql, params)`. On exception, closes cursor and re-raises.
4. Based on `result_type`:
   - **CURSOR**: Returns the cursor to caller for manual processing/closing.
   - **SINGLE**: Calls `fetchone()`, returns first `col_count` elements or None. Closes cursor in finally.
   - **NO_RESULTS**: Closes cursor, returns None.
   - **MULTI** (default): Uses `cursor_iter()` helper to fetch rows in chunks. If not chunked_fetch or backend doesn't support it, materializes into a list and closes cursor. Otherwise yields the generator.

---

#### `as_subquery_condition(self, alias, columns, compiler)` → `(str, tuple)`

Creates an EXISTS subquery condition for use in WHERE clauses:
- For each select column index: compiles the column SQL+params; builds RHS as `'alias.column'`. Adds a `QueryWrapper('%s = %s', lhs_params)` with 'AND' to `self.query.where`.
- Calls `self.as_sql()` to get the subquery SQL.
- Returns `('EXISTS (%s)' % sql, params)`.

---

#### `explain_query(self)` → generator[str]

Executes the query as an EXPLAIN and yields formatted explanation rows: executes with `execute_sql()`, iterates over the first row's elements; if an element is not a string (e.g., tuple of ints/strings), joins them with spaces. Yields each row as a flat string.

---

### 3.2 Class `SQLInsertCompiler(SQLCompiler)`

**Class attribute:**
- `return_id = False` — Flag set by `execute_sql()` to request returned insert IDs.

---

#### `field_as_sql(self, field, val)` → `(str, list)`

Generates placeholder SQL and params for a single field value:
- If `field is None`: treats value as raw; returns `(val, [])`.
- If `val` has `as_sql` (is an expression): compiles via `self.compile(val)`.
- Else if `field` has `get_placeholder()`: calls `field.get_placeholder(val, self, self.connection)` and wraps val in `[val]`.
- Else: returns `('%s', [val])`.
- Applies `self.connection.ops.modify_insert_params(sql, params)` for backend-specific param modification (e.g., Oracle Spatial).
- Returns `(sql, params)`.

---

#### `prepare_value(self, field, value)` → value

Prepares a value for insertion:
- If value has `resolve_expression`: resolves it with `allow_joins=False, for_save=True`. Raises `ValueError` if the resolved expression contains column references (F() on existing columns not allowed in INSERT). Raises `FieldError` if it contains aggregates or window expressions.
- Else: calls `field.get_db_prep_save(value, connection=self.connection)`.
- Returns the prepared value.

---

#### `pre_save_val(self, field, obj)` → value

Gets a field's pre-save value from an object:
- If `self.query.raw` is True: returns `getattr(obj, field.attname)`.
- Else: calls `field.pre_save(obj, add=True)` (handles auto_now etc.).

---

#### `assemble_as_sql(self, fields, value_rows)` → `(placeholder_rows, param_rows)`

Takes N fields and M value rows; generates placeholder SQL and params:
- If no value rows, returns `([], [])`.
- For each row, zips fields with values through `field_as_sql()`, producing a list of `(sql, [params])` tuples.
- Transposes to separate SQL placeholders and param lists per field.
- Flattens nested param lists: `[p for ps in row for p in ps]`.
- Returns `(placeholder_rows, param_rows)` where each is an M-element sequence of N-element sequences.

---

#### `as_sql(self)` → `list[tuple[str, tuple]]`

Generates INSERT statement SQL(s):
1. Gets table name via `opts.db_table`; quotes with `connection.ops.quote_name()`.
2. Builds `'INSERT [IGNORE] INTO table'` prefix.
3. Determines fields: `self.query.fields or [opts.pk]`. Builds column list `(col1, col2, ...)`.
4. If fields are specified: builds value rows by calling `prepare_value(field, pre_save_val(field, obj))` for each field/obj pair. Else (empty insert): uses `[pk_default_value()]` per object and sets `fields = [None]`.
5. Determines bulk capability: `can_bulk = not self.return_id and connection.features.has_bulk_insert`.
6. Calls `assemble_as_sql(fields, value_rows)`.
7. Gets ignore-conflicts suffix SQL if applicable.
8. **Return ID path** (`self.return_id` and backend supports return columns):
   - If bulk insert supported: uses `bulk_insert_sql()`, params is the full param_rows list.
   - Else: uses single-row VALUES clause, params is `[param_rows[0]]`.
   - Appends ignore-conflicts suffix if present. Adds RETURNING clause via `connection.ops.return_insert_id()` with primary key column. Returns a single-item list `[("full_sql", combined_params)]`.
9. **Bulk path** (`can_bulk`): Uses `bulk_insert_sql()`, appends ignore-conflicts suffix, returns single SQL with all params flattened: `[("sql", tuple(p for ps in param_rows for p in ps))]`.
10. **Single-row path**: Appends ignore-conflicts suffix if present. Returns one SQL per value row: `[("INSERT INTO table (cols) VALUES (vals)", vals)]` for each `(placeholder_row, param_row)` pair.

---

#### `execute_sql(self, return_id=False)` → varies

Executes the INSERT and optionally returns generated IDs:
1. Asserts that if `return_id` is True and there are multiple objects, the backend must support bulk row return.
2. Sets `self.return_id = return_id`.
3. Opens cursor; iterates over all `(sql, params)` from `as_sql()`, executing each.
4. If not returning ID: returns None.
5. If returning ID and bulk insert supported with multiple objects: calls `connection.ops.fetch_returned_insert_ids(cursor)`, returns list of IDs.
6. Else if column return supported (single object): calls `connection.ops.fetch_returned_insert_id(cursor)`.
7. Else: calls `connection.ops.last_insert_id(cursor, table, pk_column)`.

---

### 3.3 Class `SQLDeleteCompiler(SQLCompiler)`

---

#### `as_sql(self)` → `(str, tuple)`

Generates DELETE statement SQL:
1. Asserts exactly one table has a non-zero refcount in `alias_map` (can only delete from one table).
2. Builds `'DELETE FROM quoted_table'`.
3. Compiles `self.query.where`; if present, appends `'WHERE ' + where`.
4. Returns `' '.join(result), tuple(params)`.

---

### 3.4 Class `SQLUpdateCompiler(SQLCompiler)`

---

#### `as_sql(self)` → `(str, tuple)`

Generates UPDATE statement SQL:
1. Calls `pre_sql_setup()`. If no values to update, returns `('', ())`.
2. For each `(field, model, val)` in `self.query.values`:
   - If val has `resolve_expression`: resolves with `allow_joins=False, for_save=True`. Raises `FieldError` if it contains aggregates or window expressions.
   - Else if val has `prepare_database_save`: if field is a relation, calls `field.get_db_prep_save(val.prepare_database_save(field), connection)`. Else raises `TypeError`.
   - Else: calls `field.get_db_prep_save(val, connection)`.
   - Gets placeholder via `field.get_placeholder()` or `'%s'`.
   - If val has `as_sql` (expression): compiles it; appends `'quoted_name = placeholder % compiled_sql'` to values, extends params.
   - Else if val is not None: appends `'quoted_name = placeholder'`, appends val to params.
   - Else (None/NULL): appends `'quoted_name = NULL'`.
3. Builds result: `['UPDATE quoted_table SET', ', '.join(values)]`.
4. Compiles where clause; if present, appends `'WHERE ' + where`.
5. Returns `' '.join(result), tuple(update_params + params)`.

---

#### `execute_sql(self, result_type)` → `int`

Executes the UPDATE and returns rows affected:
1. Calls parent `execute_sql(result_type)` to get cursor (or None if no query).
2. Gets `rows = cursor.rowcount` (0 if cursor is None); tracks whether the primary query was empty.
3. Closes cursor in finally block.
4. For each related update from `self.query.get_related_updates()`: executes via its own compiler, gets aux_rows. If primary was empty but aux has rows, uses aux count as result.
5. Returns total row count.

---

#### `pre_sql_setup(self)` → None

Adjusts WHERE conditions for updates that depend on other tables:
1. Saves refcounts; ensures base table is in query via `get_initial_alias()`.
2. Counts active tables. If no related updates and only one active table, returns early (simple update).
3. Creates a chain Query to determine IDs to update: disables select_related, clears ordering/extra/select, adds primary key field. Calls parent `pre_sql_setup()`.
4. Determines if pre-selection is needed (`count > 1` and backend doesn't support self-select in UPDATE).
5. Resets the current query's WHERE clause to empty; removes unnecessary tables via refcount reset.
6. If pre-selection needed or related updates exist: executes the ID-finding query, collects IDs into a list, adds `'pk__in': idents` filter, stores `self.query.related_ids`.
7. Else (fast path): adds `'pk__in': query` directly as a subquery filter.
8. Resets refcounts to pre-setup state.

---

### 3.5 Class `SQLAggregateCompiler(SQLCompiler)`

---

#### `as_sql(self)` → `(str, tuple)`

Generates SQL for aggregate-only queries:
1. For each annotation in `self.query.annotation_select.values()`: compiles with `select_format=FORCE`, collects SQL and params.
2. Sets `self.col_count = len(self.query.annotation_select)`.
3. Joins all annotation SQLs with `, `.
4. Wraps as `'SELECT %s FROM (%s) subquery'` where the inner query is `self.query.subquery`, appending `self.query.sub_params`.
5. Returns `(sql, params)`.

---

### 3.6 Function `cursor_iter(cursor, sentinel, col_count, itersize)` → generator[list]

Yields blocks of rows from a database cursor:
- Uses `iter(lambda: cursor.fetchmany(itersize), sentinel)` to fetch in chunks until the sentinel value is returned (empty batch).
- For each batch of rows: if `col_count` is not None, slices each row to `[:col_count]`; otherwise yields as-is.
- Ensures `cursor.close()` is called in a finally block regardless of iteration completion.

---

## django/db/models/sql/query.py
Now I have the complete file content. Let me compile the full natural-language specification.

---

## Module-Level Preamble

### Imports

```python
import difflib
import functools
import inspect
import sys
import warnings
from collections import Counter, namedtuple
from collections.abc import Iterator, Mapping
from itertools import chain, count, product
from string import ascii_uppercase

from django.core.exceptions import (EmptyResultSet, FieldDoesNotExist, FieldError)
from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections
from django.db.models.aggregates import Count
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import (BaseExpression, Col, F, OuterRef, Ref, SimpleCol)
from django.db.models.fields import Field
from django.db.models.fields.related_lookups import MultiColSource
from django.db.models.lookups import Lookup
from django.db.models.query_utils import (Q, check_rel_lookup_compatibility, refs_expression)
from django.db.models.sql.constants import (INNER, LOUTER, ORDER_DIR, ORDER_PATTERN, SINGLE)
from django.db.models.sql.datastructures import (BaseTable, Empty, Join, MultiJoin)
from django.db.models.sql.where import (AND, OR, ExtraWhere, NothingNode, WhereNode)
from django.utils.deprecation import RemovedInDjango40Warning
from django.utils.functional import cached_property
from django.utils.tree import Node
```

### Constants & Globals

- `__all__ = ['Query', 'RawQuery']` — exported symbols.
- `JoinInfo = namedtuple('JoinInfo', ('final_field', 'targets', 'opts', 'joins', 'path', 'transform_function'))` — a 6-field named tuple used to return join resolution results from `setup_joins()`.

### Module-Level Functions

**`get_field_names_from_opts(opts)`**: Returns a set of all field names and attname pairs for concrete fields in `opts.get_fields()`; for non-concrete fields, only the name is included. Uses `chain.from_iterable` over the generator `(f.name, f.attname) if f.concrete else (f.name,)`.

**`get_children_from_q(q)`**: Generator that recursively yields leaf children from a Q-object tree (`q.children`). If a child is itself a `Node`, recurses; otherwise yields it directly.

**`_get_col(target, field, alias, simple_col)`**: Returns either `SimpleCol(target, field)` if `simple_col` is truthy, or calls `target.get_col(alias, field)`.

**`get_order_dir(field, default='ASC')`**: Parses an ordering specification string. If it starts with `'-'`, strips the prefix and returns `(field[1:], dirn[1])` where `dirn = ORDER_DIR[default]`; otherwise returns `(field, dirn[0])`.

**`add_to_dict(data, key, value)`**: Adds `value` to a set at `data[key]`, creating the set if the key doesn't exist.

**`is_reverse_o2o(field)`**: Returns `True` if `field.is_relation and field.one_to_one and not field.concrete`.

---

## Code Objects

### Class `RawQuery`

A single raw SQL query, providing a minimal interface compatible with Django's compiler for result processing.

**Attributes (set in `__init__`):**
- `params`: tuple or dict of query parameters; defaults to `()` if None.
- `sql`: the raw SQL string.
- `using`: database alias string.
- `cursor`: initially `None`, set by `_execute_query()`.
- `low_mark, high_mark`: both initialized to `0, None` (offset/limit).
- `extra_select`: empty dict `{}`.
- `annotation_select`: empty dict `{}`.

**Methods:**

1. **`__init__(self, sql, using, params=None)`**: Initializes all attributes above.

2. **`chain(self, using)`**: Returns `self.clone(using)`.

3. **`clone(self, using)`**: Returns a new `RawQuery(sql, using, params=self.params)`.

4. **`get_columns(self)`**: If `self.cursor is None`, calls `_execute_query()`. Then returns a list of column names from `self.cursor.description`, each passed through `connections[self.using].introspection.identifier_converter`.

5. **`__iter__(self)`**: Executes the query via `_execute_query()`. If the database connection's `features.can_use_chunked_reads` is False, materializes all rows into a list; otherwise returns the cursor directly. Returns `iter(result)`.

6. **`__repr__(self)`**: Returns `"<RawQuery: %s>" % self`.

7. **`params_type` (property)**: Returns `dict` if `isinstance(self.params, Mapping)`, else `tuple`.

8. **`__str__(self)`**: Returns `self.sql % self.params_type(self.params)`.

9. **`_execute_query(self)`**: Gets the connection via `connections[self.using]`. Adapts parameters using `connection.ops.adapt_unknown_value`: if params is a tuple, adapts each element; if dict, adapts each value; otherwise raises `RuntimeError`. Creates a cursor and executes `self.sql` with adapted params.

---

### Class `Query(BaseExpression)`

A single SQL query builder. Inherits from `BaseExpression`.

**Class-level attributes:**
- `alias_prefix = 'T'` — prefix for generated aliases.
- `subq_aliases = frozenset([alias_prefix])` — set of alias prefixes used by subqueries to avoid conflicts.
- `compiler = 'SQLCompiler'` — compiler class name.

**Instance Attributes (set in `__init__`):**
- `model`: the model class for this query.
- `alias_refcount`: dict mapping alias → reference count; initially `{}`.
- `alias_map`: dict mapping alias → `Join` or `BaseTable` datastructure; records which joins exist and their types. Initially `{}`.
- `external_aliases`: set of aliases from outer queries (for correct quoting); initially `set()`.
- `table_map`: dict mapping table name → list of aliases for that table; initially `{}`.
- `default_cols = True` — whether to select default model columns.
- `default_ordering = True` — whether to use the model's default ordering.
- `standard_ordering = True` — whether standard (ASC/DESC) ordering applies.
- `used_aliases`: set of aliases used in previous filter operations; initially `set()`.
- `filter_is_sticky = False`.
- `subquery = False`.
- `select`: tuple of expressions for the SELECT clause; initially `()`.
- `where`: a `WhereNode` instance (type determined by `where_class` parameter); created via `where()`.
- `where_class`: the class to use for where nodes, defaults to `WhereNode`.
- `group_by`: None (no GROUP BY), a tuple of expressions, or True (group by all select fields).
- `order_by`: tuple of ordering specs; initially `()`.
- `low_mark, high_mark`: both `0, None` for offset/limit.
- `distinct = False`.
- `distinct_fields = ()` — fields for DISTINCT ON.
- `select_for_update = False`.
- `select_for_update_nowait = False`.
- `select_for_update_skip_locked = False`.
- `select_for_update_of = ()`.
- `select_related = False`.
- `max_depth = 5` — recursion limit for select_related.
- `values_select`: tuple of field names from `values()`/`values_list()`, excluding annotations and extras; initially `()`.
- `annotations`: dict mapping alias → Annotation Expression; initially `{}`.
- `annotation_select_mask`: None or set of annotation aliases to include in SELECT.
- `_annotation_select_cache`: cached result of `annotation_select`; initially None.
- `combinator`: None, or a string for UNION/INTERSECT/EXCEPT operations.
- `combinator_all = False` — whether ALL is used with the combinator.
- `combined_queries`: tuple of Query objects to combine; initially `()`.
- `extra`: dict mapping col_alias → `(col_sql, params)` for user-supplied SQL extensions; initially `{}`.
- `extra_select_mask`: None or set of extra select aliases to include.
- `_extra_select_cache`: cached result of `extra_select`; initially None.
- `extra_tables`: tuple of table names for extras; initially `()`.
- `extra_order_by`: tuple of ordering specs from extras; initially `()`.
- `deferred_loading`: tuple `(frozenset(), True)` — (field_names, defer_mode). True means "defer these"; False means "load only these".
- `_filtered_relations`: dict mapping alias → FilteredRelation; initially `{}`.
- `explain_query = False`, `explain_format = None`, `explain_options = {}`.

**Properties:**

1. **`output_field`**: If `len(self.select) == 1`, returns `self.select[0].field`; elif `len(self.annotation_select) == 1`, returns the single annotation's `output_field`; else None.

2. **`has_select_fields`**: Returns `bool(self.select or self.annotation_select_mask or self.extra_select_mask)`.

3. **`base_table`** (`@cached_property`): Iterates over keys of `self.alias_map` and returns the first alias found (the root table).

4. **`annotation_select`** (property, cached): Returns annotations not masked out. If `_annotation_select_cache` is set, returns it; if no annotations exist, returns `{}`; if `annotation_select_mask` is a set, filters to only those aliases; otherwise returns all of `self.annotations`.

5. **`extra_select`** (property, cached): Returns extras not masked out. If `_extra_select_cache` is set, returns it; if no extras exist, returns `{}`; if `extra_select_mask` is a set, filters to only those aliases; otherwise returns all of `self.extra`.

**Methods:**

1. **`__str__(self)`**: Calls `self.sql_with_params()` and returns `sql % params`.

2. **`sql_with_params(self)`**: Returns `(sql, params)` from `self.get_compiler(DEFAULT_DB_ALIAS).as_sql()`.

3. **`__deepcopy__(self, memo)`**: Calls `self.clone()` and stores result in `memo[id(self)]`, returns it.

4. **`get_compiler(self, using=None, connection=None)`**: Requires either `using` or `connection`. If `using`, resolves the connection via `connections[using]`. Returns `connection.ops.compiler(self.compiler)(self, connection, using)`.

5. **`get_meta(self)`**: Returns `self.model._meta`.

6. **`clone(self)`**: Creates a lightweight copy: sets `obj.__class__ = self.__class__`, copies `__dict__`, then deep-copies mutable structures (`alias_refcount`, `alias_map`, `external_aliases`, `table_map`, `where.clone()`, `annotations`, `annotation_select_mask`, `extra`, `extra_select_mask`, `_extra_select_cache` if not None, `subq_aliases` if present, `used_aliases`, `_filtered_relations`). Clears `_annotation_select_cache = None`. Deletes cached `base_table` property if it exists. Returns the copy.

7. **`chain(self, klass=None)`**: Calls `self.clone()`. If `klass` is given and differs from current class, changes `obj.__class__ = klass`. Resets `used_aliases = set()` and `filter_is_sticky = False` unless sticky. Calls `_setup_query()` if the object has that attribute. Returns the copy.

8. **`relabeled_clone(self, change_map)`**: Returns `self.clone().change_aliases(change_map)`.

9. **`rewrite_cols(self, annotation, col_cnt)`**: Ensures columns referenced by an aggregate expression are present in the inner query's SELECT clause when aggregating over annotations or related model columns. Iterates over `annotation.get_source_expressions()`:
   - If expr is a `Ref`, appends it as-is.
   - If expr is a `WhereNode` or `Lookup`, recursively calls `rewrite_cols()` on it and appends the result.
   - Otherwise, checks if any existing annotation matches the expression; if so, wraps in `Ref(col_alias, expr)`.
   - If not found and expr is a `Col` or contains aggregate but is not summary: increments `col_cnt`, creates alias `'__col%d' % col_cnt`, adds expr to `self.annotations[col_alias]`, appends to annotation mask via `append_annotation_mask([col_alias])`, wraps in `Ref(col_alias, expr)`.
   - Otherwise, recursively rewrites subexpressions.
   Sets new expressions on the annotation and returns `(annotation, col_cnt)`.

10. **`get_aggregation(self, using, added_aggregate_names)`**: Returns a dict of aggregation results. If no `self.annotation_select`, returns `{}`. Checks if there's a limit (`low_mark != 0 or high_mark is not None`). Filters existing annotations to those not in `added_aggregate_names`. If GROUP BY tuple exists, has limit, has existing annotations, distinct, or combinator: wraps the query in an outer `AggregateQuery` subquery. Clears ordering/limits/select_for_update/select_related on the outer query. Executes via compiler with `SINGLE`, applies converters, returns zipped dict. Otherwise (no wrapping needed), clears select/default_cols/extra on self, executes directly.

11. **`get_count(self, using)`**: Clones self, adds annotation `Count('*')` as `'__count'` with `is_summary=True`, calls `get_aggregation(using, ['__count'])['__count']`. Returns 0 if None.

12. **`has_filters(self)`**: Returns `self.where` (truthy if where clause has content).

13. **`has_results(self, using)`**: Clones self. If not distinct and group_by is True, adds concrete field names and calls `set_group_by()`. Clears select clause, clears ordering, sets limit to high=1. Gets compiler and returns `compiler.has_results()`.

14. **`explain(self, using, format=None, **options)`**: Clones self, sets `explain_query=True`, `explain_format=format`, `explain_options=options`. Gets compiler and returns `'\n'.join(compiler.explain_query())`.

15. **`combine(self, rhs, connector)`**: Merges `rhs` query into self with the given connector (AND/OR). Asserts models match, can_filter(), distinct flags match, and distinct_fields match. Computes a `change_map` for relabeling RHS aliases. For AND: creates empty reuse set; for OR: reuses all existing aliases. Gets initial alias. Creates `JoinPromoter(connector, 2, False)`. Adds votes from inner joins in self's alias_map. Iterates over RHS tables (skipping base), relabels each join via `change_map`, joins into self with reuse, tracks new aliases and votes. Relabels a copy of RHS where-clause and adds to self's where with connector. Copies RHS select/extra/ordering into self per the merge rules. For OR: raises ValueError if both sides have extra(select). Updates `extra_tables`. Sets ordering from rhs or keeps self's.

16. **`deferred_to_data(self, target, callback)`**: Converts `self.deferred_loading` data to a structure describing which fields will be loaded. Splits field names by `LOOKUP_SEP`, traverses the relation path tracking models and required fields (must_include). For each field in the deferred list: resolves through filtered relations if needed, tracks intermediate model joins, adds pk and reference fields to must_include. If defer mode is True: builds a workset of non-selected concrete fields per model, merges must_include into it, calls callback for each model's loaded fields. If defer mode is False: merges must_include into seen sets, ensures all parent models in the inheritance chain are mentioned, calls callback for each.

17. **`table_alias(self, table_name, create=False, filtered_relation=None)`**: Returns an alias for a table. If `create=False` and there's an existing alias list in `self.table_map`, reuses the first one (increments refcount). Otherwise creates a new alias: if the table already has aliases, generates `'%s%d' % (self.alias_prefix, len(self.alias_map) + 1)`; otherwise uses `filtered_relation.alias` or `table_name`. Adds to `table_map`, sets refcount to 1. Returns `(alias, True)` for new, `(alias, False)` for reused.

18. **`ref_alias(self, alias)`**: Increments `self.alias_refcount[alias]` by 1.

19. **`unref_alias(self, alias, amount=1)`**: Decrements `self.alias_refcount[alias]` by `amount`.

20. **`promote_joins(self, aliases)`**: Promotes join types of given aliases and their children to LOUTER (outer join). Iterates through aliases: skips base table (None join_type). If the join is nullable or parent is LOUTER and not already LOUTER, promotes it via `join.promote()`. Then recursively adds child joins (those whose `parent_alias` equals this alias) for further promotion.

21. **`demote_joins(self, aliases)`**: Changes LOUTER joins to INNER for given aliases. Iterates: if join is LOUTER, demotes via `join.demote()`. If parent is INNER, adds parent to the queue for recursive demotion (to avoid LOUTER→INNER chains).

22. **`reset_refcounts(self, to_counts)`**: For each alias in `self.alias_refcount`, computes `unref_amount = cur - to_counts.get(alias, 0)`, calls `unref_alias(alias, unref_amount)`.

23. **`change_aliases(self, change_map)`**: Relabels aliases per the mapping (old→new). Updates where clause via `relabel_aliases(change_map)`. Relabels group_by expressions, select columns, and annotations. Renames entries in `alias_map`, `alias_refcount`, and `table_map`. Updates `external_aliases` by applying the change map to each element.

24. **`bump_prefix(self, outer_query)`**: Changes `self.alias_prefix` to avoid conflicts with `outer_query`. Generates new prefixes alphabetically (`'A', 'B', ...`, then `'AA', 'AB', ...`). Skips prefixes already in `subq_aliases`. Raises `RecursionError` if exceeded `sys.getrecursionlimit() // 16`. Updates both queries' `subq_aliases`. Relabels all aliases using the new prefix format.

25. **`get_initial_alias(self)`**: Returns the first alias, increasing its refcount. If `alias_map` is non-empty, returns `self.base_table` with ref incremented; otherwise joins a `BaseTable(self.get_meta().db_table, None)`.

26. **`count_active_tables(self)`**: Returns count of aliases in `alias_refcount` with nonzero values.

27. **`join(self, join, reuse=None, reuse_with_filtered_relation=False)`**: Returns an alias for a join, reusing if possible. If `reuse_with_filtered_relation`, finds matching joins among those in the reuse set via `equals(join, ...)`. Otherwise finds any matching join where `a in reuse or reuse is None` and `j == join`. Reuses the most recent alias (or `join.table_alias` if it's in the list), increments refcount. If no reuse: creates a new alias via `table_alias()`, determines join type as LOUTER if parent is LOUTER or join is nullable, else INNER; sets `join.join_type = join_type`; stores in `alias_map`.

28. **`join_parent_model(self, opts, model, alias, seen)`**: Ensures a model is joined for inheritance chains. If model already in `seen`, returns its alias. Gets the chain from opts to model via `get_base_chain(model)`. Iterates through intermediate models: if already in `seen`, updates curr_opts and alias; if proxy (no parent link), skips to next base. Otherwise, calls `setup_joins([link_field.name], ...)` for the ancestor link field, joins it, stores alias in `seen[int_model]`. Returns final alias or `seen[None]` if no-op.

29. **`add_annotation(self, annotation, alias, is_summary=False)`**: Resolves the annotation expression via `annotation.resolve_expression(self, allow_joins=True, reuse=None, summarize=is_summary)`, appends to annotation mask, stores in `self.annotations[alias]`.

30. **`resolve_expression(self, query, *args, **kwargs)`**: Clones self, bumps prefix for subquery alias isolation, sets `subquery = True`. Clears ordering if no limit/distinct/select_for_update. Resolves where clause and all annotations (updating `external_aliases` on resolved expressions that have it). Adds outer query's join aliases to `clone.external_aliases` based on whether they reference different tables. Returns the clone.

31. **`as_sql(self, compiler, connection)`**: Gets SQL via `self.get_compiler(connection=connection).as_sql()`. If `self.subquery`, wraps in parentheses: `'(%s)' % sql`. Returns `(sql, params)`.

32. **`resolve_lookup_value(self, value, can_reuse, allow_joins, simple_col)`**: If value has `resolve_expression`, resolves it (passing `simple_col` for F expressions). If value is a list/tuple, resolves each sub-expression independently. Returns the resolved value.

33. **`solve_lookup_type(self, lookup)`**: Splits lookup by `LOOKUP_SEP`. Checks if any annotation matches via `refs_expression()`. Calls `names_to_path()` to resolve field parts. Returns `(lookup_parts, field_parts, reffed_expression)`. Raises `FieldError` for invalid multi-part lookups on non-field paths.

34. **`check_query_object_type(self, value, opts, field)`**: If value has `_meta`, checks compatibility via `check_rel_lookup_compatibility()`, raises `ValueError` if incompatible.

35. **`check_related_objects(self, field, value, opts)`**: For relation fields: if value is a Query without select fields, checks model compatibility; if value has `_meta`, calls `check_query_object_type`; if iterable, recursively checks each element.

36. **`build_lookup(self, lookups, lhs, rhs)`**: Extracts transforms and lookup from the list. Default lookup is `'exact'`. Applies each transform via `try_transform()`. Gets lookup class from `lhs.get_lookup(lookup_name)`. If not found and field is relational, raises `FieldError`; otherwise tries interpreting as a transform with exact lookup. Creates `Lookup(lhs, rhs)`. Handles None RHS: if lookup isn't `'exact'`/`'iexact'`, raises ValueError; returns `isnull(True)` for exact/iexact. For Oracle (empty strings as null), converts `''` exact lookups to `isnull(True)`. Returns the Lookup instance or None.

37. **`try_transform(self, lhs, name)`**: Gets transform class from `lhs.get_transform(name)`. If found, returns `transform_class(lhs)`. Otherwise, suggests close matches via `difflib.get_close_matches()` and raises `FieldError`.

38. **`build_filter(self, filter_expr, branch_negated=False, current_negated=False, can_reuse=None, allow_joins=True, split_subq=True, reuse_with_filtered_relation=False, simple_col=False)`**: Builds a WhereNode for a single filter clause without adding it to the query. Parses `filter_expr` into `(arg, value)`. Solves lookup type via `solve_lookup_type()`. Checks if the referenced expression is filterable. Validates `allow_joins` constraint on parts count. Resolves lookup values. Records pre-join refcounts to track used joins. If referencing an annotation/expression: builds lookup directly and returns. Otherwise, gets initial alias, calls `setup_joins()` for the field path. Handles `Iterator` values by materializing them. Checks related object compatibility. Catches `MultiJoin` and delegates to `split_exclude()`. Trims joins via `trim_joins()`, updates `can_reuse`. Builds a column (`_get_col` or `MultiColSource`), then builds the lookup. Handles `isnull=True` and negated conditions by adding extra IS NULL clauses for proper SQL null handling. Returns `(clause, used_joins)` — joins are returned empty if outer join is required.

39. **`add_filter(self, filter_clause)`**: Calls `self.add_q(Q(**{filter_clause[0]: filter_clause[1]}))`.

40. **`add_q(self, q_object)`**: Preprocessor for `_add_q()`. Collects existing inner joins before processing. Calls `_add_q(q_object, self.used_aliases)`. If a clause is returned, adds it to `self.where` with AND connector. Demotes existing inner joins via `demote_joins(existing_inner)`.

41. **`build_where(self, q_object)`**: Returns the result of `_add_q(q_object, used_aliases=set(), allow_joins=False, simple_col=True)[0]`.

42. **`_add_q(self, q_object, used_aliases, branch_negated=False, current_negated=False, allow_joins=True, split_subq=True, simple_col=False)`**: Recursively adds a Q-object to the filter. Computes effective negation via XOR. Creates target clause with appropriate connector/negation. Creates `JoinPromoter` for tracking join votes. For each child: if it's a Node, recursively calls `_add_q`; otherwise calls `build_filter()`. Adds votes from needed_inner joins. Adds child clauses to target with the connector. Calls `joinpromoter.update_join_types(self)` to promote/demote joins. Returns `(target_clause, needed_inner)`.

43. **`build_filtered_relation_q(self, q_object, reuse, branch_negated=False, current_negated=False)`**: Similar to `_add_q()` but for FilteredRelation objects. Uses `reuse_with_filtered_relation=True` and `split_subq=False` in build_filter calls. Recursively processes child Nodes via itself or leaf filters via `build_filter()`. Returns the target clause.

44. **`add_filtered_relation(self, filtered_relation, alias)`**: Sets `filtered_relation.alias = alias`. Validates that no nested relations exist beyond one level by checking lookup parts against field parts for all lookups in the condition and the relation name. Stores in `self._filtered_relations[alias]`.

45. **`names_to_path(self, names, opts, allow_many=True, fail_on_missing=False)`**: Walks a list of field names to produce PathInfo tuples. Handles `'pk'` → pk field name. Checks filtered relations at position 0. For each name: gets the field from opts or annotations; checks for GenericForeignKey compatibility; handles concrete inheritance by adding path-to-parent joins. If the field has `get_path_info()`, follows relation paths, raising `MultiJoin` on m2m if `allow_many=False`. Otherwise treats as a local non-relational field. Returns `(path, final_field, targets, remaining_names)`.

46. **`setup_joins(self, names, opts, alias, can_reuse=None, allow_many=True, reuse_with_filtered_relation=False)`**: Computes necessary table joins for the given field path. Iterates over pivot points to resolve transforms vs. fields. Builds a `final_transformer` that wraps fields through any transforms found. For each join in the resolved path: creates a `Join` datastructure (INNER by default, nullable based on field type), calls `self.join()` with reuse logic for m2m/filtered relations. Tracks filtered relation paths. Returns a `JoinInfo(final_field, targets, opts, joins, path, final_transformer)`.

47. **`trim_joins(self, targets, joins, path)`**: Trims unnecessary trailing joins from the join chain. Works backwards through the path: if the target column is already in the previous table (target columns are a subset of foreign-related fields), unrefs and pops the alias. Stops at reverse joins or filtered relations. Returns `(targets, final_alias, remaining_joins)`.

48. **`resolve_ref(self, name, allow_joins=True, reuse=None, summarize=False, simple_col=False)`**: Resolves a reference (annotation name or field path) to a column expression. If `allow_joins=False` and name contains LOOKUP_SEP, raises FieldError. If the name is an annotation: returns it directly, or a `Ref()` if summarizing. Otherwise, calls `setup_joins()` on the field list, trims joins, verifies multicolumn restriction, applies transform function, gets column via `_get_col()`, updates reuse set.

49. **`split_exclude(self, filter_expr, can_reuse, names_with_path)`**: Constructs a subquery for exclude operations on N-to-many relations. Creates an inner `Query`, adds the filter expression (converting F to OuterRef), clears ordering. Trims leading joins via `trim_start()`. Adds IS NULL check if the selected field is nullable. If the alias can be reused, adds a self-join restriction using pk comparison and registers the outer alias as external. Builds an `IN` subquery filter with negation. For queries containing LOUTER joins, also adds an OR condition for IS NULL on the trimmed prefix. Returns `(condition, needed_inner)`.

50. **`set_empty(self)`**: Adds a `NothingNode()` to the where clause (produces always-false query).

51. **`is_empty(self)`**: Returns True if any child of `self.where` is a `NothingNode`.

52. **`set_limits(self, low=None, high=None)`**: Adjusts row limits. For high: clamps to existing high_mark or adds to low_mark. For low: clamps to high_mark or adds to current low_mark. If low equals high after adjustment, calls `set_empty()`.

53. **`clear_limits(self)`**: Resets `low_mark=0`, `high_mark=None`.

54. **`has_limit_one(self)`**: Returns True if `high_mark is not None and (high_mark - low_mark) == 1`.

55. **`can_filter(self)`**: Returns True if no limits have been taken (`not self.low_mark and self.high_mark is None`).

56. **`clear_select_clause(self)`**: Clears select, sets `default_cols=False`, `select_related=False`, clears extra mask and annotation mask.

57. **`clear_select_fields(self)`**: Sets `select=()` and `values_select=()`.

58. **`set_select(self, cols)`**: Sets `default_cols=False` and `self.select = tuple(cols)`.

59. **`add_distinct_fields(self, *field_names)`**: Sets `distinct_fields = field_names` and `distinct = True`.

60. **`add_fields(self, field_names, allow_m2m=True)`**: Adds model fields to the select set. Gets initial alias and opts. For each name: calls `setup_joins()`, trims joins, creates columns via `transform_function(target, final_alias)`. Sets select if columns were added. Handles MultiJoin/FieldError with appropriate messages.

61. **`add_ordering(self, *ordering)`**: Validates ordering items against `ORDER_PATTERN` regex and checks for aggregates without annotation inclusion. If errors found, raises FieldError. Appends to `self.order_by`; if empty, sets `default_ordering=False`.

62. **`clear_ordering(self, force_empty)`**: Sets `order_by=()` and `extra_order_by=()`. If `force_empty`, also sets `default_ordering=False`.

63. **`set_group_by(self)`**: Expands GROUP BY from select columns plus annotation group-by columns. Calls each annotation's `get_group_by_cols(alias=alias)`, with a deprecation warning for the old signature (no alias parameter). Sets `self.group_by = tuple(group_by)`.

64. **`add_select_related(self, fields)`**: Builds a nested dict structure from field paths (split by LOOKUP_SEP), storing in `self.select_related`. If currently a bool, initializes to `{}` first.

65. **`add_extra(self, select, select_params, where, params, tables, order_by)`**: Adds user-supplied SQL extensions. For select: pairs each entry with parameters from `select_params`, handling `%s` placeholders (skipping escaped `%%`). Updates `self.extra`. Adds ExtraWhere to the where clause if where/params provided. Appends table names to `extra_tables`. Sets `extra_order_by`.

66. **`clear_deferred_loading(self)`**: Resets `deferred_loading = (frozenset(), True)`.

67. **`add_deferred_loading(self, field_names)`**: Adds field names to the deferred loading set. If defer mode is True, unions with existing; if False, removes from immediate-loading set.

68. **`add_immediate_loading(self, field_names)`**: Sets fields for immediate (non-deferred) loading. Replaces `'pk'` with `model._meta.pk.name`. If defer mode was True, removes deferred names from the new set; otherwise replaces existing immediate set.

69. **`get_loaded_field_names(self)`**: Returns a dict mapping models to sets of loaded field attname strings (computed from deferred loading). Caches result in `_loaded_field_names_cache`, computed via `deferred_to_data()` with `get_loaded_field_names_cb`.

70. **`get_loaded_field_names_cb(self, target, model, fields)`**: Callback for deferred_to_data: sets `target[model] = {f.attname for f in fields}`.

71. **`set_annotation_mask(self, names)`**: Sets the annotation select mask to a set of names (or None). Clears `_annotation_select_cache`.

72. **`append_annotation_mask(self, names)`**: If mask exists, updates it with `self.annotation_select_mask.union(names)`.

73. **`set_extra_mask(self, names)`**: Sets the extra select mask to a set of names (or None). Clears `_extra_select_cache`.

74. **`set_values(self, fields)`**: Prepares for values()/values_list() queries. Disables select_related, clears deferred loading and select fields. If group_by is True, adds concrete fields and sets group-by before clearing again. Categorizes field names into extra/annotation/field groups based on what's in self.extra and self.annotations. Sets masks accordingly. If no fields given, uses all concrete model field attname strings. Sets `values_select` tuple and calls `add_fields(field_names)`.

75. **`trim_start(self, names_with_path)`**: Trims leading joins from the join path for subquery generation in split_exclude(). Identifies m2m join positions to determine trim point. Unrefs trimmed aliases. Builds a trimmed prefix string from field names and foreign key references. Handles LOUTER vs INNER first-join cases differently for select fields. Resets the base table entry (from Join to BaseTable). Sets select to the appropriate related-field columns. Returns `(trimmed_prefix, contains_louter)`.

76. **`is_nullable(self, field)`**: Returns True if the database interprets empty strings as null AND the field allows them, OR if `field.null` is True. Uses `DEFAULT_DB_ALIAS` for backend feature check.

---

### Class `JoinPromoter`

A class to manage join promotion/demotion decisions for complex filter conditions (Q-objects with AND/OR).

**Attributes (set in `__init__`):**
- `connector`: the Q-object's connector ('AND' or 'OR').
- `negated`: whether the Q-object is negated.
- `effective_connector`: if negated, flips AND↔OR; otherwise same as connector.
- `num_children`: number of children in the Q-object.
- `votes`: a `Counter()` mapping table alias → vote count (how many times it's needed for inner/outer joins).

**Methods:**

1. **`__init__(self, connector, num_children, negated)`**: Sets up all attributes above. Computes effective_connector based on negation logic.

2. **`add_votes(self, votes)`**: Updates `self.votes` with the given iterable (one vote per item).

3. **`update_join_types(self, query)`**: Determines which aliases to promote to LOUTER and which to demote to INNER:
   - For OR effective_connector: if a table's votes < num_children, it must be promoted (not present in all branches → need outer join to preserve rows).
   - For AND effective_connector, or for OR where votes == num_children: the table can be demoted to INNER (all branches require it, so no rows would be lost).
   Calls `query.promote_joins(to_promote)` and `query.demote_joins(to_demote)`. Returns `to_demote`.