## django/core/management/base.py
I have successfully read the source file and written the complete natural-language specification to `/tmp/tmptgocwbdt.md` as requested.

## django/db/migrations/executor.py
### 1. Module-Level Preamble

**Imports:**
*   `from django.apps.registry import apps as global_apps`
*   `from django.db import migrations, router`
*   `from .exceptions import InvalidMigrationPlan`
*   `from .loader import MigrationLoader`
*   `from .recorder import MigrationRecorder`
*   `from .state import ProjectState`

**Constants & Globals:**
None.

### 2. Code Objects (Classes and Functions)

#### `class MigrationExecutor`
**Base Classes:** None

**Attributes:**
*   `connection`: Initialized in `__init__` from the `connection` parameter.
*   `loader`: Initialized in `__init__` as `MigrationLoader(self.connection)`.
*   `recorder`: Initialized in `__init__` as `MigrationRecorder(self.connection)`.
*   `progress_callback`: Initialized in `__init__` from the `progress_callback` parameter.

**Methods:**

*   **`__init__(self, connection, progress_callback=None)`**
    *   **Logic:** Initializes the instance attributes `connection`, `loader`, `recorder`, and `progress_callback`.

*   **`migration_plan(self, targets, clean_start=False)`**
    *   **Signature:** `def migration_plan(self, targets, clean_start=False):`
    *   **Logic:**
        *   Initializes an empty list `plan`.
        *   If `clean_start` is `True`, initializes `applied` as an empty set. Otherwise, initializes `applied` as a set of `self.loader.applied_migrations`.
        *   Iterates over each `target` in `targets`:
            *   If `target[1]` is `None` (unmigrate everything for the app):
                *   Iterates over `self.loader.graph.root_nodes()`. If a root's app label (`root[0]`) matches `target[0]`, iterates over `self.loader.graph.backwards_plan(root)`. If the migration is in `applied`, appends `(self.loader.graph.nodes[migration], True)` to `plan` and removes it from `applied`.
            *   Else if `target` is in `applied` (backwards mode):
                *   Finds `next_in_app`: a sorted list of nodes from `self.loader.graph.node_map[target].children` where the app label matches `target[0]`.
                *   Iterates over `next_in_app`. For each node, iterates over `self.loader.graph.backwards_plan(node)`. If the migration is in `applied`, appends `(self.loader.graph.nodes[migration], True)` to `plan` and removes it from `applied`.
            *   Else (forwards mode):
                *   Iterates over `self.loader.graph.forwards_plan(target)`. If the migration is not in `applied`, appends `(self.loader.graph.nodes[migration], False)` to `plan` and adds it to `applied`.
    *   **Returns:** `plan` (a list of 2-tuples: `(Migration instance, backwards?)`).

*   **`_create_project_state(self, with_applied_migrations=False)`**
    *   **Signature:** `def _create_project_state(self, with_applied_migrations=False):`
    *   **Logic:**
        *   Creates `state = ProjectState(real_apps=list(self.loader.unmigrated_apps))`.
        *   If `with_applied_migrations` is `True`:
            *   Gets `full_plan = self.migration_plan(self.loader.graph.leaf_nodes(), clean_start=True)`.
            *   Creates `applied_migrations`, a set of `self.loader.graph.nodes[key]` for `key` in `self.loader.applied_migrations` if `key` is in `self.loader.graph.nodes`.
            *   Iterates over `(migration, _)` in `full_plan`. If `migration` is in `applied_migrations`, calls `migration.mutate_state(state, preserve=False)`.
    *   **Returns:** `state`.

