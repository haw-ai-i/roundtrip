# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/db/backends/mysql/base.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CursorWrapper`
- `DatabaseWrapper`
- `django_conversions`
- `server_version_re`
- `version`

## `django/db/backends/mysql/client.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DatabaseClient`

Implement them to satisfy the specification. Do not write tests.
