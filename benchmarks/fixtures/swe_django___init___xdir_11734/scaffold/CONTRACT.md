# Implementation target
Write the following 3 modules. They live in the same package and may import each other.

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

## `django/db/models/fields/related_lookups.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `MultiColSource`
- `RelatedExact`
- `RelatedGreaterThan`
- `RelatedGreaterThanOrEqual`
- `RelatedIn`
- `RelatedIsNull`
- `RelatedLessThan`
- `RelatedLessThanOrEqual`
- `RelatedLookupMixin`
- `get_normalized_value`

## `django/db/models/sql/query.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `JoinInfo`
- `JoinPromoter`
- `Query`
- `RawQuery`
- `add_to_dict`
- `get_children_from_q`
- `get_field_names_from_opts`
- `get_order_dir`
- `is_reverse_o2o`

Implement them to satisfy the specification. Do not write tests.
