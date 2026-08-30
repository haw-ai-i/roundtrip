## django/db/models/fields/related.py
Now I have the complete source. Here is the full specification:

---

## Module-Level Preamble

### Imports

```python
import functools
import inspect
from functools import partial

from django import forms
from django.apps import apps
from django.conf import SettingsReference
from django.core import checks, exceptions
from django.db import connection, router
from django.db.backends import utils
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP
from django.db.models.deletion import CASCADE, SET_DEFAULT, SET_NULL
from django.db.models.query_utils import PathInfo
from django.db.models.utils import make_model_tuple
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from . import Field
from .mixins import FieldCacheMixin
from .related_descriptors import (
    ForeignKeyDeferredAttribute, ForwardManyToOneDescriptor,
    ForwardOneToOneDescriptor, ManyToManyDescriptor,
    ReverseManyToOneDescriptor, ReverseOneToOneDescriptor,
)
from .related_lookups import (
    RelatedExact, RelatedGreaterThan, RelatedGreaterThanOrEqual, RelatedIn,
    RelatedIsNull, RelatedLessThan, RelatedLessThanOrEqual,
)
from .reverse_related import (
    ForeignObjectRel, ManyToManyRel, ManyToOneRel, OneToOneRel,
)
```

### Constants & Globals

- **`RECURSIVE_RELATIONSHIP_CONSTANT`** = `'self'` — sentinel string used to denote a recursive/self-referential relationship.

---

## Code Objects

### Function: `resolve_relation(scope_model, relation)`

Transforms `relation` into either a model class or a fully-qualified model string of the form `"app_label.ModelName"`, relative to `scope_model`.

**Logic:**
1. If `relation == RECURSIVE_RELATIONSHIP_CONSTANT` (`'self'`), replace it with `scope_model`.
2. If `relation` is a string and does not contain `'.'`, prepend `scope_model._meta.app_label + '.'`.
3. Return the (possibly modified) relation unchanged otherwise (model classes pass through; already-qualified strings pass through).

**Returns:** A model class or an `"app_label.ModelName"` string.

---

### Function: `lazy_related_operation(function, model, *related_models, **kwargs)`

Schedules `function` to be called once `model` and all `related_models` have been loaded into the app registry.

**Logic:**
1. Build a list of models: `[model] + [resolve_relation(model, rel) for rel in related_models]`.
2. Convert each model to a `(app_label, model_name)` tuple via `make_model_tuple`.
3. Call `apps.lazy_model_operation(partial(function, **kwargs), *model_keys)` where `apps = model._meta.apps`.

**Returns:** The result of `apps.lazy_model_operation(...)`.

---

### Class: `RelatedField(FieldCacheMixin, Field)`

Base class for all relational fields. No metaclass.

#### Class-level attributes (field flags)
- `one_to_many` = `False`
- `one_to_one` = `False`
- `many_to_many` = `False`
- `many_to_one` = `False`

#### Instance attributes
- `opts` — set in `contribute_to_class`; the model's `_meta`.
- `swappable` — boolean, set by subclasses.

#### Method: `related_model` (property, `@cached_property`)
Returns `self.remote_field.model`. Raises if models are not yet loaded (`apps.check_models_ready()` is called first).

#### Method: `check(**kwargs)` → `list[checks.Error | checks.Warning]`
Runs five sub-checks and returns the concatenation of all results:
1. `super().check(**kwargs)` (base Field checks)
2. `_check_related_name_is_valid()`
3. `_check_related_query_name_is_valid()`
4. `_check_relation_model_exists()`
5. `_check_clashes()`

#### Method: `_check_related_name_is_valid(self)` → `list[checks.Error]`
Validates that `self.remote_field.related_name` (if not `None`) is either a valid Python identifier and not a keyword, or ends with `'+'`. Returns an error (`fields.E306`) if invalid.

#### Method: `_check_related_query_name_is_valid(self)` → `list[checks.Error]`
If the remote field is hidden (`is_hidden()`), returns `[]`. Otherwise checks that the reverse query name (from `related_query_name()`) does not end with `'_'` and does not contain `LOOKUP_SEP`. Returns errors (`fields.E308`, `fields.E309`) for violations.

#### Method: `_check_relation_model_exists(self)` → `list[checks.Error]`
Checks that the remote model exists in the app registry (is installed or is abstract). Skips if the model has been swapped out. Returns error (`fields.E300`) if missing and not a string reference to an unloaded model, or if it's a string but not yet resolved.

#### Method: `_check_referencing_to_swapped_model(self)` → `list[checks.Error]`
If the remote model is in the app registry but has been swapped out (`_meta.swapped`), returns error (`fields.E301`) with a hint to update the relation to `'settings.<swappable_setting>'`.

#### Method: `_check_clashes(self)` → `list[checks.Error]`
Checks for accessor and reverse query name clashes between this field and other fields/accessors on both the local model's target and the related model. Four sub-checks:
1. **Accessor vs. field name** (`fields.E302`): If the remote model has a field whose name equals `self.remote_field.get_accessor_name()`.
2. **Reverse query name vs. field name** (`fields.E303`): If the remote model has a field whose name equals `self.related_query_name()`.
3. **Accessor vs. accessor** (`fields.E304`): If another related object on the same target model has an accessor with the same name as this field's accessor.
4. **Reverse query name vs. reverse query name** (`fields.E305`): If another related object on the same target model has a reverse query name matching this field's.

Skips all checks if `rel_is_hidden` is true or if `self.remote_field.model` is not yet resolved to a `ModelBase`.

#### Method: `db_type(self, connection)` → `None`
Returns `None` — related fields don't map to a single column.

#### Method: `contribute_to_class(cls, name, private_only=False, **kwargs)`
1. Calls `super().contribute_to_class(...)`.
2. Sets `self.opts = cls._meta`.
3. If the model is not abstract:
   - Resolves `related_name` (falls back to `opts.default_related_name`). Applies string formatting with `{class}`, `{model_name}`, `{app_label}` placeholders.
   - Resolves `related_query_name` similarly, applying `{class}`, `{app_label}` placeholders.
   - Schedules a lazy operation: when the related model loads, calls `field.remote_field.model = related` then `field.do_related_class(related, cls)`.

#### Method: `deconstruct(self)` → `(name, path, args, kwargs)`
Calls `super().deconstruct()`, then adds to `kwargs`:
- `'limit_choices_to'` if non-empty.
- `'related_name'` if not `None`.
- `'related_query_name'` if not `None`.

#### Method: `get_forward_related_filter(self, obj)` → `dict[str, any]`
Returns keyword arguments for filtering the local model's queryset to select instances related through this field to `obj` (an instance of the remote model). Uses `self.related_fields` pairs.

#### Method: `get_reverse_related_filter(self, obj)` → `Q`
Complement of `get_forward_related_filter()`. Returns a `Q` object for filtering the remote model's queryset to select instances related to `obj` (an instance of the local model). Combines base filter fields with any extra descriptor filter via `&`.

#### Property: `swappable_setting` → `str | None`
If `self.swappable`, computes the settings name for the target model using `apps.get_swappable_settings_name()`. Returns `None` otherwise.

#### Method: `set_attributes_from_rel(self)`
Sets `self.name` to either its current value or defaults to `'{remote_model._meta.model_name}_{remote_field.model._meta.pk.name}'`. Sets `self.verbose_name` from the remote model's `_meta.verbose_name` if not already set. Calls `self.remote_field.set_field_name()`.

#### Method: `do_related_class(self, other, cls)`
Calls `set_attributes_from_rel()` then `contribute_to_related_class(other, self.remote_field)`.

#### Method: `get_limit_choices_to(self)` → `Q | dict | None`
If `self.remote_field.limit_choices_to` is callable, invokes it and returns the result. Otherwise returns it directly.

#### Method: `formfield(self, **kwargs)` → `FormField`
Passes `'limit_choices_to'` to the form field if `self.remote_field` has a `get_related_field` attribute. Merges with `kwargs`. Calls `super().formfield(**defaults)`.

#### Method: `related_query_name(self)` → `str`
Returns `self.remote_field.related_query_name`, or falls back to `self.remote_field.related_name`, or falls back to `self.opts.model_name`.

#### Property: `target_field` → `Field`
Gets the last `PathInfo` from `get_path_info()`, returns its first target field. Raises `exceptions.FieldError` if there are multiple target fields.

