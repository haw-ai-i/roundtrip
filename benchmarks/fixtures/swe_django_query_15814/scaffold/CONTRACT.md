# Implementation target
Write the module at `django/db/models/sql/query.py`.

## `django/db/models/sql/query.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `EXPLAIN_OPTIONS_PATTERN`
- `ExplainInfo`
- `FORBIDDEN_ALIAS_PATTERN`
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
