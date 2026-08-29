## sphinx/application.py
Now I have read the entire file (1206 lines). Here is the complete natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import os, pickle, platform, sys, warnings
from collections import deque
from io import StringIO
from os import path
from typing import Any, Callable, Dict, IO, List, Tuple, Union
from docutils import nodes
from docutils.nodes import Element, TextElement
from docutils.parsers.rst import Directive, roles
from docutils.transforms import Transform
from pygments.lexer import Lexer
import sphinx
from sphinx import package_dir, locale
from sphinx.config import Config
from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.domains import Domain, Index
from sphinx.environment import BuildEnvironment
from sphinx.environment.collectors import EnvironmentCollector
from sphinx.errors import ApplicationError, ConfigError, VersionRequirementError
from sphinx.events import EventManager
from sphinx.extension import Extension
from sphinx.highlighting import lexer_classes, lexers
from sphinx.locale import __
from sphinx.project import Project
from sphinx.registry import SphinxComponentRegistry
from sphinx.roles import XRefRole
from sphinx.theming import Theme
from sphinx.util import docutils
from sphinx.util import logging
from sphinx.util import progress_message
from sphinx.util.build_phase import BuildPhase
from sphinx.util.console import bold  # type: ignore
from sphinx.util.i18n import CatalogRepository
from sphinx.util.logging import prefixed_warnings
from sphinx.util.osutil import abspath, ensuredir, relpath
from sphinx.util.tags import Tags
from sphinx.util.typing import RoleFunction, TitleGetter
# TYPE-ONLY (guarded by `if False:`): from docutils.nodes import Node; from typing import Type; from sphinx.builders import Builder
```

### Constants & Globals

* **`builtin_extensions`** — A tuple of 56 string module paths for built-in extensions. The entries are: `'sphinx.addnodes'`, `'sphinx.builders.changes'`, `'sphinx.builders.epub3'`, `'sphinx.builders.dirhtml'`, `'sphinx.builders.dummy'`, `'sphinx.builders.gettext'`, `'sphinx.builders.html'`, `'sphinx.builders.latex'`, `'sphinx.builders.linkcheck'`, `'sphinx.builders.manpage'`, `'sphinx.builders.singlehtml'`, `'sphinx.builders.texinfo'`, `'sphinx.builders.text'`, `'sphinx.builders.xml'`, `'sphinx.config'`, `'sphinx.domains.c'`, `'sphinx.domains.changeset'`, `'sphinx.domains.citation'`, `'sphinx.domains.cpp'`, `'sphinx.domains.index'`, `'sphinx.domains.javascript'`, `'sphinx.domains.math'`, `'sphinx.domains.python'`, `'sphinx.domains.rst'`, `'sphinx.domains.std'`, `'sphinx.directives'`, `'sphinx.directives.code'`, `'sphinx.directives.other'`, `'sphinx.directives.patches'`, `'sphinx.extension'`, `'sphinx.parsers'`, `'sphinx.registry'`, `'sphinx.roles'`, `'sphinx.transforms'`, `'sphinx.transforms.compact_bullet_list'`, `'sphinx.transforms.i18n'`, `'sphinx.transforms.references'`, `'sphinx.transforms.post_transforms'`, `'sphinx.transforms.post_transforms.code'`, `'sphinx.transforms.post_transforms.images'`, `'sphinx.util.compat'`, `'sphinx.versioning'`, `'sphinx.environment.collectors.dependencies'`, `'sphinx.environment.collectors.asset'`, `'sphinx.environment.collectors.metadata'`, `'sphinx.environment.collectors.title'`, `'sphinx.environment.collectors.toctree'`, `'sphinxcontrib.applehelp'`, `'sphinxcontrib.devhelp'`, `'sphinxcontrib.htmlhelp'`, `'sphinxcontrib.serializinghtml'`, `'sphinxcontrib.qthelp'`, `'alabaster'`.

* **`ENV_PICKLE_FILENAME`** — The string `'environment.pickle'`.

* **`logger`** — A module-level logger obtained via `logging.getLogger(__name__)`.

---

## Code Objects

### Class: `Sphinx`

The main application class and extensibility interface. Inherits from no base classes (implicitly `object`).

#### Attributes (initialized in `__init__`)

| Attribute | Type | Description |
|-----------|------|-------------|
| `phase` | `BuildPhase` | Set to `BuildPhase.INITIALIZATION` at construction |
| `verbosity` | `int` | Verbosity level from constructor |
| `extensions` | `Dict[str, Extension]` | Loaded extension registry (empty dict) |
| `builder` | `Builder \| None` | The active builder instance |
| `env` | `BuildEnvironment \| None` | The build environment |
| `project` | `Project \| None` | The project object |
| `registry` | `SphinxComponentRegistry` | Component registry (always instantiated) |
| `html_themes` | `Dict[str, str]` | HTML theme name → path mapping (empty dict) |
| `srcdir` | `str` | Absolute source directory path |
| `outdir` | `str` | Absolute output directory path |
| `doctreedir` | `str` | Absolute doctree storage directory path |
| `confdir` | `str \| None` | Absolute config directory path (or `None`) |
| `parallel` | `int` | Parallelism count from constructor |
| `_status` | `IO` | Status output stream (`StringIO` if `None` passed) |
| `quiet` | `bool` | `True` if status was `None`, else `False` |
| `_warning` | `IO` | Warning output stream |
| `_warncount` | `int` | Counter of warnings emitted (starts at 0) |
| `keep_going` | `bool` | Whether to continue despite warnings |
| `warningiserror` | `bool` | Whether warnings are treated as errors |
| `events` | `EventManager` | Event manager bound to this app instance |
| `messagelog` | `deque[str]` | Last 10 messages for traceback (maxlen=10) |
| `statuscode` | `int` | Exit status code (starts at 0) |
| `tags` | `Tags` | Tags object from constructor list |
| `config` | `Config` | Configuration object |
| `translator` | — | Translation translator (set by `_init_i18n`) |
| `has_translation` | — | Whether translation is available (set by `_init_i18n`) |

#### Constructor: `__init__(self, srcdir: str, confdir: str, outdir: str, doctreedir: str, buildername: str, confoverrides: Dict = None, status: IO = sys.stdout, warning: IO = sys.stderr, freshenv: bool = False, warningiserror: bool = False, tags: List[str] = None, verbosity: int = 0, parallel: int = 0, keep_going: bool = False) -> None`

1. Sets `self.phase = BuildPhase.INITIALIZATION`, stores `verbosity`.
2. Initializes `extensions = {}`, `builder = None`, `env = None`, `project = None`, `registry = SphinxComponentRegistry()`, `html_themes = {}`.
3. Converts `srcdir`, `outdir`, `doctreedir` to absolute paths via `abspath()`. If `confdir` is non-empty, converts it to an absolute path and validates that `conf.py` exists inside it; raises `ApplicationError` if not found.
4. Validates: `srcdir` must be a directory (raises `ApplicationError` otherwise); `outdir` must not exist as a non-directory file (raises `ApplicationError`). Raises `ApplicationError` if `srcdir == outdir`.
5. Stores `parallel`, sets `_status`/`quiet` based on whether `status is None` (uses `StringIO()`), sets `_warning` from the `warning` parameter, initializes `_warncount = 0`. Sets `keep_going = warningiserror and keep_going`; if `keep_going` is true, forces `warningiserror = False`, else uses the passed value. Calls `logging.setup(self, self._status, self._warning)`.
6. Creates `self.events = EventManager(self)`. Initializes `messagelog = deque(maxlen=10)`. Logs a startup message with Sphinx version. If macOS + Python > 3.8 + parallel > 1, logs a security warning about parallel mode being disabled. Sets `statuscode = 0`.
7. Creates `self.tags = Tags(tags)`. If `confdir is None`, creates `Config({}, confoverrides or {})`; otherwise calls `Config.read(self.confdir, confoverrides or {}, self.tags)`. Calls `self.config.pre_init_values()`.
8. Calls `_init_i18n()` to set up translation infrastructure.
9. Checks `self.config.needs_sphinx` against `sphinx.__display_version__`; raises `VersionRequirementError` if the running version is too old. If `confdir is None`, sets it to `srcdir`.
10. Loads all built-in extensions by iterating `builtin_extensions` and calling `setup_extension()` for each. Then loads user extensions from `self.config.extensions` via `setup_extension()`.
11. Calls `preload_builder(buildername)`. Creates the output directory if it doesn't exist (via `ensuredir`). If `self.config.setup` is set, calls it as a callable with `self` as argument; raises `ConfigError` if it's not callable.
12. Calls `self.config.init_values()`, emits `'config-inited'` event. Creates `self.project = Project(self.srcdir, self.config.source_suffix)`. Creates the builder via `create_builder(buildername)`. Initializes environment via `_init_env(freshenv)`. Initializes builder via `_init_builder()`.

#### Method: `_init_i18n(self) -> None`

If `self.config.language is None`, calls `locale.init([], None)` to set `self.translator, has_translation`. Otherwise, logs a translation loading message. Creates a `CatalogRepository` from `srcdir`, `config.locale_dirs`, `config.language`, and `config.source_encoding`. For each catalog where `domain == 'sphinx'` and the catalog is outdated, calls `catalog.write_mo(language)`. Builds `locale_dirs = [None, path.join(package_dir, 'locale')] + list(repo.locale_dirs)` and calls `locale.init(locale_dirs, config.language)`. Logs `'done'` if translation is available or language is `'en'`; otherwise logs `'not available for built-in messages'`.

#### Method: `_init_env(self, freshenv: bool) -> None`

Constructs the pickle filename as `path.join(self.doctreedir, ENV_PICKLE_FILENAME)`. If `freshenv` is true or the file does not exist, creates a new `BuildEnvironment()`, calls `self.env.setup(self)`, then `self.env.find_files(self.config, self.builder)`. Otherwise, attempts to load from pickle via `pickle.load()` inside a progress message context. On any exception, logs `'failed: <err>'` and recursively calls `_init_env(freshenv=True)`.

#### Method: `preload_builder(self, name: str) -> None`

Delegates to `self.registry.preload_builder(self, name)`.

#### Method: `create_builder(self, name: str) -> "Builder"`

If `name is None`, logs `'No builder selected, using default: html'` and sets `name = 'html'`. Returns `self.registry.create_builder(self, name)`.

#### Method: `_init_builder(self) -> None`

Calls `self.builder.set_environment(self.env)`, then `self.builder.init()`, then emits the `'builder-inited'` event.

#### Method: `build(self, force_all: bool = False, filenames: List[str] = None) -> None`

Sets `self.phase = BuildPhase.READING`. Wraps all logic in a try/except/else block:
- If `force_all`: calls `self.builder.compile_all_catalogs()` then `self.builder.build_all()`.
- Else if `filenames` is truthy: calls `self.builder.compile_specific_catalogs(filenames)` then `self.builder.build_specific(filenames)`.
- Else: calls `self.builder.compile_update_catalogs()` then `self.builder.build_update()`.

After building, if `_warncount > 0` and `keep_going`, sets `statuscode = 1`. Constructs a status message (`'succeeded'` or `'finished with problems'`) and a formatted log line including the warning count (singular/plural-aware) and whether warnings are treated as errors. If `statuscode == 0` and `self.builder.epilog` exists, logs an epilogue with `outdir` and `project`.

On exception: deletes the environment pickle file if it exists, emits `'build-finished'` event with the error object, then re-raises. On success (else branch): emits `'build-finished'` event with `None`. Finally calls `self.builder.cleanup()`.

#### Method: `setup_extension(self, extname: str) -> None`

Logs debug message `[app] setting up extension: <extname>`, delegates to `self.registry.load_extension(self, extname)`. No-op if called twice (handled by registry).

#### Method: `require_sphinx(self, version: str) -> None`

Compares `version` against the first 3 characters of `sphinx.__display_version__`; raises `VersionRequirementError(version)` if the running version is older.

#### Method: `connect(self, event: str, callback: Callable, priority: int = 500) -> int`

Delegates to `self.events.connect(event, callback, priority)`, logs a debug message with event name, priority, callback repr, and listener ID. Returns the listener ID integer.

#### Method: `disconnect(self, listener_id: int) -> None`

Logs a debug message with the listener ID, delegates to `self.events.disconnect(listener_id)`.

#### Method: `emit(self, event: str, *args: Any, allowed_exceptions: Tuple["Type[Exception]", ...] = ()) -> List`

Delegates to `self.events.emit(event, *args, allowed_exceptions=allowed_exceptions)`, returns the list of callback return values.

#### Method: `emit_firstresult(self, event: str, *args: Any, allowed_exceptions: Tuple["Type[Exception]", ...] = ()) -> Any`

Delegates to `self.events.emit_firstresult(event, *args, allowed_exceptions=allowed_exceptions)`, returns the first non-None callback result.

#### Method: `add_builder(self, builder: "Type[Builder]", override: bool = False) -> None`

Delegates to `self.registry.add_builder(builder, override=override)`.

#### Method: `add_config_value(self, name: str, default: Any, rebuild: Union[bool, str], types: Any = ()) -> None`

Logs debug message. If `rebuild` is a boolean (`False` or `True`), converts it to `'env'` for True and `''` for False. Delegates to `self.config.add(name, default, rebuild, types)`.

#### Method: `add_event(self, name: str) -> None`

Logs debug message, delegates to `self.events.add(name)`.

#### Method: `set_translator(self, name: str, translator_class: "Type[nodes.NodeVisitor]", override: bool = False) -> None`

Delegates to `self.registry.add_translator(name, translator_class, override=override)`.

#### Method: `add_node(self, node: "Type[Element]", override: bool = False, **kwargs: Tuple[Callable, Callable]) -> None`

Logs debug message. If not overriding and the node is already registered (checked via `docutils.is_node_registered(node)`), logs a warning that its visitors will be overridden. Calls `docutils.register_node(node)`, then delegates to `self.registry.add_translation_handlers(node, **kwargs)`. Keyword arguments map translator names (`'html'`, `'latex'`, `'text'`, `'man'`, `'texinfo'`) to 2-tuples of `(visit, depart)` methods where `depart` can be `None` (indicating `SkipNode`).

#### Method: `add_enumerable_node(self, node: "Type[Element]", figtype: str, title_getter: TitleGetter = None, override: bool = False, **kwargs: Tuple[Callable, Callable]) -> None`

Delegates to `self.registry.add_enumerable_node(node, figtype, title_getter, override=override)`, then calls `self.add_node(node, override=override, **kwargs)`.

#### Method: `add_directive(self, name: str, cls: "Type[Directive]", override: bool = False) -> None`

Logs debug message. If not overriding and the directive is already registered (via `docutils.is_directive_registered(name)`), logs a warning. Calls `docutils.register_directive(name, cls)`.

#### Method: `add_role(self, name: str, role: Any, override: bool = False) -> None`

Logs debug message. If not overriding and the role is already registered (via `docutils.is_role_registered(name)`), logs a warning. Calls `docutils.register_role(name, role)`.

#### Method: `add_generic_role(self, name: str, nodeclass: Any, override: bool = False) -> None`

Logs debug message. If not overriding and the role is already registered, logs a warning. Creates `role = roles.GenericRole(name, nodeclass)` and calls `docutils.register_role(name, role)`. Does NOT use `roles.register_generic_role` (avoids canonical registration).

#### Method: `add_domain(self, domain: "Type[Domain]", override: bool = False) -> None`

Delegates to `self.registry.add_domain(domain, override=override)`.

#### Method: `add_directive_to_domain(self, domain: str, name: str, cls: "Type[Directive]", override: bool = False) -> None`

Delegates to `self.registry.add_directive_to_domain(domain, name, cls, override=override)`.

#### Method: `add_role_to_domain(self, domain: str, name: str, role: Union[RoleFunction, XRefRole], override: bool = False) -> None`

Delegates to `self.registry.add_role_to_domain(domain, name, role, override=override)`.

#### Method: `add_index_to_domain(self, domain: str, index: "Type[Index]", override: bool = False) -> None`

Delegates to `self.registry.add_index_to_domain(domain, index)` (no override parameter passed).

#### Method: `add_object_type(self, directivename: str, rolename: str, indextemplate: str = '', parse_node: Callable = None, ref_nodeclass: "Type[TextElement]" = None, objname: str = '', doc_field_types: List = [], override: bool = False) -> None`

Delegates to `self.registry.add_object_type(directivename, rolename, indextemplate, parse_node, ref_nodeclass, objname, doc_field_types, override=override)`. Creates a directive and role for cross-referencing object types.

#### Method: `add_crossref_type(self, directivename: str, rolename: str, indextemplate: str = '', ref_nodeclass: "Type[TextElement]" = None, objname: str = '', override: bool = False) -> None`

Delegates to `self.registry.add_crossref_type(directivename, rolename, indextemplate, ref_nodeclass, objname, override=override)`. Similar to `add_object_type` but the generated directive is empty (produces no output).

#### Method: `add_transform(self, transform: "Type[Transform]") -> None`

Delegates to `self.registry.add_transform(transform)`. Registers a Docutils transform applied after parsing.

#### Method: `add_post_transform(self, transform: "Type[Transform]") -> None`

Delegates to `self.registry.add_post_transform(transform)`. Registers a Docutils transform applied before writing.

#### Method: `add_javascript(self, filename: str, **kwargs: str) -> None` (DEPRECATED)

Emits `RemovedInSphinx40Warning`, then delegates to `self.add_js_file(filename, **kwargs)`.

#### Method: `add_js_file(self, filename: str, **kwargs: str) -> None`

Delegates to `self.registry.add_js_file(filename, **kwargs)`. If the builder has an `add_js_file` attribute, also calls `self.builder.add_js_file(filename, **kwargs)`.

#### Method: `add_css_file(self, filename: str, **kwargs: str) -> None`

Logs debug message. Delegates to `self.registry.add_css_files(filename, **kwargs)`. If the builder has an `add_css_file` attribute, also calls `self.builder.add_css_file(filename, **kwargs)`.

#### Method: `add_stylesheet(self, filename: str, alternate: bool = False, title: str = None) -> None` (DEPRECATED)

Emits `RemovedInSphinx40Warning`. Builds an attributes dict: sets `'rel'` to `'alternate stylesheet'` if `alternate` is true, else `'stylesheet'`; adds `'title'` key if `title` is truthy. Delegates to `self.add_css_file(filename, **attributes)`.

#### Method: `add_latex_package(self, packagename: str, options: str = None, after_hyperref: bool = False) -> None`

Delegates to `self.registry.add_latex_package(packagename, options, after_hyperref)`.

#### Method: `add_lexer(self, alias: str, lexer: Union[Lexer, "Type[Lexer]"]) -> None`

Logs debug message. If `lexer` is an instance of `Lexer`, emits `RemovedInSphinx40Warning` and sets `lexers[alias] = lexer`. Otherwise (if it's a class), sets `lexer_classes[alias] = lexer`.

#### Method: `add_autodocumenter(self, cls: Any, override: bool = False) -> None`

Logs debug message. Imports `AutodocDirective` from `sphinx.ext.autodoc.directive`, calls `self.registry.add_documenter(cls.objtype, cls)`, then calls `self.add_directive('auto' + cls.objtype, AutodocDirective, override=override)`.

#### Method: `add_autodoc_attrgetter(self, typ: "Type", getter: Callable[[Any, str, Any], Any]) -> None`

Logs debug message. Delegates to `self.registry.add_autodoc_attrgetter(typ, getter)`.

#### Method: `add_search_language(self, cls: Any) -> None`

Logs debug message. Imports `languages` and `SearchLanguage` from `sphinx.search`, asserts `issubclass(cls, SearchLanguage)`, sets `languages[cls.lang] = cls`.

#### Method: `add_source_suffix(self, suffix: str, filetype: str, override: bool = False) -> None`

Delegates to `self.registry.add_source_suffix(suffix, filetype, override=override)`.

#### Method: `add_source_parser(self, *args: Any, **kwargs: Any) -> None`

Delegates to `self.registry.add_source_parser(*args, **kwargs)`.

#### Method: `add_env_collector(self, collector: "Type[EnvironmentCollector]") -> None`

Logs debug message. Instantiates the collector class and calls `.enable(self)` on it.

#### Method: `add_html_theme(self, name: str, theme_path: str) -> None`

Logs debug message. Sets `self.html_themes[name] = theme_path`.

#### Method: `add_html_math_renderer(self, name: str, inline_renderers: Tuple[Callable, Callable] = None, block_renderers: Tuple[Callable, Callable] = None) -> None`

Delegates to `self.registry.add_html_math_renderer(name, inline_renderers, block_renderers)`.

#### Method: `add_message_catalog(self, catalog: str, locale_dir: str) -> None`

Calls `locale.init([locale_dir], self.config.language, catalog)` then `locale.init_console(locale_dir, catalog)`.

#### Method: `is_parallel_allowed(self, typ: str) -> bool`

Validates that `typ` is `'read'` or `'write'`; raises `ValueError` otherwise. For each extension in `self.extensions.values()`, checks the attribute `parallel_read_safe` (for `'read'`) or `parallel_write_safe` (for `'write'`). If any extension has the attribute as `None`, logs a warning asking the author to declare it and logs that serial processing is being used, then returns `False`. If any extension explicitly sets the attribute to `False`, logs a warning about not being safe for parallel processing and logs that serial processing is being used, then returns `False`. Only if all extensions declare the attribute as truthy does the method return `True`.

---

### Class: `TemplateBridge`

An abstract base class defining the interface for template rendering bridges. No inheritance (implicitly `object`).

#### Method: `init(self, builder: "Builder", theme: Theme = None, dirs: List[str] = None) -> None`

Abstract method. Called by a builder to initialize the template system with the builder object, an optional `Theme`, and/or a list of directory paths. Always raises `NotImplementedError('must be implemented in subclasses')`.

#### Method: `newest_template_mtime(self) -> float`

Returns the mtime (as a float) of the newest template file that was changed. The default implementation returns `0`. Concrete subclasses override this to track template modification times for cache invalidation.

#### Method: `render(self, template: str, context: Dict) -> None`

Abstract method. Renders a template given as a filename string with a specified context dictionary. Always raises `NotImplementedError('must be implemented in subclasses')`.

#### Method: `render_string(self, template: str, context: Dict) -> str`

Abstract method. Renders a template given as an inline string (not a filename) with a specified context dictionary. Returns the rendered string. Always raises `NotImplementedError('must be implemented in subclasses')`.

## sphinx/locale/__init__.py
Here is the complete natural-language specification of `sphinx/locale/__init__.py`:

---

## Module-Level Preamble

### Imports

```python
import gettext
import locale
from collections import UserString, defaultdict
from gettext import NullTranslations
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
```

### Constants & Globals

- **`translators`** — `defaultdict(NullTranslations)`, typed as `Dict[Tuple[str, str], NullTranslations]`. Maps `(namespace, catalog)` key pairs to `NullTranslations` translator objects. The default factory is `NullTranslations`, so any missing key automatically yields a fresh `NullTranslations()` instance.

- **`_`** — A translation function returned by `get_translation('sphinx')`. It follows the Sphinx `:confval:`language`` setting. Used for documentation messages (menu, labels, themes).

- **`__`** — A translation function returned by `get_translation('sphinx', 'console')`. It follows system locale settings (`LC_ALL`, `LC_MESSAGES`, etc.). Used for console messages.

- **`admonitionlabels`** — A dict mapping 10 admonition type strings to their English display labels, each value produced via `_()` (lazy translation):
  - `'attention'` → `_('Attention')`
  - `'caution'` → `_('Caution')`
  - `'danger'` → `_('Danger')`
  - `'error'` → `_('Error')`
  - `'hint'` → `_('Hint')`
  - `'important'` → `_('Important')`
  - `'note'` → `_('Note')`
  - `'seealso'` → `_('See also')`
  - `'tip'` → `_('Tip')`
  - `'warning'` → `_('Warning')`

- **`versionlabels`** — An empty dict, typed as `Dict[str, str]`. Will be overridden later by `sphinx.directives.other`.

- **`pairindextypes`** — An empty dict, typed as `Dict[str, str]`. Will be overridden later by `sphinx.domains.python`.

---

## Code Objects

### Class `_TranslationProxy(UserString)`

A lazy string proxy for gettext translations. Inherits from `collections.UserString`. Used to defer translation resolution until the string is actually needed (e.g., for sorting).

**`__slots__`**: `('_func', '_args')` — stores the callable and its arguments.

#### `__new__(cls, func: Callable, *args: str) -> object`
- If called with no `args` (i.e., only a plain string is passed as `func`), returns `str(func)` directly — a real string, not a proxy.
- Otherwise, creates and returns a new instance via `object.__new__(cls)`.

#### `__getnewargs__(self) -> Tuple[str]`
Returns `(self._func,) + self._args`, used for pickle reconstruction.

#### `__init__(self, func: Callable, *args: str) -> None`
Stores the callable and its positional arguments as instance attributes `self._func` and `self._args`.

#### `data (property) -> str`
Returns `self._func(*self._args)` — resolves the lazy translation by calling the stored function with its stored args.

#### `encode(self, encoding: str = None, errors: str = None) -> bytes`
Overrides `UserString.encode`. Delegates to `self.data.encode()`:
- If both `encoding` and `errors` are provided → calls `self.data.encode(encoding, errors)`.
- If only `encoding` is provided → calls `self.data.encode(encoding)`.
- If neither is provided → calls `self.data.encode()` (default UTF-8).

#### `__dir__(self) -> List[str]`
Returns `dir(str)` — exposes all standard string methods on the proxy.

#### `__str__(self) -> str`
Returns `str(self.data)` — resolves and returns the underlying string.

#### `__add__(self, other: str) -> str`
Returns `self.data + other`.

#### `__radd__(self, other: str) -> str`
Returns `other + self.data`.

#### `__mod__(self, other: str) -> str`
Returns `self.data % other` (string formatting).

#### `__rmod__(self, other: str) -> str`
Returns `other % self.data`.

#### `__mul__(self, other: Any) -> str`
Returns `self.data * other`.

#### `__rmul__(self, other: Any) -> str`
Returns `other * self.data`.

#### `__getattr__(self, name: str) -> Any`
- If `name == '__members__'`, returns `self.__dir__()`.
- Otherwise, delegates to `getattr(self.data, name)` — forwarding any attribute access on the resolved string.

#### `__getstate__(self) -> Tuple[Callable, Tuple[str, ...]]`
Returns `(self._func, self._args)` for pickle serialization.

#### `__setstate__(self, tup: Tuple[Callable, Tuple[str]]) -> None`
Restores `self._func = tup[0]` and `self._args = tup[1]`.

#### `__copy__(self) -> "_TranslationProxy"`
Returns `self` (identity copy).

#### `__repr__(self) -> str`
- On success: returns `'i' + repr(str(self.data))` — the `'i'` prefix indicates an "internationalized" string.
- If resolving `str(self.data)` raises any exception: returns `'<%s broken>' % self.__class__.__name__`.

---

### Function `init(locale_dirs: List[str], language: str, catalog: str = 'sphinx', namespace: str = 'general') -> Tuple[NullTranslations, bool]`

Looks for message catalogs in the given locale directories and ensures a translator is registered in `translators[(namespace, catalog)]`. Reentrant — multiple calls merge `.mo` file contents.

**Steps:**
1. Declares `global translators`.
2. Retrieves existing translator from `translators.get((namespace, catalog))`. If the existing entry's class is exactly `NullTranslations` (i.e., a previously failed attempt), sets `translator = None` to ignore it. Sets `has_translation = True`.
3. Resolves language list: if `language` contains `'_'` (e.g., `"de_AT"`), creates `[language, language.split('_')[0]]` (e.g., `["de_AT", "de"]`). Otherwise, uses `[language]`.
4. Iterates over each directory in `locale_dirs`:
   - Calls `gettext.translation(catalog, localedir=dir_, languages=languages)`.
   - If `translator is None`, assigns the result to `translator`.
   - Otherwise, adds it as a fallback via `translator.add_fallback(trans)`.
   - On any exception (catalog not found), silently continues.
5. If `translator` is still `None` after all directories, creates a fresh `NullTranslations()` and sets `has_translation = False`.
6. Stores the result in `translators[(namespace, catalog)] = translator`.
7. Returns `(translator, has_translation)`.

---

### Function `setlocale(category: int, value: Union[str, Iterable[str]] = None) -> None`

Updates locale settings via `locale.setlocale(category, value)`. Silently catches and ignores any `locale.Error` exception — never raises. Documented as internal-use-only; will be removed in a future version.

---

### Function `init_console(locale_dir: str, catalog: str) -> Tuple[NullTranslations, bool]`

Initializes locale for console output.

**Steps:**
1. Attempts to get the system language via `locale.getlocale(locale.LC_MESSAGES)`, extracting just the language string (discarding encoding). If `locale.LC_MESSAGES` is not defined (`AttributeError`), sets `language = None`.
2. Calls `init([locale_dir], language, catalog, 'console')` and returns its result.

---

### Function `get_translator(catalog: str = 'sphinx', namespace: str = 'general') -> NullTranslations`

Returns the translator stored at `translators[(namespace, catalog)]`. Since `translators` is a `defaultdict(NullTranslations)`, accessing an unregistered key automatically creates and returns a fresh `NullTranslations()` instance.

---

### Function `is_translator_registered(catalog: str = 'sphinx', namespace: str = 'general') -> bool`

Returns `(namespace, catalog) in translators`. Note: because of the `defaultdict`, this will always return `True` (accessing via `in` triggers the default factory).

---

### Function `_lazy_translate(catalog: str, namespace: str, message: str) -> str`

Used internally by `_TranslationProxy` to resolve lazy translations. Calls `get_translator(catalog, namespace)` and returns `translator.gettext(message)`. Exists because `_` is not yet bound at module load time when the proxy is created.

---

### Function `get_translation(catalog: str, namespace: str = 'general') -> Callable`

Returns a translation function (closure named `gettext`) for the given catalog and namespace. The returned callable has signature `(message: str, *args: Any) -> str`.

**Closure logic (`gettext(message, *args)`):**
1. If `not is_translator_registered(catalog, namespace)` — translator not yet initialized — returns `_TranslationProxy(_lazy_translate, catalog, namespace, message)`, deferring resolution until the string is actually used.
2. Otherwise:
   - Gets the translator via `get_translator(catalog, namespace)`.
   - If `len(args) <= 1` (no pluralization args), returns `translator.gettext(message)`.
   - If `len(args) > 1` (pluralization support), returns `translator.ngettext(message, args[0], args[1])`, where `args[0]` is the plural form and `args[1]` is the count.

---