#### Method: `get_cache_name(self)` → `str`
Returns `self.name`.

---

### Class: `ForeignObject(RelatedField)`

Abstraction of the ForeignKey relation to support multi-column relations.

#### Class-level attributes
- `many_to_many` = `False`
- `many_to_one` = `True`
- `one_to_many` = `False`
- `one_to_one` = `False`
- `requires_unique_target` = `True`
- `related_accessor_class` = `ReverseManyToOneDescriptor`
- `forward_related_accessor_class` = `ForwardManyToOneDescriptor`
- `rel_class` = `ForeignObjectRel`

#### Method: `__init__(self, to, on_delete, from_fields, to_fields, rel=None, related_name=None, related_query_name=None, limit_choices_to=None, parent_link=False, swappable=True, **kwargs)`
1. If `rel is None`, creates a `self.rel_class(self, to, ...)` with all the relation parameters.
2. Calls `super().__init__(rel=rel, **kwargs)`.
3. Sets instance attributes: `from_fields`, `to_fields`, `swappable`.

#### Method: `check(**kwargs)` → `list`
Runs `super().check()` plus `_check_to_fields_exist()` and `_check_unique_target()`.

#### Method: `_check_to_fields_exist(self)` → `list[checks.Error]`
For each field name in `self.to_fields`, attempts to get the field from the remote model's meta. Returns error (`fields.E312`) if any doesn't exist. Skips if the remote model is a string (not yet resolved).

#### Method: `_check_unique_target(self)` → `list[checks.Error]`
If `requires_unique_target` is false or the remote model is unresolved, returns `[]`. Otherwise checks that the foreign-related fields have a unique constraint (either `unique=True` on individual fields or covered by `unique_together`). Returns error (`fields.E310`) if multi-column and no subset is unique; returns error (`fields.E311`) if single column without `unique=True`.

#### Method: `deconstruct(self)` → `(name, path, args, kwargs)`
Calls `super().deconstruct()`, adds to `kwargs`: `'on_delete'`, `'from_fields'`, `'to_fields'`, and optionally `'parent_link'` if true. Converts the target model to a string `"app_label.ModelName"`. If swappable, wraps in `SettingsReference`. Raises `ValueError` on conflicting swap targets.

#### Method: `resolve_related_fields(self)` → `list[tuple[Field, Field]]`
Validates that `from_fields` and `to_fields` are non-empty and equal length; raises `ValueError` if not. For each index, resolves the from-field (either `self` if `'self'`, or via `opts.get_field()`) and to-field (the remote model's pk if `None`, else via `_meta.get_field()`). Returns list of `(from_field, to_field)` tuples.

#### Cached properties
- **`related_fields`** → result of `resolve_related_fields()`.
- **`reverse_related_fields`** → reversed pairs of `related_fields`: `[(rhs, lhs) for lhs, rhs in related_fields]`.
- **`local_related_fields`** → tuple of all left-hand fields.
- **`foreign_related_fields`** → tuple of right-hand fields (excluding `None`).

#### Method: `get_local_related_value(self, instance)` → `tuple`
Returns `get_instance_value_for_fields(instance, self.local_related_fields)`.

#### Method: `get_foreign_related_value(self, instance)` → `tuple`
Returns `get_instance_value_for_fields(instance, self.foreign_related_fields)`.

#### Static method: `get_instance_value_for_fields(instance, fields)` → `tuple`
For each field in `fields`, collects the value from the instance. If the field is a primary key and there's an ancestor link that is also a primary key or abstract, uses `instance.pk`; otherwise uses `getattr(instance, field.attname)`. Returns a tuple.

#### Method: `get_attname_column(self)` → `(str, None)`
Calls `super().get_attname_column()` and returns `(attname, None)`.

#### Method: `get_joining_columns(self, reverse_join=False)` → `tuple[tuple[str, str], ...]`
Returns column-pair tuples from either `related_fields` or `reverse_related_fields` depending on `reverse_join`.

#### Method: `get_reverse_joining_columns(self)` → `tuple`
Returns `get_joining_columns(reverse_join=True)`.

#### Method: `get_extra_descriptor_filter(self, instance)` → `dict`
Returns `{}` — base implementation provides no extra filter. Subclasses may override.

#### Method: `get_extra_restriction(self, where_class, alias, related_alias)` → `None | Restriction`
Returns `None`. Subclasses may override to provide SQL restriction conditions for JOINs and subquery pushdown.

#### Method: `get_path_info(self, filtered_relation=None)` → `list[PathInfo]`
Returns a single-element list with one `PathInfo(from_opts=self.model._meta, to_opts=remote_model._meta, target_fields=self.foreign_related_fields, join_field=self, m2m=False, direct=True)`.

#### Method: `get_reverse_path_info(self, filtered_relation=None)` → `list[PathInfo]`
Returns a single-element list with one `PathInfo(from_opts=remote_model._meta, to_opts=self.model._meta, target_fields=(self.model._meta.pk,), join_field=self.remote_field, m2m=not self.unique, direct=False)`.

#### Class method: `get_lookups(cls)` → `dict`
Uses `inspect.getmro()` to walk the MRO up to and including `ForeignObject`, collects each class's `'class_lookups'` dict, merges them. Cached via `@functools.lru_cache(maxsize=None)`.

#### Method: `contribute_to_class(cls, name, private_only=False, **kwargs)`
Calls `super().contribute_to_class(...)`, then sets `setattr(cls, self.name, self.forward_related_accessor_class(self))`.

#### Method: `contribute_to_related_class(cls, related)`
If the remote field is not hidden and the model hasn't been swapped, sets a descriptor on `cls._meta.concrete_model` at the accessor name using `self.related_accessor_class(related)`. If `limit_choices_to` is set, appends it to `cls._meta.related_fkey_lookups`.

#### Module-level lookup registrations
After class definition:
```python
ForeignObject.register_lookup(RelatedIn)
ForeignObject.register_lookup(RelatedExact)
ForeignObject.register_lookup(RelatedLessThan)
ForeignObject.register_lookup(RelatedGreaterThan)
ForeignObject.register_lookup(RelatedGreaterThanOrEqual)
ForeignObject.register_lookup(RelatedLessThanOrEqual)
ForeignObject.register_lookup(RelatedIsNull)
```

---

### Class: `ForeignKey(ForeignObject)`

Provides a many-to-one relation by adding a column to the local model.

#### Class-level attributes
- `descriptor_class` = `ForeignKeyDeferredAttribute`
- `many_to_many` = `False`, `many_to_one` = `True`, `one_to_many` = `False`, `one_to_one` = `False`
- `rel_class` = `ManyToOneRel`
- `empty_strings_allowed` = `False`
- `default_error_messages` = `{'invalid': _('%(model)s instance with %(field)s %(value)r does not exist.')}`
- `description` = `_("Foreign Key (type determined by related field)")`

#### Method: `__init__(self, to, on_delete, related_name=None, related_query_name=None, limit_choices_to=None, parent_link=False, to_field=None, db_constraint=True, **kwargs)`
1. Validates `to`: tries accessing `to._meta.model_name`; if it fails (not a model class), asserts that `to` is a string and raises with a descriptive message otherwise. If it succeeds, sets `to_field = to_field or to._meta.pk.name`.
2. Asserts `on_delete` is callable; raises `TypeError` otherwise.
3. Creates the rel: `self.rel_class(self, to, to_field, related_name=..., related_query_name=..., limit_choices_to=..., parent_link=..., on_delete=...)`.
4. Defaults `'db_index'` to `True` in kwargs if not already set.
5. Calls `super().__init__(to, on_delete, from_fields=['self'], to_fields=[to_field], **kwargs)`.
6. Sets `self.db_constraint = db_constraint`.

#### Method: `check(**kwargs)` → `list`
Runs `super().check()` plus `_check_on_delete()` and `_check_unique()`.

#### Method: `_check_on_delete(self)` → `list[checks.Error]`
- If `on_delete == SET_NULL` and `not self.null`, returns error (`fields.E320`).
- If `on_delete == SET_DEFAULT` and `not self.has_default()`, returns error (`fields.E321`).

#### Method: `_check_unique(self, **kwargs)` → `list[checks.Warning]`
If `self.unique` is true, returns a warning (`fields.W342`) suggesting `OneToOneField`. Otherwise returns `[]`.

#### Method: `deconstruct(self)` → `(name, path, args, kwargs)`
Calls `super().deconstruct()`, deletes `'to_fields'` and `'from_fields'` from kwargs. If `db_index` is false, sets it explicitly; if true, removes it. If `db_constraint != True`, adds it to kwargs. If `remote_field.field_name` differs from the pk name (or model has no meta), adds `'to_field'`.

#### Method: `to_python(self, value)` → any
Delegates to `self.target_field.to_python(value)`.

#### Property: `target_field` → `Field`
Returns `self.foreign_related_fields[0]`.

#### Method: `get_reverse_path_info(self, filtered_relation=None)` → `list[PathInfo]`
Overrides parent. Returns a single `PathInfo(from_opts=self.model._meta, to_opts=remote_model._meta, target_fields=(remote_model._meta.pk,), join_field=self.remote_field, m2m=not self.unique, direct=False)`.

#### Method: `validate(self, value, model_instance)`
If `parent_link` is true, returns early. Calls `super().validate()`. If value is not None, queries the remote model using `router.db_for_read()` to check existence of a record matching `{remote_field.field_name: value}` filtered by `get_limit_choices_to()`. Raises `exceptions.ValidationError` (code `'invalid'`) if no match exists.

#### Method: `resolve_related_fields(self)` → `list[tuple[Field, Field]]`
Calls parent's `resolve_related_fields()`, then validates that each to-field is local to the remote model's concrete model. Raises `exceptions.FieldError` otherwise.

#### Method: `get_attname(self)` → `str`
Returns `'{}_id'.format(self.name)`.

#### Method: `get_attname_column(self)` → `(str, str)`
Returns `(self.get_attname(), self.db_column or attname)`.

#### Method: `get_default(self)` → any
Calls parent's `get_default()`. If the result is an instance of the remote model, returns its target field attribute value; otherwise returns as-is.

#### Method: `get_db_prep_save(self, value, connection)` → any | None
If value is None or (empty string and not empty_strings_allowed or connection interprets empty strings as nulls), returns `None`. Otherwise delegates to `self.target_field.get_db_prep_save(value, connection)`.

#### Method: `get_db_prep_value(self, value, connection, prepared=False)` → any
Delegates to `self.target_field.get_db_prep_value(value, connection, prepared)`.

#### Method: `get_prep_value(self, value)` → any
Delegates to `self.target_field.get_prep_value(value)`.

#### Method: `contribute_to_related_class(cls, related)`
Calls parent's version. If `remote_field.field_name` is None, sets it to the cls's pk name.

#### Method: `formfield(self, *, using=None, **kwargs)` → `FormField`
Raises `ValueError` if remote model is a string (not loaded). Calls `super().formfield()` with `'form_class': forms.ModelChoiceField`, `'queryset'`: the default manager for the remote model, and `'to_field_name'`: the remote field name.

#### Method: `db_check(self, connection)` → `list`
Returns `[]`.

#### Method: `db_type(self, connection)` → str | None
Delegates to `self.target_field.rel_db_type(connection=connection)`.

#### Method: `db_parameters(self, connection)` → `dict[str, any]`
Returns `{'type': self.db_type(connection), 'check': self.db_check(connection)}`.

#### Method: `convert_empty_strings(self, value, expression, connection)` → any | None
If value is falsy and a string, returns `None`; otherwise returns value unchanged.

#### Method: `get_db_converters(self, connection)` → `list[callable]`
Calls parent's converters; if the connection interprets empty strings as nulls, appends `[self.convert_empty_strings]`.

#### Method: `get_col(self, alias, output_field=None)` → `Field`
If `output_field is None`, sets it to `self.target_field`, then follows ForeignKey chains (while the field is a `ForeignKey` and not self) to find the ultimate target. Raises `ValueError('Cannot resolve output_field.')` if it loops back to self. Calls `super().get_col(alias, output_field)`.

---

### Class: `OneToOneField(ForeignKey)`

Same as ForeignKey but always carries a unique constraint; reverse relation returns a single object.

#### Class-level attributes
- `many_to_many` = `False`, `many_to_one` = `False`, `one_to_many` = `False`, `one_to_one` = `True`
- `related_accessor_class` = `ReverseOneToOneDescriptor`
- `forward_related_accessor_class` = `ForwardOneToOneDescriptor`
- `rel_class` = `OneToOneRel`
- `description` = `_("One-to-one relationship")`

#### Method: `__init__(self, to, on_delete, to_field=None, **kwargs)`
Sets `kwargs['unique'] = True`, then calls `super().__init__(to, on_delete, to_field=to_field, **kwargs)`.

#### Method: `deconstruct(self)` → `(name, path, args, kwargs)`
Calls parent's deconstruct; removes `'unique'` from kwargs (since it's implicit for OneToOneField).

