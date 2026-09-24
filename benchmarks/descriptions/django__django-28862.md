## django/db/migrations/operations/models.py
```markdown
# Specification for `django/db/migrations/operations/models.py`

## 1. Module-Level Preamble

### Imports
```python
from django.db import models
from django.db.migrations.operations.base import Operation
from django.db.migrations.state import ModelState
from django.db.models.options import normalize_together
from django.utils.functional import cached_property

from .fields import (
    AddField, AlterField, FieldOperation, RemoveField, RenameField,
)
from .utils import ModelTuple, field_references_model
```

### Constants & Globals
There are no module-level constants or globals defined outside of classes.

## 2. Code Objects (Classes and Functions)

### `_check_for_duplicates(arg_name, objs)`
*   **Signature:** `def _check_for_duplicates(arg_name, objs):`
*   **Implementation Logic:**
    *   Initializes an empty set `used_vals`.
    *   Iterates over `objs`.
    *   If a value is already in `used_vals`, raises a `ValueError` with the message `"Found duplicate value %s in CreateModel %s argument." % (val, arg_name)`.
    *   Otherwise, adds the value to `used_vals`.

### `ModelOperation(Operation)`
*   **Base Classes:** `Operation`
*   **Methods:**
    *   `__init__(self, name)`: Sets `self.name = name`.
    *   `name_lower(self)`: Decorated with `@cached_property`. Returns `self.name.lower()`.
    *   `references_model(self, name, app_label=None)`: Returns `True` if `name.lower() == self.name_lower`, else `False`.
    *   `reduce(self, operation, app_label=None)`: Returns `super().reduce(operation, app_label=app_label) or not operation.references_model(self.name, app_label)`.

### `CreateModel(ModelOperation)`
*   **Base Classes:** `ModelOperation`
*   **Class Attributes:**
    *   `serialization_expand_args`: `['fields', 'options', 'managers']`
*   **Methods:**
    *   `__init__(self, name, fields, options=None, bases=None, managers=None)`:
        *   Sets `self.fields = fields`.
        *   Sets `self.options = options or {}`.
        *   Sets `self.bases = bases or (models.Model,)`.
        *   Sets `self.managers = managers or []`.
        *   Calls `super().__init__(name)`.
        *   Calls `_check_for_duplicates` on `fields` (extracting the name from each tuple), `bases` (extracting `_meta.label_lower` if it has `_meta`, else lowercasing if it's a string), and `managers` (extracting the name).
    *   `deconstruct(self)`:
        *   Returns a tuple `(self.__class__.__qualname__, [], kwargs)`.
        *   `kwargs` always contains `'name': self.name` and `'fields': self.fields`.
        *   Adds `'options': self.options` if `self.options` is truthy.
        *   Adds `'bases': self.bases` if `self.bases` is truthy and not `(models.Model,)`.
        *   Adds `'managers': self.managers` if `self.managers` is truthy and not `[('objects', models.Manager())]`.
    *   `state_forwards(self, app_label, state)`:
        *   Calls `state.add_model` with a new `ModelState` instantiated with `app_label`, `self.name`, `list(self.fields)`, `dict(self.options)`, `tuple(self.bases)`, and `list(self.managers)`.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`:
        *   Gets the model from `to_state.apps.get_model(app_label, self.name)`.
        *   If `self.allow_migrate_model(schema_editor.connection.alias, model)` is true, calls `schema_editor.create_model(model)`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`:
        *   Gets the model from `from_state.apps.get_model(app_label, self.name)`.
        *   If `self.allow_migrate_model(schema_editor.connection.alias, model)` is true, calls `schema_editor.delete_model(model)`.
    *   `describe(self)`:
        *   Returns `"Create proxy model %s" % self.name` if `self.options.get("proxy", False)` is true, else `"Create model %s" % self.name`.
    *   `references_model(self, name, app_label=None)`:
        *   Returns `True` if `name.lower() == self.name_lower`.
        *   Creates `model_tuple = ModelTuple(app_label, name.lower())`.
        *   Iterates over `self.bases`. If a base is not `models.Model`, is an instance of `(models.base.ModelBase, str)`, and `ModelTuple.from_model(base) == model_tuple`, returns `True`.
        *   Iterates over `self.fields`. If `field_references_model(field, model_tuple)` is true, returns `True`.
        *   Returns `False`.
    *   `reduce(self, operation, app_label=None)`:
        *   If `operation` is `DeleteModel`, `self.name_lower == operation.name_lower`, and not a proxy model, returns `[]`.
        *   If `operation` is `RenameModel` and `self.name_lower == operation.old_name_lower`, returns a list with a new `CreateModel` using `operation.new_name` and the current fields, options, bases, and managers.
        *   If `operation` is `AlterModelOptions` and `self.name_lower == operation.name_lower`, returns a list with a new `CreateModel` merging `self.options` and `operation.options`.
        *   If `operation` is a `FieldOperation` and `self.name_lower == operation.model_name_lower`:
            *   If `AddField`: returns a new `CreateModel` with the field appended to `self.fields`.
            *   If `AlterField`: returns a new `CreateModel` with the specific field replaced.
            *   If `RemoveField`: returns a new `CreateModel` with the specific field removed.
            *   If `RenameField`: returns a new `CreateModel` with the specific field renamed.
        *   Otherwise, returns `super().reduce(operation, app_label=app_label)`.

### `DeleteModel(ModelOperation)`
*   **Base Classes:** `ModelOperation`
*   **Methods:**
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name})`.
    *   `state_forwards(self, app_label, state)`: Calls `state.remove_model(app_label, self.name_lower)`.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets the model from `from_state`. If allowed to migrate, calls `schema_editor.delete_model(model)`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Gets the model from `to_state`. If allowed to migrate, calls `schema_editor.create_model(model)`.
    *   `references_model(self, name, app_label=None)`: Always returns `True`.
    *   `describe(self)`: Returns `"Delete model %s" % self.name`.

