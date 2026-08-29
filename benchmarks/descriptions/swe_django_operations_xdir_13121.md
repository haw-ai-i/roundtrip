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

### Constants & Class-Level Attributes (all on `BaseDatabaseOperations`)

- **`compiler_module = "django.db.models.sql.compiler"`** — string; module path from which SQL compiler classes are dynamically loaded.
- **`integer_field_ranges`** — dict mapping field internal-type strings to `(min, max)` tuples:
  - `'SmallIntegerField'`: `(-32768, 32767)`
  - `'IntegerField'`: `(-2147483648, 2147483647)`
  - `'BigIntegerField'`: `(-9223372036854775808, 9223372036854775807)`
  - `'PositiveBigIntegerField'`: `(0, 9223372036854775807)`
  - `'PositiveSmallIntegerField'`: `(0, 32767)`
  - `'PositiveIntegerField'`: `(0, 2147483647)`
  - `'SmallAutoField'`: `(-32768, 32767)`
  - `'AutoField'`: `(-2147483648, 2147483647)`
  - `'BigAutoField'`: `(-9223372036854775808, 9223372036854775807)`
- **`set_operators`** — dict mapping operator names to SQL keywords: `'union': 'UNION'`, `'intersection': 'INTERSECT'`, `'difference': 'EXCEPT'`.
- **`cast_data_types = {}`** — empty dict; maps `Field.get_internal_type()` values to Cast() data types when different from `DatabaseWrapper.data_types`.
- **`cast_char_field_without_max_length = None`** — default char field type when no max_length is provided.
- **`PRECEDING = 'PRECEDING'`**, **`FOLLOWING = 'FOLLOWING'`**, **`UNBOUNDED_PRECEDING = 'UNBOUNDED PRECEDING'`**, **`UNBOUNDED_FOLLOWING = 'UNBOUNDED FOLLOWING'`**, **`CURRENT_ROW = 'CURRENT ROW'`** — string constants for window expression frame boundaries.
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
- Returns `None`. Placeholder for SQL needed to support auto-incrementing primary keys at table creation time.

#### `bulk_batch_size(self, fields, objs)`
- Returns `len(objs)`. The maximum batch size for bulk inserts; subclasses may override to impose limits.

#### `cache_key_culling_sql(self)`
- Returns the string: `"SELECT cache_key FROM %s ORDER BY cache_key LIMIT 1 OFFSET %%s"`. Used by the 'db' cache backend to determine culling start position.

#### `unification_cast_sql(self, output_field)`
- Given a field instance, returns `'%s'` — a placeholder for casting union results to the target type.

#### `date_extract_sql(self, lookup_type, field_name)`
- Raises `NotImplementedError`. Must be overridden; extracts a date component (e.g., 'year', 'month', 'day') from `field_name`.

#### `date_interval_sql(self, timedelta)`
- Raises `NotImplementedError`. Must be overridden; implements date interval arithmetic for expressions.

#### `date_trunc_sql(self, lookup_type, field_name)`
- Raises `NotImplementedError`. Must be overridden; truncates a date field to the given specificity ('year', 'month', or 'day').

#### `datetime_cast_date_sql(self, field_name, tzname)`
- Raises `NotImplementedError`. Must be overridden; casts a datetime column to a date.

#### `datetime_cast_time_sql(self, field_name, tzname)`
- Raises `NotImplementedError`. Must be overridden; casts a datetime column to a time.

#### `datetime_extract_sql(self, lookup_type, field_name, tzname)`
- Raises `NotImplementedError`. Must be overridden; extracts a component ('year', 'month', 'day', 'hour', 'minute', 'second') from a datetime field with timezone.

#### `datetime_trunc_sql(self, lookup_type, field_name, tzname)`
- Raises `NotImplementedError`. Must be overridden; truncates a datetime to the given specificity with timezone.

#### `time_trunc_sql(self, lookup_type, field_name)`
- Raises `NotImplementedError`. Must be overridden; truncates a time field ('hour', 'minute', or 'second').

#### `time_extract_sql(self, lookup_type, field_name)`
- Delegates to and returns `self.date_extract_sql(lookup_type, field_name)`. Reuses date extraction logic for time fields.

#### `json_cast_text_sql(self, field_name)`
- Raises `NotImplementedError`. Must be overridden; returns SQL to cast a JSON value to text.

#### `deferrable_sql(self)`
- Returns `''` (empty string). SQL fragment for making a constraint "initially deferred" in CREATE TABLE.

#### `distinct_sql(self, fields, params)`
- If `fields` is truthy: raises `NotSupportedError` ("DISTINCT ON fields is not supported by this database backend").
- Otherwise: returns the tuple `(['DISTINCT'], [])`.

#### `fetch_returned_insert_columns(self, cursor, returning_params)`
- Returns `cursor.fetchone()`. Retrieves the single row from an INSERT...RETURNING statement.

#### `field_cast_sql(self, db_type, internal_type)`
- Returns `'%s'`. SQL to cast a column before use in WHERE; contains a `%s` placeholder for the column.

#### `force_no_ordering(self)`
- Returns `[]`. An empty list used in ORDER BY clause to suppress ordering.

#### `for_update_sql(self, nowait=False, skip_locked=False, of=(), no_key=False)`
- Returns a formatted string: `'FOR%s UPDATE%s%s%s'` % `(no_key_part, of_part, nowait_part, skip_locked_part)`, where:
  - `no_key_part = ' NO KEY'` if `no_key` else `''`
  - `of_part = ' OF %s' % ', '.join(of)` if `of` is truthy else `''`
  - `nowait_part = ' NOWAIT'` if `nowait` else `''`
  - `skip_locked_part = ' SKIP LOCKED'` if `skip_locked` else `''`

#### `_get_limit_offset_params(self, low_mark, high_mark)` *(private helper)*
- Computes `(limit, offset)`:
  - `offset = low_mark or 0`.
  - If `high_mark is not None`: returns `(high_mark - offset, offset)`.
  - Else if `offset` is truthy: returns `(self.connection.ops.no_limit_value(), offset)`.
  - Otherwise: returns `(None, offset)` (i.e., `(None, 0)`).

#### `limit_offset_sql(self, low_mark, high_mark)`
- Calls `_get_limit_offset_params(low_mark, high_mark)` to get `(limit, offset)`.
- Builds a space-separated string from non-null parts: `'LIMIT %d' % limit` and/or `'OFFSET %d' % offset`. Returns the joined result.

#### `last_executed_query(self, cursor, sql, params)`
- Defines an inner helper `to_string(s)` that calls `force_str(s, strings_only=True, errors='replace')`.
- Normalizes `params`:
  - If `isinstance(params, (list, tuple))`: converts each element via `to_string`, returns a tuple.
  - If `params is None`: sets `u_params = ()`.
  - Otherwise: converts both keys and values of the dict via `to_string`, returns a new dict.
- Returns `"QUERY = %r - PARAMS = %r" % (sql, u_params)`.

#### `last_insert_id(self, cursor, table_name, pk_name)`
- Returns `cursor.lastrowid`. Retrieves the auto-increment ID from a just-executed INSERT.

#### `lookup_cast(self, lookup_type, internal_type=None)`
- Returns `"%s"`. SQL fragment for lookups (contains a `%s` placeholder).

#### `max_in_list_size(self)`
- Returns `None`. Maximum items in an IN clause; `None` means no limit.

#### `max_name_length(self)`
- Returns `None`. Maximum length of table/column names; `None` means no limit.

#### `no_limit_value(self)`
- Raises `NotImplementedError`. Must be overridden; returns the value for "LIMIT infinity" or a sentinel.

#### `pk_default_value(self)`
- Returns `'DEFAULT'`. SQL token to specify default-value insertion for a primary key column.

#### `prepare_sql_script(self, sql)`
- Splits the input `sql` string using `sqlparse.split(sql)`, formats each statement with `sqlparse.format(statement, strip_comments=True)`, and returns a list of non-empty formatted statements.

#### `process_clob(self, value)`
- Returns `value` unchanged. Hook for processing CLOB locators; no-op by default.

#### `return_insert_columns(self, fields)`
- Returns `None` (implicit `pass`). SQL fragment to append RETURNING clause to INSERT; subclasses override.

#### `compiler(self, compiler_name)`
- If `self._cache is None`: imports the module at `self.compiler_module` via `import_module()` and stores it in `self._cache`.
- Returns `getattr(self._cache, compiler_name)`. Dynamically loads a SQL compiler class by name.

#### `quote_name(self, name)`
- Raises `NotImplementedError`. Must be overridden; quotes a table/index/column name without double-quoting if already quoted.

#### `random_function_sql(self)`
- Returns `'RANDOM()'`. An SQL expression that produces a random value.

#### `regex_lookup(self, lookup_type)`
- Raises `NotImplementedError`. Must be overridden; returns regex lookup SQL with a `%s` placeholder.

#### `savepoint_create_sql(self, sid)`
- Returns `"SAVEPOINT %s" % self.quote_name(sid)`. SQL to create a savepoint.

#### `savepoint_commit_sql(self, sid)`
- Returns `"RELEASE SAVEPOINT %s" % self.quote_name(sid)`. SQL to commit a savepoint.

#### `savepoint_rollback_sql(self, sid)`
- Returns `"ROLLBACK TO SAVEPOINT %s" % self.quote_name(sid)`. SQL to roll back to a savepoint.

#### `set_time_zone_sql(self)`
- Returns `''` (empty string). SQL to set the connection's time zone; empty means unsupported.

#### `sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False)`
- Raises `NotImplementedError`. Must be overridden; returns a list of SQL statements to delete all data from given tables without dropping them. Parameters: `style` (management color style), `tables`, and keyword-only `reset_sequences`, `allow_cascade`.

#### `execute_sql_flush(self, sql_list)`
- Opens an atomic transaction via `transaction.atomic(using=self.connection.alias, savepoint=self.connection.features.can_rollback_ddl)`.
- Within that, opens a cursor (`self.connection.cursor()`), iterates over each SQL string in `sql_list`, and executes it.

#### `sequence_reset_by_name_sql(self, style, sequences)`
- Returns `[]`. SQL statements to reset named sequences; no-op by default.

#### `sequence_reset_sql(self, style, model_list)`
- Returns `[]`. SQL statements to reset sequences for given models; no-op by default.

#### `start_transaction_sql(self)`
- Returns `"BEGIN;"`. SQL to start a transaction.

#### `end_transaction_sql(self, success=True)`
- If `success` is falsy: returns `"ROLLBACK;"`.
- Otherwise: returns `"COMMIT;"`.

#### `tablespace_sql(self, tablespace, inline=False)`
- Returns `''`. SQL for defining a tablespace; empty means unsupported. The `inline` flag controls whether it appends to a row vs. the full statement.

#### `prep_for_like_query(self, x)`
- Converts `x` to string and escapes backslashes, percent signs, and underscores: `str(x).replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")`. Prepares a value for LIKE queries.

#### `prep_for_iexact_query = prep_for_like_query`
- Alias; the same function is used for iexact matches.

#### `validate_autopk_value(self, value)`
- Returns `value` unchanged. Validates serial/auto-primary-key values; raises `ValueError` if invalid (no-op by default).

