## django/core/validators.py
Now I have the complete file. Here is the full natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import ipaddress
import re
import warnings
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.deprecation import RemovedInDjango41Warning
from django.utils.encoding import punycode
from django.utils.ipv6 import is_valid_ipv6_address
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _, ngettext_lazy
```

### Constants & Globals

- **`EMPTY_VALUES`** — tuple `(None, '', [], (), {})`. Values that trigger the `self.required` check when passed to `validate()`.

---

## Code Objects

### Class `RegexValidator` (decorated with `@deconstructible`)

**Class attributes:**
- `regex = ''` — compiled regex pattern.
- `message = _('Enter a valid value.')` — default error message.
- `code = 'invalid'` — default error code.
- `inverse_match = False` — if `True`, validation fails when the regex *matches*.
- `flags = 0` — regex compilation flags.

**`__init__(self, regex=None, message=None, code=None, inverse_match=None, flags=None)`**
- For each parameter that is not `None`, assigns it to the corresponding instance attribute (`self.regex`, `self.message`, `self.code`, `self.inverse_match`, `self.flags`).
- If `flags` is truthy and `self.regex` is not a string (i.e., already compiled), raises `TypeError("If the flags are set, regex must be a regular expression string.")`.
- Compiles `self.regex` via `_lazy_re_compile(self.regex, self.flags)`, replacing whatever was assigned.

**`__call__(self, value)`**
- Converts `value` to `str(value)`, then calls `self.regex.search(...)` on it.
- If `inverse_match` is `False`: validation fails when there is **no match**.
- If `inverse_match` is `True`: validation fails when there **is a match**.
- On failure, raises `ValidationError(self.message, code=self.code)`.

**`__eq__(self, other)`**
- Returns `True` if `other` is an instance of `RegexValidator` and all of the following are equal: `self.regex.pattern == other.regex.pattern`, `self.regex.flags == other.regex.flags`, `self.message == other.message`, `self.code == other.code`, `self.inverse_match == other.inverse_match`. Otherwise returns `False`.

---

### Class `URLValidator(RegexValidator)` (decorated with `@deconstructible`)

**Class attributes:**
- `ul = '\u00a1-\uffff'` — Unicode letters range string.
- **`ipv4_re`** — pattern: `r'(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}'`.
- **`ipv6_re`** — pattern: `r'\[[0-9a-f:.]+\]'`.
- **`hostname_re`** — pattern: `r'[a-z' + ul + r'0-9](?:[a-z' + ul + r'0-9-]{0,61}[a-z' + ul + r'0-9])?'`.
- **`domain_re`** — pattern: `r'(?:\.(?!-)[a-z' + ul + r'0-9-]{1,63}(?<!-))*'`.
- **`tld_re`** — pattern built from: `\.` then `(?!-)`, then `(?:[a-z'+ul+'-]{2,63}|xn--[a-z0-9]{1,59})`, then `(?<!-)`, then `\.?`.
- **`host_re`** — concatenation of `'(' + hostname_re + domain_re + tld_re + '|localhost)'`.
- **`regex`** — compiled via `_lazy_re_compile(r'^(?:[a-z0-9.+-]*)://(?:[^\s:@/]+(?::[^\s:@/]*)?@)?(?:'+ipv4_re+'|'+ipv6_re+'|'+host_re+')(?::\d{2,5})?(?:[/?#][^\s]*)?\Z', re.IGNORECASE)`.
- `message = _('Enter a valid URL.')`
- `schemes = ['http', 'https', 'ftp', 'ftps']`

**`__init__(self, schemes=None, **kwargs)`**
- Calls `super().__init__(**kwargs)`.
- If `schemes is not None`, sets `self.schemes = schemes`.

**`__call__(self, value)`**
1. If `value` is not a string (`isinstance(value, str)`), raises `ValidationError(self.message, code=self.code)`.
2. Extracts the scheme: `scheme = value.split('://')[0].lower()`. If `scheme not in self.schemes`, raises `ValidationError(self.message, code=self.code)`.
3. Calls `super().__call__(value)` (the parent `RegexValidator.__call__`). On failure (`ValidationError`):
   - If `value` is truthy: attempts IDN fallback — calls `urlsplit(value)` to get `(scheme, netloc, path, query, fragment)`. If `urlsplit` raises `ValueError`, raises `ValidationError(self.message, code=self.code)`. Then tries `punycode(netloc)`; if that raises `UnicodeError`, re-raises the original validation error. Otherwise constructs a new URL via `urlunsplit((scheme, netloc, path, query, fragment))` and calls `super().__call__(url)` again.
   - If `value` is falsy: re-raises the original exception.
4. On success of step 3 (no exception): verifies IPv6 bracket notation — searches for `^\[(.+)\](?::\d{2,5})?$` in `urlsplit(value).netloc`. If a match is found, extracts the IP portion and calls `validate_ipv6_address(potential_ip)`. On `ValidationError`, raises `ValidationError(self.message, code=self.code)`.
5. Checks host name length: if `len(urlsplit(value).netloc) > 253`, raises `ValidationError(self.message, code=self.code)`.

---

### Module-level `integer_validator`

```python
integer_validator = RegexValidator(
    _lazy_re_compile(r'^-?\d+\Z'),
    message=_('Enter a valid integer.'),
    code='invalid',
)
```

### Function `validate_integer(value)`

Returns the result of calling `integer_validator(value)`.

---

### Class `EmailValidator` (not decorated with `@deconstructible`)

**Class attributes:**
- `message = _('Enter a valid email address.')`
- `code = 'invalid'`
- **`user_regex`** — compiled via `_lazy_re_compile(r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)", re.IGNORECASE)`. Matches dot-atom or quoted-string local parts.
- **`domain_regex`** — compiled via `_lazy_re_compile(r'((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))\Z', re.IGNORECASE)`.
- **`literal_regex`** — compiled via `_lazy_re_compile(r'\[([A-f0-9:.]+)\]\Z', re.IGNORECASE)`. Matches `[ip_address]` literal form.
- `domain_allowlist = ['localhost']`

**Property `domain_whitelist` (getter):**
- Emits a `RemovedInDjango41Warning` deprecation warning and returns `self.domain_allowlist`.

