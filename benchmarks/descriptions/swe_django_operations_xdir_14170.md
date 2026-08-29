## django/db/backends/base/operations.py
Here is the complete natural-language specification of `django/db/backends/base/operations.py`:

---

## Module-Level Preamble

### Imports
```python
import datetime
import decimal
from importlib import import_module

import sqlparse

from django.conf import settings
from django.db import NotSupportedError, transaction
from django.db.backends import utils
from django.utils import timezone
from django.utils.encoding import force_str
```

### Constants & Class-Level Attributes (on `BaseDatabaseOperations`)

- **`compiler_module = "django.db.models.sql.compiler"`** — string; module path from which SQL compiler classes are dynamically loaded.
- **`integer_field_ranges`** — dict mapping field internal type names to `(min, max)` tuples:
  - `'SmallIntegerField'`: `(-32768, 32767)`
  - `'IntegerField'`: `(-2147483648, 2147483647)`
  - `'BigIntegerField'`: `(-9223372036854775808, 9223372036854775807)`
  - `'PositiveBigIntegerField'`: `(0, 9223372036854775807)`
  - `'PositiveSmallIntegerField'`: `(0, 32767)`
  - `'PositiveIntegerField'`: `(0, 2147483647)`
  - `'SmallAutoField'`: `(-32768, 32767)`
  - `'AutoField'`: `(-2147483648, 2147483647)`
  - `'BigAutoField'`: `(-9223372036854775808, 9223372036854775807)`
- **`set_operators`** — dict mapping operator names to SQL keywords: `{'union': 'UNION', 'intersection': 'INTERSECT', 'difference': 'EXCEPT'}`.
- **`cast_data_types = {}`** — empty dict; overrides for `Cast()` function data types per backend.
- **`cast_char_field_without_max_length = None`** — default char field type when no `max_length`.
- **Window expression constants:**
  - `PRECEDING = 'PRECEDING'`
  - `FOLLOWING = 'FOLLOWING'`
  - `UNBOUNDED_PRECEDING = 'UNBOUNDED PRECEDING'`
  - `UNBOUNDED_FOLLOWING = 'UNBOUNDED FOLLOWING'`
  - `CURRENT_ROW = 'CURRENT ROW'`
- **`explain_prefix = None`** — prefix string for EXPLAIN queries, or `None` if unsupported.

---

## Code Objects (Class and Methods)

### Class: `BaseDatabaseOperations`

Encapsulates backend-specific SQL generation differences (ordering, ID retrieval, date/time handling, etc.).

#### `__init__(self, connection)`
- Stores the passed database `connection` object as `self.connection`.
- Initializes `self._cache = None` (lazy cache for compiler module imports).

---

#### `autoinc_sql(self, table, column)`
- Returns `None`. Subclasses override to return SQL needed for auto-incrementing primary keys at table creation.

#### `bulk_batch_size(self, fields, objs)`
- Returns `len(objs)`. Maximum allowed batch size for bulk inserts given the field list and object list.

#### `cache_key_culling_sql(self)`
- Returns the string: `"SELECT cache_key FROM %s ORDER BY cache_key LIMIT 1 OFFSET %%s"`. Used by the 'db' cache backend to determine cull start position.

#### `unification_cast_sql(self, output_field)`
- Returns `'%s'` (a placeholder). SQL fragment to cast union results to a given field type; contains `%s` for the expression being cast.

#### `date_extract_sql(self, lookup_type, field_name)`
- Raises `NotImplementedError`. Extracts a date component (`year`, `month`, `day`) from `field_name`. Must be overridden by subclasses.

#### `date_trunc_sql(self, lookup_type, field_name, tzname=None)`
- Raises `NotImplementedError`. Truncates a date/datetime field to given specificity (`year`, `month`, `day`). Optional `tzname` for timezone-aware truncation.

#### `datetime_cast_date_sql(self, field_name, tzname)`
- Raises `NotImplementedError`. SQL to cast a datetime value to a date value.

#### `datetime_cast_time_sql(self, field_name, tzname)`
- Raises `NotImplementedError`. SQL to cast a datetime value to a time value.

#### `datetime_extract_sql(self, lookup_type, field_name, tzname)`
- Raises `NotImplementedError`. Extracts components (`year`, `month`, `day`, `hour`, `minute`, `second`) from a datetime field.

#### `datetime_trunc_sql(self, lookup_type, field_name, tzname)`
- Raises `NotImplementedError`. Truncates a datetime field to given specificity (`year` through `second`).

#### `time_trunc_sql(self, lookup_type, field_name, tzname=None)`
- Raises `NotImplementedError`. Truncates a time/datetime field to hour/minute/second. Optional `tzname`.

#### `time_extract_sql(self, lookup_type, field_name)`
- Delegates to `self.date_extract_sql(lookup_type, field_name)`. Extracts hour/minute/second from a time field by reusing date extraction logic.

