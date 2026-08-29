## django/core/management/commands/flush.py
Here is the complete natural-language specification of `django/core/management/commands/flush.py`:

---

## Module-Level Preamble

### Imports

```python
from importlib import import_module

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.core.management.sql import emit_post_migrate_signal, sql_flush
from django.db import DEFAULT_DB_ALIAS, connections
```

### Constants & Globals

None. All behavior is encapsulated within the `Command` class.

---

## Code Objects

### Class: `Command(BaseCommand)`

**Metaclass:** None (inherits from `BaseCommand`).

#### Attributes

| Attribute | Type / Value | Initialization |
|---|---|---|
| `help` | `str` | `'Removes ALL DATA from the database, including data added during migrations. Does not achieve a "fresh install" state.'` — set at class level. |
| `stealth_options` | `tuple[str, ...]` | `('reset_sequences', 'allow_cascade', 'inhibit_post_migrate')` — set at class level; these options are consumed internally and never exposed as CLI arguments. |

#### Methods

##### `add_arguments(self, parser)`

Registers two command-line arguments on the given `ArgumentParser`:

1. **`--noinput` / `--no-input`** — `action='store_false'`, stored at destination `'interactive'`. Help text: `"Tells Django to NOT prompt the user for input of any kind."`
2. **`--database`** — default value is `DEFAULT_DB_ALIAS` (the string `"default"`). Help text: `"Nominates a database to flush. Defaults to the \"default\" database."`

No return value (`None`).

##### `handle(self, **options)`

Main entry point executed when the management command runs. Receives all parsed CLI options as keyword arguments.

**Step-by-step logic:**

1. **Extract options from `options`:**
   - `database = options['database']` — the target database alias (defaults to `"default"`).
   - `connection = connections[database]` — retrieves the database connection object for that alias.
   - `verbosity = options['verbosity']` — integer controlling output detail level.
   - `interactive = options['interactive']` — boolean; `True` unless `--noinput` was passed.

2. **Extract stealth options** (used by Django internals, not exposed as CLI flags):
   - `reset_sequences = options.get('reset_sequences', True)` — whether to reset auto-increment sequences after flush. Defaults to `True`.
   - `allow_cascade = options.get('allow_cascade', False)` — whether foreign-key cascades are permitted during truncation. Defaults to `False`.
   - `inhibit_post_migrate = options.get('inhibit_post_migrate', False)` — whether to skip emitting the post-migrate signal after flush. Defaults to `False`.

3. **Set style context:** Assigns `self.style = no_style()` — a style object that suppresses ANSI color output for SQL generation.

4. **Import management modules:** Iterates over every installed app config via `apps.get_app_configs()`, and attempts to import the `.management` submodule within each (`import_module('.management', app_config.name)`). Any `ImportError` is silently caught and ignored. This ensures that any signal handlers or dispatcher events registered by individual apps' management modules are loaded before flush proceeds.

5. **Generate SQL:** Calls `sql_flush(self.style, connection, only_django=True, reset_sequences=reset_sequences, allow_cascade=allow_cascade)`. Returns a list of SQL statements (`sql_list`) that will truncate all tables (or perform equivalent database-specific operations). The `only_django=True` flag restricts the flush to Django-managed tables.

6. **User confirmation:**
   - If `interactive` is `True`: prompts the user with a multi-line message displaying the target database name (`connection.settings_dict['NAME']`). The prompt reads:
     ```
     You have requested a flush of the database.
     This will IRREVERSIBLY DESTROY all data currently in the %r database,
     and return each table to an empty state.
     Are you sure you want to do this?

         Type 'yes' to continue, or 'no' to cancel:
     ```
     The user's raw input is stored in `confirm`.
   - If `interactive` is `False`: sets `confirm = 'yes'` (auto-confirms).

7. **Execute flush if confirmed (`confirm == 'yes'`):**
   - Calls `connection.ops.execute_sql_flush(database, sql_list)` to execute the generated SQL against the database.
   - Wraps this call in a `try/except Exception as exc`. If any exception occurs:
     - Raises `CommandError` with a message containing the database name and diagnostic hints (database not running, tables missing, invalid SQL), plus a suggestion to run `django-admin sqlflush` for debugging. The original exception is chained via `from exc`.
   - After successful execution, if **both** `sql_list` is non-empty **and** `inhibit_post_migrate` is `False`: calls `emit_post_migrate_signal(verbosity, interactive, database)` to emit the post-migrate signal, allowing individual applications to react as though a fresh migration cycle had occurred.