**Property `domain_whitelist` (setter):**
- Emits a `RemovedInDjango41Warning` deprecation warning and sets `self.domain_allowlist = allowlist`.

**`__init__(self, message=None, code=None, allowlist=None, *, whitelist=None)`**
- If `whitelist is not None`, assigns `allowlist = whitelist` and emits a `RemovedInDjango41Warning` deprecation warning.
- If `message is not None`, sets `self.message = message`.
- If `code is not None`, sets `self.code = code`.
- If `allowlist is not None`, sets `self.domain_allowlist = allowlist`.

**`__call__(self, value)`**
1. If `not value or '@' not in value`, raises `ValidationError(self.message, code=self.code)`.
2. Splits on `'@'` from the right: `user_part, domain_part = value.rsplit('@', 1)`.
3. If `self.user_regex.match(user_part)` fails, raises `ValidationError(self.message, code=self.code)`.
4. If `domain_part not in self.domain_allowlist and not self.validate_domain_part(domain_part)`:
   - Attempts `punycode(domain_part)`; on `UnicodeError`, passes (no fallback).
   - On success of punycoding, if `self.validate_domain_part(domain_part)` succeeds, returns normally.
   - Otherwise raises `ValidationError(self.message, code=self.code)`.

**`validate_domain_part(self, domain_part)`**
- If `self.domain_regex.match(domain_part)` matches, returns `True`.
- Otherwise tries `self.literal_regex.match(domain_part)`. On match, extracts the IP address from group 1 and calls `validate_ipv46_address(ip_address)`. On success returns `True`; on `ValidationError` passes. Returns `False` otherwise.

**`__eq__(self, other)`**
- Returns `True` if `other` is an instance of `EmailValidator` and all of: `self.domain_allowlist == other.domain_allowlist`, `self.message == other.message`, `self.code == other.code`. Otherwise returns `False`.

---

### Module-level `validate_email`

```python
validate_email = EmailValidator()
```

---

### Module-level regexes and validators

- **`slug_re`** — compiled via `_lazy_re_compile(r'^[-a-zA-Z0-9_]+\Z')`.
- **`validate_slug`** — `RegexValidator(slug_re, _('Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.'), 'invalid')`.
- **`slug_unicode_re`** — compiled via `_lazy_re_compile(r'^[-\w]+\Z')`.
- **`validate_unicode_slug`** — `RegexValidator(slug_unicode_re, _('Enter a valid "slug" consisting of Unicode letters, numbers, underscores, or hyphens.'), 'invalid')`.

---

### Function `validate_ipv4_address(value)`

Tries `ipaddress.IPv4Address(value)`. On `ValueError`, raises `ValidationError(_('Enter a valid IPv4 address.'), code='invalid')`.

---

### Function `validate_ipv6_address(value)`

If `not is_valid_ipv6_address(value)`, raises `ValidationError(_('Enter a valid IPv6 address.'), code='invalid')`.

---

### Function `validate_ipv46_address(value)`

Tries `validate_ipv4_address(value)`. On `ValidationError`, tries `validate_ipv6_address(value)`. If that also raises `ValidationError`, raises `ValidationError(_('Enter a valid IPv4 or IPv6 address.'), code='invalid')`.

---

### Module-level `ip_address_validator_map`

```python
ip_address_validator_map = {
    'both': ([validate_ipv46_address], _('Enter a valid IPv4 or IPv6 address.')),
    'ipv4': ([validate_ipv4_address], _('Enter a valid IPv4 address.')),
    'ipv6': ([validate_ipv6_address], _('Enter a valid IPv6 address.')),
}
```

---

### Function `ip_address_validators(protocol, unpack_ipv4)`

1. If `protocol != 'both' and unpack_ipv4`, raises `ValueError("You can only use \`unpack_ipv4\` if \`protocol\` is set to 'both'")`.
2. Looks up `ip_address_validator_map[protocol.lower()]`. On `KeyError`, raises `ValueError("The protocol '%s' is unknown. Supported: %s" % (protocol, list(ip_address_validator_map)))`.

---

### Function `int_list_validator(sep=',', message=None, code='invalid', allow_negative=False)`

Builds a regex pattern string via `_lazy_re_compile(r'^%(neg)s\d+(?:%(sep)s%(neg)s\d+)*\Z' % {'neg': '(-)?' if allow_negative else '', 'sep': re.escape(sep)})`. Returns `RegexValidator(regexp, message=message, code=code)`.

---

### Module-level `validate_comma_separated_integer_list`

```python
validate_comma_separated_integer_list = int_list_validator(
    message=_('Enter only digits separated by commas.'),
)
```

---

### Class `BaseValidator` (decorated with `@deconstructible`)

**Class attributes:**
- `message = _('Ensure this value is %(limit_value)s (it is %(show_value)s).')`
- `code = 'limit_value'`

**`__init__(self, limit_value, message=None)`**
- Sets `self.limit_value = limit_value`.
- If `message` is truthy, sets `self.message = message`.

**`__call__(self, value)`**
1. Calls `cleaned = self.clean(value)`.
2. Resolves `limit_value`: if `callable(self.limit_value)`, calls it; otherwise uses the attribute directly.
3. Builds `params = {'limit_value': limit_value, 'show_value': cleaned, 'value': value}`.
4. If `self.compare(cleaned, limit_value)` returns truthy, raises `ValidationError(self.message, code=self.code, params=params)`.

**`__eq__(self, other)`**
- Returns `NotImplemented` if `other` is not an instance of the same class. Otherwise checks: `self.limit_value == other.limit_value`, `self.message == other.message`, `self.code == other.code`.

**`compare(self, a, b)`** — default returns `a is not b`.
**`clean(self, x)`** — default returns `x` unchanged.

---

### Class `MaxValueValidator(BaseValidator)` (decorated with `@deconstructible`)

- **Class attributes:** `message = _('Ensure this value is less than or equal to %(limit_value)s.')`, `code = 'max_value'`.
- **`compare(self, a, b)`** — returns `a > b`. Validation fails when the cleaned value exceeds `limit_value`.

---

### Class `MinValueValidator(BaseValidator)` (decorated with `@deconstructible`)

- **Class attributes:** `message = _('Ensure this value is greater than or equal to %(limit_value)s.')`, `code = 'min_value'`.
- **`compare(self, a, b)`** — returns `a < b`. Validation fails when the cleaned value is below `limit_value`.

