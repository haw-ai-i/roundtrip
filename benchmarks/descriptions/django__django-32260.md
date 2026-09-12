## django/contrib/admindocs/utils.py
```markdown
# Specification for `django/contrib/admindocs/utils.py`

## 1. Module-Level Preamble

### Imports
*   `import re`
*   `from email.errors import HeaderParseError`
*   `from email.parser import HeaderParser`
*   `from inspect import cleandoc`
*   `from django.urls import reverse`
*   `from django.utils.regex_helper import _lazy_re_compile`
*   `from django.utils.safestring import mark_safe`

The following imports are attempted within a `try...except ImportError` block:
*   `import docutils.core`
*   `import docutils.nodes`
*   `import docutils.parsers.rst.roles`

### Constants & Globals
*   `docutils_is_available`: A boolean flag set to `True` if the `docutils` imports succeed, and `False` if an `ImportError` is caught.
*   `ROLES`: A dictionary mapping reST role names to their corresponding URL path templates:
    ```python
    {
        'model': '%s/models/%s/',
        'view': '%s/views/%s/',
        'template': '%s/templates/%s/',
        'filter': '%s/filters/#%s',
        'tag': '%s/tags/#%s',
    }
    ```
*   `named_group_matcher`: A compiled regular expression matching the start of a named capture group: `_lazy_re_compile(r'\(\?P(<\w+>)')`.
*   `unnamed_group_matcher`: A compiled regular expression matching an open parenthesis: `_lazy_re_compile(r'\(')`.

### Module-Level Execution
If `docutils_is_available` is `True`, the module registers canonical roles:
1.  Registers `'cmsreference'` using `default_reference_role`.
2.  Iterates over `ROLES.items()` and calls `create_reference_role(name, urlbase)` for each key-value pair.

---

## 2. Code Objects

### `get_view_name(view_func)`
*   **Signature:** `def get_view_name(view_func):`
*   **Implementation Logic:**
    *   Retrieves the module name of the view function via `view_func.__module__`.
    *   Retrieves the view name using `getattr(view_func, '__qualname__', view_func.__class__.__name__)`.
    *   Returns the concatenated string: `mod_name + '.' + view_name`.

### `parse_docstring(docstring)`
*   **Signature:** `def parse_docstring(docstring):`
*   **Implementation Logic:**
    *   If `docstring` is falsy, returns `('', '', {})`.
    *   Cleans the docstring using `cleandoc(docstring)`.
    *   Splits the docstring into parts using `re.split(r'\n{2,}', docstring)`.
    *   The first part (`parts[0]`) is assigned to `title`.
    *   If there is only one part, `body` is `''` and `metadata` is `{}`.
    *   Otherwise, it attempts to parse the last part (`parts[-1]`) as email headers using `HeaderParser().parsestr()`.
        *   If a `HeaderParseError` occurs, `metadata` is `{}` and `body` is formed by joining all parts except the first (`parts[1:]`) with `"\n\n"`.
        *   If parsing succeeds, `metadata` is converted to a standard dictionary (`dict(metadata.items())`).
            *   If `metadata` is not empty, `body` is formed by joining `parts[1:-1]` with `"\n\n"`.
            *   If `metadata` is empty, `body` is formed by joining `parts[1:]` with `"\n\n"`.
    *   Returns a tuple: `(title, body, metadata)`.

### `parse_rst(text, default_reference_context, thing_being_parsed=None)`
*   **Signature:** `def parse_rst(text, default_reference_context, thing_being_parsed=None):`
*   **Implementation Logic:**
    *   Defines a dictionary `overrides` for docutils settings:
        *   `'doctitle_xform'`: `True`
        *   `'initial_header_level'`: `3`
        *   `'default_reference_context'`: `default_reference_context`
        *   `'link_base'`: The result of `reverse('django-admindocs-docroot').rstrip('/')`
        *   `'raw_enabled'`: `False`
        *   `'file_insertion_enabled'`: `False`
    *   If `thing_being_parsed` is truthy, formats it as `'<%s>' % thing_being_parsed`.
    *   Wraps the input `text` in a reST string that sets the default role to `cmsreference` before the text and resets it after:
        ```rst
        .. default-role:: cmsreference

        %s

        .. default-role::
        ```
    *   Calls `docutils.core.publish_parts` with the formatted source, `source_path=thing_being_parsed`, `destination_path=None`, `writer_name='html'`, and `settings_overrides=overrides`.
    *   Returns the `'fragment'` part of the result, wrapped in `mark_safe()`.

### `create_reference_role(rolename, urlbase)`
*   **Signature:** `def create_reference_role(rolename, urlbase):`
*   **Implementation Logic:**
    *   Defines an inner function `_role(name, rawtext, text, lineno, inliner, options=None, content=None)`:
        *   Initializes `options` to `{}` if it is `None`.
        *   Creates a `docutils.nodes.reference` node. The `refuri` is constructed by formatting `urlbase` with `inliner.document.settings.link_base` and `text.lower()`. Passes `**options` to the node constructor.
        *   Returns `([node], [])`.
    *   Registers the inner function as a canonical role using `docutils.parsers.rst.roles.register_canonical_role(rolename, _role)`.

### `default_reference_role(name, rawtext, text, lineno, inliner, options=None, content=None)`
*   **Signature:** `def default_reference_role(name, rawtext, text, lineno, inliner, options=None, content=None):`
*   **Implementation Logic:**
    *   Initializes `options` to `{}` if it is `None`.
    *   Retrieves `context` from `inliner.document.settings.default_reference_context`.
    *   Creates a `docutils.nodes.reference` node. The `refuri` is constructed by formatting `ROLES[context]` with `inliner.document.settings.link_base` and `text.lower()`. Passes `**options` to the node constructor.
    *   Returns `([node], [])`.

### `replace_named_groups(pattern)`
*   **Signature:** `def replace_named_groups(pattern):`
*   **Implementation Logic:**
    *   Finds all matches of `named_group_matcher` in `pattern`. Collects a list of tuples: `(start_index, end_index, group_name)` for each match.
    *   Iterates over these matches to find the full extent of each named capture group, handling nested parentheses:
        *   Initializes `unmatched_open_brackets = 1` and `prev_char = None`.
        *   Iterates over the characters in `pattern` starting from `end_index`.
        *   Increments `unmatched_open_brackets` for unescaped `'('` and decrements for unescaped `')'`.
        *   When `unmatched_open_brackets` reaches `0`, the end of the group is found. Records the full group substring and its `group_name`.
    *   Iterates over the recorded substrings and replaces each occurrence in `pattern` with its corresponding `group_name`.
    *   Returns the modified `pattern`.

### `replace_unnamed_groups(pattern)`
*   **Signature:** `def replace_unnamed_groups(pattern):`
*   **Implementation Logic:**
    *   Finds all start indices of `unnamed_group_matcher` in `pattern`.
    *   Iterates over these start indices to find the full extent of each unnamed capture group, handling nested parentheses similarly to `replace_named_groups`. Records `(start, end)` indices for each group.
    *   Filters the recorded indices to remove nested unnamed groups (i.e., if a group starts before the previous group ends, it is skipped).
    *   If there are valid group indices, constructs a new string by replacing the substrings at these indices with `'<var>'`. It carefully slices the original `pattern` to avoid index shifting issues during replacement.
    *   Returns the modified `pattern` (or the original `pattern` if no unnamed groups were found).
```

