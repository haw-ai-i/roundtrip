# Implementation target
Write the module at `django/contrib/auth/backends.py`.

## `django/contrib/auth/backends.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AllowAllUsersModelBackend`
- `AllowAllUsersRemoteUserBackend`
- `BaseBackend`
- `ModelBackend`
- `RemoteUserBackend`
- `UserModel`

Implement them to satisfy the specification. Do not write tests.
