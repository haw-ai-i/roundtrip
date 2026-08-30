## sphinx/ext/autodoc/__init__.py
Now I have the full file. Here is the complete specification:

---

# Module Specification: `sphinx/ext/autodoc/__init__.py`

## 1. Module-Level Preamble

### Imports

```python
import re
import warnings
from inspect import Parameter, Signature
from types import ModuleType
from typing import (Any, Callable, Dict, Iterator, List, Optional, Sequence, Set, Tuple, Type,
                    TypeVar, Union)

from docutils.statemachine import StringList

import sphinx
from sphinx.application import Sphinx
from sphinx.config import ENUM, Config
from sphinx.deprecation import (RemovedInSphinx40Warning, RemovedInSphinx50Warning,
                                RemovedInSphinx60Warning)
from sphinx.environment import BuildEnvironment
from sphinx.ext.autodoc.importer import (ClassAttribute, get_class_members, get_module_members,
                                         import_module, import_object)
from sphinx.ext.autodoc.mock import mock
from sphinx.locale import _, __
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.util import inspect, logging
from sphinx.util.docstrings import extract_metadata, prepare_docstring
from sphinx.util.inspect import (evaluate_signature, getdoc, object_description, safe_getattr,
                                 stringify_signature)
from sphinx.util.typing import get_type_hints, restify
from sphinx.util.typing import stringify as stringify_typehint

# conditional imports for type annotations only (if False block):
#   from typing import Type  # NOQA
#   from sphinx.ext.autodoc.directive import DocumenterBridge
```

### Constants & Globals

| Name | Value / Description |
|---|---|
| `logger` | `logging.getLogger(__name__)` |
| `MethodDescriptorType` | `type(type.__subclasses__)` — the type of method descriptors |
| `py_ext_sig_re` | Compiled regex (`re.VERBOSE`) matching extended Python signatures: optional explicit module name (`::`), optional module/class prefix, a word for the thing name, optionally `(args) -> return_annotation`. Groups: `(explicit_modname, path, base_name, args, retann)` |
| `special_member_re` | Compiled regex `r'^__\S+__$'` — matches dunder names |
| `_All` class (instances below) | A sentinel whose `__contains__` always returns `True`, used for `:members:` meaning "all members" |
| `_Empty` class | A sentinel whose `__contains__` always returns `False`, used for `:exclude-members:` meaning "nothing to exclude" |
| `ALL` | Singleton instance of `_All()` |
| `EMPTY` | Singleton instance of `_Empty()` |
| `UNINITIALIZED_ATTR` | Sentinel object (`object()`) marking uninitialized (annotation-only) attributes |
| `INSTANCEATTR` | Sentinel object (`object()`) marking runtime instance attributes |
| `SLOTSATTR` | Sentinel object (`object()`) marking `__slots__` attributes |
| `SUPPRESS` | Sentinel object (`object()`) used to suppress showing the representation of an object in annotations |

### Module-Level Functions (Option Parsers & Event Listener Factories)

**`members_option(arg: Any) -> Union[object, List[str]]`**: Converts `:members:` option value. If `arg` is `None` or `True`, returns `ALL`. If `False`, returns `None`. Otherwise splits on `,`, strips whitespace, and returns a list of member name strings (empty-string entries filtered out).

**`members_set_option(arg: Any) -> Union[object, Set[str]]`**: Deprecated. Converts `:members:` to a set. If `arg` is `None`, returns `ALL`; otherwise splits on `,` into a set of stripped names. Emits `RemovedInSphinx50Warning`.

**`exclude_members_option(arg: Any) -> Union[object, Set[str]]`**: Converts `:exclude-members:` option. If `arg` is `None` or `True`, returns `EMPTY`. Otherwise splits on `,` into a set of stripped names.

**`inherited_members_option(arg: Any) -> Union[object, Set[str]]`**: Converts `:members:` for inherited members. If `arg` is `None` or `True`, returns the string `'object'`; otherwise returns `arg` unchanged.

**`member_order_option(arg: Any) -> Optional[str]`**: Validates member order option. Returns `None` if `arg` is `None`/`True`. Accepts `'alphabetical'`, `'bysource'`, `'groupwise'`. Raises `ValueError` for any other value.

**`annotation_option(arg: Any) -> Any`**: Converts annotation option. If `arg` is `None` or `True`, returns `SUPPRESS`; otherwise returns `arg` as-is (a custom annotation string).

**`bool_option(arg: Any) -> bool`**: Always returns `True`. Used for flag options that have no argument value.

**`merge_special_members_option(options: Dict) -> None`**: Deprecated. Merges `:special-members:` into `:members:`. If `'special-members'` is in options and not `ALL`: if `members` is `ALL`, do nothing; if `members` already has entries, append each special-member not already present; otherwise set `options['members'] = options['special-members']`. Emits `RemovedInSphinx50Warning`.

**`merge_members_option(options: Dict) -> None`**: Merges `:private-members:` and `:special-members:` into `:members:`. If `members` is already `ALL`, returns immediately (no merge needed). Otherwise, for each of `'private-members'` and `'special-members'` that exist in options and are not `ALL`/`None`, appends any member names not already in the members list.

**`cut_lines(pre: int, post: int = 0, what: str = None) -> Callable`**: Returns an event listener function for `'autodoc-process-docstring'`. If `what` is given and the docstring type (`what_`) is not in it, returns without modifying. Deletes the first `pre` lines from `lines`. If `post > 0`, removes one trailing blank line if present, then deletes the last `post` lines. Ensures a trailing blank line exists. The returned function has signature `(app: Sphinx, what_: str, name: str, obj: Any, options: Any, lines: List[str]) -> None`.

**`between(marker: str, what: Sequence[str] = None, keepempty: bool = False, exclude: bool = False) -> Callable`**: Returns an event listener for `'autodoc-process-docstring'`. Compiles `marker` as a regex. Iterates over lines toggling a `delete` flag each time the marker matches (toggle on/off). If `exclude=True`, keeps instead of deletes. If no lines remain and `keepempty=False`, restores original lines. Ensures trailing blank line.

### Classes: `Options`, `ObjectMember`

**`class Options(dict)`**: A dict/attribute hybrid. `__getattr__(self, name)`: looks up `name.replace('_', '-')` in the dict; returns `None` on `KeyError`. Used for compatibility with directive option access patterns.

**`class ObjectMember(tuple)`**: Immutable tuple subclass representing a member of an object (pair: `(name, obj)`). Additional attributes set via `__init__`:
- `self.__name__ = name` (str)
- `self.object = obj` (Any)
- `self.docstring = docstring` (Optional[str])
- `self.skipped = skipped` (bool)
- `self.class_ = class_` (Any)

**`ObjectMembers`**: Type alias: `Union[List[ObjectMember], List[Tuple[str, Any]]]`.

---

## 2. Code Objects — Classes and Functions

### Class: `Documenter`

**Inheritance**: None (base class). **Metaclass**: None.

**Class attributes:**
- `objtype = 'object'` — directive name suffix (`auto` + objtype)
- `content_indent = '   '` — indentation for content lines
- `priority = 0` — priority for member documenter selection (higher wins)
- `member_order = 0` — ordering key for `'groupwise'` sorting
- `titles_allowed = False` — whether generated content may contain titles
- `option_spec = {'noindex': bool_option}`