8. **If not confirmed (`confirm != 'yes'`):** Writes `"Flush cancelled.\n"` to stdout via `self.stdout.write()`.

**Return value:** None.

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
- **`integer_field_ranges`** — dict mapping field internal type names to `(min, max)` integer tuples:
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
- **`cast_data_types = {}`** — empty dict; overridden by subclasses to map field internal types to Cast() data type strings.
- **`cast_char_field_without_max_length = None`** — string or `None`; CharField data type when no `max_length` is given.
- **Window expression constants:**
  - `PRECEDING = 'PRECEDING'`
  - `FOLLOWING = 'FOLLOWING'`
  - `UNBOUNDED_PRECEDING = 'UNBOUNDED PRECEDING'`
  - `UNBOUNDED_FOLLOWING = 'UNBOUNDED FOLLOWING'`
  - `CURRENT_ROW = 'CURRENT ROW'`
- **`explain_prefix = None`** — string prefix for EXPLAIN queries, or `None` if unsupported.

---

## Code Objects (Class and Methods)

### Class: `BaseDatabaseOperations`

Encapsulates database-backend-specific SQL generation differences (ordering, ID retrieval, date/time handling, etc.).

#### `__init__(self, connection)`
- Stores the passed `connection` object as `self.connection`.
- Initializes `self._cache = None` (lazy cache for compiler module imports).

---

#### `autoinc_sql(self, table, column)` → `str | None`
Returns SQL needed to support auto-incrementing primary keys on table creation. Default returns `None`.

#### `bulk_batch_size(self, fields, objs)` → `int`
Returns the maximum batch size for bulk inserts given a list of `fields` and all objects in `objs`. Default: `len(objs)`.

#### `cache_key_culling_sql(self)` → `str`
Returns an SQL query string to retrieve the first cache key greater than the *n* smallest keys, using `%s` as placeholder for the offset. Returns: `"SELECT cache_key FROM %s ORDER BY cache_key LIMIT 1 OFFSET %%s"`.

#### `unification_cast_sql(self, output_field)` → `str`
Given a field instance, returns SQL that casts union results to that type, with a `'%s'` placeholder for the expression. Default: `'%s'`.

#### `date_extract_sql(self, lookup_type, field_name)` → `str`
Returns SQL extracting a date component (e.g., `'year'`, `'month'`, `'day'`) from `field_name`. **Must be overridden**; raises `NotImplementedError`.

#### `date_interval_sql(self, timedelta)` → `str`
Implements date interval functionality for expressions. **Must be overridden**; raises `NotImplementedError`.

#### `date_trunc_sql(self, lookup_type, field_name)` → `str`
Returns SQL truncating a date field to the given specificity (`'year'`, `'month'`, or `'day'`). **Must be overridden**; raises `NotImplementedError`.

#### `datetime_cast_date_sql(self, field_name, tzname)` → `str`
Returns SQL to cast a datetime value to a date. **Must be overridden**; raises `NotImplementedError`.

#### `datetime_cast_time_sql(self, field_name, tzname)` → `str`
Returns SQL to cast a datetime value to a time. **Must be overridden**; raises `NotImplementedError`.

#### `datetime_extract_sql(self, lookup_type, field_name, tzname)` → `str`
Extracts a datetime component (`'year'`, `'month'`, `'day'`, `'hour'`, `'minute'`, `'second'`). **Must be overridden**; raises `NotImplementedError`.

#### `datetime_trunc_sql(self, lookup_type, field_name, tzname)` → `str`
Truncates a datetime field to the given specificity. **Must be overridden**; raises `NotImplementedError`.

#### `time_trunc_sql(self, lookup_type, field_name)` → `str`
Truncates a time field (`'hour'`, `'minute'`, or `'second'`). **Must be overridden**; raises `NotImplementedError`.

#### `time_extract_sql(self, lookup_type, field_name)` → `str`
Delegates to `self.date_extract_sql(lookup_type, field_name)`. Returns the same SQL as date extraction.

#### `deferrable_sql(self)` → `str`
Returns SQL for making a constraint "initially deferred" in a CREATE TABLE statement. Default: `''`.

#### `distinct_sql(self, fields, params)` → `tuple[list[str], list]`
Returns an `(sql_clauses, params)` tuple for the DISTINCT clause. If `fields` is non-empty, raises `NotSupportedError` (DISTINCT ON not supported). Otherwise returns `(['DISTINCT'], [])`.

