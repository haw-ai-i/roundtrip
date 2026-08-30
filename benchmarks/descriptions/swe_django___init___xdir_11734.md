## django/db/models/fields/__init__.py
Now I have read every line of the 2403-line file. Here is the complete specification:

---

# Module-Level Preamble

## Imports

```python
import collections.abc
import copy
import datetime
import decimal
import operator
import uuid
import warnings
from base64 import b64decode, b64encode
from functools import partialmethod, total_ordering
from django import forms
from django.apps import apps
from django.conf import settings
from django.core import checks, exceptions, validators
from django.core.exceptions import FieldDoesNotExist  # NOQA (re-exported for backwards compatibility)
from django.db import connection, connections, router
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query_utils import DeferredAttribute, RegisterLookupMixin
from django.utils import timezone
from django.utils.datastructures import DictWrapper
from django.utils.dateparse import parse_date, parse_datetime, parse_duration, parse_time
from django.utils.duration import duration_microseconds, duration_string
from django.utils.functional import Promise, cached_property
from django.utils.ipv6 import clean_ipv6_address
from django.utils.itercompat import is_iterable
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
```

## Constants & Globals

- **`__all__`** — A list of 30 exported names: `'AutoField', 'BLANK_CHOICE_DASH', 'BigAutoField', 'BigIntegerField', 'BinaryField', 'BooleanField', 'CharField', 'CommaSeparatedIntegerField', 'DateField', 'DateTimeField', 'DecimalField', 'DurationField', 'EmailField', 'Empty', 'Field', 'FieldDoesNotExist', 'FilePathField', 'FloatField', 'GenericIPAddressField', 'IPAddressField', 'IntegerField', 'NOT_PROVIDED', 'NullBooleanField', 'PositiveIntegerField', 'PositiveSmallIntegerField', 'SlugField', 'SmallAutoField', 'SmallIntegerField', 'TextField', 'TimeField', 'URLField', 'UUIDField'`.
- **`BLANK_CHOICE_DASH`** — `[("", "---------")]`, a list used as the default blank choice for select fields.

## Helper Classes & Functions (module-level)

### `class Empty:`
A sentinel class with no attributes or methods, used to create proxy objects whose `__class__` is later reassigned.

### `class NOT_PROVIDED:`
A sentinel class with no attributes or methods, used as the default value for the `default` parameter of `Field.__init__` to distinguish "no default was set" from an explicit `None` default.

### `_load_field(app_label, model_name, field_name)` → Field
Looks up a model via `apps.get_model(app_label, model_name)`, then calls `._meta.get_field(field_name)` and returns the resulting Field instance. Used as the unpickling target for fields attached to models.

### `_empty(of_cls)` → object
Creates an `Empty()` instance, sets its `__class__` to `of_cls`, and returns it. Used during pickling when a field is not yet attached to a model.

### `return_None()` → None
A zero-argument function that returns `None`. Used as the default getter for fields with no explicit default but which should return `None` at the database level.

---

# Code Objects (Classes and Functions)

## `@total_ordering class Field(RegisterLookupMixin)`

**Base class for all field types.** Decorated with `functools.total_ordering`. Inherits from `RegisterLookupMixin`.

### Class Attributes

| Attribute | Type/Value | Description |
|---|---|---|
| `empty_strings_allowed` | `True` (bool) | Whether empty strings are permitted at the database level. |
| `empty_values` | `list(validators.EMPTY_VALUES)` | List of values considered "empty". |
| `creation_counter` | `0` (int, class-level) | Monotonically decreasing counter for ordering user-specified fields. |
| `auto_creation_counter` | `-1` (int, class-level) | Counter for auto-created fields; decremented on each use. |
| `default_validators` | `[]` (list) | Default set of validators (empty). |
| `default_error_messages` | `dict` with keys `'invalid_choice'`, `'null'`, `'blank'`, `'unique_for_date'` — all values are lazy-translated strings. | Error message templates. |
| `system_check_deprecated_details` | `None` or `dict` | Details for deprecation system checks. |
| `system_check_removed_details` | `None` or `dict` | Details for removal system checks. |
| `hidden` | `False` (bool) | Field flag. |
| `many_to_many` | `None` | Field flag. |
| `many_to_one` | `None` | Field flag. |
| `one_to_many` | `None` | Field flag. |
| `one_to_one` | `None` | Field flag. |
| `related_model` | `None` | Field flag. |
| `descriptor_class` | `DeferredAttribute` | The descriptor class used to store the field value on model instances. |
| `description` | `property(_description)` | Returns a lazy-translated string `"Field of type: %(field_type)s"` where `% (field_type)s` is substituted with `self.__class__.__name__`. |

### Instance Attributes (set in `__init__`)

Set by `__init__`: `name`, `verbose_name`, `_verbose_name`, `primary_key`, `max_length`, `_unique`, `blank`, `null`, `remote_field`, `is_relation`, `default`, `editable`, `serialize`, `unique_for_date`, `unique_for_month`, `unique_for_year`, `choices`, `help_text`, `db_index`, `db_column`, `_db_tablespace`, `auto_created`, `creation_counter` (instance), `_validators`, `_error_messages`, `error_messages`.

### `__init__(self, verbose_name=None, name=None, primary_key=False, max_length=None, unique=False, blank=False, null=False, db_index=False, rel=None, default=NOT_PROVIDED, editable=True, serialize=True, unique_for_date=None, unique_for_month=None, unique_for_year=None, choices=None, help_text='', db_column=None, db_tablespace=None, auto_created=False, validators=(), error_messages=None)`

1. Sets `self.name = name`.
2. Stores `verbose_name` in both `self.verbose_name` and `self._verbose_name` (the latter for deconstruction).
3. Sets `primary_key`, `max_length`, `_unique`, `blank`, `null`, `remote_field = rel`, `is_relation = remote_field is not None`, `default`, `editable`, `serialize`, `unique_for_date/month/year`.
4. If `choices` is an instance of `collections.abc.Iterator`, converts it to a list. Stores in `self.choices`.
5. Sets `help_text`, `db_index`, `db_column`, `_db_tablespace`, `auto_created`.
6. **Creation counter**: if `auto_created`, sets `self.creation_counter = Field.auto_creation_counter` and decrements the class-level counter; otherwise uses `Field.creation_counter` and increments it.
7. Stores `self._validators = list(validators)`.
8. Merges error messages: iterates over `__mro__` in reverse, collecting all `default_error_messages` dicts from each class, then updates with the passed `error_messages` dict (if any). Stores merged result in `self.error_messages` and original in `self._error_messages`.

### `__str__(self)` → str
If the field has a `model` attribute, returns `"{app_label}.{object_name}.{name}"`; otherwise delegates to `super().__str__()`.

