## sphinx/ext/autodoc/__init__.py
Now I have read the complete file (2499 lines). Here is the full natural-language specification:

---

# Module Specification: `sphinx/ext/autodoc/__init__.py`

## 1. Module-Level Preamble

### Imports

```python
import importlib
import re
import warnings
from inspect import Parameter, Signature
from types import ModuleType
from typing import (Any, Callable, Dict, Iterator, List, Optional, Sequence, Set, Tuple, Type, TypeVar, Union)

from docutils.statemachine import StringList
import sphinx
from sphinx.application import Sphinx
from sphinx.config import ENUM, Config
from sphinx.deprecation import RemovedInSphinx40Warning, RemovedInSphinx50Warning, RemovedInSphinx60Warning
from sphinx.environment import BuildEnvironment
from sphinx.ext.autodoc.importer import get_class_members, get_module_members, get_object_members, import_object
from sphinx.ext.autodoc.mock import mock
from sphinx.locale import _, __
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.util import inspect, logging
from sphinx.util.docstrings import extract_metadata, prepare_docstring
from sphinx.util.inspect import evaluate_signature, getdoc, object_description, safe_getattr, stringify_signature
from sphinx.util.typing import get_type_hints, restify
from sphinx.util.typing import stringify as stringify_typehint

# Conditional (type-annotation only):
if False:
    from typing import Type  # NOQA
    from sphinx.ext.autodoc.directive import DocumenterBridge
```

### Constants & Globals

| Name | Value / Description |
|---|---|
| `logger` | `logging.getLogger(__name__)` — module logger |
| `MethodDescriptorType` | `type(type.__subclasses__)` — the type of method descriptors |
| `py_ext_sig_re` | Compiled regex (`re.VERBOSE`) matching extended Python signatures: optional explicit module name (`::`), optional module/class path, a word for the thing name, optionally `(args) -> return_annotation`. Groups: `(explicit_modname, path, base_name, args, retann)` |
| `special_member_re` | Compiled regex `r'^__\S+__$'` — matches dunder names |
| `ALL` | Instance of `_All()` — a sentinel whose `__contains__` always returns `True`, used for `:members:` to mean "all members" |
| `EMPTY` | Instance of `_Empty()` — a sentinel whose `__contains__` always returns `False`, used for `:exclude-members:` to mean "nothing excluded" |
| `UNINITIALIZED_ATTR` | `object()` — sentinel marking an uninitialized (annotation-only) instance attribute |
| `INSTANCEATTR` | `object()` — sentinel marking an instance attribute defined in `__init__` with a doc-comment |
| `SLOTSATTR` | `object()` — sentinel marking a slot attribute |
| `SUPPRESS` | `object()` — sentinel for suppressing annotation/value display (from `:annotation:` option) |

### Helper Classes

**`_All`**: A special value matching any member. Has `__contains__(self, item)` returning `True`.

**`_Empty`**: A special value never matching any member. Has `__contains__(self, item)` returning `False`.

### Option-Conversion Functions

| Function | Signature | Behavior |
|---|---|---|
| `members_option(arg)` | `(arg: Any) → Union[object, List[str]]` | If `arg is None or arg is True`, return `ALL`. If `arg is False`, return `None`. Otherwise split on `,`, strip whitespace, return list of non-empty strings. |
| `members_set_option(arg)` | `(arg: Any) → Union[object, Set[str]]` | **Deprecated** (warns `RemovedInSphinx50Warning`). If `arg is None`, return `ALL`. Otherwise split on `,`, strip whitespace, return set of non-empty strings. |
| `exclude_members_option(arg)` | `(arg: Any) → Union[object, Set[str]]` | If `arg is None`, return `EMPTY`. Otherwise split on `,`, strip whitespace, return set of non-empty strings. |
| `inherited_members_option(arg)` | `(arg: Any) → Union[object, Set[str]]` | If `arg is None`, return `'object'`. Otherwise return `arg` unchanged. |
| `member_order_option(arg)` | `(arg: Any) → Optional[str]` | If `arg is None`, return `None`. If `arg in ('alphabetical', 'bysource', 'groupwise')`, return it. Else raise `ValueError`. |
| `annotation_option(arg)` | `(arg: Any) → Any` | If `arg is None`, return `SUPPRESS`. Otherwise return `arg`. |
| `bool_option(arg)` | `(arg: Any) → bool` | Always returns `True`. |

### Merge Functions

**`merge_special_members_option(options: Dict) → None`**: **Deprecated**. Merges `:special-members:` into `:members:`. If `'special-members' in options and options['special-members'] is not ALL`: if `options.get('members') is ALL`, do nothing; elif `options.get('members')`, append each special-member to the members list if not already present; else set `options['members'] = options['special-members']`.

**`merge_members_option(options: Dict) → None`**: If `options.get('members') is ALL`, return early. Otherwise, get or create `members = options.setdefault('members', [])`. For each of `'private-members'` and `'special-members'`: if present in options and not `ALL`/`None`, append each member to `members` if not already there.

### Event Listener Factories

**`cut_lines(pre: int, post: int = 0, what: str = None) → Callable`**: Returns a listener function for the `'autodoc-process-docstring'` event. The returned `process(app, what_, name, obj, options, lines)` function: if `what` is given and `what_ not in what`, return; delete first `pre` lines (`del lines[:pre]`); if `post > 0`, pop the trailing blank line (if present), then delete last `post` lines; ensure there's a trailing blank line.

**`between(marker: str, what: Sequence[str] = None, keepempty: bool = False, exclude: bool = False) → Callable`**: Returns a listener for `'autodoc-process-docstring'`. Compiles `marker` as regex. The returned `process(app, what_, name, obj, options, lines)` function: if `what` given and `what_ not in what`, return; iterates over original lines; toggles a `delete` flag (initially `not exclude`) when a line matches the marker regex; removes matching lines and lines between them. If result is empty and `keepempty` is False, restore original lines. Ensures trailing blank line.

### Compatibility Classes

**`Options(dict)`**: A dict/attribute hybrid. `__getattr__(self, name)`: tries to return `self[name.replace('_', '-')]`; if KeyError, returns `None`.

**`ObjectMember(tuple)`**: Immutable tuple subclass representing a member of an object. `__new__(cls, name, obj)` creates the tuple `(name, obj)`. `__init__(self, name, obj, docstring=None, skipped=False)` sets attributes: `__name__`, `object`, `docstring`, `skipped`. Behaves as a 2-tuple for backward compatibility.

**`ObjectMembers`**: Type alias = `Union[List[ObjectMember], List[Tuple[str, Any]]]`.

