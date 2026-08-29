## django/urls/base.py
Here is the complete natural-language specification of `/tmp/omp_desc_hefzpnk4/django/urls/base.py`:

---

## Module-Level Preamble

### Imports

```python
from urllib.parse import urlsplit, urlunsplit
from asgiref.local import Local
from django.utils.encoding import iri_to_uri
from django.utils.functional import lazy
from django.utils.translation import override
from .exceptions import NoReverseMatch, Resolver404
from .resolvers import get_ns_resolver, get_resolver
from .utils import get_callable
```

### Constants & Globals

- **`_prefixes`** — An instance of `asgiref.local.Local`. Stores SCRIPT_NAME prefixes scoped to the current thread. If no entry exists for the current thread (the only one ever accessed), it is assumed to be empty.
- **`_urlconfs`** — An instance of `asgiref.local.Local`. Stores overridden URLconf module names scoped to the current thread.

---

## Code Objects

### `resolve(path, urlconf=None)`

**Signature:** `(path: str, urlconf: Optional[str] = None) -> ResolverMatch`

1. If `urlconf` is `None`, set it to the result of `get_urlconf()`.
2. Call `get_resolver(urlconf)` to obtain a resolver instance, then call `.resolve(path)` on it and return its result.

---

### `reverse(viewname, urlconf=None, args=None, kwargs=None, current_app=None)`

**Signature:** `(viewname: Union[str, Callable], urlconf: Optional[str] = None, args: Optional[list] = None, kwargs: Optional[dict] = None, current_app: Optional[str] = None) -> str`

1. If `urlconf` is `None`, set it to the result of `get_urlconf()`.
2. Obtain a resolver via `get_resolver(urlconf)`.
3. Set `args = args or []` and `kwargs = kwargs or {}`.
4. Retrieve the script prefix via `prefix = get_script_prefix()`.
5. **If `viewname` is not a string** (i.e., it is a callable/view): directly call `resolver._reverse_with_prefix(viewname, prefix, *args, **kwargs)` and return `iri_to_uri(...)` of that result.
6. **If `viewname` is a string:**
   - Split `viewname` on `':'` into components: `*path, view = viewname.split(':')`. Here `path` is a list of namespace segments (possibly empty), and `view` is the final URL name.
   - If `current_app` is provided, split it on `':'`, reverse the resulting list, and assign to `current_path`; otherwise set `current_path = None`.
   - Initialize `resolved_path = []`, `ns_pattern = ''`, and `ns_converters = {}`.
   - **For each namespace segment `ns` in `path`:**
     a. Pop the last element from `current_path` (if non-empty) into `current_ns`; otherwise `current_ns = None`.
     b. Attempt to look up `ns` in `resolver.app_dict[ns]` to see if it matches an app name:
        - If lookup succeeds and `current_ns` is set and present in the resulting `app_list`, override `ns = current_ns`.
        - If lookup succeeds but `ns` is not in `app_list` (i.e., multiple app instances share different namespaces), set `ns = app_list[0]` (first instance as default).
     c. If `ns != current_ns`, reset `current_path = None`.
     d. Attempt to look up `ns` in `resolver.namespace_dict[ns]`:
        - On success, unpack `(extra, resolver)` from the tuple: append `ns` to `resolved_path`, update `ns_pattern += extra`, and merge `resolver.pattern.converters` into `ns_converters`. Then reassign `resolver = get_ns_resolver(ns_pattern, resolver, tuple(ns_converters.items()))` for the next iteration.
        - On `KeyError`: if `resolved_path` is non-empty, raise `NoReverseMatch(f"{key} is not a registered namespace inside '{':'.join(resolved_path)}'")`; otherwise raise `NoReverseMatch(f"{key} is not a registered namespace" % key)`.
   - After the loop, if `ns_pattern` is non-empty, call `resolver = get_ns_resolver(ns_pattern, resolver, tuple(ns_converters.items()))`.
7. Return `iri_to_uri(resolver._reverse_with_prefix(view, prefix, *args, **kwargs))`.

---

### `reverse_lazy`

A lazy-evaluation wrapper created by `lazy(reverse, str)`. It returns a lazy string object that defers execution of `reverse()` until the value is coerced to a string.

---

### `clear_url_caches()`

1. Call `get_callable.cache_clear()`.
2. Call `get_resolver.cache_clear()`.
3. Call `get_ns_resolver.cache_clear()`.

---

