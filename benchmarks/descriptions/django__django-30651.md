## django/contrib/messages/storage/base.py
An expert natural-language specification of the `django/contrib/messages/storage/base.py` file.

### 1. Module-Level Preamble

**Imports:**
*   `from django.conf import settings`
*   `from django.contrib.messages import constants, utils`

**Constants & Globals:**
*   `LEVEL_TAGS`: Initialized by calling `utils.get_level_tags()`.

---

### 2. Code Objects (Classes and Functions)

#### Class: `Message`
Represents a single message with a level, text, and optional tags.

**Header:**
*   Name: `Message`
*   Base classes: None

**Methods:**

*   `__init__(self, level, message, extra_tags=None)`
    *   **Logic:**
        *   Sets `self.level` to the integer conversion of `level` (`int(level)`).
        *   Sets `self.message` to `message`.
        *   Sets `self.extra_tags` to `extra_tags`.

*   `_prepare(self)`
    *   **Logic:** Prepares the message for serialization by forcing lazy evaluation.
        *   Sets `self.message` to `str(self.message)`.
        *   Sets `self.extra_tags` to `str(self.extra_tags)` if `self.extra_tags` is not `None`, otherwise sets it to `None`.

*   `__eq__(self, other)`
    *   **Logic:** Returns `True` if `other` is an instance of `Message`, `self.level` equals `other.level`, and `self.message` equals `other.message`. Otherwise, returns `False`.

*   `__str__(self)`
    *   **Logic:** Returns `str(self.message)`.

*   `tags` (Property)
    *   **Logic:** Returns a space-separated string joining `self.extra_tags` and `self.level_tag`. It filters out any falsy values (e.g., `None` or empty strings) before joining.

*   `level_tag` (Property)
    *   **Logic:** Returns the string value from the `LEVEL_TAGS` dictionary corresponding to the key `self.level`. Returns an empty string `''` if the level is not found.

---

#### Class: `BaseStorage`
The base class for message storage backends.

**Header:**
*   Name: `BaseStorage`
*   Base classes: None

**Attributes:**
*   `request`: The request object passed during initialization.
*   `_queued_messages`: A list of messages added during the current request.
*   `used`: A boolean indicating if the messages have been iterated over.
*   `added_new`: A boolean indicating if new messages have been added.

**Methods:**

*   `__init__(self, request, *args, **kwargs)`
    *   **Logic:**
        *   Sets `self.request = request`.
        *   Sets `self._queued_messages = []`.
        *   Sets `self.used = False`.
        *   Sets `self.added_new = False`.
        *   Calls `super().__init__(*args, **kwargs)`.

*   `__len__(self)`
    *   **Logic:** Returns the sum of the lengths of `self._loaded_messages` and `self._queued_messages`.

*   `__iter__(self)`
    *   **Logic:**
        *   Sets `self.used = True`.
        *   If `self._queued_messages` is not empty, extends `self._loaded_messages` with `self._queued_messages` and then clears `self._queued_messages` (sets it to `[]`).
        *   Returns an iterator over `self._loaded_messages` (`iter(self._loaded_messages)`).

*   `__contains__(self, item)`
    *   **Logic:** Returns `True` if `item` is in `self._loaded_messages` or in `self._queued_messages`. Otherwise, returns `False`.

*   `_loaded_messages` (Property)
    *   **Logic:**
        *   Checks if the instance has the attribute `_loaded_data` (`hasattr(self, '_loaded_data')`).
        *   If it does not, calls `self._get()` which returns a tuple `(messages, all_retrieved)`. Sets `self._loaded_data` to `messages` if it is truthy, otherwise sets it to an empty list `[]`.
        *   Returns `self._loaded_data`.

*   `_get(self, *args, **kwargs)`
    *   **Logic:** Raises a `NotImplementedError` with the message `'subclasses of BaseStorage must provide a _get() method'`.

*   `_store(self, messages, response, *args, **kwargs)`
    *   **Logic:** Raises a `NotImplementedError` with the message `'subclasses of BaseStorage must provide a _store() method'`.

*   `_prepare_messages(self, messages)`
    *   **Logic:** Iterates over the provided `messages` list and calls `message._prepare()` on each message.

*   `update(self, response)`
    *   **Logic:** Stores unread messages.
        *   Calls `self._prepare_messages(self._queued_messages)`.
        *   If `self.used` is `True`, returns the result of `self._store(self._queued_messages, response)`.
        *   Else if `self.added_new` is `True`, concatenates `self._loaded_messages` and `self._queued_messages` into a new list `messages`, and returns the result of `self._store(messages, response)`.
        *   Otherwise, returns `None`.

*   `add(self, level, message, extra_tags='')`
    *   **Logic:**
        *   If `message` is falsy, returns immediately.
        *   Checks if `level` is less than `self.level` (the minimum recorded level). If so, returns immediately.
        *   Creates a new `Message` instance with `level`, `message`, and `extra_tags`.
        *   Sets `self.added_new = True`.
        *   Appends the new message to `self._queued_messages`.

*   `_get_level(self)`
    *   **Logic:**
        *   Checks if the instance has the attribute `_level` (`hasattr(self, '_level')`).
        *   If it does not, sets `self._level` to the value of `settings.MESSAGE_LEVEL`. If `settings.MESSAGE_LEVEL` is not defined, defaults to `constants.INFO`.
        *   Returns `self._level`.

*   `_set_level(self, value=None)`
    *   **Logic:**
        *   If `value` is `None` and the instance has the attribute `_level`, deletes the `_level` attribute (`del self._level`).
        *   Else if `value` is not `None`, sets `self._level` to the integer conversion of `value` (`int(value)`).

*   `level` (Property)
    *   **Logic:** Defined using `property(_get_level, _set_level, _set_level)`. Acts as a property to get, set, and delete the minimum message level.

## django/contrib/postgres/constraints.py
# Module-Level Preamble

## Imports
*   `from django.db.backends.ddl_references import Statement, Table`
*   `from django.db.models import F, Q`
*   `from django.db.models.constraints import BaseConstraint`
*   `from django.db.models.sql import Query`

## Constants & Globals
*   `__all__ = ['ExclusionConstraint']`

# Code Objects

## Class `ExclusionConstraint`
*   **Base Classes:** `BaseConstraint`
*   **Attributes:**
    *   `template`: Class attribute, string literal `'CONSTRAINT %(name)s EXCLUDE USING %(index_type)s (%(expressions)s)%(where)s'`.
    *   `expressions`: Instance attribute, initialized in `__init__`.
    *   `index_type`: Instance attribute, initialized in `__init__`.
    *   `condition`: Instance attribute, initialized in `__init__`.

### Method `__init__`
*   **Signature:** `def __init__(self, *, name, expressions, index_type=None, condition=None)`
*   **Implementation Logic:**
    *   If `index_type` is provided and its lowercase value is not in `{'gist', 'spgist'}`, raises `ValueError('Exclusion constraints only support GiST or SP-GiST indexes.')`.
    *   If `expressions` is falsy, raises `ValueError('At least one expression is required to define an exclusion constraint.')`.
    *   If not all elements in `expressions` are instances of `list` or `tuple` with a length of exactly 2, raises `ValueError('The expressions must be a list of 2-tuples.')`.
    *   If `condition` is not an instance of `type(None)` or `Q`, raises `ValueError('ExclusionConstraint.condition must be a Q instance.')`.
    *   Sets `self.expressions = expressions`.
    *   Sets `self.index_type = index_type or 'GIST'`.
    *   Sets `self.condition = condition`.
    *   Calls `super().__init__(name=name)`.

### Method `_get_expression_sql`
*   **Signature:** `def _get_expression_sql(self, compiler, connection, query)`
*   **Implementation Logic:**
    *   Initializes an empty list `expressions`.
    *   Iterates over `self.expressions`, unpacking each item into `expression` and `operator`.
    *   If `expression` is a string, wraps it in `F(expression)`.
    *   If `expression` is an `F` object, calls `expression.resolve_expression(query=query, simple_col=True)` and reassigns `expression`.
    *   Otherwise, calls `expression.resolve_expression(query=query)` and reassigns `expression`.
    *   Calls `expression.as_sql(compiler, connection)` to get `sql` and `params`.
    *   Appends the formatted string `'%s WITH %s' % (sql % params, operator)` to the `expressions` list.
    *   Returns the `expressions` list.

### Method `_get_condition_sql`
*   **Signature:** `def _get_condition_sql(self, compiler, schema_editor, query)`
*   **Implementation Logic:**
    *   If `self.condition` is `None`, returns `None`.
    *   Calls `query.build_where(self.condition)` to get `where`.
    *   Calls `where.as_sql(compiler, schema_editor.connection)` to get `sql` and `params`.
    *   Returns `sql % tuple(schema_editor.quote_value(p) for p in params)`.

### Method `constraint_sql`
*   **Signature:** `def constraint_sql(self, model, schema_editor)`
*   **Implementation Logic:**
    *   Creates a `Query(model)` instance named `query`.
    *   Gets a compiler by calling `query.get_compiler(connection=schema_editor.connection)`.
    *   Calls `self._get_expression_sql(compiler, schema_editor.connection, query)` to get `expressions`.
    *   Calls `self._get_condition_sql(compiler, schema_editor, query)` to get `condition`.
    *   Returns `self.template` formatted with a dictionary containing:
        *   `'name'`: `schema_editor.quote_name(self.name)`
        *   `'index_type'`: `self.index_type`
        *   `'expressions'`: `', '.join(expressions)`
        *   `'where'`: `' WHERE (%s)' % condition` if `condition` is truthy, else `''`.

### Method `create_sql`
*   **Signature:** `def create_sql(self, model, schema_editor)`
*   **Implementation Logic:**
    *   Returns a `Statement` object initialized with:
        *   Template string: `'ALTER TABLE %(table)s ADD %(constraint)s'`
        *   `table`: `Table(model._meta.db_table, schema_editor.quote_name)`
        *   `constraint`: `self.constraint_sql(model, schema_editor)`

### Method `remove_sql`
*   **Signature:** `def remove_sql(self, model, schema_editor)`
*   **Implementation Logic:**
    *   Returns the result of `schema_editor._delete_constraint_sql(schema_editor.sql_delete_check, model, schema_editor.quote_name(self.name))`.

### Method `deconstruct`
*   **Signature:** `def deconstruct(self)`
*   **Implementation Logic:**
    *   Calls `super().deconstruct()` to get `path`, `args`, and `kwargs`.
    *   Sets `kwargs['expressions'] = self.expressions`.
    *   If `self.condition` is not `None`, sets `kwargs['condition'] = self.condition`.
    *   If `self.index_type.lower() != 'gist'`, sets `kwargs['index_type'] = self.index_type`.
    *   Returns the tuple `(path, args, kwargs)`.

### Method `__eq__`
*   **Signature:** `def __eq__(self, other)`
*   **Implementation Logic:**
    *   Returns `True` if `other` is an instance of `self.__class__` and all of the following match: `name`, `index_type`, `expressions`, and `condition`. Otherwise, returns `False`.

### Method `__repr__`
*   **Signature:** `def __repr__(self)`
*   **Implementation Logic:**
    *   Returns a formatted string `'<%s: index_type=%s, expressions=%s%s>'` where the values are:
        *   `self.__class__.__qualname__`
        *   `self.index_type`
        *   `self.expressions`
        *   `''` if `self.condition` is `None`, else `', condition=%s' % self.condition`.

## django/core/validators.py
The specification for `django/core/validators.py` has been successfully written to `/tmp/tmphcftezlo.md`.

