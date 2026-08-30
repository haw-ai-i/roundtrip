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
- `settings.SESSION_ENGINE` — dotted Python path to the session engine module (e.g., `"django.contrib.sessions.backends.db"`).
- `settings.SESSION_COOKIE_NAME` — string name of the session cookie.
- `settings.SESSION_COOKIE_PATH` — string path for the session cookie.
- `settings.SESSION_COOKIE_DOMAIN` — string domain for the session cookie, or `None`.
- `settings.SESSION_COOKIE_SAMESITE` — string (`"Lax"` or `"Strict"`).
- `settings.SESSION_COOKIE_SECURE` — boolean; whether to require HTTPS for the cookie.
- `settings.SESSION_COOKIE_HTTPONLY` — boolean; whether to mark the cookie as HTTP-only.
- `settings.SESSION_SAVE_EVERY_REQUEST` — boolean; if `True`, always save the session on every request regardless of modification status.

---

## Code Objects

### Class: `SessionMiddleware(MiddlewareMixin)`

**Inheritance:** Subclass of `django.utils.deprecation.MiddlewareMixin`.

#### Attributes (instance, set in `__init__`)

| Attribute | Type | Description |
|---|---|---|
| `get_response` | callable or `None` | The next middleware / view callable in the chain. Set from the constructor argument after deprecation handling. |
| `SessionStore` | class (callable) | The session store class, obtained as `engine.SessionStore` where `engine = import_module(settings.SESSION_ENGINE)`. Used to instantiate per-request session objects. |

#### Methods

##### `__init__(self, get_response=None)`

**Signature:** Accepts a single keyword-or-positional argument `get_response`, defaulting to `None`.

**Logic:**
1. Calls `self._get_response_none_deprecation(get_response)`, which is inherited from `MiddlewareMixin` and emits a deprecation warning when `get_response` is `None` (scheduled for removal in Django 4.0).
2. Assigns the passed `get_response` to `self.get_response`.
3. Calls `self._async_check()` (inherited from `MiddlewareMixin`) to verify async compatibility.
4. Imports the session engine module via `import_module(settings.SESSION_ENGINE)`.
5. Stores the engine's `SessionStore` class on `self.SessionStore`.

**Return:** None.

---

##### `process_request(self, request)`

**Signature:** Accepts a single argument `request`, an HTTP request object.

**Logic:**
1. Retrieves the session key from the incoming request cookies by looking up `settings.SESSION_COOKIE_NAME` in `request.COOKIES`. If the cookie is absent, this yields `None`.
2. Instantiates a new session store object by calling `self.SessionStore(session_key)` and assigns it to `request.session`.

**Return:** None (standard Django middleware request hook; no return value expected).

---

##### `process_response(self, request, response)`

**Signature:** Accepts two arguments:
- `request` — the HTTP request object.
- `response` — the HTTP response object being returned.

**Logic:**

1. **Guard clause (attribute absence):** Attempts to read three attributes from `request.session`:
   - `accessed` — boolean indicating whether the session was accessed during this request.
   - `modified` — boolean indicating whether the session data was modified during this request.
   - `empty` — result of calling `request.session.is_empty()`, a boolean indicating whether the session has no stored data.

   If any of these raises `AttributeError` (e.g., if `request.session` is not a proper session object), returns `response` unchanged and exits.

2. **Cookie deletion path** — evaluated when both conditions hold:
   - The session cookie name (`settings.SESSION_COOKIE_NAME`) exists in `request.COOKIES`, AND
   - The session is empty (`empty` is `True`).

   In this case:
   a. Calls `response.delete_cookie()` with the following arguments:
      - `name`: `settings.SESSION_COOKIE_NAME`
      - `path`: `settings.SESSION_COOKIE_PATH`
      - `domain`: `settings.SESSION_COOKIE_DOMAIN`
      - `samesite`: `settings.SESSION_COOKIE_SAMESITE`
   b. Calls `patch_vary_headers(response, ('Cookie',))` to add a `Vary: Cookie` header.

