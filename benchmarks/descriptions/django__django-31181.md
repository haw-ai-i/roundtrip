## django/contrib/admin/helpers.py
**Module-Level Preamble**

**Imports:**
```python
import json
from django import forms
from django.contrib.admin.utils import (
    display_for_field, flatten_fieldsets, help_text_for_field, label_for_field,
    lookup_field,
)
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ManyToManyRel
from django.forms.utils import flatatt
from django.template.defaultfilters import capfirst, linebreaksbr
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext, gettext_lazy as _
```

**Constants & Globals:**
*   `ACTION_CHECKBOX_NAME`: `'_selected_action'`
*   `checkbox`: A `forms.CheckboxInput` instance initialized with `{'class': 'action-select'}` and a `check_test` lambda that always returns `False` (`lambda value: False`).

---

**Code Objects**

**`ActionForm(forms.Form)`**
A form for selecting an action and whether to apply it across all pages.
*   **Attributes:**
    *   `action`: A `forms.ChoiceField` with `label=_('Action:')`.
    *   `select_across`: A `forms.BooleanField` with `label=''`, `required=False`, `initial=0`, and `widget=forms.HiddenInput({'class': 'select-across'})`.

**`AdminForm`**
A wrapper around a form and its fieldsets for the admin interface.
*   **`__init__(self, form, fieldsets, prepopulated_fields, readonly_fields=None, model_admin=None)`**
    *   Assigns `form` and `fieldsets` to `self.form` and `self.fieldsets`.
    *   Initializes `self.prepopulated_fields` as a list of dictionaries. Each dictionary corresponds to an item in `prepopulated_fields.items()` (where the key is `field_name` and the value is `dependencies`), containing:
        *   `'field'`: `form[field_name]`
        *   `'dependencies'`: A list of `form[f]` for each `f` in `dependencies`.
    *   Assigns `model_admin` to `self.model_admin`.
    *   Assigns `readonly_fields` to `self.readonly_fields`, defaulting to an empty tuple `()` if `None`.
*   **`__iter__(self)`**
    *   Yields a `Fieldset` instance for each `(name, options)` pair in `self.fieldsets`. The `Fieldset` is initialized with `self.form`, `name`, `readonly_fields=self.readonly_fields`, `model_admin=self.model_admin`, and unpacked `**options`.
*   **`errors(self)` (Property)**
    *   Returns `self.form.errors`.
*   **`non_field_errors(self)` (Property)**
    *   Returns `self.form.non_field_errors`.
*   **`media(self)` (Property)**
    *   Starts with `self.form.media`. Iterates over `self` (yielding `Fieldset`s) and adds each fieldset's `media` to the total media. Returns the combined media.

**`Fieldset`**
Represents a fieldset in the admin form.
*   **`__init__(self, form, name=None, readonly_fields=(), fields=(), classes=(), description=None, model_admin=None)`**
    *   Assigns all parameters to instance attributes: `self.form`, `self.name`, `self.fields`, `self.description`, `self.model_admin`, and `self.readonly_fields`. `self.classes` is set to `' '.join(classes)`.
*   **`media(self)` (Property)**
    *   Returns `forms.Media(js=['admin/js/collapse.js'])` if `'collapse'` is in `self.classes`. Otherwise, returns an empty `forms.Media()`.
*   **`__iter__(self)`**
    *   Yields a `Fieldline` instance for each `field` in `self.fields`, initialized with `self.form`, `field`, `self.readonly_fields`, and `model_admin=self.model_admin`.

**`Fieldline`**
Represents a line of fields in a fieldset.
*   **`__init__(self, form, field, readonly_fields=None, model_admin=None)`**
    *   Assigns `form` to `self.form`.
    *   If `field` is not iterable or is a string, sets `self.fields = [field]`. Otherwise, sets `self.fields = field`.
    *   Sets `self.has_visible_field` to `True` if not all fields in `self.fields` are hidden (a field is hidden if it's in `self.form.fields` and its widget's `is_hidden` is true).
    *   Assigns `model_admin` to `self.model_admin`.
    *   Assigns `readonly_fields` to `self.readonly_fields`, defaulting to `()` if `None`.
