## django/contrib/admindocs/utils.py
Here is the complete natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import re
from email.errors import HeaderParseError
from email.parser import HeaderParser
from django.urls import reverse
from django.utils.regex_helper import _lazy_re_compile
from django.utils.safestring import mark_safe
```

A conditional block attempts to import `docutils.core`, `docutils.nodes`, and `docutils.parsers.rst.roles`. If any of these imports fail, the module-level boolean constant `docutils_is_available` is set to `False`; otherwise it is set to `True`.

### Constants & Globals

- **`ROLES`** — A dict mapping string keys to URL-format strings:
  - `'model'`: `'%s/models/%s/'`
  - `'view'`: `'%s/views/%s/'`
  - `'template'`: `'%s/templates/%s/'`
  - `'filter'`: `'%s/filters/#%s'`
  - `'tag'`: `'%s/tags/#%s'`

- **`named_group_matcher`** — A compiled regex (via `_lazy_re_compile`) matching the pattern `r'\(\?P(<\w+>)'`. It matches the beginning of a named capture group, capturing only the `<name>` portion.

- **`unnamed_group_matcher`** — A compiled regex (via `_lazy_re_compile`) matching the pattern `r'\('`. It matches any opening parenthesis.

### Conditional Role Registration (module-level side effects)

When `docutils_is_available` is `True`, at module import time:
1. The canonical reST role `'cmsreference'` is registered with `docutils.parsers.rst.roles.register_canonical_role`, bound to the function `default_reference_role`.
2. For each `(name, urlbase)` pair in `ROLES`, `create_reference_role(name, urlbase)` is called, which registers a canonical reST role under that name (e.g., `'model'`, `'view'`, etc.).

---

## Code Objects

### `get_view_name(view_func)` → `str`

1. Retrieves the module name from `view_func.__module__`.
2. Gets the view's qualified name via `getattr(view_func, '__qualname__', view_func.__class__.__name__)` — falls back to the class name if `__qualname__` is absent.
3. Returns the concatenation `mod_name + '.' + view_name`.

### `trim_docstring(docstring)` → `str`

1. If `docstring` is falsy or its stripped form is empty, returns `''`.
2. Expands all tabs to spaces via `.expandtabs()`, then splits into lines with `.splitlines()`.
3. Computes the minimum indentation (`indent`) across all non-blank lines (where indentation = line length minus left-stripped length).
4. Constructs a new list: the first line, left-stripped; followed by each subsequent line with `indent` characters removed from its left side and trailing whitespace stripped via `.rstrip()`.
5. Joins the trimmed lines with `'\n'` and strips leading/trailing whitespace from the result. Returns this string.

### `parse_docstring(docstring)` → `(str, str, dict)`

1. Trims the docstring using `trim_docstring(docstring)`.
2. Splits the trimmed docstring on two-or-more consecutive newlines (`re.split(r'\n{2,}', docstring)`), producing a list of parts.
3. The first part is assigned to `title`.
4. If there is only one part: returns `(title, '', {})`.
5. Otherwise, attempts to parse the last part as email-style metadata using `HeaderParser().parsestr(parts[-1])`:
   - **On `HeaderParseError`**: sets `metadata = {}` and `body = "\n\n".join(parts[1:])`.
   - **On success**: converts the parsed result to a dict via `dict(metadata.items())`. If the resulting metadata is non-empty, sets `body = "\n\n".join(parts[1:-1])`; otherwise (metadata is empty), sets `body = "\n\n".join(parts[1:])`.
6. Returns `(title, body, metadata)`.

### `parse_rst(text, default_reference_context, thing_being_parsed=None)` → `mark_safe`-wrapped XHTML fragment (`str`)

1. Builds an `overrides` dict:
   - `'doctitle_xform'`: `True`
   - `'initial_header_level'`: `3`
   - `"default_reference_context"`: the value of `default_reference_context`
   - `"link_base"`: the result of `reverse('django-admindocs-docroot').rstrip('/')`
   - `'raw_enabled'`: `False`
   - `'file_insertion_enabled'`: `False`
2. If `thing_being_parsed` is truthy, wraps it as `'<%s>' % thing_being_parsed`; otherwise leaves it as `None`.
3. Wraps the input `text` in a reST template:
   ```rst
   .. default-role:: cmsreference

   <text>

   .. default-role::
   ```
4. Calls `docutils.core.publish_parts()` with the wrapped source, passing `source_path=thing_being_parsed`, `destination_path=None`, `writer_name='html'`, and `settings_overrides=overrides`.
5. Returns `mark_safe(parts['fragment'])` — a safe-marked XHTML fragment string extracted from the published parts dict.

### `create_reference_role(rolename, urlbase)` → `None` (side effect)

Defines an inner function `_role(name, rawtext, text, lineno, inliner, options=None, content=None)` and registers it as a canonical reST role:

1. If `options` is `None`, sets it to `{}`.
2. Creates a `docutils.nodes.reference` node with:
   - `rawtext`: the raw text from the inliner.
   - `text`: the display text.
   - `refuri`: computed as `(urlbase % (inliner.document.settings.link_base, text.lower()))`.
   - Any additional keyword arguments from `options`.
3. Returns `([node], [])` — a list containing the single reference node and an empty list of messages.
4. Registers `_role` via `docutils.parsers.rst.roles.register_canonical_role(rolename, _role)`.

### `default_reference_role(name, rawtext, text, lineno, inliner, options=None, content=None)` → `(list[docutils.nodes.reference], list)`

1. If `options` is `None`, sets it to `{}`.
2. Retrieves the default reference context from `inliner.document.settings.default_reference_context`.
3. Looks up the URL format string for that context in `ROLES[context]`.
4. Creates a `docutils.nodes.reference` node with:
   - `rawtext`: the raw text from the inliner.
   - `text`: the display text.
   - `refuri`: computed as `(ROLES[context] % (inliner.document.settings.link_base, text.lower()))`.
   - Any additional keyword arguments from `options`.
5. Returns `([node], [])` — a list containing the single reference node and an empty list of messages.

### `replace_named_groups(pattern)` → `str`

Finds named capture groups in a regex pattern string and replaces each entire named group (including its inner content) with just the group name enclosed in angle brackets:

1. Finds all matches of `named_group_matcher` (`r'\(\?P(<\w+>)'`) across `pattern`, collecting tuples `(m.start(0), m.end(0), m.group(1))` — i.e., (start index, end index, captured group name).
2. For each match:
   - Starting after the initial `(?P<name>` prefix, scans forward character by character through `pattern[end:]`, tracking unmatched open brackets (`unmatched_open_brackets`, initialized to 1) and whether the previous character was a backslash (`prev_char`).
   - Increments the bracket counter on unescaped `'('`; decrements it on unescaped `')'`.
   - When the bracket count reaches zero, the full named group span is `pattern[start:end + idx + 1]` (where `idx` is the offset within `pattern[end:]`). Appends `(full_group_pattern, group_name)` to `group_pattern_and_name`.
3. For each `(group_pattern, group_name)` in `group_pattern_and_name`, replaces all occurrences of `group_pattern` in `pattern` with just `group_name`.
4. Returns the modified pattern string.

### `replace_unnamed_groups(pattern)` → `str`

Finds unnamed capture groups (parenthesized subpatterns not preceded by `(?P<`) and replaces each with `<var>`:

1. Finds all start indices of matches of `unnamed_group_matcher` (`r'\('`) across `pattern`.
2. For each start index, scans forward character by character through `pattern[start + 1:]`, tracking unmatched open brackets (initialized to 1) and whether the previous character was a backslash:
   - Increments on unescaped `'('`; decrements on unescaped `')'`.
   - When bracket count reaches zero, records `(start, start + 2 + idx)` as a group span.
3. Filters out nested unnamed groups: iterates through the collected spans in order, keeping only those whose start index is greater than the previous kept end (or has no predecessor). This eliminates inner groups that fall within an outer unnamed group's span.
4. If any kept spans remain:
   - Builds `final_pattern` as a list of strings. Iterates through `(start, end)` pairs:
     - Appends the substring between the previous end and current start (`pattern[prev_end:start]`).
     - Appends `pattern[:start] + '<var>'`.
     - Updates `prev_end = end`.
   - After all groups, appends the remaining tail `pattern[prev_end:]`.
   - Returns `''.join(final_pattern)`.
5. If no kept spans remain (no unnamed groups found), returns the original `pattern` unchanged.

## django/contrib/admindocs/views.py
I now have the complete file (all 413 lines). Here is the natural-language specification:

---

# Module Specification: `django/contrib/admindocs/views.py`

## 1. Module-Level Preamble

### Imports

```python
import inspect
from importlib import import_module
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admindocs import utils
from django.contrib.admindocs.utils import (
    replace_named_groups, replace_unnamed_groups,
)
from django.core.exceptions import ImproperlyConfigured, ViewDoesNotExist
from django.db import models
from django.http import Http404
from django.template.engine import Engine
from django.urls import get_mod_func, get_resolver, get_urlconf
from django.utils.decorators import method_decorator
from django.utils.inspect import (
    func_accepts_kwargs, func_accepts_var_args, get_func_full_args,
    method_has_no_args,
)
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from .utils import get_view_name
```

### Constants & Globals

- **`MODEL_METHODS_EXCLUDE`** — tuple of five string prefixes: `('_', 'add_', 'delete', 'save', 'set_')`. Used to filter out model methods that should not appear in documentation.

---

## 2. Code Objects

### Class `BaseAdminDocsView(TemplateView)`

A base view class for all admin docs views. Inherits from `django.views.generic.TemplateView`.

**`dispatch(self, request, *args, **kwargs)`** — decorated with `@method_decorator(staff_member_required)`. Overrides the parent dispatch to check whether `utils.docutils_is_available` is truthy. If docutils is unavailable, sets `self.template_name = 'admin_doc/missing_docutils.html'` and returns a response rendered with `self.render_to_response(admin.site.each_context(request))`, bypassing normal template rendering. Otherwise delegates to `super().dispatch(request, *args, **kwargs)`.

**`get_context_data(self, **kwargs)`** — merges the parent's context data kwargs with `admin.site.each_context(self.request)` and returns the result. This provides admin site navigation context to every subclass view.

---

### Class `BookmarkletsView(BaseAdminDocsView)`

- **`template_name`** = `'admin_doc/bookmarklets.html'`.
- No custom methods; inherits all behavior from `BaseAdminDocsView`. Renders a template providing bookmarklet helpers for generating admin docs.

---

### Class `TemplateTagIndexView(BaseAdminDocsView)`

- **`template_name`** = `'admin_doc/template_tag_index.html'`.

**`get_context_data(self, **kwargs)`** — builds a list of tag documentation entries:
1. Initializes an empty `tags` list.
2. Attempts to get the default template engine via `Engine.get_default()`. If `ImproperlyConfigured` is raised (non-trivial TEMPLATES settings), skips processing and returns an empty tags list.
3. Otherwise, collects app libraries from `engine.template_libraries.items()` sorted by module name, and builtin libraries as `[('', lib) for lib in engine.template_builtins]`. Iterates over the concatenation of builtin_libs + app_libs.
4. For each `(module_name, library)` pair, iterates over `library.tags.items()`, extracting `(tag_name, tag_func)`:
   - Calls `utils.parse_docstring(tag_func.__doc__)` to extract `(title, body, metadata)`.
   - If title is truthy, parses it as reStructuredText via `utils.parse_rst(title, 'tag', _('tag:') + tag_name)`; otherwise leaves it falsy.
   - Same for body: `utils.parse_rst(body, 'tag', _('tag:') + tag_name)`.
   - For each key in metadata, parses its value as RST with the same context prefix.
   - Extracts the library name from `module_name.split('.')[-1]`.
   - Appends a dict: `{'name': tag_name, 'title': title, 'body': body, 'meta': metadata, 'library': tag_library}`.
5. Returns `super().get_context_data(**{**kwargs, 'tags': tags})`.

---

### Class `TemplateFilterIndexView(BaseAdminDocsView)`

- **`template_name`** = `'admin_doc/template_filter_index.html'`.

**`get_context_data(self, **kwargs)`** — structurally identical to `TemplateTagIndexView.get_context_data`, but iterates over `library.filters.items()` instead of `.tags.items()`, and uses the RST context category `'filter'` with prefix `_('filter:') + filter_name`. Produces a list of dicts: `{'name': filter_name, 'title': title, 'body': body, 'meta': metadata, 'library': tag_library}`. Returns via `super().get_context_data(**{**kwargs, 'filters': filters})`.

---

### Class `ViewIndexView(BaseAdminDocsView)`

- **`template_name`** = `'admin_doc/view_index.html'`.

**`get_context_data(self, **kwargs)`** — builds a list of all registered URL patterns:
1. Initializes an empty `views` list.
2. Imports the root URLconf module via `import_module(settings.ROOT_URLCONF)`.
3. Calls `extract_views_from_urlpatterns(urlconf.urlpatterns)` to get a flat list of `(func, regex, namespace, name)` tuples.
4. For each tuple, appends a dict:
   - `'full_name'`: result of `get_view_name(func)`.
   - `'url'`: result of `simplify_regex(regex)`, which humanizes the raw regex pattern.
   - `'url_name'`: `':'.join((namespace or []) + (name and [name] or []))` — joins namespace components and view name with colons.
   - `'namespace'`: `':'.join(namespace or [])`.
   - `'name'`: the raw view name string.
5. Returns `super().get_context_data(**{**kwargs, 'views': views})`.

---

### Class `ViewDetailView(BaseAdminDocsView)`

- **`template_name`** = `'admin_doc/view_detail.html'`.

**`_get_view_func(view)`** — static method that resolves a view identifier string to its actual callable:
1. Gets the current URLconf via `get_urlconf()`.
2. Checks if `get_resolver(urlconf)._is_callback(view)` is true (i.e., `view` refers to a callback-style URL pattern).
3. Calls `get_mod_func(view)` to split `'mymodule.views.myview'` into `(mod, func)`.
4. Attempts `getattr(import_module(mod), func)` to import and retrieve the callable.
5. If `ImportError` is raised (e.g., view contains a class name like `'mymodule.views.ViewContainer.my_view'`), re-parses: calls `get_mod_func(mod)` to split module from class, then does `getattr(getattr(import_module(mod), klass), func)`.
6. Returns the resolved callable, or `None` if `_is_callback` is false.

**`get_context_data(self, **kwargs)`**:
1. Extracts `view = self.kwargs['view']`.
2. Calls `self._get_view_func(view)` to resolve the view function. If it returns `None`, raises `Http404`.
3. Parses the docstring of the resolved view via `utils.parse_docstring(view_func.__doc__)` → `(title, body, metadata)`.
4. Parses title and body as RST with category `'view'` and prefix `_('view:') + view`.
5. For each key in metadata, parses its value as RST with the same context.
6. Returns `super().get_context_data(**{**kwargs, 'name': view, 'summary': title, 'body': body, 'meta': metadata})`.

---

### Class `ModelIndexView(BaseAdminDocsView)`

- **`template_name`** = `'admin_doc/model_index.html'`.

**`get_context_data(self, **kwargs)`** — retrieves all registered Django models via `apps.get_models()`, extracts each model's `_meta` object (a `Options` instance), and passes the list as `'models'` to the parent context. Returns `super().get_context_data(**{**kwargs, 'models': m_list})`.

---

### Class `ModelDetailView(BaseAdminDocsView)`

- **`template_name`** = `'admin_doc/model_detail.html'`.

**`get_context_data(self, **kwargs)`** — builds a comprehensive documentation page for a single model:
1. Extracts `model_name = self.kwargs['model_name']`.
2. Looks up the app config via `apps.get_app_config(self.kwargs['app_label'])`; raises `Http404(_("App %(app_label)r not found") % self.kwargs)` on `LookupError`.
3. Retrieves the model class via `app_config.get_model(model_name)`; raises `Http404(_("Model %(model_name)r not found in app %(app_label)r") % self.kwargs)` on `LookupError`.
4. Gets `opts = model._meta` (the model's Options metadata).
5. Parses the model's docstring via `utils.parse_docstring(model.__doc__)` → `(title, body, metadata)`, then parses title and body as RST with category `'model'` and prefix `_('model:') + model_name`.
6. **Gathers fields** (iterates over `opts.fields`):
   - For each field: if it is a `models.ForeignKey`, sets `data_type = field.remote_field.model.__name__`, constructs verbose text as `_("the related \`%(app_label)s.%(data_type)s\` object") % {...}`, and parses it as RST with category `'model'`. Otherwise, calls `get_readable_field_data_type(field)` for the data type and uses `field.verbose_name` as verbose.
   - Appends each field dict: `{'name': field.name, 'data_type': data_type, 'verbose': verbose or '', 'help_text': field.help_text}`.
7. **Gathers many-to-many fields** (iterates over `opts.many_to_many`):
   - For each M2M field, creates two entries:
     - `'name'`: `"%s.all" % field.name`, `'data_type'`: `'List'`, verbose = RST-parsed `_("all %(verbose)s")`.
     - `'name'`: `"%s.count" % field.name`, `'data_type'`: `'Integer'`, verbose = RST-parsed `_("number of %(verbose)s")`.
   - Where verbose is constructed as `_("related \`%(app_label)s.%(object_name)s\` objects") % {...}` and parsed with category `'model'`.
8. **Gathers methods** (iterates over `model.__dict__.items()`):
   - For each `(func_name, func)`: if `inspect.isfunction(func)` or `isinstance(func, property)`, checks whether `func_name` starts with any string in `MODEL_METHODS_EXCLUDE`. If so, skips via `StopIteration`/`continue`.
   - Parses the docstring: `verbose = utils.parse_rst(utils.trim_docstring(verbose), 'model', _('model:') + opts.model_name)` if truthy.
   - If it is a `property`, appends as a field dict (same structure as regular fields, with `'data_type'` from `get_return_data_type(func_name)`).
   - Else if `method_has_no_args(func) and not func_accepts_kwargs(func) and not func_accepts_var_args(func)`, appends as a field dict.
   - Otherwise, calls `get_func_full_args(func)` to get argument tuples `(arg_el[0], arg_el[1:])` where the first element is the name and rest are defaults. Formats each as `'='.join([name, *map(repr, defaults)])`, joins with `', '`. Appends a method dict: `{'name': func_name, 'arguments': print_arguments, 'verbose': verbose or ''}`.
9. **Gathers related objects** (iterates over `opts.related_objects`):
   - For each relation, constructs verbose as `_("related \`%(app_label)s.%(object_name)s\` objects") % {...}`, gets the accessor name via `rel.get_accessor_name()`, and appends two field dicts: `'name': "%s.all" % accessor` with data type `'List'`, and `'name': "%s.count" % accessor` with data type `'Integer'`. Both verbose values are RST-parsed.
10. Returns `super().get_context_data(**{**kwargs, 'name': '%s.%s' % (opts.app_label, opts.object_name), 'summary': title, 'description': body, 'fields': fields, 'methods': methods})`.

---

### Class `TemplateDetailView(BaseAdminDocsView)`

- **`template_name`** = `'admin_doc/template_detail.html'`.

**`get_context_data(self, **kwargs)`**:
1. Extracts `template = self.kwargs['template']`.
2. Initializes an empty `templates` list.
3. Attempts to get the default engine via `Engine.get_default()`. If `ImproperlyConfigured`, skips (non-trivial TEMPLATES settings unsupported).
4. Otherwise, iterates over `enumerate(default_engine.dirs)` — each directory in the template search path:
   - Constructs `template_file = Path(directory) / template`.
   - Reads file contents via `template_file.read_text()` if it exists; otherwise sets `template_contents = ''`.
   - Appends a dict: `{'file': template_file, 'exists': template_file.exists(), 'contents': template_contents, 'order': index}`.
5. Returns `super().get_context_data(**{**kwargs, 'name': template, 'templates': templates})`.

---

### Function `get_return_data_type(func_name)`

Given a function name string, returns an inferred return type:
- If the name starts with `'get_'` and ends with `'_list'`, returns `'List'`.
- If it starts with `'get_'` and ends with `'_count'`, returns `'Integer'`.
- Otherwise returns `''`.

---

### Function `get_readable_field_data_type(field)`

Given a Django model field instance, returns its human-readable type description by interpolating the format string `field.description` with `field.__dict__` via `%` formatting. This produces a readable type name (e.g., "Boolean", "Date") from the field's internal description template.

---

### Function `extract_views_from_urlpatterns(urlpatterns, base='', namespace=None)`

Recursively extracts all view functions from URL patterns:
1. Initializes an empty `views` list.
2. For each pattern `p` in `urlpatterns`:
   - If `p` has a `url_patterns` attribute (i.e., it is a nested URLconf): recursively calls itself with the concatenated base path (`base + str(p.pattern)`) and extended namespace `(namespace or []) + (p.namespace and [p.namespace] or [])`. Results are extended into `views`.
   - Else if `p` has a `callback` attribute: appends `(p.callback, base + str(p.pattern), namespace, p.name)` to `views`. If this raises `ViewDoesNotExist`, skips the pattern.
   - Else: raises `TypeError(_("%s does not appear to be a urlpattern object") % p)`.
3. Returns the flat list of tuples `(view_func, regex_string, namespace_list, view_name)`.

---

### Function `simplify_regex(pattern)`

Humanizes a URL pattern regex string into a readable path:
1. Calls `replace_named_groups(pattern)` to convert named capture groups like `(?P<sport_slug>\w+)` into `<sport_slug>`.
2. Calls `replace_unnamed_groups(pattern)` to convert unnamed capture groups like `(\d+)` into `<...>`.
3. Strips leading `^`, trailing `$`, and all `?` characters.
4. If the result does not start with `/`, prepends one.
5. Returns the cleaned path string (e.g., `"^(?P<sport_slug>\w+)/athletes/(?P<athlete_slug>\w+)/$"` → `"/<sport_slug>/athletes/<athlete_slug>/"`).