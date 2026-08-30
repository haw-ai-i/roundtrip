## django/db/backends/mysql/base.py
Now I have the complete source. Here is the specification:

---

## Module-Level Preamble

### Imports

```python
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError
from django.db.backends import utils as backend_utils
from django.db.backends.base.base import BaseDatabaseWrapper
from django.utils.asyncio import async_unsafe
from django.utils.functional import cached_property
from django.utils.regex_helper import _lazy_re_compile

import MySQLdb as Database          # (may raise ImproperlyConfigured)
from MySQLdb.constants import CLIENT, FIELD_TYPE
from MySQLdb.converters import conversions
from .client import DatabaseClient
from .creation import DatabaseCreation
from .features import DatabaseFeatures
from .introspection import DatabaseIntrospection
from .operations import DatabaseOperations
from .schema import DatabaseSchemaEditor
from .validation import DatabaseValidation
```

### Constants & Globals

- **`version`** — `Database.version_info` (a tuple from the mysqlclient library). If `version < (1, 4, 0)`, raises `ImproperlyConfigured('mysqlclient 1.4.0 or newer is required; you have %s.' % Database.__version__)`.

- **`django_conversions`** — A dict formed by merging two dicts: `{**conversions, **{FIELD_TYPE.TIME: backend_utils.typecast_time}}`. The `conversions` dict comes from `MySQLdb.converters`; the merge overrides the `FIELD_TYPE.TIME` entry with Django's `backend_utils.typecast_time` function (because MySQLdb returns TIME columns as timedeltas rather than Python `time.time` objects).

- **`server_version_re`** — A compiled lazy regex pattern: `_lazy_re_compile(r'(\d{1,2})\.(\d{1,2})\.(\d{1,2})')`. Matches the numerical portion of MySQL/MariaDB version strings (e.g. `5.0.24`, `10.3.1`).

---

## Code Objects

### Class: `CursorWrapper`

A thin wrapper around a MySQLdb cursor that catches specific `Database.OperationalError` error codes and reraises them as Django's `IntegrityError`. Implemented as composition (not subclassing) so it is not tied to the particular underlying cursor representation.

**Class attribute:**
- **`codes_for_integrityerror`** — A tuple of four integer MySQL error codes: `(1048, 1690, 3819, 4025)` corresponding to "Column cannot be null", "BIGINT UNSIGNED value is out of range", "CHECK constraint is violated", and "CHECK constraint failed".

**`__init__(self, cursor)`:**
- Stores the passed MySQLdb cursor as `self.cursor`.

**`execute(self, query, args=None)`:**
- Calls `self.cursor.execute(query, args)` (where `args=None` means no string interpolation).
- Catches `Database.OperationalError`. If `e.args[0]` is in `codes_for_integrityerror`, raises `IntegrityError(*tuple(e.args))`; otherwise re-raises the original exception.
- Returns whatever `self.cursor.execute()` returns.

**`executemany(self, query, args)`:**
- Calls `self.cursor.executemany(query, args)`.
- Same error-code mapping as `execute()`: if caught `Database.OperationalError` has a code in `codes_for_integrityerror`, raises `IntegrityError(*tuple(e.args))`; otherwise re-raises.
- Returns whatever `self.cursor.executemany()` returns.

**`__getattr__(self, attr)`:**
- Delegates attribute access to `self.cursor` via `getattr(self.cursor, attr)`.

**`__iter__(self)`:**
- Returns `iter(self.cursor)`, making the wrapper itself iterable over cursor rows.

---

### Class: `DatabaseWrapper(BaseDatabaseWrapper)`

The main MySQL database connection wrapper, extending Django's base wrapper class.

#### Class attributes

