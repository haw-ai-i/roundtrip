## django/db/models/base.py
Now I have read all sections of the file. Let me compile the complete natural-language specification:

---

# Module-Level Preamble

## Imports

```python
import copy
import inspect
import warnings
from functools import partialmethod
from itertools import chain

from django.apps import apps
from django.conf import settings
from django.core import checks
from django.core.exceptions import (
    NON_FIELD_ERRORS, FieldDoesNotExist, FieldError, MultipleObjectsReturned,
    ObjectDoesNotExist, ValidationError,
)
from django.db import (
    DEFAULT_DB_ALIAS, DJANGO_VERSION_PICKLE_KEY, DatabaseError, connection,
    connections, router, transaction,
)
from django.db.models import (
    NOT_PROVIDED, ExpressionWrapper, IntegerField, Max, Value,
)
from django.db.models.constants import LOOKUP_SEP
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.db.models.deletion import CASCADE, Collector
from django.db.models.fields.related import (
    ForeignObjectRel, OneToOneField, lazy_related_operation, resolve_relation,
)
from django.db.models.functions import Coalesce
from django.db.models.manager import Manager
from django.db.models.options import Options
from django.db.models.query import Q
from django.db.models.signals import (
    class_prepared, post_init, post_save, pre_init, pre_save,
)
from django.db.models.utils import make_model_tuple
from django.utils.encoding import force_str
from django.utils.hashable import make_hashable
from django.utils.text import capfirst, get_text_list
from django.utils.translation import gettext_lazy as _
from django.utils.version import get_version
```

## Constants & Globals

- **`DEFERRED`** — A singleton instance of the `Deferred` class (line 50). Used to mark fields that should be deferred during model instantiation. The `Deferred` class defines `__repr__` and `__str__`, both returning the string `'<Deferred field>'`.
- **`LOOKUP_SEP`** — Imported from `django.db.models.constants`; used as a separator in ORM lookups (typically `'__'`).
- **`NON_FIELD_ERRORS`** — Imported from `django.core.exceptions`; used as a key for non-field-level validation errors.

## Helper Functions (module-level, before classes)

### `subclass_exception(name, bases, module, attached_to)` → `type`

Creates an exception class dynamically using `type()`. The new class has:
- `__module__` set to the provided `module` string.
- `__qualname__` set to `'{attached_to.__qualname__}.{name}'`.

Used by `ModelBase.__new__` to create per-model `DoesNotExist` and `MultipleObjectsReturned` exceptions that can be pickled correctly when attached as attributes on the target class.

### `_has_contribute_to_class(value)` → `bool`

Returns `True` if `value` is not a class (`not inspect.isclass(value)`) AND has an attribute named `'contribute_to_class'`. Used to determine whether an attribute should be passed through `type.__new__` or handled via its `contribute_to_class()` method during model metaclass setup.

---

# Code Objects

## Class: `Deferred`

A marker class with two dunder methods:
- **`__repr__(self)`** → Returns the string `'<Deferred field>'`.
- **`__str__(self)`** → Returns the string `'<Deferred field>'`.

Used as a sentinel to represent deferred (not-yet-loaded) model fields.

---

## Class: `ModelBase(type)` — Metaclass for all Django models

### Method: `__new__(cls, name, bases, attrs, **kwargs)` → `type`

Creates a new model class. The logic proceeds as follows:

1. **Early exit for non-model classes:** Collects parent classes that are instances of `ModelBase` into `parents`. If `parents` is empty (i.e., this class does not subclass any Django model), delegates directly to `super().__new__(cls, name, bases, attrs)` and returns the result without any Django-specific setup.

2. **Class creation:** Pops `'__module__'`, `'__classcell__'` (if present), and `'Meta'` from `attrs`. Separates attributes into two groups: those with a `contribute_to_class()` method (`contributable_attrs`) go to the metaclass for later processing; all others go directly into `new_attrs` for `type.__new__()`. Calls `super().__new__(cls, name, bases, new_attrs, **kwargs)` to create the class.

3. **Meta options extraction:** Reads `attr_meta.abstract` (defaulting to `False`). Gets or creates a `meta` object from `Meta` class attribute or `_meta`. Checks for an existing `_meta` on the new class (`base_meta`). Determines `app_label` by looking up the containing app config via `apps.get_containing_app_config(module)`. If no explicit `app_label` is set in `Meta`, uses the discovered one; raises `RuntimeError` if abstract is `False` and no app can be found.

4. **Options initialization:** Creates an `Options(meta, app_label)` object and adds it to the class as `'_meta'`.

5. **Exception classes (non-abstract only):** For non-abstract models, creates per-model exception subclasses:
   - `'DoesNotExist'` — inherits from each parent's `DoesNotExist` (if they have `_meta` and are not abstract), or falls back to `ObjectDoesNotExist`.
   - `'MultipleObjectsReturned'` — same inheritance pattern with parents' `MultipleObjectsReturned`, falling back to the imported `MultipleObjectsReturned`.

6. **Inheritance of Meta options:** If a non-abstract parent has `_meta` and the child's `Meta` does not explicitly define `ordering`, inherits the parent's `ordering`. Same for `get_latest_by`.

7. **Proxy model setup:** Determines `is_proxy = new_class._meta.proxy`. If proxy and base is swapped, raises `TypeError`. For proxy models:
   - Iterates parents to find exactly one non-abstract model base (abstract parents with fields raise `TypeError`; multiple non-abstract bases raise `TypeError`).
   - Calls `new_class._meta.setup_proxy(base)` and sets `new_class._meta.concrete_model = base._meta.concrete_model`.
   - If not a proxy, sets `new_class._meta.concrete_model = new_class`.

8. **Add contributable attributes:** Iterates `contributable_attrs` and calls `new_class.add_to_class(obj_name, obj)` for each.

9. **Field collection & parent link setup:** Collects all local fields (`local_fields`, `local_many_to_many`, `private_fields`) into a set of field names. Then iterates parents in reverse order (including the new class itself):
   - Skips bases without `_meta` and concrete non-matching parents.
   - For abstract or self: locates `OneToOneField` instances and records them in `parent_links` keyed by `make_model_tuple(related)`.