#### `adapt_unknown_value(self, value)`
- Dispatches based on type:
  - If `isinstance(value, datetime.datetime)`: returns `self.adapt_datetimefield_value(value)`.
  - Else if `isinstance(value, datetime.date)`: returns `self.adapt_datefield_value(value)`.
  - Else if `isinstance(value, datetime.time)`: returns `self.adapt_timefield_value(value)`.
  - Else if `isinstance(value, decimal.Decimal)`: returns `self.adapt_decimalfield_value(value)`.
  - Otherwise: returns `value` unchanged.

#### `adapt_datefield_value(self, value)`
- If `value is None`: returns `None`.
- Otherwise: returns `str(value)`. Converts a date to its string representation for the backend driver.

#### `adapt_datetimefield_value(self, value)`
- If `value is None`: returns `None`.
- Otherwise: returns `str(value)`. Converts a datetime to its string representation.

#### `adapt_timefield_value(self, value)`
- If `value is None`: returns `None`.
- If `timezone.is_aware(value)` is truthy: raises `ValueError("Django does not support timezone-aware times.")`.
- Otherwise: returns `str(value)`. Converts a naive time to its string representation.

#### `adapt_decimalfield_value(self, value, max_digits=None, decimal_places=None)`
- Returns `utils.format_number(value, max_digits, decimal_places)`. Formats a Decimal for the backend driver using the shared utility.

#### `adapt_ipaddressfield_value(self, value)`
- Returns `value or None`. Converts an IP address string; falsy values become `None`.

#### `year_lookup_bounds_for_date_field(self, value)`
- Constructs `first = datetime.date(value, 1, 1)` and `second = datetime.date(value, 12, 31)`.
- Adapts both via `self.adapt_datefield_value()`.
- Returns `[first, second]` as a two-element list for use in a BETWEEN clause.

#### `year_lookup_bounds_for_datetime_field(self, value)`
- Constructs `first = datetime.datetime(value, 1, 1)` and `second = datetime.datetime(value, 12, 31, 23, 59, 59, 999999)`.
- If `settings.USE_TZ` is truthy: gets the current timezone via `timezone.get_current_timezone()`, then makes both aware with `timezone.make_aware(first, tz)` and `timezone.make_aware(second, tz)`.
- Adapts both via `self.adapt_datetimefield_value()`.
- Returns `[first, second]` as a two-element list.

#### `get_db_converters(self, expression)`
- Returns `[]`. List of converter functions for field data; no-op by default.

#### `convert_durationfield_value(self, value, expression, connection)`
- If `value is not None`: returns `datetime.timedelta(0, 0, value)`, converting an integer microsecond count to a timedelta.
- Otherwise: implicitly returns `None`.

#### `check_expression_support(self, expression)`
- Does nothing (`pass`). Hook for backends to raise `NotSupportedError` for unsupported expressions.

#### `conditional_expression_supported_in_where_clause(self, expression)`
- Returns `True`. Indicates whether a conditional expression is valid in WHERE clauses.

#### `combine_expression(self, connector, sub_expressions)`
- Formats the connector as `' %s '` (space-wrapped), then joins all elements of `sub_expressions` with it. Returns the resulting string.

#### `combine_duration_expression(self, connector, sub_expressions)`
- Delegates to and returns `self.combine_expression(connector, sub_expressions)`. Reuses generic expression combining for durations.

#### `binary_placeholder_sql(self, value)`
- Returns `'%s'`. Placeholder syntax for binary content; some backends override (e.g., MySQL uses `_binary %s`).

#### `modify_insert_params(self, placeholder, params)`
- Returns `params` unchanged. Hook to modify insert parameters before execution.

#### `integer_field_range(self, internal_type)`
- Returns `self.integer_field_ranges[internal_type]`. Looks up the `(min, max)` tuple for a given integer field type from the class-level dict.

#### `subtract_temporals(self, internal_type, lhs, rhs)`
- If `self.connection.features.supports_temporal_subtraction` is truthy: unpacks `lhs` and `rhs` as `(sql, params)` tuples; returns `'(%s - %s)' % (lhs_sql, rhs_sql)` with concatenated params `(*lhs_params, *rhs_params)`.
- Otherwise: raises `NotSupportedError("This backend does not support %s subtraction." % internal_type)`.

#### `window_frame_start(self, start)`
- If `isinstance(start, int)`:
  - If `start < 0`: returns `'%d PRECEDING' % abs(start)`.
  - If `start == 0`: returns `'CURRENT ROW'`.
- Else if `start is None`: returns `'UNBOUNDED PRECEDING'`.
- Otherwise: raises `ValueError("start argument must be a negative integer, zero, or None, but got '%s'." % start)`.

#### `window_frame_end(self, end)`
- If `isinstance(end, int)`:
  - If `end == 0`: returns `'CURRENT ROW'`.
  - If `end > 0`: returns `'%d FOLLOWING' % end`.
- Else if `end is None`: returns `'UNBOUNDED FOLLOWING'`.
- Otherwise: raises `ValueError("end argument must be a positive integer, zero, or None, but got '%s'." % end)`.

#### `window_frame_rows_start_end(self, start=None, end=None)`
- If `not self.connection.features.supports_over_clause`: raises `NotSupportedError('This backend does not support window expressions.')`.
- Returns `(self.window_frame_start(start), self.window_frame_end(end))` as a tuple of two strings.

#### `window_frame_range_start_end(self, start=None, end=None)`
- Calls `self.window_frame_rows_start_end(start, end)` to get `(start_, end_)`.
- If `self.connection.features.only_supports_unbounded_with_preceding_and_following` is truthy **and** either `start and start < 0` or `end and end > 0`: raises `NotSupportedError('%s only supports UNBOUNDED together with PRECEDING and FOLLOWING.' % self.connection.display_name)`.
- Returns `(start_, end_)`.

#### `explain_query_prefix(self, format=None, **options)`
- If `not self.connection.features.supports_explaining_query_execution`: raises `NotSupportedError('This backend does not support explaining query execution.')`.
- If `format` is truthy: gets `supported_formats = self.connection.features.supported_explain_formats`; normalizes to uppercase; if the normalized format is not in `supported_formats`, raises `ValueError` with a message indicating the unrecognized format and listing allowed formats (if any).
- If `options` is truthy: raises `ValueError('Unknown options: %s' % ', '.join(sorted(options.keys())))`.
- Returns `self.explain_prefix`.

#### `insert_statement(self, ignore_conflicts=False)`
- Returns `'INSERT INTO'`. The base INSERT SQL prefix.

#### `ignore_conflicts_suffix_sql(self, ignore_conflicts=None)`
- Returns `''`. Suffix appended when ignoring insert conflicts; no-op by default.

## django/db/backends/mysql/operations.py
Here is the complete natural-language specification of `django/db/backends/mysql/operations.py`:

---

## Module-Level Preamble

### Imports
```python
import uuid

from django.conf import settings
from django.db.backends.base.operations import BaseDatabaseOperations
from django.utils import timezone
from django.utils.duration import duration_microseconds
from django.utils.encoding import force_str
```

### Class: `DatabaseOperations(BaseDatabaseOperations)`

**Metaclass:** None (inherits from `BaseDatabaseOperations`).

#### Class-Level Attributes

- **`compiler_module`**: Literal string `"django.db.backends.mysql.compiler"`.

- **`integer_field_ranges`**: Dict extending the parent class's `integer_field_ranges` with three additional entries:
  - `'PositiveSmallIntegerField'`: tuple `(0, 65535)`
  - `'PositiveIntegerField'`: tuple `(0, 4294967295)`
  - `'PositiveBigIntegerField'`: tuple `(0, 18446744073709551615)`

- **`cast_data_types`**: Dict mapping Django field type names to MySQL CAST target types:
  - `'AutoField'` → `'signed integer'`
  - `'BigAutoField'` → `'signed integer'`
  - `'SmallAutoField'` → `'signed integer'`
  - `'CharField'` → `'char(%(max_length)s)'`
  - `'DecimalField'` → `'decimal(%(max_digits)s, %(decimal_places)s)'`
  - `'TextField'` → `'char'`
  - `'IntegerField'` → `'signed integer'`
  - `'BigIntegerField'` → `'signed integer'`
  - `'SmallIntegerField'` → `'signed integer'`
  - `'PositiveBigIntegerField'` → `'unsigned integer'`
  - `'PositiveIntegerField'` → `'unsigned integer'`
  - `'PositiveSmallIntegerField'` → `'unsigned integer'`

- **`cast_char_field_without_max_length`**: Literal string `'char'`.

- **`explain_prefix`**: Literal string `'EXPLAIN'`.

---

#### Instance Methods

##### `date_extract_sql(self, lookup_type, field_name)`
Returns a SQL fragment for extracting date components from `field_name`.
- If `lookup_type == 'week_day'`: returns `"DAYOFWEEK(%s)" % field_name` (returns 1–7, Sunday=1).
- If `lookup_type == 'iso_week_day'`: returns `"WEEKDAY(%s) + 1" % field_name` (converts Monday=0 to Monday=1).
- If `lookup_type == 'week'`: returns `"WEEK(%s, 3)" % field_name` (mode 3: Monday start, weeks numbered 1–53 with ≥4 days in the new year).
- If `lookup_type == 'iso_year'`: returns `"TRUNCATE(YEARWEEK(%s, 3), -2) / 100" % field_name` (extracts the ISO year from YEARWEEK).
- Otherwise: returns `"EXTRACT(%s FROM %s)" % (lookup_type.upper(), field_name)` for all other extract types.

##### `date_trunc_sql(self, lookup_type, field_name)`
Returns a SQL fragment for truncating a date/timestamp to the given granularity.
- If `lookup_type == 'year'`: returns `"CAST(DATE_FORMAT(%s, '%%Y-01-01') AS DATE)" % field_name`.
- If `lookup_type == 'month'`: returns `"CAST(DATE_FORMAT(%s, '%%Y-%%m-01') AS DATE)" % field_name`.
- If `lookup_type == 'quarter'`: returns `"MAKEDATE(YEAR(%s), 1) + INTERVAL QUARTER(%s) QUARTER - INTERVAL 1 QUARTER" % (field_name, field_name)` — computes the first day of the quarter.
- If `lookup_type == 'week'`: returns `"DATE_SUB(%s, INTERVAL WEEKDAY(%s) DAY)" % (field_name, field_name)` — truncates to the Monday of that week.
- Otherwise: returns `"DATE(%s)" % field_name` (truncates to midnight).

##### `_prepare_tzname_delta(self, tzname)`
Private helper. Extracts the timezone offset portion from a timezone name string:
- If `'+'` is in `tzname`, returns the substring starting at the first `'+'`.
- Else if `'-'` is in `tzname`, returns the substring starting at the first `'-'`.
- Otherwise, returns `tzname` unchanged.

##### `_convert_field_to_tz(self, field_name, tzname)`
Private helper. Wraps a field name with MySQL's `CONVERT_TZ` if timezone conversion is needed:
- If `settings.USE_TZ` is True **and** `self.connection.timezone_name != tzname`, returns `"CONVERT_TZ(%s, '%s', '%s')" % (field_name, self.connection.timezone_name, self._prepare_tzname_delta(tzname))`.
- Otherwise, returns `field_name` unchanged.

##### `datetime_cast_date_sql(self, field_name, tzname)`
Returns a SQL fragment for casting a datetime to a date with timezone awareness:
- Converts the field via `_convert_field_to_tz(field_name, tzname)`, then returns `"DATE(%s)" % converted_field`.

