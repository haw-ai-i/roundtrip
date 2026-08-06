# Implementation target
Write the module at `django/utils/formats.py`.

## `django/utils/formats.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `FORMAT_SETTINGS`
- `ISO_INPUT_FORMATS`
- `date_format`
- `get_format`
- `get_format_lazy`
- `get_format_modules`
- `iter_format_modules`
- `localize`
- `localize_input`
- `number_format`
- `reset_format_cache`
- `sanitize_separators`
- `sanitize_strftime_format`
- `time_format`

Implement them to satisfy the specification. Do not write tests.
