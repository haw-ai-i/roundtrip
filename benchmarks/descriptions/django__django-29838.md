## django/db/models/expressions.py
This is a natural-language specification of the `django/db/models/expressions.py` file.

## Module-Level Preamble

### Imports
*   `import copy`
*   `import datetime`
*   `import inspect`
*   `from decimal import Decimal`
*   `from django.core.exceptions import EmptyResultSet, FieldError`
*   `from django.db import connection`
*   `from django.db.models import fields`
*   `from django.db.models.query_utils import Q`
*   `from django.utils.deconstruct import deconstructible`
*   `from django.utils.functional import cached_property`

### Functions
*   `make_hashable(value)`: Converts a value into a hashable form. If `value` is a list, it converts it to a tuple. If it's a dictionary, it converts it to a tuple of sorted key-value pairs. Otherwise, it returns the value as is.

## Code Objects (Classes)

### `SQLiteNumericMixin`
A mixin class for SQLite numeric operations.
*   **Methods:**
    *   `as_sqlite(self, compiler, connection, **extra_context)`: Compiles the expression for SQLite. If the output field is a `DecimalField`, `DurationField`, or `TimeField`, it casts the result to `NUMERIC`.

### `Combinable`
A base class for objects that can be combined using operators.
*   **Constants:**
    *   `ADD = '+'`
    *   `SUB = '-'`
    *   `MUL = '*'`
    *   `DIV = '/'`
    *   `POW = '^'`
    *   `MOD = '%%'`
    *   `BITAND = '&'`
    *   `BITOR = '|'`
    *   `BITLEFTSHIFT = '<<'`
    *   `BITRIGHTSHIFT = '>>'`
    *   `BITXOR = '#'`
*   **Methods:**
    *   Implements magic methods for arithmetic and bitwise operations (`__add__`, `__sub__`, `__mul__`, `__truediv__`, `__mod__`, `__pow__`, `__and__`, `__or__`, `__xor__`, `__lshift__`, `__rshift__`) and their right-hand counterparts (`__radd__`, etc.). These methods return a `CombinedExpression` combining `self` and the other operand with the corresponding connector.
    *   `_combine(self, other, connector, reversed)`: Helper method to create a `CombinedExpression`. If `reversed` is True, `other` is the left-hand side and `self` is the right-hand side.

### `BaseExpression`
Base class for all query expressions. Decorated with `@deconstructible`.
*   **Attributes:**
    *   `is_summary = False`
    *   `filterable = True`
    *   `window_compatible = False`
*   **Methods:**
    *   `__init__(self)`: Initializes the expression.
    *   `get_db_converters(self, connection)`: Returns an empty list.
    *   `get_source_expressions(self)`: Returns an empty list.
    *   `set_source_expressions(self, exprs)`: Asserts that `exprs` is empty.
    *   `_parse_expressions(self, *expressions)`: Helper to parse expressions.
    *   `as_sql(self, compiler, connection)`: Raises `NotImplementedError`.
    *   `contains_aggregate(self)`: Returns True if any source expression contains an aggregate.
    *   `contains_over_clause(self)`: Returns True if any source expression contains an over clause.
    *   `contains_column_references(self)`: Returns True if any source expression contains column references.
    *   `resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`: Resolves source expressions and returns a copy of `self`.
    *   `get_source_fields(self)`: Returns a list of output fields from source expressions.
    *   `asc(self, **kwargs)`: Returns an `OrderBy` expression with `self` and `descending=False`.
    *   `desc(self, **kwargs)`: Returns an `OrderBy` expression with `self` and `descending=True`.
    *   `reverse_ordering(self)`: Returns `self`.
    *   `flatten(self)`: Yields `self` and flattens source expressions.
    *   `__eq__(self, other)`: Compares `self.identity` with `other.identity`.
    *   `__hash__(self)`: Returns the hash of `self.identity`.
    *   `identity(self)`: Property returning a tuple of the class, output field, and source expressions.

### `Expression(BaseExpression, Combinable)`
An expression that can be combined with other expressions.

