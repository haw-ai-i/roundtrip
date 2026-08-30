## django/contrib/messages/storage/cookie.py
Now I have the complete source file. Here is the natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import json

from django.conf import settings
from django.contrib.messages.storage.base import BaseStorage, Message
from django.core import signing
from django.http import SimpleCookie
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.safestring import SafeData, mark_safe
```

### Constants & Globals (module-level)

None. All constants are class attributes on `MessageEncoder` and `CookieStorage`.

---

## Code Objects

### Class: `MessageEncoder(json.JSONEncoder)`

**Purpose:** A custom JSON encoder that serializes `Message` instances into a compact list representation for cookie storage.

**Class Attributes:**
- `message_key = '__json_message'` — a sentinel string used as the first element of serialized message lists to identify them during decoding.

**Methods:**

#### `default(self, obj)`

- **Input:** An object that is not natively JSON-serializable by `json.JSONEncoder`.
- **Logic:**
  1. If `obj` is an instance of `Message`:
     - Determine `is_safedata`: set to `1` if `obj.message` (the message body) is a `SafeData` instance, otherwise `0`. Using integers instead of booleans produces more compact JSON output.
     - Build a list: `[self.message_key, is_safedata, obj.level, obj.message]`.
     - If `obj.extra_tags` is truthy (non-empty), append it as a fifth element to the list.
     - Return this list.
  2. Otherwise, delegate to `super().default(obj)`, which will raise `TypeError`.
- **Return:** A JSON-compatible list representing the `Message` instance, or whatever `super().default()` returns for non-`Message` objects.

---

### Class: `MessageDecoder(json.JSONDecoder)`

**Purpose:** A custom JSON decoder that reconstructs `Message` instances from their compact list representation during cookie deserialization.

**Methods:**

#### `process_messages(self, obj)`

- **Input:** An arbitrary Python object (the result of partial JSON decoding).
- **Logic:**
  1. If `obj` is a non-empty `list`:
     - If the first element equals `MessageEncoder.message_key` (`'__json_message'`):
       - If `obj[1]` is truthy (i.e., `1`, meaning the message body was marked as safe data), wrap `obj[3]` (the message string) with `mark_safe()`.
       - Return a new `Message(*obj[2:])` — unpacking from index 2 onward, which yields `(level, message)` or `(extra_tags, level, message)` depending on whether the list has 4 or 5 elements. The `Message` constructor receives these as positional arguments.
     - Otherwise (the list is not a serialized message), recursively apply `process_messages` to each item in the list and return the resulting list: `[self.process_messages(item) for item in obj]`.
  2. If `obj` is a `dict`:
     - Recursively apply `process_messages` to every value, preserving keys: `{key: self.process_messages(value) for key, value in obj.items()}`. Return the result.
  3. Otherwise (scalar or unrecognized type): return `obj` unchanged.
- **Return:** The processed object with any embedded serialized `Message` instances reconstructed as real `Message` objects.

#### `decode(self, s, **kwargs)`

- **Input:** A JSON string `s`, plus optional keyword arguments forwarded to the parent decoder.
- **Logic:**
  1. Call `super().decode(s, **kwargs)` to perform standard JSON decoding into a Python object (list/dict/scalar).
  2. Pass the result through `self.process_messages(decoded)`.
- **Return:** The fully decoded and processed Python object with any serialized messages restored as `Message` instances.

---

### Class: `CookieStorage(BaseStorage)`

**Purpose:** A Django message storage backend that persists messages in an HTTP cookie, using JSON serialization and cryptographic signing for integrity verification. Inherits all abstract methods from `BaseStorage`.

**Class Attributes:**
- `cookie_name = 'messages'` — the name of the cookie used to store messages.
- `max_cookie_size = 2048` — maximum allowed size (in bytes) for the encoded cookie value. Set to half of 4 KB to leave room for other HTTP headers and cookies, per uwsgi's default header-size limit.
- `not_finished = '__messagesnotfinished__'` — a sentinel string appended to the message list when messages were truncated due to size constraints, indicating that not all messages fit in the cookie.
- `key_salt = 'django.contrib.messages'` — salt used for generating the cryptographic cookie signer.

**Instance Attributes (initialized in `__init__`):**
- `self.signer` — a Django `signing.TimestampSigner` instance created via `signing.get_cookie_signer(salt=self.key_salt)`. Used to sign and verify encoded message data.

#### `__init__(self, *args, **kwargs)`

- Delegates all positional and keyword arguments to the parent `BaseStorage.__init__()`, then creates `self.signer` using `signing.get_cookie_signer(salt=self.key_salt)`.
- **Return:** None (constructor).

#### `_get(self, *args, **kwargs)`

- **Purpose:** Retrieve stored messages from the cookie. Called by the base storage to load messages for the current request.
- **Logic:**
  1. Read the cookie value: `data = self.request.COOKIES.get(self.cookie_name)`. Returns `None` if the cookie is absent.
  2. Decode the data via `self._decode(data)`, which returns a list of `Message` objects or `None` on failure.
  3. Determine whether all messages were retrieved: `all_retrieved = not (messages and messages[-1] == self.not_finished)`. If the last message is the sentinel, `all_retrieved` is `False`.
  4. If messages exist but `not all_retrieved`, remove the sentinel from the end of the list via `messages.pop()`.
- **Return:** A tuple `(messages, all_retrieved)` where:
  - `messages` is a list of `Message` objects (possibly empty), or `None` if decoding failed.
  - `all_retrieved` is a boolean (`True` if the full message set was retrieved; `False` if truncation occurred and the sentinel was removed).

#### `_update_cookie(self, encoded_data, response)`

- **Purpose:** Set or delete the cookie on the HTTP response based on whether there is data to store.
- **Parameters:**
  - `encoded_data`: a signed string (from `_encode`), or falsy value indicating no data.
  - `response`: an `HttpResponse` object.
- **Logic:**
  1. If `encoded_data` is truthy: call `response.set_cookie()` with the following arguments:
     - `key = self.cookie_name` (`'messages'`)
     - `value = encoded_data`
     - `domain = settings.SESSION_COOKIE_DOMAIN`
     - `secure = settings.SESSION_COOKIE_SECURE or None`
     - `httponly = settings.SESSION_COOKIE_HTTPONLY or None`
     - `samesite = settings.SESSION_COOKIE_SAMESITE`
  2. If `encoded_data` is falsy: call `response.delete_cookie(self.cookie_name, domain=settings.SESSION_COOKIE_DOMAIN)`.
- **Return:** None (side-effect on the response object).

#### `_store(self, messages, response, remove_oldest=True, *args, **kwargs)`

- **Purpose:** Encode and store a list of messages in the cookie. If the encoded data exceeds `max_cookie_size`, iteratively remove messages until it fits, then append the `not_finished` sentinel to indicate truncation.
- **Parameters:**
  - `messages`: a mutable list of `Message` objects to store.
  - `response`: an `HttpResponse` object.
  - `remove_oldest`: boolean (default `True`). Controls which end of the message list is trimmed: `True` removes from the front (oldest first); `False` removes from the back (newest first).
- **Logic:**
  1. Initialize `unstored_messages = []`.
  2. Encode all messages: `encoded_data = self._encode(messages)`.
  3. If `self.max_cookie_size` is truthy (non-zero):
     - Create a `SimpleCookie()` instance outside the loop to reuse for length estimation.
     - Define an inner function `stored_length(val)` that returns `len(cookie.value_encode(val)[1])` — the actual byte length of the encoded value as it would appear in a cookie header.
     - While `encoded_data` is truthy and `stored_length(encoded_data) > self.max_cookie_size`:
       - If `remove_oldest` is `True`: pop the first message from `messages` (`messages.pop(0)`) and append it to `unstored_messages`.
       - Otherwise: pop the last message from `messages` (`messages.pop()`) and insert it at position 0 of `unstored_messages` (preserving original order).
       - Re-encode with the truncated messages plus the sentinel: `encoded_data = self._encode(messages + [self.not_finished], encode_empty=unstored_messages)`. The `encode_empty=True` flag ensures the cookie is still set even if all messages are removed.
  4. Call `self._update_cookie(encoded_data, response)` to apply the cookie change.
- **Return:** A list of `Message` objects that could not be stored in the cookie (`unstored_messages`).

#### `_legacy_hash(self, value)`

- **Purpose:** Compute an HMAC/SHA1 hash for pre-Django 3.1 message data format (used only during backward-compatible decoding).
- **Parameters:**
  - `value`: a string whose hash is to be computed.
- **Logic:**
  1. Use the hardcoded salt `'django.contrib.messages'` (not `self.key_salt`, because older Django versions had this salt fixed and changing it would invalidate existing hashes).
  2. Call `salted_hmac(key_salt, value).hexdigest()`.
- **Return:** A hexadecimal HMAC digest string.

#### `_encode(self, messages, encode_empty=False)`

- **Purpose:** Serialize a list of messages to JSON, then cryptographically sign the result for integrity verification.
- **Parameters:**
  - `messages`: a list of `Message` objects.
  - `encode_empty`: boolean (default `False`). If `True`, encodes even an empty message list (used when truncating all messages and setting the sentinel).
- **Logic:**
  1. If `messages` is truthy or `encode_empty` is `True`:
     - Create a `MessageEncoder` with compact separators: `separators=(',', ':')` (no whitespace in JSON output).
     - Encode the messages list to a JSON string via `encoder.encode(messages)`.
     - Sign the resulting string using `self.signer.sign(value)`, which produces a signed, tamper-evident token.
  2. Otherwise (`messages` is empty and `encode_empty` is `False`): return `None` implicitly (no explicit return statement).
- **Return:** A signed string representing the encoded messages, or `None` if no encoding was performed.

#### `_decode(self, data)`

- **Purpose:** Safely decode a signed cookie value back into a list of `Message` objects. Handles both current and legacy formats, with fallback for tampered or corrupted data.
- **Parameters:**
  - `data`: the raw (unsigned) string from the cookie, or `None`.
- **Logic:**
  1. If `data` is falsy (`None` or empty string): return `None`.
  2. Attempt to unsign and verify the data: `decoded = self.signer.unsign(data)`.
     - If this raises `signing.BadSignature` (indicating tampering or an incompatible signing key): fall back to legacy decoding by calling `self._legacy_decode(data)`. The result is stored in `decoded`.
  3. If `decoded` is truthy:
     - Parse the JSON string using `json.loads(decoded, cls=MessageDecoder)` to reconstruct `Message` instances.
     - If this raises `json.JSONDecodeError`: silently ignore it (the data was signed but contained invalid JSON).
  4. In any failure case (bad signature with legacy decode returning falsy, or JSON parse error): set `self.used = True` to mark the cookie as used so it will be deleted on the next response, then return `None`.
- **Return:** A list of `Message` objects on success, or `None` on any failure.

#### `_legacy_decode(self, data)`

- **Purpose:** Decode pre-Django 3.1 format messages where the cookie value was in the form `hash$value` (a hash prefix separated by `$`).
- **Parameters:**
  - `data`: a string potentially in legacy format.
- **Logic:**
  1. Split `data` on the first occurrence of `$`: `bits = data.split('$', 1)`.
  2. If exactly two parts are produced:
     - Extract `hash_` (first part) and `value` (second part).
     - Compute the expected legacy hash via `self._legacy_hash(value)`.
     - Compare using constant-time comparison: if `constant_time_compare(hash_, self._legacy_hash(value))` is `True`, return `value` (the raw JSON string, which will then be parsed by `_decode`).
  3. Otherwise (not two parts or hash mismatch): return `None`.
- **Return:** The unsigned JSON string from legacy format data, or `None` if the data does not match the legacy format or fails verification.

## django/contrib/sessions/middleware.py
Here is the complete natural-language specification of `django/contrib/sessions/middleware.py`:

---

## Module-Level Preamble

### Imports

```python
import time
from importlib import import_module