#### `deferrable_sql(self)`
- Returns `''`. SQL fragment for making constraints "initially deferred" in CREATE TABLE.

#### `distinct_sql(self, fields, params)`
- If `fields` is truthy: raises `NotSupportedError` (DISTINCT ON not supported).
- Otherwise: returns `(['DISTINCT'], [])`.

#### `fetch_returned_insert_columns(self, cursor, returning_params)`
- Returns `cursor.fetchone()`. Retrieves data from an INSERT...RETURNING statement.

#### `field_cast_sql(self, db_type, internal_type)`
- Returns `'%s'`. SQL to cast a column before use in WHERE; contains `%s` placeholder for the column.

#### `force_no_ordering(self)`
- Returns `[]`. List used in ORDER BY clause to force no ordering (empty list = no clause).

#### `for_update_sql(self, nowait=False, skip_locked=False, of=(), no_key=False)`
- Returns a formatted string: `'FOR%s UPDATE%s%s%s'` with optional modifiers:
  - `' NO KEY'` if `no_key` is True.
  - `' OF %s'` joined from `of` tuple if non-empty.
  - `' NOWAIT'` if `nowait` is True.
  - `' SKIP LOCKED'` if `skip_locked` is True.

#### `_get_limit_offset_params(self, low_mark, high_mark)` *(private helper)*
- Computes `(limit, offset)` tuple:
  - `offset = low_mark or 0`.
  - If `high_mark` is not None: returns `(high_mark - offset, offset)`.
  - Else if `offset` is truthy: returns `(self.connection.ops.no_limit_value(), offset)`.
  - Otherwise: returns `(None, offset)` (i.e., `(None, 0)`).

#### `limit_offset_sql(self, low_mark, high_mark)`
- Calls `_get_limit_offset_params(low_mark, high_mark)` to get `(limit, offset)`.
- Returns a space-separated string of `'LIMIT %d'` and/or `'OFFSET %d'` clauses for non-null/non-zero values.

#### `last_executed_query(self, cursor, sql, params)`
- Defines inner function `to_string(s)` that calls `force_str(s, strings_only=True, errors='replace')`.
- Converts `params`: if list/tuple → tuple of stringified values; if None → empty tuple; else → dict with stringified keys and values.
- Returns `"QUERY = %r - PARAMS = %r" % (sql, u_params)`.

#### `last_insert_id(self, cursor, table_name, pk_name)`
- Returns `cursor.lastrowid`. Retrieves the auto-increment ID after an INSERT.

#### `lookup_cast(self, lookup_type, internal_type=None)`
- Returns `"%s"`. Cast string for lookups (contains `%s` placeholder).

#### `max_in_list_size(self)`
- Returns `None`. Maximum items in a single IN list condition; None means no limit.

#### `max_name_length(self)`
- Returns `None`. Maximum length of table/column names; None means no limit.

#### `no_limit_value(self)`
- Raises `NotImplementedError`. Value to use for LIMIT when requesting "LIMIT infinity"; subclasses must override.

#### `pk_default_value(self)`
- Returns `'DEFAULT'`. SQL value to specify default in INSERT statements.

#### `prepare_sql_script(self, sql)`
- Uses `sqlparse.split(sql)` and `sqlparse.format(statement, strip_comments=True)` for each non-empty statement.
- Returns a list of formatted individual SQL statements suitable for successive `cursor.execute()` calls.

#### `process_clob(self, value)`
- Returns `value` unchanged. Hook for processing CLOB locators that require additional handling.

#### `return_insert_columns(self, fields)`
- Returns `None` (via bare `pass`). SQL/params fragment to append RETURNING clause to INSERT; subclasses override.

#### `compiler(self, compiler_name)`
- If `self._cache is None`: imports the module at `self.compiler_module` and stores it in `self._cache`.
- Returns `getattr(self._cache, compiler_name)`. Dynamically loads a SQL compiler class by name.

#### `quote_name(self, name)`
- Raises `NotImplementedError`. Quotes table/index/column names; does not re-quote already-quoted names. Must be overridden.

#### `regex_lookup(self, lookup_type)`
- Raises `NotImplementedError`. Cast string for regex/iregex lookups (contains `%s` placeholder).

#### `savepoint_create_sql(self, sid)`
- Returns `"SAVEPOINT %s" % self.quote_name(sid)`. SQL to start a new savepoint.

#### `savepoint_commit_sql(self, sid)`
- Returns `"RELEASE SAVEPOINT %s" % self.quote_name(sid)`. SQL to commit a savepoint.

#### `savepoint_rollback_sql(self, sid)`
- Returns `"ROLLBACK TO SAVEPOINT %s" % self.quote_name(sid)`. SQL to roll back a savepoint.

#### `set_time_zone_sql(self)`
- Returns `''`. SQL to set the connection's timezone; empty string if unsupported.