### `CombinedExpression(SQLiteNumericMixin, Expression)`
Represents a combination of two expressions.
*   **Methods:**
    *   `__init__(self, lhs, connector, rhs, output_field=None)`: Initializes with left-hand side, connector, right-hand side, and optional output field.
    *   `as_sql(self, compiler, connection)`: Compiles the left and right expressions and joins them with the connector.

### `DurationExpression(CombinedExpression)`
A combined expression specifically for durations.
*   **Methods:**
    *   `compile(self, side, compiler, connection)`: Compiles a side of the expression, handling `datetime.timedelta` values.

### `TemporalSubtraction(CombinedExpression)`
Represents the subtraction of two temporal values.
*   **Attributes:**
    *   `output_field = fields.DurationField()`
*   **Methods:**
    *   `as_sql(self, compiler, connection)`: Uses `connection.ops.subtract_temporals` to generate SQL.

### `F(Combinable)`
An object capable of resolving references to existing query objects. Decorated with `@deconstructible`.
*   **Methods:**
    *   `__init__(self, name)`: Initializes with the name of the field.
    *   `resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`: Resolves the reference using `query.resolve_ref`.
    *   `asc(self, **kwargs)`: Returns an `OrderBy` expression.
    *   `desc(self, **kwargs)`: Returns an `OrderBy` expression.

### `ResolvedOuterRef(F)`
An object that contains a reference to an outer query.

### `OuterRef(F)`
A reference to an outer query.
*   **Methods:**
    *   `resolve_expression(self, *args, **kwargs)`: Returns a `ResolvedOuterRef`.

### `Func(SQLiteNumericMixin, Expression)`
An SQL function call.
*   **Attributes:**
    *   `function = None`
    *   `template = '%(function)s(%(expressions)s)'`
    *   `arg_joiner = ', '`
    *   `arity = None`
*   **Methods:**
    *   `__init__(self, *expressions, output_field=None, **extra)`: Initializes with source expressions and extra context.
    *   `as_sql(self, compiler, connection, function=None, template=None, arg_joiner=None, **extra_context)`: Compiles the function call into SQL.

### `Value(Expression)`
Represents a wrapped value as a node within an expression.
*   **Methods:**
    *   `__init__(self, value, output_field=None)`: Initializes with the value.
    *   `as_sql(self, compiler, connection)`: Returns the SQL placeholder and the value as a parameter.

### `DurationValue(Value)`
A value representing a duration.
*   **Methods:**
    *   `as_sql(self, compiler, connection)`: Uses `connection.ops.date_interval_sql` to generate SQL.

### `RawSQL(Expression)`
Represents raw SQL.
*   **Methods:**
    *   `__init__(self, sql, params, output_field=None)`: Initializes with SQL string and parameters.
    *   `as_sql(self, compiler, connection)`: Returns the SQL string and parameters.

### `Star(Expression)`
Represents the `*` in `SELECT *` or `COUNT(*)`.
*   **Methods:**
    *   `as_sql(self, compiler, connection)`: Returns `'*'` and an empty list of parameters.

### `Random(Expression)`
Represents a random value function.
*   **Attributes:**
    *   `output_field = fields.FloatField()`
*   **Methods:**
    *   `as_sql(self, compiler, connection)`: Uses `connection.ops.random_function_sql`.

### `Col(Expression)`
Represents a column reference.
*   **Attributes:**
    *   `contains_column_references = True`
*   **Methods:**
    *   `__init__(self, alias, target, output_field=None)`: Initializes with table alias and target field.
    *   `as_sql(self, compiler, connection)`: Returns the quoted table alias and column name.

### `SimpleCol(Expression)`
A simpler version of `Col` that doesn't include the table alias.
*   **Methods:**
    *   `as_sql(self, compiler, connection)`: Returns the quoted column name.

### `Ref(Expression)`
Reference to column alias of the query.
*   **Methods:**
    *   `__init__(self, refs, source)`: Initializes with the reference name and source expression.
    *   `as_sql(self, compiler, connection)`: Returns the quoted reference name.

### `ExpressionList(Func)`
A list of expressions.
*   **Attributes:**
    *   `template = '%(expressions)s'`
*   **Methods:**
    *   `__init__(self, *expressions, **extra)`: Initializes with expressions.

