# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/contrib/contenttypes/fields.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `GenericForeignKey`
- `GenericRel`
- `GenericRelation`
- `ReverseGenericManyToOneDescriptor`
- `create_generic_related_manager`

## `django/db/models/fields/related_descriptors.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ForeignKeyDeferredAttribute`
- `ForwardManyToOneDescriptor`
- `ForwardOneToOneDescriptor`
- `ManyToManyDescriptor`
- `ReverseManyToOneDescriptor`
- `ReverseOneToOneDescriptor`
- `create_forward_many_to_many_manager`
- `create_reverse_many_to_one_manager`

Implement them to satisfy the specification. Do not write tests.
