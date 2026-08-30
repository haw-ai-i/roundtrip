## django/db/backends/mysql/operations.py
Here is the complete natural-language specification of `django/db/backends/mysql/operations.py`:

---

## Module-Level Preamble

### Imports
- `import uuid`
- `from django.conf import settings`
- `from django.db.backends.base.operations import BaseDatabaseOperations`
- `from django.utils import timezone`
- `from django.utils.duration import duration_microseconds`

### Class: `DatabaseOperations(BaseDatabaseOperations)`

#### Class-Level Attributes

**`compiler_module = "django.db.backends.mysql.compiler"`** — string constant specifying the module path for the MySQL query compiler.

**`integer_field_ranges`** — dict extending `BaseDatabaseOperations.integer_field_ranges` with two additional entries:
- `'PositiveSmallIntegerField': (0, 65535)`
- `'PositiveIntegerField': (0, 4294967295)`

**`cast_data_types`** — dict mapping Django field type names to MySQL CAST target types:
- `'AutoField': 'signed integer'`
- `'BigAutoField': 'signed integer'`
- `'CharField': 'char(%(max_length)s)'`
- `'DecimalField': 'decimal(%(max_digits)s, %(decimal_places)s)'`
- `'TextField': 'char'`
- `'IntegerField': 'signed integer'`
- `'BigIntegerField': 'signed integer'`
- `'SmallIntegerField': 'signed integer'`
- `'PositiveIntegerField': 'unsigned integer'`
- `'PositiveSmallIntegerField': 'unsigned integer'`

**`cast_char_field_without_max_length = 'char'`** — fallback cast type for CharFields without a max_length.

**`explain_prefix = 'EXPLAIN'`** — the SQL prefix used for EXPLAIN queries.

---

### Methods

#### `date_extract_sql(self, lookup_type, field_name)`
Returns SQL for extracting date components from `field_name`.
- If `lookup_type == 'week_day'`: returns `"DAYOFWEEK(%s)" % field_name` (returns 1–7, Sunday=1).
- If `lookup_type == 'week'`: returns `"WEEK(%s, 3)" % field_name` (mode 3: Monday start, weeks numbered 1–53 with ≥4 days in the new year).
- If `lookup_type == 'iso_year'`: returns `"TRUNCATE(YEARWEEK(%s, 3), -2) / 100" % field_name` (extracts ISO year from YEARWEEK).
- Otherwise: returns `"EXTRACT(%s FROM %s)" % (lookup_type.upper(), field_name)` (ISO-8601 compliant for week numbers).

#### `date_trunc_sql(self, lookup_type, field_name)`
Returns SQL for truncating a date to the specified granularity.
- If `lookup_type == 'year'`: returns `"CAST(DATE_FORMAT(%s, '%%Y-01-01') AS DATE)" % field_name`.
- If `lookup_type == 'month'`: returns `"CAST(DATE_FORMAT(%s, '%%Y-%%m-01') AS DATE)" % field_name`.
- If `lookup_type == 'quarter'`: returns `"MAKEDATE(YEAR(%s), 1) + INTERVAL QUARTER(%s) QUARTER - INTERVAL 1 QUARTER" % (field_name, field_name)` — computes the first day of the quarter.
- If `lookup_type == 'week'`: returns `"DATE_SUB(%s, INTERVAL WEEKDAY(%s) DAY)" % (field_name, field_name)` — truncates to Monday of that week.
- Otherwise: returns `"DATE(%s)" % field_name` — truncates to midnight of the date.

#### `_convert_field_to_tz(self, field_name, tzname)`
Private helper. If `settings.USE_TZ` is True, wraps `field_name` as `"CONVERT_TZ(%s, 'UTC', '%s')" % (field_name, tzname)`. Otherwise returns `field_name` unchanged.

#### `datetime_cast_date_sql(self, field_name, tzname)`
Converts a datetime column to a date. First calls `_convert_field_to_tz(field_name, tzname)`, then returns `"DATE(%s)" % converted_field_name`.

#### `datetime_cast_time_sql(self, field_name, tzname)`
Converts a datetime column to a time. First calls `_convert_field_to_tz(field_name, tzname)`, then returns `"TIME(%s)" % converted_field_name`.

#### `datetime_extract_sql(self, lookup_type, field_name, tzname)`
Extracts a date/time component from a datetime column with timezone conversion. Calls `_convert_field_to_tz(field_name, tzname)`, then delegates to `self.date_extract_sql(lookup_type, converted_field_name)`.

#### `datetime_trunc_sql(self, lookup_type, field_name, tzname)`
Truncates a datetime to the specified granularity with timezone conversion. First calls `_convert_field_to_tz(field_name, tzname)`. Then:
- If `lookup_type == 'quarter'`: returns `"CAST(DATE_FORMAT(MAKEDATE(YEAR({field_name}), 1) + INTERVAL QUARTER({field_name}) QUARTER - INTERVAL 1 QUARTER, '%%Y-%%m-01 00:00:00') AS DATETIME)"` (formatted via `.format(field_name=...)`).
- If `lookup_type == 'week'`: returns `"CAST(DATE_FORMAT(DATE_SUB({field_name}, INTERVAL WEEKDAY({field_name}) DAY), '%%Y-%%m-%%d 00:00:00') AS DATETIME)"` (formatted via `.format(field_name=...)`).
- For `lookup_type` in `['year', 'month', 'day', 'hour', 'minute', 'second']`: builds a format string by joining the first `i+1` elements of `('%%Y-', '%%m', '-%%d', ' %%H:', '%%i', ':%%s')` with remaining default elements from `('0000-', '01', '-01', ' 00:', '00', ':00')`, then returns `"CAST(DATE_FORMAT(%s, '%s') AS DATETIME)" % (field_name, format_str)`.
- For any other `lookup_type`: returns `field_name` unchanged.

#### `time_trunc_sql(self, lookup_type, field_name)`
Truncates a time to the specified granularity.
- If `lookup_type == 'hour'`: returns `"CAST(DATE_FORMAT(%s, '%%H:00:00') AS TIME)" % field_name`.
- If `lookup_type == 'minute'`: returns `"CAST(DATE_FORMAT(%s, '%%H:%%i:00') AS TIME)" % field_name`.
- If `lookup_type == 'second'`: returns `"CAST(DATE_FORMAT(%s, '%%H:%%i:%%s') AS TIME)" % field_name`.
- Otherwise: returns `"TIME(%s)" % field_name`.

#### `date_interval_sql(self, timedelta)`
Returns SQL for a timedelta interval. Calls `duration_microseconds(timedelta)` to convert the timedelta to microseconds, then returns `'INTERVAL %s MICROSECOND' % result`.

#### `format_for_duration_arithmetic(self, sql)`
Wraps an existing SQL expression as a MySQL interval: returns `'INTERVAL %s MICROSECOND' % sql`.

#### `force_no_ordering(self)`
Returns `[(None, ("NULL", [], False))]` — produces `"ORDER BY NULL"` to prevent MySQL's implicit ordering on grouped columns.

#### `last_executed_query(self, cursor, sql, params)`
Reconstructs the last executed query string from a cursor object. Attempts `getattr(cursor, '_executed', None)`. If found and not None, decodes it with `.decode(errors='replace')`. Returns the decoded string or `None` if unavailable.

#### `no_limit_value(self)`
Returns `18446744073709551615` (2⁶⁴ − 1), the maximum unsigned 64-bit integer, as recommended by MySQL documentation for representing "no limit" in LIMIT clauses.

