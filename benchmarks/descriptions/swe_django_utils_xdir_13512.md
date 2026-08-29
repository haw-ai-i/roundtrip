## django/contrib/admin/utils.py
Now I have the full file (550 lines). Here is the complete natural-language specification:

---

# Module Specification: `django/contrib/admin/utils.py`

## 1. Module-Level Preamble

### Imports

```python
import datetime
import decimal
from collections import defaultdict

from django.core.exceptions import FieldDoesNotExist
from django.db import models, router
from django.db.models.constants import LOOKUP_SEP
from django.db.models.deletion import Collector
from django.forms.utils import pretty_name
from django.urls import NoReverseMatch, reverse
from django.utils import formats, timezone
from django.utils.html import format_html
from django.utils.regex_helper import _lazy_re_compile
from django.utils.text import capfirst
from django.utils.translation import ngettext, override as translation_override
```

### Constants & Globals

- **`QUOTE_MAP`** — `dict[int, str]`: A mapping from byte values (integers 0–255) to URL-encoded replacement strings for characters that could confuse admin URLs. Keys are the integer ordinals of each character in the bytes literal `b'":/_#?;@&=+$,"[]<>%\n\\'`. Values are `'_%02X' % i` (e.g., byte 47 → `'_2F'`).

- **`UNQUOTE_MAP`** — `dict[str, str]`: The inverse of `QUOTE_MAP`, mapping each encoded string back to the original character: `{v: chr(k) for k, v in QUOTE_MAP.items()}`.

- **`UNQUOTE_RE`** — compiled regex pattern: `_lazy_re_compile('_(?:%s)' % '|'.join([x[1:] for x in UNQUOTE_MAP]))`. Matches underscore-prefixed two-digit hex sequences produced by `quote()` (e.g., `_2F`).

### Exception Classes

- **`FieldIsAForeignKeyColumnName(Exception)`** — Raised when a field name is a foreign key attname (i.e., `<FK>_id`) rather than the FK field itself.

- **`NotRelationField(Exception)`** — Raised when `get_model_from_relation()` receives a field that has no `get_path_info` attribute, meaning it is not a relation field.

---

## 2. Code Objects

### `lookup_needs_distinct(opts, lookup_path) → bool`

Determines whether `distinct()` must be used for a given ORM lookup path.

1. Splits `lookup_path` by `LOOKUP_SEP` (`'__'`) into field names.
2. Iterates over each field name:
   - If the name is `'pk'`, replaces it with `opts.pk.name`.
   - Attempts `opts.get_field(field_name)`. On `FieldDoesNotExist`, continues (the lookup may be a query filter, not a relation).
   - Otherwise, if the field has `get_path_info` (it is a relation), follows the path: sets `opts = path_info[-1].to_opts`. If any segment in the path has `m2m == True`, returns `True` immediately.
3. Returns `False` if no M2M relation was encountered along the entire lookup chain.

---

### `prepare_lookup_value(key, value) → Any`

Prepares a filter value for queryset lookups with special suffixes.

1. If `key.endswith('__in')`: splits `value` on commas (`','`) into a list and returns it.
2. Else if `key.endswith('__isnull')`: converts `value` to lowercase; returns `True` if the lowercased value is **not** in `('', 'false', '0')`, else `False`.
3. Otherwise: returns `value` unchanged.

---

### `quote(s) → str | Any`

URL-encodes a string so that primary key values do not confuse admin URLs. Uses `str.translate(QUOTE_MAP)` to replace problematic characters (`/`, `_`, `:`, etc.) with hex-encoded forms like `_2F`. If `s` is not a `str`, returns it unchanged.

---

### `unquote(s) → str`

Reverses the effects of `quote()`. Uses `UNQUOTE_RE.sub()` with a callback that maps each matched encoded sequence (e.g., `_2F`) back to its original character via `UNQUOTE_MAP`.

---

### `flatten(fields) → list`

Performs one level of flattening on a nested iterable of field names. Iterates over `fields`; if an element is a `list` or `tuple`, extends the result with its contents; otherwise appends it directly. Returns the flat list.

---

