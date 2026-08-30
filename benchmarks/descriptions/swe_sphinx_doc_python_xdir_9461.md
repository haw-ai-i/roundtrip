## sphinx/domains/python.py
Now I have all the details. Here is the complete specification:

---

# Module Specification: `sphinx/domains/python.py`

## 1. Module-Level Preamble

### Imports

```python
import builtins
import inspect
import re
import sys
import typing
import warnings
from inspect import Parameter
from typing import Any, Dict, Iterable, Iterator, List, NamedTuple, Optional, Tuple, Type, cast

from docutils import nodes
from docutils.nodes import Element, Node
from docutils.parsers.rst import directives
from docutils.parsers.rst.states import Inliner

from sphinx import addnodes
from sphinx.addnodes import desc_signature, pending_xref, pending_xref_condition
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.deprecation import RemovedInSphinx50Warning
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, Index, IndexEntry, ObjType
from sphinx.environment import BuildEnvironment
from sphinx.locale import _, __
from sphinx.pycode.ast import ast
from sphinx.pycode.ast import parse as ast_parse
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docfields import Field, GroupedField, TypedField
from sphinx.util.docutils import SphinxDirective
from sphinx.util.inspect import signature_from_str
from sphinx.util.nodes import find_pending_xref_condition, make_id, make_refnode
from sphinx.util.typing import OptionSpec, TextlikeNode
```

### Constants & Globals

- **`logger`**: `logging.getLogger(__name__)` — module logger.
- **`py_sig_re`**: Compiled regex (`re.VERBOSE`) matching Python signatures with four capture groups: `(prefix,)`, `(name)`, `(arglist?)`, `(retann?)`. Pattern: `^([\w.]*\.)?(\w+)\s*(?:\(\s*(.*)\s*\)(?:\s*->\s*(.*))?)?$`
- **`pairindextypes`**: Dict mapping string keys to localized strings:
  - `'module'` → `_('module')`, `'keyword'` → `_('keyword')`, `'operator'` → `_('operator')`, `'object'` → `_('object')`, `'exception'` → `_('exception')`, `'statement'` → `_('statement')`, `'builtin'` → `_('built-in function')`.

### NamedTuples

- **`ObjectEntry(NamedTuple)`**: Fields: `docname: str`, `node_id: str`, `objtype: str`, `aliased: bool`.
- **`ModuleEntry(NamedTuple)`**: Fields: `docname: str`, `node_id: str`, `synopsis: str`, `platform: str`, `deprecated: bool`.

---

## 2. Free Functions

### `type_to_xref(text: str, env: BuildEnvironment = None) -> addnodes.pending_xref`

Converts a type string to a cross-reference node. If `text == 'None'`, sets `reftype='obj'`; otherwise `reftype='class'`. If `env` is provided, passes `'py:module'` and `'py:class'` from `env.ref_context` as kwargs. If `env.config.python_use_unqualified_type_names` is true, creates two `pending_xref_condition` nodes — one with the short name (last segment after `.`) for resolved condition, one with full text for unresolved; otherwise a single `nodes.Text(text)` child. Returns a `pending_xref` node with `refdomain='py'`, `reftype`, `reftarget=text`.

### `_parse_annotation(annotation: str, env: BuildEnvironment = None) -> List[Node]`

Parses a type annotation string into a list of docutils nodes using the AST module. Emits a `RemovedInSphinx50Warning` if `env is None`. Internally defines recursive `unparse(node: ast.AST) -> List[Node]` handling these AST node types:
- `ast.Attribute`: returns `[nodes.Text("%s.%s" % (unparse(value)[0], attr))]`.
- `ast.BinOp`: concatenates unparse of left, op, right.
- `ast.BitOr`: returns `[Text(' '), desc_sig_punctuation('|'), Text(' ')]`.
- `ast.Constant` (Python 3.8+): if value is `Ellipsis`, returns `[desc_sig_punctuation("...")]`; else `[nodes.Text(value)]`.
- `ast.Expr`: delegates to unparse of its value.
- `ast.Index`: delegates to unparse of its value.
- `ast.List`: wraps elements in `[...]` with `, ` separators (pops trailing comma).
- `ast.Module`: flattens body via `sum()`.
- `ast.Name`: returns `[nodes.Text(id)]`.
- `ast.Subscript`: concatenates unparse(value) + `[` + unparse(slice) + `]`.
- `ast.Tuple`: if elements exist, joins with `, `; else returns `()` punctuation.
- Fallback for Python < 3.8: `ast.Ellipsis` → `"..."`, `ast.NameConstant` → text value. Any other node type raises `SyntaxError`.

After unparsing the AST tree, iterates result nodes: any `nodes.Text` with stripped content is replaced by a `type_to_xref()` call. On `SyntaxError`, returns `[type_to_xref(annotation, env)]`.

### `_parse_arglist(arglist: str, env: BuildEnvironment = None) -> addnodes.desc_parameterlist`

Parses an argument list string using AST-based signature parsing via `signature_from_str('(%s)' % arglist)`. Creates a `desc_parameterlist`, iterates parameters in order. Tracks `last_kind` to insert separators:
- Before first non-POSITIONAL_ONLY after POSITIONAL_ONLY: inserts `/` operator (PEP-570).
- Before KEYWORD_ONLY when last was POSITIONAL_OR_KEYWORD, POSITIONAL_ONLY, or None: inserts `*` operator (PEP-3102).

For each parameter: creates a `desc_parameter` node. For VAR_POSITIONAL (`*args`): adds `*` operator + name. For VAR_KEYWORD (`**kwargs`): adds `**` operator + name. Otherwise just the name. If annotation is not empty: appends `:` punctuation, space, and parsed annotation children via `_parse_annotation`. If default is not empty: if annotation also present, adds space + `=` + space; else just `=`; then an `inline` node with class `'default_value'`. After all params, if last kind was POSITIONAL_ONLY, appends `/` operator. Returns the parameterlist.

### `_pseudo_parse_arglist(signode: desc_signature, arglist: str) -> None`

Fallback parser for argument lists using bracket-based nesting. Creates a `desc_parameterlist` and a stack starting with it. Splits on commas; for each argument, processes leading `[` (pushes `desc_optional`, adds to parent), leading `]` (pops stack), trailing `]` (counts closes), trailing `[` (counts opens). Non-empty arguments become `desc_parameter` nodes added to `stack[-1]`. After processing all args, pushes open brackets onto the stack and pops closing ones. If stack depth ≠ 1 at end or any exception occurs, discards the partial list and creates a single `desc_parameter(arglist, arglist)` inside a fresh parameterlist appended to signode. On success, appends paramlist to signode.

### `PyXRefMixin.make_xref(self, rolename: str, domain: str, target: str, innernode: Type[TextlikeNode] = nodes.emphasis, contnode: Node = None, env: BuildEnvironment = None, inliner: Inliner = None, location: Node = None) -> Node`

Calls `super().make_xref()` with `inliner=None, location=None`. Sets `'refspecific' = True` on result. Copies `'py:module'` and `'py:class'` from `env.ref_context`. If target starts with `'.'`: sets prefix to `'.'`, strips it from reftarget; display text is the remainder (without dot). If target starts with `'~'`: sets prefix to `'~'`, strips it; display text is last segment after `.`. Modifies first Text node in result's traverse to show the display text. If target has no special prefix and `env.config.python_use_unqualified_type_names` is true: extracts shortname (last dot-segment), creates two `pending_xref_condition` nodes — resolved with shortname, unresolved with full children. Returns result.

### `PyXRefMixin.make_xrefs(self, rolename: str, domain: str, target: str, innernode: Type[TextlikeNode] = nodes.emphasis, contnode: Node = None, env: BuildEnvironment = None, inliner: Inliner = None, location: Node = None) -> List[Node]`

Splits `target` by delimiter regex `\s*[\[\]\(\),](?:\s+or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.`. For each non-empty sub-target: if it matches a delimiter, appends the innernode (or contnode); otherwise calls `make_xref()` for that sub-target. If contnode's text equals target, splits contnode per sub-target. Returns list of nodes.

### `type_to_xref` (standalone) — already described above.

### `filter_meta_fields(app: Sphinx, domain: str, objtype: str, content: Element) -> None`

If `domain != 'py'`, returns immediately. Iterates children of `content`; for each `nodes.field_list`, iterates fields; if a field's body text is `'meta'` or starts with `'meta '`, removes that field from the list and breaks.

### `builtin_resolver(app: Sphinx, env: BuildEnvironment, node: pending_xref, contnode: Element) -> Element`

Handles missing references for built-in types to suppress nitpicky warnings. If `node.refdomain != 'py'`, returns None. If `reftype in ('class', 'obj')` and `reftarget == 'None'`, returns contnode. If `reftype in ('class', 'exc')`: checks if `getattr(builtins, reftarget)` is a class via `inspect.isclass()`, or if it's a typing module type (strips `'typing.'` prefix, checks membership in `typing.__all__`). Returns contnode on match. Otherwise returns None.

### `setup(app: Sphinx) -> Dict[str, Any]`

Registers the Python domain: calls `app.setup_extension('sphinx.directives')`, `app.add_domain(PythonDomain)`, adds config value `'python_use_unqualified_type_names'` (default False, scope 'env'), connects `'object-description-transform'` to `filter_meta_fields`, connects `'missing-reference'` to `builtin_resolver` with priority 900. Returns `{'version': 'builtin', 'env_version': 3, 'parallel_read_safe': True, 'parallel_write_safe': True}`.

---

## 3. Classes

### `class PyXrefMixin`

Base mixin providing cross-reference generation for Python types. See functions above (`make_xref`, `make_xrefs`). Sets `'refspecific' = True` on all generated xrefs; handles `'.'` prefix (namespace-specific search) and `'~'` prefix (display short name). Supports `python_use_unqualified_type_names` config to show short names by default.

### `class PyField(PyXrefMixin, Field)`

Overrides `make_xref`: if `rolename == 'class'` and `target == 'None'`, changes rolename to `'obj'` (since None is not a type). Calls parent's `make_xref`.

### `class PyGroupedField(PyXrefMixin, GroupedField)`

No overrides; inherits both mixins.

### `class PyTypedField(PyXrefMixin, TypedField)`

Same as `PyField`: maps `'class'` + `'None'` → `'obj'` rolename before delegating to parent.

---

### `class PyObject(ObjectDescription[Tuple[str, str]])`

**Base class for all Python object descriptions.**

**Class attributes:**
- `option_spec: OptionSpec = {'noindex': directives.flag, 'noindexentry': directives.flag, 'module': directives.unchanged, 'canonical': directives.unchanged, 'annotation': directives.unchanged}`
- `doc_field_types`: List of doc field definitions — `PyTypedField('parameter')` for Parameters (names: param/parameter/arg/argument/keyword/kwarg/kwparam), `PyTypedField('variable')` for Variables (var/ivar/cvar), `PyGroupedField('exceptions')` for Raises, `Field('returnvalue')` for Returns, `PyField('returntype')` for Return type.
- `allow_nesting = False`

