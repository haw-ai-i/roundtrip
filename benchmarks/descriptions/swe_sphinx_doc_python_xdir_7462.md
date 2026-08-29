## sphinx/domains/python.py
Now I have the full file. Here is the complete specification:

---

# Module-Level Preamble

## Imports

```python
import builtins
import inspect
import re
import typing
import warnings
from inspect import Parameter
from typing import Any, Dict, Iterable, Iterator, List, NamedTuple, Tuple
from typing import cast

from docutils import nodes
from docutils.nodes import Element, Node
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.addnodes import pending_xref, desc_signature
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.deprecation import RemovedInSphinx40Warning, RemovedInSphinx50Warning
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType, Index, IndexEntry
from sphinx.environment import BuildEnvironment
from sphinx.locale import _, __
from sphinx.pycode.ast import ast, parse as ast_parse
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docfields import Field, GroupedField, TypedField
from sphinx.util.docutils import SphinxDirective
from sphinx.util.inspect import signature_from_str
from sphinx.util.nodes import make_id, make_refnode
from sphinx.util.typing import TextlikeNode

if False:
    from typing import Type  # for python3.5.1
```

## Constants & Globals

- **`logger`**: `logging.getLogger(__name__)` — module logger instance.
- **`py_sig_re`**: Compiled regex (`re.VERBOSE`) matching Python signatures with groups: `(class_name_prefix)`, `(thing_name)`, `(optional_arguments)`, `(optional_return_annotation)`. Pattern: `^([\w.]*\.)?(\w+)\s*(?:\(\s*(.*)\s*\)(?:\s*->\s*(.*))?)?$`
- **`pairindextypes`**: Dict mapping string keys to localized strings:
  - `'module'` → `_('module')`, `'keyword'` → `_('keyword')`, `'operator'` → `_('operator')`, `'object'` → `_('object')`, `'exception'` → `_('exception')`, `'statement'` → `_('statement')`, `'builtin'` → `_('built-in function')`.
- **`ObjectEntry`**: NamedTuple with fields `(docname: str, node_id: str, objtype: str)`.
- **`ModuleEntry`**: NamedTuple with fields `(docname: str, node_id: str, synopsis: str, platform: str, deprecated: bool)`.

---

# Code Objects

## Function `_parse_annotation(annotation: str) -> List[Node]`

Parses a type annotation string into a list of docutils `Node` objects. Internally defines two nested functions:

### Nested `make_xref(text: str) -> addnodes.pending_xref`
Creates a pending cross-reference node. If `text == 'None'`, sets `reftype='obj'`; otherwise `reftype='class'`. Returns `pending_xref('', nodes.Text(text), refdomain='py', reftype=reftype, reftarget=text)`.

### Nested `unparse(node: ast.AST) -> List[Node]`
Recursively converts an AST node to a list of docutils nodes. Handles these AST types:
- **`ast.Attribute`**: Returns `[nodes.Text("value.attr")]` by concatenating the unparsed value's first element with `.attr`.
- **`ast.Expr` / `ast.Module` / `ast.Index`**: Recursively unparses the inner node (for `Expr`/`Index`, unwraps one level; for `Module`, flattens all body elements).
- **`ast.List`**: Wraps each element's unparsed result with `[` and `, ]` punctuation nodes (`desc_sig_punctuation`). Trailing comma is removed.
- **`ast.Name`**: Returns `[nodes.Text(node.id)]`.
- **`ast.Subscript`**: Unparses value, appends `[`, unparses slice, appends `]`.
- **`ast.Tuple`**: Unparses each element separated by `, `. Trailing comma removed.
- **Any other type**: Raises `SyntaxError`.

### Main body
Tries to parse the annotation string via `ast_parse(annotation)`, then unparse it. Iterates over the result; any `nodes.Text` node is replaced with a cross-reference from `make_xref`. On `SyntaxError`, returns `[make_xref(annotation)]` (single text-based xref wrapping the entire raw annotation).

---

## Function `_parse_arglist(arglist: str) -> addnodes.desc_parameterlist`

Parses an argument list string using Python's AST/signature machinery. Creates a `desc_parameterlist`. Calls `signature_from_str('(%s)' % arglist)` to get a signature object, then iterates over its parameters in order, tracking `last_kind`:

- If current param is `POSITIONAL_ONLY` and previous was also `POSITIONAL_ONLY`, inserts a `/` operator parameter (PEP 570 separator).
- If current param is `KEYWORD_ONLY` and previous was `POSITIONAL_OR_KEYWORD`, `POSITIONAL_ONLY`, or `None`, inserts a `*` operator parameter (PEP 3102 separator).

For each parameter, creates a `desc_parameter` node:
- **`VAR_POSITIONAL`**: Adds `*` operator + name.
- **`VAR_KEYWORD`**: Adds `**` operator + name.
- **Other kinds**: Adds just the name.

