# Implementation target
Write the module at `django/db/models/fields/related.py`.

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

Implement them to satisfy the specification. Do not write tests.