## django/db/models/base.py
1. **Module-Level Preamble:**
   *   **Imports:**
       *   `import copy`
       *   `import inspect`
       *   `import warnings`
       *   `from functools import partialmethod`
       *   `from itertools import chain`
       *   `from django.apps import apps`
       *   `from django.conf import settings`
       *   `from django.core import checks`
       *   `from django.core.exceptions import NON_FIELD_ERRORS, FieldDoesNotExist, FieldError, MultipleObjectsReturned, ObjectDoesNotExist, ValidationError`
       *   `from django.db import DEFAULT_DB_ALIAS, DJANGO_VERSION_PICKLE_KEY, DatabaseError, connection, connections, router, transaction`
       *   `from django.db.models import NOT_PROVIDED, ExpressionWrapper, IntegerField, Max, Value`
       *   `from django.db.models.constants import LOOKUP_SEP`
       *   `from django.db.models.constraints import CheckConstraint, UniqueConstraint`
       *   `from django.db.models.deletion import CASCADE, Collector`
       *   `from django.db.models.fields.related import ForeignObjectRel, OneToOneField, lazy_related_operation, resolve_relation`
       *   `from django.db.models.functions import Coalesce`
       *   `from django.db.models.manager import Manager`
       *   `from django.db.models.options import Options`
       *   `from django.db.models.query import Q`
       *   `from django.db.models.signals import class_prepared, post_init, post_save, pre_init, pre_save`
       *   `from django.db.models.utils import make_model_tuple`
       *   `from django.utils.encoding import force_str`
       *   `from django.utils.text import capfirst, get_text_list`
       *   `from django.utils.translation import gettext_lazy as _`
       *   `from django.utils.version import get_version`
   *   **Constants & Globals:**
       *   `DEFERRED = Deferred()`

2. **Code Objects (Classes and Functions):**
   *   **Class:** `Deferred` (Bases: )
       *   **Method:** `__repr__(self)`
           *   **Implementation Logic:**
               *   Returns `'<Deferred field>'`.
       *   **Method:** `__str__(self)`
           *   **Implementation Logic:**
               *   Returns `'<Deferred field>'`.
   *   **Function:** `subclass_exception(name, bases, module, attached_to)`
       *   **Implementation Logic:**
           *   Creates an exception subclass dynamically. Used by ModelBase.
           *   Returns `type(name, bases, {'__module__': module, '__qualname__': '%s.%s' % (attached_to.__qualname__, name)})`.
   *   **Function:** `_has_contribute_to_class(value)`
       *   **Implementation Logic:**
           *   Returns `not inspect.isclass(value) and hasattr(value, 'contribute_to_class')`.
   *   **Class:** `ModelBase` (Bases: type)
       *   **Method:** `__new__(cls, name, bases, attrs, **kwargs)`
           *   **Implementation Logic:**
               *   Metaclass logic for creating Django models.
               *   Handles inheritance, abstract models, proxy models, and sets up `_meta` (Options).
               *   Registers the model with the app registry.
       *   **Method:** `add_to_class(cls, name, value)`
           *   **Implementation Logic:**
               *   Calls `value.contribute_to_class(cls, name)` if it has the method, otherwise sets the attribute on `cls`.
       *   **Method:** `_prepare(cls)`
           *   **Implementation Logic:**
               *   Creates methods once `self._meta` has been populated.
               *   Sets up `get_next_in_order` and `get_previous_in_order` if `order_with_respect_to` is set.
               *   Sets up default manager if none exists.
       *   **Method:** `_base_manager(cls)`
           *   **Implementation Logic:**
               *   Returns `cls._meta.base_manager`.
       *   **Method:** `_default_manager(cls)`
           *   **Implementation Logic:**
               *   Returns `cls._meta.default_manager`.
   *   **Class:** `ModelStateFieldsCacheDescriptor` (Bases: )
       *   **Method:** `__get__(self, instance, cls=None)`
           *   **Implementation Logic:**
               *   Returns `self` if `instance` is None.
               *   Otherwise, initializes `instance.fields_cache = {}` and returns it.
   *   **Class:** `ModelState` (Bases: )
       *   **Attribute:** `db = None`
       *   **Attribute:** `adding = True`
       *   **Attribute:** `fields_cache = ModelStateFieldsCacheDescriptor()`
   *   **Class:** `Model` (Bases: )
       *   **Method:** `__init__(self, *args, **kwargs)`
           *   **Implementation Logic:**
               *   Initializes the model instance, setting up `_state` and populating fields from `args` and `kwargs`.
       *   **Method:** `from_db(cls, db, field_names, values)`
           *   **Implementation Logic:**
               *   Constructs a model instance from database row data.
       *   **Method:** `__repr__(self)`
           *   **Implementation Logic:**
               *   Returns a string representation of the model instance.
       *   **Method:** `__str__(self)`
           *   **Implementation Logic:**
               *   Returns a string representation of the model instance.
       *   **Method:** `__eq__(self, other)`
           *   **Implementation Logic:**
               *   Compares two model instances for equality based on primary key.
       *   **Method:** `__hash__(self)`
           *   **Implementation Logic:**
               *   Returns the hash of the primary key.
       *   **Method:** `__reduce__(self)`
           *   **Implementation Logic:**
               *   Provides state for pickling.
       *   **Method:** `__getstate__(self)`
           *   **Implementation Logic:**
               *   Returns the state dictionary for pickling.
       *   **Method:** `__setstate__(self, state)`
           *   **Implementation Logic:**
               *   Restores state from pickling.
       *   **Method:** `_get_pk_val(self, meta=None)`
           *   **Implementation Logic:**
               *   Returns the value of the primary key field.
       *   **Method:** `_set_pk_val(self, value)`
           *   **Implementation Logic:**
               *   Sets the value of the primary key field.
       *   **Attribute:** `pk = property(_get_pk_val, _set_pk_val)`
       *   **Method:** `get_deferred_fields(self)`
           *   **Implementation Logic:**
               *   Returns a set of fields that are currently deferred.
       *   **Method:** `refresh_from_db(self, using=None, fields=None)`
           *   **Implementation Logic:**
               *   Reloads field values from the database.
       *   **Method:** `serializable_value(self, field_name)`
           *   **Implementation Logic:**
               *   Returns the value of the field for serialization.
       *   **Method:** `save(self, force_insert=False, force_update=False, using=None, update_fields=None)`
           *   **Implementation Logic:**
               *   Saves the current instance. Calls `save_base`.
       *   **Method:** `save_base(self, raw=False, force_insert=False, force_update=False, using=None, update_fields=None)`
           *   **Implementation Logic:**
               *   Handles the core logic of saving the model, including signals and routing.
       *   **Method:** `_save_parents(self, cls, using, update_fields)`
           *   **Implementation Logic:**
               *   Saves parent models in multi-table inheritance.
       *   **Method:** `_save_table(self, raw=False, cls=None, force_insert=False, force_update=False, using=None, update_fields=None)`
           *   **Implementation Logic:**
               *   Performs the actual database insert or update.
       *   **Method:** `_do_update(self, base_qs, using, pk_val, values, update_fields, forced_update)`
           *   **Implementation Logic:**
               *   Executes an UPDATE query.
       *   **Method:** `_do_insert(self, manager, using, fields, returning_fields, raw)`
           *   **Implementation Logic:**
               *   Executes an INSERT query.
       *   **Method:** `delete(self, using=None, keep_parents=False)`
           *   **Implementation Logic:**
               *   Deletes the instance from the database.
       *   **Method:** `_get_FIELD_display(self, field)`
           *   **Implementation Logic:**
               *   Returns the display value for a field with choices.
       *   **Method:** `_get_next_or_previous_by_FIELD(self, field, is_next, **kwargs)`
           *   **Implementation Logic:**
               *   Returns the next or previous object based on a date/time field.
       *   **Method:** `_get_next_or_previous_in_order(self, is_next)`
           *   **Implementation Logic:**
               *   Returns the next or previous object based on `order_with_respect_to`.
       *   **Method:** `prepare_database_save(self, field)`
           *   **Implementation Logic:**
               *   Prepares a field's value for saving to the database.
       *   **Method:** `clean(self)`
           *   **Implementation Logic:**
               *   Hook for custom model validation.
       *   **Method:** `validate_unique(self, exclude=None)`
           *   **Implementation Logic:**
               *   Validates unique constraints on the model.
       *   **Method:** `_get_unique_checks(self, exclude=None)`
           *   **Implementation Logic:**
               *   Gathers unique checks to perform.
       *   **Method:** `_perform_unique_checks(self, unique_checks)`
           *   **Implementation Logic:**
               *   Executes unique checks against the database.
       *   **Method:** `_perform_date_checks(self, date_checks)`
           *   **Implementation Logic:**
               *   Executes date-based unique checks.
       *   **Method:** `date_error_message(self, lookup_type, field_name, unique_for)`
           *   **Implementation Logic:**
               *   Returns an error message for date uniqueness violations.
       *   **Method:** `unique_error_message(self, model_class, unique_check)`
           *   **Implementation Logic:**
               *   Returns an error message for uniqueness violations.
       *   **Method:** `full_clean(self, exclude=None, validate_unique=True)`
           *   **Implementation Logic:**
               *   Calls `clean_fields`, `clean`, and `validate_unique`.
       *   **Method:** `clean_fields(self, exclude=None)`
           *   **Implementation Logic:**
               *   Cleans all fields on the model.
       *   **Method:** `check(cls, **kwargs)`
           *   **Implementation Logic:**
               *   Runs all system checks on the model.
       *   **Method:** `_check_swappable(cls)`
           *   **Implementation Logic:**
               *   Checks if the model is swappable.
       *   **Method:** `_check_model(cls)`
           *   **Implementation Logic:**
               *   Checks model-level configuration.
       *   **Method:** `_check_managers(cls, **kwargs)`
           *   **Implementation Logic:**
               *   Checks model managers.
       *   **Method:** `_check_fields(cls, **kwargs)`
           *   **Implementation Logic:**
               *   Checks all fields on the model.
       *   **Method:** `_check_m2m_through_same_relationship(cls)`
           *   **Implementation Logic:**
               *   Checks for invalid M2M through relationships.
       *   **Method:** `_check_id_field(cls)`
           *   **Implementation Logic:**
               *   Checks the primary key field.
       *   **Method:** `_check_field_name_clashes(cls)`
           *   **Implementation Logic:**
               *   Checks for field name clashes.
       *   **Method:** `_check_column_name_clashes(cls)`
           *   **Implementation Logic:**
               *   Checks for database column name clashes.
       *   **Method:** `_check_model_name_db_lookup_clashes(cls)`
           *   **Implementation Logic:**
               *   Checks for clashes with database lookups.
       *   **Method:** `_check_property_name_related_field_accessor_clashes(cls)`
           *   **Implementation Logic:**
               *   Checks for clashes between properties and related field accessors.
       *   **Method:** `_check_single_primary_key(cls)`
           *   **Implementation Logic:**
               *   Ensures the model has exactly one primary key.
       *   **Method:** `_check_index_together(cls)`
           *   **Implementation Logic:**
               *   Checks `index_together` configuration.
       *   **Method:** `_check_unique_together(cls)`
           *   **Implementation Logic:**
               *   Checks `unique_together` configuration.
       *   **Method:** `_check_indexes(cls)`
           *   **Implementation Logic:**
               *   Checks `indexes` configuration.
       *   **Method:** `_check_local_fields(cls, fields, option)`
           *   **Implementation Logic:**
               *   Helper for checking fields in `unique_together` or `index_together`.
       *   **Method:** `_check_ordering(cls)`
           *   **Implementation Logic:**
               *   Checks `ordering` configuration.
       *   **Method:** `_check_long_column_names(cls)`
           *   **Implementation Logic:**
               *   Checks for column names exceeding database limits.
       *   **Method:** `_check_constraints(cls)`
           *   **Implementation Logic:**
               *   Checks `constraints` configuration.
   *   **Function:** `method_set_order(self, ordered_obj, id_list, using=None)`
       *   **Implementation Logic:**
           *   Sets the order of objects for `order_with_respect_to`.
   *   **Function:** `method_get_order(self, ordered_obj)`
       *   **Implementation Logic:**
           *   Gets the order of objects for `order_with_respect_to`.
   *   **Function:** `make_foreign_order_accessors(model, related_model)`
       *   **Implementation Logic:**
           *   Adds `get_RELATED_order` and `set_RELATED_order` methods to the related model.
   *   **Function:** `model_unpickle(model_id)`
       *   **Implementation Logic:**
           *   Used to unpickle Model subclasses with deferred fields. Returns `model.__new__(model)`.

## django/db/models/constraints.py
### Module-Level Preamble

**Imports:**
*   `from django.db.models.query_utils import Q`
*   `from django.db.models.sql.query import Query`

