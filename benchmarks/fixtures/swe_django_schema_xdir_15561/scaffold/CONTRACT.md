# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/db/backends/base/schema.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseDatabaseSchemaEditor`
- `_related_non_m2m_objects`
- `logger`

## `django/db/models/fields/__init__.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AutoField`
- `AutoFieldMeta`
- `AutoFieldMixin`
- `BLANK_CHOICE_DASH`
- `BigAutoField`
- `BigIntegerField`
- `BinaryField`
- `BooleanField`
- `CharField`
- `CommaSeparatedIntegerField`
- `DateField`
- `DateTimeCheckMixin`
- `DateTimeField`
- `DecimalField`
- `DurationField`
- `EmailField`
- `Empty`
- `Field`
- `FilePathField`
- `FloatField`
- `GenericIPAddressField`
- `IPAddressField`
- `IntegerField`
- `NOT_PROVIDED`
- `NullBooleanField`
- `PositiveBigIntegerField`
- `PositiveIntegerField`
- `PositiveIntegerRelDbTypeMixin`
- `PositiveSmallIntegerField`
- `SlugField`
- `SmallAutoField`
- `SmallIntegerField`
- `TextField`
- `TimeField`
- `URLField`
- `UUIDField`
- `return_None`

Implement them to satisfy the specification. Do not write tests.