#### `sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False)`
- Raises `NotImplementedError`. Must be overridden. Returns a list of SQL statements to remove all data from given tables (without dropping them). Parameters: `style` (coloring object), `tables`, optional `reset_sequences` and `allow_cascade`.

#### `execute_sql_flush(self, sql_list)`
- Opens an atomic transaction using `self.connection.alias`, with savepoint if `self.connection.features.can_rollback_ddl` is True.
- Iterates over `sql_list`, executing each SQL via `cursor.execute(sql)`.

#### `sequence_reset_by_name_sql(self, style, sequences)`
- Returns `[]`. SQL statements to reset sequences by name.

#### `sequence_reset_sql(self, style, model_list)`
- Returns `[]`. SQL statements to reset sequences for given models.

#### `start_transaction_sql(self)`
- Returns `"BEGIN;"`. SQL to start a transaction.

#### `end_transaction_sql(self, success=True)`
- If `success` is False: returns `"ROLLBACK;"`.
- Otherwise: returns `"COMMIT;"`.

#### `tablespace_sql(self, tablespace, inline=False)`
- Returns `''`. SQL for defining a tablespace; empty if unsupported. `inline` controls whether appended to row vs statement level.

#### `prep_for_like_query(self, x)`
- Converts `x` to string and escapes backslashes (`\` → `\\`), percent signs (`%` → `\%`), and underscores (`_` → `\_`). Returns the escaped string.

#### `prep_for_iexact_query = prep_for_like_query`
- Alias: same function as `prep_for_like_query`.

#### `validate_autopk_value(self, value)`
- Returns `value` unchanged. Raises `ValueError` if the serial field value is invalid (subclasses may override).

#### `adapt_unknown_value(self, value)`
- Dispatches by type:
  - `datetime.datetime` → calls `self.adapt_datetimefield_value(value)`.
  - `datetime.date` → calls `self.adapt_datefield_value(value)`.
  - `datetime.time` → calls `self.adapt_timefield_value(value)`.
  - `decimal.Decimal` → calls `self.adapt_decimalfield_value(value)`.
  - Otherwise: returns `value` unchanged.

#### `adapt_datefield_value(self, value)`
- If `value is None`: returns `None`.
- Otherwise: returns `str(value)`.

#### `adapt_datetimefield_value(self, value)`
- If `value is None`: returns `None`.
- Otherwise: returns `str(value)`.

#### `adapt_timefield_value(self, value)`
- If `value is None`: returns `None`.
- If `timezone.is_aware(value)` is True: raises `ValueError("Django does not support timezone-aware times.")`.
- Otherwise: returns `str(value)`.

#### `adapt_decimalfield_value(self, value, max_digits=None, decimal_places=None)`
- Returns `utils.format_number(value, max_digits, decimal_places)`. Formats a Decimal for the backend driver.

#### `adapt_ipaddressfield_value(self, value)`
- Returns `value or None`. Converts IP address string to expected backend type (None if falsy).

#### `year_lookup_bounds_for_date_field(self, value)`
- Creates `first = datetime.date(value, 1, 1)` and `second = datetime.date(value, 12, 31)`.
- Adapts both via `self.adapt_datefield_value()`.
- Returns `[first, second]` for use in a BETWEEN clause.

#### `year_lookup_bounds_for_datetime_field(self, value)`
- Creates `first = datetime.datetime(value, 1, 1)` and `second = datetime.datetime(value, 12, 31, 23, 59, 59, 999999)`.
- If `settings.USE_TZ` is True: makes both timezone-aware using `timezone.get_current_timezone()` and `timezone.make_aware()`.
- Adapts both via `self.adapt_datetimefield_value()`.
- Returns `[first, second]`.

#### `get_db_converters(self, expression)`
- Returns `[]`. List of converter functions for field data that arrives in incorrect format.

#### `convert_durationfield_value(self, value, expression, connection)`
- If `value is not None`: returns `datetime.timedelta(0, 0, value)`. Converts integer microseconds to a timedelta.
- Otherwise: implicitly returns `None`.

#### `check_expression_support(self, expression)`
- Does nothing (bare `pass`). Subclasses override to raise `NotSupportedError` for unsupported expressions.

#### `conditional_expression_supported_in_where_clause(self, expression)`
- Returns `True`. Whether a conditional expression is valid in WHERE clauses.

#### `combine_expression(self, connector, sub_expressions)`
- Joins `sub_expressions` list with `' %s '` (the `connector`). Returns the combined string.

#### `combine_duration_expression(self, connector, sub_expressions)`
- Delegates to `self.combine_expression(connector, sub_expressions)`. Same logic for duration expressions.

#### `binary_placeholder_sql(self, value)`
- Returns `'%s'`. Placeholder syntax for binary content (e.g., MySQL uses `_binary %s`).

#### `modify_insert_params(self, placeholder, params)`
- Returns `params` unchanged. Hook to modify insert parameters before execution.

#### `integer_field_range(self, internal_type)`
- Returns `self.integer_field_ranges[internal_type]`. Looks up the `(min, max)` tuple for a given integer field type.

#### `subtract_temporals(self, internal_type, lhs, rhs)`
- If `self.connection.features.supports_temporal_subtraction` is True: unpacks `lhs` and `rhs` as `(sql, params)` tuples; returns `'(%s - %s)'` with combined params `(*lhs_params, *rhs_params)`.
- Otherwise: raises `NotSupportedError("This backend does not support %s subtraction." % internal_type)`.

#### `window_frame_start(self, start)`
- If `start` is an int:
  - Negative → returns `'%d PRECEDING' % abs(start)`.
  - Zero → returns `'CURRENT ROW'`.
- If `start is None`: returns `'UNBOUNDED PRECEDING'`.
- Otherwise: raises `ValueError("start argument must be a negative integer, zero, or None, but got '%s'." % start)`.

#### `window_frame_end(self, end)`
- If `end` is an int:
  - Zero → returns `'CURRENT ROW'`.
  - Positive → returns `'%d FOLLOWING' % end`.
- If `end is None`: returns `'UNBOUNDED FOLLOWING'`.
- Otherwise: raises `ValueError("end argument must be a positive integer, zero, or None, but got '%s'." % end)`.

#### `window_frame_rows_start_end(self, start=None, end=None)`
- If `not self.connection.features.supports_over_clause`: raises `NotSupportedError('This backend does not support window expressions.')`.
- Returns `(self.window_frame_start(start), self.window_frame_end(end))` as a tuple of two SQL strings.

#### `window_frame_range_start_end(self, start=None, end=None)`
- Calls `self.window_frame_rows_start_end(start, end)` to get `(start_, end_)`.
- If `self.connection.features.only_supports_unbounded_with_preceding_and_following` is True **and** either `start < 0` or `end > 0`: raises `NotSupportedError('%s only supports UNBOUNDED together with PRECEDING and FOLLOWING.' % self.connection.display_name)`.
- Returns `(start_, end_)`.

#### `explain_query_prefix(self, format=None, **options)`
- If `not self.connection.features.supports_explaining_query_execution`: raises `NotSupportedError('This backend does not support explaining query execution.')`.
- If `format` is provided: normalizes to uppercase; checks against `self.connection.features.supported_explain_formats`; if not found, raises `ValueError` with message including allowed formats (if any).
- If `options` dict is non-empty: raises `ValueError('Unknown options: %s' % ', '.join(sorted(options.keys())))`.
- Returns `self.explain_prefix`.

#### `insert_statement(self, ignore_conflicts=False)`
- Returns `'INSERT INTO'`. Base INSERT SQL; subclasses may override for conflict handling variants.

#### `ignore_conflicts_suffix_sql(self, ignore_conflicts=None)`
- Returns `''`. Suffix appended when ignoring insert conflicts (e.g., `ON CONFLICT DO NOTHING`).

---

## django/db/models/lookups.py
Now I have the complete source. Here is the specification:

---

# Module Specification: `django/db/models/lookups.py`

## 1. Imports

```python
import itertools
import math
from copy import copy

from django.core.exceptions import EmptyResultSet
from django.db.models.expressions import Case, Exists, Func, Value, When
from django.db.models.fields import (
    CharField, DateTimeField, Field, IntegerField, UUIDField,
)
from django.db.models.query_utils import RegisterLookupMixin
from django.utils.datastructures import OrderedSet
from django.utils.functional import cached_property
from django.utils.hashable import make_hashable
```

## 2. Code Objects

### Class `Lookup`

**Base class for all field lookups.** No inheritance from other classes defined in this file.

**Class attributes:**
- `lookup_name = None` — string identifier for the lookup, overridden by subclasses.
- `prepare_rhs = True` — boolean; when `True`, the right-hand side value is passed through the LHS field's `get_prep_value()` during initialization.
- `can_use_none_as_rhs = False`

**`__init__(self, lhs, rhs)`:** Stores `lhs` and `rhs` as instance attributes. Then calls `self.get_prep_lookup()` to prepare/validate `rhs`, reassigning `self.rhs`. If `lhs` has a `get_bilateral_transforms()` method, those transforms are collected; otherwise an empty list is used. If bilateral transforms exist and `rhs` is a `Query` instance (imported from `django.db.models.sql.query`), raises `NotImplementedError("Bilateral transformations on nested querysets are not implemented.")`. Stores the transforms in `self.bilateral_transforms`.

**`apply_bilateral_transforms(self, value)`:** Iterates over `self.bilateral_transforms`, applying each transform to `value` sequentially (each is called as a callable: `transform(value)`), and returns the final result.

**`batch_process_rhs(self, compiler, connection, rhs=None)`:** If `rhs` is `None`, uses `self.rhs`. If bilateral transforms exist: for each element `p` in `rhs`, creates a `Value(p, output_field=self.lhs.output_field)`, applies bilateral transforms via `apply_bilateral_transforms()`, resolves it against `compiler.query`, compiles it with the compiler, and collects `(sql, params)` pairs. Returns `(sqls_list, sqls_params_list)`. If no bilateral transforms: calls `self.get_db_prep_lookup(rhs, connection)`, then creates a list of `%s` placeholders matching the number of parameters and returns `(placeholders, params)`.

**`get_source_expressions(self)`:** If `rhs_is_direct_value()` is `True`, returns `[self.lhs]`; otherwise returns `[self.lhs, self.rhs]`.

**`set_source_expressions(self, new_exprs)`:** If `len(new_exprs) == 1`, sets `self.lhs = new_exprs[0]`; else sets `self.lhs, self.rhs = new_exprs[0], new_exprs[1]`.

**`get_prep_lookup(self)`:** If `rhs` has a `resolve_expression` attribute (i.e., it is an expression), returns `rhs` unchanged. If `prepare_rhs` is `True` and `lhs.output_field` has a `get_prep_value` method, calls `self.lhs.output_field.get_prep_value(self.rhs)` and returns the result. Otherwise returns `self.rhs` as-is.

**`get_db_prep_lookup(self, value, connection)`:** Returns `('%s', [value])`. Default implementation for non-mixin lookups.

**`process_lhs(self, compiler, connection, lhs=None)`:** If `lhs` is `None`, uses `self.lhs`. If `lhs` has a `resolve_expression` attribute, resolves it against `compiler.query`. Then returns `(sql, params)` from `compiler.compile(lhs)`.

**`process_rhs(self, compiler, connection)`:** Starts with `value = self.rhs`. If bilateral transforms exist and `rhs_is_direct_value()` is `True`, wraps the value in `Value(value, output_field=self.lhs.output_field)`. Applies bilateral transforms, resolves against `compiler.query`. If the resulting `value` has an `as_sql` method, returns `(sql, params)` from `compiler.compile(value)`; otherwise calls and returns `self.get_db_prep_lookup(value, connection)`.

**`rhs_is_direct_value(self)`:** Returns `not hasattr(self.rhs, 'as_sql')`.

**`relabeled_clone(self, relabels)`:** Creates a shallow copy via `copy(self)`. Recursively calls `relabel_clone(relabels)` on the new object's `lhs`, and if its `rhs` also has `relabel_clone`, applies it to `rhs`. Returns the new object.

**`get_group_by_cols(self, alias=None)`:** Gets group-by columns from `self.lhs`; if `self.rhs` has `get_group_by_cols`, extends with those too. Returns the combined list.

**`as_sql(self, compiler, connection)`:** Raises `NotImplementedError`. Must be overridden by subclasses.

**`as_oracle(self, compiler, connection)`:** For Oracle compatibility: iterates over `(self.lhs, self.rhs)`; if any is an `Exists` instance, wraps it in `Case(When(expr, then=True), default=False)`, setting a `wrapped` flag. If wrapped, creates a new lookup of the same type with the modified expressions; otherwise uses `self`. Returns `lookup.as_sql(compiler, connection)`.

**`contains_aggregate` (cached_property):** Returns `self.lhs.contains_aggregate or getattr(self.rhs, 'contains_aggregate', False)`.

**`contains_over_clause` (cached_property):** Returns `self.lhs.contains_over_clause or getattr(self.rhs, 'contains_over_clause', False)`.

**`is_summary` (property):** Returns `self.lhs.is_summary or getattr(self.rhs, 'is_summary', False)`.

**`identity` (property):** Returns a tuple `(self.__class__, self.lhs, self.rhs)`.

**`__eq__(self, other)`:** If `other` is not an instance of `Lookup`, returns `NotImplemented`; otherwise compares `self.identity == other.identity`.

**`__hash__(self)`:** Returns `hash(make_hashable(self.identity))`.

---

### Class `Transform(RegisterLookupMixin, Func)`

**Base class for field transforms.** Inherits from `RegisterLookupMixin` (first, so `get_lookup()`/`get_transform()` checks self before output_field) and `Func`.

**Class attributes:**
- `bilateral = False` — whether this transform is applied bilaterally.
- `arity = 1` — number of arguments the function takes.

**`lhs` (property):** Returns `self.get_source_expressions()[0]`.

**`get_bilateral_transforms(self)`:** If `lhs` has `get_bilateral_transforms`, calls it to get existing transforms; otherwise starts with an empty list. If `self.bilateral` is `True`, appends `self.__class__` to the list. Returns the list.

---

### Class `BuiltinLookup(Lookup)`

**Base for built-in SQL operator lookups.**

**`process_lhs(self, compiler, connection, lhs=None)`:** Calls parent's `process_lhs()` to get `(lhs_sql, params)`. Gets `field_internal_type = self.lhs.output_field.get_internal_type()` and `db_type = self.lhs.output_field.db_type(connection=connection)`. Applies `connection.ops.field_cast_sql(db_type, field_internal_type)` as a format string around `lhs_sql`, then applies `connection.ops.lookup_cast(self.lookup_name, field_internal_type)` similarly. Returns `(modified_lhs_sql, list(params))`.

**`as_sql(self, compiler, connection)`:** Calls `process_lhs()` and `process_rhs()`, extends params with rhs_params. Gets the RHS operator string via `self.get_rhs_op(connection, rhs_sql)`. Returns `('%s %s' % (lhs_sql, rhs_sql), params)`.

**`get_rhs_op(self, connection, rhs)`:** Returns `connection.operators[self.lookup_name] % rhs`.

---

### Class `FieldGetDbPrepValueMixin`

**Mixin that ensures `Field.get_db_prep_value()` is called on lookup values.**

**Class attribute:**
- `get_db_prep_lookup_value_is_iterable = False`

**`get_db_prep_lookup(self, value, connection)`:** Determines the field to use: if `self.lhs.output_field` has a `target_field` attribute, uses that; otherwise falls back to `self.lhs.output_field`. Gets its `get_db_prep_value` method. If `get_db_prep_lookup_value_is_iterable` is `True`, calls `get_db_prep_value(v, connection, prepared=True)` for each `v` in `value`; else calls it once on `value`. Returns `('%s', [prepared_values])`.

---

### Class `FieldGetDbPrepValueIterableMixin(FieldGetDbPrepValueMixin)`

**Mixin for lookups whose RHS is an iterable (e.g., `IN`, `range`).**

**Class attribute:**
- `get_db_prep_lookup_value_is_iterable = True`

**`get_prep_lookup(self)`:** If `rhs` has `resolve_expression`, returns it unchanged. Otherwise iterates over each element in `self.rhs`; if an element has `resolve_expression`, passes through; else if `prepare_rhs` is `True` and the field has `get_prep_value`, calls it on the value. Appends all to a list and returns it.

**`process_rhs(self, compiler, connection)`:** If `rhs_is_direct_value()` (i.e., RHS is plain values), delegates to `self.batch_process_rhs(compiler, connection)`; else calls parent's `process_rhs`.

**`resolve_expression_parameter(self, compiler, connection, sql, param)`:** Wraps `param` in `[param]`. If `param` has `resolve_expression`, resolves it against `compiler.query`. If the result has `as_sql`, compiles it with the compiler. Returns `(sql, params)`.

**`batch_process_rhs(self, compiler, connection, rhs=None)`:** Calls parent's `batch_process_rhs()` to get pre-processed `(sqls, sqls_params)`. Then zips them together and for each pair calls `resolve_expression_parameter()`, collecting the resulting SQL strings and parameter lists. Flattens all parameters via `itertools.chain.from_iterable()`. Returns `(tuple_of_sql_strings, flattened_tuple_of_params)`.

---

### Class `PostgresOperatorLookup(FieldGetDbPrepValueMixin, Lookup)`

**Base for PostgreSQL-specific operator lookups.**

**Class attribute:**
- `postgres_operator = None` — the SQL operator string (e.g., `@>`, `<@`).

**`as_postgresql(self, compiler, connection)`:** Calls `process_lhs()` and `process_rhs()`. Concatenates lhs_params + rhs_params. Returns `'%s %s %s' % (lhs, self.postgres_operator, rhs)` with the combined params tuple.

---

### Class `Exact(FieldGetDbPrepValueMixin, BuiltinLookup)`

**`lookup_name = 'exact'`** — equality comparison (`=`). Registered on `Field`.

**`process_rhs(self, compiler, connection)`:** If `rhs` is a `Query` instance: if it has limit 1 and no select fields, clears the select clause and adds `'pk'`; else raises `ValueError("The QuerySet value for an exact lookup must be limited to one result using slicing.")`. Calls parent's `process_rhs`.

**`as_sql(self, compiler, connection)`:** If `rhs` is a `bool`, `lhs` has `conditional=True`, and the connection supports conditional expressions in WHERE: if `rhs` is truthy, returns `'%s' % lhs_sql`; else `'NOT %s' % lhs_sql`. Otherwise delegates to parent's `as_sql()`.

---

### Class `IExact(BuiltinLookup)`

**`lookup_name = 'iexact'`, `prepare_rhs = False`** — case-insensitive exact match. Registered on `Field`.

**`process_rhs(self, qn, connection)`:** Calls parent's `process_rhs()`. If params exist, replaces `params[0]` with `connection.ops.prep_for_iexact_query(params[0])`. Returns `(rhs, params)`.

---

### Class `GreaterThan(FieldGetDbPrepValueMixin, BuiltinLookup)`

**`lookup_name = 'gt'`** — greater-than (`>`). Registered on `Field`. No overrides.

### Class `GreaterThanOrEqual(FieldGetDbPrepValueMixin, BuiltinLookup)`

**`lookup_name = 'gte'`** — greater-or-equal (`>=`). Registered on `Field`. No overrides.

### Class `LessThan(FieldGetDbPrepValueMixin, BuiltinLookup)`

**`lookup_name = 'lt'`** — less-than (`<`). Registered on `Field`. No overrides.

### Class `LessThanOrEqual(FieldGetDbPrepValueMixin, BuiltinLookup)`

**`lookup_name = 'lte'`** — less-or-equal (`<=`). Registered on `Field`. No overrides.

---

### Class `IntegerFieldFloatRounding`

**Mixin for integer field lookups that need float-to-integer rounding.**

**`get_prep_lookup(self)`:** If `self.rhs` is a `float`, replaces it with `math.ceil(self.rhs)`. Calls parent's `get_prep_lookup()` and returns the result.

---

### Class `IntegerGreaterThanOrEqual(IntegerFieldFloatRounding, GreaterThanOrEqual)`

**Registered on `IntegerField`.** No overrides; inherits float rounding for `>=` comparisons.

### Class `IntegerLessThan(IntegerFieldFloatRounding, LessThan)`

**Registered on `IntegerField`.** No overrides; inherits float rounding for `<` comparisons.

---

### Class `In(FieldGetDbPrepValueIterableMixin, BuiltinLookup)`

**`lookup_name = 'in'`** — SQL `IN` clause. Registered on `Field`.

**`process_rhs(self, compiler, connection)`:** If `rhs` has a `_db` attribute and it differs from `connection.alias`, raises `ValueError("Subqueries aren't allowed across different databases...")`. If `rhs_is_direct_value()`: creates an `OrderedSet` from `self.rhs`, discards `None`; if that fails with `TypeError` (unhashable items), filters out `None` via list comprehension. If the resulting set is empty, raises `EmptyResultSet`. Calls `batch_process_rhs()` to prepare values, wraps in parentheses as a placeholder string `(v1, v2, ...)`, returns `(placeholder, params)`. Else (subquery): if it lacks select fields, clears and adds `'pk'`; calls parent's `process_rhs()`.

**`get_rhs_op(self, connection, rhs)`:** Returns `'IN %s' % rhs`.

**`as_sql(self, compiler, connection)`:** If RHS is direct values and exceeds `connection.ops.max_in_list_size()`, delegates to `split_parameter_list_as_sql()`; else calls parent's `as_sql()`.

**`split_parameter_list_as_sql(self, compiler, connection)`:** For databases with IN-list size limits. Gets LHS SQL/params. Calls `batch_process_rhs()` for RHS. Builds a string starting with `'('`, then iterates over RHS params in chunks of `max_in_list_size`: appends `' OR '` between groups (not before the first), then `'%s IN (' % lhs` + comma-joined chunk SQLs + `')`. Appends final `')'`. Returns the joined string and accumulated params.

