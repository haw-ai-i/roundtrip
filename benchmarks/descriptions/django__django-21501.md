## django/forms/formsets.py
1.  **Module-Level Preamble:**
    *   **Imports:**
        *   `from __future__ import unicode_literals`
        *   `from django.core.exceptions import ValidationError`
        *   `from django.forms import Form`
        *   `from django.forms.fields import BooleanField, IntegerField`
        *   `from django.forms.utils import ErrorList`
        *   `from django.forms.widgets import HiddenInput`
        *   `from django.utils import six`
        *   `from django.utils.encoding import python_2_unicode_compatible`
        *   `from django.utils.functional import cached_property`
        *   `from django.utils.html import html_safe`
        *   `from django.utils.safestring import mark_safe`
        *   `from django.utils.six.moves import range`
        *   `from django.utils.translation import ugettext as _, ungettext`
    *   **Constants & Globals:**
        *   `__all__ = ('BaseFormSet', 'formset_factory', 'all_valid')`
        *   `TOTAL_FORM_COUNT = 'TOTAL_FORMS'`
        *   `INITIAL_FORM_COUNT = 'INITIAL_FORMS'`
        *   `MIN_NUM_FORM_COUNT = 'MIN_NUM_FORMS'`
        *   `MAX_NUM_FORM_COUNT = 'MAX_NUM_FORMS'`
        *   `ORDERING_FIELD_NAME = 'ORDER'`
        *   `DELETION_FIELD_NAME = 'DELETE'`
        *   `DEFAULT_MIN_NUM = 0`
        *   `DEFAULT_MAX_NUM = 1000`