---

### Class `MinLengthValidator(BaseValidator)` (decorated with `@deconstructible`)

- **Class attributes:** `message = ngettext_lazy('Ensure this value has at least %(limit_value)d character (it has %(show_value)d).', 'Ensure this value has at least %(limit_value)d characters (it has %(show_value)d).', 'limit_value')`, `code = 'min_length'`.
- **`compare(self, a, b)`** — returns `a < b`. Validation fails when the length is less than `limit_value`.
- **`clean(self, x)`** — returns `len(x)`.

---

### Class `MaxLengthValidator(BaseValidator)` (decorated with `@deconstructible`)

- **Class attributes:** `message = ngettext_lazy('Ensure this value has at most %(limit_value)d character (it has %(show_value)d).', 'Ensure this value has at most %(limit_value)d characters (it has %(show_value)d).', 'limit_value')`, `code = 'max_length'`.
- **`compare(self, a, b)`** — returns `a > b`. Validation fails when the length exceeds `limit_value`.
- **`clean(self, x)`** — returns `len(x)`.

---

### Class `DecimalValidator` (decorated with `@deconstructible`)

**Class attributes:**
```python
messages = {
    'invalid': _('Enter a number.'),
    'max_digits': ngettext_lazy('Ensure that there are no more than %(max)s digit in total.', 'Ensure that there are no more than %(max)s digits in total.', 'max'),
    'max_decimal_places': ngettext_lazy('Ensure that there are no more than %(max)s decimal place.', 'Ensure that there are no more than %(max)s decimal places.', 'max'),
    'max_whole_digits': ngettext_lazy('Ensure that there are no more than %(max)s digit before the decimal point.', 'Ensure that there are no more than %(max)s digits before the decimal point.', 'max'),
}
```

**`__init__(self, max_digits, decimal_places)`** — sets `self.max_digits = max_digits`, `self.decimal_places = decimal_places`.

**`__call__(self, value)`**
1. Extracts `(digit_tuple, exponent) = value.as_tuple()[1:]` from a Python `Decimal` object.
2. If `exponent in {'F', 'n', 'N'}` (infinity, NaN, negative infinity), raises `ValidationError(self.messages['invalid'])`.
3. Computes digit counts:
   - **If `exponent >= 0`:** `digits = len(digit_tuple) + exponent`, `decimals = 0`.
   - **If `exponent < 0`:** If `abs(exponent) > len(digit_tuple)`, then `digits = decimals = abs(exponent)`. Otherwise, `digits = len(digit_tuple)`, `decimals = abs(exponent)`.
4. Computes `whole_digits = digits - decimals`.
5. If `self.max_digits is not None and digits > self.max_digits`: raises `ValidationError(self.messages['max_digits'], code='max_digits', params={'max': self.max_digits})`.
6. If `self.decimal_places is not None and decimals > self.decimal_places`: raises `ValidationError(self.messages['max_decimal_places'], code='max_decimal_places', params={'max': self.decimal_places})`.
7. If both `self.max_digits` and `self.decimal_places` are not `None` and `whole_digits > (self.max_digits - self.decimal_places)`: raises `ValidationError(self.messages['max_whole_digits'], code='max_whole_digits', params={'max': (self.max_digits - self.decimal_places)})`.

**`__eq__(self, other)`** — returns `True` if `other` is an instance of the same class and `self.max_digits == other.max_digits` and `self.decimal_places == other.decimal_places`. Otherwise returns `False`.

---

### Class `FileExtensionValidator` (decorated with `@deconstructible`)

**Class attributes:**
- `message = _('File extension "%(extension)s" is not allowed. Allowed extensions are: %(allowed_extensions)s.')`
- `code = 'invalid_extension'`

**`__init__(self, allowed_extensions=None, message=None, code=None)`**
- If `allowed_extensions is not None`, converts each element to lowercase: `[ext.lower() for ext in allowed_extensions]`.
- Sets `self.allowed_extensions = allowed_extensions`.
- If `message is not None`, sets `self.message = message`.
- If `code is not None`, sets `self.code = code`.

**`__call__(self, value)`**
1. Extracts the file extension: `extension = Path(value.name).suffix[1:].lower()`. (Strips the leading dot and lowercases.)
2. If `self.allowed_extensions is not None and extension not in self.allowed_extensions`, raises `ValidationError(self.message, code=self.code, params={'extension': extension, 'allowed_extensions': ', '.join(self.allowed_extensions)})`.

**`__eq__(self, other)`** — returns `True` if `other` is an instance of the same class and all of: `self.allowed_extensions == other.allowed_extensions`, `self.message == other.message`, `self.code == other.code`. Otherwise returns `False`.

---

### Function `get_available_image_extensions()`

1. Tries to import `PIL.Image`. On `ImportError`, returns `[]`.
2. Calls `Image.init()`. Returns `[ext.lower()[1:] for ext in Image.EXTENSION]` — the list of image extensions supported by Pillow, with leading dots stripped and lowercased.

---

### Function `validate_image_file_extension(value)`

Returns the result of calling `FileExtensionValidator(allowed_extensions=get_available_image_extensions())(value)`.

---

### Class `ProhibitNullCharactersValidator` (decorated with `@deconstructible`)

**Class attributes:**
- `message = _('Null characters are not allowed.')`
- `code = 'null_characters_not_allowed'`

**`__init__(self, message=None, code=None)`**
- If `message is not None`, sets `self.message = message`.
- If `code is not None`, sets `self.code = code`.

**`__call__(self, value)`**
- Converts `value` to string via `str(value)`. If `'\x00' in str(value)`, raises `ValidationError(self.message, code=self.code)`.

**`__eq__(self, other)`** — returns `True` if `other` is an instance of the same class and `self.message == other.message` and `self.code == other.code`. Otherwise returns `False`.

## django/forms/fields.py
I now have the full file content. Here is the complete natural-language specification:

---

# Module Specification: `django/forms/fields.py`

## 1. Module-Level Preamble

### Imports

