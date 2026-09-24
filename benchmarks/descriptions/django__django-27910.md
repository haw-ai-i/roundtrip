## django/db/migrations/serializer.py
```markdown
# Specification for `django/db/migrations/serializer.py`

## 1. Module-Level Preamble

### Imports
```python
import builtins
import collections.abc
import datetime
import decimal
import enum
import functools
import math
import re
import types
import uuid

from django.conf import SettingsReference
from django.db import models
from django.db.migrations.operations.base import Operation
from django.db.migrations.utils import COMPILED_REGEX_TYPE, RegexObject
from django.utils.functional import LazyObject, Promise
from django.utils.timezone import utc
from django.utils.version import get_docs_version
```

## 2. Code Objects (Classes and Functions)

### `BaseSerializer`
Base class for all serializers.
*   **`__init__(self, value)`**: Initializes the serializer with `self.value = value`.
*   **`serialize(self)`**: Raises `NotImplementedError('Subclasses of BaseSerializer must implement the serialize() method.')`.

### `BaseSequenceSerializer(BaseSerializer)`
Base class for sequence-like objects.
*   **`_format(self)`**: Raises `NotImplementedError('Subclasses of BaseSequenceSerializer must implement the _format() method.')`.
*   **`serialize(self)`**: Iterates over `self.value`. For each item, calls `serializer_factory(item).serialize()` to get its string representation and imports. Collects all imports into a set and strings into a list. Returns `self._format() % (", ".join(strings)), imports`.

### `BaseSimpleSerializer(BaseSerializer)`
*   **`serialize(self)`**: Returns `repr(self.value), set()`.

### `DateTimeSerializer(BaseSerializer)`
For `datetime.*` objects except `datetime.datetime`.
*   **`serialize(self)`**: Returns `repr(self.value), {'import datetime'}`.

### `DatetimeDatetimeSerializer(BaseSerializer)`
For `datetime.datetime` objects.
*   **`serialize(self)`**: If `self.value.tzinfo` is not `None` and not `utc`, converts the value to UTC using `self.value.astimezone(utc)`. Initializes `imports = ["import datetime"]`. If `self.value.tzinfo` is not `None`, appends `"from django.utils.timezone import utc"` to `imports`. Returns `repr(self.value).replace('<UTC>', 'utc'), set(imports)`.

### `DecimalSerializer(BaseSerializer)`
*   **`serialize(self)`**: Returns `repr(self.value), {"from decimal import Decimal"}`.

### `DeconstructableSerializer(BaseSerializer)`
*   **`@staticmethod serialize_deconstructed(path, args, kwargs)`**: Calls `DeconstructableSerializer._serialize_path(path)` to get `name` and `imports`. Serializes each argument in `args` and each key-value pair in `sorted(kwargs.items())` using `serializer_factory`. Updates `imports` and collects strings. Returns `"%s(%s)" % (name, ", ".join(strings)), imports`.
*   **`@staticmethod _serialize_path(path)`**: Splits `path` from the right once (`path.rsplit(".", 1)`) into `module` and `name`. If `module == "django.db.models"`, sets `imports = {"from django.db import models"}` and `name = "models.%s" % name`. Otherwise, sets `imports = {"import %s" % module}` and `name = path`. Returns `name, imports`.
*   **`serialize(self)`**: Returns `self.serialize_deconstructed(*self.value.deconstruct())`.

### `DictionarySerializer(BaseSerializer)`
*   **`serialize(self)`**: Iterates over `sorted(self.value.items())`. Serializes each key and value using `serializer_factory`. Collects imports and formats strings as `"%s: %s" % (k, v)`. Returns `"{%s}" % (", ".join(...)), imports`.

### `EnumSerializer(BaseSerializer)`
*   **`serialize(self)`**: Gets `enum_class = self.value.__class__` and `module = enum_class.__module__`. Serializes `self.value.value` to get `v_string` and `v_imports`. Sets `imports = {'import %s' % module, *v_imports}`. Returns `"%s.%s(%s)" % (module, enum_class.__name__, v_string), imports`.

### `FloatSerializer(BaseSimpleSerializer)`
*   **`serialize(self)`**: If `math.isnan(self.value)` or `math.isinf(self.value)`, returns `'float("{}")'.format(self.value), set()`. Otherwise, returns `super().serialize()`.

### `FrozensetSerializer(BaseSequenceSerializer)`
*   **`_format(self)`**: Returns `"frozenset([%s])"`.

### `FunctionTypeSerializer(BaseSerializer)`
*   **`serialize(self)`**:
    *   If `getattr(self.value, "__self__", None)` is truthy and `isinstance(self.value.__self__, type)`, gets `klass = self.value.__self__` and `module = klass.__module__`. Returns `"%s.%s.%s" % (module, klass.__name__, self.value.__name__), {"import %s" % module}`.
    *   If `self.value.__name__ == '<lambda>'`, raises `ValueError("Cannot serialize function: lambda")`.
    *   If `self.value.__module__ is None`, raises `ValueError("Cannot serialize function %r: No module" % self.value)`.
    *   If `'<' not in self.value.__qualname__`, returns `'%s.%s' % (self.value.__module__, self.value.__qualname__), {'import %s' % self.value.__module__}`.
    *   Otherwise, raises `ValueError('Could not find function %s in %s.\n' % (self.value.__name__, self.value.__module__))`.

### `FunctoolsPartialSerializer(BaseSerializer)`
*   **`serialize(self)`**: Serializes `self.value.func`, `self.value.args`, and `self.value.keywords` using `serializer_factory`. Combines their imports with `{'import functools'}`. Returns `'functools.%s(%s, *%s, **%s)' % (self.value.__class__.__name__, func_string, args_string, keywords_string), imports`.

### `IterableSerializer(BaseSerializer)`
*   **`serialize(self)`**: Serializes each item in `self.value`. Returns `"(%s)" if len(strings) != 1 else "(%s,)"` formatted with `", ".join(strings)`, along with the collected imports.

### `ModelFieldSerializer(DeconstructableSerializer)`
*   **`serialize(self)`**: Unpacks `self.value.deconstruct()` into `attr_name, path, args, kwargs`. Returns `self.serialize_deconstructed(path, args, kwargs)`.

### `ModelManagerSerializer(DeconstructableSerializer)`
*   **`serialize(self)`**: Unpacks `self.value.deconstruct()` into `as_manager, manager_path, qs_path, args, kwargs`. If `as_manager` is true, gets `name, imports = self._serialize_path(qs_path)` and returns `"%s.as_manager()" % name, imports`. Otherwise, returns `self.serialize_deconstructed(manager_path, args, kwargs)`.

### `OperationSerializer(BaseSerializer)`
*   **`serialize(self)`**: Imports `OperationWriter` from `django.db.migrations.writer`. Calls `OperationWriter(self.value, indentation=0).serialize()` to get `string, imports`. Returns `string.rstrip(','), imports`.

### `RegexSerializer(BaseSerializer)`
*   **`serialize(self)`**: Serializes `self.value.pattern`. Calculates `flags = self.value.flags ^ re.compile('').flags`. Serializes `flags`. Sets `imports = {'import re', *pattern_imports, *flag_imports}`. Constructs `args = [regex_pattern]`, appending `regex_flags` if `flags` is non-zero. Returns `"re.compile(%s)" % ', '.join(args), imports`.

### `SequenceSerializer(BaseSequenceSerializer)`
*   **`_format(self)`**: Returns `"[%s]"`.

### `SetSerializer(BaseSequenceSerializer)`
*   **`_format(self)`**: Returns `'{%s}' if self.value else 'set(%s)'`.

### `SettingsReferenceSerializer(BaseSerializer)`
*   **`serialize(self)`**: Returns `"settings.%s" % self.value.setting_name, {"from django.conf import settings"}`.

### `TupleSerializer(BaseSequenceSerializer)`
*   **`_format(self)`**: Returns `"(%s)" if len(self.value) != 1 else "(%s,)"`.

### `TypeSerializer(BaseSerializer)`
*   **`serialize(self)`**: Checks `special_cases = [(models.Model, "models.Model", []), (type(None), 'type(None)', [])]`. If `case is self.value`, returns `string, set(imports)`. If `hasattr(self.value, "__module__")`, gets `module = self.value.__module__`. If `module == builtins.__name__`, returns `self.value.__name__, set()`. Otherwise, returns `"%s.%s" % (module, self.value.__name__), {"import %s" % module}`.

### `UUIDSerializer(BaseSerializer)`
*   **`serialize(self)`**: Returns `"uuid.%s" % repr(self.value), {"import uuid"}`.

### `Serializer`
A registry for serializers.
*   **`_registry`**: A class-level dictionary mapping types to serializer classes:
    *   `frozenset`: `FrozensetSerializer`
    *   `list`: `SequenceSerializer`
    *   `set`: `SetSerializer`
    *   `tuple`: `TupleSerializer`
    *   `dict`: `DictionarySerializer`
    *   `enum.Enum`: `EnumSerializer`
    *   `datetime.datetime`: `DatetimeDatetimeSerializer`
    *   `(datetime.date, datetime.timedelta, datetime.time)`: `DateTimeSerializer`
    *   `SettingsReference`: `SettingsReferenceSerializer`
    *   `float`: `FloatSerializer`
    *   `(bool, int, type(None), bytes, str, range)`: `BaseSimpleSerializer`
    *   `decimal.Decimal`: `DecimalSerializer`
    *   `(functools.partial, functools.partialmethod)`: `FunctoolsPartialSerializer`
    *   `(types.FunctionType, types.BuiltinFunctionType, types.MethodType)`: `FunctionTypeSerializer`
    *   `collections.abc.Iterable`: `IterableSerializer`
    *   `(COMPILED_REGEX_TYPE, RegexObject)`: `RegexSerializer`
    *   `uuid.UUID`: `UUIDSerializer`
*   **`@classmethod register(cls, type_, serializer)`**: If `serializer` is not a subclass of `BaseSerializer`, raises `ValueError("'%s' must inherit from 'BaseSerializer'." % serializer.__name__)`. Sets `cls._registry[type_] = serializer`.
*   **`@classmethod unregister(cls, type_)`**: Removes and returns the serializer for `type_` using `cls._registry.pop(type_)`.

### `serializer_factory(value)`
*   **Signature:** `def serializer_factory(value):`
*   **Logic:**
    1.  If `isinstance(value, Promise)`, sets `value = str(value)`.
    2.  Else if `isinstance(value, LazyObject)`, sets `value = value.__reduce__()[1][0]`.
    3.  If `isinstance(value, models.Field)`, returns `ModelFieldSerializer(value)`.
    4.  If `isinstance(value, models.manager.BaseManager)`, returns `ModelManagerSerializer(value)`.
    5.  If `isinstance(value, Operation)`, returns `OperationSerializer(value)`.
    6.  If `isinstance(value, type)`, returns `TypeSerializer(value)`.
    7.  If `hasattr(value, 'deconstruct')`, returns `DeconstructableSerializer(value)`.
    8.  Iterates over `Serializer._registry.items()`. If `isinstance(value, type_)`, returns `serializer_cls(value)`.
    9.  If no serializer is found, raises `ValueError` with a message indicating the value cannot be serialized, including a link to the Django documentation formatted with `get_docs_version()`.
```

