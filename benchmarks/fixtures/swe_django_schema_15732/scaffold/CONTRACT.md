# Implementation target
Write the module at `django/db/backends/base/schema.py`.

## `django/db/backends/base/schema.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseDatabaseSchemaEditor`
- `_related_non_m2m_objects`
- `logger`

Implement them to satisfy the specification. Do not write tests.
