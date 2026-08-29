## django/db/models/expressions.py
I now have the full source code. Here is the complete specification:

---

# Module Specification: `django/db/models/expressions.py`

## 1. Imports & Constants

**Imports:**
```python
import copy, datetime, functools, inspect, warnings
from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import EmptyResultSet, FieldError, FullResultSet
from django.db import DatabaseError, NotSupportedError, connection
from django.db.models import fields
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query_utils import Q
from django.utils.deconstruct import deconstructible
from django.utils.deprecation import RemovedInDjango50Warning
from django.utils.functional import cached_property
from django.utils.hashable import make_hashable
```

**Module-level constants:**
- `NoneType = type(None)` — alias for the None type, used in `_connector_combinations`.
- `_connector_combinations` — a list of 6 dicts defining field-type inference rules for combined expressions:
  1. **Numeric same-type** (ADD, SUB, MUL, DIV, MOD, POW): `(IntegerField, IntegerField → IntegerField)`, `(FloatField, FloatField → FloatField)`, `(DecimalField, DecimalField → DecimalField)`.
  2. **Numeric mixed-type** (ADD, SUB, MUL, DIV, MOD): `(IntegerField, DecimalField → DecimalField)`, `(DecimalField, IntegerField → DecimalField)`, `(IntegerField, FloatField → FloatField)`, `(FloatField, IntegerField → FloatField)`.
  3. **Bitwise operators** (BITAND, BITOR, BITLEFTSHIFT, BITRIGHTSHIFT, BITXOR): `(IntegerField, IntegerField → IntegerField)`.
  4. **Numeric with NULL** (ADD, SUB, MUL, DIV, MOD, POW): for each of `IntegerField`, `DecimalField`, `FloatField`: `(field_type, NoneType → field_type)` and `(NoneType, field_type → field_type)`.
  5. **Temporal ADD** (Combinable.ADD only): `(DateField, DurationField → DateTimeField)`, `(DateTimeField, DurationField → DateTimeField)`, `(DurationField, DateField → DateTimeField)`, `(DurationField, DateTimeField → DateTimeField)`, `(DurationField, DurationField → DurationField)`, `(TimeField, DurationField → TimeField)`, `(DurationField, TimeField → TimeField)`.
  6. **Temporal SUB** (Combinable.SUB only): `(DateField, DurationField → DateTimeField)`, `(DateTimeField, DurationField → DateTimeField)`, `(DateField, DateField → DurationField)`, `(DateField, DateTimeField → DurationField)`, `(DateTimeField, DateField → DurationField)`, `(DateTimeField, DateTimeField → DurationField)`, `(DurationField, DurationField → DurationField)`, `(TimeField, DurationField → TimeField)`, `(TimeField, TimeField → DurationField)`.

- `_connector_combinators` — a `defaultdict(list)` populated at module load by iterating `_connector_combinations` and calling `register_combinable_fields(lhs, connector, rhs, result)` for each tuple. This maps each connector string to a list of `(lhs_type, rhs_type, result_type)` triples.

## 2. Classes & Functions

### `SQLiteNumericMixin`
A mixin class (no base classes). Provides one method:

- **`as_sqlite(self, compiler, connection, **extra_context)`** — Calls `self.as_sql(compiler, connection, **extra_context)`, then if `self.output_field.get_internal_type() == "DecimalField"`, wraps the resulting SQL string with `"CAST(%s AS NUMERIC)" % sql`. Catches `FieldError` (if output_field is unresolved) and passes through. Returns `(sql, params)` tuple.

---

### `Combinable`
Base class providing arithmetic/bitwise operators that produce `CombinedExpression` objects. No inheritance.

**Class attributes:**
- `ADD = "+"`, `SUB = "-"`, `MUL = "*"`, `DIV = "/"`, `POW = "^"`, `MOD = "%%"` (double-percent for parameter-substitution safety).
- `BITAND = "&"`, `BITOR = "|"`, `BITLEFTSHIFT = "<<"`, `BITRIGHTSHIFT = ">>"`, `BITXOR = "#"`.

**Methods:**
- **`_combine(self, other, connector, reversed)`** — If `other` lacks `resolve_expression`, wraps it in `Value(other)`. Returns `CombinedExpression(other, connector, self)` if `reversed` is True, else `CombinedExpression(self, connector, other)`.

**Operator methods (all return a CombinedExpression or raise):**
- **`__neg__(self)`** → `_combine(-1, MUL, False)` — unary negation.
- **`__add__(self, other)`** → `_combine(other, ADD, False)`.
- **`__sub__(self, other)`** → `_combine(other, SUB, False)`.
- **`__mul__(self, other)`** → `_combine(other, MUL, False)`.
- **`__truediv__(self, other)`** → `_combine(other, DIV, False)`.
- **`__mod__(self, other)`** → `_combine(other, MOD, False)`.
- **`__pow__(self, other)`** → `_combine(other, POW, False)`.
- **`__and__(self, other)`** — If both operands have `conditional == True`, returns `Q(self) & Q(other)`. Otherwise raises `NotImplementedError`.
- **`bitand(self, other)`** → `_combine(other, BITAND, False)`.
- **`bitleftshift(self, other)`** → `_combine(other, BITLEFTSHIFT, False)`.
- **`bitrightshift(self, other)`** → `_combine(other, BITRIGHTSHIFT, False)`.
- **`__xor__(self, other)`** — If both conditional, returns `Q(self) ^ Q(other)`. Else raises `NotImplementedError`.
- **`bitxor(self, other)`** → `_combine(other, BITXOR, False)`.
- **`__or__(self, other)`** — If both conditional, returns `Q(self) | Q(other)`. Else raises `NotImplementedError`.
- **`bitor(self, other)`** → `_combine(other, BITOR, False)`.
- **`__radd__(self, other)`** → `_combine(other, ADD, True)`.
- **`__rsub__(self, other)`** → `_combine(other, SUB, True)`.
- **`__rmul__(self, other)`** → `_combine(other, MUL, True)`.
- **`__rtruediv__(self, other)`** → `_combine(other, DIV, True)`.
- **`__rmod__(self, other)`** → `_combine(other, MOD, True)`.
- **`__rpow__(self, other)`** → `_combine(other, POW, True)`.
- **`__rand__(self, other)`** — Always raises `NotImplementedError`.
- **`__ror__(self, other)`** — Always raises `NotImplementedError`.
- **`__rxor__(self, other)`** — Always raises `NotImplementedError`.
- **`__invert__(self)`** → `NegatedExpression(self)`.

---

### `BaseExpression`
Abstract base class for all query expressions. No mixin inheritance.

**Class attributes:**
- `empty_result_set_value = NotImplemented`
- `is_summary = False`
- `_output_field_resolved_to_none = False`
- `filterable = True`
- `window_compatible = False`

**Methods:**
- **`__init__(self, output_field=None)`** — If `output_field is not None`, sets `self.output_field = output_field`.
- **`__getstate__(self)`** — Returns a copy of `self.__dict__` with `"convert_value"` key removed (if present). Used for pickling.
- **`get_db_converters(self, connection)`** — Returns `[self.convert_value] + self.output_field.get_db_converters(connection)` if `self.convert_value is not self._convert_value_noop`, else just the field's converters.
- **`get_source_expressions(self)`** → `[]`.
- **`set_source_expressions(self, exprs)`** — Asserts `exprs` is empty/falsy.
- **`_parse_expressions(self, *expressions)`** → List: each arg kept as-is if it has `resolve_expression`, else wrapped in `F(arg)` (if string) or `Value(arg)`.
- **`as_sql(self, compiler, connection)`** — Raises `NotImplementedError`. Must return `(sql_string, params_list)`.
- **`contains_aggregate`** (`@cached_property`) → `bool`: True if any source expression has `contains_aggregate == True`.
- **`contains_over_clause`** (`@cached_property`) → `bool`: True if any source expression has `contains_over_clause == True`.
- **`contains_column_references`** (`@cached_property`) → `bool`: True if any source expression has `contains_column_references == True`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Copies self via `self.copy()`, sets `c.is_summary = summarize`, recursively resolves each source expression, calls `c.set_source_expressions(...)`, returns the copy.
- **`conditional`** (`@property`) → `bool`: True if `isinstance(self.output_field, fields.BooleanField)`.
- **`field`** (`@property`) → `self.output_field`.
- **`output_field`** (`@cached_property`) — Calls `_resolve_output_field()`. If result is None, sets `self._output_field_resolved_to_none = True` and raises `FieldError("Cannot resolve expression type, unknown output_field")`. Otherwise returns the field.
- **`_output_field_or_none`** (`@cached_property`) — Tries to return `self.output_field`; catches `FieldError` and re-raises only if `_output_field_resolved_to_none` is False; otherwise returns None.
- **`_resolve_output_field(self)`** — Iterates source fields (excluding None). If all non-None sources share the same field class, returns that field type. Otherwise raises `FieldError("Expression contains mixed types: ...")`.
- **`_convert_value_noop(value, expression, connection)`** → `value` (identity function).
- **`convert_value`** (`@cached_property`) — Returns a converter lambda based on `self.output_field.get_internal_type()`: `"FloatField"` → float conversion; `"...IntegerField"` → int conversion; `"DecimalField"` → Decimal conversion; else `_convert_value_noop`. None values pass through as None.
- **`get_lookup(self, lookup)`** → delegates to `self.output_field.get_lookup(lookup)`.
- **`get_transform(self, name)`** → delegates to `self.output_field.get_transform(name)`.
- **`relabeled_clone(self, change_map)`** — Copies self and recursively relabels each source expression via `e.relabeled_clone(change_map)`, returns clone.
- **`replace_expressions(self, replacements)`** — If `self in replacements`, returns the replacement. Else copies self, recursively replaces sub-expressions, returns clone.
- **`copy(self)`** → `copy.copy(self)`.
- **`prefix_references(self, prefix)`** — Copies self; for each source expression: if it's an `F`, creates a new `F(f"{prefix}{expr.name}")`; else recursively calls `prefix_references(prefix)`. Sets the modified list as source expressions. Returns clone.
- **`get_group_by_cols(self)`** — If no aggregate, returns `[self]`. Else collects `source.get_group_by_cols()` from each source and returns the flat list.
- **`get_source_fields(self)`** → List of `_output_field_or_none` for each source expression.
- **`asc(self, **kwargs)`** → `OrderBy(self, **kwargs)`.
- **`desc(self, **kwargs)`** → `OrderBy(self, descending=True, **kwargs)`.
- **`reverse_ordering(self)`** → returns self (no-op).
- **`flatten(self)`** — Generator: yields self, then depth-first yields from each non-None source expression's `flatten()` or the expression itself.
- **`select_format(self, compiler, sql, params)`** — If output_field has a `select_format` method, calls it; else returns `(sql, params)`.

---

### `Expression(BaseExpression, Combinable)`
Combines base expression and combinable behavior. Decorated with `@deconstructible`.

**Methods:**
- **`identity`** (`@cached_property`) — Builds a tuple: `[self.__class__] + [(arg_name, hashable_value) for each arg in constructor signature]`. For field values, uses `(model._meta.label, field.name)` if both name and model are set, else `type(value)`. Other values passed through `make_hashable()`.
- **`__eq__(self, other)`** → `NotImplemented` if not an Expression; else compares `other.identity == self.identity`.
- **`__hash__(self)`** → `hash(self.identity)`.

---

### `register_combinable_fields(lhs, connector, rhs, result)`
Module-level function. Appends `(lhs, rhs, result)` to `_connector_combinators[connector]`. Called at module load time for every entry in `_connector_combinations`.