### `__repr__(self)` → str
Returns `"<{module}.{qualname}: {name}>"` if `name` is set, else `"<{module}.{qualname}>"`.

### `check(self, **kwargs)` → list[CheckMessage]
Returns a list of check errors from: `_check_field_name()`, `_check_choices()`, `_check_db_index()`, `_check_null_allowed_for_primary_keys()`, `_check_backend_specific_checks(**kwargs)`, `_check_deprecation_details()`.

### `_check_field_name(self)` → list[CheckMessage]
Validates the field name: returns an error (`fields.E001`) if it ends with `'_'`; `fields.E002` if it contains `LOOKUP_SEP` (`'__'`); `fields.E003` if it equals `'pk'`. Otherwise returns `[]`.

### `_check_choices(self)` → list[CheckMessage]
Validates the `choices` attribute:
- If falsy, returns `[]`.
- Defines inner helper `is_value(value, accept_promise=True)`: returns True if value is a `str`, `Promise` (when `accept_promise=True`), or not iterable.
- If `self.choices` itself fails `is_value(choices, accept_promise=False)`, returns error `fields.E004`.
- Iterates over each element of `choices`: tries to unpack as `(group_name, group_choices)`. If that fails (not a pair), treats it as flat `[value, human_name]`. Validates that all values and names are valid. Special-cases single-element string choices like `['ab']` which break validation.
- If all groups pass, returns `[]`; otherwise returns error `fields.E005`.

### `_check_db_index(self)` → list[CheckMessage]
Returns error `fields.E006` if `self.db_index` is not in `(None, True, False)`. Otherwise `[]`.

### `_check_null_allowed_for_primary_keys(self)` → list[CheckMessage]
If `primary_key and null` and the current connection does **not** interpret empty strings as nulls (checked via `connection.features.interprets_empty_strings_as_nulls`), returns error `fields.E007` with hint. Otherwise `[]`.

### `_check_backend_specific_checks(self, **kwargs)` → list[CheckMessage]
For each database in `connections`, if `router.allow_migrate(db, app_label, model_name)` is True, delegates to `connections[db].validation.check_field(self, **kwargs)`. Returns `[]` if no databases match.

### `_check_validators(self)` → list[CheckMessage]
Iterates over `self.validators`; for each non-callable validator, returns error `fields.E008` with a hint showing the index and repr.

### `_check_deprecation_details(self)` → list[CheckMessage]
If `system_check_removed_details` is not None, returns an Error (`id='fields.EXXX'`) using its `'msg'`, `'hint'`, `'id'`. If `system_check_deprecated_details` is not None, returns a Warning (`id='fields.WXXX'`). Otherwise `[]`.

### `get_col(self, alias, output_field=None)` → Col
If `output_field` is None, sets it to `self`. If `alias != self.model._meta.db_table` or `output_field != self`, imports and returns `Col(alias, self, output_field)`. Otherwise returns `self.cached_col`.

### `cached_col` (property via `@cached_property`) → Col
Returns `Col(self.model._meta.db_table, self)`.

### `select_format(self, compiler, sql, params)` → tuple[str, list]
Default: returns `(sql, params)`. Overridden by GIS fields.

### `deconstruct(self)` → tuple[str, str, list, dict]
Returns a 4-tuple `(name, path, args, kwargs)` for migration serialization:
1. Builds `keywords` dict from `possibles`: a mapping of parameter names to their default values (`None`, `False`, `NOT_PROVIDED`, `''`, `[]`). Maps attribute overrides: `_unique→unique`, `_error_messages→error_messages`, `_validators→validators`, `_verbose_name→verbose_name`, `_db_tablespace→db_tablespace`.
2. For each parameter, gets the actual value (using override mapping). If name is `"choices"` and value is iterable, converts to list. Compares: for `{"choices", "validators"}`, uses `!=`; for all others, uses `is not`. Adds non-default values to `keywords`.
3. Computes import path from module + qualname, shortening known prefixes (`django.db.models.fields.related`, `files`, `proxy`, general `fields`) down to `django.db.models`.
4. Returns `(self.name, path, [], keywords)`.

### `clone(self)` → Field
Calls `deconstruct()` and instantiates a new copy via `self.__class__(*args, **kwargs)`. Does not preserve class attachments.

### `__eq__(self, other)` → bool
If `other` is a `Field`, compares `creation_counter`; else returns `NotImplemented`.

### `__lt__(self, other)` → bool
If `other` is a `Field`, compares `creation_counter <`; else `NotImplemented`.

### `__hash__(self)` → int
Returns `hash(self.creation_counter)`.

### `__deepcopy__(self, memodict)` → Field
Creates a shallow copy via `copy.copy(self)`. If `remote_field` exists, copies it and fixes the back-reference if needed. Stores in `memodict` and returns.

### `__copy__(self)` → Field
Creates an `Empty()` instance, sets its class to `self.__class__`, copies `__dict__`, and returns it (avoids `__reduce__`).

### `__reduce__(self)` → tuple
If the field has no `model` attribute: returns `(_empty, (self.__class__,), state)` where `state = self.__dict__.copy()` with `_get_default` removed. If attached to a model: returns `(_load_field, (app_label, object_name, name))`.

### `get_pk_value_on_save(self, instance)` → int|None
If the field has a default, calls `self.get_default()`. Otherwise returns `None`. Called when saving instances without a PK.

### `to_python(self, value)` → any
Identity function: returns `value` unchanged. Subclasses override. Raises `ValidationError` on conversion failure.

### `validators` (property via `@cached_property`) → list[Validator]
Returns `[*self.default_validators, *self._validators]`.

### `run_validators(self, value)`
If `value in self.empty_values`, returns early. Otherwise iterates over validators; for each, calls it and catches `ValidationError`, remapping the error message if the code matches a key in `self.error_messages`. Extends an errors list. If non-empty, raises `ValidationError(errors)`.

### `validate(self, value, model_instance)`
If not editable, returns early. If choices are defined: iterates over them (handling optgroups), returns on first match; otherwise raises `invalid_choice` ValidationError. If `value is None and not self.null`, raises `null` error. If not blank and value in empty values, raises `blank` error.

### `clean(self, value, model_instance)` → any
Calls `to_python(value)`, then `validate()`, then `run_validators()`. Returns the converted value. Propagates all validation errors.

### `db_type_parameters(self, connection)` → DictWrapper
Returns a `DictWrapper(self.__dict__, connection.ops.quote_name, 'qn_')`.

### `db_check(self, connection)` → str|None
Builds data from `db_type_parameters()`. Looks up `connection.data_type_check_constraints[self.get_internal_type()]` and formats with the data dict. Returns `None` on KeyError.

### `db_type(self, connection)` → str|None
Looks up `connection.data_types[self.get_internal_type()]`, formats with db type parameters. Returns `None` on KeyError.