from django.conf import settings
from django.contrib.sessions.backends.base import UpdateError
from django.core.exceptions import SuspiciousOperation
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import http_date
```

### Constants & Globals

None. All configuration is read dynamically from `django.conf.settings` at runtime via the following setting keys:
- `SESSION_COOKIE_NAME` — name of the session cookie (default `"sessionid"`)
- `SESSION_COOKIE_PATH` — path for the cookie (default `"/"`)
- `SESSION_COOKIE_DOMAIN` — domain for the cookie (may be `None`)
- `SESSION_COOKIE_SECURE` — whether the cookie requires HTTPS (`True`/`False`)
- `SESSION_COOKIE_HTTPONLY` — whether the cookie is HTTP-only (`True`/`False`)
- `SESSION_COOKIE_SAMESITE` — SameSite attribute value (`"Lax"` or `"Strict"`)
- `SESSION_ENGINE` — dotted Python path to the session engine module (default `"django.contrib.sessions.backends.db"`)
- `SESSION_SAVE_EVERY_REQUEST` — whether to save the session on every request regardless of modification flag (`True`/`False`)

---

## Code Objects

### Class: `SessionMiddleware(MiddlewareMixin)`

**Inheritance:** Subclasses Django's `MiddlewareMixin`.

#### Method: `__init__(self, get_response=None)`

- **Parameters:**
  - `get_response` — callable (the next middleware/view in the chain); defaults to `None`.
- **Logic:**
  1. Stores `get_response` as instance attribute `self.get_response`.
  2. Imports the session engine module specified by `settings.SESSION_ENGINE` using `import_module()`.
  3. Extracts the `SessionStore` class from that imported engine module and stores it as `self.SessionStore`.
- **Return:** None (standard constructor).

#### Method: `process_request(self, request)`

- **Parameters:**
  - `request` — an HTTP request object with a `.COOKIES` dict-like attribute.
- **Logic:**
  1. Retrieves the session cookie value from `request.COOKIES` using the key `settings.SESSION_COOKIE_NAME`. If no such cookie exists, the result is `None`.
  2. Creates a new session store instance by calling `self.SessionStore(session_key)` with the retrieved (possibly `None`) session key.
  3. Assigns this session store to `request.session`, making it available for downstream middleware and views.
- **Return:** None (standard Django middleware hook; returning `None` continues processing).

#### Method: `process_response(self, request, response)`

- **Parameters:**
  - `request` — the HTTP request object (must have `.COOKIES`, `.session`).
  - `response` — an HTTP response object with attributes/methods: `.status_code`, `.delete_cookie()`, `.set_cookie()`.
- **Logic:**
  1. Enters a `try` block and reads three boolean/attribute values from `request.session`:
     - `accessed` — whether the session was accessed during this request.
     - `modified` — whether the session data was modified during this request.
     - `empty` — whether the session has no stored data (i.e., is empty).
  2. If any of these attributes raises an `AttributeError` (e.g., if `request.session` was never set), returns `response` unchanged and exits.
  3. **Cookie deletion path:** If the session cookie name exists in `request.COOKIES` *and* the session is empty:
     - Calls `response.delete_cookie()` with arguments:
       - `name = settings.SESSION_COOKIE_NAME`
       - `path = settings.SESSION_COOKIE_PATH`
       - `domain = settings.SESSION_COOKIE_DOMAIN`
     - Calls `patch_vary_headers(response, ('Cookie',))` to add a `Vary: Cookie` header.
  4. **Else (cookie not deleted):**
     - If `accessed` is `True`, calls `patch_vary_headers(response, ('Cookie',))`.
     - If `(modified OR settings.SESSION_SAVE_EVERY_REQUEST)` AND the session is NOT empty:
       a. Determines cookie expiry parameters:
          - Calls `request.session.get_expire_at_browser_close()`:
            - If it returns `True`: sets `max_age = None`, `expires = None`.
            - If it returns `False`: calls `request.session.get_expiry_age()` to get `max_age` (integer seconds), computes `expires_time = time.time() + max_age`, and converts `expires_time` to an HTTP-date string via `http_date(expires_time)`, stored in `expires`.
       b. Checks that `response.status_code != 500`:
          - If the status code is **not** 500:
            - Attempts to call `request.session.save()`.
            - If `save()` raises `UpdateError`, catches it and raises `SuspiciousOperation` with the message: `"The request's session was deleted before the request completed. The user may have logged out in a concurrent request, for example."`
          - After saving (or if status is 500), calls `response.set_cookie()` with arguments:
            - `name = settings.SESSION_COOKIE_NAME`
            - `value = request.session.session_key`
            - `max_age = max_age` (may be `None`)
            - `expires = expires` (may be `None`)
            - `domain = settings.SESSION_COOKIE_DOMAIN`
            - `path = settings.SESSION_COOKIE_PATH`
            - `secure = settings.SESSION_COOKIE_SECURE or None`
            - `httponly = settings.SESSION_COOKIE_HTTPONLY or None`
            - `samesite = settings.SESSION_COOKIE_SAMESITE`
  5. Returns the (possibly modified) `response`.

---

### Summary of Behavioral Contract

The middleware performs two-phase session handling per HTTP request:

1. **On request (`process_request`):** It extracts the session cookie from the incoming request and instantiates a session store, attaching it to `request.session` for use by views.

2. **On response (`process_response`):** It inspects whether the session was accessed or modified during request processing. If the session is empty and a cookie exists, it deletes the cookie. Otherwise, if the session was accessed (to set `Vary: Cookie`) or modified/saved-on-every-request (to persist data), it saves the session to the backend (skipping 500-error responses) and writes/refreshes the session cookie with appropriate expiry, domain, path, security, and SameSite attributes. If a concurrent request deleted the session during processing, an `UpdateError` is raised as a `SuspiciousOperation`.

## django/http/response.py
Here is the complete natural-language specification of `django/http/response.py`:

---

## Module-Level Preamble

### Imports

```python
import datetime
import json
import mimetypes
import os
import re
import sys
import time
from email.header import Header
from http.client import responses
from urllib.parse import quote, urlparse