---

## 2. Code Objects (Classes and Functions)

### Class: `Documenter`

**Inheritance**: Base class (no explicit base).

**Class attributes:**
- `objtype = 'object'` — directive name suffix (`auto<objtype>`)
- `content_indent = '   '` — indentation for content lines
- `priority = 0` — priority for member documenter selection
- `member_order = 0` — ordering key for `'groupwise'` sorting
- `titles_allowed = False` — whether generated content may contain titles
- `option_spec = {'noindex': bool_option}`

**Instance attributes (set in `__init__`):**
- `directive`, `config`, `env`, `options`, `name`, `indent` — from constructor
- `modname`, `module`, `objpath`, `fullname` — set after `resolve_name` succeeds
- `args`, `retann` — signature arguments and return annotation, set after `parse_name`
- `object`, `object_name`, `parent` — set after `import_object`
- `analyzer` — ModuleAnalyzer or None

**Methods:**

**`get_attr(self, obj, name, *defargs)`**: Calls `autodoc_attrgetter(self.env.app, obj, name, *defargs)`.

**`can_document_member(cls, member, membername, isattr, parent) → bool`**: Abstract; raises `NotImplementedError`. Must be implemented in subclasses.

**`__init__(self, directive: DocumenterBridge, name: str, indent: str = '')`**: Stores `directive`, extracts `config`, `env`, `genopt`; sets `name`, `indent`; initializes all resolution/import attributes to `None`.

**`documenters (property) → Dict[str, Type[Documenter]]`**: Returns `self.env.app.registry.documenters`.

**`add_line(self, line: str, source: str, *lineno: int)`**: Appends the indented line to `self.directive.result`. Blank lines are appended without indentation.

**`resolve_name(self, modname, parents, path, base) → Tuple[str, List[str]]`**: Abstract; must be implemented in subclasses. Returns `(module_name, [attr_chain])`.

**`parse_name(self) → bool`**: Parses `self.name` using `py_ext_sig_re`. Extracts groups: `explicit_modname`, `path`, `base`, `args`, `retann`. If explicit module given (`::`), sets `modname = explicit_modname[:-2]`, `parents = path.split('.')`; else both empty. Calls `self.resolve_name(modname, parents, path, base)` inside a `mock(self.config.autodoc_mock_imports)` context. Sets `self.modname`, `self.objpath`, `self.args`, `self.retann`, `self.fullname`. Returns `True` on success, `False` if parsing fails or module name is empty.

**`import_object(self, raiseerror: bool = False) → bool`**: Imports the object via `import_object(self.modname, self.objpath, self.objtype, attrgetter=self.get_attr, warningiserror=...)` inside a mock context. On success, sets `self.module`, `self.parent`, `self.object_name`, `self.object`; returns `True`. On `ImportError`: if `raiseerror`, re-raises; else logs warning, calls `self.env.note_reread()`, returns `False`.

**`get_real_modname(self) → str`**: Returns `self.get_attr(self.object, '__module__', None)` or falls back to `self.modname`.

**`check_module(self) → bool`**: If `self.options.imported_members`, return `True`. Else get the subject's `__module__`; if it differs from `self.modname`, return `False`; else `True`.

**`format_args(self, **kwargs) → Optional[str]`**: Returns `None` (base implementation). Subclasses override.

**`format_name(self) → str`**: Returns `'.'.join(self.objpath)` or `self.modname`.

**`_call_format_args(self, **kwargs) → str`**: Tries `self.format_args(**kwargs)`; on `TypeError`, retries with no arguments. Used for backward compatibility.

**`format_signature(self, **kwargs) → str`**: If `self.args is not None` (explicit signature), uses it wrapped in parentheses. Else calls `_call_format_args(**kwargs)`, then parses out `(args) -> retann` via regex. Emits `'autodoc-process-signature'` event; if a handler returns `(args, retann)`, uses those. Returns `args + (' -> ' + retann)` or empty string.

**`add_directive_header(self, sig: str)`**: Gets `domain` (default `'py'`) and `directive` (from `directivetype` or `objtype`). Formats as `.. domain:directive:: name`. Multi-line signatures get continued lines indented to match the first line's prefix. Adds `:noindex:` if option set; adds `:module: modname` if `self.objpath` is non-empty.

**`get_doc(self, encoding=None, ignore=None) → List[List[str]]`**: **Deprecated** arguments `encoding`, `ignore`. Gets docstring via `getdoc(self.object, self.get_attr, ...)`. If present, returns `[prepare_docstring(docstring, ...)]`; else `[]`.

**`process_doc(self, docstrings: List[List[str]]) → Iterator[str]`**: For each docstring list, emits `'autodoc-process-docstring'` event. Appends a blank line if the last line is not already empty. Yields all lines.

**`get_sourcename(self) → str`**: If `self.object` has `__module__` and `__qualname__`, uses `'{module}.{qualname}'`; else `self.fullname`. If `self.analyzer` exists, returns `'{analyzer.srcname}:docstring of {fullname}'`; else `'docstring of {fullname}'`.

**`add_content(self, more_content: Optional[StringList], no_docstring: bool = False)`**: **Deprecated** `no_docstring` argument. If `self.analyzer`, looks up attr docs via `find_attr_docs()`; if found for this objpath key, processes those docstrings first (sets `no_docstring=True`). Then calls `get_doc()`, processing them. Finally appends any lines from `more_content`.

**`get_object_members(self, want_all: bool) → Tuple[bool, ObjectMembers]`**: **Deprecated**. Calls `get_object_members(...)` from the importer module. If not `want_all`: if no members option, returns `(False, [])`; else iterates given member names, looks them up in the dict, logs warnings for missing ones. If `want_all` and `inherited_members`, returns all; else only directly-defined members.

**`filter_members(self, members: ObjectMembers, want_all: bool) → List[Tuple[str, Any, bool]]`**: Filters member list based on privacy, special methods, documentation status, and options. Inner function `is_filtered_inherited_member(name)` checks if a name belongs to a specified super-class in the MRO. For each member: determines `isattr`; gets docstring; detects inherited docs (same as class doc); checks `'private'`/`'public'` metadata; defaults privacy to `_`-prefix. Decision tree: mocked → skip; excluded by option → skip; special method (`__dunder__`) → include only if in `special_members` option and not `__doc__` and not filtered inherited, with doc or undoc-members; documented attribute in source → keep (if private, check `private_members`); private member → keep if has doc/undoc-members and in `private_members`; else → keep if has doc or undoc-members. Also checks `autodoc-skip-member` event for user override. Returns list of `(membername, member, isattr)` tuples for kept members.