#### Method: `formfield(self, **kwargs)` → `FormField | None`
If `parent_link` is true, returns `None`. Otherwise calls `super().formfield(**kwargs)`.

#### Method: `save_form_data(self, instance, data)`
If `data` is an instance of the remote model, sets it directly on `self.name`. Otherwise sets `self.attname` to `data`; if `data is None`, also clears `self.name` to prevent `Model.save()` from reassigning via pk.

#### Method: `_check_unique(self, **kwargs)` → `list`
Returns `[]` — the unique check warning from ForeignKey doesn't apply here.

---

### Function: `create_many_to_many_intermediary_model(field, klass)`

Factory function that creates an auto-generated intermediary model class for a ManyToManyField.

**Logic:**
1. Defines inner function `set_managed(model, related, through)`: sets `through._meta.managed = model._meta.managed or related._meta.managed`. Schedules it via `lazy_related_operation`.
2. Resolves the target model: `to_model = resolve_relation(klass, field.remote_field.model)`.
3. Constructs table name components: `from_ = klass._meta.model_name`, `to = make_model_tuple(to_model)[1]`. If self-referential (`to == from_`), prefixes with `'from_'` and `'to_'`.
4. Creates a `Meta` class dynamically via `type('Meta', (), {...})` with:
   - `db_table`: from `field._get_m2m_db_table(klass._meta)`
   - `auto_created`: klass
   - `app_label`, `db_tablespace`: from klass's meta
   - `unique_together`: `(from_, to)`
   - `verbose_name` / `verbose_name_plural`: formatted strings
   - `apps`: field.model._meta.apps
5. Creates and returns a new model class via `type(name, (models.Model,), {...})` with:
   - The `Meta` class above
   - `__module__`: klass's module
   - A ForeignKey from the source (`from_`) pointing to `klass`, with related_name `'{}+'.format(name)'`, db_tablespace, db_constraint from remote_field, on_delete=CASCADE.
   - A ForeignKey to the target (`to`) pointing to `to_model`, similarly configured.

---

### Class: `ManyToManyField(RelatedField)`

Provides a many-to-many relation using an intermediary model with two ForeignKey fields.

#### Class-level attributes
- `many_to_many` = `True`, `many_to_one` = `False`, `one_to_many` = `False`, `one_to_one` = `False`
- `rel_class` = `ManyToManyRel`
- `description` = `_("Many-to-many relationship")`

#### Method: `__init__(self, to, related_name=None, related_query_name=None, limit_choices_to=None, symmetrical=None, through=None, through_fields=None, db_constraint=True, db_table=None, swappable=True, **kwargs)`
1. Validates `to`: tries accessing `to._meta`; if it fails, asserts that `to` is a string (or `'self'`).
2. If `symmetrical is None`, sets it to `True` when `to == RECURSIVE_RELATIONSHIP_CONSTANT`.
3. Asserts `db_table is None` if `through is not None`.
4. Creates the rel: `self.rel_class(self, to, related_name=..., related_query_name=..., limit_choices_to=..., symmetrical=..., through=..., through_fields=..., db_constraint=...)`.
5. Sets `self.has_null_arg = 'null' in kwargs`.
6. Calls `super().__init__(**kwargs)`.
7. Sets instance attributes: `db_table`, `swappable`.

#### Method: `check(**kwargs)` → `list`
Runs `super().check()` plus `_check_unique()`, `_check_relationship_model()`, `_check_ignored_options()`, and `_check_table_uniqueness()`.

#### Method: `_check_unique(self, **kwargs)` → `list[checks.Error]`
If `self.unique` is true, returns error (`fields.E330`). Otherwise `[]`.

