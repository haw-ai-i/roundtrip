## django/core/management/commands/dumpdata.py
**1. Module-Level Preamble:**

*   **Imports:**
    *   `import warnings`
    *   `from django.apps import apps`
    *   `from django.core import serializers`
    *   `from django.core.management.base import BaseCommand, CommandError`
    *   `from django.core.management.utils import parse_apps_and_model_labels`
    *   `from django.db import DEFAULT_DB_ALIAS, router`

*   **Constants & Globals:** None.

**2. Code Objects (Classes and Functions):**

*   **Class `ProxyModelWarning`:**
    *   **Header:** `class ProxyModelWarning(Warning):`
    *   **Implementation Logic:** An empty exception class inheriting from `Warning`.

*   **Class `Command`:**
    *   **Header:** `class Command(BaseCommand):`
    *   **Attributes:**
        *   `help`: A string describing the command: `"Output the contents of the database as a fixture of the given format (using each model's default manager unless --all is specified)."`
    *   **Method `add_arguments`:**
        *   **Header:** `def add_arguments(self, parser):`
        *   **Implementation Logic:** Adds the following arguments to the parser:
            *   `args`: `metavar='app_label[.ModelName]'`, `nargs='*'`, help text about restricting dumped data.
            *   `--format`: `default='json'`, help text about output serialization format.
            *   `--indent`: `type=int`, help text about indent level.
            *   `--database`: `default=DEFAULT_DB_ALIAS`, help text about nominating a specific database.
            *   `-e`, `--exclude`: `action='append'`, `default=[]`, help text about excluding apps/models.
            *   `--natural-foreign`: `action='store_true'`, `dest='use_natural_foreign_keys'`, help text about using natural foreign keys.
            *   `--natural-primary`: `action='store_true'`, `dest='use_natural_primary_keys'`, help text about using natural primary keys.
            *   `-a`, `--all`: `action='store_true'`, `dest='use_base_manager'`, help text about using Django's base manager.
            *   `--pks`: `dest='primary_keys'`, help text about dumping objects with given primary keys.
            *   `-o`, `--output`: help text about specifying the output file.
    *   **Method `handle`:**
        *   **Header:** `def handle(self, *app_labels, **options):`
        *   **Implementation Logic:**
            1.  Extracts options: `format`, `indent`, `using` (from `database`), `excludes` (from `exclude`), `output`, `show_traceback` (from `traceback`), `use_natural_foreign_keys`, `use_natural_primary_keys`, `use_base_manager`, `pks` (from `primary_keys`).
            2.  If `pks` is truthy, splits it by `','`, strips whitespace from each, and assigns to `primary_keys`. Otherwise, `primary_keys = []`.
            3.  Calls `parse_apps_and_model_labels(excludes)` to get `excluded_models` and `excluded_apps`.
            4.  **App/Model Resolution:**
                *   If `app_labels` is empty:
                    *   If `primary_keys` is truthy, raises `CommandError("You can only use --pks option with one model")`.
                    *   Creates `app_list` as a dict with keys from `apps.get_app_configs()` where `app_config.models_module is not None` and `app_config not in excluded_apps`, and values as `None`.
                *   If `app_labels` is not empty:
                    *   If `len(app_labels) > 1` and `primary_keys` is truthy, raises `CommandError("You can only use --pks option with one model")`.
                    *   Initializes `app_list = {}`.
                    *   Iterates over `label` in `app_labels`:
                        *   Tries to split `label` by `'.'` into `app_label` and `model_label`.
                        *   If successful:
                            *   Gets `app_config` via `apps.get_app_config(app_label)`. Raises `CommandError(str(e))` on `LookupError`.
                            *   If `app_config.models_module is None` or `app_config in excluded_apps`, `continue`.
                            *   Gets `model` via `app_config.get_model(model_label)`. Raises `CommandError("Unknown model: %s.%s" % (app_label, model_label))` on `LookupError`.
                            *   Gets or sets `app_list_value = app_list.setdefault(app_config, [])`.
                            *   If `app_list_value is not None` and `model not in app_list_value`, appends `model` to `app_list_value`.
                        *   If `ValueError` (no `.` in label):
                            *   If `primary_keys` is truthy, raises `CommandError("You can only use --pks option with one model")`.
                            *   Sets `app_label = label`.
                            *   Gets `app_config` via `apps.get_app_config(app_label)`. Raises `CommandError(str(e))` on `LookupError`.
                            *   If `app_config.models_module is None` or `app_config in excluded_apps`, `continue`.
                            *   Sets `app_list[app_config] = None`.
            5.  **Format Validation:**
                *   Checks if `format` is in `serializers.get_public_serializer_formats()`.
                *   If not, tries `serializers.get_serializer(format)`. If `serializers.SerializerDoesNotExist` is caught, passes.
                *   Raises `CommandError("Unknown serialization format: %s" % format)`.
            6.  **Inner Function `get_objects(count_only=False)`:**
                *   Calls `serializers.sort_dependencies(app_list.items())` to get `models`.
                *   Iterates over `model` in `models`:
                    *   If `model in excluded_models`, `continue`.
                    *   If `model._meta.proxy` and `model._meta.proxy_for_model not in models`, issues a `ProxyModelWarning` using `warnings.warn`.
                    *   If `not model._meta.proxy` and `router.allow_migrate_model(using, model)`:
                        *   Selects manager: `model._base_manager` if `use_base_manager` else `model._default_manager`.
                        *   Gets `queryset = objects.using(using).order_by(model._meta.pk.name)`.
                        *   If `primary_keys` is truthy, filters `queryset` by `pk__in=primary_keys`.
                        *   If `count_only`, yields `queryset.order_by().count()`.
                        *   Else, yields from `queryset.iterator()`.
            7.  **Serialization Execution:**
                *   Sets `self.stdout.ending = None`.
                *   Initializes `progress_output = None` and `object_count = 0`.
                *   If `output` is truthy, `self.stdout.isatty()` is true, and `options['verbosity'] > 0`:
                    *   Sets `progress_output = self.stdout`.
                    *   Sets `object_count = sum(get_objects(count_only=True))`.
                *   Opens `stream = open(output, 'w')` if `output` is truthy, else `None`.
                *   In a `try...finally` block:
                    *   Calls `serializers.serialize(format, get_objects(), indent=indent, use_natural_foreign_keys=use_natural_foreign_keys, use_natural_primary_keys=use_natural_primary_keys, stream=stream or self.stdout, progress_output=progress_output, object_count=object_count)`.
                    *   In `finally`, if `stream` is truthy, calls `stream.close()`.
                *   Catches `Exception as e`:
                    *   If `show_traceback` is truthy, re-raises the exception.
                    *   Else, raises `CommandError("Unable to serialize database: %s" % e)`.

