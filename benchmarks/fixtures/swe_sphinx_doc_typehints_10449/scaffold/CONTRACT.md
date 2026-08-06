# Implementation target
Write the module at `sphinx/ext/autodoc/typehints.py`.

## `sphinx/ext/autodoc/typehints.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `augment_descriptions_with_types`
- `insert_field_list`
- `merge_typehints`
- `modify_field_list`
- `record_typehints`
- `setup`

Implement them to satisfy the specification. Do not write tests.
