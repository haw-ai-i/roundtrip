# Implementation target
Write the module at `django/db/models/sql/compiler.py`.

## `django/db/models/sql/compiler.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `FORCE`
- `SQLAggregateCompiler`
- `SQLCompiler`
- `SQLDeleteCompiler`
- `SQLInsertCompiler`
- `SQLUpdateCompiler`
- `cursor_iter`

Implement them to satisfy the specification. Do not write tests.
