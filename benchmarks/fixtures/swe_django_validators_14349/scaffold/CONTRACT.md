# Implementation target
Write the module at `django/core/validators.py`.

## `django/core/validators.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BaseValidator`
- `DecimalValidator`
- `EMPTY_VALUES`
- `EmailValidator`
- `FileExtensionValidator`
- `MaxLengthValidator`
- `MaxValueValidator`
- `MinLengthValidator`
- `MinValueValidator`
- `ProhibitNullCharactersValidator`
- `RegexValidator`
- `URLValidator`
- `get_available_image_extensions`
- `int_list_validator`
- `integer_validator`
- `ip_address_validator_map`
- `ip_address_validators`
- `slug_re`
- `slug_unicode_re`
- `validate_comma_separated_integer_list`
- `validate_email`
- `validate_image_file_extension`
- `validate_integer`
- `validate_ipv46_address`
- `validate_ipv4_address`
- `validate_ipv6_address`
- `validate_slug`
- `validate_unicode_slug`

Implement them to satisfy the specification. Do not write tests.
