## django/forms/forms.py
**1. Module-Level Preamble**

*   **Imports:**
    *   `from __future__ import unicode_literals`
    *   `from collections import OrderedDict`
    *   `import copy`
    *   `import datetime`
    *   `import warnings`
    *   `from django.core.exceptions import ValidationError, NON_FIELD_ERRORS`
    *   `from django.forms.fields import Field, FileField`
    *   `from django.forms.utils import flatatt, ErrorDict, ErrorList`
    *   `from django.forms.widgets import Media, MediaDefiningClass, TextInput, Textarea`
    *   `from django.utils.deprecation import RemovedInDjango19Warning`
    *   `from django.utils.encoding import smart_text, force_text, python_2_unicode_compatible`
    *   `from django.utils.html import conditional_escape, format_html`
    *   `from django.utils.safestring import mark_safe`
    *   `from django.utils.translation import ugettext as _`
    *   `from django.utils import six`
*   **Constants & Globals:**
    *   `__all__ = ('BaseForm', 'Form')`

**2. Code Objects (Classes and Functions)**

*   **Function: `pretty_name(name)`**
    *   **Signature:** `def pretty_name(name):`
    *   **Implementation Logic:**
        *   If `name` is falsy, return an empty string `''`.
        *   Otherwise, replace all underscores `'_'` in `name` with spaces `' '`, capitalize the resulting string, and return it.

*   **Function: `get_declared_fields(bases, attrs, with_base_fields=True)`**
    *   **Signature:** `def get_declared_fields(bases, attrs, with_base_fields=True):`
    *   **Implementation Logic:**
        *   Issue a `RemovedInDjango19Warning` using `warnings.warn` stating that the function is deprecated and will be removed in Django 1.9 (stacklevel=2).
        *   Extract all items from `attrs` where the value is an instance of `Field`. Remove these items from `attrs` using `pop`. Store them as a list of `(field_name, obj)` tuples.
        *   Sort this list of tuples based on the `creation_counter` attribute of the `Field` objects (the second element of each tuple).
        *   If `with_base_fields` is `True`:
            *   Iterate over `bases` in reverse order (`bases[::-1]`).
            *   For each base class, if it has a `base_fields` attribute, prepend its items (as a list of tuples) to the current list of fields.
        *   If `with_base_fields` is `False`:
            *   Iterate over `bases` in reverse order.
            *   For each base class, if it has a `declared_fields` attribute, prepend its items to the current list of fields.
        *   Return an `OrderedDict` constructed from the final list of fields.

*   **Class: `DeclarativeFieldsMetaclass`**
    *   **Inheritance:** `MediaDefiningClass`
    *   **Method: `__new__(mcs, name, bases, attrs)`**
        *   **Signature:** `def __new__(mcs, name, bases, attrs):`
        *   **Implementation Logic:**
            *   Iterate over a list of `attrs.items()`. If a value is an instance of `Field`, append `(key, value)` to a `current_fields` list and remove the key from `attrs`.
            *   Sort `current_fields` by the `creation_counter` of the fields.
            *   Set `attrs['declared_fields']` to an `OrderedDict` of `current_fields`.
            *   Call `super().__new__(mcs, name, bases, attrs)` to create the `new_class`.
            *   Initialize an empty `OrderedDict` called `declared_fields`.
            *   Iterate over `new_class.__mro__` in reverse order.
                *   If the base class has a `declared_fields` attribute, update `declared_fields` with it.
                *   Iterate over `base.__dict__.items()`. If a value is `None` and the attribute name is in `declared_fields`, remove it from `declared_fields` (field shadowing).
            *   Set both `new_class.base_fields` and `new_class.declared_fields` to `declared_fields`.
            *   Return `new_class`.

