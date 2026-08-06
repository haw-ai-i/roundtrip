# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/db/backends/base/client.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseDatabaseClient`

## `django/db/backends/postgresql/client.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DatabaseClient`

Implement them to satisfy the specification. Do not write tests.
