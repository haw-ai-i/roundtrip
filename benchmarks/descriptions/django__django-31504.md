## django/core/management/commands/makemigrations.py
```markdown
# Specification for `django/core/management/commands/makemigrations.py`

## 1. Module-Level Preamble

### Imports
*   `os`
*   `sys`
*   `itertools.takewhile`
*   `django.apps.apps`
*   `django.conf.settings`
*   `django.core.management.base.BaseCommand`
*   `django.core.management.base.CommandError`
*   `django.core.management.base.no_translations`
*   `django.db.DEFAULT_DB_ALIAS`
*   `django.db.connections`
*   `django.db.router`
*   `django.db.migrations.Migration`
*   `django.db.migrations.autodetector.MigrationAutodetector`
*   `django.db.migrations.loader.MigrationLoader`
*   `django.db.migrations.questioner.InteractiveMigrationQuestioner`
*   `django.db.migrations.questioner.MigrationQuestioner`
*   `django.db.migrations.questioner.NonInteractiveMigrationQuestioner`
*   `django.db.migrations.state.ProjectState`
*   `django.db.migrations.utils.get_migration_name_timestamp`
*   `django.db.migrations.writer.MigrationWriter`

### Constants & Globals
None defined at the module level.

---

## 2. Code Objects

### Class: `Command`
Inherits from `BaseCommand`.

#### Attributes
*   `help`: String literal `"Creates new migration(s) for apps."`

#### Method: `add_arguments`
**Signature:** `def add_arguments(self, parser)`
**Logic:**
Adds the following arguments to the command parser:
*   `args`: Positional, `nargs='*'`, `metavar='app_label'`, help text about specifying app labels.
*   `--dry-run`: Action `store_true`, help text about showing migrations without writing.
*   `--merge`: Action `store_true`, help text about fixing conflicts.
*   `--empty`: Action `store_true`, help text about creating an empty migration.
*   `--noinput`, `--no-input`: Action `store_false`, `dest='interactive'`, help text about not prompting for input.
*   `-n`, `--name`: Help text about using a specific name for migration files.
*   `--no-header`: Action `store_false`, `dest='include_header'`, help text about not adding header comments.
*   `--check`: Action `store_true`, `dest='check_changes'`, help text about exiting with non-zero status if changes are missing migrations.

#### Method: `handle`
**Signature:** `@no_translations def handle(self, *app_labels, **options)`
**Logic:**
1.  **Option Extraction:** Extracts `verbosity`, `interactive`, `dry_run`, `merge`, `empty`, `name` (as `migration_name`), `include_header`, and `check_changes` from `options`.
2.  **Validation:** If `migration_name` is provided and is not a valid Python identifier (`isidentifier()`), raises `CommandError`.
3.  **App Label Validation:** Converts `app_labels` to a set. Iterates through it, calling `apps.get_app_config(app_label)`. If `LookupError` is raised, writes the error to `self.stderr` and sets a flag. If any bad labels were found, calls `sys.exit(2)`.
4.  **Loader Initialization:** Instantiates `MigrationLoader(None, ignore_no_migrations=True)`.
5.  **Consistency Check:**
    *   Gets a set of all app labels from `apps.get_app_configs()`.
    *   Determines aliases to check: `connections` if `settings.DATABASE_ROUTERS` is truthy, else `[DEFAULT_DB_ALIAS]`.
    *   For each sorted alias, gets the connection. If the engine is not `'django.db.backends.dummy'` and `router.allow_migrate` returns true for at least one model in the consistency check labels, calls `loader.check_consistent_history(connection)`.
6.  **Conflict Detection:** Calls `loader.detect_conflicts()`.
    *   If `app_labels` is specified, filters the conflicts dictionary to only include keys present in `app_labels`.
    *   If conflicts exist and `self.merge` is false, raises `CommandError` detailing the conflicting apps and leaf nodes, advising to run with `--merge`.
    *   If `self.merge` is true and no conflicts exist, writes "No conflicts detected to merge." to `self.stdout` and returns.
    *   If `self.merge` is true and conflicts exist, returns the result of `self.handle_merge(loader, conflicts)`.
7.  **Questioner & Autodetector Setup:**
    *   Instantiates `InteractiveMigrationQuestioner` if `self.interactive` is true, else `NonInteractiveMigrationQuestioner`, passing `specified_apps=app_labels` and `dry_run=self.dry_run`.
    *   Instantiates `MigrationAutodetector` with `loader.project_state()`, `ProjectState.from_apps(apps)`, and the questioner.
8.  **Empty Migration Handling:** If `self.empty` is true:
    *   Raises `CommandError` if `app_labels` is empty.
    *   Creates a `changes` dictionary mapping each app label to a list containing a single `Migration("custom", app)`.
    *   Calls `autodetector.arrange_for_graph` with the changes, `loader.graph`, and `self.migration_name`.
    *   Calls `self.write_migration_files(changes)` and returns.
9.  **Change Detection:** Calls `autodetector.changes` with `loader.graph`, `trim_to_apps=app_labels or None`, `convert_apps=app_labels or None`, and `migration_name=self.migration_name`.
10. **Output/Write:**
    *   If no changes are detected: If `verbosity >= 1`, writes a message to `self.stdout` indicating no changes (formatting differently for 1 app, multiple apps, or no specific apps).
    *   If changes are detected: Calls `self.write_migration_files(changes)`. If `check_changes` is true, calls `sys.exit(1)`.

#### Method: `write_migration_files`
**Signature:** `def write_migration_files(self, changes)`
**Logic:**
1.  Iterates over `changes.items()` (app_label, app_migrations).
2.  If `verbosity >= 1`, writes a styled heading for the app to `self.stdout`.
3.  Iterates over `app_migrations`:
    *   Instantiates `MigrationWriter(migration, self.include_header)`.
    *   If `verbosity >= 1`, attempts to get a relative path for `writer.path`. If it fails or starts with `'..'`, uses the absolute path. Writes the path and describes each operation in `migration.operations` to `self.stdout`.
    *   If `not self.dry_run`:
        *   Gets the directory of `writer.path`.
        *   If the directory hasn't been created for this app yet (tracked via a local dict), calls `os.makedirs(..., exist_ok=True)`, creates an empty `__init__.py` if it doesn't exist, and marks the app as created.
        *   Writes `writer.as_string()` to `writer.path` using UTF-8 encoding.
    *   Else if `self.dry_run` and `verbosity == 3`: Writes a styled heading with `writer.filename` and the full migration string (`writer.as_string()`) to `self.stdout`.

#### Method: `handle_merge`
**Signature:** `def handle_merge(self, loader, conflicts)`
**Logic:**
1.  Instantiates `InteractiveMigrationQuestioner()` if `self.interactive` is true, else `MigrationQuestioner(defaults={'ask_merge': True})`.
2.  Iterates over `conflicts.items()` (app_label, migration_names):
    *   For each `migration_name`, gets the migration via `loader.get_migration`. Calculates its `ancestry` by filtering `loader.graph.forwards_plan` for nodes matching the app label. Appends to a `merge_migrations` list.
    *   Finds the common ancestor count by zipping the ancestries and using `takewhile` with a helper function `all_items_equal` to count matching generations.
    *   If `common_ancestor_count` is 0, raises `ValueError`.
    *   For each migration in `merge_migrations`, sets `migration.branch` to the ancestry slice from `common_ancestor_count` onwards. Calculates `migration.merged_operations` by summing the operations of all migrations in the branch.
    *   If `verbosity > 0`, writes a styled heading for merging the app, and for each migration, writes its branch name and describes its merged operations to `self.stdout`.
    *   Calls `questioner.ask_merge(app_label)`. If true:
        *   Parses numbers from the migration names using `MigrationAutodetector.parse_number`. Finds the maximum number (defaulting to 1 if none found).
        *   Creates a new dynamic subclass of `Migration` with `dependencies` set to the conflicting migrations.
        *   Generates a `migration_name` using the next number and either `self.migration_name` or a timestamped string (`"merge_" + get_migration_name_timestamp()`).
        *   Instantiates the new migration and a `MigrationWriter`.
        *   If `not self.dry_run`: Writes the migration to disk (UTF-8) and, if `verbosity > 0`, prints a success message.
        *   Else if `self.dry_run` and `verbosity == 3`: Prints the full merge migration file contents to `self.stdout`.
```