*   **Class: `BaseForm`**
    *   **Inheritance:** `object`
    *   **Decorators:** `@python_2_unicode_compatible`
    *   **Method: `__init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False)`**
        *   **Implementation Logic:**
            *   Set `self.is_bound` to `True` if either `data` or `files` is not `None`, else `False`.
            *   Set `self.data` to `data` or `{}`.
            *   Set `self.files` to `files` or `{}`.
            *   Set `self.auto_id` to `auto_id`.
            *   Set `self.prefix` to `prefix`.
            *   Set `self.initial` to `initial` or `{}`.
            *   Set `self.error_class` to `error_class`.
            *   Set `self.label_suffix` to `label_suffix` if it is not `None`, else `_(':')`.
            *   Set `self.empty_permitted` to `empty_permitted`.
            *   Set `self._errors` and `self._changed_data` to `None`.
            *   Set `self.fields` to a deep copy of `self.base_fields`.
    *   **Method: `__str__(self)`**
        *   **Implementation Logic:** Returns `self.as_table()`.
    *   **Method: `__iter__(self)`**
        *   **Implementation Logic:** Yields `self[name]` for each `name` in `self.fields`.
    *   **Method: `__getitem__(self, name)`**
        *   **Implementation Logic:**
            *   Attempts to get `field` from `self.fields[name]`.
            *   If `KeyError` is raised, raises a new `KeyError` with a formatted message: `"Key %r not found in '%s'"` using `name` and the class name.
            *   Returns a new `BoundField(self, field, name)`.
    *   **Property: `errors`**
        *   **Implementation Logic:**
            *   If `self._errors` is `None`, calls `self.full_clean()`.
            *   Returns `self._errors`.
    *   **Method: `is_valid(self)`**
        *   **Implementation Logic:** Returns `True` if `self.is_bound` is true and `self.errors` is falsy, else `False`.
    *   **Method: `add_prefix(self, field_name)`**
        *   **Implementation Logic:** Returns `'%s-%s' % (self.prefix, field_name)` if `self.prefix` is truthy, else returns `field_name`.
    *   **Method: `add_initial_prefix(self, field_name)`**
        *   **Implementation Logic:** Returns `'initial-%s' % self.add_prefix(field_name)`.
    *   **Method: `_html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row)`**
        *   **Implementation Logic:**
            *   Initializes `top_errors` with `self.non_field_errors()`.
            *   Initializes `output` and `hidden_fields` as empty lists.
            *   Iterates over `self.fields.items()`:
                *   Gets the `BoundField` `bf = self[name]`.
                *   Creates `bf_errors` by applying `conditional_escape` to each error in `bf.errors` and wrapping them in `self.error_class`.
                *   If `bf.is_hidden`:
                    *   If `bf_errors` exist, appends formatted error strings to `top_errors`.
                    *   Appends `six.text_type(bf)` to `hidden_fields`.
                *   Else (visible field):
                    *   Gets `css_classes` from `bf.css_classes()`. If truthy, formats as `' class="%s"'`.
                    *   If `errors_on_separate_row` and `bf_errors`, appends `error_row % force_text(bf_errors)` to `output`.
                    *   Formats `label` using `conditional_escape(force_text(bf.label))` and `bf.label_tag()`.
                    *   Formats `help_text` using `help_text_html` if `field.help_text` exists.
                    *   Appends `normal_row` formatted with a dictionary containing `errors`, `label`, `field`, `help_text`, `html_class_attr`, and `field_name` to `output`.
            *   If `top_errors` exist, inserts `error_row % force_text(top_errors)` at the beginning of `output`.
            *   If `hidden_fields` exist:
                *   Joins them into `str_hidden`.
                *   If `output` is not empty, modifies the last row to insert `str_hidden` before `row_ender`. If the last row doesn't end with `row_ender`, appends a new empty row and inserts `str_hidden` there.
                *   If `output` is empty, appends `str_hidden` to `output`.
            *   Returns `mark_safe('\n'.join(output))`.
    *   **Method: `as_table(self)`**
        *   **Implementation Logic:** Calls and returns `self._html_output` with specific HTML strings for table rows (`<tr>`, `<th>`, `<td>`).
    *   **Method: `as_ul(self)`**
        *   **Implementation Logic:** Calls and returns `self._html_output` with specific HTML strings for unordered list items (`<li>`).
    *   **Method: `as_p(self)`**
        *   **Implementation Logic:** Calls and returns `self._html_output` with specific HTML strings for paragraphs (`<p>`), setting `errors_on_separate_row=True`.
    *   **Method: `non_field_errors(self)`**
        *   **Implementation Logic:** Returns `self.errors.get(NON_FIELD_ERRORS, self.error_class())`.
    *   **Method: `_raw_value(self, fieldname)`**
        *   **Implementation Logic:** Gets the field, calculates its prefix, and returns `field.widget.value_from_datadict(self.data, self.files, prefix)`.
    *   **Method: `add_error(self, field, error)`**
        *   **Implementation Logic:**
            *   If `error` is not a `ValidationError`, wraps it in one.
            *   If `error` has an `error_dict` attribute:
                *   If `field` is not `None`, raises a `TypeError`.
                *   Sets `error` to `error.error_dict`.
            *   Else, sets `error` to `{field or NON_FIELD_ERRORS: error.error_list}`.
            *   Iterates over `error.items()`:
                *   If the field is not in `self.errors`:
                    *   If the field is not `NON_FIELD_ERRORS` and not in `self.fields`, raises a `ValueError`.
                    *   Initializes `self._errors[field]` with `self.error_class()`.
                *   Extends `self._errors[field]` with the error list.
                *   If the field is in `self.cleaned_data`, deletes it from `self.cleaned_data`.
    *   **Method: `has_error(self, field, code=None)`**
        *   **Implementation Logic:**
            *   If `code` is `None`, returns `field in self.errors`.
            *   If `field` is in `self.errors`, iterates over `self.errors.as_data()[field]` and returns `True` if any error's `code` matches `code`.
            *   Returns `False`.
    *   **Method: `full_clean(self)`**
        *   **Implementation Logic:**
            *   Sets `self._errors = ErrorDict()`.
            *   If not `self.is_bound`, returns immediately.
            *   Sets `self.cleaned_data = {}`.
            *   If `self.empty_permitted` is true and `self.has_changed()` is false, returns immediately.
            *   Calls `self._clean_fields()`, `self._clean_form()`, and `self._post_clean()`.
    *   **Method: `_clean_fields(self)`**
        *   **Implementation Logic:**
            *   Iterates over `self.fields.items()`.
            *   Gets the value using `field.widget.value_from_datadict`.
            *   In a try block:
                *   If the field is a `FileField`, gets the initial value and calls `field.clean(value, initial)`.
                *   Else, calls `field.clean(value)`.
                *   Stores the result in `self.cleaned_data[name]`.
                *   If `self` has a method named `clean_<name>`, calls it and updates `self.cleaned_data[name]` with its return value.
            *   Catches `ValidationError` and calls `self.add_error(name, e)`.
    *   **Method: `_clean_form(self)`**
        *   **Implementation Logic:**
            *   In a try block, calls `self.clean()`.
            *   Catches `ValidationError` and calls `self.add_error(None, e)`.
            *   In the else block, if the returned `cleaned_data` is not `None`, updates `self.cleaned_data` with it.
    *   **Method: `_post_clean(self)`**
        *   **Implementation Logic:** A no-op (`pass`).
    *   **Method: `clean(self)`**
        *   **Implementation Logic:** Returns `self.cleaned_data`.
    *   **Method: `has_changed(self)`**
        *   **Implementation Logic:** Returns `bool(self.changed_data)`.
    *   **Property: `changed_data`**
        *   **Implementation Logic:**
            *   If `self._changed_data` is `None`, initializes it to `[]`.
            *   Iterates over `self.fields.items()`.
            *   Gets `data_value` using `field.widget.value_from_datadict`.
            *   If `not field.show_hidden_initial`:
                *   Gets `initial_value` from `self.initial` or `field.initial`. If callable, calls it.
            *   Else:
                *   Gets `initial_value` by extracting data from the hidden widget using `initial_prefixed_name`.
                *   If a `ValidationError` occurs during `field.to_python`, appends the field name to `self._changed_data` and continues.
            *   If `field._has_changed(initial_value, data_value)` is true, appends the field name to `self._changed_data`.
            *   Returns `self._changed_data`.
    *   **Property: `media`**
        *   **Implementation Logic:** Initializes a `Media` object and adds the `media` of every field's widget to it. Returns the combined `Media`.
    *   **Method: `is_multipart(self)`**
        *   **Implementation Logic:** Returns `True` if any field's widget has `needs_multipart_form` set to true, else `False`.
    *   **Method: `hidden_fields(self)`**
        *   **Implementation Logic:** Returns a list of fields in `self` where `field.is_hidden` is true.
    *   **Method: `visible_fields(self)`**
        *   **Implementation Logic:** Returns a list of fields in `self` where `field.is_hidden` is false.