## django/urls/resolvers.py
```markdown
# Specification for `django/urls/resolvers.py`

## 1. Module-Level Preamble

### Imports
```python
import functools
import inspect
import re
import string
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
from django.utils.regex_helper import _lazy_re_compile, normalize
from django.utils.translation import get_language
from .converters import get_converter
from .exceptions import NoReverseMatch, Resolver404
from .utils import get_callable
```

### Constants & Globals
- `_PATH_PARAMETER_COMPONENT_RE`: `_lazy_re_compile(r'<(?:(?P<converter>[^>:]+):)?(?P<parameter>[^>]+)>')`

---

## 2. Code Objects

### `ResolverMatch`
**Header:** `class ResolverMatch:`
**Implementation Logic:**
- `__init__(self, func, args, kwargs, url_name=None, app_names=None, namespaces=None, route=None, tried=None)`:
  - Assigns `func`, `args`, `kwargs`, `url_name`, `route`, and `tried` to instance attributes.
  - `app_names`: Filters the provided `app_names` for truthy values; defaults to `[]`.
  - `app_name`: Joins `app_names` with `':'`.
  - `namespaces`: Filters the provided `namespaces` for truthy values; defaults to `[]`.
  - `namespace`: Joins `namespaces` with `':'`.
  - `_func_path`: If `func` lacks a `__name__` attribute, it is set to `func.__class__.__module__ + '.' + func.__class__.__name__`. Otherwise, it is set to `func.__module__ + '.' + func.__name__`.
  - `view_name`: Joins `namespaces` and `[url_name or self._func_path]` with `':'`.
- `__getitem__(self, index)`: Returns the element at `index` from the tuple `(self.func, self.args, self.kwargs)`.
- `__repr__(self)`: Returns a string representation of the object.

### `get_resolver`
**Header:** `def get_resolver(urlconf=None)`
**Implementation Logic:**
- If `urlconf` is `None`, defaults to `settings.ROOT_URLCONF`.
- Returns the result of `_get_cached_resolver(urlconf)`.

### `_get_cached_resolver`
**Header:** `@functools.lru_cache(maxsize=None) def _get_cached_resolver(urlconf=None)`
**Implementation Logic:**
- Returns a new `URLResolver` instantiated with `RegexPattern(r'^/')` and `urlconf`.

### `get_ns_resolver`
**Header:** `@functools.lru_cache(maxsize=None) def get_ns_resolver(ns_pattern, resolver, converters)`
**Implementation Logic:**
- Creates a `RegexPattern` from `ns_pattern`.
- Sets the pattern's `converters` to `dict(converters)`.
- Creates a `URLResolver` named `ns_resolver` using the pattern and `resolver.url_patterns`.
- Returns a new `URLResolver` instantiated with `RegexPattern(r'^/')` and `[ns_resolver]`.

### `LocaleRegexDescriptor`
**Header:** `class LocaleRegexDescriptor:`
**Implementation Logic:**
- `__init__(self, attr)`: Stores the attribute name `attr`.
- `__get__(self, instance, cls=None)`:
  - Returns `self` if `instance` is `None`.
  - Retrieves the pattern string from `getattr(instance, self.attr)`.
  - If the pattern is a standard `str`, compiles it via `instance._compile(pattern)`, caches it in `instance.__dict__['regex']`, and returns it.
  - Otherwise, gets the current language code via `get_language()`.
  - Compiles and caches the pattern in `instance._regex_dict[language_code]` if not already present, and returns it.

### `CheckURLMixin`
**Header:** `class CheckURLMixin:`
**Implementation Logic:**
- `describe(self)`: Returns a string representation of the pattern, appending its name if it exists.
- `_check_pattern_startswith_slash(self)`:
  - Returns `[]` if `settings.APPEND_SLASH` is `False`.
  - Returns a list containing a `Warning` (id `"urls.W002"`) if the regex pattern starts with `'/'`, `'^/'`, or `'^\\/'` and does not end with `'/'`. Otherwise, returns `[]`.

### `RegexPattern`
**Header:** `class RegexPattern(CheckURLMixin):`
**Attributes:**
- `regex = LocaleRegexDescriptor('_regex')`
**Implementation Logic:**
- `__init__(self, regex, name=None, is_endpoint=False)`: Initializes `_regex`, `_regex_dict = {}`, `_is_endpoint`, `name`, and `converters = {}`.
- `match(self, path)`:
  - Searches `path` using `self.regex`.
  - If a match is found, extracts `kwargs` from `match.groupdict()`. If `kwargs` is empty, extracts `args` from `match.groups()`; otherwise, `args` is `()`.
  - Filters `kwargs` to remove `None` values.
  - Returns a tuple: `(path[match.end():], args, kwargs)`. Returns `None` if no match.
- `check(self)`: Returns a list of warnings from `_check_pattern_startswith_slash()` and, if `not self._is_endpoint`, `_check_include_trailing_dollar()`.
- `_check_include_trailing_dollar(self)`: Returns a `Warning` (id `'urls.W001'`) if the pattern ends with `'$'` but not `r'\$'`.
- `_compile(self, regex)`: Compiles the regex. Raises `ImproperlyConfigured` on `re.error`.
- `__str__(self)`: Returns `str(self._regex)`.

### `_route_to_regex`
**Header:** `def _route_to_regex(route, is_endpoint=False)`
**Implementation Logic:**
- Converts a path route (e.g., `'foo/<int:pk>'`) into a regex string and a dictionary of converters.
- Iterates over matches of `_PATH_PARAMETER_COMPONENT_RE` in `route`.
- Raises `ImproperlyConfigured` if the parameter contains whitespace, uses an invalid Python identifier, or specifies an unregistered converter.
- Defaults the converter to `'str'` if unspecified.
- Returns a tuple containing the joined regex string and the `converters` dictionary.

### `RoutePattern`
**Header:** `class RoutePattern(CheckURLMixin):`
**Attributes:**
- `regex = LocaleRegexDescriptor('_route')`
**Implementation Logic:**
- `__init__(self, route, name=None, is_endpoint=False)`: Initializes `_route`, `_regex_dict = {}`, `_is_endpoint`, and `name`. Sets `converters` using `_route_to_regex`.
- `match(self, path)`:
  - Searches `path` using `self.regex`.
  - If a match is found, extracts `kwargs` from `match.groupdict()`.
  - Converts each value in `kwargs` using the corresponding converter's `to_python` method. Returns `None` if a `ValueError` occurs.
  - Returns `(path[match.end():], (), kwargs)`. Returns `None` if no match.
- `check(self)`: Returns warnings from `_check_pattern_startswith_slash()`. Appends a `Warning` (id `'2_0.W001'`) if the route contains `'(?P<'`, starts with `'^'`, or ends with `'$'`.
- `_compile(self, route)`: Compiles the regex generated by `_route_to_regex`.
- `__str__(self)`: Returns `str(self._route)`.

### `LocalePrefixPattern`
**Header:** `class LocalePrefixPattern:`
**Implementation Logic:**
- `__init__(self, prefix_default_language=True)`: Initializes `prefix_default_language` and `converters = {}`.
- `regex` (property): Returns `re.compile(self.language_prefix)`.
- `language_prefix` (property): Returns `''` if the current language is the default and `prefix_default_language` is `False`. Otherwise, returns `'%s/' % language_code`.
- `match(self, path)`: Returns `(path[len(self.language_prefix):], (), {})` if `path` starts with `self.language_prefix`. Otherwise, returns `None`.
- `check(self)`: Returns `[]`.
- `describe(self)`: Returns a string representation.
- `__str__(self)`: Returns `self.language_prefix`.

### `URLPattern`
**Header:** `class URLPattern:`
**Implementation Logic:**
- `__init__(self, pattern, callback, default_args=None, name=None)`: Initializes `pattern`, `callback`, `default_args` (defaults to `{}`), and `name`.
- `__repr__(self)`: Returns a string representation.
- `check(self)`: Returns warnings from `_check_pattern_name()` and `self.pattern.check()`.
- `_check_pattern_name(self)`: Returns a `Warning` (id `"urls.W003"`) if `self.pattern.name` contains a colon.
- `resolve(self, path)`: Calls `self.pattern.match(path)`. If a match is found, updates `kwargs` with `self.default_args` and returns a `ResolverMatch`.
- `lookup_str` (cached property): Returns a string identifying the callback view.

### `URLResolver`
**Header:** `class URLResolver:`
**Implementation Logic:**
- `__init__(self, pattern, urlconf_name, default_kwargs=None, app_name=None, namespace=None)`: Initializes attributes including `_reverse_dict`, `_namespace_dict`, `_app_dict`, `_callback_strs`, `_populated = False`, and `_local = Local()`.
- `__repr__(self)`: Returns a string representation.
- `check(self)`: Returns messages from `check_resolver` for each pattern in `self.url_patterns`, plus `self._check_custom_error_handlers()`. Falls back to `self.pattern.check()` if empty.
- `_check_custom_error_handlers(self)`: Validates custom error handlers (400, 403, 404, 500). Returns `Error`s (ids `'urls.E008'`, `'urls.E007'`) for import failures or incorrect signatures.
- `_populate(self)`: Populates the reverse, namespace, and app dictionaries for the current language. Uses `self._local.populating` to prevent infinite recursion during concurrent access.
- `reverse_dict`, `namespace_dict`, `app_dict` (properties): Calls `_populate()` if the current language code is not cached, then returns the respective dictionary.
- `_extend_tried(tried, pattern, sub_tried=None)` (static method): Appends `pattern` and any `sub_tried` patterns to the `tried` list.
- `_join_route(route1, route2)` (static method): Joins two routes, stripping a leading `'^'` from `route2`.
- `_is_callback(self, name)`: Returns `True` if `name` is in `self._callback_strs`.
- `resolve(self, path)`:
  - Matches `path` against `self.pattern`.
  - If matched, iterates through `self.url_patterns` and attempts to resolve the remaining path.
  - Merges `kwargs` and `args` from sub-matches.
  - Returns a `ResolverMatch` on success.
  - Raises `Resolver404` if no patterns match, extending the `tried` list for debugging.
- `urlconf_module` (cached property): Imports and returns `self.urlconf_name` if it is a string; otherwise returns it directly.
- `url_patterns` (cached property): Returns the `urlpatterns` attribute of `self.urlconf_module`. Raises `ImproperlyConfigured` if it is not iterable.
- `resolve_error_handler(self, view_type)`: Returns the callable for the specified error handler (e.g., `handler404`).
- `reverse(self, lookup_view, *args, **kwargs)`: Calls `self._reverse_with_prefix(lookup_view, '', *args, **kwargs)`.
- `_reverse_with_prefix(self, lookup_view, _prefix, *args, **kwargs)`:
  - Raises `ValueError` if both `args` and `kwargs` are provided.
  - Looks up `lookup_view` in `self.reverse_dict`.
  - Iterates over possibilities, matching provided arguments against expected parameters.
  - Converts arguments to URL strings using converters.
  - Substitutes arguments into the pattern and verifies the regex match.
  - Returns the quoted URL using `escape_leading_slashes`.
  - Raises `NoReverseMatch` if no valid URL can be constructed.
```