---

### Class `PatternLookup(BuiltinLookup)`

**Base for LIKE-based pattern lookups.**

**Class attributes:**
- `param_pattern = '%%%s%%'` — default: wraps value with `%` on both sides (LIKE '%value%').
- `prepare_rhs = False`

**`get_rhs_op(self, connection, rhs)`:** If RHS has `as_sql` or bilateral transforms exist: gets the pattern operation from `connection.pattern_ops[self.lookup_name]`, formats it with `connection.pattern_esc`, then formats with `rhs`. Else delegates to parent's `get_rhs_op()`.

**`process_rhs(self, qn, connection)`:** Calls parent's `process_rhs()`. If RHS is a direct value and params exist and no bilateral transforms: replaces `params[0]` with `self.param_pattern % connection.ops.prep_for_like_query(params[0])`. Returns `(rhs, params)`.

---

### Class `Contains(PatternLookup)`

**`lookup_name = 'contains'`** — LIKE '%value%'. Registered on `Field`. No overrides.

### Class `IContains(Contains)`

**`lookup_name = 'icontains'`** — case-insensitive contains. Registered on `Field`. No overrides.

### Class `StartsWith(PatternLookup)`

**`lookup_name = 'startswith'`, `param_pattern = '%s%%'`** — LIKE 'value%'. Registered on `Field`. No overrides.

