## django/db/models/query_utils.py
```markdown
# Specification for `django/db/models/query_utils.py`

## 1. Module-Level Preamble

### Imports
```python
from __future__ import unicode_literals
import inspect
from collections import namedtuple
from django.core.exceptions import FieldDoesNotExist
from django.db.backends import utils
from django.db.models.constants import LOOKUP_SEP
from django.utils import tree
```

### Constants & Globals
*   `PathInfo`: A `namedtuple` defined as `namedtuple('PathInfo', 'from_opts to_opts target_fields join_field m2m direct')`.

---

## 2. Code Objects (Classes and Functions)

### `InvalidQuery(Exception)`
An empty subclass of `Exception`.

### `QueryWrapper(object)`
*   **Attributes:**
    *   `contains_aggregate = False` (Class attribute)
*   **`__init__(self, sql, params)`**
    *   Initializes `self.data` as a tuple containing `sql` and `list(params)`.
*   **`as_sql(self, compiler=None, connection=None)`**
    *   Returns `self.data`.

### `Q(tree.Node)`
*   **Attributes:**
    *   `AND = 'AND'` (Class attribute)
    *   `OR = 'OR'` (Class attribute)
    *   `default = AND` (Class attribute)
*   **`__init__(self, *args, **kwargs)`**
    *   Calls the superclass `__init__` with `children=list(args) + list(kwargs.items())`.
*   **`_combine(self, other, conn)`**
    *   If `other` is not an instance of `Q`, raises `TypeError(other)`.
    *   Creates a new instance of `type(self)()`.
    *   Sets the new instance's `connector` to `conn`.
    *   Calls `add(self, conn)` and `add(other, conn)` on the new instance.
    *   Returns the new instance.
*   **`__or__(self, other)`**
    *   Returns `self._combine(other, self.OR)`.
*   **`__and__(self, other)`**
    *   Returns `self._combine(other, self.AND)`.
*   **`__invert__(self)`**
    *   Creates a new instance of `type(self)()`.
    *   Calls `add(self, self.AND)` and `negate()` on the new instance.
    *   Returns the new instance.
*   **`clone(self)`**
    *   Creates a clone using `self.__class__._new_instance(children=[], connector=self.connector, negated=self.negated)`.
    *   Iterates over `self.children`. If a child has a `clone` attribute, appends `child.clone()` to `clone.children`; otherwise, appends `child` directly.
    *   Returns the clone.
*   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`**
    *   Calls `query._add_q(self, reuse, allow_joins=allow_joins, split_subq=False)` and unpacks the result into `clause, joins`.
    *   Calls `query.promote_joins(joins)`.
    *   Returns `clause`.
*   **`_refs_aggregate(cls, obj, existing_aggregates)`** (Class method)
    *   If `obj` is not an instance of `tree.Node`:
        *   Calls `refs_aggregate(obj[0].split(LOOKUP_SEP), existing_aggregates)` and unpacks into `aggregate, aggregate_lookups`.
        *   If `not aggregate` and `obj[1]` has a `refs_aggregate` attribute, returns `obj[1].refs_aggregate(existing_aggregates)`.
        *   Otherwise, returns `aggregate, aggregate_lookups`.
    *   If `obj` is a `tree.Node`, iterates over `c` in `obj.children`:
        *   Calls `cls._refs_aggregate(c, existing_aggregates)` and unpacks into `aggregate, aggregate_lookups`.
        *   If `aggregate` is truthy, returns `aggregate, aggregate_lookups`.
    *   If the loop completes without returning, returns `False, ()`.
*   **`refs_aggregate(self, existing_aggregates)`**
    *   If `not existing_aggregates`, returns `False`.
    *   Returns `self._refs_aggregate(self, existing_aggregates)`.

### `DeferredAttribute(object)`
*   **`__init__(self, field_name, model)`**
    *   Sets `self.field_name = field_name`.
*   **`__get__(self, instance, cls=None)`**
    *   Gets `non_deferred_model = instance._meta.proxy_for_model` and `opts = non_deferred_model._meta`.
    *   Asserts that `instance is not None`.
    *   Gets `data = instance.__dict__`.
    *   If `data.get(self.field_name, self) is self`:
        *   Tries to get `f = opts.get_field(self.field_name)`. If `FieldDoesNotExist` is raised, sets `f = [f for f in opts.fields if f.attname == self.field_name][0]`.
        *   Sets `name = f.name`.
        *   Calls `val = self._check_parent_chain(instance, name)`.
        *   If `val is None`, calls `instance.refresh_from_db(fields=[self.field_name])` and sets `val = getattr(instance, self.field_name)`.
        *   Sets `data[self.field_name] = val`.
    *   Returns `data[self.field_name]`.
*   **`__set__(self, instance, value)`**
    *   Sets `instance.__dict__[self.field_name] = value`.
*   **`_check_parent_chain(self, instance, name)`**
    *   Gets `opts = instance._meta`, `f = opts.get_field(name)`, and `link_field = opts.get_ancestor_link(f.model)`.
    *   If `f.primary_key` is truthy and `f != link_field`, returns `getattr(instance, link_field.attname)`.
    *   Returns `None`.