**Methods:**

- **`get_signature_prefix(sig: str) -> str`**: Returns empty string. Overridden by subclasses to return prefixes like `'async '`, `'classmethod'`, etc.
- **`needs_arglist() -> bool`**: Returns `False`. Overridden to return `True` for callables needing `( )`.
- **`handle_signature(sig: str, signode: desc_signature) -> Tuple[str, str]`**: Core signature parsing. Matches `sig` against `py_sig_re`; raises `ValueError` on no match. Extracts `(prefix, name, arglist, retann)`. Determines `modname` from options or `ref_context['py:module']`, `classname` from `ref_context['py:class']`. Computes `fullname`:
  - If classname exists and prefix matches/starts-with classname: `fullname = prefix + name`; strips classname from prefix.
  - If classname exists but prefix differs: `fullname = classname + '.' + prefix + name`.
  - If classname exists but no prefix: `fullname = classname + '.' + name`.
  - If no classname and prefix: `classname = prefix.rstrip('.')`, `fullname = prefix + name`, `add_module = True`.
  - If no classname, no prefix: `classname = ''`, `fullname = name`, `add_module = True`.
  
  Sets signode attributes `'module'`, `'class'`, `'fullname'`. Adds signature prefix via `desc_annotation` if non-empty. Adds module/class prefix via `desc_addname` (either explicit prefix, or modname + dot if `add_module` and config says so). Adds name via `desc_name`. Parses arglist: tries `_parse_arglist`; falls back to `_pseudo_parse_arglist` on `SyntaxError` or `NotImplementedError` (with warning). If no arglist but `needs_arglist()`, adds empty `desc_parameterlist`. Adds return annotation via `desc_returns` if present. Adds custom annotation option text if provided. Returns `(fullname, prefix)`.

- **`get_index_text(modname: str, name: Tuple[str, str]) -> str`**: Raises `NotImplementedError`; must be overridden by subclasses.
- **`add_target_and_index(name_cls: Tuple[str, str], sig: str, signode: desc_signature) -> None`**: Computes `modname`, builds `fullname`. Generates `node_id = make_id(...)`. Appends node_id to signode's `'ids'`; also appends old-style `fullname` as id if different and not already in document. Notes explicit target. Calls `domain.note_object(fullname, objtype, node_id)`. If `'canonical'` option present, notes canonical name as aliased. If no `'noindexentry'`, calls `get_index_text()` and appends single index entry.
- **`before_content() -> None`**: Handles nesting. If `self.names` has entries, gets `(fullname, name_prefix)` from last. If `allow_nesting`: sets `ref_context['py:class'] = fullname` and pushes to `'py:classes'` list. Else if `name_prefix` exists: strips dots, sets as class. If `'module'` option present: saves current module to `'py:modules'` stack, updates `ref_context['py:module']`.
- **`after_content() -> None`**: Reverses nesting. Gets `'py:classes'` list; if `allow_nesting`, pops one class. Sets `ref_context['py:class']` to remaining top or None. If `'module'` option present, restores previous module from stack (or pops it entirely).

---

### `class PyFunction(PyObject)`

**Description of a function.**

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'async': directives.flag`.
- **`get_signature_prefix(sig: str) -> str`**: Returns `'async '` if `'async'` in options, else `''`.
- **`needs_arglist() -> bool`**: Returns `True`.
- **`add_target_and_index(name_cls, sig, signode)`**: Calls parent. If no `'noindexentry'`, gets modname and node_id. Creates index entry: if modname exists → single entry `'%s() (in module %s)'`; else → pair entry with builtin type + name.
- **`get_index_text(modname, name_cls) -> str`**: Returns `None` (index text handled in `add_target_and_index`).

---

### `class PyDecoratorFunction(PyFunction)`

**Description of a decorator function.**

- **`run() -> List[Node]`**: Sets `self.name = 'py:function'`, calls parent `run()`.
- **`handle_signature(sig, signode) -> Tuple[str, str]`**: Calls parent; inserts `'@'` as `desc_addname` at position 0 of signode.
- **`needs_arglist() -> bool`**: Returns `False`.

---

### `class PyVariable(PyObject)`

**Description of a variable.**

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'type': directives.unchanged`, `'value': directives.unchanged`.
- **`handle_signature(sig, signode) -> Tuple[str, str]`**: Calls parent; if `'type'` option present, parses annotation and appends as `desc_annotation` with `: ` prefix; if `'value'` option present, appends as `desc_annotation` with ` = ` prefix.
- **`get_index_text(modname, name_cls) -> str`**: If modname → `'%s (in module %s)'`; else → `'%s (built-in variable)'`.

---

### `class PyClasslike(PyObject)`

**Description of a class-like object (classes, interfaces, exceptions).**

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'final': directives.flag`.
- **`allow_nesting = True`**.
- **`get_signature_prefix(sig: str) -> str`**: If `'final'` in options → `'final %s '` (where `%s` is `self.objtype`); else `'%s '` (objtype).
- **`get_index_text(modname, name_cls) -> str`**: If objtype == 'class': no modname → `'%s (built-in class)'`; with modname → `'%s (class in %s)'`. If objtype == 'exception': returns just the name. Else: empty string.

---

### `class PyMethod(PyObject)`

**Description of a method.**

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'abstractmethod': directives.flag`, `'async': directives.flag`, `'classmethod': directives.flag`, `'final': directives.flag`, `'property': directives.flag`, `'staticmethod': directives.flag`.
- **`needs_arglist() -> bool`**: Returns `False` if `'property'` in options; else `True`.
- **`get_signature_prefix(sig: str) -> str`**: Builds prefix list from present flags: `'final'`, `'abstract'`, `'async'`, `'classmethod'`, `'property'`, `'staticmethod'`; joins with space + trailing space. Returns empty string if none.
- **`get_index_text(modname, name_cls) -> str`**: Tries `rsplit('.', 1)` to get `(clsname, methname)`. If fails (ValueError): if modname → `'%s() (in module %s)'`; else → `'%s()'`. If succeeds: with `'classmethod'` → `'%s() (%s class method)'`; with `'property'` → `'%s() (%s property)'`; with `'staticmethod'` → `'%s() (%s static method)'`; else → `'%s() (%s method)'`. If modname and config adds module names, prepends modname to clsname.

---

### `class PyClassMethod(PyMethod)`

**Description of a classmethod.**