### `ExpressionWrapper(Expression)`
Wraps an expression to provide an output field.
*   **Methods:**
    *   `__init__(self, expression, output_field)`: Initializes with the expression and output field.
    *   `as_sql(self, compiler, connection)`: Delegates to the wrapped expression.

### `When(Expression)`
Represents a `WHEN` clause in a `CASE` expression.
*   **Attributes:**
    *   `template = 'WHEN %(condition)s THEN %(result)s'`
*   **Methods:**
    *   `__init__(self, condition=None, then=None, **lookups)`: Initializes with a condition and a result.
    *   `as_sql(self, compiler, connection, template=None, **extra_context)`: Compiles the `WHEN` clause.

### `Case(Expression)`
Represents a `CASE` expression.
*   **Attributes:**
    *   `template = 'CASE %(cases)s ELSE %(default)s END'`
*   **Methods:**
    *   `__init__(self, *cases, default=None, output_field=None, **extra)`: Initializes with `When` clauses and a default value.
    *   `as_sql(self, compiler, connection, template=None, case_joiner=None, **extra_context)`: Compiles the `CASE` expression.

### `Subquery(Expression)`
Represents a subquery.
*   **Attributes:**
    *   `template = '(%(subquery)s)'`
*   **Methods:**
    *   `__init__(self, queryset, output_field=None, **extra)`: Initializes with a queryset.
    *   `as_sql(self, compiler, connection, template=None, **extra_context)`: Compiles the subquery.

### `Exists(Subquery)`
Represents an `EXISTS` subquery.
*   **Attributes:**
    *   `template = 'EXISTS(%(subquery)s)'`
    *   `output_field = fields.BooleanField()`
*   **Methods:**
    *   `__init__(self, queryset, negated=False, **kwargs)`: Initializes with a queryset and negation flag.
    *   `as_sql(self, compiler, connection, template=None, **extra_context)`: Compiles the `EXISTS` clause.

### `OrderBy(BaseExpression)`
Represents an `ORDER BY` clause.
*   **Attributes:**
    *   `template = '%(expression)s %(ordering)s'`
*   **Methods:**
    *   `__init__(self, expression, descending=False, nulls_first=False, nulls_last=False)`: Initializes with an expression and ordering options.
    *   `as_sql(self, compiler, connection, template=None, **extra_context)`: Compiles the `ORDER BY` clause.

### `Window(Expression)`
Represents a window function.
*   **Attributes:**
    *   `template = '%(expression)s OVER (%(window)s)'`
*   **Methods:**
    *   `__init__(self, expression, partition_by=None, order_by=None, frame=None, output_field=None)`: Initializes with an expression, partition, ordering, and frame.
    *   `as_sql(self, compiler, connection, template=None)`: Compiles the window function.

### `WindowFrame(Expression)`
Base class for window frames.
*   **Methods:**
    *   `__init__(self, start=None, end=None)`: Initializes with start and end boundaries.
    *   `as_sql(self, compiler, connection)`: Compiles the window frame.
    *   `window_frame_start_end(self, connection, start, end)`: Raises `NotImplementedError`.

### `RowRange(WindowFrame)`
Represents a `ROWS` window frame.
*   **Attributes:**
    *   `frame_type = 'ROWS'`
*   **Methods:**
    *   `window_frame_start_end(self, connection, start, end)`: Uses `connection.ops.window_frame_rows_start_end`.

### `ValueRange(WindowFrame)`
Represents a `RANGE` window frame.
*   **Attributes:**
    *   `frame_type = 'RANGE'`
*   **Methods:**
    *   `window_frame_start_end(self, connection, start, end)`: Uses `connection.ops.window_frame_range_start_end`.

## django/utils/tree.py
**1. Module-Level Preamble:**

*   **Imports:**
    *   `import copy`
*   **Constants & Globals:**
    *   None (other than the class definition).

**2. Code Objects (Classes and Functions):**