```python
import copy
import datetime
import json
import math
import operator
import os
import re
import uuid
import warnings
from decimal import Decimal, DecimalException
from io import BytesIO

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.forms.boundfield import BoundField
from django.forms.utils import from_current_timezone, to_current_timezone
from django.forms.widgets import (
    FILE_INPUT_CONTRADICTION,
    CheckboxInput, ClearableFileInput, DateInput, DateTimeInput,
    EmailInput, FileInput, HiddenInput, MultipleHiddenInput,
    NullBooleanSelect, NumberInput, Select, SelectMultiple,
    SplitDateTimeWidget, SplitHiddenDateTimeWidget, Textarea,
    TextInput, TimeInput, URLInput,
)
from django.utils import formats
from django.utils.choices import normalize_choices
from django.utils.dateparse import parse_datetime, parse_duration
from django.utils.deprecation import RemovedInDjango60Warning
from django.utils.duration import duration_string
from django.utils.ipv6 import MAX_IPV6_ADDRESS_LENGTH, clean_ipv6_address
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _, ngettext_lazy
```

### `__all__` (exported names)

A tuple of 28 strings: `"Field"`, `"CharField"`, `"IntegerField"`, `"DateField"`, `"TimeField"`, `"DateTimeField"`, `"DurationField"`, `"RegexField"`, `"EmailField"`, `"FileField"`, `"ImageField"`, `"URLField"`, `"BooleanField"`, `"NullBooleanField"`, `"ChoiceField"`, `"MultipleChoiceField"`, `"ComboField"`, `"MultiValueField"`, `"FloatField"`, `"DecimalField"`, `"SplitDateTimeField"`, `"GenericIPAddressField"`, `"FilePathField"`, `"JSONField"`, `"SlugField"`, `"TypedChoiceField"`, `"TypedMultipleChoiceField"`, `"UUIDField"`.

### Module-Level Constants & Globals

- `re_decimal` — a compiled regex pattern (`_lazy_re_compile(r"\.0*\s*$")`) used by `IntegerField.to_python` to strip trailing decimal points and zeros from numeric strings.

---

## 2. Code Objects

### Class: `Field` (inherits `object`)

**Class attributes:**
- `widget = TextInput` — default widget class for rendering.
- `hidden_widget = HiddenInput` — default widget class when rendered as hidden.
- `default_validators = []` — empty list of validators.
- `default_error_messages = {"required": _("This field is required.")}` — lazy-translated string.
- `empty_values = list(validators.EMPTY_VALUES)` — the list of values Django considers "empty" (e.g., `None`, `""`, `[]`, `{}`).
- `bound_field_class = None`

**`__init__(self, *, required=True, widget=None, label=None, initial=None, help_text="", error_messages=None, show_hidden_initial=False, validators=(), localize=False, disabled=False, label_suffix=None, template_name=None, bound_field_class=None)`**

1. Assigns `required`, `label`, `initial`, `show_hidden_initial`, `help_text`, `disabled`, `label_suffix` to instance attributes.
2. Sets `bound_field_class = bound_field_class or self.bound_field_class`.
3. Resolves widget: if `widget is None`, uses `self.widget`; if it's a class, instantiates it; otherwise deep-copies the provided widget instance.
4. If `localize` is truthy, sets `widget.is_localized = True`.
5. Sets `widget.is_required = self.required`.
6. Calls `self.widget_attrs(widget)` and merges returned dict into `widget.attrs`.
7. Stores resolved widget as `self.widget`.
8. Builds `error_messages`: iterates the class MRO in reverse, collecting all `default_error_messages` dicts from each ancestor; then updates with `error_messages or {}`.
9. Sets `self.validators = [*self.default_validators, *validators]`.
10. Stores `template_name`.
11. Calls `super().__init__()`.

**Attributes set on instance:** `required`, `label`, `initial`, `show_hidden_initial`, `help_text`, `disabled`, `label_suffix`, `bound_field_class`, `localize`, `widget`, `error_messages`, `validators`, `template_name`.

**`prepare_value(self, value)`** — Returns `value` unchanged.

**`to_python(self, value)`** — Returns `value` unchanged.

**`validate(self, value)`** — If `value in self.empty_values and self.required`, raises `ValidationError` with message key `"required"`.

**`run_validators(self, value)`** — If `value in self.empty_values`, returns immediately. Otherwise iterates each validator in `self.validators`; if a validator raises `ValidationError` and the exception has an `.error_messages` code that matches a key in `self.error_messages`, replaces the error message with the localized one from `self.error_messages`. Collects all errors into a list; if non-empty, raises `ValidationError(errors)`.

**`clean(self, value)`** — Calls `self.to_python(value)`, then `self.validate(value)`, then `self.run_validators(value)`. Returns the cleaned value.

**`bound_data(self, data, initial)`** — If `self.disabled`, returns `initial`; otherwise returns `data`.

**`widget_attrs(self, widget)`** — Returns `{}` (empty dict). Overridable by subclasses to add HTML attributes.

**`has_changed(self, initial, data)`** — If `self.disabled`, returns `False`. Otherwise: tries `to_python(data)`, and if the field has a `_coerce` method, compares `_coerce(data) != _coerce(initial)`. On `ValidationError`, returns `True`. Falls back to comparing `initial or ""` vs `data or ""` (treating `None` as empty string). Returns whether they differ.

**`get_bound_field(self, form, field_name)`** — Resolves the bound field class from `self.bound_field_class or form.bound_field_class or BoundField`, then returns an instance of that class with `(form, self, field_name)`.

**`__deepcopy__(self, memo)`** — Creates a shallow copy via `copy.copy(self)`, registers it in `memo`, deep-copies the widget and error_messages dict, slices the validators list, and returns the result.

**`_clean_bound_field(self, bf)`** — If disabled, uses `bf.initial`; otherwise uses `bf.data`. Calls `self.clean(value)` on that value and returns it.

---

### Class: `CharField(Field)`

**Class attributes:** none beyond inherited.

**`__init__(self, *, max_length=None, min_length=None, strip=True, empty_value="", **kwargs)`**
1. Sets `max_length`, `min_length`, `strip`, `empty_value`.
2. Calls `super().__init__(**kwargs)`.
3. If `min_length is not None`, appends `validators.MinLengthValidator(int(min_length))` to `self.validators`.
4. If `max_length is not None`, appends `validators.MaxLengthValidator(int(max_length))` to `self.validators`.
5. Appends `validators.ProhibitNullCharactersValidator()` to `self.validators`.