10. **Inheritance from parent classes (MRO iteration):** Iterates through `new_class.mro()`:
    - Non-abstract parents: checks for field name clashes between locally declared fields and base class fields; raises `FieldError` on clash. Records inherited attribute names. Creates an auto-generated `OneToOneField` (`'{base_model_name}_ptr'`) with `on_delete=CASCADE`, `auto_created=True`, `parent_link=True` for each concrete non-abstract parent (unless it's a proxy or the field already exists). Stores in `new_class._meta.parents`.
    - Abstract parents: copies inherited fields from the abstract base if not overridden; updates `base_parents` for any OneToOneField parent links. Propagates non-abstract parent chain via `new_class._meta.parents.update(base_parents)`.
    - Private fields (e.g., `GenericForeignKey`): deep-copies and adds to the class; raises `FieldError` if a local field shadows a private field from a non-abstract base.

11. **Index deep-copy:** Deep-copies all indexes in `new_class._meta.indexes` so that index names are unique when extending abstract models.

12. **Abstract model early return:** If the model is abstract, sets `attr_meta.abstract = False`, assigns `new_class.Meta = attr_meta`, and returns (abstract models cannot be instantiated).

13. **Final preparation for concrete models:** Calls `new_class._prepare()`, then registers the model with its app via `new_class._meta.apps.register_model(...)`. Returns the new class.

### Method: `add_to_class(cls, name, value)`

If `_has_contribute_to_class(value)` is true, calls `value.contribute_to_class(cls, name)`. Otherwise, sets the attribute directly via `setattr(cls, name, value)`.

### Method: `_prepare(cls)`

Called after `_meta` has been populated. Performs post-initialization setup:
1. Calls `opts._prepare(cls)`.
2. If `opts.order_with_respect_to` is set, creates `get_next_in_order` and `get_previous_in_order` methods via `partialmethod(cls._get_next_or_previous_in_order, ...)`. If the order field has a `remote_field`, schedules a lazy operation to create foreign order accessors on the related model.
3. Sets a default docstring if none exists: `'{ClassName}({field1}, {field2}, ...)'`.
4. Overrides `get_absolute_url` if `settings.ABSOLUTE_URL_OVERRIDES` has an entry for this model's label.
5. If no managers are defined and no field is named `'objects'`, auto-creates a `Manager()` instance with `auto_created=True` and adds it as `'objects'`. Raises `ValueError` if a field named `'objects'` exists without a custom manager.
6. Sets names on unnamed indexes via `index.set_name_with_model(cls)`.
7. Sends the `class_prepared` signal.

### Property: `_base_manager(cls)` → Returns `cls._meta.base_manager`.

### Property: `_default_manager(cls)` → Returns `cls._meta.default_manager`.

---

## Class: `ModelStateFieldsCacheDescriptor`

A descriptor used for lazy initialization of a fields cache on `ModelState`:
- **`__get__(self, instance, cls=None)`** — If `instance` is `None`, returns `self` (class-level access). Otherwise, initializes `instance.fields_cache = {}` and returns it.

---

## Class: `ModelState`

Stores the runtime state of a model instance:
- **`db`** (class attribute) — Default `None`. The database alias the instance was loaded from / saved to.
- **`adding`** (class attribute) — Default `True`. When `False`, indicates the instance has been persisted; affects uniqueness validation for objects with explicit PKs.
- **`fields_cache`** — A descriptor (`ModelStateFieldsCacheDescriptor`) that lazily initializes an empty dict on first access, used to cache field values.

---

## Class: `Model(metaclass=ModelBase)`

The base class for all Django ORM models.

### Attributes (class-level)
- **`_meta`** — An `Options` instance, set by the metaclass during class creation.
- **`DoesNotExist`** — Per-model exception class, created by the metaclass.
- **`MultipleObjectsReturned`** — Per-model exception class, created by the metaclass.
- **`objects`** — A default `Manager()` instance (auto-created if none specified), set by `_prepare()`.
- **`_state`** — An instance-level `ModelState`, initialized in `__init__()`.

### Method: `__init__(self, *args, **kwargs)`

Initializes a model instance. Steps:
1. Sends `pre_init` signal with `sender=cls`, `args=args`, `kwargs=kwargs`.
2. Creates `self._state = ModelState()`.
3. Validates that positional args do not exceed the number of concrete fields; raises `IndexError` if they do.
4. **Positional argument path** (no kwargs): Iterates over `(val, field)` pairs from `zip(args, opts.concrete_fields)`, skipping any value equal to `DEFERRED`. Sets each field's attribute via `_setattr(self, field.attname, val)`.
5. **Keyword argument path**: First iterates positional args against `opts.fields` (all fields), setting attributes and popping matched names from kwargs. Then processes remaining fields:
   - For related fields (`ForeignObjectRel`): tries to pop the field name from kwargs (expecting a related object instance); if not found, pops the attname (expecting an ID); if neither exists, uses `field.get_default()`.
   - For non-related fields: tries to pop the attname from kwargs; falls back to `field.get_default()`.
   - If a related object was passed and is not `DEFERRED`, sets it via the field name (not attname) so that the `RelatedObjectDescriptor` properly caches it.
6. Handles remaining kwargs: checks if each key matches a property name or a real field; if so, sets the attribute (unless value is `DEFERRED`) and deletes from kwargs. Any leftover kwargs raise `TypeError` with an "unexpected keyword argument" message.
7. Calls `super().__init__()`.
8. Sends `post_init` signal with `sender=cls`, `instance=self`.

### Method: `from_db(cls, db, field_names, values)` → `Model` (classmethod)

Creates a model instance from database-fetched data:
1. If the number of values doesn't match the number of concrete fields, maps each value to either its actual value (if the field's attname is in `field_names`) or `DEFERRED` (if deferred).
2. Creates a new instance via `cls(*values)`.
3. Sets `_state.adding = False` and `_state.db = db`.
4. Returns the new instance.

### Method: `__repr__(self)` → `str`

Returns `'<ClassName: str(self)>'`.

### Method: `__str__(self)` → `str`

Returns `'{ClassName} object ({pk})'`.

### Method: `__eq__(self, other)` → `bool | NotImplemented`

Compares two model instances for equality:
- Returns `NotImplemented` if `other` is not a `Model` instance.
- Returns `False` if the concrete models differ (`self._meta.concrete_model != other._meta.concrete_model`).
- If `self.pk` is `None`, returns `self is other` (identity comparison).
- Otherwise, compares primary key values: `my_pk == other.pk`.

### Method: `__hash__(self)` → `int`

Returns `hash(self.pk)`. Raises `TypeError` if `self.pk` is `None` (unsaved instances are unhashable).

### Method: `__reduce__(self)` → `tuple`

Supports pickling. Returns `(model_unpickle, (class_id,), data)` where:
- `data = self.__getstate__()` (which returns `self.__dict__`).
- `data[DJANGO_VERSION_PICKLE_KEY] = get_version()`.
- `class_id = (self._meta.app_label, self._meta.object_name)`.

### Method: `__getstate__(self)` → `dict`

Returns `self.__dict__` for pickling.

### Method: `__setstate__(self, state)`

Restores a pickled model instance:
1. Checks the Django version stored in `state[DJANGO_VERSION_PICKLE_KEY]` against the current version; emits a `RuntimeWarning` if they differ or are missing.
2. Updates `self.__dict__.update(state)`.

### Property: `pk` (getter/setter)

- **Getter `_get_pk_val(self, meta=None)`** — Returns `getattr(self, meta.pk.attname)` where `meta` defaults to `self._meta`.
- **Setter `_set_pk_val(self, value)`** — For each parent link field in `self._meta.parents`, if the parent's PK is `None` and the link field has a value, syncs them. Then sets `self._meta.pk.attname` to `value`. Returns the result of `setattr()`.

### Method: `get_deferred_fields(self)` → `set[str]`