## django/views/debug.py
This is a complete natural-language specification of the `django/views/debug.py` file.

## Module-Level Preamble

### Imports
*   `import functools`
*   `import re`
*   `import sys`
*   `import types`
*   `import warnings`
*   `from pathlib import Path`
*   `from django.conf import settings`
*   `from django.http import Http404, HttpResponse, HttpResponseNotFound`
*   `from django.template import Context, Engine, TemplateDoesNotExist`
*   `from django.template.defaultfilters import pprint`
*   `from django.urls import resolve`
*   `from django.utils import timezone`
*   `from django.utils.datastructures import MultiValueDict`
*   `from django.utils.encoding import force_str`
*   `from django.utils.module_loading import import_string`
*   `from django.utils.regex_helper import _lazy_re_compile`
*   `from django.utils.version import get_docs_version`

### Constants & Globals
*   `DEBUG_ENGINE`: An instance of `django.template.Engine` initialized with `debug=True` and `libraries={'i18n': 'django.templatetags.i18n'}`.
*   `CURRENT_DIR`: A `pathlib.Path` object representing the parent directory of the current file (`Path(__file__).parent`).

## Code Objects

### `ExceptionCycleWarning` (Class)
*   **Base Class:** `UserWarning`
*   **Implementation Logic:** An empty exception class used to warn about cycles in exception chains.