#### `fetch_returned_insert_columns(self, cursor, returning_params)` → `tuple`
Given a cursor that executed INSERT…RETURNING, returns the newly created row data via `cursor.fetchone()`.

#### `field_cast_sql(self, db_type, internal_type)` → `str`
Returns SQL to cast a column before use in WHERE, with a `'%s'` placeholder. Default: `'%s'`.

#### `force_no_ordering(self)` → `list[str]`
Returns a list used in ORDER BY to force no ordering. Default: `[]`.

#### `for_update_sql(self, nowait=False, skip_locked=False, of=())` → `str`
Returns the FOR UPDATE SQL clause string for row locking. Composes: `'FOR UPDATE'`, optionally `' OF <of_cols>'` if `of` is non-empty, plus `' NOWAIT'` or `' SKIP LOCKED'` as flags dictate.

#### `_get_limit_offset_params(self, low_mark, high_mark)` → `tuple[int | None, int]`
Private helper computing `(limit, offset)`:
- `offset = low_mark or 0`.
- If `high_mark is not None`: returns `(high_mark - offset, offset)`.
- Else if `offset > 0`: returns `(self.connection.ops.no_limit_value(), offset)`.
- Otherwise: returns `(None, 0)`.

#### `limit_offset_sql(self, low_mark, high_mark)` → `str`
Returns the LIMIT/OFFSET SQL clause string. Uses `_get_limit_offset_params`, then joins non-empty `'LIMIT %d'` and `'OFFSET %d'` fragments with a space.

#### `last_executed_query(self, cursor, sql, params)` → `str`
Returns a human-readable string of the last executed query with placeholders replaced by actual values. Internally:
- Defines `to_string(s)` using `force_str(s, strings_only=True, errors='replace')`.
- If `params` is a list/tuple: converts each element via `to_string`, producing a tuple.
- If `params is None`: produces an empty tuple `()`.
- Otherwise (dict): converts both keys and values via `to_string`.
- Returns `"QUERY = %r - PARAMS = %r" % (sql, u_params)`.

#### `last_insert_id(self, cursor, table_name, pk_name)` → `int`
Returns the last auto-incremented ID from an INSERT. Default: `cursor.lastrowid`.

#### `lookup_cast(self, lookup_type, internal_type=None)` → `str`
Returns SQL to use for lookups (contains, like, etc.), with a `'%s'` placeholder. Default: `"%s"`.

#### `max_in_list_size(self)` → `int | None`
Returns the maximum number of items in an IN list condition, or `None` if unlimited. Default: `None`.

#### `max_name_length(self)` → `int | None`
Returns the maximum length for table/column names, or `None` if no limit. Default: `None`.

#### `no_limit_value(self)` → `int | None`
Returns the value to use when "LIMIT infinity" is desired, or `None` if the clause can be omitted. **Must be overridden**; raises `NotImplementedError`.

#### `pk_default_value(self)` → `str`
Returns the SQL token for specifying a field's default value in INSERT. Default: `'DEFAULT'`.

#### `prepare_sql_script(self, sql)` → `list[str]`
Splits a multi-line SQL script into individual statements using `sqlparse.split(sql)`, strips comments via `sqlparse.format(statement, strip_comments=True)`, and filters out empty strings. Returns the list of formatted statement strings.

#### `process_clob(self, value)` → `any`
Returns the CLOB column value as-is (for backends returning a locator object). Default: returns `value`.

#### `return_insert_columns(self, fields)` → `None | tuple[str, ...]`
For backends supporting INSERT…RETURNING, returns SQL and params to append. Default: `pass` (returns `None`).

#### `compiler(self, compiler_name)` → `type`
Returns the SQLCompiler class for the given name from `self.compiler_module`. Uses lazy import via `import_module`: if `self._cache is None`, imports the module and stores it in `self._cache`; then returns `getattr(self._cache, compiler_name)`.

#### `quote_name(self, name)` → `str`
Quotes a table/index/column name without double-quoting if already quoted. **Must be overridden**; raises `NotImplementedError`.

#### `random_function_sql(self)` → `str`
Returns an SQL expression for random values. Default: `'RANDOM()'`.

#### `regex_lookup(self, lookup_type)` → `str`
Returns SQL for regex/iregex lookups with a `'%s'` placeholder. **Must be overridden**; raises `NotImplementedError`.

#### `savepoint_create_sql(self, sid)` → `str`
Returns `"SAVEPOINT %s" % self.quote_name(sid)`.