### `flatten_fieldsets(fieldsets) → list[str]`

Extracts all field names from an admin fieldsets structure. A fieldsets structure is an iterable of `(name, opts)` tuples where `opts['fields']` is a (possibly nested) list of field name strings. Iterates over each fieldset entry, flattens its `'fields'` sub-list via `flatten()`, and extends the result. Returns the combined flat list of all field names.

---

### `get_deleted_objects(objs, request, admin_site) → tuple[list, dict, set, list]`

Collects all objects related to `objs` that should also be deleted, formats them for display in the admin confirmation page, and returns a 4-tuple: `(to_delete, model_count, perms_needed, protected)`.

1. If `objs` is empty (IndexError on indexing), returns `([], {}, set(), [])`.
2. Otherwise, determines the database connection via `router.db_for_write(obj._meta.model)` from the first object.
3. Creates a `NestedObjects(using=using)` collector and calls `collector.collect(objs)`.
4. Defines an inner function `format_callback(obj)`:
   - Gets the model class and its `_meta`.
   - Checks if the model is registered in `admin_site._registry`.
   - If registered, checks delete permission; if denied, adds `opts.verbose_name` to `perms_needed`. Attempts to build a change URL via `reverse('%s:%s_%s_change' % (admin_site.name, opts.app_label, opts.model_name), None, (quote(obj.pk),))`. On `NoReverseMatch`, returns the plain label string. Otherwise, returns an HTML link: `format_html('{}: <a href="{}">{}</a>', capfirst(opts.verbose_name), admin_url, obj)`.
   - If not registered, returns the plain label string (`'%s: %s' % (capfirst(opts.verbose_name), obj)`).
5. Calls `collector.nested(format_callback)` to produce a nested list structure for template rendering.
6. Formats protected objects similarly via `[format_callback(obj) for obj in collector.protected]`.
7. Builds `model_count`: `{model._meta.verbose_name_plural: len(objs) for model, objs in collector.model_objs.items()}`.
8. Returns `(to_delete, model_count, perms_needed, protected)`.

---

### `class NestedObjects(Collector)`

Extends Django's `Collector` (from `django.db.models.deletion`) to track dependency edges between objects and produce a nested representation of the deletion graph.

**Attributes:**
- **`edges`** — `dict[Any, list[Any]]`: Maps each source instance to a list of target instances it references. Keyed by `{from_instance: [to_instances]}`. `None` is used as key for root objects (those not referenced by any other object in the graph).
- **`protected`** — `set[Any]`: Set of objects that could not be deleted due to `ProtectedError` or `RestrictedError`.
- **`model_objs`** — `defaultdict(set)`: Maps each model class to a set of its instances encountered during collection.

**Methods:**

#### `__init__(self, *args, **kwargs)`
Calls `super().__init__(*args, **kwargs)`, then initializes `edges = {}`, `protected = set()`, and `model_objs = defaultdict(set)`.

#### `add_edge(self, source, target)`
Adds a directed edge: appends `target` to the list at `self.edges.setdefault(source, [])`.

#### `collect(self, objs, source=None, source_attr=None, **kwargs)`
Overrides `Collector.collect()`:
1. For each object in `objs`:
   - If `source_attr` is provided and does not end with `'+'`, computes a `related_name` by formatting `source_attr` with `{class: source._meta.model_name, app_label: source._meta.app_label}`, then gets the related instance via `getattr(obj, related_name)` and adds an edge from that related instance to `obj`.
   - Otherwise (no `source_attr` or it ends with `'+'`), adds an edge from `None` to `obj` (marking it as a root).
   - Adds `obj` to `self.model_objs[obj._meta.model]`.
2. Calls `super().collect(objs, source_attr=source_attr, **kwargs)`.
3. Catches `models.ProtectedError` and updates `self.protected` with `e.protected_objects`.
4. Catches `models.RestrictedError` and updates `self.protected` with `e.restricted_objects`.

#### `related_objects(self, related_model, related_fields, objs) → QuerySet`
Overrides `Collector.related_objects()`: calls the parent method to get the queryset of related objects, then applies `.select_related(*[related_field.name for related_field in related_fields])` to optimize queries.

