# Implementation target
Write the module at `django/db/backends/sqlite3/base.py`.

## `django/db/backends/sqlite3/base.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DatabaseWrapper`
- `FORMAT_QMARK_REGEX`
- `SQLiteCursorWrapper`
- `check_sqlite_version`
- `decoder`
- `list_aggregate`
- `none_guard`

Implement them to satisfy the specification. Do not write tests.
