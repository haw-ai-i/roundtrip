# Implementation target
Write the module at `src/_pytest/skipping.py`.

## `src/_pytest/skipping.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Skip`
- `Xfail`
- `evaluate_condition`
- `evaluate_skip_marks`
- `evaluate_xfail_marks`
- `pytest_addoption`
- `pytest_configure`
- `pytest_report_teststatus`
- `pytest_runtest_call`
- `pytest_runtest_makereport`
- `pytest_runtest_setup`
- `skipped_by_mark_key`
- `unexpectedsuccess_key`
- `xfailed_key`

Implement them to satisfy the specification. Do not write tests.
