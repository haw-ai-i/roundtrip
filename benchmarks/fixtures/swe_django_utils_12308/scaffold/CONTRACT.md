# Implementation target
Write the module at `django/contrib/admin/utils.py`.

## `django/contrib/admin/utils.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `FieldIsAForeignKeyColumnName`
- `NestedObjects`
- `NotRelationField`
- `QUOTE_MAP`
- `UNQUOTE_MAP`
- `UNQUOTE_RE`
- `construct_change_message`
- `display_for_field`
- `display_for_value`
- `flatten`
- `flatten_fieldsets`
- `get_deleted_objects`
- `get_fields_from_path`
- `get_model_from_relation`
- `help_text_for_field`
- `label_for_field`
- `lookup_field`
- `lookup_needs_distinct`
- `model_format_dict`
- `model_ngettext`
- `prepare_lookup_value`
- `quote`
- `reverse_field_path`
- `unquote`

Implement them to satisfy the specification. Do not write tests.