### `RegisterLookupMixin(object)`
*   **`_get_lookup(self, lookup_name)`**
    *   Tries to return `self.class_lookups[lookup_name]`.
    *   On `KeyError`, iterates over `parent` in `inspect.getmro(self.__class__)`. If `'class_lookups'` is in `parent.__dict__` and `lookup_name` is in `parent.class_lookups`, returns `parent.class_lookups[lookup_name]`.
    *   On `AttributeError`, passes.
    *   Returns `None` if no lookup is found.
*   **`get_lookup(self, lookup_name)`**
    *   Imports `Lookup` from `django.db.models.lookups`.
    *   Calls `found = self._get_lookup(lookup_name)`.
    *   If `found is None` and `hasattr(self, 'output_field')`, returns `self.output_field.get_lookup(lookup_name)`.
    *   If `found is not None` and `not issubclass(found, Lookup)`, returns `None`.
    *   Returns `found`.
*   **`get_transform(self, lookup_name)`**
    *   Imports `Transform` from `django.db.models.lookups`.
    *   Calls `found = self._get_lookup(lookup_name)`.
    *   If `found is None` and `hasattr(self, 'output_field')`, returns `self.output_field.get_transform(lookup_name)`.
    *   If `found is not None` and `not issubclass(found, Transform)`, returns `None`.
    *   Returns `found`.
*   **`register_lookup(cls, lookup, lookup_name=None)`** (Class method)
    *   If `lookup_name is None`, sets `lookup_name = lookup.lookup_name`.
    *   If `'class_lookups'` is not in `cls.__dict__`, sets `cls.class_lookups = {}`.
    *   Sets `cls.class_lookups[lookup_name] = lookup`.
    *   Returns `lookup`.
*   **`_unregister_lookup(cls, lookup, lookup_name=None)`** (Class method)
    *   If `lookup_name is None`, sets `lookup_name = lookup.lookup_name`.
    *   Deletes `cls.class_lookups[lookup_name]`.

### `select_related_descend(field, restricted, requested, load_fields, reverse=False)`
*   If `not field.remote_field`, returns `False`.
*   If `field.remote_field.parent_link` and `not reverse`, returns `False`.
*   If `restricted`:
    *   If `reverse` and `field.related_query_name() not in requested`, returns `False`.
    *   If `not reverse` and `field.name not in requested`, returns `False`.
*   If `not restricted` and `field.null`, returns `False`.
*   If `load_fields`:
    *   If `field.attname not in load_fields`:
        *   If `restricted` and `field.name in requested`, raises `InvalidQuery` with the message `"Field %s.%s cannot be both deferred and traversed using select_related at the same time." % (field.model._meta.object_name, field.name)`.
        *   Returns `False`.
*   Returns `True`.

### `deferred_class_factory(model, attrs)`
*   If `not attrs`, returns `model`.
*   Sets `opts = model._meta`.
*   If `model._deferred`, sets `model = opts.proxy_for_model`.
*   Generates `name = "%s_Deferred_%s" % (model.__name__, '_'.join(sorted(attrs)))`.
*   Truncates the name using `name = utils.truncate_name(name, 80, 32)`.
*   Tries to return `opts.apps.get_model(model._meta.app_label, name)`.
*   On `LookupError`:
    *   Defines an inner class `Meta` with `proxy = True`, `apps = opts.apps`, and `app_label = opts.app_label`.
    *   Creates a dictionary `overrides = {attr: DeferredAttribute(attr, model) for attr in attrs}`.
    *   Adds to `overrides`: `"Meta": Meta`, `"__module__": model.__module__`, and `"_deferred": True`.
    *   Returns a new type created via `type(str(name), (model,), overrides)`.

### `refs_aggregate(lookup_parts, aggregates)`
*   Iterates `n` over `range(len(lookup_parts) + 1)`:
    *   Sets `level_n_lookup = LOOKUP_SEP.join(lookup_parts[0:n])`.
    *   If `level_n_lookup in aggregates` and `aggregates[level_n_lookup].contains_aggregate`, returns `aggregates[level_n_lookup], lookup_parts[n:]`.
*   Returns `False, ()`.

### `refs_expression(lookup_parts, annotations)`
*   Iterates `n` over `range(len(lookup_parts) + 1)`:
    *   Sets `level_n_lookup = LOOKUP_SEP.join(lookup_parts[0:n])`.
    *   If `level_n_lookup in annotations` and `annotations[level_n_lookup]`, returns `annotations[level_n_lookup], lookup_parts[n:]`.
*   Returns `False, ()`.

### `check_rel_lookup_compatibility(model, target_opts, field)`
*   Defines an inner function `check(opts)` that returns `True` if `model._meta.concrete_model == opts.concrete_model`, or `opts.concrete_model in model._meta.get_parent_list()`, or `model in opts.get_parent_list()`.
*   Returns `True` if `check(target_opts)` is truthy, OR if `getattr(field, 'primary_key', False)` is truthy AND `check(field.model._meta)` is truthy. Otherwise, returns `False`.
```