from django.conf import settings
from django.core import signals, signing
from django.core.exceptions import DisallowedRedirect
from django.core.serializers.json import DjangoJSONEncoder
from django.http.cookie import SimpleCookie
from django.utils import timezone
from django.utils.encoding import iri_to_uri
from django.utils.http import http_date
from django.utils.regex_helper import _lazy_re_compile
```

### Constants & Globals

- **`_charset_from_content_type_re`** — A lazy-compiled regular expression (`re.I` flag) matching `; charset=<value>` within a Content-Type header value. Capture group named `charset` extracts the charset string (characters up to whitespace or semicolon).

---

## Code Objects

### Class: `BadHeaderError(ValueError)`

A subclass of `ValueError`. Raised when a header key or value contains newline characters (`\n` or `\r`). No additional attributes or methods.

---

### Class: `HttpResponseBase`

**Inheritance:** None (base class)

#### Attributes

- **`status_code`** — `int`, default `200`. The HTTP status code.
- **`_headers`** — `dict[str, tuple[str, str]]`, initialized in `__init__` as `{}`. Maps lowercase header name to a `(original_case_name, value)` tuple. Both key and value are ASCII strings.
- **`_resource_closers`** — `list[callable]`, initialized in `__init__` as `[]`. Stores close callbacks for resources (e.g., file handles).
- **`_handler_class`** — `None | type`, initialized in `__init__` as `None`. Set by the request handler; used to send `request_finished` signal.
- **`cookies`** — `SimpleCookie`, initialized in `__init__` via `SimpleCookie()`.
- **`closed`** — `bool`, initialized in `__init__` as `False`.

#### Properties

- **`reason_phrase`** (getter): Returns `_reason_phrase` if set; otherwise looks up the standard reason phrase from `http.client.responses` dict by `status_code`, defaulting to `'Unknown Status Code'`.
- **`reason_phrase`** (setter): Assigns directly to `_reason_phrase`.
- **`charset`** (getter): Returns `_charset` if explicitly set; otherwise searches the Content-Type header value with `_charset_from_content_type_re`; strips double quotes from matched charset. Falls back to `settings.DEFAULT_CHARSET`.
- **`charset`** (setter): Assigns directly to `_charset`.

#### Methods

- **`__init__(self, content_type=None, status=None, reason=None, charset=None)`**
  - Initializes `_headers = {}`, `_resource_closers = []`, `_handler_class = None`, `cookies = SimpleCookie()`, `closed = False`.
  - If `status` is not `None`: converts to `int`; raises `TypeError` if conversion fails. Validates range `100–599`; raises `ValueError` otherwise. Assigns to `self.status_code`.
  - Stores `reason` in `_reason_phrase`, `charset` in `_charset`.
  - If `content_type` is `None`, defaults to `'text/html; charset=<self.charset>'`. Sets header via `self['Content-Type'] = content_type`.

- **`serialize_headers(self) -> bytes`** — Returns all headers as a bytestring formatted as HTTP header lines joined by `\r\n`. Each header line: key encoded as ASCII + `b': '` + value encoded as Latin-1. Also aliased as `__bytes__`.

- **`_content_type_for_repr`** (property) → `str`: Returns `', "<Content-Type>"'` if `'Content-Type'` is in headers, else empty string. Used by `__repr__`.

- **`_convert_to_charset(self, value, charset: str, mime_encode=False)`** — Converts a header key or value to the specified charset (`'ascii'` for keys, `'latin-1'` for values).
  - If `value` is not `bytes`/`str`, converts via `str(value)`.
  - Raises `BadHeaderError` if value contains `\n` or `\r`.
  - For `str`: encodes to charset; raises `UnicodeError` (with appended message about charset format) on failure.
  - For `bytes`: decodes from charset; on `UnicodeError`, if `mime_encode=True`, MIME-encodes via `Header(value, 'utf-8', maxlinlen=sys.maxsize).encode()`; otherwise re-raises with appended charset error message.
  - Returns the converted value (always a string after processing).

- **`__setitem__(self, header: str, value)`** — Converts key to ASCII and value to Latin-1 (with MIME encoding allowed for values). Stores in `_headers[header.lower()] = (original_header, converted_value)`.

- **`__delitem__(self, header)`** — Removes entry from `_headers` by lowercase key. No-op if absent.

- **`__getitem__(self, header: str) -> str`** — Returns the value tuple's second element for the lowercase key.

- **`has_header(self, header: str) -> bool`** — Case-insensitive check: returns `header.lower() in self._headers`. Also aliased as `__contains__`.

- **`items(self)`** — Returns `self._headers.values()` (iterator of `(original_name, value)` tuples).

- **`get(self, header: str, alternate=None) -> str | None`** — Case-insensitive lookup. Returns the value from `_headers`, or `alternate` if absent.

- **`set_cookie(self, key, value='', max_age=None, expires=None, path='/', domain=None, secure=False, httponly=False, samesite=None)`**
  - Sets `self.cookies[key] = value`.
  - If `expires` is a `datetime.datetime`: if aware, converts to naive UTC via `timezone.make_naive(expires, timezone.utc)`. Computes delta from `expires.utcnow()`, adds one second. Sets `max_age = max(0, delta.days * 86400 + delta.seconds)`, sets `expires = None`. If not a datetime, stores raw string in `self.cookies[key]['expires']`.
  - If `expires` is `None`, sets `self.cookies[key]['expires'] = ''`.
  - If `max_age` is set: assigns to `'max-age'`; if no expires was already set, computes `http_date(time.time() + max_age)` and stores as `'expires'`.
  - If `path` is not `None`: sets `'path'`.
  - If `domain` is not `None`: sets `'domain'`.
  - If `secure=True`: sets `'secure' = True`.
  - If `httponly=True`: sets `'httponly' = True`.
  - If `samesite` is set: validates it is one of `'lax'`, `'none'`, `'strict'` (case-insensitive); raises `ValueError` otherwise. Sets `'samesite'`.

- **`setdefault(self, key, value)`** — If `key not in self`, calls `self[key] = value`. No-op if header already exists.

- **`set_signed_cookie(self, key, value, salt='', **kwargs)`** — Signs the value using `signing.get_cookie_signer(salt=key + salt).sign(value)`, then delegates to `self.set_cookie(key, signed_value, **kwargs)`. Returns result of `set_cookie`.

- **`delete_cookie(self, key, path='/', domain=None)`** — Sets `secure=True` if key starts with `'__Secure-'` or `'__Host-''`. Calls `set_cookie(key, max_age=0, path=path, domain=domain, secure=secure, expires='Thu, 01 Jan 1970 00:00:00 GMT')`.