## django/core/serializers/__init__.py
### 1. Module-Level Preamble

**Imports:**
*   `import importlib`
*   `from django.apps import apps`
*   `from django.conf import settings`
*   `from django.core.serializers.base import SerializerDoesNotExist`

**Constants & Globals:**
*   `BUILTIN_SERIALIZERS`: A dictionary mapping format strings to their built-in serializer module paths:
    ```python
    {
        "xml": "django.core.serializers.xml_serializer",
        "python": "django.core.serializers.python",
        "json": "django.core.serializers.json",
        "yaml": "django.core.serializers.pyyaml",
    }
    ```
*   `_serializers`: An empty dictionary `{}` used as a global registry for loaded serializers.

---

### 2. Code Objects (Classes and Functions)

#### `class BadSerializer`
*   **Base Classes:** None.
*   **Attributes:**
    *   `internal_use_only`: Class attribute, boolean `False`.
    *   `exception`: Instance attribute, initialized in `__init__`.
*   **Implementation Logic:**
    *   `__init__(self, exception)`: Stores the provided `exception` in `self.exception`.
    *   `__call__(self, *args, **kwargs)`: Raises `self.exception` when the instance is called.

#### `def register_serializer(format, serializer_module, serializers=None)`
*   **Signature:** `register_serializer(format, serializer_module, serializers=None)`
*   **Implementation Logic:**
    *   If `serializers` is `None` and the global `_serializers` dictionary is empty, calls `_load_serializers()`.
    *   Attempts to import `serializer_module` using `importlib.import_module(serializer_module)`.
    *   If an `ImportError` is caught:
        *   Instantiates `BadSerializer` with the caught exception.
        *   Creates a dynamic class named `'BadSerializerModule'` using `type('BadSerializerModule', (), {'Deserializer': bad_serializer, 'Serializer': bad_serializer})` and assigns it to the `module` variable.
    *   If `serializers` is `None`, assigns the `module` to the global `_serializers[format]`.
    *   Otherwise, assigns the `module` to the provided `serializers[format]` dictionary.

#### `def unregister_serializer(format)`
*   **Signature:** `unregister_serializer(format)`
*   **Implementation Logic:**
    *   If `_serializers` is empty, calls `_load_serializers()`.
    *   If `format` is not a key in `_serializers`, raises `SerializerDoesNotExist(format)`.
    *   Deletes the `format` key from `_serializers`.

#### `def get_serializer(format)`
*   **Signature:** `get_serializer(format)`
*   **Implementation Logic:**
    *   If `_serializers` is empty, calls `_load_serializers()`.
    *   If `format` is not a key in `_serializers`, raises `SerializerDoesNotExist(format)`.
    *   Returns the `Serializer` attribute of the module stored at `_serializers[format]`.

