## django/db/migrations/operations/models.py
# Specification for `django/db/migrations/operations/models.py`

## 1. Module-Level Preamble

### Imports
*   `from django.db import models`
*   `from django.db.migrations.operations.base import Operation`
*   `from django.db.migrations.state import ModelState`
*   `from django.db.models.options import normalize_together`
*   `from django.utils.functional import cached_property`
*   `from .fields import AddField, AlterField, FieldOperation, RemoveField, RenameField`
*   `from .utils import ModelTuple, field_references_model`

### Constants & Globals
None.

## 2. Code Objects

### `_check_for_duplicates(arg_name, objs)`
*   **Signature:** `def _check_for_duplicates(arg_name, objs)`
*   **Implementation Logic:**
    *   Iterates through `objs`.
    *   Maintains a `set` of seen values.
    *   If a value is already in the set, raises a `ValueError` with the message `"Found duplicate value %s in CreateModel %s argument." % (val, arg_name)`.
    *   Otherwise, adds the value to the set.

### `ModelOperation(Operation)`
*   **Signature:** `class ModelOperation(Operation)`
*   **Implementation Logic:**
    *   `__init__(self, name)`: Sets `self.name = name`.
    *   `name_lower(self)`: A `@cached_property` returning `self.name.lower()`.
    *   `references_model(self, name, app_label=None)`: Returns `True` if `name.lower() == self.name_lower`, else `False`.
    *   `reduce(self, operation, app_label=None)`: Returns `super().reduce(operation, app_label=app_label) or not operation.references_model(self.name, app_label)`.

### `CreateModel(ModelOperation)`
*   **Signature:** `class CreateModel(ModelOperation)`
*   **Attributes:** `serialization_expand_args = ['fields', 'options', 'managers']`
*   **Implementation Logic:**
    *   `__init__(self, name, fields, options=None, bases=None, managers=None)`:
        *   Sets `self.fields = fields`.
        *   Sets `self.options = options or {}`.
        *   Sets `self.bases = bases or (models.Model,)`.
        *   Sets `self.managers = managers or []`.
        *   Calls `super().__init__(name)`.
        *   Calls `_check_for_duplicates` on `fields` (extracting the name from each tuple), `bases` (extracting `_meta.label_lower` if it has `_meta`, else `lower()` if it's a string, else the base itself), and `managers` (extracting the name from each tuple).
    *   `deconstruct(self)`: Returns a tuple `(self.__class__.__qualname__, [], kwargs)` where `kwargs` contains `name` and `fields`. It conditionally includes `options` (if truthy), `bases` (if truthy and not `(models.Model,)`), and `managers` (if truthy and not `[('objects', models.Manager())]`).
    *   `state_forwards(self, app_label, state)`: Adds a new `ModelState` to `state` using `app_label`, `self.name`, `list(self.fields)`, `dict(self.options)`, `tuple(self.bases)`, and `list(self.managers)`.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets the model from `to_state`. If `self.allow_migrate_model` returns true, calls `schema_editor.create_model(model)`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Gets the model from `from_state`. If `self.allow_migrate_model` returns true, calls `schema_editor.delete_model(model)`.
    *   `describe(self)`: Returns `"Create proxy model %s"` if `self.options.get("proxy", False)` is true, else `"Create model %s"`.
    *   `references_model(self, name, app_label=None)`: Returns `True` if `name.lower() == self.name_lower`. Checks if any base in `self.bases` (that is not `models.Model` and is an instance of `models.base.ModelBase` or `str`) matches `ModelTuple(app_label, name.lower())`. Checks if any field in `self.fields` references the model using `field_references_model`. Returns `False` otherwise.
    *   `reduce(self, operation, app_label=None)`:
        *   If `operation` is `DeleteModel`, `self.name_lower == operation.name_lower`, and not a proxy model, returns `[]`.
        *   If `operation` is `RenameModel` and `self.name_lower == operation.old_name_lower`, returns a new `CreateModel` with the new name.
        *   If `operation` is `AlterModelOptions` and `self.name_lower == operation.name_lower`, returns a new `CreateModel` with merged options.
        *   If `operation` is a `FieldOperation` and `self.name_lower == operation.model_name_lower`:
            *   If `AddField`: returns `CreateModel` with the field appended.
            *   If `AlterField`: returns `CreateModel` with the field replaced.
            *   If `RemoveField`: returns `CreateModel` with the field removed.
            *   If `RenameField`: returns `CreateModel` with the field renamed.
        *   Otherwise, returns `super().reduce(operation, app_label=app_label)`.

### `DeleteModel(ModelOperation)`
*   **Signature:** `class DeleteModel(ModelOperation)`
*   **Implementation Logic:**
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name})`.
    *   `state_forwards(self, app_label, state)`: Calls `state.remove_model(app_label, self.name_lower)`.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets the model from `from_state`. If allowed to migrate, calls `schema_editor.delete_model(model)`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Gets the model from `to_state`. If allowed to migrate, calls `schema_editor.create_model(model)`.
    *   `references_model(self, name, app_label=None)`: Always returns `True`.
    *   `describe(self)`: Returns `"Delete model %s" % self.name`.

### `RenameModel(ModelOperation)`
*   **Signature:** `class RenameModel(ModelOperation)`
*   **Implementation Logic:**
    *   `__init__(self, old_name, new_name)`: Sets `self.old_name` and `self.new_name`, then calls `super().__init__(old_name)`.
    *   `old_name_lower(self)` and `new_name_lower(self)`: `@cached_property` returning the lowercased names.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'old_name': self.old_name, 'new_name': self.new_name})`.
    *   `state_forwards(self, app_label, state)`: Clones the old model state, changes its name, and adds it to `state.models` under the new name. Iterates through all models in `state` to repoint any fields (including `remote_field.model` and `remote_field.through`) that referenced the old model to the new model. Reloads affected models, removes the old model, and reloads the new model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets new and old models. Alters the DB table name. Alters fields pointing to the model. Renames M2M tables and columns based on the model's name.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Swaps old and new names, calls `database_forwards`, then swaps them back.
    *   `references_model(self, name, app_label=None)`: Returns `True` if `name.lower()` matches `self.old_name_lower` or `self.new_name_lower`.
    *   `describe(self)`: Returns `"Rename model %s to %s" % (self.old_name, self.new_name)`.
    *   `reduce(self, operation, app_label=None)`: If `operation` is `RenameModel` and `self.new_name_lower == operation.old_name_lower`, returns a single `RenameModel` from `self.old_name` to `operation.new_name`. Otherwise, returns `super(ModelOperation, self).reduce(...) or not operation.references_model(self.new_name, app_label)`.