#### `savepoint_commit_sql(self, sid)` → `str`
Returns `"RELEASE SAVEPOINT %s" % self.quote_name(sid)`.

#### `savepoint_rollback_sql(self, sid)` → `str`
Returns `"ROLLBACK TO SAVEPOINT %s" % self.quote_name(sid)`.

#### `set_time_zone_sql(self)` → `str`
Returns SQL to set the connection's time zone. Default: `''` (no support).

#### `sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False)` → `list[str]`
Returns a list of SQL statements to remove all data from given tables (without dropping them). **Must be overridden**; raises `NotImplementedError`.

#### `execute_sql_flush(self, using, sql_list)` → `None`
Executes each SQL statement in `sql_list` inside an atomic transaction (`transaction.atomic(using=using, savepoint=self.connection.features.can_rollback_ddl)`), iterating over a cursor from `self.connection.cursor()`.

#### `sequence_reset_by_name_sql(self, style, sequences)` → `list[str]`
Returns SQL to reset sequences by name. Default: `[]`.

#### `sequence_reset_sql(self, style, model_list)` → `list[str]`
Returns SQL to reset sequences for given models. Default: `[]`.

#### `start_transaction_sql(self)` → `str`
Returns the SQL to start a transaction. Default: `"BEGIN;"`.

#### `end_transaction_sql(self, success=True)` → `str`
Returns the SQL to end a transaction. If `success is False`: returns `"ROLLBACK;"`; otherwise: returns `"COMMIT;"`.

#### `tablespace_sql(self, tablespace, inline=False)` → `str`
Returns SQL for defining a tablespace in CREATE TABLE/INDEX. Default: `''`.

#### `prep_for_like_query(self, x)` → `str`
Escapes a value for LIKE queries by replacing `\` with `\\`, `%` with `\%`, and `_` with `\_`. Returns `str(x).replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")`.

#### `prep_for_iexact_query(self, x)` → `str`
Alias for `prep_for_like_query`; same implementation.

#### `validate_autopk_value(self, value)` → `int`
Validates a serial/auto-primary-key value; raises `ValueError` if invalid. Default: returns `value` unchanged.

#### `adapt_unknown_value(self, value)` → `any`
Transforms a Python value to backend-compatible form when the target type is unknown (e.g., `.raw()` queries). Dispatches by type in order:
- `datetime.datetime` → calls `self.adapt_datetimefield_value(value)`.
- `datetime.date` → calls `self.adapt_datefield_value(value)`.
- `datetime.time` → calls `self.adapt_timefield_value(value)`.
- `decimal.Decimal` → calls `self.adapt_decimalfield_value(value)`.
- Otherwise: returns `value` unchanged.

#### `adapt_datefield_value(self, value)` → `str | None`
Converts a date to backend-compatible form. If `value is None`: returns `None`; else: returns `str(value)`.

#### `adapt_datetimefield_value(self, value)` → `str | None`
Converts a datetime to backend-compatible form. If `value is None`: returns `None`; else: returns `str(value)`.

#### `adapt_timefield_value(self, value)` → `str | None`
Converts a time to backend-compatible form. If `value is None`: returns `None`. If `timezone.is_aware(value)` is true: raises `ValueError("Django does not support timezone-aware times.")`. Otherwise: returns `str(value)`.

#### `adapt_decimalfield_value(self, value, max_digits=None, decimal_places=None)` → `str`
Converts a `decimal.Decimal` to backend-compatible form by calling `utils.format_number(value, max_digits, decimal_places)`.

#### `adapt_ipaddressfield_value(self, value)` → `str | None`
Converts an IP address string. Returns `value or None`.

#### `year_lookup_bounds_for_date_field(self, value)` → `list[any]`
Returns `[first, second]` bounds for a BETWEEN query on a DateField by year. Constructs `datetime.date(value, 1, 1)` and `datetime.date(value, 12, 31)`, adapts both via `self.adapt_datefield_value()`.

#### `year_lookup_bounds_for_datetime_field(self, value)` → `list[any]`
Returns `[first, second]` bounds for a BETWEEN query on a DateTimeField by year. Constructs `datetime.datetime(value, 1, 1)` and `datetime.datetime(value, 12, 31, 23, 59, 59, 999999)`. If `settings.USE_TZ` is true: makes both timezone-aware using `timezone.get_current_timezone()` and `timezone.make_aware()`. Adapts via `self.adapt_datetimefield_value()`.