---

### `_resolve_combined_type(connector, lhs_type, rhs_type)`
`@functools.lru_cache(maxsize=128)`. Looks up combinators for the connector. Returns the first `combined_type` where `issubclass(lhs_type, combinator_lhs_type)` and `issubclass(rhs_type, combinator_rhs_type)`. Returns None if no match.

---

### `CombinedExpression(SQLiteNumericMixin, Expression)`
Represents a binary operation between two expressions.

**Methods:**
- **`__init__(self, lhs, connector, rhs, output_field=None)`** — Calls super with `output_field`; sets `self.connector`, `self.lhs`, `self.rhs`.
- **`__repr__(self)`** → `"<CombinedExpression: {lhs} {connector} {rhs}>"`.
- **`__str__(self)`** → `"{lhs} {connector} {rhs}"`.
- **`get_source_expressions(self)`** → `[self.lhs, self.rhs]`.
- **`set_source_expressions(self, exprs)`** — Unpacks `exprs` into `self.lhs, self.rhs`.
- **`_resolve_output_field(self)`** — Calls `_resolve_combined_type(self.connector, type(self.lhs._output_field_or_none), type(self.rhs._output_field_or_none))`. If None, raises `FieldError("Cannot infer type of ...")`. Otherwise returns `combined_type()`.
- **`as_sql(self, compiler, connection)`** — Compiles lhs and rhs via `compiler.compile(...)`, collects SQL fragments and params. Calls `connection.ops.combine_expression(self.connector, expressions)`, wraps in `"(%s)"`, returns `(wrapped_sql, params)`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Resolves lhs and rhs independently. If not a `DurationExpression` or `TemporalSubtraction`: checks if one side is DurationField and the other isn't → returns a new `DurationExpression(...).resolve_expression(...)`. If connector is SUB and both sides are same datetime field type → returns a new `TemporalSubtraction(self.lhs, self.rhs).resolve_expression(...)`. Otherwise copies self, sets `c.is_summary = summarize`, assigns resolved lhs/rhs, returns clone.

---

### `DurationExpression(CombinedExpression)`
Handles duration arithmetic with database-specific formatting.

**Methods:**
- **`compile(self, side, compiler, connection)`** — If side has a DurationField output, wraps the SQL via `connection.ops.format_for_duration_arithmetic(sql)`. Else returns `compiler.compile(side)`.
- **`as_sql(self, compiler, connection)`** — If backend has native duration field (`has_native_duration_field`), delegates to parent. Otherwise calls `connection.ops.check_expression_support(self)`, compiles lhs/rhs via `self.compile()`, joins with `connection.ops.combine_duration_expression(self.connector, expressions)`, wraps in `"(%s)"`.
- **`as_sqlite(self, compiler, connection, **extra_context)`** — Calls parent `as_sql()`. If connector is MUL or DIV and either side's field type is not in `{DecimalField, DurationField, FloatField, IntegerField}`, raises `DatabaseError("Invalid arguments for operator ...")`.

---

### `TemporalSubtraction(CombinedExpression)`
Represents subtraction of temporal values producing a DurationField.

**Class attribute:** `output_field = fields.DurationField()`.

**Methods:**
- **`__init__(self, lhs, rhs)`** — Calls super with `(lhs, self.SUB, rhs)`.
- **`as_sql(self, compiler, connection)`** — Calls `connection.ops.check_expression_support(self)`, compiles lhs and rhs, returns `connection.ops.subtract_temporals(lhs.output_field.get_internal_type(), lhs_tuple, rhs_tuple)`.

---

### `F(Combinable)`
Field reference expression. Decorated with `@deconstructible(path="django.db.models.F")`.

**Methods:**
- **`__init__(self, name)`** — Sets `self.name = name`.
- **`__repr__(self)`** → `"F({name})"`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** → delegates to `query.resolve_ref(self.name, ...)`.
- **`replace_expressions(self, replacements)`** → returns `replacements.get(self, self)`.
- **`asc(self, **kwargs)`** → `OrderBy(self, **kwargs)`.
- **`desc(self, **kwargs)`** → `OrderBy(self, descending=True, **kwargs)`.
- **`__eq__(self, other)`** → True if same class and same name.
- **`__hash__(self)`** → `hash(self.name)`.
- **`copy(self)`** → `copy.copy(self)`.

---

### `ResolvedOuterRef(F)`
A resolved outer reference (inner query used as subquery). No decorator.

**Class attributes:** `contains_aggregate = False`, `contains_over_clause = False`.

**Methods:**
- **`as_sql(self, *args, **kwargs)`** — Raises `ValueError("This queryset contains a reference to an outer query and may only be used in a subquery.")`.
- **`resolve_expression(self, *args, **kwargs)`** — Calls super's resolve_expression; sets `col.possibly_multivalued = LOOKUP_SEP in self.name`; returns the column.
- **`relabeled_clone(self, relabels)`** → returns self.
- **`get_group_by_cols(self)`** → `[]`.

---

### `OuterRef(F)`
Unresolved outer reference placeholder. No decorator.

**Class attribute:** `contains_aggregate = False`.

**Methods:**
- **`resolve_expression(self, *args, **kwargs)`** — If `self.name` is already an OuterRef instance, returns it; else returns `ResolvedOuterRef(self.name)`.
- **`relabeled_clone(self, relabels)`** → returns self.

---

### `Func(SQLiteNumericMixin, Expression)`
SQL function call expression. Decorated with `@deconstructible(path="django.db.models.Func")`.

**Class attributes:**
- `function = None`, `template = "%(function)s(%(expressions)s)"`, `arg_joiner = ", "`, `arity = None`.

**Methods:**
- **`__init__(self, *expressions, output_field=None, **extra)`** — If `arity is not None` and `len(expressions) != arity`, raises `TypeError("'ClassName' takes exactly N argument(s) (M given)")`. Calls super with `output_field`; sets `self.source_expressions = self._parse_expressions(*expressions)` and `self.extra = extra`.
- **`__repr__(self)`** — Joins source expressions with `arg_joiner`, appends sorted extra options if any.
- **`_get_repr_options(self)`** → `{}` (overridable).
- **`get_source_expressions(self)`** → `self.source_expressions`.
- **`set_source_expressions(self, exprs)`** — Sets `self.source_expressions = exprs`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Copies self, sets `c.is_summary = summarize`, resolves each source expression in-place, returns clone.
- **`as_sql(self, compiler, connection, function=None, template=None, arg_joiner=None, **extra_context)`** — Calls `connection.ops.check_expression_support(self)`. For each source: compiles it; catches `EmptyResultSet` → if the arg has `empty_result_set_value != NotImplemented`, compiles `Value(empty_result_set_value)` instead (re-raises if NotImplemented); catches `FullResultSet` → compiles `Value(True)`. Collects SQL parts and params. Builds data dict from `{**self.extra, **extra_context}`; resolves function/template/arg_joiner with priority: method arg > extra > class attr. Sets `"expressions"` and `"field"` to joined SQL parts. Returns `template % data, params`.
- **`copy(self)`** — Copies self via super; copies `source_expressions[:]` and `extra.copy()`.

---

### `Value(SQLiteNumericMixin, Expression)`
Wraps a literal Python value as an expression node. Decorated with `@deconstructible(path="django.db.models.Value")`.

**Class attribute:** `for_save = False` (default).

**Methods:**
- **`__init__(self, value, output_field=None)`** — Calls super; sets `self.value = value`.
- **`__repr__(self)`** → `"Value({value!r})"`.
- **`as_sql(self, compiler, connection)`** — Calls `connection.ops.check_expression_support(self)`. Gets `_output_field_or_none`. If output_field exists: if `for_save`, calls `output_field.get_db_prep_save(val, connection)`; else `get_db_prep_value(val, connection)`. If field has `get_placeholder`, returns `(placeholder, [val])`. If val is None, returns `"NULL", []`. Else returns `"%s", [val]`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Calls super; sets `c.for_save = for_save`; returns clone.
- **`get_group_by_cols(self)`** → `[]`.
- **`_resolve_output_field(self)`** — Type inference: `str → CharField`, `bool → BooleanField`, `int → IntegerField`, `float → FloatField`, `datetime.datetime → DateTimeField`, `datetime.date → DateField`, `datetime.time → TimeField`, `datetime.timedelta → DurationField`, `Decimal → DecimalField`, `bytes → BinaryField`, `UUID → UUIDField`. Returns None if no match.
- **`empty_result_set_value`** (`@property`) → returns `self.value`.

---

### `RawSQL(Expression)`
Wraps raw SQL string as an expression.

**Methods:**
- **`__init__(self, sql, params, output_field=None)`** — If output_field is None, uses `fields.Field()`. Sets `self.sql = sql`, `self.params = params`; calls super with `output_field`.
- **`__repr__(self)`** → `"RawSQL({sql}, {params})"`.
- **`as_sql(self, compiler, connection)`** → `"(sql)", self.params`.
- **`get_group_by_cols(self)`** → `[self]`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — If `query.model`, iterates parent model fields; if a parent field's column name appears in the SQL (case-insensitive), calls `query.resolve_ref(parent_field.name, ...)`. Calls super. Returns result.

---

### `Star(Expression)`
Represents the SQL `*` wildcard.

**Methods:**
- **`__repr__(self)`** → `"'*'"`.
- **`as_sql(self, compiler, connection)`** → `"*", []`.

---

### `Col(Expression)`
Represents a column reference in SQL.

**Class attributes:** `contains_column_references = True`, `possibly_multivalued = False`.

**Methods:**
- **`__init__(self, alias, target, output_field=None)`** — If output_field is None, uses `target`. Calls super; sets `self.alias = alias`, `self.target = target`.
- **`__repr__(self)`** → `"Col(alias, str(target))"` or `"Col(str(target))"` if alias is None.
- **`as_sql(self, compiler, connection)`** — Builds SQL as `"alias.column"` (or just `"column"`) using `compiler.quote_name_unless_alias`. Returns `(sql, [])`.
- **`relabeled_clone(self, relabels)`** — If alias is None, returns self. Else returns new `Col(relabels.get(alias, alias), target, output_field)`.
- **`get_group_by_cols(self)`** → `[self]`.
- **`get_db_converters(self, connection)`** — If `target == output_field`, returns field's converters; else concatenates `output_field.get_db_converters(connection) + target.get_db_converters(connection)`.

---

### `Ref(Expression)`
Reference to a column alias in the query (e.g., from an annotation).

**Methods:**
- **`__init__(self, refs, source)`** — Calls super; sets `self.refs = refs`, `self.source = source`.
- **`__repr__(self)`** → `"Ref({refs}, {source})"`.
- **`get_source_expressions(self)`** → `[self.source]`.
- **`set_source_expressions(self, exprs)`** — Sets `(self.source,) = exprs`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** → returns self (source already resolved).
- **`relabeled_clone(self, relabels)`** → returns self.
- **`as_sql(self, compiler, connection)`** → `(connection.ops.quote_name(self.refs), [])`.
- **`get_group_by_cols(self)`** → `[self]`.

---

### `ExpressionList(Func)`
A list of expressions (e.g., for PARTITION BY clauses). No decorator.

**Class attribute:** `template = "%(expressions)s"`.

**Methods:**
- **`__init__(self, *expressions, **extra)`** — Raises `ValueError` if no expressions. Calls super with expressions and extra.
- **`__str__(self)`** → joins source expressions with `arg_joiner`.
- **`as_sqlite(self, compiler, connection, **extra_context)`** → delegates to `self.as_sql(...)` (no numeric casting needed).