**Instance attributes** (set in `__init__`):
- `self.directive` — the `DocumenterBridge` from the directive
- `self.config` — `directive.env.config`
- `self.env` — `BuildEnvironment`
- `self.options` — `directive.genopt`
- `self.name` — the fully qualified name string given to the documenter
- `self.indent` — indentation prefix for output lines
- `self.modname` (str) — module name, set after `resolve_name` succeeds
- `self.module` (ModuleType) — imported module object
- `self.objpath` (List[str]) — chain of attribute names within the module
- `self.fullname` (str) — fully qualified name (`modname + '.' + objpath joined`)
- `self.args` (str) — explicit signature arguments from parsing
- `self.retann` (str) — explicit return annotation from parsing
- `self.object` (Any) — the actual Python object to document, set after `import_object`
- `self.object_name` (str) — name of the imported object
- `self.parent` (Any) — parent/owner object (e.g., class for a method)
- `self.analyzer` (ModuleAnalyzer or None) — source code analyzer

**Methods:**

**`get_attr(obj: Any, name: str, *defargs: Any) -> Any`**: Calls `autodoc_attrgetter(self.env.app, obj, name, *defargs)` as a custom getattr for types like Zope interfaces.

**`can_document_member(cls, member: Any, membername: str, isattr: bool, parent: Any) -> bool`**: Class method. Must be implemented in subclasses. Returns whether this documenter can handle the given member. Raises `NotImplementedError` if not overridden.

**`__init__(self, directive: "DocumenterBridge", name: str, indent: str = '') -> None`**: Initializes all instance attributes from the directive and parameters. Sets `modname`, `module`, `objpath`, `fullname`, `args`, `retann`, `object`, `object_name`, `parent`, `analyzer` to `None`.

**`documenters (property) -> Dict[str, Type[Documenter]]`**: Returns `self.env.app.registry.documenters`.

**`add_line(self, line: str, source: str, *lineno: int) -> None`**: Appends the indented line to `self.directive.result`. Blank lines are appended without indentation.

**`resolve_name(self, modname: str, parents: Any, path: str, base: Any) -> Tuple[str, List[str]]`**: Abstract method. Resolves module name and attribute chain from arguments plus current context. Must be implemented in subclasses. Returns `(modname, objpath_list)`.

**`parse_name(self) -> bool`**: Parses `self.name` using `py_ext_sig_re`. Extracts explicit module name, path, base name, args, return annotation. Calls `resolve_name(modname, parents, path, base)` inside a `mock(autodoc_mock_imports)` context. Sets `self.modname`, `self.objpath`, `self.args`, `self.retann`, `self.fullname`. Returns `True` on success; logs warning and returns `False` on parse failure or missing module name.

**`import_object(self, raiseerror: bool = False) -> bool`**: Imports the object via `import_object(self.modname, self.objpath, self.objtype, attrgetter=self.get_attr, ...)` inside a `mock()` context. Sets `self.module`, `self.parent`, `self.object_name`, `self.object`. Returns `True` on success. On `ImportError`: if `raiseerror=True`, re-raises; otherwise logs warning, calls `self.env.note_reread()`, returns `False`.

**`get_real_modname(self) -> str`**: Returns the object's `__module__` attribute (via `get_attr`) or falls back to `self.modname`.

**`check_module(self) -> bool`**: Checks if `self.object` is really defined in `self.modname`. If `options.imported_members` is set, returns `True`. Otherwise gets the object's `__module__`; if different from `self.modname`, returns `False`.

**`format_args(self, **kwargs: Any) -> str`**: Returns `None` by default. Subclasses override to format argument signatures.

**`format_name(self) -> str`**: Returns `'.'.join(self.objpath)` or `self.modname`.

**`_call_format_args(self, **kwargs: Any) -> str`**: Tries `self.format_args(**kwargs)`; on `TypeError`, retries with no arguments for backward compatibility.

**`format_signature(self, **kwargs: Any) -> str`**: If explicit `self.args` is set, wraps it as `"(%s)"`. Otherwise calls `_call_format_args(**kwargs)` to introspect the signature. Parses out return annotation from `"(...)->..."` pattern if present. Emits `'autodoc-process-signature'` event; if a handler returns `(args, retann)`, uses those. Returns `args + (' -> ' + retann if retann else '')`.

**`add_directive_header(self, sig: str) -> None`**: Determines domain (`self.domain` or `'py'`) and directive name (`self.directivetype` or `self.objtype`). Formats the header as `.. {domain}:{directive}::{name}{sig}` (one per line, subsequent lines indented). Adds `:noindex:` if option set. Adds `:module: {modname}` if `objpath` is non-empty.

**`get_doc(self, encoding=None, ignore=None) -> Optional[List[List[str]]]`**: Emits deprecation warnings for `encoding`/`ignore`. Calls `getdoc(self.object, self.get_attr, config.autodoc_inherit_docstrings, self.parent, self.object_name)`. If docstring exists, returns `[prepare_docstring(docstring, ignore, tab_width)]`; otherwise returns `[]`.

**`process_doc(self, docstrings: List[List[str]]) -> Iterator[str]`**: For each docstring list, emits `'autodoc-process-docstring'` event. Appends a blank line if the last line is not already empty. Yields all lines from each processed docstring.

**`get_sourcename(self) -> str`**: If object has `__module__` and `__qualname__`, returns `'docstring of {module}.{qualname}'`. Otherwise uses `self.fullname`. If `self.analyzer` exists, prepends the analyzer's source name as `{srcname}:docstring of ...`.

**`add_content(self, more_content: Optional[StringList], no_docstring=False) -> None`**: 
1. If `no_docstring` is set, emits deprecation warning.
2. Gets sourcename. If `self.analyzer` exists, looks up attribute docs via `find_attr_docs()`. If a matching key `(objpath[:-1], objpath[-1])` is found, sets `no_docstring=True`, processes those docstrings, and adds lines.
3. If not `no_docstring`, calls `get_doc()`; if it returns `None`, skips processing-docstring event; otherwise ensures at least one empty list in the result (to fire the event), then processes each via `process_doc()`.
4. If `more_content` is provided, iterates over its `.data` and `.items` pairs, adding each line with its source location.

**`get_object_members(self, want_all: bool) -> Tuple[bool, ObjectMembers]`**: Deprecated (emits `RemovedInSphinx60Warning`). Calls `get_object_members()` from the importer module. If not `want_all`: if no members option, returns `(False, [])`; otherwise filters to only those in `self.options.members`. If `want_all` and `inherited_members`, returns all; else returns only directly-defined members.

**`filter_members(self, members: ObjectMembers, want_all: bool) -> List[Tuple[str, Any, bool]]`**: Filters the member list based on privacy, special methods, documentation status, and options. For each `(membername, member)` pair:
- Determines `isattr` (True if member is `INSTANCEATTR`).
- Gets docstring via `getdoc()`; checks for inherited docstrings (same as class doc).
- Checks ObjectMember's injected docstring.
- Determines `has_doc` and extracts `'private'`/`'public'` metadata from docstring. Default privacy: starts with `_`.
- Skips mocked objects (`__sphinx_mock__`).
- Excluded members → skip.
- Special dunder names: kept only if in `special_members` option, not `__doc__`, and not filtered inherited; keeps if has_doc or undoc_members.
- Documented attributes (in attr_docs): keep if private with proper options, else always keep.
- Private members: keep if has_doc/undoc_members and in private_members list, unless filtered inherited.
- Regular members: keep if `has_doc` or `undoc_members`, unless filtered inherited when `members is ALL`.
- Skipped ObjectMembers → skip.
- Emits `'autodoc-skip-member'` event; user can override the decision.
- Returns list of `(membername, member, isattr)` for kept members.