**`to_python(self, value)`** — If `value in self.empty_values`, returns `self.empty_value`. Otherwise converts `value` via `str(value)`, strips it if `self.strip` is truthy, and returns the result.

**`widget_attrs(self, widget)`** — Calls parent's `widget_attrs`; if `max_length` is set and widget is not hidden, adds `"maxlength": str(self.max_length)`; if `min_length` is set and widget is not hidden, adds `"minlength": str(self.min_length)`. Returns the dict.

---

### Class: `IntegerField(Field)`

**Class attributes:**
- `widget = NumberInput`
- `default_error_messages = {"invalid": _("Enter a whole number.")}`
- `re_decimal = _lazy_re_compile(r"\.0*\s*$")` — compiled regex for stripping trailing `.0*`.

**`__init__(self, *, max_value=None, min_value=None, step_size=None, **kwargs)`**
1. Sets `max_value`, `min_value`, `step_size`.
2. If `localize` is truthy and widget is `NumberInput`, overrides the widget to the parent class's default (`TextInput`).
3. Calls `super().__init__(**kwargs)`.
4. Appends `validators.MaxValueValidator(max_value)` if `max_value` is not None.
5. Appends `validators.MinValueValidator(min_value)` if `min_value` is not None.
6. Appends `validators.StepValueValidator(step_size, offset=min_value)` if `step_size` is not None.

**`to_python(self, value)`** — Calls parent's `to_python(value)`. If result is in `empty_values`, returns `None`. If `self.localize`, sanitizes separators via `formats.sanitize_separators(value)`. Strips trailing decimal/zeros using `re_decimal.sub("", str(value))`, then converts to `int()`. On `ValueError`/`TypeError`, raises `ValidationError("invalid")`. Returns the integer.

**`widget_attrs(self, widget)`** — Calls parent's `widget_attrs`; if widget is a `NumberInput` instance, adds `"min"`, `"max"`, and/or `"step"` attributes from corresponding instance attributes (only if not None). Returns the dict.

---

### Class: `FloatField(IntegerField)`

**Class attributes:**
- `default_error_messages = {"invalid": _("Enter a number.")}`

**`to_python(self, value)`** — Calls `super(IntegerField, self).to_python(value)` (i.e., skips IntegerField's to_python, going directly to Field's identity version). If in empty values, returns `None`. If localized, sanitizes separators. Converts via `float(value)`, raising `ValidationError("invalid")` on failure. Returns the float.

**`validate(self, value)`** — Calls parent's `validate(value)`. If value is not empty and `not math.isfinite(value)`, raises `ValidationError("invalid")`.

**`widget_attrs(self, widget)`** — Calls parent's `widget_attrs`; if widget is a `NumberInput` and `"step"` not already in attrs, sets `"step"` to `str(self.step_size)` or `"any"`. Returns the dict.

---

### Class: `DecimalField(IntegerField)`

**Class attributes:**
- `default_error_messages = {"invalid": _("Enter a number.")}`

**`__init__(self, *, max_value=None, min_value=None, max_digits=None, decimal_places=None, **kwargs)`** — Sets `max_digits`, `decimal_places`. Calls parent's `__init__` with `max_value`, `min_value`. Appends `validators.DecimalValidator(max_digits, decimal_places)`.

**`to_python(self, value)`** — If in empty values, returns `None`. If localized, sanitizes separators. Converts via `Decimal(str(value))`; on `DecimalException`, raises `ValidationError("invalid")`. Returns the Decimal.

**`validate(self, value)`** — Calls parent's `validate(value)`. If not empty and `not value.is_finite()`, raises `ValidationError("invalid", params={"value": value})`.

**`widget_attrs(self, widget)`** — Calls parent's `widget_attrs`; if widget is a `NumberInput` and `"step"` not in attrs: if `decimal_places` is set, computes step as `str(Decimal(1).scaleb(-self.decimal_places)).lower()` (exponential notation); otherwise uses `"any"`. Returns the dict.

---

### Class: `BaseTemporalField(Field)`

**`__init__(self, *, input_formats=None, **kwargs)`** — Calls parent's `__init__`; if `input_formats is not None`, sets `self.input_formats = input_formats`.

**`to_python(self, value)`** — Strips whitespace from `value`. Iterates each format in `self.input_formats`, calling `self.strptime(value, format)`. On `(ValueError, TypeError)`, continues to next format. If all fail, raises `ValidationError("invalid")`.

**`strptime(self, value, format)`** — Raises `NotImplementedError` (must be overridden by subclasses).

---

### Class: `DateField(BaseTemporalField)`

**Class attributes:**
- `widget = DateInput`
- `input_formats = formats.get_format_lazy("DATE_INPUT_FORMATS")`
- `default_error_messages = {"invalid": _("Enter a valid date.")}`

**`to_python(self, value)`** — If in empty values, returns `None`. If already a `datetime.datetime`, returns `.date()`. If already a `datetime.date`, returns it unchanged. Otherwise calls parent's `to_python(value)`.

**`strptime(self, value, format)`** — Returns `datetime.datetime.strptime(value, format).date()`.

---

### Class: `TimeField(BaseTemporalField)`

**Class attributes:**
- `widget = TimeInput`
- `input_formats = formats.get_format_lazy("TIME_INPUT_FORMATS")`
- `default_error_messages = {"invalid": _("Enter a valid time.")}`

**`to_python(self, value)`** — If in empty values, returns `None`. If already a `datetime.time`, returns it unchanged. Otherwise calls parent's `to_python(value)`.

**`strptime(self, value, format)`** — Returns `datetime.datetime.strptime(value, format).time()`.

---

### Class: `DateTimeFormatsIterator`

**`__iter__(self)`** — Yields all formats from `formats.get_format("DATETIME_INPUT_FORMATS")`, then yields all formats from `formats.get_format("DATE_INPUT_FORMATS")`. A lazy iterator used as the `input_formats` for `DateTimeField`.

---

### Class: `DateTimeField(BaseTemporalField)`

**Class attributes:**
- `widget = DateTimeInput`
- `input_formats = DateTimeFormatsIterator()` — an instance of the iterator.
- `default_error_messages = {"invalid": _("Enter a valid date/time.")}`