3. **Else (cookie not deleted):** The session is non-empty or the cookie does not exist in the request.

   a. If `accessed` is `True`, calls `patch_vary_headers(response, ('Cookie',))`.

   b. If either `modified` is `True` OR `settings.SESSION_SAVE_EVERY_REQUEST` is `True`, AND `empty` is `False`:
      i. Determines cookie expiry parameters:
         - Calls `request.session.get_expire_at_browser_close()`. If it returns `True`: sets `max_age = None` and `expires = None`.
         - Otherwise: calls `request.session.get_expiry_age()` to get a numeric max-age in seconds, computes `expires_time = time.time() + max_age`, then converts to an HTTP-date string via `http_date(expires_time)` assigned to `expires`.
      ii. Checks that the response status code is not 500 (`response.status_code != 500`). If it is 500, skips saving entirely (to avoid losing session data on server errors).
      iii. If the status code is not 500:
           - Calls `request.session.save()` to persist session data to the backend store.
           - Catches `UpdateError` from the save operation and re-raises it as a `SuspiciousOperation` with the message: `"The request's session was deleted before the request completed. The user may have logged out in a concurrent request, for example."`
           - Calls `response.set_cookie()` with these arguments:
             * `name`: `settings.SESSION_COOKIE_NAME`
             * `value`: `request.session.session_key`
             * `max_age`: the computed `max_age` (or `None`)
             * `expires`: the computed `expires` string (or `None`)
             * `domain`: `settings.SESSION_COOKIE_DOMAIN`
             * `path`: `settings.SESSION_COOKIE_PATH`
             * `secure`: `settings.SESSION_COOKIE_SECURE or None`
             * `httponly`: `settings.SESSION_COOKIE_HTTPONLY or None`
             * `samesite`: `settings.SESSION_COOKIE_SAMESITE`

4. Returns the (possibly modified) `response`.

**Return:** The HTTP response object (`response`).

**Exceptions raised:**
- `SuspiciousOperation` — if `request.session.save()` raises `UpdateError` during a non-500 response, indicating the session was concurrently deleted (e.g., by another request logging the user out).

## django/middleware/cache.py
Here is the complete natural-language specification of `django/middleware/cache.py`:

---

## Module-Level Preamble

### Imports

```python
from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS, caches
from django.utils.cache import (
    get_cache_key, get_max_age, has_vary_header, learn_cache_key,
    patch_response_headers,
)
from django.utils.deprecation import MiddlewareMixin
```

### Constants & Globals

None. All configuration is read from `django.conf.settings` at runtime via the `settings` object.

---

## Code Objects

### Class: `UpdateCacheMiddleware(MiddlewareMixin)`

**Docstring:** Response-phase cache middleware that updates the cache if the response is cacheable. Must be used as part of the two-part update/fetch cache middleware. Must be the first piece of middleware in `MIDDLEWARE` so it gets called last during the response phase.

#### `__init__(self, get_response=None)`

- Calls `self._get_response_none_deprecation(get_response)`.
- Sets instance attributes:
  - `self.cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS` — default cache timeout in seconds.
  - `self.page_timeout = None` — optional per-instance page-level override (defaults to no override).
  - `self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX` — prefix for cache keys.
  - `self.cache_alias = settings.CACHE_MIDDLEWARE_ALIAS` — alias of the cache backend to use.
  - `self.cache = caches[self.cache_alias]` — resolved cache instance from the Django cache registry.
  - `self.get_response = get_response` — the next middleware / view callable.

#### `_should_update_cache(self, request, response)`

- Returns `True` if and only if `request` has an attribute `_cache_update_cache` whose value is truthy; otherwise returns `False`. This flag is set by `FetchFromCacheMiddleware.process_request()` to signal whether the response should be cached.

#### `process_response(self, request, response)`

- **Step 1 — Check update flag:** Calls `self._should_update_cache(request, response)`. If it returns `False`, immediately returns `response` unchanged (no caching needed).
- **Step 2 — Streaming / non-cacheable status:** If `response.streaming` is truthy or `response.status_code` is not in `(200, 304)`, returns `response` unchanged.
- **Step 3 — Cookie-less request with security-sensitive Vary: Cookie:** If the request has no cookies (`not request.COOKIES`) but the response sets cookies (`response.cookies`), and the response's `Vary` header contains `'Cookie'` (checked via `has_vary_header(response, 'Cookie')`), returns `response` unchanged. This prevents caching a user-specific response for cookie-less requests.
- **Step 4 — Cache-Control: private:** If `'private'` appears in the response's `Cache-Control` header value (`response.get('Cache-Control', ())`), returns `response` unchanged.
- **Step 5 — Determine timeout (precedence order):**
  - First, try `self.page_timeout`. If it is not `None`, use it as `timeout`.
  - Otherwise, call `get_max_age(response)` to extract the `max-age` value from the response's `Cache-Control` header. If that returns a non-`None` value, use it as `timeout`.
    - If `timeout == 0` (i.e., `max-age=0`), return `response` unchanged — do not cache.
  - Otherwise, fall back to `self.cache_timeout` (`settings.CACHE_MIDDLEWARE_SECONDS`).
