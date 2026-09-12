## django/db/models/fields/__init__.py
This is a comprehensive natural-language specification of the `django/db/models/fields/__init__.py` file, designed as a blueprint for a code-generation AI.

### 1. Module-Level Preamble

**Imports:**
*   Standard library: `collections.abc`, `copy`, `datetime`, `decimal`, `operator`, `uuid`, `warnings`.
*   From `base64`: `b64decode`, `b64encode`.
*   From `functools`: `partialmethod`, `total_ordering`.
*   From `django`: `forms`.
*   From `django.apps`: `apps`.
*   From `django.conf`: `settings`.
*   From `django.core`: `checks`, `exceptions`, `validators`.
*   From `django.db`: `connection`, `connections`, `router`.
*   From `django.db.models.constants`: `LOOKUP_SEP`.
*   From `django.db.models.query_utils`: `DeferredAttribute`, `RegisterLookupMixin`.
*   From `django.utils`: `timezone`.
*   From `django.utils.datastructures`: `DictWrapper`.
*   From `django.utils.dateparse`: `parse_date`, `parse_datetime`, `parse_duration`, `parse_time`.
*   From `django.utils.duration`: `duration_microseconds`, `duration_string`.
*   From `django.utils.functional`: `Promise`, `cached_property`.
*   From `django.utils.ipv6`: `clean_ipv6_address`.
*   From `django.utils.itercompat`: `is_iterable`.
*   From `django.utils.text`: `capfirst`.
*   From `django.utils.translation`: `gettext_lazy` as `_`.

**Constants & Globals:**
*   `__all__`: A list containing the names of all public field classes (e.g., `'AutoField'`, `'CharField'`, `'IntegerField'`, etc.) and constants like `'BLANK_CHOICE_DASH'`, `'Empty'`, `'NOT_PROVIDED'`.
*   `BLANK_CHOICE_DASH`: A list containing a single tuple `[("", "---------")]`, used as the default blank choice in select fields.

### 2. Code Objects (Classes and Functions)

**Utility Classes:**
*   `Empty`: An empty class used as a marker.
*   `NOT_PROVIDED`: An empty class used as a sentinel value for missing defaults.

**Utility Functions:**
*   `_load_field(app_label, model_name, field_name)`: Retrieves a field instance from a model using the app registry.
*   `_empty(of_cls)`: Creates an empty instance of a given class by instantiating `Empty` and changing its `__class__`.
*   `return_None()`: Simply returns `None`.

**Base Field Class:**
*   `Field(RegisterLookupMixin)`: The base class for all model fields. Decorated with `@total_ordering`.
    *   **Attributes:** `empty_strings_allowed = True`, `empty_values = list(validators.EMPTY_VALUES)`, `creation_counter = 0`, `auto_creation_counter = -1`, `default_validators = []`, `default_error_messages` (dict with keys like 'invalid_choice', 'null', 'blank', 'unique', 'unique_for_date'), `system_check_deprecated_details = None`, `system_check_removed_details = None`, `hidden = False`, `many_to_many = None`, `many_to_one = None`, `one_to_many = None`, `one_to_one = None`, `related_model = None`, `descriptor_class = DeferredAttribute`.
    *   **Methods:** `__init__` (accepts numerous field options like `verbose_name`, `name`, `primary_key`, `max_length`, `unique`, `blank`, `null`, `db_index`, `default`, `editable`, `choices`, `help_text`, `db_column`, etc.), `__str__`, `__repr__`, `check`, `_check_field_name`, `_check_choices`, `_check_db_index`, `_check_null_allowed_for_primary_keys`, `_check_backend_specific_checks`, `_check_validators`, `_check_deprecation_details`, `get_col`, `cached_col`, `select_format`, `deconstruct`, `clone`, `__eq__`, `__lt__`, `__hash__`, `__deepcopy__`, `get_internal_type`, `pre_save`, `get_prep_value`, `get_db_prep_value`, `get_db_prep_save`, `has_default`, `get_default`, `get_choices`, `value_to_string`, `to_python`, `clean`, `run_validators`, `validate`, `save_form_data`, `formfield`, `value_from_object`.

**Specific Field Types (Inheriting from `Field` or its subclasses):**
*   `BooleanField(Field)`: Represents a boolean (true/false) field. `empty_strings_allowed = False`.
*   `CharField(Field)`: Represents a string field. Requires `max_length`.
*   `CommaSeparatedIntegerField(CharField)`: Deprecated field for comma-separated integers.
*   `DateField(DateTimeCheckMixin, Field)`: Represents a date. Handles `auto_now` and `auto_now_add`.
*   `DateTimeField(DateField)`: Represents a date and time.
*   `DecimalField(Field)`: Represents a fixed-precision decimal number. Requires `max_digits` and `decimal_places`.
*   `DurationField(Field)`: Represents a time duration (Python `timedelta`).
*   `EmailField(CharField)`: A `CharField` that validates the input as an email address.
*   `FilePathField(Field)`: Represents a file path. Accepts `path`, `match`, `recursive`, `allow_files`, `allow_folders`.
*   `FloatField(Field)`: Represents a floating-point number.
*   `IntegerField(Field)`: Represents an integer.
*   `BigIntegerField(IntegerField)`: Represents a 64-bit integer.
*   `IPAddressField(Field)`: Deprecated field for IPv4 addresses.
*   `GenericIPAddressField(Field)`: Represents an IPv4 or IPv6 address. Accepts `protocol` and `unpack_ipv4`.
*   `NullBooleanField(BooleanField)`: Deprecated field for a boolean that can be null.
*   `PositiveIntegerField(PositiveIntegerRelDbTypeMixin, IntegerField)`: Represents a positive integer.
*   `PositiveSmallIntegerField(PositiveIntegerRelDbTypeMixin, IntegerField)`: Represents a positive small integer.
*   `SlugField(CharField)`: Represents a slug (short label containing only letters, numbers, underscores, or hyphens).
*   `SmallIntegerField(IntegerField)`: Represents a small integer (typically 16-bit).
*   `TextField(Field)`: Represents a large text field.
*   `TimeField(DateTimeCheckMixin, Field)`: Represents a time. Handles `auto_now` and `auto_now_add`.
*   `URLField(CharField)`: A `CharField` that validates the input as a URL.
*   `BinaryField(Field)`: Represents raw binary data.
*   `UUIDField(Field)`: Represents a Universally Unique Identifier (UUID).

**Auto Fields:**
*   `AutoFieldMixin`: A mixin for auto-incrementing primary key fields. Sets `db_returning = True`.
*   `AutoFieldMeta(type)`: Metaclass for `AutoField` to handle subclass checks.
*   `AutoField(AutoFieldMixin, IntegerField, metaclass=AutoFieldMeta)`: An integer field that automatically increments.
*   `BigAutoField(AutoFieldMixin, BigIntegerField)`: A 64-bit integer field that automatically increments.
*   `SmallAutoField(AutoFieldMixin, SmallIntegerField)`: A small integer field that automatically increments.

**Mixins:**
*   `DateTimeCheckMixin`: Provides a `check` method to verify that `auto_now` and `auto_now_add` are mutually exclusive, and that default values are not used with them.
*   `PositiveIntegerRelDbTypeMixin`: Provides a `rel_db_type` method to ensure related fields use the standard integer database type rather than the positive integer type, to maintain referential integrity across different database backends.