#### `quote_name(self, name)`
Quotes a database object name with backticks. If `name` already starts and ends with `` ` ``, returns it unchanged (avoids double-quoting). Otherwise returns `` `%s` `` % name.

#### `random_function_sql(self)`
Returns `'RAND()'`.

#### `sql_flush(self, style, tables, sequences, allow_cascade=False)`
Generates SQL to truncate all given tables. If `tables` is non-empty: builds a list starting with `'SET FOREIGN_KEY_CHECKS = 0;'`, then for each table appends `'%s %s;' % (style.SQL_KEYWORD('TRUNCATE'), style.SQL_FIELD(self.quote_name(table)))`, then appends `'SET FOREIGN_KEY_CHECKS = 1;'`, then extends with `self.sequence_reset_by_name_sql(style, sequences)`. Returns the full list. If `tables` is empty, returns `[]`.

#### `validate_autopk_value(self, value)`
Validates an explicit AUTO_INCREMENT primary key value. If `value == 0`, raises `ValueError('The database backend does not accept 0 as a value for AutoField.')`. Otherwise returns `value` unchanged.

#### `adapt_datetimefield_value(self, value)`
Adapts a datetime value for MySQL storage.
- If `value is None`: returns `None`.
- If `value` has attribute `'resolve_expression'` (i.e., it's an expression node): returns `value` unchanged (database will handle adaptation).
- If `timezone.is_aware(value)` is True: if `settings.USE_TZ` is True, converts to naive via `timezone.make_naive(value, self.connection.timezone)`; otherwise raises `ValueError("MySQL backend does not support timezone-aware datetimes when USE_TZ is False.")`.
- Returns `str(value)`.

#### `adapt_timefield_value(self, value)`
Adapts a time value for MySQL storage.
- If `value is None`: returns `None`.
- If `value` has attribute `'resolve_expression'`: returns `value` unchanged.
- If `timezone.is_aware(value)` is True: raises `ValueError("MySQL backend does not support timezone-aware times.")`.
- Returns `str(value)`.

#### `max_name_length(self)`
Returns `64`, the maximum length for database object names in MySQL.

#### `bulk_insert_sql(self, fields, placeholder_rows)`
Generates the VALUES clause for bulk INSERT statements. Joins each row's placeholders with commas inside parentheses: `"(%s)" % sql` for each row. Then joins all rows with `", "`. Returns `"VALUES " + values_sql`.

#### `combine_expression(self, connector, sub_expressions)`
Combines expressions using bitwise/logical connectors specific to MySQL.
- If `connector == '^'`: returns `'POW(%s)' % ','.join(sub_expressions)`.
- If `connector` in `('&', '|', '<<')`: returns `'CONVERT(%s, SIGNED)' % connector.join(sub_expressions)` — casts result to signed integer since MySQL bitwise operators return unsigned.
- If `connector == '>>'`: returns `"FLOOR(%(lhs)s / POW(2, %(rhs)s))" % {'lhs': lhs, 'rhs': rhs}` where `lhs, rhs = sub_expressions`.
- Otherwise: delegates to `super().combine_expression(connector, sub_expressions)`.

#### `get_db_converters(self, expression)`
Returns a list of database-to-Python converters for the given expression. Calls `super().get_db_converters(expression)` first, then inspects `expression.output_field.get_internal_type()`:
- If `'BooleanField'` or `'NullBooleanField'`: appends `self.convert_booleanfield_value`.
- If `'DateTimeField'` and `settings.USE_TZ` is True: appends `self.convert_datetimefield_value`.
- If `'UUIDField'`: appends `self.convert_uuidfield_value`.
Returns the full list of converters.

#### `convert_booleanfield_value(self, value, expression, connection)`
Converts MySQL boolean values (0/1) to Python booleans. If `value` is 0 or 1, returns `bool(value)`. Otherwise returns `value` unchanged.

#### `convert_datetimefield_value(self, value, expression, connection)`
Converts naive datetime from MySQL to timezone-aware. If `value is not None`, calls `timezone.make_aware(value, self.connection.timezone)`. Returns the (possibly converted) value.

#### `convert_uuidfield_value(self, value, expression, connection)`
Converts string UUID to Python `uuid.UUID` object. If `value is not None`, returns `uuid.UUID(value)`. Otherwise returns `None`.

#### `binary_placeholder_sql(self, value)`
Returns the placeholder SQL for binary parameters. If `value is not None and not hasattr(value, 'as_sql')`: returns `'_binary %s'`. Otherwise returns `'%s'`.

#### `subtract_temporals(self, internal_type, lhs, rhs)`
Generates SQL for subtracting two temporal values. Each of `lhs` and `rhs` is a tuple `(sql, params)`.
- If `internal_type == 'TimeField'`: if `self.connection.mysql_is_mariadb` is True, returns `'CAST((TIME_TO_SEC(%(lhs)s) - TIME_TO_SEC(%(rhs)s)) * 1000000 AS SIGNED)' % {'lhs': lhs_sql, 'rhs': rhs_sql}, lhs_params + rhs_params`. Otherwise (MySQL): returns `"((TIME_TO_SEC(%(lhs)s) * 1000000 + MICROSECOND(%(lhs)s)) - (TIME_TO_SEC(%(rhs)s) * 1000000 + MICROSECOND(%(rhs)s)))" % {'lhs': lhs_sql, 'rhs': rhs_sql}, lhs_params * 2 + rhs_params * 2`.
- Otherwise (DateTimeField/DateField): returns `"TIMESTAMPDIFF(MICROSECOND, %s, %s)" % (rhs_sql, lhs_sql), rhs_params + lhs_params` — note the reversed order: `TIMESTAMPDIFF(MICROSECOND, right, left)` computes `left - right`.

#### `explain_query_prefix(self, format=None, **options)`
Builds the prefix for EXPLAIN queries. If `format` is not None and `format.upper() == 'TEXT'`, normalizes it to `'TRADITIONAL'` (for consistency with other backends). Calls `super().explain_query_prefix(format, **options)`. If `format` was provided, appends `" FORMAT=%s" % format`. If `self.connection.features.needs_explain_extended` is True and `format is None`, appends `' EXTENDED'` (EXTENDED and FORMAT are mutually exclusive). Returns the final prefix string.

#### `regex_lookup(self, lookup_type)`
Generates SQL for regex lookups, handling version differences across MySQL/MariaDB. If `self.connection.mysql_version < (8, 0, 0)` or `self.connection.mysql_is_mariadb` is True: if `lookup_type == 'regex'`, returns `'%s REGEXP BINARY %s'`; otherwise returns `'%s REGEXP %s'`. For MySQL ≥ 8.0 and not MariaDB: sets `match_option = 'c'` for case-sensitive regex or `'i'` for case-insensitive, then returns `"REGEXP_LIKE(%%s, %%s, '%s')" % match_option`.

#### `insert_statement(self, ignore_conflicts=False)`
Returns the INSERT statement prefix. If `ignore_conflicts` is True, returns `'INSERT IGNORE INTO'`. Otherwise delegates to `super().insert_statement(ignore_conflicts)`.

## django/db/backends/oracle/operations.py
The complete natural-language specification has been written to `spec.md`. It covers:

- **All 13 imports** (standard library, Django modules, and local oracle backend imports)
- **6 class-level constants/attributes**: `integer_field_ranges`, `set_operators`, `_sequence_reset_sql` (full PL/SQL block), `cast_char_field_without_max_length`, `cast_data_types`, `_tzname_re`
- **25 methods** of the `DatabaseOperations` class, each with exact signatures, branching logic, return values, and edge cases documented
- **1 cached property**: `_foreign_key_constraints` (wraps private `__foreign_key_constraints` with `lru_cache(maxsize=512)`)

Every method's control flow, Oracle-specific SQL generation patterns, timezone handling, type conversion logic, and error-raising conditions are specified in detail.

## django/db/backends/sqlite3/base.py
I now have the full source code. Here is the complete natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import datetime
import decimal
import functools
import hashlib
import math
import operator
import re
import statistics
import warnings
from itertools import chain
from sqlite3.dbapi2 import Database as Database  # aliased as `Database` via `from sqlite3 import dbapi2 as Database`

import pytz

from django.core.exceptions import ImproperlyConfigured
from django.db import utils
from django.db.backends import utils as backend_utils
from django.db.backends.base.base import BaseDatabaseWrapper
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_time
from django.utils.duration import duration_microseconds

from .client import DatabaseClient          # isort:skip
from .creation import DatabaseCreation       # isort:skip
from .features import DatabaseFeatures       # isort:skip
from .introspection import DatabaseIntrospection  # isort:skip
from .operations import DatabaseOperations   # isort:skip
from .schema import DatabaseSchemaEditor     # isort:skip
```

### Module-Level Constants & Globals

- **`FORMAT_QMARK_REGEX`** — A compiled `re.Pattern` object matching the regex `r'(?<!%)%s'`. Used to convert Django's format-style `%s` placeholders into SQLite's qmark-style `?`, but only when not preceded by a literal `%`.
- **Module-level function calls:** `check_sqlite_version()` is called at import time (line 67), raising `ImproperlyConfigured` if the SQLite version is below `(3, 8, 3)`.

### Type Aliases / Complex Data Structures