- **Step 6 — Patch response headers:** Calls `patch_response_headers(response, timeout)`, which sets the `ETag`, `Last-Modified`, `Expires`, and `Cache-Control` headers on the response based on `timeout`.
- **Step 7 — Store in cache (only if `timeout` is truthy and status is 200):**
  - Calls `learn_cache_key(request, response, timeout, self.key_prefix, cache=self.cache)` to compute the cache key. This function also reads the `Vary` header from the response and incorporates relevant request headers into the key.
  - If the response has a callable `render` attribute (`hasattr(response, 'render') and callable(response.render)`) — indicating it is an `HttpResponseBase` subclass that may need deferred rendering (e.g., `TemplateResponse`) — registers a post-render callback via `response.add_post_render_callback(lambda r: self.cache.set(cache_key, r, timeout))`. The actual cache write happens after the response is fully rendered.
  - Otherwise, immediately writes to the cache: `self.cache.set(cache_key, response, timeout)`.
- **Returns:** Always returns `response` (the original or patched response object).

---

### Class: `FetchFromCacheMiddleware(MiddlewareMixin)`

**Docstring:** Request-phase cache middleware that fetches a page from the cache. Must be used as part of the two-part update/fetch cache middleware. Must be the last piece of middleware in `MIDDLEWARE` so it gets called last during the request phase.

#### `__init__(self, get_response=None)`

- Calls `self._get_response_none_deprecation(get_response)`.
- Sets instance attributes:
  - `self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX` — prefix for cache keys.
  - `self.cache_alias = settings.CACHE_MIDDLEWARE_ALIAS` — alias of the cache backend to use.
  - `self.cache = caches[self.cache_alias]` — resolved cache instance from the Django cache registry.
  - `self.get_response = get_response` — the next middleware / view callable.

#### `process_request(self, request)`

- **Step 1 — Method check:** If `request.method` is not in `('GET', 'HEAD')`, sets `request._cache_update_cache = False` and returns `None`. This signals that no cache lookup should be attempted and the request proceeds normally.
- **Step 2 — Try GET cache key:** Calls `get_cache_key(request, self.key_prefix, 'GET', cache=self.cache)` to compute a cache key for the current request as a GET request. If this returns `None` (no cache information available), sets `request._cache_update_cache = True` and returns `None` — the response will be rebuilt and cached later by `UpdateCacheMiddleware`.
- **Step 3 — Fetch from cache:** Calls `self.cache.get(cache_key)` to retrieve the cached response. If the result is not `None`, proceeds directly to Step 6 (cache hit).
- **Step 4 — HEAD fallback:** If the retrieved `response` is `None` and `request.method == 'HEAD'`, calls `get_cache_key(request, self.key_prefix, 'HEAD', cache=self.cache)` to compute a separate HEAD-specific cache key, then attempts `self.cache.get(cache_key)` again. This handles the case where only a GET response was cached but a HEAD request is being served.
- **Step 5 — Cache miss:** If `response` is still `None`, sets `request._cache_update_cache = True` and returns `None` — the response will be rebuilt and cached later by `UpdateCacheMiddleware`.
- **Step 6 — Cache hit:** Sets `request._cache_update_cache = False` (signaling that the cache was updated, so `UpdateCacheMiddleware` should not overwrite it) and returns the cached `response` object. This is a shallow copy of the original response stored in the cache.

---

### Class: `CacheMiddleware(UpdateCacheMiddleware, FetchFromCacheMiddleware)`

**Docstring:** Cache middleware that provides basic behavior for many simple sites. Also used as the hook point for the cache decorator (generated via the `decorator-from-middleware` utility).

This class inherits from both `UpdateCacheMiddleware` and `FetchFromCacheMiddleware`, combining their functionality into a single middleware class suitable for simple sites where no other middleware needs to affect the cache key.

#### `__init__(self, get_response=None, cache_timeout=None, page_timeout=None, **kwargs)`

- Calls `self._get_response_none_deprecation(get_response)`.
- Sets `self.get_response = get_response`.
- **`key_prefix`:** Attempts to read `kwargs['key_prefix']`. If present and the value is `None`, sets it to `''` (empty string). If absent from kwargs, falls back to `settings.CACHE_MIDDLEWARE_KEY_PREFIX`. Stores in `self.key_prefix`.
- **`cache_alias`:** Attempts to read `kwargs['cache_alias']`. If present and the value is `None`, defaults to `DEFAULT_CACHE_ALIAS`. If absent from kwargs, falls back to `settings.CACHE_MIDDLEWARE_ALIAS`. Stores in `self.cache_alias`.
- **`cache_timeout`:** If `cache_timeout` is `None`, defaults to `settings.CACHE_MIDDLEWARE_SECONDS`. Stores in `self.cache_timeout`.
- **`page_timeout`:** Stored directly as `self.page_timeout` (may be `None`).
- Sets `self.cache = caches[self.cache_alias]` — resolved cache instance.

