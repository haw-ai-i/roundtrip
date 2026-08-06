# Implementation target
Write the module at `src/_pytest/compat.py`.

## `src/_pytest/compat.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `COLLECT_FAKEMODULE_ATTRIBUTES`
- `CaptureIO`
- `FuncargnamesCompatAttr`
- `MODULE_NOT_FOUND_ERROR`
- `NOTSET`
- `REGEX_TYPE`
- `STRING_TYPES`
- `ascii_escaped`
- `get_default_arg_names`
- `get_real_func`
- `get_real_method`
- `getfslineno`
- `getfuncargnames`
- `getimfunc`
- `getlocation`
- `is_generator`
- `iscoroutinefunction`
- `num_mock_patch_args`
- `safe_getattr`
- `safe_isclass`

Implement them to satisfy the specification. Do not write tests.