### Class `IStartsWith(StartsWith)`

**`lookup_name = 'istartswith'`** — case-insensitive startswith. Registered on `Field`. No overrides.

### Class `EndsWith(PatternLookup)`

**`lookup_name = 'endswith'`, `param_pattern = '%%%s'`** — LIKE '%value'. Registered on `Field`. No overrides.

### Class `IEndsWith(EndsWith)`

**`lookup_name = 'iendswith'`** — case-insensitive endswith. Registered on `Field`. No overrides.

---

### Class `Range(FieldGetDbPrepValueIterableMixin, BuiltinLookup)`

**`lookup_name = 'range'`** — SQL `BETWEEN ... AND ...`. Registered on `Field`.

**`get_rhs_op(self, connection, rhs)`:** Returns `"BETWEEN %s AND %s" % (rhs[0], rhs[1])`.

---

### Class `IsNull(BuiltinLookup)`

**`lookup_name = 'isnull'`, `prepare_rhs = False`** — SQL `IS NULL` / `IS NOT NULL`. Registered on `Field`.

**`as_sql(self, compiler, connection)`:** If `rhs` is not a `bool`, raises `ValueError("The QuerySet value for an isnull lookup must be True or False.")`. Compiles `self.lhs` to SQL. If `rhs` is truthy, returns `"%s IS NULL" % sql`; else `"%s IS NOT NULL" % sql`.