---

### `OrderByList(Func)`
An ORDER BY clause expression. No decorator.

**Class attribute:** `template = "ORDER BY %(expressions)s"`.

**Methods:**
- **`__init__(self, *expressions, **extra)`** — Converts string expressions starting with `"-"` to `OrderBy(F(expr[1:]), descending=True)`. Calls super with the processed expressions.
- **`as_sql(self, *args, **kwargs)`** — If no source expressions, returns `"", ()`. Else delegates to parent.
- **`get_group_by_cols(self)`** → collects `order_by.get_group_by_cols()` from each source expression and flattens.

---

### `ExpressionWrapper(SQLiteNumericMixin, Expression)`
Wraps another expression with an explicit output_field. Decorated with `@deconstructible(path="django.db.models.ExpressionWrapper")`.

**Methods:**
- **`__init__(self, expression, output_field)`** — Calls super with `output_field`; sets `self.expression = expression`.
- **`set_source_expressions(self, exprs)`** — Sets `self.expression = exprs[0]`.
- **`get_source_expressions(self)`** → `[self.expression]`.
- **`get_group_by_cols(self)`** — If expression is an Expression instance: copies it, sets its output_field to self's output_field, calls get_group_by_cols. Else delegates to parent (returns `[self]`).
- **`as_sql(self, compiler, connection)`** → `compiler.compile(self.expression)`.
- **`__repr__(self)`** → `"ExpressionWrapper({expression})"`.

---

### `NegatedExpression(ExpressionWrapper)`
Logical negation of a conditional expression. No decorator.

**Methods:**
- **`__init__(self, expression)`** — Calls super with `(expression, output_field=fields.BooleanField())`.
- **`__invert__(self)`** → returns `self.expression.copy()`.
- **`as_sql(self, compiler, connection)`** — Tries parent as_sql. If it raises `EmptyResultSet`: if backend doesn't support boolean expr in select clause, returns `"1=1", ()`; else compiles `Value(True)`. Otherwise: if the expression is not supported in WHERE clause by the ops, returns `"CASE WHEN {sql} = 0 THEN 1 ELSE 0 END", params`; else returns `"NOT {sql}", params`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Calls super; if resolved expression's `conditional` attribute is False, raises `TypeError("Cannot negate non-conditional expressions.")`. Returns resolved.
- **`select_format(self, compiler, sql, params)`** — If backend doesn't support boolean expr in select AND the expression IS supported in WHERE clause (avoid double wrapping), wraps with `"CASE WHEN {sql} THEN 1 ELSE 0 END"`. Returns `(sql, params)`.

---

### `When(Expression)`
A single WHEN...THEN clause for use inside Case. Decorated with `@deconstructible(path="django.db.models.When")`.

**Class attributes:** `template = "WHEN %(condition)s THEN %(result)s"`, `conditional = False`.

**Methods:**
- **`__init__(self, condition=None, then=None, **lookups)`** — If lookups provided: if condition is None, creates `Q(**lookups)`. If condition has `conditional == True`, wraps in `Q(condition, **lookups)`. Validates that condition exists and is conditional (or lookups are set). If Q object is empty, raises `ValueError("An empty Q() can't be used as a When() condition.")`. Calls super with `output_field=None`; sets `self.condition = condition`, `self.result = self._parse_expressions(then)[0]`.
- **`__str__(self)`** → `"WHEN {condition!r} THEN {result!r}"`.
- **`__repr__(self)`** → `"<When: WHEN ... THEN ...>"`.
- **`get_source_expressions(self)`** → `[self.condition, self.result]`.
- **`set_source_expressions(self, exprs)`** — Unpacks into `self.condition, self.result = exprs`.
- **`get_source_fields(self)`** → `[self.result._output_field_or_none]`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Copies self; if condition has `resolve_expression`, resolves it (with `for_save=False`); resolves result with full params. Returns clone.
- **`as_sql(self, compiler, connection, template=None, **extra_context)`** — Calls `connection.ops.check_expression_support(self)`. Compiles condition and result. Builds template dict with `"condition"` and `"result"`. Uses provided or default template. Returns `(template % params_tuple, (*cond_params, *result_params))`.
- **`get_group_by_cols(self)`** → collects from both source expressions (not a complete expression for GROUP BY).

---

### `Case(SQLiteNumericMixin, Expression)`
SQL searched CASE...WHEN...ELSE expression. Decorated with `@deconstructible(path="django.db.models.Case")`.

**Class attributes:** `template = "CASE %(cases)s ELSE %(default)s END"`, `case_joiner = " "`.

**Methods:**
- **`__init__(self, *cases, default=None, output_field=None, **extra)`** — Validates all positional args are When instances (raises TypeError). Calls super with `output_field`; sets `self.cases = list(cases)`, `self.default = self._parse_expressions(default)[0]`, `self.extra = extra`.
- **`__str__(self)`** → `"CASE {cases}, ELSE {default!r}"`.
- **`__repr__(self)`** → `"<Case: CASE ...>"`.
- **`get_source_expressions(self)`** → `self.cases + [self.default]`.
- **`set_source_expressions(self, exprs)`** — Unpacks via `*self.cases, self.default = exprs`.
- **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`** — Copies self; resolves each case and the default in-place. Returns clone.
- **`copy(self)`** — Calls super copy; copies `self.cases[:]`.
- **`as_sql(self, compiler, connection, template=None, case_joiner=None, **extra_context)`** — Checks expression support. If no cases, returns compiled default. Merges extra dicts. Compiles each case: skips on EmptyResultSet; if FullResultSet, uses that case's result as the new default and breaks. Joins case SQLs with `case_joiner`. Sets `"cases"` and `"default"` in template params. Applies unification cast via `connection.ops.unification_cast_sql(self.output_field) % sql` if output field is resolved. Returns `(sql, params)`.
- **`get_group_by_cols(self)`** — If no cases, returns default's group-by cols; else delegates to parent (which iterates all sources).

---

### `Subquery(BaseExpression, Combinable)`
An explicit subquery expression. No decorator.

**Class attributes:** `template = "(%(subquery)s)"`, `contains_aggregate = False`, `empty_result_set_value = None`.

**Methods:**
- **`__init__(self, queryset, output_field=None, **extra)`** — Clones the queryset (or uses it directly if already a Query), sets `self.query.subquery = True`; sets `self.extra = extra`; calls super with `output_field`.
- **`get_source_expressions(self)`** → `[self.query]`.
- **`set_source_expressions(self, exprs)`** — Sets `self.query = exprs[0]`.
- **`_resolve_output_field(self)`** → returns `self.query.output_field`.
- **`copy(self)`** — Copies self via super; deep-clones `self.query.clone()`.
- **`external_aliases`** (`@property`) → delegates to `self.query.external_aliases`.
- **`get_external_cols(self)`** → delegates to `self.query.get_external_cols()`.
- **`as_sql(self, compiler, connection, template=None, **extra_context)`** — Checks expression support. Merges extra dicts. Compiles subquery via `self.query.as_sql(...)`, strips outer parens from SQL. Uses provided or default template. Returns `(template % data, params)`.
- **`get_group_by_cols(self)`** → returns `self.query.get_group_by_cols(wrapper=self)`.

---

### `Exists(Subquery)`
EXISTS subquery expression. No decorator.

**Class attributes:** `template = "EXISTS(%(subquery)s)"`, `output_field = fields.BooleanField()`.

**Methods:**
- **`__init__(self, queryset, **kwargs)`** — Calls super; then calls `self.query.exists()` to add EXISTS clause to the inner query.
- **`select_format(self, compiler, sql, params)`** — If backend doesn't support boolean expr in select clause, wraps with `"CASE WHEN {sql} THEN 1 ELSE 0 END"`. Returns `(sql, params)`.

---

### `OrderBy(Expression)`
Represents an ORDER BY expression. Decorated with `@deconstructible(path="django.db.models.OrderBy")`.

**Class attributes:** `template = "%(expression)s %(ordering)s"`, `conditional = False`.

**Methods:**
- **`__init__(self, expression, descending=False, nulls_first=None, nulls_last=None)`** — If both nulls_first and nulls_last are True, raises ValueError. If either is False, emits a RemovedInDjango50Warning. Sets `self.nulls_first`, `self.nulls_last`, `self.descending`. Validates expression has `resolve_expression` (raises ValueError if not). Sets `self.expression = expression`.
- **`__repr__(self)`** → `"OrderBy({expression}, descending={descending})"`.
- **`set_source_expressions(self, exprs)`** — Sets `self.expression = exprs[0]`.
- **`get_source_expressions(self)`** → `[self.expression]`.
- **`as_sql(self, compiler, connection, template=None, **extra_context)`** — Uses provided or default template. If backend supports nulls modifier: appends `" NULLS LAST"` or `" NULLS FIRST"` to template based on flags. Else (fallback): if `nulls_last` and not `(descending and order_by_nulls_first)`, prepends `"{expression} IS NULL, "`; if `nulls_first` and not `(not descending and order_by_nulls_first)`, prepends `"{expression} IS NOT NULL, "`. Compiles expression. Sets `"ordering"` to `"DESC"` or `"ASC"`. Multiplies params by count of `"%(expression)s"` placeholders in template. Returns `(template % placeholders).rstrip(), params)`.
- **`as_oracle(self, compiler, connection)`** — If the expression IS supported in WHERE clause (needs wrapping for Oracle), copies self, wraps expression in `Case(When(expression, then=True), default=False)`, calls as_sql on copy. Else delegates to normal as_sql.
- **`get_group_by_cols(self)`** → collects from source expressions.
- **`reverse_ordering(self)`** — Toggles `self.descending`; swaps nulls_first/nulls_last (if nulls_first was set, sets nulls_last=True and clears nulls_first; vice versa). Returns self.
- **`asc(self)`** — Sets `self.descending = False`.
- **`desc(self)`** — Sets `self.descending = True`.

---

### `Window(SQLiteNumericMixin, Expression)`
SQL window function expression (expression OVER (...)). No decorator.

**Class attributes:** `template = "%(expression)s OVER (%(window)s)"`, `contains_aggregate = False`, `contains_over_clause = True`.

**Methods:**
- **`__init__(self, expression, partition_by=None, order_by=None, frame=None, output_field=None)`** — Sets raw `partition_by`, `order_by`, `frame`. Validates expression has `window_compatible == True` (raises ValueError if not). If partition_by is provided: converts to tuple/list then wraps in `ExpressionList(...)`. If order_by is provided: if list/tuple → `OrderByList(...)`; if string or BaseExpression → `OrderByList(expression)`; else raises ValueError. Calls super with `output_field`; sets `self.source_expression = self._parse_expressions(expression)[0]`.
- **`_resolve_output_field(self)`** → returns `self.source_expression.output_field`.
- **`get_source_expressions(self)`** → `[self.source_expression, self.partition_by, self.order_by, self.frame]`.
- **`set_source_expressions(self, exprs)`** — Unpacks into the four attributes.
- **`as_sql(self, compiler, connection, template=None)`** — Checks expression support and backend `supports_over_clause` (raises NotSupportedError if not). Compiles source_expression. Builds window SQL: if partition_by, calls its as_sql with `"PARTITION BY %(expressions)s"` template; if order_by, compiles it; if frame, compiles it. Joins window parts with spaces. Returns `(template % {"expression": expr_sql, "window": joined_window}, (params + window_params))`.
- **`as_sqlite(self, compiler, connection)`** — If output_field is DecimalField: copies self, changes source_expression's output_field to FloatField, calls parent as_sqlite on copy. Else delegates to normal as_sql.
- **`__str__(self)`** → `"{source_expr} OVER ({PARTITION BY ...}{order_by}{frame})"`.
- **`__repr__(self)`** → `"<Window: {str(self)}>"`.
- **`get_group_by_cols(self)`** — Collects from partition_by and order_by (not frame).

---

### `WindowFrame(Expression)`
Base class for window frame clauses. No decorator.

**Class attributes:** `template = "%(frame_type)s BETWEEN %(start)s AND %(end)s"`.

**Methods:**
- **`__init__(self, start=None, end=None)`** — Sets `self.start = Value(start)`, `self.end = Value(end)`.
- **`set_source_expressions(self, exprs)`** — Unpacks into `self.start, self.end = exprs`.
- **`get_source_expressions(self)`** → `[self.start, self.end]`.
- **`as_sql(self, compiler, connection)`** — Checks expression support. Calls abstract `window_frame_start_end(connection, start.value, end.value)`. Returns `(template % {"frame_type": ..., "start": ..., "end": ...}, [])`.
- **`__repr__(self)`** → `"<WindowFrame: {str(self)}>"`.
- **`get_group_by_cols(self)`** → `[]`.
- **`__str__(self)`** — Formats start/end based on value: negative → `"{abs(value)} PRECEDING"`, zero → `"CURRENT ROW"`, None/positive end → `"UNBOUNDED FOLLOWING"`, positive start → `"{value} FOLLOWING"`. Uses `connection.ops.PRECEDING`, `.FOLLOWING`, `.CURRENT_ROW`, `.UNBOUNDED_PRECEDING`, `.UNBOUNDED_FOLLOWING` constants. Returns template-substituted string.
- **`window_frame_start_end(self, connection, start, end)`** — Raises `NotImplementedError`. Must be implemented by subclasses.

---

### `RowRange(WindowFrame)`
ROWS frame type. No decorator.

**Class attribute:** `frame_type = "ROWS"`.

**Methods:**
- **`window_frame_start_end(self, connection, start, end)`** → returns `connection.ops.window_frame_rows_start_end(start, end)`.

---

### `ValueRange(WindowFrame)`
RANGE frame type. No decorator.

**Class attribute:** `frame_type = "RANGE"`.

**Methods:**
- **`window_frame_start_end(self, connection, start, end)`** → returns `connection.ops.window_frame_range_start_end(start, end)`.

## django/db/models/query_utils.py
Here is the complete natural-language specification of `django/db/models/query_utils.py`:

---

## Module-Level Preamble

### Imports

```python
import functools
import inspect
import logging
from collections import namedtuple