### `RenameModel(ModelOperation)`
*   **Base Classes:** `ModelOperation`
*   **Methods:**
    *   `__init__(self, old_name, new_name)`: Sets `self.old_name = old_name`, `self.new_name = new_name`, and calls `super().__init__(old_name)`.
    *   `old_name_lower(self)`: Decorated with `@cached_property`. Returns `self.old_name.lower()`.
    *   `new_name_lower(self)`: Decorated with `@cached_property`. Returns `self.new_name.lower()`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'old_name': self.old_name, 'new_name': self.new_name})`.
    *   `state_forwards(self, app_label, state)`:
        *   Clones the old model state, renames it to `self.new_name`, and adds it to `state.models`.
        *   Iterates over all models in `state.models` to repoint any fields (including `remote_field.model` and `remote_field.through`) pointing to the old model to the new model.
        *   Reloads models related to the old model (`state.reload_models(to_reload, delay=True)`).
        *   Removes the old model from `state`.
        *   Reloads the new model (`state.reload_model(app_label, self.new_name_lower, delay=True)`).
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`:
        *   Gets `new_model` from `to_state`.
        *   If allowed to migrate:
            *   Gets `old_model` from `from_state`.
            *   Calls `schema_editor.alter_db_table` to rename the main table.
            *   Alters fields pointing to the model by iterating over `old_model._meta.related_objects` and calling `schema_editor.alter_field`.
            *   Renames M2M fields whose name is based on this model's name by iterating over `old_model._meta.local_many_to_many` and `new_model._meta.local_many_to_many`, calling `schema_editor.alter_db_table` and `schema_editor.alter_field` for auto-created through models.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`:
        *   Swaps `self.new_name_lower` with `self.old_name_lower` and `self.new_name` with `self.old_name`.
        *   Calls `self.database_forwards(app_label, schema_editor, from_state, to_state)`.
        *   Swaps them back.
    *   `references_model(self, name, app_label=None)`: Returns `True` if `name.lower()` matches `self.old_name_lower` or `self.new_name_lower`.
    *   `describe(self)`: Returns `"Rename model %s to %s" % (self.old_name, self.new_name)`.
    *   `reduce(self, operation, app_label=None)`:
        *   If `operation` is `RenameModel` and `self.new_name_lower == operation.old_name_lower`, returns `[RenameModel(self.old_name, operation.new_name)]`.
        *   Otherwise, returns `super(ModelOperation, self).reduce(operation, app_label=app_label) or not operation.references_model(self.new_name, app_label)`.

### `AlterModelTable(ModelOperation)`
*   **Base Classes:** `ModelOperation`
*   **Methods:**
    *   `__init__(self, name, table)`: Sets `self.table = table` and calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name, 'table': self.table})`.
    *   `state_forwards(self, app_label, state)`: Sets `state.models[app_label, self.name_lower].options["db_table"] = self.table` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`:
        *   Gets `new_model` from `to_state`.
        *   If allowed to migrate, gets `old_model` from `from_state`, calls `schema_editor.alter_db_table` for the main table, and iterates over `local_many_to_many` to call `schema_editor.alter_db_table` for auto-created through models.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Returns `self.database_forwards(app_label, schema_editor, from_state, to_state)`.
    *   `describe(self)`: Returns `"Rename table for %s to %s" % (self.name, self.table if self.table is not None else "(default)")`.
    *   `reduce(self, operation, app_label=None)`: If `operation` is `AlterModelTable` or `DeleteModel` and `self.name_lower == operation.name_lower`, returns `[operation]`. Otherwise, returns `super().reduce(operation, app_label=app_label)`.