### `AlterModelTable(ModelOperation)`
*   **Signature:** `class AlterModelTable(ModelOperation)`
*   **Implementation Logic:**
    *   `__init__(self, name, table)`: Sets `self.table = table`, calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name, 'table': self.table})`.
    *   `state_forwards(self, app_label, state)`: Updates `db_table` in the model's options and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Alters the DB table name. Also alters auto-created M2M tables.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Calls `database_forwards`.
    *   `describe(self)`: Returns `"Rename table for %s to %s"`.
    *   `reduce(self, operation, app_label=None)`: If `operation` is `AlterModelTable` or `DeleteModel` for the same model, returns `[operation]`. Otherwise, calls `super().reduce`.

### `ModelOptionOperation(ModelOperation)`
*   **Signature:** `class ModelOptionOperation(ModelOperation)`
*   **Implementation Logic:**
    *   `reduce(self, operation, app_label=None)`: If `operation` is of the same class or `DeleteModel` for the same model, returns `[operation]`. Otherwise, calls `super().reduce`.

### `FieldRelatedOptionOperation(ModelOptionOperation)`
*   **Signature:** `class FieldRelatedOptionOperation(ModelOptionOperation)`
*   **Implementation Logic:**
    *   `reduce(self, operation, app_label=None)`: If `operation` is a `FieldOperation` for the same model and does not reference the field, returns `[operation, self]`. Otherwise, calls `super().reduce`.

### `AlterUniqueTogether(FieldRelatedOptionOperation)`
*   **Signature:** `class AlterUniqueTogether(FieldRelatedOptionOperation)`
*   **Attributes:** `option_name = "unique_together"`
*   **Implementation Logic:**
    *   `__init__(self, name, unique_together)`: Normalizes `unique_together` to a set of tuples, sets `self.unique_together`, calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name, 'unique_together': self.unique_together})`.
    *   `state_forwards(self, app_label, state)`: Updates the option in `state` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Calls `schema_editor.alter_unique_together`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Calls `database_forwards`.
    *   `references_field(self, model_name, name, app_label=None)`: Returns `True` if it references the model and either `unique_together` is empty or the field name is in any of the tuples.
    *   `describe(self)`: Returns `"Alter %s for %s (%s constraint(s))"`.

### `AlterIndexTogether(FieldRelatedOptionOperation)`
*   **Signature:** `class AlterIndexTogether(FieldRelatedOptionOperation)`
*   **Attributes:** `option_name = "index_together"`
*   **Implementation Logic:**
    *   Identical to `AlterUniqueTogether`, but operates on `index_together` and calls `schema_editor.alter_index_together`.

