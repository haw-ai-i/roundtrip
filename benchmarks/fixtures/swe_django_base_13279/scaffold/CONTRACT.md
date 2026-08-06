# Implementation target
Write the module at `django/contrib/sessions/backends/base.py`.

## `django/contrib/sessions/backends/base.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CreateError`
- `SessionBase`
- `UpdateError`
- `VALID_KEY_CHARS`

Implement them to satisfy the specification. Do not write tests.