#### `_nested(self, obj, seen, format_callback)` — recursive helper
Produces a nested list representation starting from `obj`. If `obj` is already in `seen`, returns `[]`. Otherwise adds it to `seen`, recursively processes each child in `self.edges.get(obj, ())`, and builds the result: `[format_callback(obj)]` (or `[obj]` if no callback) optionally followed by a list of children. Returns the nested structure.

#### `nested(self, format_callback=None) → list`
Returns the full dependency graph as a nested list. Iterates over roots (`self.edges.get(None, ())`) and extends the result with `_nested()` for each root. Uses a shared `seen` set to avoid cycles.

#### `can_fast_delete(self, *args, **kwargs) → bool`
Always returns `False`, forcing all objects to be loaded into memory so they can be displayed on the admin confirmation page.

---

### `model_format_dict(obj) → dict[str, str]`

Returns a dictionary with keys `'verbose_name'` and `'verbose_name_plural'` extracted from an object's `_meta`. Handles three input types:
- If `obj` is a `models.Model` instance or `ModelBase` subclass: uses `obj._meta`.
- If `obj` is a `QuerySet`: uses `obj.model._meta`.
- Otherwise (assumes `obj` already has `_meta`): uses `obj` directly.

Returns `{'verbose_name': opts.verbose_name, 'verbose_name_plural': opts.verbose_name_plural}`.

---

### `model_ngettext(obj, n=None) → str`

Returns the appropriate singular or plural verbose name for an object/model/queryset, using Django's `ngettext()` for translation-aware pluralization.
- If `obj` is a `QuerySet`: if `n` is `None`, sets `n = obj.count()`, then extracts the model class as `obj`.
- Calls `model_format_dict(obj)` to get singular and plural strings.
- Returns `ngettext(singular, plural, n or 0)`.

---

### `lookup_field(name, obj, model_admin=None) → tuple[Field | None, callable | str | None, Any]`

Looks up a field value on an object for admin display. Returns `(f, attr, value)` where `f` is the Field instance (or `None`), `attr` is the resolved attribute/callable (or `None` or a string name), and `value` is the resolved value.