### `CallableSettingWrapper` (Class)
*   **Implementation Logic:** Wraps a callable setting to prevent it from being called or breaking the debug page.
*   **`__init__(self, callable_setting)`:** Stores `callable_setting` in `self._wrapped`.
*   **`__repr__(self)`:** Returns the `repr()` of `self._wrapped`.

### `technical_500_response(request, exc_type, exc_value, tb, status_code=500)` (Function)
*   **Implementation Logic:**
    1.  Instantiates the exception reporter class obtained via `get_exception_reporter_class(request)`, passing `request`, `exc_type`, `exc_value`, and `tb`.
    2.  If `request.accepts('text/html')` is true, calls `reporter.get_traceback_html()` and returns an `HttpResponse` with the HTML content, the given `status_code`, and `content_type='text/html'`.
    3.  Otherwise, calls `reporter.get_traceback_text()` and returns an `HttpResponse` with the text content, the given `status_code`, and `content_type='text/plain; charset=utf-8'`.

### `get_default_exception_reporter_filter()` (Function)
*   **Decorators:** `@functools.lru_cache()`
*   **Implementation Logic:** Imports the class specified by `settings.DEFAULT_EXCEPTION_REPORTER_FILTER` using `import_string` and returns an instance of it.

### `get_exception_reporter_filter(request)` (Function)
*   **Implementation Logic:** Retrieves the default filter using `get_default_exception_reporter_filter()`. Returns the value of `request.exception_reporter_filter` if it exists, otherwise returns the default filter.

