## django/core/checks/model_checks.py
### 1. Module-Level Preamble

**Imports:**
*   `import inspect`
*   `import types`
*   `from itertools import chain`
*   `from django.apps import apps`
*   `from django.core.checks import Error, Tags, register`

---

### 2. Code Objects

#### `check_all_models`
*   **Signature:** `def check_all_models(app_configs=None, **kwargs)`
*   **Decorators:** `@register(Tags.models)`
*   **Implementation Logic:**
    1.  Initializes an empty list `errors`.
    2.  If `app_configs` is `None`, retrieves all models by calling `apps.get_models()`.
    3.  Otherwise, retrieves models by chaining the results of `app_config.get_models()` for each `app_config` in `app_configs` (using `chain.from_iterable`).
    4.  Iterates over each `model` in the retrieved models:
        *   Checks if `model.check` is a method using `inspect.ismethod(model.check)`.
        *   If it is *not* a method, appends an `Error` object to `errors` with:
            *   Message: `"The '%s.check()' class method is currently overridden by %r." % (model.__name__, model.check)`
            *   `obj`: `model`
            *   `id`: `'models.E020'`
        *   If it *is* a method, calls `model.check(**kwargs)` and extends the `errors` list with the returned results.
    5.  Returns the `errors` list.

#### `_check_lazy_references`
*   **Signature:** `def _check_lazy_references(apps, ignore=None)`
*   **Implementation Logic:**
    1.  Calculates `pending_models` as the set difference between `set(apps._pending_operations)` and `(ignore or set())`.
    2.  If `pending_models` is empty, short-circuits and returns an empty list `[]`.
    3.  Imports `signals` from `django.db.models`.
    4.  Creates a dictionary `model_signals` mapping `signal` to `name` for each `name, signal` in `vars(signals).items()` where `isinstance(signal, signals.ModelSignal)` is true.
    5.  **Nested Function `extract_operation(obj)`:**
        *   Initializes `operation, args, keywords = obj, [], {}`.
        *   Loops as long as `hasattr(operation, 'func')` is true:
            *   Extends `args` with `getattr(operation, 'args', []) or []`.
            *   Updates `keywords` with `getattr(operation, 'keywords', {}) or {}`.
            *   Sets `operation = operation.func`.
        *   Returns the tuple `(operation, args, keywords)`.
    6.  **Nested Function `app_model_error(model_key)`:**
        *   Attempts to call `apps.get_app_config(model_key[0])`.
        *   If successful, sets `model_error` to `"app '%s' doesn't provide model '%s'" % model_key`.
        *   If a `LookupError` is raised, sets `model_error` to `"app '%s' isn't installed" % model_key[0]`.
        *   Returns `model_error`.
    7.  **Nested Function `field_error(model_key, func, args, keywords)`:**
        *   Constructs an error message: `"The field %(field)s was declared with a lazy reference to '%(model)s', but %(model_error)s."`
        *   Formats the message using a dictionary where `'model'` is `'.'.join(model_key)`, `'field'` is `keywords['field']`, and `'model_error'` is `app_model_error(model_key)`.
        *   Returns an `Error` object with the formatted message, `obj=keywords['field']`, and `id='fields.E307'`.
    8.  **Nested Function `signal_connect_error(model_key, func, args, keywords)`:**
        *   Constructs an error message: `"%(receiver)s was connected to the '%(signal)s' signal with a lazy reference to the sender '%(model)s', but %(model_error)s."`
        *   Sets `receiver = args[0]`.
        *   Determines a `description` string based on the type of `receiver`:
            *   If `isinstance(receiver, types.FunctionType)`, description is `"The function '%s'" % receiver.__name__`.
            *   If `isinstance(receiver, types.MethodType)`, description is `"Bound method '%s.%s'" % (receiver.__self__.__class__.__name__, receiver.__name__)`.
            *   Otherwise, description is `"An instance of class '%s'" % receiver.__class__.__name__`.
        *   Retrieves `signal_name` using `model_signals.get(func.__self__, 'unknown')`.
        *   Formats the message using a dictionary where `'model'` is `'.'.join(model_key)`, `'receiver'` is `description`, `'signal'` is `signal_name`, and `'model_error'` is `app_model_error(model_key)`.
        *   Returns an `Error` object with the formatted message, `obj=receiver.__module__`, and `id='signals.E001'`.
    9.  **Nested Function `default_error(model_key, func, args, keywords)`:**
        *   Constructs an error message: `"%(op)s contains a lazy reference to %(model)s, but %(model_error)s."`
        *   Formats the message using a dictionary where `'op'` is `func`, `'model'` is `'.'.join(model_key)`, and `'model_error'` is `app_model_error(model_key)`.
        *   Returns an `Error` object with the formatted message, `obj=func`, and `id='models.E022'`.
    10. Defines a dictionary `known_lazy` mapping specific module/function name tuples to the nested error functions:
        *   `('django.db.models.fields.related', 'resolve_related_class')`: `field_error`
        *   `('django.db.models.fields.related', 'set_managed')`: `None`
        *   `('django.dispatch.dispatcher', 'connect')`: `signal_connect_error`
    11. **Nested Function `build_error(model_key, func, args, keywords)`:**
        *   Creates a `key` tuple: `(func.__module__, func.__name__)`.
        *   Retrieves `error_fn` from `known_lazy` using `key`, defaulting to `default_error`.
        *   If `error_fn` is truthy, returns the result of `error_fn(model_key, func, args, keywords)`. Otherwise, returns `None`.
    12. Generates a list of errors by iterating over each `model_key` in `pending_models` and each `func` in `apps._pending_operations[model_key]`. For each combination, it calls `build_error(model_key, *extract_operation(func))`.
    13. Filters out any `None` values from the generated errors.
    14. Returns the filtered list of errors, sorted by the `msg` attribute of each error (`key=lambda error: error.msg`).

#### `check_lazy_references`
*   **Signature:** `def check_lazy_references(app_configs=None, **kwargs)`
*   **Decorators:** `@register(Tags.models)`
*   **Implementation Logic:**
    1.  Calls `_check_lazy_references(apps)` and returns its result. (Note: `app_configs` and `kwargs` are ignored).