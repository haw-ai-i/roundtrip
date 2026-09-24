## django/contrib/admin/checks.py
```markdown
# Specification for `django/contrib/admin/checks.py`

## 1. Module-Level Preamble

### Imports
- `import collections`
- `from itertools import chain`
- `from django.apps import apps`
- `from django.conf import settings`
- `from django.contrib.admin.utils import NotRelationField, flatten, get_fields_from_path`
- `from django.core import checks`
- `from django.core.exceptions import FieldDoesNotExist`
- `from django.db import models`
- `from django.db.models.constants import LOOKUP_SEP`
- `from django.db.models.expressions import Combinable`
- `from django.forms.models import BaseModelForm, BaseModelFormSet, _get_foreign_key`
- `from django.template import engines`
- `from django.template.backends.django import DjangoTemplates`
- `from django.utils.module_loading import import_string`
- `from django.contrib.admin.sites import all_sites`
- `from django.contrib.admin.options import HORIZONTAL, VERTICAL, InlineModelAdmin, ModelAdmin`
- `from django.contrib.admin import FieldListFilter, ListFilter`

### Constants & Globals
None explicitly defined at the module level.

## 2. Code Objects (Classes and Functions)

### Functions

- **`_issubclass(cls, classinfo)`**
  - **Logic:** A safe variant of `issubclass()` that catches `TypeError` and returns `False` if `cls` is not a class.

- **`_contains_subclass(class_path, candidate_paths)`**
  - **Logic:** Checks if a dotted class path (or its subclass) exists in a list of candidate paths. Uses `import_string` to resolve paths. Ignores `ImportError` for candidates.

- **`check_admin_app(app_configs, **kwargs)`**
  - **Logic:** Iterates over `all_sites` from `django.contrib.admin.sites` and calls `site.check(app_configs)`, aggregating and returning all errors.

- **`check_dependencies(**kwargs)`**
  - **Logic:** Validates that the admin app's dependencies are correctly installed. Checks for `django.contrib.contenttypes`, `django.contrib.auth`, and `django.contrib.messages` in `INSTALLED_APPS`. Verifies that a `DjangoTemplates` instance is configured in `TEMPLATES` and that required context processors (`auth`, `messages`, and optionally `request` if the sidebar is enabled) are present. Also checks that required middleware (`AuthenticationMiddleware`, `MessageMiddleware`, `SessionMiddleware`) are in `MIDDLEWARE`. Returns a list of `checks.Error` or `checks.Warning`.

- **`must_be(type, option, obj, id)`**
  - **Logic:** Returns a list containing a single `checks.Error` indicating that the value of `obj.option` must be of the specified `type`.

- **`must_inherit_from(parent, option, obj, id)`**
  - **Logic:** Returns a list containing a single `checks.Error` indicating that the value of `obj.option` must inherit from `parent`.

- **`refer_to_missing_field(field, option, obj, id)`**
  - **Logic:** Returns a list containing a single `checks.Error` indicating that `obj.option` refers to a missing field `field`.

### Classes

#### `BaseModelAdminChecks`
Base class for checking `ModelAdmin` and `InlineModelAdmin` configurations.

- **`check(self, admin_obj, **kwargs)`**
  - **Logic:** Aggregates and returns the results of various `_check_*` methods for autocomplete fields, raw ID fields, fields, fieldsets, exclude, form, filter vertical/horizontal, radio fields, prepopulated fields, view on site URL, ordering, and readonly fields.

- **`_check_autocomplete_fields(self, obj)`**
  - **Logic:** Validates that `autocomplete_fields` is a list or tuple. Iterates over items and calls `_check_autocomplete_fields_item`.

- **`_check_autocomplete_fields_item(self, obj, field_name, label)`**
  - **Logic:** Validates that the field exists, is a `ForeignKey` or `ManyToManyField`, and that the related model has a registered `ModelAdmin` with `search_fields` defined.

- **`_check_raw_id_fields(self, obj)`**
  - **Logic:** Validates that `raw_id_fields` is a list or tuple. Iterates over items and calls `_check_raw_id_fields_item`.

- **`_check_raw_id_fields_item(self, obj, field_name, label)`**
  - **Logic:** Validates that the field exists and is a `ForeignKey` or `ManyToManyField`.

- **`_check_fields(self, obj)`**
  - **Logic:** Validates that `fields` is a list or tuple, contains no duplicates, and that at most one of `fields` or `fieldsets` is defined.

- **`_check_fieldsets(self, obj)`**
  - **Logic:** Validates that `fieldsets` is a list or tuple, contains no duplicate fieldset names, and iterates over items calling `_check_fieldsets_item`.

- **`_check_fieldsets_item(self, obj, fieldset, label, seen_fields)`**
  - **Logic:** Validates the structure of a fieldset (a tuple of name and a dictionary with a 'fields' key).

- **`_check_field_spec(self, obj, fields, label)`**
  - **Logic:** Validates that `fields` is a string or a tuple of strings.

- **`_check_field_spec_item(self, obj, field_name, label)`**
  - **Logic:** Validates that the field exists on the model or is a valid attribute/callable on the admin object or model.

- **`_check_exclude(self, obj)`**
  - **Logic:** Validates that `exclude` is a list or tuple and contains no duplicates.

- **`_check_form(self, obj)`**
  - **Logic:** Validates that `form` inherits from `BaseModelForm`.

- **`_check_filter_vertical(self, obj)`** / **`_check_filter_horizontal(self, obj)`**
  - **Logic:** Validates that the attribute is a list or tuple and iterates over items calling `_check_filter_item`.

- **`_check_filter_item(self, obj, field_name, label)`**
  - **Logic:** Validates that the field exists and is a `ManyToManyField`.

- **`_check_radio_fields(self, obj)`**
  - **Logic:** Validates that `radio_fields` is a dictionary and iterates over keys/values calling `_check_radio_fields_key` and `_check_radio_fields_value`.

- **`_check_radio_fields_key(self, obj, field_name, label)`**
  - **Logic:** Validates that the field exists and is a `ForeignKey` or has `choices` defined.

- **`_check_radio_fields_value(self, obj, val, label)`**
  - **Logic:** Validates that the value is either `admin.HORIZONTAL` or `admin.VERTICAL`.

- **`_check_view_on_site_url(self, obj)`**
  - **Logic:** Validates that `view_on_site` is a boolean or a callable.

- **`_check_prepopulated_fields(self, obj)`**
  - **Logic:** Validates that `prepopulated_fields` is a dictionary and iterates over keys/values calling `_check_prepopulated_fields_key` and `_check_prepopulated_fields_value`.

- **`_check_prepopulated_fields_key(self, obj, field_name, label)`**
  - **Logic:** Validates that the field exists and is a `CharField`, `ImageField`, or `SlugField`.

- **`_check_prepopulated_fields_value(self, obj, val, label)`**
  - **Logic:** Validates that the value is a list or tuple and iterates over items calling `_check_prepopulated_fields_value_item`.

- **`_check_prepopulated_fields_value_item(self, obj, field_name, label)`**
  - **Logic:** Validates that the field exists.

- **`_check_ordering(self, obj)`**
  - **Logic:** Validates that `ordering` is a list or tuple and iterates over items calling `_check_ordering_item`.

- **`_check_ordering_item(self, obj, field_name, label)`**
  - **Logic:** Validates that the field exists or is a valid random ordering marker (`'?'`).

- **`_check_readonly_fields(self, obj)`**
  - **Logic:** Validates that `readonly_fields` is a list or tuple and iterates over items calling `_check_readonly_fields_item`.

- **`_check_readonly_fields_item(self, obj, field_name, label)`**
  - **Logic:** Validates that the field exists on the model or is a valid attribute/callable on the admin object or model.

#### `ModelAdminChecks(BaseModelAdminChecks)`
Checks specific to `ModelAdmin`.

- **`check(self, admin_obj, **kwargs)`**
  - **Logic:** Extends `BaseModelAdminChecks.check` with checks for `save_as`, `save_on_top`, `inlines`, `list_display`, `list_display_links`, `list_filter`, `list_select_related`, `list_per_page`, `list_max_show_all`, `list_editable`, `search_fields`, `date_hierarchy`, `action_permission_methods`, and `actions_uniqueness`.

- **`_check_save_as(self, obj)`** / **`_check_save_on_top(self, obj)`**
  - **Logic:** Validates that the attribute is a boolean.

- **`_check_inlines(self, obj)`**
  - **Logic:** Validates that `inlines` is a list or tuple and iterates over items calling `_check_inlines_item`.

- **`_check_inlines_item(self, obj, inline, label)`**
  - **Logic:** Validates that the inline inherits from `InlineModelAdmin`.

- **`_check_list_display(self, obj)`**
  - **Logic:** Validates that `list_display` is a list or tuple and iterates over items calling `_check_list_display_item`.

- **`_check_list_display_item(self, obj, item, label)`**
  - **Logic:** Validates that the item is a callable, an attribute of the admin object, an attribute of the model, or a valid field.

- **`_check_list_display_links(self, obj)`**
  - **Logic:** Validates that `list_display_links` is a list, tuple, or `None`, and iterates over items calling `_check_list_display_links_item`.

- **`_check_list_display_links_item(self, obj, field_name, label)`**
  - **Logic:** Validates that the item is present in `list_display`.

- **`_check_list_filter(self, obj)`**
  - **Logic:** Validates that `list_filter` is a list or tuple and iterates over items calling `_check_list_filter_item`.

- **`_check_list_filter_item(self, obj, item, label)`**
  - **Logic:** Validates that the item is a callable, a subclass of `ListFilter`, or a valid field path.

- **`_check_list_select_related(self, obj)`**
  - **Logic:** Validates that `list_select_related` is a boolean, list, or tuple.

- **`_check_list_per_page(self, obj)`** / **`_check_list_max_show_all(self, obj)`**
  - **Logic:** Validates that the attribute is an integer.

- **`_check_list_editable(self, obj)`**
  - **Logic:** Validates that `list_editable` is a list or tuple, does not contain the first item of `list_display_links`, and iterates over items calling `_check_list_editable_item`.

- **`_check_list_editable_item(self, obj, field_name, label)`**
  - **Logic:** Validates that the field is in `list_display` and is an editable field.

- **`_check_search_fields(self, obj)`**
  - **Logic:** Validates that `search_fields` is a list or tuple.

- **`_check_date_hierarchy(self, obj)`**
  - **Logic:** Validates that `date_hierarchy` refers to a valid `DateField` or `DateTimeField`.

- **`_check_action_permission_methods(self, obj)`**
  - **Logic:** Validates that for any action with an `allowed_permissions` attribute, the `ModelAdmin` implements a corresponding `has_<perm>_permission` method.

- **`_check_actions_uniqueness(self, obj)`**
  - **Logic:** Validates that all actions have unique names.

#### `InlineModelAdminChecks(BaseModelAdminChecks)`
Checks specific to `InlineModelAdmin`.

- **`check(self, inline_obj, **kwargs)`**
  - **Logic:** Extends `BaseModelAdminChecks.check` with checks for `exclude_of_parent_model`, `relation`, `extra`, `max_num`, `min_num`, and `formset`.

- **`_check_exclude_of_parent_model(self, obj, parent_model)`**
  - **Logic:** Validates that the parent model is not in `exclude`.

- **`_check_relation(self, obj, parent_model)`**
  - **Logic:** Validates that the inline model has a valid foreign key relationship to the parent model.

- **`_check_extra(self, obj)`** / **`_check_max_num(self, obj)`** / **`_check_min_num(self, obj)`**
  - **Logic:** Validates that the attribute is an integer.

- **`_check_formset(self, obj)`**
  - **Logic:** Validates that `formset` inherits from `BaseModelFormSet`.
```