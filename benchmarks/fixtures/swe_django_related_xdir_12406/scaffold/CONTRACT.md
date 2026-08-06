# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/db/models/fields/related.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ForeignKey`
- `ForeignObject`
- `ManyToManyField`
- `OneToOneField`
- `RECURSIVE_RELATIONSHIP_CONSTANT`
- `RelatedField`
- `create_many_to_many_intermediary_model`
- `lazy_related_operation`
- `resolve_relation`

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
