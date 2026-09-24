## django/contrib/sessions/backends/base.py
```markdown
# Specification for `django/contrib/sessions/backends/base.py`

## 1. Module-Level Preamble

### Imports
```python
import base64
import logging
import string
import warnings
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.sessions.exceptions import SuspiciousSession
from django.core import signing
from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from django.utils.crypto import constant_time_compare, get_random_string, salted_hmac
from django.utils.deprecation import RemovedInDjango40Warning
from django.utils.module_loading import import_string
from django.utils.translation import LANGUAGE_SESSION_KEY
```

### Constants & Globals
*   `VALID_KEY_CHARS`: `string.ascii_lowercase + string.digits`

---

## 2. Code Objects

### `CreateError(Exception)`
An empty exception class used internally to catch creation errors from `save()`.

### `UpdateError(Exception)`
An empty exception class raised when trying to update a deleted session.

### `SessionBase`
Base class for all Session classes.

#### Class Attributes
*   `TEST_COOKIE_NAME`: `'testcookie'`
*   `TEST_COOKIE_VALUE`: `'worked'`
*   `__not_given`: `object()` (used as a sentinel value)

#### Methods

*   **`__init__(self, session_key=None)`**
    *   Sets `self._session_key = session_key` (invokes the property setter).
    *   Sets `self.accessed = False`.
    *   Sets `self.modified = False`.
    *   Sets `self.serializer = import_string(settings.SESSION_SERIALIZER)`.

*   **`__contains__(self, key)`**
    *   Returns `key in self._session`.

*   **`__getitem__(self, key)`**
    *   If `key == LANGUAGE_SESSION_KEY`, issues a `RemovedInDjango40Warning` with a specific message and `stacklevel=2`.
    *   Returns `self._session[key]`.

*   **`__setitem__(self, key, value)`**
    *   Sets `self._session[key] = value`.
    *   Sets `self.modified = True`.

*   **`__delitem__(self, key)`**
    *   Deletes `self._session[key]`.
    *   Sets `self.modified = True`.

*   **`key_salt` (property)**
    *   Returns `'django.contrib.sessions.' + self.__class__.__qualname__`.

*   **`get(self, key, default=None)`**
    *   Returns `self._session.get(key, default)`.

*   **`pop(self, key, default=__not_given)`**
    *   Sets `self.modified = self.modified or key in self._session`.
    *   If `default is self.__not_given`, calls and returns `self._session.pop(key)`. Otherwise, calls and returns `self._session.pop(key, default)`.

*   **`setdefault(self, key, value)`**
    *   If `key in self._session`, returns `self._session[key]`.
    *   Otherwise, sets `self.modified = True`, sets `self._session[key] = value`, and returns `value`.

*   **`set_test_cookie(self)`**
    *   Sets `self[self.TEST_COOKIE_NAME] = self.TEST_COOKIE_VALUE`.

*   **`test_cookie_worked(self)`**
    *   Returns `self.get(self.TEST_COOKIE_NAME) == self.TEST_COOKIE_VALUE`.

*   **`delete_test_cookie(self)`**
    *   Deletes `self[self.TEST_COOKIE_NAME]`.

*   **`_hash(self, value)`**
    *   Calculates a salt as `"django.contrib.sessions" + self.__class__.__name__`.
    *   Returns `salted_hmac(salt, value).hexdigest()`.

*   **`encode(self, session_dict)`**
    *   Returns `signing.dumps(session_dict, salt=self.key_salt, serializer=self.serializer, compress=True)`.

*   **`decode(self, session_data)`**
    *   Attempts to return `signing.loads(session_data, salt=self.key_salt, serializer=self.serializer)`.
    *   If any `Exception` is raised, catches it and returns `self._legacy_decode(session_data)`.

*   **`_legacy_decode(self, session_data)`**
    *   Base64 decodes `session_data.encode('ascii')`.
    *   Attempts to split the decoded bytes by `b':'` with a maxsplit of 1 into `hash` and `serialized`.
    *   Calculates `expected_hash = self._hash(serialized)`.
    *   If `not constant_time_compare(hash.decode(), expected_hash)`, raises `SuspiciousSession("Session data corrupted")`.
    *   Otherwise, returns `self.serializer().loads(serialized)`.
    *   If any `Exception` is raised during this process (e.g., `ValueError`, `SuspiciousOperation`):
        *   If the exception is an instance of `SuspiciousOperation`, logs a warning using a logger named `'django.security.%s' % e.__class__.__name__` with the string representation of the exception.
        *   Returns an empty dictionary `{}`.

*   **`update(self, dict_)`**
    *   Calls `self._session.update(dict_)`.
    *   Sets `self.modified = True`.

*   **`has_key(self, key)`**
    *   Returns `key in self._session`.

*   **`keys(self)`**
    *   Returns `self._session.keys()`.

*   **`values(self)`**
    *   Returns `self._session.values()`.

*   **`items(self)`**
    *   Returns `self._session.items()`.

*   **`clear(self)`**
    *   Sets `self._session_cache = {}`.
    *   Sets `self.accessed = True`.
    *   Sets `self.modified = True`.

*   **`is_empty(self)`**
    *   Attempts to return `not self._session_key and not self._session_cache`.
    *   If an `AttributeError` is raised (because `_session_cache` is not yet initialized), returns `True`.

*   **`_get_new_session_key(self)`**
    *   Loops indefinitely: generates a random string of length 32 using `VALID_KEY_CHARS`. If `not self.exists(session_key)`, returns it.

*   **`_get_or_create_session_key(self)`**
    *   If `self._session_key is None`, sets it to `self._get_new_session_key()`.
    *   Returns `self._session_key`.

*   **`_validate_session_key(self, key)`**
    *   Returns `key and len(key) >= 8`.

*   **`_get_session_key(self)`**
    *   Returns `self.__session_key`.

*   **`_set_session_key(self, value)`**
    *   If `self._validate_session_key(value)` is true, sets `self.__session_key = value`.
    *   Otherwise, sets `self.__session_key = None`.

*   **`session_key` (property)**
    *   Uses `_get_session_key` as the getter.

*   **`_session_key` (property)**
    *   Uses `_get_session_key` as the getter and `_set_session_key` as the setter.

*   **`_get_session(self, no_load=False)`**
    *   Sets `self.accessed = True`.
    *   Attempts to return `self._session_cache`.
    *   If an `AttributeError` is raised:
        *   If `self.session_key is None` or `no_load` is true, sets `self._session_cache = {}`.
        *   Otherwise, sets `self._session_cache = self.load()`.
        *   Returns `self._session_cache`.

*   **`_session` (property)**
    *   Uses `_get_session` as the getter.

*   **`get_session_cookie_age(self)`**
    *   Returns `settings.SESSION_COOKIE_AGE`.

*   **`get_expiry_age(self, **kwargs)`**
    *   Extracts `modification` from `kwargs`; defaults to `timezone.now()` if not present.
    *   Extracts `expiry` from `kwargs`; defaults to `self.get('_session_expiry')` if not present.
    *   If `not expiry` (handles `None` and `0`), returns `self.get_session_cookie_age()`.
    *   If `not isinstance(expiry, datetime)`, returns `expiry`.
    *   Calculates `delta = expiry - modification`.
    *   Returns `delta.days * 86400 + delta.seconds`.

*   **`get_expiry_date(self, **kwargs)`**
    *   Extracts `modification` from `kwargs`; defaults to `timezone.now()` if not present.
    *   Extracts `expiry` from `kwargs`; defaults to `self.get('_session_expiry')` if not present.
    *   If `isinstance(expiry, datetime)`, returns `expiry`.
    *   Sets `expiry = expiry or self.get_session_cookie_age()`.
    *   Returns `modification + timedelta(seconds=expiry)`.

*   **`set_expiry(self, value)`**
    *   If `value is None`: attempts to `del self['_session_expiry']` (ignoring `KeyError`), then returns.
    *   If `isinstance(value, timedelta)`, sets `value = timezone.now() + value`.
    *   Sets `self['_session_expiry'] = value`.

*   **`get_expire_at_browser_close(self)`**
    *   If `self.get('_session_expiry') is None`, returns `settings.SESSION_EXPIRE_AT_BROWSER_CLOSE`.
    *   Returns `self.get('_session_expiry') == 0`.

*   **`flush(self)`**
    *   Calls `self.clear()`.
    *   Calls `self.delete()`.
    *   Sets `self._session_key = None`.

*   **`cycle_key(self)`**
    *   Saves `data = self._session` and `key = self.session_key`.
    *   Calls `self.create()`.
    *   Sets `self._session_cache = data`.
    *   If `key` is truthy, calls `self.delete(key)`.

*   **`exists(self, session_key)`**
    *   Raises `NotImplementedError('subclasses of SessionBase must provide an exists() method')`.

*   **`create(self)`**
    *   Raises `NotImplementedError('subclasses of SessionBase must provide a create() method')`.

*   **`save(self, must_create=False)`**
    *   Raises `NotImplementedError('subclasses of SessionBase must provide a save() method')`.

*   **`delete(self, session_key=None)`**
    *   Raises `NotImplementedError('subclasses of SessionBase must provide a delete() method')`.

*   **`load(self)`**
    *   Raises `NotImplementedError('subclasses of SessionBase must provide a load() method')`.

*   **`clear_expired(cls)` (classmethod)**
    *   Raises `NotImplementedError('This backend does not support clear_expired().')`.
```