**`prepare_value(self, value)`** — If `value` is a `datetime.datetime`, converts it to current timezone via `to_current_timezone(value)`. Returns the result.

**`to_python(self, value)`** — If in empty values, returns `None`. If already a `datetime.datetime`, returns it converted to current timezone via `from_current_timezone(value)`. If already a `datetime.date`, constructs `datetime.datetime(year, month, day)` and converts to current timezone. Otherwise: tries `parse_datetime(value.strip())`; on `ValueError`, raises `ValidationError("invalid")`. If the result is falsy (None), falls back to parent's `to_python(value)`. Returns the result converted via `from_current_timezone(result)`.

**`strptime(self, value, format)`** — Returns `datetime.datetime.strptime(value, format)`.

---

### Class: `DurationField(Field)`

**Class attributes:**
- `default_error_messages = {"invalid": _("Enter a valid duration."), "overflow": _("The number of days must be between {min_days} and {max_days}.")}`

**`prepare_value(self, value)`** — If `value` is a `datetime.timedelta`, returns `duration_string(value)`. Otherwise returns `value`.

**`to_python(self, value)`** — If in empty values, returns `None`. If already a `datetime.timedelta`, returns it. Otherwise: tries `parse_duration(str(value))`; on `OverflowError`, raises `ValidationError("overflow", params={"min_days": datetime.timedelta.min.days, "max_days": datetime.timedelta.max.days})`. If the result is `None`, raises `ValidationError("invalid")`. Returns the timedelta.

---

### Class: `RegexField(CharField)`

**`__init__(self, regex, **kwargs)`** — Sets `strip=False` in kwargs via `setdefault`. Calls parent's `__init__(**kwargs)`. Then calls `self._set_regex(regex)`.

**`_get_regex(self)`** — Returns `self._regex`.

**`_set_regex(self, regex)`** — If `regex` is a string, compiles it via `re.compile(regex)`. Stores as `self._regex`. If the field already has `_regex_validator` in its validators list, removes it. Creates a new `validators.RegexValidator(regex=regex)`, stores it as `self._regex_validator`, and appends to `self.validators`.

**`regex = property(_get_regex, _set_regex)`** — Read-write property for the compiled regex.

---

### Class: `EmailField(CharField)`

**Class attributes:**
- `widget = EmailInput`
- `default_validators = [validators.validate_email]`

**`__init__(self, **kwargs)`** — Sets default `max_length=320`. Calls parent's `__init__(strip=True, **kwargs)`.

---

### Class: `FileField(Field)`

**Class attributes:**
- `widget = ClearableFileInput`
- `default_error_messages = {"invalid": _("No file was submitted. Check the encoding type on the form."), "missing": _("No file was submitted."), "empty": _("The submitted file is empty."), "max_length": ngettext_lazy("Ensure this filename has at most %(max)d character (it has %(length)d).", "Ensure this filename has at most %(max)d characters (it has %(length)d).", "max"), "contradiction": _("Please either submit a file or check the clear checkbox, not both.")}`

**`__init__(self, *, max_length=None, allow_empty_file=False, **kwargs)`** — Sets `max_length`, `allow_empty_file`. Calls parent's `__init__(**kwargs)`.

**`to_python(self, data)`** — If in empty values, returns `None`. Tries to read `data.name` and `data.size`; on `AttributeError`, raises `ValidationError("invalid")`. If `max_length` is set and `len(file_name) > max_length`, raises `ValidationError("max_length", params={"max": ..., "length": ...})`. If `not file_name`, raises `ValidationError("invalid")`. If not `allow_empty_file` and `not file_size`, raises `ValidationError("empty")`. Returns the data.

**`clean(self, data, initial=None)`** — If `data is FILE_INPUT_CONTRADICTION`, raises `ValidationError("contradiction")`. If `data is False`: if not required, returns `False`; otherwise treats as `None`. If `not data and initial`, returns `initial`. Otherwise calls parent's `clean(data)`.

**`bound_data(self, _, initial)`** — Always returns `initial`.

**`has_changed(self, initial, data)`** — Returns `not self.disabled and data is not None`.

**`_clean_bound_field(self, bf)`** — Uses `bf.initial` if disabled, else `bf.data`. Calls `self.clean(value, bf.initial)`.

---

### Class: `ImageField(FileField)`

**Class attributes:**
- `default_validators = [validators.validate_image_file_extension]`
- `default_error_messages = {"invalid_image": _("Upload a valid image. The file you uploaded was either not an image or a corrupted image.")}`

**`to_python(self, data)`** — Calls parent's `to_python(data)`. If result is `None`, returns `None`. Imports `PIL.Image`. Gets a file object: if `data` has `.temporary_file_path()`, uses that; else if it has `.read()`, wraps in `BytesIO(data.read())`; else uses `BytesIO(data["content"])`. Opens image via `Image.open(file)`, calls `image.verify()` immediately. Stores the image on the result as `f.image = image` and sets `f.content_type = Image.MIME.get(image.format)`. On any exception, raises `ValidationError("invalid_image")`. If `f` has a callable `.seek()`, seeks to 0. Returns `f`.

**`widget_attrs(self, widget)`** — Calls parent's `widget_attrs`; if widget is a `FileInput` and `"accept"` not in attrs, sets `"accept": "image/*"`. Returns the dict.

---

### Class: `URLField(CharField)`

**Class attributes:**
- `widget = URLInput`
- `default_error_messages = {"invalid": _("Enter a valid URL.")}`
- `default_validators = [validators.URLValidator()]`

**`__init__(self, *, assume_scheme=None, **kwargs)`** — If `assume_scheme is None`: if `settings.FORMS_URLFIELD_ASSUME_HTTPS`, sets to `"https"`; otherwise emits a `RemovedInDjango60Warning` (deprecation warning about default scheme changing from `'http'` to `'https'`) and sets to `"http"`. Stores as `self.assume_scheme`. Calls parent's `__init__(strip=True, **kwargs)`.

**`to_python(self, value)`** — Calls parent's `to_python(value)`. If result is truthy: detects scheme via `value.partition(":")`; if no separator found, or scheme is empty/non-ASCII-first/non-alpha-first/contains `/`, prepends the assumed scheme (scheme-relative URLs `"//..."` get `assume_scheme + ":" + value`; others get `assume_scheme + "://" + value`). Returns the result.