- **`make_bytes(self, value)`** — Converts a value to bytes encoded in `self.charset`:
  - If `bytes` or `memoryview`: returns `bytes(value)`.
  - If `str`: returns `value.encode(self.charset)`.
  - Otherwise: returns `str(value).encode(self.charset)`.

- **`close(self)`** — Iterates `_resource_closers`, calling each closer (catching all exceptions). Clears the list. Sets `closed = True`. Sends `signals.request_finished.send(sender=self._handler_class)`.

- **`write(self, content)`** — Raises `OSError('This <ClassName> instance is not writable')`.

- **`flush(self)`** — No-op (pass).

- **`tell(self)`** — Raises `OSError('This %s instance cannot tell its position' % self.__class__.__name__)`.

- **`readable(self) -> bool`** — Returns `False`.

- **`seekable(self) -> bool`** — Returns `False`.

- **`writable(self) -> bool`** — Returns `False`.

- **`writelines(self, lines)`** — Raises `OSError('This %s instance is not writable' % self.__class__.__name__)`.

---

### Class: `HttpResponse(HttpResponseBase)`

**Inheritance:** `HttpResponseBase`

#### Attributes

- **`streaming`** — `False` (class attribute).
- **`_container`** — `list[bytes]`, initialized in the `content` setter as `[content_bytes]`.