**`document_members(self, all_members: bool = False) → None`**: Sets temp data (`autodoc:module`, `autodoc:class`). Determines `want_all`. Calls `get_object_members(want_all)`, then `filter_members(...)`. For each filtered member, finds documenter classes via `can_document_member`, picks highest priority. Creates full member name with `::` separator. Sorts by `member_order` using `sort_members()`. Generates each member's documentation recursively. Resets temp data.

**`sort_members(self, documenters: List[Tuple[Documenter, bool]], order: str) → List[...]`**: If `'groupwise'`: sort by `(member_order, name)`. If `'bysource'`: if analyzer exists, use `tagorder`; else no-op (relies on insertion order). Else alphabetical by name.

**`generate(self, more_content=None, real_modname=None, check_module=False, all_members=False) → None`**: Main entry point. Calls `parse_name()`; if fails, logs warning and returns. Calls `import_object()`; if fails, returns. Determines `real_modname`. Tries to create a `ModuleAnalyzer`; on failure, adds module file as dependency. Checks module with `check_module()`. Adds blank line, formats signature (logs warning on error), adds directive header, increases indent, adds content, documents members.

---

### Class: `ModuleDocumenter(Documenter)`

**Class attributes:**
- `objtype = 'module'`
- `content_indent = ''`
- `titles_allowed = True`
- `option_spec`: `'members': members_option`, `'undoc-members': bool_option`, `'noindex': bool_option`, `'inherited-members': inherited_members_option`, `'show-inheritance': bool_option`, `'synopsis': identity`, `'platform': identity`, `'deprecated': bool_option`, `'member-order': member_order_option`, `'exclude-members': exclude_members_option`, `'private-members': members_option`, `'special-members': members_option`, `'imported-members': bool_option`, `'ignore-module-all': bool_option`

