## django/db/models/fields/related.py
1.  **Module-Level Preamble:**
    *   **Imports:**
        *   `import functools`
        *   `import inspect`
        *   `from functools import partial`
        *   `from django import forms`
        *   `from django.apps import apps`
        *   `from django.conf import SettingsReference`
        *   `from django.core import checks, exceptions`
        *   `from django.db import connection, router`
        *   `from django.db.backends import utils`
        *   `from django.db.models import Q`
        *   `from django.db.models.constants import LOOKUP_SEP`
        *   `from django.db.models.deletion import CASCADE, SET_DEFAULT, SET_NULL`
        *   `from django.db.models.query_utils import PathInfo`
        *   `from django.db.models.utils import make_model_tuple`
        *   `from django.utils.functional import cached_property`
        *   `from django.utils.translation import gettext_lazy as _`
        *   `from . import Field`
        *   `from .mixins import FieldCacheMixin`
        *   `from .related_descriptors import ForwardManyToOneDescriptor, ForwardOneToOneDescriptor, ManyToManyDescriptor, ReverseManyToOneDescriptor, ReverseOneToOneDescriptor`
        *   `from .related_lookups import RelatedExact, RelatedGreaterThan, RelatedGreaterThanOrEqual, RelatedIn, RelatedIsNull, RelatedLessThan, RelatedLessThanOrEqual`
        *   `from .reverse_related import ForeignObjectRel, ManyToManyRel, ManyToOneRel, OneToOneRel`
    *   **Constants & Globals:**
        *   `RECURSIVE_RELATIONSHIP_CONSTANT = 'self'`