### `set_script_prefix(prefix)`

**Signature:** `(prefix: str) -> None`

1. If `prefix` does not end with `'/'`, append `'/'` to it.
2. Set `_prefixes.value = prefix`.

---

### `get_script_prefix()`

**Signature:** `() -> str`

Return `getattr(_prefixes, "value", '/')`. Defaults to `'/'` if no thread-local value is set.

---

### `clear_script_prefix()`

1. Attempt `del _prefixes.value`.
2. If an `AttributeError` is raised (no entry exists), silently pass.

---

### `set_urlconf(urlconf_name)`

**Signature:** `(urlconf_name: Optional[str]) -> None`

1. If `urlconf_name` is truthy, set `_urlconfs.value = urlconf_name`.
2. Otherwise (`None` or falsy): if `_urlconfs` has a `"value"` attribute, delete it via `del _urlconfs.value`.

---

### `get_urlconf(default=None)`

**Signature:** `(default: Optional[str] = None) -> Optional[str]`

Return `getattr(_urlconfs, "value", default)`. Returns the thread-local URLconf override if set; otherwise returns `default`.

---

### `is_valid_path(path, urlconf=None)`

**Signature:** `(path: str, urlconf: Optional[str] = None) -> bool`

1. Attempt to call `resolve(path, urlconf)`.
2. If it succeeds, return `True`.
3. If it raises `Resolver404`, catch the exception and return `False`.

---

### `translate_url(url, lang_code)`

**Signature:** `(url: str, lang_code: str) -> str`

1. Parse `url` via `urlsplit(url)` into a named tuple with fields `scheme`, `netloc`, `path`, `query`, and `fragment`.
2. Attempt to call `resolve(parsed.path)`:
   - On `Resolver404`, skip the translation block entirely.
   - On success, construct `to_be_reversed` as `"%s:%s" % (match.namespace, match.url_name)` if `match.namespace` is truthy; otherwise `"match.url_name"`.
3. Within a `with override(lang_code):` context:
   - Attempt to call `reverse(to_be_reversed, args=match.args, kwargs=match.kwargs)`.
   - On `NoReverseMatch`, silently pass (keep the original URL).
   - On success, reconstruct the full URL via `urlunsplit((parsed.scheme, parsed.netloc, url, parsed.query, parsed.fragment))` and assign to `url`.
4. Return `url` (either the translated version or the original if no translation was found).

---

## django/urls/resolvers.py
I now have the full source. Here is the complete natural-language specification:

---

# Module-Level Preamble

## Imports

```python
import functools
import inspect
import re
from importlib import import_module
from urllib.parse import quote

from asgiref.local import Local

from django.conf import settings
from django.core.checks import Error, Warning
from django.core.checks.urls import check_resolver
from django.core.exceptions import ImproperlyConfigured, ViewDoesNotExist
from django.utils.datastructures import MultiValueDict
from django.utils.functional import cached_property
from django.utils.http import RFC3986_SUBDELIMS, escape_leading_slashes
from django.utils.regex_helper import normalize
from django.utils.translation import get_language

from .converters import get_converter
from .exceptions import NoReverseMatch, Resolver404
from .utils import get_callable
```

## Module Docstring

This module converts requested URLs to callback view functions. `URLResolver` is the main class; its `resolve()` method takes a URL string and returns a `ResolverMatch` object providing access to all attributes of the resolved URL match.

---

# Code Objects

## Class: `ResolverMatch`

**Header:** `class ResolverMatch(func, args, kwargs, url_name=None, app_names=None, namespaces=None, route=None)`

**Attributes (initialized in `__init__`):**
- `func` — the view callback function/class.
- `args` — positional arguments captured from URL matching.
- `kwargs` — keyword arguments captured from URL matching.
- `url_name` — the named URL pattern name, or `None`.
- `route` — the route string of the matched pattern, or `None`.
- `app_names` — list of app-name strings; computed as `[x for x in app_names if x]` (filters falsy entries), defaulting to `[]` when `app_names` is falsy.
- `app_name` — colon-joined string of `self.app_names` (`':'.join(self.app_names)`).
- `namespaces` — list of namespace strings; computed as `[x for x in namespaces if x]`, defaulting to `[]`.
- `namespace` — colon-joined string of `self.namespaces`.
- `_func_path` — dotted path identifying the view: if `func` lacks a `__name__` attribute (class-based view), it is `func.__class__.__module__ + '.' + func.__class__.__name__`; otherwise `func.__module__ + '.' + func.__name__`.
- `view_name` — colon-joined string of `self.namespaces + [url_name or self._func_path]`.