Returns a set of attname strings for concrete fields whose names are not present in `self.__dict__` (i.e., deferred fields).

### Method: `refresh_from_db(self, using=None, fields=None)`

Reloads field values from the database:
1. If `fields` is `None`, clears `_prefetched_objects_cache = {}`. Otherwise, removes any fields present in the prefetch cache from both the cache and the `fields` list; returns early if no fields remain. Raises `ValueError` if any field name contains `LOOKUP_SEP` (relations/transforms not allowed).
2. Builds a query via `self.__class__._base_manager.db_manager(using, hints={'instance': self}).filter(pk=self.pk)`.
3. Determines which fields to reload: if `fields` is provided, uses `.only(*fields)`; else if there are deferred fields, computes the non-deferred concrete field attnames and uses `.only()` on those.
4. Executes `db_instance_qs.get()`, then for each concrete field in the DB instance that was loaded (not deferred), sets the attribute on `self` via `setattr(self, field.attname, getattr(db_instance, field.attname))`. Clears cached foreign keys and related object caches as needed.
5. Updates `self._state.db = db_instance._state.db`.

### Method: `serializable_value(self, field_name)` → `Any`

Returns the value of a field for serialization purposes:
1. Tries to get the `Field` object via `self._meta.get_field(field_name)`. If it doesn't exist (`FieldDoesNotExist`), returns `getattr(self, field_name)` (the raw attribute).
2. Otherwise, returns `getattr(self, field.attname)` — for foreign keys, this returns the ID rather than the related object.

### Method: `save(self, force_insert=False, force_update=False, using=None, update_fields=None)`

Saves the current instance to the database:
1. **Related object validation:** Iterates concrete fields that are relations and cached on self. For each:
   - If the related object is not set (or is `None`), skips.
   - If the related object's `pk` is `None`, deletes any cached reverse reference from the related object and raises `ValueError` ("save() prohibited to prevent data loss due to unsaved related object").
   - If `self`'s FK attname is `None` but the related object has a PK, sets it from `obj.pk`.
   - If the relationship's target field value differs from the current attname, clears the cached relationship.
2. Validates that `force_insert` and (`force_update` or `update_fields`) are not both set; raises `ValueError` if so.
3. Determines the database alias via `router.db_for_write()`.
4. If `update_fields` is provided: validates that all field names exist in the model (checking against `_meta.fields` for both name and attname); raises `ValueError` for non-model/m2m fields. Empty `update_fields` causes an early return.
5. If no explicit `update_fields` but deferred fields exist and saving to the same database, computes `loaded_fields` (non-PK concrete fields without a `through` attribute minus deferred ones) and sets `update_fields = frozenset(loaded_fields)`.
6. Delegates to `self.save_base(...)`.

### Method: `save_base(self, raw=False, force_insert=False, force_update=False, using=None, update_fields=None)`

Handles the core save logic (called once per save operation):
1. Validates assertions: not both `force_insert` and (`force_update` or `update_fields`); `update_fields` is either `None` or non-empty.
2. Determines database alias via `router.db_for_write()`.
3. Resolves proxy models: if the class is a proxy, uses its concrete model for saving but tracks the original (proxy) class as `origin` for signal sending.
4. Sends `pre_save` signal (if not auto-created) with `sender=origin`, `instance=self`, `raw`, `using`, `update_fields`.
5. Enters a transaction context: uses `transaction.atomic(using, savepoint=False)` if there are parent models to save; otherwise `transaction.mark_for_rollback_on_error(using)`.
6. Inside the transaction:
   - If not `raw`, calls `_save_parents(cls, using, update_fields)` which recursively saves parent model instances and returns whether a parent was newly inserted.
   - Calls `_save_table(raw, cls, force_insert or parent_inserted, force_update, using, update_fields)`.
7. After the transaction: sets `self._state.db = using` and `self._state.adding = False`.
8. Sends `post_save` signal (if not auto-created) with `sender=origin`, `instance=self`, `created=(not updated)`, `update_fields`, `raw`, `using`.

### Method: `_save_parents(self, cls, using, update_fields)` → `bool`

Saves all parent model instances in a multi-table inheritance hierarchy:
1. For each parent and its link field in `meta.parents`:
   - Syncs the parent's PK from the link field if the parent's PK is `None` but the link field has a value.
   - Recursively calls `_save_parents(cls=parent, ...)` to handle grandparent chains; captures whether the parent was newly inserted.
   - Calls `_save_table()` for the parent with `force_insert=parent_inserted`. If not updated, marks this level as inserted.
   - Sets the link field's attname on self to the parent's PK value.
   - If the field is cached on self, deletes the cached value.
2. Returns whether any parent was newly inserted.

### Method: `_save_table(self, raw=False, cls=None, force_insert=False, force_update=False, using=None, update_fields=None)` → `bool`

Performs the actual INSERT or UPDATE for a single table:
1. Collects non-PK concrete local fields into `non_pks`. If `update_fields` is set, filters to only those fields whose name or attname appears in it.
2. Gets/sets the PK value via `_get_pk_val()` and `meta.pk.get_pk_value_on_save()`. Raises `ValueError` if no PK and force_update/update_fields are set.
3. If not raw, not force_insert, adding, and the PK field has a default (not `NOT_PROVIDED`), forces an INSERT instead of UPDATE.
4. **UPDATE path** (PK is set and not force_insert): Builds values list from non-PK fields (`f.pre_save(self, False)` for each). Calls `_do_update()` with the base query, PK value, values, update_fields, and forced_update flag. If `force_update` or `update_fields` is set but no rows were affected, raises `DatabaseError`.
5. **INSERT path** (if not updated): If `order_with_respect_to` is configured, computes the next `_order` value via an aggregate of `Max('_order') + 1` with a `Coalesce(..., Value(0))` fallback. Filters fields to exclude auto-fields if PK is not set. Calls `_do_insert()` and sets returned values on field attributes.
6. Returns whether the row was updated (not inserted).

### Method: `_do_update(self, base_qs, using, pk_val, values, update_fields, forced_update)` → `bool`

Attempts an UPDATE query:
1. Filters the base queryset by PK. If no values to update, returns `True` if `update_fields is not None` (explicit field list) or checks existence via `filtered.exists()`.
2. If `select_on_save` is enabled and not forced: checks row exists first, then does `_update(values)`; if zero rows affected, re-checks existence to distinguish between "row deleted" and "database returned 0".
3. Otherwise, returns whether `_update(values) > 0`.

### Method: `_do_insert(self, manager, using, fields, returning_fields, raw)` → `list`

Performs an INSERT via `manager._insert([self], fields=fields, returning_fields=returning_fields, using=using, raw=raw)`. Returns the list of returned data (e.g., auto-generated PK values).

### Method: `delete(self, using=None, keep_parents=False)` → tuple of counts

Deletes this instance and all related objects:
1. Determines database via `router.db_for_write()`. Asserts that `self.pk` is not `None`; raises `AssertionError` if it is.
2. Creates a `Collector(using=using)`, collects `[self]` (optionally keeping parent references), then calls `collector.delete()` which returns the deletion counts.

