# Implementation target
Write the module at `django/db/migrations/state.py`.

## `django/db/migrations/state.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AppConfigStub`
- `ModelState`
- `ProjectState`
- `StateApps`
- `get_related_models_recursive`
- `get_related_models_tuples`

Implement them to satisfy the specification. Do not write tests.
