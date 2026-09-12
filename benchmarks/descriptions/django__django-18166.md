## django/forms/formsets.py
```markdown
# Specification for `django/forms/formsets.py`

## 1. Module-Level Preamble

### Imports
```python
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.forms import Form
from django.forms.fields import BooleanField, IntegerField
from django.forms.utils import ErrorList
from django.forms.widgets import HiddenInput
from django.utils import six
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.html import html_safe
from django.utils.safestring import mark_safe
from django.utils.six.moves import range
from django.utils.translation import ugettext as _, ungettext
```

### Constants & Globals
*   `__all__ = ('BaseFormSet', 'formset_factory', 'all_valid')`
*   `TOTAL_FORM_COUNT = 'TOTAL_FORMS'`
*   `INITIAL_FORM_COUNT = 'INITIAL_FORMS'`
*   `MIN_NUM_FORM_COUNT = 'MIN_NUM_FORMS'`
*   `MAX_NUM_FORM_COUNT = 'MAX_NUM_FORMS'`
*   `ORDERING_FIELD_NAME = 'ORDER'`
*   `DELETION_FIELD_NAME = 'DELETE'`
*   `DEFAULT_MIN_NUM = 0`
*   `DEFAULT_MAX_NUM = 1000`

---

## 2. Code Objects

### `ManagementForm(Form)`
A form used to keep track of how many form instances are displayed on the page.

*   **`__init__(self, *args, **kwargs)`**
    *   **Logic:**
        *   Adds `TOTAL_FORM_COUNT` to `self.base_fields` as an `IntegerField` with `widget=HiddenInput`.
        *   Adds `INITIAL_FORM_COUNT` to `self.base_fields` as an `IntegerField` with `widget=HiddenInput`.
        *   Adds `MIN_NUM_FORM_COUNT` to `self.base_fields` as an `IntegerField` with `required=False` and `widget=HiddenInput`.
        *   Adds `MAX_NUM_FORM_COUNT` to `self.base_fields` as an `IntegerField` with `required=False` and `widget=HiddenInput`.
        *   Calls `super(ManagementForm, self).__init__(*args, **kwargs)`.

### `BaseFormSet(object)`
A collection of instances of the same Form class.
*   **Decorators:** `@html_safe`, `@python_2_unicode_compatible`

*   **`__init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList)`**
    *   **Logic:**
        *   Sets `self.is_bound` to `True` if `data is not None or files is not None`, else `False`.
        *   Sets `self.prefix` to `prefix` if provided, else `self.get_default_prefix()`.
        *   Sets `self.auto_id` to `auto_id`.
        *   Sets `self.data` to `data` or `{}`.
        *   Sets `self.files` to `files` or `{}`.
        *   Sets `self.initial` to `initial`.
        *   Sets `self.error_class` to `error_class`.
        *   Sets `self._errors` and `self._non_form_errors` to `None`.

*   **`__str__(self)`**
    *   **Logic:** Returns `self.as_table()`.

*   **`__iter__(self)`**
    *   **Logic:** Returns `iter(self.forms)`.

*   **`__getitem__(self, index)`**
    *   **Logic:** Returns `self.forms[index]`.

*   **`__len__(self)`**
    *   **Logic:** Returns `len(self.forms)`.

*   **`__bool__(self)`**
    *   **Logic:** Returns `True`.

*   **`__nonzero__(self)`**
    *   **Logic:** Returns `type(self).__bool__(self)`.

*   **`@property management_form(self)`**
    *   **Logic:**
        *   If `self.is_bound`: Instantiates `ManagementForm(self.data, auto_id=self.auto_id, prefix=self.prefix)`. If it is not valid, raises a `ValidationError` with the message `_('ManagementForm data is missing or has been tampered with')` and `code='missing_management_form'`.
        *   If not bound: Instantiates `ManagementForm` with `auto_id=self.auto_id`, `prefix=self.prefix`, and `initial` data containing `TOTAL_FORM_COUNT: self.total_form_count()`, `INITIAL_FORM_COUNT: self.initial_form_count()`, `MIN_NUM_FORM_COUNT: self.min_num`, and `MAX_NUM_FORM_COUNT: self.max_num`.
        *   Returns the instantiated form.

*   **`total_form_count(self)`**
    *   **Logic:**
        *   If `self.is_bound`: Returns the minimum of `self.management_form.cleaned_data[TOTAL_FORM_COUNT]` and `self.absolute_max`.
        *   If not bound: Calculates `initial_forms = self.initial_form_count()`. Sets `total_forms = max(initial_forms, self.min_num) + self.extra`.
            *   If `initial_forms > self.max_num >= 0`, sets `total_forms = initial_forms`.
            *   Else if `total_forms > self.max_num >= 0`, sets `total_forms = self.max_num`.
            *   Returns `total_forms`.

*   **`initial_form_count(self)`**
    *   **Logic:**
        *   If `self.is_bound`: Returns `self.management_form.cleaned_data[INITIAL_FORM_COUNT]`.
        *   If not bound: Returns `len(self.initial)` if `self.initial` is truthy, else `0`.

*   **`@cached_property forms(self)`**
    *   **Logic:** Returns a list comprehension `[self._construct_form(i) for i in range(self.total_form_count())]`.

*   **`_construct_form(self, i, **kwargs)`**
    *   **Logic:**
        *   Initializes `defaults = {'auto_id': self.auto_id, 'prefix': self.add_prefix(i), 'error_class': self.error_class}`.
        *   If `self.is_bound`, adds `data=self.data` and `files=self.files` to `defaults`.
        *   If `self.initial` and `'initial' not in kwargs`, attempts to set `defaults['initial'] = self.initial[i]`, catching and ignoring `IndexError`.
        *   If `i >= self.initial_form_count()` and `i >= self.min_num`, sets `defaults['empty_permitted'] = True`.
        *   Updates `defaults` with `kwargs`.
        *   Instantiates `form = self.form(**defaults)`.
        *   Calls `self.add_fields(form, i)`.
        *   Returns `form`.

*   **`@property initial_forms(self)`**
    *   **Logic:** Returns `self.forms[:self.initial_form_count()]`.

*   **`@property extra_forms(self)`**
    *   **Logic:** Returns `self.forms[self.initial_form_count():]`.

*   **`@property empty_form(self)`**
    *   **Logic:**
        *   Instantiates `form = self.form(auto_id=self.auto_id, prefix=self.add_prefix('__prefix__'), empty_permitted=True)`.
        *   Calls `self.add_fields(form, None)`.
        *   Returns `form`.

*   **`@property cleaned_data(self)`**
    *   **Logic:**
        *   If `not self.is_valid()`, raises `AttributeError("'%s' object has no attribute 'cleaned_data'" % self.__class__.__name__)`.
        *   Returns `[form.cleaned_data for form in self.forms]`.

*   **`@property deleted_forms(self)`**
    *   **Logic:**
        *   If `not self.is_valid()` or `not self.can_delete`, returns `[]`.
        *   If `not hasattr(self, '_deleted_form_indexes')`:
            *   Initializes `self._deleted_form_indexes = []`.
            *   Iterates `i` from `0` to `self.total_form_count()`.
            *   For each `form = self.forms[i]`, if `i >= self.initial_form_count()` and `not form.has_changed()`, continues.
            *   If `self._should_delete_form(form)` is true, appends `i` to `self._deleted_form_indexes`.
        *   Returns `[self.forms[i] for i in self._deleted_form_indexes]`.

*   **`@property ordered_forms(self)`**
    *   **Logic:**
        *   If `not self.is_valid()` or `not self.can_order`, raises `AttributeError("'%s' object has no attribute 'ordered_forms'" % self.__class__.__name__)`.
        *   If `not hasattr(self, '_ordering')`:
            *   Initializes `self._ordering = []`.
            *   Iterates `i` from `0` to `self.total_form_count()`.
            *   For each `form = self.forms[i]`, if `i >= self.initial_form_count()` and `not form.has_changed()`, continues.
            *   If `self.can_delete` and `self._should_delete_form(form)`, continues.
            *   Appends `(i, form.cleaned_data[ORDERING_FIELD_NAME])` to `self._ordering`.
            *   Sorts `self._ordering` using a key function that returns `(1, 0)` if the ordering value is `None`, else `(0, value)`.
        *   Returns `[self.forms[i[0]] for i in self._ordering]`.

*   **`@classmethod get_default_prefix(cls)`**
    *   **Logic:** Returns `'form'`.

*   **`non_form_errors(self)`**
    *   **Logic:**
        *   If `self._non_form_errors is None`, calls `self.full_clean()`.
        *   Returns `self._non_form_errors`.

*   **`@property errors(self)`**
    *   **Logic:**
        *   If `self._errors is None`, calls `self.full_clean()`.
        *   Returns `self._errors`.

*   **`total_error_count(self)`**
    *   **Logic:** Returns `len(self.non_form_errors()) + sum(len(form_errors) for form_errors in self.errors)`.

*   **`_should_delete_form(self, form)`**
    *   **Logic:** Returns `form.cleaned_data.get(DELETION_FIELD_NAME, False)`.

*   **`is_valid(self)`**
    *   **Logic:**
        *   If `not self.is_bound`, returns `False`.
        *   Sets `forms_valid = True`.
        *   Accesses `self.errors` to trigger a full clean.
        *   Iterates `i` from `0` to `self.total_form_count()`.
        *   For each `form = self.forms[i]`, if `self.can_delete` and `self._should_delete_form(form)`, continues.
        *   Updates `forms_valid &= form.is_valid()`.
        *   Returns `forms_valid and not self.non_form_errors()`.

*   **`full_clean(self)`**
    *   **Logic:**
        *   Sets `self._errors = []` and `self._non_form_errors = self.error_class()`.
        *   If `not self.is_bound`, returns immediately.
        *   Iterates `i` from `0` to `self.total_form_count()`, appending `self.forms[i].errors` to `self._errors`.
        *   In a `try` block:
            *   If `(self.validate_max and self.total_form_count() - len(self.deleted_forms) > self.max_num)` or `self.management_form.cleaned_data[TOTAL_FORM_COUNT] > self.absolute_max`, raises `ValidationError` with `ungettext("Please submit %d or fewer forms.", "Please submit %d or fewer forms.", self.max_num) % self.max_num` and `code='too_many_forms'`.
            *   If `(self.validate_min and self.total_form_count() - len(self.deleted_forms) < self.min_num)`, raises `ValidationError` with `ungettext("Please submit %d or more forms.", "Please submit %d or more forms.", self.min_num) % self.min_num` and `code='too_few_forms'`.
            *   Calls `self.clean()`.
        *   Catches `ValidationError as e` and sets `self._non_form_errors = self.error_class(e.error_list)`.

*   **`clean(self)`**
    *   **Logic:** A no-op hook (`pass`).

*   **`has_changed(self)`**
    *   **Logic:** Returns `any(form.has_changed() for form in self)`.

*   **`add_fields(self, form, index)`**
    *   **Logic:**
        *   If `self.can_order`: If `index is not None and index < self.initial_form_count()`, sets `form.fields[ORDERING_FIELD_NAME] = IntegerField(label=_('Order'), initial=index + 1, required=False)`. Else, sets `form.fields[ORDERING_FIELD_NAME] = IntegerField(label=_('Order'), required=False)`.
        *   If `self.can_delete`: Sets `form.fields[DELETION_FIELD_NAME] = BooleanField(label=_('Delete'), required=False)`.

*   **`add_prefix(self, index)`**
    *   **Logic:** Returns `'%s-%s' % (self.prefix, index)`.

*   **`is_multipart(self)`**
    *   **Logic:** Returns `self.forms[0].is_multipart()` if `self.forms` is not empty, else `self.empty_form.is_multipart()`.

*   **`@property media(self)`**
    *   **Logic:** Returns `self.forms[0].media` if `self.forms` is not empty, else `self.empty_form.media`.

*   **`as_table(self)`**
    *   **Logic:** Joins `form.as_table()` for each form with a space. Returns `mark_safe('\n'.join([six.text_type(self.management_form), forms]))`.

*   **`as_p(self)`**
    *   **Logic:** Joins `form.as_p()` for each form with a space. Returns `mark_safe('\n'.join([six.text_type(self.management_form), forms]))`.

*   **`as_ul(self)`**
    *   **Logic:** Joins `form.as_ul()` for each form with a space. Returns `mark_safe('\n'.join([six.text_type(self.management_form), forms]))`.

### `formset_factory`
*   **Signature:** `def formset_factory(form, formset=BaseFormSet, extra=1, can_order=False, can_delete=False, max_num=None, validate_max=False, min_num=None, validate_min=False)`
*   **Logic:**
    *   If `min_num is None`, sets `min_num = DEFAULT_MIN_NUM`.
    *   If `max_num is None`, sets `max_num = DEFAULT_MAX_NUM`.
    *   Sets `absolute_max = max_num + DEFAULT_MAX_NUM`.
    *   Creates a dictionary `attrs` containing `'form': form`, `'extra': extra`, `'can_order': can_order`, `'can_delete': can_delete`, `'min_num': min_num`, `'max_num': max_num`, `'absolute_max': absolute_max`, `'validate_min': validate_min`, and `'validate_max': validate_max`.
    *   Returns a new class created via `type(form.__name__ + str('FormSet'), (formset,), attrs)`.

### `all_valid`
*   **Signature:** `def all_valid(formsets)`
*   **Logic:**
    *   Initializes `valid = True`.
    *   Iterates over `formsets`. If `not formset.is_valid()`, sets `valid = False`.
    *   Returns `valid`.
```