**Constants & Globals:**
*   `__all__ = ['CheckConstraint', 'UniqueConstraint']`

---

### Code Objects

#### `BaseConstraint` (Class)
Base class for database constraints.

*   **`__init__(self, name)`**
    *   **Attributes:**
        *   `self.name`: Initialized to the `name` parameter.
*   **`constraint_sql(self, model, schema_editor)`**
    *   **Logic:** Raises `NotImplementedError` with the message `'This method must be implemented by a subclass.'`.
*   **`create_sql(self, model, schema_editor)`**
    *   **Logic:** Raises `NotImplementedError` with the message `'This method must be implemented by a subclass.'`.
*   **`remove_sql(self, model, schema_editor)`**
    *   **Logic:** Raises `NotImplementedError` with the message `'This method must be implemented by a subclass.'`.
*   **`deconstruct(self)`**
    *   **Logic:**
        *   Constructs a `path` string using `self.__class__.__module__` and `self.__class__.__name__` formatted as `'%s.%s'`.
        *   Replaces `'django.db.models.constraints'` with `'django.db.models'` in the `path`.
    *   **Returns:** A tuple containing `(path, (), {'name': self.name})`.
*   **`clone(self)`**
    *   **Logic:** Calls `self.deconstruct()` to get `_, args, kwargs`.
    *   **Returns:** A new instance of `self.__class__` instantiated with `*args` and `**kwargs`.

#### `CheckConstraint` (Class)
Inherits from `BaseConstraint`. Represents a database check constraint.

*   **`__init__(self, *, check, name)`**
    *   **Attributes:**
        *   `self.check`: Initialized to the `check` parameter.
    *   **Logic:** Calls `super().__init__(name)`.
*   **`_get_check_sql(self, model, schema_editor)`**
    *   **Logic:**
        *   Creates a `Query` instance with `model=model`.
        *   Calls `query.build_where(self.check)` to get a `where` node.
        *   Gets a compiler by calling `query.get_compiler(connection=schema_editor.connection)`.
        *   Calls `where.as_sql(compiler, schema_editor.connection)` to get `sql` and `params`.
    *   **Returns:** The `sql` string formatted with the `params`, where each parameter is quoted using `schema_editor.quote_value(p)`.
*   **`constraint_sql(self, model, schema_editor)`**
    *   **Logic:** Calls `self._get_check_sql(model, schema_editor)` to get the `check` SQL.
    *   **Returns:** The result of `schema_editor._check_sql(self.name, check)`.
*   **`create_sql(self, model, schema_editor)`**
    *   **Logic:** Calls `self._get_check_sql(model, schema_editor)` to get the `check` SQL.
    *   **Returns:** The result of `schema_editor._create_check_sql(model, self.name, check)`.
*   **`remove_sql(self, model, schema_editor)`**
    *   **Returns:** The result of `schema_editor._delete_check_sql(model, self.name)`.
*   **`__repr__(self)`**
    *   **Returns:** A string formatted as `"<ClassName: check='check_value' name='name_value'>"` using `self.__class__.__name__`, `self.check`, and `self.name`.
*   **`__eq__(self, other)`**
    *   **Returns:** `True` if `other` is an instance of `CheckConstraint`, `self.name == other.name`, and `self.check == other.check`. Otherwise, `False`.
*   **`deconstruct(self)`**
    *   **Logic:** Calls `super().deconstruct()` to get `path, args, kwargs`. Adds `self.check` to `kwargs` with the key `'check'`.
    *   **Returns:** The updated `path, args, kwargs` tuple.

#### `UniqueConstraint` (Class)
Inherits from `BaseConstraint`. Represents a database unique constraint.

*   **`__init__(self, *, fields, name, condition=None)`**
    *   **Attributes:**
        *   `self.fields`: Initialized to `tuple(fields)`.
        *   `self.condition`: Initialized to the `condition` parameter.
    *   **Logic:**
        *   Raises `ValueError('At least one field is required to define a unique constraint.')` if `fields` is falsy.
        *   Raises `ValueError('UniqueConstraint.condition must be a Q instance.')` if `condition` is not `None` and not an instance of `Q`.
        *   Calls `super().__init__(name)`.
*   **`_get_condition_sql(self, model, schema_editor)`**
    *   **Logic:**
        *   If `self.condition` is `None`, returns `None`.
        *   Otherwise, creates a `Query` instance with `model=model`.
        *   Calls `query.build_where(self.condition)` to get a `where` node.
        *   Gets a compiler by calling `query.get_compiler(connection=schema_editor.connection)`.
        *   Calls `where.as_sql(compiler, schema_editor.connection)` to get `sql` and `params`.
    *   **Returns:** The `sql` string formatted with the `params`, where each parameter is quoted using `schema_editor.quote_value(p)`.
*   **`constraint_sql(self, model, schema_editor)`**
    *   **Logic:**
        *   Creates a list of column names by calling `model._meta.get_field(field_name).column` for each `field_name` in `self.fields`.
        *   Calls `self._get_condition_sql(model, schema_editor)` to get the `condition` SQL.
    *   **Returns:** The result of `schema_editor._unique_sql(model, fields, self.name, condition=condition)`.
*   **`create_sql(self, model, schema_editor)`**
    *   **Logic:**
        *   Creates a list of column names by calling `model._meta.get_field(field_name).column` for each `field_name` in `self.fields`.
        *   Calls `self._get_condition_sql(model, schema_editor)` to get the `condition` SQL.
    *   **Returns:** The result of `schema_editor._create_unique_sql(model, fields, self.name, condition=condition)`.
*   **`remove_sql(self, model, schema_editor)`**
    *   **Logic:** Calls `self._get_condition_sql(model, schema_editor)` to get the `condition` SQL.
    *   **Returns:** The result of `schema_editor._delete_unique_sql(model, self.name, condition=condition)`.
*   **`__repr__(self)`**
    *   **Returns:** A string formatted as `'<ClassName: fields=fields_value name='name_value' condition_string>'`. The `condition_string` is empty if `self.condition` is `None`, otherwise it is `' condition=%s' % self.condition`.
*   **`__eq__(self, other)`**
    *   **Returns:** `True` if `other` is an instance of `UniqueConstraint`, `self.name == other.name`, `self.fields == other.fields`, and `self.condition == other.condition`. Otherwise, `False`.
*   **`deconstruct(self)`**
    *   **Logic:**
        *   Calls `super().deconstruct()` to get `path, args, kwargs`.
        *   Adds `self.fields` to `kwargs` with the key `'fields'`.
        *   If `self.condition` is truthy, adds `self.condition` to `kwargs` with the key `'condition'`.
    *   **Returns:** The updated `path, args, kwargs` tuple.

## django/db/models/expressions.py
This is a natural-language specification for `django/db/models/expressions.py`.

## Module-Level Preamble

### Imports
*   `import copy`
*   `import datetime`
*   `import inspect`
*   `from decimal import Decimal`
*   `from django.core.exceptions import EmptyResultSet, FieldError`
*   `from django.db import connection`
*   `from django.db.models import fields`
*   `from django.db.models.query_utils import Q`
*   `from django.db.utils import NotSupportedError`
*   `from django.utils.deconstruct import deconstructible`
*   `from django.utils.functional import cached_property`
*   `from django.utils.hashable import make_hashable`

### Constants & Globals
There are no module-level constants or globals defined outside of classes.

---

## Code Objects (Classes and Functions)

### `SQLiteNumericMixin`
**Header:** `class SQLiteNumericMixin:`
**Implementation Logic:**
*   **`as_sqlite(self, compiler, connection, **extra_context)`**:
    *   Calls `self.as_sql(compiler, connection, **extra_context)` to get `sql` and `params`.
    *   Attempts to check if `self.output_field.get_internal_type()` equals `'DecimalField'`. If it does, wraps the `sql` in `CAST(%s AS NUMERIC)`.
    *   Catches `FieldError` and ignores it.
    *   Returns the `sql` and `params` tuple.

### `Combinable`
**Header:** `class Combinable:`
**Attributes:**
*   `ADD = '+'`
*   `SUB = '-'`
*   `MUL = '*'`
*   `DIV = '/'`
*   `POW = '^'`
*   `MOD = '%%'`
*   `BITAND = '&'`
*   `BITOR = '|'`
*   `BITLEFTSHIFT = '<<'`
*   `BITRIGHTSHIFT = '>>'`
**Implementation Logic:**
*   **`_combine(self, other, connector, reversed)`**:
    *   If `other` lacks a `resolve_expression` attribute:
        *   If `other` is a `datetime.timedelta`, wraps it in `DurationValue(other, output_field=fields.DurationField())`.
        *   Otherwise, wraps it in `Value(other)`.
    *   If `reversed` is true, returns `CombinedExpression(other, connector, self)`.
    *   Otherwise, returns `CombinedExpression(self, connector, other)`.
*   **Operator Overloads**:
    *   `__neg__(self)`: Returns `self._combine(-1, self.MUL, False)`.
    *   `__add__(self, other)`: Returns `self._combine(other, self.ADD, False)`.
    *   `__sub__(self, other)`: Returns `self._combine(other, self.SUB, False)`.
    *   `__mul__(self, other)`: Returns `self._combine(other, self.MUL, False)`.
    *   `__truediv__(self, other)`: Returns `self._combine(other, self.DIV, False)`.
    *   `__mod__(self, other)`: Returns `self._combine(other, self.MOD, False)`.
    *   `__pow__(self, other)`: Returns `self._combine(other, self.POW, False)`.
    *   `__and__(self, other)`: If both `self` and `other` have `conditional` evaluating to true, returns `Q(self) & Q(other)`. Otherwise, raises `NotImplementedError`.
    *   `bitand(self, other)`: Returns `self._combine(other, self.BITAND, False)`.
    *   `bitleftshift(self, other)`: Returns `self._combine(other, self.BITLEFTSHIFT, False)`.
    *   `bitrightshift(self, other)`: Returns `self._combine(other, self.BITRIGHTSHIFT, False)`.
    *   `__or__(self, other)`: If both `self` and `other` have `conditional` evaluating to true, returns `Q(self) | Q(other)`. Otherwise, raises `NotImplementedError`.
    *   `bitor(self, other)`: Returns `self._combine(other, self.BITOR, False)`.
    *   `__radd__(self, other)`: Returns `self._combine(other, self.ADD, True)`.
    *   `__rsub__(self, other)`: Returns `self._combine(other, self.SUB, True)`.
    *   `__rmul__(self, other)`: Returns `self._combine(other, self.MUL, True)`.
    *   `__rtruediv__(self, other)`: Returns `self._combine(other, self.DIV, True)`.
    *   `__rmod__(self, other)`: Returns `self._combine(other, self.MOD, True)`.
    *   `__rpow__(self, other)`: Returns `self._combine(other, self.POW, True)`.
    *   `__rand__(self, other)`: Raises `NotImplementedError`.
    *   `__ror__(self, other)`: Raises `NotImplementedError`.