*   **`migrate(self, targets, plan=None, state=None, fake=False, fake_initial=False)`**
    *   **Signature:** `def migrate(self, targets, plan=None, state=None, fake=False, fake_initial=False):`
    *   **Logic:**
        *   If `plan` is `None`, sets `plan = self.migration_plan(targets)`.
        *   Gets `full_plan = self.migration_plan(self.loader.graph.leaf_nodes(), clean_start=True)`.
        *   Calculates `all_forwards` (all `backwards` are `False` in `plan`) and `all_backwards` (all `backwards` are `True` in `plan`).
        *   If `not plan`:
            *   If `state` is `None`, sets `state = self._create_project_state(with_applied_migrations=True)`.
        *   Else if `all_forwards == all_backwards`:
            *   Raises `InvalidMigrationPlan` with a message about mixed plans and the `plan`.
        *   Else if `all_forwards`:
            *   If `state` is `None`, sets `state = self._create_project_state(with_applied_migrations=True)`.
            *   Sets `state = self._migrate_all_forwards(state, plan, full_plan, fake=fake, fake_initial=fake_initial)`.
        *   Else:
            *   Sets `state = self._migrate_all_backwards(plan, full_plan, fake=fake)`.
        *   Calls `self.check_replacements()`.
    *   **Returns:** `state`.

*   **`_migrate_all_forwards(self, state, plan, full_plan, fake, fake_initial)`**
    *   **Signature:** `def _migrate_all_forwards(self, state, plan, full_plan, fake, fake_initial):`
    *   **Logic:**
        *   Creates `migrations_to_run = {m[0] for m in plan}`.
        *   Iterates over `(migration, _)` in `full_plan`:
            *   If `not migrations_to_run`, breaks the loop.
            *   If `migration` is in `migrations_to_run`:
                *   If `'apps'` is not in `state.__dict__`:
                    *   Calls `self.progress_callback("render_start")` if it exists.
                    *   Accesses `state.apps` (to render all).
                    *   Calls `self.progress_callback("render_success")` if it exists.
                *   Sets `state = self.apply_migration(state, migration, fake=fake, fake_initial=fake_initial)`.
                *   Removes `migration` from `migrations_to_run`.
    *   **Returns:** `state`.

*   **`_migrate_all_backwards(self, plan, full_plan, fake)`**
    *   **Signature:** `def _migrate_all_backwards(self, plan, full_plan, fake):`
    *   **Logic:**
        *   Creates `migrations_to_run = {m[0] for m in plan}`.
        *   Initializes `states = {}`.
        *   Sets `state = self._create_project_state()`.
        *   Creates `applied_migrations`, a set of `self.loader.graph.nodes[key]` for `key` in `self.loader.applied_migrations` if `key` is in `self.loader.graph.nodes`.
        *   Calls `self.progress_callback("render_start")` if it exists.
        *   Iterates over `(migration, _)` in `full_plan`:
            *   If `not migrations_to_run`, breaks the loop.
            *   If `migration` is in `migrations_to_run`:
                *   If `'apps'` is not in `state.__dict__`, accesses `state.apps`.
                *   Sets `states[migration] = state`.
                *   Sets `state = migration.mutate_state(state, preserve=True)`.
                *   Removes `migration` from `migrations_to_run`.
            *   Else if `migration` is in `applied_migrations`:
                *   Calls `migration.mutate_state(state, preserve=False)`.
        *   Calls `self.progress_callback("render_success")` if it exists.
        *   Iterates over `(migration, _)` in `plan`:
            *   Calls `self.unapply_migration(states[migration], migration, fake=fake)`.
            *   Removes `migration` from `applied_migrations`.
        *   Sets `last_unapplied_migration = plan[-1][0]`.
        *   Sets `state = states[last_unapplied_migration]`.
        *   Iterates over `index, (migration, _)` in `enumerate(full_plan)`:
            *   If `migration == last_unapplied_migration`:
                *   Iterates over `(migration, _)` in `full_plan[index:]`:
                    *   If `migration` is in `applied_migrations`, calls `migration.mutate_state(state, preserve=False)`.
                *   Breaks the loop.
    *   **Returns:** `state`.

*   **`collect_sql(self, plan)`**
    *   **Signature:** `def collect_sql(self, plan):`
    *   **Logic:**
        *   Initializes `statements = []` and `state = None`.
        *   Iterates over `(migration, backwards)` in `plan`:
            *   Opens a context manager `with self.connection.schema_editor(collect_sql=True, atomic=migration.atomic) as schema_editor:`.
            *   If `state` is `None`, sets `state = self.loader.project_state((migration.app_label, migration.name), at_end=False)`.
            *   If `not backwards`, sets `state = migration.apply(state, schema_editor, collect_sql=True)`.
            *   Else, sets `state = migration.unapply(state, schema_editor, collect_sql=True)`.
            *   Extends `statements` with `schema_editor.collected_sql`.
    *   **Returns:** `statements`.

