## django/contrib/admin/utils.py
Now I have the complete file. Let me write the specification.

---

# Module Specification: `django/contrib/admin/utils.py`

## 1. Module-Level Preamble

### Imports

```python
import datetime
import decimal
import re
from collections import defaultdict

from django.core.exceptions import FieldDoesNotExist
from django.db import models, router
from django.db.models.constants import LOOKUP_SEP
from django.db.models.deletion import Collector
from django.forms.utils import pretty_name
from django.urls import NoReverseMatch, reverse
from django.utils import formats, timezone
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import ngettext, override as translation_override
```

### Constants & Globals

- **`QUOTE_MAP`**: `dict[int, str]` — A mapping from each byte value `i` in the bytes literal `b'":/_#?;@&=+$,"[]<>%\n\\'` to the string `'_%02X' % i`. Used by `quote()` for URL-safe character escaping.

- **`UNQUOTE_MAP`**: `dict[str, str]` — The inverse of `QUOTE_MAP`, built as `{v: chr(k) for k, v in QUOTE_MAP.items()}`. Maps encoded strings back to their original characters.

- **`UNQUOTE_RE`**: compiled `re.Pattern` — A regex created by `re.compile('_(?:%s)' % '|'.join([x[1:] for x in UNQUOTE_MAP]))`. Matches any `_XX` escape sequence (where `XX` is a two-digit hex code) for use with `unquote()`.

### Exception Classes

- **`FieldIsAForeignKeyColumnName(Exception)`**: Raised when a field name refers to a foreign key's attname (e.g., `<FK>_id`) rather than the FK field itself.

- **`NotRelationField(Exception)`**: Raised when a field does not support relation traversal via `get_path_info()`.

---

## 2. Code Objects

### Function: `lookup_needs_distinct(opts, lookup_path) -> bool`

**Signature:** `(opts: Options, lookup_path: str) -> bool`

