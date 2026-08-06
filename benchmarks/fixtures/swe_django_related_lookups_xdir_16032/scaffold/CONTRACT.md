# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

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
- `EXPLAIN_OPTIONS_PATTERN`
- `ExplainInfo`
- `FORBIDDEN_ALIAS_PATTERN`
- `JoinInfo`
- `JoinPromoter`
- `Query`
- `RawQuery`
- `get_children_from_q`
- `get_field_names_from_opts`
- `get_order_dir`

Implement them to satisfy the specification. Do not write tests.
