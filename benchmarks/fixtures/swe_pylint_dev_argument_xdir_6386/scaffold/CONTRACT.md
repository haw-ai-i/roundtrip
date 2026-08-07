# Implementation target
Write the following 4 modules. They live in the same package and may import each other.

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

## `pylint/config/arguments_manager.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ConfigProvider`
- `_ArgumentsManager`

## `pylint/config/utils.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `_convert_option_to_argument`
- `_parse_rich_type_value`
- `_preprocess_options`

## `pylint/lint/base_options.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `_make_linter_options`
- `_make_run_options`

Implement them to satisfy the specification. Do not write tests.
