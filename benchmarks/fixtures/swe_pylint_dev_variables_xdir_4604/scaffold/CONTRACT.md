# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `pylint/checkers/variables.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BUILTIN_RANGE`
- `FUTURE`
- `IGNORED_ARGUMENT_NAMES`
- `METACLASS_NAME_TRANSFORMS`
- `MSGS`
- `NamesConsumer`
- `SPECIAL_OBJ`
- `ScopeConsumer`
- `TYPING_MODULE`
- `TYPING_NAMES`
- `TYPING_TYPE_CHECKS_GUARDS`
- `VariablesChecker`
- `in_for_else_branch`
- `overridden_method`
- `register`

## `pylint/constants.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `IS_PYPY`
- `MAIN_CHECKER_NAME`
- `MSG_STATE_CONFIDENCE`
- `MSG_STATE_SCOPE_CONFIG`
- `MSG_STATE_SCOPE_MODULE`
- `MSG_TYPES`
- `MSG_TYPES_LONG`
- `MSG_TYPES_STATUS`
- `PY310_PLUS`
- `PY38_PLUS`
- `PY39_PLUS`
- `PY_EXTS`
- `WarningScope`
- `_MSG_ORDER`
- `_SCOPE_EXEMPT`
- `full_version`

Implement them to satisfy the specification. Do not write tests.