*   **Class: `Form`**
    *   **Inheritance:** `six.with_metaclass(DeclarativeFieldsMetaclass, BaseForm)`
    *   **Implementation Logic:** An empty class definition (just a docstring and comments) that combines `BaseForm` with the `DeclarativeFieldsMetaclass`.

*   **Class: `BoundField`**
    *   **Inheritance:** `object`
    *   **Decorators:** `@python_2_unicode_compatible`
    *   **Method: `__init__(self, form, field, name)`**
        *   **Implementation Logic:**
            *   Sets `self.form`, `self.field`, and `self.name`.
            *   Sets `self.html_name` using `form.add_prefix(name)`.
            *   Sets `self.html_initial_name` using `form.add_initial_prefix(name)`.
            *   Sets `self.html_initial_id` using `form.add_initial_prefix(self.auto_id)`.
            *   Sets `self.label` to `pretty_name(name)` if `field.label` is `None`, else `field.label`.
            *   Sets `self.help_text` to `field.help_text` or `''`.
    *   **Method: `__str__(self)`**
        *   **Implementation Logic:** If `self.field.show_hidden_initial` is true, returns `self.as_widget() + self.as_hidden(only_initial=True)`. Otherwise, returns `self.as_widget()`.
    *   **Method: `__iter__(self)`**
        *   **Implementation Logic:** Yields subwidgets from `self.field.widget.subwidgets(self.html_name, self.value(), attrs)`.
    *   **Method: `__len__(self)`**
        *   **Implementation Logic:** Returns the length of the list generated by `self.__iter__()`.
    *   **Method: `__getitem__(self, idx)`**
        *   **Implementation Logic:** Returns the item at `idx` from the list generated by `self.__iter__()`.
    *   **Property: `errors`**
        *   **Implementation Logic:** Returns `self.form.errors.get(self.name, self.form.error_class())`.
    *   **Method: `as_widget(self, widget=None, attrs=None, only_initial=False)`**
        *   **Implementation Logic:**
            *   Uses `self.field.widget` if `widget` is not provided.
            *   Sets `widget.is_localized = True` if `self.field.localize` is true.
            *   Merges `attrs` and handles `id` generation based on `self.auto_id` and `only_initial`.
            *   Calls and returns `widget.render(name, self.value(), attrs=attrs)`.
    *   **Method: `as_text(self, attrs=None, **kwargs)`**
        *   **Implementation Logic:** Returns `self.as_widget(TextInput(), attrs, **kwargs)`.
    *   **Method: `as_textarea(self, attrs=None, **kwargs)`**
        *   **Implementation Logic:** Returns `self.as_widget(Textarea(), attrs, **kwargs)`.
    *   **Method: `as_hidden(self, attrs=None, **kwargs)`**
        *   **Implementation Logic:** Returns `self.as_widget(self.field.hidden_widget(), attrs, **kwargs)`.
    *   **Property: `data`**
        *   **Implementation Logic:** Returns `self.field.widget.value_from_datadict(self.form.data, self.form.files, self.html_name)`.
    *   **Method: `value(self)`**
        *   **Implementation Logic:**
            *   If the form is not bound, gets the initial data. If callable, calls it. If it's a datetime/time object and the widget doesn't support microseconds, strips the microseconds.
            *   If bound, gets the data using `self.field.bound_data`.
            *   Returns `self.field.prepare_value(data)`.
    *   **Method: `label_tag(self, contents=None, attrs=None, label_suffix=None)`**
        *   **Implementation Logic:**
            *   Determines the contents and label suffix. Appends the suffix if the contents don't end with punctuation (`:?.!`).
            *   If the widget has an ID, generates a `<label>` tag with a `for` attribute pointing to the widget's ID. Adds the form's `required_css_class` if the field is required.
            *   If no ID, just conditionally escapes the contents.
            *   Returns the result wrapped in `mark_safe`.
    *   **Method: `css_classes(self, extra_classes=None)`**
        *   **Implementation Logic:**
            *   Splits `extra_classes` if it's a string, converts to a set.
            *   Adds the form's `error_css_class` if the field has errors.
            *   Adds the form's `required_css_class` if the field is required.
            *   Returns a space-separated string of the classes.
    *   **Property: `is_hidden`**
        *   **Implementation Logic:** Returns `self.field.widget.is_hidden`.
    *   **Property: `auto_id`**
        *   **Implementation Logic:** Calculates the ID attribute based on `self.form.auto_id` and `self.html_name`.
    *   **Property: `id_for_label`**
        *   **Implementation Logic:** Returns `widget.id_for_label(id_)` using the widget's ID or `self.auto_id`.