**Methods:**
- `__getitem__(index)` — returns `(self.func, self.args, self.kwargs)[index]`, supporting tuple-style indexing.
- `__repr__()` — returns `"ResolverMatch(func=%s, args=%s, kwargs=%s, url_name=%s, app_names=%s, namespaces=%s, route=%s)" % (self._func_path, self.args, self.kwargs, self.url_name, self.app_names, self.namespaces, self.route)`.

---

## Function: `get_resolver(urlconf=None)`

**Header:** `@functools.lru_cache(maxsize=None) def get_resolver(urlconf=None)`

**Logic:**
1. If `urlconf` is `None`, set it to `settings.ROOT_URLCONF`.
2. Return a new `URLResolver(RegexPattern(r'^/'), urlconf)`.

**Return:** A root-level `URLResolver` wrapping the given (or default) URLconf module path, with a pattern matching `^/`.

---

## Function: `get_ns_resolver(ns_pattern, resolver, converters)`

**Header:** `@functools.lru_cache(maxsize=None) def get_ns_resolver(ns_pattern, resolver, converters)`

**Logic:**
1. Create `pattern = RegexPattern(ns_pattern)`.
2. Assign `pattern.converters = dict(converters)`.
3. Create `ns_resolver = URLResolver(pattern, resolver.url_patterns)`.
4. Return `URLResolver(RegexPattern(r'^/'), [ns_resolver])`.

**Purpose:** Builds a namespaced resolver for the given parent URLconf pattern, enabling captured parameters in the parent URLconf pattern.

---

## Class: `LocaleRegexDescriptor`

**Header:** `class LocaleRegexDescriptor(attr)`

**Attributes (initialized in `__init__`):**
- `attr` — the name of the instance attribute holding the raw regex/route string.

**Methods:**
- `__get__(instance, cls=None)` — descriptor protocol:
  1. If `instance is None`, return `self`.
  2. Retrieve the pattern via `getattr(instance, self.attr)`.
  3. If the pattern is a plain `str` (not a lazy-translated proxy), compile it once and cache on the instance as `instance.__dict__['regex'] = instance._compile(pattern)`, then return it.
  4. Otherwise, get the active language via `get_language()`. If not already in `instance._regex_dict`, compile with `instance._compile(str(pattern))` and store at `instance._regex_dict[language_code]`. Return the compiled regex for that language.

---

## Class: `CheckURLMixin`

**Header:** `class CheckURLMixin`

**Methods:**
- `describe()` — formats the URL pattern for display in warning messages: `"'{self}'"` with an optional `[name='...']` suffix if `self.name` is truthy. Returns a string.
- `_check_pattern_startswith_slash()` — checks that the pattern does not begin with `/`:
  1. If `settings.APPEND_SLASH` is falsy, return `[]`.
  2. Get `regex_pattern = self.regex.pattern`.
  3. If it starts with `'/'`, `'^/'`, or `'^\\/'` and does **not** end with `'/'`, emit a `Warning("Your URL pattern ... has a route beginning with a '/'. Remove this slash...", id="urls.W002")` in a list; otherwise return `[]`.

---

## Class: `RegexPattern(CheckURLMixin)`

**Header:** `class RegexPattern(CheckURLMixin)`

**Class attribute:**
- `regex = LocaleRegexDescriptor('_regex')` — lazy, language-aware compiled regex descriptor.

**Attributes (initialized in `__init__`):**
- `_regex` — the raw regex string.
- `_regex_dict` — dict mapping language codes to compiled regexes.
- `_is_endpoint` — boolean flag; if falsy, this pattern is used with `include()` and gets extra checks.
- `name` — optional name for the pattern.
- `converters` — empty dict `{}` (unused by RegexPattern itself).

**Methods:**
- `match(path)` — attempts to match the path against the compiled regex:
  1. Call `self.regex.search(path)`.
  2. If no match, return `None`.
  3. Build `kwargs = {k: v for k, v in match.groupdict().items() if v is not None}` (named groups only, filtering out `None` values).
  4. If kwargs are non-empty, set `args = ()`; otherwise `args = match.groups()` (all positional captures).
  5. Return `(path[match.end():], args, kwargs)`.