#### Method: `_check_ignored_options(self, **kwargs)` → `list[checks.Warning]`
- If `has_null_arg`, adds warning (`fields.W340`) that null has no effect.
- If `self._validators` is non-empty, adds warning (`fields.W341`).
- If `limit_choices_to` is set and a custom through model is used (not auto-created), adds warning (`fields.W343`).

#### Method: `_check_relationship_model(self, from_model=None, **kwargs)` → `list[checks.Error]`
Validates the intermediary/through model for ManyToManyField. Multiple sub-checks:
1. If the through model is not installed in the app registry (and not a string), returns error (`fields.E331`).
2. Otherwise validates FK counts in the through model:
   - **Self-referential**: if more than 2 FKs to self and no `through_fields` specified, returns error (`fields.E333`).
   - **Non-self-referential**: if more than 1 FK from source or more than 1 FK to target (and no `through_fields`), returns errors (`fields.E334`, `fields.E335`). If zero FKs to either side, returns error (`fields.E336`).
3. Validates `through_fields`: must be an iterable of at least 2 non-falsy items; each must be a field on the through model that is a ForeignKey to the expected model. Returns errors (`fields.E337`, `fields.E338`, `fields.E339`) for violations.

#### Method: `_check_table_uniqueness(self, **kwargs)` → `list[checks.Error]`
If the through model is a string or not managed, returns `[]`. Otherwise checks that no other managed model (including auto-created ones) uses the same db table name. Returns error (`fields.E340`) if there's a clash with a different concrete model.

#### Method: `deconstruct(self)` → `(name, path, args, kwargs)`
Calls parent's deconstruct. Adds to kwargs: `'db_table'` if not None; `'db_constraint'` if not True; `'to'` as string or `"app_label.ModelName"`; `'through'` if set and not auto-created (as string or `"app_label.ModelName"`). Handles swappable via `SettingsReference`. Raises `ValueError` on conflicting swap targets.

#### Method: `_get_path_info(self, direct=False, filtered_relation=None)` → `list[PathInfo]`
Builds path info through the intermediary model for both forward and reverse traversal:
1. Gets `linkfield1` (source FK in through) and `linkfield2` (target FK in through).
2. If `direct`: join1 = linkfield1's reverse path, join2 = linkfield2's forward path. Else reversed.
3. Computes intermediate infos between the end of join1 and start of join2 to handle model inheritance.
4. Returns `[join1infos..., intermediate_infos..., join2infos...]`.

#### Method: `get_path_info(self, filtered_relation=None)` → `list[PathInfo]`
Returns `_get_path_info(direct=True, ...)`.

#### Method: `get_reverse_path_info(self, filtered_relation=None)` → `list[PathInfo]`
Returns `_get_path_info(direct=False, ...)`.

#### Method: `_get_m2m_db_table(self, opts)` → str
If a custom through model is used, returns its db table. If `self.db_table` is set, returns it. Otherwise generates `'{db_table}_{field_name}'`, truncated to the max name length.

#### Method: `_get_m2m_attr(self, related, attr)` → any
Cached lookup of an attribute on the source FK in the through model. Uses a cache key `'_m2m_{attr}_cache'`. If `through_fields` is set, uses the first field name; otherwise iterates through fields to find one whose remote model matches and (if no explicit link) is the first match.

#### Method: `_get_m2m_reverse_attr(self, related, attr)` → any
Cached lookup of an attribute on the target FK in the through model. Similar logic to `_get_m2m_attr` but uses `through_fields[1]` and handles self-referential M2M by finding the second matching FK.

#### Method: `contribute_to_class(cls, name, **kwargs)`
1. If symmetrical and self-referential (recursive or same class name), sets `related_name = '{name}_rel_+'`.
2. If hidden, sets a generated related_name `'_classname_field_+'` to avoid clashes.
3. Calls `super().contribute_to_class(...)`.
4. If not abstract: if custom through is provided, schedules lazy resolution; otherwise auto-creates the intermediary model via `create_many_to_many_intermediary_model()`.
5. Sets a descriptor on the class: `setattr(cls, self.name, ManyToManyDescriptor(self.remote_field, reverse=False))`.
6. Sets up `self.m2m_db_table` as a partial of `_get_m2m_db_table` with `cls._meta`.

#### Method: `contribute_to_related_class(cls, related)`
If not hidden and model not swapped, sets a descriptor on cls at the accessor name using `ManyToManyDescriptor(self.remote_field, reverse=True)`. Sets up cached partials for column names, field names, and target field names via `_get_m2m_attr` / `_get_m2m_reverse_attr`.

#### Method: `set_attributes_from_rel(self)`
No-op (pass).

#### Method: `value_from_object(self, obj)` → `list`
Returns `[]` if `obj.pk is None`; otherwise returns `list(getattr(obj, self.attname).all())`.

#### Method: `save_form_data(self, instance, data)`
Calls `getattr(instance, self.attname).set(data)`.

#### Method: `formfield(self, *, using=None, **kwargs)` → `FormField`
Sets defaults: `'form_class': forms.ModelMultipleChoiceField`, `'queryset'`: the default manager for the remote model. If `'initial'` is provided and callable, invokes it; converts each initial object to its pk. Calls `super().formfield(**defaults)`.

#### Method: `db_check(self, connection)` → `None`
Returns `None`.

#### Method: `db_type(self, connection)` → `None`
Returns `None` — M2M fields are not represented by a single column.

#### Method: `db_parameters(self, connection)` → `dict[str, None]`
Returns `{'type': None, 'check': None}`.

## django/forms/models.py
Now I have the complete file. Let me write the full natural-language specification.

---

# Django `forms/models.py` — Complete Natural-Language Specification

## 1. Module-Level Preamble

### Imports

```python
from itertools import chain

from django.core.exceptions import (
    NON_FIELD_ERRORS, FieldError, ImproperlyConfigured, ValidationError,
)
from django.forms.fields import ChoiceField, Field
from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass
from django.forms.formsets import BaseFormSet, formset_factory
from django.forms.utils import ErrorList
from django.forms.widgets import (
    HiddenInput, MultipleHiddenInput, SelectMultiple,
)
from django.utils.text import capfirst, get_text_list
from django.utils.translation import gettext, gettext_lazy as _
```

### `__all__` — Public API Exports

A tuple of 10 exported names: `'ModelForm'`, `'BaseModelForm'`, `'model_to_dict'`, `'fields_for_model'`, `'ModelChoiceField'`, `'ModelMultipleChoiceField'`, `'ALL_FIELDS'`, `'BaseModelFormSet'`, `'modelformset_factory'`, `'BaseInlineFormSet'`, `'inlineformset_factory'`, `'modelform_factory'`.

### Constants & Globals

- **`ALL_FIELDS = '__all__'`** — Sentinel string used in `Meta.fields` to mean "include all model fields."

---

## 2. Code Objects

### Function: `construct_instance(form, instance, fields=None, exclude=None)`

Constructs and returns a Django model `instance` from the bound form's `cleaned_data`, without saving to the database.

**Logic:**
1. Import `django.db.models`; get `opts = instance._meta`.
2. Get `cleaned_data = form.cleaned_data`. Initialize empty list `file_field_list = []`.
3. Iterate over each field `f` in `opts.fields`:
   - Skip if `not f.editable`, or `isinstance(f, models.AutoField)`, or `f.name not in cleaned_data`.
   - Skip if `fields is not None and f.name not in fields`.
   - Skip if `exclude and f.name in exclude`.
   - Check if the widget value was omitted from POST data: if `f.has_default()` AND the form's widget for this field reports the value as omitted via `form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name))` AND `cleaned_data.get(f.name)` is in the field's `empty_values`, then skip (leave default).
   - If `isinstance(f, models.FileField)`, append to `file_field_list`. Otherwise, call `f.save_form_data(instance, cleaned_data[f.name])` immediately.
4. After iterating all fields, iterate `file_field_list` and call `f.save_form_data(instance, cleaned_data[f.name])` for each (deferred so callable `upload_to` can use other field values).
5. Return `instance`.

---

### Function: `model_to_dict(instance, fields=None, exclude=None)`

Returns a dict containing data from `instance`, suitable as a Form's `initial` argument.

**Logic:**
1. Get `opts = instance._meta`; initialize empty `data = {}`.
2. Iterate over each field `f` in `chain(opts.concrete_fields, opts.private_fields, opts.many_to_many)`:
   - Skip if `not getattr(f, 'editable', False)`.
   - Skip if `fields is not None and f.name not in fields`.
   - Skip if `exclude and f.name in exclude`.
   - Set `data[f.name] = f.value_from_object(instance)`.