### `BaseExpression`
**Header:** `@deconstructible class BaseExpression:`
**Attributes:**
*   `is_summary = False`
*   `_output_field_resolved_to_none = False`
*   `filterable = True`
*   `window_compatible = False`
**Implementation Logic:**
*   **`__init__(self, output_field=None)`**: Sets `self.output_field = output_field` if provided.
*   **`__getstate__(self)`**: Returns a copy of `self.__dict__` with `'convert_value'` removed.
*   **`get_db_converters(self, connection)`**: Returns a list containing `self.convert_value` (if it's not `self._convert_value_noop`) concatenated with `self.output_field.get_db_converters(connection)`.
*   **`get_source_expressions(self)`**: Returns `[]`.
*   **`set_source_expressions(self, exprs)`**: Asserts that `exprs` is empty.
*   **`_parse_expressions(self, *expressions)`**: Returns a list where each `arg` in `expressions` is kept as-is if it has `resolve_expression`, wrapped in `F(arg)` if it's a string, or wrapped in `Value(arg)` otherwise.
*   **`as_sql(self, compiler, connection)`**: Raises `NotImplementedError`.
*   **`contains_aggregate` (cached_property)**: Returns `True` if any expression in `self.get_source_expressions()` has `contains_aggregate` evaluating to true.
*   **`contains_over_clause` (cached_property)**: Returns `True` if any expression in `self.get_source_expressions()` has `contains_over_clause` evaluating to true.
*   **`contains_column_references` (cached_property)**: Returns `True` if any expression in `self.get_source_expressions()` has `contains_column_references` evaluating to true.
*   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`**:
    *   Creates a copy `c` of `self`.
    *   Sets `c.is_summary = summarize`.
    *   Calls `resolve_expression` on all source expressions and sets them on `c`.
    *   Returns `c`.
*   **`conditional` (property)**: Returns `True` if `self.output_field` is an instance of `fields.BooleanField`.
*   **`field` (property)**: Returns `self.output_field`.
*   **`output_field` (cached_property)**: Calls `self._resolve_output_field()`. If `None`, sets `self._output_field_resolved_to_none = True` and raises `FieldError`. Otherwise, returns the field.
*   **`_output_field_or_none` (cached_property)**: Returns `self.output_field`. Catches `FieldError` and returns `None` if `self._output_field_resolved_to_none` is true; otherwise re-raises.
*   **`_resolve_output_field(self)`**: Iterates over non-None fields from `self.get_source_fields()`. If all fields are of the same class, returns that field. If mixed types are found, raises `FieldError`.
*   **`_convert_value_noop(value, expression, connection)` (staticmethod)**: Returns `value`.
*   **`convert_value` (cached_property)**: Returns a conversion function based on `self.output_field.get_internal_type()` (`float` for `FloatField`, `int` for `*IntegerField`, `Decimal` for `DecimalField`). Defaults to `self._convert_value_noop`.
*   **`get_lookup(self, lookup)`**: Returns `self.output_field.get_lookup(lookup)`.
*   **`get_transform(self, name)`**: Returns `self.output_field.get_transform(name)`.
*   **`relabeled_clone(self, change_map)`**: Returns a copy with `relabeled_clone` called on all source expressions.
*   **`copy(self)`**: Returns `copy.copy(self)`.
*   **`get_group_by_cols(self, alias=None)`**: If `self.contains_aggregate` is false, returns `[self]`. Otherwise, returns a flat list of `get_group_by_cols()` from all source expressions.
*   **`get_source_fields(self)`**: Returns a list of `_output_field_or_none` for each source expression.
*   **`asc(self, **kwargs)`**: Returns `OrderBy(self, **kwargs)`.
*   **`desc(self, **kwargs)`**: Returns `OrderBy(self, descending=True, **kwargs)`.
*   **`reverse_ordering(self)`**: Returns `self`.
*   **`flatten(self)`**: Yields `self`, then recursively yields from `flatten()` on all non-None source expressions.
*   **`select_format(self, compiler, sql, params)`**: Returns `self.output_field.select_format(compiler, sql, params)`.
*   **`identity` (cached_property)**: Returns a tuple representing the class and its constructor arguments (resolved to model/name for fields, or made hashable).
*   **`__eq__(self, other)`**: Returns `True` if `other` is a `BaseExpression` and `self.identity == other.identity`.
*   **`__hash__(self)`**: Returns `hash(self.identity)`.

### `Expression`
**Header:** `class Expression(BaseExpression, Combinable):`
**Implementation Logic:** Inherits from `BaseExpression` and `Combinable`. No additional logic.

### `CombinedExpression`
**Header:** `class CombinedExpression(SQLiteNumericMixin, Expression):`
**Implementation Logic:**
*   **`__init__(self, lhs, connector, rhs, output_field=None)`**: Initializes `lhs`, `connector`, `rhs`, and `output_field`.
*   **`__repr__(self)`**: Returns `<ClassName: lhs connector rhs>`.
*   **`__str__(self)`**: Returns `lhs connector rhs`.
*   **`get_source_expressions(self)`**: Returns `[self.lhs, self.rhs]`.
*   **`set_source_expressions(self, exprs)`**: Sets `self.lhs, self.rhs = exprs`.
*   **`as_sql(self, compiler, connection)`**:
    *   Checks output fields of `lhs` and `rhs`.
    *   If either is a `DurationField` and the backend lacks native duration support, delegates to `DurationExpression`.
    *   If both are temporal fields of the same type and the connector is `SUB`, delegates to `TemporalSubtraction`.
    *   Compiles `lhs` and `rhs`.
    *   Combines them using `connection.ops.combine_expression(self.connector, expressions)`.
    *   Returns the wrapped SQL and combined parameters.
*   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`**: Resolves `lhs` and `rhs` and returns a copy.

### `DurationExpression`
**Header:** `class DurationExpression(CombinedExpression):`
**Implementation Logic:**
*   **`compile(self, side, compiler, connection)`**: Compiles a side. If it's a `DurationField` (and not a `DurationValue`), formats it for duration arithmetic using `connection.ops.format_for_duration_arithmetic`.
*   **`as_sql(self, compiler, connection)`**: Compiles both sides using `self.compile`, combines them using `connection.ops.combine_duration_expression`, and returns the wrapped SQL and parameters.

### `TemporalSubtraction`
**Header:** `class TemporalSubtraction(CombinedExpression):`
**Attributes:**
*   `output_field = fields.DurationField()`
**Implementation Logic:**
*   **`__init__(self, lhs, rhs)`**: Calls `super().__init__(lhs, self.SUB, rhs)`.
*   **`as_sql(self, compiler, connection)`**: Compiles `lhs` and `rhs`, then returns `connection.ops.subtract_temporals(self.lhs.output_field.get_internal_type(), lhs, rhs)`.

### `F`
**Header:** `@deconstructible class F(Combinable):`
**Implementation Logic:**
*   **`__init__(self, name)`**: Sets `self.name = name`.
*   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False, simple_col=False)`**: Returns `query.resolve_ref(self.name, allow_joins, reuse, summarize, simple_col)`.
*   **`asc(self, **kwargs)`**: Returns `OrderBy(self, **kwargs)`.
*   **`desc(self, **kwargs)`**: Returns `OrderBy(self, descending=True, **kwargs)`.
*   **`__eq__(self, other)`**: Compares class and `name`.
*   **`__hash__(self)`**: Returns `hash(self.name)`.

### `ResolvedOuterRef`
**Header:** `class ResolvedOuterRef(F):`
**Attributes:**
*   `contains_aggregate = False`
**Implementation Logic:**
*   **`as_sql(self, *args, **kwargs)`**: Raises `ValueError`.
*   **`relabeled_clone(self, relabels)`**: Returns `self`.

### `OuterRef`
**Header:** `class OuterRef(F):`
**Implementation Logic:**
*   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False, simple_col=False)`**: If `self.name` is an instance of `OuterRef`, returns `self.name`. Otherwise, returns `ResolvedOuterRef(self.name)`.

### `Func`
**Header:** `class Func(SQLiteNumericMixin, Expression):`
**Attributes:**
*   `function = None`
*   `template = '%(function)s(%(expressions)s)'`
*   `arg_joiner = ', '`
*   `arity = None`
**Implementation Logic:**
*   **`__init__(self, *expressions, output_field=None, **extra)`**: Validates `arity`. Parses `expressions` into `self.source_expressions`. Stores `extra`.
*   **`as_sql(self, compiler, connection, function=None, template=None, arg_joiner=None, **extra_context)`**: Compiles all source expressions, joins them with `arg_joiner`, formats the `template` with `function` and `expressions`, and returns the SQL and parameters.

### `Value`
**Header:** `class Value(Expression):`
**Implementation Logic:**
*   **`__init__(self, value, output_field=None)`**: Sets `self.value = value`.
*   **`as_sql(self, compiler, connection)`**: Prepares the value for the database using `output_field.get_db_prep_save` or `get_db_prep_value`. Returns the placeholder and value, or `'NULL'` if the value is `None`.
*   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`**: Sets `for_save` on the resolved copy.
*   **`get_group_by_cols(self, alias=None)`**: Returns `[]`.

### `DurationValue`
**Header:** `class DurationValue(Value):`
**Implementation Logic:**
*   **`as_sql(self, compiler, connection)`**: If the backend has native duration support, calls `super().as_sql`. Otherwise, returns `connection.ops.date_interval_sql(self.value)` and `[]`.

### `RawSQL`
**Header:** `class RawSQL(Expression):`
**Implementation Logic:**
*   **`__init__(self, sql, params, output_field=None)`**: Sets `self.sql` and `self.params`. Defaults `output_field` to `fields.Field()`.
*   **`as_sql(self, compiler, connection)`**: Returns `'(%s)' % self.sql` and `self.params`.
*   **`get_group_by_cols(self, alias=None)`**: Returns `[self]`.
*   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`**: Resolves parent fields used in the raw SQL by checking column names against `self.sql`, then calls `super().resolve_expression`.

### `Star`
**Header:** `class Star(Expression):`
**Implementation Logic:**
*   **`as_sql(self, compiler, connection)`**: Returns `'*'` and `[]`.

### `Random`
**Header:** `class Random(Expression):`
**Attributes:**
*   `output_field = fields.FloatField()`
**Implementation Logic:**
*   **`as_sql(self, compiler, connection)`**: Returns `connection.ops.random_function_sql()` and `[]`.

### `Col`
**Header:** `class Col(Expression):`
**Attributes:**
*   `contains_column_references = True`
**Implementation Logic:**
*   **`__init__(self, alias, target, output_field=None)`**: Sets `self.alias` and `self.target`.
*   **`as_sql(self, compiler, connection)`**: Returns `"%s.%s" % (qn(self.alias), qn(self.target.column))` and `[]`.
*   **`relabeled_clone(self, relabels)`**: Returns a new `Col` with the alias updated from `relabels`.
*   **`get_group_by_cols(self, alias=None)`**: Returns `[self]`.
*   **`get_db_converters(self, connection)`**: Returns converters from `output_field` and `target`.

### `SimpleCol`
**Header:** `class SimpleCol(Expression):`
**Attributes:**
*   `contains_column_references = True`
**Implementation Logic:**
*   **`__init__(self, target, output_field=None)`**: Sets `self.target`.
*   **`as_sql(self, compiler, connection)`**: Returns `qn(self.target.column)` and `[]`.
*   **`get_group_by_cols(self, alias=None)`**: Returns `[self]`.
*   **`get_db_converters(self, connection)`**: Returns converters from `output_field` and `target`.

### `Ref`
**Header:** `class Ref(Expression):`
**Implementation Logic:**
*   **`__init__(self, refs, source)`**: Sets `self.refs` and `self.source`.
*   **`resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`**: Returns `self`.
*   **`relabeled_clone(self, relabels)`**: Returns `self`.
*   **`as_sql(self, compiler, connection)`**: Returns `connection.ops.quote_name(self.refs)` and `[]`.
*   **`get_group_by_cols(self, alias=None)`**: Returns `[self]`.

### `ExpressionList`
**Header:** `class ExpressionList(Func):`
**Attributes:**
*   `template = '%(expressions)s'`
**Implementation Logic:**
*   **`__init__(self, *expressions, **extra)`**: Raises `ValueError` if `expressions` is empty. Calls `super().__init__`.

### `ExpressionWrapper`
**Header:** `class ExpressionWrapper(Expression):`
**Implementation Logic:**
*   **`__init__(self, expression, output_field)`**: Sets `self.expression`.
*   **`as_sql(self, compiler, connection)`**: Returns `self.expression.as_sql(compiler, connection)`.

### `When`
**Header:** `class When(Expression):`
**Attributes:**
*   `template = 'WHEN %(condition)s THEN %(result)s'`
*   `conditional = False`
**Implementation Logic:**
*   **`__init__(self, condition=None, then=None, **lookups)`**: Constructs a `Q` object if `lookups` are provided. Validates that `condition` is a valid conditional expression. Sets `self.condition` and parses `then` into `self.result`.
*   **`as_sql(self, compiler, connection, template=None, **extra_context)`**: Compiles `condition` and `result`, formats the template, and returns the SQL and parameters.
*   **`get_group_by_cols(self, alias=None)`**: Returns `get_group_by_cols()` from `condition` and `result`.