This class does not override any methods from its parent classes; it relies on the MRO (Method Resolution Order) to call both `FetchFromCacheMiddleware.process_request()` and `UpdateCacheMiddleware.process_response()`. The combined behavior is: request-phase cache lookup via the inherited `process_request`, then response-phase cache storage via the inherited `process_response`.

---

## django/middleware/security.py
Here is the complete natural-language specification of `django/middleware/security.py`:

---

## Module-Level Preamble

### Imports

```python
import re

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
```

### Constants & Globals

None. All configuration is read dynamically from Django's `settings` object at instantiation time.

---

## Code Objects

### Class: `SecurityMiddleware(MiddlewareMixin)`

No metaclass; inherits directly from `MiddlewareMixin`.

#### Attributes (initialized in `__init__`)

| Attribute | Type | Source / Initialization |
|---|---|---|
| `sts_seconds` | `int` or falsy value | `settings.SECURE_HSTS_SECONDS` |
| `sts_include_subdomains` | `bool` | `settings.SECURE_HSTS_INCLUDE_SUBDOMAINS` |
| `sts_preload` | `bool` | `settings.SECURE_HSTS_PRELOAD` |
| `content_type_nosniff` | `bool` | `settings.SECURE_CONTENT_TYPE_NOSNIFF` |
| `xss_filter` | `bool` | `settings.SECURE_BROWSER_XSS_FILTER` |
| `redirect` | `bool` | `settings.SECURE_SSL_REDIRECT` |
| `redirect_host` | `str` or falsy value | `settings.SECURE_SSL_HOST` |
| `redirect_exempt` | `list[re.Pattern]` | Each element of `settings.SECURE_REDIRECT_EXEMPT` (a list of regex strings) is compiled via `re.compile()` and stored in a new list. |
| `referrer_policy` | `str`, iterable, or falsy value | `settings.SECURE_REFERRER_POLICY` |
| `get_response` | callable or `None` | Passed through from the constructor argument. |

#### Constructor: `__init__(self, get_response=None)`

1. Calls `self._get_response_none_deprecation(get_response)` — a deprecation helper inherited from `MiddlewareMixin`.
2. Reads nine security-related settings from Django's global `settings` object and assigns each to a corresponding instance attribute (see table above).
3. Assigns the raw `get_response` argument to `self.get_response`.

#### Method: `process_request(self, request)`

**Parameters:** `request` — an HTTP request object.  
**Returns:** An `HttpResponsePermanentRedirect` if SSL redirect conditions are met; otherwise `None` (implicit).

Logic:
1. Strip all leading `/` characters from `request.path`, producing a bare path string.
2. Evaluate three conditions conjunctively:
   - `self.redirect` is truthy, **and**
   - `request.is_secure()` returns `False` (the request is not HTTPS), **and**
   - The stripped path does **not** match any regex pattern in `self.redirect_exempt`.
3. If all three conditions hold:
   a. Determine the target host: use `self.redirect_host` if it is truthy; otherwise fall back to `request.get_host()`.  
   b. Construct the redirect URL as `"https://%s%s" % (host, request.get_full_path())`.  
   c. Return an `HttpResponsePermanentRedirect` with that URL.
4. If any condition fails, return `None` implicitly.

#### Method: `process_response(self, request, response)`

**Parameters:**  
- `request` — the HTTP request object.  
- `response` — an `HttpResponse` (or subclass) instance to be modified in place.  

**Returns:** The same `response` object (possibly mutated).

Logic proceeds through four independent header-setting blocks:

1. **Strict-Transport-Security (HSTS):**
   - Condition: `self.sts_seconds` is truthy, `request.is_secure()` is `True`, and the response does not already contain a `'Strict-Transport-Security'` header.
   - Build the header value starting with `"max-age=%s" % self.sts_seconds`.
   - If `self.ststs_include_subdomains` is truthy, append `"; includeSubDomains"` to the value.
   - If `self.sts_preload` is truthy, append `"; preload"` to the value.
   - Set `response['Strict-Transport-Security'] = sts_header`.

2. **X-Content-Type-Options:**
   - Condition: `self.content_type_nosniff` is truthy.
   - Call `response.setdefault('X-Content-Type-Options', 'nosniff')`. This sets the header only if it is not already present.

3. **X-XSS-Protection:**
   - Condition: `self.xss_filter` is truthy.
   - Call `response.setdefault('X-XSS-Protection', '1; mode=block')`. Sets the header only if absent.

4. **Referrer-Policy:**
   - Condition: `self.referrer_policy` is truthy.
   - Normalize the value to a comma-separated string:
     - If `self.referrer_policy` is an instance of `str`: split on commas, strip whitespace from each resulting token, then rejoin with commas.
     - Otherwise (it is some other iterable): use it directly as-is.
   - Call `response.setdefault('Referrer-Policy', normalized_value)`. Sets the header only if absent.

5. Return `response`.