3. Return `data`.

---

### Function: `apply_limit_choices_to_to_formfield(formfield)`

Applies `limit_choices_to` to a formfield's queryset if applicable.

**Logic:**
1. If `formfield` has both `'queryset'` attribute and `'get_limit_choices_to'` method:
   - Call `limit_choices_to = formfield.get_limit_choices_to()`.
   - If `limit_choices_to is not None`, set `formfield.queryset = formfield.queryset.complex_filter(limit_choices_to)`.

---

### Function: `fields_for_model(model, fields=None, exclude=None, widgets=None, formfield_callback=None, localized_fields=None, labels=None, help_texts=None, error_messages=None, field_classes=None, *, apply_limit_choices_to=True)`

Returns a dict of form fields for the given Django model.

**Parameters:**
- `model`: A Django model class.
- `fields` / `exclude`: Optional lists of field names to include/exclude.
- `widgets`: Dict mapping field names to widget classes/instances.
- `formfield_callback`: Callable taking a model field and kwargs, returning a form field; or `None`.
- `localized_fields`: List of field names to localize, or `ALL_FIELDS`.
- `labels` / `help_texts` / `error_messages` / `field_classes`: Dicts mapping field names to label/help text/error messages/form class overrides.
- `apply_limit_choices_to`: Boolean (keyword-only); whether to apply `limit_choices_to` filtering.

**Logic:**
1. Initialize empty `field_dict = {}`, empty list `ignored = []`.
2. Get `opts = model._meta`. Import `django.db.models.Field as ModelField`. Build `sortable_private_fields = [f for f in opts.private_fields if isinstance(f, ModelField)]`.
3. Iterate over each field `f` in the sorted chain of `(opts.concrete_fields, sortable_private_fields, opts.many_to_many)`:
   - If `not getattr(f, 'editable', False)`:
     - If `fields is not None and f.name in fields and (exclude is None or f.name not in exclude)`, raise `FieldError` saying the non-editable field cannot be specified.
     - Continue to next field.
   - Skip if `fields is not None and f.name not in fields`.
   - Skip if `exclude and f.name in exclude`.
   - Build `kwargs = {}`:
     - If `widgets and f.name in widgets`, set `kwargs['widget'] = widgets[f.name]`.
     - If `localized_fields == ALL_FIELDS or (localized_fields and f.name in localized_fields)`, set `kwargs['localize'] = True`.
     - If `labels and f.name in labels`, set `kwargs['label'] = labels[f.name]`.
     - If `help_texts and f.name in help_texts`, set `kwargs['help_text'] = help_texts[f.name]`.
     - If `error_messages and f.name in error_messages`, set `kwargs['error_messages'] = error_messages[f.name]`.
     - If `field_classes and f.name in field_classes`, set `kwargs['form_class'] = field_classes[f.name]`.
   - Get the formfield: if `formfield_callback is None`, call `f.formfield(**kwargs)`; else if not callable, raise `TypeError`; else call `formfield_callback(f, **kwargs)`.
   - If `formfield` is truthy: if `apply_limit_choices_to`, call `apply_limit_choices_to_to_formfield(formfield)`; set `field_dict[f.name] = formfield`. Else append `f.name` to `ignored`.
4. If `fields` was provided, rebuild `field_dict` as `{f: field_dict.get(f) for f in fields if (not exclude or f not in exclude) and f not in ignored}` — preserving the order of `fields` and filtering out ignored/invalid entries.
5. Return `field_dict`.

---

### Class: `ModelFormOptions`

Stores options extracted from a ModelForm's inner `Meta` class.

**Attributes (all set in `__init__`, defaulting to `None`):**
- `model`: From `options.model`.
- `fields`: From `options.fields`.
- `exclude`: From `options.exclude`.
- `widgets`: From `options.widgets`.
- `localized_fields`: From `options.localized_fields`.
- `labels`: From `options.labels`.
- `help_texts`: From `options.help_texts`.
- `error_messages`: From `options.error_messages`.
- `field_classes`: From `options.field_classes`.

**`__init__(self, options=None)`:** Uses `getattr(options, attr_name, None)` for each attribute above.

---

### Class: `ModelFormMetaclass(DeclarativeFieldsMetaclass)`

Metaclass that builds ModelForm classes by extracting fields from a model and merging with declared form fields.

**`__new__(mcs, name, bases, attrs)`:**
1. Search through `bases` for the first base having both `'Meta'` and `'formfield_callback'`; store as `base_formfield_callback`.
2. Pop `'formfield_callback'` from `attrs`, falling back to `base_formfield_callback`.
3. Call `super().__new__(mcs, name, bases, attrs)` to create the class (this processes declared fields via `DeclarativeFieldsMetaclass`).
4. If `bases == (BaseModelForm,)`, return immediately — no Meta processing needed for direct subclasses of BaseModelForm.
5. Create `opts = new_class._meta = ModelFormOptions(getattr(new_class, 'Meta', None))`.
6. Validate string values: For each option in `['fields', 'exclude', 'localized_fields']`, if the value is a `str` and not equal to `ALL_FIELDS`, raise `TypeError` with a message suggesting tuple syntax.
7. If `opts.model` exists:
   - If both `opts.fields is None and opts.exclude is None`, raise `ImproperlyConfigured`.
   - If `opts.fields == ALL_FIELDS`, set `opts.fields = None` (sentinel for "all fields").
   - Call `fields_for_model(opts.model, opts.fields, opts.exclude, opts.widgets, formfield_callback, opts.localized_fields, opts.labels, opts.help_texts, opts.error_messages, opts.field_classes, apply_limit_choices_to=False)` to get model-derived fields.
   - Find `none_model_fields = {k for k, v in fields.items() if not v}`; compute `missing_fields = none_model_fields.difference(new_class.declared_fields)`. If any exist, raise `FieldError` listing them.
   - Merge: `fields.update(new_class.declared_fields)` (declared fields override model-derived ones).
8. Else (`opts.model` is None): set `fields = new_class.declared_fields`.
9. Set `new_class.base_fields = fields`.
10. Return `new_class`.

---

### Class: `BaseModelForm(BaseForm)`

Base class for ModelForms with model-specific instance handling, validation, and saving logic.

**`__init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList, label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None)`:**
1. Get `opts = self._meta`. If `opts.model is None`, raise `ValueError`.
2. If `instance is None`: create `self.instance = opts.model()` and set `object_data = {}`. Else: set `self.instance = instance` and get `object_data = model_to_dict(instance, opts.fields, opts.exclude)`.
3. If `initial is not None`, call `object_data.update(initial)` (initial overrides instance values).
4. Set `self._validate_unique = False` (prevents unique validation unless `clean()` calls super).
5. Call `super().__init__(data, files, auto_id, prefix, object_data, error_class, label_suffix, empty_permitted, use_required_attribute=use_required_attribute, renderer=renderer)`.
6. For each formfield in `self.fields.values()`, call `apply_limit_choices_to_to_formfield(formfield)` (applies limit_choices_to at init time).

**`_get_validation_exclusions(self)`:** Returns a list of field names to exclude from model-level validation.
1. Initialize empty `exclude = []`.
2. For each field `f` in `self.instance._meta.fields`:
   - If the field name is not in `self.fields`, append it (developer may add values post-validation).
   - Else if `self._meta.fields` exists and the field name is not in `self._meta.fields`, append it.
   - Else if `self._meta.exclude` exists and the field name is in `self._meta.exclude`, append it.
   - Else if the field name is in `self._errors` (failed form validation), append it.
   - Else: get `form_field = self.fields[field]`; if `not f.blank and not form_field.required and field_value in form_field.empty_values` (where `field_value = self.cleaned_data.get(field)`), append the field name.
3. Return `exclude`.

**`clean(self)`:** Sets `self._validate_unique = True`, returns `self.cleaned_data`.

**`_update_errors(self, errors)`:** Overrides model-level validation error messages with form-level ones.
1. Get `opts = self._meta`.
2. If `errors` has `'error_dict'` attribute, use it; else wrap as `{NON_FIELD_ERRORS: errors}`.
3. For each `(field, messages)` in the error dict:
   - Determine `error_messages`: if field is `NON_FIELD_ERRORS` and `opts.error_messages` contains it, use that; elif field is in `self.fields`, use `self.fields[field].error_messages`; else continue (skip).
   - For each message in messages: if it's a `ValidationError` with a code present in `error_messages`, replace `message.message` with the form-level error string.
