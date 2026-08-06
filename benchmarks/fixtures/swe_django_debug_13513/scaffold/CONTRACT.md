# Implementation target
Write the module at `django/views/debug.py`.

## `django/views/debug.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CURRENT_DIR`
- `CallableSettingWrapper`
- `DEBUG_ENGINE`
- `ExceptionCycleWarning`
- `ExceptionReporter`
- `SafeExceptionReporterFilter`
- `default_urlconf`
- `get_default_exception_reporter_filter`
- `get_exception_reporter_class`
- `get_exception_reporter_filter`
- `technical_404_response`
- `technical_500_response`

Implement them to satisfy the specification. Do not write tests.
