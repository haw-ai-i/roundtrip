# Implementation target
Write the module at `django/contrib/admin/checks.py`.

## `django/contrib/admin/checks.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseModelAdminChecks`
- `InlineModelAdminChecks`
- `ModelAdminChecks`
- `check_admin_app`
- `check_dependencies`
- `must_be`
- `must_inherit_from`
- `refer_to_missing_field`

Implement them to satisfy the specification. Do not write tests.