2.  **Code Objects (Classes and Functions):**

    *   **Class `ManagementForm`:**
        *   **Base Classes:** `Form`
        *   **Method `__init__(self, *args, **kwargs)`:**
            *   Adds `TOTAL_FORM_COUNT` and `INITIAL_FORM_COUNT` to `self.base_fields` as `IntegerField` with `widget=HiddenInput`.
            *   Adds `MIN_NUM_FORM_COUNT` and `MAX_NUM_FORM_COUNT` to `self.base_fields` as `IntegerField` with `required=False` and `widget=HiddenInput`.
            *   Calls `super(ManagementForm, self).__init__(*args, **kwargs)`.

    *   **Class `BaseFormSet`:**
        *   **Decorators:** `@html_safe`, `@python_2_unicode_compatible`
        *   **Base Classes:** `object`
        *   **Method `__init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList)`:**
            *   Sets `self.is_bound` to `True` if `data` or `files` is not `None`, else `False`.
            *   Sets `self.prefix` to `prefix` or `self.get_default_prefix()`.
            *   Sets `self.auto_id` to `auto_id`.
            *   Sets `self.data` to `data` or `{}`.
            *   Sets `self.files` to `files` or `{}`.
            *   Sets `self.initial` to `initial`.
            *   Sets `self.error_class` to `error_class`.
            *   Sets `self._errors` and `self._non_form_errors` to `None`.
        *   **Method `__str__(self)`:** Returns `self.as_table()`.
        *   **Method `__iter__(self)`:** Returns `iter(self.forms)`.
        *   **Method `__getitem__(self, index)`:** Returns `self.forms[index]`.
        *   **Method `__len__(self)`:** Returns `len(self.forms)`.
        *   **Method `__bool__(self)`:** Returns `True`.
        *   **Method `__nonzero__(self)`:** Returns `type(self).__bool__(self)`.
        *   **Property `management_form`:**
            *   If `self.is_bound`, instantiates `ManagementForm` with `self.data`, `auto_id=self.auto_id`, `prefix=self.prefix`. If it's not valid, raises `ValidationError` with message `_('ManagementForm data is missing or has been tampered with')` and code `'missing_management_form'`.
            *   If not bound, instantiates `ManagementForm` with `auto_id=self.auto_id`, `prefix=self.prefix`, and `initial` dict containing `TOTAL_FORM_COUNT: self.total_form_count()`, `INITIAL_FORM_COUNT: self.initial_form_count()`, `MIN_NUM_FORM_COUNT: self.min_num`, `MAX_NUM_FORM_COUNT: self.max_num`.
            *   Returns the form.
        *   **Method `total_form_count(self)`:**
            *   If `self.is_bound`, returns the minimum of `self.management_form.cleaned_data[TOTAL_FORM_COUNT]` and `self.absolute_max`.
            *   If not bound, calculates `initial_forms = self.initial_form_count()`. `total_forms = max(initial_forms, self.min_num) + self.extra`.
            *   If `initial_forms > self.max_num >= 0`, sets `total_forms = initial_forms`.
            *   Else if `total_forms > self.max_num >= 0`, sets `total_forms = self.max_num`.
            *   Returns `total_forms`.
        *   **Method `initial_form_count(self)`:**
            *   If `self.is_bound`, returns `self.management_form.cleaned_data[INITIAL_FORM_COUNT]`.
            *   If not bound, returns `len(self.initial)` if `self.initial` is truthy, else `0`.
        *   **Property `forms` (decorated with `@cached_property`):**
            *   Returns a list of forms created by calling `self._construct_form(i)` for `i` in `range(self.total_form_count())`.
        *   **Method `_construct_form(self, i, **kwargs)`:**
            *   Creates `defaults` dict with `auto_id=self.auto_id`, `prefix=self.add_prefix(i)`, `error_class=self.error_class`.
            *   If `self.is_bound`, adds `data=self.data` and `files=self.files` to `defaults`.
            *   If `self.initial` and `'initial'` not in `kwargs`, tries to add `initial=self.initial[i]` to `defaults`, ignoring `IndexError`.
            *   If `i >= self.initial_form_count()` and `i >= self.min_num`, sets `empty_permitted=True` in `defaults`.
            *   Updates `defaults` with `kwargs`.
            *   Instantiates `form = self.form(**defaults)`.
            *   Calls `self.add_fields(form, i)`.
            *   Returns `form`.
        *   **Property `initial_forms`:** Returns `self.forms[:self.initial_form_count()]`.
        *   **Property `extra_forms`:** Returns `self.forms[self.initial_form_count():]`.
        *   **Property `empty_form`:**
            *   Instantiates `form = self.form(auto_id=self.auto_id, prefix=self.add_prefix('__prefix__'), empty_permitted=True)`.
            *   Calls `self.add_fields(form, None)`.
            *   Returns `form`.
        *   **Property `cleaned_data`:**
            *   If `not self.is_valid()`, raises `AttributeError` with message `"'%s' object has no attribute 'cleaned_data'" % self.__class__.__name__`.
            *   Returns a list of `form.cleaned_data` for each `form` in `self.forms`.
        *   **Property `deleted_forms`:**
            *   If `not self.is_valid()` or `not self.can_delete`, returns `[]`.
            *   If `not hasattr(self, '_deleted_form_indexes')`, initializes it to `[]`. Iterates `i` from `0` to `self.total_form_count()`. For each `form = self.forms[i]`, if `i >= self.initial_form_count()` and `not form.has_changed()`, continues. If `self._should_delete_form(form)` is true, appends `i` to `self._deleted_form_indexes`.
            *   Returns a list of `self.forms[i]` for `i` in `self._deleted_form_indexes`.
        *   **Property `ordered_forms`:**
            *   If `not self.is_valid()` or `not self.can_order`, raises `AttributeError` with message `"'%s' object has no attribute 'ordered_forms'" % self.__class__.__name__`.
            *   If `not hasattr(self, '_ordering')`, initializes it to `[]`. Iterates `i` from `0` to `self.total_form_count()`. For each `form = self.forms[i]`, if `i >= self.initial_form_count()` and `not form.has_changed()`, continues. If `self.can_delete` and `self._should_delete_form(form)`, continues. Appends `(i, form.cleaned_data[ORDERING_FIELD_NAME])` to `self._ordering`.
            *   Sorts `self._ordering` using a key function that returns `(1, 0)` if the second element is `None`, else `(0, k[1])`.
            *   Returns a list of `self.forms[i[0]]` for `i` in `self._ordering`.
        *   **Class Method `get_default_prefix(cls)`:** Returns `'form'`.
        *   **Method `non_form_errors(self)`:**
            *   If `self._non_form_errors` is `None`, calls `self.full_clean()`.
            *   Returns `self._non_form_errors`.
        *   **Property `errors`:**
            *   If `self._errors` is `None`, calls `self.full_clean()`.
            *   Returns `self._errors`.
        *   **Method `total_error_count(self)`:** Returns `len(self.non_form_errors()) + sum(len(form_errors) for form_errors in self.errors)`.
        *   **Method `_should_delete_form(self, form)`:** Returns `form.cleaned_data.get(DELETION_FIELD_NAME, False)`.
        *   **Method `is_valid(self)`:**
            *   If `not self.is_bound`, returns `False`.
            *   Initializes `forms_valid = True`.
            *   Accesses `self.errors` to trigger full clean.
            *   Iterates `i` from `0` to `self.total_form_count()`. For each `form = self.forms[i]`, if `self.can_delete` and `self._should_delete_form(form)`, continues. Updates `forms_valid &= form.is_valid()`.
            *   Returns `forms_valid and not self.non_form_errors()`.
        *   **Method `full_clean(self)`:**
            *   Sets `self._errors = []` and `self._non_form_errors = self.error_class()`.
            *   If `not self.is_bound`, returns.
            *   Iterates `i` from `0` to `self.total_form_count()`. Appends `self.forms[i].errors` to `self._errors`.
            *   In a `try` block:
                *   If `self.validate_max` and `self.total_form_count() - len(self.deleted_forms) > self.max_num`, or `self.management_form.cleaned_data[TOTAL_FORM_COUNT] > self.absolute_max`, raises `ValidationError` with ungettext message `"Please submit %d or fewer forms."` formatted with `self.max_num`, and code `'too_many_forms'`.
                *   If `self.validate_min` and `self.total_form_count() - len(self.deleted_forms) < self.min_num`, raises `ValidationError` with ungettext message `"Please submit %d or more forms."` formatted with `self.min_num`, and code `'too_few_forms'`.
                *   Calls `self.clean()`.
            *   Catches `ValidationError` as `e` and sets `self._non_form_errors = self.error_class(e.error_list)`.
        *   **Method `clean(self)`:** Passes (does nothing).
        *   **Method `has_changed(self)`:** Returns `any(form.has_changed() for form in self)`.
        *   **Method `add_fields(self, form, index)`:**
            *   If `self.can_order`: if `index` is not `None` and `index < self.initial_form_count()`, adds `ORDERING_FIELD_NAME` to `form.fields` as `IntegerField` with `label=_('Order')`, `initial=index + 1`, `required=False`. Else, adds it without `initial`.
            *   If `self.can_delete`: adds `DELETION_FIELD_NAME` to `form.fields` as `BooleanField` with `label=_('Delete')`, `required=False`.
        *   **Method `add_prefix(self, index)`:** Returns `'%s-%s' % (self.prefix, index)`.
        *   **Method `is_multipart(self)`:** Returns `self.forms[0].is_multipart()` if `self.forms` is truthy, else `self.empty_form.is_multipart()`.
        *   **Property `media`:** Returns `self.forms[0].media` if `self.forms` is truthy, else `self.empty_form.media`.
        *   **Method `as_table(self)`:** Returns `mark_safe('\n'.join([six.text_type(self.management_form), ' '.join(form.as_table() for form in self)]))`.
        *   **Method `as_p(self)`:** Returns `mark_safe('\n'.join([six.text_type(self.management_form), ' '.join(form.as_p() for form in self)]))`.
        *   **Method `as_ul(self)`:** Returns `mark_safe('\n'.join([six.text_type(self.management_form), ' '.join(form.as_ul() for form in self)]))`.

    *   **Function `formset_factory(form, formset=BaseFormSet, extra=1, can_order=False, can_delete=False, max_num=None, validate_max=False, min_num=None, validate_min=False)`:**
        *   If `min_num` is `None`, sets it to `DEFAULT_MIN_NUM`.
        *   If `max_num` is `None`, sets it to `DEFAULT_MAX_NUM`.
        *   Calculates `absolute_max = max_num + DEFAULT_MAX_NUM`.
        *   Creates `attrs` dict with keys `'form'`, `'extra'`, `'can_order'`, `'can_delete'`, `'min_num'`, `'max_num'`, `'absolute_max'`, `'validate_min'`, `'validate_max'` mapped to their respective arguments/variables.
        *   Returns a new class created with `type(form.__name__ + str('FormSet'), (formset,), attrs)`.

    *   **Function `all_valid(formsets)`:**
        *   Initializes `valid = True`.
        *   Iterates over `formsets`. If `not formset.is_valid()`, sets `valid = False`.
        *   Returns `valid`.