##### `datetime_cast_time_sql(self, field_name, tzname)`
Returns a SQL fragment for casting a datetime to a time with timezone awareness:
- Converts the field via `_convert_field_to_tz(field_name, tzname)`, then returns `"TIME(%s)" % converted_field`.

##### `datetime_extract_sql(self, lookup_type, field_name, tzname)`
Returns a SQL fragment for extracting date/time components from a datetime column with timezone awareness:
- Converts the field via `_convert_field_to_tz(field_name, tzname)`, then delegates to `self.date_extract_sql(lookup_type, converted_field)`.

##### `datetime_trunc_sql(self, lookup_type, field_name, tzname)`
Returns a SQL fragment for truncating a datetime to the given granularity with timezone awareness:
- Converts the field via `_convert_field_to_tz(field_name, tzname)`.
- If `lookup_type == 'quarter'`: returns `"CAST(DATE_FORMAT(MAKEDATE(YEAR({field}), 1) + INTERVAL QUARTER({field}) QUARTER - INTERVAL 1 QUARTER, '%%Y-%%m-01 00:00:00') AS DATETIME)"` with `field` substituted.
- If `lookup_type == 'week'`: returns `"CAST(DATE_FORMAT(DATE_SUB({field}, INTERVAL WEEKDAY({field}) DAY), '%%Y-%%m-%%d 00:00:00') AS DATETIME)"` with `field` substituted.
- For lookup types in `['year', 'month', 'day', 'hour', 'minute', 'second']`: builds a format string by joining the first `i+1` elements of `('%%Y-', '%%m', '-%%d', ' %%H:', '%%i', ':%%s')` with zero-fill defaults for remaining positions, then returns `"CAST(DATE_FORMAT(%s, '%s') AS DATETIME)" % (field_name, format_str)`.
- For any other lookup type: returns `field_name` unchanged.

##### `time_trunc_sql(self, lookup_type, field_name)`
Returns a SQL fragment for truncating a time value to the given granularity.
- If `lookup_type == 'hour'`: returns `"CAST(DATE_FORMAT(%s, '%%H:00:00') AS TIME)" % field_name`.
- If `lookup_type == 'minute'`: returns `"CAST(DATE_FORMAT(%s, '%%H:%%i:00') AS TIME)" % field_name`.
- If `lookup_type == 'second'`: returns `"CAST(DATE_FORMAT(%s, '%%H:%%i:%%s') AS TIME)" % field_name`.
- Otherwise: returns `"TIME(%s)" % field_name`.

##### `date_interval_sql(self, timedelta)`
Returns a SQL fragment representing the given `timedelta` as an interval for addition/subtraction. Delegates to `duration_microseconds(timedelta)` and returns `'INTERVAL %s MICROSECOND' % microseconds_value`.

##### `fetch_returned_insert_rows(self, cursor)`
Given a cursor that executed an `INSERT...RETURNING` statement, returns the result of `cursor.fetchall()` — a tuple/list of returned rows.

##### `format_for_duration_arithmetic(self, sql)`
Wraps a SQL expression for duration arithmetic: returns `'INTERVAL %s MICROSECOND' % sql`.

##### `force_no_ordering(self)`
Returns `[(None, ("NULL", [], False))]` to produce an `ORDER BY NULL` clause, preventing MySQL's implicit ordering on grouped columns.

##### `last_executed_query(self, cursor, sql, params)`
Attempts to retrieve the exact query string last executed by the given cursor:
- Uses `getattr(cursor, '_executed', None)` (MySQLdb stores the executed query here; PyMySQL returns bytes).
- Wraps the result with `force_str(..., errors='replace')` and returns it as a string. Returns an empty string if `_executed` is absent or falsy.

##### `no_limit_value(self)`
Returns `18446744073709551615` (2⁶⁴ − 1), the maximum unsigned 64-bit integer, as recommended by MySQL documentation for representing "no limit" in LIMIT clauses.

##### `quote_name(self, name)`
Quotes a database object name with backticks:
- If `name` already starts and ends with `` ` ``, returns it unchanged (avoids double-quoting).
- Otherwise, returns `` `%s` `` % name.

##### `random_function_sql(self)`
Returns the literal string `'RAND()'`.

##### `return_insert_columns(self, fields)`
Generates a RETURNING clause for INSERT...RETURNING statements:
- If `fields` is empty/falsy, returns `('', ())`.
- Otherwise, builds column references as `` `%s.%s` `` (table.column) for each field using `self.quote_name(field.model._meta.db_table)` and `self.quote_name(field.column)`, joins them with `, `, and returns `'RETURNING %s' % joined_columns` with an empty params tuple.

##### `sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False)`
Generates SQL statements to flush (empty) the given tables:
- If `tables` is empty/falsy, returns `[]`.
- Always starts with `'SET FOREIGN_KEY_CHECKS = 0;'` to disable foreign key checks.
- If `reset_sequences` is True: generates `TRUNCATE \`table\`;` for each table (faster and resets AUTO_INCREMENT).
- If `reset_sequences` is False: generates `DELETE FROM \`table\`;` for each table (preserves sequences, faster than TRUNCATE when no reset needed).
- Ends with `'SET FOREIGN_KEY_CHECKS = 1;'`.
- Returns the list of SQL strings.

##### `sequence_reset_by_name_sql(self, style, sequences)`
Returns a list of SQL statements to reset AUTO_INCREMENT counters:
- For each sequence info dict (with keys `'table'`), generates `'ALTER TABLE \`table\` AUTO_INCREMENT = 1;'`.
- Returns the list of such strings.

##### `validate_autopk_value(self, value)`
Validates an explicit AutoField value before insertion:
- If `value == 0`, raises `ValueError('The database backend does not accept 0 as a value for AutoField.')` (MySQL AUTO_INCREMENT rejects zero).
- Otherwise, returns the value unchanged.

##### `adapt_datetimefield_value(self, value)`
Adapts a Python datetime value for MySQL:
- If `value is None`, returns `None`.
- If `value` has attribute `resolve_expression` (is an expression), returns it unchanged (database will adapt).
- If the value is timezone-aware (`timezone.is_aware(value)`):
  - If `settings.USE_TZ` is True: converts to naive using `timezone.make_naive(value, self.connection.timezone)`.
  - If `settings.USE_TZ` is False: raises `ValueError("MySQL backend does not support timezone-aware datetimes when USE_TZ is False.")`.
- Returns `str(value)` (the string representation of the datetime).

##### `adapt_timefield_value(self, value)`
Adapts a Python time value for MySQL:
- If `value is None`, returns `None`.
- If `value` has attribute `resolve_expression`, returns it unchanged.
- If timezone-aware (`timezone.is_aware(value)`): raises `ValueError("MySQL backend does not support timezone-aware times.")`.
- Returns `str(value)`.

##### `max_name_length(self)`
Returns the integer `64`, the maximum length for database object names in MySQL.

##### `bulk_insert_sql(self, fields, placeholder_rows)`
Generates the VALUES clause for bulk INSERT statements:
- Joins each row of placeholders with `, `.
- Wraps all rows as `(row1), (row2), ...`.
- Returns `'VALUES ' + combined_values_string`.

##### `combine_expression(self, connector, sub_expressions)`
Combines two expressions with a binary operator connector for MySQL:
- If `connector == '^'`: returns `'POW(%s)' % ','.join(sub_expressions)` (MySQL uses POW for exponentiation).
- If `connector` is one of `('&', '|', '<<', '#')`: replaces `'#'` with `'^'`, then wraps the joined expression in `'CONVERT(%s, SIGNED)'` to force signed integer result (MySQL bitwise ops return unsigned).
- If `connector == '>>'`: returns `'FLOOR(%(lhs)s / POW(2, %(rhs)s))' % {'lhs': lhs, 'rhs': rhs}`.
- Otherwise: delegates to `super().combine_expression(connector, sub_expressions)`.

##### `get_db_converters(self, expression)`
Returns a list of database-to-Python conversion functions for the given expression's output field:
- Calls `super().get_db_converters(expression)` to get base converters.
- Gets `internal_type = expression.output_field.get_internal_type()`:
  - If `'BooleanField'` or `'NullBooleanField'`: appends `self.convert_booleanfield_value`.
  - If `'DateTimeField'` and `settings.USE_TZ`: appends `self.convert_datetimefield_value`.
  - If `'UUIDField'`: appends `self.convert_uuidfield_value`.
- Returns the accumulated list.

##### `convert_booleanfield_value(self, value, expression, connection)`
Converts a MySQL boolean (0 or 1) to Python bool:
- If `value` is `0` or `1`, returns `bool(value)`.
- Otherwise, returns `value` unchanged.

##### `convert_datetimefield_value(self, value, expression, connection)`
Converts a naive datetime from MySQL to timezone-aware:
- If `value is not None`, wraps it with `timezone.make_aware(value, self.connection.timezone)`.
- Returns the (possibly converted) value.

##### `convert_uuidfield_value(self, value, expression, connection)`
Converts a string UUID from MySQL to a Python `uuid.UUID` object:
- If `value is not None`, returns `uuid.UUID(value)`.
- Otherwise, returns `None`.

##### `binary_placeholder_sql(self, value)`
Returns the placeholder SQL for binary data:
- If `value is not None and not hasattr(value, 'as_sql')`: returns `'_binary %s'` (MySQL binary literal prefix).
- Otherwise: returns `'%s'`.

##### `subtract_temporals(self, internal_type, lhs, rhs)`
Generates SQL for subtracting two temporal values, returning `(sql_string, params_tuple)`:
- Unpacks `lhs` and `rhs` as `(sql, params)` tuples.
- If `internal_type == 'TimeField'`:
  - If `self.connection.mysql_is_mariadb`: returns `'CAST((TIME_TO_SEC(%(lhs)s) - TIME_TO_SEC(%(rhs)s)) * 1000000 AS SIGNED)'` with params `(*lhs_params, *rhs_params)` (MariaDB includes microseconds as decimal in TIME_TO_SEC).
  - Otherwise (MySQL): returns `"((TIME_TO_SEC(%(lhs)s) * 1000000 + MICROSECOND(%(lhs)s)) - (TIME_TO_SEC(%(rhs)s) * 1000000 + MICROSECOND(%(rhs)s)))"` with params `tuple(lhs_params) * 2 + tuple(rhs_params) * 2`.
- For other types (`DateTimeField`, `DateField`): returns `"TIMESTAMPDIFF(MICROSECOND, %s, %s)" % (rhs_sql, lhs_sql)` with params `(*rhs_params, *lhs_params)`.