- `check()` — returns a list of warnings:
  1. Start with `warnings = []`, extend with `_check_pattern_startswith_slash()`.
  2. If not `self._is_endpoint`, also extend with `_check_include_trailing_dollar()`.
  3. Return the warnings list.
- `_check_include_trailing_dollar()` — checks for a trailing `$` in the regex when used with `include()`:
  1. Get `regex_pattern = self.regex.pattern`.
  2. If it ends with `'$'` but not `r'\$'`, emit a `Warning("Your URL pattern ... uses include with a route ending with a '$'. Remove the dollar...", id='urls.W001')`; otherwise return `[]`.
- `_compile(regex)` — compiles and returns `re.compile(regex)`. Raises `ImproperlyConfigured` with message `'"%s" is not a valid regular expression: %s' % (regex, e)` if the regex is invalid.
- `__str__()` — returns `str(self._regex)`.

---

## Module-Level Constant: `_PATH_PARAMETER_COMPONENT_RE`

```python
_PATH_PARAMETER_COMPONENT_RE = re.compile(r'<(?:(?P<converter>[^>:]+):)?(?P<parameter>\w+)>')
```

Regex matching Django path parameter components like `<int:pk>` or `<slug>`. Named groups: `converter` (optional, before `:`) and `parameter` (required).

---

## Function: `_route_to_regex(route, is_endpoint=False)`

**Header:** `def _route_to_regex(route, is_endpoint=False)`

**Logic:**
1. Save `original_route = route`. Initialize `parts = ['^']`, `converters = {}`.
2. Loop: search for `_PATH_PARAMETER_COMPONENT_RE` in `route`.
   - If no match: append `re.escape(route)` to parts and break.
   - Otherwise, append `re.escape(route[:match.start()])` to parts; advance `route = route[match.end():]`.
   - Extract `parameter = match.group('parameter')`. If not a valid Python identifier (`not parameter.isidentifier()`), raise `ImproperlyConfigured("URL route '%s' uses parameter name %r which isn't a valid Python identifier." % (original_route, parameter))`.
   - Get `raw_converter = match.group('converter')`; if `None`, default to `'str'`.
   - Look up the converter via `get_converter(raw_converter)`. If not found (`KeyError`), raise `ImproperlyConfigured("URL route '%s' uses invalid converter %s." % (original_route, e))`.
   - Store `converters[parameter] = converter`.
   - Append `'(?P<' + parameter + '>' + converter.regex + ')'` to parts.
3. If `is_endpoint`, append `'$'` to parts.
4. Return `''.join(parts)` and the `converters` dict as a tuple `(regex_string, converters)`.

**Return:** Tuple of `(compiled_regex_string, converters_dict)`.

---

## Class: `RoutePattern(CheckURLMixin)`

**Header:** `class RoutePattern(CheckURLMixin)`

**Class attribute:**
- `regex = LocaleRegexDescriptor('_route')` — lazy, language-aware compiled regex descriptor.

**Attributes (initialized in `__init__`):**
- `_route` — the raw route string (e.g., `'articles/<int:pk>/'`).
- `_regex_dict` — dict mapping language codes to compiled regexes.
- `_is_endpoint` — boolean flag controlling whether a trailing `$` is appended during compilation.
- `name` — optional name for the pattern.
- `converters` — dict of parameter-name-to-converter mappings, set from `_route_to_regex(str(route), is_endpoint)[1]`.

**Methods:**
- `match(path)` — attempts to match the path against the compiled regex:
  1. Call `self.regex.search(path)`.
  2. If no match, return `None`.
  3. Build `kwargs = match.groupdict()`. For each `(key, value)` in kwargs, look up `converter = self.converters[key]` and call `converter.to_python(value)`, replacing the string value with its Python-converted form. If any conversion raises `ValueError`, return `None`.
  4. Return `(path[match.end():], (), kwargs)` — positional args are always empty (RoutePattern does not support unnamed groups).
- `check()` — returns warnings:
  1. Start with `_check_pattern_startswith_slash()`.
  2. If `'(?P<'` is in the route, or the route starts with `'^'`, or ends with `'$'`, append a `Warning("Your URL pattern ... has a route that contains '(?P<', begins with a '^', or ends with a '$'. This was likely an oversight when migrating to django.urls.path().", id='2_0.W001')`.
  3. Return the warnings list.
- `_compile(route)` — returns `re.compile(_route_to_regex(route, self._is_endpoint)[0])`.
- `__str__()` — returns `str(self._route)`.