4. Call `self.add_error(None, errors)`.

**`_post_clean(self)`:** Performs post-validation cleaning.
1. Get `opts = self._meta`; call `exclude = self._get_validation_exclusions()`.
2. For each `(name, field)` in `self.fields`: if `isinstance(field, InlineForeignKeyField)`, append name to `exclude` (FK inline fields excluded from basic validation but included in uniqueness checks).
3. Try: call `construct_instance(self, self.instance, opts.fields, opts.exclude)`. Catch `ValidationError e`; call `self._update_errors(e)`.
4. Try: call `self.instance.full_clean(exclude=exclude, validate_unique=False)`. Catch `ValidationError e`; call `self._update_errors(e)`.
5. If `self._validate_unique`, call `self.validate_unique()`.

**`validate_unique(self)`:** Calls the instance's `validate_unique()` and updates form errors.
1. Call `exclude = self._get_validation_exclusions()`.
2. Try: call `self.instance.validate_unique(exclude=exclude)`. Catch `ValidationError e`; call `self._update_errors(e)`.

**`_save_m2m(self)`:** Saves many-to-many fields and generic relations.
1. Get `cleaned_data = self.cleaned_data`, `exclude = self._meta.exclude`, `fields = self._meta.fields`, `opts = self.instance._meta`.
2. Iterate over each field `f` in `chain(opts.many_to_many, opts.private_fields)`:
   - Skip if `not hasattr(f, 'save_form_data')`.
   - Skip if `fields and f.name not in fields`.
   - Skip if `exclude and f.name in exclude`.
   - If `f.name in cleaned_data`, call `f.save_form_data(self.instance, cleaned_data[f.name])`.

**`save(self, commit=True)`:** Saves the form's instance and returns it.
1. If `self.errors`, raise `ValueError` saying the model could not be created/changed because data didn't validate (uses `self.instance._meta.object_name`).
2. If `commit is True`: call `self.instance.save()`, then `self._save_m2m()`.
3. Else: set `self.save_m2m = self._save_m2m` (deferred m2m save method).
4. Return `self.instance`.
5. Set `save.alters_data = True` (module-level attribute on the method).

---

### Class: `ModelForm(BaseModelForm, metaclass=ModelFormMetaclass)`

A thin subclass of `BaseModelForm` with no additional methods or attributes — inherits everything from `BaseModelForm` and gets its field-building behavior from `ModelFormMetaclass`.

---

### Function: `modelform_factory(model, form=ModelForm, fields=None, exclude=None, formfield_callback=None, widgets=None, localized_fields=None, labels=None, help_texts=None, error_messages=None, field_classes=None)`

Dynamically creates a ModelForm class for the given model.

**Logic:**
1. Build `attrs = {'model': model}` dict; conditionally add `'fields'`, `'exclude'`, `'widgets'`, `'localized_fields'`, `'labels'`, `'help_texts'`, `'error_messages'`, `'field_classes'` keys if their corresponding arguments are not `None`.
2. Set `bases = (form.Meta,)` if `form` has a `'Meta'` attribute; else empty tuple. Create `Meta = type('Meta', bases, attrs)`.
3. If `formfield_callback` is provided, set `Meta.formfield_callback = staticmethod(formfield_callback)`.
4. Set `class_name = model.__name__ + 'Form'`.
5. Build `form_class_attrs = {'Meta': Meta, 'formfield_callback': formfield_callback}`.
6. If both `getattr(Meta, 'fields', None)` and `getattr(Meta, 'exclude', None)` are `None`, raise `ImproperlyConfigured`.
7. Return `type(form)(class_name, (form,), form_class_attrs)` — instantiates a new class using the same metaclass as `form`.

---

### Class: `BaseModelFormSet(BaseFormSet)`

A FormSet for editing a queryset and/or adding new objects to it.

**Class attributes:**
- `model = None`
- `unique_fields = set()` — fields that must be unique among forms in this formset.

**`__init__(self, data=None, files=None, auto_id='id_%s', prefix=None, queryset=None, *, initial=None, **kwargs)`:**
1. Set `self.queryset = queryset`, `self.initial_extra = initial`.
2. Call `super().__init__(data=data, files=files, auto_id=auto_id, prefix=prefix, **kwargs)`.

**`initial_form_count(self)`:** Returns the number of required forms. If not bound, returns `len(self.get_queryset())`; else calls `super().initial_form_count()`.

**`_existing_object(self, pk)`:** Lazily builds and caches `self._object_dict = {o.pk: o for o in self.get_queryset()}`; returns the object with the given pk or `None`.

**`_get_to_python(self, field)`:** Traverses through related fields via `field.remote_field.get_related_field()` until reaching a concrete (non-related) field; returns that field's `to_python` method.

**`_construct_form(self, i, **kwargs)`:** Constructs the form at index `i`.
1. Set `pk_required = i < self.initial_form_count()`.
2. If `pk_required`:
   - If bound: build `pk_key = '%s-%s' % (self.add_prefix(i), self.model._meta.pk.name)`; try to get `pk` from `self.data[pk_key]`; if KeyError, pass (user tampered). Else convert via `to_python = self._get_to_python(self.model._meta.pk)`, catching `ValidationError`. On success, set `kwargs['instance'] = self._existing_object(pk)`.
   - If not bound: set `kwargs['instance'] = self.get_queryset()[i]`.
3. Else if `self.initial_extra`: try to get initial data from `self.initial_extra[i - self.initial_form_count()]` and set as `kwargs['initial']`; catch IndexError.
4. Call `form = super()._construct_form(i, **kwargs)`.
5. If `pk_required`, set `form.fields[self.model._meta.pk.name].required = True`.
6. Return `form`.

**`get_queryset(self)`:** Lazily builds and caches the queryset.
1. If `_queryset` not cached: if `self.queryset is not None`, use it; else use `self.model._default_manager.get_queryset()`.
2. If the queryset isn't ordered, add `.order_by(self.model._meta.pk.name)`.
3. Cache as `self._queryset`; return it.

**`save_new(self, form, commit=True)`:** Returns `form.save(commit=commit)`.

**`save_existing(self, form, instance, commit=True)`:** Returns `form.save(commit=commit)`.

**`delete_existing(self, obj, commit=True)`:** If `commit`, calls `obj.delete()`.

**`save(self, commit=True)`:** Saves all forms and returns list of instances.
1. If not committing: set `self.saved_forms = []`; define inner function `save_m2m()` that iterates `self.saved_forms` calling each form's `save_m2m()`; assign to `self.save_m2m`.
2. Return `self.save_existing_objects(commit) + self.save_new_objects(commit)`.
3. Set `save.alters_data = True`.

**`clean(self)`:** Calls `self.validate_unique()`.

**`validate_unique(self)`:** Validates uniqueness across all forms in the formset.
1. Initialize empty sets `all_unique_checks`, `all_date_checks`; get `forms_to_delete = self.deleted_forms`.
2. Build `valid_forms = [form for form in self.forms if form.is_valid() and form not in forms_to_delete]`.
3. For each valid form: call `exclude = form._get_validation_exclusions()`; call `unique_checks, date_checks = form.instance._get_unique_checks(exclude=exclude)`; update the sets.
4. Initialize empty list `errors`.
5. **Unique checks:** For each `(uclass, unique_check)` in `all_unique_checks`:
   - Initialize `seen_data = set()`.
   - For each valid form: build `row_data` from field values for fields in `unique_check` that are in the form's `cleaned_data`; if field is in `self.unique_fields`, use the raw field value; else use `form.cleaned_data[field]`. Reduce model instances to their pk via `_get_pk_val()`, lists to tuples.
   - If `row_data` is non-empty and contains no `None`: if already in `seen_data`, append `self.get_unique_error_message(unique_check)` to errors, set `form._errors[NON_FIELD_ERRORS] = self.error_class([self.get_form_error()])`, delete the unique fields from `form.cleaned_data`; else add to `seen_data`.
6. **Date checks:** For each `(uclass, lookup, field, unique_for)` in `all_date_checks`:
   - Initialize `seen_data = set()`.
   - For each valid form: if both `field` and `unique_for` have non-None data: build `date_data` (tuple of year/month/day for 'date' lookup; else tuple of the attribute); build `data = (form.cleaned_data[field],) + date_data`. If already in `seen_data`, append error message, set form errors, delete from cleaned_data; else add to seen.
