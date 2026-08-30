## django/contrib/contenttypes/fields.py
Here is the complete natural-language specification of `django/contrib/contenttypes/fields.py`:

---

## Module-Level Preamble

### Imports

```python
import functools
import itertools
from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.core import checks
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.db import DEFAULT_DB_ALIAS, models, router, transaction
from django.db.models import DO_NOTHING, ForeignObject, ForeignObjectRel
from django.db.models.base import ModelBase, make_foreign_order_accessors
from django.db.models.fields.mixins import FieldCacheMixin
from django.db.models.fields.related import (
    ReverseManyToOneDescriptor,
    lazy_related_operation,
)
from django.db.models.query_utils import PathInfo
from django.db.models.sql import AND
from django.db.models.sql.where import WhereNode
from django.db.models.utils import AltersData
from django.utils.functional import cached_property
```

### Constants & Globals

None. All logic is encapsulated in classes and one factory function defined below.

---

## Code Objects

### Class `GenericForeignKey(FieldCacheMixin)`

**Purpose:** Provides a generic many-to-one relation through `content_type` and `object_id` fields on the containing model. Also acts as a descriptor for accessing the related object from an instance.

**Class-level attributes (field flags):**
- `auto_created = False`
- `concrete = False`
- `editable = False`
- `hidden = False`
- `is_relation = True`
- `many_to_many = False`
- `many_to_one = True`
- `one_to_many = False`
- `one_to_one = False`
- `related_model = None`
- `remote_field = None`

**`__init__(self, ct_field="content_type", fk_field="object_id", for_concrete_model=True)`**
Sets instance attributes: `self.ct_field`, `self.fk_field`, `self.for_concrete_model`. Also sets `self.editable = False`, `self.rel = None`, `self.column = None`.

**`contribute_to_class(self, cls, name, **kwargs)`**
Assigns `self.name = name` and `self.model = cls`. Registers the field on `cls._meta` as a private field via `add_field(self, private=True)`. Sets `setattr(cls, name, self)` to install itself as a Python descriptor on the class.

**`get_filter_kwargs_for_object(self, obj)`**
Returns a dict `{self.fk_field: getattr(obj, self.fk_field), self.ct_field: getattr(obj, self.ct_field)}` — used for filtering queries by this GFK's values on `obj`.

**`get_forward_related_filter(self, obj)`**
Returns `{self.fk_field: obj.pk, self.ct_field: ContentType.objects.get_for_model(obj).pk}` — a filter dict matching objects whose content type and object ID correspond to `obj`.

**`__str__(self)`**
Returns `"%s.%s" % (model._meta.label, self.name)`, where `model = self.model`.

**`check(self, **kwargs)`**
Returns the concatenation of three lists: `self._check_field_name()`, `self._check_object_id_field()`, `self._check_content_type_field()`. Each returns a list of Django check `Error` objects (or empty list).

**`_check_field_name(self)`**
If `self.name.endswith("_")`, returns `[checks.Error("Field names must not end with an underscore.", obj=self, id="fields.E001")]`; otherwise `[]`.

**`_check_object_id_field(self)`**
Attempts `self.model._meta.get_field(self.fk_field)`. If it raises `FieldDoesNotExist`, returns `[checks.Error("The GenericForeignKey object ID references the nonexistent field '%s'." % self.fk_field, obj=self, id="contenttypes.E001")]`; otherwise `[]`.

**`_check_content_type_field(self)`**
Attempts `self.model._meta.get_field(self.ct_field)`. If it raises `FieldDoesNotExist`, returns `[checks.Error("The GenericForeignKey content type references the nonexistent field '%s.%s'." % (self.model._meta.object_name, self.ct_field), obj=self, id="contenttypes.E002")]`. On success: if the retrieved field is not an instance of `models.ForeignKey`, returns `[checks.Error("'%s.%s' is not a ForeignKey." % (...), hint="GenericForeignKeys must use a ForeignKey to 'contenttypes.ContentType' as the 'content_type' field.", obj=self, id="contenttypes.E003")]`. If it is a ForeignKey but `field.remote_field.model != ContentType`, returns `[checks.Error("'%s.%s' is not a ForeignKey to 'contenttypes.ContentType'." % (...), hint=..., obj=self, id="contenttypes.E004")]`. Otherwise returns `[]`.

**`get_cache_name(self)`**
Returns `self.name`.

**`get_content_type(self, obj=None, id=None, using=None)`**
- If `obj is not None`: calls `ContentType.objects.db_manager(obj._state.db).get_for_model(obj, for_concrete_model=self.for_concrete_model)`.
- Elif `id is not None`: calls `ContentType.objects.db_manager(using).get_for_id(id)`.
- Else: raises `Exception("Impossible arguments to GFK.get_content_type!")`.

**`get_prefetch_queryset(self, instances, queryset=None)`**
If `queryset is not None`, raises `ValueError("Custom queryset can't be used for this lookup.")`. Groups the given `instances` by content type ID into a `defaultdict(set)` called `fk_dict`, collecting `(ct_id → set of fk_vals)`. Also builds `instance_dict[ct_id] = instance` to track which instance owns each group. Skips instances where either `ct_id` or `fk_val` is `None`. For each `(ct_id, fkeys)` pair, retrieves the `ContentType` via `self.get_content_type(id=ct_id, using=...)`, then calls `ct.get_all_objects_for_this_type(pk__in=fkeys)`, extending `ret_val`. Defines a nested key function `gfk_key(obj)` that returns `(model._meta.pk.get_prep_value(getattr(obj, self.fk_field)), model)` where `model = self.get_content_type(id=ct_id).model_class()`, or `None` if `ct_id is None`. Returns the tuple:
```python
(ret_val, lambda obj: (obj.pk, obj.__class__), gfk_key, True, self.name, False)
```

**`__get__(self, instance, cls=None)`**
- If `instance is None`, returns `self` (descriptor protocol for class-level access).
- Otherwise, retrieves the content type ID via `f = self.model._meta.get_field(self.ct_field); ct_id = getattr(instance, f.get_attname(), None)`, and `pk_val = getattr(instance, self.fk_field)`.
- Gets cached value: `rel_obj = self.get_cached_value(instance, default=None)`. If `rel_obj is None` and `self.is_cached(instance)` is true, returns `None`.
- If `rel_obj is not None`, checks `ct_match = (ct_id == self.get_content_type(obj=rel_obj, using=instance._state.db).id)` and `pk_match = (rel_obj._meta.pk.to_python(pk_val) == rel_obj.pk)`. If both match, returns `rel_obj`; else sets `rel_obj = None` and continues.
- If `ct_id is not None`, retrieves `ct = self.get_content_type(id=ct_id, using=instance._state.db)` and attempts `rel_obj = ct.get_object_for_this_type(pk=pk_val)`. Catches `ObjectDoesNotExist` silently (leaving `rel_obj = None`).
- Calls `self.set_cached_value(instance, rel_obj)` and returns `rel_obj`.