**Methods:**
- **`__init__(self, *args)`**: Calls super; calls `merge_members_option(self.options)`. Sets `self.__all__ = None`.
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Always returns `False` (doesn't document submodules).
- **`resolve_name(self, modname, parents, path, base)`**: Warns if `modname` not None. Returns `((path or '') + base, [])`.
- **`parse_name(self) → bool`**: Calls super; warns if args/retann given for automodule.
- **`import_object(self, raiseerror=False) → bool`**: Calls super. Tries `inspect.getall(self.object)` to get `__all__`; catches `AttributeError` (raises error on __all__) and `ValueError` (invalid __all__). Returns result.
- **`add_directive_header(self, sig)`**: Calls super. Adds `:synopsis:`, `:platform:`, `:deprecated:` if options set.
- **`get_object_members(self, want_all) → Tuple[bool, ObjectMembers]`**: If `want_all`: calls `get_module_members(self.object)`. If no `__all__`, returns `(True, members)` (check module). Else wraps each member in `ObjectMember(name, value)` or `ObjectMember(name, value, skipped=True)` for non-`__all__` items; returns `(False, ret)`. If not `want_all`: iterates `self.options.members`, looks up via `safe_getattr`, logs warnings for missing.
- **`sort_members(self, documenters, order)`**: If `'bysource' and self.__all__`: sorts alphabetically first, then by `__all__` index (non-listed at end). Else calls super.

---

### Class: `ModuleLevelDocumenter(Documenter)`

**Methods:**
- **`resolve_name(self, modname, parents, path, base) → Tuple[str, List[str]]`**: If `modname is None`: if `path`, use it stripped; else check `self.env.temp_data.get('autodoc:module')`, then `self.env.ref_context.get('py:module')`. Returns `(modname, parents + [base])`.

---

### Class: `ClassLevelDocumenter(Documenter)`

**Methods:**
- **`resolve_name(self, modname, parents, path, base) → Tuple[str, List[str]]`**: If `modname is None`: if `path`, use it; else check `self.env.temp_data.get('autodoc:class')`, then `self.env.ref_context.get('py:class')`. If still None, return `(None, [])`. Splits `mod_cls` on last `.` to get `modname` and `cls`. Gets module from temp_data/ref_context. Returns `(modname, [cls] + [base])`.

---

### Class: `DocstringSignatureMixin`

**Class attributes:**
- `_new_docstrings = None` — List[List[str]]
- `_signatures = None` — List[str]

**Methods:**
- **`_find_signature(self, encoding=None) → Tuple[str, str]`**: Builds `valid_names`: `[self.objpath[-1]]`, plus `'__init__'` and all MRO class names if ClassDocumenter. Gets docstrings via `get_doc()`. Scans for a line matching `py_ext_sig_re` where the base name matches one of `valid_names`. On match: re-prepares remaining docstring lines (skipping signature), stores in `_new_docstrings[i]`. First match sets result; subsequent multiline matches (ending with `\`) append to `_signatures`. Returns `(args, retann)` or `None`.
- **`get_doc(self, encoding=None, ignore=None) → List[List[str]]`**: If `_new_docstrings is not None`, returns it. Else calls super's `get_doc()`.
- **`format_signature(self, **kwargs) → str`**: If `self.args is None and autodoc_docstring_signature`: calls `_find_signature()`; if result found, sets `self.args`, `self.retann`. Calls super's `format_signature()`. If `_signatures` non-empty, joins with newlines.

---

### Class: `DocstringStripSignatureMixin(DocstringSignatureMixin)`

**Methods:**
- **`format_signature(self, **kwargs) → str`**: Same as parent but discards `args` from the result (only sets `self.retann`). Calls super's `format_signature()` which uses only `retann`.

---

### Class: `FunctionDocumenter(DocstringSignatureMixin, ModuleLevelDocumenter)`

**Class attributes:**
- `objtype = 'function'`
- `member_order = 30`

**Methods:**
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Returns True if `inspect.isfunction(member)` or `inspect.isbuiltin(member)` or (`inspect.isroutine(member)` and `isinstance(parent, ModuleDocumenter)`).
- **`format_args(self, **kwargs) → str`**: If `autodoc_typehints in ('none', 'description')`, sets `show_annotation=False`. Emits `'autodoc-before-process-signature'`. Gets signature via `inspect.signature()`, stringifies it. If `strip_signature_backslash`, escapes backslashes. Returns args or None on TypeError, empty string on ValueError.
- **`document_members(self, all_members=False)`**: No-op (functions have no members).
- **`add_directive_header(self, sig)`**: Calls super. Adds `:async:` if coroutine function.
- **`format_signature(self, **kwargs) → str`**: Checks for overloaded functions in analyzer; if so and `autodoc_typehints == 'signature'`, uses overload signatures. Else calls super. Handles singledispatch: iterates registry items (skipping default), annotates first argument via `annotate_to_first_argument()`, creates temporary FunctionDocumenter to format each signature. For overloads, evaluates and stringifies each. Returns joined signatures.
- **`annotate_to_first_argument(self, func, typ) → None`**: Gets function signature; if no params or first param already annotated, returns. Otherwise replaces first parameter's annotation with `typ`, sets `func.__signature__`. Catches TypeError for built-in types.

---

### Class: `DecoratorDocumenter(FunctionDocumenter)`

**Class attributes:**
- `objtype = 'decorator'`
- `priority = -1` (lower than FunctionDocumenter)

**Methods:**
- **`format_args(self, **kwargs) → Optional[str]`**: Calls super; if args contain `,`, returns them; else returns None.

---

### Module-level Constants for ClassDocumenter

```python
_METACLASS_CALL_BLACKLIST = ['enum.EnumMeta.__call__']
_CLASS_NEW_BLACKLIST = ['typing.Generic.__new__']
```

---

### Class: `ClassDocumenter(DocstringSignatureMixin, ModuleLevelDocumenter)`

**Class attributes:**
- `objtype = 'class'`
- `member_order = 20`
- `option_spec`: `'members': members_option`, `'undoc-members': bool_option`, `'noindex': bool_option`, `'inherited-members': inherited_members_option`, `'show-inheritance': bool_option`, `'member-order': member_order_option`, `'exclude-members': exclude_members_option`, `'private-members': members_option`, `'special-members': members_option`
- `_signature_class = None`
- `_signature_method_name = None`

**Methods:**
- **`__init__(self, *args)`**: Calls super; calls `merge_members_option(self.options)`.
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Returns `isinstance(member, type)`.
- **`import_object(self, raiseerror=False) → bool`**: Calls super. If successful and object has `__name__`, sets `self.doc_as_attr = (self.objpath[-1] != self.object.__name__)`; else `True`.
- **`_get_signature(self) → Tuple[Optional[Any], Optional[str], Optional[Signature]]`**: Inner helper `get_user_defined_function_or_method(obj, attr)` — returns the attribute if it's a user-defined method/function (not builtin class method). Checks in order: 1) `__signature__` attribute; 2) metaclass `__call__`; 3) class `__new__`; 4) class `__init__`. Each step emits `'autodoc-before-process-signature'`, tries `inspect.signature()`, returns `(class, method_name, sig)` or continues. Falls back to generic `inspect.signature(self.object, bound_method=False)`. Returns `(None, None, None)` if nothing found.
- **`format_args(self, **kwargs) → str`**: If typehints disabled, sets `show_annotation=False`. Calls `_get_signature()`. On TypeError (bad `__signature__`), logs warning and returns None. If sig is None, returns None. Else stringifies with `show_return_annotation=False`.
- **`format_signature(self, **kwargs) → str`**: If `doc_as_attr`, returns empty. Calls super's format_signature. Gets overloaded signatures via `get_overloaded_signatures()`. If overloads exist and typehints == 'signature', strips first parameter (self), sets return_annotation to empty, stringifies each. Else uses the single signature. Returns joined.
- **`get_overloaded_signatures(self) → List[Signature]`**: If `_signature_class` and `_signature_method_name`, iterates MRO; for each class, tries `ModuleAnalyzer.for_module()`; checks if qualname is in analyzer's overloads or tagorder. Returns list of overload signatures or empty.
- **`add_directive_header(self, sig)`**: If `doc_as_attr`, sets `directivetype = 'attribute'`. Calls super. Adds `:final:` if in analyzer's finals. If not doc_as_attr and show_inheritance, adds `Bases:` line using `__orig_bases__` (generic) or `__bases__` (normal), restified.
- **`get_object_members(self, want_all) → Tuple[bool, ObjectMembers]`**: Calls `get_class_members()`. If not want_all: if no members option, returns `(False, [])`; else creates ObjectMember for each named member with docstring from the member info. If inherited_members, returns all; else only those where `m.class_ == self.object`.
- **`get_doc(self, encoding=None, ignore=None) → List[List[str]]`**: If `doc_as_attr`, returns `[]`. Gets `_new_docstrings` if set. Otherwise checks `autoclass_content`: always includes class docstring. If content in ('both', 'init'), gets `__init__` doc (or `__new__` if init has default doc). If content == 'init', replaces; else appends. Prepares all docstrings.
- **`add_content(self, more_content, no_docstring=False)`**: If `doc_as_attr`, replaces content with `'alias of <restified object>'`. Calls super.
- **`document_members(self, all_members=False)`**: If `doc_as_attr`, returns; else calls super.
- **`generate(self, ...)`**: Does not pass `real_modname`; calls super's generate without it (so analyzer uses the class's own module).

---

### Class: `ExceptionDocumenter(ClassDocumenter)`

**Class attributes:**
- `objtype = 'exception'`
- `member_order = 10`
- `priority = 10`

**Methods:**
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Returns `isinstance(member, type) and issubclass(member, BaseException)`.

---

### Class: `DataDocumenterMixinBase`

**Class attributes:**
- `config = None`, `env = None`, `modname = None`, `parent = None`, `object = None`, `objpath = None`

**Methods:**
- **`should_suppress_directive_header(self) → bool`**: Returns `False`.
- **`should_suppress_value_header(self) → bool`**: Returns `False`.
- **`update_content(self, more_content: StringList)`**: No-op.

---

### Class: `GenericAliasMixin(DataDocumenterMixinBase)`

**Methods:**
- **`should_suppress_directive_header(self) → bool`**: Returns True if `inspect.isgenericalias(self.object)`.
- **`update_content(self, more_content)`**: If generic alias, appends `'alias of <stringified type>'` and blank line. Calls super.

---

### Class: `NewTypeMixin(DataDocumenterMixinBase)`

**Methods:**
- **`should_suppress_directive_header(self) → bool`**: Returns True if `inspect.isNewType(self.object)`.
- **`update_content(self, more_content)`**: If NewType, appends `'alias of <supertype restified>'` and blank line. Calls super.

---

### Class: `TypeVarMixin(DataDocumenterMixinBase)`

**Methods:**
- **`should_suppress_directive_header(self) → bool`**: Returns True if `isinstance(self.object, TypeVar)`.
- **`get_doc(self, encoding=None, ignore=None) → List[List[str]]`**: If object is a TypeVar with default docstring (same as `TypeVar.__doc__`), returns `[]`; else calls super.
- **`update_content(self, more_content)`**: If TypeVar, builds attrs list: name repr, constraint typehints, `'covariant=True'`, `'contravariant=True'`. Appends `'alias of TypeVar(...)'` and blank line. Calls super.

---

### Class: `UninitializedGlobalVariableMixin(DataDocumenterMixinBase)`

**Methods:**
- **`import_object(self, raiseerror=False) → bool`**: Tries super's import with `raiseerror=True`. On ImportError: tries to re-import the module and look up the name in type hints. If found, sets `self.object = UNINITIALIZED_ATTR`, returns True. On failure: if `raiseerror`, re-raises; else logs warning, returns False.
- **`should_suppress_value_header(self) → bool`**: Returns True if `self.object is UNINITIALIZED_ATTR`.
- **`get_doc(self, encoding=None, ignore=None) → List[List[str]]`**: If object is UNINITIALIZED_ATTR, returns `[]`; else calls super.

---

### Class: `DataDocumenter(GenericAliasMixin, NewTypeMixin, TypeVarMixin, UninitializedGlobalVariableMixin, ModuleLevelDocumenter)`

**Class attributes:**
- `objtype = 'data'`
- `member_order = 40`
- `priority = -10`
- `option_spec`: copy of `ModuleLevelDocumenter.option_spec` plus `'annotation': annotation_option`, `'no-value': bool_option`

**Methods:**
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Returns `isinstance(parent, ModuleDocumenter) and isattr`.
- **`update_annotations(self, parent)`**: Gets annotations via `inspect.getannotations()`, then merges analyzer's module-level annotations.
- **`import_object(self, raiseerror=False) → bool`**: Calls super; if parent exists, calls `update_annotations(parent)`.
- **`add_directive_header(self, sig)`**: Calls super. If annotation suppressed or directive header suppressed: skip. Else if explicit annotation option, adds it. Else looks up type hint from annotations and adds `:type:`. Tries to add `:value:` via `object_description()` unless `no_value` or value header suppressed; catches ValueError.
- **`document_members(self, all_members=False)`**: No-op.
- **`get_real_modname(self) → str`**: Returns module of parent or object, or modname.
- **`add_content(self, more_content, no_docstring=False)`**: Ensures `more_content` is not None; calls `update_content()` then super's `add_content()`.

---

### Class: `NewTypeDataDocumenter(DataDocumenter)`

**Class attributes:**
- `objtype = 'newtypedata'`
- `directivetype = 'data'`
- `priority = FunctionDocumenter.priority + 1`

**Methods:**
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Returns `inspect.isNewType(member) and isattr`.

---

### Class: `MethodDocumenter(DocstringSignatureMixin, ClassLevelDocumenter)`

**Class attributes:**
- `objtype = 'method'`
- `directivetype = 'method'`
- `member_order = 50`
- `priority = 1`

**Methods:**
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Returns `inspect.isroutine(member) and not isinstance(parent, ModuleDocumenter)`.
- **`import_object(self, raiseerror=False) → bool`**: Calls super. If successful, checks `self.parent.__dict__.get(self.object_name)` to distinguish classmethod/staticmethod. Adjusts `member_order -= 1` for class/static methods.
- **`format_args(self, **kwargs) → str`**: If typehints disabled, sets `show_annotation=False`. Special case: if object is `object.__init__` and parent != object, returns `'()'`. For staticmethods, calls with `bound_method=False`; else `bound_method=True`. Emits `'autodoc-before-process-signature'`. Escapes backslashes. Returns args or None/empty on error.
- **`add_directive_header(self, sig)`**: Calls super. Adds `:abstractmethod:`, `:async:`, `:classmethod:`, `:staticmethod:`, `:final:` as appropriate based on inspection and analyzer.
- **`document_members(self, all_members=False)`**: No-op.
- **`format_signature(self, **kwargs) → str`**: Checks for overloaded methods in analyzer; if so, uses overload signatures (stripping first parameter unless staticmethod). Handles singledispatch: iterates registry, annotates second argument (self is index 1), creates temporary MethodDocumenter. Returns joined signatures.
- **`annotate_to_first_argument(self, func, typ) → None`**: Gets signature; if only one param, returns. Otherwise annotates `params[1]` (second parameter, after self). Sets `func.__signature__`.

---

### Class: `NonDataDescriptorMixin(DataDocumenterMixinBase)`

**Methods:**
- **`should_suppress_value_header(self) → bool`**: Returns True if `inspect.isattributedescriptor(self.object)`.
- **`get_doc(self, encoding=None, ignore=None) → List[List[str]]`**: If not an attribute descriptor, returns `[]`; else calls super.

---

### Class: `SlotsMixin(DataDocumenterMixinBase)`

**Methods:**
- **`isslotsattribute(self) → bool`**: Gets slots via `inspect.getslots()`; checks if objpath[-1] is in slots dict. Catches errors, returns False.
- **`import_object(self, raiseerror=False) → bool`**: Calls super. If slot attribute, sets `self.object = SLOTSATTR`.
- **`should_suppress_directive_header(self) → bool`**: If object is SLOTSATTR, sets `_datadescriptor = True`, returns True; else calls super.
- **`get_doc(self, encoding=None, ignore=None) → List[List[str]]`**: If SLOTSATTR, gets slot docstring from slots dict and prepares it; else calls super.

---

### Class: `UninitializedInstanceAttributeMixin(DataDocumenterMixinBase)`

**Methods:**
- **`get_attribute_comment(self, parent) → Optional[List[str]]`**: Iterates MRO of parent; for each class, gets module/qualname, creates analyzer, looks up `(qualname, objpath[-1])` in `analyzer.attr_docs`. Returns comment lines or None.
- **`is_uninitialized_instance_attribute(self, parent) → bool`**: Returns True if `get_attribute_comment(parent)` returns non-None.
- **`import_object(self, raiseerror=False) → bool`**: Tries super with `raiseerror=True`. On ImportError: tries to import the class (objpath[:-1]), checks for uninitialized instance attribute; if found, sets `self.object = UNINITIALIZED_ATTR`, `self.parent = parent`, returns True. On failure: re-raises or logs warning/returns False.
- **`should_suppress_value_header(self) → bool`**: Returns True if object is UNINITIALIZED_ATTR.
- **`get_doc(self, encoding=None, ignore=None) → List[List[str]]`**: If UNINITIALIZED_ATTR, returns attribute comment lines; else calls super.
- **`add_content(self, more_content, no_docstring=False)`**: If UNINITIALIZED_ATTR, sets `self.analyzer = None`. Calls super.

---

### Class: `AttributeDocumenter(GenericAliasMixin, NewTypeMixin, SlotsMixin, TypeVarMixin, UninitializedInstanceAttributeMixin, NonDataDescriptorMixin, DocstringStripSignatureMixin, ClassLevelDocumenter)`

**Class attributes:**
- `objtype = 'attribute'`
- `member_order = 60`
- `option_spec`: copy of ModuleLevelDocumenter's plus `'annotation': annotation_option`, `'no-value': bool_option`
- `priority = 10` (higher than MethodDocumenter)

**Methods:**
- **`is_function_or_method(obj)`**: Static method; returns True if function, builtin, or method.
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Returns True if attribute descriptor; OR (not module-level and not routine and not type).
- **`document_members(self, all_members=False)`**: No-op.
- **`isinstanceattribute(self) → bool`**: Tries to import the class (objpath[:-1]), gets type hints; if objpath[-1] in annotations, sets `self.object = UNINITIALIZED_ATTR`, returns True. Catches ImportError.
- **`update_annotations(self, parent)`**: Gets annotations via `inspect.getannotations()`. Iterates MRO of parent; for each class, creates analyzer and merges class-level annotations where classname matches qualname.
- **`import_object(self, raiseerror=False) → bool`**: Tries super with `raiseerror=True`; if enum attribute, replaces object with its `.value`. On ImportError: if isinstanceattribute(), sets `self.object = INSTANCEATTR`, returns True; else re-raises or logs/returns False. If parent exists, calls update_annotations().
- **`get_real_modname(self) → str`**: Returns module of parent or object, or modname.
- **`add_directive_header(self, sig)`**: Calls super. If annotation suppressed: skip. Else if explicit annotation option, adds it. Else looks up type hint and adds `:type:`. Tries to add `:value:` unless INSTANCEATTR/no_value/suppressed; catches ValueError.
- **`get_doc(self, encoding=None, ignore=None) → List[List[str]]`**: If INSTANCEATTR, returns `[]`. Temporarily disables `autodoc_inherit_docstrings`, calls super, restores setting.
- **`add_content(self, more_content, no_docstring=False)`**: Ensures not None; calls update_content then super's add_content.

---

### Class: `PropertyDocumenter(DocstringStripSignatureMixin, ClassLevelDocumenter)`

**Class attributes:**
- `objtype = 'property'`
- `directivetype = 'method'`
- `member_order = 60`
- `priority = AttributeDocumenter.priority + 1` (i.e., 11)

**Methods:**
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Returns `inspect.isproperty(member) and isinstance(parent, ClassDocumenter)`.
- **`document_members(self, all_members=False)`**: No-op.
- **`get_real_modname(self) → str`**: Returns module of parent or object, or modname.
- **`add_directive_header(self, sig)`**: Calls super. Adds `:abstractmethod:` if abstract; always adds `:property:`.

---

### Class: `NewTypeAttributeDocumenter(AttributeDocumenter)`

**Class attributes:**
- `objtype = 'newvarattribute'`
- `directivetype = 'attribute'`
- `priority = MethodDocumenter.priority + 1` (i.e., 2)

**Methods:**
- **`can_document_member(cls, member, membername, isattr, parent) → bool`**: Returns `not isinstance(parent, ModuleDocumenter) and inspect.isNewType(member)`.

---

## 3. Standalone Functions

### `get_documenters(app: Sphinx) → Dict[str, Type[Documenter]]`
**Deprecated** (warns `RemovedInSphinx50Warning`). Returns `app.registry.documenters`.

### `autodoc_attrgetter(app: Sphinx, obj: Any, name: str, *defargs: Any) → Any`
Iterates over `app.registry.autodoc_attrgettrs.items()` — for each `(typ, func)` where `isinstance(obj, typ)`, calls `func(obj, name, *defargs)`. Falls back to `safe_getattr(obj, name, *defargs)`.

### `migrate_autodoc_member_order(app: Sphinx, config: Config) → None`
If `config.autodoc_member_order == 'alphabetic'`: logs warning and changes it to `'alphabetical'`.

---

## 4. Compatibility Imports (from deprecated submodule)

```python
from sphinx.ext.autodoc.deprecated import DataDeclarationDocumenter
from sphinx.ext.autodoc.deprecated import GenericAliasDocumenter
from sphinx.ext.autodoc.deprecated import InstanceAttributeDocumenter
from sphinx.ext.autodoc.deprecated import SingledispatchFunctionDocumenter
from sphinx.ext.autodoc.deprecated import SingledispatchMethodDocumenter
from sphinx.ext.autodoc.deprecated import SlotsAttributeDocumenter
from sphinx.ext.autodoc.deprecated import TypeVarDocumenter
```

---

## 5. `setup(app: Sphinx) → Dict[str, Any]`

Registers documenters with the app:
1. `ModuleDocumenter`, `ClassDocumenter`, `ExceptionDocumenter`, `DataDocumenter`, `NewTypeDataDocumenter`, `FunctionDocumenter`, `DecoratorDocumenter`, `MethodDocumenter`, `AttributeDocumenter`, `PropertyDocumenter`, `NewTypeAttributeDocumenter`

Adds config values:
- `autoclass_content`: `'class'`, ENUM(`'both'`, `'class'`, `'init'`)
- `autodoc_member_order`: `'alphabetical'`, ENUM(`'alphabetic'`, `'alphabetical'`, `'bysource'`, `'groupwise'`)
- `autodoc_default_options`: `{}`
- `autodoc_docstring_signature`: `True`
- `autodoc_mock_imports`: `[]`
- `autodoc_typehints`: `"signature"`, ENUM(`"signature"`, `"description"`, `"none"`)
- `autodoc_type_aliases`: `{}`
- `autodoc_warningiserror`: `True`
- `autodoc_inherit_docstrings`: `True`

Registers events: `'autodoc-before-process-signature'`, `'autodoc-process-docstring'`, `'autodoc-process-signature'`, `'autodoc-skip-member'`.

Connects `migrate_autodoc_member_order` to `'config-inited'` at priority 800.

Sets up extensions: `'sphinx.ext.autodoc.type_comment'`, `'sphinx.ext.autodoc.typehints'`.

Returns `{'version': sphinx.__display_version__, 'parallel_read_safe': True}`.

## sphinx/ext/autodoc/importer.py
Now I have the full file content (339 lines). Here is the complete natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import importlib
import traceback
import warnings
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Tuple

from sphinx.deprecation import RemovedInSphinx40Warning, deprecated_alias
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import logging
from sphinx.util.inspect import (getannotations, getmro, getslots, isclass, isenumclass, safe_getattr)
```

Conditional (type-annotation-only, guarded by `if False`):
```python
from typing import Type  # NOQA
```

### Constants & Globals

* **`logger`** — `logging.getLogger(__name__)`, the module-level logger instance.

External constants referenced but defined in `sphinx.ext.autodoc`:
* **`INSTANCEATTR`** — sentinel value used to represent an instance attribute whose actual value is not known at introspection time (e.g., annotation-only members).
* **`SLOTSATTR`** — sentinel value used to represent a slot-defined attribute.

---

## Code Objects

### `mangle(subject: Any, name: str) -> str`

Mangles a private name using Python's name-mangling convention (`_ClassName__name`).

1. Attempts to check whether `subject` is a class via `isclass(subject)` and whether `name` starts with `"__"` but does not end with `"__"`.
2. If both conditions hold, returns `"_<subject.__name>_<name>"` (i.e., prepends `_ClassName` before the double-underscore prefix).
3. On `AttributeError`, falls through to step 4.
4. Returns `name` unchanged.

---

### `unmangle(subject: Any, name: str) -> Optional[str]`

Reverses Python's name-mangling for a given subject class.

1. Attempts the following checks on `subject`:
   - If `subject` is a class and `name` does not end with `"__"`:
     - Constructs `prefix = "_<subject.__name>__"`. If `name` starts with this prefix, returns `name` with that prefix replaced by `"__"` (single replacement). This restores the original dunder-style name.
     - Otherwise, iterates over every class in `subject.__mro__`:
       - For each ancestor `cls`, constructs `prefix = "_<cls.__name>__"`. If `name` starts with this prefix, returns `None` — indicating the mangled attribute was defined in a parent class and cannot be unmangled to the current class's namespace.
2. On any `AttributeError`, falls through to step 3.
3. Returns `name` unchanged (no mangling detected).

---

### `import_module(modname: str, warningiserror: bool = False) -> Any`

Imports a module by name using `importlib.import_module`, with controlled warning behavior and error conversion.

1. Enters a `warnings.catch_warnings()` context that filters out all `ImportWarning` instances (ignored).
2. Within that, enters `logging.skip_warningiserror(not warningiserror)` — if `warningiserror` is `False`, warnings are not treated as errors during import; if `True`, they are.
3. Calls `importlib.import_module(modname)` and returns the resulting module object.
4. Catches any `BaseException` (including `SystemExit`) and raises a new `ImportError(exc, traceback.format_exc())` chained from the original exception.

---

### `import_object(modname: str, objpath: List[str], objtype: str = '', attrgetter: Callable[[Any, str], Any] = safe_getattr, warningiserror: bool = False) -> Any`

Imports and resolves a nested object path within a module, returning `[module, parent, object_name, obj]`.

**Logging:**
- If `objpath` is non-empty, logs `[autodoc] from <modname> import <joined_objpath>`.
- Otherwise, logs `[autodoc] import <modname>`.

**Module resolution loop (lines 86–98):**
1. Initializes `module = None`, `exc_on_importing = None`, and copies `objpath` into a mutable list.
2. Enters a `while module is None:` loop:
   - Attempts to import `modname` via `import_module(modname, warningiserror)`. On success, logs the result and exits the loop.
   - On `ImportError`: stores it in `exc_on_importing`, logs failure. If `modname` contains a dot (`.`), splits off the last component via `rsplit('.', 1)`, prepends that component to the front of `objpath`, and retries with the parent module name. If no dot remains, re-raises.

**Attribute resolution (lines 100–110):**
1. Sets `obj = module`, `parent = None`, `object_name = None`.
2. For each `attrname` in `objpath`:
   - Saves the current `obj` as `parent`.
   - Logs the getattr operation.
   - Computes `mangled_name = mangle(obj, attrname)`.
   - Retrieves the attribute via `obj = attrgetter(obj, mangled_name)` (default: `safe_getattr`).
   - Sets `object_name = attrname`.
3. Returns `[module, parent, object_name, obj]`.

**Error handling (lines 111–137):**
- Catches `(AttributeError, ImportError)`:
  - If an `AttributeError` occurred and `exc_on_importing` is set, replaces the exception with the stored `ImportError`.
  - Constructs a descriptive error message:
    - If `objpath` is non-empty: `'autodoc: failed to import <objtype> <joined_objpath> from module <modname>'`.
    - Otherwise: `'autodoc: failed to import <objtype> <modname>'`.
  - If the exception is an `ImportError` (from `import_module`, carrying `(real_exc, traceback_msg)`):
    - If `real_exc` is a `SystemExit`: appends `'; the module executes module level statement and it might call sys.exit().'`.
    - If `real_exc` is an `ImportError` with args: appends `'; the following exception was raised:\n<arg0>'`.
    - Otherwise: appends `'; the following exception was raised:\n<traceback_msg>'`.
  - For non-`ImportError` exceptions: appends `'; the following exception was raised:\n<trraceback.format_exc()>'`.
  - Logs the error message and raises a new `ImportError(errmsg)` chained from the original exception.

---

### `get_module_members(module: Any) -> List[Tuple[str, Any]]`

Collects all members of a module as a sorted list of `(name, value)` tuples.

1. Imports `INSTANCEATTR` from `sphinx.ext.autodoc`.
2. Initializes an empty dict `members`.
3. Iterates over every name in `dir(module)`:
   - Attempts `value = safe_getattr(module, name, None)`. On success, stores `(name, value)` in the dict.
   - On `AttributeError`, continues to the next name.
4. Annotation-only members: attempts to iterate over `getannotations(module)`. For each annotation name not already in `members`, adds `(name, INSTANCEATTR)`. Catches `AttributeError` silently.
5. Returns `sorted(list(members.values()))` — a sorted list of `(str, Any)` tuples.

---

### `Attribute = NamedTuple('Attribute', [('name', str), ('directly_defined', bool), ('value', Any)])`

A named tuple with three fields:
- **`name`** (`str`) — the attribute's name.
- **`directly_defined`** (`bool`) — whether the attribute is defined directly on the subject (vs. inherited).
- **`value`** (`Any`) — the attribute's value, or a sentinel like `INSTANCEATTR`.

---

### `_getmro(obj: Any) -> Tuple["Type", ...]`

**Deprecated.** Issues a `RemovedInSphinx40Warning` and delegates to `getmro(obj)` from `sphinx.util.inspect`, returning the method resolution order tuple.

---

### `_getannotations(obj: Any) -> Mapping[str, Any]`

**Deprecated.** Issues a `RemovedInSphinx40Warning` and delegates to `getannotations(obj)` from `sphinx.util.inspect`, returning the annotations mapping.

---

### `get_object_members(subject: Any, objpath: List[str], attrgetter: Callable, analyzer: ModuleAnalyzer = None) -> Dict[str, Attribute]`

Collects members and attributes of a target object (module or class), returning a dict mapping name to `Attribute`.

1. Imports `INSTANCEATTR` from `sphinx.ext.autodoc`.
2. Retrieves the subject's own `__dict__` via `attrgetter(subject, '__dict__', {})`.
3. Initializes an empty dict `members`.

**Enum members (if `isenumclass(subject)`):**
- Iterates over `subject.__members__.items()`. For each `(name, value)`, if `name` is not already in `members`, adds `Attribute(name, True, value)`.
- Gets the superclass as `subject.__mro__[1]`. Iterates over names in `obj_dict`; for any name not present in the superclass's `__dict__`, retrieves its value via `safe_getattr(subject, name)` and adds `Attribute(name, True, value)`.

**`__slots__` members:**
- Attempts to call `getslots(subject)`. If non-empty:
  - Imports `SLOTSATTR` from `sphinx.ext.autodoc`.
  - For each slot name in the result, adds `Attribute(name, True, SLOTSATTR)`.
- Catches `(AttributeError, TypeError, ValueError)` and passes.

**Other members (via `dir(subject)`):**
- Iterates over every name from `dir(subject)`:
  - Retrieves `value = attrgetter(subject, name)`.
  - Sets `directly_defined = name in obj_dict`.
  - Computes `name = unmangle(subject, name)`. If the result is truthy and not already in `members`, adds `Attribute(name, directly_defined, value)`.
  - Catches `AttributeError` and continues.

**Annotation-only members:**
- Iterates over every class in `getmro(subject)` with its index `i`:
  - Attempts to iterate over `getannotations(cls)`. For each annotation name:
    - Computes `name = unmangle(cls, name)`. If truthy and not already in `members`, adds `Attribute(name, i == 0, INSTANCEATTR)` — `directly_defined` is `True` only for annotations on the first (subject) class.
  - Catches `AttributeError` and passes.

**Analyzer-provided instance attributes:**
- If `analyzer` is provided:
  - Constructs `namespace = '.'.join(objpath)`.
  - Iterates over `analyzer.find_attr_docs()` yielding `(ns, name)` tuples. For each where `namespace == ns` and the name is not already in `members`, adds `Attribute(name, True, INSTANCEATTR)`.

Returns `members`.

---

### `class ClassAttribute`

A simple data class representing a class attribute with optional docstring.

**`__init__(self, cls: Any, name: str, value: Any, docstring: Optional[str] = None)`**
- Sets four instance attributes:
  - **`self.class_`** (`Any`) — the class that owns this attribute.
  - **`self.name`** (`str`) — the attribute's name.
  - **`self.value`** (`Any`) — the attribute's value.
  - **`self.docstring`** (`Optional[str]`) — an optional docstring; defaults to `None`.

---

### `get_class_members(subject: Any, objpath: List[str], attrgetter: Callable, analyzer: ModuleAnalyzer = None) -> Dict[str, ClassAttribute]`

Collects members and attributes of a target class, returning a dict mapping name to `ClassAttribute`.

1. Imports `INSTANCEATTR` from `sphinx.ext.autodoc`.
2. Retrieves the subject's own `__dict__` via `attrgetter(subject, '__dict__', {})`.
3. Initializes an empty dict `members`.

**Enum members (if `isenumclass(subject)`):**
- Iterates over `subject.__members__.items()`. For each `(name, value)`, if `name` is not already in `members`, adds `ClassAttribute(subject, name, value)`.
- Gets the superclass as `subject.__mro__[1]`. Iterates over names in `obj_dict`; for any name not present in the superclass's `__dict__`, retrieves its value via `safe_getattr(subject, name)` and adds `ClassAttribute(subject, name, value)`.

**`__slots__` members:**
- Attempts to call `getslots(subject)`. If non-empty:
  - Imports `SLOTSATTR` from `sphinx.ext.autodoc`.
  - For each `(name, docstring)` pair in the slots dict, adds `ClassAttribute(subject, name, SLOTSATTR, docstring)`.
- Catches `(AttributeError, TypeError, ValueError)` and passes.

**Other members (via `dir(subject)`):**
- Iterates over every name from `dir(subject)`:
  - Retrieves `value = attrgetter(subject, name)`.
  - Computes `unmangled = unmangle(subject, name)`. If truthy and not already in `members`:
    - If the original `name` is in `obj_dict`, adds `ClassAttribute(subject, unmangled, value)` (class owner is `subject`).
    - Otherwise, adds `ClassAttribute(None, unmangled, value)` (no class owner).
  - Catches `AttributeError` and continues.

**Annotation-only members:**
- Iterates over every class in `getmro(subject)`:
  - Attempts to iterate over `getannotations(cls)`. For each annotation name:
    - Computes `name = unmangle(cls, name)`. If truthy and not already in `members`, adds `ClassAttribute(cls, name, INSTANCEATTR)` — the owning class is set to the class where the annotation was found.
  - Catches `AttributeError` and passes.

**Analyzer-provided instance attributes:**
- If `analyzer` is provided:
  - Constructs `namespace = '.'.join(objpath)`.
  - Iterates over `analyzer.attr_docs.items()` yielding `((ns, name), docstring)` tuples. For each where `namespace == ns` and the name is not already in `members`, adds `ClassAttribute(subject, name, INSTANCEATTR, '\n'.join(docstring))`.

Returns `members`.

---

### Post-import: Mock re-exports and deprecation aliases

**Import from mock module:**
```python
from sphinx.ext.autodoc.mock import (MockFinder, MockLoader, _MockModule, _MockObject, mock)
```
These are imported with `# NOQA` to suppress unused-import warnings.

**Deprecated alias registration via `deprecated_alias`:**
Registers backward-compatible aliases for the following symbols under `sphinx.ext.autodoc.importer`, all deprecated with `RemovedInSphinx40Warning`:

| Old name | New location |
|---|---|
| `_MockModule` | `sphinx.ext.autodoc.mock._MockModule` |
| `_MockObject` | `sphinx.ext.autodoc.mock._MockObject` |
| `MockFinder` | `sphinx.ext.autodoc.mock.MockFinder` |
| `MockLoader` | `sphinx.ext.autodoc.mock.MockLoader` |
| `mock` | `sphinx.ext.autodoc.mock.mock` |

The `deprecated_alias` call maps each old name to its new import path, so that code importing from the old location receives a deprecation warning and is redirected.