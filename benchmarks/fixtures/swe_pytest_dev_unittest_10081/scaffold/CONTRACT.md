# Implementation target
Write the module at `src/_pytest/unittest.py`.

## `src/_pytest/unittest.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `TestCaseFunction`
- `UnitTestCase`
- `check_testcase_implements_trial_reporter`
- `pytest_pycollect_makeitem`
- `pytest_runtest_makereport`
- `pytest_runtest_protocol`

Implement them to satisfy the specification. Do not write tests.
