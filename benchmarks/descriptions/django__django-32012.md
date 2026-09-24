## django/db/backends/base/creation.py
**Module-Level Preamble**

*   **Imports:**
    *   `import os`
    *   `import sys`
    *   `from io import StringIO`
    *   `from django.apps import apps`
    *   `from django.conf import settings`
    *   `from django.core import serializers`
    *   `from django.db import router`
    *   `from django.db.transaction import atomic`
*   **Constants:**
    *   `TEST_DATABASE_PREFIX = 'test_'`

**Code Objects**

**Class: `BaseDatabaseCreation`**
Encapsulates backend-specific differences pertaining to creation and destruction of the test database.

*   **`__init__(self, connection)`**
    *   Sets `self.connection = connection`.

*   **`_nodb_cursor(self)`**
    *   Returns `self.connection._nodb_cursor()`.

*   **`log(self, msg)`**
    *   Writes `msg + os.linesep` to `sys.stderr`.

*   **`create_test_db(self, verbosity=1, autoclobber=False, serialize=True, keepdb=False)`**
    *   Imports `call_command` from `django.core.management`.
    *   Gets the test database name by calling `self._get_test_db_name()`.
    *   If `verbosity >= 1`:
        *   Determines the action string: `"Using existing"` if `keepdb` is `True`, else `'Creating'`.
        *   Logs `"%s test database for alias %s..." % (action, self._get_database_display_str(verbosity, test_database_name))`.
    *   Calls `self._create_test_db(verbosity, autoclobber, keepdb)`.
    *   Closes the connection: `self.connection.close()`.
    *   Updates the database name in settings:
        *   `settings.DATABASES[self.connection.alias]["NAME"] = test_database_name`
        *   `self.connection.settings_dict["NAME"] = test_database_name`
    *   If `self.connection.settings_dict['TEST']['MIGRATE']` is truthy:
        *   Calls `call_command('migrate', verbosity=max(verbosity - 1, 0), interactive=False, database=self.connection.alias, run_syncdb=True)`.
    *   If `serialize` is truthy:
        *   Sets `self.connection._test_serialized_contents = self.serialize_db_to_string()`.
    *   Calls `call_command('createcachetable', database=self.connection.alias)`.
    *   Calls `self.connection.ensure_connection()`.
    *   Returns `test_database_name`.

*   **`set_as_test_mirror(self, primary_settings_dict)`**
    *   Sets `self.connection.settings_dict['NAME'] = primary_settings_dict['NAME']`.

*   **`serialize_db_to_string(self)`**
    *   Defines an inner generator function `get_objects()`:
        *   Imports `MigrationLoader` from `django.db.migrations.loader`.
        *   Instantiates `loader = MigrationLoader(self.connection)`.
        *   Iterates over `apps.get_app_configs()`.
        *   For each `app_config`, if `app_config.models_module is not None`, `app_config.label in loader.migrated_apps`, and `app_config.name not in settings.TEST_NON_SERIALIZED_APPS`:
            *   Iterates over `app_config.get_models()`.
            *   For each `model`, if `model._meta.can_migrate(self.connection)` and `router.allow_migrate_model(self.connection.alias, model)`:
                *   Gets a queryset: `model._default_manager.using(self.connection.alias).order_by(model._meta.pk.name)`.
                *   Yields from `queryset.iterator()`.
    *   Creates `out = StringIO()`.
    *   Calls `serializers.serialize("json", get_objects(), indent=None, stream=out)`.
    *   Returns `out.getvalue()`.

*   **`deserialize_db_from_string(self, data)`**
    *   Reassigns `data = StringIO(data)`.
    *   Initializes `table_names = set()`.
    *   Enters a context manager: `with atomic(using=self.connection.alias):`
        *   Enters a nested context manager: `with self.connection.constraint_checks_disabled():`
            *   Iterates over `serializers.deserialize('json', data, using=self.connection.alias)`:
                *   Calls `obj.save()`.
                *   Adds `obj.object.__class__._meta.db_table` to `table_names`.
        *   Calls `self.connection.check_constraints(table_names=table_names)`.

*   **`_get_database_display_str(self, verbosity, database_name)`**
    *   Returns a formatted string: `"'%s'%s" % (self.connection.alias, (" ('%s')" % database_name) if verbosity >= 2 else '')`.

*   **`_get_test_db_name(self)`**
    *   If `self.connection.settings_dict['TEST']['NAME']` is truthy, returns it.
    *   Otherwise, returns `TEST_DATABASE_PREFIX + self.connection.settings_dict['NAME']`.

