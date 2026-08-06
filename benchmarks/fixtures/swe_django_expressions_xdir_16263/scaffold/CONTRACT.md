# Implementation target
Write the following 4 modules. They live in the same package and may import each other.

## `django/db/models/expressions.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseExpression`
- `Case`
- `Col`
- `Combinable`
- `CombinedExpression`
- `DurationExpression`
- `Exists`
- `Expression`
- `ExpressionList`
- `ExpressionWrapper`
- `F`
- `Func`
- `NegatedExpression`
- `NoneType`
- `OrderBy`
- `OrderByList`
- `OuterRef`
- `RawSQL`
- `Ref`
- `ResolvedOuterRef`
- `RowRange`
- `SQLiteNumericMixin`
- `Star`
- `Subquery`
- `TemporalSubtraction`
- `Value`
- `ValueRange`
- `When`
- `Window`
- `WindowFrame`
- `register_combinable_fields`

## `django/db/models/query_utils.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DeferredAttribute`
- `FilteredRelation`
- `PathInfo`
- `Q`
- `RegisterLookupMixin`
- `check_rel_lookup_compatibility`
- `class_or_instance_method`
- `logger`
- `refs_expression`
- `select_related_descend`
- `subclasses`

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

## `django/db/models/sql/where.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AND`
- `ExtraWhere`
- `NothingNode`
- `OR`
- `SubqueryConstraint`
- `WhereNode`
- `XOR`

Implement them to satisfy the specification. Do not write tests.
