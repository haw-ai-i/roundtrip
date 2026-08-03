# Implementation target
Write the module at `src/_pytest/setuponly.py`.

## `src/_pytest/setuponly.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `pytest_addoption`
- `pytest_cmdline_main`
- `pytest_fixture_post_finalizer`
- `pytest_fixture_setup`

Implement them to satisfy the specification. Do not write tests.