### `get_exception_reporter_class(request)` (Function)
*   **Implementation Logic:** Imports the class specified by `settings.DEFAULT_EXCEPTION_REPORTER` using `import_string`. Returns the value of `request.exception_reporter_class` if it exists, otherwise returns the imported class.

### `SafeExceptionReporterFilter` (Class)
*   **Attributes:**
    *   `cleansed_substitute`: String `'********************'`.
    *   `hidden_settings`: A compiled regex object matching `'API|TOKEN|KEY|SECRET|PASS|SIGNATURE'` (case-insensitive), created using `_lazy_re_compile`.
*   **`cleanse_setting(self, key, value)`:**
    *   Checks if `key` matches `self.hidden_settings`. If `TypeError` occurs during the check, treats it as not matching.
    *   If it matches, returns `self.cleansed_substitute`.
    *   If `value` is a `dict`, recursively cleanses its values (passing the dictionary keys as the `key` argument).
    *   If `value` is a `list` or `tuple`, recursively cleanses its items (passing an empty string `''` as the `key` argument).
    *   Otherwise, keeps the original `value`.
    *   If the resulting cleansed value is callable, wraps it in `CallableSettingWrapper`.
    *   Returns the cleansed value.
*   **`get_safe_settings(self)`:**
    *   Iterates over all uppercase attributes of `settings` (using `dir(settings)`).
    *   Returns a dictionary where keys are the setting names and values are the result of `self.cleanse_setting(key, value)`.
*   **`get_safe_request_meta(self, request)`:**
    *   If `request` lacks a `META` attribute, returns an empty dictionary.
    *   Otherwise, returns a dictionary where keys are from `request.META` and values are cleansed using `self.cleanse_setting(key, value)`.
*   **`is_active(self, request)`:**
    *   Returns `True` if `settings.DEBUG` is exactly `False`, otherwise `False`.
*   **`get_cleansed_multivaluedict(self, request, multivaluedict)`:**
    *   Retrieves `sensitive_post_parameters` from `request` (defaults to `[]`).
    *   If `self.is_active(request)` is true and `sensitive_post_parameters` is truthy:
        *   Creates a copy of `multivaluedict`.
        *   For each parameter in `sensitive_post_parameters`, if it exists in the copied dict, replaces its value with `self.cleansed_substitute`.
        *   Returns the copied dict.
    *   Otherwise, returns the original `multivaluedict`.
*   **`get_post_parameters(self, request)`:**
    *   If `request` is `None`, returns an empty dictionary.
    *   Retrieves `sensitive_post_parameters` from `request` (defaults to `[]`).
    *   If `self.is_active(request)` is true and `sensitive_post_parameters` is truthy:
        *   Creates a copy of `request.POST`.
        *   If `sensitive_post_parameters` equals `'__ALL__'`, replaces all values in the copy with `self.cleansed_substitute`.
        *   Otherwise, replaces values for keys present in `sensitive_post_parameters` with `self.cleansed_substitute`.
        *   Returns the cleansed copy.
    *   Otherwise, returns `request.POST`.
*   **`cleanse_special_types(self, request, value)`:**
    *   Checks if `value` is an instance of `MultiValueDict`. If an exception occurs during the check, returns a string formatted as `'{!r} while evaluating {!r}'.format(e, value)`.
    *   If it is a `MultiValueDict`, returns the result of `self.get_cleansed_multivaluedict(request, value)`.
    *   Otherwise, returns `value`.
