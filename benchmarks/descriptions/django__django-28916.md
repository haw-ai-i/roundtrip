## django/db/migrations/operations/models.py
```markdown
1.  **Module-Level Preamble:**
    *   **Imports:**
        *   `from django.db import models`
        *   `from django.db.migrations.operations.base import Operation`
        *   `from django.db.migrations.state import ModelState`
        *   `from django.db.models.options import normalize_together`
        *   `from django.utils.functional import cached_property`
        *   `from .fields import AddField, AlterField, FieldOperation, RemoveField, RenameField`
        *   `from .utils import ModelTuple, field_references_model`
    *   **Constants & Globals:** None.

2.  **Code Objects (Classes and Functions):**

    *   **`def _check_for_duplicates(arg_name, objs)`**
        *   **Signature:** `def _check_for_duplicates(arg_name, objs)`
        *   **Implementation Logic:** Iterates over `objs`. Maintains a set of `used_vals`. If a value is already in `used_vals`, raises `ValueError("Found duplicate value %s in CreateModel %s argument." % (val, arg_name))`. Otherwise, adds it to `used_vals`.

    *   **`class ModelOperation(Operation)`**
        *   **Base Classes:** `Operation`
        *   **Attributes:** None.
        *   **`__init__(self, name)`:** Sets `self.name = name`.
        *   **`name_lower(self)`:** Decorated with `@cached_property`. Returns `self.name.lower()`.
        *   **`references_model(self, name, app_label=None)`:** Returns `name.lower() == self.name_lower`.
        *   **`reduce(self, operation, app_label=None)`:** Returns `super().reduce(operation, app_label=app_label) or not operation.references_model(self.name, app_label)`.

    *   **`class CreateModel(ModelOperation)`**
        *   **Base Classes:** `ModelOperation`
        *   **Attributes:**
            *   `serialization_expand_args`: `['fields', 'options', 'managers']`
        *   **`__init__(self, name, fields, options=None, bases=None, managers=None)`:**
            *   Sets `self.fields = fields`.
            *   Sets `self.options = options or {}`.
            *   Sets `self.bases = bases or (models.Model,)`.
            *   Sets `self.managers = managers or []`.
            *   Calls `super().__init__(name)`.
            *   Calls `_check_for_duplicates('fields', (name for name, _ in self.fields))`.
            *   Calls `_check_for_duplicates('bases', (base._meta.label_lower if hasattr(base, '_meta') else base.lower() if isinstance(base, str) else base for base in self.bases))`.
            *   Calls `_check_for_duplicates('managers', (name for name, _ in self.managers))`.
        *   **`deconstruct(self)`:** Returns a tuple `(self.__class__.__qualname__, [], kwargs)`. `kwargs` contains `name` and `fields`. Adds `options` if truthy. Adds `bases` if truthy and not `(models.Model,)`. Adds `managers` if truthy and not `[('objects', models.Manager())]`.
        *   **`state_forwards(self, app_label, state)`:** Calls `state.add_model(ModelState(app_label, self.name, list(self.fields), dict(self.options), tuple(self.bases), list(self.managers)))`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model = to_state.apps.get_model(app_label, self.name)`. If `self.allow_migrate_model(schema_editor.connection.alias, model)`, calls `schema_editor.create_model(model)`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model = from_state.apps.get_model(app_label, self.name)`. If `self.allow_migrate_model(schema_editor.connection.alias, model)`, calls `schema_editor.delete_model(model)`.
        *   **`describe(self)`:** Returns `"Create %smodel %s" % ("proxy " if self.options.get("proxy", False) else "", self.name)`.
        *   **`references_model(self, name, app_label=None)`:**
            *   If `name.lower() == self.name_lower`, returns `True`.
            *   Creates `model_tuple = ModelTuple(app_label, name.lower())`.
            *   Iterates over `self.bases`. If `base is not models.Model` and `isinstance(base, (models.base.ModelBase, str))` and `ModelTuple.from_model(base) == model_tuple`, returns `True`.
            *   Iterates over `_name, field` in `self.fields`. If `field_references_model(field, model_tuple)`, returns `True`.
            *   Returns `False`.
        *   **`reduce(self, operation, app_label=None)`:**
            *   If `operation` is `DeleteModel` and `self.name_lower == operation.name_lower` and not `self.options.get("proxy", False)`, returns `[]`.
            *   If `operation` is `RenameModel` and `self.name_lower == operation.old_name_lower`, returns `[CreateModel(operation.new_name, fields=self.fields, options=self.options, bases=self.bases, managers=self.managers)]`.
            *   If `operation` is `AlterModelOptions` and `self.name_lower == operation.name_lower`, returns `[CreateModel(self.name, fields=self.fields, options={**self.options, **operation.options}, bases=self.bases, managers=self.managers)]`.
            *   If `operation` is `FieldOperation` and `self.name_lower == operation.model_name_lower`:
                *   If `operation` is `AddField`, returns `[CreateModel(self.name, fields=self.fields + [(operation.name, operation.field)], options=self.options, bases=self.bases, managers=self.managers)]`.
                *   If `operation` is `AlterField`, returns `[CreateModel(self.name, fields=[(n, operation.field if n == operation.name else v) for n, v in self.fields], options=self.options, bases=self.bases, managers=self.managers)]`.
                *   If `operation` is `RemoveField`, returns `[CreateModel(self.name, fields=[(n, v) for n, v in self.fields if n.lower() != operation.name_lower], options=self.options, bases=self.bases, managers=self.managers)]`.
                *   If `operation` is `RenameField`, returns `[CreateModel(self.name, fields=[(operation.new_name if n == operation.old_name else n, v) for n, v in self.fields], options=self.options, bases=self.bases, managers=self.managers)]`.
            *   Returns `super().reduce(operation, app_label=app_label)`.

    *   **`class DeleteModel(ModelOperation)`**
        *   **Base Classes:** `ModelOperation`
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [], {'name': self.name})`.
        *   **`state_forwards(self, app_label, state)`:** Calls `state.remove_model(app_label, self.name_lower)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model = from_state.apps.get_model(app_label, self.name)`. If `self.allow_migrate_model(schema_editor.connection.alias, model)`, calls `schema_editor.delete_model(model)`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model = to_state.apps.get_model(app_label, self.name)`. If `self.allow_migrate_model(schema_editor.connection.alias, model)`, calls `schema_editor.create_model(model)`.
        *   **`references_model(self, name, app_label=None)`:** Returns `True`.
        *   **`describe(self)`:** Returns `"Delete model %s" % self.name`.

    *   **`class RenameModel(ModelOperation)`**
        *   **Base Classes:** `ModelOperation`
        *   **`__init__(self, old_name, new_name)`:** Sets `self.old_name = old_name`, `self.new_name = new_name`. Calls `super().__init__(old_name)`.
        *   **`old_name_lower(self)`:** Decorated with `@cached_property`. Returns `self.old_name.lower()`.
        *   **`new_name_lower(self)`:** Decorated with `@cached_property`. Returns `self.new_name.lower()`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [], {'old_name': self.old_name, 'new_name': self.new_name})`.
        *   **`state_forwards(self, app_label, state)`:**
            *   Clones `state.models[app_label, self.old_name_lower]` to `renamed_model`.
            *   Sets `renamed_model.name = self.new_name`.
            *   Sets `state.models[app_label, self.new_name_lower] = renamed_model`.
            *   Iterates over `state.models.items()`. For each field, if `remote_field` points to `old_model_tuple`, clones field and updates `remote_field.model` to `new_remote_model`. If `through` points to `old_model_tuple`, updates `remote_field.through`. Updates `model_state.fields` and adds to `to_reload`.
            *   Calls `state.reload_models(to_reload, delay=True)`.
            *   Calls `state.remove_model(app_label, self.old_name_lower)`.
            *   Calls `state.reload_model(app_label, self.new_name_lower, delay=True)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:**
            *   Gets `new_model = to_state.apps.get_model(app_label, self.new_name)`.
            *   If `self.allow_migrate_model(schema_editor.connection.alias, new_model)`:
                *   Gets `old_model = from_state.apps.get_model(app_label, self.old_name)`.
                *   Calls `schema_editor.alter_db_table(new_model, old_model._meta.db_table, new_model._meta.db_table)`.
                *   Iterates over `old_model._meta.related_objects`. Alters fields pointing to the model.
                *   Iterates over `zip(old_model._meta.local_many_to_many, new_model._meta.local_many_to_many)`. Renames M2M tables and columns based on the model's name.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Swaps `new_name` and `old_name` (and their lower versions), calls `database_forwards`, then swaps back.
        *   **`references_model(self, name, app_label=None)`:** Returns `name.lower() == self.old_name_lower or name.lower() == self.new_name_lower`.
        *   **`describe(self)`:** Returns `"Rename model %s to %s" % (self.old_name, self.new_name)`.
        *   **`reduce(self, operation, app_label=None)`:**
            *   If `operation` is `RenameModel` and `self.new_name_lower == operation.old_name_lower`, returns `[RenameModel(self.old_name, operation.new_name)]`.
            *   Returns `super(ModelOperation, self).reduce(operation, app_label=app_label) or not operation.references_model(self.new_name, app_label)`.

    *   **`class AlterModelTable(ModelOperation)`**
        *   **Base Classes:** `ModelOperation`
        *   **`__init__(self, name, table)`:** Sets `self.table = table`. Calls `super().__init__(name)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [], {'name': self.name, 'table': self.table})`.
        *   **`state_forwards(self, app_label, state)`:** Sets `state.models[app_label, self.name_lower].options["db_table"] = self.table`. Calls `state.reload_model(app_label, self.name_lower, delay=True)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `new_model`. If allowed, gets `old_model`, calls `schema_editor.alter_db_table`. Also alters auto-created M2M tables.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Returns `self.database_forwards(app_label, schema_editor, from_state, to_state)`.
        *   **`describe(self)`:** Returns `"Rename table for %s to %s" % (self.name, self.table if self.table is not None else "(default)")`.
        *   **`reduce(self, operation, app_label=None)`:** If `operation` is `AlterModelTable` or `DeleteModel` and `self.name_lower == operation.name_lower`, returns `[operation]`. Else returns `super().reduce(operation, app_label=app_label)`.

    *   **`class ModelOptionOperation(ModelOperation)`**
        *   **Base Classes:** `ModelOperation`
        *   **`reduce(self, operation, app_label=None)`:** If `operation` is `self.__class__` or `DeleteModel` and `self.name_lower == operation.name_lower`, returns `[operation]`. Else returns `super().reduce(operation, app_label=app_label)`.

    *   **`class FieldRelatedOptionOperation(ModelOptionOperation)`**
        *   **Base Classes:** `ModelOptionOperation`
        *   **`reduce(self, operation, app_label=None)`:** If `operation` is `FieldOperation` and `self.name_lower == operation.model_name_lower` and not `self.references_field(operation.model_name, operation.name)`, returns `[operation, self]`. Else returns `super().reduce(operation, app_label=app_label)`.

    *   **`class AlterUniqueTogether(FieldRelatedOptionOperation)`**
        *   **Base Classes:** `FieldRelatedOptionOperation`
        *   **Attributes:**
            *   `option_name`: `"unique_together"`
        *   **`__init__(self, name, unique_together)`:** Sets `self.unique_together = {tuple(cons) for cons in normalize_together(unique_together)}`. Calls `super().__init__(name)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [], {'name': self.name, 'unique_together': self.unique_together})`.
        *   **`state_forwards(self, app_label, state)`:** Sets `state.models[app_label, self.name_lower].options[self.option_name] = self.unique_together`. Calls `state.reload_model(app_label, self.name_lower, delay=True)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `new_model`. If allowed, gets `old_model`, calls `schema_editor.alter_unique_together(new_model, getattr(old_model._meta, self.option_name, set()), getattr(new_model._meta, self.option_name, set()))`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Returns `self.database_forwards(app_label, schema_editor, from_state, to_state)`.
        *   **`references_field(self, model_name, name, app_label=None)`:** Returns `self.references_model(model_name, app_label) and (not self.unique_together or any((name in together) for together in self.unique_together))`.
        *   **`describe(self)`:** Returns `"Alter %s for %s (%s constraint(s))" % (self.option_name, self.name, len(self.unique_together or ''))`.

    *   **`class AlterIndexTogether(FieldRelatedOptionOperation)`**
        *   **Base Classes:** `FieldRelatedOptionOperation`
        *   **Attributes:**
            *   `option_name`: `"index_together"`
        *   **`__init__(self, name, index_together)`:** Sets `self.index_together = {tuple(cons) for cons in normalize_together(index_together)}`. Calls `super().__init__(name)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [], {'name': self.name, 'index_together': self.index_together})`.
        *   **`state_forwards(self, app_label, state)`:** Sets `state.models[app_label, self.name_lower].options[self.option_name] = self.index_together`. Calls `state.reload_model(app_label, self.name_lower, delay=True)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `new_model`. If allowed, gets `old_model`, calls `schema_editor.alter_index_together(new_model, getattr(old_model._meta, self.option_name, set()), getattr(new_model._meta, self.option_name, set()))`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Returns `self.database_forwards(app_label, schema_editor, from_state, to_state)`.
        *   **`references_field(self, model_name, name, app_label=None)`:** Returns `self.references_model(model_name, app_label) and (not self.index_together or any((name in together) for together in self.index_together))`.
        *   **`describe(self)`:** Returns `"Alter %s for %s (%s constraint(s))" % (self.option_name, self.name, len(self.index_together or ''))`.

    *   **`class AlterOrderWithRespectTo(FieldRelatedOptionOperation)`**
        *   **Base Classes:** `FieldRelatedOptionOperation`
        *   **`__init__(self, name, order_with_respect_to)`:** Sets `self.order_with_respect_to = order_with_respect_to`. Calls `super().__init__(name)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [], {'name': self.name, 'order_with_respect_to': self.order_with_respect_to})`.
        *   **`state_forwards(self, app_label, state)`:** Sets `state.models[app_label, self.name_lower].options['order_with_respect_to'] = self.order_with_respect_to`. Calls `state.reload_model(app_label, self.name_lower, delay=True)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `to_model`. If allowed, gets `from_model`. If `from_model` has `order_with_respect_to` and `to_model` doesn't, calls `schema_editor.remove_field(from_model, from_model._meta.get_field("_order"))`. If `to_model` has it and `from_model` doesn't, gets `_order` field, sets default to 0 if no default, calls `schema_editor.add_field(from_model, field)`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Calls `self.database_forwards(app_label, schema_editor, from_state, to_state)`.
        *   **`references_field(self, model_name, name, app_label=None)`:** Returns `self.references_model(model_name, app_label) and (self.order_with_respect_to is None or name == self.order_with_respect_to)`.
        *   **`describe(self)`:** Returns `"Set order_with_respect_to on %s to %s" % (self.name, self.order_with_respect_to)`.

    *   **`class AlterModelOptions(ModelOptionOperation)`**
        *   **Base Classes:** `ModelOptionOperation`
        *   **Attributes:**
            *   `ALTER_OPTION_KEYS`: `["base_manager_name", "default_manager_name", "get_latest_by", "managed", "ordering", "permissions", "default_permissions", "select_on_save", "verbose_name", "verbose_name_plural"]`
        *   **`__init__(self, name, options)`:** Sets `self.options = options`. Calls `super().__init__(name)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [], {'name': self.name, 'options': self.options})`.
        *   **`state_forwards(self, app_label, state)`:** Updates `state.models[app_label, self.name_lower].options` with `self.options`. Removes keys in `ALTER_OPTION_KEYS` that are not in `self.options`. Calls `state.reload_model(app_label, self.name_lower, delay=True)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** `pass`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** `pass`.
        *   **`describe(self)`:** Returns `"Change Meta options on %s" % self.name`.

    *   **`class AlterModelManagers(ModelOptionOperation)`**
        *   **Base Classes:** `ModelOptionOperation`
        *   **Attributes:**
            *   `serialization_expand_args`: `['managers']`
        *   **`__init__(self, name, managers)`:** Sets `self.managers = managers`. Calls `super().__init__(name)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [self.name, self.managers], {})`.
        *   **`state_forwards(self, app_label, state)`:** Sets `state.models[app_label, self.name_lower].managers = list(self.managers)`. Calls `state.reload_model(app_label, self.name_lower, delay=True)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** `pass`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** `pass`.
        *   **`describe(self)`:** Returns `"Change managers on %s" % self.name`.

    *   **`class IndexOperation(Operation)`**
        *   **Base Classes:** `Operation`
        *   **Attributes:**
            *   `option_name`: `'indexes'`
        *   **`model_name_lower(self)`:** Decorated with `@cached_property`. Returns `self.model_name.lower()`.

    *   **`class AddIndex(IndexOperation)`**
        *   **Base Classes:** `IndexOperation`
        *   **`__init__(self, model_name, index)`:** Sets `self.model_name = model_name`. If `not index.name`, raises `ValueError`. Sets `self.index = index`.
        *   **`state_forwards(self, app_label, state)`:** Appends `self.index.clone()` to `state.models[app_label, self.model_name_lower].options[self.option_name]`. Calls `state.reload_model(app_label, self.model_name_lower, delay=True)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model`. If allowed, calls `schema_editor.add_index(model, self.index)`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model`. If allowed, calls `schema_editor.remove_index(model, self.index)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [], {'model_name': self.model_name, 'index': self.index})`.
        *   **`describe(self)`:** Returns `'Create index %s on field(s) %s of model %s' % (self.index.name, ', '.join(self.index.fields), self.model_name)`.

    *   **`class RemoveIndex(IndexOperation)`**
        *   **Base Classes:** `IndexOperation`
        *   **`__init__(self, model_name, name)`:** Sets `self.model_name = model_name`, `self.name = name`.
        *   **`state_forwards(self, app_label, state)`:** Removes index with `name == self.name` from `state.models[app_label, self.model_name_lower].options[self.option_name]`. Calls `state.reload_model(app_label, self.model_name_lower, delay=True)`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model`. If allowed, gets `index = from_state.models[app_label, self.model_name_lower].get_index_by_name(self.name)`. Calls `schema_editor.remove_index(model, index)`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model`. If allowed, gets `index = to_state.models[app_label, self.model_name_lower].get_index_by_name(self.name)`. Calls `schema_editor.add_index(model, index)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__qualname__, [], {'model_name': self.model_name, 'name': self.name})`.
        *   **`describe(self)`:** Returns `'Remove index %s from %s' % (self.name, self.model_name)`.

    *   **`class AddConstraint(IndexOperation)`**
        *   **Base Classes:** `IndexOperation`
        *   **Attributes:**
            *   `option_name`: `'constraints'`
        *   **`__init__(self, model_name, constraint)`:** Sets `self.model_name = model_name`, `self.constraint = constraint`.
        *   **`state_forwards(self, app_label, state)`:** Appends `self.constraint` to `state.models[app_label, self.model_name_lower].options[self.option_name]`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model`. If allowed, calls `schema_editor.add_constraint(model, self.constraint)`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model`. If allowed, calls `schema_editor.remove_constraint(model, self.constraint)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__name__, [], {'model_name': self.model_name, 'constraint': self.constraint})`.
        *   **`describe(self)`:** Returns `'Create constraint %s on model %s' % (self.constraint.name, self.model_name)`.

    *   **`class RemoveConstraint(IndexOperation)`**
        *   **Base Classes:** `IndexOperation`
        *   **Attributes:**
            *   `option_name`: `'constraints'`
        *   **`__init__(self, model_name, name)`:** Sets `self.model_name = model_name`, `self.name = name`.
        *   **`state_forwards(self, app_label, state)`:** Removes constraint with `name == self.name` from `state.models[app_label, self.model_name_lower].options[self.option_name]`.
        *   **`database_forwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model`. If allowed, gets `constraint = from_state.models[app_label, self.model_name_lower].get_constraint_by_name(self.name)`. Calls `schema_editor.remove_constraint(model, constraint)`.
        *   **`database_backwards(self, app_label, schema_editor, from_state, to_state)`:** Gets `model`. If allowed, gets `constraint = to_state.models[app_label, self.model_name_lower].get_constraint_by_name(self.name)`. Calls `schema_editor.add_constraint(model, constraint)`.
        *   **`deconstruct(self)`:** Returns `(self.__class__.__name__, [], {'model_name': self.model_name, 'name': self.name})`.
        *   **`describe(self)`:** Returns `'Remove constraint %s from model %s' % (self.name, self.model_name)`.
```