from django.core.exceptions import FieldError
from django.db import DEFAULT_DB_ALIAS, DatabaseError, connections
from django.db.models.constants import LOOKUP_SEP
from django.utils import tree
```

### Constants & Globals

- **`logger`** — `logging.getLogger("django.db.models")`; the module-level logger.
- **`PathInfo`** — a `namedtuple` with fields: `"from_opts"`, `"to_opts"`, `"target_fields"`, `"join_field"`, `"m2m"`, `"direct"`, `"filtered_relation"`. Used when converting lookups (e.g., `fk__somecol`) to describe the relation in model terms (model Options and Fields for both sides of the relation; `join_field` is the field backing the relation).

---

## Code Objects

### Function: `subclasses(cls)`

A recursive generator that yields a class and all its subclasses (transitively, depth-first) via `cls.__subclasses__()`. Yields `cls` itself first.

---

### Class: `Q(tree.Node)`

Encapsulates filters as objects combinable logically using `&` (AND), `|` (OR), and `^` (XOR). Inherits from `tree.Node`.

**Class attributes:**
- `AND = "AND"` — AND connector string.
- `OR = "OR"` — OR connector string.
- `XOR = "XOR"` — XOR connector string.
- `default = AND` — default connector type.
- `conditional = True` — marks this as a conditional expression node.

**`__init__(self, *args, _connector=None, _negated=False, **kwargs)`**
Initializes the Q object by calling `super().__init__()` with:
- `children`: a list containing all positional `*args` followed by all keyword arguments as `(key, value)` tuples from `sorted(kwargs.items())`.
- `connector`: `_connector` (or inherited default).
- `negated`: `_negated`.

**`_combine(self, other, conn)`**
Combines this Q object with another. If `other.conditional is False`, raises `TypeError(other)`. If `self` is falsy (`not self`), returns `other.copy()`. If `other` is falsy and is a `Q` instance, returns `self.copy()`. Otherwise creates a new Q via `self.create(connector=conn)`, adds both `self` and `other` to it, and returns the result.

**`__or__(self, other)`** — Returns `self._combine(other, self.OR)`.

**`__and__(self, other)`** — Returns `self._combine(other, self.AND)`.

**`__xor__(self, other)`** — Returns `self._combine(other, self.XOR)`.

**`__invert__(self)`**
Creates a copy of itself via `self.copy()`, calls `.negate()` on the copy to flip its negation flag, and returns it.

**`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`**
Delegates to `query._add_q(self, reuse, allow_joins=allow_joins, split_subq=False, check_filterable=False)`, capturing the returned `(clause, joins)` tuple. Then calls `query.promote_joins(joins)` to promote any new joins to left outer joins (so rows aren't filtered when Q is used as an expression). Returns `clause`.

**`flatten(self)`**
A generator that yields this Q object and all subexpressions in depth-first order. For each child in `self.children`: if the child is a tuple, extracts `child[1]` (the lookup); if it has a `flatten` attribute, recurses via `yield from child.flatten()`; otherwise yields the child directly.

**`check(self, against, using=DEFAULT_DB_ALIAS)`**
Performs a database query to check whether the Q instance's expressions match against given values in `against`. Imports `BooleanField`, `Value`, `Coalesce` from `django.db.models`, and `Query` / `SINGLE` from SQL modules. Creates a `Query(None)`, adds each value from `against` as an annotation (wrapping non-expression values with `Value()`), and adds `Value(1)` as annotation `_check`. If the database supports comparing boolean expressions (`connections[using].features.supports_comparing_boolean_expr`), wraps `self` in a `Coalesce(self, True, output_field=BooleanField())` before adding via `query.add_q()`. Gets a compiler for `using`, executes `compiler.execute_sql(SINGLE)`, and returns whether the result is not None. Catches `DatabaseError`, logs a warning, and returns `True`.

**`deconstruct(self)`**
Returns `(path, args, kwargs)` for serialization:
- `path`: `"module.classname"` of the class; if it starts with `"django.db.models.query_utils"`, replaces that prefix with `"django.db.models"`.
- `args`: tuple of `self.children`.
- `kwargs`: dict containing `_connector` (if `self.connector != self.default`) and/or `_negated=True` (if `self.negated`).

---

### Class: `DeferredAttribute`

A descriptor for deferred-loading model fields. On first access, executes a query to fetch the value from the datastore; subsequent accesses return the cached value.

**Attributes:**
- `field` — set in `__init__`; the field being wrapped.

**`__init__(self, field)`** — Stores `field` as `self.field`.

**`__get__(self, instance, cls=None)`**
Descriptor protocol: if `instance is None`, returns `self` (class-level access). Otherwise:
1. Gets the instance's `__dict__` and the field's `attname`.
2. If the field name is not in `data`: calls `_check_parent_chain(instance)`. If that returns a non-None value, stores it in `data[field_name]`. Otherwise calls `instance.refresh_from_db(fields=[field_name])` to fetch from DB.
3. Returns `data[field_name]`.

**`_check_parent_chain(self, instance)`**
Checks if the field value can be fetched from a parent field already loaded on the instance (for multi-table inheritance). Gets `opts = instance._meta` and `link_field = opts.get_ancestor_link(self.field.model)`. If `self.field.primary_key` is True AND `self.field != link_field`, returns `getattr(instance, link_field.attname)`; otherwise returns `None`.

---

### Class: `class_or_instance_method`

A descriptor that returns a `functools.partial` bound to either the class or an instance, depending on how it's accessed. Used by `RegisterLookupMixin`.

**Attributes:**
- `class_method` — set in `__init__`; the method to call when accessed from the class.
- `instance_method` — set in `__init__`; the method to call when accessed from an instance.

**`__init__(self, class_method, instance_method)`** — Stores both methods.

**`__get__(self, instance, owner)`**
If `instance is None`, returns `functools.partial(self.class_method, owner)`. Otherwise returns `functools.partial(self.instance_method, instance)`.

---

### Class: `RegisterLookupMixin`

Mixin providing lookup registration and retrieval for model fields.

**`_get_lookup(self, lookup_name)`** — Returns `self.get_lookups().get(lookup_name, None)`.

**`get_class_lookups(cls)`** (classmethod + `@functools.lru_cache(maxsize=None)`)
Builds a merged dict of class-level lookups by iterating through `inspect.getmro(cls)` and collecting each parent's `__dict__.get("class_lookups", {})`, then merging them in reverse MRO order via `merge_dicts`.

**`get_instance_lookups(self)`**
Gets class lookups, then if the instance has an `instance_lookups` attribute, returns `{**class_lookups, **instance_lookups}`; otherwise returns just `class_lookups`.

**`get_lookups`** — A `class_or_instance_method` wrapping `get_class_lookups` (class path) and `get_instance_lookups` (instance path). Also assigned as a plain classmethod: `get_class_lookups = classmethod(get_class_lookups)`.

**`get_lookup(self, lookup_name)`**
Imports `Lookup` from `django.db.models.lookups`. Gets the found lookup via `_get_lookup(lookup_name)`. If not found and the instance has an `output_field`, delegates to `self.output_field.get_lookup(lookup_name)`. If found but is not a subclass of `Lookup`, returns `None`. Otherwise returns `found`.

**`get_transform(self, lookup_name)`**
Same pattern as `get_lookup`, but imports and validates against `Transform` from `django.db.models.lookups`. Delegates to `self.output_field.get_transform(lookup_name)` if not found.

**`merge_dicts(dicts)`** (staticmethod)
Merges a list of dicts in reverse order so that earlier dicts' keys take precedence over later ones. Returns the merged dict.

**`_clear_cached_class_lookups(cls)`** (classmethod)
Iterates through all subclasses of `cls` via `subclasses(cls)` and calls `.cache_clear()` on each subclass's `get_class_lookups`.

**`register_class_lookup(cls, lookup, lookup_name=None)`**
If `lookup_name is None`, uses `lookup.lookup_name`. Ensures `"class_lookups"` exists in `cls.__dict__` (initializing `{}` if not). Stores the lookup at `cls.class_lookups[lookup_name] = lookup`. Clears all cached lookups via `_clear_cached_class_lookups()`. Returns `lookup`.

**`register_instance_lookup(self, lookup, lookup_name=None)`**
If `lookup_name is None`, uses `lookup.lookup_name`. Ensures `"instance_lookups"` exists in `self.__dict__` (initializing `{}` if not). Stores at `self.instance_lookups[lookup_name] = lookup`. Returns `lookup`.

**`register_lookup`** — A `class_or_instance_method` wrapping `register_class_lookup` and `register_instance_lookup`. Also assigned as: `register_class_lookup = classmethod(register_class_lookup)`.

**`_unregister_class_lookup(cls, lookup, lookup_name=None)`**
For test use only (not thread-safe). If `lookup_name is None`, uses `lookup.lookup_name`. Deletes from `cls.class_lookups[lookup_name]`. Clears cached lookups.

**`_unregister_instance_lookup(self, lookup, lookup_name=None)`**
Same pattern for instance-level: deletes from `self.instance_lookups[lookup_name]`.

**`_unregister_lookup`** — A `class_or_instance_method` wrapping the two unregister methods. Also assigned as: `_unregister_class_lookup = classmethod(_unregister_class_lookup)`.

---

### Function: `select_related_descend(field, restricted, requested, select_mask, reverse=False)`

Determines whether a field should be used to descend deeper for `select_related()` purposes.

- If `field.remote_field` is falsy → returns `False`.
- If `field.remote_field.parent_link` and not `reverse` → returns `False`.
- If `restricted`: if `reverse` and `field.related_query_name()` not in `requested`, return `False`; if not `reverse` and `field.name` not in `requested`, return `False`.
- If not `restricted` and `field.null` is falsy → returns `False`.
- If `restricted` and `select_mask` and `field.name` in `requested` and `field` not in `select_mask` → raises `FieldError("Field {model}.{name} cannot be both deferred and traversed using select_related at the same time.")`.
- Otherwise returns `True`.

---

### Function: `refs_expression(lookup_parts, annotations)`

Checks if `lookup_parts` contains references to any annotation in the `annotations` dict. Iterates `n` from 1 to `len(lookup_parts)`, joining `lookup_parts[0:n]` with `LOOKUP_SEP`. If the joined string is a key in `annotations` and its value is truthy, returns `(annotations[level_n_lookup], lookup_parts[n:])`. Otherwise returns `(False, ())`.

---

### Function: `check_rel_lookup_compatibility(model, target_opts, field)`

Checks that `model` is compatible with `target_opts` for relational lookups. Defines an inner helper `check(opts)`:
- Returns True if `model._meta.concrete_model == opts.concrete_model`, or `opts.concrete_model in model._meta.get_parent_list()`, or `model in opts.get_parent_list()`.

Returns `check(target_opts)` OR (if `field.primary_key` is truthy, `check(field.model._meta)`). This handles the case where a primary key field's query target model differs from the field's own model.

---

### Class: `FilteredRelation`

Specifies custom filtering in the ON clause of SQL joins.

**Attributes:**
- `relation_name` — set in `__init__`.
- `alias` — initialized to `None`, set later by the compiler.
- `condition` — a `Q` instance, set in `__init__`.
- `path` — list of path components, initialized to `[]`.

**`__init__(self, relation_name, *, condition=Q())`**
If `relation_name` is falsy → raises `ValueError("relation_name cannot be empty.")`. Stores `relation_name`, sets `alias = None`. If `condition` is not a `Q` instance → raises `ValueError("condition argument must be a Q() instance.")`. Stores `condition` and initializes `path = []`.

**`__eq__(self, other)`**
If `other` is not the same class → returns `NotImplemented`. Otherwise compares `relation_name`, `alias`, and `condition` for equality.

**`clone(self)`**
Creates a new `FilteredRelation(relation_name, condition=self.condition)`, copies `alias` and `path[:]` (shallow copy of list), and returns it.

**`resolve_expression(self, *args, **kwargs)`**
Raises `NotImplementedError("FilteredRelation.resolve_expression() is unused.")`. This exists because `QuerySet.annotate()` only accepts expression-like arguments with a `resolve_expression()` method.

**`as_sql(self, compiler, connection)`**
Resolves the condition for use in `Join.filtered_relation`. Gets `query = compiler.query`, builds a WHERE clause via `query.build_filtered_relation_q(self.condition, reuse=set(self.path))`, and returns `compiler.compile(where)`.

## django/db/models/sql/query.py
Now I have read all 2671 lines of the file. Let me write the complete natural-language specification.

---

# Module Specification: `django/db/models/sql/query.py`

## 1. Module-Level Preamble

### Imports (lines 9–45)
```python
import copy, difflib, functools, sys
from collections import Counter, namedtuple
from collections.abc import Iterator, Mapping
from itertools import chain, count, product
from string import ascii_uppercase
from django.core.exceptions import FieldDoesNotExist, FieldError
from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections
from django.db.models.aggregates import Count
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import (BaseExpression, Col, Exists, F, OuterRef, Ref, ResolvedOuterRef, Value)
from django.db.models.fields import Field
from django.db.models.fields.related_lookups import MultiColSource
from django.db.models.lookups import Lookup
from django.db.models.query_utils import Q, check_rel_lookup_compatibility, refs_expression
from django.db.models.sql.constants import INNER, LOUTER, ORDER_DIR, SINGLE
from django.db.models.sql.datastructures import BaseTable, Empty, Join, MultiJoin
from django.db.models.sql.where import AND, OR, ExtraWhere, NothingNode, WhereNode
from django.utils.functional import cached_property
from django.utils.regex_helper import _lazy_re_compile
from django.utils.tree import Node
```

### Constants & Globals (lines 47–55)
- `__all__ = ["Query", "RawQuery"]`
- `FORBIDDEN_ALIAS_PATTERN`: compiled regex (`_lazy_re_compile`) matching forbidden characters in column aliases: single quotes, backticks, double quotes, `]`, `[`, whitespace, semicolons, or SQL comment markers (`--`, `/*`, `*/`).
- `EXPLAIN_OPTIONS_PATTERN`: compiled regex matching valid EXPLAIN option names: `[\w\-]+`.

### Helper Functions (lines 58–73)
- **`get_field_names_from_opts(opts)`**: Returns a set of field names from model options. If `opts is None`, returns empty set. Otherwise iterates over `opts.get_fields()`: for each concrete field, yields both `(f.name, f.attname)`; for non-concrete fields, yields only `(f.name,)`.
- **`get_children_from_q(q)`**: Generator that recursively walks a Q-node tree (`q.children`). For each child: if it is a `Node`, recurses; otherwise yields the child directly.

### NamedTuple (lines 76–79)
- **`JoinInfo`** = `namedtuple("JoinInfo", ("final_field", "targets", "opts", "joins", "path", "transform_function"))`. Used to return join resolution results from `setup_joins()`.

---

## 2. Code Objects

### Class: `RawQuery` (lines 82–153)
**Purpose**: Represents a single raw SQL query that can be iterated like a QuerySet result.

#### Attributes
- `params`: tuple of query parameters (default `()`).
- `sql`: the raw SQL string.
- `using`: database alias string.
- `cursor`: cursor object, initially `None`.
- `low_mark`, `high_mark`: offset/limit markers, initialized to `0` and `None`.
- `extra_select`: dict (initialized `{}`).
- `annotation_select`: dict (initialized `{}`).

#### Methods
- **`__init__(self, sql, using, params=())`**: Stores `sql`, `using`, `params`; initializes `cursor=None`, `low_mark=0`, `high_mark=None`, `extra_select={}`, `annotation_select={}`.
- **`chain(self, using)`**: Returns `self.clone(using)`.
- **`clone(self, using)`**: Returns new `RawQuery(sql=self.sql, using=using, params=self.params)`.
- **`get_columns(self)`**: If `cursor is None`, calls `_execute_query()`. Then returns a list of column names by iterating over `self.cursor.description`, applying `connections[self.using].introspection.identifier_converter` to each column's first element.
- **`__iter__(self)`**: Calls `_execute_query()`; if the database cannot use chunked reads (`not connections[self.using].features.can_use_chunked_reads`), materializes all rows into a list before returning `iter(result)`; otherwise returns `iter(self.cursor)`.
- **`__repr__(self)`**: Returns `"<RawQuery: {self}>"`.
- **`params_type (property)`**: Returns `None` if `self.params is None`; else returns `dict` if `isinstance(self.params, Mapping)`, else `tuple`.
- **`__str__(self)`**: If `params_type is None`, returns raw `self.sql`; otherwise returns `self.sql % self.params_type(self.params)`.
- **`_execute_query(self)`**: Gets connection via `connections[self.using]`. Adapts parameters using `connection.ops.adapt_unknown_value`: if params are tuple, adapts each; if dict, adapts each value; if None, passes None; else raises `RuntimeError("Unexpected params type: ...")`. Creates cursor and executes `self.sql` with adapted params.

---

### Class: `Query(BaseExpression)` (lines 158–2565)
**Purpose**: Encapsulates all SQL construction logic for a single Django ORM query. Inherits from `BaseExpression`.

#### Class-Level Attributes
- `alias_prefix = "T"` — prefix for generated table aliases.
- `empty_result_set_value = None` — value to return when the result set is empty.
- `subq_aliases = frozenset([alias_prefix])` — set of alias prefixes used by subqueries.
- `compiler = "SQLCompiler"`.
- `base_table_class = BaseTable`, `join_class = Join`.
- `default_cols = True`, `default_ordering = True`, `standard_ordering = True`.
- `filter_is_sticky = False`, `subquery = False`.

#### SQL-Related Class Attributes (defaults)
- `select = ()` — expressions for the SELECT clause.
- `group_by`: `None` (no GROUP BY), a tuple of expressions, or `True` (GROUP BY all select fields).
- `order_by = ()`.
- `low_mark = 0`, `high_mark = None` — offset/limit markers.
- `distinct = False`, `distinct_fields = ()`.
- `select_for_update = False`, `select_for_update_nowait = False`, `select_for_update_skip_locked = False`, `select_for_update_of = ()`, `select_for_no_key_update = False`.
- `select_related = False` (or a nested dict when specified).
- `has_select_fields = False`.
- `max_depth = 5` — recursion limit for select_related.
- `values_select = ()` — fields defined by `values()`/`values_list()`.

#### Annotation-Related Class Attributes
- `annotation_select_mask = None`, `_annotation_select_cache = None`.

#### Set Combination Attributes
- `combinator = None`, `combinator_all = False`, `combined_queries = ()`.

#### Extension Attributes
- `extra_select_mask = None`, `_extra_select_cache = None`.
- `extra_tables = ()`, `extra_order_by = ()`.
- `deferred_loading = (frozenset(), True)` — `(field_names, defer)`.
- `explain_info = None`.

#### Instance Attributes (initialized in `__init__`)
- `model` — the model class.
- `alias_refcount = {}` — maps alias → reference count.
- `alias_map = {}` — maps alias → Join/BaseTable object.
- `alias_cols = True` — whether to provide aliases during reference resolving.
- `external_aliases = {}` — maps external table aliases to boolean (whether aliased).
- `table_map = {}` — maps table name → list of aliases.
- `used_aliases = set()`.
- `where = WhereNode()` — the WHERE clause tree.
- `annotations = {}` — maps alias → Annotation Expression.
- `extra = {}` — maps col_alias → `(col_sql, params)`.
- `_filtered_relations = {}`.

#### Methods

##### `__init__(self, model, alias_cols=True)`
Stores `model`, initializes all instance attributes as described above.

##### `output_field (property)`
If `len(self.select) == 1`: returns `select[0].target` or `select[0].field`. If `len(self.annotation_select) == 1`: returns the single annotation's `output_field`. Otherwise returns `None`.

##### `base_table (cached_property)`
Iterates over keys of `self.alias_map`; returns the first key found.

##### `__str__(self)`
Calls `self.sql_with_params()`, returns `sql % params`.

##### `sql_with_params(self)`
Returns `(sql, params)` from `self.get_compiler(DEFAULT_DB_ALIAS).as_sql()`.

##### `__deepcopy__(self, memo)`
Returns `self.clone()` and stores in `memo[id(self)]`.

##### `get_compiler(self, using=None, connection=None, elide_empty=True)`
Validates that either `using` or `connection` is provided (raises `ValueError` otherwise). If `using`, resolves `connection = connections[using]`. Returns `connection.ops.compiler(self.compiler)(self, connection, using, elide_empty)`.

##### `get_meta(self)`
Returns `self.model._meta` if `self.model` is truthy; else returns `None`.

##### `clone(self)`
Creates a lightweight copy: instantiates `Empty()`, sets its class to `self.__class__`, shallow-copies `__dict__`. Then deep-clones mutable structures: `alias_refcount`, `alias_map`, `external_aliases`, `table_map`, `where` (via `.clone()`), `annotations`, `annotation_select_mask` (if not None), `combined_queries` (cloning each), `extra`, `extra_select_mask` (if not None), `_extra_select_cache` (if not None), `select_related` (deepcopy if not False), `subq_aliases` (if present in `__dict__`), `used_aliases`, `_filtered_relations`. Sets `_annotation_select_cache = None`. Pops `"base_table"` from `obj.__dict__` to clear cached property. Returns the clone.

##### `chain(self, klass=None)`
Returns a clone; if `klass` is provided and differs from current class, changes `obj.__class__` to `klass`. If `not obj.filter_is_sticky`, resets `used_aliases = set()`. Sets `filter_is_sticky = False`. Calls `_setup_query()` if the attribute exists. Returns the object.

##### `relabeled_clone(self, change_map)`
Returns a clone with aliases changed via `change_aliases(change_map)`.

##### `_get_col(self, target, field, alias)`
If `not self.alias_cols`, sets `alias = None`. Returns `target.get_col(alias, field)`.

##### `rewrite_cols(self, annotation, col_cnt)`
Rewrites expressions in an annotation to reference columns from the subquery. Iterates over `annotation.get_source_expressions()`: for each expression: if it is a `Ref`, appends as-is; if it is a `WhereNode` or `Lookup`, recursively rewrites and appends; otherwise, tries to find a matching selected annotation by identity (`selected_annotation is expr`) and creates a `Ref(col_alias, expr)`; if not found, checks if the expression is a `Col` or contains an aggregate but is not a summary — if so, generates a new alias `"__col{col_cnt}"`, adds it to `self.annotations`, appends to annotation mask, creates a `Ref`; otherwise recursively rewrites subexpressions. Sets source expressions on the annotation and returns `(annotation, col_cnt)`.

##### `get_aggregation(self, using, added_aggregate_names)`
Returns a dict of aggregation results. If no annotations, returns `{}`. Filters existing annotations not in `added_aggregate_names`. If any of: `group_by` is tuple, query is sliced, there are existing annotations, distinct is True, or combinator exists — creates an inner subquery (`AggregateQuery`) wrapping the cloned self; sets `subquery=True`, clears ordering, handles default columns and GROUP BY for aggregates. Relabels aliases to `"subquery"`. Moves summary expressions from inner to outer query via `rewrite_cols` and `relabeled_clone`. Ensures at least one field is selected if needed. Otherwise uses `self` directly as the outer query (clearing select, setting `default_cols=False`, clearing extra). Clears ordering/limits/select_for_update/select_related on outer query. Gets compiler with `elide_empty` flag, executes SQL for `SINGLE`. If result is None, returns empty-set values. Applies converters and returns a dict zipping `outer_query.annotation_select` keys with results.

##### `get_count(self, using)`
Clones the query, adds annotation `Count("*")` as `"__count"` (is_summary=True), calls `get_aggregation(using, ["__count"])["__count"]`.

##### `has_filters(self)`
Returns `bool(self.where)`.

##### `exists(self, limit=True)`
Clones the query. If not both distinct and sliced: if `group_by is True`, adds concrete field columns and disables GROUP BY aliases; clears select clause. For combined queries with combinator `"union"`, recursively calls `exists(limit=False)` on each. Clears ordering. If `limit`, sets limits to high=1. Adds annotation `Value(1)` as `"a"`. Returns the clone.

##### `has_results(self, using)`
Calls `self.exists(using)`, gets compiler, returns `compiler.has_results()`.

##### `explain(self, using, format=None, **options)`
Clones query. Validates each option name against `EXPLAIN_OPTIONS_PATTERN.fullmatch()` and rejects names containing `"--"` (raises `ValueError`). Sets `q.explain_info = ExplainInfo(format, options)`. Gets compiler, returns joined lines from `compiler.explain_query()`.

##### `combine(self, rhs, connector)`
Merges `rhs` query into self. Validates: models must match; no slicing allowed; distinct flags and distinct_fields must match. Bumps `rhs` prefix (excluding initial alias). Computes change_map for relabeling. Determines reuse set: empty if AND conjunction, all aliases if OR. Creates `JoinPromoter(connector, 2, False)`, adds votes from inner joins in self. Iterates over rhs tables (skipping base table): relabels join via change_map, joins into self with reuse tracking, updates change_map for alias renames, handles unused aliases. Combines subq_aliases. Clones and relabels rhs where clause, adds to self's where. Merges select/extra/ordering from rhs (rhs takes precedence). For OR merges: raises `ValueError` if both sides have extra(select). Updates extra_tables. Sets ordering from rhs or keeps self's.

##### `_get_defer_select_mask(self, opts, mask, select_mask=None)`
Recursively builds a select mask for deferred loading. Starts with PK in mask. For each concrete field: if not in defer mask, adds to select_mask; if in defer mask and is relation, recursively processes related model's mask. Remaining entries are reverse relationships or filtered relations — resolves them similarly. Returns `select_mask`.

##### `_get_only_select_mask(self, opts, mask, select_mask=None)`
Recursively builds a select mask for only-select loading. Starts with PK. For each field in mask: gets the field, adds to select_mask; if mask is non-empty and field is relation, recursively processes related model. Returns `select_mask`.

##### `get_select_mask(self)`
Converts `deferred_loading` into a field selection mask. If no field names, returns `{}`. Builds a nested dict from field names split by `LOOKUP_SEP`. If defer mode: calls `_get_defer_select_mask`; else calls `_get_only_select_mask`.

##### `table_alias(self, table_name, create=False, filtered_relation=None)`
Returns `(alias, created)`. If not creating and alias exists in `table_map`, reuses the first alias and increments refcount. Otherwise creates new: if existing aliases exist, generates `"T{len(alias_map)+1}"`; else uses `filtered_relation.alias` or `table_name` directly. Updates `table_map` and `alias_refcount`.

##### `ref_alias(self, alias)`
Increments `alias_refcount[alias]`.

##### `unref_alias(self, alias, amount=1)`
Decrements `alias_refcount[alias]` by `amount`.

##### `promote_joins(self, aliases)`
Promotes join types to LOUTER recursively. For each alias: skips base table (None join_type). If parent is LOUTER or join is nullable and not already LOUTER, promotes the join via `.promote()`, then re-examines all child joins referencing this alias.

##### `demote_joins(self, aliases)`
Demotes LOUTER joins to INNER recursively. For each alias: if LOUTER, demotes; if parent is INNER, adds parent to queue for potential demotion.

##### `reset_refcounts(self, to_counts)`
For each alias in refcount, computes difference from target count and calls `unref_alias` with that amount.

##### `change_aliases(self, change_map)`
Asserts no overlap between keys and values of change_map. Relabels references in where clause (via `.relabel_aliases()`), group_by tuple, select tuple, annotations dict. Then renames entries in alias_map, refcount, table_map for each old→new mapping. Updates `external_aliases` accordingly.

##### `bump_prefix(self, other_query, exclude=None)`
If prefixes already differ, returns immediately. Otherwise generates new prefix from alphabet sequence (`A`, `B`, ... then `AA`, `AB`, ...). Skips prefixes in `subq_aliases`. Raises `RecursionError` if limit exceeded (recursion_limit // 16). Updates both queries' subq_aliases. Relabels all aliases using the new prefix, excluding specified ones.

##### `get_initial_alias(self)`
If alias_map exists: returns base_table and refs it. If model exists but no map: joins a BaseTable for `model._meta.db_table`. Else returns None.

##### `count_active_tables(self)`
Returns count of aliases with non-zero refcount.

##### `join(self, join, reuse=None, reuse_with_filtered_relation=False)`
If `reuse_with_filtered_relation` and reuse set: finds matching joins via `.equals()`. Otherwise finds exact matches in reuse set. If found: reuses the most recent alias (or table_alias if in reuse), refs it, returns it. Otherwise creates new alias via `table_alias()`. Determines join type: LOUTER if parent is LOUTER or join is nullable; else INNER. Sets `join.join_type`, stores in alias_map, returns alias.

##### `join_parent_model(self, opts, model, alias, seen)`
If model already in seen, returns its alias. Gets inheritance chain via `opts.get_base_chain(model)`. If no chain, returns current alias. Walks the chain: for each intermediate model, if not in seen, gets ancestor link field, sets up joins, records new alias in seen. Returns final alias or `seen[None]` as fallback.

##### `check_alias(self, alias)`
If `FORBIDDEN_ALIAS_PATTERN.search(alias)`, raises `ValueError`.

##### `add_annotation(self, annotation, alias, is_summary=False, select=True)`
Checks alias validity. Resolves annotation expression with `allow_joins=True, reuse=None, summarize=is_summary`. If select: appends to annotation mask; else sets mask to all annotations minus this one. Stores in `self.annotations[alias]`.

##### `resolve_expression(self, query, *args, **kwargs)`
Clones self. Bumps prefix for alias separation. Sets `subquery=True`. Resolves where clause with outer query context. If combinator: resolves each combined query. For each annotation: resolves expression; updates external_aliases if applicable. Marks outer query's aliases as external based on whether they are Joins to different tables or BaseTables with aliased names. Returns clone.

##### `get_external_cols(self)`
Generates columns from annotations and where children via `_gen_cols(include_external=True)`, filters to those whose alias is in `external_aliases`.

##### `get_group_by_cols(self, wrapper=None)`
Gets external cols; if any are possibly multivalued, returns `[wrapper or self]`; else returns the external cols.

##### `as_sql(self, compiler, connection)`
If subquery and backend doesn't ignore unnecessary ORDER BY: clears ordering on self and combined queries. Gets SQL from compiler. If subquery, wraps in parentheses. Returns `(sql, params)`.

##### `resolve_lookup_value(self, value, can_reuse, allow_joins)`
If value has `resolve_expression`, resolves it with query context. If tuple/list: recursively resolves each element, preserving type (including namedtuple). Otherwise returns value as-is.

##### `solve_lookup_type(self, lookup)`
Splits lookup by `LOOKUP_SEP`. Checks if lookup references an annotation via `refs_expression()`. If so, returns `(expression_lookups, (), expression)`. Otherwise calls `names_to_path()` to resolve field path. Returns `(lookup_parts, field_parts, False)`. Raises `FieldError` for invalid multi-part lookups without field parts.

##### `check_query_object_type(self, value, opts, field)`
If value has `_meta`, checks compatibility via `check_rel_lookup_compatibility()`. Raises `ValueError` if incompatible.

##### `check_related_objects(self, field, value, opts)`
For relation fields: if value is a Query without select fields, checks model compatibility; if value has `_meta`, calls `check_query_object_type`; if iterable, recursively checks each element.

##### `check_filterable(self, expression)`
If expression has `resolve_expression` and `filterable=False`, raises `NotSupportedError`. Recursively checks source expressions.

##### `build_lookup(self, lookups, lhs, rhs)`
Default lookup is `"exact"`. Applies transforms from lookups (excluding last). Gets lookup class; if not found, tries interpreting the name as a transform then exact lookup. If still no lookup, returns None. Handles `None` RHS: for non-exact/iexact lookups, raises ValueError; for exact/iexact with None, converts to isnull(True). For Oracle empty-string-as-null: converts `"exact"` with `""` RHS to isnull(True). Returns the Lookup instance.

##### `try_transform(self, lhs, name)`
Gets transform class from lhs; if found, instantiates it. If not, suggests similar lookups via difflib and raises `FieldError`.

##### `build_filter(self, filter_expr, branch_negated=False, current_negated=False, can_reuse=None, allow_joins=True, split_subq=True, reuse_with_filtered_relation=False, check_filterable=True)`
Handles dict input (raises FieldError). Handles Q objects via `_add_q()`. Handles expressions with `resolve_expression` — if not conditional, raises TypeError; otherwise resolves and wraps in Lookup. Extracts `(arg, value)`. Solves lookup type. Checks filterability. Validates join permissions. Resolves lookup values. Tracks used joins before/after resolution. If referencing an expression directly (annotation), builds lookup on it. Otherwise: gets initial alias, sets up joins via `setup_joins()`, checks related objects compatibility. On MultiJoin, calls `split_exclude()`. Trims joins, determines target column(s). Builds lookup on the column. Handles IS NULL / negation logic for outer join requirements. Returns `(WhereNode, used_joins)`.

##### `add_filter(self, filter_lhs, filter_rhs)`
Calls `self.add_q(Q((filter_lhs, filter_rhs)))`.

##### `add_q(self, q_object)`
Collects existing inner joins. Calls `_add_q(q_object, self.used_aliases)`. If clause returned, adds to where with AND connector. Demotes existing inner joins.

##### `build_where(self, filter_expr)`
Returns first element of `build_filter(filter_expr, allow_joins=False)`.

##### `clear_where(self)`
Replaces `self.where` with a new `WhereNode()`.

##### `_add_q(self, q_object, used_aliases, branch_negated=False, current_negated=False, allow_joins=True, split_subq=True, check_filterable=True)`
Creates target WhereNode with connector/negation from q_object. Creates JoinPromoter. For each child: calls `build_filter()`, adds votes to promoter, adds child clause to target. Updates join types via promoter. Returns `(target_clause, needed_inner)`.

##### `build_filtered_relation_q(self, q_object, reuse, branch_negated=False, current_negated=False)`
Similar to `_add_q` but for FilteredRelation: recursively processes children; non-Node children use `build_filter()` with `reuse_with_filtered_relation=True` and `split_subq=False`. Returns target clause.

##### `add_filtered_relation(self, filtered_relation, alias)`
Sets alias on filtered relation. Validates that relation_name has no lookups. Validates that all condition lookups don't exceed the depth of relation_name. Stores in `_filtered_relations[alias]`.

##### `names_to_path(self, names, opts, allow_many=True, fail_on_missing=False)`
Walks name list building PathInfo tuples. Handles `"pk"` → pk field name. Checks filtered relations at position 0. On FieldDoesNotExist: checks annotations; if not found and fail_on_missing or pos==-1, raises `FieldError` with available choices. For relation fields: gets path to parent for concrete inheritance. Gets path_infos from field; if allow_many=False and m2m encountered, raises MultiJoin. Extends path and opts. For non-relation fields: sets final_field/targets/breaks. Returns `(path, final_field, targets, remaining_names)`.

##### `setup_joins(self, names, opts, alias, can_reuse=None, allow_many=True, reuse_with_filtered_relation=False)`
Iterates pivot points to find the longest prefix of names that resolves as fields. Builds transform chain from remaining names. For each path element: creates Join objects (INNER for direct joins), handles filtered relations, calls `self.join()`. Returns `JoinInfo(final_field, targets, opts, joins, path, final_transformer)`.

##### `trim_joins(self, targets, joins, path)`
Copies joins list. Iterates reversed path: if only one join left or not direct or has filtered_relation, breaks. Checks if target columns are a subset of the join's related fields; if so, remaps targets and unrefs/removes the join. Returns `(targets, final_alias, remaining_joins)`.

##### `_gen_cols(cls, exprs, include_external=False)`
Generator: yields `Col` instances directly; if include_external and expression has `get_external_cols`, yields those; recursively processes source expressions.

##### `_gen_col_aliases(cls, exprs)`
Generator yielding `.alias` for each col from `_gen_cols(exprs)`.

##### `resolve_ref(self, name, allow_joins=True, reuse=None, summarize=False)`
Looks up annotation by name. If found: checks join permissions if not allowing joins; if summarizing and not in select, raises FieldError; returns `Ref(name, annotation)` or the annotation itself. If not an annotation: splits by LOOKUP_SEP, tries first part as annotation with transforms on remaining parts. Otherwise sets up joins via `names_to_path`, trims them, checks permissions, validates single-column, applies transform function. Returns the resolved expression.

##### `split_exclude(self, filter_expr, can_reuse, names_with_path)`
Creates inner query for NOT EXISTS subquery. Handles OuterRef/F RHS conversion. Adds filter to inner query, clears ordering. Calls `trim_start(names_with_path)`. If alias is reusable: adds PK equality restriction with external alias. Creates exact lookup between select column and ResolvedOuterRef(trimmed_prefix). Builds Exists filter on the inner query. If contains LEFT OUTER join: adds IS NULL condition for the trimmed prefix with OR connector. Returns `(condition, needed_inner)`.

##### `set_empty(self)`
Adds NothingNode to where clause; recursively calls on combined queries.

##### `is_empty(self)`
Returns True if any child of where is a NothingNode.

##### `set_limits(self, low=None, high=None)`
Applies limits: for high, takes min with existing or adds to low_mark; for low, adds to current low_mark (clamped by high). If low == high, calls set_empty().

##### `clear_limits(self)`
Sets `low_mark=0`, `high_mark=None`.

##### `is_sliced (property)`
Returns `low_mark != 0 or high_mark is not None`.

##### `has_limit_one(self)`
Returns `high_mark is not None and (high_mark - low_mark) == 1`.

##### `can_filter(self)`
Returns `not self.is_sliced`.

##### `clear_select_clause(self)`
Sets select=(), default_cols=False, select_related=False, extra/annotation masks to empty tuples.

##### `clear_select_fields(self)`
Sets select=(), values_select=().

##### `add_select_col(self, col, name)`
Appends col to select and name to values_select.

##### `set_select(self, cols)`
Sets default_cols=False, select=tuple(cols).

##### `add_distinct_fields(self, *field_names)`
Sets distinct_fields=field_names, distinct=True.

##### `add_fields(self, field_names, allow_m2m=True)`
Gets initial alias and meta. For each field: splits by LOOKUP_SEP, sets up joins, trims, collects columns via transform function. If columns exist, calls set_select(). Catches MultiJoin/FieldError with descriptive messages.

##### `add_ordering(self, *ordering)`
For each item: if string `"?"`, skips; if starts with `-`, strips prefix; checks annotation/extra existence; validates field path via names_to_path; rejects aggregates without annotate. If errors list non-empty, raises FieldError. Appends to order_by or clears default ordering.

##### `clear_ordering(self, force=False, clear_default=True)`
If not forced and query is sliced/distinct/select_for_update, returns early. Clears order_by, extra_order_by; optionally sets default_ordering=False.

##### `set_group_by(self, allow_aliases=True)`
If allowing aliases: collects column names from joins to detect collisions. Moves Col-based values_select entries back to select; non-Col entries become annotations. Builds group_by from select + annotation group-by columns (using Ref for aliasable non-aggregate annotations). Sets self.group_by as tuple.

##### `add_select_related(self, fields)`
If select_related is bool, initializes empty dict. For each field path: traverses/creates nested dicts. Stores result in select_related.

##### `add_extra(self, select, select_params, where, params, tables, order_by)`
For select: pairs entries with positional parameters from select_params (handling `%s` placeholders). Stores `(entry, entry_params)` in extra dict. For where/params: adds ExtraWhere to where clause. For tables: appends to extra_tables. For order_by: sets extra_order_by.

##### `clear_deferred_loading(self)`
Sets deferred_loading = (frozenset(), True).

##### `add_deferred_loading(self, field_names)`
Adds field names to existing deferred set or removes from immediate set. If all fields become deferred, sets defer=True; if all become immediate, sets defer=False with remaining fields.

##### `add_immediate_loading(self, field_names)`
Replaces immediate loading fields. Handles `"pk"` → pk name. Respects existing deferrals by removing them from the new set. Sets deferred_loading = (new_set, False).

##### `set_annotation_mask(self, names)`
If None: sets mask to None; else converts to set. Clears `_annotation_select_cache`.

##### `append_annotation_mask(self, names)`
If mask exists, unions it with names and calls set_annotation_mask.

##### `set_extra_mask(self, names)`
Similar to set_annotation_mask but for extra select items.

##### `set_values(self, fields)`
Disables select_related, clears deferred loading/select fields/has_select_fields=True. Categorizes fields into field_names, extra_names, annotation_names. Sets masks accordingly. If group_by is True: adds concrete fields, disables GROUP BY aliases, clears select fields. If group_by exists: resolves Ref expressions not in selected set. Sets values_select and calls add_fields().

##### `annotation_select (property)`
Returns cached result if available; else returns annotations filtered by mask (if mask exists) or all annotations. Caches the result.

##### `extra_select (property)`
Similar pattern to annotation_select: caches, filters by extra_select_mask if set.

##### `trim_start(self, names_with_path)`
Collects all paths from names_with_path. Trims m2m joins from start, tracking LEFT OUTER presence. Unrefs trimmed aliases. Builds trimmed_prefix string from field names plus foreign key field name. If first remaining join is not LOUTER and has no filtered_relation: unrefs one more alias, adds extra restriction to where; else uses alternative select fields. Converts first active table back to BaseTable. Sets select to columns of the starting point. Returns `(trimmed_prefix, contains_louter)`.

##### `is_nullable(self, field)`
Returns `field.null` or (`field.empty_strings_allowed` and backend interprets empty strings as nulls using DEFAULT_DB_ALIAS).

---

### Function: `get_order_dir(field, default="ASC")` (lines 2568–2579)
Returns `(field_name, direction)` tuple. Uses `ORDER_DIR[default]` for the ascending/descending mapping. If field starts with `"-"`, strips it and returns reversed direction; otherwise returns original field and first direction element.

---

### Class: `JoinPromoter` (lines 2582–2671)
**Purpose**: Manages join type promotion/demotion for complex filter conditions.

#### Attributes
- `connector`: the Q-object connector (AND/OR).
- `negated`: whether the Q-object is negated.
- `effective_connector`: OR if negated+AND, AND if negated+OR, else same as connector.
- `num_children`: number of children in the Q-object.
- `votes = Counter()`: maps alias → vote count for inner/outer join decisions.

#### Methods
##### `__init__(self, connector, num_children, negated)`
Sets attributes; computes effective_connector based on negation logic. Initializes votes as empty Counter.

##### `__repr__(self)`
Returns formatted string with connector, num_children, negated.

##### `add_votes(self, votes)`
Updates self.votes with the iterable (one vote per item).

##### `update_join_types(self, query)`
Computes to_promote and to_demote sets: promotes to LOUTER if effective_connector is OR and votes < num_children; demotes to INNER if effective_connector is AND or (OR and votes == num_children). Calls `query.promote_joins(to_promote)` then `query.demote_joins(to_demote)`. Returns `to_demote`.

## django/db/models/sql/where.py
Now I have the complete source. Here is the specification:

---

## Module-Level Preamble

### Imports
```python
import operator
from functools import reduce

from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db.models.expressions import Case, When
from django.db.models.functions import Mod
from django.db.models.lookups import Exact
from django.utils import tree
from django.utils.functional import cached_property
```

### Constants & Globals
- `AND = "AND"` — Connection type constant for AND logic.
- `OR = "OR"` — Connection type constant for OR logic.
- `XOR = "XOR"` — Connection type constant for XOR logic.

---

## Code Objects

### Class `WhereNode(tree.Node)`

**Inheritance:** Extends `tree.Node` (from `django.utils.tree`).

**Class-level attributes:**
- `default = AND` — Default connector type for new child connections.
- `resolved = False` — Boolean flag indicating whether all expressions have been resolved.
- `conditional = True` — Marks this node as a conditional filter.

**Instance attributes (inherited from `tree.Node`):**
- `children` — List of child nodes/expressions.
- `connector` — One of `"AND"`, `"OR"`, or `"XOR"`; how children are combined.
- `negated` — Boolean; if `True`, the entire node is wrapped in a NOT.

**Methods:**

#### `split_having_qualify(self, negated=False, must_group_by=False)`
Returns three possibly-None nodes: `(where_node, having_node, qualify_node)`. Splits children based on whether they reference aggregates or window functions.

Logic:
1. If neither `self.contains_aggregate` nor `self.contains_over_clause`, return `(self, None, None)` — everything belongs in WHERE.
2. Compute `in_negated = negated ^ self.negated` (XOR).
3. Determine `must_remain_connected`: True if the connector forces children to stay together:
   - `in_negated and self.connector == AND`, or
   - `not in_negated and self.connector == OR`, or
   - `self.connector == XOR`.
4. If `must_remain_connected` is True, `contains_aggregate` is True, and `contains_over_clause` is False, short-circuit: return `(None, self, None)` — stash everything in HAVING (cheaper than splitting).
5. Otherwise, iterate over each child `c`:
   - If `c` has a `split_having_qualify` method, call it with `(in_negated, must_group_by)` and distribute the returned parts into `where_parts`, `having_parts`, or `qualify_parts`.
   - Else if `c.contains_over_clause`, append to `qualify_parts`.
   - Else if `c.contains_aggregate`, append to `having_parts`.
   - Else append to `where_parts`.
6. If `must_remain_connected` and there are qualify parts:
   - If no where_parts, or where_parts exist but `not must_group_by`: return `(None, None, self)` — push everything to QUALIFY.
   - If both where_parts and qualify_parts exist with conditional aggregation: raise `NotImplementedError("Heterogeneous disjunctive predicates against window functions are not implemented when performing conditional aggregation.")`.
7. Build three new nodes via `self.create(parts_list, self.connector, self.negated)` for each non-empty list; return `(where_node, having_node, qualify_node)`.

**Return:** Tuple of three `(WhereNode | None, WhereNode | None, WhereNode | None)`.

---

#### `as_sql(self, compiler, connection)`
Compiles the WHERE clause to SQL.

Logic:
1. Initialize `result = []` and `result_params = []`.
2. Set `full_needed` and `empty_needed`:
   - If `self.connector == AND`: `full_needed = len(self.children)`, `empty_needed = 1`.
   - Otherwise (OR or XOR): `full_needed = 1`, `empty_needed = len(self.children)`.
3. If `self.connector == XOR` and the database does not support logical XOR (`not connection.features.supports_logical_xor`), convert to a compound expression:
   - Build `lhs` as a new `WhereNode` with all children connected by OR.
   - Build `rhs_sum` using `reduce(operator.add, (Case(When(c, then=1), default=0) for c in self.children))`. If more than 2 children, wrap with `Mod(rhs_sum, 2)`.
   - Build `rhs = Exact(1, rhs_sum)`.
   - Return the result of `WhereNode([lhs, rhs], AND, self.negated).as_sql(compiler, connection)`.
4. Iterate over each child:
   - Try to compile it via `compiler.compile(child)`, getting `(sql, params)`.
   - If `EmptyResultSet` is raised: decrement `empty_needed`.
   - If `FullResultSet` is raised: decrement `full_needed`.
   - Otherwise (successful compilation):
     - If `sql` is non-empty: append to `result`, extend `result_params` with `params`.
     - Else (`sql` is empty string): decrement `full_needed`.
   - After each child, check short-circuit conditions:
     - If `empty_needed == 0`: if `self.negated`, raise `FullResultSet`; else raise `EmptyResultSet`.
     - If `full_needed == 0`: if `self.negated`, raise `EmptyResultSet`; else raise `FullResultSet`.
5. Join results with connector: `sql_string = " %s ".join(result)`.
6. If `sql_string` is empty, raise `FullResultSet`.
7. Apply negation wrapping:
   - If `self.negated`: wrap as `"NOT (%s)" % sql_string`.
   - Else if more than one result or `self.resolved` is True: wrap as `"(%s)" % sql_string`.
8. Return `(sql_string, result_params)`.

**Return:** Tuple of `(str SQL, list params)`, or raises `EmptyResultSet` / `FullResultSet`.

---

#### `get_group_by_cols(self)`
Recursively collects group-by columns from all children. Iterates over `self.children`, calling each child's `get_group_by_cols()` and extending a flat list. Returns the accumulated list of column references.

**Return:** `list` of group-by column references.

---

#### `get_source_expressions(self)`
Returns a shallow copy of `self.children`.

**Return:** `list` (copy of children).

---

#### `set_source_expressions(self, children)`
Replaces the current children list with the provided one. Asserts that `len(children) == len(self.children)`. Sets `self.children = children`.

---

#### `relabel_aliases(self, change_map)`
Relabels alias values in all child nodes. If `change_map` is empty/falsy, returns `self` immediately. Otherwise iterates over children by index:
- If the child has a `relabel_aliases` method (e.g., another WhereNode), call it with `change_map`.
- Else if the child has a `relabeled_clone` method, replace that child in-place at its position with `child.relabeled_clone(change_map)`.

**Return:** `self` (modified in place).

---

#### `clone(self)`
Creates and returns a deep copy of this node. Creates a new node via `self.create(connector=self.connector, negated=self.negated)`, then for each child: if the child has a `clone` method, use `child.clone()`; otherwise append the child directly. Returns the clone.

**Return:** A new `WhereNode` instance with cloned children.

---

#### `relabeled_clone(self, change_map)`
Creates a clone of this node and then relabels its aliases using `change_map`. Equivalent to chaining `self.clone()` followed by `.relabel_aliases(change_map)`.

**Return:** A new `WhereNode` with cloned and relabeled children.

---

#### `replace_expressions(self, replacements)`
Replaces sub-expressions according to a mapping dict. If `replacements` is empty/falsy, returns `self`. If `self` itself is in `replacements`, return the replacement directly. Otherwise, create a new node via `self.create(connector=self.connector, negated=self.negated)`, and for each child, append `child.replace_expressions(replacements)` (recursively). Returns the new node.

**Return:** A new `WhereNode` or an existing one if no replacements apply.

---

#### `get_refs(self)`
Collects all referenced names from children. Iterates over `self.children`, calling each child's `get_refs()` and unioning into a set. Returns the accumulated set.

**Return:** `set` of reference strings.

---

#### `_contains_aggregate(cls, obj)` *(classmethod)*
Checks if an object contains aggregate expressions. If `obj` is a `tree.Node`, recursively checks all its children via `any()`. Otherwise returns `obj.contains_aggregate`.

**Return:** `bool`.

---

#### `contains_aggregate` *(cached_property)*
Returns the result of `_contains_aggregate(self)`. Cached for performance.

**Return:** `bool`.

---

#### `_contains_over_clause(cls, obj)` *(classmethod)*
Checks if an object contains window (OVER clause) expressions. If `obj` is a `tree.Node`, recursively checks all its children via `any()`. Otherwise returns `obj.contains_over_clause`.

**Return:** `bool`.

---

#### `contains_over_clause` *(cached_property)*
Returns the result of `_contains_over_clause(self)`. Cached for performance.

**Return:** `bool`.

---

#### `is_summary` *(property)*
Returns True if any child has `is_summary == True`. Iterates over children and returns `any(child.is_summary for child in self.children)`.

**Return:** `bool`.

---

#### `_resolve_leaf(expr, query, *args, **kwargs)` *(staticmethod)*
Resolves a single expression. If `expr` has a `resolve_expression` method, calls it with `(query, *args, **kwargs)` and returns the result; otherwise returns `expr` unchanged.

**Return:** Resolved expression or original.

---

#### `_resolve_node(cls, node, query, *args, **kwargs)` *(classmethod)*
Recursively resolves all expressions within a node tree. If the node has children, recursively calls itself on each child. Then if the node has `lhs`, replaces it with the resolved leaf via `_resolve_leaf`. Same for `rhs`.

---

#### `resolve_expression(self, *args, **kwargs)`
Creates a clone of this node and resolves all expressions within it by calling `_resolve_node` on the clone. Sets `clone.resolved = True`. Returns the cloned, resolved node.

**Return:** A new resolved `WhereNode`.

---

#### `output_field` *(cached_property)*
Imports `BooleanField` from `django.db.models` and returns a new instance of it.

**Return:** `BooleanField` instance.

---

#### `_output_field_or_none` *(property)*
Returns `self.output_field`.

**Return:** `BooleanField` instance.

---

#### `select_format(self, compiler, sql, params)`
Wraps the SQL in a CASE WHEN expression if the database backend does not support boolean expressions in SELECT/GROUP BY clauses. If `not compiler.connection.features.supports_boolean_expr_in_select_clause`, transforms `sql` to `"CASE WHEN {sql} THEN 1 ELSE 0 END"`. Otherwise returns `sql` unchanged.

**Return:** Tuple of `(str SQL, list params)`.

---

#### `get_db_converters(self, connection)`
Delegates to the output field's converters. Returns `self.output_field.get_db_converters(connection)`.

**Return:** List of database converter functions.

---

#### `get_lookup(self, lookup)`
Delegates to the output field. Returns `self.output_field.get_lookup(lookup)`.

**Return:** A lookup class or instance from BooleanField.

---

#### `leaves(self)`
Generator that yields all leaf (non-WhereNode) children recursively. For each child: if it is a `WhereNode`, recurse via `child.leaves()`; otherwise yield the child directly.

**Yields:** Leaf expression/lookup objects.

---

### Class `NothingNode`

A sentinel node that matches nothing.

**Class-level attributes:**
- `contains_aggregate = False`
- `contains_over_clause = False`

#### `as_sql(self, compiler=None, connection=None)`
Always raises `EmptyResultSet`. No parameters are used.

**Raises:** `EmptyResultSet`.

---

### Class `ExtraWhere`

Represents raw SQL fragments added via the legacy `extra(where=...)` API on QuerySets. The contents are treated as a black box — no aggregate or window detection is performed.

**Class-level attributes:**
- `contains_aggregate = False`
- `contains_over_clause = False`

#### `__init__(self, sqls, params)`
Stores the raw SQL strings and their parameters:
- `self.sqls` — iterable of raw SQL condition strings.
- `self.params` — iterable of parameter values (may be None).

#### `as_sql(self, compiler=None, connection=None)`
Wraps each SQL string in parentheses (`"(sql)"`) and joins them with `" AND "`. Returns the joined string and a list of parameters (`list(self.params or ())`).

**Return:** Tuple of `(str SQL, list params)`.