### `rel_db_type(self, connection)` → str
Returns `self.db_type(connection)`. Used by ForeignKey/OneToOneField to determine their column type.

### `cast_db_type(self, connection)` → str
Looks up `connection.ops.cast_data_types[self.get_internal_type()]`; if found, formats with db type parameters; otherwise returns `self.db_type(connection)`.

### `db_parameters(self, connection)` → dict
Returns `{"type": self.db_type(connection), "check": self.db_check(connection)}`.

### `db_type_suffix(self, connection)` → str|None
Looks up `connection.data_types_suffix[self.get_internal_type()]`.

### `get_db_converters(self, connection)` → list[callable]
If the field has a `from_db_value` method, returns `[self.from_db_value]`; else `[]`.

### `unique` (property) → bool
Returns `self._unique or self.primary_key`.

### `db_tablespace` (property) → str
Returns `self._db_tablespace or settings.DEFAULT_INDEX_TABLESPACE`.

### `set_attributes_from_name(self, name)`
Sets `self.name = name or self.name`. Calls `get_attname_column()` to set `attname` and `column`. Sets `concrete = column is not None`. If verbose_name is None and name exists, sets it to `name.replace('_', ' ')`.

### `contribute_to_class(self, cls, name, private_only=False)`
Calls `set_attributes_from_name(name)`, sets `self.model = cls`, calls `cls._meta.add_field(self, private=private_only)`. If column is set and the attribute doesn't already exist on the class (to avoid overriding classmethods), sets `setattr(cls, self.attname, self.descriptor_class(self))`. If choices are defined, sets a partial method `get_{name}_display` on the class.

### `get_filter_kwargs_for_object(self, obj)` → dict
Returns `{self.name: getattr(obj, self.attname)}`.

### `get_attname(self)` → str
Returns `self.name`.

### `get_attname_column(self)` → tuple[str, str]
Returns `(attname, column)` where `column = self.db_column or attname`.

### `get_internal_type(self)` → str
Returns `self.__class__.__name__`.

### `pre_save(self, model_instance, add)` → any
Returns `getattr(model_instance, self.attname)`. Subclasses override for auto_now/auto_now_add.

### `get_prep_value(self, value)` → any
If value is a `Promise`, casts it via `_proxy____cast()`. Returns the (possibly cast) value.

### `get_db_prep_value(self, value, connection, prepared=False)` → any
If not prepared, calls `self.get_prep_value(value)`. Returns the value as-is.

### `get_db_prep_save(self, value, connection)` → any
Returns `self.get_db_prep_value(value, connection=connection, prepared=False)`.

### `has_default(self)` → bool
Returns `self.default is not NOT_PROVIDED`.

### `get_default(self)` → any
Returns `self._get_default()`.

### `_get_default` (property via `@cached_property`) → callable
If the field has a default: if callable, returns it; otherwise returns `lambda: self.default`. If no default but `not empty_strings_allowed or (null and not connection.features.interprets_empty_strings_as_nulls)`, returns `return_None`; else returns `str` (the empty-string getter).

### `get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH, limit_choices_to=None, ordering=())` → list[tuple]
If choices are defined: converts to list; if include_blank and no blank already defined in flatchoices, prepends `blank_choice`; returns. Otherwise (relation-based): gets the related model, applies `limit_choices_to`, orders by `ordering`, builds a choice func from the remote field's related field attname or `'pk'`, and returns `[(*choice_func(x), str(x)) for x in qs]` optionally prepended with `blank_choice`.

### `value_to_string(self, obj)` → str
Returns `str(self.value_from_object(obj))`.

### `_get_flatchoices(self)` → list[tuple] (property via `@cached_property`)
If choices is None, returns `[]`. Otherwise flattens grouped choices: for each `(choice, value)`, if value is a list/tuple (optgroup), extends flat with its items; otherwise appends the pair.

### `flatchoices` (property) → list[tuple]
Returns `_get_flatchoices()`.

### `save_form_data(self, instance, data)`
Sets `setattr(instance, self.name, data)`.

### `formfield(self, form_class=None, choices_form_class=None, **kwargs)` → forms.Field
Builds defaults: `required = not self.blank`, `label = capfirst(self.verbose_name)`, `help_text`. If has default: sets `initial` (calling it if callable, else calling `get_default()`), and `show_hidden_initial=True` if callable. If choices are defined: sets include_blank logic, calls `get_choices()`, sets `coerce=self.to_python`, sets `empty_value=None` if null, selects form_class (`choices_form_class` or `forms.TypedChoiceField`). Strips kwargs keys not understood by TypedChoiceField. Default form_class is `forms.CharField`. Returns the instantiated form field.

### `value_from_object(self, obj)` → any
Returns `getattr(obj, self.attname)`.

---

## `class BooleanField(Field)`

- **Class attrs**: `empty_strings_allowed = False`; `default_error_messages = {'invalid': '…must be either True or False.', 'invalid_nullable': '…must be either True, False, or None.'}`; `description = "Boolean (Either True or False)"`.
- **`get_internal_type()`** → `"BooleanField"`.
- **`to_python(self, value)`**: If null and value in empty_values, returns None. If already True/False, returns `bool(value)`. Converts `'t'`, `'True'`, `'1'` to True; `'f'`, `'False'`, `'0'` to False. Otherwise raises ValidationError (using `'invalid_nullable'` if null else `'invalid'`).
- **`get_prep_value(self, value)`**: Calls parent's `get_prep_value`; if None returns None; else calls `to_python(value)`.
- **`formfield(self, **kwargs)`**: If choices defined: sets include_blank logic and uses `get_choices()`. Else: selects `forms.NullBooleanField` if null else `forms.BooleanField`, with `required=False`. Merges defaults with kwargs.

---

## `class CharField(Field)`

- **Class attrs**: `description = "String (up to %(max_length)s)"`.
- **`__init__(self, *args, **kwargs)`**: Calls parent init; appends `validators.MaxLengthValidator(self.max_length)` to validators list.
- **`check(self, **kwargs)`**: Extends parent check with `_check_max_length_attribute()`.
- **`_check_max_length_attribute(self, **kwargs)`**: Returns error `fields.E120` if max_length is None; `fields.E121` if not a positive int (or is bool); else `[]`.
- **`cast_db_type(self, connection)`**: If max_length is None, returns `connection.ops.cast_char_field_without_max_length`; else parent.
- **`get_internal_type()`** → `"CharField"`.
- **`to_python(self, value)`**: Returns value if str or None; else `str(value)`.
- **`get_prep_value(self, value)`**: Calls parent prep; returns `to_python(value)`.
- **`formfield(self, **kwargs)`**: Sets `max_length`; if null and connection doesn't interpret empty strings as nulls, sets `empty_value=None`. Merges with kwargs.

---

## `class CommaSeparatedIntegerField(CharField)`