### `ModelOptionOperation(ModelOperation)`
*   **Base Classes:** `ModelOperation`
*   **Methods:**
    *   `reduce(self, operation, app_label=None)`: If `operation` is of the same class or `DeleteModel` and `self.name_lower == operation.name_lower`, returns `[operation]`. Otherwise, returns `super().reduce(operation, app_label=app_label)`.

### `FieldRelatedOptionOperation(ModelOptionOperation)`
*   **Base Classes:** `ModelOptionOperation`
*   **Methods:**
    *   `reduce(self, operation, app_label=None)`: If `operation` is a `FieldOperation`, `self.name_lower == operation.model_name_lower`, and `not self.references_field(operation.model_name, operation.name)`, returns `[operation, self]`. Otherwise, returns `super().reduce(operation, app_label=app_label)`.

### `AlterUniqueTogether(FieldRelatedOptionOperation)`
*   **Base Classes:** `FieldRelatedOptionOperation`
*   **Class Attributes:**
    *   `option_name`: `"unique_together"`
*   **Methods:**
    *   `__init__(self, name, unique_together)`: Normalizes `unique_together` using `normalize_together`, sets `self.unique_together = {tuple(cons) for cons in unique_together}`, and calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name, 'unique_together': self.unique_together})`.
    *   `state_forwards(self, app_label, state)`: Sets `model_state.options[self.option_name] = self.unique_together` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets `new_model`. If allowed to migrate, gets `old_model` and calls `schema_editor.alter_unique_together(new_model, getattr(old_model._meta, self.option_name, set()), getattr(new_model._meta, self.option_name, set()))`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Returns `self.database_forwards(app_label, schema_editor, from_state, to_state)`.
    *   `references_field(self, model_name, name, app_label=None)`: Returns `True` if it references the model and either `self.unique_together` is empty or `name` is in any of the tuples in `self.unique_together`.
    *   `describe(self)`: Returns `"Alter %s for %s (%s constraint(s))" % (self.option_name, self.name, len(self.unique_together or ''))`.

### `AlterIndexTogether(FieldRelatedOptionOperation)`
*   **Base Classes:** `FieldRelatedOptionOperation`
*   **Class Attributes:**
    *   `option_name`: `"index_together"`
*   **Methods:**
    *   Identical logic to `AlterUniqueTogether`, but operates on `index_together` instead of `unique_together`.

### `AlterOrderWithRespectTo(FieldRelatedOptionOperation)`
*   **Base Classes:** `FieldRelatedOptionOperation`
*   **Methods:**
    *   `__init__(self, name, order_with_respect_to)`: Sets `self.order_with_respect_to = order_with_respect_to` and calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name, 'order_with_respect_to': self.order_with_respect_to})`.
    *   `state_forwards(self, app_label, state)`: Sets `model_state.options['order_with_respect_to'] = self.order_with_respect_to` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets `to_model`. If allowed to migrate, gets `from_model`. If `from_model` has `order_with_respect_to` and `to_model` doesn't, calls `schema_editor.remove_field` for `_order`. If `to_model` has it and `from_model` doesn't, gets the `_order` field, sets its default to `0` if it has none, and calls `schema_editor.add_field`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Calls `self.database_forwards(app_label, schema_editor, from_state, to_state)`.
    *   `references_field(self, model_name, name, app_label=None)`: Returns `True` if it references the model and either `self.order_with_respect_to` is `None` or `name == self.order_with_respect_to`.
    *   `describe(self)`: Returns `"Set order_with_respect_to on %s to %s" % (self.name, self.order_with_respect_to)`.

### `AlterModelOptions(ModelOptionOperation)`
*   **Base Classes:** `ModelOptionOperation`
*   **Class Attributes:**
    *   `ALTER_OPTION_KEYS`: `["base_manager_name", "default_manager_name", "get_latest_by", "managed", "ordering", "permissions", "default_permissions", "select_on_save", "verbose_name", "verbose_name_plural"]`
