# Implementation target
Write the module at `django/template/autoreload.py`.

## `django/template/autoreload.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `get_template_directories`
- `reset_loaders`
- `template_changed`
- `watch_for_template_changes`

Implement them to satisfy the specification. Do not write tests.