If param has an annotation (not `param.empty`), appends `:` + space + unparsed annotation children via `_parse_annotation`. If param has a default value (not `param.empty`): if there's also an annotation, adds space + `=` + space; otherwise just `=`. The default is rendered as an `inline` node with class `'default_value'`.

After all params: if the last kind was `POSITIONAL_ONLY`, appends `/` operator. Returns the populated `desc_parameterlist`.

---

## Function `_pseudo_parse_arglist(signode: desc_signature, arglist: str) -> None`

Fallback parser for argument lists using bracket-based optional grouping. Creates a `desc_parameterlist` and a stack (initially `[paramlist]`). Iterates over comma-split arguments:

For each stripped argument:
- While it starts with `[`: push `desc_optional()` onto stack, add to parent, strip prefix.
- While it starts with `]`: pop from stack, strip prefix.
- While it ends with `]` (but not `[]`): count closing brackets (`ends_close`).
- While it ends with `[`: count opening brackets (`ends_open`).
- If non-empty argument remains: add as `desc_parameter` to top of stack.
- Push `ends_open` new `desc_optional()` wrappers onto the stack, adding each to its parent.
- Pop `ends_close` times from the stack.

After all arguments: if stack length ≠ 1, raises `IndexError`. On `IndexError`, discards the partially-built paramlist and creates a single-param list containing the entire raw arglist string. Otherwise adds the paramlist to signode.

---

## Class `PyXrefMixin`

Provides cross-reference creation methods with support for `.` and `~` prefixes (similar to `:class:` behavior).

### Method `make_xref(self, rolename: str, domain: str, target: str, innernode: Type[TextlikeNode] = nodes.emphasis, contnode: Node = None, env: BuildEnvironment = None) -> Node`
Calls parent's `make_xref`, sets `result['refspecific'] = True`. If target starts with `.` or `~`: extracts prefix as first char and strips it from reftarget. For `.`, display text is the stripped target; for `~`, display text is the last component after splitting on `.`. Replaces the first `nodes.Text` child in result with the computed display text. Returns result.