**`document_members(self, all_members: bool = False) -> None`**: Sets `self.env.temp_data['autodoc:module']` and `'autodoc:class'`. Determines `want_all`. Calls `get_object_members(want_all)`, then `filter_members()`. For each filtered member, finds documenter classes via `can_document_member()` on all registered documenters; picks the one with highest priority. Creates a new documenter instance for each. Sorts members via `sort_members()`. Generates documentation for each member recursively. Resets temp data.

**`sort_members(self, documenters: List[Tuple[Documenter, bool]], order: str) -> List[Tuple[Documenter, bool]]`**: 
- `'groupwise'`: sorts by `(member_order, name)`.
- `'bysource'`: uses `analyzer.tagorder` to sort by source position; falls back to no-op (relies on insertion order).
- Default (alphabetical): sorts by `name`.

**`generate(self, more_content: Optional[StringList] = None, real_modname: str = None, check_module: bool = False, all_members: bool = False) -> None`**: Main entry point. 
1. Calls `parse_name()`; if fails, logs warning and returns.
2. Calls `import_object()`; if fails, returns.
3. Determines `real_modname` from `get_real_modname()`.
4. Tries to create a `ModuleAnalyzer`; on failure sets `analyzer=None`, adds module file as dependency. Adds analyzer source name to filename set. If real_modname differs from guess, also adds the guessed module's analyzer source.
5. If `check_module`, calls `check_module()`; if false, returns.
6. Adds a blank line. Calls `format_signature()`, catching exceptions and logging warnings.
7. Calls `add_directive_header(sig)`. Adds another blank line. Increases indent by `content_indent`.
8. Calls `add_content(more_content)`.
9. Calls `document_members(all_members)`.

---

### Class: `ModuleDocumenter(Documenter)`

**Class attributes:**
- `objtype = 'module'`
- `content_indent = ''`
- `titles_allowed = True`
- `option_spec`: `'members': members_option, 'undoc-members': bool_option, 'noindex': bool_option, 'inherited-members': inherited_members_option, 'show-inheritance': bool_option, 'synopsis': identity, 'platform': identity, 'deprecated': bool_option, 'member-order': member_order_option, 'exclude-members': exclude_members_option, 'private-members': members_option, 'special-members': members_option, 'imported-members': bool_option, 'ignore-module-all': bool_option`

**Instance attributes:**
- `self.__all__` (Optional[Sequence[str]]) — set in `__init__`, populated from module's `__all__`.

**Methods:**

