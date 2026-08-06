# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/contrib/admindocs/utils.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ROLES`
- `create_reference_role`
- `default_reference_role`
- `get_view_name`
- `named_group_matcher`
- `parse_docstring`
- `parse_rst`
- `replace_named_groups`
- `replace_unnamed_groups`
- `unnamed_group_matcher`

## `django/contrib/admindocs/views.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseAdminDocsView`
- `BookmarkletsView`
- `MODEL_METHODS_EXCLUDE`
- `ModelDetailView`
- `ModelIndexView`
- `TemplateDetailView`
- `TemplateFilterIndexView`
- `TemplateTagIndexView`
- `ViewDetailView`
- `ViewIndexView`
- `extract_views_from_urlpatterns`
- `get_readable_field_data_type`
- `get_return_data_type`
- `simplify_regex`

Implement them to satisfy the specification. Do not write tests.