## django/forms/utils.py
### 1. Module-Level Preamble

**Imports:**
*   `from __future__ import unicode_literals`
*   `import json`
*   `import sys`
*   `from collections import UserList` (wrapped in a `try` block, with an `except ImportError:` fallback to `from UserList import UserList` for Python 2 compatibility)
*   `from django.conf import settings`
*   `from django.utils.encoding import force_text, python_2_unicode_compatible`
*   `from django.utils.html import format_html, format_html_join, escape`
*   `from django.utils import timezone`
*   `from django.utils.translation import ugettext_lazy as _`
*   `from django.utils import six`
*   `from django.core.exceptions import ValidationError`

**Constants & Globals:**
*   None defined at the module level.

---

### 2. Code Objects

#### `flatatt(attrs)`
*   **Signature:** `def flatatt(attrs):`
*   **Implementation Logic:**
    *   Initializes an empty list `boolean_attrs`.
    *   Iterates over a list of the items in the `attrs` dictionary (`list(attrs.items())`).
    *   For each `attr` and `value`:
        *   If `value is True`, appends a tuple `(attr,)` to `boolean_attrs` and deletes the key `attr` from `attrs`.
        *   If `value is False`, deletes the key `attr` from `attrs`.
    *   Returns a concatenated string of two `format_html_join` calls:
        1.  Joins `sorted(attrs.items())` using the format string `' {0}="{1}"'` and an empty string separator.
        2.  Joins `sorted(boolean_attrs)` using the format string `' {0}'` and an empty string separator.