*   **`get_traceback_frame_variables(self, request, tb_frame)`:**
    *   Traverses the frame's callers (`tb_frame.f_back`) to find if the `sensitive_variables` decorator was used (looks for a frame where `f_code.co_name` is `'sensitive_variables_wrapper'` and `'sensitive_variables_wrapper'` is in `f_locals`).
    *   If found, extracts the `sensitive_variables` attribute from the wrapper function.
    *   Initializes an empty `cleansed` dictionary.
    *   If `self.is_active(request)` is true and `sensitive_variables` is truthy:
        *   If `sensitive_variables` equals `'__ALL__'`, replaces all local variables in `tb_frame.f_locals` with `self.cleansed_substitute`.
        *   Otherwise, replaces variables named in `sensitive_variables` with `self.cleansed_substitute`, and cleanses the rest using `self.cleanse_special_types`.
    *   If not active or no sensitive variables, cleanses all local variables using `self.cleanse_special_types`.
    *   If the current frame itself is the `'sensitive_variables_wrapper'`, explicitly sets `'func_args'` and `'func_kwargs'` in the `cleansed` dictionary to `self.cleansed_substitute`.
    *   Returns `cleansed.items()`.

### `ExceptionReporter` (Class)
*   **Attributes:**
    *   `html_template_path`: `CURRENT_DIR / 'templates' / 'technical_500.html'`
    *   `text_template_path`: `CURRENT_DIR / 'templates' / 'technical_500.txt'`
*   **`__init__(self, request, exc_type, exc_value, tb, is_email=False)`:**
    *   Initializes instance variables: `request`, `exc_type`, `exc_value`, `tb`, `is_email`.
    *   Sets `self.filter` using `get_exception_reporter_filter(self.request)`.
    *   Sets `self.template_info` to `getattr(self.exc_value, 'template_debug', None)`.
    *   Sets `self.template_does_not_exist` to `False`.
    *   Sets `self.postmortem` to `None`.
*   **`get_traceback_data(self)`:**
    *   If `exc_type` is a subclass of `TemplateDoesNotExist`, sets `self.template_does_not_exist = True` and `self.postmortem` to `self.exc_value.chain` or `[self.exc_value]`.
    *   Retrieves frames using `self.get_traceback_frames()`.
    *   Iterates over frames. For each frame's `'vars'`, applies `pprint` to the values. If a string representation exceeds 4096 characters, trims it and appends `… <trimmed X bytes string>`.
    *   If `exc_type` is a subclass of `UnicodeError`, attempts to extract a `unicode_hint` from the exception arguments using `start` and `end` attributes, decoding with `force_str(..., 'ascii', errors='replace')`.
    *   Determines `user_str`: `None` if `request` is `None`, `str(self.request.user)` if available, or `'[unable to retrieve the current user]'` if an exception occurs.
    *   Constructs a context dictionary `c` containing: `is_email`, `unicode_hint`, `frames`, `request`, `request_meta` (from filter), `user_str`, `filtered_POST_items` (from filter), `settings` (from filter), `sys_executable`, `sys_version_info`, `server_time`, `django_version_info` (from `django.get_version()`), `sys_path`, `template_info`, `template_does_not_exist`, `postmortem`.
    *   If `request` is not `None`, adds `request_GET_items`, `request_FILES_items`, and `request_COOKIES_items` to `c`.
    *   If `exc_type` is available, adds `exception_type` (its `__name__`).
    *   If `exc_value` is available, adds `exception_value` (its string representation).
    *   If `frames` is not empty, adds `lastframe` (the last frame).
    *   Returns `c`.
*   **`get_traceback_html(self)`:**
    *   Reads `self.html_template_path` (utf-8).
    *   Creates a template using `DEBUG_ENGINE.from_string()`.
    *   Renders the template with a `Context` created from `self.get_traceback_data()` with `use_l10n=False`.
    *   Returns the rendered HTML string.
*   **`get_traceback_text(self)`:**
    *   Reads `self.text_template_path` (utf-8).
    *   Creates a template using `DEBUG_ENGINE.from_string()`.
    *   Renders the template with a `Context` created from `self.get_traceback_data()` with `autoescape=False` and `use_l10n=False`.
    *   Returns the rendered text string.
*   **`_get_source(self, filename, loader, module_name)`:**
    *   Attempts to get source code lines using `loader.get_source(module_name)`.
    *   If that fails or returns `None`, attempts to read `filename` directly as bytes and split into lines.
    *   Returns the list of source lines or `None`.
*   **`_get_lines_from_file(self, filename, lineno, context_lines, loader=None, module_name=None)`:**
    *   Retrieves source using `self._get_source`. Returns `None, [], None, []` if source is `None`.
    *   If source lines are bytes, detects encoding from the first two lines (PEP-263 regex `br'coding[:=]\s*([-\w.]+)'`), defaulting to `'ascii'`. Decodes all lines to strings.
    *   Calculates `lower_bound` (`max(0, lineno - context_lines)`) and `upper_bound` (`lineno + context_lines`).
    *   Extracts `pre_context`, `context_line`, and `post_context` based on `lineno`.
    *   Returns `(lower_bound, pre_context, context_line, post_context)`. Returns `None, [], None, []` on `IndexError`.
*   **`_get_explicit_or_implicit_cause(self, exc_value)`:**
    *   Returns `exc_value.__cause__` if it exists.
    *   Otherwise, returns `None` if `exc_value.__suppress_context__` is true, else returns `exc_value.__context__`.