7. If any errors exist, raise `ValidationError(errors)`.

**`get_unique_error_message(self, unique_check)`:** Returns a gettext string: if one field, `"Please correct the duplicate data for %(field)s."`; else `"Please correct the duplicate data for %(field)s, which must be unique."` with fields joined by "and".

**`get_date_error_message(self, date_check)`:** Returns `"Please correct the duplicate data for %(field_name)s which must be unique for the %(lookup)s in %(date_field)s."`.

**`get_form_error(self)`:** Returns `"Please correct the duplicate values below."`.

**`save_existing_objects(self, commit=True)`:** Saves changed existing objects.
1. Initialize `self.changed_objects = []`, `self.deleted_objects = []`. If no initial forms, return `[]`.
2. Get `forms_to_delete = self.deleted_forms`; initialize `saved_instances = []`.
3. For each form in `self.initial_forms`: get `obj = form.instance`. If `obj.pk is None` (unexpected empty model or already deleted), continue.
4. If form is in `forms_to_delete`: append obj to `self.deleted_objects`, call `self.delete_existing(obj, commit=commit)`.
5. Else if `form.has_changed()`: append `(obj, form.changed_data)` to `self.changed_objects`; append result of `self.save_existing(form, obj, commit=commit)` to `saved_instances`; if not committing, append form to `self.saved_forms`.
6. Return `saved_instances`.

**`save_new_objects(self, commit=True)`:** Saves new objects from extra forms.
1. Initialize `self.new_objects = []`.
2. For each form in `self.extra_forms`: skip if `not form.has_changed()`. Skip if `self.can_delete and self._should_delete_form(form)`. Append result of `self.save_new(form, commit=commit)` to `self.new_objects`; if not committing, append form to `self.saved_forms`.
3. Return `self.new_objects`.

**`add_fields(self, form, index)`:** Adds a hidden field for the object's primary key.
1. Import `AutoField`, `OneToOneField`, `ForeignKey` from `django.db.models`.
2. Set `self._pk_field = pk = self.model._meta.pk`.
3. Define inner function `pk_is_not_editable(pk)`: returns True if `(not pk.editable) or (pk.auto_created or isinstance(pk, AutoField)) or (pk.remote_field and pk.remote_field.parent_link and pk_is_not_editable(pk.remote_field.model._meta.pk))`.
4. If `pk_is_not_editable(pk)` or `pk.name not in form.fields`:
   - Determine `pk_value`: if bound, use `None` if `form.instance._state.adding`, else `form.instance.pk`; else try to get from `self.get_queryset()[index].pk` (or `None` on IndexError).
   - Build queryset: if pk is ForeignKey or OneToOneField, use `pk.remote_field.model._default_manager.get_queryset()`; else use `self.model._default_manager.get_queryset()`. Apply `.using(form.instance._state.db)`.
   - Determine widget: if `form._meta.widgets`, get from dict (defaulting to `HiddenInput`); else `HiddenInput`.
   - Set `form.fields[self._pk_field.name] = ModelChoiceField(qs, initial=pk_value, required=False, widget=widget)`.
5. Call `super().add_fields(form, index)`.

---

### Function: `modelformset_factory(model, form=ModelForm, formfield_callback=None, formset=BaseModelFormSet, extra=1, can_delete=False, can_order=False, max_num=None, fields=None, exclude=None, widgets=None, validate_max=False, localized_fields=None, labels=None, help_texts=None, error_messages=None, min_num=None, validate_min=False, field_classes=None)`

Returns a FormSet class for the given model.

**Logic:**
1. Get `meta = getattr(form, 'Meta', None)`. If both `getattr(meta, 'fields', fields)` and `getattr(meta, 'exclude', exclude)` are `None`, raise `ImproperlyConfigured`.
2. Call `modelform_factory(model, form=form, fields=fields, exclude=exclude, formfield_callback=formfield_callback, widgets=widgets, localized_fields=localized_fields, labels=labels, help_texts=help_texts, error_messages=error_messages, field_classes=field_classes)` to get the form class.
3. Call `formset_factory(form, formset, extra=extra, min_num=min_num, max_num=max_num, can_order=can_order, can_delete=can_delete, validate_min=validate_min, validate_max=validate_max)` to get the FormSet class.
4. Set `FormSet.model = model`.
5. Return `FormSet`.

---

### Class: `BaseInlineFormSet(BaseModelFormSet)`

A formset for child objects related to a parent via ForeignKey.

**`__init__(self, data=None, files=None, instance=None, save_as_new=False, prefix=None, queryset=None, **kwargs)`:**
1. If `instance is None`, set `self.instance = self.fk.remote_field.model()`; else `self.instance = instance`.
2. Set `self.save_as_new = save_as_new`.
3. If `queryset is None`, use `self.model._default_manager`; if `self.instance.pk is not None`, filter by `{self.fk.name: self.instance}`; else use `queryset.none()`.
4. Set `self.unique_fields = {self.fk.name}`.
5. Call `super().__init__(data, files, prefix=prefix, queryset=qs, **kwargs)`.
6. If `self.form._meta.fields` exists and `self.fk.name not in self.form._meta.fields`: if it's a tuple, convert to list; append `self.fk.name`.

**`initial_form_count(self)`:** If `self.save_as_new`, return 0; else call `super().initial_form_count()`.

**`_construct_form(self, i, **kwargs)`:**
1. Call `form = super()._construct_form(i, **kwargs)`.
2. If `self.save_as_new`: make `form.data` mutable if needed; set `form.data[form.add_prefix(self._pk_field.name)] = None`; set `form.data[form.add_prefix(self.fk.name)] = None`; restore mutability.
3. Set FK value on form instance: get `fk_value = self.instance.pk` (or use `remote_field.field_name` if not pk); call `setattr(form.instance, self.fk.get_attname(), fk_value)`.
4. Return `form`.

**`get_default_prefix(cls)`:** Returns the accessor name from `cls.fk.remote_field.get_accessor_name(model=cls.model)` with `'+'` removed.

**`save_new(self, form, commit=True)`:** Calls `setattr(form.instance, self.fk.name, self.instance)`, then calls `super().save_new(form, commit=commit)`.

**`add_fields(self, form, index)`:**
1. Call `super().add_fields(form, index)`.
2. If `self._pk_field == self.fk`: set `name = self._pk_field.name`, `kwargs = {'pk_field': True}`; else: set `name = self.fk.name`, `kwargs = {'label': getattr(form.fields.get(name), 'label', capfirst(self.fk.verbose_name))}`.
3. If `self.fk.remote_field.field_name != self.fk.remote_field.model._meta.pk.name`, add `'to_field'` to kwargs.
4. If `self.instance._state.adding`: if `kwargs.get('to_field')` is set, get the field via `self.instance._meta.get_field(kwargs['to_field'])`; else use pk; if it has a default, set `setattr(self.instance, to_field.attname, None)`.
5. Set `form.fields[name] = InlineForeignKeyField(self.instance, **kwargs)`.

**`get_unique_error_message(self, unique_check)`:** Filters out `self.fk.name` from `unique_check`, then calls `super().get_unique_error_message(unique_check)`.

---

### Function: `_get_foreign_key(parent_model, model, fk_name=None, can_fail=False)`

Finds and returns the ForeignKey field from `model` to `parent_model`.

**Logic:**
1. Import `ForeignKey` from `django.db.models`; get `opts = model._meta`.
2. If `fk_name` is provided: filter `opts.fields` for fields named `fk_name`. If exactly one found, verify it's a ForeignKey pointing to `parent_model` or its parents; raise `ValueError` if not. If none found, raise `ValueError`.
3. Else (no `fk_name`): find all ForeignKeys from `model` to `parent_model` (or its parent models). If exactly one, return it. If none: if `can_fail`, return `None`; else raise `ValueError`. If more than one: raise `ValueError` requiring explicit `fk_name`.
4. Return the ForeignKey field.

---

### Function: `inlineformset_factory(parent_model, model, form=ModelForm, formset=BaseInlineFormSet, fk_name=None, fields=None, exclude=None, extra=3, can_order=False, can_delete=True, max_num=None, formfield_callback=None, widgets=None, validate_max=False, localized_fields=None, labels=None, help_texts=None, error_messages=None, min_num=None, validate_min=False, field_classes=None)`