- **Class attrs**: `default_validators = [validators.validate_comma_separated_integer_list]`; `description = "Comma-separated integers"`; `system_check_removed_details = {'msg': '…removed except for support in historical migrations.', 'hint': 'Use CharField(validators=[validate_comma_separated_integer_list]) instead.', 'id': 'fields.E901'}`.
- No methods overridden beyond class attributes (deprecated field).

---

## `class DateTimeCheckMixin`

### `check(self, **kwargs)` → list[CheckMessage]
Returns parent check + `_check_mutually_exclusive_options()` + `_check_fix_default_value()`.

### `_check_mutually_exclusive_options(self)` → list[CheckMessage]
Checks that at most one of `auto_now_add`, `auto_now`, and `has_default()` is enabled. If more than one, returns error `fields.E160`; else `[]`.

### `_check_fix_default_value(self)` → list[CheckMessage]
Returns `[]` (abstract; overridden by subclasses).

---

## `class DateField(DateTimeCheckMixin, Field)`

- **Class attrs**: `empty_strings_allowed = False`; `default_error_messages = {'invalid': '…YYYY-MM-DD format.', 'invalid_date': '…correct format but invalid date.'}`; `description = "Date (without time)"`.
- **`__init__(self, verbose_name=None, name=None, auto_now=False, auto_now_add=False, **kwargs)`**: Sets `auto_now`, `auto_now_add`; if either is True, sets `editable=False` and `blank=True` in kwargs. Calls parent init.
- **`_check_fix_default_value(self)`**: If no default, returns `[]`. Compares the default value against current date (within ±1 day). Normalizes aware datetimes to naive UTC before comparing. Returns warning `fields.W161` if within range; else `[]`.
- **`deconstruct(self)`**: Calls parent deconstruct; adds `auto_now`/`auto_now_add` kwargs if True; removes `editable` and `blank` if either auto flag is set.
- **`get_internal_type()`** → `"DateField"`.
- **`to_python(self, value)`**: None→None. datetime→date (converting aware to default timezone first). date→as-is. String: tries `parse_date`; on ValueError raises `invalid_date`. On parse failure raises `invalid`.
- **`pre_save(self, model_instance, add)`**: If auto_now or (auto_now_add and add), sets `datetime.date.today()`; else parent.
- **`contribute_to_class(self, cls, name, **kwargs)`**: Calls parent; if not null, registers `get_next_by_{name}` and `get_previous_by_{name}` partial methods on the class.
- **`get_prep_value(self, value)`**: Calls parent prep; returns `to_python(value)`.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If not prepared, calls get_prep_value; returns `connection.ops.adapt_datefield_value(value)`.
- **`value_to_string(self, obj)`**: Returns `val.isoformat()` or `''` if None.
- **`formfield(self, **kwargs)`**: Sets `form_class=forms.DateField`.

---

## `class DateTimeField(DateField)`

- **Class attrs**: `empty_strings_allowed = False`; `default_error_messages = {'invalid': '…YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ] format.', 'invalid_date': '…correct YYYY-MM-DD but invalid date.', 'invalid_datetime': '…correct datetime format but invalid.'}`; `description = "Date (with time)"`.
- **`__init__`** inherited from DateField.
- **`_check_fix_default_value(self)`**: Similar to DateField but uses ±10 second window and handles both datetime and date defaults by converting dates to midnight datetimes for comparison. Returns warning `fields.W161`.
- **`get_internal_type()`** → `"DateTimeField"`.
- **`to_python(self, value)`**: None→None. datetime→as-is. date→converts to datetime (with timezone awareness if USE_TZ). String: tries `parse_datetime`; on failure tries `parse_date` and converts to midnight datetime; raises appropriate errors.
- **`pre_save(self, model_instance, add)`**: If auto_now or (auto_now_add and add), sets `timezone.now()`; else parent.
- **`contribute_to_class`** inherited from DateField.
- **`get_prep_value(self, value)`**: Calls parent prep + to_python; if USE_TZ and naive datetime, warns and makes aware with default timezone.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If not prepared, calls get_prep_value; returns `connection.ops.adapt_datetimefield_value(value)`.
- **`value_to_string(self, obj)`**: Returns `val.isoformat()` or `''` if None.
- **`formfield(self, **kwargs)`**: Sets `form_class=forms.DateTimeField`.

---

## `class DecimalField(Field)`

- **Class attrs**: `empty_strings_allowed = False`; `default_error_messages = {'invalid': '…must be a decimal number.'}`; `description = "Decimal number"`.
- **`__init__(self, verbose_name=None, name=None, max_digits=None, decimal_places=None, **kwargs)`**: Sets `max_digits`, `decimal_places`; calls parent init.
- **`check(self, **kwargs)`**: Parent check + `_check_decimal_places()` + `_check_max_digits()`. If no digit errors, also runs `_check_decimal_places_and_max_digits()`.
- **`_check_decimal_places(self)`**: Returns error `fields.E130` if not defined; `fields.E131` if negative or non-int; else `[]`.
- **`_check_max_digits(self)`**: Returns error `fields.E132` if not defined; `fields.E133` if ≤ 0 or non-int; else `[]`.
- **`_check_decimal_places_and_max_digits(self, **kwargs)`**: Returns error `fields.E134` if decimal_places > max_digits; else `[]`.
- **`validators`** (cached_property): Parent validators + `[validators.DecimalValidator(self.max_digits, self.decimal_places)]`.
- **`context`** (cached_property): `decimal.Context(prec=self.max_digits)`.
- **`deconstruct(self)`**: Adds `max_digits`/`decimal_places` kwargs if not None.
- **`get_internal_type()`** → `"DecimalField"`.
- **`to_python(self, value)`**: None→None. float→uses `context.create_decimal_from_float(value)`. Otherwise tries `decimal.Decimal(value)`; on InvalidOperation raises ValidationError.
- **`get_db_prep_save(self, value, connection)`**: Returns `connection.ops.adapt_decimalfield_value(self.to_python(value), self.max_digits, self.decimal_places)`.
- **`get_prep_value(self, value)`**: Calls parent prep; returns `to_python(value)`.
- **`formfield(self, **kwargs)`**: Sets `max_digits`, `decimal_places`, `form_class=forms.DecimalField`.

---

## `class DurationField(Field)`

- **Class attrs**: `empty_strings_allowed = False`; `default_error_messages = {'invalid': '…[DD] [[HH:]MM:]ss[.uuuuuu] format.'}`; `description = "Duration"`.
- **`get_internal_type()`** → `"DurationField"`.
- **`to_python(self, value)`**: None→None. timedelta→as-is. String: tries `parse_duration`; on failure or None result raises ValidationError.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If native duration field supported, returns as-is. If None, returns None. Otherwise returns `duration_microseconds(value)`.
- **`get_db_converters(self, connection)`**: If no native support, adds `connection.ops.convert_durationfield_value`; then extends parent converters.
- **`value_to_string(self, obj)`**: Returns `duration_string(val)` or `''` if None.
- **`formfield(self, **kwargs)`**: Sets `form_class=forms.DurationField`.