**Logic:**
1. Split `lookup_path` by `LOOKUP_SEP` (typically `"__"`) into a list of field names.
2. Iterate over each `field_name`:
   - If `field_name == 'pk'`, replace it with `opts.pk.name`.
   - Attempt to retrieve the field via `opts.get_field(field_name)`.
     - If `FieldDoesNotExist` is raised, skip this lookup segment (it's a query filter, not a real field).
     - Otherwise:
       - If the field has `get_path_info()` (i.e., it is a relation), follow the relation chain by calling `field.get_path_info()`, updating `opts` to `path_info[-1].to_opts`.
       - If any path in that chain has `m2m == True`, return `True` immediately.
3. After iterating all segments without finding an m2m, return `False`.

**Return:** `True` if the lookup traverses a many-to-many relation (requiring `.distinct()`), else `False`.

---

### Function: `prepare_lookup_value(key, value) -> Any`

**Signature:** `(key: str, value: str) -> str | list[str] | bool`

**Logic:**
1. If `key.endswith('__in')`: split `value` by `','` into a list and return it.
2. Else if `key.endswith('__isnull')`: convert `value` to lowercase; return `True` if the lowercased value is not in `('', 'false', '0')`, else `False`.
3. Otherwise: return `value` unchanged.

**Return:** The prepared lookup value, possibly transformed into a list or boolean.

---

### Function: `quote(s) -> str | Any`

**Signature:** `(s: str | Any) -> str | Any`

**Logic:** If `s` is an instance of `str`, return `s.translate(QUOTE_MAP)` to escape problematic URL characters; otherwise return `s` unchanged.

**Return:** The quoted string, or the original value if not a string.

---

### Function: `unquote(s) -> str`

**Signature:** `(s: str) -> str`

**Logic:** Apply `UNQUOTE_RE.sub()` with a callback that replaces each matched `_XX` escape sequence by looking it up in `UNQUOTE_MAP`.

**Return:** The unquoted string.

---

### Function: `flatten(fields) -> list`

**Signature:** `(fields: Iterable[list | tuple | str]) -> list[str]`

**Logic:**
1. Initialize an empty list `flat`.
2. For each element in `fields`:
   - If it is a `list` or `tuple`, extend `flat` with its elements.
   - Otherwise, append the element directly to `flat`.
3. Return `flat`.

**Return:** A single-level flattened list of field names.

---

### Function: `flatten_fieldsets(fieldsets) -> list[str]`

**Signature:** `(fieldsets: Iterable[tuple[str, dict]]) -> list[str]`

**Logic:**
1. Initialize an empty list `field_names`.
2. For each `(name, opts)` tuple in `fieldsets`:
   - Flatten `opts['fields']` using `flatten()` and extend `field_names`.
3. Return `field_names`.

**Return:** A flat list of all field names from the admin fieldsets structure.

---

### Function: `get_deleted_objects(objs, request, admin_site) -> tuple[list, dict, set, list]`

**Signature:** `(objs: Iterable[Model], request: HttpRequest, admin_site: AdminSite) -> tuple[list[str], dict[str, int], set[str], list[str]]`

**Logic:**
1. Attempt to get `obj = objs[0]`. If `IndexError`, return `([], {}, set(), [])`.
2. Otherwise, determine the database connection via `router.db_for_write(obj._meta.model)`.
3. Create a `NestedObjects(using=using)` collector and call `collector.collect(objs)`.
4. Initialize an empty `perms_needed` set.
5. Define inner function `format_callback(obj)`:
   - Get the model class and its `_meta`.
   - Check if the model is registered in `admin_site._registry`.
   - Build `no_edit_link = '%s: %s' % (capfirst(opts.verbose_name), obj)`.
   - If registered:
     - Check delete permission via `admin_site._registry[model].has_delete_permission(request, obj)`. If denied, add `opts.verbose_name` to `perms_needed`.
     - Attempt to build an admin change URL using `reverse('%s:%s_%s_change' % (admin_site.name, opts.app_label, opts.model_name), None, (quote(obj.pk),))`.
       - On `NoReverseMatch`, return `no_edit_link`.
     - Otherwise, return a formatted HTML link via `format_html('{}: <a href="{}">{}</a>', capfirst(opts.verbose_name), admin_url, obj)`.
   - If not registered, return `no_edit_link`.
6. Build `to_delete = collector.nested(format_callback)` — the nested deletion tree with formatted strings.
7. Build `protected = [format_callback(obj) for obj in collector.protected]`.
8. Build `model_count = {model._meta.verbose_name_plural: len(objs) for model, objs in collector.model_objs.items()}`.
9. Return `(to_delete, model_count, perms_needed, protected)`.

---

### Class: `NestedObjects(Collector)`

**Inheritance:** Extends `django.db.models.deletion.Collector`.

#### Attributes (initialized in `__init__`)
- **`edges`**: `dict[Any, list[Any]]` — Maps a source instance to a list of dependent target instances.
- **`protected`**: `set[Model]` — Set of objects that could not be deleted due to `PROTECT` constraints.
- **`model_objs`**: `defaultdict[type, set]` — Maps model classes to sets of collected instances.

#### Methods

**`__init__(self, *args, **kwargs)`**
- Calls `super().__init__(*args, **kwargs)`.
- Initializes `edges = {}`, `protected = set()`, `model_objs = defaultdict(set)`.

**`add_edge(self, source, target)`**
- Adds a directed edge: appends `target` to the list at `self.edges.setdefault(source, [])`.

**`collect(self, objs, source=None, source_attr=None, **kwargs)`**
1. For each `obj` in `objs`:
   - If `source_attr` is truthy and does not end with `'+'`: compute a `related_name` by formatting `source_attr` with `{class: source._meta.model_name, app_label: source._meta.app_label}`, then get the related object via `getattr(obj, related_name)` and add an edge from that related object to `obj`.
   - Otherwise, add an edge from `None` to `obj`.
   - Add `obj` to `self.model_objs[obj._meta.model]`.
2. Call `super().collect(objs, source_attr=source_attr, **kwargs)`.
3. If a `models.ProtectedError` is raised, update `self.protected` with the exception's `protected_objects`.

**`related_objects(self, related, objs)`**
- Calls `super().related_objects(related, objs)` to get the queryset, then applies `.select_related(related.field.name)` and returns it.

**`_nested(self, obj, seen, format_callback)` -> list**
1. If `obj in seen`, return `[]`.
2. Add `obj` to `seen`.
3. Initialize empty `children = []`.
4. For each child in `self.edges.get(obj, ())`: recursively call `_nested(child, seen, format_callback)` and extend `children`.
5. Build `ret`: if `format_callback`, `[format_callback(obj)]`; else `[obj]`.
6. If `children` is non-empty, append it as a nested list element to `ret`.
7. Return `ret`.

**`nested(self, format_callback=None) -> list`**
1. Initialize `seen = set()`, `roots = []`.
2. For each root in `self.edges.get(None, ())`: recursively call `_nested(root, seen, format_callback)` and extend `roots`.
3. Return `roots`.

**`can_fast_delete(self, *args, **kwargs) -> bool`**
- Always returns `False`, forcing all objects to be loaded into memory for display on the confirmation page.

---

### Function: `model_format_dict(obj) -> dict[str, str]`

**Signature:** `(obj: Model | ModelBase | QuerySet | Options) -> dict[str, str]`

**Logic:**
1. If `obj` is a `models.Model` instance or `models.base.ModelBase` subclass: set `opts = obj._meta`.
2. Else if `obj` is a `models.query.QuerySet`: set `opts = obj.model._meta`.
3. Otherwise (already an Options): set `opts = obj`.
4. Return `{'verbose_name': opts.verbose_name, 'verbose_name_plural': opts.verbose_name_plural}`.

**Return:** A dict with keys `'verbose_name'` and `'verbose_name_plural'`.

---

### Function: `model_ngettext(obj, n=None) -> str`

**Signature:** `(obj: Model | ModelBase | QuerySet | Options, n: int | None = None) -> str`

**Logic:**
1. If `obj` is a `models.query.QuerySet`: if `n is None`, set `n = obj.count()`; then set `obj = obj.model`.
2. Call `model_format_dict(obj)` to get `{verbose_name, verbose_name_plural}`.
3. Extract `singular` and `plural` from the dict.
4. Return `ngettext(singular, plural, n or 0)`.

**Return:** The properly pluralized model name string for count `n`.

---

### Function: `lookup_field(name, obj, model_admin=None) -> tuple[Field | None, Any | None, Any]`

**Signature:** `(name: str | Callable, obj: Model, model_admin: ModelAdmin | None = None) -> tuple[Field | None, Any | None, Any]`

Returns a 3-tuple of `(field, attr, value)`.

**Logic:**
1. Get `opts = obj._meta`.
2. Try to get the field via `_get_non_gfk_field(opts, name)`:
   - If it raises `FieldDoesNotExist` or `FieldIsAForeignKeyColumnName`:
     - The value is a method, property, or callable.
     - If `name` is callable: set `attr = name`, `value = attr(obj)`.
     - Else if `model_admin` has attribute `name` and `name != '__str__'`: set `attr = getattr(model_admin, name)`, `value = attr(obj)`.
     - Otherwise: set `attr = getattr(obj, name)`; if `callable(attr)`, set `value = attr()`; else `value = attr`.
     - Set `f = None`.
   - Else (field found): set `attr = None`, `value = getattr(obj, name)`.
3. Return `(f, attr, value)`.

---

### Function: `_get_non_gfk_field(opts, name) -> Field`

**Signature:** `(opts: Options, name: str) -> Field`

**Logic:**
1. Get the field via `opts.get_field(name)`.
2. If it is a relation (`field.is_relation`) and either:
   - It is many-to-one but not pointing to a related model (`field.many_to_one and not field.related_model`, i.e., a GenericForeignKey), or
   - It is one-to-many (a reverse relation),
   then raise `FieldDoesNotExist()`.
3. If it is a relation, not many-to-many, has an `attname` attribute, and the attname equals `name` (i.e., `<FK>_id`): raise `FieldIsAForeignKeyColumnName()`.
4. Return the field.

---

### Function: `label_for_field(name, model, model_admin=None, return_attr=False, form=None) -> str | tuple[str, Any]`

**Signature:** `(name: str | Callable, model: type[Model], model_admin: ModelAdmin | None = None, return_attr: bool = False, form: Form | None = None) -> str | tuple[str, Any]`

Returns a label string for the given field name. If `return_attr=True`, also returns the resolved attribute.

**Logic:**
1. Initialize `attr = None`.
2. Try to get the field via `_get_non_gfk_field(model._meta, name)`:
   - Attempt `label = field.verbose_name`.
   - On `AttributeError` (field is a ForeignObjectRel): set `label = field.related_model._meta.verbose_name`.
3. If `FieldDoesNotExist`:
   - If `name == '__str__'`: set `label = str(model._meta.verbose_name)`, `attr = str`.
   - Otherwise, resolve the attribute:
     - If `callable(name)`: `attr = name`.
     - Else if `model_admin` has `name`: `attr = getattr(model_admin, name)`.
     - Else if `model` (the class) has `name`: `attr = getattr(model, name)`.
     - Else if `form` is provided and `name in form.fields`: `attr = form.fields[name]`.
     - Otherwise: raise `AttributeError` with a message including the model, model_admin, and form class names.
   - Determine label from `attr`:
     - If `attr` has `short_description`: `label = attr.short_description`.
     - Else if `attr` is a `property` with an `fget` that has `short_description`: `label = attr.fget.short_description`.
     - Else if `callable(attr)`: if `attr.__name__ == '<lambda>'`, set `label = '--'`; else `label = pretty_name(attr.__name__)`.
     - Otherwise: `label = pretty_name(name)`.
4. If `FieldIsAForeignKeyColumnName`: set `label = pretty_name(name)`, `attr = name`.
5. If `return_attr`: return `(label, attr)`; else return `label`.

---

### Function: `help_text_for_field(name, model) -> str`

**Signature:** `(name: str, model: type[Model]) -> str`

**Logic:**
1. Initialize `help_text = ''`.
2. Try to get the field via `_get_non_gfk_field(model._meta, name)`:
   - If it has a `help_text` attribute, set `help_text = field.help_text`.
3. Return `help_text` (empty string if not found or not applicable).

---

### Function: `display_for_field(value, field, empty_value_display) -> str`

**Signature:** `(value: Any, field: Field, empty_value_display: str) -> str`

**Logic:**
1. Import `_boolean_icon` from `django.contrib.admin.templatetags.admin_list`.
2. If the field has a `flatchoices` attribute: return `dict(field.flatchoices).get(value, empty_value_display)`.
3. Else if `field` is an instance of `models.BooleanField`: return `_boolean_icon(value)`.
4. Else if `value is None`: return `empty_value_display`.
5. Else if `field` is a `models.DateTimeField`: return `formats.localize(timezone.template_localtime(value))`.
6. Else if `field` is an instance of `(models.DateField, models.TimeField)`: return `formats.localize(value)`.
7. Else if `field` is a `models.DecimalField`: return `formats.number_format(value, field.decimal_places)`.
8. Else if `field` is an instance of `(models.IntegerField, models.FloatField)`: return `formats.number_format(value)`.
9. Else if `field` is a `models.FileField` and `value` is truthy: return `format_html('<a href="{}">{}</a>', value.url, value)`.
10. Otherwise: call `display_for_value(value, empty_value_display)` and return its result.

---

### Function: `display_for_value(value, empty_value_display, boolean=False) -> str`

**Signature:** `(value: Any, empty_value_display: str, boolean: bool = False) -> str`

**Logic:**
1. Import `_boolean_icon` from `django.contrib.admin.templatetags.admin_list`.
2. If `boolean` is truthy: return `_boolean_icon(value)`.
3. Else if `value is None`: return `empty_value_display`.
4. Else if `isinstance(value, bool)`: return `str(value)`.
5. Else if `isinstance(value, datetime.datetime)`: return `formats.localize(timezone.template_localtime(value))`.
6. Else if `isinstance(value, (datetime.date, datetime.time))`: return `formats.localize(value)`.
7. Else if `isinstance(value, (int, decimal.Decimal, float))`: return `formats.number_format(value)`.
8. Else if `isinstance(value, (list, tuple))`: return `', '.join(str(v) for v in value)`.
9. Otherwise: return `str(value)`.

---

### Function: `get_model_from_relation(field) -> type[Model]`

**Signature:** `(field: Field) -> type[Model]`

**Logic:**
1. If the field has `get_path_info()`: return `field.get_path_info()[-1].to_opts.model`.
2. Otherwise: raise `NotRelationField`.

---

### Function: `reverse_field_path(model, path) -> tuple[type[Model], str]`

**Signature:** `(model: type[Model], path: str) -> tuple[type[Model], str]`

Creates a reversed field path (e.g., given `(Order, "user__groups")`, returns `(Group, "user__order")`). The final field must be a related model.

**Logic:**
1. Initialize `reversed_path = []`, `parent = model`.
2. Split `path` by `LOOKUP_SEP` into `pieces`.
3. For each `piece` in `pieces`:
   - Get the field: `field = parent._meta.get_field(piece)`.
   - If this is the last piece (`len(reversed_path) == len(pieces) - 1`): try to call `get_model_from_relation(field)`; if it raises `NotRelationField`, break out of the loop (skip trailing data field).
   - If the field is a relation and not auto-created non-concrete: get `related_name = field.related_query_name()`, set `parent = field.remote_field.model`.
   - Otherwise: get `related_name = field.field.name`, set `parent = field.related_model`.
   - Insert `related_name` at position 0 of `reversed_path`.
4. Return `(parent, LOOKUP_SEP.join(reversed_path))`.

---

### Function: `get_fields_from_path(model, path) -> list[Field]`

**Signature:** `(model: type[Model], path: str) -> list[Field]`

Returns a list of Field objects for each segment in the dotted path. E.g., `(ModelX, "user__groups__name")` returns `[ForeignKey, ManyToManyField, CharField]`.

**Logic:**
1. Split `path` by `LOOKUP_SEP` into `pieces`.
2. Initialize empty `fields = []`.
3. For each `piece`:
   - If `fields` is non-empty: set `parent = get_model_from_relation(fields[-1])`; else `parent = model`.
   - Append `parent._meta.get_field(piece)` to `fields`.
4. Return `fields`.

---

### Function: `construct_change_message(form, formsets, add) -> list[dict]`

**Signature:** `(form: Form, formsets: Iterable[BaseFormSet], add: bool) -> list[dict]`

Constructs a JSON-serializable change message describing model changes. Translations are deactivated during construction so strings are stored untranslated (translation happens later on LogEntry access).

**Logic:**
1. Evaluate `changed_data = form.changed_data` before disabling translations (to avoid localization artifacts in date formats).
2. Enter `translation_override(None)` context: call `_get_changed_field_labels_from_form(form, changed_data)` to get `changed_field_labels`.
3. Initialize empty `change_message = []`.
4. If `add` is truthy: append `{'added': {}}` to `change_message`.
5. Else if `form.changed_data` is non-empty: append `{'changed': {'fields': changed_field_labels}}`.
6. If `formsets` is non-empty, enter another `translation_override(None)` context and for each formset:
   - For each `added_object` in `formset.new_objects`: append `{'added': {'name': str(added_object._meta.verbose_name), 'object': str(added_object)}}`.
   - For each `(changed_object, changed_fields)` in `formset.changed_objects`: append `{'changed': {'name': str(changed_object._meta.verbose_name), 'object': str(changed_object), 'fields': _get_changed_field_labels_from_form(formset.forms[0], changed_fields)}}`.
   - For each `deleted_object` in `formset.deleted_objects`: append `{'deleted': {'name': str(deleted_object._meta.verbose_name), 'object': str(deleted_object)}}`.
7. Return `change_message`.

---

### Function: `_get_changed_field_labels_from_form(form, changed_data) -> list[str]`

**Signature:** `(form: Form, changed_data: list[str]) -> list[str]`

Returns a list of human-readable field labels for the fields in `changed_data`.

**Logic:**
1. Initialize empty `changed_field_labels = []`.
2. For each `field_name` in `changed_data`:
   - Try to get `verbose_field_name = form.fields[field_name].label or field_name`.
   - On `KeyError`: set `verbose_field_name = field_name`.
   - Append `str(verbose_field_name)` to the list.
3. Return `changed_field_labels`.

## django/db/models/deletion.py
Now I have the complete source. Here is the specification:

---

## Module-Level Preamble

### Imports

```python
from collections import Counter
from itertools import chain
from operator import attrgetter

from django.db import IntegrityError, connections, transaction
from django.db.models import signals, sql
```

### Constants & Globals

No module-level constants or global variables. The file defines one exception class (`ProtectedError`), six deletion-handler functions (`CASCADE`, `PROTECT`, `SET`, `SET_NULL`, `SET_DEFAULT`, `DO_NOTHING`), one utility function (`get_candidate_relations_to_delete`), and one main class (`Collector`).

---

## Code Objects

### Exception: `ProtectedError(IntegrityError)`

**Inheritance:** Subclass of `django.db.IntegrityError`.

#### `__init__(self, msg, protected_objects)`
- Stores the second argument as an instance attribute `self.protected_objects = protected_objects`.
- Calls `super().__init__(msg, protected_objects)`, passing both arguments to the parent constructor.
- No return value (returns `None`).

---

### Function: `CASCADE(collector, field, sub_objs, using)`

**Signature:** Four positional parameters — `collector` (a `Collector` instance), `field` (a model field with a `remote_field` and `null` attribute), `sub_objs` (an iterable of model instances), `using` (string database alias).

**Logic:**
1. Calls `collector.collect(sub_objs, source=field.remote_field.model, source_attr=field.name, nullable=field.null)`, recursively collecting all related objects for deletion or handling via their own on_delete handlers.
2. If `field.null` is `True` **and** the database connection identified by `using` does not support deferred constraint checks (`not connections[using].features.can_defer_constraint_checks`), calls `collector.add_field_update(field, None, sub_objs)` to schedule nulling out the foreign key on all `sub_objs`.

**Return:** Implicitly returns `None`.

---

### Function: `PROTECT(collector, field, sub_objs, using)`

**Signature:** Same four parameters as `CASCADE`.

**Logic:**
- Raises a `ProtectedError` with a message formatted as `"Cannot delete some instances of model '%s' because they are referenced through a protected foreign key: '%s.%s'"`, where the three `%s` values are filled by `field.remote_field.model.__name__`, `sub_objs[0].__class__.__name__`, and `field.name`.
- The second argument to `ProtectedError` is `sub_objs` (the full list of protected objects).

**Return:** Never returns; always raises `ProtectedError`.

---

### Function: `SET(value)`

**Signature:** One parameter — `value`, which may be either a callable or any other value.

**Logic:**
- If `callable(value)`: defines an inner function `set_on_delete(collector, field, sub_objs, using)` that calls `collector.add_field_update(field, value(), sub_objs)` (invoking the callable to produce the new value at deletion time).
- Otherwise: defines an inner function `set_on_delete(collector, field, sub_objs, using)` that calls `collector.add_field_update(field, value, sub_objs)` (using `value` directly as the replacement).
- Attaches a `deconstruct` attribute to the returned function: `set_on_delete.deconstruct = lambda: ('django.db.models.SET', (value,), {})`, returning a 3-tuple of (import path string, positional args tuple, keyword args dict) for serialization.
- Returns the inner `set_on_delete` function.

**Return:** A callable with signature `(collector, field, sub_objs, using)` that schedules a field update to `value()` (if callable) or `value` (if not).

---

### Function: `SET_NULL(collector, field, sub_objs, using)`

**Signature:** Same four parameters as `CASCADE`.

**Logic:** Calls `collector.add_field_update(field, None, sub_objs)` to schedule nulling out the field on all `sub_objs`.

**Return:** Implicitly returns `None`.

---

### Function: `SET_DEFAULT(collector, field, sub_objs, using)`

**Signature:** Same four parameters as `CASCADE`.

**Logic:** Calls `collector.add_field_update(field, field.get_default(), sub_objs)`, scheduling a field update to the default value obtained by calling `field.get_default()`.

**Return:** Implicitly returns `None`.

---

### Function: `DO_NOTHING(collector, field, sub_objs, using)`

**Signature:** Same four parameters as `CASCADE`.

**Logic:** Does nothing (empty body).

**Return:** Implicitly returns `None`.

---

### Function: `get_candidate_relations_to_delete(opts)`

**Signature:** One parameter — `opts` (a model `_meta` object).

**Logic:**
- Iterates over all fields returned by `opts.get_fields(include_hidden=True)`.
- Filters to only those fields where **all three** conditions hold:
  1. `f.auto_created` is `True` (the field was auto-created, e.g., reverse FK or M2M).
  2. `not f.concrete` (the field does not correspond to a concrete database column on the model's own table).
  3. `f.one_to_one or f.one_to_many` (the relation cardinality is 1-1 or 1-N, excluding many-to-many).

**Return:** A generator yielding the filtered field objects. Many-to-many relations are excluded from deletion consideration.

---

### Class: `Collector`

#### Attributes (initialized in `__init__`)

| Attribute | Type | Description |
|-----------|------|-------------|
| `self.using` | `str` | Database alias string passed to constructor. |
| `self.data` | `dict[Model, set]` | Initially maps model classes to sets of instances; values may later become lists after sorting. Tracks all objects collected for deletion. |
| `self.field_updates` | `dict[Model, dict[(field, value), set]]` | Maps model → {(field, value) → {instances}}. Schedules field updates to be applied before or during deletion. |
| `self.fast_deletes` | `list` | List of queryset-like objects that can be deleted via bulk SQL without fetching instances into memory. |
| `self.dependencies` | `dict[Model, set]` | Maps concrete model → {set of concrete models it depends on}. Used for topological ordering in databases without transaction support or deferred constraint checks. |

#### `__init__(self, using)`
- Stores `using` as `self.using`.
- Initializes all four attributes to empty containers (`{}`, `{}`, `[]`, `{}`).

---

#### Method: `add(self, objs, source=None, nullable=False, reverse_dependency=False)`

**Signature:** `objs` (iterable of model instances), `source` (model or None), `nullable` (bool, default `False`), `reverse_dependency` (bool, default `False`).

**Logic:**
1. If `objs` is empty/falsy, returns `[]`.
2. Creates an empty list `new_objs = []`.
3. Determines the model class from `objs[0].__class__`.
4. Gets or creates a set for this model in `self.data` via `self.data.setdefault(model, set())`.
5. Iterates over each obj in objs; if not already in the set, appends to `new_objs`.
6. Updates the set with all new objects: `instances.update(new_objs)`.
7. If `source is not None and not nullable`:
   - If `reverse_dependency` is True, swaps source and model: `source, model = model, source`.
   - Records a dependency: adds `model._meta.concrete_model` to the set of dependencies for `source._meta.concrete_model` in `self.dependencies`.
8. Returns `new_objs` (the list of objects that were newly added).

**Return:** List of newly-added instances, or empty list if all were already collected.

---

#### Method: `add_field_update(self, field, value, objs)`

**Signature:** `field` (model field), `value` (replacement value), `objs` (homogeneous iterable of model instances).

**Logic:**
1. If `objs` is empty/falsy, returns immediately.
2. Determines the model from `objs[0].__class__`.
3. Uses nested `setdefault` calls to build a three-level structure: `self.field_updates[model][(field, value)].update(objs)`, adding all objs to the set for that (field, value) pair on that model.

**Return:** Implicitly returns `None`.

---

#### Method: `_has_signal_listeners(self, model)`

**Signature:** One parameter — `model` (a model class).

**Logic:** Returns `True` if either `signals.pre_delete.has_listeners(model)` or `signals.post_delete.has_listeners(model)` is True; otherwise returns `False`.

**Return:** Boolean indicating whether any Django signals are connected for the given model.

---

#### Method: `can_fast_delete(self, objs, from_field=None)`

**Signature:** `objs` (queryset-like or single object), `from_field` (a field or None).

**Logic — returns False if any of these conditions hold:**
1. `from_field is not None and from_field.remote_field.on_delete is not CASCADE`.
2. `objs` does not have a `_meta` attribute, **and** (`objs.model` doesn't exist **or** `objs._raw_delete` doesn't exist). If neither condition identifies a model, returns False.
3. The identified model has signal listeners (checked via `_has_signal_listeners`).
4. Not all parent links in `opts.concrete_model._meta.parents.values()` equal `from_field` (i.e., there are non-parent-inheritance relationships that would prevent fast deletion).
5. Any candidate relation pointing to this model has an on_delete handler other than `DO_NOTHING` (checked via `get_candidate_relations_to_delete(opts)`).
6. Any private field on the model has a `bulk_related_objects` attribute (e.g., generic foreign keys).

**Return:** Boolean — True only if all conditions above are satisfied, meaning the objects can be deleted in bulk without fetching them into memory.

---

#### Method: `get_del_batches(self, objs, field)`

**Signature:** `objs` (iterable of model instances), `field` (model field).

**Logic:**
1. Computes `conn_batch_size = max(connections[self.using].ops.bulk_batch_size([field.name], objs), 1)`.
2. If `len(objs) > conn_batch_size`, splits objs into chunks of size `conn_batch_size` and returns a list of slices: `[objs[i:i + conn_batch_size] for i in range(0, len(objs), conn_batch_size)]`.
3. Otherwise, returns `[objs]` (a single-element list containing the original iterable).

**Return:** List of batched sub-iterables sized according to the database connection's bulk operation limits.

---

#### Method: `collect(self, objs, source=None, nullable=False, collect_related=True, source_attr=None, reverse_dependency=False, keep_parents=False)`

**Signature:** Seven parameters — `objs` (homogeneous iterable of model instances), `source` (model or None), `nullable` (bool), `collect_related` (bool, default True), `source_attr` (string or None), `reverse_dependency` (bool), `keep_parents` (bool).

**Logic:**
1. If `self.can_fast_delete(objs)` returns True: appends `objs` to `self.fast_deletes` and returns immediately.
2. Calls `new_objs = self.add(objs, source, nullable, reverse_dependency=reverse_dependency)`.
3. If `new_objs` is empty (all already collected), returns.
4. Determines `model = new_objs[0].__class__`.
5. **Parent collection** (if not `keep_parents`): For each pointer field in `concrete_model._meta.parents.values()`: if the pointer name is truthy, extracts parent objects via `[getattr(obj, ptr.name) for obj in new_objs]`, then recursively calls `self.collect(parent_objs, source=model, source_attr=ptr.remote_field.related_name, collect_related=False, reverse_dependency=True)`.
6. **Related object collection** (if `collect_related`):
   - If `keep_parents`, builds a set of parent models from `model._meta.get_parent_list()`.
   - For each relation returned by `get_candidate_relations_to_delete(model._meta)`:
     - If `keep_parents` and the related model is in the parents set, skips this relation.
     - Gets the field: `field = related.field`.
     - If `field.remote_field.on_delete is DO_NOTHING`, continues to next relation.
     - Splits new_objs into batches via `self.get_del_batches(new_objs, field)`.
     - For each batch: calls `sub_objs = self.related_objects(related, batch)`.
       - If `self.can_fast_delete(sub_objs, from_field=field)` is True: appends to `self.fast_deletes`.
       - Otherwise: if neither `sub_objs.query.select_related` nor signal listeners exist for the related model, restricts sub_objs to only referenced FK fields (via `.only()`). Then, if `sub_objs` is non-empty, calls `field.remote_field.on_delete(self, field, sub_objs, self.using)`.
   - For each field in `model._meta.private_fields`: if it has a `bulk_related_objects` attribute, calls `sub_objs = field.bulk_related_objects(new_objs, self.using)` and recursively collects with `source=model, nullable=True`.

**Return:** Implicitly returns `None`.

---

#### Method: `related_objects(self, related, objs)`

**Signature:** `related` (a relation field object), `objs` (iterable of model instances).

**Logic:** Returns a QuerySet constructed by filtering the related model's base manager on the given database alias (`self.using`) with the lookup `"{field.name}__in": objs`.

**Return:** A QuerySet of objects related to `objs` through the `related` relation.

---

#### Method: `instances_with_model(self)`

**Signature:** No parameters beyond `self`.

**Logic:** Iterates over `self.data.items()`, yielding `(model, obj)` tuples for each model and each instance in its set.

**Return:** A generator of `(Model, instance)` pairs.

---

#### Method: `sort(self)`

**Signature:** No parameters beyond `self`.

**Logic — topological sort of models based on dependency graph:**
1. Initializes `sorted_models = []` and `concrete_models = set()`.
2. Sets `models = list(self.data)`.
3. While the length of `sorted_models` is less than the total number of models:
   - Iterates over each model in `models`:
     - If already in `sorted_models`, skips.
     - Gets dependencies for this model's concrete version from `self.dependencies.get(model._meta.concrete_model)`.
     - If there are no dependencies, or all dependencies are already in `concrete_models`, appends the model to `sorted_models` and adds its concrete model to `concrete_models`; sets `found = True`.
   - If no model was found in this pass (cycle detected), returns early without modifying data.
4. Replaces `self.data` with an ordered dict: `{model: self.data[model] for model in sorted_models}`.

**Return:** Implicitly returns `None`; mutates `self.data` in place to reflect deletion order.

---

#### Method: `delete(self)`

**Signature:** No parameters beyond `self`.

**Logic — multi-phase deletion within a transaction:**
1. **Sort instances by PK:** For each model and its set of instances in `self.data`, replaces the set with a sorted list keyed by `pk`: `sorted(instances, key=attrgetter("pk"))`.
2. **Topological sort:** Calls `self.sort()` to order models by dependency.
3. Initializes `deleted_counter = Counter()`.
4. **Single-object optimization:** If exactly one model and exactly one instance exist in `self.data`, and `self.can_fast_delete(instance)` is True:
   - Enters a transaction via `transaction.mark_for_rollback_on_error()`.
   - Calls `count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)`.
   - Sets the instance's PK attribute to None: `setattr(instance, model._meta.pk.attname, None)`.
   - Returns `(count, {model._meta.label: count})`.
5. **Main deletion block** (within `transaction.atomic(using=self.using, savepoint=False)`):
   a. **Send pre_delete signals:** For each `(model, obj)` from `instances_with_model()`, if the model is not auto-created (`not model._meta.auto_created`), sends `signals.pre_delete.send(sender=model, instance=obj, using=self.using)`.
   b. **Fast deletes:** For each queryset-like `qs` in `self.fast_deletes`, calls `count = qs._raw_delete(using=self.using)` and accumulates: `deleted_counter[qs.model._meta.label] += count`.
   c. **Field updates:** For each model and its field-value mappings in `self.field_updates`: for each `(field, value), instances` pair, creates an `sql.UpdateQuery(model)`, calls `query.update_batch([obj.pk for obj in instances], {field.name: value}, self.using)`.
   d. **Reverse instance collections:** For each list of instances in `self.data.values()`, reverses the list in place (`instances.reverse()`).
   e. **Delete instances:** For each model and its (now reversed) instance list: creates an `sql.DeleteQuery(model)`, extracts PKs, calls `count = query.delete_batch(pk_list, self.using)`, accumulates into `deleted_counter`. If the model is not auto-created, sends `signals.post_delete.send(sender=model, instance=obj, using=self.using)` for each deleted object.
6. **Update collected instances in memory:** For each field-value mapping in `self.field_updates.values()`: for each `(field, value), instances` pair, sets `setattr(obj, field.attname, value)` on every instance. Then for each model and its instances: sets the PK attribute to None via `setattr(instance, model._meta.pk.attname, None)`.
7. Returns `(sum(deleted_counter.values()), dict(deleted_counter))` — a tuple of (total count deleted, dict mapping model labels to per-model counts).

**Return:** Tuple of `(int total_deleted, dict[str: int] per_model_counts)`.