*   **Methods:**
    *   `__init__(self, name, options)`: Sets `self.options = options` and calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name, 'options': self.options})`.
    *   `state_forwards(self, app_label, state)`: Updates `model_state.options` with `self.options`. For each key in `ALTER_OPTION_KEYS`, if it's not in `self.options`, pops it from `model_state.options` with a default of `False`. Reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: `pass`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: `pass`.
    *   `describe(self)`: Returns `"Change Meta options on %s" % self.name`.

### `AlterModelManagers(ModelOptionOperation)`
*   **Base Classes:** `ModelOptionOperation`
*   **Class Attributes:**
    *   `serialization_expand_args`: `['managers']`
*   **Methods:**
    *   `__init__(self, name, managers)`: Sets `self.managers = managers` and calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [self.name, self.managers], {})`.
    *   `state_forwards(self, app_label, state)`: Sets `model_state.managers = list(self.managers)` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: `pass`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: `pass`.
    *   `describe(self)`: Returns `"Change managers on %s" % self.name`.

### `IndexOperation(Operation)`
*   **Base Classes:** `Operation`
*   **Class Attributes:**
    *   `option_name`: `'indexes'`
*   **Methods:**
    *   `model_name_lower(self)`: Decorated with `@cached_property`. Returns `self.model_name.lower()`.

### `AddIndex(IndexOperation)`
*   **Base Classes:** `IndexOperation`
*   **Methods:**
    *   `__init__(self, model_name, index)`: Sets `self.model_name = model_name`. If `not index.name`, raises a `ValueError`. Sets `self.index = index`.
    *   `state_forwards(self, app_label, state)`: Appends `self.index.clone()` to `model_state.options[self.option_name]` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets `model`. If allowed to migrate, calls `schema_editor.add_index(model, self.index)`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Gets `model`. If allowed to migrate, calls `schema_editor.remove_index(model, self.index)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'model_name': self.model_name, 'index': self.index})`.
    *   `describe(self)`: Returns `'Create index %s on field(s) %s of model %s' % (self.index.name, ', '.join(self.index.fields), self.model_name)`.

### `RemoveIndex(IndexOperation)`
*   **Base Classes:** `IndexOperation`
*   **Methods:**
    *   `__init__(self, model_name, name)`: Sets `self.model_name = model_name` and `self.name = name`.
    *   `state_forwards(self, app_label, state)`: Removes the index where `idx.name == self.name` from `model_state.options[self.option_name]` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets `model`. If allowed to migrate, gets the index via `from_model_state.get_index_by_name(self.name)` and calls `schema_editor.remove_index(model, index)`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Gets `model`. If allowed to migrate, gets the index via `to_model_state.get_index_by_name(self.name)` and calls `schema_editor.add_index(model, index)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'model_name': self.model_name, 'name': self.name})`.
    *   `describe(self)`: Returns `'Remove index %s from %s' % (self.name, self.model_name)`.

### `AddConstraint(IndexOperation)`
*   **Base Classes:** `IndexOperation`
*   **Class Attributes:**
    *   `option_name`: `'constraints'`
*   **Methods:**
    *   `__init__(self, model_name, constraint)`: Sets `self.model_name = model_name` and `self.constraint = constraint`.
    *   `state_forwards(self, app_label, state)`: Appends `self.constraint` to `model_state.options[self.option_name]`.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets `model`. If allowed to migrate, calls `schema_editor.add_constraint(model, self.constraint)`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Gets `model`. If allowed to migrate, calls `schema_editor.remove_constraint(model, self.constraint)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__name__, [], {'model_name': self.model_name, 'constraint': self.constraint})`.
    *   `describe(self)`: Returns `'Create constraint %s on model %s' % (self.constraint.name, self.model_name)`.

### `RemoveConstraint(IndexOperation)`
*   **Base Classes:** `IndexOperation`
*   **Class Attributes:**
    *   `option_name`: `'constraints'`
*   **Methods:**
    *   `__init__(self, model_name, name)`: Sets `self.model_name = model_name` and `self.name = name`.
    *   `state_forwards(self, app_label, state)`: Removes the constraint where `c.name == self.name` from `model_state.options[self.option_name]`.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets `model`. If allowed to migrate, gets the constraint via `from_model_state.get_constraint_by_name(self.name)` and calls `schema_editor.remove_constraint(model, constraint)`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Gets `model`. If allowed to migrate, gets the constraint via `to_model_state.get_constraint_by_name(self.name)` and calls `schema_editor.add_constraint(model, constraint)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__name__, [], {'model_name': self.model_name, 'name': self.name})`.
    *   `describe(self)`: Returns `'Remove constraint %s from model %s' % (self.name, self.model_name)`.
```