*   **`apply_migration(self, state, migration, fake=False, fake_initial=False)`**
    *   **Signature:** `def apply_migration(self, state, migration, fake=False, fake_initial=False):`
    *   **Logic:**
        *   Calls `self.progress_callback("apply_start", migration, fake)` if it exists.
        *   If `not fake`:
            *   If `fake_initial`:
                *   Calls `applied, state = self.detect_soft_applied(state, migration)`.
                *   If `applied`, sets `fake = True`.
            *   If `not fake`:
                *   Opens a context manager `with self.connection.schema_editor(atomic=migration.atomic) as schema_editor:`.
                *   Sets `state = migration.apply(state, schema_editor)`.
        *   If `migration.replaces`:
            *   Iterates over `app_label, name` in `migration.replaces` and calls `self.recorder.record_applied(app_label, name)`.
        *   Else:
            *   Calls `self.recorder.record_applied(migration.app_label, migration.name)`.
        *   Calls `self.progress_callback("apply_success", migration, fake)` if it exists.
    *   **Returns:** `state`.

*   **`unapply_migration(self, state, migration, fake=False)`**
    *   **Signature:** `def unapply_migration(self, state, migration, fake=False):`
    *   **Logic:**
        *   Calls `self.progress_callback("unapply_start", migration, fake)` if it exists.
        *   If `not fake`:
            *   Opens a context manager `with self.connection.schema_editor(atomic=migration.atomic) as schema_editor:`.
            *   Sets `state = migration.unapply(state, schema_editor)`.
        *   If `migration.replaces`:
            *   Iterates over `app_label, name` in `migration.replaces` and calls `self.recorder.record_unapplied(app_label, name)`.
        *   Else:
            *   Calls `self.recorder.record_unapplied(migration.app_label, migration.name)`.
        *   Calls `self.progress_callback("unapply_success", migration, fake)` if it exists.
    *   **Returns:** `state`.

*   **`check_replacements(self)`**
    *   **Signature:** `def check_replacements(self):`
    *   **Logic:**
        *   Gets `applied = self.recorder.applied_migrations()`.
        *   Iterates over `key, migration` in `self.loader.replacements.items()`:
            *   Checks if `all(m in applied for m in migration.replaces)`.
            *   If all are applied and `key` is not in `applied`, calls `self.recorder.record_applied(*key)`.

*   **`detect_soft_applied(self, project_state, migration)`**
    *   **Signature:** `def detect_soft_applied(self, project_state, migration):`
    *   **Logic:**
        *   Defines a nested function `should_skip_detecting_model(migration, model)`:
            *   Returns `True` if `model._meta.proxy` or `not model._meta.managed` or `not router.allow_migrate(self.connection.alias, migration.app_label, model_name=model._meta.model_name)`. Otherwise `False`.
        *   If `migration.initial is None`:
            *   If `any(app == migration.app_label for app, name in migration.dependencies)`, returns `False, project_state`.
        *   Else if `migration.initial is False`:
            *   Returns `False, project_state`.
        *   If `project_state is None`, sets `after_state = self.loader.project_state((migration.app_label, migration.name), at_end=True)`.
        *   Else, sets `after_state = migration.mutate_state(project_state)`.
        *   Sets `apps = after_state.apps`.
        *   Initializes `found_create_model_migration = False` and `found_add_field_migration = False`.
        *   Gets `existing_table_names = self.connection.introspection.table_names(self.connection.cursor())`.
        *   Iterates over `operation` in `migration.operations`:
            *   If `isinstance(operation, migrations.CreateModel)`:
                *   Gets `model = apps.get_model(migration.app_label, operation.name)`.
                *   If `model._meta.swapped`, gets `model = global_apps.get_model(model._meta.swapped)`.
                *   If `should_skip_detecting_model(migration, model)`, continues.
                *   If `model._meta.db_table` is not in `existing_table_names`, returns `False, project_state`.
                *   Sets `found_create_model_migration = True`.
            *   Else if `isinstance(operation, migrations.AddField)`:
                *   Gets `model = apps.get_model(migration.app_label, operation.model_name)`.
                *   If `model._meta.swapped`, gets `model = global_apps.get_model(model._meta.swapped)`.
                *   If `should_skip_detecting_model(migration, model)`, continues.
                *   Gets `table = model._meta.db_table` and `field = model._meta.get_field(operation.name)`.
                *   If `field.many_to_many`:
                    *   If `field.remote_field.through._meta.db_table` is not in `existing_table_names`, returns `False, project_state`.
                    *   Else, sets `found_add_field_migration = True` and continues.
                *   Gets `column_names = [column.name for column in self.connection.introspection.get_table_description(self.connection.cursor(), table)]`.
                *   If `field.column` is not in `column_names`, returns `False, project_state`.
                *   Sets `found_add_field_migration = True`.
    *   **Returns:** `(found_create_model_migration or found_add_field_migration), after_state`.