#### Methods

- **`__init__(self, content=b'', *args, **kwargs)`** — Calls `super().__init__(*args, **kwargs)`. Sets `self.content = content`.

- **`__repr__(self) -> str`** — Returns `'<HttpResponse status_code=<code>[, "<content_type>"]>'` format using class name, `status_code`, and `_content_type_for_repr`.

- **`serialize(self) -> bytes`** — Returns full HTTP message: `self.serialize_headers() + b'\r\n\r\n' + self.content`. Also aliased as `__bytes__`.

#### Properties

- **`content`** (getter): Returns `b''.join(self._container)` — concatenation of all bytestring chunks.
- **`content`** (setter): If value has `__iter__` but is not `bytes`/`str`: iterates, converts each chunk via `self.make_bytes(chunk)`, joins into bytes; if value has a `close()` method, calls it (catching exceptions). Otherwise: `self.make_bytes(value)`. Sets `self._container = [content]`.

#### Methods (file-like interface)

- **`__iter__(self)`** — Returns `iter(self._container)`.
- **`write(self, content)`** — Appends `self.make_bytes(content)` to `_container`.
- **`tell(self)`** — Returns `len(self.content)`.
- **`getvalue(self)`** — Returns `self.content`.
- **`writable(self)`** — Returns `True`.
- **`writelines(self, lines)`** — Iterates `lines`, calling `self.write(line)` for each.