**`__set__(self, instance, value)`**
If `value is not None`, computes `ct = self.get_content_type(obj=value)` and `fk = value.pk`; otherwise both are `None`. Sets `setattr(instance, self.ct_field, ct)`, `setattr(instance, self.fk_field, fk)`, and `self.set_cached_value(instance, value)`.

---

### Class `GenericRel(ForeignObjectRel)`

**Purpose:** Stores information about the reverse relation created by `GenericRelation`.

**`__init__(self, field, to, related_name=None, related_query_name=None, limit_choices_to=None)`**
Calls `super().__init__()` with: `field`, `to`, `related_name=related_query_name or "+"`, `related_query_name=related_query_name`, `limit_choices_to=limit_choices_to`, `on_delete=DO_NOTHING`.

---

### Class `GenericRelation(ForeignObject)`

**Purpose:** Provides a reverse relation to objects that have a matching `GenericForeignKey` pointing back.

**Class-level attributes (field flags):**
- `auto_created = False`
- `empty_strings_allowed = False`
- `many_to_many = False`
- `many_to_one = False`
- `one_to_many = True`
- `one_to_one = False`
- `rel_class = GenericRel`
- `mti_inherited = False`

**`__init__(self, to, object_id_field="object_id", content_type_field="content_type", for_concrete_model=True, related_query_name=None, limit_choices_to=None, **kwargs)`**
Builds `kwargs["rel"] = self.rel_class(self, to, related_query_name=related_query_name, limit_choices_to=limit_choices_to)`. Sets `kwargs["null"] = True`, `kwargs["blank"] = True`, `kwargs["on_delete"] = models.CASCADE`, `kwargs["editable"] = False`, `kwargs["serialize"] = False`. Calls `super().__init__(to, from_fields=[object_id_field], to_fields=[], **kwargs)`. Sets instance attributes: `self.object_id_field_name = object_id_field`, `self.content_type_field_name = content_type_field`, `self.for_concrete_model = for_concrete_model`.

**`check(self, **kwargs)`**
Returns `[*super().check(**kwargs), *self._check_generic_foreign_key_existence()]`.

**`_is_matching_generic_foreign_key(self, field)`**
Returns `True` if `field` is an instance of `GenericForeignKey` and `field.ct_field == self.content_type_field_name` and `field.fk_field == self.object_id_field_name`; else `False`.

**`_check_generic_foreign_key_existence(self)`**
Gets `target = self.remote_field.model`. If `isinstance(target, ModelBase)`, iterates over `target._meta.private_fields` checking `_is_matching_generic_foreign_key(field)` for each. If any match, returns `[]`; else returns `[checks.Error("The GenericRelation defines a relation with the model '%s', but that model does not have a GenericForeignKey." % target._meta.label, obj=self, id="contenttypes.E004")]`. If `target` is not a `ModelBase`, returns `[]`.

**`resolve_related_fields(self)`**
Sets `self.to_fields = [self.model._meta.pk.name]`. Returns `[(self.remote_field.model._meta.get_field(self.object_id_field_name), self.model._meta.pk)]`.

**`_get_path_info_with_parent(self, filtered_relation)`**
Handles multi-table inheritance: if the GFK is on a parent model and this GenericRelation points to a child. Gets `opts = self.remote_field.model._meta.concrete_model._meta`, then `parent_opts = opts.get_field(self.object_id_field_name).model._meta` and `target = parent_opts.pk`. Appends one `PathInfo(from_opts=self.model._meta, to_opts=parent_opts, target_fields=(target,), join_field=self.remote_field, m2m=True, direct=False, filtered_relation=filtered_relation)`. Walks the inheritance chain from child up to parent via `opts.get_ancestor_link(parent_opts.model)`, collecting fields into `parent_field_chain`, reverses it, and for each field extends `path` with `field.remote_field.path_infos`. Returns `path`.

**`get_path_info(self, filtered_relation=None)`**
Gets `object_id_field = opts.get_field(self.object_id_field_name)` where `opts = self.remote_field.model._meta`. If `object_id_field.model != opts.model`, delegates to `_get_path_info_with_parent(filtered_relation)`. Otherwise returns a single-element list with one `PathInfo(from_opts=self.model._meta, to_opts=opts, target_fields=(opts.pk,), join_field=self.remote_field, m2m=True, direct=False, filtered_relation=filtered_relation)`.

**`get_reverse_path_info(self, filtered_relation=None)`**
Returns a single-element list with one `PathInfo(from_opts=self.remote_field.model._meta, to_opts=self.model._meta, target_fields=(opts.pk,), join_field=self, m2m=not self.unique, direct=False, filtered_relation=filtered_relation)`.

**`value_to_string(self, obj)`**
Calls `qs = getattr(obj, self.name).all()` and returns `str([instance.pk for instance in qs])`.

**`contribute_to_class(self, cls, name, **kwargs)`**
Sets `kwargs["private_only"] = True`, calls `super().contribute_to_class(cls, name, **kwargs)`, sets `self.model = cls`. If `self.mti_inherited`, sets `self.remote_field.related_name = "+"` and `self.remote_field.related_query_name = None`. Sets `setattr(cls, self.name, ReverseGenericManyToOneDescriptor(self.remote_field))`. If `not cls._meta.abstract`, defines a nested function `make_generic_foreign_order_accessors(related_model, model)` that calls `make_foreign_order_accessors(model, related_model)` if `self._is_matching_generic_foreign_key(model._meta.order_with_respect_to)`. Registers this via `lazy_related_operation(make_generic_foreign_order_accessors, self.model, self.remote_field.model)`.

**`set_attributes_from_rel(self)`**
No-op (empty body).

**`get_internal_type(self)`**
Returns `"ManyToManyField"`.

**`get_content_type(self)`**
Returns `ContentType.objects.get_for_model(self.model, for_concrete_model=self.for_concrete_model)`.

**`get_extra_restriction(self, alias, remote_alias)`**
Gets `field = self.remote_field.model._meta.get_field(self.content_type_field_name)`, gets `contenttype_pk = self.get_content_type().pk`, creates a lookup: `lookup = field.get_lookup("exact")(field.get_col(remote_alias), contenttype_pk)`. Returns `WhereNode([lookup], connector=AND)`.