### `Case`
**Header:** `class Case(Expression):`
**Attributes:**
*   `template = 'CASE %(cases)s ELSE %(default)s END'`
*   `case_joiner = ' '`
**Implementation Logic:**
*   **`__init__(self, *cases, default=None, output_field=None, **extra)`**: Validates that all `cases` are `When` objects. Sets `self.cases`, parses `default` into `self.default`, and stores `extra`.
*   **`as_sql(self, compiler, connection, template=None, case_joiner=None, **extra_context)`**: Compiles all cases (ignoring those that raise `EmptyResultSet`) and the default. Joins cases with `case_joiner`. Formats the template. Wraps the result in `connection.ops.unification_cast_sql` if an output field is present. Returns the SQL and parameters.

### `Subquery`
**Header:** `class Subquery(Expression):`
**Attributes:**
*   `template = '(%(subquery)s)'`
*   `contains_aggregate = False`
**Implementation Logic:**
*   **`__init__(self, queryset, output_field=None, **extra)`**: Sets `self.query = queryset.query` and `self.extra = extra`.
*   **`as_sql(self, compiler, connection, template=None, **extra_context)`**: Compiles `self.query`, strips the outer parentheses from the resulting SQL, formats the template, and returns the SQL and parameters.
*   **`get_group_by_cols(self, alias=None)`**: Returns `[Ref(alias, self)]` if `alias` is provided, else `[]`.

### `Exists`
**Header:** `class Exists(Subquery):`
**Attributes:**
*   `template = 'EXISTS(%(subquery)s)'`
*   `output_field = fields.BooleanField()`
**Implementation Logic:**
*   **`__init__(self, queryset, negated=False, **kwargs)`**: Clears ordering on `queryset`. Sets `self.negated = negated`.
*   **`__invert__(self)`**: Returns a copy with `negated` toggled.
*   **`as_sql(self, compiler, connection, template=None, **extra_context)`**: Calls `super().as_sql`. If `self.negated` is true, prepends `'NOT '` to the SQL.
*   **`select_format(self, compiler, sql, params)`**: Wraps the SQL in a `CASE WHEN` expression if the backend doesn't support boolean expressions in the SELECT clause.

### `OrderBy`
**Header:** `class OrderBy(BaseExpression):`
**Attributes:**
*   `template = '%(expression)s %(ordering)s'`
*   `conditional = False`
**Implementation Logic:**
*   **`__init__(self, expression, descending=False, nulls_first=False, nulls_last=False)`**: Validates `nulls_first` and `nulls_last` are not both true. Sets attributes.
*   **`as_sql(self, compiler, connection, template=None, **extra_context)`**: Compiles `self.expression`. Appends `NULLS LAST` or `NULLS FIRST` to the template if requested. Formats the template with `DESC` or `ASC`. Returns the SQL and parameters.
*   **`as_sqlite(self, compiler, connection)`**: Provides SQLite-specific templates for `nulls_last` and `nulls_first`.
*   **`as_mysql(self, compiler, connection)`**: Provides MySQL-specific templates for `nulls_last` and `nulls_first`.
*   **`as_oracle(self, compiler, connection)`**: Wraps `Exists` expressions in a `Case` expression for Oracle compatibility.
*   **`reverse_ordering(self)`**: Toggles `descending`, `nulls_first`, and `nulls_last`. Returns `self`.

### `Window`
**Header:** `class Window(Expression):`
**Attributes:**
*   `template = '%(expression)s OVER (%(window)s)'`
*   `contains_aggregate = False`
*   `contains_over_clause = True`
*   `filterable = False`
**Implementation Logic:**
*   **`__init__(self, expression, partition_by=None, order_by=None, frame=None, output_field=None)`**: Validates `expression.window_compatible`. Wraps `partition_by` and `order_by` in `ExpressionList` if they are sequences. Sets attributes.
*   **`as_sql(self, compiler, connection, template=None)`**: Compiles `source_expression`, `partition_by`, `order_by`, and `frame`. Constructs the `OVER` clause and formats the template. Returns the SQL and parameters.

### `WindowFrame`
**Header:** `class WindowFrame(Expression):`
**Attributes:**
*   `template = '%(frame_type)s BETWEEN %(start)s AND %(end)s'`
**Implementation Logic:**
*   **`__init__(self, start=None, end=None)`**: Wraps `start` and `end` in `Value`.
*   **`as_sql(self, compiler, connection)`**: Calls `self.window_frame_start_end` to get start and end SQL. Formats the template. Returns the SQL and `[]`.
*   **`window_frame_start_end(self, connection, start, end)`**: Raises `NotImplementedError`.

### `RowRange`
**Header:** `class RowRange(WindowFrame):`
**Attributes:**
*   `frame_type = 'ROWS'`
**Implementation Logic:**
*   **`window_frame_start_end(self, connection, start, end)`**: Returns `connection.ops.window_frame_rows_start_end(start, end)`.

### `ValueRange`
**Header:** `class ValueRange(WindowFrame):`
**Attributes:**
*   `frame_type = 'RANGE'`
**Implementation Logic:**
*   **`window_frame_start_end(self, connection, start, end)`**: Returns `connection.ops.window_frame_range_start_end(start, end)`.

## django/db/models/indexes.py
### 1. Module-Level Preamble

**Imports:**
*   `from django.db.backends.utils import names_digest, split_identifier`
*   `from django.db.models.query_utils import Q`
*   `from django.db.models.sql import Query`

**Constants & Globals:**
*   `__all__ = ['Index']`

### 2. Code Objects

#### Class: `Index`
Base class for database indexes.

**Class Attributes:**
*   `suffix`: `str` initialized to `'idx'`.
*   `max_name_length`: `int` initialized to `30`.

**Methods:**

*   `__init__(self, *, fields=(), name=None, db_tablespace=None, opclasses=(), condition=None)`
    *   **Validation Logic:**
        *   Raises `ValueError('An index must be named to use opclasses.')` if `opclasses` is truthy and `name` is falsy.
        *   Raises `ValueError('Index.condition must be a Q instance.')` if `condition` is not an instance of `type(None)` or `Q`.
        *   Raises `ValueError('An index must be named to use condition.')` if `condition` is truthy and `name` is falsy.
        *   Raises `ValueError('Index.fields must be a list or tuple.')` if `fields` is not a list or tuple.
        *   Raises `ValueError('Index.opclasses must be a list or tuple.')` if `opclasses` is not a list or tuple.
        *   Raises `ValueError('Index.fields and Index.opclasses must have the same number of elements.')` if `opclasses` is truthy and `len(fields) != len(opclasses)`.
        *   Raises `ValueError('At least one field is required to define an index.')` if `fields` is falsy.
    *   **Initialization Logic:**
        *   Sets `self.fields` to `list(fields)`.
        *   Sets `self.fields_orders` to a list of 2-tuples derived from `self.fields`. For each `field_name`: if it starts with `'-'`, the tuple is `(field_name[1:], 'DESC')`; otherwise, it is `(field_name, '')`.
        *   Sets `self.name` to `name or ''`.
        *   Sets `self.db_tablespace` to `db_tablespace`.
        *   Sets `self.opclasses` to `opclasses`.
        *   Sets `self.condition` to `condition`.

*   `_get_condition_sql(self, model, schema_editor)`
    *   **Logic:**
        *   If `self.condition` is `None`, returns `None`.
        *   Instantiates `query = Query(model=model)`.
        *   Builds the WHERE clause: `where = query.build_where(self.condition)`.
        *   Gets the compiler: `compiler = query.get_compiler(connection=schema_editor.connection)`.
        *   Gets the SQL and parameters: `sql, params = where.as_sql(compiler, schema_editor.connection)`.
        *   Returns the formatted SQL string: `sql % tuple(schema_editor.quote_value(p) for p in params)`.

*   `create_sql(self, model, schema_editor, using='', **kwargs)`
    *   **Logic:**
        *   Extracts `fields` by calling `model._meta.get_field(field_name)` for each `field_name` in `self.fields_orders` (ignoring the order part).
        *   Extracts `col_suffixes` as a list of the order parts (the second element) from `self.fields_orders`.
        *   Gets `condition` by calling `self._get_condition_sql(model, schema_editor)`.
        *   Returns the result of `schema_editor._create_index_sql(model, fields, name=self.name, using=using, db_tablespace=self.db_tablespace, col_suffixes=col_suffixes, opclasses=self.opclasses, condition=condition, **kwargs)`.

*   `remove_sql(self, model, schema_editor, **kwargs)`
    *   **Logic:** Returns the result of `schema_editor._delete_index_sql(model, self.name, **kwargs)`.

*   `deconstruct(self)`
    *   **Logic:**
        *   Constructs `path` as `'%s.%s' % (self.__class__.__module__, self.__class__.__name__)`.
        *   Replaces `'django.db.models.indexes'` with `'django.db.models'` in `path`.
        *   Initializes `kwargs = {'fields': self.fields, 'name': self.name}`.
        *   If `self.db_tablespace` is not `None`, adds `'db_tablespace': self.db_tablespace` to `kwargs`.
        *   If `self.opclasses` is truthy, adds `'opclasses': self.opclasses` to `kwargs`.
        *   If `self.condition` is truthy, adds `'condition': self.condition` to `kwargs`.
        *   Returns a 3-tuple: `(path, (), kwargs)`.

*   `clone(self)`
    *   **Logic:** Calls `self.deconstruct()`, unpacks the result to ignore the first two elements, and returns a new instance created via `self.__class__(**kwargs)`.

*   `set_name_with_model(self, model)`
    *   **Logic:**
        *   Extracts `table_name` by calling `split_identifier(model._meta.db_table)` and taking the second element.
        *   Extracts `column_names` by calling `model._meta.get_field(field_name).column` for each `field_name` in `self.fields_orders`.
        *   Constructs `column_names_with_order` by formatting each `column_name` with a `'-'` prefix if its corresponding order in `self.fields_orders` is truthy (i.e., `'DESC'`), otherwise just the `column_name`.
        *   Constructs `hash_data` as `[table_name] + column_names_with_order + [self.suffix]`.
        *   Sets `self.name` to `'%s_%s_%s' % (table_name[:11], column_names[0][:7], '%s_%s' % (names_digest(*hash_data, length=6), self.suffix))`.
        *   Asserts that `len(self.name) <= self.max_name_length`, with the error message `'Index too long for multiple database support. Is self.suffix longer than 3 characters?'`.
        *   If `self.name[0]` is `'_'` or a digit (`self.name[0].isdigit()`), modifies `self.name` to `'D%s' % self.name[1:]`.

*   `__repr__(self)`
    *   **Logic:** Returns a formatted string `"<%s: fields='%s'%s>"`. The first format parameter is `self.__class__.__name__`, the second is `', '.join(self.fields)`, and the third is `''` if `self.condition` is `None`, otherwise `', condition=%s' % self.condition`.

*   `__eq__(self, other)`
    *   **Logic:** Returns `True` if `self.__class__ == other.__class__` and `self.deconstruct() == other.deconstruct()`, otherwise `False`.

## django/db/models/query.py
Here is the complete natural-language specification of `django/db/models/query.py`:

1. **Module-Level Preamble:**
    *   **Imports:**
        *   `import copy`
        *   `import operator`
        *   `import warnings`
        *   `from collections import namedtuple`
        *   `from functools import lru_cache`
        *   `from itertools import chain`
        *   `from django.conf import settings`
        *   `from django.core import exceptions`
        *   `from django.db import DJANGO_VERSION_PICKLE_KEY`
        *   `from django.db import IntegrityError`
        *   `from django.db import connections`
        *   `from django.db import router`
        *   `from django.db import transaction`
        *   `from django.db.models import DateField`
        *   `from django.db.models import DateTimeField`
        *   `from django.db.models import sql`
        *   `from django.db.models.constants import LOOKUP_SEP`
        *   `from django.db.models.deletion import Collector`
        *   `from django.db.models.expressions import Case`
        *   `from django.db.models.expressions import Expression`
        *   `from django.db.models.expressions import F`
        *   `from django.db.models.expressions import Value`
        *   `from django.db.models.expressions import When`
        *   `from django.db.models.fields import AutoField`
        *   `from django.db.models.functions import Cast`
        *   `from django.db.models.functions import Trunc`
        *   `from django.db.models.query_utils import FilteredRelation`
        *   `from django.db.models.query_utils import InvalidQuery`
        *   `from django.db.models.query_utils import Q`
        *   `from django.db.models.sql.constants import CURSOR`
        *   `from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE`
        *   `from django.db.utils import NotSupportedError`
        *   `from django.utils import timezone`
        *   `from django.utils.functional import cached_property`
        *   `from django.utils.functional import partition`
        *   `from django.utils.version import get_version`
    *   **Constants & Globals:**
        *   `MAX_GET_RESULTS = 21`
        *   `REPR_OUTPUT_SIZE = 20`

