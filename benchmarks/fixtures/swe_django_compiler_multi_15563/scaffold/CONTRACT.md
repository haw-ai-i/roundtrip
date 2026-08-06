# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/db/models/sql/compiler.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `SQLAggregateCompiler`
- `SQLCompiler`
- `SQLDeleteCompiler`
- `SQLInsertCompiler`
- `SQLUpdateCompiler`
- `cursor_iter`

## `django/db/models/sql/subqueries.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AggregateQuery`
- `DeleteQuery`
- `InsertQuery`
- `UpdateQuery`

Implement them to satisfy the specification. Do not write tests.
