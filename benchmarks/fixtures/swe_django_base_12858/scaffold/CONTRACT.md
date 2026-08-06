# Implementation target
Write the module at `django/db/models/base.py`.

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

Implement them to satisfy the specification. Do not write tests.
