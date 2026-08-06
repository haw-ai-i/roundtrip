# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/db/models/sql/compiler.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `FORCE`
- `SQLAggregateCompiler`
- `SQLCompiler`
- `SQLDeleteCompiler`
- `SQLInsertCompiler`
- `SQLUpdateCompiler`
- `cursor_iter`

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