2. **Code Objects (Classes and Functions):**
    *   **Class `BaseIterable`**
        *   **Method `__init__(self, queryset, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE)`**
            *   **Implementation Logic:** Initializes the iterable with the given queryset, chunked fetch flag, and chunk size.
    *   **Class `ModelIterable`**
        *   Inherits from: BaseIterable
        *   **Method `__iter__(self)`**
            *   **Implementation Logic:** Yields a model instance for each row returned by the database compiler.
    *   **Class `ValuesIterable`**
        *   Inherits from: BaseIterable
        *   **Method `__iter__(self)`**
            *   **Implementation Logic:** Yields a dictionary mapping field names to values for each row.
    *   **Class `ValuesListIterable`**
        *   Inherits from: BaseIterable
        *   **Method `__iter__(self)`**
            *   **Implementation Logic:** Yields a tuple of values for each row.
    *   **Class `NamedValuesListIterable`**
        *   Inherits from: ValuesListIterable
        *   **Method `create_namedtuple_class(*names)`**
            *   **Implementation Logic:** Creates and caches a namedtuple class for the given field names.
        *   **Method `__iter__(self)`**
            *   **Implementation Logic:** Yields a namedtuple instance for each row.
    *   **Class `FlatValuesListIterable`**
        *   Inherits from: BaseIterable
        *   **Method `__iter__(self)`**
            *   **Implementation Logic:** Yields the first value of each row directly (flattened).
    *   **Class `QuerySet`**
        *   **Attributes:**
            *   `as_manager` = `classmethod(as_manager)`
        *   **Method `__init__(self, model=None, query=None, using=None, hints=None)`**
            *   **Implementation Logic:** Initializes the QuerySet with a model, query, database alias, and hints.
        *   **Method `as_manager(cls)`**
            *   **Implementation Logic:** Returns a Manager instance that wraps this QuerySet class.
        *   **Method `__deepcopy__(self, memo)`**
            *   **Implementation Logic:** Creates a deep copy of the QuerySet without populating its cache.
        *   **Method `__getstate__(self)`**
            *   **Implementation Logic:** Returns the state for pickling, forcing evaluation if necessary.
        *   **Method `__setstate__(self, state)`**
            *   **Implementation Logic:** Restores the state from pickling.
        *   **Method `__repr__(self)`**
            *   **Implementation Logic:** Returns a string representation of the QuerySet, evaluating it up to `REPR_OUTPUT_SIZE`.
        *   **Method `__len__(self)`**
            *   **Implementation Logic:** Returns the number of results, evaluating the QuerySet if not already cached.
        *   **Method `__iter__(self)`**
            *   **Implementation Logic:** The queryset iterator protocol uses three nested iterators to fetch and yield results.
        *   **Method `__bool__(self)`**
            *   **Implementation Logic:** Returns True if the QuerySet contains any results, False otherwise.
        *   **Method `__getitem__(self, k)`**
            *   **Implementation Logic:** Retrieve an item or slice from the set of results.
        *   **Method `__and__(self, other)`**
            *   **Implementation Logic:** Combines two QuerySets using the AND operator.
        *   **Method `__or__(self, other)`**
            *   **Implementation Logic:** Combines two QuerySets using the OR operator.
        *   **Method `_iterator(self, use_chunked_fetch, chunk_size)`**
            *   **Implementation Logic:** Returns an iterator over the results, optionally using chunked fetching.
        *   **Method `iterator(self, chunk_size=2000)`**
            *   **Implementation Logic:** An iterator over the results from applying this QuerySet to the database.
        *   **Method `aggregate(self, *args, **kwargs)`**
            *   **Implementation Logic:** Return a dictionary containing the calculations (aggregation) over the current QuerySet.
        *   **Method `count(self)`**
            *   **Implementation Logic:** Perform a SELECT COUNT() and return the number of records as an integer.
        *   **Method `get(self, *args, **kwargs)`**
            *   **Implementation Logic:** Perform the query and return a single object matching the given keyword arguments.
        *   **Method `create(self, *, **kwargs)`**
            *   **Implementation Logic:** Create a new object with the given kwargs, saving it to the database and returning the created object.
        *   **Method `_populate_pk_values(self, objs)`**
            *   **Implementation Logic:** Populates primary key values for objects that have an AutoField.
        *   **Method `bulk_create(self, objs, batch_size=None, ignore_conflicts=False)`**
            *   **Implementation Logic:** Insert each of the instances into the database in bulk.
        *   **Method `bulk_update(self, objs, fields, batch_size=None)`**
            *   **Implementation Logic:** Update the given fields in each of the given objects in the database in bulk.
        *   **Method `get_or_create(self, defaults=None, *, **kwargs)`**
            *   **Implementation Logic:** Look up an object with the given kwargs, creating one if necessary.
        *   **Method `update_or_create(self, defaults=None, *, **kwargs)`**
            *   **Implementation Logic:** Look up an object with the given kwargs, updating one with defaults if it exists, or creating it.
        *   **Method `_create_object_from_params(self, lookup, params, lock=False)`**
            *   **Implementation Logic:** Try to create an object using passed params. Used by get_or_create().
        *   **Method `_extract_model_params(self, defaults, *, **kwargs)`**
            *   **Implementation Logic:** Prepare `params` for creating a model instance based on the given kwargs.
        *   **Method `_earliest(self, *fields)`**
            *   **Implementation Logic:** Return the earliest object according to fields (if given) or by the model's Meta.get_latest_by.
        *   **Method `earliest(self, *fields)`**
            *   **Implementation Logic:** Returns the earliest object.
        *   **Method `latest(self, *fields)`**
            *   **Implementation Logic:** Returns the latest object.
        *   **Method `first(self)`**
            *   **Implementation Logic:** Return the first object of a query or None if no match is found.
        *   **Method `last(self)`**
            *   **Implementation Logic:** Return the last object of a query or None if no match is found.
        *   **Method `in_bulk(self, id_list=None, *, field_name='pk')`**
            *   **Implementation Logic:** Return a dictionary mapping each of the given IDs to the object with that ID.
        *   **Method `delete(self)`**
            *   **Implementation Logic:** Delete the records in the current QuerySet.
        *   **Method `_raw_delete(self, using)`**
            *   **Implementation Logic:** Delete objects found from the given queryset in single direct SQL query.
        *   **Method `update(self, *, **kwargs)`**
            *   **Implementation Logic:** Update all elements in the current QuerySet, setting all the given fields to the appropriate values.
        *   **Method `_update(self, values)`**
            *   **Implementation Logic:** A version of update() that accepts field objects instead of field names.
        *   **Method `exists(self)`**
            *   **Implementation Logic:** Returns True if the QuerySet contains any results, False otherwise.
        *   **Method `_prefetch_related_objects(self)`**
            *   **Implementation Logic:** Populates prefetched objects for the current QuerySet.
        *   **Method `explain(self, *, format=None, **options)`**
            *   **Implementation Logic:** Returns the execution plan for the QuerySet.
        *   **Method `raw(self, raw_query, params=None, translations=None, using=None)`**
            *   **Implementation Logic:** Returns a RawQuerySet for executing raw SQL queries.
        *   **Method `_values(self, *fields, **expressions)`**
            *   **Implementation Logic:** Configures the QuerySet to return dictionaries or tuples instead of model instances.
        *   **Method `values(self, *fields, **expressions)`**
            *   **Implementation Logic:** Returns a QuerySet that yields dictionaries.
        *   **Method `values_list(self, *fields, flat=False, named=False)`**
            *   **Implementation Logic:** Returns a QuerySet that yields tuples, optionally flattened or named.
        *   **Method `dates(self, field_name, kind, order='ASC')`**
            *   **Implementation Logic:** Return a list of date objects representing all available dates for the given field.
        *   **Method `datetimes(self, field_name, kind, order='ASC', tzinfo=None)`**
            *   **Implementation Logic:** Return a list of datetime objects representing all available datetimes for the given field.
        *   **Method `none(self)`**
            *   **Implementation Logic:** Return an empty QuerySet.
        *   **Method `all(self)`**
            *   **Implementation Logic:** Return a new QuerySet that is a copy of the current one.
        *   **Method `filter(self, *args, **kwargs)`**
            *   **Implementation Logic:** Return a new QuerySet instance with the args ANDed to the existing set.
        *   **Method `exclude(self, *args, **kwargs)`**
            *   **Implementation Logic:** Return a new QuerySet instance with NOT (args) ANDed to the existing set.
        *   **Method `_filter_or_exclude(self, negate, *args, **kwargs)`**
            *   **Implementation Logic:** Helper method for filter() and exclude().
        *   **Method `complex_filter(self, filter_obj)`**
            *   **Implementation Logic:** Return a new QuerySet instance with filter_obj added to the filters.
        *   **Method `_combinator_query(self, combinator, *other_qs, all=False)`**
            *   **Implementation Logic:** Helper method for union(), intersection(), and difference().
        *   **Method `union(self, *other_qs, all=False)`**
            *   **Implementation Logic:** Returns a new QuerySet representing the union of this QuerySet with others.
        *   **Method `intersection(self, *other_qs)`**
            *   **Implementation Logic:** Returns a new QuerySet representing the intersection of this QuerySet with others.
        *   **Method `difference(self, *other_qs)`**
            *   **Implementation Logic:** Returns a new QuerySet representing the difference of this QuerySet with others.
        *   **Method `select_for_update(self, nowait=False, skip_locked=False, of=())`**
            *   **Implementation Logic:** Return a new QuerySet instance that will select objects with a FOR UPDATE lock.
        *   **Method `select_related(self, *fields)`**
            *   **Implementation Logic:** Return a new QuerySet instance that will select related objects via JOINs.
        *   **Method `prefetch_related(self, *lookups)`**
            *   **Implementation Logic:** Return a new QuerySet instance that will prefetch the specified related objects in separate queries.
        *   **Method `annotate(self, *args, **kwargs)`**
            *   **Implementation Logic:** Return a query set in which the returned objects have been annotated with extra data or aggregations.
        *   **Method `order_by(self, *field_names)`**
            *   **Implementation Logic:** Return a new QuerySet instance with the ordering changed.
        *   **Method `distinct(self, *field_names)`**
            *   **Implementation Logic:** Return a new QuerySet instance that will select only distinct results.
        *   **Method `extra(self, select=None, where=None, params=None, tables=None, order_by=None, select_params=None)`**
            *   **Implementation Logic:** Add extra SQL fragments to the query.
        *   **Method `reverse(self)`**
            *   **Implementation Logic:** Reverse the ordering of the QuerySet.
        *   **Method `defer(self, *fields)`**
            *   **Implementation Logic:** Defer the loading of data for certain fields until they are accessed.
        *   **Method `only(self, *fields)`**
            *   **Implementation Logic:** Essentially, the opposite of defer(). Only the fields passed into this method will be loaded immediately.
        *   **Method `using(self, alias)`**
            *   **Implementation Logic:** Select which database this QuerySet should execute against.
        *   **Method `ordered(self)`**
            *   **Implementation Logic:** Return True if the QuerySet is ordered -- i.e. has an order_by() clause or a default ordering.
        *   **Method `db(self)`**
            *   **Implementation Logic:** Return the database used if this query is executed now.
        *   **Method `_insert(self, objs, fields, returning_fields=None, raw=False, using=None, ignore_conflicts=False)`**
            *   **Implementation Logic:** Insert a new record for the given model.
        *   **Method `_batched_insert(self, objs, fields, batch_size, ignore_conflicts=False)`**
            *   **Implementation Logic:** Helper method for bulk_create() to insert objs one batch at a time.
        *   **Method `_chain(self, *, **kwargs)`**
            *   **Implementation Logic:** Return a copy of the current QuerySet that's ready for another operation.
        *   **Method `_clone(self)`**
            *   **Implementation Logic:** Return a copy of the current QuerySet.
        *   **Method `_fetch_all(self)`**
            *   **Implementation Logic:** Evaluates the QuerySet and populates the result cache.
        *   **Method `_next_is_sticky(self)`**
            *   **Implementation Logic:** Indicate that the next filter call and the one following that should be treated as a single filter.
        *   **Method `_merge_sanity_check(self, other)`**
            *   **Implementation Logic:** Check that two QuerySet classes may be merged.
        *   **Method `_merge_known_related_objects(self, other)`**
            *   **Implementation Logic:** Keep track of all known related objects from either QuerySet instance.
        *   **Method `resolve_expression(self, *args, **kwargs)`**
            *   **Implementation Logic:** Resolves the QuerySet as an expression.
        *   **Method `_add_hints(self, *, **hints)`**
            *   **Implementation Logic:** Update hinting information for use by routers.
        *   **Method `_has_filters(self)`**
            *   **Implementation Logic:** Check if this QuerySet has any filtering going on.
        *   **Method `_validate_values_are_expressions(values, method_name)`**
            *   **Implementation Logic:** Validates that the given values are valid expressions.
        *   **Method `_not_support_combined_queries(self, operation_name)`**
            *   **Implementation Logic:** Raises NotSupportedError if the operation is not supported on combined queries.
    *   **Class `InstanceCheckMeta`**
        *   Inherits from: type
        *   **Method `__instancecheck__(self, instance)`**
            *   **Implementation Logic:** Custom instance check for EmptyQuerySet.
    *   **Class `EmptyQuerySet`**
        *   Inherits from: , metaclass=InstanceCheckMeta
        *   **Method `__init__(self, *args, **kwargs)`**
            *   **Implementation Logic:** Raises TypeError as EmptyQuerySet cannot be instantiated.
    *   **Class `RawQuerySet`**
        *   **Method `__init__(self, raw_query, model=None, query=None, params=None, translations=None, using=None, hints=None)`**
            *   **Implementation Logic:** Initializes the RawQuerySet with a raw SQL query and parameters.
        *   **Method `resolve_model_init_order(self)`**
            *   **Implementation Logic:** Resolve the init field names and value positions.
        *   **Method `prefetch_related(self, *lookups)`**
            *   **Implementation Logic:** Same as QuerySet.prefetch_related()
        *   **Method `_prefetch_related_objects(self)`**
            *   **Implementation Logic:** Populates prefetched objects for the RawQuerySet.
        *   **Method `_clone(self)`**
            *   **Implementation Logic:** Same as QuerySet._clone()
        *   **Method `_fetch_all(self)`**
            *   **Implementation Logic:** Evaluates the RawQuerySet and populates the result cache.
        *   **Method `__len__(self)`**
            *   **Implementation Logic:** Returns the number of results.
        *   **Method `__bool__(self)`**
            *   **Implementation Logic:** Returns True if the RawQuerySet contains any results.
        *   **Method `__iter__(self)`**
            *   **Implementation Logic:** Iterates over the results of the raw query.
        *   **Method `iterator(self)`**
            *   **Implementation Logic:** Returns an iterator over the results.
        *   **Method `__repr__(self)`**
            *   **Implementation Logic:** Returns a string representation of the RawQuerySet.
        *   **Method `__getitem__(self, k)`**
            *   **Implementation Logic:** Retrieve an item or slice from the set of results.
        *   **Method `db(self)`**
            *   **Implementation Logic:** Return the database used if this query is executed now.
        *   **Method `using(self, alias)`**
            *   **Implementation Logic:** Select the database this RawQuerySet should execute against.
        *   **Method `columns(self)`**
            *   **Implementation Logic:** A list of model field names in the order they'll appear in the query results.
        *   **Method `model_fields(self)`**
            *   **Implementation Logic:** A dict mapping column names to model field names.
    *   **Class `Prefetch`**
        *   **Method `__init__(self, lookup, queryset=None, to_attr=None)`**
            *   **Implementation Logic:** Initializes a Prefetch object with a lookup, optional queryset, and optional to_attr.
        *   **Method `__getstate__(self)`**
            *   **Implementation Logic:** Returns the state for pickling.
        *   **Method `add_prefix(self, prefix)`**
            *   **Implementation Logic:** Adds a prefix to the prefetch lookup.
        *   **Method `get_current_prefetch_to(self, level)`**
            *   **Implementation Logic:** Returns the current prefetch_to path for the given level.
        *   **Method `get_current_to_attr(self, level)`**
            *   **Implementation Logic:** Returns the current to_attr for the given level.
        *   **Method `get_current_queryset(self, level)`**
            *   **Implementation Logic:** Returns the current queryset for the given level.
        *   **Method `__eq__(self, other)`**
            *   **Implementation Logic:** Checks equality with another Prefetch object.
        *   **Method `__hash__(self)`**
            *   **Implementation Logic:** Returns the hash of the Prefetch object.
    *   **Function `normalize_prefetch_lookups(lookups, prefix=None)`**
        *   **Implementation Logic:** Normalize lookups into Prefetch objects.
    *   **Function `prefetch_related_objects(model_instances, *related_lookups)`**
        *   **Implementation Logic:** Populate prefetched object caches for a list of model instances based on the given lookups.
    *   **Function `get_prefetcher(instance, through_attr, to_attr)`**
        *   **Implementation Logic:** For the attribute 'through_attr' on the given instance, find the prefetcher.
    *   **Function `prefetch_one_level(instances, prefetcher, lookup, level)`**
        *   **Implementation Logic:** Helper function for prefetch_related_objects() to prefetch a single level.
    *   **Class `RelatedPopulator`**
        *   **Method `__init__(self, klass_info, select, db)`**
            *   **Implementation Logic:** Initializes the populator with class info, select fields, and database.
        *   **Method `populate(self, row, from_obj)`**
            *   **Implementation Logic:** Populates the related object on the given from_obj using the data in the row.
    *   **Function `get_related_populators(klass_info, select, db)`**
        *   **Implementation Logic:** Returns a list of RelatedPopulator instances for the given class info.

