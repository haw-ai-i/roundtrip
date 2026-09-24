## django/db/migrations/operations/models.py
```markdown
1.  **Module-Level Preamble:**
    *   **Imports:**
        *   `from django.db import models`
        *   `from django.db.migrations.operations.base import Operation`
        *   `from django.db.migrations.state import ModelState`
        *   `from django.db.migrations.utils import field_references, resolve_relation`
        *   `from django.db.models.options import normalize_together`
        *   `from django.utils.functional import cached_property`
        *   `from .fields import AddField, AlterField, FieldOperation, RemoveField, RenameField`
    *   **Constants & Globals:** None explicitly defined outside of classes.

2.  **Code Objects (Classes and Functions):**

    *   **Function:** `_check_for_duplicates(arg_name, objs)`
        *   **Implementation Logic:** Iterates over `objs` and checks for duplicates using a set `used_vals`. Raises `ValueError` if a duplicate is found, formatting the message with the duplicate value and `arg_name`. Adds each value to `used_vals`.

    *   **Class:** `ModelOperation(Operation)`
        *   **Method:** `__init__(self, name)`
            *   **Implementation Logic:** Initializes `self.name = name`.
        *   **Method:** `name_lower(self)` (decorated with `@cached_property`)
            *   **Implementation Logic:** Returns `self.name.lower()`.
        *   **Method:** `references_model(self, name, app_label)`
            *   **Implementation Logic:** Returns `name.lower() == self.name_lower`.
        *   **Method:** `reduce(self, operation, app_label)`
            *   **Implementation Logic:** Returns `super().reduce(operation, app_label) or self.can_reduce_through(operation, app_label)`.
        *   **Method:** `can_reduce_through(self, operation, app_label)`
            *   **Implementation Logic:** Returns `not operation.references_model(self.name, app_label)`.

    *   **Class:** `CreateModel(ModelOperation)`
        *   **Class Attribute:** `serialization_expand_args = ['fields', 'options', 'managers']`
        *   **Method:** `__init__(self, name, fields, options=None, bases=None, managers=None)`
            *   **Implementation Logic:** Initializes attributes. Sets `options` to `{}` if `None`, `bases` to `(models.Model,)` if `None`, and `managers` to `[]` if `None`. Calls `super().__init__(name)`. Calls `_check_for_duplicates` on fields, bases, and managers.
        *   **Method:** `deconstruct(self)`
            *   **Implementation Logic:** Returns a tuple `(self.__class__.__qualname__, [], kwargs)` where `kwargs` contains `name`, `fields`, and optionally `options`, `bases`, and `managers` if they differ from defaults.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Adds a new `ModelState` to `state` using the operation's attributes.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Gets the model from `to_state`. If `self.allow_migrate_model` is true, calls `schema_editor.create_model(model)`.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Gets the model from `from_state`. If `self.allow_migrate_model` is true, calls `schema_editor.delete_model(model)`.
        *   **Method:** `describe(self)`
            *   **Implementation Logic:** Returns a string describing the creation of the model (including if it's a proxy).
        *   **Method:** `migration_name_fragment(self)` (property)
            *   **Implementation Logic:** Returns `self.name_lower`.
        *   **Method:** `references_model(self, name, app_label)`
            *   **Implementation Logic:** Checks if the model name matches, or if any base class or field references the given model.
        *   **Method:** `reduce(self, operation, app_label)`
            *   **Implementation Logic:** Handles reduction with `DeleteModel`, `RenameModel`, `AlterModelOptions`, `AlterModelManagers`, `AlterTogetherOptionOperation`, `AlterOrderWithRespectTo`, `AlterModelTable`, `AlterModelTableComment`, and various field operations (`AddField`, `AlterField`, `RemoveField`, `RenameField`). Returns a list of optimized operations or `super().reduce`.

    *   **Class:** `DeleteModel(ModelOperation)`
        *   **Method:** `deconstruct(self)`
            *   **Implementation Logic:** Returns `(self.__class__.__qualname__, [], {"name": self.name})`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Removes the model from `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Deletes the model table using `schema_editor.delete_model`.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Creates the model table using `schema_editor.create_model`.
        *   **Method:** `references_model(self, name, app_label)`
            *   **Implementation Logic:** Returns `True`.
        *   **Method:** `describe(self)`
            *   **Implementation Logic:** Returns `"Delete model %s" % self.name`.
        *   **Method:** `migration_name_fragment(self)` (property)
            *   **Implementation Logic:** Returns `"delete_%s" % self.name_lower`.

    *   **Class:** `RenameModel(ModelOperation)`
        *   **Method:** `__init__(self, old_name, new_name)`
            *   **Implementation Logic:** Initializes `self.old_name` and `self.new_name`.
        *   **Method:** `old_name_lower(self)` (cached_property)
            *   **Implementation Logic:** Returns `self.old_name.lower()`.
        *   **Method:** `new_name_lower(self)` (cached_property)
            *   **Implementation Logic:** Returns `self.new_name.lower()`.
        *   **Method:** `deconstruct(self)`
            *   **Implementation Logic:** Returns deconstruction tuple with `old_name` and `new_name`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Renames the model in `state` and updates related fields.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Alters the DB table name using `schema_editor.alter_db_table`.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Reverses the DB table name alteration.
        *   **Method:** `references_model(self, name, app_label)`
            *   **Implementation Logic:** Checks if `name.lower()` matches `old_name_lower` or `new_name_lower`.
        *   **Method:** `describe(self)`
            *   **Implementation Logic:** Returns `"Rename model %s to %s"`.
        *   **Method:** `migration_name_fragment(self)` (property)
            *   **Implementation Logic:** Returns `"rename_%s_%s"`.
        *   **Method:** `reduce(self, operation, app_label)`
            *   **Implementation Logic:** Optimizes consecutive `RenameModel` operations.

    *   **Class:** `ModelOptionOperation(ModelOperation)`
        *   **Method:** `reduce(self, operation, app_label)`
            *   **Implementation Logic:** Optimizes operations that alter the same model option consecutively.

    *   **Class:** `AlterModelTable(ModelOptionOperation)`
        *   **Method:** `__init__(self, name, table)`
            *   **Implementation Logic:** Initializes `name` and `table`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Updates the `db_table` option in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Alters the DB table name.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Reverses the DB table name alteration.

    *   **Class:** `AlterModelTableComment(ModelOptionOperation)`
        *   **Method:** `__init__(self, name, table_comment)`
            *   **Implementation Logic:** Initializes `name` and `table_comment`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Updates the `db_table_comment` option in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Alters the DB table comment.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Reverses the DB table comment alteration.

    *   **Class:** `AlterTogetherOptionOperation(ModelOptionOperation)`
        *   **Class Attribute:** `option_name = None`
        *   **Method:** `__init__(self, name, option_value)`
            *   **Implementation Logic:** Initializes `name` and `option_value` (normalized).
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Updates the together option in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Alters the together option in the database.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Reverses the together option alteration.

    *   **Class:** `AlterUniqueTogether(AlterTogetherOptionOperation)`
        *   **Class Attribute:** `option_name = 'unique_together'`
        *   **Method:** `__init__(self, name, unique_together)`
            *   **Implementation Logic:** Calls `super().__init__(name, unique_together)`.

    *   **Class:** `AlterIndexTogether(AlterTogetherOptionOperation)`
        *   **Class Attribute:** `option_name = 'index_together'`
        *   **Method:** `__init__(self, name, index_together)`
            *   **Implementation Logic:** Calls `super().__init__(name, index_together)`.

    *   **Class:** `AlterOrderWithRespectTo(ModelOptionOperation)`
        *   **Method:** `__init__(self, name, order_with_respect_to)`
            *   **Implementation Logic:** Initializes `name` and `order_with_respect_to`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Updates the `order_with_respect_to` option in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Alters the `order_with_respect_to` option in the database.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Reverses the `order_with_respect_to` option alteration.

    *   **Class:** `AlterModelOptions(ModelOptionOperation)`
        *   **Class Attribute:** `ALTER_OPTION_KEYS = [...]`
        *   **Method:** `__init__(self, name, options)`
            *   **Implementation Logic:** Initializes `name` and `options`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Updates the model options in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Alters the model options in the database.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Reverses the model options alteration.

    *   **Class:** `AlterModelManagers(ModelOptionOperation)`
        *   **Method:** `__init__(self, name, managers)`
            *   **Implementation Logic:** Initializes `name` and `managers`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Updates the model managers in `state`.

    *   **Class:** `IndexOperation(Operation)`
        *   **Class Attribute:** `option_name = 'indexes'`
        *   **Method:** `__init__(self, model_name, index)`
            *   **Implementation Logic:** Initializes `model_name` and `index`.

    *   **Class:** `AddIndex(IndexOperation)`
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Adds the index to the model in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Adds the index to the database.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Removes the index from the database.

    *   **Class:** `RemoveIndex(IndexOperation)`
        *   **Method:** `__init__(self, model_name, name)`
            *   **Implementation Logic:** Initializes `model_name` and `name`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Removes the index from the model in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Removes the index from the database.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Adds the index to the database.

    *   **Class:** `RenameIndex(IndexOperation)`
        *   **Method:** `__init__(self, model_name, new_name, old_name=None, old_fields=None)`
            *   **Implementation Logic:** Initializes `model_name`, `new_name`, `old_name`, and `old_fields`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Renames the index in the model in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Renames the index in the database.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Reverses the index rename in the database.

    *   **Class:** `AddConstraint(IndexOperation)`
        *   **Class Attribute:** `option_name = 'constraints'`
        *   **Method:** `__init__(self, model_name, constraint)`
            *   **Implementation Logic:** Initializes `model_name` and `constraint`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Adds the constraint to the model in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Adds the constraint to the database.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Removes the constraint from the database.

    *   **Class:** `RemoveConstraint(IndexOperation)`
        *   **Class Attribute:** `option_name = 'constraints'`
        *   **Method:** `__init__(self, model_name, name)`
            *   **Implementation Logic:** Initializes `model_name` and `name`.
        *   **Method:** `state_forwards(self, app_label, state)`
            *   **Implementation Logic:** Removes the constraint from the model in `state`.
        *   **Method:** `database_forwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Removes the constraint from the database.
        *   **Method:** `database_backwards(self, app_label, schema_editor, from_state, to_state)`
            *   **Implementation Logic:** Adds the constraint to the database.
```