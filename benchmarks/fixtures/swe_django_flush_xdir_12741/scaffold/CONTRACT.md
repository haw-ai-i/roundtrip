# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/core/management/commands/flush.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Command`

## `django/db/backends/base/operations.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseDatabaseOperations`

Implement them to satisfy the specification. Do not write tests.