**`DatabaseWrapper.data_types`** — A dict mapping Django field class names to SQLite column type strings:
- `'AutoField'`: `'integer'`
- `'BigAutoField'`: `'integer'`
- `'BinaryField'`: `'BLOB'`
- `'BooleanField'`: `'bool'`
- `'CharField'`: `'varchar(%(max_length)s)'`
- `'DateField'`: `'date'`
- `'DateTimeField'`: `'datetime'`
- `'DecimalField'`: `'decimal'`
- `'DurationField'`: `'bigint'`
- `'FileField'`: `'varchar(%(max_length)s)'`
- `'FilePathField'`: `'varchar(%(max_length)s)'`
- `'FloatField'`: `'real'`
- `'IntegerField'`: `'integer'`
- `'BigIntegerField'`: `'bigint'`
- `'IPAddressField'`: `'char(15)'`
- `'GenericIPAddressField'`: `'char(39)'`
- `'NullBooleanField'`: `'bool'`
- `'OneToOneField'`: `'integer'`
- `'PositiveIntegerField'`: `'integer unsigned'`
- `'PositiveSmallIntegerField'`: `'smallint unsigned'`
- `'SlugField'`: `'varchar(%(max_length)s)'`
- `'SmallIntegerField'`: `'smallint'`
- `'TextField'`: `'text'`
- `'TimeField'`: `'time'`
- `'UUIDField'`: `'char(32)'`

**`DatabaseWrapper.data_type_check_constraints`** — A dict mapping field class names to SQL check constraint strings:
- `'PositiveIntegerField'`: `'"%(column)s" >= 0'`
- `'PositiveSmallIntegerField'`: `'"%(column)s" >= 0'`

**`DatabaseWrapper.data_types_suffix`** — A dict mapping field class names to SQL suffixes appended after the type:
- `'AutoField'`: `'AUTOINCREMENT'`
- `'BigAutoField'`: `'AUTOINCREMENT'`

**`DatabaseWrapper.operators`** — A dict of lookup operators to their SQL template strings:
- `'exact'`: `'= %s'`
- `'iexact'`: `"LIKE %s ESCAPE '\\'"` 
- `'contains'`: `"LIKE %s ESCAPE '\\'"` 
- `'icontains'`: `"LIKE %s ESCAPE '\\'"` 
- `'regex'`: `'REGEXP %s'`
- `'iregex'`: `"REGEXP '(?i)' || %s"`
- `'gt'`: `'> %s'`
- `'gte'`: `'>= %s'`
- `'lt'`: `'< %s'`
- `'lte'`: `'< = %s'`
- `'startswith'`: `"LIKE %s ESCAPE '\\'"` 
- `'endswith'`: `"LIKE %s ESCAPE '\\'"` 
- `'istartswith'`: `"LIKE %s ESCAPE '\\'"` 
- `'iendswith'`: `"LIKE %s ESCAPE '\\'"` 

**`DatabaseWrapper.pattern_esc`** — A string: `r"REPLACE(REPLACE(REPLACE({}, '\', '\\'), '%%', '\%%'), '_', '\_')"` — used to escape special LIKE characters in dynamic pattern lookups.

**`DatabaseWrapper.pattern_ops`** — A dict of lookup operators for dynamic (non-raw-string) pattern matching:
- `'contains'`: `r"LIKE '%%' || {} || '%%' ESCAPE '\\'"` 
- `'icontains'`: `r"LIKE '%%' || UPPER({}) || '%%' ESCAPE '\\'"` 
- `'startswith'`: `r"LIKE {} || '%%' ESCAPE '\\'"` 
- `'istartswith'`: `r"LIKE UPPER({}) || '%%' ESCAPE '\\'"` 
- `'endswith'`: `r"LIKE '%%' || {} ESCAPE '\\'"` 
- `'iendswith'`: `r"LIKE '%%' || UPPER({}) ESCAPE '\\'"` 

---

## Code Objects (Functions and Classes)

### Function: `decoder(conv_func)`

**Signature:** `def decoder(conv_func):` — parameter `conv_func` is a callable accepting a decoded string.

**Logic:** Returns a lambda function `lambda s: conv_func(s.decode())`. The returned lambda takes a bytes object, decodes it to a UTF-8 string via `.decode()`, then passes the result to `conv_func`. Used as a factory for SQLite type converters that need to operate on strings rather than raw bytes.

**Return:** A callable (lambda) accepting `bytes` and returning whatever `conv_func` returns when given a decoded string.

---

### Function: `none_guard(func)`

**Signature:** `def none_guard(func):` — parameter `func` is any callable.

**Logic:** Returns a wrapper function decorated with `@functools.wraps(func)`. The wrapper accepts `*args, **kwargs`. If any element of `args` is `None`, the wrapper returns `None` immediately without calling `func`. Otherwise, it calls and returns `func(*args, **kwargs)`.

**Return:** A callable that short-circuits to `None` on any `None` argument.

---

### Function: `list_aggregate(function)`

**Signature:** `def list_aggregate(function):` — parameter `function` is a callable accepting an iterable of values and returning a single aggregate result (e.g., `statistics.pstdev`).

**Logic:** Uses `type()` to dynamically create a new class named `'ListAggregate'` that inherits from `list`. The class has two attributes:
- `'step'`: set to `list.append` — called by SQLite's aggregate mechanism for each row value.
- `'finalize'`: set to the provided `function` — called once after all rows have been accumulated, receiving the list of values as its argument.

**Return:** A dynamically-created class (not an instance) that can be used with `Database.create_aggregate()`.

---

### Function: `check_sqlite_version()`

**Signature:** `def check_sqlite_version():` — no parameters.

**Logic:** Checks `Database.sqlite_version_info` against the tuple `(3, 8, 3)`. If the installed SQLite version is less than this minimum, raises `ImproperlyConfigured` with the message `'SQLite 3.8.3 or later is required (found %s).'` formatted with `Database.sqlite_version`.

**Return:** None (raises on failure). Called at module import time.

---

### Module-Level Registration Calls (at import time)

- **`Database.register_converter("bool", b'1'.__eq__)`** — Registers a type converter for the `"bool"` declared type. The converter is `b'1'.__eq__`, which returns `True` when the incoming bytes equal `b'1'`.
- **`Database.register_converter("time", decoder(parse_time))`** — Registers a converter for `"time"`, using `decoder()` to wrap `parse_time` from `django.utils.dateparse`.
- **`Database.register_converter("datetime", decoder(parse_datetime))`** — Same pattern for `"datetime"`.
- **`Database.register_converter("timestamp", decoder(parse_datetime))`** — Same pattern for `"timestamp"`.
- **`Database.register_converter("TIMESTAMP", decoder(parse_datetime))`** — Case-sensitive alias for `"TIMESTAMP"` (uppercase).
- **`Database.register_adapter(decimal.Decimal, str)`** — Registers an adapter so that `decimal.Decimal` Python objects are converted to their string representation when bound as parameters.

---

### Class: `DatabaseWrapper(BaseDatabaseWrapper)`

**Inheritance:** Extends `BaseDatabaseWrapper`.

**Class Attributes (inherited + defined):**
- `vendor = 'sqlite'` — String identifying the database vendor.
- `display_name = 'SQLite'` — Human-readable name.
- `data_types` — Dict as described above, mapping Django field types to SQLite column types.
- `data_type_check_constraints` — Dict as described above.
- `data_types_suffix` — Dict as described above.
- `operators` — Dict of SQL operator templates as described above.
- `pattern_esc` — String for escaping LIKE special characters.
- `pattern_ops` — Dict of dynamic pattern lookup operators.
- `Database = Database` — Reference to the sqlite3 dbapi2 module.
- `SchemaEditorClass = DatabaseSchemaEditor` — The schema editor class.
- `client_class = DatabaseClient` — Client subprocess class.
- `creation_class = DatabaseCreation` — Database creation helper.
- `features_class = DatabaseFeatures` — Feature flags for SQLite capabilities.
- `introspection_class = DatabaseIntrospection` — Schema introspection helper.
- `ops_class = DatabaseOperations` — SQL operations helper.

#### Method: `get_connection_params()`

**Signature:** `def get_connection_params(self):` — no parameters beyond `self`.

**Logic:** 
1. Reads `settings_dict['NAME']`. If empty/falsy, raises `ImproperlyConfigured` with `"settings.DATABASES is improperly configured. Please supply the NAME value."`.
2. Builds a kwargs dict: `'database'` set to `settings_dict['NAME']`, `'detect_types'` set to `Database.PARSE_DECLTYPES | Database.PARSE_COLNAMES` (bitwise OR of two sqlite3 flags), and unpacks all key-value pairs from `settings_dict['OPTIONS']`.
3. If `'check_same_thread'` is present in kwargs and its value is truthy, emits a `RuntimeWarning` via `warnings.warn()` explaining that the option will be overridden to `False`, directing users to use `allow_thread_sharing` instead.
4. Updates kwargs with `'check_same_thread': False` and `'uri': True`.
5. Returns kwargs.

**Return:** A dict of connection parameters for `Database.connect()`.

#### Method: `get_new_connection(conn_params)`