### Method `make_xrefs(self, rolename: str, domain: str, target: str, innernode: Type[TextlikeNode] = nodes.emphasis, contnode: Node = None, env: BuildEnvironment = None) -> List[Node]`
Splits the target string by delimiters matching `(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+)`. For each non-empty sub-target: if it matches a delimiter pattern, appends `contnode` or an `innernode` with the delimiter text; otherwise calls `make_xref` for that sub-target. If `split_contnode` is true (contnode's text equals target), creates a new `nodes.Text(sub_target)` as contnode for each split piece. Returns list of nodes.

---

## Class `PyField(PyXrefMixin, Field)`

Overrides `make_xref`: if `rolename == 'class'` and `target == 'None'`, changes rolename to `'obj'`. Calls parent's `make_xref`.

---

## Class `PyGroupedField(PyXrefMixin, GroupedField)`

No overrides; inherits all behavior from both parents.

---

## Class `PyTypedField(PyXrefMixin, TypedField)`

Same as `PyField`: if `rolename == 'class'` and `target == 'None'`, changes rolename to `'obj'`. Calls parent's `make_xref`.

---

## Class `PyObject(ObjectDescription)`

Base class for general Python object descriptions.

### Class attributes
- **`option_spec`**: Dict with keys: `'noindex'` (`directives.flag`), `'module'` (`directives.unchanged`), `'annotation'` (`directives.unchanged`).
- **`doc_field_types`**: List of doc field type definitions:
  - `PyTypedField('parameter', label=_('Parameters'), names=('param','parameter','arg','argument','keyword','kwarg','kwparam'), typerolename='class', typenames=('paramtype','type'), can_collapse=True)`
  - `PyTypedField('variable', label=_('Variables'), rolename='obj', names=('var','ivar','cvar'), typerolename='class', typenames=('vartype',), can_collapse=True)`
  - `PyGroupedField('exceptions', label=_('Raises'), rolename='exc', names=('raises','raise','exception','except'), can_collapse=True)`
  - `Field('returnvalue', label=_('Returns'), has_arg=False, names=('returns','return'))`
  - `PyField('returntype', label=_('Return type'), has_arg=False, names=('rtype',), bodyrolename='class')`
- **`allow_nesting`**: `False`.

### Method `get_signature_prefix(self, sig: str) -> str`
Returns empty string. Subclasses may override to add a prefix (e.g., `'async '`).

### Method `needs_arglist(self) -> bool`
Returns `False`. Subclasses may override.

### Method `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`
Parses the signature using `py_sig_re`, extracting `(prefix, name, arglist, retann)`. Determines module and class context from `self.options.get('module')` or `self.env.ref_context['py:module']`, and `self.env.ref_context['py:class']`.

Computes `fullname`:
- If a class is active (`classname` set): if prefix matches or starts with classname, uses prefix+name as fullname and strips the classname from prefix; if prefix differs from classname, prepends classname to prefix+name; otherwise fullname = classname + '.' + name.
- If no class: if prefix exists, classname = prefix stripped of trailing dots, fullname = prefix + name; else classname = '', fullname = name.

Sets `signode['module']`, `signode['class']`, `signode['fullname']`. Adds signature prefix via `get_signature_prefix` as a `desc_annotation`. If prefix is set, adds it as `desc_addname`; otherwise if `add_module` and config says so (and modname ≠ 'exceptions'), adds modname + '.' as `desc_addname`. Adds the name as `desc_name`.

If arglist exists: tries `_parse_arglist(arglist)`, falling back to `_pseudo_parse_arglist` on `SyntaxError` or `NotImplementedError` (with a warning logged). If no arglist but `needs_arglist()` is true, adds empty `desc_parameterlist()`.

If return annotation exists: parses it via `_parse_annotation(retann)` and adds as `desc_returns`. If `'annotation'` option is set, appends it as `desc_annotation`. Returns `(fullname, prefix)`.

### Method `get_index_text(self, modname: str, name: Tuple[str, str]) -> str`
Raises `NotImplementedError`; must be overridden in subclasses.

### Method `add_target_and_index(self, name_cls: Tuple[str, str], sig: str, signode: desc_signature) -> None`
Computes `fullname` from modname + name_cls[0]. Generates a node_id via `make_id`. Appends the node_id to `signode['ids']`. Also appends the raw `fullname` as an old-style ID if it differs and isn't already in document ids. Notes the signode as explicit target. Registers the object with the PythonDomain via `domain.note_object()`. If `get_index_text()` returns non-empty text, adds a `'single'` index entry.

### Method `before_content(self) -> None`
Handles nesting setup. If `self.names` is set, extracts `(fullname, name_prefix)` from the last entry. Sets `py:class` in ref_context: if `allow_nesting`, uses fullname; else uses stripped name_prefix. Pushes onto `py:classes` stack if nestable. If `'module'` option is present, pushes current module onto a `py:modules` stack and sets new module from the option.

### Method `after_content(self) -> None`
Handles nesting teardown. Gets `py:classes` list; pops it if `allow_nesting`. Sets `py:class` to last element of classes list or `None`. If `'module'` option was set, pops from `py:modules` stack (or removes `py:module` entirely if empty).

---

## Class `PyModulelevel(PyObject)`

Description of module-level objects (functions, data). **Deprecated** — emits `RemovedInSphinx40Warning` on every `run()`.

### Method `run(self) -> List[Node]`
Emits deprecation warning, calls parent's `run()`.

### Method `needs_arglist(self) -> bool`
Returns `True` if `objtype == 'function'`, else `False`.

### Method `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`
For `'function'`: if no modname → `_('%(name)s() (built-in function)')`; else → `_('%(name)s() (in module %(modname)s)')`. For `'data'`: similar pattern with "built-in variable" / "(in module ...)". Otherwise returns empty string.

---

## Class `PyFunction(PyObject)`

Description of a function.

### Class attributes
- **`option_spec`**: Copies `PyObject.option_spec`, adds `'async'` (`directives.flag`).

### Method `get_signature_prefix(self, sig: str) -> str`
Returns `'async '` if `'async'` in options; else empty string.

### Method `needs_arglist(self) -> bool`
Returns `True`.

### Method `add_target_and_index(self, name_cls: Tuple[str, str], sig: str, signode: desc_signature) -> None`
Calls parent's method. Then adds an additional index entry: if modname exists → `'single'` entry with `_('%(name)s() (in module %(modname)s)')`; else → `'pair'` entry with `'%(name); %(name)s()'` mapped to `pairindextypes['builtin']`.

### Method `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`
Returns `None` (index is added manually in `add_target_and_index`).

---

## Class `PyDecoratorFunction(PyFunction)`

Description of a decorator.

### Method `run(self) -> List[Node]`
Sets `self.name = 'py:function'`, calls parent's `run()`.

### Method `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`
Calls parent's method, then inserts `'@'` as a `desc_addname` at position 0 of signode. Returns result.

### Method `needs_arglist(self) -> bool`
Returns `False`.

---

## Class `PyVariable(PyObject)`

Description of a variable.

### Class attributes
- **`option_spec`**: Copies `PyObject.option_spec`, adds `'type'` and `'value'` (both `directives.unchanged`).

### Method `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`
Calls parent's method. If `'type'` option exists, appends it as `desc_annotation(typ, ': ' + typ)`. If `'value'` option exists, appends it as `desc_annotation(value, ' = ' + value)`. Returns result.

### Method `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`
If modname → `_('%(name)s (in module %(modname)s)')`; else → `_('%(name)s (built-in variable)')`.

---

## Class `PyClasslike(PyObject)`

Description of class-like objects (classes, interfaces, exceptions).

### Class attributes
- **`allow_nesting`**: `True`.

### Method `get_signature_prefix(self, sig: str) -> str`
Returns `'%(objtype)s '`.

### Method `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`
For `'class'`: if no modname → `_('%(name)s (built-in class)')`; else → `_('%(name)s (class in %(modname)s)')`. For `'exception'`: returns just the name. Otherwise empty string.

---

## Class `PyClassmember(PyObject)`

Description of a class member (methods, attributes). **Deprecated** — emits `RemovedInSphinx40Warning` on every `run()`.

### Method `run(self) -> List[Node]`
Emits deprecation warning (checking MRO for non-DirectiveAdapter classes), calls parent's `run()`.

### Method `needs_arglist(self) -> bool`
Returns `True` if objtype ends with `'method'`, else `False`.

### Method `get_signature_prefix(self, sig: str) -> str`
For `'staticmethod'`: returns `'static '`. For `'classmethod'`: returns `'classmethod '`. Otherwise empty string.

### Method `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`
Gets `add_modules` from config. For each sub-type (`method`, `staticmethod`, `classmethod`, `attribute`): tries to split name on last `'.'` into `(clsname, methname/attrname)`. If that fails (ValueError), falls back to module-based text or bare name. When successful: if modname and add_modules → includes full path; otherwise just class name. Formats vary by type: `%(meth)s() (%(cls)s method)`, `%(meth)s() (%(mod)s.%(cls)s static method)`, etc. For `'attribute'` without module: returns bare name. Otherwise empty string.

---

## Class `PyMethod(PyObject)`

Description of a method.

### Class attributes
- **`option_spec`**: Copies `PyObject.option_spec`, adds `'abstractmethod'`, `'async'`, `'classmethod'`, `'property'`, `'staticmethod'` (all `directives.flag`).

### Method `needs_arglist(self) -> bool`
Returns `False` if `'property'` in options; else `True`.

### Method `get_signature_prefix(self, sig: str) -> str`
Builds a prefix list from active flags (`'abstract'`, `'async'`, `'classmethod'`, `'property'`, `'staticmethod'`). Joins with spaces + trailing space if non-empty; otherwise empty string.

### Method `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`
Tries to split name on last `'.'`. If fails and modname exists → `_('%(name)s() (in module %(modname)s)')`; else → bare `'%(name)s()'`. If successful: prepends modname to clsname if add_modules. Returns formatted text based on options: class method, property, static method, or regular method.

---

## Class `PyClassMethod(PyMethod)`

Description of a classmethod directive.

### Class attributes
- **`option_spec`**: Copies `PyObject.option_spec`.

### Method `run(self) -> List[Node]`
Sets `self.name = 'py:method'`, sets `'classmethod': True` in options, calls parent's `run()`.

---

## Class `PyStaticMethod(PyMethod)`

Description of a staticmethod directive.

### Class attributes
- **`option_spec`**: Copies `PyObject.option_spec`.

### Method `run(self) -> List[Node]`
Sets `self.name = 'py:method'`, sets `'staticmethod': True` in options, calls parent's `run()`.

---

## Class `PyDecoratorMethod(PyMethod)`

Description of a decorator method.

### Method `run(self) -> List[Node]`
Sets `self.name = 'py:method'`, calls parent's `run()`.

### Method `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`
Calls parent's method, inserts `'@'` as `desc_addname` at position 0 of signode. Returns result.

### Method `needs_arglist(self) -> bool`
Returns `False`.

---

## Class `PyAttribute(PyObject)`

Description of an attribute.

### Class attributes
- **`option_spec`**: Copies `PyObject.option_spec`, adds `'type'` and `'value'` (both `directives.unchanged`).

### Method `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`
Calls parent's method. If `'type'` option exists, appends as `desc_annotation(typ, ': ' + typ)`. If `'value'` option exists, appends as `desc_annotation(value, ' = ' + value)`. Returns result.

### Method `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`
Tries to split name on last `'.'`. If fails and modname → `_('%(name)s (in module %(modname)s)')`; else bare name. If successful: prepends modname if add_modules. Returns `'%(attr)s (%(cls)s attribute)'`.

---

## Class `PyDecoratorMixin`

**Deprecated** mixin for decorator directives. Emits `RemovedInSphinx50Warning` on every `handle_signature()`.

### Method `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`
Emits deprecation warning (checking MRO). Calls parent's method, inserts `'@'` as `desc_addname` at position 0. Returns result.

### Method `needs_arglist(self) -> bool`
Returns `False`.

---

## Class `PyModule(SphinxDirective)`

Directive to mark description of a new module.

### Class attributes
- **`has_content`**: `False`.
- **`required_arguments`**: `1`.
- **`optional_arguments`**: `0`.
- **`final_argument_whitespace`**: `False`.
- **`option_spec`**: `'platform'` (lambda x: x), `'synopsis'` (lambda x: x), `'noindex'` (`directives.flag`), `'deprecated'` (`directives.flag`).

### Method `run(self) -> List[Node]`
Gets PythonDomain. Strips module name from arguments. Sets `py:module` in ref_context. If not noindex: generates a node_id via `make_id`, creates a `nodes.target` with `ismod=True`. Generates old-style node_id for backward compatibility (appends if different and not already present). Notes the target as explicit. Registers module with domain (`note_module`) and object (`note_object`). Creates an index entry with `'pair'` type using `pairindextypes['module']`. Returns `[target, index_node]`.

### Method `make_old_id(self, name: str) -> str`
Returns `'module-%s' % name`. Old-style IDs incompatible with docutils (can contain dots/hyphens).

---

## Class `PyCurrentModule(SphinxDirective)`

Directive to set the current module context without creating an index entry.

### Class attributes
- **`has_content`**: `False`.
- **`required_arguments`**: `1`.
- **`optional_arguments`**: `0`.
- **`final_argument_whitespace`**: `False`.
- **`option_spec`**: `{}` (empty dict).

### Method `run(self) -> List[Node]`
Strips module name. If `'None'`, removes `py:module` from ref_context; otherwise sets it. Returns empty list.

---

## Class `PyXRefRole(XRefRole)`

Custom cross-reference role for Python objects.

### Method `process_link(self, env: BuildEnvironment, refnode: Element, has_explicit_title: bool, title: str, target: str) -> Tuple[str, str]`
Sets `refnode['py:module']` and `refnode['py:class']` from ref_context. If no explicit title: strips leading `.` from title (only meaningful for target), strips leading `~` from target (for display). If title starts with `~`: removes it, then finds last `.` and keeps only the part after it. If target starts with `.`: strips the dot and sets `refnode['refspecific'] = True`. Returns `(title, target)`.

---

## Function `filter_meta_fields(app: Sphinx, domain: str, objtype: str, content: Element) -> None`

Event handler for `'object-description-transform'`. If domain is not `'py'`, returns immediately. Otherwise iterates over content nodes; if a node is a `nodes.field_list`, iterates its fields and removes the first field whose body text equals `'meta'` or starts with `'meta '`.

---

## Class `PythonModuleIndex(Index)`

Index subclass providing the Python module index page.

### Class attributes
- **`name`**: `'modindex'`.
- **`localname`**: `_('Python Module Index')`.
- **`shortname`**: `_('modules')`.

### Method `generate(self, docnames: Iterable[str] = None) -> Tuple[List[Tuple[str, List[IndexEntry]]], bool]`
Gets `modindex_common_prefix` from config (sorted by length descending). Gets sorted modules from domain data. Iterates over each module: skips if docname not in docnames. Strips common prefix from modname per the ignores list. If entire name was stripped, restores original. Groups entries by first lowercase letter of the (possibly-stripped) module name. Determines if it's a submodule (`package != modname`): if so, makes parent a group head on first occurrence; adds dummy entry for orphan submodules. Sets subtype: 1 for package/group-head, 2 for submodule, 0 for top-level. Sets qualifier to `_('Deprecated')` if deprecated. Appends an `IndexEntry`. Tracks `num_toplevels`.

Collapse heuristic: collapse = `(total_modules - num_toplevels) < num_toplevels` (collapse when submodules outnumber top-level modules). Returns sorted content dict and collapse flag.

---

## Class `PythonDomain(Domain)`

The Python language domain, managing objects, modules, cross-references, and indexing.

### Class attributes
- **`name`**: `'py'`.
- **`label`**: `'Python'`.
- **`object_types`**: Dict mapping objtype names to `ObjType` instances with labels and role mappings:
  - `'function'`: ObjType(_('function'), 'func', 'obj')
  - `'data'`: ObjType(_('data'), 'data', 'obj')
  - `'class'`: ObjType(_('class'), 'class', 'exc', 'obj')
  - `'exception'`: ObjType(_('exception'), 'exc', 'class', 'obj')
  - `'method'`: ObjType(_('method'), 'meth', 'obj')
  - `'classmethod'`: ObjType(_('class method'), 'meth', 'obj')
  - `'staticmethod'`: ObjType(_('static method'), 'meth', 'obj')
  - `'attribute'`: ObjType(_('attribute'), 'attr', 'obj')
  - `'module'`: ObjType(_('module'), 'mod', 'obj')
- **`directives`**: Dict mapping directive names to classes: function→PyFunction, data→PyVariable, class→PyClasslike, exception→PyClasslike, method→PyMethod, classmethod→PyClassMethod, staticmethod→PyStaticMethod, attribute→PyAttribute, module→PyModule, currentmodule→PyCurrentModule, decorator→PyDecoratorFunction, decoratormethod→PyDecoratorMethod.
- **`roles`**: Dict mapping role names to `PyXRefRole()` instances: data, exc, class, const, attr, mod, obj (plain); func, meth (with `fix_parens=True`).
- **`initial_data`**: `{'objects': {}, 'modules': {}}`.
- **`indices`**: `[PythonModuleIndex]`.

### Property `objects -> Dict[str, ObjectEntry]`
Returns `self.data.setdefault('objects', {})`. Maps fullname to ObjectEntry.

### Method `note_object(self, name: str, objtype: str, node_id: str, location: Any = None) -> None`
If name already exists in objects, logs a warning about duplicate description (showing other's docname). Sets `self.objects[name] = ObjectEntry(self.env.docname, node_id, objtype)`.

### Property `modules -> Dict[str, ModuleEntry]`
Returns `self.data.setdefault('modules', {})`. Maps modname to ModuleEntry.

### Method `note_module(self, name: str, node_id: str, synopsis: str, platform: str, deprecated: bool) -> None`
Sets `self.modules[name] = ModuleEntry(self.env.docname, node_id, synopsis, platform, deprecated)`.

### Method `clear_doc(self, docname: str) -> None`
Removes all objects and modules whose docname matches the given document.

### Method `merge_domaindata(self, docnames: List[str], otherdata: Dict) -> None`
Merges object/module entries from another domain's data where the entry's docname is in docnames. No duplicate checking.

### Method `find_obj(self, env: BuildEnvironment, modname: str, classname: str, name: str, type: str, searchmode: int = 0) -> List[Tuple[str, ObjectEntry]]`
Strips trailing `'()'` from name. Returns empty list if name is empty. Initializes `matches = []`.

**Search mode 1 (refspecific/fuzzy):** Determines objtypes to match (all types if type is None, else via `objtypes_for_role(type)`). Tries exact matches in order: `modname.classname.name`, `modname.name`, bare `name`. If none found, does fuzzy search: finds all objects ending with `'.' + name` matching the objtypes.

**Search mode 0 (exact):** Checks `name` directly; if type is `'mod'`, returns empty (only exact matches for modules). Otherwise tries `classname.name`, `modname.name`, `modname.classname.name`. If a match found, appends to matches and returns.

### Method `resolve_xref(self, env: BuildEnvironment, fromdocname: str, builder: Builder, type: str, target: str, node: pending_xref, contnode: Element) -> Element`
Extracts `py:module` and `py:class` from the pending_xref node. Determines searchmode (1 if `refspecific`, else 0). Calls `find_obj()`. If no matches and type is `'attr'`, retries with type `'meth'` (for properties). Returns None if still no match. Logs warning if multiple matches found. For module matches, calls `_make_module_refnode()`; otherwise creates a refnode via `make_refnode()`.

### Method `resolve_any_xref(self, env: BuildEnvironment, fromdocname: str, builder: Builder, target: str, node: pending_xref, contnode: Element) -> List[Tuple[str, Element]]`
Extracts module/class context. Calls `find_obj()` with searchmode=1 and type=None (any type). For each match: if module → creates a `'py:mod'` refnode via `_make_module_refnode`; else → creates the appropriate role (`'py:' + role_for_objtype(obj[2])`) refnode. Returns list of `(role, element)` tuples.

### Method `_make_module_refnode(self, builder: Builder, fromdocname: str, name: str, contnode: Node) -> Element`
Gets module info from `self.modules[name]`. Builds title: starts with modname; appends `': ' + synopsis` if present; appends `' (deprecated)'` if deprecated; appends `' (' + platform + ')'` if platform. Returns refnode to the module's docname and node_id.

### Method `get_objects(self) -> Iterator[Tuple[str, str, str, str, str, int]]`
Yields `(modname, modname, 'module', mod.docname, mod.node_id, 0)` for each module. Then yields `(refname, refname, obj.objtype, obj.docname, obj.node_id, 1)` for each non-module object.

### Method `get_full_qualified_name(self, node: Element) -> str`
Gets `py:module`, `py:class`, and `reftarget` from the node. Returns `'.'.join(filter(None, [modname, clsname, target]))` or None if target is None.

---

## Function `builtin_resolver(app: Sphinx, env: BuildEnvironment, node: pending_xref, contnode: Element) -> Element`

Event handler for `'missing-reference'`, priority 900. Suppresses nitpicky warnings for built-in types. Defines nested `istyping(s: str)`: strips `'typing.'` prefix if present, checks if remaining name is in `typing.__all__`.

Logic:
- If node's refdomain ≠ `'py'`, returns None (not handled).
- If reftype is `'class'` or `'obj'` and target is `'None'`, returns contnode.
- If reftype is `'class'` or `'exc'`: checks if the target name corresponds to a built-in class via `inspect.isclass(getattr(builtins, reftarget, None))`; or if it's a typing type via `istyping()`. Returns contnode in either case.
- Otherwise returns None (no resolution).

---

## Function `setup(app: Sphinx) -> Dict[str, Any]`

Sphinx extension entry point. Calls `app.setup_extension('sphinx.directives')`. Registers the PythonDomain via `app.add_domain(PythonDomain)`. Connects `'object-description-transform'` to `filter_meta_fields`. Connects `'missing-reference'` to `builtin_resolver` with priority 900. Returns:
```python
{
    'version': 'builtin',
    'env_version': 2,
    'parallel_read_safe': True,
    'parallel_write_safe': True,
}
```

## sphinx/pycode/ast.py
Here is the complete natural-language specification of `sphinx/pycode/ast.py`:

---

## Module-Level Preamble

### Imports

```python
import sys
from typing import Dict, List, Type
```

Conditional import block (lines 14–21): If `sys.version_info > (3, 8)`, then `import ast`. Otherwise, attempt `from typed_ast import ast3 as ast`; if that fails with `ImportError`, fall back to `import ast` (with a `# type: ignore` comment).

### Constants & Globals

**`OPERATORS`** — A module-level dictionary of type `Dict[Type[ast.AST], str]` mapping AST operator node classes to their string representations. The exact contents are:

| Key | Value |
|-----|-------|
| `ast.Add` | `"+"` |
| `ast.And` | `"and"` |
| `ast.BitAnd` | `"&"` |
| `ast.BitOr` | `"|"` |
| `ast.BitXor` | `"^"` |
| `ast.Div` | `"/"` |
| `ast.FloorDiv` | `"//"` |
| `ast.Invert` | `"~"` |
| `ast.LShift` | `"<<"` |
| `ast.MatMult` | `"@"` |
| `ast.Mult` | `"*"` |
| `ast.Mod` | `"%"` |
| `ast.Not` | `"not"` |
| `ast.Pow` | `"**"` |
| `ast.Or` | `"or"` |
| `ast.RShift` | `">>"` |
| `ast.Sub` | `"-"` |
| `ast.UAdd` | `"+"` |
| `ast.USub` | `"-"` |

---

## Code Objects (Functions)

### Function: `parse(code: str, mode: str = 'exec') -> "ast.AST"`

**Signature:** Takes two parameters — `code` (a string of Python source code) and `mode` (a string, defaulting to `'exec'`). Returns an AST node of type `"ast.AST"`.

**Logic:**
1. Attempts to call `ast.parse(code, mode=mode, type_comments=True)` (line 54). The `type_comments=True` parameter enables parsing of inline type comments; this is available on Python 3.8+.
2. If that raises a `TypeError` (because the installed AST library does not support the `type_comments` keyword), catches it and falls back to calling `ast.parse(code, mode=mode)` without `type_comments`.

**Return value:** The parsed AST root node from whichever `ast.parse` call succeeds.

---

### Function: `unparse(node: ast.AST) -> str`

**Signature:** Takes a single parameter `node` of type `ast.AST`. Returns a string representation of the node.

**Logic — dispatch chain (elif ladder, order matters):**

1. **`None` check:** If `node is None`, returns Python's `None` literal (`return None`).
2. **String check:** If `isinstance(node, str)`, returns the string as-is.
3. **Operator lookup:** If `node.__class__ in OPERATORS`, returns `OPERATORS[node.__class__]`.
4. **`ast.arg`:** If `isinstance(node, ast.arg)`: if `node.annotation` is truthy, returns `"%s: %s" % (node.arg, unparse(node.annotation))`; otherwise returns just `node.arg`.
5. **`ast.arguments`:** Delegates to `unparse_arguments(node)` and returns its result.
6. **`ast.Attribute`:** Returns `"%s.%s" % (unparse(node.value), node.attr)`.
7. **`ast.BinOp`:** Returns `" ".join(unparse(e) for e in [node.left, node.op, node.right])` — left operand, operator, right operand separated by spaces.
8. **`ast.BoolOp`:** Computes `op = " %s " % unparse(node.op)`; returns `op.join(unparse(e) for e in node.values)` — joins all values with the operator surrounded by spaces.
9. **`ast.Bytes`:** Returns `repr(node.s)`.
10. **`ast.Call`:** Builds a list of argument strings: first, `[unparse(e) for e in node.args]`; then, `["%s=%s" % (k.arg, unparse(k.value)) for k in node.keywords]`. Concatenates them and returns `"%s(%s)" % (unparse(node.func), ", ".join(args))`.
11. **`ast.Dict`:** Creates generators for keys `(unparse(k) for k in node.keys)` and values `(unparse(v) for v in node.values)`, zips them into `"k: v"` items, joins with `", "`, wraps in `{}`. Returns `"{" + ", ".join(items) + "}"`.
12. **`ast.Ellipsis`:** Returns the literal string `"..."`.
13. **`ast.Index`:** Returns `unparse(node.value)` (unpacks the index wrapper).
14. **`ast.Lambda`:** Returns `"lambda %s: ..."` where `%s` is `unparse(node.args)`. The body is always replaced with `"..."`.
15. **`ast.List`:** Returns `"[" + ", ".join(unparse(e) for e in node.elts) + "]"`.
16. **`ast.Name`:** Returns `node.id`.
17. **`ast.NameConstant`:** Returns `repr(node.value)`.
18. **`ast.Num`:** Returns `repr(node.n)`.
19. **`ast.Set`:** Returns `"{" + ", ".join(unparse(e) for e in node.elts) + "}"`.
20. **`ast.Str`:** Returns `repr(node.s)`.
21. **`ast.Subscript`:** Returns `"%s[%s]" % (unparse(node.value), unparse(node.slice))`.
22. **`ast.UnaryOp`:** Returns `"%s %s" % (unparse(node.op), unparse(node.operand))`.
23. **`ast.Tuple`:** Returns `", ".join(unparse(e) for e in node.elts)` — note: no surrounding parentheses are added.
24. **`ast.Constant` (version-gated):** If `sys.version_info > (3, 6)` and `isinstance(node, ast.Constant)`, returns `repr(node.value)`. This branch is explicitly placed last to avoid shadowing the more specific node-type branches above.
25. **Fallback:** For any unrecognized AST node type, raises `NotImplementedError('Unable to parse %s object' % type(node).__name__)`.

**Return value:** A string representation of the AST node, or `None` if the input is `None`, or a `NotImplementedError` for unsupported node types.

---

### Function: `unparse_arguments(node: ast.arguments) -> str`

**Signature:** Takes a single parameter `node` of type `ast.arguments`. Returns a string representing the function signature's argument list.

**Logic — step by step:**

1. **Defaults alignment (positional args):**
   - Copies `node.defaults` into a new list `defaults = list(node.defaults)`.
   - Computes `positionals = len(node.args)` (number of regular positional arguments).
   - Initializes `posonlyargs = 0`. If the node has a `posonlyargs` attribute (Python 3.8+), adds `len(node.posonlyargs)` to both `posonlyargs` and `positionals`.
   - Pads `defaults` with leading `None` values: for each index from `len(defaults)` up to `positionals`, inserts `None` at position 0. This aligns defaults so that `defaults[i]` corresponds to the i-th positional argument (including posonlyargs).

2. **Keyword-only defaults alignment:**
   - Copies `node.kw_defaults` into a new list `kw_defaults = list(node.kw_defaults)`.
   - Pads with leading `None` values: for each index from `len(kw_defaults)` up to `len(node.kwonlyargs)`, inserts `None` at position 0. This aligns keyword-only defaults so that `kw_defaults[i]` corresponds to the i-th keyword-only argument.

3. **Build argument string list (`args = []`):**
   - **Positional-only args (Python 3.8+ only, guarded by `hasattr(node, "posonlyargs")`):** For each `(i, arg)` in `node.posonlyargs`, unparses the arg name. If `defaults[i]` is truthy, appends `" = %s"` or `"=%s"` (with a space before `=` only if `arg.annotation` exists) followed by `unparse(defaults[i])`. Appends the resulting string to `args`. After all positional-only args, if any exist (`node.posonlyargs` is truthy), appends the literal `"/"`.
   - **Regular positional args:** For each `(i, arg)` in `node.args`, unparses the name. If `defaults[i + posonlyargs]` is truthy, appends `" = %s"` or `"=%s"` (space before `=` only if annotation exists) followed by `unparse(defaults[i + posonlyargs])`. Appends to `args`.
   - **`*args`:** If `node.vararg` is truthy, appends `"*" + unparse(node.vararg)` to `args`.
   - **Keyword-only separator:** If `node.kwonlyargs` exists but `node.vararg` does not, appends the literal `"*"` (to indicate that following args are keyword-only). For each `(i, arg)` in `node.kwonlyargs`, unparses the name. If `kw_defaults[i]` is truthy, appends `" = %s"` or `"=%s"` (space before `=` only if annotation exists) followed by `unparse(kw_defaults[i])`. Appends to `args`.
   - **`**kwargs`:** If `node.kwarg` is truthy, appends `"**" + unparse(node.kwarg)` to `args`.

4. **Return:** Returns `", ".join(args)` — all argument strings joined by `", "`.

**Return value:** A string representing the full function signature's parameter list (e.g., `"a, b=10, /, c, *args, d, e=20, **kwargs"`).