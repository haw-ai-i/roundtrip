# Implementation target
Write the module at `src/_pytest/python.py`.

## `src/_pytest/python.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CallSpec2`
- `Class`
- `Function`
- `FunctionDefinition`
- `FunctionMixin`
- `Instance`
- `Metafunc`
- `Module`
- `Package`
- `PyCollector`
- `PyobjContext`
- `PyobjMixin`
- `hasinit`
- `hasnew`
- `idmaker`
- `path_matches_patterns`
- `pyobj_property`
- `pytest_addoption`
- `pytest_cmdline_main`
- `pytest_collect_file`
- `pytest_configure`
- `pytest_generate_tests`
- `pytest_make_parametrize_id`
- `pytest_pycollect_makeitem`
- `pytest_pycollect_makemodule`
- `pytest_pyfunc_call`
- `show_fixtures_per_test`
- `showfixtures`
- `write_docstring`

Implement them to satisfy the specification. Do not write tests.
