# Implementation target
Write the following 3 modules. They live in the same package and may import each other.

## `pylint/config/argument.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `NO_VALUES`
- `YES_VALUES`
- `_Argument`
- `_CallableArgument`
- `_ExtendArgument`
- `_StoreArgument`
- `_StoreNewNamesArgument`
- `_StoreOldNamesArgument`
- `_StoreTrueArgument`

## `pylint/utils/__init__.py`
Other modules import these names from it, so they MUST exist with these exact names:

## `pylint/utils/utils.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CMPS`
- `DEFAULT_LINE_LENGTH`
- `GLOBAL_OPTION_BOOL`
- `GLOBAL_OPTION_INT`
- `GLOBAL_OPTION_LIST`
- `GLOBAL_OPTION_NAMES`
- `GLOBAL_OPTION_PATTERN`
- `GLOBAL_OPTION_PATTERN_LIST`
- `GLOBAL_OPTION_TUPLE_INT`
- `IsortDriver`
- `T_GlobalOptionReturnTypes`
- `_check_csv`
- `_check_regexp_csv`
- `_splitstrip`
- `_unquote`
- `cmp`
- `decoding_stream`
- `diff_string`
- `format_section`
- `get_module_and_frameid`
- `get_rst_section`
- `get_rst_title`
- `normalize_text`
- `register_plugins`
- `tokenize_module`

Implement them to satisfy the specification. Do not write tests.
