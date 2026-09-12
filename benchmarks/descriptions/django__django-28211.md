## django/db/models/query_utils.py
**1. Module-Level Preamble**

*   **Imports:**
    *   `import functools`
    *   `import inspect`
    *   `from collections import namedtuple`
    *   `from django.db.models.constants import LOOKUP_SEP`
    *   `from django.utils import tree`
*   **Constants & Globals:**
    *   `PathInfo`: `namedtuple('PathInfo', 'from_opts to_opts target_fields join_field m2m direct')`

**2. Code Objects (Classes and Functions)**

*   **`InvalidQuery`**
    *   **Header:** `class InvalidQuery(Exception):`
    *   **Implementation Logic:** An empty exception class inheriting from `Exception`.

*   **`subclasses`**
    *   **Header:** `def subclasses(cls):`
    *   **Implementation Logic:** A generator function that yields `cls`, then iterates over `cls.__subclasses__()` and recursively yields from `subclasses(subclass)`.

*   **`QueryWrapper`**
    *   **Header:** `class QueryWrapper:`
    *   **Attributes:**
        *   `contains_aggregate`: Class attribute, initialized to `False`.
    *   **`__init__(self, sql, params)`**
        *   **Implementation Logic:** Initializes `self.data` as a tuple containing `sql` and `list(params)`.
    *   **`as_sql(self, compiler=None, connection=None)`**
        *   **Implementation Logic:** Returns `self.data`.

