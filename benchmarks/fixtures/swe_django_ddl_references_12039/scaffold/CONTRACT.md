# Implementation target
Write the module at `django/db/backends/ddl_references.py`.

## `django/db/backends/ddl_references.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Columns`
- `ForeignKeyName`
- `IndexColumns`
- `IndexName`
- `Reference`
- `Statement`
- `Table`
- `TableColumns`

Implement them to satisfy the specification. Do not write tests.
