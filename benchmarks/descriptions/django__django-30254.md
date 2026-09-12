## django/db/models/base.py
This is a natural-language specification for `django/db/models/base.py`.

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
from django.db.models.constants import LOOKUP_SEP
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.db.models.deletion import CASCADE, Collector
from django.db.models.fields.related import (
    ForeignObjectRel, OneToOneField, lazy_related_operation, resolve_relation,
)
from django.db.models.manager import Manager
from django.db.models.options import Options
from django.db.models.query import Q
from django.db.models.signals import (
    class_prepared, post_init, post_save, pre_init, pre_save,
)
from django.db.models.utils import make_model_tuple
from django.utils.text import capfirst, get_text_list
from django.utils.translation import gettext_lazy as _
from django.utils.version import get_version
```

## Constants & Globals
*   `DEFERRED`: An instance of the `Deferred` class.

# Code Objects

## Class: `Deferred`
A marker class for deferred fields.
*   **`__repr__(self)`**: Returns `'<Deferred field>'`.
*   **`__str__(self)`**: Returns `'<Deferred field>'`.

## Function: `subclass_exception`
*   **Signature**: `def subclass_exception(name, bases, module, attached_to)`
*   **Logic**: Creates and returns a new exception class using `type(name, bases, dict)`. The dictionary contains `__module__` set to `module` and `__qualname__` set to `f"{attached_to.__qualname__}.{name}"`.

## Function: `_has_contribute_to_class`
*   **Signature**: `def _has_contribute_to_class(value)`
*   **Logic**: Returns `True` if `value` is not a class (`inspect.isclass(value)` is false) and has a `contribute_to_class` attribute. Otherwise, returns `False`.

## Class: `ModelBase`
*   **Inheritance**: `type`
*   **Logic**: The metaclass for all Django models.
    *   **`__new__(cls, name, bases, attrs, **kwargs)`**:
        *   Checks if the class being created has `ModelBase` in its parents. If not (meaning it's the `Model` class itself), it just calls `super().__new__`.
        *   Extracts `__module__`, `__classcell__`, and `Meta` from `attrs`.
        *   Moves attributes without a `contribute_to_class` method to a new dictionary `new_attrs` and creates the class using `super().__new__`.
        *   Sets up the `_meta` attribute (an instance of `Options`) on the new class.
        *   Resolves the `app_label`.
        *   Adds `DoesNotExist` and `MultipleObjectsReturned` exceptions to the class.
        *   Iterates over the remaining attributes in `attrs` and calls their `contribute_to_class` method, passing the new class and the attribute name.
        *   Sets up managers, relationships, and signals.

## Class: `ModelStateFieldsCacheDescriptor`
*   **Logic**: A descriptor used to manage the `fields_cache` on `ModelState`.
    *   **`__get__(self, instance, cls=None)`**: Returns a new empty dictionary if accessed on an instance, otherwise returns the descriptor itself.

## Class: `ModelState`
*   **Logic**: Stores the state of a model instance.
    *   **Attributes**:
        *   `db`: The database alias (default `None`).
        *   `adding`: A boolean indicating if the instance is new (default `True`).
        *   `fields_cache`: Managed by `ModelStateFieldsCacheDescriptor`.
    *   **`__init__(self, db=None)`**: Initializes `db` and `adding`.

## Class: `Model`
*   **Metaclass**: `ModelBase`
*   **Logic**: The base class for all Django models.
    *   **`__init__(self, *args, **kwargs)`**: Initializes the model instance. Sets up `_state` (a `ModelState` instance). Populates fields from `args` and `kwargs`. Sends the `pre_init` and `post_init` signals.
    *   **`save(self, force_insert=False, force_update=False, using=None, update_fields=None)`**: Saves the current instance. Calls `save_base`.
    *   **`save_base(self, raw=False, force_insert=False, force_update=False, using=None, update_fields=None)`**: Handles the actual saving logic, including sending `pre_save` and `post_save` signals, and calling the database backend to insert or update the record.
    *   **`delete(self, using=None, keep_parents=False)`**: Deletes the instance from the database. Uses a `Collector` to handle cascading deletes.
    *   **`clean(self)`**: Hook for providing custom model validation.
    *   **`clean_fields(self, exclude=None)`**: Validates all fields on the model.
    *   **`validate_unique(self, exclude=None)`**: Validates unique constraints.
    *   **`full_clean(self, exclude=None, validate_unique=True)`**: Calls `clean_fields`, `clean`, and `validate_unique`.
    *   **`refresh_from_db(self, using=None, fields=None)`**: Reloads field values from the database.

## Function: `method_set_order`
*   **Signature**: `def method_set_order(self, ordered_obj, id_list, using=None)`
*   **Logic**: Updates the `_order` field of related objects to match the order in `id_list`.

## Function: `method_get_order`
*   **Signature**: `def method_get_order(self, ordered_obj)`
*   **Logic**: Returns the primary keys of related objects ordered by their `_order` field.

## Function: `make_foreign_order_accessors`
*   **Signature**: `def make_foreign_order_accessors(model, related_model)`
*   **Logic**: Dynamically adds `get_RELATED_order` and `set_RELATED_order` methods to a model class for managing ordered relations.

## Function: `model_unpickle`
*   **Signature**: `def model_unpickle(model_id)`
*   **Logic**: Helper function used during unpickling of model instances, especially those with deferred fields. It retrieves the model class from the app registry and creates a new instance without calling `__init__`.
*   **Attributes**: `model_unpickle.__safe_for_unpickle__ = True`.