---

## Class: `LocalePrefixPattern`

**Header:** `class LocalePrefixPattern`

**Attributes (initialized in `__init__`):**
- `prefix_default_language` — boolean; if falsy and the active language equals `settings.LANGUAGE_CODE`, no prefix is added.
- `converters` — empty dict `{}`.

**Methods:**
- `regex` property — returns `re.compile(self.language_prefix)`. Only used by `reverse()` and cached in `_reverse_dict`.
- `language_prefix` property:
  1. Get `language_code = get_language() or settings.LANGUAGE_CODE`.
  2. If `language_code == settings.LANGUAGE_CODE` and not `self.prefix_default_language`, return `''`.
  3. Otherwise, return `'%s/' % language_code`.
- `match(path)` — if the path starts with `self.language_prefix`, return `(path[len(language_prefix):], (), {})`; otherwise return `None`.
- `check()` — returns `[]` (no warnings).
- `describe()` — returns `"'{self}'"` (i.e., `"''"` or `"'/en/'"`, etc.).
- `__str__()` — returns `self.language_prefix`.

---

## Class: `URLPattern`

**Header:** `class URLPattern(pattern, callback, default_args=None, name=None)`

**Attributes (initialized in `__init__`):**
- `pattern` — a pattern object (`RegexPattern`, `RoutePattern`, or `LocalePrefixPattern`).
- `callback` — the view callable.
- `default_args` — dict of default arguments; defaults to `{}` if falsy.
- `name` — optional URL name for reverse lookups.

**Methods:**
- `__repr__()` — returns `'<%s %s>' % (self.__class__.__name__, self.pattern.describe())`.
- `check()` — returns warnings: start with `_check_pattern_name()`, extend with `self.pattern.check()`. Returns the combined list.
- `_check_pattern_name()` — if `self.pattern.name` is not `None` and contains `':'`, emit a `Warning("Your URL pattern ... has a name including a ':'. Remove the colon, to avoid ambiguous namespace references.", id="urls.W003")`; otherwise return `[]`.
- `resolve(path)` — attempts to match:
  1. Call `self.pattern.match(path)`. If no match, implicitly returns `None`.
  2. Unpack `(new_path, args, kwargs) = match`.
  3. Update `kwargs` with `self.default_args` (`kwargs.update(self.default_args)`).
  4. Return `ResolverMatch(self.callback, args, kwargs, self.pattern.name, route=str(self.pattern))`.
- `lookup_str` property (via `@cached_property`) — returns a dotted path identifying the view:
  1. If `self.callback` is a `functools.partial`, unwrap to `callback.func`.
  2. If callback lacks `__name__` (class-based), return `callback.__module__ + "." + callback.__class__.__name__`.
  3. Otherwise, return `callback.__module__ + "." + callback.__qualname__`.

---

## Class: `URLResolver`

**Header:** `class URLResolver(pattern, urlconf_name, default_kwargs=None, app_name=None, namespace=None)`

**Attributes (initialized in `__init__`):**
- `pattern` — the pattern object for this resolver.
- `urlconf_name` — dotted Python path to a URLconf module, or an object with `urlpatterns`, or the patterns list itself.
- `callback` — always initialized to `None`.
- `default_kwargs` — dict of default keyword arguments; defaults to `{}` if falsy.
- `namespace` — optional namespace string.
- `app_name` — optional app-name string.
- `_reverse_dict` — dict mapping language codes to `MultiValueDict`s for reverse lookups.
- `_namespace_dict` — dict mapping language codes to namespace prefix → resolver mappings.
- `_app_dict` — dict mapping language codes to app_name → [namespace, ...] mappings.
- `_callback_strs` — a `set()` of dotted paths to all view functions/classes used in the URL patterns.
- `_populated` — boolean flag; initially `False`.
- `_local` — an `asgiref.local.Local()` instance for thread-local recursion detection during population.

**Methods:**
- `__repr__()` — if `self.urlconf_name` is a non-empty list, use `'<' + self.urlconf_name[0].__class__.__name__ + ' list>'`; otherwise `repr(self.urlconf_name)`. Return `'<%s %s (%s:%s) %s>' % (self.__class__.__name__, urlconf_repr, self.app_name, self.namespace, self.pattern.describe())`.
- `check()` — returns a list of check messages:
  1. For each pattern in `self.url_patterns`, extend with `check_resolver(pattern)` results.
  2. Extend with `self._check_custom_error_handlers()`.
  3. Return the combined list, or fall back to `self.pattern.check()` if no messages were collected.
