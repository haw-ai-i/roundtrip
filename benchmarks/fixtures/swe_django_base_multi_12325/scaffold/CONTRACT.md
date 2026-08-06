# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/db/models/base.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DEFERRED`
- `Deferred`
- `Model`
- `ModelBase`
- `ModelState`
- `ModelStateFieldsCacheDescriptor`
- `make_foreign_order_accessors`
- `method_get_order`
- `method_set_order`
- `model_unpickle`
- `subclass_exception`

## `django/db/models/options.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DEFAULT_NAMES`
- `EMPTY_RELATION_TREE`
- `IMMUTABLE_WARNING`
- `Options`
- `PROXY_PARENTS`
- `make_immutable_fields_list`
- `normalize_together`

Implement them to satisfy the specification. Do not write tests.
