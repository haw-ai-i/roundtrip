# Implementation target
Write the module at `django/contrib/admin/options.py`.

## `django/contrib/admin/options.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseModelAdmin`
- `FORMFIELD_FOR_DBFIELD_DEFAULTS`
- `IS_POPUP_VAR`
- `IncorrectLookupParameters`
- `InlineModelAdmin`
- `ModelAdmin`
- `StackedInline`
- `TO_FIELD_VAR`
- `TabularInline`
- `csrf_protect_m`
- `get_content_type_for_model`
- `get_ul_class`

Implement them to satisfy the specification. Do not write tests.
