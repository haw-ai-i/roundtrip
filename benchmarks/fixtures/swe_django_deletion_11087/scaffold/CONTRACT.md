# Implementation target
Write the module at `django/db/models/deletion.py`.

## `django/db/models/deletion.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CASCADE`
- `Collector`
- `DO_NOTHING`
- `PROTECT`
- `ProtectedError`
- `SET`
- `SET_DEFAULT`
- `SET_NULL`
- `get_candidate_relations_to_delete`

Implement them to satisfy the specification. Do not write tests.