1. Gets `opts = obj._meta`.
2. Attempts `_get_non_gfk_field(opts, name)`:
   - **On success** (it's a real field): sets `attr = None`, gets `value = getattr(obj, name)`.
   - **On failure** (`FieldDoesNotExist` or `FieldIsAForeignKeyColumnName`): it's a non-field value:
     - If `name` is callable: `attr = name`, `value = attr(obj)`.
     - Else if `model_admin` has the attribute and `name != '__str__'`: `attr = getattr(model_admin, name)`, `value = attr(obj)`.
     - Else: `attr = getattr(obj, name)`; if callable, `value = attr()`, else `value = attr`.
3. Returns `(f, attr, value)`.

---

### `_get_non_gfk_field(opts, name) → Field`

Internal helper that retrieves a field by name while excluding GenericForeignKeys and reverse relations.

1. Calls `opts.get_field(name)`.
2. If the field is a relation (`field.is_relation`) and either:
   - It's many-to-one but has no `related_model` (GenericForeignKey), or
   - It's one-to-many (reverse relation),
   raises `FieldDoesNotExist()`.
3. If the field is a relation, not many-to-many, has an `attname`, and `field.attname == name` (i.e., it's a `<FK>_id` attname rather than the FK field itself), raises `FieldIsAForeignKeyColumnName()`.
4. Otherwise returns the field.

---

### `label_for_field(name, model, model_admin=None, return_attr=False, form=None) → str | tuple[str, Any]`

Returns a human-readable label for a field name used in admin display. The name can be a model field name, a callable, a property, or an attribute on the model/model_admin/form. If `return_attr=True`, also returns the resolved attribute.

1. Attempts `_get_non_gfk_field(model._meta, name)`:
   - **On success** (it's a real field): tries to get `field.verbose_name`. On `AttributeError` (likely a `ForeignObjectRel`), falls back to `field.related_model._meta.verbose_name`.
2. **On `FieldDoesNotExist`**: the name is not a model field:
   - If `name == "__str__"`: label = `str(model._meta.verbose_name)`, attr = `str`.
   - Otherwise, resolves `attr` by checking (in order): `callable(name)` → `hasattr(model_admin, name)` → `hasattr(model, name)` → `form and name in form.fields`. If none match, raises `AttributeError` with a descriptive message including the model/model_admin/form class names.
   - Determines label from `attr`:
     - If `attr` has `short_description`: uses it.
     - Else if `attr` is a `property` with an `fget` that has `short_description`: uses `attr.fget.short_description`.
     - Else if callable: if `__name__ == '<lambda>'`, label = `'--'`; else `pretty_name(attr.__name__)`.
     - Else: `pretty_name(name)`.
3. **On `FieldIsAForeignKeyColumnName`**: label = `pretty_name(name)`, attr = `name`.
4. If `return_attr`: returns `(label, attr)`; otherwise returns just `label`.

---

### `help_text_for_field(name, model) → str`

Returns the help text for a field name on a model.

1. Attempts `_get_non_gfk_field(model._meta, name)`.
2. On success and if the field has a `help_text` attribute: returns it.
3. Otherwise (field not found or no `help_text`): returns `""`.

---

### `display_for_field(value, field, empty_value_display) → str | SafeString`

Displays a field value for admin list/detail views, handling type-specific formatting.

1. If the field has `flatchoices`: returns `dict(field.flatchoices).get(value, empty_value_display)` (choice display).
2. Else if `field` is a `BooleanField`: returns `_boolean_icon(value)` from `admin_list`.
3. Else if `value is None`: returns `empty_value_display`.
4. Else if `field` is a `DateTimeField`: returns `formats.localize(timezone.template_localtime(value))`.
5. Else if `field` is a `DateField` or `TimeField`: returns `formats.localize(value)`.
6. Else if `field` is a `DecimalField`: returns `formats.number_format(value, field.decimal_places)`.
7. Else if `field` is an `IntegerField` or `FloatField`: returns `formats.number_format(value)`.
8. Else if `field` is a `FileField` and `value` is truthy: returns `format_html('<a href="{}">{}</a>', value.url, value)`.
9. Else if `field` is a `JSONField` and `value`: tries `field.get_prep_value(value)`; on `TypeError`, falls back to `display_for_value(value, empty_value_display)`.
10. Otherwise: returns `display_for_value(value, empty_value_display)`.

---

### `display_for_value(value, empty_value_display, boolean=False) → str | SafeString`

Displays a raw value for admin views with type-specific formatting (no field metadata).

1. If `boolean` is truthy: returns `_boolean_icon(value)` from `admin_list`.
2. Else if `value is None`: returns `empty_value_display`.
3. Else if `isinstance(value, bool)`: returns `str(value)`.
4. Else if `isinstance(value, datetime.datetime)`: returns `formats.localize(timezone.template_localtime(value))`.
5. Else if `isinstance(value, (datetime.date, datetime.time))`: returns `formats.localize(value)`.
6. Else if `isinstance(value, (int, decimal.Decimal, float))`: returns `formats.number_format(value)`.
7. Else if `isinstance(value, (list, tuple))`: returns `', '.join(str(v) for v in value)`.
8. Otherwise: returns `str(value)`.

---

### `get_model_from_relation(field) → type[Model]`

Extracts the target model from a relation field. If the field has `get_path_info`, returns `field.get_path_info()[-1].to_opts.model`. Otherwise raises `NotRelationField`.

---

### `reverse_field_path(model, path) → tuple[type[Model], str]`

Creates a reversed field path for reverse lookups. Given `(Order, "user__groups")`, returns `(Group, "user__order")`. The final segment may be a data field (not necessarily a relation).

1. Splits `path` by `LOOKUP_SEP` into pieces.
2. Iterates over each piece with index tracking:
   - Gets the current parent model's field via `parent._meta.get_field(piece)`.
   - If this is the final piece and the field is not a relation (checked via `get_model_from_relation()`), breaks out of the loop (skipping trailing data fields).
   - For each non-skipped piece: if `field.is_relation` and not `(field.auto_created and not field.concrete)`, gets `related_name = field.related_query_name()` and sets `parent = field.remote_field.model`. Otherwise, sets `related_name = field.field.name` and `parent = field.related_model`.
   - Inserts `related_name` at the front of `reversed_path`.
3. Returns `(parent, LOOKUP_SEP.join(reversed_path))`.

---

### `get_fields_from_path(model, path) → list[Field]`

Returns a list of Field objects traversed by following a dotted path from a model. Given `(ModelX, "user__groups__name")`, returns `[ForeignKey, ManyToManyField, CharField]`.

1. Splits `path` by `LOOKUP_SEP`.
2. Iterates over pieces: if there are already collected fields, gets the parent model via `get_model_from_relation(fields[-1])`; otherwise uses the original `model`. Appends `parent._meta.get_field(piece)` to the result list.
3. Returns the list of fields.

---

### `construct_change_message(form, formsets, add) → list[dict]`

Constructs a JSON-serializable change message describing what was added/changed/deleted in an admin save operation. Translations are deactivated during construction so strings are stored untranslated (translation happens at LogEntry access time).

1. Evaluates `form.changed_data` **before** disabling translations (to avoid localization artifacts affecting which fields appear changed).
2. Enters `translation_override(None)` context and calls `_get_changed_field_labels_from_form(form, changed_data)` to get verbose field names for the main form's changes.
3. Initializes `change_message = []`.
4. If `add` is True: appends `{'added': {}}`.
5. Else if `form.changed_data`: appends `{'changed': {'fields': changed_field_labels}}`.
6. If `formsets` is non-empty, enters another `translation_override(None)` context and iterates over each formset:
   - For each `added_object` in `formset.new_objects`: appends `{'added': {'name': str(added_object._meta.verbose_name), 'object': str(added_object)}}`.
   - For each `(changed_object, changed_fields)` in `formset.changed_objects`: appends `{'changed': {'name': str(changed_object._meta.verbose_name), 'object': str(changed_object), 'fields': _get_changed_field_labels_from_form(formset.forms[0], changed_fields)}}`.
   - For each `deleted_object` in `formset.deleted_objects`: appends `{'deleted': {'name': str(deleted_object._meta.verbose_name), 'object': str(deleted_object)}}`.
7. Returns the `change_message` list of dicts.

---

### `_get_changed_field_labels_from_form(form, changed_data) → list[str]`

Internal helper that converts field names from `form.changed_data` into human-readable labels.

1. Iterates over each `field_name` in `changed_data`.
2. Attempts to get the verbose label via `form.fields[field_name].label`; if the field is not in `form.fields` (KeyError), falls back to using `field_name` itself.
3. Converts the result to `str` and appends it.
4. Returns the list of labels.

---

## django/forms/fields.py
The complete natural-language specification of `django/forms/fields.py` has been written to `/tmp/omp_desc__n1aym1d/spec_fields.md`. It covers all 30 code objects in the file:

- **Imports** (28 imports from stdlib, Django core, and Django utils)
- **`__all__`** (28 exported class names)
- **Core classes**: `Field`, `CharField`, `IntegerField`, `FloatField`, `DecimalField`
- **Temporal fields**: `BaseTemporalField`, `DateField`, `TimeField`, `DateTimeFormatsIterator`, `DateTimeField`, `DurationField`
- **Text/regex fields**: `RegexField`, `EmailField`, `URLField`, `GenericIPAddressField`, `SlugField`, `UUIDField`
- **File/image fields**: `FileField`, `ImageField`
- **Boolean fields**: `BooleanField`, `NullBooleanField`
- **Choice fields**: `ChoiceField`, `TypedChoiceField`, `MultipleChoiceField`, `TypedMultipleChoiceField`, `FilePathField`
- **Composite fields**: `ComboField`, `MultiValueField`, `SplitDateTimeField`
- **JSON fields**: `InvalidJSONInput`, `JSONString`, `JSONField`

Each class includes its full signature, all attributes (class and instance), complete implementation logic for every method, return types, exception conditions, and inheritance relationships.