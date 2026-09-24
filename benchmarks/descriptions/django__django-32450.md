## django/db/models/query_utils.py
```markdown
1.  **Module-Level Preamble:**
    *   **Imports:**
        *   `import copy`
        *   `import functools`
        *   `import inspect`
        *   `from collections import namedtuple`
        *   `from django.core.exceptions import FieldError`
        *   `from django.db.models.constants import LOOKUP_SEP`
        *   `from django.utils import tree`
    *   **Constants & Globals:**
        *   `PathInfo`: A `namedtuple` created with the name `'PathInfo'` and fields `'from_opts to_opts target_fields join_field m2m direct filtered_relation'`.

2.  **Code Objects (Classes and Functions):**

    *   **Function `subclasses(cls)`:**
        *   **Signature:** `def subclasses(cls):`
        *   **Implementation Logic:** A generator function that first yields the provided `cls`. Then, it iterates over `cls.__subclasses__()` and recursively yields from `subclasses(subclass)`.

    *   **Class `Q(tree.Node)`:**
        *   **Base Classes:** `tree.Node`
        *   **Attributes:**
            *   `AND`: Class attribute, string `'AND'`.
            *   `OR`: Class attribute, string `'OR'`.
            *   `default`: Class attribute, set to `AND`.
            *   `conditional`: Class attribute, boolean `True`.
        *   **Method `__init__`:**
            *   **Signature:** `def __init__(self, *args, _connector=None, _negated=False, **kwargs):`
            *   **Implementation Logic:** Calls `super().__init__()` with `children` set to a list containing all `*args` followed by the sorted items of `**kwargs`. Passes `connector=_connector` and `negated=_negated`.
        *   **Method `_combine`:**
            *   **Signature:** `def _combine(self, other, conn):`
            *   **Implementation Logic:**
                *   Raises `TypeError(other)` if `other` is not an instance of `Q`.
                *   If `other` is empty (evaluates to false), returns a deep copy of `self`.
                *   If `self` is empty, returns a deep copy of `other`.
                *   Otherwise, creates a new instance of `type(self)`. Sets its `connector` to `conn`. Calls `add(self, conn)` and `add(other, conn)` on the new instance, then returns it.
        *   **Method `__or__`:**
            *   **Signature:** `def __or__(self, other):`
            *   **Implementation Logic:** Returns `self._combine(other, self.OR)`.
        *   **Method `__and__`:**
            *   **Signature:** `def __and__(self, other):`
            *   **Implementation Logic:** Returns `self._combine(other, self.AND)`.
        *   **Method `__invert__`:**
            *   **Signature:** `def __invert__(self):`
            *   **Implementation Logic:** Creates a new instance of `type(self)`. Calls `add(self, self.AND)` on it, then calls `negate()`, and returns the new instance.
        *   **Method `resolve_expression`:**
            *   **Signature:** `def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):`
            *   **Implementation Logic:** Calls `query._add_q(self, reuse, allow_joins=allow_joins, split_subq=False, check_filterable=False)` which returns `clause` and `joins`. Calls `query.promote_joins(joins)` and returns `clause`.
        *   **Method `deconstruct`:**
            *   **Signature:** `def deconstruct(self):`
            *   **Implementation Logic:**
                *   Constructs `path` as `'%s.%s' % (self.__class__.__module__, self.__class__.__name__)`.
                *   If `path` starts with `'django.db.models.query_utils'`, replaces it with `'django.db.models'`.
                *   Initializes `args = ()` and `kwargs = {}`.
                *   If `self.children` has exactly 1 element and it is not a `Q` instance, sets `child = self.children[0]` and `kwargs = {child[0]: child[1]}`.
                *   Else, sets `args = tuple(self.children)`. If `self.connector != self.default`, sets `kwargs = {'_connector': self.connector}`.
                *   If `self.negated` is true, adds `'_negated': True` to `kwargs`.
                *   Returns the tuple `(path, args, kwargs)`.

    *   **Class `DeferredAttribute`:**
        *   **Method `__init__`:**
            *   **Signature:** `def __init__(self, field):`
            *   **Implementation Logic:** Sets `self.field = field`.
        *   **Method `__get__`:**
            *   **Signature:** `def __get__(self, instance, cls=None):`
            *   **Implementation Logic:**
                *   If `instance` is `None`, returns `self`.
                *   Gets `data = instance.__dict__` and `field_name = self.field.attname`.
                *   If `field_name` is not in `data`:
                    *   Calls `self._check_parent_chain(instance)` and assigns to `val`.
                    *   If `val` is `None`, calls `instance.refresh_from_db(fields=[field_name])`.
                    *   Else, sets `data[field_name] = val`.
                *   Returns `data[field_name]`.
        *   **Method `_check_parent_chain`:**
            *   **Signature:** `def _check_parent_chain(self, instance):`
            *   **Implementation Logic:**
                *   Gets `opts = instance._meta`.
                *   Gets `link_field = opts.get_ancestor_link(self.field.model)`.
                *   If `self.field.primary_key` is true and `self.field != link_field`, returns `getattr(instance, link_field.attname)`.
                *   Returns `None`.

    *   **Class `RegisterLookupMixin`:**
        *   **Method `_get_lookup` (classmethod):**
            *   **Signature:** `def _get_lookup(cls, lookup_name):`
            *   **Implementation Logic:** Returns `cls.get_lookups().get(lookup_name, None)`.
        *   **Method `get_lookups` (classmethod):**
            *   **Signature:** `def get_lookups(cls):`
            *   **Decorators:** `@functools.lru_cache(maxsize=None)`
            *   **Implementation Logic:** Creates a list `class_lookups` by extracting the `'class_lookups'` dict (defaulting to `{}`) from `parent.__dict__` for each `parent` in `inspect.getmro(cls)`. Returns `cls.merge_dicts(class_lookups)`.
        *   **Method `get_lookup`:**
            *   **Signature:** `def get_lookup(self, lookup_name):`
            *   **Implementation Logic:**
                *   Imports `Lookup` from `django.db.models.lookups`.
                *   Calls `self._get_lookup(lookup_name)` and assigns to `found`.
                *   If `found` is `None` and `self` has attribute `'output_field'`, returns `self.output_field.get_lookup(lookup_name)`.
                *   If `found` is not `None` and not a subclass of `Lookup`, returns `None`.
                *   Returns `found`.
        *   **Method `get_transform`:**
            *   **Signature:** `def get_transform(self, lookup_name):`
            *   **Implementation Logic:**
                *   Imports `Transform` from `django.db.models.lookups`.
                *   Calls `self._get_lookup(lookup_name)` and assigns to `found`.
                *   If `found` is `None` and `self` has attribute `'output_field'`, returns `self.output_field.get_transform(lookup_name)`.
                *   If `found` is not `None` and not a subclass of `Transform`, returns `None`.
                *   Returns `found`.
        *   **Method `merge_dicts` (staticmethod):**
            *   **Signature:** `def merge_dicts(dicts):`
            *   **Implementation Logic:** Initializes an empty dict `merged`. Iterates over `reversed(dicts)` and updates `merged` with each dict. Returns `merged`.
        *   **Method `_clear_cached_lookups` (classmethod):**
            *   **Signature:** `def _clear_cached_lookups(cls):`
            *   **Implementation Logic:** Iterates over `subclasses(cls)` and calls `subclass.get_lookups.cache_clear()`.
        *   **Method `register_lookup` (classmethod):**
            *   **Signature:** `def register_lookup(cls, lookup, lookup_name=None):`
            *   **Implementation Logic:**
                *   If `lookup_name` is `None`, sets it to `lookup.lookup_name`.
                *   If `'class_lookups'` is not in `cls.__dict__`, sets `cls.class_lookups = {}`.
                *   Sets `cls.class_lookups[lookup_name] = lookup`.
                *   Calls `cls._clear_cached_lookups()`.
                *   Returns `lookup`.
        *   **Method `_unregister_lookup` (classmethod):**
            *   **Signature:** `def _unregister_lookup(cls, lookup, lookup_name=None):`
            *   **Implementation Logic:** If `lookup_name` is `None`, sets it to `lookup.lookup_name`. Deletes `cls.class_lookups[lookup_name]`.

    *   **Function `select_related_descend`:**
        *   **Signature:** `def select_related_descend(field, restricted, requested, load_fields, reverse=False):`
        *   **Implementation Logic:**
            *   If `not field.remote_field`, returns `False`.
            *   If `field.remote_field.parent_link` and `not reverse`, returns `False`.
            *   If `restricted`:
                *   If `reverse` and `field.related_query_name() not in requested`, returns `False`.
                *   If `not reverse` and `field.name not in requested`, returns `False`.
            *   If `not restricted` and `field.null`, returns `False`.
            *   If `load_fields`:
                *   If `field.attname not in load_fields`:
                    *   If `restricted` and `field.name in requested`, raises `FieldError` with a message indicating the field cannot be both deferred and traversed.
            *   Returns `True`.

    *   **Function `refs_expression`:**
        *   **Signature:** `def refs_expression(lookup_parts, annotations):`
        *   **Implementation Logic:** Iterates `n` from 1 to `len(lookup_parts)`. Joins `lookup_parts[0:n]` with `LOOKUP_SEP` to form `level_n_lookup`. If `level_n_lookup` is in `annotations` and `annotations[level_n_lookup]` is truthy, returns `(annotations[level_n_lookup], lookup_parts[n:])`. If the loop finishes without returning, returns `(False, ())`.

    *   **Function `check_rel_lookup_compatibility`:**
        *   **Signature:** `def check_rel_lookup_compatibility(model, target_opts, field):`
        *   **Implementation Logic:**
            *   Defines an inner function `check(opts)` that returns `True` if `model._meta.concrete_model == opts.concrete_model`, or `opts.concrete_model in model._meta.get_parent_list()`, or `model in opts.get_parent_list()`.
            *   Returns `True` if `check(target_opts)` is true, or if `getattr(field, 'primary_key', False)` is true and `check(field.model._meta)` is true. Otherwise returns `False`.

    *   **Class `FilteredRelation`:**
        *   **Method `__init__`:**
            *   **Signature:** `def __init__(self, relation_name, *, condition=Q()):`
            *   **Implementation Logic:**
                *   Raises `ValueError` if `relation_name` is empty.
                *   Sets `self.relation_name = relation_name` and `self.alias = None`.
                *   Raises `ValueError` if `condition` is not an instance of `Q`.
                *   Sets `self.condition = condition` and `self.path = []`.
        *   **Method `__eq__`:**
            *   **Signature:** `def __eq__(self, other):`
            *   **Implementation Logic:** Returns `NotImplemented` if `other` is not an instance of `self.__class__`. Otherwise, returns `True` if `relation_name`, `alias`, and `condition` all match between `self` and `other`.
        *   **Method `clone`:**
            *   **Signature:** `def clone(self):`
            *   **Implementation Logic:** Creates a new `FilteredRelation` with `self.relation_name` and `condition=self.condition`. Sets its `alias` to `self.alias` and `path` to a shallow copy of `self.path`. Returns the clone.
        *   **Method `resolve_expression`:**
            *   **Signature:** `def resolve_expression(self, *args, **kwargs):`
            *   **Implementation Logic:** Raises `NotImplementedError('FilteredRelation.resolve_expression() is unused.')`.
        *   **Method `as_sql`:**
            *   **Signature:** `def as_sql(self, compiler, connection):`
            *   **Implementation Logic:** Gets `query = compiler.query`. Calls `query.build_filtered_relation_q(self.condition, reuse=set(self.path))` and assigns to `where`. Returns `compiler.compile(where)`.
```