**Signature:** `def get_new_connection(self, conn_params):` — parameter `conn_params` is the dict returned by `get_connection_params()`.

**Logic:**
1. Calls `Database.connect(**conn_params)` to create a new sqlite3 connection object.
2. Registers **custom scalar functions** on the connection via `conn.create_function(name, num_args, callable)`:
   - `"django_date_extract"` (2 args) → `_sqlite_datetime_extract`
   - `"django_date_trunc"` (2 args) → `_sqlite_date_trunc`
   - `"django_datetime_cast_date"` (2 args) → `_sqlite_datetime_cast_date`
   - `"django_datetime_cast_time"` (2 args) → `_sqlite_datetime_cast_time`
   - `"django_datetime_extract"` (3 args) → `_sqlite_datetime_extract`
   - `"django_datetime_trunc"` (3 args) → `_sqlite_datetime_trunc`
   - `"django_time_extract"` (2 args) → `_sqlite_time_extract`
   - `"django_time_trunc"` (2 args) → `_sqlite_time_trunc`
   - `"django_time_diff"` (2 args) → `_sqlite_time_diff`
   - `"django_timestamp_diff"` (2 args) → `_sqlite_timestamp_diff`
   - `"django_format_dtdelta"` (3 args) → `_sqlite_format_dtdelta`
   - `'regexp'` (2 args) → `_sqlite_regexp`
   - `'ACOS'` (1 arg) → `none_guard(math.acos)`
   - `'ASIN'` (1 arg) → `none_guard(math.asin)`
   - `'ATAN'` (1 arg) → `none_guard(math.atan)`
   - `'ATAN2'` (2 args) → `none_guard(math.atan2)`
   - `'CEILING'` (1 arg) → `none_guard(math.ceil)`
   - `'COS'` (1 arg) → `none_guard(math.cos)`
   - `'COT'` (1 arg) → `none_guard(lambda x: 1 / math.tan(x))`
   - `'DEGREES'` (1 arg) → `none_guard(math.degrees)`
   - `'EXP'` (1 arg) → `none_guard(math.exp)`
   - `'FLOOR'` (1 arg) → `none_guard(math.floor)`
   - `'LN'` (1 arg) → `none_guard(math.log)`
   - `'LOG'` (2 args) → `none_guard(lambda x, y: math.log(y, x))` — note: arguments are `(base, value)`, not `(value, base)`.
   - `'LPAD'` (3 args) → `_sqlite_lpad`
   - `'MD5'` (1 arg) → `none_guard(lambda x: hashlib.md5(x.encode()).hexdigest())`
   - `'MOD'` (2 args) → `none_guard(math.fmod)`
   - `'PI'` (0 args) → `lambda: math.pi` — note: **not** wrapped in `none_guard`.
   - `'POWER'` (2 args) → `none_guard(operator.pow)`
   - `'RADIANS'` (1 arg) → `none_guard(math.radians)`
   - `'REPEAT'` (2 args) → `none_guard(operator.mul)` — string repetition.
   - `'REVERSE'` (1 arg) → `none_guard(lambda x: x[::-1])` — string reversal.
   - `'RPAD'` (3 args) → `_sqlite_rpad`
   - `'SHA1'` (1 arg) → `none_guard(lambda x: hashlib.sha1(x.encode()).hexdigest())`
   - `'SHA224'` (1 arg) → `none_guard(lambda x: hashlib.sha224(x.encode()).hexdigest())`
   - `'SHA256'` (1 arg) → `none_guard(lambda x: hashlib.sha256(x.encode()).hexdigest())`
   - `'SHA384'` (1 arg) → `none_guard(lambda x: hashlib.sha384(x.encode()).hexdigest())`
   - `'SHA512'` (1 arg) → `none_guard(lambda x: hashlib.sha512(x.encode()).hexdigest())`
   - `'SIGN'` (1 arg) → `none_guard(lambda x: (x > 0) - (x < 0))` — returns 1, 0, or -1.
   - `'SIN'` (1 arg) → `none_guard(math.sin)`
   - `'SQRT'` (1 arg) → `none_guard(math.sqrt)`
   - `'TAN'` (1 arg) → `none_guard(math.tan)`
3. Registers **custom aggregate functions** via `conn.create_aggregate(name, num_args, class_factory)`:
   - `'STDDEV_POP'` (1 arg) → `list_aggregate(statistics.pstdev)` — population standard deviation.
   - `'STDDEV_SAMP'` (1 arg) → `list_aggregate(statistics.stdev)` — sample standard deviation.
   - `'VAR_POP'` (1 arg) → `list_aggregate(statistics.pvariance)` — population variance.
   - `'VAR_SAMP'` (1 arg) → `list_aggregate(statistics.variance)` — sample variance.
4. Executes `'PRAGMA foreign_keys = ON'` to enable foreign key enforcement.
5. Returns the connection object.

**Return:** A sqlite3 Connection instance with all custom functions and aggregates registered, and foreign keys enabled.

#### Method: `init_connection_state()`

**Signature:** `def init_connection_state(self):` — no parameters beyond `self`.

**Logic:** Does nothing (empty body). Overrides the base class method to be a no-op for SQLite.

**Return:** None.

#### Method: `create_cursor(name=None)`

**Signature:** `def create_cursor(self, name=None):` — optional parameter `name` defaults to `None`.

**Logic:** Calls `self.connection.cursor(factory=SQLiteCursorWrapper)`, passing the custom cursor factory class.

**Return:** A `SQLiteCursorWrapper` instance wrapping a sqlite3 Cursor.

#### Method: `close()`

**Signature:** `def close(self):` — no parameters beyond `self`.

**Logic:**
1. Calls `self.validate_thread_sharing()`.
2. Checks `self.is_in_memory_db()`. If the database is **not** in-memory, calls `BaseDatabaseWrapper.close(self)` to actually close the connection. If it **is** in-memory, does nothing (to prevent accidental data loss from closing an in-memory database).

**Return:** None.

#### Method: `_savepoint_allowed()`

**Signature:** `def _savepoint_allowed(self):` — no parameters beyond `self`.

**Logic:** Returns `self.in_atomic_block`. Savepoints are only allowed when inside an atomic transaction block, because SQLite's savepoint behavior with autocommit is buggy.

**Return:** A boolean (`True` if in an atomic block, `False` otherwise).

#### Method: `_set_autocommit(autocommit)`

**Signature:** `def _set_autocommit(self, autocommit):` — parameter `autocommit` is a boolean.

**Logic:**
1. If `autocommit` is truthy, sets `level = None`. Otherwise, sets `level = ''` (empty string). The empty string is SQLite's internal default for the isolation level, distinct from `None`.
2. Within a `self.wrap_database_errors` context manager, sets `self.connection.isolation_level = level`.

**Return:** None.

#### Method: `disable_constraint_checking()`

**Signature:** `def disable_constraint_checking(self):` — no parameters beyond `self`.

**Logic:**
1. Opens a cursor via `self.cursor()`.
2. Executes `'PRAGMA foreign_keys = OFF'`.
3. Fetches the current state by executing `'PRAGMA foreign_keys'` and reading `.fetchone()[0]`.
4. Returns the negation of the boolean value of that result (i.e., returns `True` if constraints were successfully disabled, `False` if they remain enabled).

**Return:** A boolean indicating whether constraint checking is effectively disabled.

#### Method: `enable_constraint_checking()`

**Signature:** `def enable_constraint_checking(self):` — no parameters beyond `self`.

**Logic:** Opens a cursor and executes `'PRAGMA foreign_keys = ON'`.

**Return:** None.

#### Method: `check_constraints(table_names=None)`

**Signature:** `def check_constraints(self, table_names=None):` — optional parameter `table_names` defaults to `None`, can be an iterable of table name strings or omitted.

**Logic:**
- **If `self.features.supports_pragma_foreign_key_check` is truthy:**
  1. Opens a cursor via `self.cursor()`.
  2. If `table_names` is `None`, executes `'PRAGMA foreign_key_check'` and fetches all violations. Otherwise, for each table name in `table_names`, executes `'PRAGMA foreign_key_check(%s)' % table_name` and chains all results together using `chain.from_iterable`.
  3. Iterates over each violation tuple `(table_name, rowid, referenced_table_name, foreign_key_index)`:
     - Executes `'PRAGMA foreign_key_list(%s)' % table_name` to get the foreign key definition for that index.
     - Extracts `column_name` and `referenced_column_name` from indices 3–4 of the foreign key entry.
     - Gets the primary key column name via `self.introspection.get_primary_key_column(cursor, table_name)`.
     - Executes `'SELECT %s, %s FROM %s WHERE rowid = %%s' % (primary_key_column_name, column_name, table_name)` with `(rowid,)` to fetch the primary key value and the bad foreign key value.
     - Raises `utils.IntegrityError` with a formatted message describing the violation: `"The row in table '%s' with primary key '%s' has an invalid foreign key: %s.%s contains a value '%s' that does not have a corresponding value in %s.%s."`

