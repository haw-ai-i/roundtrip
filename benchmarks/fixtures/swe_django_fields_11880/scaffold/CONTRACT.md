# Implementation target
Write the module at `django/forms/fields.py`.

## `django/forms/fields.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseTemporalField`
- `BooleanField`
- `CallableChoiceIterator`
- `CharField`
- `ChoiceField`
- `ComboField`
- `DateField`
- `DateTimeField`
- `DecimalField`
- `DurationField`
- `EmailField`
- `Field`
- `FileField`
- `FilePathField`
- `FloatField`
- `GenericIPAddressField`
- `ImageField`
- `IntegerField`
- `MultiValueField`
- `MultipleChoiceField`
- `NullBooleanField`
- `RegexField`
- `SlugField`
- `SplitDateTimeField`
- `TimeField`
- `TypedChoiceField`
- `TypedMultipleChoiceField`
- `URLField`
- `UUIDField`

Implement them to satisfy the specification. Do not write tests.