---

### Class: `BooleanField(Field)`

**Class attributes:**
- `widget = CheckboxInput`

**`to_python(self, value)`** — If `value` is a string and `value.lower()` in `("false", "0")`, sets to `False`. Otherwise converts via `bool(value)`. Calls parent's `to_python(value)` (which returns the boolean). Returns it.

**`validate(self, value)`** — If not value and required, raises `ValidationError("required")`.

**`has_changed(self, initial, data)`** — If disabled, returns `False`. Otherwise converts both via `self.to_python()` and compares for inequality.

---

### Class: `NullBooleanField(BooleanField)`

**Class attributes:**
- `widget = NullBooleanSelect`

**`to_python(self, value)`** — If in `(True, "True", "true", "1")`, returns `True`. If in `(False, "False", "false", "0")`, returns `False`. Otherwise returns `None`.

**`validate(self, value)`** — Does nothing (pass).

---

### Class: `ChoiceField(Field)`

**Class attributes:**
- `widget = Select`
- `default_error_messages = {"invalid_choice": _("Select a valid choice. %(value)s is not one of the available choices.")}`

**`__init__(self, *, choices=(), **kwargs)`** — Calls parent's `__init__(**kwargs)`. Sets `self.choices = choices`.

**`__deepcopy__(self, memo)`** — Calls parent's `__deepcopy__`, then deep-copies `self._choices` and stores it. Returns the result.

**`choices` property (getter)** — Returns `self._choices`.

**`choices` setter** — Normalizes via `normalize_choices(value)`, sets both `self._choices` and `self.widget.choices` to the normalized value.

**`to_python(self, value)`** — If in empty values, returns `""`. Otherwise returns `str(value)`.

**`validate(self, value)`** — Calls parent's `validate(value)`. If truthy and not `self.valid_value(value)`, raises `ValidationError("invalid_choice", params={"value": value})`.

**`valid_value(self, value)`** — Converts to string. Iterates choices: for each `(k, v)` pair, if `v` is a list/tuple (optgroup), iterates nested options and checks equality with the nested key; otherwise checks direct equality. Returns `True` on first match, else `False`.

---

### Class: `TypedChoiceField(ChoiceField)`

**`__init__(self, *, coerce=lambda val: val, empty_value="", **kwargs)`** — Sets `coerce`, `empty_value`. Calls parent's `__init__(**kwargs)`.

**`_coerce(self, value)`** — If `value == self.empty_value or in empty_values`, returns `self.empty_value`. Otherwise tries `self.coerce(value)`; on `(ValueError, TypeError, ValidationError)`, raises `ValidationError("invalid_choice", params={"value": value})`. Returns the coerced value.

**`clean(self, value)`** — Calls parent's `clean(value)`, then `_coerce(result)`. Returns it.

---

### Class: `MultipleChoiceField(ChoiceField)`

**Class attributes:**
- `hidden_widget = MultipleHiddenInput`
- `widget = SelectMultiple`
- `default_error_messages = {"invalid_choice": _("Select a valid choice. %(value)s is not one of the available choices."), "invalid_list": _("Enter a list of values.")}`

**`to_python(self, value)`** — If falsy, returns `[]`. If not a list/tuple, raises `ValidationError("invalid_list")`. Otherwise returns `[str(val) for val in value]`.

**`validate(self, value)`** — If required and empty, raises `ValidationError("required")`. For each value, if not `self.valid_value(val)`, raises `ValidationError("invalid_choice", params={"value": val})`.

**`has_changed(self, initial, data)`** — If disabled, returns `False`. Normalizes both to lists (None → `[]`). If lengths differ, returns `True`. Compares sets of stringified values; returns whether they differ.

---

### Class: `TypedMultipleChoiceField(MultipleChoiceField)`

**`__init__(self, *, coerce=lambda val: val, **kwargs)`** — Sets `coerce`, pops `empty_value` from kwargs (defaulting to `[]`). Calls parent's `__init__(**kwargs)`.

**`_coerce(self, value)`** — If `value == self.empty_value or in empty_values`, returns `self.empty_value`. Otherwise builds a new list by coercing each choice; on coercion failure, raises `ValidationError("invalid_choice", params={"value": choice})`. Returns the new list.

**`clean(self, value)`** — Calls parent's `clean(value)`, then `_coerce(result)`. Returns it.

**`validate(self, value)`** — If not equal to empty_value, calls parent's `validate(value)`. Else if required, raises `ValidationError("required")`.

---

### Class: `ComboField(Field)`

**`__init__(self, fields, **kwargs)`** — Calls parent's `__init__(**kwargs)`. Sets `f.required = False` for each field in the list. Stores as `self.fields`.

**`clean(self, value)`** — Calls parent's `clean(value)`. Iterates each field in `self.fields`, calling `field.clean(value)` and reassigning the result to `value`. Returns the final value.

---

### Class: `MultiValueField(Field)`

**Class attributes:**
- `default_error_messages = {"invalid": _("Enter a list of values."), "incomplete": _("Enter a complete value.")}`

**`__init__(self, fields, *, require_all_fields=True, **kwargs)`** — Sets `require_all_fields`. Calls parent's `__init__(**kwargs)`. For each field in `fields`: sets its error_messages `"incomplete"` to this field's `"incomplete"` message; if disabled, sets the field's `disabled = True`; if `require_all_fields`, sets the field's `required = False`. Stores as `self.fields`.

**`__deepcopy__(self, memo)`** — Calls parent's `__deepcopy__`, then deep-copies each field in `self.fields` into a tuple. Returns the result.

**`validate(self, value)`** — Does nothing (pass).

**`clean(self, value)`** — Initializes `clean_data = []`, `errors = []`. If disabled and not a list, decompresses via `self.widget.decompress(value)`. If falsy or is a list/tuple: if all values are empty, raises `"required"` if required, else returns `self.compress([])`. Otherwise (single non-list value), raises `"invalid"`. For each field at index `i`: gets `value[i]` (or `None` on IndexError). If the field value is empty: if `require_all_fields` and required, raises `"required"`; elif the individual field is required, adds an `"incomplete"` error (deduplicated) and skips. Otherwise calls `field.clean(field_value)` and appends to `clean_data`; collects any `ValidationError` errors (deduplicating). If errors collected, raises them all. Calls `self.compress(clean_data)`, then validates and runs validators on the compressed result. Returns it.

