# Implementation target
Write the following 4 modules. They live in the same package and may import each other.

## `django/db/backends/mysql/operations.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DatabaseOperations`

## `django/db/backends/oracle/operations.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DatabaseOperations`

## `django/db/backends/sqlite3/base.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DatabaseWrapper`
- `FORMAT_QMARK_REGEX`
- `SQLiteCursorWrapper`
- `check_sqlite_version`
- `decoder`
- `list_aggregate`
- `none_guard`

## `django/db/backends/sqlite3/operations.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DatabaseOperations`

Implement them to satisfy the specification. Do not write tests.