## django/db/models/query_utils.py
This is a natural-language specification of the `django/db/models/query_utils.py` file.

## Module-Level Preamble

### Imports
*   `import copy`
*   `import functools`
*   `import inspect`
*   `from collections import namedtuple`
*   `from django.db.models.constants import LOOKUP_SEP`
*   `from django.utils import tree`

### Constants & Globals
*   `PathInfo`: A named tuple defined as `namedtuple('PathInfo', 'from_opts to_opts target_fields join_field m2m direct filtered_relation')`.

---

## Code Objects

### `InvalidQuery` (Exception)
*   **Header:** `class InvalidQuery(Exception):`
*   **Implementation Logic:** An empty exception class used to indicate that a query passed to `raw()` is not safe.

### `subclasses`
*   **Header:** `def subclasses(cls):`
*   **Implementation Logic:** A generator function that yields the provided `cls` and then recursively yields all of its subclasses by iterating over `cls.__subclasses__()` and yielding from `subclasses(subclass)`.

### `QueryWrapper`
*   **Header:** `class QueryWrapper:`
*   **Attributes:**
    *   `contains_aggregate`: Class attribute, initialized to `False`.
*   **Implementation Logic:**
    *   `__init__(self, sql, params)`: Initializes `self.data` as a tuple containing `sql` and `list(params)`.
    *   `as_sql(self, compiler=None, connection=None)`: Returns `self.data`.

### `Q`
*   **Header:** `class Q(tree.Node):`
*   **Attributes:**
    *   `AND`: Class attribute, initialized to `'AND'`.
    *   `OR`: Class attribute, initialized to `'OR'`.
    *   `default`: Class attribute, initialized to `AND`.
    *   `conditional`: Class attribute, initialized to `True`.
*   **Implementation Logic:**
    *   `__init__(self, *args, _connector=None, _negated=False, **kwargs)`: Calls `super().__init__()` with `children` set to a list containing `*args` followed by `*sorted(kwargs.items())`, `connector` set to `_connector`, and `negated` set to `_negated`.
    *   `_combine(self, other, conn)`: Combines two `Q` objects.
        *   Raises a `TypeError` with `other` if `other` is not an instance of `Q`.
        *   If `other` is empty (falsy), returns `copy.deepcopy(self)`.
        *   If `self` is empty (falsy), returns `copy.deepcopy(other)`.
        *   Otherwise, creates a new instance of `type(self)()`, sets its `connector` to `conn`, calls `add(self, conn)` and `add(other, conn)` on the new object, and returns it.
    *   `__or__(self, other)`: Returns `self._combine(other, self.OR)`.
    *   `__and__(self, other)`: Returns `self._combine(other, self.AND)`.
    *   `__invert__(self)`: Creates a new instance of `type(self)()`, calls `add(self, self.AND)` on it, calls `negate()` on it, and returns it.
    *   `resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False)`: Calls `query._add_q(self, reuse, allow_joins=allow_joins, split_subq=False)` to get `clause` and `joins`. Calls `query.promote_joins(joins)` and returns `clause`.
    *   `deconstruct(self)`: Returns a tuple `(path, args, kwargs)`.
        *   `path` is constructed as `f"{self.__class__.__module__}.{self.__class__.__name__}"`. If it starts with `'django.db.models.query_utils'`, it is replaced with `'django.db.models'`.
        *   `args` defaults to `()`, `kwargs` defaults to `{}`.
        *   If `self.children` has exactly one element and it is not a `Q` instance, `kwargs` is set to `{child[0]: child[1]}` (where `child` is `self.children[0]`).
        *   Otherwise, `args` is set to `tuple(self.children)`. If `self.connector` is not `self.default`, `kwargs` gets `'_connector': self.connector`.
        *   If `self.negated` is true, `kwargs['_negated'] = True` is added.

### `DeferredAttribute`
*   **Header:** `class DeferredAttribute:`
*   **Implementation Logic:**
    *   `__init__(self, field)`: Sets `self.field = field`.
    *   `__get__(self, instance, cls=None)`:
        *   If `instance` is `None`, returns `self`.
        *   Gets `data = instance.__dict__` and `field_name = self.field.attname`.
        *   If `data.get(field_name, self)` is `self`, it attempts to fetch the value. It calls `self._check_parent_chain(instance)`. If that returns `None`, it calls `instance.refresh_from_db(fields=[field_name])` and gets the value via `getattr(instance, field_name)`. It then stores the value in `data[field_name]`.
        *   Returns `data[field_name]`.
    *   `_check_parent_chain(self, instance)`: Gets `opts = instance._meta` and `link_field = opts.get_ancestor_link(self.field.model)`. If `self.field.primary_key` is true and `self.field != link_field`, returns `getattr(instance, link_field.attname)`. Otherwise, returns `None`.

### `RegisterLookupMixin`
*   **Header:** `class RegisterLookupMixin:`
*   **Implementation Logic:**
    *   `_get_lookup(cls, lookup_name)` (classmethod): Returns `cls.get_lookups().get(lookup_name, None)`.
    *   `get_lookups(cls)` (classmethod, decorated with `@functools.lru_cache(maxsize=None)`): Collects the `'class_lookups'` dictionary from the `__dict__` of every parent class in `inspect.getmro(cls)` (defaulting to `{}` if not present). Returns `cls.merge_dicts(class_lookups)`.
    *   `get_lookup(self, lookup_name)`: Imports `Lookup` from `django.db.models.lookups`. Gets `found = self._get_lookup(lookup_name)`. If `found` is `None` and `self` has an `output_field` attribute, returns `self.output_field.get_lookup(lookup_name)`. If `found` is not `None` and is not a subclass of `Lookup`, returns `None`. Otherwise, returns `found`.
    *   `get_transform(self, lookup_name)`: Imports `Transform` from `django.db.models.lookups`. Gets `found = self._get_lookup(lookup_name)`. If `found` is `None` and `self` has an `output_field` attribute, returns `self.output_field.get_transform(lookup_name)`. If `found` is not `None` and is not a subclass of `Transform`, returns `None`. Otherwise, returns `found`.
    *   `merge_dicts(dicts)` (staticmethod): Iterates over `dicts` in reverse order, updating a new dictionary `merged` with each. Returns `merged`.
    *   `_clear_cached_lookups(cls)` (classmethod): Iterates over `subclasses(cls)` and calls `cache_clear()` on their `get_lookups` method.
    *   `register_lookup(cls, lookup, lookup_name=None)` (classmethod): If `lookup_name` is `None`, defaults to `lookup.lookup_name`. If `'class_lookups'` is not in `cls.__dict__`, initializes `cls.class_lookups = {}`. Sets `cls.class_lookups[lookup_name] = lookup`. Calls `cls._clear_cached_lookups()` and returns `lookup`.
    *   `_unregister_lookup(cls, lookup, lookup_name=None)` (classmethod): If `lookup_name` is `None`, defaults to `lookup.lookup_name`. Deletes `cls.class_lookups[lookup_name]`.