##### `explain_query_prefix(self, format=None, **options)`
Generates the prefix for an EXPLAIN query:
- If `format` is `'TEXT'` (case-insensitive), converts it to `'TRADITIONAL'` (MySQL's name for TEXT format).
- If no `format` is given and `self.connection.features.supported_explain_formats` contains `'TREE'`, defaults `format` to `'TREE'`.
- Pops `analyze = options.pop('analyze', False)`.
- Calls `super().explain_query_prefix(format, **options)` to get the base prefix.
- If `analyze` is True and `self.connection.features.supports_explain_analyze`:
  - If MariaDB (`self.connection.mysql_is_mariadb`): replaces prefix with `'ANALYZE'`.
  - Otherwise: appends `' ANALYZE'` to the prefix.
- If a format was specified (and not in the analyze+non-MariaDB case), appends `' FORMAT=%s' % format` to the prefix.
- Returns the final prefix string.

##### `regex_lookup(self, lookup_type)`
Generates SQL for regex/iregex lookups:
- If MySQL version < `(8, 0, 0)` or MariaDB (`self.connection.mysql_is_mariadb`):
  - If `lookup_type == 'regex'`: returns `'%s REGEXP BINARY %s'`.
  - Otherwise (iregex): returns `'%s REGEXP %s'`.
- For MySQL ≥ 8.0: returns `"REGEXP_LIKE(%%s, %%s, '%s')" % match_option` where `match_option = 'c'` for `'regex'` and `'i'` for `'iregex'`.

##### `insert_statement(self, ignore_conflicts=False)`
Returns the INSERT statement prefix:
- If `ignore_conflicts` is True: returns `'INSERT IGNORE INTO'`.
- Otherwise: delegates to `super().insert_statement(ignore_conflicts)`.

##### `lookup_cast(self, lookup_type, internal_type=None)`
Returns a SQL cast wrapper for lookups on specific field types:
- Default lookup is `'%s'`.
- If `internal_type == 'JSONField'` and either MariaDB or the lookup type is one of `'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'regex', 'iregex'`: returns `'JSON_UNQUOTE(%s)'`.
- Otherwise, returns `'%s'`.

## django/db/backends/sqlite3/operations.py
Now I have the complete file. Here is the specification:

---

# Module Specification: `django/db/backends/sqlite3/operations.py`

## 1. Imports

```python
import datetime
import decimal
import uuid
from functools import lru_cache
from itertools import chain
from django.conf import settings
from django.core.exceptions import FieldError
from django.db import DatabaseError, NotSupportedError, models
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.models.expressions import Col
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from django.utils.duration import duration_microseconds
from django.utils.functional import cached_property
```

## 2. Class: `DatabaseOperations(BaseDatabaseOperations)`

### 2.1 Class Attributes

| Attribute | Value | Description |
|-----------|-------|-------------|
| `cast_char_field_without_max_length` | `'text'` | SQL type used when casting a char field that has no max length defined. |
| `cast_data_types` | `{'DateField': 'TEXT', 'DateTimeField': 'TEXT'}` | Mapping of Django field internal types to their SQLite cast target types. Date and datetime fields are cast to TEXT because SQLite stores them as text strings. |
| `explain_prefix` | `'EXPLAIN QUERY PLAN'` | The SQL prefix used for query plan explanation (SQLite-specific; differs from the plain `'EXPLAIN'` used by other backends). |

### 2.2 Methods

#### `bulk_batch_size(self, fields, objs) → int`

Computes the maximum number of rows that can be safely batched in a single bulk INSERT for SQLite.

- If `len(fields) == 1`: returns `500`. This is because SQLite's `SQLITE_MAX_COMPOUND_SELECT` limit caps compound SELECT statements (used internally for single-field inserts) at 500 elements.
- If `len(fields) > 1`: returns `self.connection.features.max_query_params // len(fields)`. Divides the global maximum query parameter count by the number of fields to stay within SQLite's `SQLITE_LIMIT_VARIABLE_NUMBER` limit (default 999).
- Otherwise (`len(fields) == 0`, i.e., no fields): returns `len(objs)` — all objects in a single batch.

#### `check_expression_support(self, expression)` → None

Validates that the given ORM expression is supported by SQLite; raises exceptions for unsupported constructs.

1. **Date/time aggregate check:** If `expression` is an instance of any of `(models.Sum, models.Avg, models.Variance, models.StdDev)`, iterates over each sub-expression returned by `expression.get_source_expressions()`. For each sub-expression that has an `output_field` attribute (skipping those that raise `AttributeError` or `FieldError`), if the output field is an instance of `(models.DateField, models.DateTimeField, models.TimeField)`, raises `NotSupportedError` with the message: `"You cannot use Sum, Avg, StdDev, and Variance aggregations on date/time fields in sqlite3 since date/time is saved as text."`

2. **Distinct multi-argument aggregate check:** If `expression` is an instance of `models.Aggregate`, has `distinct == True`, and `len(expression.source_expressions) > 1`, raises `NotSupportedError` with the message: `"SQLite doesn't support DISTINCT on aggregate functions accepting multiple arguments."`

#### `date_extract_sql(self, lookup_type, field_name) → str`

Returns SQL for extracting a date component. Formats as:
```sql
django_date_extract('<lookup_type_lower>', <field_name>)
```
where `<lookup_type_lower>` is the lowercase version of `lookup_type`. The custom function `django_date_extract()` is registered at connection time. Single quotes are used around the lookup type to avoid field name collisions.

#### `date_interval_sql(self, timedelta) → str`

Returns a string representation of the total microseconds in the given `timedelta`, computed via `duration_microseconds(timedelta)`.

#### `format_for_duration_arithmetic(self, sql) → str`

Returns `sql` unchanged. Duration arithmetic formatting is handled entirely by custom SQL functions registered at connection time; no transformation is needed here.

#### `date_trunc_sql(self, lookup_type, field_name) → str`

Returns SQL for truncating a date to the given precision:
```sql
django_date_trunc('<lookup_type_lower>', <field_name>)
```

#### `time_trunc_sql(self, lookup_type, field_name) → str`

Returns SQL for truncating a time value:
```sql
django_time_trunc('<lookup_type_lower>', <field_name>)
```

#### `_convert_tznames_to_sql(self, tzname) → tuple[str, str]`

Private helper that converts timezone names to SQL parameter strings based on the `USE_TZ` setting.

- If `settings.USE_TZ` is truthy: returns a 2-tuple of `(f"'{tzname}'", f"'{self.connection.timezone_name}'")`.
- Otherwise: returns `('NULL', 'NULL')`.

#### `datetime_cast_date_sql(self, field_name, tzname) → str`

Returns SQL for casting a datetime column to a date, accounting for timezone conversion:
```sql
django_datetime_cast_time(<field_name>, <tzname_or_NULL>, <connection_tzname_or_NULL>)
```
The second and third parameters come from `_convert_tznames_to_sql(tzname)`.

#### `datetime_cast_time_sql(self, field_name, tzname) → str`

Returns SQL for casting a datetime column to a time:
```sql
django_datetime_cast_time(<field_name>, <tzname_or_NULL>, <connection_tzname_or_NULL>)
```

#### `datetime_extract_sql(self, lookup_type, field_name, tzname) → str`

Returns SQL for extracting a component from a datetime with timezone awareness:
```sql
django_datetime_extract('<lookup_type_lower>', <field_name>, <tzname_or_NULL>, <connection_tzname_or_NULL>)
```

#### `datetime_trunc_sql(self, lookup_type, field_name, tzname) → str`

Returns SQL for truncating a datetime with timezone awareness:
```sql
django_datetime_trunc('<lookup_type_lower>', <field_name>, <tzname_or_NULL>, <connection_tzname_or_NULL>)
```

#### `time_extract_sql(self, lookup_type, field_name) → str`

Returns SQL for extracting a time component:
```sql
django_time_extract('<lookup_type_lower>', <field_name>)
```

#### `pk_default_value(self) → str`

Returns the string `"NULL"`. SQLite auto-increment primary keys are implicit; inserting NULL into an AUTOINCREMENT column triggers auto-generation of the next integer.

#### `_quote_params_for_last_executed_query(self, params) → tuple[str, ...]`

Private helper that quotes parameter values for use in `last_executed_query()`. Only for display/debugging — never for executing SQL.

1. If `len(params) > 999` (the `SQLITE_LIMIT_VARIABLE_NUMBER` default): splits `params` into chunks of 999, recursively calls itself on each chunk, and concatenates the results via tuple addition (`results += ...`).
2. Otherwise: constructs a SQL query string `'SELECT ' + ', '.join(['QUOTE(?)'] * len(params))`, bypasses Django's cursor wrapper by calling `self.connection.connection.cursor()` to get the raw sqlite3 cursor (avoiding infinite recursion from logging), executes the query with `params`, and returns `cursor.execute(sql, params).fetchone()`. The cursor is closed in a `finally` block.

#### `last_executed_query(self, cursor, sql, params) → str | None`

Reconstructs the full SQL string (with parameters substituted as quoted literals) from the raw `sql` template and `params`, for debugging purposes.

- If `params` is truthy:
  - If `isinstance(params, (list, tuple))`: calls `_quote_params_for_last_executed_query(params)` to get a tuple of quoted string values, then returns `sql % params`.
  - Otherwise (`dict`): extracts `tuple(params.values())`, quotes them via `_quote_params_for_last_executed_query()`, reconstructs the dict as `dict(zip(params, quoted_values))`, and returns `sql % params`.
- If `params` is falsy: returns `sql` unchanged (for consistency with `SQLiteCursorWrapper.execute()`).

#### `quote_name(self, name) → str`

Quotes a database object name for use in SQL.

- If `name` already starts and ends with double quotes (`"..."`): returns it unchanged (quoting once is sufficient).
- Otherwise: wraps the name in double quotes: `'"%s"' % name`.

#### `no_limit_value(self) → int`

Returns `-1`. SQLite uses -1 to represent "no LIMIT" internally.

#### `__references_graph(self, table_name) → list[str]`

Private method that builds a graph of all tables referencing the given `table_name`, using a recursive CTE with regex matching on foreign key REFERENCES clauses in the SQLite schema.

Executes this SQL query:
```sql
WITH tables AS (
    SELECT <table_name> name
    UNION
    SELECT sqlite_master.name
    FROM sqlite_master
    JOIN tables ON (sql REGEXP (?i)\s+references\s+("|\')?) || tables.name || ("|\')?\s*\()
) SELECT name FROM tables;
```

Parameters: `(table_name, r'(?i)\s+references\s+("|\')?', r'("|\')?\s*\(')` — the regex matches REFERENCES keywords (case-insensitive) followed by an optional quoted or unquoted table name. Returns a list of all referenced table names from `cursor.fetchall()`.

#### `_references_graph` (`@cached_property`) → callable

Wraps `__references_graph` with `lru_cache(maxsize=512)` and caches it as a cached property. The max size of 512 is chosen to comfortably fit Django's test suite (~330 tables). This provides memoization across calls while keeping memory bounded.

#### `sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False) → list[str]`

Generates SQL statements to flush (truncate) the given tables.

1. If `tables` is non-empty and `allow_cascade` is truthy: replaces `tables` with a set of all transitively referenced tables by computing `set(chain.from_iterable(self._references_graph(table) for table in tables))`.
2. Builds a list of DELETE statements, one per table: `'DELETE FROM "<table_name>";'` using `style.SQL_KEYWORD('DELETE')`, `style.SQL_KEYWORD('FROM')`, and `self.quote_name(table)`.
3. If `reset_sequences` is truthy: extends the SQL list with sequence reset statements via `self.sequence_reset_by_name_sql(style, [{'table': table} for table in tables])`.
4. Returns the complete list of SQL strings.

#### `sequence_reset_by_name_sql(self, style, sequences) → list[str]`

Generates SQL to reset auto-increment counters by updating SQLite's internal `sqlite_sequence` table.

- If `sequences` is empty: returns an empty list `[]`.
- Otherwise: returns a single-element list containing one UPDATE statement:
  ```sql
  UPDATE "sqlite_sequence" SET "seq" = 0 WHERE "name" IN ('<table1>', '<table2>', ...);
  ```
  The table names are drawn from each dict in `sequences` (each has a `'table'` key), quoted with single quotes and joined by commas.

#### `adapt_datetimefield_value(self, value) → str | None`

Adapts a Python datetime object for storage in SQLite as a text string.

1. If `value is None`: returns `None`.
2. If `value` has a `resolve_expression` attribute (i.e., it's an ORM expression): returns `value` unchanged (the database will handle adaptation).
3. If `timezone.is_aware(value)` is truthy:
   - If `settings.USE_TZ`: converts to naive datetime in the connection's timezone via `timezone.make_naive(value, self.connection.timezone)`.
   - Otherwise (`USE_TZ` is falsy): raises `ValueError("SQLite backend does not support timezone-aware datetimes when USE_TZ is False.")`.
4. Returns `str(value)` — the ISO-format string representation of the datetime.

#### `adapt_timefield_value(self, value) → str | None`

Adapts a Python time object for storage in SQLite as a text string.

1. If `value is None`: returns `None`.
2. If `value` has a `resolve_expression` attribute: returns `value` unchanged.
3. If `timezone.is_aware(value)` is truthy: raises `ValueError("SQLite backend does not support timezone-aware times.")`. (TimeField values should never be timezone-aware.)
4. Returns `str(value)`.

#### `get_db_converters(self, expression) → list[callable]`

Returns a list of converter functions to apply when reading database values back into Python objects for the given expression's output field.

1. Starts with the parent class converters: `converters = super().get_db_converters(expression)`.
2. Gets the internal type via `expression.output_field.get_internal_type()`.
3. Appends a converter based on the internal type:
   - `'DateTimeField'`: appends `self.convert_datetimefield_value`.
   - `'DateField'`: appends `self.convert_datefield_value`.
   - `'TimeField'`: appends `self.convert_timefield_value`.
   - `'DecimalField'`: appends the result of `self.get_decimalfield_converter(expression)`.
   - `'UUIDField'`: appends `self.convert_uuidfield_value`.
   - `'NullBooleanField'` or `'BooleanField'`: appends `self.convert_booleanfield_value`.
4. Returns the accumulated list of converters.

#### `convert_datetimefield_value(self, value, expression, connection) → datetime.datetime | None`

Converts a raw database value (text string) to a Python datetime object with timezone awareness.

1. If `value is not None`:
   - If `not isinstance(value, datetime.datetime)`: parses the string via `parse_datetime(value)` and reassigns to `value`.
   - If `settings.USE_TZ` and `not timezone.is_aware(value)`: makes it timezone-aware via `timezone.make_aware(value, self.connection.timezone)`.
2. Returns `value` (either the original datetime, parsed datetime, or None).

#### `convert_datefield_value(self, value, expression, connection) → datetime.date | None`

Converts a raw database value to a Python date object.

1. If `value is not None`:
   - If `not isinstance(value, datetime.date)`: parses the string via `parse_date(value)` and reassigns to `value`.
2. Returns `value`.

#### `convert_timefield_value(self, value, expression, connection) → datetime.time | None`

Converts a raw database value to a Python time object.

1. If `value is not None`:
   - If `not isinstance(value, datetime.time)`: parses the string via `parse_time(value)` and reassigns to `value`.
2. Returns `value`.

#### `get_decimalfield_converter(self, expression) → callable`

Returns a converter function that handles SQLite's limited precision for DecimalField values (SQLite stores only 15 significant digits; float inaccuracy must be removed).

Creates `create_decimal = decimal.Context(prec=15).create_decimal_from_float`.

- If `isinstance(expression, Col)` (i.e., the expression refers to a column): computes `quantize_value = decimal.Decimal(1).scaleb(-expression.output_field.decimal_places)`, then returns a converter function that:
  - If `value is not None`: returns `create_decimal(value).quantize(quantize_value, context=expression.output_field.context)`.
- Otherwise (not a Col): returns a converter function that:
  - If `value is not None`: returns `create_decimal(value)` (no quantization applied).

#### `convert_uuidfield_value(self, value, expression, connection) → uuid.UUID | None`

Converts a raw database string to a Python UUID object.

1. If `value is not None`: converts via `uuid.UUID(value)`.
2. Returns the resulting UUID or None.

#### `convert_booleanfield_value(self, value, expression, connection) → bool | int | None`

Converts SQLite boolean values (stored as integers 0/1) to Python booleans.

- If `value in (1, 0)`: returns `bool(value)` (`True` for 1, `False` for 0).
- Otherwise: returns `value` unchanged (handles None or other unexpected values).

#### `bulk_insert_sql(self, fields, placeholder_rows) → str`

Generates SQL for bulk inserts using SQLite's `UNION ALL SELECT ...` pattern.

Returns a string formed by joining each row of placeholders with `" UNION ALL "`:
```sql
SELECT <placeholder1>,<placeholder2>,... UNION ALL SELECT <placeholder1>,<placeholder2>,... UNION ALL ...
```
Each `row` in `placeholder_rows` is joined with commas to form one `SELECT` sub-statement.

#### `combine_expression(self, connector, sub_expressions) → str`

Combines two or more expressions with a given operator connector, handling SQLite-specific operators.

- If `connector == '^'`: returns `'POWER(%s)' % ','.join(sub_expressions)` (SQLite lacks a native exponentiation operator; uses the custom POWER function registered at connection time).
- If `connector == '#'` (bitwise XOR): returns `'BITXOR(%s)' % ','.join(sub_expressions)` (uses the custom BITXOR function).
- Otherwise: delegates to `super().combine_expression(connector, sub_expressions)`.

#### `combine_duration_expression(self, connector, sub_expressions) → str`

Combines timedelta expressions for arithmetic operations.

1. If `connector not in ['+', '-']`: raises `DatabaseError('Invalid connector for timedelta: <connector>.')`.
2. Builds `fn_params = ["'<connector>'"] + list(sub_expressions)` (the connector is the first parameter to the custom function).
3. If `len(fn_params) > 3`: raises `ValueError('Too many params for timedelta operations.')`.
4. Returns `"django_format_dtdelta(<params>)"` where `<params>` is the comma-joined list of connector and sub-expression SQL strings.

#### `integer_field_range(self, internal_type) → tuple[None, None]`

Returns `(None, None)` indicating that SQLite does not enforce any integer range constraints (all integer types are unbounded).

#### `subtract_temporals(self, internal_type, lhs, rhs) → tuple[str, tuple]`

Generates SQL for subtracting two temporal values. Each of `lhs` and `rhs` is a `(sql_string, params_tuple)` pair.

1. Combines parameters: `params = (*lhs_params, *rhs_params)`.
2. If `internal_type == 'TimeField'`: returns `('django_time_diff(<lhs_sql>, <rhs_sql>)', params)`.
3. Otherwise (datetime or date): returns `('django_timestamp_diff(<lhs_sql>, <rhs_sql>)', params)`.

#### `insert_statement(self, ignore_conflicts=False) → str`

Returns the INSERT statement prefix for SQLite.

- If `ignore_conflicts` is truthy: returns `'INSERT OR IGNORE INTO'` (SQLite's conflict resolution mechanism).
- Otherwise: delegates to `super().insert_statement(ignore_conflicts)` (the base class default, typically `'INSERT INTO'`).

## django/db/models/expressions.py
Now I have the complete file. Here is the full specification:

---

# Module-Level Preamble

## Imports

```python
import copy
import datetime
import functools
from collections import defaultdict
from decimal import Decimal
from enum import Enum
from itertools import chain
from types import NoneType
from uuid import UUID

from django.core.exceptions import EmptyResultSet, FieldError, FullResultSet
from django.db import DatabaseError, NotSupportedError, connection
from django.db.models import fields
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query_utils import Q
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property, classproperty
from django.utils.hashable import make_hashable
from django.utils.inspect import signature
```

## Constants & Globals

- **`_connector_combinations`** — A list of dicts mapping connector strings (`"+"`, `"-"`, `"*"`, `"/"`, `"^"`, `"%%"`, `"&"`, `"|"`, `"<<"`, `">>"`, `"#"`) to lists of `(lhs_field_type, rhs_field_type, result_field_type)` tuples. Defines type-inference rules for `CombinedExpression.output_field`. Covers:
  - Same-type numeric ops (`PositiveIntegerField` → `PositiveIntegerField` for `+`,`*`,`/`,`%`,`^`; `IntegerField`/`FloatField`/`DecimalField` → same for all except subtraction).
  - Mixed-type numeric ops (e.g. `IntegerField` + `DecimalField` → `DecimalField`).
  - Bitwise operators: always `IntegerField` × `IntegerField` → `IntegerField`.
  - Numeric with `NoneType`: `(field, None) → field`, `(None, field) → field`.
  - Date/DateTimeField + DurationField → DateTimeField (ADD only).
  - DurationField ± DurationField → DurationField.
  - TimeField + DurationField → TimeField (ADD); TimeField − TimeField → DurationField (SUB).
  - DateField − DateField/DateTimeField → DurationField; DateTimeField − DateField/DateTimeField → DurationField.

- **`_connector_combinators`** — A `defaultdict(list)` populated at module load by iterating `_connector_combinations` and calling `register_combinable_fields(lhs, connector, rhs, result)`. Used as a lookup table for `_resolve_combined_type()`.

---

# Code Objects (Classes and Functions)

## `SQLiteNumericMixin`

A mixin class. Provides one method:

- **`as_sqlite(self, compiler, connection, **extra_context)`** — Calls `self.as_sql(compiler, connection, **extra_context)`, then if `self.output_field.get_internal_type() == "DecimalField"`, wraps the SQL in `(CAST(%s AS NUMERIC))`. Catches `FieldError` silently. Returns `(sql, params)`.

## `Combinable`

Base class providing arithmetic and bitwise operators that return `CombinedExpression` instances. Class attributes:
- `ADD = "+"`, `SUB = "-"`, `MUL = "*"`, `DIV = "/"`, `POW = "^"`, `MOD = "%%"` (double-percent for parameter-substitution safety).
- `BITAND = "&"`, `BITOR = "|"`, `BITLEFTSHIFT = "<<"`, `BITRIGHTSHIFT = ">>"`, `BITXOR = "#"`.

Methods:
- **`_combine(self, other, connector, reversed)`** — If `other` lacks `resolve_expression`, wraps it in `Value(other)`. Returns `CombinedExpression(other, connector, self)` if `reversed`, else `CombinedExpression(self, connector, other)`.
- **Arithmetic dunder methods:** `__neg__` → `_combine(-1, MUL, False)`; `__add__`/`__sub__`/`__mul__`/`__truediv__`/`__mod__`/`__pow__` → respective connector with `reversed=False`.
- **Bitwise dunder methods:** `__and__`, `__xor__`, `__or__` — If both operands have `conditional=True`, delegate to `Q(self) & Q(other)` / `^` / `|`; else raise `NotImplementedError`. Dedicated methods: `bitand()`, `bitleftshift()`, `bitrightshift()`, `bitxor()`, `bitor()` → `_combine(..., connector, False)`.
- **Reversed arithmetic:** `__radd__`, `__rsub__`, `__rmul__`, `__rtruediv__`, `__rmod__`, `__rpow__` → respective connector with `reversed=True`.
- **Reversed bitwise:** `__rand__`, `__ror__`, `__rxor__` — all raise `NotImplementedError`.
- **`__invert__(self)`** — Returns `NegatedExpression(self)`.

## `OutputFieldIsNoneError(FieldError)`

Empty subclass of `FieldError`. Raised when an expression's `_resolve_output_field()` returns `None`.

## `BaseExpression`

Abstract base class for all query expressions. Class attributes:
- `empty_result_set_value = NotImplemented`
- `is_summary = False`
- `filterable = True`
- `window_compatible = False`
- `allowed_default = False`
- `constraint_validation_compatible = True`
- `set_returning = False`
- `allows_composite_expressions = False`

Methods:
- **`__init__(self, output_field=None)`** — If `output_field is not None`, sets `self.output_field`.
- **`__getstate__(self)`** — Returns a copy of `__dict__` with `"convert_value"` key removed.
- **`get_db_converters(self, connection)`** — Returns `[self.convert_value] + self.output_field.get_db_converters(connection)` if `self.convert_value is not self._convert_value_noop`, else just the field converters.
- **`get_source_expressions(self)`** — Returns `[]`.
- **`set_source_expressions(self, exprs)`** — Asserts `exprs` is empty.
- **`_parse_expressions(self, *expressions)`** — Converts each arg: if it has `resolve_expression`, keep as-is; if string, wrap in `F(arg)`; else wrap in `Value(arg)`. Returns list.
- **`as_sql(self, compiler, connection)`** — Raises `NotImplementedError`. Must return `(sql, params)`.
- **`contains_aggregate` (cached_property)** — True if any source expression has `contains_aggregate=True`.
- **`contains_over_clause` (cached_property)** — True if any source expression has `contains_over_clause=True`.
- **`contains_column_references` (cached_property)** — True if any source expression has `contains_column_references=True`.
- **`contains_subquery` (cached_property)** — True if any source has attribute `subquery` or recursively `contains_subquery`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Copies self via `copy()`, sets `c.is_summary = summarize`, resolves each source expression recursively, checks that no source is a `ColPairs` if `allows_composite_expressions` is False (raises `ValueError`), calls `set_source_expressions(source_expressions)`, returns the copy.
- **`conditional` (property)** — True if `self.output_field` is an instance of `BooleanField`.
- **`field` (property)** — Returns `self.output_field`.
- **`output_field` (cached_property)** — Calls `_resolve_output_field()`. If result is None, raises `OutputFieldIsNoneError`; else returns the field.
- **`_output_field_or_none` (property)** — Returns `self.output_field`, or `None` if `OutputFieldIsNoneError` was raised.
- **`_resolve_output_field(self)`** — Iterates source fields from `get_source_fields()`. If all non-None sources share the same class, returns that field type; else raises `FieldError` for mixed types.
- **`_convert_value_noop(value, expression, connection)` (static)** — Returns value unchanged.
- **`convert_value` (cached_property)** — Returns a lambda converting DB values: `None → None`, otherwise `float()` for FloatField, `int()` for IntegerField subclasses, `Decimal()` for DecimalField; else `_convert_value_noop`.
- **`get_lookup(self, lookup)`** — Delegates to `self.output_field.get_lookup(lookup)`.
- **`get_transform(self, name)`** — Delegates to `self.output_field.get_transform(name)`.
- **`relabeled_clone(self, change_map)`** — Copies self and recursively relabels each source expression via `relabeled_clone(change_map)`.
- **`replace_expressions(self, replacements)`** — If `replacements` is empty or maps self directly, returns the replacement. Otherwise copies self and recursively replaces each source; returns clone.
- **`get_refs(self)`** — Returns a set of all refs from source expressions.
- **`copy(self)`** — Returns `copy.copy(self)`.
- **`prefix_references(self, prefix)`** — Copies self; for each source: if it's an `F`, creates `F(f"{prefix}{expr.name}")`; else calls `prefix_references(prefix)` recursively.
- **`get_group_by_cols(self)`** — If not containing aggregate, returns `[self]`. Else collects group-by cols from all sources.
- **`get_source_fields(self)`** — Returns list of `_output_field_or_none` for each source expression.
- **`asc(self, **kwargs)`** — Returns `OrderBy(self, **kwargs)`.
- **`desc(self, **kwargs)`** — Returns `OrderBy(self, descending=True, **kwargs)`.
- **`reverse_ordering(self)`** — Returns self.
- **`flatten(self)`** — Generator: yields self, then depth-first yields from each source's `flatten()` or the source itself.
- **`select_format(self, compiler, sql, params)`** — If output_field has `select_format`, delegates; else returns `(sql, params)`.
- **`get_expression_for_validation(self)`** — If `constraint_validation_compatible` is False, extracts and returns the single source expression (raises `ValueError` if more than one); else returns self.

## `Expression(BaseExpression, Combinable)`

Adds identity-based equality/hashing for caching. Decorated with `@deconstructible`. Class attribute:
- **`_constructor_signature`** — Cached classproperty returning `signature(cls.__init__)`.

Methods:
- **`_identity(cls, value)` (classmethod)** — Normalizes values to hashable form: tuples → mapped recursively; dicts → sorted key-value tuple pairs; Field instances with name+model → `(model._meta.label, field.name)`, else `type(value)`; everything else via `make_hashable()`.
- **`identity` (cached_property)** — Binds `_constructor_signature` to self + args/kwargs, applies defaults, skips first argument (`self`), maps each value through `_identity()`, returns a tuple of `(class, (arg_name, normalized_value), ...)`.
- **`__eq__(self, other)`** — Returns `NotImplemented` if not an Expression; else compares `other.identity == self.identity`.
- **`__hash__(self)`** — Returns `hash(self.identity)`.

## `_resolve_combined_type(connector, lhs_type, rhs_type)`

Cached function (`lru_cache(maxsize=128)`). Looks up `_connector_combinators[connector]`, iterates `(combinator_lhs, combinator_rhs, combined_type)` tuples, returns the first `combined_type` where `lhs_type` is subclass of `combinator_lhs` and `rhs_type` is subclass of `combinator_rhs`. Returns `None` if no match.

## `register_combinable_fields(lhs, connector, rhs, result)`

Registers a type-inference rule: appends `(lhs, rhs, result)` to `_connector_combinators[connector]`. Called at module load time for all entries in `_connector_combinations`.

## `CombinedExpression(SQLiteNumericMixin, Expression)`

Represents binary operations between expressions.

Attributes (set in `__init__`):
- `self.connector` — connector string (`+`, `-`, etc.)
- `self.lhs` — left-hand expression
- `self.rhs` — right-hand expression

Methods:
- **`__init__(self, lhs, connector, rhs, output_field=None)`** — Calls parent with `output_field`; stores `connector`, `lhs`, `rhs`.
- **`__repr__(self)`** — `<CombinedExpression: {str(self)}>`
- **`__str__(self)`** — `"{lhs} {connector} {rhs}"`
- **`get_source_expressions(self)`** — Returns `[self.lhs, self.rhs]`.
- **`set_source_expressions(self, exprs)`** — Unpacks to `self.lhs, self.rhs = exprs`.
- **`_resolve_output_field(self)`** — Calls `_resolve_combined_type(connector, type(lhs._output_field_or_none), type(rhs._output_field_or_none))`. If None, raises `FieldError`; else returns `combined_type()`.
- **`as_sql(self, compiler, connection)`** — Compiles lhs and rhs via `compiler.compile()`, collects SQL fragments and params. Wraps in `(sql)`. Uses `connection.ops.combine_expression(connector, expressions)`. Returns `("(%s)", params)`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Resolves via parent. If not a `DurationExpression` or `TemporalSubtraction`: checks if one side is `DurationField` and the other isn't → returns `DurationExpression(resolved.lhs, resolved.connector, resolved.rhs)`. If connector is SUB and both sides are same datetime field type → returns `TemporalSubtraction(resolved.lhs, resolved.rhs)`. Else returns resolved.
- **`allowed_default` (cached_property)** — True if both lhs and rhs have `allowed_default=True`.

## `DurationExpression(CombinedExpression)`

Handles duration arithmetic with backend-specific formatting.

Methods:
- **`compile(self, side, compiler, connection)`** — If side's output field is a DurationField, compiles via `compiler.compile()` then wraps SQL with `connection.ops.format_for_duration_arithmetic(sql)`. Else just returns `compiler.compile(side)`.
- **`as_sql(self, compiler, connection)`** — If backend has native duration fields, delegates to parent. Otherwise: checks expression support, compiles lhs/rhs via `self.compile()`, joins via `connection.ops.combine_duration_expression(connector, expressions)`, wraps in `(sql)`.
- **`as_sqlite(self, compiler, connection, **extra_context)`** — Calls `as_sql()`. If connector is MUL or DIV, validates that both lhs and rhs types are in `{DecimalField, DurationField, FloatField, IntegerField}`; raises `DatabaseError` otherwise.

## `TemporalSubtraction(CombinedExpression)`

Specializes subtraction of temporal values to produce a duration. Class attribute:
- `output_field = fields.DurationField()`

Methods:
- **`__init__(self, lhs, rhs)`** — Calls parent with `(lhs, SUB, rhs)`.
- **`as_sql(self, compiler, connection)`** — Checks expression support, compiles lhs/rhs, returns `connection.ops.subtract_temporals(lhs_internal_type, lhs_sql, rhs_sql)`.

## `F(Combinable)`

Reference to a model field in queries. Decorated with `@deconstructible(path="django.db.models.F")`. Class attribute:
- `allowed_default = False`

Methods:
- **`__init__(self, name)`** — Stores `self.name`.
- **`__repr__(self)`** — `"F({name})"`.
- **`__getitem__(self, subscript)`** — Returns `Sliced(self, subscript)`.
- **`__contains__(self, other)`** — Raises `TypeError`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Delegates to `query.resolve_ref(self.name, ...)`.
- **`replace_expressions(self, replacements)`** — If self is in replacements, returns replacement. Otherwise splits name by `LOOKUP_SEP`; if no transforms, returns self. Looks up base field in replacements; if found and has output_field, applies each transform sequentially via `get_transform()`. Returns final replacement or self.
- **`asc(self, **kwargs)`** — Returns `OrderBy(self, **kwargs)`.
- **`desc(self, **kwargs)`** — Returns `OrderBy(self, descending=True, **kwargs)`.
- **`__eq__(self, other)`** — True if same class and same name.
- **`__hash__(self)`** — Hash of name.
- **`copy(self)`** — Returns `copy.copy(self)`.

## `ResolvedOuterRef(F)`

An outer query reference that has been resolved into a column. Class attributes:
- `contains_aggregate = False`, `contains_over_clause = False`

Methods:
- **`as_sql(self, *args, **kwargs)`** — Raises `ValueError` (must only be used in subqueries).
- **`resolve_expression(self, *args, **kwargs)`** — Calls parent; if result contains over clause, raises `NotSupportedError`; sets `col.possibly_multivalued = LOOKUP_SEP in self.name`. Returns the column.
- **`relabeled_clone(self, relabels)`** — Returns self (no alias to relabel).
- **`get_group_by_cols(self)`** — Returns `[]`.

## `OuterRef(F)`

Unresolved outer query reference. Class attributes:
- `contains_aggregate = False`, `contains_over_clause = False`

Methods:
- **`resolve_expression(self, *args, **kwargs)`** — If self.name is itself an OuterRef, returns it; else returns `ResolvedOuterRef(self.name)`.
- **`relabeled_clone(self, relabels)`** — Returns self.

## `Sliced(F)`

Represents a slice of an F expression (e.g., `F('field')[0:2]`).

Methods:
- **`__init__(self, obj, subscript)`** — Calls parent with `obj.name`. Stores `self.obj`. Validates subscript: int ≥ 0 → `start = subscript + 1`, `length = 1`; slice → validates no negative indices, no step, stop > start; sets `start = 1 if None else subscript.start + 1`, `length = None or (stop - (start or 0))`. Raises `ValueError`/`TypeError` on invalid input.
- **`__repr__(self)`** — `"Sliced({obj!r}, {slice(start, stop)!r})"`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Resolves the column via `query.resolve_ref()`. If obj is OuterRef or Sliced, resolves it recursively. Returns `resolved.output_field.slice_expression(expr, self.start, self.length)`.

## `Func(SQLiteNumericMixin, Expression)`

An SQL function call. Decorated with `@deconstructible(path="django.db.models.Func")`. Class attributes:
- `function = None` — name of the SQL function
- `template = "%(function)s(%(expressions)s)"`
- `arg_joiner = ", "`
- `arity = None`

Methods:
- **`__init__(self, *expressions, output_field=None, **extra)`** — If arity is not None and len(expressions) != arity, raises `TypeError`. Calls parent with `output_field`; sets `self.source_expressions = self._parse_expressions(*expressions)`; stores `self.extra = extra`.
- **`__repr__(self)`** — Joins source expressions with `arg_joiner`, appends sorted extra kwargs.
- **`_get_repr_options(self)`** — Returns `{}` (overridable).
- **`get_source_expressions(self)`** — Returns `self.source_expressions`.
- **`set_source_expressions(self, exprs)`** — Sets `self.source_expressions = exprs`.
- **`as_sql(self, compiler, connection, function=None, template=None, arg_joiner=None, **extra_context)`** — Checks expression support. For each source: compiles via `compiler.compile()`, catching `EmptyResultSet` (replaces with `Value(empty_result_set_value)`) and `FullResultSet` (replaces with `Value(True)`). Builds data dict from extra + extra_context; sets function/template/arg_joiner in priority order (method param > init extra > class attr). Sets `expressions = field = arg_joiner.join(sql_parts)`. Returns `template % data, params`.
- **`copy(self)`** — Copies parent, then copies `source_expressions[:]` and `extra.copy()`.
- **`allowed_default` (cached_property)** — True if all source expressions have `allowed_default=True`.

## `Value(SQLiteNumericMixin, Expression)`

Represents a literal value in an expression. Decorated with `@deconstructible(path="django.db.models.Value")`. Class attributes:
- `for_save = False`
- `allowed_default = True`

Methods:
- **`__init__(self, value, output_field=None)`** — Calls parent; stores `self.value`.
- **`__repr__(self)`** — `"Value({value!r})"`.
- **`as_sql(self, compiler, connection)`** — Checks expression support. If `_output_field_or_none` is not None: if `for_save`, calls `output_field.get_db_prep_save(val, connection)`; else `get_db_prep_value()`. If field has `get_placeholder`, returns `(placeholder, [val])`. If value is None, returns `"NULL", []`; else `"%s", [val]`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Calls parent; sets `c.for_save = for_save`; returns copy.
- **`get_group_by_cols(self)`** — Returns `[]`.
- **`_resolve_output_field(self)`** — Type inference: str → CharField, bool → BooleanField, int → IntegerField, float → FloatField, datetime.datetime → DateTimeField, datetime.date → DateField, datetime.time → TimeField, datetime.timedelta → DurationField, Decimal → DecimalField, bytes → BinaryField, UUID → UUIDField. Returns None if no match (caller raises).
- **`empty_result_set_value` (property)** — Returns `self.value`.

## `RawSQL(Expression)`

Wraps raw SQL strings. Class attribute:
- `allowed_default = True`

Methods:
- **`__init__(self, sql, params, output_field=None)`** — If output_field is None, uses `fields.Field()`. Stores `sql`, `params`; calls parent.
- **`__repr__(self)`** — `"RawSQL({sql}, {params})"`.
- **`as_sql(self, compiler, connection)`** — Returns `"(%s)" % self.sql, self.params`.
- **`get_group_by_cols(self)`** — Returns `[self]`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — If query has a model, iterates parent fields and resolves refs if the parent field column name appears in `self.sql.lower()`. Calls parent resolve.

## `Star(Expression)`

Represents the SQL `*` wildcard.

Methods:
- **`__repr__(self)`** — `"'*'"`.
- **`as_sql(self, compiler, connection)`** — Returns `"*", []`.

## `DatabaseDefault(Expression)`

Expression that uses the SQL `DEFAULT` keyword during INSERT.

Methods:
- **`__init__(self, expression, output_field=None)`** — Calls parent; stores `self.expression`.
- **`get_source_expressions(self)`** — Returns `[self.expression]`.
- **`set_source_expressions(self, exprs)`** — Unpacks `(self.expression,) = exprs`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Resolves the inner expression. If `for_save`, returns a new `DatabaseDefault(resolved_expression, output_field=self._output_field_or_none)`. Else returns the resolved expression directly.
- **`as_sql(self, compiler, connection)`** — If backend supports `DEFAULT` keyword in INSERT, returns `"DEFAULT", []`; else delegates to `compiler.compile(self.expression)`.

## `Col(Expression)`

Represents a reference to a model column in SQL. Class attributes:
- `contains_column_references = True`
- `possibly_multivalued = False`

Methods:
- **`__init__(self, alias, target, output_field=None)`** — If output_field is None, uses `target`. Stores `alias`, `target`; calls parent with `output_field`.
- **`__repr__(self)`** — `"Col({alias}, {target})"` or `"Col({target})"` if no alias.
- **`as_sql(self, compiler, connection)`** — Builds dot-separated identifier from `(alias, column)` or just `(column)`, quoting via `compiler.quote_name_unless_alias`. Returns `(sql, [])`.
- **`relabeled_clone(self, relabels)`** — If alias is None, returns self; else creates new Col with `relabels.get(alias, alias)`, same target and output_field.
- **`get_group_by_cols(self)`** — Returns `[self]`.
- **`get_db_converters(self, connection)`** — If `target == output_field`, returns field converters; else concatenates output_field + target converters.

## `ColPairs(Expression)`

Represents a set of columns for composite primary key support.

Methods:
- **`__init__(self, alias, targets, sources, output_field)`** — Calls parent with `output_field`; stores `alias`, `targets`, `sources`.
- **`__len__(self)`** — Returns `len(self.targets)`.
- **`__iter__(self)`** — Returns `iter(self.get_cols())`.
- **`__repr__(self)`** — `"ColPairs({alias!r}, {targets!r}, {sources!r}, {output_field!r})"`.
- **`get_cols(self)`** — Creates `[Col(alias, target, source) for target, source in zip(targets, sources)]`.
- **`get_source_expressions(self)`** — Returns `self.get_cols()`.
- **`set_source_expressions(self, exprs)`** — Asserts all are Col with matching alias; sets targets/sources from col.target/col.field.
- **`as_sql(self, compiler, connection)`** — Compiles each Col, joins SQL with `,`, collects params. Returns `(joined_sql, flat_params)`.
- **`relabeled_clone(self, relabels)`** — Creates new ColPairs with relabeled alias, same targets/sources/field.
- **`resolve_expression(self, *args, **kwargs)`** — Returns self.
- **`select_format(self, compiler, sql, params)`** — Returns `(sql, params)`.

## `Ref(Expression)`

Reference to a column alias in the query (e.g., from an annotation).

Methods:
- **`__init__(self, refs, source)`** — Calls parent with no output_field; stores `refs`, `source`.
- **`__repr__(self)`** — `"Ref({refs}, {source})"`.
- **`get_source_expressions(self)`** — Returns `[self.source]`.
- **`set_source_expressions(self, exprs)`** — Unpacks `(self.source,) = exprs`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Returns self (source already resolved).
- **`get_refs(self)`** — Returns `{self.refs}`.
- **`relabeled_clone(self, relabels)`** — Copies self; sets `clone.source = self.source.relabeled_clone(relabels)`.
- **`as_sql(self, compiler, connection)`** — Returns `(connection.ops.quote_name(self.refs), [])`.
- **`get_group_by_cols(self)`** — Returns `[self]`.

## `ExpressionList(Func)`

A list of expressions (e.g., for PARTITION BY clauses). Class attribute:
- `template = "%(expressions)s"`

Methods:
- **`__str__(self)`** — Joins source expression strings with `arg_joiner`.
- **`as_sql(self, *args, **kwargs)`** — If no source expressions, returns `"", ()`; else delegates to parent.
- **`as_sqlite(self, compiler, connection, **extra_context)`** — Delegates to `self.as_sql()` (no numeric casting needed).
- **`get_group_by_cols(self)`** — Collects group-by cols from all source expressions.

## `OrderByList(ExpressionList)`

Specialized ExpressionList for ORDER BY clauses. Class attributes:
- `allowed_default = False`
- `template = "ORDER BY %(expressions)s"`

Methods:
- **`__init__(self, *expressions, **extra)`** — Converts string expressions starting with `"-"` to `OrderBy(F(expr[1:]), descending=True)`. Calls parent.

## `ExpressionWrapper(SQLiteNumericMixin, Expression)`

Wraps an expression to provide explicit output_field context. Decorated with `@deconstructible(path="django.db.models.ExpressionWrapper")`.

Methods:
- **`__init__(self, expression, output_field)`** — Calls parent with `output_field`; stores `self.expression`.
- **`set_source_expressions(self, exprs)`** — Sets `self.expression = exprs[0]`.
- **`get_source_expressions(self)`** — Returns `[self.expression]`.
- **`get_group_by_cols(self)`** — If expression is an Expression, copies it and sets its output_field to self's; returns that copy's group-by cols. Else delegates to parent.
- **`as_sql(self, compiler, connection)`** — Delegates to `compiler.compile(self.expression)`.
- **`__repr__(self)`** — `"ExpressionWrapper({expression})"`.
- **`allowed_default` (property)** — Returns `self.expression.allowed_default`.

## `NegatedExpression(ExpressionWrapper)`

Logical negation of a conditional expression.

Methods:
- **`__init__(self, expression)`** — Calls parent with `expression`, `output_field=BooleanField()`.
- **`__invert__(self)`** — Returns `self.expression.copy()`.
- **`as_sql(self, compiler, connection)`** — Compiles via parent. If EmptyResultSet: if backend doesn't support boolean in select, returns `"1=1", ()`; else compiles `Value(True)`. Otherwise: if expression not supported in WHERE clause, returns `"CASE WHEN {sql} = 0 THEN 1 ELSE 0 END", params`; else `"NOT {sql}", params`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Resolves via parent. If resolved expression is not conditional, raises `TypeError`. Returns resolved.
- **`select_format(self, compiler, sql, params)`** — If backend doesn't support boolean in select AND expression is supported in WHERE clause (avoiding double-wrap), returns `"CASE WHEN {sql} THEN 1 ELSE 0 END", params`; else `(sql, params)`.

## `When(Expression)`

A single WHEN…THEN branch for Case. Decorated with `@deconstructible(path="django.db.models.When")`. Class attributes:
- `template = "WHEN %(condition)s THEN %(result)s"`
- `conditional = False`

Methods:
- **`__init__(self, condition=None, then=None, **lookups)`** — If lookups provided and condition is None or conditional, wraps in `Q()`. Validates condition is a Q object, boolean expression, or lookups; raises `TypeError` if not. Raises `ValueError` for empty Q(). Calls parent with no output_field. Stores `self.condition`, `self.result = _parse_expressions(then)[0]`.
- **`__str__(self)`** — `"WHEN {condition!r} THEN {result!r}"`.
- **`__repr__(self)`** — `"<When: {str(self)}>"`.
- **`get_source_expressions(self)`** — Returns `[self.condition, self.result]`.
- **`set_source_expressions(self, exprs)`** — Unpacks to `condition, result = exprs`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Copies via parent. If `for_save`, re-resolves condition with `for_save=False`. Returns copy.
- **`get_source_fields(self)`** — Returns `[self.result._output_field_or_none]`.
- **`as_sql(self, compiler, connection, template=None, **extra_context)`** — Checks expression support. Compiles condition and result. Returns `(template % {condition: cond_sql, result: res_sql}, flat_params)`.
- **`get_group_by_cols(self)`** — Collects group-by cols from both sources (not a complete expression).
- **`allowed_default` (cached_property)** — True if both condition and result have `allowed_default=True`.

## `Case(SQLiteNumericMixin, Expression)`

An SQL searched CASE…WHEN…ELSE expression. Decorated with `@deconstructible(path="django.db.models.Case")`. Class attributes:
- `template = "CASE %(cases)s ELSE %(default)s END"`
- `case_joiner = " "`

Methods:
- **`__init__(self, *cases, default=None, output_field=None, **extra)`** — Validates all positional args are When instances. Calls parent with `output_field`. Stores `self.cases = list(cases)`, `self.default = _parse_expressions(default)[0]`, `self.extra = extra`.
- **`__str__(self)`** — `"CASE {cases}, ELSE {default!r}"`.
- **`__repr__(self)`** — `"<Case: {str(self)}>"`.
- **`get_source_expressions(self)`** — Returns `self.cases + [self.default]`.
- **`set_source_expressions(self, exprs)`** — Unpacks: `*cases, default = exprs`.
- **`copy(self)`** — Copies parent; copies `cases[:]`.
- **`as_sql(self, compiler, connection, template=None, case_joiner=None, **extra_context)`** — Checks expression support. If no cases, compiles and returns default. Iterates cases: compiles each; skips EmptyResultSet; on FullResultSet, breaks to compile result and exit loop. Collects SQL parts and params. Compiles default if no cases matched or after break. Joins case_parts with `case_joiner`. Sets template from param/extra/class priority. If `_output_field_or_none` is not None, wraps SQL in `connection.ops.unification_cast_sql(output_field) % sql`. Returns `(sql, params)`.
- **`get_group_by_cols(self)`** — If no cases, returns default's group-by cols; else delegates to parent.
- **`allowed_default` (cached_property)** — True if default and all cases have `allowed_default=True`.

## `Subquery(BaseExpression, Combinable)`

An explicit subquery expression. Class attributes:
- `template = "(%(subquery)s)"`
- `contains_aggregate = False`
- `empty_result_set_value = None`
- `subquery = True`

Methods:
- **`__init__(self, queryset, output_field=None, **extra)`** — Clones the queryset's query (supports both QuerySet and sql.Query); sets `query.subquery = True`. Stores `self.extra`; calls parent with `output_field`.
- **`get_source_expressions(self)`** — Returns `[self.query]`.
- **`set_source_expressions(self, exprs)`** — Sets `self.query = exprs[0]`.
- **`_resolve_output_field(self)`** — Returns `self.query.output_field`.
- **`copy(self)`** — Copies parent; deep-clones the query.
- **`external_aliases` (property)** — Delegates to `self.query.external_aliases`.
- **`get_external_cols(self)`** — Delegates to `self.query.get_external_cols()`.
- **`as_sql(self, compiler, connection, template=None, **extra_context)`** — Checks expression support. Builds subquery SQL via `self.query.as_sql(compiler, connection)`. Strips outer parens from subquery SQL. Returns `(template % {subquery: stripped_sql}, sql_params)`.
- **`get_group_by_cols(self)`** — Delegates to `self.query.get_group_by_cols(wrapper=self)`.

## `Exists(Subquery)`

An EXISTS() subquery expression. Class attributes:
- `template = "EXISTS(%(subquery)s)"`
- `output_field = fields.BooleanField()`
- `empty_result_set_value = False`

Methods:
- **`__init__(self, queryset, **kwargs)`** — Calls parent; wraps query with `.exists()`.
- **`select_format(self, compiler, sql, params)`** — If backend doesn't support boolean in select clause, returns `"CASE WHEN {sql} THEN 1 ELSE 0 END", params`; else `(sql, params)`.
- **`as_sql(self, compiler, *args, **kwargs)`** — Tries parent as_sql. On EmptyResultSet: if no boolean support, returns `"1=0", ()`; else compiles `Value(False)`.

## `OrderBy(Expression)`

Represents an ORDER BY clause element. Decorated with `@deconstructible(path="django.db.models.OrderBy")`. Class attributes:
- `template = "%(expression)s %(ordering)s"`
- `conditional = False`
- `constraint_validation_compatible = False`
- `allows_composite_expressions = True`

Methods:
- **`__init__(self, expression, descending=False, nulls_first=None, nulls_last=None)`** — Validates mutually exclusive/null-only nulls_first/nulls_last. Stores `nulls_first`, `nulls_last`, `descending`. If expression lacks `resolve_expression`, raises `ValueError`. Stores `expression`.
- **`__repr__(self)`** — `"OrderBy({expression}, descending={descending})"`.
- **`set_source_expressions(self, exprs)`** — Sets `self.expression = exprs[0]`.
- **`get_source_expressions(self)`** — Returns `[self.expression]`.
- **`as_sql(self, compiler, connection, template=None, **extra_context)`** — If expression is ColPairs: iterates cols, compiles each copy of OrderBy, joins with `,`. Otherwise: if backend supports NULLS modifier and nulls_last/nulls_first set, appends `NULLS LAST`/`NULLS FIRST` to template. Else (fallback): uses IS NULL / IS NOT NULL trick based on descending + backend's order_by_nulls_first setting. Checks expression support. Compiles expression. Sets placeholders: `{expression: sql, ordering: DESC/ASC}`. Multiplies params for repeated `%(expression)s`. Returns `(template.rstrip(), params)`.
- **`as_oracle(self, compiler, connection)`** — If backend doesn't support boolean in select AND expression is conditional, wraps expression in `Case(When(expression, then=True), default=False)`, compiles copy. Else delegates to `as_sql()`.
- **`get_group_by_cols(self)`** — Collects group-by cols from source expressions.
- **`reverse_ordering(self)`** — Toggles `descending`; swaps nulls_first/nulls_last; returns self.
- **`asc(self)`** — Sets `self.descending = False`.
- **`desc(self)`** — Sets `self.descending = True`.

## `Window(SQLiteNumericMixin, Expression)`

Represents a SQL window function with OVER clause. Class attributes:
- `template = "%(expression)s OVER (%(window)s)"`
- `contains_aggregate = False`
- `contains_over_clause = True`

Methods:
- **`__init__(self, expression, partition_by=None, order_by=None, frame=None, output_field=None)`** — Validates `partition_by` is tuple/list → wraps in ExpressionList. Validates `order_by`: list/tuple/str/BaseExpression → wraps in OrderByList; else raises ValueError. Calls parent with `output_field`. Stores `self.source_expression = _parse_expressions(expression)[0]`.
- **`_resolve_output_field(self)`** — Returns `self.source_expression.output_field`.
- **`get_source_expressions(self)`** — Returns `[source_expression, partition_by, order_by, frame]`.
- **`set_source_expressions(self, exprs)`** — Unpacks to four attributes.
- **`as_sql(self, compiler, connection, template=None)`** — Checks expression support and backend OVER clause support (raises NotSupportedError if not). Compiles source expression. If partition_by: compiles with `PARTITION BY %(expressions)s` template. If order_by: compiles via `compiler.compile()`. If frame: compiles via `compiler.compile()`. Joins window parts, returns `(template % {expression, window}, flat_params)`.
- **`as_sqlite(self, compiler, connection)`** — If output_field is DecimalField: copies self, changes source expression's output_field to FloatField, calls parent as_sqlite. Else delegates to `as_sql()`.
- **`__str__(self)`** — `"source_expression OVER (PARTITION BY partition_by order_by frame)"`.
- **`__repr__(self)`** — `"<Window: {str(self)}>"`.
- **`get_group_by_cols(self)`** — Collects group-by cols from partition_by and order_by.

## `WindowFrameExclusion(Enum)`

Enum with values:
- `CURRENT_ROW = "CURRENT ROW"`
- `GROUP = "GROUP"`
- `TIES = "TIES"`
- `NO_OTHERS = "NO OTHERS"`

Method:
- **`__repr__(self)`** — Returns `"WindowFrameExclusion.{_name_}"`.

## `WindowFrame(Expression)`

Base class for window frame specifications (ROWS/RANGE). Class attribute:
- `template = "%(frame_type)s BETWEEN %(start)s AND %(end)s%(exclude)s"`

Methods:
- **`__init__(self, start=None, end=None, exclusion=None)`** — Wraps start/end in `Value()`. Validates exclusion is None or WindowFrameExclusion instance (raises TypeError). Stores all three.
- **`set_source_expressions(self, exprs)`** — Unpacks to `start, end = exprs`.
- **`get_source_expressions(self)`** — Returns `[self.start, self.end]`.
- **`get_exclusion(self)`** — Returns `" EXCLUDE {exclusion.value}"` or `""`.
- **`as_sql(self, compiler, connection)`** — Checks expression support. Calls abstract `window_frame_start_end(connection, start.value, end.value)`. If exclusion set and backend doesn't support frame exclusions, raises NotSupportedError. Returns `(template % {frame_type, start, end, exclude}, [])`.
- **`__repr__(self)`** — `"<WindowFrame: {str(self)}>"`.
- **`get_group_by_cols(self)`** — Returns `[]`.
- **`__str__(self)`** — Builds frame string from start/end values using connection ops constants (`PRECEDING`, `FOLLOWING`, `CURRENT_ROW`, `UNBOUNDED_PRECEDING`, `UNBOUNDED_FOLLOWING`). Returns template-formatted string.
- **`window_frame_start_end(self, connection, start, end)`** — Raises `NotImplementedError`.

## `RowRange(WindowFrame)`

ROWS frame type. Class attribute:
- `frame_type = "ROWS"`

Methods:
- **`window_frame_start_end(self, connection, start, end)`** — Delegates to `connection.ops.window_frame_rows_start_end(start, end)`.

## `ValueRange(WindowFrame)`

RANGE frame type. Class attribute:
- `frame_type = "RANGE"`

Methods:
- **`window_frame_start_end(self, connection, start, end)`** — Delegates to `connection.ops.window_frame_range_start_end(start, end)`.