**`compress(self, data_list)`** — Raises `NotImplementedError` (must be overridden by subclasses).

**`has_changed(self, initial, data)`** — If disabled, returns `False`. If initial is None, creates a list of empty strings matching data length. Otherwise decompresses via widget if not already a list. Zips through fields/initial/data: converts each initial via `to_python`, on error returns `True`; calls `field.has_changed(initial, data)`, returning `True` on first difference. Returns `False`.

---

### Class: `FilePathField(ChoiceField)`

**`__init__(self, path, *, match=None, recursive=False, allow_files=True, allow_folders=False, **kwargs)`**
1. Sets `path`, `match`, `recursive`, `allow_files`, `allow_folders`.
2. Calls parent's `__init__(choices=(), **kwargs)`.
3. If required: sets `self.choices = []`; else: `[("", "---------")]`.
4. If `match is not None`: compiles via `re.compile(self.match)` → `self.match_re`.
5. If recursive: walks the directory tree with `os.walk(self.path)` (sorted). For each file, if `allow_files` and match passes, appends `(full_path, relative_path)`. For each dir, if `allow_folders`, name is not `"__pycache__"`, and match passes, appends similarly.
6. If non-recursive: scans the path with `os.scandir(self.path)`. Collects entries matching criteria (file/dir + optional regex), sorts by display name, extends choices.
7. Sets `self.widget.choices = self.choices`.

---

### Class: `SplitDateTimeField(MultiValueField)`

**Class attributes:**
- `widget = SplitDateTimeWidget`
- `hidden_widget = SplitHiddenDateTimeWidget`
- `default_error_messages = {"invalid_date": _("Enter a valid date."), "invalid_time": _("Enter a valid time.")}`

**`__init__(self, *, input_date_formats=None, input_time_formats=None, **kwargs)`** — Merges default error messages with any provided ones. Extracts `localize` from kwargs. Creates two fields: `DateField(input_formats=input_date_formats, error_messages={"invalid": errors["invalid_date"]}, localize=localize)` and `TimeField(input_formats=input_time_formats, error_messages={"invalid": errors["invalid_time"]}, localize=localize)`. Calls parent's `__init__(fields, **kwargs)`.

**`compress(self, data_list)`** — If data_list is truthy: if first element (date) is empty, raises `"invalid_date"`; if second (time) is empty, raises `"invalid_time"`. Combines via `datetime.datetime.combine(*data_list)`, converts to current timezone. Returns the datetime. If falsy, returns `None`.

---

### Class: `GenericIPAddressField(CharField)`

**`__init__(self, *, protocol="both", unpack_ipv4=False, **kwargs)`** — Sets `unpack_ipv4`. Sets `default_validators = validators.ip_address_validators(protocol, unpack_ipv4)`. Sets default `max_length = MAX_IPV6_ADDRESS_LENGTH`. Calls parent's `__init__(**kwargs)`.

**`to_python(self, value)`** — If in empty values, returns `""`. Strips whitespace. If non-empty and contains `":"`, calls `clean_ipv6_address(value, self.unpack_ipv4, max_length=self.max_length)`. Otherwise returns the stripped string.

---

### Class: `SlugField(CharField)`

**Class attributes:**
- `default_validators = [validators.validate_slug]`

**`__init__(self, *, allow_unicode=False, **kwargs)`** — Sets `allow_unicode`. If truthy, replaces `default_validators` with `[validators.validate_unicode_slug]`. Calls parent's `__init__(**kwargs)`.

---

### Class: `UUIDField(CharField)`

**Class attributes:**
- `default_error_messages = {"invalid": _("Enter a valid UUID.")}`

**`prepare_value(self, value)`** — If `value` is a `uuid.UUID`, returns `str(value)`. Otherwise returns `value`.

**`to_python(self, value)`** — Calls parent's `to_python(value)`. If in empty values, returns `None`. If not already a `uuid.UUID`, tries `uuid.UUID(value)`; on `ValueError`, raises `ValidationError("invalid")`. Returns the UUID.

---

### Class: `InvalidJSONInput(str)`

A simple subclass of `str` with no additional methods or attributes. Used as a sentinel type for JSON parsing failures in `JSONField.bound_data`.

---

### Class: `JSONString(str)`

A simple subclass of `str` with no additional methods or attributes. Returned by `JSONField.to_python` when the parsed JSON value is itself a string, to distinguish it from raw input strings.

---

### Class: `JSONField(CharField)`

**Class attributes:**
- `default_error_messages = {"invalid": _("Enter a valid JSON.")}`
- `widget = Textarea`

**`__init__(self, encoder=None, decoder=None, **kwargs)`** — Sets `encoder`, `decoder`. Calls parent's `__init__(**kwargs)`.

**`to_python(self, value)`** — If disabled, returns `value` unchanged. If in empty values, returns `None`. If already a list/dict/int/float/JSONString, returns it unchanged. Otherwise tries `json.loads(value, cls=self.decoder)`; on `json.JSONDecodeError`, raises `ValidationError("invalid", params={"value": value})`. If the parsed result is a string, wraps in `JSONString(converted)`. Returns the parsed object.

**`bound_data(self, data, initial)`** — If disabled, returns `initial`. If `data is None`, returns `None`. Otherwise tries `json.loads(data, cls=self.decoder)`; on `json.JSONDecodeError`, returns `InvalidJSONInput(data)`.

**`prepare_value(self, value)`** — If `value` is an `InvalidJSONInput`, returns it unchanged. Otherwise calls `json.dumps(value, ensure_ascii=False, cls=self.encoder)`.

**`has_changed(self, initial, data)`** — Calls parent's `has_changed(initial, data)`; if truthy, returns `True`. Otherwise compares `json.dumps(initial, sort_keys=True, cls=self.encoder)` with `json.dumps(self.to_python(data), sort_keys=True, cls=self.encoder)`, returning whether they differ. This ensures semantic equality (e.g., `True` vs `1`, key order independence).