*   **`__iter__(self)`**
    *   Iterates over `enumerate(self.fields)`. For each `(i, field)`:
        *   If `field` is in `self.readonly_fields`, yields an `AdminReadonlyField` initialized with `self.form`, `field`, `is_first=(i == 0)`, and `model_admin=self.model_admin`.
        *   Otherwise, yields an `AdminField` initialized with `self.form`, `field`, and `is_first=(i == 0)`.
*   **`errors(self)`**
    *   Returns a `mark_safe` string containing the newline-joined `as_ul()` errors for each field in `self.fields` that is not in `self.readonly_fields`. The resulting string has trailing/leading newlines stripped.

**`AdminField`**
A wrapper for a bound form field in the admin.
*   **`__init__(self, form, field, is_first)`**
    *   Sets `self.field = form[field]`.
    *   Sets `self.is_first = is_first`.
    *   Sets `self.is_checkbox` to `True` if `self.field.field.widget` is an instance of `forms.CheckboxInput`, else `False`.
    *   Sets `self.is_readonly = False`.
*   **`label_tag(self)`**
    *   Escapes `self.field.label` using `conditional_escape`.
    *   Builds a list of CSS classes: adds `'vCheckboxLabel'` if `self.is_checkbox`, `'required'` if `self.field.field.required`, and `'inline'` if not `self.is_first`.
    *   Calls `self.field.label_tag()` with the escaped contents (wrapped in `mark_safe`), the classes as `attrs={'class': ...}`, and `label_suffix=''` if `self.is_checkbox` (otherwise `None`). Returns the result.
*   **`errors(self)`**
    *   Returns `mark_safe(self.field.errors.as_ul())`.