- **`vendor = 'mysql'`** — Identifies this backend as MySQL.
- **`data_types`** — A dict mapping Django field class names to MySQL column type strings (format strings may contain `%(field_attr)s` keys):
  - `'AutoField': 'integer AUTO_INCREMENT'`
  - `'BigAutoField': 'bigint AUTO_INCREMENT'`
  - `'BinaryField': 'longblob'`
  - `'BooleanField': 'bool'`
  - `'CharField': 'varchar(%(max_length)s)'`
  - `'DateField': 'date'`
  - `'DateTimeField': 'datetime(6)'`
  - `'DecimalField': 'numeric(%(max_digits)s, %(decimal_places)s)'`
  - `'DurationField': 'bigint'`
  - `'FileField': 'varchar(%(max_length)s)'`
  - `'FilePathField': 'varchar(%(max_length)s)'`
  - `'FloatField': 'double precision'`
  - `'IntegerField': 'integer'`
  - `'BigIntegerField': 'bigint'`
  - `'IPAddressField': 'char(15)'`
  - `'GenericIPAddressField': 'char(39)'`
  - `'JSONField': 'json'`
  - `'OneToOneField': 'integer'`
  - `'PositiveBigIntegerField': 'bigint UNSIGNED'`
  - `'PositiveIntegerField': 'integer UNSIGNED'`
  - `'PositiveSmallIntegerField': 'smallint UNSIGNED'`
  - `'SlugField': 'varchar(%(max_length)s)'`
  - `'SmallAutoField': 'smallint AUTO_INCREMENT'`
  - `'SmallIntegerField': 'smallint'`
  - `'TextField': 'longtext'`
  - `'TimeField': 'time(6)'`
  - `'UUIDField': 'char(32)'`

- **`_limited_data_types`** — A tuple of column type strings that do not support full-width database indexes or default values on MySQL < 8.0.13 / MariaDB < 10.2.1: `('tinyblob', 'blob', 'mediumblob', 'longblob', 'tinytext', 'text', 'mediumtext', 'longtext', 'json')`.

- **`operators`** — A dict mapping lookup types to SQL operator templates with `%s` placeholders:
  - `'exact': '= %s'`, `'iexact': 'LIKE %s'`, `'contains': 'LIKE BINARY %s'`, `'icontains': 'LIKE %s'`, `'gt': '> %s'`, `'gte': '>= %s'`, `'lt': '< %s'`, `'lte': '<= %s'`, `'startswith': 'LIKE BINARY %s'`, `'endswith': 'LIKE BINARY %s'`, `'istartswith': 'LIKE %s'`, `'iendswith': 'LIKE %s'`.

