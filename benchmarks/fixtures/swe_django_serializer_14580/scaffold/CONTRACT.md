# Implementation target
Write the module at `django/db/migrations/serializer.py`.

## `django/db/migrations/serializer.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseSequenceSerializer`
- `BaseSerializer`
- `BaseSimpleSerializer`
- `ChoicesSerializer`
- `DateTimeSerializer`
- `DatetimeDatetimeSerializer`
- `DecimalSerializer`
- `DeconstructableSerializer`
- `DictionarySerializer`
- `EnumSerializer`
- `FloatSerializer`
- `FrozensetSerializer`
- `FunctionTypeSerializer`
- `FunctoolsPartialSerializer`
- `IterableSerializer`
- `ModelFieldSerializer`
- `ModelManagerSerializer`
- `OperationSerializer`
- `PathLikeSerializer`
- `PathSerializer`
- `RegexSerializer`
- `SequenceSerializer`
- `Serializer`
- `SetSerializer`
- `SettingsReferenceSerializer`
- `TupleSerializer`
- `TypeSerializer`
- `UUIDSerializer`
- `serializer_factory`

Implement them to satisfy the specification. Do not write tests.