**`AdminReadonlyField`**
A wrapper for a read-only field or callable in the admin.
*   **`__init__(self, form, field, is_first, model_admin=None)`**
    *   Determines `class_name`: if `field` is callable, uses `field.__name__` (or `''` if it's `'<lambda>'`); otherwise uses `field`.
    *   Determines `label`: looks up `class_name` in `form._meta.labels`; if not found, uses `label_for_field(field, form._meta.model, model_admin, form=form)`.
    *   Determines `help_text`: looks up `class_name` in `form._meta.help_texts`; if not found, uses `help_text_for_field(class_name, form._meta.model)`.
    *   Sets `self.field` to a dict: `{'name': class_name, 'label': label, 'help_text': help_text, 'field': field}`.
    *   Assigns `form`, `model_admin`, and `is_first` to instance attributes.
    *   Sets `self.is_checkbox = False` and `self.is_readonly = True`.
    *   Sets `self.empty_value_display = model_admin.get_empty_value_display()`.
*   **`label_tag(self)`**
    *   Returns an HTML `<label>` tag using `format_html`. Adds `class="inline"` if not `self.is_first`. The label text is `capfirst(self.field['label'])` followed by `self.form.label_suffix`.
*   **`contents(self)`**
    *   Imports `_boolean_icon` from `django.contrib.admin.templatetags.admin_list`.
    *   Attempts to get `f, attr, value` using `lookup_field(field, obj, model_admin)`.
    *   If `AttributeError`, `ValueError`, or `ObjectDoesNotExist` is raised, sets `result_repr = self.empty_value_display`.
    *   Otherwise:
        *   If `field` is in `self.form.fields` and its widget has `read_only=True`, returns `widget.render(field, value)`.
        *   If `f` is `None`:
            *   If `attr.boolean` is true, `result_repr = _boolean_icon(value)`.
            *   Else if `value` has `__html__`, `result_repr = value`.
            *   Else, `result_repr = linebreaksbr(value)`.
        *   If `f` is not `None`:
            *   If `f.remote_field` is a `ManyToManyRel` and `value` is not `None`, `result_repr` is a comma-separated string of `value.all()`.
            *   Else, `result_repr = display_for_field(value, f, self.empty_value_display)`.
            *   Applies `linebreaksbr(result_repr)`.
    *   Returns `conditional_escape(result_repr)`.

**`InlineAdminFormSet`**
A wrapper around an inline formset.
*   **`__init__(self, inline, formset, fieldsets, prepopulated_fields=None, readonly_fields=None, model_admin=None, has_add_permission=True, has_change_permission=True, has_delete_permission=True, has_view_permission=True)`**
    *   Assigns parameters to instance attributes. Defaults `readonly_fields` to `()` and `prepopulated_fields` to `{}`. Sets `self.classes` to `' '.join(inline.classes)` if present, else `''`.
*   **`__iter__(self)`**
    *   Determines `readonly_fields_for_editing`: `self.readonly_fields` if `self.has_change_permission`, else `self.readonly_fields + flatten_fieldsets(self.fieldsets)`.
    *   Yields an `InlineAdminForm` for each `(form, original)` in `zip(self.formset.initial_forms, self.formset.get_queryset())`. Passes `view_on_site_url=self.opts.get_view_on_site_url(original)`.
    *   Yields an `InlineAdminForm` for each `form` in `self.formset.extra_forms` (with `original=None`).
    *   If `self.has_add_permission`, yields an `InlineAdminForm` for `self.formset.empty_form` (with `original=None`).
*   **`fields(self)`**
    *   Yields a dictionary for each field in `flatten_fieldsets(self.fieldsets)`. Skips the foreign key field (`self.formset.fk.name`).
        *   If no change permission or field is readonly: yields dict with `name`, `label` (from meta or `label_for_field`), `widget: {'is_hidden': False}`, `required: False`, and `help_text`.
        *   Otherwise: yields dict with `name`, `label`, `widget`, `required`, and `help_text` from the empty form's field.
*   **`inline_formset_data(self)`**
    *   Returns a JSON string containing configuration for the inline formset JavaScript (name, prefix, addText, deleteText).
*   **`forms(self)` (Property)**
    *   Returns `self.formset.forms`.
*   **`non_form_errors(self)` (Property)**
    *   Returns `self.formset.non_form_errors`.
*   **`media(self)` (Property)**
    *   Combines `self.opts.media`, `self.formset.media`, and the media of all fieldsets in `self`.

**`InlineAdminForm(AdminForm)`**
A wrapper around an inline form.
*   **`__init__(self, formset, form, fieldsets, prepopulated_fields, original, readonly_fields=None, model_admin=None, view_on_site_url=None)`**
    *   Assigns `formset`, `model_admin`, `original`. Sets `self.show_url = original and view_on_site_url is not None` and `self.absolute_url = view_on_site_url`. Calls `super().__init__`.
*   **`__iter__(self)`**
    *   Yields an `InlineFieldset` for each `(name, options)` in `self.fieldsets`.
*   **`needs_explicit_pk_field(self)`**
    *   Returns `True` if the model has an auto field, or its PK is not editable, or any parent model has an auto field or non-editable PK.
*   **`pk_field(self)`**
    *   Returns `AdminField(self.form, self.formset._pk_field.name, False)`.
*   **`fk_field(self)`**
    *   Returns `AdminField(self.form, fk.name, False)` if `self.formset.fk` exists, else `""`.
*   **`deletion_field(self)`**
    *   Imports `DELETION_FIELD_NAME` from `django.forms.formsets`. Returns `AdminField(self.form, DELETION_FIELD_NAME, False)`.
*   **`ordering_field(self)`**
    *   Imports `ORDERING_FIELD_NAME` from `django.forms.formsets`. Returns `AdminField(self.form, ORDERING_FIELD_NAME, False)`.

**`InlineFieldset(Fieldset)`**
A fieldset for an inline form.
*   **`__init__(self, formset, *args, **kwargs)`**
    *   Assigns `self.formset = formset` and calls `super().__init__(*args, **kwargs)`.
*   **`__iter__(self)`**
    *   Yields a `Fieldline` for each field in `self.fields`, skipping the foreign key field (`self.formset.fk.name`) if it exists.

**`AdminErrorList(forms.utils.ErrorList)`**
Stores errors for forms/formsets in admin views.
*   **`__init__(self, form, inline_formsets)`**
    *   Calls `super().__init__()`. If `form.is_bound`, extends `self` with `form.errors.values()`. Then iterates over `inline_formsets`, extending `self` with `inline_formset.non_form_errors()` and the values of each error dict in `inline_formset.errors`.