- **Else (fallback path when `supports_pragma_foreign_key_check` is falsy):**
  1. Opens a cursor via `self.cursor()`.
  2. If `table_names` is `None`, populates it from `self.introspection.table_names(cursor)`.
  3. For each table name:
     - Gets the primary key column name; if none, skips the table.
     - Gets key columns via `self.introspection.get_key_columns(cursor, table_name)`.
     - For each `(column_name, referenced_table_name, referenced_column_name)` tuple:
       - Executes a LEFT JOIN query to find orphaned rows (rows in the referencing table where the foreign key is non-null but has no match in the referenced table). The SQL uses backtick-quoted identifiers and `%s` formatting.
       - For each bad row returned by `.fetchall()`, raises `utils.IntegrityError` with a similar formatted message using `bad_row[0]` (primary key value) and `bad_row[1]` (the invalid foreign key value).

**Return:** None (raises `utils.IntegrityError` on violation, or returns normally if no violations found).

#### Method: `is_usable()`

**Signature:** `def is_usable(self):` — no parameters beyond `self`.

**Logic:** Always returns `True`. SQLite does not have a concept of "unusable" connections in the same way as other databases.

**Return:** `True`.

#### Method: `_start_transaction_under_autocommit()`

**Signature:** `def _start_transaction_under_autocommit(self):` — no parameters beyond `self`.

**Logic:** Executes `"BEGIN"` via a cursor to explicitly start a transaction while staying in autocommit mode. This works around an SQLite3 bug that breaks savepoints when autocommit is disabled.

**Return:** None.

#### Method: `is_in_memory_db()`

**Signature:** `def is_in_memory_db(self):` — no parameters beyond `self`.

**Logic:** Delegates to `self.creation.is_in_memory_db(self.settings_dict['NAME'])`, checking whether the database name indicates an in-memory database (e.g., `'memory'`, `':memory:'`).

**Return:** A boolean.

---

### Class: `SQLiteCursorWrapper(Database.Cursor)`

**Inheritance:** Extends `Database.Cursor` (i.e., `sqlite3.dbapi2.Cursor`).

#### Method: `execute(self, query, params=None)`

**Signature:** `def execute(self, query, params=None):` — parameters: `query` (string), `params` defaults to `None`.

**Logic:**
1. If `params` is `None`, delegates directly to `Database.Cursor.execute(self, query)` without conversion.
2. Otherwise, converts the query via `self.convert_query(query)`, then calls `Database.Cursor.execute(self, converted_query, params)`.

**Return:** The return value of the underlying `Database.Cursor.execute()`.

#### Method: `executemany(self, query, param_list)`

**Signature:** `def executemany(self, query, param_list):` — parameters: `query` (string), `param_list` (iterable of parameter sequences).

**Logic:** Converts the query via `self.convert_query(query)`, then calls `Database.Cursor.executemany(self, converted_query, param_list)`.

**Return:** The return value of the underlying `Database.Cursor.executemany()`.

#### Method: `convert_query(self, query)`

**Signature:** `def convert_query(self, query):` — parameter `query` is a string.

**Logic:**
1. Applies `FORMAT_QMARK_REGEX.sub('?', query)`, which replaces all `%s` placeholders with `?` **except** when preceded by another `%` (i.e., `%%s` is preserved as-is).
2. Then applies `.replace('%%', '%')`, converting escaped percent signs back to literal single percents.

**Return:** A string with Django-style `%s` converted to SQLite qmark `?`, and `%%` converted to `%`.

---

### Function: `_sqlite_datetime_parse(dt, tzname=None)`

**Signature:** `def _sqlite_datetime_parse(dt, tzname=None):` — parameters: `dt` (datetime value or string), optional `tzname` (timezone name string).

**Logic:**
1. If `dt` is `None`, returns `None`.
2. Attempts to parse via `backend_utils.typecast_timestamp(dt)`. On `TypeError` or `ValueError`, returns `None`.
3. If `tzname` is not `None`, converts the datetime to local time using `timezone.localtime(dt, pytz.timezone(tzname))`.
4. Returns the (possibly timezone-converted) datetime object.

**Return:** A `datetime.datetime` object or `None`.

---

### Function: `_sqlite_date_trunc(lookup_type, dt)`

**Signature:** `def _sqlite_date_trunc(lookup_type, dt):` — parameters: `lookup_type` (string), `dt` (datetime value).

**Logic:**
1. Parses `dt` via `_sqlite_datetime_parse(dt)`. If result is `None`, returns `None`.
2. Based on `lookup_type`:
   - `'year'`: Returns `"%i-01-01" % dt.year` — January 1st of the same year.
   - `'quarter'`: Computes `month_in_quarter = dt.month - (dt.month - 1) % 3`, returns `'%i-%02i-01' % (dt.year, month_in_quarter)` — first day of the quarter's starting month.
   - `'month'`: Returns `"%i-%02i-01" % (dt.year, dt.month)` — first day of the same month.
   - `'week'`: Subtracts `datetime.timedelta(days=dt.weekday())` to get Monday of that week, returns `"%i-%02i-%02i" % (dt.year, dt.month, dt.day)`.
   - `'day'`: Returns `"%i-%02i-%02i" % (dt.year, dt.month, dt.day)` — same date.

**Return:** A string in `YYYY-MM-DD` format or `None`.

---

### Function: `_sqlite_time_trunc(lookup_type, dt)`

**Signature:** `def _sqlite_time_trunc(lookup_type, dt):` — parameters: `lookup_type` (string), `dt` (time value).

**Logic:**
1. If `dt` is `None`, returns `None`.
2. Attempts to parse via `backend_utils.typecast_time(dt)`. On `ValueError` or `TypeError`, returns `None`.
3. Based on `lookup_type`:
   - `'hour'`: Returns `"%02i:00:00" % dt.hour`.
   - `'minute'`: Returns `"%02i:%02i:00" % (dt.hour, dt.minute)`.
   - `'second'`: Returns `"%02i:%02i:%02i" % (dt.hour, dt.minute, dt.second)`.

**Return:** A string in `HH:MM:SS` format or `None`.

---

### Function: `_sqlite_datetime_cast_date(dt, tzname)`

**Signature:** `def _sqlite_datetime_cast_date(dt, tzname):` — parameters: `dt` (datetime value), `tzname` (timezone name).

**Logic:**
1. Parses `dt` via `_sqlite_datetime_parse(dt, tzname)`. If result is `None`, returns `None`.
2. Returns `dt.date().isoformat()` — the date portion as a string in `YYYY-MM-DD` format.

**Return:** A string or `None`.

---

### Function: `_sqlite_datetime_cast_time(dt, tzname)`

**Signature:** `def _sqlite_datetime_cast_time(dt, tzname):` — parameters: `dt` (datetime value), `tzname` (timezone name).

**Logic:**
1. Parses `dt` via `_sqlite_datetime_parse(dt, tzname)`. If result is `None`, returns `None`.
2. Returns `dt.time().isoformat()` — the time portion as a string in ISO format (`HH:MM:SS[.%f]`).

**Return:** A string or `None`.

---

### Function: `_sqlite_datetime_extract(lookup_type, dt, tzname=None)`

**Signature:** `def _sqlite_datetime_extract(lookup_type, dt, tzname=None):` — parameters: `lookup_type` (string), `dt` (datetime value), optional `tzname`.

**Logic:**
1. Parses `dt` via `_sqlite_datetime_parse(dt, tzname)`. If result is `None`, returns `None`.
2. Based on `lookup_type`:
   - `'week_day'`: Returns `(dt.isoweekday() % 7) + 1` — converts ISO weekday (Mon=1..Sun=7) to SQLite convention (Sun=1..Sat=7).
   - `'week'`: Returns `dt.isocalendar()[1]` — the ISO week number.
   - `'quarter'`: Returns `math.ceil(dt.month / 3)` — quarter number (1–4).
   - `'iso_year'`: Returns `dt.isocalendar()[0]` — the ISO year.
   - **Else:** Returns `getattr(dt, lookup_type)` — directly accesses the datetime attribute (e.g., `'year'`, `'month'`, `'day'`, `'hour'`, `'minute'`, `'second'`).

**Return:** An integer or `None`.

---

