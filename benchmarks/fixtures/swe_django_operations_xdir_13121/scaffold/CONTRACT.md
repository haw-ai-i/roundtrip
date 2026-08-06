# Implementation target
Write the following 4 modules. They live in the same package and may import each other.

## `django/db/backends/base/operations.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseDatabaseOperations`

## `django/db/backends/mysql/operations.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DatabaseOperations`

## `django/db/backends/sqlite3/operations.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DatabaseOperations`

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
- `OrderBy`
- `OuterRef`
- `Random`
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

Implement them to satisfy the specification. Do not write tests.