---

### Class: `StreamingHttpResponse(HttpResponseBase)`

**Inheritance:** `HttpResponseBase`

#### Attributes

- **`streaming`** — `True` (class attribute).
- **`_iterator`** — `iterator`, set in `_set_streaming_content`.

#### Methods

- **`__init__(self, streaming_content=(), *args, **kwargs)`** — Calls `super().__init__(*args, **kwargs)`. Sets `self.streaming_content = streaming_content`.

#### Properties

- **`content`** (getter): Raises `AttributeError("This <ClassName> instance has no 'content' attribute. Use 'streaming_content' instead.")`.
- **`streaming_content`** (getter): Returns `map(self.make_bytes, self._iterator)` — lazily converts each yielded item to bytes via the output charset.
- **`streaming_content`** (setter): Calls `self._set_streaming_content(value)`.

#### Methods

- **`_set_streaming_content(self, value)`** — Sets `self._iterator = iter(value)`. If `value` has a `close()` method, appends it to `_resource_closers`.
- **`__iter__(self)`** — Returns `self.streaming_content`.
- **`getvalue(self)`** — Consumes and returns `b''.join(self.streaming_content)`.

---

### Class: `FileResponse(StreamingHttpResponse)`

**Inheritance:** `StreamingHttpResponse`

#### Attributes