### Function: `_sqlite_datetime_trunc(lookup_type, dt, tzname)`

**Signature:** `def _sqlite_datetime_trunc(lookup_type, dt, tzname):` — parameters: `lookup_type` (string), `dt` (datetime value), `tzname` (timezone name).

**Logic:**
1. Parses `dt` via `_sqlite_datetime_parse(dt, tzname)`. If result is `None`, returns `None`.
2. Based on `lookup_type`:
   - `'year'`: Returns `"%i-01-01 00:00:00" % dt.year`.
   - `'quarter'`: Computes `month_in_quarter = dt.month - (dt.month - 1) % 3`, returns `'%i-%02i-01 00:00:00' % (dt.year, month_in_quarter)`.
   - `'month'`: Returns `"%i-%02i-01 00:00:00" % (dt.year, dt.month)`.
   - `'week'`: Subtracts `datetime.timedelta(days=dt.weekday())`, returns `"%i-%02i-%02i 00:00:00" % (dt.year, dt.month, dt.day)`.
   - `'day'`: Returns `"%i-%02i-%02i 00:00:00" % (dt.year, dt.month, dt.day)`.
   - `'hour'`: Returns `"%i-%02i-%02i %02i:00:00" % (dt.year, dt.month, dt.day, dt.hour)`.
   - `'minute'`: Returns `"%i-%02i-%02i %02i:%02i:00" % (dt.year, dt.month, dt.day, dt.hour, dt.minute)`.
   - `'second'`: Returns `"%i-%02i-%02i %02i:%02i:%02i" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)`.

**Return:** A string in `YYYY-MM-DD HH:MM:SS` format or `None`.

---

### Function: `_sqlite_time_extract(lookup_type, dt)`

**Signature:** `def _sqlite_time_extract(lookup_type, dt):` — parameters: `lookup_type` (string), `dt` (time value).

**Logic:**
1. If `dt` is `None`, returns `None`.
2. Attempts to parse via `backend_utils.typecast_time(dt)`. On `ValueError` or `TypeError`, returns `None`.
3. Returns `getattr(dt, lookup_type)` — directly accesses the time attribute (e.g., `'hour'`, `'minute'`, `'second'`).

**Return:** An integer or `None`.

---

### Function: `_sqlite_format_dtdelta(conn, lhs, rhs)`

**Signature:** `def _sqlite_format_dtdelta(conn, lhs, rhs):` — parameters: `conn` (string, either `'+'` or `'-'`), `lhs` (int microseconds or datetime string), `rhs` (int microseconds or datetime string). Decorated with `@none_guard`.

**Logic:**
1. Determines `real_lhs`: if `lhs` is an `int`, creates `datetime.timedelta(0, 0, lhs)`; otherwise calls `backend_utils.typecast_timestamp(lhs)`. Same for `rhs` → `real_rhs`.
2. If `conn.strip() == '+'`, computes `out = real_lhs + real_rhs`; otherwise `out = real_lhs - real_rhs`.
3. On `ValueError` or `TypeError`, returns `None`.
4. Returns `str(out)` — the string representation of the resulting timedelta (format: `[D day[s]], HH:MM:SS[.UUUUUU]`).

**Return:** A string representing a timedelta, or `None`.

---

### Function: `_sqlite_time_diff(lhs, rhs)`

**Signature:** `def _sqlite_time_diff(lhs, rhs):` — parameters: `lhs`, `rhs` (time values). Decorated with `@none_guard`.

**Logic:**
1. Parses both via `backend_utils.typecast_time()`.
2. Computes the difference in microseconds: `(left_hour * 3600 + left_minute * 60 + left_second) * 1_000_000 + left_microsecond - (right_hour * 3600 + right_minute * 60 + right_second) * 1_000_000 - right_microsecond`.

**Return:** An integer representing the time difference in microseconds.

---

### Function: `_sqlite_timestamp_diff(lhs, rhs)`

**Signature:** `def _sqlite_timestamp_diff(lhs, rhs):` — parameters: `lhs`, `rhs` (datetime values). Decorated with `@none_guard`.

**Logic:**
1. Parses both via `backend_utils.typecast_timestamp()`.
2. Returns `duration_microseconds(left - right)` — converts the timedelta difference to microseconds using Django's utility function.

**Return:** An integer representing the timestamp difference in microseconds.

---

### Function: `_sqlite_regexp(re_pattern, re_string)`

**Signature:** `def _sqlite_regexp(re_pattern, re_string):` — parameters: `re_pattern` (regex pattern string), `re_string` (string to match). Decorated with `@none_guard`.

**Logic:** Returns `bool(re.search(re_pattern, str(re_string)))` — performs a regex search and returns `True` if there is a match, `False` otherwise.

**Return:** A boolean.

---

### Function: `_sqlite_lpad(text, length, fill_text)`

**Signature:** `def _sqlite_lpad(text, length, fill_text):` — parameters: `text` (string), `length` (int), `fill_text` (string). Decorated with `@none_guard`.

**Logic:**
1. If `len(text) >= length`, returns `text[:length]` (truncates if longer).
2. Otherwise, returns `(fill_text * length)[:length - len(text)] + text` — prepends enough repetitions of `fill_text` to reach the desired total length.

**Return:** A string of exactly `length` characters, left-padded with `fill_text`.

---

### Function: `_sqlite_rpad(text, length, fill_text)`

**Signature:** `def _sqlite_rpad(text, length, fill_text):` — parameters: `text` (string), `length` (int), `fill_text` (string). Decorated with `@none_guard`.

**Logic:** Returns `(text + fill_text * length)[:length]` — appends enough repetitions of `fill_text` to reach the desired total length, then truncates if longer.

**Return:** A string of exactly `length` characters, right-padded with `fill_text`.

## django/db/backends/sqlite3/operations.py
Here is the complete natural-language specification of `django/db/backends/sqlite3/operations.py`:

---

## Module-Level Preamble

### Imports

```python
import datetime
import decimal
import uuid
from functools import lru_cache
from itertools import chain

from django.conf import settings
from django.core.exceptions import FieldError
from django.db import utils
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.models import aggregates, fields
from django.db.models.expressions import Col
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from django.utils.duration import duration_microseconds
from django.utils.functional import cached_property
```

### Constants & Class-Level Attributes (on `DatabaseOperations`)

| Name | Value |
|---|---|
| `cast_char_field_without_max_length` | `'text'` — the SQL type used when casting a CharField that has no max length. |
| `cast_data_types` | `{'DateField': 'TEXT', 'DateTimeField': 'TEXT'}` — maps Django field internal types to their SQLite cast target types. |
| `explain_prefix` | `'EXPLAIN QUERY PLAN'` — the SQL prefix used for query-plan explanation. |

---

## Code Objects (Class and Methods)

### Class: `DatabaseOperations(BaseDatabaseOperations)`

A subclass of `BaseDatabaseOperations` that provides SQLite-specific database operations. It also has one cached property (`_references_graph`) described below.

---

#### Method: `bulk_batch_size(self, fields, objs)`

**Purpose:** Compute the maximum number of objects that can be batched into a single bulk-insert query for SQLite.

**Logic:**
1. If `len(fields) == 1`, return `500` (the `SQLITE_MAX_COMPOUND_SELECT` limit).
2. Else if `len(fields) > 1`, return `self.connection.features.max_query_params // len(fields)` (respecting the `SQLITE_LIMIT_VARIABLE_NUMBER` limit of ~999 variables per query, divided by the number of fields).
3. Otherwise (`len(fields) == 0`), return `len(objs)` — no batching is possible, so all objects are returned as-is.

**Returns:** An integer batch size.

---

#### Method: `check_expression_support(self, expression)`

**Purpose:** Validate that the given ORM expression is supported by SQLite; raise errors for unsupported patterns.

**Logic:**
1. Define `bad_fields` as `(fields.DateField, fields.DateTimeField, fields.TimeField)`.
2. Define `bad_aggregates` as `(aggregates.Sum, aggregates.Avg, aggregates.Variance, aggregates.StdDev)`.
3. If the expression is an instance of any aggregate in `bad_aggregates`:
   - Iterate over each sub-expression returned by `expression.get_source_expressions()`.
   - For each sub-expression, attempt to read its `output_field` attribute. If a `FieldError` is raised (the sub-expression has no output field), skip it silently.
   - If the sub-expression's `output_field` is an instance of any type in `bad_fields`, raise `utils.NotSupportedError` with the message: `'You cannot use Sum, Avg, StdDev, and Variance aggregations on date/time fields in sqlite3 since date/time is saved as text.'`
