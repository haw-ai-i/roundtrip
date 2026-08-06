# Implementation target
Write the module at `django/forms/models.py`.

## `django/forms/models.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ALL_FIELDS`
- `BaseInlineFormSet`
- `BaseModelForm`
- `BaseModelFormSet`
- `InlineForeignKeyField`
- `ModelChoiceField`
- `ModelChoiceIterator`
- `ModelChoiceIteratorValue`
- `ModelForm`
- `ModelFormMetaclass`
- `ModelFormOptions`
- `ModelMultipleChoiceField`
- `_get_foreign_key`
- `apply_limit_choices_to_to_formfield`
- `construct_instance`
- `fields_for_model`
- `inlineformset_factory`
- `model_to_dict`
- `modelform_defines_fields`
- `modelform_factory`
- `modelformset_factory`

Implement them to satisfy the specification. Do not write tests.