*   **Class: `Node`**
    *   **Base Classes:** None (implicitly inherits from `object`).
    *   **Attributes:**
        *   `default` (class attribute): A string literal `'DEFAULT'`. Represents the standard connector type.
        *   `children` (instance attribute): A list of children nodes or leaf data.
        *   `connector` (instance attribute): A string representing the connection type.
        *   `negated` (instance attribute): A boolean indicating if the node is negated.

    *   **Method: `__init__(self, children=None, connector=None, negated=False)`**
        *   **Logic:**
            *   Initializes `self.children` to a shallow copy of `children` (`children[:]`) if `children` is truthy; otherwise, initializes it to an empty list `[]`.
            *   Initializes `self.connector` to `connector` if it is truthy; otherwise, falls back to `self.default`.
            *   Initializes `self.negated` to the value of `negated`.

    *   **Method: `_new_instance(cls, children=None, connector=None, negated=False)`**
        *   **Decorator:** `@classmethod`
        *   **Logic:**
            *   Creates a new instance of `Node` by calling `Node(children, connector, negated)`.
            *   Reassigns the `__class__` attribute of the newly created object to `cls`.
            *   Returns the newly created object.

    *   **Method: `__str__(self)`**
        *   **Logic:**
            *   Constructs a string representation of the node.
            *   If `self.negated` is `True`, uses the template `'(NOT (%s: %s))'`. Otherwise, uses `'(%s: %s)'`.
            *   Formats the template with `self.connector` and a comma-separated string of the string representations of all items in `self.children`.
            *   Returns the formatted string.

    *   **Method: `__repr__(self)`**
        *   **Logic:**
            *   Returns a string in the format `"<ClassName: StringRepresentation>"`, where `ClassName` is `self.__class__.__name__` and `StringRepresentation` is the result of `str(self)`.

    *   **Method: `__deepcopy__(self, memodict)`**
        *   **Logic:**
            *   Creates a new `Node` instance using `Node(connector=self.connector, negated=self.negated)`.
            *   Sets the `__class__` of the new object to `self.__class__`.
            *   Sets the `children` attribute of the new object to a deep copy of `self.children`, passing `memodict` to `copy.deepcopy`.
            *   Returns the new object.

    *   **Method: `__len__(self)`**
        *   **Logic:** Returns the integer length of `self.children`.

    *   **Method: `__bool__(self)`**
        *   **Logic:** Returns `True` if `self.children` is truthy (non-empty), otherwise `False`.

    *   **Method: `__contains__(self, other)`**
        *   **Logic:** Returns `True` if `other` is present in `self.children`, otherwise `False`.

    *   **Method: `__eq__(self, other)`**
        *   **Logic:** Returns `True` if all of the following conditions are met, otherwise `False`:
            *   `self.__class__` is identical to `other.__class__`.
            *   The tuple `(self.connector, self.negated)` equals `(other.connector, other.negated)`.
            *   `self.children` equals `other.children`.

    *   **Method: `__hash__(self)`**
        *   **Logic:**
            *   Constructs a tuple containing `self.__class__`, `self.connector`, `self.negated`, and all elements of `self.children`.
            *   Before adding children to the tuple, any child that is an instance of `list` is converted to a `tuple`.
            *   Returns the hash of this constructed tuple.

    *   **Method: `add(self, data, conn_type, squash=True)`**
        *   **Logic:**
            *   If `data` is already in `self.children`, returns `data` immediately.
            *   If `squash` is `False`, appends `data` to `self.children` and returns `data`.
            *   If `self.connector` equals `conn_type`:
                *   Checks if `data` can be squashed: `data` must be an instance of `Node`, `data.negated` must be `False`, and either `data.connector` equals `conn_type` or the length of `data` (number of children) is 1.
                *   If squashing is possible, extends `self.children` with `data.children` and returns `self`.
                *   If squashing is not possible, appends `data` to `self.children` and returns `data`.
            *   If `self.connector` does not equal `conn_type`:
                *   Creates a new node `obj` using `self._new_instance(self.children, self.connector, self.negated)`.
                *   Updates `self.connector` to `conn_type`.
                *   Replaces `self.children` with a new list containing `[obj, data]`.
                *   Returns `data`.

    *   **Method: `negate(self)`**
        *   **Logic:** Toggles the boolean value of `self.negated` (i.e., `self.negated = not self.negated`).