- **`block_size`** — `4096` (class attribute).
- **`as_attachment`** — `bool`, set in `__init__` from parameter.
- **`filename`** — `str`, set in `__init__` from parameter.
- **`file_to_stream`** — file-like object or `None`, set in `_set_streaming_content`.

#### Methods

- **`__init__(self, *args, as_attachment=False, filename='', **kwargs)`** — Sets `as_attachment`, `filename`; calls `super().__init__(*args, **kwargs)`.

- **`_set_streaming_content(self, value)`** — If `value` has a `read` attribute:
  - Stores `value` in `self.file_to_stream`.
  - If it has `close()`, appends to `_resource_closers`.
  - Creates an iterator: `iter(lambda: filelike.read(self.block_size), b'')` — reads chunks of `block_size` until empty bytes.
  - Calls `self.set_headers(filelike)`.
  - Delegates to `super()._set_streaming_content(value)` with the chunked iterator.
- If `value` does not have `read`: sets `file_to_stream = None`, delegates to parent `_set_streaming_content(value)`.

- **`set_headers(self, filelike)`** — Sets common response headers based on the file-like object:
  - **Content-Length**: If `filelike.name` is an absolute path, uses `os.path.getsize(filelike.name)`. Else if `filelike` has `getbuffer()`, uses `filelike.getbuffer().nbytes`.
  - **Content-Type**: If existing Content-Type starts with `'text/html'`: if filename exists, guesses MIME type via `mimetypes.guess_type(filename)`; maps encodings (`bzip2→application/x-bzip`, `gzip→application/gzip`, `xz→application/x-xz`); sets to guessed type or `'application/octet-stream'`. If no filename, sets `'application/octet-stream'`.
  - **Content-Disposition**: Extracts filename from `self.filename` or `os.path.basename(filelike.name)`. If filename exists: if it encodes as ASCII, uses `filename="<name>"`; else uses `filename*=utf-8'<quoted>'` via `quote()`. Sets `'inline'` disposition (or `'attachment'` if `as_attachment=True`). If no filename but `as_attachment=True`, sets `'Content-Disposition': 'attachment'`.

