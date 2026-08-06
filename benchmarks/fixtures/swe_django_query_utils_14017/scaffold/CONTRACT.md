# Implementation target
Write the module at `django/db/models/query_utils.py`.

## `django/db/models/query_utils.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DeferredAttribute`
- `FilteredRelation`
- `PathInfo`
- `Q`
- `RegisterLookupMixin`
- `check_rel_lookup_compatibility`
- `refs_expression`
- `select_related_descend`
- `subclasses`

Implement them to satisfy the specification. Do not write tests.
