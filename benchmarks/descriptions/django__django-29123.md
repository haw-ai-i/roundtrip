## django/db/migrations/operations/models.py
This is a natural-language specification of the `django/db/migrations/operations/models.py` file.

### 1. Module-Level Preamble

**Imports:**
*   `from django.db import models`
*   `from django.db.migrations.operations.base import Operation`
*   `from django.db.migrations.state import ModelState`
*   `from django.db.models.options import normalize_together`
*   `from django.utils.functional import cached_property`
*   `from .fields import AddField, AlterField, FieldOperation, RemoveField, RenameField`
*   `from .utils import ModelTuple, field_references_model`

**Functions:**
*   `_check_for_duplicates(arg_name, objs)`: Checks for duplicate names in a list of objects (like fields or managers) and raises a `ValueError` if duplicates are found.

### 2. Code Objects (Classes)

The file defines a hierarchy of migration operations related to models. All operations inherit from `Operation` (from `django.db.migrations.operations.base`).

#### Base Classes

*   **`ModelOperation(Operation)`**: Base class for operations that act on a specific model.
    *   `__init__(self, name)`: Initializes with the model's `name`.
    *   `name_lower`: A cached property returning the lowercase model name.
    *   `references_model(self, name, app_label)`: Checks if the operation references the given model.

*   **`ModelOptionOperation(ModelOperation)`**: Base class for operations that alter model options (like `Meta` options).
    *   `reduce(self, operation, app_label=None)`: Handles reduction logic for option operations.

*   **`FieldRelatedOptionOperation(ModelOptionOperation)`**: Base class for option operations that relate to fields (like `unique_together`).

*   **`IndexOperation(Operation)`**: Base class for index and constraint operations.
    *   `__init__(self, model_name)`: Initializes with the `model_name`.
    *   `model_name_lower`: A cached property returning the lowercase model name.

#### Concrete Operations

*   **`CreateModel(ModelOperation)`**: Creates a new model table.
    *   `__init__(self, name, fields, options=None, bases=None, managers=None)`: Initializes with model details.
    *   `state_forwards(self, app_label, state)`: Adds a new `ModelState` to the project state.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.create_model` to create the table.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.delete_model` to drop the table.
    *   `describe(self)`: Returns "Create model {name}".

*   **`DeleteModel(ModelOperation)`**: Drops a model table.
    *   `__init__(self, name)`: Initializes with the model name.
    *   `state_forwards(self, app_label, state)`: Removes the model from the project state.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.delete_model`.
    *   `database_backwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.create_model`.

*   **`RenameModel(ModelOperation)`**: Renames a model.
    *   `__init__(self, old_name, new_name)`: Initializes with old and new names.
    *   `state_forwards(self, app_label, state)`: Updates the model name in the state and updates all related fields in other models to point to the new name.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.alter_db_table` to rename the table.

*   **`AlterModelTable(ModelOperation)`**: Changes a model's `db_table`.
    *   `__init__(self, name, table)`: Initializes with model name and new table name.
    *   `state_forwards(self, app_label, state)`: Updates the `db_table` option in the model state.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.alter_db_table`.

*   **`AlterUniqueTogether(FieldRelatedOptionOperation)`**: Changes a model's `unique_together`.
    *   `__init__(self, name, unique_together)`: Initializes with model name and new `unique_together` value.
    *   `state_forwards(self, app_label, state)`: Updates the `unique_together` option in the model state.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.alter_unique_together`.

*   **`AlterIndexTogether(FieldRelatedOptionOperation)`**: Changes a model's `index_together`.
    *   `__init__(self, name, index_together)`: Initializes with model name and new `index_together` value.
    *   `state_forwards(self, app_label, state)`: Updates the `index_together` option in the model state.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.alter_index_together`.

*   **`AlterOrderWithRespectTo(FieldRelatedOptionOperation)`**: Changes a model's `order_with_respect_to`.
    *   `__init__(self, name, order_with_respect_to)`: Initializes with model name and new value.
    *   `state_forwards(self, app_label, state)`: Updates the `order_with_respect_to` option in the model state.

*   **`AlterModelOptions(ModelOptionOperation)`**: Changes a model's `Meta` options (excluding `db_table`, `unique_together`, `index_together`, `order_with_respect_to`).
    *   `__init__(self, name, options)`: Initializes with model name and new options dictionary.
    *   `state_forwards(self, app_label, state)`: Updates the options in the model state.

*   **`AlterModelManagers(ModelOptionOperation)`**: Changes a model's managers.
    *   `__init__(self, name, managers)`: Initializes with model name and new managers list.
    *   `state_forwards(self, app_label, state)`: Updates the managers in the model state.

*   **`AddIndex(IndexOperation)`**: Adds an index to a model.
    *   `__init__(self, model_name, index)`: Initializes with model name and an `Index` instance.
    *   `state_forwards(self, app_label, state)`: Adds the index to the model state's options.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.add_index`.

*   **`RemoveIndex(IndexOperation)`**: Removes an index from a model.
    *   `__init__(self, model_name, name)`: Initializes with model name and index name.
    *   `state_forwards(self, app_label, state)`: Removes the index from the model state's options.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.remove_index`.

*   **`AddConstraint(IndexOperation)`**: Adds a constraint to a model.
    *   `__init__(self, model_name, constraint)`: Initializes with model name and a `Constraint` instance.
    *   `state_forwards(self, app_label, state)`: Adds the constraint to the model state's options.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.add_constraint`.

*   **`RemoveConstraint(IndexOperation)`**: Removes a constraint from a model.
    *   `__init__(self, model_name, name)`: Initializes with model name and constraint name.
    *   `state_forwards(self, app_label, state)`: Removes the constraint from the model state's options.
    *   `database_forwards(self, app_label, schema_editor, from_state, to_state)`: Uses `schema_editor.remove_constraint`.