#### `get_db_converters(self, expression)` → `list[callable]`
Returns a list of converter functions for field data. Default: `[]`.

#### `convert_durationfield_value(self, value, expression, connection)` → `datetime.timedelta | None`
If `value is not None`: returns `datetime.timedelta(0, 0, value)`. Otherwise: returns `None`.

#### `check_expression_support(self, expression)` → `None`
Checks if the backend supports a given expression. Default: no-op (`pass`). Subclasses may raise `NotSupportedError`.

#### `conditional_expression_supported_in_where_clause(self, expression)` → `bool`
Returns whether a conditional expression is supported in WHERE clauses. Default: `True`.

#### `combine_expression(self, connector, sub_expressions)` → `str`
Joins a list of sub-expression strings with the given connector (e.g., `'+'`, `'-'`) surrounded by spaces (`' %s '`). Returns `conn.join(sub_expressions)`.

#### `combine_duration_expression(self, connector, sub_expressions)` → `str`
Delegates to `self.combine_expression(connector, sub_expressions)`.

#### `binary_placeholder_sql(self, value)` → `str`
Returns the placeholder syntax for binary content. Default: `'%s'`.

#### `modify_insert_params(self, placeholder, params)` → `list | tuple`
Allows modification of insert parameters. Default: returns `params` unchanged.

#### `integer_field_range(self, internal_type)` → `tuple[int, int]`
Looks up and returns `(min_value, max_value)` from `self.integer_field_ranges[internal_type]`.

#### `subtract_temporals(self, internal_type, lhs, rhs)` → `tuple[str, tuple] | NoReturn`
If `self.connection.features.supports_temporal_subtraction` is true: unpacks `lhs` and `rhs` as `(sql, params)` tuples, returns `'(%s - %s)' % (lhs_sql, rhs_sql), (*lhs_params, *rhs_params)`. Otherwise: raises `NotSupportedError("This backend does not support <internal_type> subtraction.")`.

#### `window_frame_start(self, start)` → `str`
Formats a window frame start bound:
- If `start` is an int `< 0`: returns `'%d PRECEDING' % abs(start)`.
- If `start == 0`: returns `'CURRENT ROW'`.
- If `start is None`: returns `'UNBOUNDED PRECEDING'`.
- Otherwise: raises `ValueError("start argument must be a negative integer, zero, or None, but got '<start>'.")`.

#### `window_frame_end(self, end)` → `str`
Formats a window frame end bound:
- If `end` is an int `== 0`: returns `'CURRENT ROW'`.
- If `end > 0`: returns `'%d FOLLOWING' % end`.
- If `end is None`: returns `'UNBOUNDED FOLLOWING'`.
- Otherwise: raises `ValueError("end argument must be a positive integer, zero, or None, but got '<end>'.")`.

#### `window_frame_rows_start_end(self, start=None, end=None)` → `tuple[str, str]`
Returns `(start_sql, end_sql)` for ROWS window frames. If `self.connection.features.supports_over_clause` is false: raises `NotSupportedError('This backend does not support window expressions.')`. Otherwise: returns `(self.window_frame_start(start), self.window_frame_end(end))`.

#### `window_frame_range_start_end(self, start=None, end=None)` → `tuple[str, str]`
Returns `(start_sql, end_sql)` for RANGE window frames. First calls `self.window_frame_rows_start_end(start, end)`. If `self.connection.features.only_supports_unbounded_with_preceding_and_following` is true and either `start < 0` or `end > 0`: raises `NotSupportedError('%s only supports UNBOUNDED together with PRECEDING and FOLLOWING.' % self.connection.display_name)`. Otherwise: returns `(start_, end_)`.

#### `explain_query_prefix(self, format=None, **options)` → `str | NoReturn`
Returns the EXPLAIN prefix for query explanation. If `self.connection.features.supports_explaining_query_execution` is false: raises `NotSupportedError('This backend does not support explaining query execution.')`. If `format` is provided: checks that its uppercased form is in `self.connection.features.supported_explain_formats`; if not, raises `ValueError` with a message naming the format and listing allowed formats (if any). If `options` dict is non-empty: raises `ValueError('Unknown options: <keys>')`. Returns `self.explain_prefix`.

#### `insert_statement(self, ignore_conflicts=False)` → `str`
Returns the INSERT statement prefix. Default: `'INSERT INTO'`.

#### `ignore_conflicts_suffix_sql(self, ignore_conflicts=None)` → `str`
Returns a suffix for IGNORE CONFLICTS clauses. Default: `''`.