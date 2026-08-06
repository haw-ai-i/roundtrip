# Implementation target
Write the module at `django/contrib/staticfiles/storage.py`.

## `django/contrib/staticfiles/storage.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ConfiguredStorage`
- `HashedFilesMixin`
- `ManifestFilesMixin`
- `ManifestStaticFilesStorage`
- `StaticFilesStorage`
- `staticfiles_storage`

Implement them to satisfy the specification. Do not write tests.