- **`option_spec`**: Copies `PyObject.option_spec` (not parent's).
- **`run() -> List[Node]`**: Sets `self.name = 'py:method'`, sets `'classmethod': True` in options, calls parent `run()`.

---

### `class PyStaticMethod(PyMethod)`

**Description of a staticmethod.**

- **`option_spec`**: Copies `PyObject.option_spec`.
- **`run() -> List[Node]`**: Sets `self.name = 'py:method'`, sets `'staticmethod': True` in options, calls parent `run()`.

---

### `class PyDecoratorMethod(PyMethod)`

**Description of a decorator method.**

- **`run() -> List[Node]`**: Sets `self.name = 'py:method'`, calls parent `run()`.
- **`handle_signature(sig, signode) -> Tuple[str, str]`**: Calls parent; inserts `'@'` as `desc_addname` at position 0.
- **`needs_arglist() -> bool`**: Returns `False`.

---

### `class PyAttribute(PyObject)`

**Description of an attribute.**

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'type': directives.unchanged`, `'value': directives.unchanged`.
- **`handle_signature(sig, signode) -> Tuple[str, str]`**: Calls parent; if `'type'` option: parses annotation and appends as `desc_annotation` with `: ` prefix; if `'value'` option: appends as `desc_annotation` with ` = ` prefix.
- **`get_index_text(modname, name_cls) -> str`**: Tries `rsplit('.', 1)` for `(clsname, attrname)`. If fails: if modname → `'%s (in module %s)'`; else → just the name. If succeeds and modname + config adds names: prepends modname to clsname. Returns `'%s (%s attribute)'` with attrname and clsname.

---

### `class PyProperty(PyObject)`

**Description of a property.**

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'abstractmethod': directives.flag`, `'type': directives.unchanged`.
- **`handle_signature(sig, signode) -> Tuple[str, str]`**: Calls parent; if `'type'` option: appends as `desc_annotation` with `: ` prefix (no annotation parsing).
- **`get_signature_prefix(sig: str) -> str`**: Starts list `['property']`; if `'abstractmethod'` in options, inserts `'abstract'` at position 0. Returns joined + trailing space.
- **`get_index_text(modname, name_cls) -> str`**: Same logic as PyAttribute — rsplit for clsname/attrname; with modname → `'%s (in module %s)'`; else just name; if both: `'%s (%s property)'`.

---

### `class PyDecoratorMixin`

**Deprecated mixin for decorator directives.** Emits `RemovedInSphinx50Warning` on use.

- **`handle_signature(sig, signode) -> Tuple[str, str]`**: Warns about deprecation (checks MRO for `'DirectiveAdapter'` to determine warning scope). Calls parent's `handle_signature`; inserts `'@'` as `desc_addname` at position 0.
- **`needs_arglist() -> bool`**: Returns `False`.

---

### `class PyModule(SphinxDirective)`

**Directive to mark description of a new module.**

- **Class attributes**: `has_content = False`, `required_arguments = 1`, `optional_arguments = 0`, `final_argument_whitespace = False`.
- **`option_spec: OptionSpec = {'platform': lambda x: x, 'synopsis': lambda x: x, 'noindex': directives.flag, 'deprecated': directives.flag}`**.
- **`run() -> List[Node]`**: Gets domain. Extracts `modname` from first argument (stripped). If not `'noindex'`: generates `node_id = make_id(...)`, creates `nodes.target` with `ismod=True`; also generates old-style id via `make_old_id()` and appends if different; notes explicit target; calls `domain.note_module(modname, node_id, synopsis, platform, deprecated)` and `domain.note_object(modname, 'module', node_id)`. Creates index entry: pair type with `pairindextypes['module']` + modname. Returns `[target, inode]`.
- **`make_old_id(name: str) -> str`**: Returns `'module-%s' % name`.

---

### `class PyCurrentModule(SphinxDirective)`

**Directive to set the current module context without creating an index entry.**

- **Class attributes**: `has_content = False`, `required_arguments = 1`, `optional_arguments = 0`, `final_argument_whitespace = False`, `option_spec: OptionSpec = {}`.
- **`run() -> List[Node]`**: Extracts modname (stripped). If `'None'`: pops `'py:module'` from ref_context. Else: sets `ref_context['py:module'] = modname`. Returns empty list.

---

### `class PyXRefRole(XRefRole)`

**Cross-reference role for Python objects.**

- **`process_link(env, refnode, has_explicit_title, title, target) -> Tuple[str, str]`**: Sets `'py:module'` and `'py:class'` on refnode from `env.ref_context`. If no explicit title: strips leading `'.'` from title (only meaningful for target), strips leading `'~'` from target. If title starts with `'~'`: removes tilde, finds last dot, truncates title to last segment only. If target starts with `'.'`: strips the dot and sets `refnode['refspecific'] = True`. Returns `(title, target)`.

---

### `class PythonModuleIndex(Index)`

**Index subclass providing the Python Module Index.**

- **Class attributes**: `name = 'modindex'`, `localname = _('Python Module Index')`, `shortname = _('modules')`.
- **`generate(docnames: Iterable[str] = None) -> Tuple[List[Tuple[str, List[IndexEntry]]], bool]`**: Gets ignore prefixes from config (`modindex_common_prefix`), sorted by length descending. Sorts modules by lowercase name. For each module (skipping if `docnames` given and docname not in it): strips ignored prefix; if entire name stripped, restores original. Groups entries by first character of (possibly-stripped) modname (lowercased). Determines if submodule or toplevel: splits on `.`, checks if package != modname. If submodule and previous module was the same package: converts last entry's subtype to 1 (group head). If submodule without parent in list: adds dummy entry with subtype 1. Sets subtype 2 for submodules, 0 for top-level. Creates `IndexEntry` with qualifier `'Deprecated'` if deprecated. Tracks `num_toplevels`. After all modules: collapse = `(total_modules - toplevels) < toplevels`. Sorts content by first letter. Returns `(sorted_content, collapse)`.

---

### `class PythonDomain(Domain)`

**Python language domain.**

- **Class attributes**:
  - `name = 'py'`, `label = 'Python'`
  - `object_types: Dict[str, ObjType]`: Maps object type names to ObjTypes with display labels and search roles — `'function'` → (func, obj), `'data'` → (data, obj), `'class'` → (class, exc, obj), `'exception'` → (exc, class, obj), `'method'` → (meth, obj), `'classmethod'` → (meth, obj), `'staticmethod'` → (meth, obj), `'attribute'` → (attr, obj), `'property'` → (attr, _prop, obj), `'module'` → (mod, obj).
  - `directives: Dict[str, type]`: Maps directive names to classes — function→PyFunction, data→PyVariable, class→PyClasslike, exception→PyClasslike, method→PyMethod, classmethod→PyClassMethod, staticmethod→PyStaticMethod, attribute→PyAttribute, property→PyProperty, module→PyModule, currentmodule→PyCurrentModule, decorator→PyDecoratorFunction, decoratormethod→PyDecoratorMethod.
  - `roles: Dict[str, XRefRole]`: data→XRefRole(), exc→XRefRole(), func→XRefRole(fix_parens=True), class→XRefRole(), const→XRefRole(), attr→XRefRole(), meth→XRefRole(fix_parens=True), mod→XRefRole(), obj→XRefRole().
  - `initial_data: Dict[str, Dict[str, Tuple[Any]]]`: `'objects': {}`, `'modules': {}`.
  - `indices = [PythonModuleIndex]`

- **Properties**:
  - **`objects -> Dict[str, ObjectEntry]`**: Returns `self.data.setdefault('objects', {})`.
  - **`modules -> Dict[str, ModuleEntry]`**: Returns `self.data.setdefault('modules', {})`.

- **Methods:**
  - **`note_object(name: str, objtype: str, node_id: str, aliased: bool = False, location: Any = None) -> None`**: If name already exists: checks aliasing rules — if existing is aliased and new is not, overrides; if existing is not aliased and new is aliased, returns (keeps original); otherwise logs warning about duplicate. Sets `self.objects[name] = ObjectEntry(...)`.
  - **`note_module(name: str, node_id: str, synopsis: str, platform: str, deprecated: bool) -> None`**: Sets `self.modules[name] = ModuleEntry(...)`.
  - **`clear_doc(docname: str) -> None`**: Deletes all objects and modules whose docname matches.
  - **`merge_domaindata(docnames: List[str], otherdata: Dict) -> None`**: Copies objects/modules from otherdata where their docname is in the given list.
  - **`find_obj(env, modname: str, classname: str, name: str, type: str, searchmode: int = 0) -> List[Tuple[str, ObjectEntry]]`**: Strips trailing `'()'` from name. Returns empty for blank name. In searchmode 1 (refspecific): if no type specified, uses all objtypes; else uses role's objtypes. Tries exact qualified match (`modname.classname.name`), then module-qualified (`modname.name`), then bare name. If none found, does fuzzy search: finds entries ending with `'.name'`. In searchmode 0 (exact): tries bare name, classname.name, modname.name, modname.classname.name. Returns list of `(name, entry)` tuples.
  - **`resolve_xref(env, fromdocname, builder, type, target, node, contnode) -> Optional[Element]`**: Gets `py:module`, `py:class` from node; searchmode = 1 if `'refspecific'` else 0. Calls `find_obj()`. Falls back to `'meth'` for `'attr'` type and vice versa (for property compatibility). If multiple matches, prefers non-aliased; logs warning if still ambiguous. For modules: calls `_make_module_refnode()`. Otherwise: resolves pending_xref condition or uses contnode; returns `make_refnode(...)`.
  - **`resolve_any_xref(env, fromdocname, builder, target, node, contnode) -> List[Tuple[str, Element]]`**: Always searchmode 1. For each match: modules → `_make_module_refnode()` with role `'py:mod'`; others → `make_refnode()` with role from `role_for_objtype()`. Returns list of `(role, element)` tuples.
  - **`_make_module_refnode(builder, fromdocname, name, contnode) -> Element`**: Gets module entry; builds title as `name + synopsis (if any) + ' (deprecated)' (if deprecated) + ' (' + platform + ')'`. Returns `make_refnode(...)`.
  - **`get_objects() -> Iterator[Tuple[str, str, str, str, str, int]]`**: Yields module entries first. For objects: aliased → priority -1; non-aliased → priority 1 (full-text searchable). Skips modules (already yielded). Each yield: `(refname, display_name, objtype, docname, node_id, priority)`.
  - **`get_full_qualified_name(node: Element) -> Optional[str]`**: Joins `py:module`, `py:class`, and `reftarget` with dots, filtering empty strings.

---

## sphinx/ext/autodoc/__init__.py
Now I have read every section of the file. Here is the complete natural-language specification:

---

# Module Specification: `sphinx/ext/autodoc/__init__.py` (2784 lines)

## 1. Module-Level Preamble

### Imports

```python
import re
import warnings
from inspect import Parameter, Signature
from types import ModuleType
from typing import (TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional, Sequence,
                    Set, Tuple, Type, TypeVar, Union)

from docutils.statemachine import StringList

import sphinx
from sphinx.application import Sphinx
from sphinx.config import ENUM, Config
from sphinx.deprecation import RemovedInSphinx50Warning, RemovedInSphinx60Warning
from sphinx.environment import BuildEnvironment
from sphinx.ext.autodoc.importer import (get_class_members, get_object_members, import_module,
                                         import_object)
from sphinx.ext.autodoc.mock import ismock, mock, undecorate
from sphinx.locale import _, __
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.util import inspect, logging
from sphinx.util.docstrings import prepare_docstring, separate_metadata
from sphinx.util.inspect import (evaluate_signature, getdoc, object_description, safe_getattr,
                                 stringify_signature)
from sphinx.util.typing import OptionSpec, get_type_hints, restify
from sphinx.util.typing import stringify as stringify_typehint

if TYPE_CHECKING:
    from sphinx.ext.autodoc.directive import DocumenterBridge
```

### Constants & Globals

- **`logger`** — `logging.getLogger(__name__)`
- **`MethodDescriptorType`** — `type(type.__subclasses__)`; a type alias for method descriptor types.
- **`py_ext_sig_re`** — Compiled regex (`re.VERBOSE`) matching Python extended signatures: optional explicit module name (`::`), optional module/class path, required name, optional parenthesized arguments with optional return annotation (`->`). Groups: `(explicit_modname, path, base, args, retann)`.
- **`special_member_re`** — Compiled regex `r'^__\S+__$'`; matches dunder names.
- **`ALL`** — Singleton `_All()` instance; a special value for `:*-members:` that always returns `True` from `__contains__` and has a no-op `append`.
- **`EMPTY`** — Singleton `_Empty()` instance; a special value for `:exclude-members:` that always returns `False` from `__contains__`.
- **`UNINITIALIZED_ATTR`** — Sentinel object (`object()`) marking annotation-only (PEP-526) attributes.
- **`INSTANCEATTR`** — Sentinel object (`object()`) marking runtime instance attributes defined in `__init__()`.
- **`SLOTSATTR`** — Sentinel object (`object()`) marking `__slots__` attributes.
- **`SUPPRESS`** — Sentinel object (`object()`) for suppressing value display via the `:annotation:` option.

### Module-Level Functions (Option Parsers)

- **`identity(x)`** → `x`. Identity function used as a passthrough option parser.
- **`members_option(arg)`** → `Union[object, List[str]]`. Converts `:members:` directive arg: if `None`/`True`, returns `ALL`; if `False`, returns `None`; otherwise splits comma-separated string into stripped list.
- **`members_set_option(arg)`** → `Union[object, Set[str]]`. Deprecated (warns `RemovedInSphinx50Warning`). If `None`, returns `ALL`; else splits into set of stripped strings.
- **`exclude_members_option(arg)`** → `Union[object, Set[str]]`. If `None`/`True`, returns `EMPTY`; otherwise splits comma-separated string into set of stripped strings.
- **`inherited_members_option(arg)`** → `Union[object, Set[str]]`. If `None`/`True`, returns `'object'`; else returns `arg` unchanged.
- **`member_order_option(arg)`** → `Optional[str]`. Validates against `('alphabetical', 'bysource', 'groupwise')`; raises `ValueError` otherwise; `None`/`True` returns `None`.
- **`class_doc_from_option(arg)`** → `Optional[str]`. Validates against `('both', 'class', 'init')`; raises `ValueError` otherwise.
- **`annotation_option(arg)`** → `Any`. If `None`/`True`, returns `SUPPRESS`; else returns `arg`.
- **`bool_option(arg)`** → `bool`. Always returns `True` (for flag options).
- **`merge_special_members_option(options: Dict)`** → `None`. Deprecated. Merges `special-members` into `members`: if members is ALL, no-op; if members has entries, appends special-members not already present; else replaces members with special-members.
- **`merge_members_option(options: Dict)`** → `None`. Merges `private-members` and `special-members` (if not ALL/None) into the `members` list, deduplicating. No-op if members is ALL.

### Event Listener Factories

- **`cut_lines(pre: int, post: int = 0, what: str = None)`** → `Callable`. Returns a listener for `autodoc-process-docstring` that deletes the first `pre` lines and last `post` lines of docstrings (filtered by `what`). Ensures trailing blank line.
- **`between(marker: str, what: Sequence[str] = None, keepempty: bool = False, exclude: bool = False)`** → `Callable`. Returns a listener that keeps or excludes (if `exclude=True`) lines between those matching the `marker` regex. If result would be empty and `keepempty=False`, restores original lines. Ensures trailing blank line.

### Classes at Module Level

- **`Options(dict)`** — A dict/attribute hybrid returning `None` on missing keys via `__getattr__`. Key lookup translates underscores to hyphens (`name.replace('_', '-')`).
- **`ObjectMember(tuple)`** — Immutable tuple subclass of `(name, obj)`. Additional attributes: `__name__` (str), `object` (Any), `docstring` (Optional[str]), `skipped` (bool), `class_` (Any). Created via `__new__` returning a 2-tuple.

---

## 2. Code Objects

### Class `Documenter` (base class, lines 296–976)

**Inheritance:** None (root of documenter hierarchy)

**Class attributes:**
- `objtype = 'object'` — directive name suffix (`auto<objtype>`) and default generated directive.
- `content_indent = '   '` — indentation for content lines.
- `priority = 0` — priority for member resolution when multiple documenters claim a member.
- `member_order = 0` — ordering key for groupwise sorting.
- `titles_allowed = False` — whether generated content may contain titles.
- `option_spec: OptionSpec = {'noindex': bool_option}`

**Instance attributes (set in `__init__`):**
- `directive: DocumenterBridge`, `config: Config`, `env: BuildEnvironment`, `options: dict`, `name: str`, `indent: str`
- `modname: str = None`, `module: ModuleType = None`, `objpath: List[str] = None`, `fullname: str = None`
- `args: str = None`, `retann: str = None`
- `object: Any = None`, `object_name: str = None`
- `parent: Any = None`, `analyzer: ModuleAnalyzer = None`

**Methods:**

1. **`get_attr(obj, name, *defargs)`** → `Any`. Delegates to `autodoc_attrgetter(self.env.app, obj, name, *defargs)`.

2. **`can_document_member(member, membername, isattr, parent)`** (classmethod). Returns `NotImplementedError`; must be overridden in subclasses.

3. **`__init__(directive, name, indent='')`**. Initializes all instance attributes from `directive`, sets defaults to `None`. Calls `merge_members_option(self.options)`.

4. **`documenters`** (property) → `Dict[str, Type[Documenter]]`. Returns `self.env.app.registry.documenters`.

5. **`add_line(line, source, *lineno)`**. Appends indented line to `self.directive.result`; blank lines are added without indentation.

6. **`resolve_name(modname, parents, path, base)`** → `Tuple[str, List[str]]`. Abstract; must be overridden. Returns `(module_name, [attr_chain])`.

7. **`parse_name()`** → `bool`. Parses `self.name` using `py_ext_sig_re`, extracts `(explicit_modname, path, base, args, retann)`. Resolves module via `resolve_name()`, sets `modname`, `objpath`, `fullname`, `args`, `retann`. Returns `True` on success. Logs warning and returns `False` on parse failure or unresolved module. Uses `mock(self.config.autodoc_mock_imports)` context during resolution.

8. **`import_object(raiseerror=False)`** → `bool`. Imports the object via `import_object(modname, objpath, objtype, attrgetter=get_attr)`, sets `module`, `parent`, `object_name`, `object`. If object is a mock, undecorates it. Returns `True` on success; logs warning and returns `False` on ImportError (unless `raiseerror=True`).

9. **`get_real_modname()`** → `str`. Returns `self.object.__module__` or falls back to `self.modname`.

10. **`check_module()`** → `bool`. If `options.imported_members`, returns `True`. Otherwise checks that the object's `__module__` matches `self.modname`; returns `False` if different.

11. **`format_args(**kwargs)`** → `Optional[str]`. Returns `None` (abstract; overridden in subclasses).

12. **`format_name()`** → `str`. Joins `objpath` with dots, or falls back to `modname`.

13. **`_call_format_args(**kwargs)`** → `str`. Tries `self.format_args(**kwargs)`, catches `TypeError` and retries without arguments for backward compatibility.

14. **`format_signature(**kwargs)`** → `str`. If explicit `args` is set, wraps in parens. Otherwise calls `_call_format_args()`, extracts args/retann via regex if combined. Emits `autodoc-process-signature` event; uses first result if any handler returns a value. Returns formatted string or empty string.

15. **`add_directive_header(sig)`**. Gets domain (`'py'`) and directive name. Adds `.. <domain>:<directive>:: <name><sig>` with multi-line support (continuation lines indented). Adds `:noindex:` if set, adds `:module: <modname>` if objpath is non-empty.

16. **`get_doc(ignore=None)`** → `Optional[List[List[str]]]`. Retrieves docstring via `getdoc()`, prepares with `prepare_docstring()`. Returns list of line lists or empty list. Warns on deprecated `ignore` arg.

17. **`process_doc(docstrings)`** → `Iterator[str]`. For each docstring, emits `autodoc-process-docstring` event via app if available; ensures trailing blank line; yields lines.

18. **`get_sourcename()`** → `str`. Constructs source name from object's `__module__.__qualname__` or `fullname`; prepends analyzer's `srcname` if present.

19. **`add_content(more_content, no_docstring=False)`**. If analyzer exists and objpath has a key in `attr_docs`, extracts attribute docstring and processes it (setting `no_docstring=True`). Otherwise calls `get_doc()` and processes docstrings. Then appends any additional content from `more_content`. Warns on deprecated `no_docstring` arg.

20. **`get_object_members(want_all)`** → `Tuple[bool, ObjectMembers]`. Deprecated (warns `RemovedInSphinx60Warning`). Calls `get_object_members()` from importer module. If not want_all and no members option, returns empty list; if specific members listed, selects them; else filters by directly-defined or inherited based on options.

21. **`filter_members(members, want_all)`** → `List[Tuple[str, Any, bool]]`. Filters member list:
    - Inner function `is_filtered_inherited_member(name, obj)`: checks if member belongs to a specific super class listed in `options.inherited_members`.
    - For each member: determines `isattr` (INSTANCEATTR or attr_docs key → True). Gets docstring via `getdoc()`, strips inherited docs. Separates metadata from doc. Determines privacy (`_` prefix, or "private"/"public" metadata). Applies filtering rules: mocked objects always pass; excluded members skipped; special dunder methods only if in `special_members`; attributes with comments kept; private members only if in `private_members` and have docs or undoc-members set; regular members kept if documented or undoc-members. Forced-skipped members (not in `__all__`) are dropped. Emits `autodoc-skip-member` event for user override. Returns list of `(name, member, isattr)`.

22. **`document_members(all_members=False)`**. Sets temp data (`autodoc:module`, `autodoc:class`). Determines if all members wanted. Calls `get_object_members()`. For each filtered member, finds applicable documenter classes via `can_document_member()`, sorts by priority, creates the highest-priority documenter, collects them. Sorts via `sort_members()` using `member_order` config. Generates each member documenter recursively. Resets temp data.

23. **`sort_members(documenters, order)`** → list. If `'groupwise'`: sort by `(member_order, name)`. If `'bysource'`: uses analyzer's `tagorder` for source-order sorting (falls back to discovery order). Else alphabetical by name.

24. **`generate(more_content=None, real_modname=None, check_module=False, all_members=False)`**. Main entry point:
    - Calls `parse_name()`; returns on failure with warning.
    - Calls `import_object()`; returns on failure.
    - Sets `real_modname` from `get_real_modname()`.
    - Creates `ModuleAnalyzer`; adds dependency tracking.
    - If `check_module`, calls `check_module()` and returns if false.
    - Adds blank line, formats signature (with error handling), adds directive header.
    - Increases indent, adds content, documents members.

---

### Class `ModuleDocumenter(Documenter)` (lines 979–1120)

**Class attributes:** `objtype = 'module'`, `content_indent = ''`, `titles_allowed = True`

**option_spec:** `{members: members_option, undoc-members: bool_option, noindex: bool_option, inherited-members: inherited_members_option, show-inheritance: bool_option, synopsis: identity, platform: identity, deprecated: bool_option, member-order: member_order_option, exclude-members: exclude_members_option, private-members: members_option, special-members: members_option, imported-members: bool_option, ignore-module-all: bool_option}`

**Methods:**
- **`__init__(*args)`**. Calls super; calls `merge_members_option(self.options)`. Sets `self.__all__: Optional[Sequence[str]] = None`.
- **`can_document_member(member, membername, isattr, parent)`** → `False`. Never documents submodules.
- **`resolve_name(modname, parents, path, base)`**. Warns if explicit modname given; returns `(path + base, [])`.
- **`parse_name()`**. Calls super; warns if args/retann provided for automodule.
- **`import_object(raiseerror=False)`**. Calls super; calls `inspect.getall(self.object)` to populate `self.__all__`; catches ValueError from invalid `__all__`.
- **`add_directive_header(sig)`**. Calls super; adds `:synopsis:`, `:platform:`, `:deprecated:` if set.
- **`get_module_members()`** → `Dict[str, ObjectMember]`. Iterates `dir(self.object)`, gets each value (undecorating mocks), collects from analyzer's attr_docs. Also adds annotation-only members as `INSTANCEATTR`. Returns dict of name→ObjectMember.
- **`get_object_members(want_all)`**. If want_all and no `__all__`, returns all members with `members_check_module=True`; if `__all__` set, marks non-`__all__` members as skipped; if specific members listed, selects them (warning on missing).
- **`sort_members(documenters, order)`**. For `'bysource'` with `__all__`: sorts alphabetically first, then by `__all__` index.

---

### Class `ModuleLevelDocumenter(Documenter)` (lines 1123–1141)

**Methods:**
- **`resolve_name(modname, parents, path, base)`**. If modname is None: uses `path.rstrip('.')`, or falls back to `env.temp_data['autodoc:module']`, then `env.ref_context['py:module']`. Returns `(modname, parents + [base])`.

---

### Class `ClassLevelDocumenter(Documenter)` (lines 1144–1174)

**Methods:**
- **`resolve_name(modname, parents, path, base)`**. If modname is None: uses `path.rstrip('.')`, or falls back to `env.temp_data['autodoc:class']` then `env.ref_context['py:class']`. If still None, returns `(None, [])`. Parses `mod_cls.rpartition('.')` for module and class. Returns `(modname, parents + [base])`.

---

### Class `DocstringSignatureMixin` (lines 1177–1252)

**Class attributes:** `_new_docstrings: List[List[str]] = None`, `_signatures: List[str] = None`

**Methods:**
- **`_find_signature()`** → `Tuple[Optional[str], Optional[str]]`. Builds valid names from objpath[-1]; for ClassDocumenter also includes `'__init__'` and all MRO class names. Calls `get_doc()`, scans docstring lines for signature match via `py_ext_sig_re`. On first match, re-prepares remaining docstring lines (stripping matched line), stores in `_new_docstrings`, returns `(args, retann)`. Subsequent matches appended to `_signatures` as `"(<args>) -> <retann>"`.
- **`get_doc(ignore=None)`**. Returns `_new_docstrings` if set; else calls super.
- **`format_signature(**kwargs)`**. If args is None and `autodoc_docstring_signature` enabled, calls `_find_signature()` to populate args/retann. Calls super for base signature. Appends any collected `_signatures`.

---

### Class `DocstringStripSignatureMixin(DocstringSignatureMixin)` (lines 1255–1270)

**Methods:**
- **`format_signature(**kwargs)`**. Same as parent but discards `_args` from `_find_signature()`, only setting `self.retann`. This strips the signature from docstrings while keeping return annotation.

---

### Class `FunctionDocumenter(DocstringSignatureMixin, ModuleLevelDocumenter)` (lines 1273–1392)

**Class attributes:** `objtype = 'function'`, `member_order = 30`

**Methods:**
- **`can_document_member(member, membername, isattr, parent)`**. Returns True if function/builtin, or routine with ModuleDocumenter parent.
- **`format_args(**kwargs)`**. If typehints disabled, hides annotations. Emits `autodoc-before-process-signature`. Gets signature via `inspect.signature()`, stringifies it. Escapes backslashes if configured. Catches TypeError (returns None) and ValueError (returns empty).
- **`document_members(all_members=False)`** → no-op (functions have no members to document).
- **`add_directive_header(sig)`**. Calls super; adds `:async:` for coroutine functions.
- **`format_signature(**kwargs)`**. Checks for overloaded function signatures in analyzer. If overloaded and typehints enabled, uses overload signatures instead of implementation. For singledispatch functions, appends signatures for each dispatched type (annotating first argument). Merges default values from actual into overloads via `merge_default_value()`. Evaluates and stringifies each overload signature.
- **`merge_default_value(actual_sig, overload_sig)`** → `Signature`. Replaces `'...'` defaults in overload with actual parameter defaults.
- **`annotate_to_first_argument(func, typ)`** → `Optional[Callable]`. Gets func's signature; if first param has no annotation, annotates it and returns a dummy function with updated signature (for singledispatch display).

---

### Class `DecoratorDocumenter(FunctionDocumenter)` (lines 1395–1409)

**Class attributes:** `objtype = 'decorator'`, `priority = -1` (lower than FunctionDocumenter)

**Methods:**
- **`format_args(**kwargs)`**. Calls super; returns None if no comma in args (decorators must have at least one parameter besides self).

---

### Module-Level Constants for ClassDocumenter

- **`_METACLASS_CALL_BLACKLIST = ['enum.EnumMeta.__call__']`** — Methods whose metaclass `__call__` signature should be hidden.
- **`_CLASS_NEW_BLACKLIST = ['typing.Generic.__new__']`** — Methods whose `__new__` signature is a pass-through and should be hidden.

---

### Class `ClassDocumenter(DocstringSignatureMixin, ModuleLevelDocumenter)` (lines 1426–1766)

**Class attributes:** `objtype = 'class'`, `member_order = 20`

**option_spec:** `{members: members_option, undoc-members: bool_option, noindex: bool_option, inherited-members: inherited_members_option, show-inheritance: bool_option, member-order: member_order_option, exclude-members: exclude_members_option, private-members: members_option, special-members: members_option, class-doc-from: class_doc_from_option}`

**Instance attributes:** `_signature_class`, `_signature_method_name` (set in `_get_signature`)

**Methods:**
- **`__init__(*args)`**. If `autodoc_class_signature == 'separated'`, adds `'__new__', '__init__'` to special-members. Calls `merge_members_option()`.
- **`can_document_member(member, membername, isattr, parent)`** → `isinstance(member, type)`.
- **`import_object(raiseerror=False)`**. Calls super; sets `self.doc_as_attr = True` if class is documented under a different name (objpath[-1] != object.__name__).
- **`_get_signature()`** → `Tuple[Optional[Any], Optional[str], Optional[Signature]]`. Checks in order: `__signature__` attribute, metaclass `__call__`, class `__new__`, class `__init__`, fallback to inspect. For each user-defined method candidate, checks blacklist, emits `autodoc-before-process-signature`, gets signature via `inspect.signature()`. Returns `(class_obj, method_name, sig)` or `(None, None, sig)` for fallback, or `(None, None, None)`.
- **`format_args(**kwargs)`**. Calls `_get_signature()`; stringifies with `show_return_annotation=False`. Catches TypeError.
- **`format_signature(**kwargs)`**. If `doc_as_attr`, returns empty. If `autodoc_class_signature == 'separated'`, returns empty. Otherwise calls super, then checks for overloaded signatures via `get_overloaded_signatures()`. For overloads, strips first parameter (self), removes return annotation, stringifies each.
- **`get_overloaded_signatures()`** → `List[Signature]`. Walks MRO of `_signature_class`, tries ModuleAnalyzer for overload info at `<class_qualname>.<method_name>`.
- **`get_canonical_fullname()`** → `Optional[str]`. Returns `<module>.<qualname>` if valid (no `<locals>`).
- **`add_directive_header(sig)`**. If `doc_as_attr`, sets `directivetype = 'attribute'`. Calls super. Adds `:final:` if in analyzer's finals. Adds `:canonical:` if class is aliased. Adds `Bases:` line with restified base classes (from `__orig_bases__` or `__bases__`) if `show_inheritance` set; emits `autodoc-process-bases` event.
- **`get_object_members(want_all)`**. Calls `get_class_members()`. If not want_all, selects specific members. If inherited_members, returns all; else filters to only those defined on this class (`m.class_ == self.object`).
- **`get_doc(ignore=None)`**. If `doc_as_attr`, gets variable comment and returns empty or None. Otherwise checks `_new_docstrings`. Gets docstring from class `__doc__`; if `class-doc-from` is `'both'` or `'init'`, also includes `__init__` (or `__new__`) docstring, skipping default object docs.
- **`get_variable_comment()`** → `Optional[List[str]]`. Looks up comment in analyzer's attr_docs for the class-level variable.
- **`add_content(more_content, no_docstring=False)`**. If `doc_as_attr` and no variable comment, adds "alias of <restified object>" content. Calls super.
- **`document_members(all_members=False)`**. No-op if `doc_as_attr`; else calls super.
- **`generate(...)`**. Does not pass `real_modname` to parent (uses class's own `__module__`).

---

### Class `ExceptionDocumenter(ClassDocumenter)` (lines 1769–1782)

**Class attributes:** `objtype = 'exception'`, `member_order = 10`, `priority = 10`

**Methods:**
- **`can_document_member(member, membername, isattr, parent)`** → `isinstance(member, type) and issubclass(member, BaseException)`.

---

### Class `DataDocumenterMixinBase` (lines 1785–1804)

**Class attributes:** `config`, `env`, `modname`, `parent`, `object`, `objpath` — all typed as class-level annotations with default `None`.

**Methods:**
- **`should_suppress_directive_header()`** → `False`.
- **`should_suppress_value_header()`** → `False`.
- **`update_content(more_content)`** → no-op.

---

### Class `GenericAliasMixin(DataDocumenterMixinBase)` (lines 1807–1822)

**Methods:**
- **`should_suppress_directive_header()`**. Returns True if object is a GenericAlias.
- **`update_content(more_content)`**. If GenericAlias, appends "alias of <restified type>" to content.

---

### Class `NewTypeMixin(DataDocumenterMixinBase)` (lines 1825–1841)

**Methods:**
- **`should_suppress_directive_header()`**. Returns True if object is a NewType.
- **`update_content(more_content)`**. If NewType, appends "alias of <restified supertype>" to content.

---

### Class `TypeVarMixin(DataDocumenterMixinBase)` (lines 1844–1883)

**Methods:**
- **`should_suppress_directive_header()`**. Returns True if object is a TypeVar.
- **`get_doc(ignore=None)`**. If TypeVar with custom docstring, returns super's doc; else returns empty list (TypeVars with default `object.__doc__` are suppressed).
- **`update_content(more_content)`**. If TypeVar, appends "alias of TypeVar(<name>, <constraints>, bound=..., covariant=True, contravariant=True)" to content.

---

### Class `UninitializedGlobalVariableMixin(DataDocumenterMixinBase)` (lines 1886–1924)

**Methods:**
- **`import_object(raiseerror=False)`**. Tries super with `raiseerror=True`; on ImportError, tries importing module and checking type hints for the attribute name. If found, sets `self.object = UNINITIALIZED_ATTR`. Falls back to normal error handling.
- **`should_suppress_value_header()`**. Returns True if object is UNINITIALIZED_ATTR.
- **`get_doc(ignore=None)`**. Returns empty list if UNINITIALIZED_ATTR; else super.

---

### Class `DataDocumenter(GenericAliasMixin, NewTypeMixin, TypeVarMixin, UninitializedGlobalVariableMixin, ModuleLevelDocumenter)` (lines 1927–2039)

**Class attributes:** `objtype = 'data'`, `member_order = 40`, `priority = -10`

**option_spec:** Inherits from ModuleLevelDocumenter plus `"annotation": annotation_option`, `"no-value": bool_option`.

**Methods:**
- **`can_document_member(member, membername, isattr, parent)`** → `isinstance(parent, ModuleDocumenter) and isattr`.
- **`update_annotations(parent)`**. Updates `parent.__annotations__` from `inspect.getannotations()` plus analyzer annotations.
- **`import_object(raiseerror=False)`**. Calls super; updates annotations on parent if present.
- **`should_suppress_value_header()`**. Checks mixins first, then parses docstring metadata for `'hide-value'`.
- **`add_directive_header(sig)`**. Calls super. If annotation suppressed or should_suppress_directive_header, no-op. Else adds `:annotation:` from option or type hint (`:type:`). Adds `:value:` with object description unless suppressed by options/no_value/hide-value metadata. Catches ValueError.
- **`document_members(all_members=False)`** → no-op.
- **`get_real_modname()`**. Returns parent's or object's `__module__`, fallback to modname.
- **`get_module_comment(attrname)`**. Looks up comment in analyzer for module-level attribute.
- **`get_doc(ignore=None)`**. Checks for module-level docstring-comment first; else super.
- **`add_content(more_content, no_docstring=False)`**. Disables analyzer (self.analyzer = None). Calls `update_content()`, then super.

---

### Class `NewTypeDataDocumenter(DataDocumenter)` (lines 2042–2057)

**Class attributes:** `objtype = 'newtypedata'`, `directivetype = 'data'`, `priority = FunctionDocumenter.priority + 1`

**Methods:**
- **`can_document_member(member, membername, isattr, parent)`** → `inspect.isNewType(member) and isattr`.

---

### Class `MethodDocumenter(DocstringSignatureMixin, ClassLevelDocumenter)` (lines 2060–2261)

**Class attributes:** `objtype = 'method'`, `directivetype = 'method'`, `member_order = 50`, `priority = 1`

**Methods:**
- **`can_document_member(member, membername, isattr, parent)`** → `inspect.isroutine(member) and not isinstance(parent, ModuleDocumenter)`.
- **`import_object(raiseerror=False)`**. Calls super; checks if classmethod/staticmethod via `parent.__dict__`; adjusts `member_order` downward for class/static methods.
- **`format_args(**kwargs)`**. If typehints disabled, hides annotations. Special case: `object.__init__` shown as `()`. For staticmethods, uses `bound_method=False`; else `bound_method=True`. Emits `autodoc-before-process-signature`. Escapes backslashes. Catches TypeError (returns None) and ValueError (returns empty).
- **`add_directive_header(sig)`**. Calls super; adds `:abstractmethod:`, `:async:`, `:classmethod:`, `:staticmethod:`, `:final:` as appropriate.
- **`document_members(all_members=False)`** → no-op.
- **`format_signature(**kwargs)`**. Checks for overloaded methods in analyzer. If overloaded, uses overload signatures (stripping first parameter for non-staticmethods). For singledispatch methods, appends dispatched type signatures via `annotate_to_first_argument()`. Merges defaults from actual into overloads.
- **`merge_default_value(actual_sig, overload_sig)`** → `Signature`. Same as FunctionDocumenter's version.
- **`annotate_to_first_argument(func, typ)`**. Similar to FunctionDocumenter but annotates the second parameter (index 1) since first is `self`.
- **`get_doc(ignore=None)`**. For `__init__`: gets docstring, strips default object.__init__.__doc__, returns prepared or empty. For `__new__`: same logic with object.__new__.__doc__. Else calls super.

---

### Class `NonDataDescriptorMixin(DataDocumenterMixinBase)` (lines 2264–2292)

**Methods:**
- **`import_object(raiseerror=False)`**. Calls super; sets `self.non_data_descriptor = True` if object is not an attribute descriptor.
- **`should_suppress_value_header()`**. Returns True unless non-data descriptor and directive header suppressed.
- **`get_doc(ignore=None)`**. If non-data descriptor, returns None (docstring likely wrong); else super.

---

### Class `SlotsMixin(DataDocumenterMixinBase)` (lines 2295–2339)

**Methods:**
- **`isslotsattribute()`** → `bool`. Checks if attribute name is in parent's `__slots__`.
- **`import_object(raiseerror=False)`**. Calls super; if slots attribute, sets `self.object = SLOTSATTR`.
- **`should_suppress_directive_header()`**. Returns True if object is SLOTSATTR (sets `_datadescriptor=True`).
- **`get_doc(ignore=None)`**. If SLOTSATTR, returns docstring from `__slots__` dict; else super.

---

### Class `RuntimeInstanceAttributeMixin(DataDocumenterMixinBase)` (lines 2342–2419)

**Class attribute:** `RUNTIME_INSTANCE_ATTRIBUTE = object()`

**Methods:**
- **`is_runtime_instance_attribute(parent)`** → `bool`. Checks for doc-comment or runtime instance attribute via tagorder.
- **`is_runtime_instance_attribute_not_commented(parent)`** → `Optional[bool]`. Walks MRO, checks analyzer's tagorder for `<qualname>.<attrname>`.
- **`import_object(raiseerror=False)`**. Tries super with raiseerror=True; on ImportError, imports parent class and checks if it's a runtime instance attribute. Sets object to RUNTIME_INSTANCE_ATTRIBUTE.
- **`should_suppress_value_header()`**. Returns True for RUNTIME_INSTANCE_ATTRIBUTE.
- **`get_doc(ignore=None)`**. If RUNTIME_INSTANCE_ATTRIBUTE without comment, returns None (no doc); else super.

---

### Class `UninitializedInstanceAttributeMixin(DataDocumenterMixinBase)` (lines 2422–2474)

**Methods:**
- **`is_uninitialized_instance_attribute(parent)`** → `bool`. Checks if attribute name is in parent's type hints.
- **`import_object(raiseerror=False)`**. Tries super with raiseerror=True; on ImportError, imports parent class and checks for annotation-only attribute. Sets object to UNINITIALIZED_ATTR.
- **`should_suppress_value_header()`**. Returns True for UNINITIALIZED_ATTR.
- **`get_doc(ignore=None)`**. Returns None if UNINITIALIZED_ATTR (no doc available); else super.

---

### Class `AttributeDocumenter(GenericAliasMixin, NewTypeMixin, SlotsMixin, TypeVarMixin, RuntimeInstanceAttributeMixin, UninitializedInstanceAttributeMixin, NonDataDescriptorMixin, DocstringStripSignatureMixin, ClassLevelDocumenter)` (lines 2477–2648)

**Class attributes:** `objtype = 'attribute'`, `member_order = 60`, `priority = 10`

**option_spec:** Inherits from ModuleLevelDocumenter plus `"annotation": annotation_option`, `"no-value": bool_option`.

**Methods:**
- **`is_function_or_method(obj)`** (staticmethod) → `bool`. Checks function/builtin/method.
- **`can_document_member(member, membername, isattr, parent)`**. Returns True for attribute descriptors; or if not module-level and not routine and not type.
- **`document_members(all_members=False)`** → no-op.
- **`isinstanceattribute()`** (deprecated). Checks for uninitialized instance variable via import + type hints.
- **`update_annotations(parent)`**. Updates parent's `__annotations__` from inspect + analyzer, walking MRO.
- **`import_object(raiseerror=False)`**. Calls super; converts enum attributes to their value; updates annotations on parent.
- **`get_real_modname()`**. Returns parent's or object's `__module__`, fallback to modname.
- **`should_suppress_value_header()`**. Checks mixins, then docstring metadata for `'hide-value'`.
- **`add_directive_header(sig)`**. Calls super. Adds `:annotation:` from option or type hint (`:type:`). Adds `:value:` with object description unless suppressed. Catches ValueError.
- **`get_attribute_comment(parent, attrname)`** → `Optional[List[str]]`. Walks MRO, checks analyzer's attr_docs for `<qualname>.<attrname>`.
- **`get_doc(ignore=None)`**. Checks attribute comment first; else calls super with temporarily disabled `autodoc_inherit_docstrings` to avoid descriptor docstring issues.
- **`add_content(more_content, no_docstring=False)`**. Disables analyzer (self.analyzer = None). Calls `update_content()`, then super.

---

### Class `PropertyDocumenter(DocstringStripSignatureMixin, ClassLevelDocumenter)` (lines 2651–2691)

**Class attributes:** `objtype = 'property'`, `member_order = 60`, `priority = AttributeDocumenter.priority + 1`

**Methods:**
- **`can_document_member(member, membername, isattr, parent)`** → `inspect.isproperty(member) and isinstance(parent, ClassDocumenter)`.
- **`document_members(all_members=False)`** → no-op.
- **`get_real_modname()`**. Returns parent's or object's `__module__`, fallback to modname.
- **`add_directive_header(sig)`**. Calls super; adds `:abstractmethod:` if abstract; adds `:type:` with return annotation from `fget` signature if available.

---

### Class `NewTypeAttributeDocumenter(AttributeDocumenter)` (lines 2694–2709)

**Class attributes:** `objtype = 'newvarattribute'`, `directivetype = 'attribute'`, `priority = MethodDocumenter.priority + 1`

**Methods:**
- **`can_document_member(member, membername, isattr, parent)`** → `not isinstance(parent, ModuleDocumenter) and inspect.isNewType(member)`.

---

## 3. Standalone Functions (lines 2712–2784)

### `get_documenters(app: Sphinx)` → `Dict[str, Type[Documenter]]`
Deprecated (warns `RemovedInSphinx50Warning`). Returns `app.registry.documenters`.

### `autodoc_attrgetter(app: Sphinx, obj: Any, name: str, *defargs: Any)` → `Any`
Iterates over `app.registry.autodoc_attrgettrs` items; if obj is instance of a registered type, calls the custom getter. Falls back to `safe_getattr(obj, name, *defargs)`.

### `migrate_autodoc_member_order(app: Sphinx, config: Config)` → `None`
If `config.autodoc_member_order == 'alphabetic'`, logs warning and migrates to `'alphabetical'`.

### Compatibility Imports (lines 2736–2742)
Re-exports from `sphinx.ext.autodoc.deprecated`:
- `DataDeclarationDocumenter`
- `GenericAliasDocumenter`
- `InstanceAttributeDocumenter`
- `SingledispatchFunctionDocumenter`
- `SingledispatchMethodDocumenter`
- `SlotsAttributeDocumenter`
- `TypeVarDocumenter`

### `setup(app: Sphinx)` → `Dict[str, Any]`

Registers 11 autodocumenters via `app.add_autodocumenter()`:
1. ModuleDocumenter
2. ClassDocumenter
3. ExceptionDocumenter
4. DataDocumenter
5. NewTypeDataDocumenter
6. FunctionDocumenter
7. DecoratorDocumenter
8. MethodDocumenter
9. AttributeDocumenter
10. PropertyDocumenter
11. NewTypeAttributeDocumenter

Adds config values:
- `autoclass_content`: `'class'`, ENUM('both', 'class', 'init')
- `autodoc_member_order`: `'alphabetical'`, ENUM('alphabetic', 'alphabetical', 'bysource', 'groupwise')
- `autodoc_class_signature`: `'mixed'`, ENUM('mixed', 'separated')
- `autodoc_default_options`: `{}`
- `autodoc_docstring_signature`: `True`
- `autodoc_mock_imports`: `[]`
- `autodoc_typehints`: `"signature"`, ENUM("signature", "description", "none", "both")
- `autodoc_typehints_description_target`: `'all'`, ENUM('all', 'documented')
- `autodoc_type_aliases`: `{}`
- `autodoc_warningiserror`: `True`
- `autodoc_inherit_docstrings`: `True`

Adds events: `autodoc-before-process-signature`, `autodoc-process-docstring`, `autodoc-process-signature`, `autodoc-skip-member`, `autodoc-process-bases`.

Connects `migrate_autodoc_member_order` to `'config-inited'` at priority 800.

Sets up sub-extensions: `sphinx.ext.autodoc.preserve_defaults`, `sphinx.ext.autodoc.type_comment`, `sphinx.ext.autodoc.typehints`.

Returns `{'version': sphinx.__display_version__, 'parallel_read_safe': True}`.

## sphinx/util/inspect.py
Here is the complete natural-language specification of `sphinx/util/inspect.py`:

---

## Module-Level Preamble

### Imports

```python
import builtins
import contextlib
import enum
import inspect
import re
import sys
import types
import typing
import warnings
from functools import partial, partialmethod
from importlib import import_module
from inspect import Parameter, isclass, ismethod, ismethoddescriptor, ismodule  # NOQA
from io import StringIO
from types import ModuleType
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple, Type, cast

from sphinx.deprecation import RemovedInSphinx50Warning
from sphinx.pycode.ast import ast  # for py36-37
from sphinx.pycode.ast import unparse as ast_unparse
from sphinx.util import logging
from sphinx.util.typing import ForwardRef
from sphinx.util.typing import stringify as stringify_annotation

if sys.version_info > (3, 7):
    from types import ClassMethodDescriptorType, MethodDescriptorType, WrapperDescriptorType
else:
    ClassMethodDescriptorType = type(object.__init__)
    MethodDescriptorType = type(str.join)
    WrapperDescriptorType = type(dict.__dict__['fromkeys'])

if False:
    # For type annotation only (never executed at runtime)
    from typing import Type  # NOQA
```

### Constants & Globals

- **`logger`**: `logging.getLogger(__name__)` — module-level logger.
- **`memory_address_re`**: `re.compile(r' at 0x[0-9a-f]{8,16}(?=>)', re.IGNORECASE)` — regex for stripping memory addresses from repr strings.

### Version-dependent type aliases (conditional)

When `sys.version_info > (3, 7)`:
- **`ClassMethodDescriptorType`**: imported from `types`.
- **`MethodDescriptorType`**: imported from `types`.
- **`WrapperDescriptorType`**: imported from `types`.

Otherwise:
- **`ClassMethodDescriptorType`** = `type(object.__init__)`
- **`MethodDescriptorType`** = `type(str.join)`
- **`WrapperDescriptorType`** = `type(dict.__dict__['fromkeys'])`

---

## Code Objects (Functions and Classes)

### `getargspec(func: Callable) -> Any`

Returns an `inspect.FullArgSpec` for *func*, supporting bound methods and wrapped functions. Emits a deprecation warning (`RemovedInSphinx50Warning`).

1. Calls `inspect.signature(func)` to obtain a `Signature`.
2. Initializes: `args=[]`, `varargs=None`, `varkw=None`, `kwonlyargs=[]`, `defaults=()`, `annotations={}`, `kwdefaults={}`.
3. If the signature's `return_annotation` is not empty, sets `annotations['return'] = signature.return_annotation`.
4. Iterates over each parameter in `signature.parameters.values()`:
   - **POSITIONAL_ONLY**: appends name to `args`.
   - **POSITIONAL_OR_KEYWORD**: appends name to `args`; if the param has a non-empty default, appends it to `defaults`.
   - **VAR_POSITIONAL**: sets `varargs = name`.
   - **KEYWORD_ONLY**: appends name to `kwonlyargs`; if the param has a non-empty default, sets `kwdefaults[name] = param.default`.
   - **VAR_KEYWORD**: sets `varkw = name`.
   - If the param's annotation is not empty, sets `annotations[name] = param.annotation`.
5. If `kwdefaults` is empty (falsy), sets it to `None` (for compatibility with `func.__kwdefaults__`).
6. If `defaults` is empty (falsy), sets it to `None` (for compatibility with `func.__defaults__`).
7. Returns `inspect.FullArgSpec(args, varargs, varkw, defaults, kwonlyargs, kwdefaults, annotations)`.

---

### `unwrap(obj: Any) -> Any`

Unwraps a single level of decoration from *obj*. If *obj* has the attribute `__sphinx_mock__`, returns it unchanged (to avoid RecursionError with mock objects). Otherwise calls `inspect.unwrap(obj)`. Catches `ValueError` and returns *obj* on failure.

---

### `unwrap_all(obj: Any, *, stop: Callable = None) -> Any`

Repeatedly unwraps a chain of wrappers until no more can be removed or the optional *stop* callable returns True for the current object. The loop checks in order:
1. If `stop(obj)` is truthy → return `obj`.
2. If `ispartial(obj)` → replace `obj` with `obj.func`.
3. If `inspect.isroutine(obj)` and `hasattr(obj, '__wrapped__')` → replace `obj` with `obj.__wrapped__`.
4. If `isclassmethod(obj)` → replace `obj` with `obj.__func__`.
5. If `isstaticmethod(obj)` → replace `obj` with `obj.__func__`.
6. Otherwise return `obj`.

---

### `getall(obj: Any) -> Optional[Sequence[str]]`

Returns the `__all__` attribute of *obj* as a sequence of strings, or `None` if absent. Raises `ValueError(__all__)` if `__all__` exists but is not a list/tuple of all-strings. Uses `safe_getattr(obj, '__all__', None)`.

---

### `getannotations(obj: Any) -> Mapping[str, Any]`

Returns the `__annotations__` attribute of *obj* as a `Mapping`, or `{}` if absent or not a mapping. Uses `safe_getattr(obj, '__annotations__', None)`.

---

### `getglobals(obj: Any) -> Mapping[str, Any]`

Returns the `__globals__` attribute of *obj* as a `Mapping`, or `{}` if absent or not a mapping. Uses `safe_getattr(obj, '__globals__', None)`.

---

### `getmro(obj: Any) -> Tuple[Type, ...]`

Returns the `__mro__` attribute of *obj* as a tuple, or `()` if absent or not a tuple. Uses `safe_getattr(obj, '__mro__', None)`.

---

### `getslots(obj: Any) -> Optional[Dict]`

Returns the `__slots__` attribute of class *obj* as a dict mapping slot names to `None`, or `None` if absent.
- If *obj* is not a class, raises `TypeError`.
- Uses `safe_getattr(obj, '__slots__', None)`:
  - `None` → return `None`.
  - `dict` → return as-is.
  - `str` → return `{__slots__: None}`.
  - `list`/`tuple` → return `{e: None for e in __slots__}`.
  - Otherwise → raise `ValueError`.

---

### `isNewType(obj: Any) -> bool`

Returns `True` if *obj* is a PEP 613 `NewType`, determined by checking that `safe_getattr(obj, '__module__', None)` equals `'typing'` and `safe_getattr(obj, '__qualname__', None)` equals `'NewType.<locals>.new_type'`.

---

### `isenumclass(x: Any) -> bool`

Returns `True` if *x* is a class that is a subclass of `enum.Enum`. Equivalent to `inspect.isclass(x) and issubclass(x, enum.Enum)`.

---

### `isenumattribute(x: Any) -> bool`

Returns `True` if *x* is an instance of `enum.Enum`.

---

### `unpartial(obj: Any) -> Any`

Strips all layers of `functools.partial`/`partialmethod` wrapping from *obj*. While `ispartial(obj)` is true, replaces `obj` with `obj.func`. Returns the final unwrapped object (which may be the original if not partial).

---

### `ispartial(obj: Any) -> bool`

Returns `True` if *obj* is an instance of `functools.partial` or `functools.partialmethod`.

---

### `isclassmethod(obj: Any) -> bool`

Returns `True` if *obj* is a classmethod. Checks:
1. `isinstance(obj, classmethod)` → True.
2. `inspect.ismethod(obj)` and `obj.__self__ is not None` and `isclass(obj.__self__)` → True (bound to a class).

---

### `isstaticmethod(obj: Any, cls: Any = None, name: str = None) -> bool`

Returns `True` if *obj* is a staticmethod. Checks:
1. `isinstance(obj, staticmethod)` → True.
2. If both *cls* and *name* are provided: iterates over the MRO of *cls* (or `[cls]` if no `__mro__`). For each base class, looks up `basecls.__dict__.get(name)`. If found and is a `staticmethod`, returns True; otherwise returns False.

---

### `isdescriptor(x: Any) -> bool`

Returns `True` if *x* has any of `__get__`, `__set__`, or `__delete__` that are callable (checked via `safe_getattr`).

---

### `isabstractmethod(obj: Any) -> bool`

Returns `True` if `safe_getattr(obj, '__isabstractmethod__', False)` is exactly `True`.

---

### `is_cython_function_or_method(obj: Any) -> bool`

Returns `True` if `obj.__class__.__name__ == 'cython_function_or_method'`, catching `AttributeError` and returning `False`.

---

### `isattributedescriptor(obj: Any) -> bool`

Determines whether *obj* is an attribute-like descriptor (non-callable, non-method). Logic:
1. If `inspect.isdatadescriptor(obj)` → True (data descriptors are attribute-like).
2. Otherwise if `isdescriptor(obj)` (has `__get__`/`__set__`/`__delete__`):
   - Unwrap via `unwrap(obj)`.
   - If unwrapped is a function, builtin, or method → False.
   - If unwrapped is a cython function/method → False.
   - If unwrapped is a class (`inspect.isclass`) → False.
   - If unwrapped is an instance of `ClassMethodDescriptorType`, `MethodDescriptorType`, or `WrapperDescriptorType` → False.
   - If `type(unwrapped).__name__ == "instancemethod"` → False (C-API instancemethod).
   - Otherwise → True.
3. Else → False.

---

### `is_singledispatch_function(obj: Any) -> bool`

Returns `True` if *obj* is a `functools.singledispatch`-decorated function: checks that it's a function (`inspect.isfunction`), has attributes `dispatch` and `register`, and `obj.dispatch.__module__ == 'functools'`.

---

### `is_singledispatch_method(obj: Any) -> bool`

Returns `True` if *obj* is an instance of `functools.singledispatchmethod` (Python 3.8+). Imports `singledispatchmethod` from `functools`; catches `ImportError` for Python 3.6–37 and returns `False`.

---

### `isfunction(obj: Any) -> bool`

Returns `inspect.isfunction(unwrap_all(obj))`.

---

### `isbuiltin(obj: Any) -> bool`

Returns `inspect.isbuiltin(unwrap_all(obj))`.

---

### `isroutine(obj: Any) -> bool`

Returns `inspect.isroutine(unwrap_all(obj))`.

---

### `iscoroutinefunction(obj: Any) -> bool`

Inner helper `iswrappedcoroutine(obj)`: returns True if *obj* has `__wrapped__` but is not a staticmethod, classmethod, or partial. Then:
1. Calls `unwrap_all(obj, stop=iswrappedcoroutine)` to unwrap until hitting a wrapped coroutine or a non-wrappable type.
2. If the result has `__code__` and `inspect.iscoroutinefunction(obj)` → True.
3. Otherwise → False.

---

### `isproperty(obj: Any) -> bool`

Returns `True` if *obj* is an instance of `functools.cached_property` (Python 3.8+) or `property`. On Python < 3.8, only checks for `property`.

---

### `isgenericalias(obj: Any) -> bool`

Returns `True` if *obj* is a generic alias type. Checks in order:
1. If `typing._GenericAlias` exists (Python 3.7+) and `isinstance(obj, typing._GenericAlias)` → True.
2. If `types.GenericAlias` exists (Python 3.9+) and `isinstance(obj, types.GenericAlias)` → True.
3. If `typing._SpecialGenericAlias` exists (Python 3.9+) and `isinstance(obj, typing._SpecialGenericAlias)` → True.

---

### `safe_getattr(obj: Any, name: str, *defargs: Any) -> Any`

A safe `getattr` that converts all exceptions to `AttributeError`. Tries `getattr(obj, name, *defargs)` first. If it raises, tries `obj.__dict__[name]`. If that also fails and a default was provided (`defargs`), returns `defargs[0]`. Otherwise re-raises as `AttributeError(name) from exc`.

---

### `object_description(object: Any) -> str`

A repr-like function producing text safe for reST. Handles special types:
1. **dict**: sorts keys (falls back to generic repr if unsortable). Recursively calls itself on each key and value, formats as `"{key: value, ...}"`.
2. **set**: sorts values (falls back to generic repr if unorderable). Formats as `"{value, ...}"`.
3. **frozenset**: sorts values (falls back to generic repr). Formats as `"frozenset({value, ...})"`.
4. **enum.Enum**: returns `"%s.%s" % (object.__class__.__name__, object.name)`.
5. For all others: calls `repr(object)`; if that raises, re-raises as `ValueError`. Strips memory addresses via `memory_address_re.sub('', s)` and replaces newlines with spaces.

---

### `is_builtin_class_method(obj: Any, attr_name: str) -> bool`

Returns `True` if *attr_name* is implemented in a builtin class (e.g., `int.__init__`). Iterates over the MRO of *obj*, finds the first class containing *attr_name* in its `__dict__`. Gets that class's `__name__` and checks whether `getattr(builtins, name, None) is cls`. Returns False if not found or on AttributeError.

---

### Class: `DefaultValue`

A simple wrapper for default values of overloaded function parameters.
- **Attributes**: `value: str` — set in `__init__(self, value: str) -> None`.
- **Methods**:
  - `__eq__(self, other: object) -> bool`: returns `self.value == other`.
  - `__repr__(self) -> str`: returns `self.value`.

---

### Class: `TypeAliasForwardRef`

Pseudo typing class for `autodoc_type_aliases`, avoiding errors during `get_type_hints()` evaluation.
- **Attributes**: `name: str` — set in `__init__(self, name: str) -> None`.
- **Methods**:
  - `__call__(self) -> None`: dummy method imitating special typing classes; does nothing.
  - `__eq__(self, other: Any) -> bool`: returns `self.name == other`.

---

### Class: `TypeAliasModule`

Pseudo module class for `autodoc_type_aliases`, enabling nested lookups like `mod1.mod2.Class`.
- **Attributes**:
  - `__modname: str` — the base module name.
  - `__mapping: Dict[str, str]` — mapping of dotted names to alias strings.
  - `__module: Optional[ModuleType] = None` — lazily loaded real module.
- **Methods**:
  - `__init__(self, modname: str, mapping: Dict[str, str]) -> None`: stores `modname`, `mapping`; initializes `__module` to `None`.
  - `__getattr__(self, name: str) -> Any`: constructs `fullname = '.'.join(filter(None, [self.__modname, name]))`. If `fullname in self.__mapping`, returns `TypeAliasForwardRef(self.__mapping[fullname])`. Else if any mapping keys start with `fullname + '.'`, recursively creates a nested `TypeAliasModule(fullname, nested)`. Otherwise tries to import the real submodule via `import_module(fullname)`; on ImportError, lazily loads `self.__module = import_module(self.__modname)` and returns `getattr(self.__module, name)`.

---

### Class: `TypeAliasNamespace(Dict[str, Any])`

Pseudo namespace class for `autodoc_type_aliases`, enabling nested lookups like `mod1.mod2.Class`.
- **Attributes**: `__mapping: Dict[str, str]` — set in `__init__(self, mapping: Dict[str, str]) -> None`.
- **Methods** (overrides dict behavior):
  - `__getitem__(self, key: str) -> Any`: if `key in self.__mapping`, returns `TypeAliasForwardRef(self.__mapping[key])`. Else if any keys start with `key + '.'`, creates a nested `TypeAliasModule(key, nested)`. Otherwise raises `KeyError`.

---

### `_should_unwrap(subject: Callable) -> bool`

Private helper. Returns `True` if *subject* is from the `contextlib` module (checked via `__globals__.get('__name__') == 'contextlib'` and `__globals__.get('__file__') == contextlib.__file__`). Used to determine whether contextmanager-decorated functions should be unwrapped when getting signatures.

---

### `signature(subject: Callable, bound_method: bool = False, follow_wrapped: bool = None, type_aliases: Dict = {}) -> inspect.Signature`

Returns an `inspect.Signature` for *subject*.
1. If `follow_wrapped is None`, sets it to `True`. Otherwise emits a deprecation warning (`RemovedInSphinx50Warning`).
2. Tries to get the signature: if `_should_unwrap(subject)` → calls `inspect.signature(subject)`. Else → `inspect.signature(subject, follow_wrapped=follow_wrapped)`. Catches `ValueError` and retries with bare `inspect.signature(subject)`. Extracts `parameters = list(signature.parameters.values())` and `return_annotation = signature.return_annotation`.
3. Catches `IndexError`: if the subject has `_partialmethod`, sets `parameters = []` and `return_annotation = Parameter.empty`; otherwise re-raises.
4. Resolves annotations: creates a `TypeAliasNamespace(type_aliases)` as local namespace, calls `typing.get_type_hints(subject, None, localns)`. For each parameter whose name is in the resolved annotations, replaces its annotation (handling `TypeAliasForwardRef` by extracting `.name`). Same for return annotation if `'return'` is present. Catches all exceptions and silently passes.
5. If `bound_method` is True: if *subject* is already a bound method (`inspect.ismethod(subject)`), does nothing; else removes the first parameter from the list (the implicit `self`).
6. Returns `inspect.Signature(parameters, return_annotation=return_annotation, __validate_parameters__=False)`.

---

### `evaluate_signature(sig: inspect.Signature, globalns: Dict = None, localns: Dict = None) -> inspect.Signature`

Evaluates unresolved type annotations (string forward refs) in a signature.
- Inner function `evaluate_forwardref(ref: ForwardRef, globalns, localns)`: calls `ref._evaluate(globalns, localns, frozenset())` on Python 3.9+, or `ref._evaluate(globalns, localns)` otherwise.
- Inner function `evaluate(annotation, globalns, localns)`: if annotation is a string, creates a `ForwardRef(annotation, True)` and evaluates it; if the result is still a ForwardRef or string, re-evaluates. Catches `NameError`/`TypeError` and returns the unresolved annotation.
- Sets defaults: `globalns = {}`, `localns = globalns`.
- Iterates over parameters; for each with a non-empty annotation, evaluates it and replaces via `param.replace(annotation=...)`.
- Evaluates return_annotation similarly if non-empty.
- Returns `sig.replace(parameters=parameters, return_annotation=return_annotation)`.

---

### `stringify_signature(sig: inspect.Signature, show_annotation: bool = True, show_return_annotation: bool = True) -> str`

Converts a signature to its string representation (e.g., `(a: int, /, b, *, c=1) -> str`).
- Iterates over parameters in order. Tracks `last_kind`.
- Inserts `/` separator when transitioning from POSITIONAL_ONLY to non-PPOSITIONAL_ONLY, or at the end if last param was POSITIONAL_ONLY (PEP 570).
- Inserts `*` separator when a KEYWORD_ONLY follows POSITIONAL_OR_KEYWORD, POSITIONAL_ONLY, or None (PEP 3102).
- For each parameter: writes name; for VAR_POSITIONAL prepends `*`, for VAR_KEYWORD prepends `**`. If annotation is present and `show_annotation` is True, appends `: <stringified annotation>`. If default is not empty, appends `= <object_description(default)>` (with space before `=` only if annotation was also shown).
- Appends each formatted arg to a list.
- If return annotation is empty or either show flag is False, returns `'(%s)' % ', '.join(args)`. Otherwise returns `'(%s) -> %s' % (', '.join(args), stringify_annotation(return_annotation))`.

---

### `signature_from_str(signature: str) -> inspect.Signature`

Parses a signature string like `(x: int, y=1) -> str` into an `inspect.Signature`. Prepends `'def func'` and appends `': pass'`, parses with `ast.parse()`, casts the first body element to `ast.FunctionDef`, then delegates to `signature_from_ast(function, code)`.

---

### `signature_from_ast(node: ast.FunctionDef, code: str = '') -> inspect.Signature`

Creates an `inspect.Signature` from an AST function definition node.
1. Extracts `args = node.args`. Builds a list of defaults from `args.defaults`, padded with `Parameter.empty` at the front to match positional count (positionals = posonlyargs + len(args.args)).
2. If Python has `posonlyargs`: processes them first, then regular args; else only regular args.
3. For each positional/positional-only arg: if its corresponding default is not empty, creates a `DefaultValue(ast_unparse(default, code))`; annotation via `ast_unparse(arg.annotation, code)` or `Parameter.empty`. Creates `Parameter` with kind POSITIONAL_ONLY or POSITIONAL_OR_KEYWORD.
4. If `args.vararg` exists: creates VAR_POSITIONAL parameter with its annotation.
5. For each kwonly arg: default is `ast_unparse(args.kw_defaults[i], code)` or empty; annotation similarly. Creates KEYWORD_ONLY parameter.
6. If `args.kwarg` exists: creates VAR_KEYWORD parameter with its annotation.
7. Return annotation from `ast_unparse(node.returns, code)` or `Parameter.empty`.
8. Returns `inspect.Signature(params, return_annotation=return_annotation)`.

---

### `getdoc(obj: Any, attrgetter: Callable = safe_getattr, allow_inherited: bool = False, cls: Any = None, name: str = None) -> str`

Obtains the docstring for *obj*, with special handling for partials and inherited methods.
1. Gets `doc = attrgetter(obj, '__doc__', None)`.
2. If *obj* is a partial and its `__doc__` equals `obj.__class__.__doc__`, recursively calls `getdoc(obj.func)` to get the wrapped function's docstring.
3. Else if `doc is None` and `allow_inherited`:
   - If both *cls* and *name* are provided: iterates over the MRO of *cls*. For each base class, gets the attribute via `safe_getattr(basecls, name, None)`. If found, tries to get its docstring via `attrgetter`; if non-None, breaks. If still None, retries with `inspect.getdoc(meth)` for each base class.
   - If doc is still None after MRO search, calls `inspect.getdoc(obj)`.
4. Returns the final `doc` string (may be `None`).