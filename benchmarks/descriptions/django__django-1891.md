## django/forms/models.py
1. **Module-Level Preamble:**
    *   **Imports:**
        *   `import warnings`
        *   `from itertools import chain`
        *   `from django.core.exceptions import NON_FIELD_ERRORS, FieldError, ImproperlyConfigured, ValidationError`
        *   `from django.forms.fields import ChoiceField, Field`
        *   `from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass`
        *   `from django.forms.formsets import BaseFormSet, formset_factory`
        *   `from django.forms.utils import ErrorList`
        *   `from django.forms.widgets import HiddenInput, MultipleHiddenInput, RadioSelect, SelectMultiple`
        *   `from django.utils.deprecation import RemovedInDjango40Warning`
        *   `from django.utils.text import capfirst, get_text_list`
        *   `from django.utils.translation import gettext, gettext_lazy as _`
    *   **Constants & Globals:**
        *   `__all__ = ('ModelForm', 'BaseModelForm', 'model_to_dict', 'fields_for_model', 'ModelChoiceField', 'ModelMultipleChoiceField', 'ALL_FIELDS', 'BaseModelFormSet', 'modelformset_factory', 'BaseInlineFormSet', 'inlineformset_factory', 'modelform_factory')`
        *   `ALL_FIELDS = '__all__'`

2. **Code Objects (Classes and Functions):**

*   **Function:** `def construct_instance(form, instance, fields=None, exclude=None):`
    *   **Implementation Logic:** Updates the model `instance` with cleaned data from the `form`. Iterates over the form's cleaned data, skipping fields not in `fields` or in `exclude`. Sets the corresponding attribute on the instance. Returns the updated `instance`.

*   **Function:** `def model_to_dict(instance, fields=None, exclude=None):`
    *   **Implementation Logic:** Converts a model `instance` into a dictionary. Iterates over the model's fields, filtering by `fields` and `exclude`. Extracts the value for each field using `field.value_from_object(instance)`. Returns the resulting dictionary.

*   **Function:** `def apply_limit_choices_to_to_formfield(formfield):`
    *   **Implementation Logic:** Applies the `limit_choices_to` attribute of a model field to the corresponding form field's queryset, if applicable.

*   **Function:** `def fields_for_model(model, fields=None, exclude=None, widgets=None, formfield_callback=None, localized_fields=None, labels=None, help_texts=None