4. If the expression is an instance of `aggregates.Aggregate` (any aggregate) and has more than one source expression (`len(expression.source_expressions) > 1`), raise `utils.NotSupportedError` with the message: `"SQLite doesn't support DISTINCT on aggregate functions accepting multiple arguments."`

**Returns:** None. Raises exceptions on unsupported expressions.

---

#### Method: `date_extract_sql(self, lookup_type, field_name)`

**Purpose:** Generate SQL for extracting a date component (year, month, day, etc.) from a date/time column.

**Logic:** Returns the string `"django_date_extract('%s', %s)"` formatted with `lookup_type.lower()` and `field_name`. This delegates to a custom SQLite function registered at connection time.

**Returns:** A SQL fragment string.

---

#### Method: `date_interval_sql(self, timedelta)`

**Purpose:** Convert a Python `timedelta` into a numeric representation for date arithmetic.

**Logic:** Returns `str(duration_microseconds(timedelta))`.

**Returns:** A string containing the total microseconds of the timedelta.

---

#### Method: `format_for_duration_arithmetic(self, sql)`

**Purpose:** No-op adapter — SQLite duration formatting is handled by a custom function at connection time.

**Logic:** Returns `sql` unchanged.

**Returns:** The input SQL string verbatim.

---

#### Method: `date_trunc_sql(self, lookup_type, field_name)`

**Purpose:** Generate SQL for truncating a date/time value to a given precision (year, month, day, etc.).

**Logic:** Returns the string `"django_date_trunc('%s', %s)"` formatted with `lookup_type.lower()` and `field_name`.

**Returns:** A SQL fragment string.

---

#### Method: `time_trunc_sql(self, lookup_type, field_name)`

**Purpose:** Generate SQL for truncating a time value to a given precision (hour, minute, second).

**Logic:** Returns the string `"django_time_trunc('%s', %s)"` formatted with `lookup_type.lower()` and `field_name`.

**Returns:** A SQL fragment string.

---

#### Method: `_convert_tzname_to_sql(self, tzname)`

**Purpose:** Convert a timezone name into an SQL-safe parameter for custom functions.

**Logic:**
- If `settings.USE_TZ` is truthy, return `"'%s'" % tzname` (the timezone name wrapped in single quotes).
- Otherwise, return `'NULL'`.

**Returns:** A string — either a quoted timezone name or the literal `'NULL'`.

---

#### Method: `datetime_cast_date_sql(self, field_name, tzname)`

**Purpose:** Generate SQL for casting a datetime column to a date.

**Logic:** Returns `"django_datetime_cast_date(%s, %s)"` formatted with `field_name` and the result of `self._convert_tzname_to_sql(tzname)`.

**Returns:** A SQL fragment string.

---

#### Method: `datetime_cast_time_sql(self, field_name, tzname)`

**Purpose:** Generate SQL for casting a datetime column to a time.

**Logic:** Returns `"django_datetime_cast_time(%s, %s)"` formatted with `field_name` and the result of `self._convert_tzname_to_sql(tzname)`.

**Returns:** A SQL fragment string.

---

#### Method: `datetime_extract_sql(self, lookup_type, field_name, tzname)`

**Purpose:** Generate SQL for extracting a component from a datetime column with timezone handling.

**Logic:** Returns `"django_datetime_extract('%s', %s, %s)"` formatted with `lookup_type.lower()`, `field_name`, and the result of `self._convert_tzname_to_sql(tzname)`.

**Returns:** A SQL fragment string.

---

#### Method: `datetime_trunc_sql(self, lookup_type, field_name, tzname)`

**Purpose:** Generate SQL for truncating a datetime column to a given precision with timezone handling.

**Logic:** Returns `"django_datetime_trunc('%s', %s, %s)"` formatted with `lookup_type.lower()`, `field_name`, and the result of `self._convert_tzname_to_sql(tzname)`.

**Returns:** A SQL fragment string.

---

#### Method: `time_extract_sql(self, lookup_type, field_name)`

**Purpose:** Generate SQL for extracting a component from a time column.

**Logic:** Returns `"django_time_extract('%s', %s)"` formatted with `lookup_type.lower()` and `field_name`.

**Returns:** A SQL fragment string.

---

#### Method: `pk_default_value(self)`

**Purpose:** Return the default value for an auto-incrementing primary key in INSERT statements.

**Logic:** Returns `"NULL"`.

**Returns:** The string `'NULL'`.

---

#### Method: `_quote_params_for_last_executed_query(self, params)`

**Purpose:** Quote query parameters as SQL literals for display by `last_executed_query()`, using SQLite's native `QUOTE()` function. Handles batching due to parameter limits.

**Logic:**
1. Define `BATCH_SIZE = 999` (matching `SQLITE_LIMIT_VARIABLE_NUMBER`).
2. If `len(params) > BATCH_SIZE`:
   - Initialize `results = ()`.
   - For each chunk of `params` in slices of size `BATCH_SIZE`, recursively call `self._quote_params_for_last_executed_query(chunk)` and concatenate the results into `results`.
   - Return `results`.