*   **`get_traceback_frames(self)`:**
    *   Builds a list of `exceptions` by traversing causes using `self._get_explicit_or_implicit_cause`. Warns with `ExceptionCycleWarning` and breaks if a cycle is detected.
    *   If no exceptions, returns an empty list.
    *   Pops exceptions from the list (starting from the root cause). For the first exception, uses `self.tb` if it's the only one, otherwise uses its `__traceback__`.
    *   Collects frames for each exception using `self.get_exception_traceback_frames(exc_value, tb)`.
    *   Returns the combined list of frames.
*   **`get_exception_traceback_frames(self, exc_value, tb)`:**
    *   Yields a dictionary for each frame in the traceback `tb`.
    *   If `tb` is `None`, yields a single dummy frame dict indicating the exception cause.
    *   Iterates through `tb`. Skips frames where `__traceback_hide__` is true in `f_locals`.
    *   Extracts `filename`, `function`, `lineno`, `loader`, and `module_name`.
    *   Gets context lines using `self._get_lines_from_file` with 7 context lines.
    *   Yields a dictionary containing: `exc_cause`, `exc_cause_explicit`, `tb`, `type` (`'django'` if module starts with `'django.'`, else `'user'`), `filename`, `function`, `lineno` (1-indexed), `vars` (from filter), `id`, `pre_context`, `context_line`, `post_context`, and `pre_context_lineno` (1-indexed).
    *   Advances to `tb.tb_next`.

### `technical_404_response(request, exception)` (Function)
*   **Implementation Logic:**
    1.  Attempts to extract `error_url` from `exception.args[0]['path']`. Falls back to `request.path_info[1:]`.
    2.  Attempts to extract `tried` from `exception.args[0]['tried']`. If successful, sets `resolved = False`.
    3.  If extraction fails, sets `resolved = True` and gets `tried` from `request.resolver_match.tried`.
    4.  If not resolved, and the URLconf is empty or it's the default URLconf (path is `'/'`, one tried pattern which is the `'admin'` namespace), returns `default_urlconf(request)`.
    5.  Determines `urlconf` from `request.urlconf` or `settings.ROOT_URLCONF`.
    6.  Attempts to `resolve(request.path)` to find the `caller` view name.
    7.  Reads `technical_404.html` template, renders it using `DEBUG_ENGINE` with a context containing `urlconf`, `root_urlconf`, `request_path`, `urlpatterns`, `resolved`, `reason`, `request`, `settings` (cleansed), and `raising_view_name`.
    8.  Returns an `HttpResponseNotFound` with the rendered HTML.

### `default_urlconf(request)` (Function)
*   **Implementation Logic:**
    1.  Reads `default_urlconf.html` template.
    2.  Renders it using `DEBUG_ENGINE` with a context containing `version` (from `get_docs_version()`).
    3.  Returns an `HttpResponse` with the rendered HTML and `content_type='text/html'`.