#### `ErrorDict`
*   **Header:** `@python_2_unicode_compatible` decorated class `ErrorDict(dict)`.
*   **Implementation Logic:**
    *   **`as_data(self)`**: Returns a dictionary comprehension mapping each field `f` to `e.as_data()` for `f, e` in `self.items()`.
    *   **`as_json(self, escape_html=False)`**: Returns a JSON string (using `json.dumps`) of a dictionary comprehension mapping each field `f` to `e.get_json_data(escape_html)` for `f, e` in `self.items()`.
    *   **`as_ul(self)`**:
        *   If the dictionary is empty (`not self`), returns an empty string `''`.
        *   Otherwise, returns an HTML unordered list string using `format_html('<ul class="errorlist">{0}</ul>', ...)`. The inner content is generated by `format_html_join('', '<li>{0}{1}</li>', ((k, force_text(v)) for k, v in self.items()))`.
    *   **`as_text(self)`**:
        *   Initializes an empty list `output`.
        *   Iterates over `self.items()` (field, errors).
        *   Appends `'* %s' % field` to `output`.
        *   Appends a newline-joined string of `'  * %s' % e` for each `e` in `errors`.
        *   Returns `output` joined by newlines (`'\n'.join(output)`).
    *   **`__str__(self)`**: Returns `self.as_ul()`.