**`bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS)`**
Returns the queryset result of filtering `self.remote_field.model._base_manager.db_manager(using)` with `{content_type_field_name + "__pk": ContentType.objects.db_manager(using).get_for_model(self.model, for_concrete_model=self.for_concrete_model).pk, object_id_field_name + "__in": [obj.pk for obj in objs]}`.

---

### Class `ReverseGenericManyToOneDescriptor(ReverseManyToOneDescriptor)`

**Purpose:** Descriptor providing access to the related objects manager on the one-to-many relation created by `GenericRelation`. Accessed as e.g. `post.comments` when `comments = GenericRelation(Comment)`.

**`@cached_property related_manager_cls(self)`**
Returns `create_generic_related_manager(self.rel.model._default_manager.__class__, self.rel)`.

---

### Function `create_generic_related_manager(superclass, rel)`

**Purpose:** Factory function that dynamically creates a manager class subclassing `superclass` (typically the model's default manager) and mixing in `AltersData`, with behaviors specific to generic relations. Returns the new class.

The returned class is named `GenericRelatedObjectManager` internally:

**`__init__(self, instance=None)`**
Calls `super().__init__()`. Sets `self.instance = instance`, `self.model = rel.model`. Creates `self.get_content_type = functools.partial(ContentType.objects.db_manager(instance._state.db).get_for_model, for_concrete_model=rel.field.for_concrete_model)`. Sets `self.content_type = self.get_content_type(instance)`, `self.content_type_field_name = rel.field.content_type_field_name`, `self.object_id_field_name = rel.field.object_id_field_name`, `self.prefetch_cache_name = rel.field.attname`, `self.pk_val = instance.pk`. Sets `self.core_filters = {content_type_field_name + "__pk": self.content_type.id, object_id_field_name: self.pk_val}`.

**`__call__(self, *, manager)`**
Gets `manager = getattr(self.model, manager)`, creates a new manager class via `create_generic_related_manager(manager.__class__, rel)`, returns an instance of it with `instance=self.instance`.

**Class attributes:**
- `do_not_call_in_templates = True`

**`__str__(self)`**
Returns `repr(self)`.

**`_apply_rel_filters(self, queryset)`**
Gets the database via `db = self._db or router.db_for_read(self.model, instance=self.instance)`. Returns `queryset.using(db).filter(**self.core_filters)`.

**`_remove_prefetched_objects(self)`**
Tries to pop `self.prefetch_cache_name` from `self.instance._prefetched_objects_cache`; silently ignores `AttributeError`/`KeyError`.

**`get_queryset(self)`**
Tries to return `self.instance._prefetched_objects_cache[self.prefetch_cache_name]`. On miss, calls `super().get_queryset()` and applies `_apply_rel_filters(queryset)`.

**`get_prefetch_queryset(self, instances, queryset=None)`**
If `queryset is None`, sets `queryset = super().get_queryset()`. Calls `queryset._add_hints(instance=instances[0])`, then `queryset.using(queryset._db or self._db)`. Groups instances by content type PK using `itertools.groupby(sorted(instances, key=lambda obj: self.get_content_type(obj).pk), lambda obj: self.get_content_type(obj).pk)`, building a list of `models.Q` objects with `(content_type_field_name + "__pk", content_type_id)` and `(object_id_field_name + "__in", {obj.pk for obj in objs})`. Combines them with `connector=models.Q.OR`. Gets `object_id_converter = instances[0]._meta.pk.to_python`, `content_type_id_field_name = "%s_id" % self.content_type_field_name`. Returns the tuple:
```python
(queryset.filter(query),
 lambda relobj: (object_id_converter(getattr(relobj, self.object_id_field_name)), getattr(relobj, content_type_id_field_name)),
 lambda obj: (obj.pk, self.get_content_type(obj).pk),
 False,
 self.prefetch_cache_name,
 False)
```

**`add(self, *objs, bulk=True)`**
Calls `_remove_prefetched_objects()`. Gets `db = router.db_for_write(self.model, instance=self.instance)`. Defines nested `check_and_update_obj(obj)`: if `obj` is not an instance of `self.model`, raises `TypeError("'instance' expected, got ...")`; otherwise sets `setattr(obj, self.content_type_field_name, self.content_type)` and `setattr(obj, self.object_id_field_name, self.pk_val)`. If `bulk=True`: iterates over `objs`, raising `ValueError` if any obj is unsaved (`obj._state.adding`) or on a different db; calls `check_and_update_obj`; collects pks. Then calls `self.model._base_manager.using(db).filter(pk__in=pks).update(content_type_field_name=self.content_type, object_id_field_name=self.pk_val)`. If `bulk=False`: enters `transaction.atomic(using=db, savepoint=False)` and for each obj calls `check_and_update_obj(obj); obj.save()`. Sets `add.alters_data = True`.

**`remove(self, *objs, bulk=True)`**
If no objs, returns. Otherwise calls `_clear(self.filter(pk__in=[o.pk for o in objs]), bulk)`. Sets `remove.alters_data = True`.

**`clear(self, *, bulk=True)`**
Calls `_clear(self, bulk)`. Sets `clear.alters_data = True`.

**`_clear(self, queryset, bulk)`**
Calls `_remove_prefetched_objects()`. Gets `db = router.db_for_write(self.model, instance=self.instance)`, applies `queryset.using(db)`. If `bulk=True`: calls `queryset.delete()` (which has its own atomic block). If `bulk=False`: enters `transaction.atomic(using=db, savepoint=False)` and iterates over queryset calling `obj.delete()`. Sets `_clear.alters_data = True`.

**`set(self, objs, *, bulk=True, clear=False)`**
Evaluates `objs = tuple(objs)`. Gets `db = router.db_for_write(self.model, instance=self.instance)`. Enters `transaction.atomic(using=db, savepoint=False)`. If `clear=True`: calls `self.clear()` then `self.add(*objs, bulk=bulk)`. Else: computes `old_objs = set(self.using(db).all())`, iterates over `objs` removing matches from `old_objs` and collecting non-matches into `new_objs`. Calls `self.remove(*old_objs)` then `self.add(*new_objs, bulk=bulk)`. Sets `set.alters_data = True`.

**`create(self, **kwargs)`**
Calls `_remove_prefetched_objects()`. Adds `content_type_field_name=self.content_type` and `object_id_field_name=self.pk_val` to kwargs. Gets `db = router.db_for_write(self.model, instance=self.instance)`. Returns `super().using(db).create(**kwargs)`. Sets `create.alters_data = True`.

**`get_or_create(self, **kwargs)`**
Adds the same content type and object ID fields to kwargs. Gets db. Returns `super().using(db).get_or_create(**kwargs)`. Sets `get_or_create.alters_data = True`.

**`update_or_create(self, **kwargs)`**
Adds the same content type and object ID fields to kwargs. Gets db. Returns `super().using(db).update_or_create(**kwargs)`. Sets `update_or_create.alters_data = True`.

## django/db/models/fields/related_descriptors.py
Now I have the full file content. Let me compile the comprehensive natural-language specification:

---

## Module-Level Preamble

### Imports

```python
from django.core.exceptions import FieldError
from django.db import (
    DEFAULT_DB_ALIAS,
    NotSupportedError,
    connections,
    router,
    transaction,
)
from django.db.models import Q, Window, signals
from django.db.models.functions import RowNumber
from django.db.models.lookups import GreaterThan, LessThanOrEqual
from django.db.models.query import QuerySet
from django.db.models.query_utils import DeferredAttribute
from django.db.models.utils import AltersData, resolve_callables
from django.utils.functional import cached_property
```

### Module Docstring Summary

This module provides descriptor classes for accessing related objects across Django model relations. Relations come in three types (many-to-one, one-to-one, many-to-many) and two directions (forward/reverse), yielding six combinations: `ForwardManyToOneDescriptor`, `ForwardOneToOneDescriptor` (subclass of the former), `ReverseOneToOneDescriptor`, `ReverseManyToOneDescriptor`, and `ManyToManyDescriptor` (used for both forward and reverse M2M).

---

## Code Objects

### Class `ForeignKeyDeferredAttribute(DeferredAttribute)`

**Header:** Subclass of `DeferredAttribute`. Overrides only `__set__`.

**Method `__set__(self, instance, value)`:**
1. If the current cached value (`instance.__dict__[self.field.attname]`) differs from `value` **and** the field is already cached on the instance (`self.field.is_cached(instance)`), delete the old cached value via `self.field.delete_cached_value(instance)`.
2. Always assign `value` to `instance.__dict__[self.field.attname]`.

---

### Function `_filter_prefetch_queryset(queryset, field_name, instances)`

**Header:** Takes a `QuerySet`, a string `field_name`, and an iterable of model instances. Returns a filtered `QuerySet`.

**Logic:**
1. Build a `Q` predicate: `{f"{field_name}__in": instances}`.
2. Determine the database alias: `queryset._db or DEFAULT_DB_ALIAS`.
3. If `queryset.query.is_sliced` (i.e., has LIMIT/OFFSET):
   - Raise `NotSupportedError` if the database backend does not support window functions (`connections[db].features.supports_over_clause`).
   - Extract `low_mark` and `high_mark` from `queryset.query`.
   - Get the query's `ORDER BY` expressions via `queryset.query.get_compiler(using=db).get_order_by()`.
   - Create a `Window(RowNumber(), partition_by=field_name, order_by=order_by)`.
   - Add `GreaterThan(window, low_mark)` to the predicate. If `high_mark is not None`, also add `LessThanOrEqual(window, high_mark)`.
   - Clear the query's limits via `queryset.query.clear_limits()`.
4. Return `queryset.filter(predicate)`.

---

### Class `ForwardManyToOneDescriptor`

**Header:** `class ForwardManyToOneDescriptor` with no base classes (standalone descriptor). Initialized by a field-with-relation object.

**Attributes:**
- `self.field`: The `Field` object defining the relation (set in `__init__`).

**Method `__init__(self, field_with_rel)`:** Sets `self.field = field_with_rel`.

**Cached Property `RelatedObjectDoesNotExist`:** Dynamically creates a new exception class inheriting from `(self.field.remote_field.model.DoesNotExist, AttributeError)`, with `__module__` set to `self.field.model.__module__` and `__qualname__` set to `"{model_qualname}.{field_name}.RelatedObjectDoesNotExist"`. This avoids referencing unresolved model references at initialization time.

**Method `is_cached(self, instance)`:** Returns `self.field.is_cached(instance)`.

**Method `get_queryset(self, **hints)`:** Returns `self.field.remote_field.model._base_manager.db_manager(hints=hints).all()`.

**Method `get_prefetch_queryset(self, instances, queryset=None)`:**
1. If `queryset is None`, call `self.get_queryset()`.
2. Call `queryset._add_hints(instance=instances[0])`.
3. Set `rel_obj_attr = self.field.get_foreign_related_value`, `instance_attr = self.field.get_local_related_value`.
4. Build `instances_dict = {instance_attr(inst): inst for inst in instances}`.
5. Get `related_field = self.field.foreign_related_fields[0]` and `remote_field = self.field.remote_field`.
6. If `remote_field.is_hidden()` or `len(self.field.foreign_related_fields) == 1`, build query as `{f"{related_field.name}__in": {instance_attr(inst)[0] for inst in instances}}`; otherwise use `{f"{self.field.related_query_name()}__in": instances}`.
7. Filter: `queryset = queryset.filter(**query)`.
8. If not a multiple relation (`not remote_field.multiple`), iterate over `queryset`: for each `rel_obj`, look up the owning instance via `instances_dict[rel_obj_attr(rel_obj)]` and call `remote_field.set_cached_value(rel_obj, instance)`.
9. Return tuple: `(queryset, rel_obj_attr, instance_attr, True, self.field.get_cache_name(), False)`.

**Method `get_object(self, instance)`:** Calls `self.get_queryset(instance=instance)` then returns `qs.get(self.field.get_reverse_related_filter(instance))`.

**Method `__get__(self, instance, cls=None)`:**
1. If `instance is None`, return `self` (class-level access).
2. Try to get the cached related object via `self.field.get_cached_value(instance)`. On `KeyError`:
   - Check if any local related field has a non-None value: `has_value = None not in self.field.get_local_related_value(instance)`.
   - If `has_value`, check for an ancestor link (`instance._meta.get_ancestor_link(self.field.model)`). If it exists and is cached, get the ancestor's cached value as fallback. Otherwise set `rel_obj = None`.
   - If `rel_obj is None` and `has_value`, fetch from DB via `self.get_object(instance)`. For one-to-one relations (`not remote_field.multiple`), also cache the current instance on the related object: `remote_field.set_cached_value(rel_obj, instance)`.
3. Set the cache: `self.field.set_cached_value(instance, rel_obj)`.
4. If `rel_obj is None and not self.field.null`, raise `self.RelatedObjectDoesNotExist` with message `"%s has no %s." % (self.field.model.__name__, self.field.name)`. Otherwise return `rel_obj`.

**Method `__set__(self, instance, value)`:**
1. If `value is not None` and not an instance of the related model's concrete class (`isinstance(value, self.field.remote_field.model._meta.concrete_model)`), raise `ValueError` with message `'Cannot assign "%r": "%s.%s" must be a "%s" instance.'`.
2. If `value is not None`:
   - Set `instance._state.db` via `router.db_for_write(instance.__class__, instance=value)` if it's `None`.
   - Set `value._state.db` via `router.db_for_write(value.__class__, instance=instance)` if it's `None`.
   - If `not router.allow_relation(value, instance)`, raise `ValueError` about database router preventing the relation.
3. Get `remote_field = self.field.remote_field`.
4. If `value is None`:
   - Get the previously-related object from cache: `related = self.field.get_cached_value(instance, default=None)`.
   - If `related is not None`, clear its reverse-cache: `remote_field.set_cached_value(related, None)`.
   - For each `(lh_field, rh_field)` in `self.field.related_fields`, set `setattr(instance, lh_field.attname, None)`.
5. Else (`value is not None`): for each `(lh_field, rh_field)` in `self.field.related_fields`, do `setattr(instance, lh_field.attname, getattr(value, rh_field.attname))`.
6. Cache the new value: `self.field.set_cached_value(instance, value)`.
7. If one-to-one (`value is not None and not remote_field.multiple`), cache current instance on related object: `remote_field.set_cached_value(value, instance)`.

**Method `__reduce__(self)`:** Returns `(getattr, (self.field.model, self.field.name))` so pickling retrieves the descriptor from the model class rather than serializing a copy.

---

### Class `ForwardOneToOneDescriptor(ForwardManyToOneDescriptor)`

**Header:** Inherits from `ForwardManyToOneDescriptor`. No additional attributes.

**Method `get_object(self, instance)`:**
1. If `self.field.remote_field.parent_link` is True (multi-table inheritance parent link):
   - Get deferred fields: `deferred = instance.get_deferred_fields()`.
   - Collect concrete field attribute names of the related model: `[field.attname for field in rel_model._meta.concrete_fields]` where `rel_model = self.field.remote_field.model`.
   - If none of the deferred fields are in that list, construct the parent object directly from instance data: `kwargs = {field: getattr(instance, field) for field in fields}`, create `obj = rel_model(**kwargs)`, copy `_state.adding` and `_state.db` from the instance, return `obj`.
2. Otherwise, fall through to `super().get_object(instance)` (standard DB query).

**Method `__set__(self, instance, value)`:**
1. Call `super().__set__(instance, value)`.
2. If `self.field.primary_key and self.field.remote_field.parent_link`:
   - Find inherited PK fields: `[field for field in opts.concrete_fields if field.primary_key and field.remote_field]` where `opts = instance._meta`.
   - For each such field, get the related model's PK attribute name: `rel_model_pk_name = field.remote_field.model._meta.pk.attname`.
   - Get raw value: `getattr(value, rel_model_pk_name) if value is not None else None`.
   - Set it on the instance: `setattr(instance, rel_model_pk_name, raw_value)`.

---

### Class `ReverseOneToOneDescriptor`

**Header:** Standalone descriptor. Initialized by a `RelatedObject` (e.g., `OneToOneRel`).

**Attributes:**
- `self.related`: The `OneToOneRel` representing the reverse relation.

**Method `__init__(self, related)`:** Sets `self.related = related`.

**Cached Property `RelatedObjectDoesNotExist`:** Dynamically creates exception class inheriting from `(self.related.related_model.DoesNotExist, AttributeError)`, with `__module__` set to `self.related.model.__module__` and `__qualname__` set to `"{model_qualname}.{relation_name}.RelatedObjectDoesNotExist"`.

**Method `is_cached(self, instance)`:** Returns `self.related.is_cached(instance)`.

**Method `get_queryset(self, **hints)`:** Returns `self.related.related_model._base_manager.db_manager(hints=hints).all()`.

**Method `get_prefetch_queryset(self, instances, queryset=None)`:**
1. If `queryset is None`, call `self.get_queryset()`.
2. Call `queryset._add_hints(instance=instances[0])`.
3. Set `rel_obj_attr = self.related.field.get_local_related_value`, `instance_attr = self.related.field.get_foreign_related_value`.
4. Build `instances_dict = {instance_attr(inst): inst for inst in instances}`.
5. Query: `{f"{self.related.field.name}__in": instances}`, filter the queryset.
6. For each `rel_obj` in `queryset`, look up owning instance via `instances_dict[rel_obj_attr(rel_obj)]` and call `self.related.field.set_cached_value(rel_obj, instance)`.
7. Return tuple: `(queryset, rel_obj_attr, instance_attr, True, self.related.get_cache_name(), False)`.

**Method `__get__(self, instance, cls=None)`:**
1. If `instance is None`, return `self`.
2. Try to get cached related object via `self.related.get_cached_value(instance)`. On `KeyError`:
   - Get `related_pk = instance.pk`. If `None`, set `rel_obj = None`.
   - Otherwise, build filter: `filter_args = self.related.field.get_forward_related_filter(instance)`, query `self.get_queryset(instance=instance).get(**filter_args)`. Catch `DoesNotExist` → `rel_obj = None`. On success, cache forward accessor on related object: `self.related.field.set_cached_value(rel_obj, instance)`.
3. Cache: `self.related.set_cached_value(instance, rel_obj)`.
4. If `rel_obj is None`, raise `self.RelatedObjectDoesNotExist` with message `"%s has no %s." % (instance.__class__.__name__, self.related.get_accessor_name())`. Otherwise return `rel_obj`.

**Method `__set__(self, instance, value)`:**
1. If `value is None`:
   - Get cached related: `rel_obj = self.related.get_cached_value(instance, default=None)`.
   - If `rel_obj is not None`, delete the cache on instance (`self.related.delete_cached_value(instance)`) and set the FK field to None on the related object: `setattr(rel_obj, self.related.field.name, None)`.
2. Else if `not isinstance(value, self.related.related_model)`, raise `ValueError` with message `'Cannot assign "%r": "%s.%s" must be a "%s" instance.'`.
3. Else (`value is not None and correct type`):
   - Set database routing for both instances (same logic as `ForwardManyToOneDescriptor.__set__`).
   - Check router allows relation; raise `ValueError` if not.
   - Build `related_pk = tuple(getattr(instance, field.attname) for field in self.related.field.foreign_related_fields)`.
   - For each `(index, field)` in enumerate of `self.related.field.local_related_fields`, set `setattr(value, field.attname, related_pk[index])`.
   - Cache: `self.related.set_cached_value(instance, value)` and forward cache on related object: `self.related.field.set_cached_value(value, instance)`.

**Method `__reduce__(self)`:** Returns `(getattr, (self.related.model, self.related.name))`.

---

### Class `ReverseManyToOneDescriptor`

**Header:** Standalone descriptor. Initialized by a `ManyToManyRel`/`ManyToOneRel` object.

**Attributes:**
- `self.rel`: The relation object.
- `self.field`: Alias set to `rel.field`.

**Method `__init__(self, rel)`:** Sets `self.rel = rel`, `self.field = rel.field`.

**Cached Property `related_manager_cls`:** Calls `create_reverse_many_to_one_manager(related_model._default_manager.__class__, self.rel)` where `related_model = self.rel.related_model`. Returns the dynamically created manager class.

**Method `__get__(self, instance, cls=None)`:**
1. If `instance is None`, return `self`.
2. Return `self.related_manager_cls(instance)` — instantiates the dynamic manager bound to this instance.

**Method `_get_set_deprecation_msg_params(self)`:** Returns tuple `("reverse side of a related set", self.rel.get_accessor_name())`.

**Method `__set__(self, instance, value)`:** Always raises `TypeError` with message `"Direct assignment to the %s is prohibited. Use %s.set() instead." % (params[0], params[1])`.

---

### Function `create_reverse_many_to_one_manager(superclass, rel)`

**Header:** Factory function that creates and returns a dynamically-defined `RelatedManager` class inheriting from `(superclass, AltersData)`. `rel` is the relation object.

**Dynamically defined class `RelatedManager`:**

**Method `__init__(self, instance)`:** Calls `super().__init__()`. Sets `self.instance = instance`, `self.model = rel.related_model`, `self.field = rel.field`, `self.core_filters = {self.field.name: instance}`.

**Method `__call__(self, *, manager)`:** Gets the named manager from `self.model` via `getattr(self.model, manager)`. Creates a new manager class via `create_reverse_many_to_one_manager(manager.__class__, rel)` and returns an instance bound to `self.instance`.

**Attribute:** `do_not_call_in_templates = True`.

**Method `_check_fk_val(self)`:** For each field in `self.field.foreign_related_fields`, if `getattr(self.instance, field.attname) is None`, raise `ValueError` saying the instance needs a value for that field.

**Method `_apply_rel_filters(self, queryset)`:**
1. Determine DB: `self._db or router.db_for_read(self.model, instance=self.instance)`.
2. Check if empty strings are treated as nulls via `connections[db].features.interprets_empty_strings_as_nulls`.
3. Call `queryset._add_hints(instance=self.instance)`. If `self._db`, apply `.using(self._db)`. Set `queryset._defer_next_filter = True`. Filter by `self.core_filters`.
4. For each field in `self.field.foreign_related_fields`: if the instance's FK value is `None` or empty-string-with-null semantics, return `queryset.none()`.
5. If `self.field.many_to_one`, try to get `target_field = self.field.target_field`; on `FieldError` (composite FK), build `rel_obj_id = tuple(getattr(self.instance, tf.attname) for tf in self.field.path_infos[-1].target_fields)`; else `rel_obj_id = getattr(self.instance, target_field.attname)`. Set `queryset._known_related_objects = {self.field: {rel_obj_id: self.instance}}`.
6. Return the queryset.

**Method `_remove_prefetched_objects(self)`:** Tries to pop `self.field.remote_field.get_cache_name()` from `self.instance._prefetched_objects_cache`; catches `AttributeError`/`KeyError` silently.

**Method `get_queryset(self)`:**
1. If `self.instance.pk is None`, raise `ValueError`.
2. Try to return cached prefetched objects: `self.instance._prefetched_objects_cache[self.field.remote_field.get_cache_name()]`. On `(AttributeError, KeyError)`, call `super().get_queryset()` and apply `_apply_rel_filters()`.

**Method `get_prefetch_queryset(self, instances, queryset=None)`:**
1. If `queryset is None`, call `super().get_queryset()`.
2. Call `_add_hints(instance=instances[0])` and `.using(queryset._db or self._db)`.
3. Set `rel_obj_attr = self.field.get_local_related_value`, `instance_attr = self.field.get_foreign_related_value`. Build `instances_dict`.
4. Filter via `_filter_prefetch_queryset(queryset, self.field.name, instances)`.
5. For each `rel_obj` in queryset: if not already cached (`not self.field.is_cached(rel_obj)`), set the FK on it: `setattr(rel_obj, self.field.name, instance)` where `instance = instances_dict[rel_obj_attr(rel_obj)]`.
6. Get cache name and return tuple: `(queryset, rel_obj_attr, instance_attr, False, cache_name, False)`.

**Method `add(self, *objs, bulk=True)`:**
1. Call `_check_fk_val()` and `_remove_prefetched_objects()`. Get DB via `router.db_for_write(self.model, instance=self.instance)`.
2. Define inner `check_and_update_obj(obj)`: if not an instance of `self.model`, raise `TypeError`; else set `setattr(obj, self.field.name, self.instance)`.
3. If `bulk`: iterate objs — check/update each, verify it's saved (`not obj._state.adding`) and on the correct DB; collect PKs; bulk-update via `self.model._base_manager.using(db).filter(pk__in=pks).update(**{self.field.name: self.instance})`.
4. If not `bulk`: within `transaction.atomic(using=db, savepoint=False)`, check/update each obj and call `obj.save()`.

**Attribute:** `add.alters_data = True`.

**Method `create(self, **kwargs)`:** Calls `_check_fk_val()`, adds `{self.field.name: self.instance}` to kwargs, gets DB, returns `super(RelatedManager, self.db_manager(db)).create(**kwargs)`.

**Attribute:** `create.alters_data = True`.

**Method `get_or_create(self, **kwargs)`:** Calls `_check_fk_val()`, adds FK to kwargs, gets DB, returns `super(RelatedManager, self.db_manager(db)).get_or_create(**kwargs)`.

**Attribute:** `get_or_create.alters_data = True`.

**Method `update_or_create(self, **kwargs)`:** Same pattern as `get_or_create` but calls `update_or_create`.

**Attribute:** `update_or_create.alters_data = True`.

**Conditional methods (only if `rel.field.null` is True):**

**Method `remove(self, *objs, bulk=True)`:**
1. If no objs, return early. Call `_check_fk_val()`. Get FK value: `val = self.field.get_foreign_related_value(self.instance)`.
2. For each obj: if not correct type, raise `TypeError`; if the object's local related value equals `val`, add its PK to `old_ids`; else raise `self.field.remote_field.model.DoesNotExist`.
3. Call `_clear(self.filter(pk__in=old_ids), bulk)`.

**Attribute:** `remove.alters_data = True`.

**Method `clear(self, *, bulk=True)`:** Calls `_check_fk_val()`, then `_clear(self, bulk)`.

**Attribute:** `clear.alters_data = True`.

**Method `_clear(self, queryset, bulk)`:**
1. Call `_remove_prefetched_objects()`. Get DB via `router.db_for_write(self.model, instance=self.instance)`. Apply `.using(db)`.
2. If `bulk`: `queryset.update(**{self.field.name: None})`.
3. Else: within `transaction.atomic(using=db, savepoint=False)`, for each obj in queryset, set FK to None and call `obj.save(update_fields=[self.field.name])`.

**Attribute:** `_clear.alters_data = True`.

**Method `set(self, objs, *, bulk=True, clear=False)`:**
1. Call `_check_fk_val()`. Force evaluation: `objs = tuple(objs)`.
2. If `rel.field.null`: within `transaction.atomic(using=db, savepoint=False)` where `db = router.db_for_write(...)`: if `clear`, call `self.clear(bulk=bulk)` then `self.add(*objs, bulk=bulk)`; else compute `old_objs = set(self.using(db).all())`, iterate objs — remove from old_objs if present, collect new ones in `new_objs`; then `self.remove(*old_objs, bulk=bulk)` and `self.add(*new_objs, bulk=bulk)`.
3. Else (FK not nullable): call `self.add(*objs, bulk=bulk)`.

**Attribute:** `set.alters_data = True`.

**Return value:** Returns the dynamically created `RelatedManager` class.

---

### Class `ManyToManyDescriptor(ReverseManyToOneDescriptor)`

**Header:** Inherits from `ReverseManyToOneDescriptor`.

**Attributes:**
- `self.reverse`: Boolean set in `__init__` (True for reverse side, False for forward).

**Method `__init__(self, rel, reverse=False)`:** Calls `super().__init__(rel)`, sets `self.reverse = reverse`.

**Property `through`:** Returns `self.rel.through` (the intermediary model).

**Cached Property `related_manager_cls`:** Determines `related_model` as `self.rel.related_model if self.reverse else self.rel.model`. Calls `create_forward_many_to_many_manager(related_model._default_manager.__class__, self.rel, reverse=self.reverse)`. Returns the dynamically created manager class.

**Method `_get_set_deprecation_msg_params(self)`:** Returns tuple `("%s side of a many-to-many set" % ("reverse" if self.reverse else "forward"), self.rel.get_accessor_name() if self.reverse else self.field.name)`.

---

### Function `create_forward_many_to_many_manager(superclass, rel, reverse)`

**Header:** Factory function that creates and returns a dynamically-defined `ManyRelatedManager` class inheriting from `(superclass, AltersData)`.

**Dynamically defined class `ManyRelatedManager`:**

**Method `__init__(self, instance=None)`:**
1. Calls `super().__init__()`, sets `self.instance = instance`.
2. If not reverse: set `self.model = rel.model`, `self.query_field_name = rel.field.related_query_name()`, `self.prefetch_cache_name = rel.field.name`, `self.source_field_name = rel.field.m2m_field_name()`, `self.target_field_name = rel.field.m2m_reverse_field_name()`, `self.symmetrical = rel.symmetrical`.
3. Else (reverse): set `self.model = rel.related_model`, `self.query_field_name = rel.field.name`, `self.prefetch_cache_name = rel.field.related_query_name()`, `self.source_field_name = rel.field.m2m_reverse_field_name()`, `self.target_field_name = rel.field.m2m_field_name()`, `self.symmetrical = False`.
4. Set `self.through = rel.through`, `self.reverse = reverse`.
5. Get source and target field objects from the through model: `self.source_field = self.through._meta.get_field(self.source_field_name)`, `self.target_field = self.through._meta.get_field(self.target_field_name)`.
6. Build `self.core_filters` and `self.pk_field_names`: for each `(lh_field, rh_field)` in `self.source_field.related_fields`, set `core_filter_key = f"{self.query_field_name}__{rh_field.name}"`, map to `getattr(instance, rh_field.attname)`. Map `lh_field.name → rh_field.name` in `pk_field_names`.
7. Get `self.related_val = self.source_field.get_foreign_related_value(instance)`. If any value is `None`, raise `ValueError` about needing a value for the source field's PK.
8. If `instance.pk is None`, raise `ValueError` about needing a primary key.

**Method `__call__(self, *, manager)`:** Gets named manager from `self.model`, creates new class via factory, returns instance bound to `self.instance`.

**Attribute:** `do_not_call_in_templates = True`.

**Method `_build_remove_filters(self, removed_vals)`:**
1. Build initial Q: `Q.create([(self.source_field_name, self.related_val)])`.
2. If `removed_vals` is a QuerySet with filters (`not isinstance(removed_vals, QuerySet) or removed_vals._has_filters()`), add `&= Q.create([f"{self.target_field_name}__in", removed_vals])`; else use the raw values directly in the filter later.
3. If symmetrical: build `symmetrical_filters = Q.create([(self.target_field_name, self.related_val)])`, and if `removed_vals` has filters, add `&= Q.create([f"{self.source_field_name}__in", removed_vals])`. Combine with `|=`.
4. Return the combined filters.

**Method `_apply_rel_filters(self, queryset)`:** Call `_add_hints(instance=self.instance)`, apply `.using(self._db)` if set, set `_defer_next_filter = True`, return `queryset._next_is_sticky().filter(**self.core_filters)`.

**Method `_remove_prefetched_objects(self)`:** Tries to pop `self.prefetch_cache_name` from `self.instance._prefetched_objects_cache`; catches `(AttributeError, KeyError)` silently.

**Method `get_queryset(self)`:** Try cached prefetched objects; on miss, call `super().get_queryset()` and apply `_apply_rel_filters()`.

**Method `get_prefetch_queryset(self, instances, queryset=None)`:**
1. If `queryset is None`, call `super().get_queryset()`.
2. Call `_add_hints(instance=instances[0])` and `.using(queryset._db or self._db)`.
3. Filter via `_filter_prefetch_queryset(queryset._next_is_sticky(), self.query_field_name, instances)`.
4. For prefetch-related value extraction: get FK from through model (`fk = self.through._meta.get_field(self.source_field_name)`), build `join_table` and quote names. Use `queryset.extra(select={...})` to annotate with the source field values from the join table for each local related field.
5. Return tuple: `(queryset, lambda result: tuple(getattr(result, f"_prefetch_related_val_{f.attname}") for f in fk.local_related_fields), lambda inst: tuple(f.get_db_prep_value(getattr(inst, f.attname), connection) for f in fk.foreign_related_fields), False, self.prefetch_cache_name, False)`.

**Method `add(self, *objs, through_defaults=None)`:**
1. Call `_remove_prefetched_objects()`. Get DB via `router.db_for_write(self.through, instance=self.instance)`.
2. Within `transaction.atomic(using=db, savepoint=False)`, call `_add_items(self.source_field_name, self.target_field_name, *objs, through_defaults=through_defaults)`.
3. If symmetrical, also call `_add_items(self.target_field_name, self.source_field_name, *objs, through_defaults=through_defaults)` to add the mirror entry.

**Attribute:** `add.alters_data = True`.

**Method `remove(self, *objs)`:** Call `_remove_prefetched_objects()`, then `_remove_items(self.source_field_name, self.target_field_name, *objs)`.

**Attribute:** `remove.alters_data = True`.

**Method `clear(self)`:**
1. Get DB via `router.db_for_write(self.through, instance=self.instance)`.
2. Within `transaction.atomic(using=db, savepoint=False)`: send `m2m_changed` signal with action `"pre_clear"`, sender=`self.through`, instance=`self.instance`, reverse=`self.reverse`, model=`self.model`, pk_set=None, using=db. Call `_remove_prefetched_objects()`. Build filters via `_build_remove_filters(super().get_queryset().using(db))`. Delete matching through records: `self.through._default_manager.using(db).filter(filters).delete()`. Send `"post_clear"` signal with same params.

**Attribute:** `clear.alters_data = True`.

**Method `set(self, objs, *, clear=False, through_defaults=None)`:**
1. Force evaluation: `objs = tuple(objs)`. Get DB via `router.db_for_write(self.through, instance=self.instance)`.
2. Within `transaction.atomic(using=db, savepoint=False)`: if `clear`, call `self.clear()` then `self.add(*objs, through_defaults=through_defaults)`; else: get `old_ids = set(self.using(db).values_list(self.target_field.target_field.attname, flat=True))`. For each obj: compute FK value (via `target_field.get_foreign_related_value(obj)[0]` if instance of model, else `target_field.get_prep_value(obj)`); if in old_ids, remove it; else add to new_objs. Call `self.remove(*old_ids)`, then `self.add(*new_objs, through_defaults=through_defaults)`.

**Attribute:** `set.alters_data = True`.

**Method `create(self, *, through_defaults=None, **kwargs)`:** Get DB via `router.db_for_write(self.instance.__class__, instance=self.instance)`. Create new object: `super(ManyRelatedManager, self.db_manager(db)).create(**kwargs)`. Add it: `self.add(new_obj, through_defaults=through_defaults)`. Return the new object.

**Attribute:** `create.alters_data = True`.

**Method `get_or_create(self, *, through_defaults=None, **kwargs)`:** Get DB, call parent's `get_or_create(**kwargs)`. If created (not retrieved), add via `self.add(obj, through_defaults=through_defaults)`. Return `(obj, created)`.

**Attribute:** `get_or_create.alters_data = True`.

**Method `update_or_create(self, *, through_defaults=None, **kwargs)`:** Same pattern as `get_or_create` but calls parent's `update_or_create`.

**Attribute:** `update_or_create.alters_data = True`.

**Method `_get_target_ids(self, target_field_name, objs)`:**
1. Import `Model` from `django.db.models`. Initialize empty set `target_ids`. Get field object: `self.through._meta.get_field(target_field_name)`.
2. For each obj: if instance of `self.model`, check router allows relation (raise `ValueError` if not), get FK value via `target_field.get_foreign_related_value(obj)[0]`; if None, raise `ValueError`; add to set. If instance of `Model` but wrong type, raise `TypeError`. Else (not a model instance), call `target_field.get_prep_value(obj)` and add the prepared value.
3. Return `target_ids`.

**Method `_get_missing_target_ids(self, source_field_name, target_field_name, db, target_ids)`:** Query through table: `self.through._default_manager.using(db).values_list(target_field_name, flat=True).filter(**{source_field_name: self.related_val[0], f"{target_field_name}__in": target_ids})`. Return `target_ids.difference(vals)` — IDs not yet in the relationship.

**Method `_get_add_plan(self, db, source_field_name)`:** Returns a 3-tuple `(can_ignore_conflicts, must_send_signals, can_fast_add)`:
1. `can_ignore_conflicts = self.through._meta.auto_created is not False and connections[db].features.supports_ignore_conflicts`.
2. `must_send_signals = (self.reverse or source_field_name == self.source_field_name) and signals.m2m_changed.has_listeners(self.through)`.
3. `can_fast_add = can_ignore_conflicts and not must_send_signals`.

**Method `_add_items(self, source_field_name, target_field_name, *objs, through_defaults=None)`:**
1. If no objs, return early. Resolve callables: `through_defaults = dict(resolve_callables(through_defaults or {}))`. Get target IDs via `_get_target_ids(target_field_name, objs)`. Get DB. Call `_get_add_plan(db, source_field_name)` to get `(can_ignore_conflicts, must_send_signals, can_fast_add)`.
2. If `can_fast_add`: bulk-create through records with `ignore_conflicts=True` for all target IDs (no missing-ID check needed). Return early.
3. Else: compute `missing_target_ids = self._get_missing_target_ids(...)`. Within `transaction.atomic(using=db, savepoint=False)`: if `must_send_signals`, send `"pre_add"` signal with pk_set=missing_target_ids; bulk-create through records for missing IDs with `ignore_conflicts=can_ignore_conflicts`; if `must_send_signals`, send `"post_add"` signal.

**Method `_remove_items(self, source_field_name, target_field_name, *objs)`:**
1. If no objs, return early. Build `old_ids` set: for each obj, if instance of model get FK value via `target_field.get_foreign_related_value(obj)[0]`; else use the raw value directly.
2. Get DB. Within `transaction.atomic(using=db, savepoint=False)`: send `"pre_remove"` signal with pk_set=old_ids. Get target queryset: `super().get_queryset()`. If it has filters, filter by target field in old_ids; else use old_ids directly. Build remove filters via `_build_remove_filters(old_vals)`. Delete matching through records. Send `"post_remove"` signal with pk_set=old_ids.

**Return value:** Returns the dynamically created `ManyRelatedManager` class.