Returns an InlineFormSet for the given parent/child model relationship.

**Logic:**
1. Call `fk = _get_foreign_key(parent_model, model, fk_name=fk_name)`.
2. If `fk.unique`, set `max_num = 1` (enforce single related object).
3. Build kwargs dict with all parameters: `'form'`, `'formfield_callback'`, `'formset'`, `'extra'`, `'can_delete'`, `'can_order'`, `'fields'`, `'exclude'`, `'min_num'`, `'max_num'`, `'widgets'`, `'validate_min'`, `'validate_max'`, `'localized_fields'`, `'labels'`, `'help_texts'`, `'error_messages'`, `'field_classes'`.
4. Call `FormSet = modelformset_factory(model, **kwargs)`.
5. Set `FormSet.fk = fk`.
6. Return `FormSet`.

---

### Class: `InlineForeignKeyField(Field)`

A basic integer field for validating inline FK values against a parent instance.

**Class attributes:**
- `widget = HiddenInput`
- `default_error_messages = {'invalid_choice': _('The inline value did not match the parent instance.')}`

**`__init__(self, parent_instance, *args, pk_field=False, to_field=None, **kwargs)`:**
1. Set `self.parent_instance = parent_instance`, `self.pk_field = pk_field`, `self.to_field = to_field`.
2. If `parent_instance is not None`: set initial value from `to_field` (via `getattr`) or from `pk`.
3. Force `kwargs["required"] = False`.
4. Call `super().__init__(*args, **kwargs)`.

**`clean(self, value)`:**
1. If `value in self.empty_values`: if `self.pk_field`, return `None`; else return `self.parent_instance`.
2. Get original value: from `to_field` via `getattr` or from `pk`.
3. Compare `str(value)` to `str(orig)`; if not equal, raise `ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')`.
4. Return `self.parent_instance`.

**`has_changed(self, initial, data)`:** Always returns `False`.

---

### Class: `ModelChoiceIteratorValue`

A wrapper for a choice value and its associated model instance.

**`__init__(self, value, instance)`:** Sets `self.value = value`, `self.instance = instance`.
**`__str__(self)`:** Returns `str(self.value)`.
**`__eq__(self, other)`:** If `other` is a `ModelChoiceIteratorValue`, compare `self.value == other.value`; else compare `self.value == other`.

---

### Class: `ModelChoiceIterator`

An iterator over model choices for `ModelChoiceField`.

**`__init__(self, field)`:** Sets `self.field = field`, `self.queryset = field.queryset`.
**`__iter__(self)`:** If `self.field.empty_label is not None`, yield `("", self.field.empty_label)`. Use `queryset.iterator()` if no prefetch_related; else use queryset directly. For each obj, yield `self.choice(obj)`.
**`__len__(self)`:** Returns `self.queryset.count() + (1 if empty_label else 0)`.
**`__bool__(self)`:** Returns `True` if `empty_label is not None or self.queryset.exists()`.
**`choice(self, obj)`:** Returns `(ModelChoiceIteratorValue(self.field.prepare_value(obj), obj), self.field.label_from_instance(obj))`.

---

### Class: `ModelChoiceField(ChoiceField)`

A ChoiceField whose choices are a model QuerySet. (Subclasses ChoiceField for type purity but does not use ChoiceField's implementation.)

**Class attributes:**
- `default_error_messages = {'invalid_choice': _('Select a valid choice. That choice is not one of the available choices.')}`
- `iterator = ModelChoiceIterator`

**`__init__(self, queryset, *, empty_label="---------", required=True, widget=None, label=None, initial=None, help_text='', to_field_name=None, limit_choices_to=None, **kwargs)`:**
1. If `required and initial is not None`, set `self.empty_label = None`; else `self.empty_label = empty_label`.
2. Call `Field.__init__(self, required=required, widget=widget, label=label, initial=initial, help_text=help_text, **kwargs)` (not ChoiceField's init).
3. Set `self.queryset = queryset`, `self.limit_choices_to = limit_choices_to`, `self.to_field_name = to_field_name`.

**`get_limit_choices_to(self)`:** If `callable(self.limit_choices_to)`, return the result of calling it; else return `self.limit_choices_to`.

**`__deepcopy__(self, memo)`:** Calls `super(ChoiceField, self).__deepcopy__(memo)` (skips ChoiceField to use Field's deepcopy). If `self.queryset is not None`, set `result.queryset = self.queryset.all()` (creates fresh queryset). Return result.

**`_get_queryset(self)` / `_set_queryset(self, queryset)`:** Property getter/setter for `queryset`. Setter: if queryset is None, set `_queryset = None`; else `_queryset = queryset.all()`, then update `self.widget.choices = self.choices`.

**`queryset = property(_get_queryset, _set_queryset)`**.

**`label_from_instance(self, obj)`:** Returns `str(obj)`. Overridable for custom labels.

**`_get_choices(self)`:** If `_choices` is set (manually assigned), return it; else return `self.iterator(self)` (fresh iterator each time for lazy evaluation).

**`choices = property(_get_choices, ChoiceField._set_choices)`**.

**`prepare_value(self, value)`:** If value has `_meta` (is a model instance): if `to_field_name`, return `value.serializable_value(to_field_name)`; else return `value.pk`. Else call `super().prepare_value(value)`.

**`to_python(self, value)`:** If in empty values, return None. Try: get key = `to_field_name or 'pk'`; if value is a model instance, extract the key attribute; call `self.queryset.get(**{key: value})`. Catch `(ValueError, TypeError, self.queryset.model.DoesNotExist)` → raise `ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')`. Return the retrieved object.

**`validate(self, value)`:** Calls `Field.validate(self, value)` (does not use ChoiceField's validate).

**`has_changed(self, initial, data)`:** If disabled, return False. Normalize: `initial_value = initial if initial is not None else ''`, `data_value = data if data is not None else ''`. Return `str(self.prepare_value(initial_value)) != str(data_value)`.

---

### Class: `ModelMultipleChoiceField(ModelChoiceField)`

A MultipleChoiceField whose choices are a model QuerySet.

**Class attributes:**
- `widget = SelectMultiple`
- `hidden_widget = MultipleHiddenInput`
- `default_error_messages = {'list': _('Enter a list of values.'), 'invalid_choice': _('Select a valid choice. %(value)s is not one of the available choices.'), 'invalid_pk_value': _('"%(pk)s" is not a valid value.')}`

**`__init__(self, queryset, **kwargs)`:** Calls `super().__init__(queryset, empty_label=None, **kwargs)` (no empty label for multiple choice).

**`to_python(self, value)`:** If not value, return `[]`; else return `list(self._check_values(value))`.

**`clean(self, value)`:** Call `value = self.prepare_value(value)`. If required and no value, raise `ValidationError(required error)`. If not required and no value, return `self.queryset.none()`. If not a list/tuple, raise `ValidationError(list error)`. Call `qs = self._check_values(value)`; run custom validators via `self.run_validators(value)`; return qs.

**`_check_values(self, value)`:** Validates and returns a QuerySet for the given PK values.
1. Get key = `to_field_name or 'pk'`.
2. Try to create `frozenset(value)` (deduplication); catch TypeError → raise ValidationError(list error).
3. For each pk in value: try `self.queryset.filter(**{key: pk})`; catch `(ValueError, TypeError)` → raise ValidationError(invalid_pk_value error with params).
4. Call `qs = self.queryset.filter(**{'%s__in' % key: value})`.
5. Build `pks = {str(getattr(o, key)) for o in qs}`.
6. For each val in value: if `str(val) not in pks`, raise ValidationError(invalid_choice error with params).
7. Return qs.

**`prepare_value(self, value)`:** If value is iterable (not str, not a model instance), call parent's prepare_value on each element and return list; else call parent's prepare_value.

**`has_changed(self, initial, data)`:** If disabled, return False. Default None to `[]`. If lengths differ, return True. Build sets: `{str(value) for value in self.prepare_value(initial)}` vs `{str(value) for value in data}`; return inequality.

---

### Function: `modelform_defines_fields(form_class)`

Returns whether a form class explicitly defines fields via its Meta (as opposed to only having declared fields).

**Logic:** Returns `hasattr(form_class, '_meta') and (form_class._meta.fields is not None or form_class._meta.exclude is not None)`.