---

### Class `Regex(BuiltinLookup)`

**`lookup_name = 'regex'`, `prepare_rhs = False`** — regex match. Registered on `Field`.

**`as_sql(self, compiler, connection)`:** If `self.lookup_name` is in `connection.operators`, delegates to parent's `as_sql()`. Else: calls `process_lhs()` and `process_rhs()`, gets the SQL template from `connection.ops.regex_lookup(self.lookup_name)`, returns `(template % (lhs, rhs), lhs_params + rhs_params)`.

### Class `IRegex(Regex)`

**`lookup_name = 'iregex'`** — case-insensitive regex. Registered on `Field`. No overrides.

---

### Class `YearLookup(Lookup)`

**Base for year-based date/datetime lookups.**

**`year_lookup_bounds(self, connection, year)`:** Gets the output field from `self.lhs.lhs.output_field`. If it is a `DateTimeField`, calls `connection.ops.year_lookup_bounds_for_datetime_field(year)`; else calls `connection.ops.year_lookup_bounds_for_date_field(year)`. Returns `(start, finish)` datetime bounds.

**`as_sql(self, compiler, connection)`:** If RHS is a direct value: processes LHS using `self.lhs.lhs` (the originating field, skipping the extract transform), gets RHS SQL via `process_rhs()`, formats it with `get_direct_rhs_sql()`, gets year bounds, calls `get_bound_params(start, finish)` to get bound parameters, extends params. Returns `'%s %s' % (lhs_sql, rhs_sql)`. Else delegates to parent's `as_sql()`.