- `_check_custom_error_handlers()` — validates custom error handler views:
  1. For each `(status_code, num_parameters)` in `[(400,2), (403,2), (404,2), (500,1)]`:
     - Call `self.resolve_error_handler(status_code)`. If it raises `ImportError` or `ViewDoesNotExist`, capture the handler path from `getattr(self.urlconf_module, 'handler%s' % status_code)` and append an `Error("The custom handler{status_code} view '{path}' could not be imported.", hint=str(e), id='urls.E008')`; continue to next.
     - Get `signature = inspect.signature(handler)`. Create `args = [None] * num_parameters`. Try `signature.bind(*args)`. If it raises `TypeError`, append an `Error("The custom handler{status_code} view '{path}' does not take the correct number of arguments ({args}).", id='urls.E007')` where `{args}` is `'request, exception'` if `num_parameters == 2` else `'request'`.
  2. Return the messages list.
- `_populate()` — builds reverse lookup dictionaries (thread-safe via thread-local flag):
  1. If `getattr(self._local, 'populating', False)`, return immediately (prevents infinite recursion in this thread).
  2. Set `self._local.populating = True`. Initialize `lookups = MultiValueDict()`, `namespaces = {}`, `apps = {}`. Get `language_code = get_language()`.
  3. Iterate over `reversed(self.url_patterns)`:
     - Strip leading `'^'` from `url_pattern.pattern.regex.pattern` to get `p_pattern`.
     - **If `isinstance(url_pattern, URLPattern)`**:
       - Add `url_pattern.lookup_str` to `self._callback_strs`.
       - Compute `bits = normalize(url_pattern.pattern.regex.pattern)`.
       - Append `(bits, p_pattern, url_pattern.default_args, url_pattern.pattern.converters)` to `lookups` keyed by `url_pattern.callback`.
       - If `url_pattern.name is not None`, also append the same tuple keyed by `url_pattern.name`.
     - **Else (it's a `URLResolver`)**:
       - Recursively call `url_pattern._populate()`.
       - If `url_pattern.app_name`: add to `apps.setdefault(url_pattern.app_name, []).append(url_pattern.namespace)`; store `namespaces[url_pattern.namespace] = (p_pattern, url_pattern)`.
       - Else: for each name in `url_pattern.reverse_dict`, for each `(matches, pat, defaults, converters)` tuple, compute `new_matches = normalize(p_pattern + pat)` and append `(new_matches, p_pattern + pat, {**defaults, **url_pattern.default_kwargs}, {**self.pattern.converters, **url_pattern.pattern.converters, **converters})` to `lookups`.
       - For each `(namespace, (prefix, sub_pattern))` in `url_pattern.namespace_dict.items()`: update `sub_pattern.pattern.converters` with `current_converters = url_pattern.pattern.converters`; store `namespaces[namespace] = (p_pattern + prefix, sub_pattern)`.
       - For each `(app_name, namespace_list)` in `url_pattern.app_dict.items()`, extend `apps.setdefault(app_name, [])`.
       - Update `self._callback_strs` with `url_pattern._callback_strs`.
  4. Store: `self._namespace_dict[language_code] = namespaces`, `self._app_dict[language_code] = apps`, `self._reverse_dict[language_code] = lookups`.
  5. Set `self._populated = True`.
  6. In a `finally` block, reset `self._local.populating = False`.
- `reverse_dict` property (via `@cached_property`) — if the current language is not in `_reverse_dict`, call `_populate()`. Return `_reverse_dict[language_code]`.
- `namespace_dict` property (via `@cached_property`) — same pattern: populate if needed, return `_namespace_dict[language_code]`.
- `app_dict` property (via `@cached_property`) — same pattern: populate if needed, return `_app_dict[language_code]`.
- `_join_route(route1, route2)` (static method) — joins two routes without the leading `^` in the second: if `route1` is falsy, return `route2`; if `route2.startswith('^')`, strip it; return `route1 + route2`.
- `_is_callback(name)` — if not populated, call `_populate()`. Return `name in self._callback_strs`.
- `resolve(path)` — resolves a URL path to a `ResolverMatch`:
  1. Convert `path` to string (`str(path)`, handles `reverse_lazy`).
  2. Initialize `tried = []`.
  3. Call `self.pattern.match(path)`. If no match, raise `Resolver404({'path': path})`.
  4. Unpack `(new_path, args, kwargs) = match`.
  5. For each pattern in `self.url_patterns`:
     - Try `pattern.resolve(new_path)`. On `Resolver404`, extract `sub_tried = e.args[0].get('tried')`; if not None, extend `tried` with `[pattern] + t for t in sub_tried`; else append `[pattern]`.
     - If successful and `sub_match` is truthy: merge kwargs as `{**kwargs, **self.default_kwargs}`, then update with `sub_match.kwargs`. If the merged dict is empty, combine positional args: `args + sub_match.args`; otherwise keep `sub_match.args`. Compute `current_route = '' if isinstance(pattern, URLPattern) else str(pattern.pattern)`. Return a new `ResolverMatch(sub_match.func, sub_match_args, sub_match_dict, sub_match.url_name, [self.app_name] + sub_match.app_names, [self.namespace] + sub_match.namespaces, self._join_route(current_route, sub_match.route))`.
     - If successful but `sub_match` is falsy (no match), append `[pattern]` to `tried`.
  6. After exhausting all patterns, raise `Resolver404({'tried': tried, 'path': new_path})`.
- `urlconf_module` property (via `@cached_property`) — if `self.urlconf_name` is a string, return `import_module(self.urlconf_name)`; otherwise return `self.urlconf_name` directly.
- `url_patterns` property (via `@cached_property`) — get `patterns = getattr(self.urlconf_module, "urlpatterns", self.urlconf_module)`. Try to iterate it; if `TypeError`, raise `ImproperlyConfigured("The included URLconf '{name}' does not appear to have any patterns in it. If you see valid patterns in the file then the issue is probably caused by a circular import.")`. Return `patterns`.
- `resolve_error_handler(view_type)` — resolves an error handler:
  1. Get `callback = getattr(self.urlconf_module, 'handler%s' % view_type, None)`.
  2. If no callback found, lazily import from `django.conf.urls` and get the default handler via `getattr(urls, 'handler%s' % view_type)`.
  3. Return `(get_callable(callback), {})`.
- `reverse(lookup_view, *args, **kwargs)` — delegates to `_reverse_with_prefix(lookup_view, '', *args, **kwargs)`.
- `_reverse_with_prefix(lookup_view, _prefix, *args, **kwargs)` — reverse URL lookup:
  1. If both `args` and `kwargs` are provided, raise `ValueError("Don't mix *args and **kwargs in call to reverse()!")`.
  2. If not populated, call `_populate()`.
  3. Get `possibilities = self.reverse_dict.getlist(lookup_view)`.
  4. For each `(possibility, pattern, defaults, converters)` tuple:
     - For each `(result, params)` in possibility:
       - **If positional args**: if `len(args) != len(params)`, skip; otherwise build `candidate_subs = dict(zip(params, args))`.
       - **Else (keyword args)**: if `set(kwargs).symmetric_difference(params).difference(defaults)` is non-empty, skip; if any `kwargs.get(k, v) != v` for `(k, v)` in defaults, skip; otherwise `candidate_subs = kwargs`.
       - Convert candidate substitutions to text: for each `(k, v)`, if `k in converters`, use `converters[k].to_url(v)`; else `str(v)`. Store as `text_candidate_subs`.
       - Build `candidate_pat = _prefix.replace('%', '%%') + result`. Check if `re.search('^%s%s' % (re.escape(_prefix), pattern), candidate_pat % text_candidate_subs)` matches. If yes: URL-encode with `quote(candidate_pat % text_candidate_subs, safe=RFC3986_SUBDELIMS + '/~:@')`, apply `escape_leading_slashes()`, and return the result.
  5. After exhausting all possibilities without a match, build an error message:
     - Derive `lookup_view_s` from `getattr(lookup_view, '__module__', None)` and `getattr(lookup_view, '__name__', None)` as `"%s.%s" % (m, n)`, or use the raw value.
     - Get `patterns = [pattern for (_, pattern, _, _) in possibilities]`.
     - If patterns exist: determine `arg_msg` from args/kwargs/no-args; raise `NoReverseMatch("Reverse for '%s' with %s not found. %d pattern(s) tried: %s" % (lookup_view_s, arg_msg, len(patterns), patterns))`.
     - Else: raise `NoReverseMatch("Reverse for '%(view)s' not found. '%(view)s' is not a valid view function or pattern name." % {'view': lookup_view_s})`.

---