### Method: `_get_FIELD_display(self, field)` → `str`

Returns the human-readable display value for a field with `choices`:
1. Gets the raw value via `getattr(self, field.attname)`.
2. Builds a choices dictionary from `field.flatchoices`, keyed by `make_hashable(value)`.
3. Returns `force_str(choices_dict.get(make_hashable(value), value), strings_only=True)` — falls back to the raw value if not found in choices.

### Method: `_get_next_or_previous_by_FIELD(self, field, is_next, **kwargs)` → `Model`

Returns the next or previous model instance ordered by a specific field:
1. Raises `ValueError` if `self.pk` is unset (unsaved object).
2. Determines operator (`'gt'` for next, `'lt'` for previous) and sort order prefix (`''` or `'-'`).
3. Builds a Q-object that matches either `field > param` OR (`field == param AND pk > self.pk`) to handle ties correctly.
4. Queries via the default manager on the instance's database, filters by kwargs and the Q-object, orders by field (and PK for tie-breaking), and returns the first result. Raises `DoesNotExist` if no match found.

### Method: `_get_next_or_previous_in_order(self, is_next)` → `Model`

Returns the next or previous model instance in ordering-with-respect-to order:
1. Uses a cache attribute (`__{is_next}_order_cache`). If not present:
   - Builds filter args from `order_with_respect_to`.
   - Queries for objects with `_order > self._order` (or `<`) using a subquery on the same model's values, orders by `_order`, and gets the single result.
   - Caches the result.
2. Returns the cached or freshly fetched object.

### Method: `prepare_database_save(self, field)` → `Any`

Prepares a saved model instance for use in an ORM query on a related field:
1. Raises `ValueError` if `self.pk` is `None`.
2. Returns the remote field's related field attname value (e.g., the FK ID).

### Method: `clean(self)`

A hook for extra model-wide validation after per-field cleaning. Default implementation does nothing (`pass`). Any `ValidationError` raised will be associated with `NON_FIELD_ERRORS`.

### Method: `validate_unique(self, exclude=None)` → validates uniqueness constraints

Checks all unique constraints on the model and raises `ValidationError` if any fail:
1. Calls `_get_unique_checks(exclude=exclude)` to get `(unique_checks, date_checks)`.
2. Runs `_perform_unique_checks(unique_checks)` and `_perform_date_checks(date_checks)`, merging errors from both.
3. If there are any errors, raises `ValidationError(errors)`.

### Method: `_get_unique_checks(self, exclude=None)` → `(list[tuple[type, tuple[str]]], list[tuple])`