### `select_related_descend`
*   **Header:** `def select_related_descend(field, restricted, requested, load_fields, reverse=False):`
*   **Implementation Logic:**
    *   Returns `False` if `not field.remote_field`.
    *   Returns `False` if `field.remote_field.parent_link` is true and `reverse` is false.
    *   If `restricted` is true: returns `False` if `reverse` is true and `field.related_query_name() not in requested`, or if `reverse` is false and `field.name not in requested`.
    *   Returns `False` if `restricted` is false and `field.null` is true.
    *   If `load_fields` is truthy: if `field.attname not in load_fields`, and if `restricted` is true and `field.name in requested`, raises an `InvalidQuery` exception with a formatted message.
    *   Returns `True` if none of the above conditions are met.

### `refs_expression`
*   **Header:** `def refs_expression(lookup_parts, annotations):`
*   **Implementation Logic:** Iterates `n` from 1 to `len(lookup_parts)`. For each `n`, joins `lookup_parts[0:n]` using `LOOKUP_SEP` to form `level_n_lookup`. If `level_n_lookup` is in `annotations` and `annotations[level_n_lookup]` is truthy, returns a tuple `(annotations[level_n_lookup], lookup_parts[n:])`. If the loop completes without returning, returns `(False, ())`.

### `check_rel_lookup_compatibility`
*   **Header:** `def check_rel_lookup_compatibility(model, target_opts, field):`
*   **Implementation Logic:**
    *   Defines an inner function `check(opts)` that returns `True` if `model._meta.concrete_model == opts.concrete_model`, or `opts.concrete_model in model._meta.get_parent_list()`, or `model in opts.get_parent_list()`.
    *   Returns `True` if `check(target_opts)` is true, or if `getattr(field, 'primary_key', False)` is true and `check(field.model._meta)` is true. Otherwise, returns `False`.

### `FilteredRelation`
*   **Header:** `class FilteredRelation:`
*   **Implementation Logic:**
    *   `__init__(self, relation_name, *, condition=Q())`: Raises `ValueError` if `relation_name` is empty. Sets `self.relation_name = relation_name` and `self.alias = None`. Raises `ValueError` if `condition` is not an instance of `Q`. Sets `self.condition = condition` and `self.path = []`.
    *   `__eq__(self, other)`: Returns `True` if `other` is an instance of `self.__class__` and `self.relation_name == other.relation_name`, `self.alias == other.alias`, and `self.condition == other.condition`.
    *   `clone(self)`: Creates a new `FilteredRelation` with `self.relation_name` and `condition=self.condition`. Copies `self.alias` and `self.path[:]` to the new instance and returns it.
    *   `resolve_expression(self, *args, **kwargs)`: Raises `NotImplementedError('FilteredRelation.resolve_expression() is unused.')`.
    *   `as_sql(self, compiler, connection)`: Gets `query = compiler.query`. Calls `query.build_filtered_relation_q(self.condition, reuse=set(self.path))` to get `where`. Returns `compiler.compile(where)`.

## django/template/context.py
### 1. Module-Level Preamble

**Imports:**
*   `from contextlib import contextmanager`
*   `from copy import copy`

**Constants & Globals:**
*   `_builtin_context_processors`: `('django.template.context_processors.csrf',)`

---

### 2. Code Objects (Classes and Functions)

#### `ContextPopException`
*   **Header:** `class ContextPopException(Exception):`
*   **Implementation Logic:** An empty exception class (contains only `pass`).

#### `ContextDict`
*   **Header:** `class ContextDict(dict):`
*   **Attributes:**
    *   `context`: The context object passed during initialization.
*   **Implementation Logic:**
    *   `__init__(self, context, *args, **kwargs)`: Calls `super().__init__(*args, **kwargs)`. Appends `self` to `context.dicts` and sets `self.context = context`.
    *   `__enter__(self)`: Returns `self`.
    *   `__exit__(self, *args, **kwargs)`: Calls `self.context.pop()`.

#### `BaseContext`
*   **Header:** `class BaseContext:`
*   **Attributes:**
    *   `dicts`: A list of dictionaries representing the context stack.
*   **Implementation Logic:**
    *   `__init__(self, dict_=None)`: Calls `self._reset_dicts(dict_)`.
    *   `_reset_dicts(self, value=None)`: Initializes `self.dicts` with a single dictionary containing built-ins: `{'True': True, 'False': False, 'None': None}`. If `value` is not `None`, appends `value` to `self.dicts`.
    *   `__copy__(self)`: Creates a duplicate using `copy(super())`. Sets `duplicate.dicts` to a shallow copy of `self.dicts` (`self.dicts[:]`). Returns the duplicate.
    *   `__repr__(self)`: Returns `repr(self.dicts)`.
    *   `__iter__(self)`: Returns an iterator over `self.dicts` in reverse order (`reversed(self.dicts)`).
    *   `push(self, *args, **kwargs)`: Initializes an empty list `dicts`. Iterates over `args`: if an argument is an instance of `BaseContext`, it extends `dicts` with the argument's `dicts[1:]`; otherwise, it appends the argument to `dicts`. Returns `ContextDict(self, *dicts, **kwargs)`.
    *   `pop(self)`: If `len(self.dicts) == 1`, raises `ContextPopException`. Otherwise, removes and returns the last item from `self.dicts` using `self.dicts.pop()`.
    *   `__setitem__(self, key, value)`: Sets `key` to `value` in the top-most dictionary (`self.dicts[-1]`).
    *   `set_upward(self, key, value)`: Iterates over `self.dicts` in reverse. If `key` is found in a dictionary, it updates that dictionary with `value` and breaks. If not found in any, it sets `key` to `value` in the top-most dictionary (`self.dicts[-1]`).
    *   `__getitem__(self, key)`: Iterates over `self.dicts` in reverse. Returns the value from the first dictionary containing `key`. If not found, raises `KeyError(key)`.
    *   `__delitem__(self, key)`: Deletes `key` from the top-most dictionary (`self.dicts[-1]`).
    *   `__contains__(self, key)`: Returns `True` if `key` exists in any dictionary within `self.dicts`, otherwise `False`.
    *   `get(self, key, otherwise=None)`: Iterates over `self.dicts` in reverse. Returns the value from the first dictionary containing `key`. If not found, returns `otherwise`.
    *   `setdefault(self, key, default=None)`: Attempts to return `self[key]`. If a `KeyError` is caught, sets `self[key] = default` and returns `default`.
    *   `new(self, values=None)`: Creates a shallow copy of `self` using `copy(self)`. Calls `_reset_dicts(values)` on the new context and returns it.
    *   `flatten(self)`: Returns a single dictionary containing all key-value pairs from all dictionaries in `self.dicts`, updated in order (so later dictionaries override earlier ones).
    *   `__eq__(self, other)`: Returns `True` if `other` is an instance of `BaseContext` and `self.flatten() == other.flatten()`. Otherwise, returns `False`.

#### `Context`
*   **Header:** `class Context(BaseContext):`
*   **Attributes:**
    *   `autoescape`: Boolean.
    *   `use_l10n`: Boolean or `None`.
    *   `use_tz`: Boolean or `None`.
    *   `template_name`: String, initialized to `"unknown"`.
    *   `render_context`: Instance of `RenderContext`.
    *   `template`: Initialized to `None`.
*   **Implementation Logic:**
    *   `__init__(self, dict_=None, autoescape=True, use_l10n=None, use_tz=None)`: Sets `self.autoescape`, `self.use_l10n`, and `self.use_tz` to the provided arguments. Sets `self.template_name = "unknown"`, `self.render_context = RenderContext()`, and `self.template = None`. Calls `super().__init__(dict_)`.
    *   `bind_template(self, template)`: Decorated with `@contextmanager`. If `self.template` is not `None`, raises `RuntimeError("Context is already bound to a template")`. Sets `self.template = template`. Yields control. In a `finally` block, resets `self.template = None`.
    *   `__copy__(self)`: Calls `super().__copy__()`. Sets `duplicate.render_context = copy(self.render_context)`. Returns the duplicate.
    *   `update(self, other_dict)`: If `other_dict` lacks a `__getitem__` attribute, raises `TypeError('other_dict must be a mapping (dictionary-like) object.')`. If `other_dict` is an instance of `BaseContext`, reassigns `other_dict` to `other_dict.dicts[1:].pop()`. Returns `ContextDict(self, other_dict)`.

#### `RenderContext`
*   **Header:** `class RenderContext(BaseContext):`
*   **Attributes:**
    *   `template`: Class attribute, initialized to `None`.
*   **Implementation Logic:**
    *   `__iter__(self)`: Yields from the top-most dictionary (`self.dicts[-1]`).
    *   `__contains__(self, key)`: Returns `key in self.dicts[-1]`.
    *   `get(self, key, otherwise=None)`: Returns `self.dicts[-1].get(key, otherwise)`.
    *   `__getitem__(self, key)`: Returns `self.dicts[-1][key]`.
    *   `push_state(self, template, isolated_context=True)`: Decorated with `@contextmanager`. Saves `self.template` to a local variable `initial`. Sets `self.template = template`. If `isolated_context` is true, calls `self.push()`. Yields control. In a `finally` block, restores `self.template = initial` and, if `isolated_context` is true, calls `self.pop()`.

#### `RequestContext`
*   **Header:** `class RequestContext(Context):`
*   **Attributes:**
    *   `request`: The request object.
    *   `_processors`: Tuple of callables.
    *   `_processors_index`: Integer index tracking where processor outputs are stored.
*   **Implementation Logic:**
    *   `__init__(self, request, dict_=None, processors=None, use_l10n=None, use_tz=None, autoescape=True)`: Calls `super().__init__(dict_, use_l10n=use_l10n, use_tz=use_tz, autoescape=autoescape)`. Sets `self.request = request`. Sets `self._processors` to `tuple(processors)` if `processors` is not `None`, else `()`. Sets `self._processors_index = len(self.dicts)`. Calls `self.update({})` twice (first as a placeholder for context processors output, second for new modifications).
    *   `bind_template(self, template)`: Decorated with `@contextmanager`. If `self.template` is not `None`, raises `RuntimeError("Context is already bound to a template")`. Sets `self.template = template`. Combines `template.engine.template_context_processors` and `self._processors` into a single iterable. Iterates over these processors, calling each with `self.request` and updating a local `updates` dictionary with their results. Sets `self.dicts[self._processors_index] = updates`. Yields control. In a `finally` block, resets `self.template = None` and clears the processor outputs by setting `self.dicts[self._processors_index] = {}`.
    *   `new(self, values=None)`: Calls `super().new(values)`. If the returned new context has a `_processors_index` attribute, deletes it. Returns the new context.

#### `make_context`
*   **Header:** `def make_context(context, request=None, **kwargs):`
*   **Implementation Logic:**
    *   If `context` is not `None` and is not an instance of `dict`, raises `TypeError('context must be a dict rather than %s.' % context.__class__.__name__)`.
    *   If `request` is `None`, returns `Context(context, **kwargs)`.
    *   Otherwise, saves `context` to `original_context` and creates a new context via `RequestContext(request, **kwargs)`. If `original_context` is truthy, calls `push(original_context)` on the new context. Returns the new context.