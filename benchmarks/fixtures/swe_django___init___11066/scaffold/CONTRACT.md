# Implementation target
Write the module at `django/contrib/contenttypes/management/__init__.py`.

## `django/contrib/contenttypes/management/__init__.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `RenameContentType`
- `create_contenttypes`
- `get_contenttypes_and_models`
- `inject_rename_contenttypes_operations`

Implement them to satisfy the specification. Do not write tests.