Builds a list of unique checks to perform:
1. Collects `unique_together` constraints from the model and all parent classes (non-abstract). Skips any check where a field name is in `exclude`.
2. Collects `UniqueConstraint` entries from `_meta.constraints` that have no condition (partial constraints can't be validated) and no excluded fields.
3. Builds date-based checks for fields with `unique_for_date`, `unique_for_year`, or `unique_for_month` attributes, skipping excluded fields.
4. Returns `(unique_checks, date_checks)`.

### Method: `_perform_unique_checks(self, unique_checks)` → `dict[str, list]`

Performs each unique check:
1. For each `(model_class, unique_check_tuple)`: builds lookup kwargs from the model's field values. Skips fields with `None` or empty-string values (if backend interprets empty as null). Skips primary key checks when editing an existing object (`not self._state.adding`).
2. If all fields in the check were skipped, continues to next check.
3. Queries for matching objects via `_default_manager.filter(**lookup_kwargs)`. Excludes the current instance if editing (using `model_class`'s PK, not `self.pk`, to handle model inheritance).
4. If a match exists: uses the field name as error key for single-field checks; uses `NON_FIELD_ERRORS` for multi-field (`unique_together`) checks. Appends the result of `self.unique_error_message(model_class, unique_check)`.

### Method: `_perform_date_checks(self, date_checks)` → `dict[str, list]`

Performs date-based uniqueness checks:
1. For each `(model_class, lookup_type, field_name, unique_for_field)`: gets the date value from `unique_for`. Skips if `None`.
2. Builds lookup kwargs: for `'date'` type, splits into day/month/year; otherwise uses `{field}__{lookup_type}` (e.g., `year`, `month`). Adds the field's own value as a kwarg.
3. Queries and excludes current instance if editing. If match found, appends error from `self.date_error_message()`.

### Method: `date_error_message(self, lookup_type, field_name, unique_for)` → `ValidationError`

Creates a `ValidationError` with message code `'unique_for_date'`, including params for model, field labels, and date field info.

### Method: `unique_error_message(self, model_class, unique_check)` → `ValidationError`

Creates a `ValidationError`:
- For single-field checks: uses the field's `'unique'` error message with code `'unique'`.
- For multi-field (`unique_together`) checks: builds a human-readable label list and returns a message like `"{model_name} with this {field_labels} already exists."` with code `'unique_together'`.

### Method: `full_clean(self, exclude=None, validate_unique=True)` → validates the entire model

Runs all validation steps in sequence:
1. Calls `clean_fields(exclude=exclude)`, catching `ValidationError` and merging errors.
2. Always calls `clean()` (even if field validation failed), catching and merging any `ValidationError`.
3. If `validate_unique` is true: builds an exclude list from fields that already have errors (excluding `NON_FIELD_ERRORS`), then calls `validate_unique(exclude=exclude)`, catching and merging errors.
4. If any errors accumulated, raises `ValidationError(errors)`.

### Method: `clean_fields(self, exclude=None)` → validates individual field values

1. Iterates all fields in `_meta.fields`. Skips excluded fields and blank fields with empty values (`f.blank` and `raw_value in f.empty_values`).
2. For each remaining field, calls `f.clean(raw_value, self)` and sets the result back on the instance via `setattr(self, f.attname, ...)`. Catches `ValidationError` and collects errors by field name.
3. If any errors, raises `ValidationError(errors)`.

### Method: `check(cls, **kwargs)` → `list[checks.Error]` (classmethod)

Runs all system checks for the model class:
1. Always runs: `_check_swappable()`, `_check_model()`, `_check_managers(**kwargs)`.
2. If not swapped: additionally runs `_check_fields()`, `_check_m2m_through_same_relationship()`, `_check_long_column_names()`.
3. Runs clash checks: `_check_id_field()`, `_check_field_name_clashes()`, `_check_model_name_db_lookup_clashes()`, `_check_property_name_related_field_accessor_clashes()`, `_check_single_primary_key()`. If any clash errors exist, skips `_check_column_name_clashes()` to avoid redundant reports.
4. Always runs (if not swapped): `_check_index_together()`, `_check_unique_together()`, `_check_indexes()`, `_check_ordering()`, `_check_constraints()`.
5. Returns the combined list of all errors/warnings.

### Method: `_check_swappable(cls)` → `list[checks.Error]` (classmethod)

Validates that a swapped model exists:
- If `cls._meta.swapped` is set, tries to resolve it via `apps.get_model()`. Raises error E001 if the string is not in `'app_label.app_name'` format; raises error E002 if the referenced model doesn't exist or is abstract.

### Method: `_check_model(cls)` → `list[checks.Error]` (classmethod)

Validates proxy model constraints:
- If the model is a proxy and has local fields or local many-to-many fields, returns error E017 ("Proxy model contains model fields").

### Method: `_check_managers(cls, **kwargs)` → `list[checks.Error]` (classmethod)

Iterates all managers in `cls._meta.managers`, calling each manager's `check(**kwargs)` and collecting errors.

### Method: `_check_fields(cls, **kwargs)` → `list[checks.Error]` (classmethod)

Calls `field.check(**kwargs)` for each local field and `field.check(from_model=cls, **kwargs)` for each local many-to-many field, collecting all errors.

### Method: `_check_m2m_through_same_relationship(cls)` → `list[checks.Error]` (classmethod)

Detects duplicate M2M relationships through the same intermediate model:
- Filters to M2M fields where both the target model and through model are actual model classes.
- Builds a signature tuple `(target_model, cls, through_model, through_fields)` for each. If a signature is seen twice, returns error E003 ("two identical many-to-many relations").

### Method: `_check_id_field(cls)` → `list[checks.Error]` (classmethod)

Validates that any field named `'id'` has `primary_key=True` when the model's PK is also named `'id'`:
- If a non-PK field named `'id'` exists and `cls._meta.pk.name == 'id'`, returns error E004.

### Method: `_check_field_name_clashes(cls)` → `list[checks.Error]` (classmethod)

Detects field name shadowing in multi-table inheritance:
1. Iterates parent classes, collecting all local fields into a `used_fields` dict keyed by both name and attname. Reports error E005 if a parent's field clashes with another parent's field.
2. Then checks the model's own local fields against accumulated names from parents (including auto-generated fields). Reports error E006 for any clash, except the special case where both are named `'id'` and defined on the same model (handled by `_check_id_field`).

### Method: `_check_column_name_clashes(cls)` → `list[checks.Error]` (classmethod)

Detects duplicate auto-generated column names among local fields:
- Iterates all local fields, collecting their database column names. Reports error E007 if a column name is used by more than one field.

### Method: `_check_model_name_db_lookup_clashes(cls)` → `list[checks.Error]` (classmethod)

Validates model naming conventions:
- Error E023 if the class name starts or ends with `'_'`.
- Error E024 if the class name contains `LOOKUP_SEP` (`'__'`).

### Method: `_check_property_name_related_field_accessor_clashes(cls)` → `list[checks.Error]` (classmethod)

Detects property names that conflict with related field accessors:
- Compares `_meta._property_names` against attname getters for relation fields. Reports error E025 on any clash.

### Method: `_check_single_primary_key(cls)` → `list[checks.Error]` (classmethod)

Ensures at most one local field has `primary_key=True`. Returns error E026 if more than one is found.

### Method: `_check_index_together(cls)` → `list[checks.Error]` (classmethod)

Validates the `index_together` option:
- Error E008 if not a list/tuple.
- Error E009 if any element is not a list/tuple.
- Otherwise, validates each field list via `_check_local_fields()`.

### Method: `_check_unique_together(cls)` → `list[checks.Error]` (classmethod)

Validates the `unique_together` option with the same structure as `_check_index_together`:
- Error E010 if not a tuple/list.
- Error E011 if any element is not a tuple/list.
- Validates each field list via `_check_local_fields()`.

### Method: `_check_indexes(cls)` → `list[checks.Error]` (classmethod)

Validates custom indexes defined in `_meta.indexes`:
- Error E033 if an index name starts with `'_'` or a digit.
- Error E034 if the index name exceeds `index.max_name_length`.
- Validates referenced fields via `_check_local_fields()`.

### Method: `_check_local_fields(cls, fields, option)` → `list[checks.Error]` (classmethod)

Validates that field names in a list refer to local, non-M2M fields on the model:
- Builds a forward fields map from `_meta._get_fields(reverse=False)`.
- Error E012 if a field name doesn't exist.
- Error E013 if it refers to a `ManyToManyField` (not permitted in ordering/indexes/etc.).
- Error E016 if the field is not local to this model (multi-table inheritance issue).

### Method: `_check_ordering(cls)` → `list[checks.Error]` (classmethod)

Validates the `ordering` option:
- Error E021 if both `ordering` and `order_with_respect_to` are set.
- Returns early if `order_with_respect_to` is set or `ordering` is empty/falsy.
- Error E014 if `ordering` is not a list/tuple.
- Filters out expressions (`?`) and non-string items, strips leading `'-'` for reverse order.
- Splits related-field lookups (containing `LOOKUP_SEP`) from simple field names. For related fields, traverses the relation chain via `get_path_info()`, reporting error E015 for nonexistent fields/lookups.
- For simple fields, checks against a valid set of field names and attnames; reports error E015 for invalid or M2M references.

### Method: `_check_long_column_names(cls)` → `list[checks.Error]` (classmethod)

Checks that auto-generated column names don't exceed database limits:
- Finds the minimum max name length across all configured databases where the model will be created.
- Error E018 if any local field's auto-generated column name exceeds this limit.
- Error E019 for M2M through-table columns that are too long.

### Method: `_check_constraints(cls)` → `list[checks.Warning]` (classmethod)

Checks database support for check constraints:
- For each database where the model will be created, if the database doesn't support table-level check constraints and the model has any `CheckConstraint` entries, returns warning W027.

---

## Helper Functions (Curried Model Methods — module-level after class)

### `method_set_order(self, ordered_obj, id_list, using=None)`

Sets the `_order` field for a set of objects in an `order_with_respect_to` hierarchy:
1. Determines database alias (`using`, defaulting to `DEFAULT_DB_ALIAS`).
2. Gets forward-related filter args from `order_wrt.get_forward_related_filter(self)`.
3. Performs a `bulk_update()` on the ordered object's manager, setting `_order` to enumerate over `id_list` (0-indexed).

### `method_get_order(self, ordered_obj)` → `QuerySet`

Returns the primary key values of objects in an `order_with_respect_to` hierarchy:
1. Gets forward-related filter args from `order_wrt.get_forward_related_filter(self)`.
2. Returns a `values_list(pk_name, flat=True)` query filtered by those args.

### `make_foreign_order_accessors(model, related_model)`

Dynamically adds two methods to `related_model`:
- `'get_{model.__name__.lower()}_order'` — bound via `partialmethod(method_get_order, model)`.
- `'set_{model.__name__.lower()}_order'` — bound via `partialmethod(method_set_order, model)`.

Used for lazy accessor creation on models that have `order_with_respect_to` pointing to another model.

### `model_unpickle(model_id)` → `Model`

Restores a pickled Model subclass with deferred fields:
1. If `model_id` is a tuple `(app_label, object_name)`, resolves the actual class via `apps.get_model(*model_id)`. Otherwise (backwards compat), uses `model_id` directly as the cached model class.
2. Returns `model.__new__(model)` — creates an uninitialized instance that will be populated by `__setstate__()`.

### `model_unpickle.__safe_for_unpickle__ = True`

Marks the function as safe for unpickling, preventing Django's pickle safety checks from rejecting it.

## django/db/models/options.py
Now I have read every line of the file. Here is the complete specification:

---

## Module-Level Preamble

### Imports

```python
import bisect
import copy
import inspect
from collections import defaultdict

from django.apps import apps
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import connections
from django.db.models import Manager
from django.db.models.fields import AutoField
from django.db.models.fields.proxy import OrderWrt
from django.db.models.query_utils import PathInfo
from django.utils.datastructures import ImmutableList, OrderedSet
from django.utils.functional import cached_property
from django.utils.text import camel_case_to_spaces, format_lazy
from django.utils.translation import override
```

### Constants & Globals

- **`PROXY_PARENTS = object()`** — Sentinel value used as a third `include_parents` option to mean "include parents only up to the concrete model in the proxy chain."
- **`EMPTY_RELATION_TREE = ()`** — Empty tuple sentinel returned when no relation tree is cached.
- **`IMMUTABLE_WARNING`** — A string template: `"The return type of '%s' should never be mutated. If you want to manipulate this list for your own use, make a copy first."` Used as the warning message for `ImmutableList`.
- **`DEFAULT_NAMES`** — A tuple of 26 strings listing all valid `'class Meta'` attribute names: `'verbose_name', 'verbose_name_plural', 'db_table', 'ordering', 'unique_together', 'permissions', 'get_latest_by', 'order_with_respect_to', 'app_label', 'db_tablespace', 'abstract', 'managed', 'proxy', 'swappable', 'auto_created', 'index_together', 'apps', 'default_permissions', 'select_on_save', 'default_related_name', 'required_db_features', 'required_db_vendor', 'base_manager_name', 'default_manager_name', 'indexes', 'constraints'`.

### Functions

#### `normalize_together(option_together)`
Normalizes an `option_together` value (used for `unique_together` / `index_together`) into a tuple of tuples. If the argument is falsy, returns `()`. If it is not a `tuple` or `list`, raises `TypeError` and falls through to return the original verbatim. If the first element is itself not a `tuple`/`list` (i.e., a single flat tuple like `('field_a', 'field_b')`), wraps it in an outer tuple: `(option_together,)`. Finally, converts every inner element to a plain `tuple` and returns the result as a `tuple` of tuples. If any step raises `TypeError`, returns the original value unchanged (the check framework handles validation later).

#### `make_immutable_fields_list(name, data)`
Returns an `ImmutableList(data, warning=IMMUTABLE_WARNING % name)`. Wraps the iterable `data` into a read-only list that emits a warning on mutation attempts.

---

## Class: `Options`

### Inheritance & Metaclass
No explicit base class or metaclass; inherits from `object`.

### Class-Level Attributes

- **`FORWARD_PROPERTIES = {'fields', 'many_to_many', 'concrete_fields', 'local_concrete_fields', '_forward_fields_map', 'managers', 'managers_map', 'base_manager', 'default_manager'}`** — Set of cached property names that are forward-only caches.
- **`REVERSE_PROPERTIES = {'related_objects', 'fields_map', '_relation_tree'}`** — Set of cached property names that involve reverse relations.
- **`default_apps = apps`** — Reference to the global Django app registry, used as a default for `self.apps`.

### Instance Attributes (initialized in `__init__`)

All initialized in `__init__(self, meta, app_label=None)`:

| Attribute | Type / Value | Description |
|---|---|---|
| `_get_fields_cache` | `{}` | Dict caching results of `_get_fields()` calls. |
| `local_fields` | `[]` | List of forward fields defined directly on the model, sorted by creation order via bisect. |
| `local_many_to_many` | `[]` | List of M2M fields defined directly on the model. |
| `private_fields` | `[]` | List of private (reverse-only) fields. |
| `local_managers` | `[]` | Managers defined locally on this model class. |
| `base_manager_name` | `None` | Name of the base manager to use. |
| `default_manager_name` | `None` | Name of the default manager. |
| `model_name` | `None` | Lowercase model class name, set in `contribute_to_class`. |
| `verbose_name` | `None` | Human-readable name, derived from camel case in `contribute_to_class`. |
| `verbose_name_plural` | `None` | Plural form; auto-set to lazy `'{}s'` format of verbose_name if not provided. |
| `db_table` | `''` | Database table name. |
| `ordering` | `[]` | Default field ordering for querysets. |
| `_ordering_clash` | `False` | Flag set when both `ordering` and `order_with_respect_to` are specified. |
| `indexes` | `[]` | List of index objects. |
| `constraints` | `[]` | List of constraint objects. |
| `unique_together` | `[]` | Normalized tuple-of-tuples for unique constraints. |
| `index_together` | `[]` | Normalized tuple-of-tuples for index-on-combinations. |
| `select_on_save` | `False` | Whether to SELECT before UPDATE on save. |
| `default_permissions` | `('add', 'change', 'delete', 'view')` | Default permission set. |
| `permissions` | `[]` | Extra permissions defined in Meta. |
| `object_name` | `None` | Camel-case model class name, set in `contribute_to_class`. |
| `app_label` | `app_label` (from arg) or `None` | Application label. |
| `get_latest_by` | `None` | Field name for `Model._base_manager.latest()`. |
| `order_with_respect_to` | `None` | FK field name for admin ordering; resolved to a field object in `_prepare`. |
| `db_tablespace` | `settings.DEFAULT_TABLESPACE` | Database tablespace. |
| `required_db_features` | `[]` | List of database feature names required for migration. |
| `required_db_vendor` | `None` | Required DB vendor string (e.g., `'postgresql'`). |
| `meta` | `meta` (from arg) | The raw `class Meta` object; deleted after processing in `contribute_to_class`. |
| `pk` | `None` | The primary key field instance. |
| `auto_field` | `None` | AutoField if one was auto-created. |
| `abstract` | `False` | Whether the model is abstract. |
| `managed` | `True` | Whether Django should create/drop tables for this model. |
| `proxy` | `False` | Whether this is a proxy model. |
| `proxy_for_model` | `None` | The concrete model this proxies (if any). |
| `concrete_model` | `None` | The ultimate concrete model in the proxy chain. |
| `swappable` | `None` | Setting name for swappable models (e.g., `'AUTH_USER_MODEL'`). |
| `parents` | `{}` | Dict mapping parent model class → pointer field for multi-table inheritance. |
| `auto_created` | `False` | Whether this model was auto-created (e.g., through M2M intermediate). |
| `related_fkey_lookups` | `[]` | Internal list of ForeignKey lookups from other models. |
| `apps` | `self.default_apps` (`apps`) | App registry reference; can be overridden for custom model sets. |
| `default_related_name` | `None` | Default related name for reverse relations. |

### Properties

#### `label` → `str`
Returns `'%s.%s' % (self.app_label, self.object_name)`.

#### `label_lower` → `str`
Returns `'%s.%s' % (self.app_label, self.model_name)`.

#### `app_config` → `AppConfig | None`
Returns `self.apps.app_configs.get(self.app_label)` without going through `get_app_config()` to avoid triggering imports.

#### `installed` → `bool`
Returns `True` if `self.app_config is not None`.

#### `verbose_name_raw` → `str`
Returns the untranslated verbose name by calling `str(self.verbose_name)` inside a `with override(None):` context (disables translation).

#### `swapped` → `str | None`
Checks whether this model has been swapped out. If `self.swappable` is set, reads the corresponding setting via `getattr(settings, self.swappable, None)`. Parses the setting value as `'app_label.model_name'`. Returns the setting value if it points to a different model (case-insensitive comparison against `self.label_lower`); otherwise returns `None`. If the setting format is invalid, returns the raw setting string.

#### `managers` → `ImmutableList[Manager]`
A `@cached_property`. Iterates over all bases in `self.model.mro()` that have a `_meta` attribute. For each base, iterates its `local_managers`, skipping those whose `.name` has already been seen (tracked in a set). Copies each manager via `copy.copy()`, sets `manager.model = self.model`, and collects tuples of `(depth, creation_counter, manager)`. Returns them sorted by `(depth, creation_counter)` as an immutable list.

#### `managers_map` → `dict[str, Manager]`
A `@cached_property`. Builds `{manager.name: manager for manager in self.managers}`.

#### `base_manager` → `Manager`
A `@cached_property`. If `self.base_manager_name` is set, looks it up in `self.managers_map`; raises `ValueError` if not found. Otherwise, walks the model MRO (`self.model.mro()[1:]`) to find the first parent with `_meta`, and uses that parent's `base_manager.name` (if it differs from `'_base_manager'`). If still no name is found, creates a fresh `Manager()`, sets `.name = '_base_manager'`, `.model = self.model`, `.auto_created = True`, and returns it.

#### `default_manager` → `Manager | None`
A `@cached_property`. If `self.default_manager_name` is not set and there are no local managers, walks the MRO to find a parent's `default_manager_name`. Looks up that name in `managers_map`; raises `ValueError` if not found. If still no name but `self.managers` exists, returns `self.managers[0]`. Returns `None` otherwise.

#### `fields` → `ImmutableList[Field]`
A `@cached_property`. Returns all forward fields on the model and its parents (excluding M2M). Filters out: (1) many-to-many fields (`f.is_relation and f.many_to_many`), (2) generic relations (`f.is_relation and f.one_to_many`), (3) generic foreign keys (`f.is_relation and f.many_to_one and not hasattr(f.remote_field, 'model') or not f.remote_field.model`). Uses `self._get_fields(reverse=False)` as the source.

#### `concrete_fields` → `ImmutableList[Field]`
A `@cached_property`. Returns `[f for f in self.fields if f.concrete]`.

#### `local_concrete_fields` → `ImmutableList[Field]`
A `@cached_property`. Returns `[f for f in self.local_fields if f.concrete]`.

#### `many_to_many` → `ImmutableList[Field]`
A `@cached_property`. Returns all M2M fields on the model and its parents: `[f for f in self._get_fields(reverse=False) if f.is_relation and f.many_to_many]`.

#### `related_objects` → `ImmutableList`
A `@cached_property`. Returns reverse relation objects pointing to this model. Calls `_get_fields(forward=False, reverse=True, include_hidden=True)` and filters: keeps fields where `not obj.hidden or obj.field.many_to_many`.

#### `_forward_fields_map` → `dict[str, Field]`
A `@cached_property`. Builds a dict mapping each forward field's `.name` to the field. Also maps each concrete relation field's `.attname` (e.g., `fk_id`) to the same field. Source: `self._get_fields(reverse=False)`.

#### `fields_map` → `dict[str, Field]`
A `@cached_property`. Builds a dict mapping all fields (forward + reverse, including hidden) by `.name`, and also by `.attname` for concrete relation fields. Source: `self._get_fields(forward=False, include_hidden=True)`.

#### `_relation_tree` → `tuple`
A `@cached_property`. Returns the result of `self._populate_directed_relation_graph()`.

#### `db_returning_fields` → `list[Field]`
A `@cached_property`. Private API. Returns `[field for field in self._get_fields(forward=True, reverse=False, include_parents=PROXY_PARENTS) if getattr(field, 'db_returning', False)]`.

### Methods

#### `__init__(self, meta, app_label=None)`
Initializes all instance attributes as described above. Sets `_get_fields_cache = {}`, empty lists for fields/managers, defaults for strings/booleans, and copies `apps` from the class-level default.

#### `contribute_to_class(self, cls, name)`
Binds this `Options` instance to a model class:
1. Imports `connection` and `truncate_name` locally.
2. Sets `cls._meta = self` and `self.model = cls`.
3. Constructs defaults: `object_name = cls.__name__`, `model_name = object_name.lower()`, `verbose_name = camel_case_to_spaces(object_name)`.
4. Initializes `self.original_attrs = {}`.
5. If `self.meta` exists: copies its `__dict__`; deletes keys starting with `_`; iterates over `DEFAULT_NAMES` — for each, if present in the cleaned dict or as an attribute on `meta`, sets it on `self` and records it in `original_attrs`. Normalizes `unique_together` and `index_together` via `normalize_together()`. For non-abstract models, formats constraint/index names using `_format_names_with_class(cls, objs)` with `{app_label, class}` interpolation. Sets `verbose_name_plural` to lazy `'{}s'` format of verbose_name if not already set. Sets `_ordering_clash = bool(self.ordering and self.order_with_respect_to)`. Raises `TypeError` if any leftover attributes remain in the cleaned dict. If no meta, sets `verbose_name_plural` to lazy `'{}s'` format. Deletes `self.meta`.
6. If `db_table` is empty, constructs it as `'{app_label}_{model_name}'`, truncated via `truncate_name(db_table, connection.ops.max_name_length())`.

#### `_format_names_with_class(self, cls, objs)`
For each object in `objs`, clones it (`obj.clone()`), then replaces `{app_label}` and `{class}` placeholders in `obj.name` with the lowercased app label and class name respectively. Returns the list of modified objects.

#### `_prepare(self, model)`
Final preparation after all fields are added:
1. If `order_with_respect_to` is set: resolves it from a string to an actual field by searching forward fields for one matching the query name or attname; raises `FieldDoesNotExist` if not found. Sets `self.ordering = ('_order',)`. If no `OrderWrt` field exists in `model._meta.local_fields`, adds one named `'_order'` via `model.add_to_class('_order', OrderWrt())`.
2. Else: sets `self.order_with_respect_to = None`.
3. If `self.pk is None`: if `self.parents` is non-empty, promotes the first parent link field to primary key (checks for a local field with the same name first); raises `ImproperlyConfigured` if the pointer field lacks `parent_link=True`. Otherwise, auto-creates an `AutoField(verbose_name='ID', primary_key=True, auto_created=True)` and adds it as `'id'`.

#### `add_manager(self, manager)`
Appends `manager` to `self.local_managers`, then calls `self._expire_cache()`.

#### `add_field(self, field, private=False)`
Inserts a field into the appropriate list using `bisect.insort()` based on creation order:
- If `private=True`: appends to `self.private_fields`.
- Else if `field.is_relation and field.many_to_many`: inserts into `self.local_many_to_many`.
- Else: inserts into `self.local_fields` and calls `self.setup_pk(field)`.

Then handles cache expiration: if the field is a relation with a non-string `remote_field.model`, expires the forward cache on that related model's `_meta` (silencing `AttributeError`) and this model's forward cache. Otherwise, expires only the reverse cache (`_expire_cache(reverse=False)`).

#### `setup_pk(self, field)`
If `self.pk` is not yet set and `field.primary_key` is True, sets `self.pk = field` and `field.serialize = False`.

#### `setup_proxy(self, target)`
Internal setup for proxy model inheritance: copies `target._meta.pk` to `self.pk`, sets `self.proxy_for_model = target`, and copies `target._meta.db_table` to `self.db_table`.

#### `__repr__(self)`
Returns `'<Options for %s>' % self.object_name`.

#### `__str__(self)`
Returns `'%s.%s' % (self.app_label, self.model_name)`.

#### `can_migrate(self, connection)`
Returns whether the model can/should be migrated on a given database connection. Returns `False` if `self.proxy`, `self.swapped`, or not `self.managed`. If `connection` is a string alias, resolves it via `connections[connection]`. Checks `required_db_vendor` (must match `connection.vendor`) and `required_db_features` (all must be present on `connection.features`). Returns `True` otherwise.

#### `_expire_cache(self, forward=True, reverse=True)`
Invalidates cached properties: deletes keys in `FORWARD_PROPERTIES` from `self.__dict__` if `forward`; deletes keys in `REVERSE_PROPERTIES` from `self.__dict__` if `reverse` and not abstract; resets `self._get_fields_cache = {}`.

#### `get_fields(self, include_parents=True, include_hidden=False)`
Public API. If `include_parents is False`, converts it to the sentinel `PROXY_PARENTS`. Delegates to `_get_fields(include_parents=..., include_hidden=...)` with default `forward=True, reverse=True`.

#### `_get_fields(self, forward=True, reverse=True, include_parents=True, include_hidden=False, seen_models=None)`
Internal recursive helper returning a subset of model fields:
1. Validates `include_parents` is one of `True`, `False`, or `PROXY_PARENTS`; raises `TypeError` otherwise.
2. Tracks visited models in `seen_models` (a set) to handle diamond inheritance; creates it on the topmost call (`seen_models is None`). Adds `self.model`.
3. Builds a cache key `(forward, reverse, include_parents, include_hidden, topmost_call)` and returns from `_get_fields_cache` if present.
4. Initializes empty `fields = []`.
5. If `include_parents is not False`: for each parent in `self.parents`, skips already-seen parents; skips parents whose concrete model differs from this model's when `include_parents == PROXY_PARENTS`; recursively calls `_get_fields` on the parent and appends results unless the field has `parent_link=True` and the field's model is not the concrete model.
6. If `reverse and not self.proxy`: iterates `self._relation_tree`, appending `field.remote_field` if `include_hidden` or `not field.remote_field.hidden`.
7. If `forward`: appends `self.local_fields`, `self.local_many_to_many`; on topmost call only, also appends `self.private_fields`.
8. Wraps result in `make_immutable_fields_list("get_fields()", fields)`, caches it, and returns.

#### `_populate_directed_relation_graph(self)`
Builds a directed graph of all reverse relations across the entire app registry:
1. Creates a `defaultdict(list)` for `related_objects_graph`.
2. Iterates all models (`self.apps.get_models(include_auto_created=True)`); skips abstract models. For each non-abstract model, iterates forward relation fields (where `f.is_relation and f.related_model is not None` and the remote model is not a string reference). Appends each such field to the graph keyed by the related model's concrete `_meta`.
3. For every model in all_models, sets `model._meta.__dict__['_relation_tree'] = related_objects_graph[model._meta.concrete_model._meta]` directly (bypassing the cached property descriptor so that `__dict__` lookup takes precedence).
4. Returns `self.__dict__.get('_relation_tree', EMPTY_RELATION_TREE)`.

#### `_property_names(self)` → `frozenset[str]`
A `@cached_property`. Iterates `dir(self.model)`, uses `inspect.getattr_static()` to get each attribute, and collects names where the attribute is an instance of `property`. Returns a frozenset.

#### `get_field(self, field_name)`
Returns a field by name (forward or reverse). First tries `_forward_fields_map[field_name]`; if that fails and `self.apps.models_ready` is False, raises `FieldDoesNotExist` with a message about the app cache not being ready. Then tries `fields_map[field_name]`; raises `FieldDoesNotExist` if still not found.

#### `get_base_chain(self, model)`
Returns a list of parent classes from closest to most distant that lead to `model`. If no parents, returns `[]`. If `model` is an immediate parent, returns `[model]`. Otherwise recursively walks each parent's chain; inserts the current parent at index 0 if a non-empty result is found. Returns `[]` if not found.

#### `get_parent_list(self)`
Returns all ancestors of this model as an ordered list by MRO. Uses `OrderedSet(self.parents)`, then for each immediate parent, recursively adds that parent's ancestors via `parent._meta.get_parent_list()`. Returns `list(result)`.

#### `get_ancestor_link(self, ancestor)`
Returns the field on the current model pointing to a given ancestor (possibly indirect). If `ancestor` is an immediate parent, returns `self.parents[ancestor]`. Otherwise recursively checks each parent's `get_ancestor_link(ancestor)`; if found, returns `self.parents[parent] or parent_link` (the pointer from this model to its direct parent, or the inherited link itself). Returns `None` if not an ancestor.

#### `get_path_to_parent(self, parent)`
Returns a list of `PathInfo` objects representing the path from the current model to `parent`. If same model, returns `[]`. Gets the concrete model and base chain via `get_base_chain(parent)`. For each intermediate model in the chain: if it equals the concrete model, switches `opts`; otherwise creates a `PathInfo(from_opts=final_field.model._meta, to_opts=int_model._meta, target_fields=(final_field.remote_field.get_related_field(),), join_field=final_field, m2m=False, direct=True, filtered_relation=None)` and appends it. Returns the path list.

#### `get_path_from_parent(self, parent)`
Returns a list of `PathInfo` objects from `parent` to the current model. If same model, returns `[]`. Gets concrete model, retrieves base chain reversed (including self), then for each consecutive pair `(ancestor, child)`, gets the ancestor link on the child and extends the path with `link.get_reverse_path_info()`.

#### `__repr__(self)`
Returns `'<Options for %s>' % self.object_name`.

#### `__str__(self)`
Returns `'%s.%s' % (self.app_label, self.model_name)`.