## django/db/models/__init__.py
**1. Module-Level Preamble:**

*   **Imports:**
    *   `ObjectDoesNotExist` from `django.core.exceptions`
    *   `signals` from `django.db.models`
    *   `*` and `__all__ as aggregates_all` from `django.db.models.aggregates`
    *   `*` and `__all__ as constraints_all` from `django.db.models.constraints`
    *   `CASCADE`, `DO_NOTHING`, `PROTECT`, `SET`, `SET_DEFAULT`, `SET_NULL`, `ProtectedError` from `django.db.models.deletion`
    *   `Case`, `Exists`, `Expression`, `ExpressionList`, `ExpressionWrapper`, `F`, `Func`, `OuterRef`, `RowRange`, `Subquery`, `Value`, `ValueRange`, `When`, `Window`, `WindowFrame` from `django.db.models.expressions`
    *   `*` and `__all__ as fields_all` from `django.db.models.fields`
    *   `FileField`, `ImageField` from `django.db.models.fields.files`
    *   `OrderWrt` from `django.db.models.fields.proxy`
    *   `*` and `__all__ as indexes_all` from `django.db.models.indexes`
    *   `Lookup`, `Transform` from `django.db.models.lookups`
    *   `Manager` from `django.db.models.manager`
    *   `Prefetch`, `Q`, `QuerySet`, `prefetch_related_objects` from `django.db.models.query`
    *   `FilteredRelation` from `django.db.models.query_utils`
    *   `DEFERRED`, `Model` from `django.db.models.base` (Note: imported after other modules to avoid circular imports)
    *   `ForeignKey`, `ForeignObject`, `OneToOneField`, `ManyToManyField`, `ManyToOneRel`, `ManyToManyRel`, `OneToOneRel` from `django.db.models.fields.related` (Note: imported after other modules to avoid circular imports)