### `AlterOrderWithRespectTo(FieldRelatedOptionOperation)`
*   **Signature:** `class AlterOrderWithRespectTo(FieldRelatedOptionOperation)`
*   **Implementation Logic:**
    *   `__init__(self, name, order_with_respect_to)`: Sets `self.order_with_respect_to`, calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name, 'order_with_respect_to': self.order_with_respect_to})`.
    *   `state_forwards(self, app_label, state)`: Updates the option in `state` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Removes the `_order` field if the option was removed. Adds the `_order` field (with default 0 if it has no default) if the option was added.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Calls `database_forwards`.
    *   `references_field(self, model_name, name, app_label=None)`: Returns `True` if it references the model and either `order_with_respect_to` is `None` or matches the field name.
    *   `describe(self)`: Returns `"Set order_with_respect_to on %s to %s"`.

### `AlterModelOptions(ModelOptionOperation)`
*   **Signature:** `class AlterModelOptions(ModelOptionOperation)`
*   **Attributes:** `ALTER_OPTION_KEYS = ["base_manager_name", "default_manager_name", "get_latest_by", "managed", "ordering", "permissions", "default_permissions", "select_on_save", "verbose_name", "verbose_name_plural"]`
*   **Implementation Logic:**
    *   `__init__(self, name, options)`: Sets `self.options`, calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'name': self.name, 'options': self.options})`.
    *   `state_forwards(self, app_label, state)`: Merges `self.options` into the model's options. Removes any keys from `ALTER_OPTION_KEYS` that are not in `self.options`. Reloads the model.
    *   `database_forwards` and `database_backwards`: `pass`.
    *   `describe(self)`: Returns `"Change Meta options on %s"`.

### `AlterModelManagers(ModelOptionOperation)`
*   **Signature:** `class AlterModelManagers(ModelOptionOperation)`
*   **Attributes:** `serialization_expand_args = ['managers']`
*   **Implementation Logic:**
    *   `__init__(self, name, managers)`: Sets `self.managers`, calls `super().__init__(name)`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [self.name, self.managers], {})`.
    *   `state_forwards(self, app_label, state)`: Sets `model_state.managers = list(self.managers)` and reloads the model.
    *   `database_forwards` and `database_backwards`: `pass`.
    *   `describe(self)`: Returns `"Change managers on %s"`.

### `IndexOperation(Operation)`
*   **Signature:** `class IndexOperation(Operation)`
*   **Attributes:** `option_name = 'indexes'`
*   **Implementation Logic:**
    *   `model_name_lower(self)`: `@cached_property` returning `self.model_name.lower()`.

### `AddIndex(IndexOperation)`
*   **Signature:** `class AddIndex(IndexOperation)`
*   **Implementation Logic:**
    *   `__init__(self, model_name, index)`: Sets `self.model_name`. Raises `ValueError` if `index.name` is empty. Sets `self.index`.
    *   `state_forwards(self, app_label, state)`: Appends a clone of `self.index` to the model's indexes in `state` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Calls `schema_editor.add_index`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Calls `schema_editor.remove_index`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'model_name': self.model_name, 'index': self.index})`.
    *   `describe(self)`: Returns `"Create index %s on field(s) %s of model %s"`.

### `RemoveIndex(IndexOperation)`
*   **Signature:** `class RemoveIndex(IndexOperation)`
*   **Implementation Logic:**
    *   `__init__(self, model_name, name)`: Sets `self.model_name` and `self.name`.
    *   `state_forwards(self, app_label, state)`: Removes the index with `self.name` from the model's indexes in `state` and reloads the model.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets the index by name from `from_state` and calls `schema_editor.remove_index`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Gets the index by name from `to_state` and calls `schema_editor.add_index`.
    *   `deconstruct(self)`: Returns `(self.__class__.__qualname__, [], {'model_name': self.model_name, 'name': self.name})`.
    *   `describe(self)`: Returns `"Remove index %s from %s"`.

### `AddConstraint(IndexOperation)`
*   **Signature:** `class AddConstraint(IndexOperation)`
*   **Attributes:** `option_name = 'constraints'`
*   **Implementation Logic:**
    *   `__init__(self, model_name, constraint)`: Sets `self.model_name` and `self.constraint`.
    *   `state_forwards(self, app_label, state)`: Appends `self.constraint` to the model's constraints in `state`.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Calls `schema_editor.add_constraint`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Calls `schema_editor.remove_constraint`.
    *   `deconstruct(self)`: Returns `(self.__class__.__name__, [], {'model_name': self.model_name, 'constraint': self.constraint})`.
    *   `describe(self)`: Returns `"Create constraint %s on model %s"`.

### `RemoveConstraint(IndexOperation)`
*   **Signature:** `class RemoveConstraint(IndexOperation)`
*   **Attributes:** `option_name = 'constraints'`
*   **Implementation Logic:**
    *   `__init__(self, model_name, name)`: Sets `self.model_name` and `self.name`.
    *   `state_forwards(self, app_label, state)`: Removes the constraint with `self.name` from the model's constraints in `state`.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Gets the constraint by name from `from_state` and calls `schema_editor.remove_constraint`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Gets the constraint by name from `to_state` and calls `schema_editor.add_constraint`.
    *   `deconstruct(self)`: Returns `(self.__class__.__name__, [], {'model_name': self.model_name, 'name': self.name})`.
    *   `describe(self)`: Returns `"Remove constraint %s from model %s"`.