**`get_direct_rhs_sql(self, connection, rhs)`:** Default returns `connection.operators[self.lookup_name] % rhs`. Overridden by subclasses.

**`get_bound_params(self, start, finish)`:** Raises `NotImplementedError`; must be overridden by subclasses.

---

### Class `YearExact(YearLookup, Exact)`

**`get_direct_rhs_sql(self, connection, rhs)`:** Returns `'BETWEEN %s AND %s'`. **`get_bound_params(self, start, finish)`:** Returns `(start, finish)`.

### Class `YearGt(YearLookup, GreaterThan)`

**`get_bound_params(self, start, finish)`:** Returns `(finish,)`.

### Class `YearGte(YearLookup, GreaterThanOrEqual)`

**`get_bound_params(self, start, finish)`:** Returns `(start,)`.

### Class `YearLt(YearLookup, LessThan)`

**`get_bound_params(self, start, finish)`:** Returns `(start,)`.

### Class `YearLte(YearLookup, LessThanOrEqual)`

**`get_bound_params(self, start, finish)`:** Returns `(finish,)`.

---

### Class `UUIDTextMixin`

**Mixin that strips hyphens from UUID values on backends without native UUID support.**

**`process_rhs(self, qn, connection)`:** If the connection does not have native UUID field (`not connection.features.has_native_uuid_field`): if RHS is a direct value, wraps it in `Value(self.rhs)`; then replaces hyphens by creating `Replace(self.rhs, Value('-'), Value(''), output_field=CharField())`. Calls parent's `process_rhs()` and returns `(rhs, params)`.

---

### UUID Field Lookups (all registered on `UUIDField`)

Each combines `UUIDTextMixin` with a text-based lookup:

- **`UUIDIExact(UUIDTextMixin, IExact)`** — case-insensitive exact match for UUIDs.
- **`UUIDContains(UUIDTextMixin, Contains)`** — contains substring in UUID string representation.
- **`UUIDIContains(UUIDTextMixin, IContains)`** — case-insensitive contains.
- **`UUIDStartsWith(UUIDTextMixin, StartsWith)`** — starts with prefix.
- **`UUIDIStartsWith(UUIDTextMixin, IStartsWith)`** — case-insensitive startswith.
- **`UUIDEndsWith(UUIDTextMixin, EndsWith)`** — ends with suffix.
- **`UUIDIEndsWith(UUIDTextMixin, IEndsWith)`** — case-insensitive endswith.

All have no additional method overrides; they inherit `process_rhs()` from `UUIDTextMixin` and the rest from their respective parent lookup classes.