*   **Constants & Globals:**
    *   `__all__`: A list of strings representing the public API of the module. It is initialized as the concatenation of `aggregates_all`, `constraints_all`, `fields_all`, and `indexes_all`. It is then extended with the following list of strings:
        *   `'ObjectDoesNotExist'`, `'signals'`
        *   `'CASCADE'`, `'DO_NOTHING'`, `'PROTECT'`, `'SET'`, `'SET_DEFAULT'`, `'SET_NULL'`, `'ProtectedError'`
        *   `'Case'`, `'Exists'`, `'Expression'`, `'ExpressionList'`, `'ExpressionWrapper'`, `'F'`, `'Func'`, `'OuterRef'`, `'RowRange'`, `'Subquery'`, `'Value'`, `'ValueRange'`, `'When'`, `'Window'`, `'WindowFrame'`
        *   `'FileField'`, `'ImageField'`, `'OrderWrt'`, `'Lookup'`, `'Transform'`, `'Manager'`
        *   `'Prefetch'`, `'Q'`, `'QuerySet'`, `'prefetch_related_objects'`, `'DEFERRED'`, `'Model'`
        *   `'FilteredRelation'`
        *   `'ForeignKey'`, `'ForeignObject'`, `'OneToOneField'`, `'ManyToManyField'`, `'ManyToOneRel'`, `'ManyToManyRel'`, `'OneToOneRel'`

**2. Code Objects (Classes and Functions):**

This module acts solely as an aggregation point for the `django.db.models` package and does not define any classes or functions of its own.