---

## `class EmailField(CharField)`

- **Class attrs**: `default_validators = [validators.validate_email]`; `description = "Email address"`.
- **`__init__(self, *args, **kwargs)`**: Defaults `max_length=254`; calls parent init.
- **`deconstruct(self)`**: Calls parent; does NOT exclude max_length (to allow future default change).
- **`formfield(self, **kwargs)`**: Sets `form_class=forms.EmailField`.

---

## `class FilePathField(Field)`

- **Class attrs**: `description = "File path"`.
- **`__init__(self, verbose_name=None, name=None, path='', match=None, recursive=False, allow_files=True, allow_folders=False, **kwargs)`**: Sets all custom params; defaults `max_length=100`; calls parent init.
- **`check(self, **kwargs)`**: Parent + `_check_allowing_files_or_folders()`.
- **`_check_allowing_files_or_folders(self, **kwargs)`**: Returns error `fields.E140` if both allow_files and allow_folders are False; else `[]`.
- **`deconstruct(self)`**: Adds non-default kwargs (`path`, `match`, `recursive`, `allow_files`, `allow_folders`); removes `max_length` if it equals 100.
- **`get_prep_value(self, value)`**: Calls parent prep; returns None or `str(value)`.
- **`formfield(self, **kwargs)`**: Sets all custom params (calling `self.path()` if callable), `form_class=forms.FilePathField`, allow_files, allow_folders.
- **`get_internal_type()`** → `"FilePathField"`.

---

## `class FloatField(Field)`

- **Class attrs**: `empty_strings_allowed = False`; `default_error_messages = {'invalid': '…must be a float.'}`; `description = "Floating point number"`.
- **`get_prep_value(self, value)`**: Calls parent prep; if None returns None; else tries `float(value)`, re-raising with a name-specific message on failure.
- **`get_internal_type()`** → `"FloatField"`.
- **`to_python(self, value)`**: None→None; tries `float(value)`; raises ValidationError on failure.
- **`formfield(self, **kwargs)`**: Sets `form_class=forms.FloatField`.

---

## `class IntegerField(Field)`