2.  **Code Objects (Classes and Functions):**

    *   **Function:** `resolve_relation(scope_model, relation)`
        *   **Logic:** Resolves a relation string (like `'app_label.ModelName'` or `RECURSIVE_RELATIONSHIP_CONSTANT`) into a model class or a string representation of the model. If `relation` is a string, it handles the `'self'` constant by returning the `scope_model`. If it's a string containing a dot, it returns it as is. If it's a string without a dot, it prepends the `scope_model`'s app label. Otherwise, it returns the `relation` unchanged.

    *   **Function:** `lazy_related_operation(function, model, *related_models, **kwargs)`
        *   **Logic:** Schedules a function to be executed when all the specified models (including `model` and `related_models`) are loaded by the app registry. It uses `apps.lazy_model_operation` to achieve this.

    *   **Class:** `RelatedField(FieldCacheMixin, Field)`
        *   **Attributes:**
            *   `one_to_many = False`
            *   `one_to_one = False`
            *   `many_to_many = False`
            *   `many_to_one = False`
        *   **Logic:** Base class for all relational fields. It provides common functionality for checking related names, query names, and resolving related models. It overrides `db_type` to return `None` (as relational fields themselves don't have a direct database column type in the same way as standard fields, except for `ForeignKey`). It handles the `contribute_to_class` logic to set up the relation and register lazy operations if the related model is not yet loaded.

    *   **Class:** `ForeignObject(RelatedField)`
        *   **Attributes:**
            *   `many_to_many = False`
            *   `many_to_one = True`
            *   `one_to_many = False`
            *   `one_to_one = False`
            *   `requires_unique_target = True`
            *   `related_accessor_class = ReverseManyToOneDescriptor`
            *   `forward_related_accessor_class = ForwardManyToOneDescriptor`
            *   `rel_class = ForeignObjectRel`
        *   **Logic:** Represents a generic foreign key relationship. It takes `from_fields` and `to_fields` to define the joining columns. It implements `get_path_info` and `get_reverse_path_info` to provide routing information for the ORM. It registers various lookups (like `RelatedIn`, `RelatedExact`, etc.) for querying.

    *   **Class:** `ForeignKey(ForeignObject)`
        *   **Attributes:**
            *   `many_to_many = False`
            *   `many_to_one = True`
            *   `one_to_many = False`
            *   `one_to_one = False`
            *   `rel_class = ManyToOneRel`
            *   `empty_strings_allowed = False`
            *   `default_error_messages = {'invalid': _('%(model)s instance with %(field)s %(value)r does not exist.')}`
            *   `description = _('Foreign Key (type determined by related field)')`
        *   **Logic:** A standard foreign key field. It inherits from `ForeignObject` but simplifies the initialization by assuming a single column join (usually to the primary key of the related model). It handles `on_delete` behavior, validation, and database column creation (`db_type`, `db_parameters`).

    *   **Class:** `OneToOneField(ForeignKey)`
        *   **Attributes:**
            *   `many_to_many = False`
            *   `many_to_one = False`
            *   `one_to_many = False`
            *   `one_to_one = True`
            *   `related_accessor_class = ReverseOneToOneDescriptor`
            *   `forward_related_accessor_class = ForwardOneToOneDescriptor`
            *   `rel_class = OneToOneRel`
            *   `description = _('One-to-one relationship')`
        *   **Logic:** A one-to-one relationship field. It's essentially a `ForeignKey` with `unique=True`. It overrides the accessor classes to provide single-object access on both sides of the relation.

    *   **Function:** `create_many_to_many_intermediary_model(field, klass)`
        *   **Logic:** Dynamically creates an intermediary model class for a `ManyToManyField` when a custom `through` model is not provided. It defines the foreign keys to the source and target models and sets up the `Meta` options (like `db_table`, `unique_together`, `auto_created`).

    *   **Class:** `ManyToManyField(RelatedField)`
        *   **Attributes:**
            *   `many_to_many = True`
            *   `many_to_one = False`
            *   `one_to_many = False`
            *   `one_to_one = False`
            *   `rel_class = ManyToManyRel`
            *   `description = _('Many-to-many relationship')`
        *   **Logic:** Represents a many-to-many relationship. It handles the creation or resolution of the intermediary (`through`) model. It provides `get_path_info` and `get_reverse_path_info` that traverse through the intermediary model. It uses `ManyToManyDescriptor` to manage the related manager on the model instances. It overrides `db_type` to return `None` as the field itself doesn't create a column in the source model's table.

## django/db/models/fields/related_descriptors.py
An expert natural-language specification of `django/db/models/fields/related_descriptors.py`.

### 1. Module-Level Preamble

**Imports:**
*   `from django.core.exceptions import FieldError`
*   `from django.db import connections, router, transaction`
*   `from django.db.models import Q, signals`
*   `from django.db.models.query import QuerySet`
*   `from django.utils.functional import cached_property`

### 2. Code Objects

#### `ForwardManyToOneDescriptor`
*   **Header:** `class ForwardManyToOneDescriptor:`
*   **Attributes:**
    *   `field`: Initialized in `__init__` with `field_with_rel`.
*   **Implementation Logic:**
    *   `__init__(self, field_with_rel)`: Sets `self.field = field_with_rel`.
    *   `RelatedObjectDoesNotExist(self)`: A `@cached_property` that returns an exception class dynamically created using `type()`, inheriting from `self.field.remote_field.model.DoesNotExist` and `AttributeError`.
    *   `is_cached(self, instance)`: Returns `self.field.is_cached(instance)`.
    *   `get_queryset(self, **hints)`: Returns `self.field.remote_field.model._base_manager.db_manager(hints=hints).all()`.
    *   `get_prefetch_queryset(self, instances, queryset=None)`: Prepares a queryset for prefetching related objects.
    *   `get_object(self, instance)`: Retrieves the related object using `self.get_queryset(instance=instance).get(self.field.get_reverse_related_filter(instance))`.
    *   `__get__(self, instance, cls=None)`: Returns the descriptor itself if `instance` is `None`. Otherwise, returns the cached related object if it exists. If not, fetches it using `get_object()`, caches it, and returns it. Raises `self.RelatedObjectDoesNotExist` if the object is not found.
    *   `__set__(self, instance, value)`: Sets the related object on the instance. Updates the underlying foreign key value and caches the related object. Also updates the reverse relation cache on the related object if applicable.
    *   `__reduce__(self)`: Returns `(getattr, (self.field.model, self.field.name))` for pickling.

#### `ForwardOneToOneDescriptor`
*   **Header:** `class ForwardOneToOneDescriptor(ForwardManyToOneDescriptor):`
*   **Implementation Logic:**
    *   Inherits from `ForwardManyToOneDescriptor`.
    *   `get_object(self, instance)`: Overrides to handle one-to-one specific logic.
    *   `__set__(self, instance, value)`: Overrides to handle setting the one-to-one relation, ensuring the reverse relation is also updated correctly.

#### `ReverseOneToOneDescriptor`
*   **Header:** `class ReverseOneToOneDescriptor:`
*   **Attributes:**
    *   `related`: Initialized in `__init__` with `related`.
*   **Implementation Logic:**
    *   `__init__(self, related)`: Sets `self.related = related`.
    *   `RelatedObjectDoesNotExist(self)`: A `@cached_property` returning an exception class.
    *   `is_cached(self, instance)`: Checks if the reverse relation is cached.
    *   `get_queryset(self, **hints)`: Returns the queryset for the related model.
    *   `get_prefetch_queryset(self, instances, queryset=None)`: Prepares prefetch queryset.
    *   `get_object(self, instance)`: Fetches the related object.
    *   `__get__(self, instance, cls=None)`: Retrieves the related object, caching it.
    *   `__set__(self, instance, value)`: Sets the related object, updating caches on both sides.
    *   `__reduce__(self)`: Returns `(getattr, (self.related.model, self.related.name))`.

#### `ReverseManyToOneDescriptor`
*   **Header:** `class ReverseManyToOneDescriptor:`
*   **Attributes:**
    *   `rel`: Initialized in `__init__` with `rel`.
*   **Implementation Logic:**
    *   `__init__(self, rel)`: Sets `self.rel = rel`.
    *   `related_manager_cls(self)`: A `@cached_property` that returns the dynamically created manager class using `create_reverse_many_to_one_manager`.
    *   `__get__(self, instance, cls=None)`: Returns the descriptor if `instance` is `None`. Otherwise, returns an instance of `self.related_manager_cls` bound to the `instance`.
    *   `__set__(self, instance, value)`: Raises `TypeError` indicating that direct assignment is not allowed (must use `.set()`).

#### `create_reverse_many_to_one_manager`
*   **Header:** `def create_reverse_many_to_one_manager(superclass, rel):`
*   **Implementation Logic:**
    *   Dynamically creates and returns a `RelatedManager` class that inherits from `superclass`.
    *   The `RelatedManager` handles operations like `add()`, `create()`, `get_or_create()`, `update_or_create()`, `remove()`, `clear()`, and `set()` for the reverse many-to-one relation.

#### `ManyToManyDescriptor`
*   **Header:** `class ManyToManyDescriptor(ReverseManyToOneDescriptor):`
*   **Attributes:**
    *   `reverse`: Initialized in `__init__` with `reverse` (default `False`).
*   **Implementation Logic:**
    *   `__init__(self, rel, reverse=False)`: Calls `super().__init__(rel)` and sets `self.reverse = reverse`.
    *   `related_manager_cls(self)`: A `@cached_property` that returns the dynamically created manager class using `create_forward_many_to_many_manager`.

#### `create_forward_many_to_many_manager`
*   **Header:** `def create_forward_many_to_many_manager(superclass, rel, reverse):`
*   **Implementation Logic:**
    *   Dynamically creates and returns a `ManyRelatedManager` class that inherits from `superclass`.
    *   The `ManyRelatedManager` handles operations like `add()`, `create()`, `get_or_create()`, `update_or_create()`, `remove()`, `clear()`, and `set()` for many-to-many relations, managing the intermediate join table.