*   **`_execute_create_test_db(self, cursor, parameters, keepdb=False)`**
    *   Executes `'CREATE DATABASE %(dbname)s %(suffix)s' % parameters` on the `cursor`.

*   **`_create_test_db(self, verbosity, autoclobber, keepdb=False)`**
    *   Gets `test_database_name = self._get_test_db_name()`.
    *   Creates `test_db_params = {'dbname': self.connection.ops.quote_name(test_database_name), 'suffix': self.sql_table_creation_suffix()}`.
    *   Enters a context manager: `with self._nodb_cursor() as cursor:`
        *   Enters a `try` block:
            *   Calls `self._execute_create_test_db(cursor, test_db_params, keepdb)`.
        *   Catches `Exception as e`:
            *   If `keepdb` is truthy, returns `test_database_name`.
            *   Logs `'Got an error creating the test database: %s' % e`.
            *   If `autoclobber` is falsy, prompts the user: `confirm = input("Type 'yes' if you would like to try deleting the test database '%s', or 'no' to cancel: " % test_database_name)`.
            *   If `autoclobber` is truthy or `confirm == 'yes'`:
                *   Enters a nested `try` block:
                    *   If `verbosity >= 1`, logs `'Destroying old test database for alias %s...' % (self._get_database_display_str(verbosity, test_database_name),)`.
                    *   Executes `'DROP DATABASE %(dbname)s' % test_db_params` on the `cursor`.
                    *   Calls `self._execute_create_test_db(cursor, test_db_params, keepdb)`.
                *   Catches `Exception as e`:
                    *   Logs `'Got an error recreating the test database: %s' % e`.
                    *   Calls `sys.exit(2)`.
            *   Else:
                *   Logs `'Tests cancelled.'`.
                *   Calls `sys.exit(1)`.
    *   Returns `test_database_name`.

*   **`clone_test_db(self, suffix, verbosity=1, autoclobber=False, keepdb=False)`**
    *   Gets `source_database_name = self.connection.settings_dict['NAME']`.
    *   If `verbosity >= 1`:
        *   Determines the action string: `'Using existing clone'` if `keepdb` is `True`, else `'Cloning test database'`.
        *   Logs `"%s for alias %s..." % (action, self._get_database_display_str(verbosity, source_database_name))`.
    *   Calls `self._clone_test_db(suffix, verbosity, keepdb)`.

*   **`get_test_db_clone_settings(self, suffix)`**
    *   Gets `orig_settings_dict = self.connection.settings_dict`.
    *   Returns a new dictionary unpacking `orig_settings_dict` and overriding `'NAME'` with `'{}_{}'.format(orig_settings_dict['NAME'], suffix)`.

*   **`_clone_test_db(self, suffix, verbosity, keepdb=False)`**
    *   Raises `NotImplementedError("The database backend doesn't support cloning databases. Disable the option to run tests in parallel processes.")`.

*   **`destroy_test_db(self, old_database_name=None, verbosity=1, keepdb=False, suffix=None)`**
    *   Calls `self.connection.close()`.
    *   If `suffix is None`, sets `test_database_name = self.connection.settings_dict['NAME']`.
    *   Else, sets `test_database_name = self.get_test_db_clone_settings(suffix)['NAME']`.
    *   If `verbosity >= 1`:
        *   Determines the action string: `'Preserving'` if `keepdb` is `True`, else `'Destroying'`.
        *   Logs `"%s test database for alias %s..." % (action, self._get_database_display_str(verbosity, test_database_name))`.
    *   If `keepdb` is falsy, calls `self._destroy_test_db(test_database_name, verbosity)`.
    *   If `old_database_name is not None`:
        *   Sets `settings.DATABASES[self.connection.alias]["NAME"] = old_database_name`.
        *   Sets `self.connection.settings_dict["NAME"] = old_database_name`.

*   **`_destroy_test_db(self, test_database_name, verbosity)`**
    *   Enters a context manager: `with self._nodb_cursor() as cursor:`
        *   Executes `"DROP DATABASE %s" % self.connection.ops.quote_name(test_database_name)` on the `cursor`.

*   **`sql_table_creation_suffix(self)`**
    *   Returns `''`.

*   **`test_db_signature(self)`**
    *   Gets `settings_dict = self.connection.settings_dict`.
    *   Returns a tuple: `(settings_dict['HOST'], settings_dict['PORT'], settings_dict['ENGINE'], self._get_test_db_name())`.