## django/db/migrations/recorder.py
**1. Module-Level Preamble**

*   **Imports:**
    *   `from django.apps.registry import Apps`
    *   `from django.db import models`
    *   `from django.db.utils import DatabaseError`
    *   `from django.utils.timezone import now`
    *   `from .exceptions import MigrationSchemaMissing`

**2. Code Objects (Classes and Functions)**

*   **Class: `MigrationRecorder`**
    *   **Description:** Manages the storage and retrieval of migration records in the database.
    *   **Inner Class: `Migration`**
        *   **Base Classes:** `models.Model`
        *   **Attributes:**
            *   `app`: A `models.CharField` with `max_length=255`.
            *   `name`: A `models.CharField` with `max_length=255`.
            *   `applied`: A `models.DateTimeField` with `default=now`.
        *   **Inner Class: `Meta`**
            *   **Attributes:**
                *   `apps`: Initialized to `Apps()`.
                *   `app_label`: Set to `"migrations"`.
                *   `db_table`: Set to `"django_migrations"`.
        *   **Method: `__str__(self)`**
            *   **Logic:** Returns a formatted string: `"Migration %s for %s" % (self.name, self.app)`.
    *   **Method: `__init__(self, connection)`**
        *   **Logic:** Initializes the instance by setting `self.connection` to the provided `connection` argument.
    *   **Property: `migration_qs`**
        *   **Logic:** Returns a QuerySet for the `Migration` model, explicitly routed to the database alias of `self.connection` using `.using(self.connection.alias)`.
    *   **Method: `ensure_schema(self)`**
        *   **Logic:**
            1.  Checks if the table name (`self.Migration._meta.db_table`) exists in the list of table names returned by `self.connection.introspection.table_names(self.connection.cursor())`. If it does, the method returns immediately.
            2.  If the table does not exist, it attempts to create it by opening a schema editor context (`with self.connection.schema_editor() as editor:`) and calling `editor.create_model(self.Migration)`.
            3.  If a `DatabaseError` is raised during creation, it catches the exception and raises a `MigrationSchemaMissing` exception with the message `"Unable to create the django_migrations table (%s)" % exc`.
    *   **Method: `applied_migrations(self)`**
        *   **Logic:**
            1.  Calls `self.ensure_schema()` to guarantee the table exists.
            2.  Queries the database using `self.migration_qs.values_list("app", "name")`.
            3.  Returns a `set` of tuples containing `(app, name)` for all applied migrations.
    *   **Method: `record_applied(self, app, name)`**
        *   **Logic:**
            1.  Calls `self.ensure_schema()`.
            2.  Creates a new record in the database by calling `self.migration_qs.create(app=app, name=name)`.
    *   **Method: `record_unapplied(self, app, name)`**
        *   **Logic:**
            1.  Calls `self.ensure_schema()`.
            2.  Deletes the corresponding record from the database by calling `self.migration_qs.filter(app=app, name=name).delete()`.
    *   **Method: `flush(self)`**
        *   **Logic:** Deletes all migration records by calling `self.migration_qs.all().delete()`.