- **Class attrs**: `empty_strings_allowed = False`; `default_error_messages = {'invalid': '…must be an integer.'}`; `description = "Integer"`.
- **`check(self, **kwargs)`**: Parent + `_check_max_length_warning()`.
- **`_check_max_length_warning(self, **kwargs)`**: Returns warning `fields.W122` if max_length is not None (since it's ignored for integer fields); else `[]`.
- **`validators`** (cached_property): Parent validators + optionally appends `MinValueValidator(min_value)` and/or `MaxValueValidator(max_value)` from `connection.ops.integer_field_range(internal_type)`, only if no existing validator already covers the range.
- **`get_prep_value(self, value)`**: Calls parent prep; if None returns None; else tries `int(value)`, re-raising with name-specific message on failure.
- **`get_internal_type()`** → `"IntegerField"`.
- **`to_python(self, value)`**: None→None; tries `int(value)`; raises ValidationError on failure.
- **`formfield(self, **kwargs)`**: Sets `form_class=forms.IntegerField`.

---

## `class BigIntegerField(IntegerField)`

- **Class attrs**: `description = "Big (8 byte) integer"`; `MAX_BIGINT = 9223372036854775807`.
- **`get_internal_type()`** → `"BigIntegerField"`.
- **`formfield(self, **kwargs)`**: Sets `min_value=-MAX_BIGINT - 1`, `max_value=MAX_BIGINT`.

---

## `class IPAddressField(Field)` (deprecated)

- **Class attrs**: `empty_strings_allowed = False`; `description = "IPv4 address"`; `system_check_removed_details = {'msg': '…removed except for support in historical migrations.', 'hint': 'Use GenericIPAddressField instead.', 'id': 'fields.E900'}`.
- **`__init__(self, *args, **kwargs)`**: Sets `max_length=15`; calls parent init.
- **`deconstruct(self)`**: Calls parent; removes `max_length`.
- **`get_prep_value(self, value)`**: Calls parent prep; returns None or `str(value)`.
- **`get_internal_type()`** → `"IPAddressField"`.

---

## `class GenericIPAddressField(Field)`

- **Class attrs**: `empty_strings_allowed = False`; `description = "IP address"`; `default_error_messages = {}` (populated in `__init__`).
- **`__init__(self, verbose_name=None, name=None, protocol='both', unpack_ipv4=False, *args, **kwargs)`**: Sets `unpack_ipv4`, `protocol`; calls `validators.ip_address_validators(protocol, unpack_ipv4)` to set `default_validators` and the `'invalid'` error message; defaults `max_length=39`; calls parent init.
- **`check(self, **kwargs)`**: Parent + `_check_blank_and_null_values()`.
- **`_check_blank_and_null_values(self, **kwargs)`**: Returns error `fields.E150` if blank=True and null=False; else `[]`.
- **`deconstruct(self)`**: Adds non-default kwargs (`unpack_ipv4`, `protocol`); removes `max_length` if 39.
- **`get_internal_type()`** → `"GenericIPAddressField"`.
- **`to_python(self, value)`**: None→None; converts to str if needed; strips whitespace; if contains `:`, calls `clean_ipv6_address(value, self.unpack_ipv4, error_msg)`; else returns as-is.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If not prepared, calls get_prep_value; returns `connection.ops.adapt_ipaddressfield_value(value)`.
- **`get_prep_value(self, value)`**: Calls parent prep; if None returns None; if contains `:`, tries `clean_ipv6_address`; on failure falls through to `str(value)`.
- **`formfield(self, **kwargs)`**: Sets `protocol`, `form_class=forms.GenericIPAddressField`.

---

## `class NullBooleanField(BooleanField)`

- **Class attrs**: `default_error_messages = {'invalid': '…None, True or False.', 'invalid_nullable': '…None, True or False.'}`; `description = "Boolean (Either True, False or None)"`.
- **`__init__(self, *args, **kwargs)`**: Forces `null=True`, `blank=True`; calls parent init.
- **`deconstruct(self)`**: Calls parent; removes `null` and `blank`.
- **`get_internal_type()`** → `"NullBooleanField"`.

---

## `class PositiveIntegerRelDbTypeMixin`

### `rel_db_type(self, connection)` → str
If `connection.features.related_fields_match_type`, returns `self.db_type(connection)`; else returns `IntegerField().db_type(connection=connection)`. Used by PositiveIntegerField and PositiveSmallIntegerField.

---

## `class PositiveIntegerField(PositiveIntegerRelDbTypeMixin, IntegerField)`

- **Class attrs**: `description = "Positive integer"`.
- **`get_internal_type()`** → `"PositiveIntegerField"`.
- **`formfield(self, **kwargs)`**: Sets `min_value=0`.

---

## `class PositiveSmallIntegerField(PositiveIntegerRelDbTypeMixin, IntegerField)`

- **Class attrs**: `description = "Positive small integer"`.
- **`get_internal_type()`** → `"PositiveSmallIntegerField"`.
- **`formfield(self, **kwargs)`**: Sets `min_value=0`.

---

## `class SlugField(CharField)`

- **Class attrs**: `default_validators = [validators.validate_slug]`; `description = "Slug (up to %(max_length)s)"`.
- **`__init__(self, *args, max_length=50, db_index=True, allow_unicode=False, **kwargs)`**: Sets `allow_unicode`; if True, replaces default_validators with `[validators.validate_unicode_slug]`; calls parent init with `max_length`, `db_index`.
- **`deconstruct(self)`**: Removes `max_length` if 50; keeps `db_index` only if False; adds `allow_unicode` if not False.
- **`get_internal_type()`** → `"SlugField"`.
- **`formfield(self, **kwargs)`**: Sets `form_class=forms.SlugField`, `allow_unicode`.

---

## `class SmallIntegerField(IntegerField)`

- **Class attrs**: `description = "Small integer"`.
- **`get_internal_type()`** → `"SmallIntegerField"`.

---

## `class TextField(Field)`

- **Class attrs**: `description = "Text"`.
- **`get_internal_type()`** → `"TextField"`.
- **`to_python(self, value)`**: Returns value if str or None; else `str(value)`.
- **`get_prep_value(self, value)`**: Calls parent prep; returns `to_python(value)`.
- **`formfield(self, **kwargs)`**: Sets `max_length`; adds `'widget': forms.Textarea` unless choices are defined.

---

## `class TimeField(DateTimeCheckMixin, Field)`

- **Class attrs**: `empty_strings_allowed = False`; `default_error_messages = {'invalid': '…HH:MM[:ss[.uuuuuu]] format.', 'invalid_time': '…correct format but invalid time.'}`; `description = "Time"`.
- **`__init__(self, verbose_name=None, name=None, auto_now=False, auto_now_add=False, **kwargs)`**: Sets `auto_now`, `auto_now_add`; if either True, sets `editable=False`, `blank=True`; calls parent init.
- **`_check_fix_default_value(self)`**: If no default, returns `[]`. Compares default against current time (±10 seconds). Handles datetime and time defaults by combining with today's date for comparison. Returns warning `fields.W161` if within range; else `[]`.
- **`deconstruct(self)`**: Adds `auto_now`/`auto_now_add` kwargs if not False; removes `blank` and `editable` if either auto flag is set.
- **`get_internal_type()`** → `"TimeField"`.
- **`to_python(self, value)`**: None→None. time→as-is. datetime→returns `.time()`. String: tries `parse_time`; on ValueError raises `invalid_time`; else raises `invalid`.
- **`pre_save(self, model_instance, add)`**: If auto_now or (auto_now_add and add), sets `datetime.datetime.now().time()`; else parent.
- **`get_prep_value(self, value)`**: Calls parent prep; returns `to_python(value)`.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If not prepared, calls get_prep_value; returns `connection.ops.adapt_timefield_value(value)`.
- **`value_to_string(self, obj)`**: Returns `val.isoformat()` or `''` if None.
- **`formfield(self, **kwargs)`**: Sets `form_class=forms.TimeField`.

---

## `class URLField(CharField)`

- **Class attrs**: `default_validators = [validators.URLValidator()]`; `description = "URL"`.
- **`__init__(self, verbose_name=None, name=None, **kwargs)`**: Defaults `max_length=200`; calls parent init.
- **`deconstruct(self)`**: Calls parent; removes `max_length` if 200.
- **`formfield(self, **kwargs)`**: Sets `form_class=forms.URLField`.

---

## `class BinaryField(Field)`

- **Class attrs**: `description = "Raw binary data"`; `empty_values = [None, b'']`.
- **`__init__(self, *args, **kwargs)`**: Defaults `editable=False`; calls parent init. If max_length is set, appends `MaxLengthValidator(max_length)`.
- **`check(self, **kwargs)`**: Parent + `_check_str_default_value()`.
- **`_check_str_default_value(self, **kwargs)`**: Returns error `fields.E170` if has default and it's a str; else `[]`.
- **`deconstruct(self)`**: Calls parent; removes `editable` unless True.
- **`get_internal_type()`** → `"BinaryField"`.
- **`get_placeholder(self, value, compiler, connection)`**: Returns `connection.ops.binary_placeholder_sql(value)`.
- **`get_default(self)`**: If has default and not callable, returns it directly; else calls parent get_default; if result is `''`, returns `b''`; else returns the result.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: Calls parent prep; if not None, wraps with `connection.Database.Binary(value)`.
- **`value_to_string(self, obj)`**: Returns base64-encoded string of the binary value via `b64encode(val).decode('ascii')`.
- **`to_python(self, value)`**: If str, decodes from base64 and returns a `memoryview`; else returns as-is.

---

## `class UUIDField(Field)`

- **Class attrs**: `default_error_messages = {'invalid': '…not a valid UUID.'}`; `description = "Universally unique identifier"`; `empty_strings_allowed = False`.
- **`__init__(self, verbose_name=None, **kwargs)`**: Sets `max_length=32`; calls parent init.
- **`deconstruct(self)`**: Calls parent; removes `max_length`.
- **`get_internal_type()`** → `"UUIDField"`.
- **`get_prep_value(self, value)`**: Calls parent prep; returns `to_python(value)`.
- **`get_db_prep_value(self, value, connection, prepared=False)`**: If None, returns None. If not already a uuid.UUID, calls `to_python()`. If native UUID supported, returns as-is; else returns `.hex`.
- **`to_python(self, value)`**: If not None and not already uuid.UUID: determines input format (`'int'` if int, `'hex'` otherwise); tries `uuid.UUID(**{input_form: value})`; on failure raises ValidationError.

---

## `class AutoFieldMixin`

### `__init__(self, *args, **kwargs)`
Defaults `blank=True`; calls parent init.

### `check(self, **kwargs)` → list[CheckMessage]
Parent check + `_check_primary_key()`.

### `_check_primary_key(self, **kwargs)` → list[CheckMessage]
Returns error `fields.E100` if `primary_key` is False; else `[]`.

### `deconstruct(self)`
Calls parent deconstruct; removes `blank`; sets `primary_key=True`.

### `validate(self, value, model_instance)`
No-op (always passes).

### `get_db_prep_value(self, value, connection, prepared=False)`
If not prepared, calls get_prep_value then `connection.ops.validate_autopk_value(value)`. Returns the result.

### `get_prep_value(self, value)`
Returns value if it's an `OuterRef` expression; else parent prep.

### `contribute_to_class(self, cls, name, **kwargs)`
Asserts that `cls._meta.auto_field` is not already set (only one auto field per model). Calls parent contribute_to_class. Sets `cls._meta.auto_field = self`.

### `formfield(self, **kwargs)` → None
Always returns None (auto fields have no form representation).

---

## `class AutoFieldMeta(type)`

Metaclass for AutoField to maintain backward compatibility with isinstance checks.

- **`_subclasses`** (property): Returns `(BigAutoField, SmallAutoField)`.
- **`__instancecheck__(self, instance)`**: Returns True if instance is an instance of any subclass in `_subclasses` or passes the normal `super().__instancecheck__`.
- **`__subclasscheck__(self, subclass)`**: Returns True if subclass is in `_subclasses` or passes the normal `super().__subclasscheck__`.

---

## `class AutoField(AutoFieldMixin, IntegerField, metaclass=AutoFieldMeta)`

- **`get_internal_type()`** → `"AutoField"`.
- **`rel_db_type(self, connection)`**: Returns `IntegerField().db_type(connection=connection)`.

---

## `class BigAutoField(AutoFieldMixin, BigIntegerField)`

- **`get_internal_type()`** → `"BigAutoField"`.
- **`rel_db_type(self, connection)`**: Returns `BigIntegerField().db_type(connection=connection)`.

---

## `class SmallAutoField(AutoFieldMixin, SmallIntegerField)`

- **`get_internal_type()`** → `"SmallAutoField"`.
- **`rel_db_type(self, connection)`**: Returns `SmallIntegerField().db_type(connection=connection)`.

## django/db/models/fields/related_lookups.py
Here is the complete natural-language specification of `django/db/models/fields/related_lookups.py`:

---

## Module-Level Preamble

### Imports

```python
from django.db.models.lookups import (
    Exact, GreaterThan, GreaterThanOrEqual, In, IsNull, LessThan,
    LessThanOrEqual,
)
```

No other module-level constants or globals are defined. All symbols in the file are either a top-level function (`get_normalized_value`) or classes (`MultiColSource`, `RelatedIn`, `RelatedLookupMixin`, and five related lookup subclasses).

---

## Code Objects

### Function: `get_normalized_value(value, lhs)`

**Signature:** `(value: Any, lhs: MultiColSource | LookupColumn) → tuple`

**Logic:**
1. If `value` is an instance of `django.db.models.Model`:
   - Initialize an empty list `value_list`.
   - Retrieve the last entry from `lhs.output_field.get_path_info()` and extract its `target_fields`.
   - For each `source` in those target fields:
     - While `value` is not an instance of `source.model` **and** `source.remote_field` exists, descend into the related model by setting `source = source.remote_field.model._meta.get_field(source.remote_field.field_name)`.
     - Attempt to append `getattr(value, source.attname)` to `value_list`. If this raises `AttributeError`, immediately return `(value.pk,)` as a single-element tuple. This handles cases like filtering on a model instance where the related field is a OneToOneField whose target is the model's primary key.
   - Return `tuple(value_list)`.
2. If `value` is not already a `tuple`, return `(value,)`.
3. Otherwise, return `value` unchanged (it is already a tuple).

**Return:** A `tuple` of values suitable for use in multi-column or single-column lookups.

---

### Class: `MultiColSource`

**Attributes (set in `__init__`):**
- `contains_aggregate = False` — class-level boolean, always false.
- `self.targets` — list of field objects (target columns).
- `self.sources` — list of source field names.
- `self.field` — the related field object.
- `self.alias` — the table alias string.
- `self.output_field = self.field` — set in `__init__`, references `self.field`.

**Methods:**

#### `__init__(self, alias, targets, sources, field)`
Stores all four arguments as instance attributes and sets `output_field = field`.

#### `__repr__(self) → str`
Returns a string formatted as `"MultiColSource({alias}, {field})"`, using the class name dynamically.

#### `relabeled_clone(self, relabels: dict) → MultiColSource`
Creates and returns a new `MultiColSource` instance with the alias remapped via `relabels.get(self.alias, self.alias)` (identity if not present), while copying `targets`, `sources`, and `field` unchanged.

#### `get_lookup(self, lookup: str) → Lookup | None`
Delegates to `self.output_field.get_lookup(lookup)` and returns the result.

---

### Class: `RelatedIn(In)`

**Inheritance:** Extends `django.db.models.lookups.In`.

#### `get_prep_lookup(self)`

1. If `self.lhs` is **not** a `MultiColSource` **and** `self.rhs_is_direct_value()` returns true (i.e., the right-hand side is a direct Python value, not a subquery):
   - For each element in `self.rhs`, call `get_normalized_value(val, self.lhs)` and take its first element `[0]`. Replace `self.rhs` with this list of single-column normalized values.
   - If `self.lhs.output_field` has the attribute `get_path_info`:
     - Retrieve the deepest target field: `self.lhs.output_field.get_path_info()[-1].target_fields[-1]`.
     - Replace each element in `self.rhs` with that target field's `get_prep_value(v)` call, performing type validation/coercion.
2. Call and return `super().get_prep_lookup()`.

#### `as_sql(self, compiler, connection) → tuple[str, list]`

**Branch A — `isinstance(self.lhs, MultiColSource)` (multi-column lookup):**
1. Import `WhereNode`, `SubqueryConstraint`, `AND`, `OR` from `django.db.models.sql.where`.
2. Create a root `WhereNode(connector=OR)`.
3. **If** `self.rhs_is_direct_value()`:
   - Normalize each value in `self.rhs` via `get_normalized_value(value, self.lhs)`, producing a list of tuples.
   - For each normalized tuple `value`:
     - Create an inner `WhereNode()` (default AND connector).
     - Zip together `self.lhs.sources`, `self.lhs.targets`, and the individual values from `value`. For each triple `(source, target, val)`:
       - Get the `'exact'` lookup class for `target`.
       - Create a lookup instance: `lookup_class(target.get_col(self.lhs.alias, source), val)`.
       - Add this lookup to the inner node with connector `AND`.
     - Add the inner node to the root constraint with connector `OR`.
4. **Else** (rhs is not a direct value — it's a queryset/subquery):
   - Create a `SubqueryConstraint` using `self.lhs.alias`, `[target.column for target in self.lhs.targets]`, `[source.name for source in self.lhs.sources]`, and `self.rhs`.
   - Add this constraint to the root with connector `AND`.
5. Return `root_constraint.as_sql(compiler, connection)`.

**Branch B — single-column lookup (else):**
1. If `self.rhs` does **not** have attribute `has_select_fields` set to true **and** `self.lhs.field.target_field.primary_key` is falsy:
   - Call `self.rhs.clear_select_clause()`.
   - Determine the target field name: if `self.lhs.output_field.primary_key` is truthy **and** `self.lhs.output_field.model == self.rhs.model`, use `self.lhs.field.name`; otherwise, use `self.lhs.field.target_field.name`.
   - Call `self.rhs.add_fields([target_field], True)`.
2. Return `super().as_sql(compiler, connection)`.

---

### Class: `RelatedLookupMixin`

This mixin provides shared preprocessing and SQL generation logic for single-lookup related field comparisons (exact, less-than, greater-than, etc.). It is always mixed in as the **first** base class before a concrete lookup from `django.db.models.lookups`.

#### `get_prep_lookup(self)`

1. If `self.lhs` is **not** a `MultiColSource` **and** `self.rhs_is_direct_value()`:
   - Normalize `self.rhs` via `get_normalized_value(self.rhs, self.lhs)` and take its first element `[0]`. Replace `self.rhs` with this single value.
   - If `self.prepare_rhs` is truthy **and** `self.lhs.output_field` has the attribute `get_path_info`:
     - Retrieve the deepest target field: `self.lhs.output_field.get_path_info()[-1].target_fields[-1]`.
     - Replace `self.rhs` with that target field's `get_prep_value(self.rhs)`, performing type validation/coercion.
2. Call and return `super().get_prep_lookup()`.

#### `as_sql(self, compiler, connection) → tuple[str, list]`

**Branch A — `isinstance(self.lhs, MultiColSource)` (multi-column lookup):**
1. Assert that `self.rhs_is_direct_value()` is true.
2. Normalize `self.rhs` via `get_normalized_value(self.rhs, self.lhs)`, producing a tuple.
3. Import `WhereNode` and `AND` from `django.db.models.sql.where`.
4. Create a root `WhereNode()` (default AND connector).
5. Zip together `self.lhs.targets`, `self.lhs.sources`, and the normalized values in `self.rhs`. For each triple `(target, source, val)`:
   - Get the lookup class for this specific lookup name: `target.get_lookup(self.lookup_name)` (e.g., `'exact'`, `'lt'`, `'gt'`).
   - Create a lookup instance: `lookup_class(target.get_col(self.lhs.alias, source), val)`.
   - Add it to the root node with connector `AND`.
6. Return `root_constraint.as_sql(compiler, connection)`.

**Branch B — single-column lookup (else):**
- Return `super().as_sql(compiler, connection)` unchanged.

---

### Class: `RelatedExact(RelatedLookupMixin, Exact)`

No additional methods or attributes. Inherits all behavior from `RelatedLookupMixin` and `Exact`. Provides the `'exact'` lookup for related field comparisons on both single-column and multi-column sources.

---

### Class: `RelatedLessThan(RelatedLookupMixin, LessThan)`

No additional methods or attributes. Inherits all behavior from `RelatedLookupMixin` and `LessThan`. Provides the `'lt'` lookup for related field comparisons.

---

### Class: `RelatedGreaterThan(RelatedLookupMixin, GreaterThan)`

No additional methods or attributes. Inherits all behavior from `RelatedLookupMixin` and `GreaterThan`. Provides the `'gt'` lookup for related field comparisons.

---

### Class: `RelatedGreaterThanOrEqual(RelatedLookupMixin, GreaterThanOrEqual)`

No additional methods or attributes. Inherits all behavior from `RelatedLookupMixin` and `GreaterThanOrEqual`. Provides the `'gte'` lookup for related field comparisons.

---

### Class: `RelatedLessThanOrEqual(RelatedLookupMixin, LessThanOrEqual)`

No additional methods or attributes. Inherits all behavior from `RelatedLookupMixin` and `LessThanOrEqual`. Provides the `'lte'` lookup for related field comparisons.

---

### Class: `RelatedIsNull(RelatedLookupMixin, IsNull)`

No additional methods or attributes. Inherits all behavior from `RelatedLookupMixin` and `IsNull`. Provides the `'isnull'` lookup for related field null checks.

---

## Summary of Architecture

The file defines a hierarchy for Django ORM lookups on **related fields** (foreign keys, one-to-one relationships, etc.), with special handling for **multi-column sources** (e.g., composite foreign keys):

- **`MultiColSource`** wraps the left-hand side when it represents multiple database columns. It carries `targets`, `sources`, `field`, and `alias`.
- **`get_normalized_value()`** converts model instances or scalar values into tuples of column values suitable for comparison against multi-column sources.
- **`RelatedIn`** extends `In` to handle both single-column (`__in` on a FK) and multi-column (`__in` on a composite key) cases, building OR-combined equality constraints for direct values or delegating to `SubqueryConstraint` for subqueries.
- **`RelatedLookupMixin`** provides shared preprocessing (normalization + type coercion via the target field's `get_prep_value`) and multi-column SQL generation (AND-combined per-column lookups) for all non-IN comparison operators.
- The five concrete classes (`RelatedExact`, `RelatedLessThan`, `RelatedGreaterThan`, `RelatedGreaterThanOrEqual`, `RelatedLessThanOrEqual`, `RelatedIsNull`) are trivial mixins that combine `RelatedLookupMixin` with their respective base lookup class from `django.db.models.lookups`.

## django/db/models/sql/query.py
The complete natural-language specification of `django/db/models/sql/query.py` (2,357 lines) has been written to `/tmp/omp_desc_cujwyzph/spec_query.py.md`. Here's a summary of what it covers:

**Structure:**
1. **Imports** — All 46 import lines listed precisely with their exact module paths and names.
2. **Module-level constants & helpers** — `JoinInfo` namedtuple, plus 5 helper functions (`get_field_names_from_opts`, `get_children_from_q`, `get_order_dir`, `add_to_dict`, `is_reverse_o2o`).
3. **Class: `RawQuery`** — Full spec of all attributes and methods for raw SQL query execution (10 methods including `__init__`, `clone`, `chain`, `get_columns`, `__iter__`, `_execute_query`, etc.).
4. **Class: `Query(BaseExpression)`** — The main class, covering:
   - 3 class attributes (`alias_prefix`, `subq_aliases`, `compiler`)
   - ~35 instance attributes with exact types and defaults from `__init__`
   - 3 properties (`output_field`, `has_select_fields`, `base_table`)
   - 40+ methods including the full filter resolution pipeline (`build_filter`, `_add_q`, `split_exclude`), join management (`join`, `promote_joins`, `demote_joins`, `change_aliases`), annotation handling, grouping, slicing, and subquery generation.
5. **Class: `JoinPromoter`** — The join promotion/demotion engine for complex AND/OR filter conditions (3 methods).

Each method documents its exact signature, step-by-step implementation logic, control flow, return values, exceptions raised, and edge cases — sufficient for a code-generation AI to recreate the original file functionally.