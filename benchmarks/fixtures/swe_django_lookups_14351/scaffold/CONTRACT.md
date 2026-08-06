# Implementation target
Write the module at `django/db/models/lookups.py`.

## `django/db/models/lookups.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BuiltinLookup`
- `Contains`
- `EndsWith`
- `Exact`
- `FieldGetDbPrepValueIterableMixin`
- `FieldGetDbPrepValueMixin`
- `GreaterThan`
- `GreaterThanOrEqual`
- `IContains`
- `IEndsWith`
- `IExact`
- `IRegex`
- `IStartsWith`
- `In`
- `IntegerFieldFloatRounding`
- `IntegerGreaterThanOrEqual`
- `IntegerLessThan`
- `IsNull`
- `LessThan`
- `LessThanOrEqual`
- `Lookup`
- `PatternLookup`
- `PostgresOperatorLookup`
- `Range`
- `Regex`
- `StartsWith`
- `Transform`
- `UUIDContains`
- `UUIDEndsWith`
- `UUIDIContains`
- `UUIDIEndsWith`
- `UUIDIExact`
- `UUIDIStartsWith`
- `UUIDStartsWith`
- `UUIDTextMixin`
- `YearExact`
- `YearGt`
- `YearGte`
- `YearLookup`
- `YearLt`
- `YearLte`

Implement them to satisfy the specification. Do not write tests.
