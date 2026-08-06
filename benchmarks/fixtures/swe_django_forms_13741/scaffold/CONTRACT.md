# Implementation target
Write the module at `django/contrib/auth/forms.py`.

## `django/contrib/auth/forms.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AdminPasswordChangeForm`
- `AuthenticationForm`
- `PasswordChangeForm`
- `PasswordResetForm`
- `ReadOnlyPasswordHashField`
- `ReadOnlyPasswordHashWidget`
- `SetPasswordForm`
- `UserChangeForm`
- `UserCreationForm`
- `UserModel`
- `UsernameField`

Implement them to satisfy the specification. Do not write tests.