3. Otherwise (single batch):
   - Build SQL: `'SELECT ' + ', '.join(['QUOTE(?)'] * len(params))` — a SELECT statement that calls `QUOTE()` on each parameter placeholder.
   - Obtain a raw cursor via `self.connection.connection.cursor()` (bypassing Django's wrapper to avoid logging recursion).
   - Execute the query with `params`, fetch one row, and return it.
   - In a `finally` block, close the cursor.

**Returns:** A tuple of quoted string representations of each parameter value.

---

#### Method: `last_executed_query(self, cursor, sql, params)`

**Purpose:** Reconstruct the full SQL statement that was last executed by quoting and substituting parameters manually (since Python's sqlite3 module does not expose the internally substituted statement).

**Logic:**
1. If `params` is truthy:
   - If `params` is a list or tuple, call `self._quote_params_for_last_executed_query(params)` to get quoted values and assign them back to `params`.
   - Otherwise (dict), extract the values via `tuple(params.values())`, quote them via `_quote_params_for_last_executed_query`, then reconstruct a dict by zipping original keys with quoted values.
   - Return `sql % params` — string-format substitution of quoted parameters into the SQL template.
2. If `params` is falsy, return `sql` unchanged (for consistency with `SQLiteCursorWrapper.execute()`).

**Returns:** A string representing the fully substituted SQL statement.

---

#### Method: `quote_name(self, name)`

**Purpose:** Quote a database object name (table or column) for SQLite.

**Logic:**
1. If `name` already starts and ends with double quotes (`"`), return it unchanged (avoid double-quoting).
2. Otherwise, wrap the name in double quotes: `'"%s"' % name`.

**Returns:** A quoted SQL identifier string.

---

#### Method: `no_limit_value(self)`

**Purpose:** Return the sentinel value SQLite uses to indicate "no LIMIT".

**Logic:** Returns `-1`.

**Returns:** The integer `-1`.

---

#### Private Method: `__references_graph(self, table_name)`

**Purpose:** Recursively discover all tables that reference a given table via foreign keys (direct or indirect), using a recursive SQL query against `sqlite_master`.

**Logic:**
1. Build a recursive CTE query:
   ```sql
   WITH tables AS (
       SELECT %s name
       UNION
       SELECT sqlite_master.name
       FROM sqlite_master
       JOIN tables ON (sql REGEXP %s || tables.name || %s)
   ) SELECT name FROM tables;
   ```
2. Parameters are `(table_name, r'(?i)\s+references\s+("|\')?', r'("|\')?\s*\(')` — the regex matches `REFERENCES` clauses in CREATE TABLE statements (case-insensitive).
3. Execute the query via `self.connection.cursor()` and collect all table names from the result rows.

**Returns:** A list of table name strings that transitively reference `table_name`.

---

#### Cached Property: `_references_graph`

**Purpose:** Memoize `__references_graph` using an LRU cache to avoid repeated expensive recursive queries.

**Logic:** Returns `lru_cache(maxsize=512)(self.__references_graph)` — wraps the private method with a 512-entry least-recently-used cache. The value is cached once on first access and reused thereafter.

---

#### Method: `sql_flush(self, style, tables, sequences, allow_cascade=False)`

**Purpose:** Generate SQL statements to flush (delete all rows from) the given tables. Supports cascade via foreign-key graph traversal.

**Logic:**
1. If `tables` is non-empty and `allow_cascade` is truthy:
   - Expand `tables` into a set of all transitively referenced table names by calling `self._references_graph(table)` for each original table and flattening the results with `chain.from_iterable`.
2. For each table in the (possibly expanded) `tables` list, generate a DELETE statement: `'DELETE FROM "table_name";'` using `style.SQL_KEYWORD('DELETE')`, `style.SQL_KEYWORD('FROM')`, and `self.quote_name(table)`.
3. Return the list of SQL strings.

**Note:** No auto-increment index reset is performed (unlike other backend implementations).

**Returns:** A list of SQL statement strings.

---

#### Method: `adapt_datetimefield_value(self, value)`

**Purpose:** Convert a Python datetime value into a SQLite-compatible string representation.

**Logic:**
1. If `value` is `None`, return `None`.
2. If `value` has a `resolve_expression` attribute (i.e., it is an ORM expression), return it unchanged — the database will handle adaptation.
3. If `timezone.is_aware(value)` (the datetime has timezone info):
   - If `settings.USE_TZ` is truthy, convert to naive UTC using `timezone.make_naive(value, self.connection.timezone)`.
   - Otherwise (`USE_TZ` is False), raise `ValueError("SQLite backend does not support timezone-aware datetimes when USE_TZ is False.")`.
4. Return `str(value)` — the datetime converted to its string representation.

**Returns:** A string (or `None`, or an expression object). Raises `ValueError` on tz-aware datetimes with `USE_TZ=False`.

---

#### Method: `adapt_timefield_value(self, value)`

**Purpose:** Convert a Python time value into a SQLite-compatible string representation.

**Logic:**
1. If `value` is `None`, return `None`.
2. If `value` has a `resolve_expression` attribute, return it unchanged.
3. If `timezone.is_aware(value)`, raise `ValueError("SQLite backend does not support timezone-aware times.")`.
4. Return `str(value)`.

**Returns:** A string (or `None`, or an expression object). Raises `ValueError` on tz-aware time values.

---

#### Method: `get_db_converters(self, expression)`

**Purpose:** Collect the list of database-to-Python type converters for a given field expression.

**Logic:**
1. Start with the parent class's converter list via `super().get_db_converters(expression)`.
2. Get the internal type of the expression's output field: `internal_type = expression.output_field.get_internal_type()`.
3. Based on `internal_type`, append specific converters:
   - `'DateTimeField'` → append `self.convert_datetimefield_value`.
   - `'DateField'` → append `self.convert_datefield_value`.
   - `'TimeField'` → append `self.convert_timefield_value`.
   - `'DecimalField'` → append the result of `self.get_decimalfield_converter(expression)`.
   - `'UUIDField'` → append `self.convert_uuidfield_value`.
   - `'NullBooleanField'` or `'BooleanField'` → append `self.convert_booleanfield_value`.
4. Return the accumulated list.

**Returns:** A list of converter callable objects.

---

#### Method: `convert_datetimefield_value(self, value, expression, connection)`

**Purpose:** Convert a raw database datetime string into a Python `datetime.datetime` object with proper timezone awareness.

**Logic:**
1. If `value` is not `None`:
   - If `value` is not already a `datetime.datetime` instance, parse it using `parse_datetime(value)`.
   - If `settings.USE_TZ` is truthy and the resulting value is naive (`not timezone.is_aware(value)`), make it aware using `timezone.make_aware(value, self.connection.timezone)`.
2. Return the (possibly converted/converted-and-aware) value.

**Returns:** A `datetime.datetime` object or `None`.

---

#### Method: `convert_datefield_value(self, value, expression, connection)`

**Purpose:** Convert a raw database date string into a Python `datetime.date` object.

**Logic:**
1. If `value` is not `None`:
   - If `value` is not already a `datetime.date` instance, parse it using `parse_date(value)`.
2. Return the value.

**Returns:** A `datetime.date` object or `None`.

---

#### Method: `convert_timefield_value(self, value, expression, connection)`

**Purpose:** Convert a raw database time string into a Python `datetime.time` object.

**Logic:**
1. If `value` is not `None`:
   - If `value` is not already a `datetime.time` instance, parse it using `parse_time(value)`.
2. Return the value.

**Returns:** A `datetime.time` object or `None`.

---

#### Method: `get_decimalfield_converter(self, expression)`

**Purpose:** Create a converter function that cleans up floating-point inaccuracy from SQLite-stored Decimal values (SQLite stores only 15 significant digits).

**Logic:**
1. Define `create_decimal = decimal.Context(prec=15).create_decimal_from_float` — a factory that creates a `Decimal` from a float with 15-digit precision, stripping float noise.
2. If the expression is an instance of `Col`:
   - Compute `quantize_value = decimal.Decimal(1).scaleb(-expression.output_field.decimal_places)` — e.g., for 4 decimal places this yields `Decimal('0.0001')`.
   - Define a nested converter function: if `value` is not `None`, return `create_decimal(value).quantize(quantize_value, context=expression.output_field.context)`.
3. Otherwise (not a `Col`):
   - Define a simpler converter: if `value` is not `None`, return `create_decimal(value)` (no quantization).
4. Return the converter function.

**Returns:** A callable `(value, expression, connection) → Decimal | None`.

---

#### Method: `convert_uuidfield_value(self, value, expression, connection)`

**Purpose:** Convert a raw database UUID string into a Python `uuid.UUID` object.

**Logic:**
1. If `value` is not `None`, convert it via `uuid.UUID(value)`.
2. Return the value (either the parsed UUID or `None`).

**Returns:** A `uuid.UUID` object or `None`.

---

#### Method: `convert_booleanfield_value(self, value, expression, connection)`

**Purpose:** Convert SQLite boolean storage values (`1`/`0`) into Python booleans.

**Logic:** If `value` is in `(1, 0)`, return `bool(value)` (i.e., `True` for `1`, `False` for `0`). Otherwise, return `value` unchanged (handles `None` and other values).

**Returns:** A boolean or the original value.

---

#### Method: `bulk_insert_sql(self, fields, placeholder_rows)`

**Purpose:** Generate SQL for bulk inserts using SQLite's `UNION ALL SELECT ...` pattern instead of multi-value INSERT.

**Logic:** For each row in `placeholder_rows`, format it as `"SELECT %s"` where `%s` is the comma-joined placeholders. Join all such SELECT statements with `' UNION ALL '`.

**Returns:** A single SQL string representing a UNION ALL of SELECT statements.

---

#### Method: `combine_expression(self, connector, sub_expressions)`

**Purpose:** Handle SQLite-specific expression combination logic.

**Logic:**
1. If `connector == '^'` (power/exponentiation), return `'POWER(%s)' % ','.join(sub_expressions)` — delegating to a custom `POWER()` function registered at connection time.
2. Otherwise, delegate to the parent class: `super().combine_expression(connector, sub_expressions)`.

**Returns:** A SQL fragment string.

---

#### Method: `combine_duration_expression(self, connector, sub_expressions)`

**Purpose:** Generate SQL for timedelta arithmetic operations.

**Logic:**
1. If `connector` is not `'+'` or `'-'`, raise `utils.DatabaseError('Invalid connector for timedelta: %s.' % connector)`.
2. Build function parameters list: `["'%s'" % connector] + sub_expressions`.
3. If the resulting parameter list has more than 3 elements, raise `ValueError('Too many params for timedelta operations.')`.
4. Return `"django_format_dtdelta(%s)" % ', '.join(fn_params)` — delegating to a custom SQLite function.

**Returns:** A SQL fragment string. Raises exceptions on invalid connectors or too many parameters.

---

#### Method: `integer_field_range(self, internal_type)`

**Purpose:** Report the valid range for integer fields in SQLite.

**Logic:** Returns `(None, None)` — SQLite does not enforce any integer constraints (all integers are variable-width).

**Returns:** A tuple of two `None` values.

---

#### Method: `subtract_temporals(self, internal_type, lhs, rhs)`

**Purpose:** Generate SQL for subtracting two temporal values.

**Logic:**
1. Unpack `lhs` and `rhs` into `(lhs_sql, lhs_params)` and `(rhs_sql, rhs_params)`.
2. If `internal_type == 'TimeField'`, return the tuple: `("django_time_diff(%s, %s)" % (lhs_sql, rhs_sql), lhs_params + rhs_params)`.
3. Otherwise, return: `("django_timestamp_diff(%s, %s)" % (lhs_sql, rhs_sql), lhs_params + rhs_params)` — for date and datetime fields.

**Returns:** A tuple of `(sql_string, combined_params_tuple)`.

---

#### Method: `insert_statement(self, ignore_conflicts=False)`

**Purpose:** Return the appropriate INSERT statement prefix for SQLite.

**Logic:**
- If `ignore_conflicts` is truthy, return `'INSERT OR IGNORE INTO'` (SQLite's conflict-resolution syntax).
- Otherwise, delegate to the parent class: `super().insert_statement(ignore_conflicts)`.

**Returns:** A SQL keyword string.