## django/views/generic/base.py
```markdown
1.  **Module-Level Preamble:**
    *   **Imports:**
        *   `import logging`
        *   `from functools import update_wrapper`
        *   `from django.core.exceptions import ImproperlyConfigured`
        *   `from django.http import HttpResponse, HttpResponseGone, HttpResponseNotAllowed, HttpResponsePermanentRedirect, HttpResponseRedirect`
        *   `from django.template.response import TemplateResponse`
        *   `from django.urls import reverse`
        *   `from django.utils.decorators import classonlymethod`
    *   **Constants & Globals:**
        *   `logger`: Initialized via `logging.getLogger('django.request')`.

2.  **Code Objects (Classes and Functions):**

    *   **Class `ContextMixin`:**
        *   **Attributes:**
            *   `extra_context`: Initialized to `None` at the class level.
        *   **Method `get_context_data(self, **kwargs)`:**
            *   **Logic:** Sets the key `'view'` in `kwargs` to `self` using `setdefault`. If `self.extra_context` is not `None`, updates `kwargs` with the contents of `self.extra_context`.
            *   **Returns:** The updated `kwargs` dictionary.

    *   **Class `View`:**
        *   **Attributes:**
            *   `http_method_names`: Class attribute, list of strings `['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']`.
        *   **Method `__init__(self, **kwargs)`:**
            *   **Logic:** Iterates over `kwargs.items()` and sets each key-value pair as an attribute on `self` using `setattr`.
        *   **Method `as_view(cls, **initkwargs)`:**
            *   **Decorators:** `@classonlymethod`
            *   **Logic:**
                *   Iterates over keys in `initkwargs`. If a key is in `cls.http_method_names`, raises a `TypeError` indicating the method name is not accepted as a keyword argument.
                *   If a key is not an existing attribute of `cls` (`hasattr(cls, key)` is false), raises a `TypeError` indicating an invalid keyword argument.
                *   Defines an inner function `view(request, *args, **kwargs)`:
                    *   Instantiates the class: `self = cls(**initkwargs)`.
                    *   Calls `self.setup(request, *args, **kwargs)`.
                    *   Checks if `self` has a `'request'` attribute. If not, raises an `AttributeError` suggesting `setup()` was overridden without calling `super()`.
                    *   Returns the result of `self.dispatch(request, *args, **kwargs)`.
                *   Sets `view.view_class = cls` and `view.view_initkwargs = initkwargs`.
                *   Calls `update_wrapper(view, cls, updated=())` to copy name and docstring.
                *   Calls `update_wrapper(view, cls.dispatch, assigned=())` to copy attributes set by decorators on `dispatch`.
            *   **Returns:** The `view` function.
        *   **Method `setup(self, request, *args, **kwargs)`:**
            *   **Logic:** If `self` has a `'get'` attribute but no `'head'` attribute, sets `self.head = self.get`. Sets `self.request = request`, `self.args = args`, and `self.kwargs = kwargs`.
        *   **Method `dispatch(self, request, *args, **kwargs)`:**
            *   **Logic:** Checks if `request.method.lower()` is in `self.http_method_names`. If so, retrieves the corresponding method from `self` using `getattr`, defaulting to `self.http_method_not_allowed` if the method doesn't exist. If the request method is not in the list, sets the handler to `self.http_method_not_allowed`.
            *   **Returns:** The result of calling the determined `handler(request, *args, **kwargs)`.
        *   **Method `http_method_not_allowed(self, request, *args, **kwargs)`:**
            *   **Logic:** Logs a warning using `logger.warning` with the message `'Method Not Allowed (%s): %s'`, passing `request.method` and `request.path`, and `extra={'status_code': 405, 'request': request}`.
            *   **Returns:** An `HttpResponseNotAllowed` instance initialized with the result of `self._allowed_methods()`.
        *   **Method `options(self, request, *args, **kwargs)`:**
            *   **Logic:** Creates an `HttpResponse` object. Sets its `'Allow'` header to a comma-separated string of the methods returned by `self._allowed_methods()`. Sets its `'Content-Length'` header to `'0'`.
            *   **Returns:** The `HttpResponse` object.
        *   **Method `_allowed_methods(self)`:**
            *   **Logic:** Iterates over `self.http_method_names`.
            *   **Returns:** A list of uppercase strings for each method name that exists as an attribute on `self` (checked via `hasattr`).

    *   **Class `TemplateResponseMixin`:**
        *   **Attributes:**
            *   `template_name`: Class attribute, initialized to `None`.
            *   `template_engine`: Class attribute, initialized to `None`.
            *   `response_class`: Class attribute, initialized to `TemplateResponse`.
            *   `content_type`: Class attribute, initialized to `None`.
        *   **Method `render_to_response(self, context, **response_kwargs)`:**
            *   **Logic:** Uses `setdefault` on `response_kwargs` to set `'content_type'` to `self.content_type`.
            *   **Returns:** An instance of `self.response_class`, initialized with `request=self.request`, `template=self.get_template_names()`, `context=context`, `using=self.template_engine`, and unpacked `**response_kwargs`.
        *   **Method `get_template_names(self)`:**
            *   **Logic:** Checks if `self.template_name` is `None`. If so, raises an `ImproperlyConfigured` exception.
            *   **Returns:** A list containing `self.template_name`.

    *   **Class `TemplateView(TemplateResponseMixin, ContextMixin, View)`:**
        *   **Method `get(self, request, *args, **kwargs)`:**
            *   **Logic:** Calls `self.get_context_data(**kwargs)` to get the context.
            *   **Returns:** The result of `self.render_to_response(context)`.

    *   **Class `RedirectView(View)`:**
        *   **Attributes:**
            *   `permanent`: Class attribute, initialized to `False`.
            *   `url`: Class attribute, initialized to `None`.
            *   `pattern_name`: Class attribute, initialized to `None`.
            *   `query_string`: Class attribute, initialized to `False`.
        *   **Method `get_redirect_url(self, *args, **kwargs)`:**
            *   **Logic:**
                *   If `self.url` is truthy, formats it using string interpolation with `kwargs` (`self.url % kwargs`).
                *   Else if `self.pattern_name` is truthy, calls `reverse(self.pattern_name, args=args, kwargs=kwargs)`.
                *   Else, returns `None`.
                *   Retrieves the query string from `self.request.META.get('QUERY_STRING', '')`.
                *   If the query string is truthy and `self.query_string` is truthy, appends `?` and the query string to the URL.
            *   **Returns:** The constructed URL string or `None`.
        *   **Method `get(self, request, *args, **kwargs)`:**
            *   **Logic:** Calls `self.get_redirect_url(*args, **kwargs)`.
                *   If a URL is returned: checks `self.permanent`. If true, returns an `HttpResponsePermanentRedirect(url)`. Otherwise, returns an `HttpResponseRedirect(url)`.
                *   If no URL is returned: logs a warning using `logger.warning` with message `'Gone: %s'`, passing `request.path` and `extra={'status_code': 410, 'request': request}`. Returns an `HttpResponseGone()`.
        *   **Methods `head`, `post`, `options`, `delete`, `put`, `patch`:**
            *   **Signature:** `(self, request, *args, **kwargs)` for all.
            *   **Logic:** All these methods simply call and return the result of `self.get(request, *args, **kwargs)`.
```