**`__init__(self, *args: Any) -> None`**: Calls super().__init__, then `merge_members_option(self.options)`. Initializes `self.__all__ = None`.

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Always returns `False` (doesn't document submodules automatically).

**`resolve_name(self, modname, parents, path, base) -> Tuple[str, List[str]]`**: Warns if `modname` is not None (`::` in automodule name doesn't make sense). Returns `((path or '') + base, [])`.

**`parse_name(self) -> bool`**: Calls super; warns if args/retann are given for automodule.

**`import_object(self, raiseerror=False) -> bool`**: Calls super. If not `ignore_module_all`, calls `inspect.getall(self.object)` to get `__all__`. Catches `AttributeError` (raises error on __all__) and `ValueError` (invalid __all__). Returns result of super call.

**`add_directive_header(self, sig: str) -> None`**: Calls super. Adds `:synopsis:`, `:platform:`, `:deprecated:` lines if options are set.

**`get_object_members(self, want_all: bool) -> Tuple[bool, ObjectMembers]`**: If `want_all`: calls `get_module_members(self.object)`. If no `__all__`, returns `(True, members)` (check module). Otherwise wraps each member as `ObjectMember(name, value)` with `skipped=True` if not in `__all__`, returning `(False, ret)`. If not `want_all`: iterates over `self.options.members`, gets each via `safe_getattr`, warns on missing attributes.

**`sort_members(self, documenters, order) -> List[Tuple[Documenter, bool]]`**: If `'bysource'` and `__all__` exists: first sorts alphabetically, then by `__all__` index (members in __all__ come first in that order). Otherwise delegates to super.

---

### Class: `ModuleLevelDocumenter(Documenter)`

**Methods:**

**`resolve_name(self, modname, parents, path, base) -> Tuple[str, List[str]]`**: If `modname` is None: uses `path.rstrip('.')` if given; else falls back to `self.env.temp_data.get('autodoc:module')`, then `self.env.ref_context.get('py:module')`. Returns `(modname, parents + [base])`.

---

### Class: `ClassLevelDocumenter(Documenter)`

**Methods:**

**`resolve_name(self, modname, parents, path, base) -> Tuple[str, List[str]]`**: If `modname` is None: uses `path.rstrip('.')` if given; else falls back to `self.env.temp_data.get('autodoc:class')`, then `self.env.ref_context.get('py:class')`. If still None, returns `(None, [])`. Otherwise splits on last `.` to get module and class. Falls back to autodoc:module / py:module for missing module name. Returns `(modname, parents + [base])`.

---

### Class: `DocstringSignatureMixin`

**Class attributes:**
- `_new_docstrings = None` (List[List[str]])
- `_signatures = None` (List[str])

**Methods:**

**`_find_signature(self, encoding=None) -> Tuple[str, str]`**: Deprecated `encoding` warning. Builds `valid_names`: the last element of `self.objpath`, plus `'__init__'` and all MRO class names if a ClassDocumenter. Calls `get_doc()` to get docstrings; copies into `_new_docstrings`. Iterates over docstring lines looking for a match against `py_ext_sig_re`. Handles multiline continuation (`\`). Checks that the matched base name is in `valid_names`. On match: re-prepares remaining docstring lines via `prepare_docstring()`, stores first signature as `(args, retann)`, subsequent ones into `_signatures` list. Returns `(args, retann)` or `None`.

**`get_doc(self, encoding=None, ignore=None) -> Optional[List[List[str]]]`**: Deprecated warnings for args. If `_new_docstrings` is not None, returns it; otherwise calls super().

**`format_signature(self, **kwargs: Any) -> str`**: If `args` is None and `autodoc_docstring_signature` config is True, calls `_find_signature()` to extract signature from docstring. Calls super's format_signature. If `_signatures` has entries, joins them with newlines after the base sig; otherwise returns just the base sig.

---

### Class: `DocstringStripSignatureMixin(DocstringSignatureMixin)`

**Methods:**

**`format_signature(self, **kwargs: Any) -> str`**: Same as parent but discards `_args` from `_find_signature()` result (only keeps `self.retann`). This prevents the signature from appearing in the directive header while still extracting return annotation. Calls super().

---

### Class: `FunctionDocumenter(DocstringSignatureMixin, ModuleLevelDocumenter)`

**Class attributes:**
- `objtype = 'function'`
- `member_order = 30`

**Methods:**

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Returns True if member is a function, builtin, or routine AND parent is a ModuleDocumenter.

**`format_args(self, **kwargs: Any) -> str`**: If `autodoc_typehints` in `('none', 'description')`, sets `show_annotation=False`. Emits `'autodoc-before-process-signature'` event with `(self.object, False)`. Gets signature via `inspect.signature()`, stringifies it. On TypeError: logs warning and returns None. On ValueError: returns empty string. If `strip_signature_backslash`, escapes backslashes.

**`document_members(self, all_members=False) -> None`**: No-op (functions have no members).

**`add_directive_header(self, sig: str) -> None`**: Calls super. Adds `:async:` if the object is a coroutine function.

**`format_signature(self, **kwargs: Any) -> str`**: Checks for overloaded functions in analyzer. If overloaded and typehints == 'signature', uses overload signatures; otherwise calls super's format_signature as base. For singledispatch functions: iterates over `registry.items()`, skips default (`object`) type, annotates first argument of each specialized function via `annotate_to_first_argument(func, typ)`, creates a temporary FunctionDocumenter to get its signature. For overloaded: evaluates each overload signature with globals and type aliases, stringifies it. Returns all signatures joined by newlines.

**`annotate_to_first_argument(self, func: Callable, typ: Type) -> None`**: Gets function's signature. If no parameters or first parameter already annotated, returns. Otherwise replaces the first parameter's annotation with `typ`, sets `func.__signature__`. Catches TypeError (built-in/extension types can't be modified).

---

### Class: `DecoratorDocumenter(FunctionDocumenter)`

**Class attributes:**
- `objtype = 'decorator'`
- `priority = -1` (lower than FunctionDocumenter)

**Methods:**

**`format_args(self, **kwargs: Any) -> Any`**: Calls super's format_args. If the result contains a comma, returns it; otherwise returns None (decorators with single argument are treated as functions).

---

### Module-Level Constants for Class Documenter

```python
_METACLASS_CALL_BLACKLIST = ['enum.EnumMeta.__call__']
_CLASS_NEW_BLACKLIST = ['typing.Generic.__new__']
```

---

### Class: `ClassDocumenter(DocstringSignatureMixin, ModuleLevelDocumenter)`

**Class attributes:**
- `objtype = 'class'`
- `member_order = 20`
- `option_spec`: `'members': members_option, 'undoc-members': bool_option, 'noindex': bool_option, 'inherited-members': inherited_members_option, 'show-inheritance': bool_option, 'member-order': member_order_option, 'exclude-members': exclude_members_option, 'private-members': members_option, 'special-members': members_option`
- `_signature_class = None` (Any)
- `_signature_method_name = None` (str)

**Instance attributes:**
- `self.doc_as_attr` — set in `import_object`; True if the class is documented under a different name than its own `__name__`.

**Methods:**

**`__init__(self, *args: Any) -> None`**: Calls super().__init__, then `merge_members_option(self.options)`.

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Returns True if member is a type (`isinstance(member, type)`).

**`import_object(self, raiseerror=False) -> bool`**: Calls super. If successful and object has `__name__`, sets `self.doc_as_attr = (objpath[-1] != self.object.__name__)`; else sets to True. Returns result of super call.

**`_get_signature(self) -> Tuple[Optional[Any], Optional[str], Optional[Signature]]`**: Inner helper `get_user_defined_function_or_method(obj, attr)` returns the attribute if it's a user-defined method/function (not builtin). Tries in order:
1. If object has `__signature__` (is a Signature instance), returns `(None, None, __signature__)`.
2. Checks metaclass for user-defined `__call__`; skips blacklisted ones; emits `'autodoc-before-process-signature'` event with `(call, True)`; tries `inspect.signature(call, bound_method=True)`. Returns `(type(self.object), '__call__', sig)` on success.
3. Checks object for user-defined `__new__`; same blacklist and process. Returns `(self.object, '__new__', sig)`.
4. Checks object for user-defined `__init__`; same process. Returns `(self.object, '__init__', sig)`.
5. Falls back to `inspect.signature(self.object, bound_method=False)` with event emission `(self.object, False)`. Returns `(None, None, sig)`.
6. If all fail (ValueError), returns `(None, None, None)`.

**`format_args(self, **kwargs: Any) -> str`**: If typehints in `('none', 'description')`, sets `show_annotation=False`. Calls `_get_signature()`. On TypeError: logs warning, returns None. If sig is None, returns None. Otherwise calls `stringify_signature(sig, show_return_annotation=False, **kwargs)`.

**`format_signature(self, **kwargs: Any) -> str`**: If `doc_as_attr`, returns empty string. Calls super's format_signature as base. Checks for overloaded signatures via `get_overloaded_signatures()`. If overloads exist and typehints == 'signature': evaluates each overload with globals/type aliases, strips first parameter (self), removes return annotation, stringifies. Otherwise uses the single sig. Returns all joined by newlines.

**`get_overloaded_signatures(self) -> List[Signature]`**: If `_signature_class` and `_signature_method_name` are set: iterates over MRO of signature class; for each, tries `ModuleAnalyzer.for_module(cls.__module__)`, analyzes it, looks up the qualified name in `analyzer.overloads`. Returns found overloads or empty list.

**`add_directive_header(self, sig: str) -> None`**: If `doc_as_attr`, sets `directivetype = 'attribute'`. Calls super. Adds `:final:` if in analyzer's finals. If not doc_as_attr and `show_inheritance`: adds `'Bases:'` line with restified base classes (from `__orig_bases__` or `__bases__`).

**`get_object_members(self, want_all: bool) -> Tuple[bool, ObjectMembers]`**: Inner `convert(m)` converts ClassAttribute to ObjectMember. Calls `get_class_members()`. If not `want_all`: returns empty if no members option; otherwise filters by `self.options.members`, warns on missing. If `inherited_members`, returns all converted members; else returns only those where `m.class_ == self.object` (directly defined).

**`get_doc(self, encoding=None, ignore=None) -> Optional[List[List[str]]]`**: Deprecated warnings. If `doc_as_attr`, returns None (no docstring for aliases). If `_new_docstrings` exists, returns it. Otherwise based on `config.autoclass_content`:
- `'class'`: only the class's own `__doc__`.
- `'both'`: class doc + `__init__` doc (or `__new__` doc if __init__ has default).
- `'init'`: only `__init__`/`__new__` doc.
Default `object.__init__.__doc__` and `object.__new__.__doc__` are treated as None. Returns `[prepare_docstring(...)]`.

**`add_content(self, more_content: Optional[StringList], no_docstring=False) -> None`**: If `doc_as_attr`, replaces content with `'alias of {restify(object)}'`. Calls super().

**`document_members(self, all_members=False) -> None`**: If `doc_as_attr`, returns (no members for aliases). Otherwise calls super.

**`generate(self, more_content=None, real_modname=None, check_module=False, all_members=False) -> None`**: Does NOT pass `real_modname` to super().generate() — uses the class's own `__module__` attribute instead so the analyzer finds source correctly. Calls `super().generate(more_content=more_content, check_module=check_module, all_members=all_members)`.

---

### Class: `ExceptionDocumenter(ClassDocumenter)`

**Class attributes:**
- `objtype = 'exception'`
- `member_order = 10`
- `priority = 10` (higher than ClassDocumenter)

**Methods:**

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Returns True if member is a type and subclass of `BaseException`.

---

### Class: `DataDocumenterMixinBase`

**Class attributes (type-annotated stubs):**
- `config = None` (Config)
- `env = None` (BuildEnvironment)
- `modname = None` (str)
- `parent = None` (Any)
- `object = None` (Any)
- `objpath = None` (List[str])

**Methods:**
- **`should_suppress_directive_header(self) -> bool`**: Returns False.
- **`should_suppress_value_header(self) -> bool`**: Returns False.
- **`update_content(self, more_content: StringList) -> None`**: No-op (pass).

---

### Class: `GenericAliasMixin(DataDocumenterMixinBase)`

**Methods:**

**`should_suppress_directive_header(self) -> bool`**: Returns True if object is a generic alias (`inspect.isgenericalias()`), or calls super.

**`update_content(self, more_content: StringList) -> None`**: If object is a generic alias, appends `'alias of {stringify_typehint(object)}'` and blank line to `more_content`. Calls super.

---

### Class: `NewTypeMixin(DataDocumenterMixinBase)`

**Methods:**

**`should_suppress_directive_header(self) -> bool`**: Returns True if object is a NewType, or calls super.

**`update_content(self, more_content: StringList) -> None`**: If object is a NewType, appends `'alias of {restify(object.__supertype__)}'` and blank line to `more_content`. Calls super.

---

### Class: `TypeVarMixin(DataDocumenterMixinBase)`

**Methods:**

**`should_suppress_directive_header(self) -> bool`**: Returns True if object is a TypeVar instance, or calls super.

**`get_doc(self, encoding=None, ignore=None) -> Optional[List[List[str]]]`**: Deprecated warning for `ignore`. If object is a TypeVar: if its doc differs from the default `TypeVar.__doc__`, returns parent's get_doc(); otherwise returns empty list (suppresses doc). Otherwise calls super.

**`update_content(self, more_content: StringList) -> None`**: If object is a TypeVar: builds attrs list with `repr(object.__name__)`, stringified constraints, and `'covariant=True'`/`'contravariant=True'` flags if set. Appends `'alias of TypeVar({attrs})'` and blank line to `more_content`. Calls super.

---

### Class: `UninitializedGlobalVariableMixin(DataDocumenterMixinBase)`

**Methods:**

**`import_object(self, raiseerror=False) -> bool`**: Tries super().import_object(raiseerror=True). On ImportError: tries to import the module and get type hints; if the objpath name is in annotations, sets `self.object = UNINITIALIZED_ATTR`, `self.parent = parent`, returns True. If still fails: re-raises or logs warning/returns False per raiseerror flag.

**`should_suppress_value_header(self) -> bool`**: Returns True if object is UNINITIALIZED_ATTR, or calls super.

**`get_doc(self, encoding=None, ignore=None) -> Optional[List[List[str]]]`**: If object is UNINITIALIZED_ATTR, returns empty list; otherwise calls super.

---

### Class: `DataDocumenter(GenericAliasMixin, NewTypeMixin, TypeVarMixin, UninitializedGlobalVariableMixin, ModuleLevelDocumenter)`

**Class attributes:**
- `objtype = 'data'`
- `member_order = 40`
- `priority = -10`
- `option_spec`: copy of `ModuleLevelDocumenter.option_spec` plus `'annotation': annotation_option`, `'no-value': bool_option`

**Methods:**

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Returns True if parent is a ModuleDocumenter and isattr is True.

**`update_annotations(self, parent: Any) -> None`**: Updates `parent.__annotations__` from `inspect.getannotations()`. Also merges annotations from the module analyzer for class-level attributes not already in annotations. Catches AttributeError.

**`import_object(self, raiseerror=False) -> bool`**: Calls super. If self.parent exists, calls `update_annotations(self.parent)`. Returns result of super call.

**`add_directive_header(self, sig: str) -> None`**: Calls super. If annotation is SUPPRESS or should_suppress_directive_header(), does nothing. Else if custom annotation option set, adds `:annotation:` line. Otherwise gets type hints from parent; if objpath name in annotations, adds `:type:` line. Tries to add `:value:` with `object_description(self.object)` unless no_value option or should_suppress_value_header() is True. Catches ValueError.

**`document_members(self, all_members=False) -> None`**: No-op (data has no members).

**`get_real_modname(self) -> str`**: Returns `self.parent.__module__` or `self.object.__module__`, falling back to `self.modname`.

**`add_content(self, more_content: Optional[StringList], no_docstring=False) -> None`**: If more_content is falsy, creates empty StringList. Calls `update_content(more_content)`. Then calls super().

---

### Class: `NewTypeDataDocumenter(DataDocumenter)`

**Class attributes:**
- `objtype = 'newtypedata'`
- `directivetype = 'data'`
- `priority = FunctionDocumenter.priority + 1`

**Methods:**

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Returns True if member is a NewType and isattr is True.

---

### Class: `MethodDocumenter(DocstringSignatureMixin, ClassLevelDocumenter)`

**Class attributes:**
- `objtype = 'method'`
- `directivetype = 'method'`
- `member_order = 50`
- `priority = 1` (higher than FunctionDocumenter)

**Methods:**

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Returns True if member is a routine and parent is NOT a ModuleDocumenter.

**`import_object(self, raiseerror=False) -> bool`**: Calls super. If successful: gets the object from `self.parent.__dict__.get(self.object_name)` (or self.object). If it's a classmethod or staticmethod, decrements `self.member_order` by 1 (to sort before ordinary methods). Returns result of super call.

**`format_args(self, **kwargs: Any) -> str`**: If typehints in `('none', 'description')`, sets `show_annotation=False`. Special case: if object is `object.__init__` and parent != object, returns `'()'`. For staticmethods: emits event with `(self.object, False)`, gets signature with `bound_method=False`. Otherwise: emits event with `(self.object, True)`, gets signature with `bound_method=True`. Stringifies. On TypeError: logs warning, returns None. On ValueError: returns empty string. Escapes backslashes if configured.

**`add_directive_header(self, sig: str) -> None`**: Calls super. Gets obj from parent.__dict__ or self.object. Adds `:abstractmethod:` if abstract, `:async:` if coroutine, `:classmethod:` if classmethod, `:staticmethod:` if staticmethod, `:final:` if in analyzer's finals.

**`document_members(self, all_members=False) -> None`**: No-op.

**`format_signature(self, **kwargs: Any) -> str`**: Checks for overloaded methods in analyzer. If overloaded and typehints == 'signature', uses overload signatures; otherwise calls super as base. For singledispatch methods: iterates over registry, skips default type, annotates second argument (after self), creates temporary MethodDocumenter to get signature. For overloaded: evaluates each overload, strips first parameter if not staticmethod, stringifies. Returns all joined by newlines.

**`annotate_to_first_argument(self, func: Callable, typ: Type) -> None`**: Gets function's signature. If only 1 parameter (just self), returns. Otherwise annotates the second parameter (`params[1]`) with `typ`, sets `func.__signature__`. Catches TypeError.

---

### Class: `NonDataDescriptorMixin(DataDocumenterMixinBase)`

**Methods:**

**`should_suppress_value_header(self) -> bool`**: Returns True if object is an attribute descriptor, or calls super (note: bug — calls `should_suppress_directive_header()` instead of `should_suppress_value_header()`, but this is the actual code).

**`get_doc(self, encoding=None, ignore=None) -> Optional[List[List[str]]]`**: If not an attribute descriptor, returns empty list (docstring probably wrong for non-data descriptors); otherwise calls super.

---

### Class: `SlotsMixin(DataDocumenterMixinBase)`

**Methods:**

**`isslotsattribute(self) -> bool`**: Calls `inspect.getslots(self.parent)`. If __slots__ exists and objpath[-1] is in it, returns True; else False. Catches AttributeError/ValueError/TypeError → returns False.

**`import_object(self, raiseerror=False) -> bool`**: Calls super. If isslotsattribute(), sets `self.object = SLOTSATTR`. Returns result of super call.

**`should_suppress_directive_header(self) -> bool`**: If object is SLOTSATTR, sets `self._datadescriptor = True`, returns True; else calls super.

**`get_doc(self, encoding=None, ignore=None) -> Optional[List[List[str]]]`**: If object is SLOTSATTR: gets __slots__ dict; if the slot name has a docstring in it, returns `[prepare_docstring(__slots__[name])]`; otherwise empty list. Catches errors and logs warning. Otherwise calls super.

---

### Class: `RuntimeInstanceAttributeMixin(DataDocumenterMixinBase)`

**Class attribute:**
- `RUNTIME_INSTANCE_ATTRIBUTE = object()` (sentinel)

**Methods:**

**`is_runtime_instance_attribute(self, parent: Any) -> bool`**: Returns True if `get_attribute_comment(parent, objpath[-1])` returns a non-empty result.

**`import_object(self, raiseerror=False) -> bool`**: Tries super().import_object(raiseerror=True). On ImportError: imports the parent class module, checks is_runtime_instance_attribute; if true, sets `self.object = RUNTIME_INSTANCE_ATTRIBUTE`, `self.parent = parent`, returns True. Otherwise re-raises or logs/returns False per raiseerror flag.

**`should_suppress_value_header(self) -> bool`**: Returns True if object is RUNTIME_INSTANCE_ATTRIBUTE, or calls super.

---

### Class: `UninitializedInstanceAttributeMixin(DataDocumenterMixinBase)`

**Methods:**

**`is_uninitialized_instance_attribute(self, parent: Any) -> bool`**: Gets type hints from parent; returns True if objpath[-1] is in annotations.

**`import_object(self, raiseerror=False) -> bool`**: Tries super().import_object(raiseerror=True). On ImportError: imports the parent class, checks is_uninitialized_instance_attribute; if true, sets `self.object = UNINITIALIZED_ATTR`, `self.parent = parent`, returns True. Otherwise re-raises or logs/returns False per raiseerror flag.

**`should_suppress_value_header(self) -> bool`**: Returns True if object is UNINITIALIZED_ATTR, or calls super.

---

### Class: `AttributeDocumenter(GenericAliasMixin, NewTypeMixin, SlotsMixin, TypeVarMixin, RuntimeInstanceAttributeMixin, UninitializedInstanceAttributeMixin, NonDataDescriptorMixin, DocstringStripSignatureMixin, ClassLevelDocumenter)`

**Class attributes:**
- `objtype = 'attribute'`
- `member_order = 60`
- `option_spec`: copy of `ModuleLevelDocumenter.option_spec` plus `'annotation': annotation_option`, `'no-value': bool_option`
- `priority = 10` (higher than MethodDocumenter)

**Methods:**

**`is_function_or_method(obj: Any) -> bool`**: Static method. Returns True if obj is a function, builtin, or method.

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Returns True if member is an attribute descriptor; OR if parent is not ModuleDocumenter AND member is not a routine AND member is not a type.

**`document_members(self, all_members=False) -> None`**: No-op.

**`isinstanceattribute(self) -> bool`**: Imports the parent class from modname/objpath[:-1]. Gets type hints; if objpath[-1] in annotations, sets `self.object = UNINITIALIZED_ATTR`, returns True. Catches ImportError → returns False.

**`update_annotations(self, parent: Any) -> None`**: Updates `parent.__annotations__` from `inspect.getannotations()`. Iterates over MRO of parent; for each class, gets module and qualname, creates ModuleAnalyzer, merges annotations from analyzer where classname matches qualname and attr not already in annotations. Catches AttributeError/PycodeError/TypeError.

**`import_object(self, raiseerror=False) -> bool`**: Calls super. If object is an enum attribute (`inspect.isenumattribute()`), replaces with `self.object.value`. If parent exists, calls `update_annotations(parent)`. Returns result of super call.

**`get_real_modname(self) -> str`**: Returns `parent.__module__` or `object.__module__`, falling back to `modname`.

**`add_directive_header(self, sig: str) -> None`**: Calls super. If annotation is SUPPRESS or should_suppress_directive_header(), does nothing. Else if custom annotation option set, adds `:annotation:` line. Otherwise gets type hints from parent; if objpath name in annotations, adds `:type:` line. Tries to add `:value:` unless no_value or should_suppress_value_header(). Catches ValueError.

**`get_attribute_comment(self, parent: Any, attrname: str) -> Optional[List[str]]`**: Iterates over MRO of parent; for each class, gets module/qualname, creates ModuleAnalyzer, looks up `(qualname, attrname)` in `analyzer.attr_docs`. Returns a copy of the doc lines if found. Catches errors → returns None.

**`get_doc(self, encoding=None, ignore=None) -> Optional[List[List[str]]]`**: Checks for attribute comment via get_attribute_comment; if found, returns it. Otherwise temporarily disables `autodoc_inherit_docstrings`, calls super().get_doc(), then restores the config value.

**`add_content(self, more_content: Optional[StringList], no_docstring=False) -> None`**: Sets `self.analyzer = None` to disable parent's attribute comment analysis. If more_content is None, creates empty StringList. Calls update_content(more_content). Then calls super().

---

### Class: `PropertyDocumenter(DocstringStripSignatureMixin, ClassLevelDocumenter)`

**Class attributes:**
- `objtype = 'property'`
- `directivetype = 'method'`
- `member_order = 60`
- `priority = AttributeDocumenter.priority + 1` (i.e., 11)

**Methods:**

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Returns True if member is a property and parent is a ClassDocumenter.

**`document_members(self, all_members=False) -> None`**: No-op.

**`get_real_modname(self) -> str`**: Returns `parent.__module__` or `object.__module__`, falling back to `modname`.

**`add_directive_header(self, sig: str) -> None`**: Calls super. Adds `:abstractmethod:` if abstract. Always adds `:property:` line.

---

### Class: `NewTypeAttributeDocumenter(AttributeDocumenter)`

**Class attributes:**
- `objtype = 'newvarattribute'`
- `directivetype = 'attribute'`
- `priority = MethodDocumenter.priority + 1` (i.e., 2)

**Methods:**

**`can_document_member(cls, member, membername, isattr, parent) -> bool`**: Returns True if parent is not a ModuleDocumenter and member is a NewType.

---

### Standalone Functions

**`get_documenters(app: Sphinx) -> Dict[str, Type[Documenter]]`**: Deprecated (emits `RemovedInSphinx50Warning`). Returns `app.registry.documenters`.

**`autodoc_attrgetter(app: Sphinx, obj: Any, name: str, *defargs: Any) -> Any`**: Iterates over `app.registry.autodoc_attrgettrs.items()` — for each `(typ, func)` pair where `isinstance(obj, typ)`, calls `func(obj, name, *defargs)`. If no match found, falls back to `safe_getattr(obj, name, *defargs)`.

**`migrate_autodoc_member_order(app: Sphinx, config: Config) -> None`**: If `config.autodoc_member_order == 'alphabetic'`, logs a warning and changes it to `'alphabetical'`.

---

### Compatibility Re-exports (from deprecated submodule)

```python
from sphinx.ext.autodoc.deprecated import DataDeclarationDocumenter  # NOQA
from sphinx.ext.autodoc.deprecated import GenericAliasDocumenter  # NOQA
from sphinx.ext.autodoc.deprecated import InstanceAttributeDocumenter  # NOQA
from sphinx.ext.autodoc.deprecated import SingledispatchFunctionDocumenter  # NOQA
from sphinx.ext.autodoc.deprecated import SingledispatchMethodDocumenter  # NOQA
from sphinx.ext.autodoc.deprecated import SlotsAttributeDocumenter  # NOQA
from sphinx.ext.autodoc.deprecated import TypeVarDocumenter  # NOQA
```

---

### Function: `setup(app: Sphinx) -> Dict[str, Any]`

Registers all documenters with the app:
- `app.add_autodocumenter(ModuleDocumenter)`
- `app.add_autodocumenter(ClassDocumenter)`
- `app.add_autodocumenter(ExceptionDocumenter)`
- `app.add_autodocumenter(DataDocumenter)`
- `app.add_autodocumenter(NewTypeDataDocumenter)`
- `app.add_autodocumenter(FunctionDocumenter)`
- `app.add_autodocumenter(DecoratorDocumenter)`
- `app.add_autodocumenter(MethodDocumenter)`
- `app.add_autodocumenter(AttributeDocumenter)`
- `app.add_autodocumenter(PropertyDocumenter)`
- `app.add_autodocumenter(NewTypeAttributeDocumenter)`

Registers config values:
- `'autoclass_content'`: default `'class'`, dynamic, ENUM('both', 'class', 'init')
- `'autodoc_member_order'`: default `'alphabetical'`, dynamic, ENUM('alphabetic', 'alphabetical', 'bysource', 'groupwise')
- `'autodoc_default_options'`: default `{}`, dynamic
- `'autodoc_docstring_signature'`: default `True`, dynamic
- `'autodoc_mock_imports'`: default `[]`, dynamic
- `'autodoc_typehints'`: default `"signature"`, dynamic, ENUM("signature", "description", "none")
- `'autodoc_type_aliases'`: default `{}`, dynamic
- `'autodoc_warningiserror'`: default `True`, dynamic
- `'autodoc_inherit_docstrings'`: default `True`, dynamic

Registers events:
- `'autodoc-before-process-signature'`
- `'autodoc-process-docstring'`
- `'autodoc-process-signature'`
- `'autodoc-skip-member'`

Connects `'config-inited'` → `migrate_autodoc_member_order` (priority 800).

Sets up extensions: `'sphinx.ext.autodoc.type_comment'`, `'sphinx.ext.autodoc.typehints'`.

Returns `{'version': sphinx.__display_version__, 'parallel_read_safe': True}`.

## sphinx/ext/autodoc/importer.py
Here is the complete natural-language specification of `sphinx/ext/autodoc/importer.py`:

---

## Module-Level Preamble

### Imports

```python
import importlib
import traceback
import warnings
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Tuple

from sphinx.deprecation import RemovedInSphinx40Warning, deprecated_alias
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.util import logging
from sphinx.util.inspect import (getannotations, getmro, getslots, isclass, isenumclass, safe_getattr)

if False:
    from typing import Type  # NOQA — for type annotation only; never executed at runtime
```

### Constants & Globals

- **`logger`**: `logging.getLogger(__name__)` — module-level logger.

---

## Code Objects

### `mangle(subject: Any, name: str) -> str`

Mangles a Python identifier using the standard name-mangling scheme for class-private attributes.

1. Attempts to check whether `subject` is a class via `isclass(subject)` and whether `name` starts with `"__"` but does not end with `"__"`.
2. If both conditions hold, returns `"_<subject.__name__><name>"` (the standard Python name-mangling prefix).
3. Catches any `AttributeError` during the check and falls through to step 4.
4. Returns `name` unchanged.

---

### `unmangle(subject: Any, name: str) -> Optional[str]`

Reverses name mangling for a given subject (class or object).

1. Attempts the following checks; catches any `AttributeError`:
   - If `subject` is a class and `name` does not end with `"__"`:
     - Computes `prefix = "_<subject.__name__>__"`. If `name` starts with this prefix, returns `name.replace(prefix, "__", 1)` (restoring the original dunder-prefixed name).
     - Otherwise, iterates over each class in `subject.__mro__`:
       - Computes `prefix = "_<cls.__name__>__"`. If `name` starts with this prefix, returns `None` — indicating the mangled attribute was defined in a parent class and cannot be unmangled to the current subject's namespace.
2. Returns `name` unchanged if no mangling pattern matched or an error occurred.

---

### `import_module(modname: str, warningiserror: bool = False) -> Any`

Imports a module by name using `importlib.import_module`, with controlled warning behavior and exception conversion.

1. Enters a `warnings.catch_warnings()` context that filters out all `ImportWarning` instances (silences them).
2. Within that, enters `logging.skip_warningiserror(not warningiserror)` — if `warningiserror` is `True`, warnings are treated as errors; otherwise they are skipped.
3. Calls `importlib.import_module(modname)` and returns the resulting module object.
4. Catches any `BaseException` (including `SystemExit`) and raises a new `ImportError(exc, traceback.format_exc())` chained from the original exception.

---

### `import_object(modname: str, objpath: List[str], objtype: str = '', attrgetter: Callable[[Any, str], Any] = safe_getattr, warningiserror: bool = False) -> Any`

Imports a nested object (module, class, function, attribute) given its module name and a path of attribute names. Returns `[module, parent, object_name, obj]`.

1. Logs a debug message indicating whether it is importing the module itself (`import <modname>`) or from-importing (`from <modname> import <objpath>`).
2. Enters a `try` block:
   - Initializes `module = None`, `exc_on_importing = None`, and copies `objpath` into a local list.
   - **Module resolution loop** (`while module is None`):
     - Attempts to import `modname` via `import_module(modname, warningiserror=warningiserror)`. On success, logs the result and exits the loop.
     - On `ImportError`: saves the exception as `exc_on_importing`, logs failure, then checks if `modname` contains a dot (`.`):
       - If yes: splits `modname` at the last dot via `rsplit('.', 1)`, pushes the rightmost segment onto the front of `objpath` (so it will be resolved as an attribute later), and retries with the parent module.
       - If no: re-raises the exception.
   - After obtaining the module, iterates over each element in `objpath`:
     - Sets `parent = obj`, logs the getattr operation.
     - Computes `mangled_name = mangle(obj, attrname)`.
     - Retrieves the attribute via `attrgetter(obj, mangled_name)` and assigns to `obj`.
     - Records `object_name = attrname`.
   - Returns `[module, parent, object_name, obj]`.
3. Catches `(AttributeError, ImportError)`:
   - If an `AttributeError` occurred but there was a prior `ImportError` from module resolution (`exc_on_importing`), replaces the current exception with that saved one.
   - Constructs an error message: if `objpath` is non-empty, `"autodoc: failed to import <objtype> '<joined objpath>' from module '<modname>'"`; otherwise `'autodoc: failed to import <objtype> <modname>'`.
   - If the exception is an `ImportError` (from `import_module`), extracts its args `(real_exc, traceback_msg)` and appends context:
     - If `real_exc` is a `SystemExit`: appends `"the module executes module level statement and it might call sys.exit()."`.
     - If `real_exc` is an `ImportError` with args: appends the first arg as the cause.
     - Otherwise: appends the traceback message.
   - If not an `ImportError`, appends `traceback.format_exc()`.
   - Logs the error and raises a new `ImportError(errmsg)` chained from the original exception.

---

### `get_module_members(module: Any) -> List[Tuple[str, Any]]`

Collects all members of a module as a list of `(name, value)` tuples, sorted by name.

1. Imports `INSTANCEATTR` from `sphinx.ext.autodoc`.
2. Iterates over every name returned by `dir(module)`:
   - Attempts to get the value via `safe_getattr(module, name, None)`. On success, stores `(name, value)` in a dict keyed by name. Catches `AttributeError` and skips.
3. Retrieves annotations from the module via `getannotations(module)`: for each annotation-only name not already present, adds `(name, INSTANCEATTR)`. Catches `AttributeError`.
4. Returns `sorted(list(members.values()))` — a sorted list of `(name, value)` tuples.

---

### `Attribute = NamedTuple('Attribute', [('name', str), ('directly_defined', bool), ('value', Any)])`

A named tuple with three fields:
- **`name`** (`str`): the attribute's name.
- **`directly_defined`** (`bool`): whether the attribute is defined directly on the subject (vs. inherited).
- **`value`** (`Any`): the attribute's value, or a sentinel like `INSTANCEATTR` / `SLOTSATTR`.

---

### `_getmro(obj: Any) -> Tuple["Type", ...]`

**Deprecated.** Issues a `RemovedInSphinx40Warning`, then delegates to `getmro(obj)` and returns the result.

---

### `_getannotations(obj: Any) -> Mapping[str, Any]`

**Deprecated.** Issues a `RemovedInSphinx40Warning`, then delegates to `getannotations(obj)` and returns the result.

---

### `get_object_members(subject: Any, objpath: List[str], attrgetter: Callable, analyzer: ModuleAnalyzer = None) -> Dict[str, Attribute]`

Collects members and attributes of a target object (class or other), returning a dict mapping name to `Attribute`.

1. Imports `INSTANCEATTR` from `sphinx.ext.autodoc`.
2. Retrieves the subject's own `__dict__` via `attrgetter(subject, '__dict__', {})`.
3. Initializes an empty `members: Dict[str, Attribute]`.
4. **Enum members** (if `isenumclass(subject)`):
   - For each `(name, value)` in `subject.__members__.items()`: if `name` is not already in `members`, adds `Attribute(name, True, value)`.
   - Gets the superclass as `subject.__mro__[1]`. For each name in `obj_dict` that is not in `superclass.__dict__`, gets its value via `safe_getattr(subject, name)` and adds `Attribute(name, True, value)`.
5. **`__slots__` members**:
   - Attempts to get slots via `getslots(subject)`. If non-empty:
     - Imports `SLOTSATTR` from `sphinx.ext.autodoc`.
     - For each slot name, adds `Attribute(name, True, SLOTSATTR)`.
   - Catches `(AttributeError, TypeError, ValueError)` and passes.
6. **Other members** (from `dir(subject)`):
   - For each name in `dir(subject)`: attempts to get its value via `attrgetter(subject, name)`, determines if it is directly defined (`name in obj_dict`), unmangles the name via `unmangle(subject, name)`. If the unmangled name is truthy and not already in `members`, adds `Attribute(name, directly_defined, value)`. Catches `AttributeError` and continues.
7. **Annotation-only members**: iterates over each class in `getmro(subject)` (index `i`). For each annotation name from `getannotations(cls)`: unmangles it; if truthy and not already present, adds `Attribute(name, i == 0, INSTANCEATTR)` — directly defined only for the first class in MRO. Catches `AttributeError`.
8. **Analyzer-provided instance attributes** (if `analyzer` is provided):
   - Builds a namespace string from `objpath` joined by dots. For each `(ns, name)` pair from `analyzer.find_attr_docs()`: if the namespace matches and the name is not already in `members`, adds `Attribute(name, True, INSTANCEATTR)`.
9. Returns `members`.

---

### `class ClassAttribute`

A data class representing a class attribute with its owning class context.

**`__init__(self, cls: Any, name: str, value: Any, docstring: Optional[str] = None)`**:
- Sets `self.class_ = cls` — the class that owns this attribute (or `None` if inherited).
- Sets `self.name = name`.
- Sets `self.value = value`.
- Sets `self.docstring = docstring` (optional, defaults to `None`).

---

### `get_class_members(subject: Any, objpath: List[str], attrgetter: Callable) -> Dict[str, ClassAttribute]`

Collects members and attributes of a target class, returning a dict mapping name to `ClassAttribute`.

1. Imports `INSTANCEATTR` from `sphinx.ext.autodoc`.
2. Retrieves the subject's own `__dict__` via `attrgetter(subject, '__dict__', {})`.
3. Initializes an empty `members: Dict[str, ClassAttribute]`.
4. **Enum members** (if `isenumclass(subject)`):
   - For each `(name, value)` in `subject.__members__.items()`: if not already present, adds `ClassAttribute(subject, name, value)`.
   - Gets the superclass as `subject.__mro__[1]`. For each name in `obj_dict` not in `superclass.__dict__`, gets its value via `safe_getattr(subject, name)` and adds `ClassAttribute(subject, name, value)`.
5. **`__slots__` members**:
   - Attempts to get slots via `getslots(subject)`. If non-empty:
     - Imports `SLOTSATTR` from `sphinx.ext.autodoc`.
     - For each `(name, docstring)` in `__slots__.items()`, adds `ClassAttribute(subject, name, SLOTSATTR, docstring)`.
   - Catches `(AttributeError, TypeError, ValueError)` and passes.
6. **Other members** (from `dir(subject)`):
   - For each name in `dir(subject)`: gets its value via `attrgetter(subject, name)`, unmangles it via `unmangle(subject, name)`. If the result is truthy and not already present: if the original name is in `obj_dict`, adds `ClassAttribute(subject, unmangled, value)` (directly defined); otherwise adds `ClassAttribute(None, unmangled, value)` (inherited). Catches `AttributeError` and continues.
7. **Per-MRO-class processing** (outer try/except for `AttributeError`):
   - For each class in `getmro(subject)`:
     - **Annotation-only members**: gets annotations via `getannotations(cls)`. For each annotation name: unmangles it; if truthy and not already present, adds `ClassAttribute(cls, name, INSTANCEATTR)`. Catches `AttributeError` per-class.
     - **Analyzer-provided instance attributes**: attempts to get `__module__` and `__qualname__` from the class via `safe_getattr`. Creates a `ModuleAnalyzer.for_module(modname)`, calls `analyzer.analyze()`, then iterates over `analyzer.attr_docs.items()`: for each `((ns, name), docstring)` where `ns == qualname` and the name is not already present, adds `ClassAttribute(cls, name, INSTANCEATTR, '\n'.join(docstring))`. Catches `(AttributeError, PycodeError)`.
8. Returns `members`.

---

### Post-module re-exports (deprecated aliases)

After all definitions, the module imports from `sphinx.ext.autodoc.mock`:

```python
from sphinx.ext.autodoc.mock import (MockFinder, MockLoader, _MockModule, _MockObject, mock)  # NOQA
```

Then registers deprecated aliases via `deprecated_alias()`, mapping these five names (`_MockModule`, `_MockObject`, `MockFinder`, `MockLoader`, `mock`) from the old location `sphinx.ext.autodoc.importer` to their new locations in `sphinx.ext.autodoc.mock`, with `RemovedInSphinx40Warning` as the deprecation warning class.