- **`pattern_esc = r"REPLACE(REPLACE(REPLACE({}, '\\', '\\\\'), '%%', '\%%'), '_', '\_')"`** — A template for escaping special LIKE characters (`\`, `%`, `_`) on the database side.

- **`pattern_ops`** — Dict of pattern-based lookup SQL templates (using `{}` as the placeholder for the escaped value):
  - `'contains': "LIKE BINARY CONCAT('%%', {}, '%%')"`
  - `'icontains': "LIKE CONCAT('%%', {}, '%%')"`
  - `'startswith': "LIKE BINARY CONCAT({}, '%%')"`
  - `'istartswith': "LIKE CONCAT({}, '%%')"`
  - `'endswith': "LIKE BINARY CONCAT('%%', {})"`
  - `'iendswith': "LIKE CONCAT('%%', {})"`

- **`isolation_levels`** — A set of four string transaction isolation levels: `{'read uncommitted', 'read committed', 'repeatable read', 'serializable'}`.

- **`Database = Database`** — The MySQLdb module, exposed as a class attribute.
- **`SchemaEditorClass = DatabaseSchemaEditor`**
- **`client_class = DatabaseClient`**
- **`creation_class = DatabaseCreation`**
- **`features_class = DatabaseFeatures`**
- **`introspection_class = DatabaseIntrospection`**
- **`ops_class = DatabaseOperations`**
- **`validation_class = DatabaseValidation`**

#### Instance attributes (set in `__init__` or methods)

- **`isolation_level`** — Set by `get_connection_params()`; the resolved transaction isolation level string (or falsy).

---

#### Methods

**`get_connection_params(self)` → dict:**
1. Initializes `kwargs = {'conv': django_conversions, 'charset': 'utf8'}`.
2. Reads `settings_dict = self.settings_dict`.
3. If `settings_dict['USER']` is truthy, sets `kwargs['user'] = settings_dict['USER']`.
4. If `settings_dict['NAME']` is truthy, sets `kwargs['db'] = settings_dict['NAME']`.
5. If `settings_dict['PASSWORD']` is truthy, sets `kwargs['passwd'] = settings_dict['PASSWORD']`.
6. If `settings_dict['HOST']` starts with `/`, sets `kwargs['unix_socket'] = settings_dict['HOST']`; else if `settings_dict['HOST']` is truthy, sets `kwargs['host'] = settings_dict['HOST']`.
7. If `settings_dict['PORT']` is truthy, sets `kwargs['port'] = int(settings_dict['PORT'])`.
8. Sets `kwargs['client_flag'] = CLIENT.FOUND_ROWS` (to get affected-row counts for UPDATEs).
9. Copies `options = settings_dict['OPTIONS']`; pops `'isolation_level'` defaulting to `'read committed'`. If the popped value is truthy, lowercases it and validates against `self.isolation_levels`; if invalid, raises `ImproperlyConfigured` with a message listing valid levels. Stores the resolved level in `self.isolation_level`.
10. Updates `kwargs` with remaining `options`.
11. Returns `kwargs`.

**`@async_unsafe get_new_connection(self, conn_params)` → connection:**
1. Calls `Database.connect(**conn_params)` to create a raw MySQLdb connection.
2. If `connection.encoders.get(bytes) is bytes`, removes the `bytes` key from `connection.encoders` (a workaround for mysqlclient's broken bytes encoder).
3. Returns the connection object.

**`init_connection_state(self)`:**
1. Initializes an empty list `assignments`.
2. If `self.features.is_sql_auto_is_null_enabled`, appends `'SET SQL_AUTO_IS_NULL = 0'` to `assignments` (disabling MySQL's non-standard auto-is-null behavior).
3. If `self.isolation_level` is truthy, appends `'SET SESSION TRANSACTION ISOLATION LEVEL %s' % self.isolation_level.upper()`.
4. If `assignments` is non-empty, opens a cursor via `self.cursor()` and executes `'; '.join(assignments)`.

**`@async_unsafe create_cursor(self, name=None)` → CursorWrapper:**
1. Calls `self.connection.cursor()` to get the raw MySQLdb cursor.
2. Wraps it in `CursorWrapper(cursor)` and returns it.

**`_rollback(self)`:**
- Calls `BaseDatabaseWrapper._rollback(self)` inside a try/except that silently catches `Database.NotSupportedError`.

**`_set_autocommit(self, autocommit)`:**
- Within `self.wrap_database_errors`, calls `self.connection.autocommit(autocommit)`.

**`disable_constraint_checking(self)` → True:**
1. Opens a cursor via `self.cursor()` and executes `'SET foreign_key_checks=0'`.
2. Returns `True`.

**`enable_constraint_checking(self)`:**
1. Saves the current `self.needs_rollback`, then sets it to `False` (overriding any nested `transaction.atomic` state). Stores the old value in a local `needs_rollback`.
2. Opens a cursor via `self.cursor()` and executes `'SET foreign_key_checks=1'`.
3. In a `finally` block, restores `self.needs_rollback = needs_rollback`.

**`check_constraints(self, table_names=None)`:**
1. Opens a cursor via `self.cursor()`.
2. If `table_names is None`, sets it to `self.introspection.table_names(cursor)` (all tables).
3. For each `table_name` in `table_names`:
   - Calls `self.introspection.get_primary_key_column(cursor, table_name)`. If falsy, skips this table.
   - Calls `self.introspection.get_key_columns(cursor, table_name)` to get a list of `(column_name, referenced_table_name, referenced_column_name)` tuples.
   - For each foreign key tuple, executes the SQL query:
     ```sql
     SELECT REFERRING.`<primary_key>`, REFERRING.`<fk_col>` FROM `<table>` as REFERRING
     LEFT JOIN `<ref_table>` as REFERRED ON (REFERRING.`<fk_col>` = REFERRED.`<ref_col>`)
     WHERE REFERRING.`<fk_col>` IS NOT NULL AND REFERRED.`<ref_col>` IS NULL
     ```
   - For each row returned by `cursor.fetchall()`, raises `IntegrityError` with a message: `"The row in table '<table>' with primary key '<pk_val>' has an invalid foreign key: <table>.<fk_col> contains a value '<fk_val>' that does not have a corresponding value in <ref_table>.<ref_col>."`.

**`is_usable(self)` → bool:**
1. Calls `self.connection.ping()`. If it raises `Database.Error`, returns `False`; otherwise returns `True`.

---

#### Cached properties

**`@cached_property display_name` → str:**
- Returns `'MariaDB'` if `self.mysql_is_mariadb` is truthy; otherwise `'MySQL'`.

**`@cached_property data_type_check_constraints` → dict:**
1. If `self.features.supports_column_check_constraints` is falsy, returns `{}`.
2. Otherwise initializes a dict:
   - `'PositiveBigIntegerField': '`%(column)s` >= 0'`
   - `'PositiveIntegerField': '`%(column)s` >= 0'`
   - `'PositiveSmallIntegerField': '`%(column)s` >= 0'`
3. If `self.mysql_is_mariadb` is truthy AND `self.mysql_version < (10, 4, 3)`, adds `'JSONField': 'JSON_VALID(`%(column)s`)'` (because MariaDB < 10.4.3 does not auto-use JSON_VALID as a check constraint).
4. Returns the dict.

**`@cached_property mysql_server_data` → dict:**
1. Opens a temporary connection via `self.temporary_connection()`.
2. Executes:
   ```sql
   SELECT VERSION(),
          @@sql_mode,
          @@default_storage_engine,
          @@sql_auto_is_null,
          @@lower_case_table_names,
          CONVERT_TZ('2001-01-01 01:00:00', 'UTC', 'UTC') IS NOT NULL
   ```
3. Fetches one row and returns a dict with keys:
   - `'version'`: `row[0]` (raw version string)
   - `'sql_mode'`: `row[1]` (raw SQL mode string)
   - `'default_storage_engine'`: `row[2]` (storage engine name)
   - `'sql_auto_is_null'`: `bool(row[3])`
   - `'lower_case_table_names'`: `bool(row[4])`
   - `'has_zoneinfo_database'`: `bool(row[5])`

**`@cached_property mysql_server_info` → str:**
- Returns `self.mysql_server_data['version']`.

**`@cached_property mysql_version` → tuple[int, ...]:**
1. Matches `server_version_re` against `self.mysql_server_info`. If no match, raises `Exception('Unable to determine MySQL version from version string %r' % self.mysql_server_info)`.
2. Returns a tuple of ints from the three captured groups: `tuple(int(x) for x in match.groups())`, e.g. `(8, 0, 27)`.

**`@cached_property mysql_is_mariadb` → bool:**
- Returns `'mariadb' in self.mysql_server_info.lower()`.

**`@cached_property sql_mode` → set[str]:**
1. Gets `sql_mode = self.mysql_server_data['sql_mode']`.
2. If `sql_mode` is truthy, splits on `','`; otherwise returns an empty set.
3. Returns the resulting `set`.

## django/db/backends/mysql/client.py
Here is the complete natural-language specification of `django/db/backends/mysql/client.py`:

---

## 1. Module-Level Preamble

### Imports
- `from django.db.backends.base.client import BaseDatabaseClient`

### Constants & Globals
None beyond what is defined inside the class.

---

## 2. Code Objects (Classes and Functions)

### Class: `DatabaseClient(BaseDatabaseClient)`

**Inheritance:** Extends `BaseDatabaseClient`.

**Class Attributes:**
- `executable_name = 'mysql'` — The name of the MySQL command-line client executable to invoke.

#### Method: `settings_to_cmd_args_env(cls, settings_dict, parameters)`

**Signature (classmethod):**
```python
@classmethod
def settings_to_cmd_args_env(cls, settings_dict: dict, parameters: list) -> tuple[list[str], str | None]
```

**Parameters:**
- `settings_dict` — A dictionary representing the Django database connection configuration. Expected keys include `'NAME'`, `'USER'`, `'PASSWORD'`, `'HOST'`, `'PORT'`, and `'OPTIONS'`. The `'OPTIONS'` sub-dictionary may contain: `'db'`, `'user'`, `'password'`, `'passwd'`, `'host'`, `'port'`, `'ssl'` (itself a dict with keys `'ca'`, `'cert'`, `'key'`), `'read_default_file'`, and `'charset'`.
- `parameters` — A list of additional command-line arguments to append verbatim to the final argument list.

**Return Value:**
A 2-tuple `(args, env)`:
- `args` — A `list[str]` representing the full command-line invocation for the MySQL client. Always starts with `'mysql'`.
- `env` — Either a `dict` containing `{'MYSQL_PWD': password}` when a password is present, or `None` otherwise.

**Implementation Logic (step-by-step):**

1. Initialize `args = [cls.executable_name]` (i.e., `['mysql']`) and `env = None`.
2. Resolve the database name (`db`) by first checking `settings_dict['OPTIONS'].get('db')`; if absent, fall back to `settings_dict['NAME']`.
3. Resolve the username (`user`) by first checking `settings_dict['OPTIONS'].get('user')`; if absent, fall back to `settings_dict['USER']`.
4. Resolve the password (`password`) via a two-level fallback: first check `settings_dict['OPTIONS'].get('password')`; if absent, check `settings_dict['OPTIONS'].get('passwd')`; if that is also absent, fall back to `settings_dict['PASSWORD']`.
5. Resolve the host (`host`) by checking `settings_dict['OPTIONS'].get('host')`; if absent, fall back to `settings_dict['HOST']`.
6. Resolve the port (`port`) by checking `settings_dict['OPTIONS'].get('port')`; if absent, fall back to `settings_dict['PORT']`.
7. Extract SSL/TLS options from nested `'OPTIONS'` → `'ssl'`:
   - `server_ca = settings_dict['OPTIONS'].get('ssl', {}).get('ca')`
   - `client_cert = settings_dict['OPTIONS'].get('ssl', {}).get('cert')`
   - `client_key = settings_dict['OPTIONS'].get('ssl', {}).get('key')`
8. Extract `defaults_file = settings_dict['OPTIONS'].get('read_default_file')`.
9. Extract `charset = settings_dict['OPTIONS'].get('charset')`.
10. Conditionally append CLI flags to `args`:
    - If `defaults_file` is truthy: append `"--defaults-file=<value>"`.
    - If `user` is truthy: append `"--user=<value>"`.
    - If `password` is truthy: set `env = {'MYSQL_PWD': password}` (the password is passed via the `MYSQL_PWD` environment variable rather than a CLI flag, per MySQL documentation and security considerations regarding process listing exposure).
    - If `host` is truthy: if the host string contains `'/'`, append `"--socket=<value>"` (treating it as a Unix socket path); otherwise, append `"--host=<value>"`.
    - If `port` is truthy: append `"--port=<value>"`.
    - If `server_ca` is truthy: append `"--ssl-ca=<value>"`.
    - If `client_cert` is truthy: append `"--ssl-cert=<value>"`.
    - If `client_key` is truthy: append `"--ssl-key=<value>"`.
    - If `charset` is truthy: append `'--default-character-set=<value>'`.
    - If `db` is truthy: append the database name as a positional argument.
11. Append all items from `parameters` to `args` via `args.extend(parameters)`.
12. Return `(args, env)`.

**Notes:**
- The method does not construct any `sql_mode` CLI flag; this is explicitly noted in the source with a comment stating there is no good way to set it via the MySQL CLI.
- The password is never passed as a command-line argument (e.g., `--password=...`). Instead, when present, it is placed into the subprocess environment under the key `'MYSQL_PWD'`. This avoids exposure in process listings and ensures that if `subprocess.run(check=True)` raises a `CalledProcessError`, the password string does not appear in the exception's args representation.