---

### Class: `HttpResponseRedirectBase(HttpResponse)`

**Inheritance:** `HttpResponse`

#### Attributes

- **`allowed_schemes`** — `['http', 'https', 'ftp']` (class attribute).

#### Methods

- **`__init__(self, redirect_to, *args, **kwargs)`** — Calls `super().__init__(*args, **kwargs)`. Sets `'Location'` header to `iri_to_uri(redirect_to)`. Parses `str(redirect_to)` with `urlparse`; if scheme is present and not in `allowed_schemes`, raises `DisallowedRedirect("Unsafe redirect to URL with protocol '<scheme>'")`.

#### Properties

- **`url`** — `property(lambda self: self['Location'])`. Returns the Location header value.

#### Methods

- **`__repr__(self) -> str`** — Returns `'<HttpResponseRedirectBase status_code=<code>[, "<content_type>"], url="<url>"'>'` format including class name, status code, content type repr, and URL.

---

### Class: `HttpResponseRedirect(HttpResponseRedirectBase)`

**Inheritance:** `HttpResponseRedirectBase`

- **`status_code`** — `302` (class attribute). No other methods or attributes.

---

### Class: `HttpResponsePermanentRedirect(HttpResponseRedirectBase)`

**Inheritance:** `HttpResponseRedirectBase`

- **`status_code`** — `301` (class attribute). No other methods or attributes.

---

### Class: `HttpResponseNotModified(HttpResponse)`

**Inheritance:** `HttpResponse`

#### Attributes

- **`status_code`** — `304` (class attribute).

#### Methods

- **`__init__(self, *args, **kwargs)`** — Calls `super().__init__(*args, **kwargs)`. Deletes `'content-type'` header via `del self['content-type']`.

#### Properties

- **`content`** (setter): If value is truthy, raises `AttributeError("You cannot set content to a 304 (Not Modified) response")`. Otherwise sets `self._container = []`.

---

### Class: `HttpResponseBadRequest(HttpResponse)`

**Inheritance:** `HttpResponse`

- **`status_code`** — `400` (class attribute). No other methods or attributes.

---

### Class: `HttpResponseNotFound(HttpResponse)`

**Inheritance:** `HttpResponse`

- **`status_code`** — `404` (class attribute). No other methods or attributes.

---

### Class: `HttpResponseForbidden(HttpResponse)`

**Inheritance:** `HttpResponse`

- **`status_code`** — `403` (class attribute). No other methods or attributes.

---

### Class: `HttpResponseNotAllowed(HttpResponse)`

**Inheritance:** `HttpResponse`

#### Attributes

- **`status_code`** — `405` (class attribute).

#### Methods

- **`__init__(self, permitted_methods, *args, **kwargs)`** — Calls `super().__init__(*args, **kwargs)`. Sets `'Allow'` header to `', '.join(permitted_methods)`.

- **`__repr__(self) -> str`** — Returns `'<HttpResponseNotAllowed [methods] status_code=<code>[, "<content_type>"]>'` format including class name, Allow header value as methods, status code, and content type repr.

---

### Class: `HttpResponseGone(HttpResponse)`

**Inheritance:** `HttpResponse`

- **`status_code`** — `410` (class attribute). No other methods or attributes.

---

### Class: `HttpResponseServerError(HttpResponse)`

**Inheritance:** `HttpResponse`

- **`status_code`** — `500` (class attribute). No other methods or attributes.

---

### Class: `Http404(Exception)`

A simple exception subclass of `Exception`. No additional attributes, methods, or custom behavior.

---

### Class: `JsonResponse(HttpResponse)`

**Inheritance:** `HttpResponse`

#### Methods

- **`__init__(self, data, encoder=DjangoJSONEncoder, safe=True, json_dumps_params=None, **kwargs)`**
  - If `safe=True` and `data` is not a `dict`: raises `TypeError("In order to allow non-dict objects to be serialized set the safe parameter to False.")`.
  - If `json_dumps_params` is `None`, sets it to `{}`.
  - Sets default `content_type='application/json'` in kwargs via `kwargs.setdefault('content_type', 'application/json')`.
  - Serializes data: `data = json.dumps(data, cls=encoder, **json_dumps_params)`.
  - Calls `super().__init__(content=data, **kwargs)` with the JSON-serialized string.