*   **`Q`**
    *   **Header:** `class Q(tree.Node):`
    *   **Attributes:**
        *   `AND`: Class attribute, initialized to `'AND'`.
        *   `OR`: Class attribute, initialized to `'OR'`.
        *   `default`: Class attribute, initialized to `AND`.
    *   **`__init__(self, *args, **kwargs)`**
        *   **Implementation Logic:** Pops `_connector` (default `None`) and `_negated` (default `False`) from `kwargs`. Calls `super().__init__(children=list(args) + list(kwargs.items()), connector=connector, negated=negated)`.
    *   **`_combine(self, other, conn)`**
        *   **Implementation Logic:** If `other` is not an instance of `Q`, raises `TypeError(other)`. Creates a new instance of `type(self)()`. Sets its `connector` to `conn`. Calls `add(self, conn)` and `add(other, conn)` on the new instance. Returns the new instance.
    *   **`__or__(self, other)`**
        *   **Implementation Logic:** Returns `self._combine(other, self.OR)`.
    *   **`__and__(self, other)`**
        *   **Implementation Logic:** Returns `self._combine(other, self.AND)`.
    *   **`__invert__(self)`**
        *   **Implementation Logic:** Creates a new instance of `type(self)()`. Calls `add(self, self.AND)` on it. Calls `negate()` on it. Returns the new instance.
    *   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`**
        *   **Implementation Logic:** Calls `query._add_q(self, reuse, allow_joins=allow_joins, split_subq=False)` which returns `clause, joins`. Calls `query.promote_joins(joins)`. Returns `clause`.
    *   **`deconstruct(self)`**
        *   **Implementation Logic:** Sets `path` to `'%s.%s' % (self.__class__.__module__, self.__class__.__name__)`. Initializes `args = ()`, `kwargs = {}`. If `len(self.children) == 1` and `self.children[0]` is not an instance of `Q`, sets `child = self.children[0]` and `kwargs = {child[0]: child[1]}`. Otherwise, sets `args = tuple(self.children)` and `kwargs = {'_connector': self.connector}`. If `self.negated` is true, sets `kwargs['_negated'] = True`. Returns `path, args, kwargs`.

*   **`DeferredAttribute`**
    *   **Header:** `class DeferredAttribute:`
    *   **`__init__(self, field_name, model)`**
        *   **Implementation Logic:** Sets `self.field_name = field_name`.
    *   **`__get__(self, instance, cls=None)`**
        *   **Implementation Logic:** If `instance` is `None`, returns `self`. Gets `data = instance.__dict__`. If `data.get(self.field_name, self) is self`, calls `self._check_parent_chain(instance, self.field_name)`. If the result is `None`, calls `instance.refresh_from_db(fields=[self.field_name])` and gets the value using `getattr(instance, self.field_name)`. Sets `data[self.field_name]` to the value. Returns `data[self.field_name]`.
    *   **`_check_parent_chain(self, instance, name)`**
        *   **Implementation Logic:** Gets `opts = instance._meta`. Gets `f = opts.get_field(name)`. Gets `link_field = opts.get_ancestor_link(f.model)`. If `f.primary_key` is true and `f != link_field`, returns `getattr(instance, link_field.attname)`. Otherwise, returns `None`.

*   **`RegisterLookupMixin`**
    *   **Header:** `class RegisterLookupMixin:`
    *   **`_get_lookup(cls, lookup_name)`** (classmethod)
        *   **Implementation Logic:** Returns `cls.get_lookups().get(lookup_name, None)`.
    *   **`get_lookups(cls)`** (classmethod, decorated with `@functools.lru_cache(maxsize=None)`)
        *   **Implementation Logic:** Creates a list of `parent.__dict__.get('class_lookups', {})` for each `parent` in `inspect.getmro(cls)`. Returns `cls.merge_dicts(class_lookups)`.
    *   **`get_lookup(self, lookup_name)`**
        *   **Implementation Logic:** Imports `Lookup` from `django.db.models.lookups`. Calls `self._get_lookup(lookup_name)`. If `None` and `hasattr(self, 'output_field')`, returns `self.output_field.get_lookup(lookup_name)`. If the found lookup is not `None` and not `issubclass(found, Lookup)`, returns `None`. Returns the found lookup.
    *   **`get_transform(self, lookup_name)`**
        *   **Implementation Logic:** Imports `Transform` from `django.db.models.lookups`. Calls `self._get_lookup(lookup_name)`. If `None` and `hasattr(self, 'output_field')`, returns `self.output_field.get_transform(lookup_name)`. If the found transform is not `None` and not `issubclass(found, Transform)`, returns `None`. Returns the found transform.
    *   **`merge_dicts(dicts)`** (staticmethod)
        *   **Implementation Logic:** Creates an empty dict `merged`. Iterates over `reversed(dicts)` and updates `merged` with each dict. Returns `merged`.
    *   **`_clear_cached_lookups(cls)`** (classmethod)
        *   **Implementation Logic:** Iterates over `subclasses(cls)` and calls `subclass.get_lookups.cache_clear()`.
    *   **`register_lookup(cls, lookup, lookup_name=None)`** (classmethod)
        *   **Implementation Logic:** If `lookup_name` is `None`, sets it to `lookup.lookup_name`. If `'class_lookups'` is not in `cls.__dict__`, sets `cls.class_lookups = {}`. Sets `cls.class_lookups[lookup_name] = lookup`. Calls `cls._clear_cached_lookups()`. Returns `lookup`.
    *   **`_unregister_lookup(cls, lookup, lookup_name=None)`** (classmethod)
        *   **Implementation Logic:** If `lookup_name` is `None`, sets it to `lookup.lookup_name`. Deletes `cls.class_lookups[lookup_name]`.

*   **`select_related_descend`**
    *   **Header:** `def select_related_descend(field, restricted, requested, load_fields, reverse=False):`
    *   **Implementation Logic:**
        *   If `not field.remote_field`, return `False`.
        *   If `field.remote_field.parent_link` and `not reverse`, return `False`.
        *   If `restricted`:
            *   If `reverse` and `field.related_query_name() not in requested`, return `False`.
            *   If `not reverse` and `field.name not in requested`, return `False`.
        *   If `not restricted` and `field.null`, return `False`.
        *   If `load_fields`:
            *   If `field.attname not in load_fields`:
                *   If `restricted` and `field.name in requested`, raise `InvalidQuery` with a message formatted as `"Field %s.%s cannot be both deferred and traversed using select_related at the same time." % (field.model._meta.object_name, field.name)`.
        *   Return `True`.

*   **`refs_expression`**
    *   **Header:** `def refs_expression(lookup_parts, annotations):`
    *   **Implementation Logic:** Iterates `n` from `0` to `len(lookup_parts) + 1`. Sets `level_n_lookup = LOOKUP_SEP.join(lookup_parts[0:n])`. If `level_n_lookup` is in `annotations` and `annotations[level_n_lookup]` is truthy, returns `annotations[level_n_lookup], lookup_parts[n:]`. If the loop completes without returning, returns `False, ()`.

*   **`check_rel_lookup_compatibility`**
    *   **Header:** `def check_rel_lookup_compatibility(model, target_opts, field):`
    *   **Implementation Logic:** Defines a nested function `check(opts)` which returns `True` if `model._meta.concrete_model == opts.concrete_model` or `opts.concrete_model in model._meta.get_parent_list()` or `model in opts.get_parent_list()`. Returns `check(target_opts) or (getattr(field, 'primary_key', False) and check(field.model._meta))`.