#### `def get_serializer_formats()`
*   **Signature:** `get_serializer_formats()`
*   **Implementation Logic:**
    *   If `_serializers` is empty, calls `_load_serializers()`.
    *   Returns a list of all keys in `_serializers` (e.g., `list(_serializers)`).

#### `def get_public_serializer_formats()`
*   **Signature:** `get_public_serializer_formats()`
*   **Implementation Logic:**
    *   If `_serializers` is empty, calls `_load_serializers()`.
    *   Returns a list of keys from `_serializers` where the corresponding module's `Serializer.internal_use_only` attribute evaluates to `False`.

#### `def get_deserializer(format)`
*   **Signature:** `get_deserializer(format)`
*   **Implementation Logic:**
    *   If `_serializers` is empty, calls `_load_serializers()`.
    *   If `format` is not a key in `_serializers`, raises `SerializerDoesNotExist(format)`.
    *   Returns the `Deserializer` attribute of the module stored at `_serializers[format]`.

#### `def serialize(format, queryset, **options)`
*   **Signature:** `serialize(format, queryset, **options)`
*   **Implementation Logic:**
    *   Calls `get_serializer(format)` and instantiates the returned class to create a serializer instance `s`.
    *   Calls `s.serialize(queryset, **options)`.
    *   Returns the result of `s.getvalue()`.

#### `def deserialize(format, stream_or_string, **options)`
*   **Signature:** `deserialize(format, stream_or_string, **options)`
*   **Implementation Logic:**
    *   Calls `get_deserializer(format)` to retrieve the deserializer callable `d`.
    *   Returns the result of calling `d(stream_or_string, **options)`.

#### `def _load_serializers()`
*   **Signature:** `_load_serializers()`
*   **Implementation Logic:**
    *   Declares `_serializers` as global.
    *   Initializes a local dictionary `serializers = {}`.
    *   Iterates over each `format` in `BUILTIN_SERIALIZERS`:
        *   Calls `register_serializer(format, BUILTIN_SERIALIZERS[format], serializers)`.
    *   Checks if the `settings` object has a `"SERIALIZATION_MODULES"` attribute. If it does:
        *   Iterates over each `format` in `settings.SERIALIZATION_MODULES`:
            *   Calls `register_serializer(format, settings.SERIALIZATION_MODULES[format], serializers)`.
    *   Assigns the local `serializers` dictionary to the global `_serializers` variable.

#### `def sort_dependencies(app_list)`
*   **Signature:** `sort_dependencies(app_list)`
*   **Implementation Logic:**
    *   Initializes an empty list `model_dependencies` and an empty set `models`.
    *   Iterates over `(app_config, model_list)` pairs in `app_list`:
        *   If `model_list` is `None`, assigns `app_config.get_models()` to `model_list`.
        *   Iterates over each `model` in `model_list`:
            *   Adds `model` to the `models` set.
            *   Checks if `model` has a `'natural_key'` attribute.
                *   If true, retrieves `getattr(model.natural_key, 'dependencies', [])`. If this list is truthy, maps each dependency string `dep` to its model class using `apps.get_model(dep)` and assigns the resulting list to `deps`.
                *   If false, sets `deps = []`.
            *   Iterates over each `field` in `model._meta.fields`:
                *   If `field.remote_field` is truthy, gets `rel_model = field.remote_field.model`.
                *   If `rel_model` has a `'natural_key'` attribute and `rel_model != model`, appends `rel_model` to `deps`.
            *   Iterates over each `field` in `model._meta.many_to_many`:
                *   If `field.remote_field.through._meta.auto_created` is truthy, gets `rel_model = field.remote_field.model`.
                *   If `rel_model` has a `'natural_key'` attribute and `rel_model != model`, appends `rel_model` to `deps`.
            *   Appends the tuple `(model, deps)` to `model_dependencies`.
    *   Reverses the `model_dependencies` list in place.
    *   Initializes an empty list `model_list`.
    *   Enters a `while` loop that continues as long as `model_dependencies` is truthy:
        *   Initializes `skipped = []` and `changed = False`.
        *   Enters an inner `while` loop that continues as long as `model_dependencies` is truthy:
            *   Pops the last item `(model, deps)` from `model_dependencies`.
            *   Checks if all dependencies `d` in `deps` satisfy the condition: `d not in models or d in model_list`.
                *   If true, appends `model` to `model_list` and sets `changed = True`.
                *   If false, appends `(model, deps)` to `skipped`.
        *   If `changed` is `False` after the inner loop finishes, it means there is a circular dependency. Raises a `RuntimeError` with the message `"Can't resolve dependencies for %s in serialized app list." % ', '.join(model._meta.label for model, deps in sorted(skipped, key=lambda obj: obj[0].__name__))`.
        *   Assigns `skipped` to `model_dependencies` for the next iteration of the outer loop.
    *   Returns the sorted `model_list`.