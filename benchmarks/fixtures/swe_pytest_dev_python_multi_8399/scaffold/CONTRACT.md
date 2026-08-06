# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `src/_pytest/python.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CallSpec2`
- `Class`
- `Function`
- `FunctionDefinition`
- `IGNORED_ATTRIBUTES`
- `Instance`
- `Metafunc`
- `Module`
- `Package`
- `PyCollector`
- `PyobjMixin`
- `async_warn_and_skip`
- `hasinit`
- `hasnew`
- `idmaker`
- `path_matches_patterns`
- `pytest_addoption`
- `pytest_cmdline_main`
- `pytest_collect_file`
- `pytest_configure`
- `pytest_generate_tests`
- `pytest_pycollect_makeitem`
- `pytest_pycollect_makemodule`
- `pytest_pyfunc_call`
- `show_fixtures_per_test`
- `showfixtures`
- `write_docstring`

## `src/_pytest/unittest.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `TestCaseFunction`
- `UnitTestCase`
- `check_testcase_implements_trial_reporter`
- `pytest_pycollect_makeitem`
- `pytest_runtest_makereport`
- `pytest_runtest_protocol`

Implement them to satisfy the specification. Do not write tests.