#### `ErrorList`
*   **Header:** `@python_2_unicode_compatible` decorated class `ErrorList(UserList, list)`.
*   **Implementation Logic:**
    *   **`as_data(self)`**: Returns `ValidationError(self.data).error_list`.
    *   **`get_json_data(self, escape_html=False)`**:
        *   Initializes an empty list `errors`.
        *   Iterates over `self.as_data()`. For each `error`:
            *   Extracts the message as `list(error)[0]`.
            *   Appends a dictionary to `errors` with keys:
                *   `'message'`: `escape(message)` if `escape_html` is True, else `message`.
                *   `'code'`: `error.code or ''`.
        *   Returns the `errors` list.
    *   **`as_json(self, escape_html=False)`**: Returns `json.dumps(self.get_json_data(escape_html))`.
    *   **`as_ul(self)`**:
        *   If `not self.data`, returns an empty string `''`.
        *   Otherwise, returns an HTML unordered list string using `format_html('<ul class="errorlist">{0}</ul>', ...)`. The inner content is generated by `format_html_join('', '<li>{0}</li>', ((force_text(e),) for e in self))`.
    *   **`as_text(self)`**: Returns a newline-joined string of `'* %s' % e` for each `e` in `self`.
    *   **`__str__(self)`**: Returns `self.as_ul()`.
    *   **`__repr__(self)`**: Returns `repr(list(self))`.
    *   **`__contains__(self, item)`**: Returns `item in list(self)`.
    *   **`__eq__(self, other)`**: Returns `list(self) == other`.
    *   **`__ne__(self, other)`**: Returns `list(self) != other`.
    *   **`__getitem__(self, i)`**:
        *   Retrieves `error = self.data[i]`.
        *   If `error` is an instance of `ValidationError`, returns `list(error)[0]`.
        *   Otherwise, returns `force_text(error)`.

#### `from_current_timezone(value)`
*   **Signature:** `def from_current_timezone(value):`
*   **Implementation Logic:**
    *   Checks if `settings.USE_TZ` is True, `value` is not `None`, and `timezone.is_naive(value)` is True.
    *   If all conditions are met:
        *   Gets the current timezone using `timezone.get_current_timezone()`.
        *   Tries to return `timezone.make_aware(value, current_timezone)`.
        *   If an `Exception` is caught:
            *   Constructs an error message (using `_`) indicating the datetime couldn't be interpreted in the timezone (ambiguous or non-existent).
            *   Constructs a `params` dictionary with `'datetime': value` and `'current_timezone': current_timezone`.
            *   Uses `six.reraise` to raise a `ValidationError` with the message, `code='ambiguous_timezone'`, and `params=params`, preserving the original traceback (`sys.exc_info()[2]`).
    *   If the conditions are not met, returns `value` unchanged.

#### `to_current_timezone(value)`
*   **Signature:** `def to_current_timezone(value):`
*   **Implementation Logic:**
    *   Checks if `settings.USE_TZ` is True, `value` is not `None`, and `timezone.is_aware(value)` is True.
    *   If all conditions are met:
        *   Gets the current timezone using `timezone.get_current_timezone()`.
        *   Returns `timezone.make_naive(value, current_timezone)`.
    *   If the conditions are not met, returns `value` unchanged.