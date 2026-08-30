## sphinx/domains/python.py
Now I have read the complete file (1406 lines). Here is the full natural-language specification:

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
from typing import Any, Dict, Iterable, Iterator, List, NamedTuple, Tuple, cast

from docutils import nodes
from docutils.nodes import Element, Node
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.addnodes import desc_signature, pending_xref
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.deprecation import RemovedInSphinx40Warning, RemovedInSphinx50Warning
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
from sphinx.util.nodes import make_id, make_refnode
from sphinx.util.typing import TextlikeNode

if False:
    from typing import Type  # for python3.5.1
```

### Constants & Globals

- **`logger`**: `logging.getLogger(__name__)` — module-level logger.

- **`py_sig_re`**: Compiled regex (`re.VERBOSE`) matching Python signatures with groups: `(class_name_prefix)`, `(thing_name)`, `(optional_arguments)`, `(optional_return_annotation)`. Pattern:
  ```
  ^ ([\w.]*\.)?            # class name(s) — group 1 (may be None)
  (\w+)  \s*               # thing name    — group 2
  (?: \(\s*(.*)\s*\)       # optional args  — group 3 (may be None)
   (?:\s* -> \s* (.*))?    # return ann     — group 4 (may be None)
  )? $                     # nothing more
  ```

- **`pairindextypes`**: Dict mapping string keys to localized strings:
  - `'module'` → `_('module')`
  - `'keyword'` → `_('keyword')`
  - `'operator'` → `_('operator')`
  - `'object'` → `_('object')`
  - `'exception'` → `_('exception')`
  - `'statement'` → `_('statement')`
  - `'builtin'` → `_('built-in function')`

- **`ObjectEntry`**: `NamedTuple('ObjectEntry', [('docname', str), ('node_id', str), ('objtype', str)])`.

- **`ModuleEntry`**: `NamedTuple('ModuleEntry', [('docname', str), ('node_id', str), ('synopsis', str), ('platform', str), ('deprecated', bool)])`.

---

## 2. Code Objects (Functions and Classes)

### Function: `type_to_xref(text: str, env: BuildEnvironment = None) -> addnodes.pending_xref`

Converts a type string to a cross-reference node (`pending_xref`). If `text == 'None'`, sets `reftype='obj'`; otherwise `reftype='class'`. If `env` is provided, extracts `'py:module'` and `'py:class'` from `env.ref_context` as kwargs. Returns a `pending_xref` with `refdomain='py'`, `reftarget=text`, and the extracted context kwargs.

### Function: `_parse_annotation(annotation: str, env: BuildEnvironment = None) -> List[Node]`

Parses a type annotation string into a list of docutils `Node` objects using AST-based unparsing. Issues a `RemovedInSphinx50Warning` if `env is None`. Internally defines recursive helper `unparse(node: ast.AST) -> List[Node]` handling these AST node types:
- `ast.Attribute`: returns `[Text("value.attr")]` where value is recursively unparsed.
- `ast.Expr`: delegates to `unparse(node.value)`.
- `ast.Index`: delegates to `unparse(node.value)`.
- `ast.List`: wraps elements with `[`, `, ` between, and `]`; pops trailing comma.
- `ast.Module`: flattens body via `sum(...)`.
- `ast.Name`: returns `[Text(node.id)]`.
- `ast.Subscript`: unparses value + `[` + slice + `]`.
- `ast.Tuple`: unparses elements with `, ` between; empty tuple yields `()` punctuation.
- `ast.Constant` (Python ≥ 3.6): if `value is Ellipsis`, returns `desc_sig_punctuation("...")`; else returns `[Text(node.value)]`.
- `ast.Ellipsis` / `ast.NameConstant` (Python < 3.8): same handling as above.
- Any other type: raises `SyntaxError`.

After unparsing, each `nodes.Text` node in the result is replaced with a `type_to_xref(...)` call. On `SyntaxError`, returns `[type_to_xref(annotation, env)]` (single fallback cross-reference).

### Function: `_parse_arglist(arglist: str, env: BuildEnvironment = None) -> addnodes.desc_parameterlist`

Parses an argument list string using the AST-based signature parser (`signature_from_str`). Creates a `desc_parameterlist`. Iterates over `sig.parameters.values()`, tracking `last_kind`:
- If param is `POSITIONAL_ONLY` and previous was also `POSITIONAL_ONLY` but this one isn't, inserts `/` operator (PEP 570).
- If param is `KEYWORD_ONLY` and previous was `POSITIONAL_OR_KEYWORD`, `POSITIONAL_ONLY`, or `None`, inserts `*` operator (PEP 3102).

For each parameter:
- Creates a `desc_parameter` node.
- If `VAR_POSITIONAL`: prepends `*` operator + name.
- If `VAR_KEYWORD`: prepends `**` operator + name.
- Otherwise: just the name.
- If annotation is not empty: appends `:` + space + parsed annotation nodes (via `_parse_annotation`).
- If default is not empty: if annotation exists, adds space + `=` + space; else just `=`. Then appends an `inline` node with class `'default_value'`.

After the loop, if last kind was `POSITIONAL_ONLY`, appends `/` operator. Returns the parameterlist.

### Function: `_pseudo_parse_arglist(signode: desc_signature, arglist: str) -> None`

A fallback comma-splitting parser for optional-argument syntax like `[foo]`. Creates a `desc_parameterlist` and a stack (initially `[paramlist]`). For each comma-separated argument:
- Strips whitespace.
- While starts with `[`: pushes `desc_optional()` onto stack, adds to parent.
- While starts with `]`: pops from stack.
- Counts trailing `]` (not `[]`) and leading `[`.
- If non-empty after stripping brackets, appends a `desc_parameter(argument, argument)` to the top of the stack.
- Re-pushes `desc_optional()` for each `ends_open`, popping for each `ends_close`.

If the stack is not exactly 1 element at end (mismatched brackets), catches `IndexError` and replaces everything with a single `desc_parameter(arglist, arglist)`. Otherwise appends the paramlist to `signode`.

### Class: `PyXrefMixin`

Provides cross-reference generation methods for Python domain roles. Handles `.` and `~` prefix semantics (like `:class:` links).

- **Method: `make_xref(self, rolename: str, domain: str, target: str, innernode: Type[TextlikeNode] = nodes.emphasis, contnode: Node = None, env: BuildEnvironment = None) -> Node`**
  Calls parent's `make_xref`, sets `result['refspecific'] = True`. If `target` starts with `'.'`: strips prefix from target, uses rest as display text. If starts with `'~'`: strips prefix, uses last segment after `.` as display text. Replaces the first `nodes.Text` in result's traversal with the computed text. Returns result.

- **Method: `make_xrefs(self, rolename: str, domain: str, target: str, innernode: Type[TextlikeNode] = nodes.emphasis, contnode: Node = None, env: BuildEnvironment = None) -> List[Node]`**
  Splits `target` by delimiter regex `\s*[\[\]\(\),](?:\s+or\s)?\s*|\s+or\s+`. For each non-empty sub-target: if it matches a delimiter pattern, appends `contnode or innernode(sub_target)`. Otherwise calls `self.make_xref(...)`. If the original contnode's text equals the full target, splits the contnode per sub-target. Returns list of nodes.

### Class: `PyField(PyXrefMixin, Field)`

Overrides `make_xref`: if `rolename == 'class'` and `target == 'None'`, changes rolename to `'obj'`. Delegates to parent's `make_xref`.

### Class: `PyGroupedField(PyXrefMixin, GroupedField)`

Pass-through; inherits all behavior from both parents.

### Class: `PyTypedField(PyXrefMixin, TypedField)`

Same as `PyField`: if `rolename == 'class'` and `target == 'None'`, changes rolename to `'obj'`. Delegates to parent's `make_xref`.

### Class: `PyObject(ObjectDescription)`

Base class for general Python object descriptions.

- **Class variable**: `allow_nesting = False` (bool).
- **`option_spec`** (dict): `{'noindex': directives.flag, 'noindexentry': directives.flag, 'module': directives.unchanged, 'annotation': directives.unchanged}`.
- **`doc_field_types`** (list of 5 doc field types):
  1. `PyTypedField('parameter', label=_('Parameters'), names=('param','parameter','arg','argument','keyword','kwarg','kwparam'), typerolename='class', typenames=('paramtype','type'), can_collapse=True)`
  2. `PyTypedField('variable', label=_('Variables'), rolename='obj', names=('var','ivar','cvar'), typerolename='class', typenames=('vartype',), can_collapse=True)`
  3. `PyGroupedField('exceptions', label=_('Raises'), rolename='exc', names=('raises','raise','exception','except'), can_collapse=True)`
  4. `Field('returnvalue', label=_('Returns'), has_arg=False, names=('returns','return'))`
  5. `PyField('returntype', label=_('Return type'), has_arg=False, names=('rtype',), bodyrolename='class')`

- **Method: `get_signature_prefix(self, sig: str) -> str`**: Returns `''`. Overridable for prefix text before the object name.
- **Method: `needs_arglist(self) -> bool`**: Returns `False`. Overridable to force empty parameter list.
- **Method: `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`**
  Matches `sig` against `py_sig_re`; raises `ValueError` on no match. Extracts `(prefix, name, arglist, retann)`. Determines `modname` from options or `env.ref_context['py:module']`, and `classname` from `env.ref_context.get('py:class')`:
  - If `classname` exists: if prefix matches classname (or starts with it + `.`), sets `fullname = prefix + name`, strips classname from prefix. If prefix differs, `fullname = classname + '.' + prefix + name`. If no prefix, `fullname = classname + '.' + name`.
  - Else (`classname` is None): if prefix exists, `classname = prefix.rstrip('.')`, `fullname = prefix + name`; else `classname = ''`, `fullname = name`.

  Sets `signode['module']`, `signode['class']`, `signode['fullname']`. Adds signature prefix via `desc_annotation` if non-empty. Adds addname (`desc_addname`) for prefix or module (if `config.add_module_names` and modname is not `'exceptions'`). Adds `desc_name(name)`. If arglist exists: tries `_parse_arglist`; falls back to `_pseudo_parse_arglist` on `SyntaxError` or `NotImplementedError`. If no arglist but `needs_arglist()` returns True, adds empty `desc_parameterlist()`. If return annotation exists, parses it and appends `desc_returns(retann)`. If `'annotation'` option present, appends it. Returns `(fullname, prefix)`.

- **Method: `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`**: Raises `NotImplementedError`; must be overridden in subclasses.
- **Method: `add_target_and_index(self, name_cls: Tuple[str, str], sig: str, signode: desc_signature) -> None`**
  Computes `fullname = (modname + '.') + name_cls[0]`. Generates `node_id = make_id(...)`, appends to `signode['ids']`. If `node_id != fullname` and fullname not already in document IDs, also appends fullname. Notes explicit target. Calls `domain.note_object(fullname, self.objtype, node_id)`. If `'noindexentry'` not in options, calls `get_index_text`; if non-empty result, appends `('single', indextext, node_id)` to `self.indexnode['entries']`.
- **Method: `before_content(self) -> None`**
  Handles object nesting. If `self.names` exists and has entries, gets `(fullname, name_prefix)` from last entry. If `allow_nesting`, sets `prefix = fullname`; else if `name_prefix`, strips dots. Sets `env.ref_context['py:class'] = prefix`. If `allow_nesting`, appends to `'py:classes'` list in ref_context. If `'module'` option present, pushes current module onto `'py:modules'` stack and sets new module from option.
- **Method: `after_content(self) -> None`**
  Reverses nesting. Gets `'py:classes'` list; if `allow_nesting`, pops it (ignoring IndexError). Sets `'py:class'` to last element or `None`. If `'module'` in options, pops from `'py:modules'` stack and restores previous module; if stack empty, removes `'py:module'` key.

### Class: `PyModulelevel(PyObject)`

Deprecated class for module-level objects (functions, data). Issues `RemovedInSphinx40Warning` on `run()`.

- **Method: `run(self) -> List[Node]`**: Warns about deprecation via MRO scan; calls `super().run()`.
- **Method: `needs_arglist(self) -> bool`**: Returns `True` if `objtype == 'function'`, else `False`.
- **Method: `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`**
  If `objtype == 'function'`: no modname → `_('%(name)s() (built-in function)')`; with modname → `_('%(name)s() (in module %(modname)s)')`. If `objtype == 'data'`: no modname → `_('%(name)s (built-in variable)')`; with modname → `_('%(name)s (in module %(modname)s)')`. Else returns `''`.

### Class: `PyFunction(PyObject)`

Description of a function.

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'async': directives.flag`.
- **Method: `get_signature_prefix(self, sig: str) -> str`**: Returns `'async '` if `'async'` in options; else `''`.
- **Method: `needs_arglist(self) -> bool`**: Returns `True`.
- **Method: `add_target_and_index(self, name_cls: Tuple[str, str], sig: str, signode: desc_signature) -> None`**
  Calls parent's method. If `'noindexentry'` not in options: gets modname and node_id. If modname exists, appends `('single', _('%(name)s() (in module %(modname)s)'))`; else appends `('pair', '%s; %s()' % (pairindextypes['builtin'], name))`.
- **Method: `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`**: Returns `None` (index handled in `add_target_and_index`).

### Class: `PyDecoratorFunction(PyFunction)`

Description of a decorator.

- **Method: `run(self) -> List[Node]`**: Sets `self.name = 'py:function'`, calls `super().run()`.
- **Method: `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`**
  Calls parent's method; inserts `desc_addname('@', '@')` at position 0 of signode. Returns result.
- **Method: `needs_arglist(self) -> bool`**: Returns `False`.

### Class: `PyVariable(PyObject)`

Description of a variable.

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'type': directives.unchanged, 'value': directives.unchanged`.
- **Method: `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`**
  Calls parent's method for `(fullname, prefix)`. If `'type'` option exists, parses it via `_parse_annotation`, appends `desc_annotation(typ, '', Text(': '), *annotations)`. If `'value'` option exists, appends `desc_annotation(value, ' = ' + value)`. Returns `(fullname, prefix)`.
- **Method: `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`**
  With modname → `_('%(name)s (in module %(modname)s)')`; without → `_('%(name)s (built-in variable)')`.

### Class: `PyClasslike(PyObject)`

Description of class-like objects (classes, interfaces, exceptions).

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'final': directives.flag`.
- **`allow_nesting = True`**.
- **Method: `get_signature_prefix(self, sig: str) -> str`**
  If `'final'` in options: returns `'final %(objtype)s '`; else returns `'%(objtype)s '`.
- **Method: `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`**
  If `objtype == 'class'`: no modname → `_('%(name)s (built-in class)')`; with modname → `_('%(name)s (class in %(modname)s)')`. If `objtype == 'exception'`: returns just the name. Else returns `''`.

### Class: `PyClassmember(PyObject)`

Base for class members (methods, attributes). Deprecated; issues `RemovedInSphinx40Warning` on `run()`.

- **Method: `run(self) -> List[Node]`**: Warns via MRO scan; calls `super().run()`.
- **Method: `needs_arglist(self) -> bool`**: Returns `True` if `objtype.endswith('method')`, else `False`.
- **Method: `get_signature_prefix(self, sig: str) -> str`**
  If `objtype == 'staticmethod'`: returns `'static '`; if `objtype == 'classmethod'`: returns `'classmethod '`; else `''`.
- **Method: `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`**
  For each objtype (`method`, `staticmethod`, `classmethod`, `attribute`): tries to split name by last `.` into `(clsname, methname/attrname)`. If split fails and modname exists, returns module-based text; if no modname, returns bare name. With modname + `add_module_names`: includes full path (`modname.clsname`). Without: uses just `clsname`. Returns localized strings like `'%(meth)s() (%(cls)s method)'`, etc. For attribute without split and no modname, returns bare name.

### Class: `PyMethod(PyObject)`

Description of a method.

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'abstractmethod': directives.flag, 'async': directives.flag, 'classmethod': directives.flag, 'final': directives.flag, 'property': directives.flag, 'staticmethod': directives.flag`.
- **Method: `needs_arglist(self) -> bool`**: Returns `False` if `'property'` in options; else `True`.
- **Method: `get_signature_prefix(self, sig: str) -> str`**
  Builds prefix list from options in order: `'final'`, `'abstractmethod'`, `'async'`, `'classmethod'`, `'property'`, `'staticmethod'`. Joins with space + trailing space if non-empty; else returns `''`.
- **Method: `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`**
  Tries to split name by last `.` into `(clsname, methname)`. If modname and `add_module_names`, prepends modname to clsname. On split failure with modname → module-based text; without → bare name. Based on options: `'classmethod'` → `'%(meth)s() (%(cls)s class method)'`; `'property'` → `'%(meth)s() (%(cls)s property)'`; `'staticmethod'` → `'%(meth)s() (%(cls)s static method)'`; else → `'%(meth)s() (%(cls)s method)'`.

### Class: `PyClassMethod(PyMethod)`

Description of a classmethod.

- **`option_spec`**: Copies `PyObject.option_spec` (not PyMethod's).
- **Method: `run(self) -> List[Node]`**
  Sets `self.name = 'py:method'`, sets `self.options['classmethod'] = True`. Calls `super().run()`.

### Class: `PyStaticMethod(PyMethod)`

Description of a staticmethod.

- **`option_spec`**: Copies `PyObject.option_spec`.
- **Method: `run(self) -> List[Node]`**
  Sets `self.name = 'py:method'`, sets `self.options['staticmethod'] = True`. Calls `super().run()`.

### Class: `PyDecoratorMethod(PyMethod)`

Description of a decorator method.

- **Method: `run(self) -> List[Node]`**: Sets `self.name = 'py:method'`, calls `super().run()`.
- **Method: `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`**
  Calls parent's method; inserts `desc_addname('@', '@')` at position 0. Returns result.
- **Method: `needs_arglist(self) -> bool`**: Returns `False`.

### Class: `PyAttribute(PyObject)`

Description of an attribute.

- **`option_spec`**: Copies `PyObject.option_spec`, adds `'type': directives.unchanged, 'value': directives.unchanged`.
- **Method: `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`**
  Calls parent's method for `(fullname, prefix)`. If `'type'` option exists, parses via `_parse_annotation`, appends `desc_annotation(typ, '', Text(': '), *annotations)`. If `'value'` option exists, appends `desc_annotation(value, ' = ' + value)`. Returns `(fullname, prefix)`.
- **Method: `get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str`**
  Tries to split name by last `.` into `(clsname, attrname)`. If modname and `add_module_names`, prepends modname. On failure with modname → `_('%(name)s (in module %(modname)s)')`; without → bare name. Returns `'%(attr)s (%(cls)s attribute)'`.

### Class: `PyDecoratorMixin`

Deprecated mixin for decorator directives. Issues `RemovedInSphinx50Warning` on `handle_signature()`.

- **Method: `handle_signature(self, sig: str, signode: desc_signature) -> Tuple[str, str]`**
  Warns about deprecation via MRO scan; calls parent's method (type: ignore); inserts `desc_addname('@', '@')` at position 0. Returns result.
- **Method: `needs_arglist(self) -> bool`**: Returns `False`.

### Class: `PyModule(SphinxDirective)`

Directive to mark a new module description.

- **Class attributes**: `has_content = False`, `required_arguments = 1`, `optional_arguments = 0`, `final_argument_whitespace = False`.
- **`option_spec`** (dict): `'platform': lambda x: x, 'synopsis': lambda x: x, 'noindex': directives.flag, 'deprecated': directives.flag`.
- **Method: `run(self) -> List[Node]`**
  Gets domain via `cast(PythonDomain, self.env.get_domain('py'))`. Strips module name from first argument. Sets `env.ref_context['py:module'] = modname`. If not `'noindex'`: generates `node_id`, creates `nodes.target(...)` with `ismod=True`; also generates old-style node_id for backward compatibility (appends if different and not already in document IDs). Notes explicit target. Calls `domain.note_module(modname, node_id, synopsis, platform, deprecated)`. Also calls `domain.note_object(modname, 'module', node_id)`. Appends target to result list. Creates index entry with pair text `'%(pairindextypes['module'])s; %(modname)s'`. Returns `[target, inode]` (or empty if noindex).
- **Method: `make_old_id(self, name: str) -> str`**: Returns `'module-%s' % name`.

### Class: `PyCurrentModule(SphinxDirective)`

Directive to set the current module context without creating an index entry.

- **Class attributes**: `has_content = False`, `required_arguments = 1`, `optional_arguments = 0`, `final_argument_whitespace = False`.
- **`option_spec`** (dict): `{}`.
- **Method: `run(self) -> List[Node]`**
  Strips module name from first argument. If `'None'`, removes `'py:module'` from ref_context; else sets it to the module name. Returns empty list.

### Class: `PyXRefRole(XRefRole)`

Custom cross-reference role for Python domain.

- **Method: `process_link(self, env: BuildEnvironment, refnode: Element, has_explicit_title: bool, title: str, target: str) -> Tuple[str, str]`**
  Sets `'py:module'` and `'py:class'` on refnode from `env.ref_context`. If no explicit title: strips leading `.` from title (only meaningful for target), strips leading `~` from target. If title starts with `~`: removes it, then truncates at last `.` to show only the final component. If target starts with `.`: strips it and sets `'refspecific' = True`. Returns `(title, target)`.

### Function: `filter_meta_fields(app: Sphinx, domain: str, objtype: str, content: Element) -> None`

Signal handler for `'object-description-transform'`. If `domain != 'py'`, returns immediately. Otherwise, traverses `content` nodes; if a `nodes.field_list` is found, iterates its fields; if any field's body text (stripped) equals `'meta'` or starts with `'meta '`, removes that field from the list and breaks.

### Class: `PythonModuleIndex(Index)`

Index subclass providing the Python module index page.

- **Class attributes**: `name = 'modindex'`, `localname = _('Python Module Index')`, `shortname = _('modules')`.
- **Method: `generate(self, docnames: Iterable[str] = None) -> Tuple[List[Tuple[str, List[IndexEntry]]], bool]`**
  Gets `ignores` from config `'modindex_common_prefix'`, sorted by length descending. Sorts modules (from `domain.data['modules']`) by lowercase name. Iterates through modules: skips if docname not in `docnames`. Strips common prefix per ignore rules; if entire module stripped, restores original. Groups entries by first character of (possibly-stripped) module name into a dict keyed by lowercase letter. Determines if submodule or toplevel: splits on `.`, checks if package differs from modname. If submodule and previous module was the same package, converts last entry's subtype to 1 (group head). If submodule without parent in list, adds dummy entry with subtype 1. Sets subtype 2 for submodules, 0 for top-levels. Increments `num_toplevels` for top-levels. Creates qualifier `'Deprecated'` if deprecated. Appends `IndexEntry(stripped + modname, subtype, docname, node_id, platforms, qualifier, synopsis)`. After loop: collapse = `(len(modules) - num_toplevels < num_toplevels)` (collapse if more submodules than top-levels). Returns sorted content items and collapse flag.

### Class: `PythonDomain(Domain)`

The Python language domain.

- **Class attributes**:
  - `name = 'py'`, `label = 'Python'`.
  - **`object_types`** (dict): Maps objtype strings to `ObjType`: `'function' → ObjType(_('function'), 'func', 'obj')`; `'data' → ObjType(_('data'), 'data', 'obj')`; `'class' → ObjType(_('class'), 'class', 'exc', 'obj')`; `'exception' → ObjType(_('exception'), 'exc', 'class', 'obj')`; `'method' → ObjType(_('method'), 'meth', 'obj')`; `'classmethod' → ObjType(_('class method'), 'meth', 'obj')`; `'staticmethod' → ObjType(_('static method'), 'meth', 'obj')`; `'attribute' → ObjType(_('attribute'), 'attr', 'obj')`; `'module' → ObjType(_('module'), 'mod', 'obj')`.
  - **`directives`** (dict): Maps directive names to classes: `'function'→PyFunction`, `'data'→PyVariable`, `'class'→PyClasslike`, `'exception'→PyClasslike`, `'method'→PyMethod`, `'classmethod'→PyClassMethod`, `'staticmethod'→PyStaticMethod`, `'attribute'→PyAttribute`, `'module'→PyModule`, `'currentmodule'→PyCurrentModule`, `'decorator'→PyDecoratorFunction`, `'decoratormethod'→PyDecoratorMethod`.
  - **`roles`** (dict): Maps role names to `PyXRefRole()` instances: `'data'→PyXRefRole()`, `'exc'→PyXRefRole()`, `'func'→PyXRefRole(fix_parens=True)`, `'class'→PyXRefRole()`, `'const'→PyXRefRole()`, `'attr'→PyXRefRole()`, `'meth'→PyXRefRole(fix_parens=True)`, `'mod'→PyXRefRole()`, `'obj'→PyXRefRole()`.
  - **`initial_data`** (dict): `{'objects': {}, 'modules': {}}`.
  - **`indices`** (list): `[PythonModuleIndex]`.

- **Property: `objects` → `Dict[str, ObjectEntry]`**: Returns `self.data.setdefault('objects', {})`.
- **Method: `note_object(self, name: str, objtype: str, node_id: str, location: Any = None) -> None`**
  If `name` already in objects, logs a warning about duplicate. Sets `self.objects[name] = ObjectEntry(self.env.docname, node_id, objtype)`.
- **Property: `modules` → `Dict[str, ModuleEntry]`**: Returns `self.data.setdefault('modules', {})`.
- **Method: `note_module(self, name: str, node_id: str, synopsis: str, platform: str, deprecated: bool) -> None`**
  Sets `self.modules[name] = ModuleEntry(self.env.docname, node_id, synopsis, platform, deprecated)`.
- **Method: `clear_doc(self, docname: str) -> None`**
  Deletes all objects and modules whose `docname` matches from the domain data.
- **Method: `merge_domaindata(self, docnames: List[str], otherdata: Dict) -> None`**
  Merges objects/modules from `otherdata['objects']`/`otherdata['modules']` where their `docname` is in `docnames`. No duplicate checking.
- **Method: `find_obj(self, env: BuildEnvironment, modname: str, classname: str, name: str, type: str, searchmode: int = 0) -> List[Tuple[str, ObjectEntry]]`**
  Strips trailing `'()'` from name. Returns empty list if name is empty. If `searchmode == 1`: determines objtypes (all or role-specific). Tries exact match with full path (`modname.classname.name`), then partial (`modname.name`), then bare name. On no match, does fuzzy search: finds all objects ending with `'.' + name`. If `searchmode != 1`: tries exact match on bare name; if type is `'mod'`, returns empty (modules require exact match); else tries `classname.name`, `modname.name`, `modname.classname.name` in order. Returns list of `(newname, ObjectEntry)` tuples.
- **Method: `resolve_xref(self, env: BuildEnvironment, fromdocname: str, builder: Builder, type: str, target: str, node: pending_xref, contnode: Element) -> Element`**
  Gets modname and clsname from node attributes. Sets searchmode to 1 if `'refspecific'`, else 0. Calls `find_obj`. If no matches and type is `'attr'`, retries with type `'meth'` (property fallback). Returns None if no matches; logs warning if >1 match. For module obj, calls `_make_module_refnode`; otherwise calls `make_refnode(builder, fromdocname, obj.docname, obj.node_id, contnode, name)`.
- **Method: `resolve_any_xref(self, env: BuildEnvironment, fromdocname: str, builder: Builder, target: str, node: pending_xref, contnode: Element) -> List[Tuple[str, Element]]`**
  Gets modname and clsname. Always uses searchmode 1 (refspecific). For each match: if module → `('py:mod', _make_module_refnode(...))`; else → `('py:' + role_for_objtype(obj.objtype), make_refnode(...))`. Returns list of `(role, element)` tuples.
- **Method: `_make_module_refnode(self, builder: Builder, fromdocname: str, name: str, contnode: Node) -> Element`**
  Gets module entry; builds title as `name + ': ' + synopsis` (if synopsis), `' (deprecated)'` (if deprecated), `' (' + platform + ')'` (if platform). Returns `make_refnode(builder, fromdocname, module.docname, module.node_id, contnode, title)`.
- **Method: `get_objects(self) -> Iterator[Tuple[str, str, str, str, str, int]]`**
  Yields `(modname, modname, 'module', docname, node_id, 0)` for each module. Then yields `(refname, refname, objtype, docname, node_id, 1)` for each non-module object.
- **Method: `get_full_qualified_name(self, node: Element) -> str`**
  Gets `'py:module'`, `'py:class'`, and `'reftarget'` from node. If target is None, returns None; else returns `'.'.join(filter(None, [modname, clsname, target]))`.

### Function: `builtin_resolver(app: Sphinx, env: BuildEnvironment, node: pending_xref, contnode: Element) -> Element`

Signal handler for `'missing-reference'`, priority 900. Skips if `refdomain != 'py'`. If `reftype in ('class', 'obj')` and `reftarget == 'None'`, returns `contnode`. If `reftype in ('class', 'exc')`: checks if reftarget is a built-in class via `inspect.isclass(getattr(builtins, reftarget, None))`; or if it's a typing module type (starts with `'typing.'` then remainder in `typing.__all__`). Returns `contnode` for matches; else returns `None`.

### Function: `setup(app: Sphinx) -> Dict[str, Any]`

Sphinx extension entry point. Calls `app.setup_extension('sphinx.directives')`. Registers `PythonDomain` via `app.add_domain(PythonDomain)`. Connects `'object-description-transform'` to `filter_meta_fields`. Connects `'missing-reference'` to `builtin_resolver` with priority 900. Returns:
```python
{
    'version': 'builtin',
    'env_version': 2,
    'parallel_read_safe': True,
    'parallel_write_safe': True,
}
```

## sphinx/util/docfields.py
Here is the complete natural-language specification of `sphinx/util/docfields.py`:

---

## Module-Level Preamble

### Imports

```python
import warnings
from typing import Any, Dict, List, Tuple, Union, cast

from docutils import nodes
from docutils.nodes import Node

from sphinx import addnodes
from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.util.typing import TextlikeNode
```

Conditional (type-annotation-only, guarded by `if False:`):
```python
from typing import Type  # for python3.5.1
from sphinx.directive import ObjectDescription
from sphinx.environment import BuildEnvironment
```

### Constants & Globals

No module-level constants or globals beyond the conditional type imports above.

---

## Code Objects

### Function: `_is_single_paragraph(node: nodes.field_body) -> bool`

**Purpose:** Determines whether a `nodes.field_body` node contains exactly one paragraph (plus optional system messages).

**Logic:**
1. If `len(node) == 0`, return `False`.
2. If `len(node) > 1`, iterate over all subnodes starting from index 1 (`node[1:]`). For each, if it is **not** an instance of `nodes.system_message`, return `False`.
3. Check whether `node[0]` (the first child) is an instance of `nodes.paragraph`. If yes, return `True`; otherwise return `False`.

**Return:** `bool` — `True` only when the field body has at least one child, all children after index 0 are system messages, and the first child is a paragraph.

---

### Class: `Field`

**Purpose:** A doc field that is **never grouped**. It can have an argument or not; the argument can be linked via a specified `rolename`. The body can also be linked using a `bodyrolename` if it consists of a single inline or text node. Used for fields that usually occur at most once (e.g., `:returns:`).

**Class attributes:**
- `is_grouped = False` — always `False`; this field type is never grouped.
- `is_typed = False` — always `False`.

#### Method: `__init__(self, name: str, names: Tuple[str, ...] = (), label: str = None, has_arg: bool = True, rolename: str = None, bodyrolename: str = None) -> None`

**Logic:**
- Calls no parent. Directly assigns all parameters to instance attributes: `self.name`, `self.names`, `self.label`, `self.has_arg`, `self.rolename`, `self.bodyrolename`.

#### Method: `make_xref(self, rolename: str, domain: str, target: str, innernode: "Type[TextlikeNode]" = addnodes.literal_emphasis, contnode: Node = None, env: "BuildEnvironment" = None) -> Node`

**Purpose:** Creates a single cross-reference node for the given `target`.

**Logic:**
1. If `rolename` is falsy (empty/None), return `contnode or innernode(target, target)` — i.e., either the provided continuation node or a new literal emphasis node wrapping the target string.
2. Otherwise, create an `addnodes.pending_xref` with attributes: empty text content (`''`), `refdomain=domain`, `refexplicit=False`, `reftype=rolename`, `reftarget=target`.
3. Append to this refnode either `contnode` or a new `innernode(target, target)`.
4. If `env` is provided, call `env.get_domain(domain).process_field_xref(refnode)` on it.
5. Return the constructed `refnode`.

**Return:** A single docutils node representing the cross-reference.

#### Method: `make_xrefs(self, rolename: str, domain: str, target: str, innernode: "Type[TextlikeNode]" = addnodes.literal_emphasis, contnode: Node = None, env: "BuildEnvironment" = None) -> List[Node]`

**Logic:** Simply wraps `self.make_xref(...)` in a list and returns it.

**Return:** A single-element `List[Node]`.

#### Method: `make_entry(self, fieldarg: str, content: List[Node]) -> Tuple[str, List[Node]]`

**Logic:** Returns `(fieldarg, content)` unchanged — identity mapping.

**Return:** The tuple `(fieldarg, content)`.

#### Method: `make_field(self, types: Dict[str, List[Node]], domain: str, item: Tuple, env: "BuildEnvironment" = None) -> nodes.field`

**Purpose:** Constructs a complete `nodes.field` from a single field entry.

**Logic:**
1. Unpack `item` into `(fieldarg, content)`.
2. Create `fieldname = nodes.field_name('', self.label)`.
3. If `fieldarg` is truthy: append a `nodes.Text(' ')`, then extend with the result of `self.make_xrefs(self.rolename, domain, fieldarg, nodes.Text, env=env)` — linking the argument name using its rolename.
4. Check if `content` has exactly one element and that element is either a `nodes.Text` or a `nodes.inline` whose sole child is a `nodes.Text`. If so, replace `content` with cross-references produced by `self.make_xrefs(self.bodyrolename, domain, content[0].astext(), contnode=content[0], env=env)`, linking the body text.
5. Create `fieldbody = nodes.field_body('', nodes.paragraph('', '', *content))`.
6. Return `nodes.field('', fieldname, fieldbody)`.

**Return:** A fully constructed `nodes.field` node.

---

### Class: `GroupedField(Field)`

**Purpose:** A doc field that is **grouped** — all fields of this type are merged into one field whose body is a bulleted list. Always has an argument. The argument can be linked via `rolename`. Used for fields that may occur multiple times (e.g., `:raises:`). If `can_collapse` is `True`, the grouped output collapses to a single non-bulleted entry when only one item exists.

**Inheritance:** Extends `Field`.

**Class attributes:**
- `is_grouped = True` — always `True`; this field type is grouped.
- `list_type = nodes.bullet_list` — the node class used for the bulleted list body.

#### Method: `__init__(self, name: str, names: Tuple[str, ...] = (), label: str = None, rolename: str = None, can_collapse: bool = False) -> None`

**Logic:**
- Calls `super().__init__(name, names, label, True, rolename)` — always passes `has_arg=True`.
- Assigns `self.can_collapse = can_collapse`.

#### Method: `make_field(self, types: Dict[str, List[Node]], domain: str, items: Tuple, env: "BuildEnvironment" = None) -> nodes.field`

**Purpose:** Constructs a grouped field from multiple `(fieldarg, content)` pairs.

**Logic:**
1. Create `fieldname = nodes.field_name('', self.label)`.
2. Create `listnode = self.list_type()` (a `nodes.bullet_list`).
3. For each `(fieldarg, content)` in `items`:
   - Create a new `nodes.paragraph()`.
   - Extend it with cross-references from `self.make_xrefs(self.rolename, domain, fieldarg, addnodes.literal_strong, env=env)`.
   - Append `nodes.Text(' -- ')` as separator.
   - Append the `content` nodes.
   - Wrap in a `nodes.list_item('', par)` and append to `listnode`.
4. If `len(items) == 1` **and** `self.can_collapse`:
   - Cast `listnode[0]` as `nodes.list_item`, extract its first child (`list_item[0]`).
   - Create `fieldbody = nodes.field_body('', list_item[0])`.
   - Return `nodes.field('', fieldname, fieldbody)` — a non-bulleted single-line field.
5. Otherwise: create `fieldbody = nodes.field_body('', listnode)`.
6. Return `nodes.field('', fieldname, fieldbody)`.

**Return:** A `nodes.field` node containing either a bulleted list or (when collapsed) the single paragraph directly.

---

### Class: `TypedField(GroupedField)`

**Purpose:** A grouped doc field that also carries **type information** for arguments. The argument can be linked via `rolename`, and the type via `typerolename`. Supports two syntaxes:
- Separate `:param name:` and `:type name:` fields.
- Combined `:param Type name:` inline syntax.

**Inheritance:** Extends `GroupedField`.

**Class attributes:**
- `is_typed = True` — always `True`; this field type carries type info.

#### Method: `__init__(self, name: str, names: Tuple[str, ...] = (), typenames: Tuple[str, ...] = (), label: str = None, rolename: str = None, typerolename: str = None, can_collapse: bool = False) -> None`

**Logic:**
- Calls `super().__init__(name, names, label, rolename, can_collapse)` — note: does **not** pass `has_arg` explicitly (relies on parent's default of `True`).
- Assigns `self.typenames = typenames`.
- Assigns `self.typerolename = typerolename`.

#### Method: `make_field(self, types: Dict[str, List[Node]], domain: str, items: Tuple, env: "BuildEnvironment" = None) -> nodes.field`

**Purpose:** Constructs a typed grouped field from `(fieldarg, content)` pairs, with type information drawn from the `types` dict.

**Inner function: `handle_item(fieldarg: str, content: str) -> nodes.paragraph`**
1. Create a new `nodes.paragraph()`.
2. Extend it with cross-references from `self.make_xrefs(self.rolename, domain, fieldarg, addnodes.literal_strong, env=env)`.
3. If `fieldarg in types`:
   - Append `nodes.Text(' ')`, then `nodes.Text('(')`.
   - **Pop** the type entry: `fieldtype = types.pop(fieldarg)` (to prevent duplicate insertion into the doctree).
   - If `len(fieldtype) == 1` and `isinstance(fieldtype[0], nodes.Text)`: extract `typename = fieldtype[0].astext()`, then extend with cross-references from `self.make_xrefs(self.typerolename, domain, typename, addnodes.literal_emphasis, env=env)`.
   - Otherwise: append the full `fieldtype` node list directly.
   - Append `nodes.Text(')')`.
4. Append `nodes.Text(' -- ')`.
5. Append `content`.
6. Return the paragraph.

**Outer logic:**
1. Create `fieldname = nodes.field_name('', self.label)`.
2. If `len(items) == 1` **and** `self.can_collapse`:
   - Unpack `items[0]` into `(fieldarg, content)`.
   - Call `bodynode = handle_item(fieldarg, content)` — a single paragraph (no list wrapper).
3. Otherwise:
   - Create `bodynode = self.list_type()` (a bulleted list).
   - For each `(fieldarg, content)` in `items`: append `nodes.list_item('', handle_item(fieldarg, content))` to `bodynode`.
4. Create `fieldbody = nodes.field_body('', bodynode)`.
5. Return `nodes.field('', fieldname, fieldbody)`.

**Return:** A `nodes.field` node with typed arguments displayed as `(Type)` after the argument name in a bulleted list (or collapsed to a single paragraph when applicable).

---

### Class: `DocFieldTransformer`

**Purpose:** Transforms raw docutils `field_list` nodes within object descriptions into better-formatted field lists, using domain-specific `Field` type definitions.

#### Class attribute:
- `typemap = None` — type annotation comment only; initialized in `__init__`. Type: `Dict[str, Tuple[Field, bool]]`, mapping field name strings to `(field_type_instance, is_type_field)` tuples.

#### Method: `__init__(self, directive: "ObjectDescription") -> None`

**Logic:**
1. Assign `self.directive = directive`.
2. Try to call `directive.get_field_type_map()` and assign the result to `self.typemap`.
3. If any exception occurs (e.g., third-party extensions calling this transformer directly):
   - Emit a deprecation warning: `'DocFieldTransformer expects given directive object is a subclass of ObjectDescription.'` with category `RemovedInSphinx40Warning`, stack level 2.
   - Fall back to `self.preprocess_fieldtypes(directive.__class__.doc_field_types)` and assign the result to `self.typemap`.

#### Method: `preprocess_fieldtypes(self, types: List[Field]) -> Dict[str, Tuple[Field, bool]]`

**Purpose:** Legacy fallback for building a typemap from a list of field type definitions. Emits a deprecation warning.

**Logic:**
1. Emit deprecation warning: `'DocFieldTransformer.preprocess_fieldtypes() is deprecated.'` with `RemovedInSphinx40Warning`, stack level 2.
2. Initialize empty `typemap = {}`.
3. For each `fieldtype` in `types`:
   - For each name in `fieldtype.names`, set `typemap[name] = (fieldtype, False)`.
   - If `fieldtype.is_typed`: cast `fieldtype` to `TypedField`; for each name in `typed_field.typenames`, set `typemap[name] = (typed_field, True)`.
4. Return `typemap`.

**Return:** A dict mapping field names to `(Field instance, is_type_flag)` tuples.

#### Method: `transform_all(self, node: addnodes.desc_content) -> None`

**Purpose:** Transform all immediate child `field_list` nodes of a `desc_content` node.

**Logic:**
1. Iterate over each direct child of `node`.
2. If the child is an instance of `nodes.field_list`, call `self.transform(child)`.

**Return:** None (in-place mutation).

#### Method: `transform(self, node: nodes.field_list) -> None`

**Purpose:** Transform a single `field_list` node into a reformatted field list. This is the core transformation logic, executed in two phases.

**Phase 1 — Collect fields and content:**
1. Initialize:
   - `entries = []` — list of either raw `nodes.field` objects (pass-through) or `(Field, List)` tuples (grouped entries).
   - `groupindices = {}` — maps field type name to index in `entries` for grouped fields.
   - `types = {}` — nested dict: `{typename: {fieldarg: [type_nodes]}}`.

2. For each `nodes.field` in the list (cast as `List[nodes.field]`, asserting `len(field) == 2`):
   a. Extract `field_name = field[0]` (a `nodes.field_name`) and `field_body = field[1]` (a `nodes.field_body`).
   b. Parse the field name text: try to split on whitespace into `(fieldtype_name, fieldarg)`. If that fails (`ValueError`), treat the entire text as `fieldtype_name` with empty `fieldarg`.
   c. Look up `typedesc, is_typefield = typemap.get(fieldtype_name, (None, None))`.
   d. Collect content: if `_is_single_paragraph(field_body)`, extract `paragraph.children`; otherwise use `field_body.children`.
   e. **Unknown or mismatched fields:** If `typedesc is None` OR `typedesc.has_arg != bool(fieldarg)`:
      - Capitalize the field name: `new_fieldname = fieldtype_name[0:1].upper() + fieldtype_name[1:]`, plus `' ' + fieldarg` if present.
      - Replace `field_name[0]` with a new `nodes.Text(new_fieldname)`.
      - Append the raw `field` to `entries` (pass-through).
      - **Type linking for unknown fields:** If `typedesc and is_typefield and content and len(content)==1 and isinstance(content[0], nodes.Text)`: cast `typedesc` to `TypedField`, extract target text, create cross-references via `make_xrefs(typerolename, ...)`, and replace the paragraph's children with these xrefs (handling both single-paragraph and multi-child body cases).
      - `continue` to next field.
   f. Set `typename = typedesc.name`.
   g. **Type fields (`is_typefield == True`):** Filter content to only inline/text nodes: `[n for n in content if isinstance(n, nodes.Inline) or isinstance(n, nodes.Text)]`. If non-empty, store as `types.setdefault(typename, {})[fieldarg] = content`. `continue`.
   h. **Typed field support (`typedesc.is_typed`):** Try to split `fieldarg` into `(argtype, argname)` on whitespace. On success: store `[nodes.Text(argtype)]` in `types.setdefault(typename, {})[argname]`, and set `fieldarg = argname`.
   i. Wrap content in a translatable inline node: create `translatable_content = nodes.inline(field_body.rawsource, translatable=True)`, copy `document`, `source`, and `line` from `field_body.parent`, then append `content`.
   j. **Grouped vs non-grouped dispatch:**
      - If `typedesc.is_grouped`: check if `typename` already has a group index in `groupindices`. If yes, retrieve the existing `(Field, List)` tuple; if no, create a new entry `(typedesc, [])`, store its index, and append to `entries`. Call `new_entry = typedesc.make_entry(fieldarg, [translatable_content])` and append it to the group's list.
      - If not grouped: call `new_entry = typedesc.make_entry(fieldarg, [translatable_content])` and append `(typedesc, new_entry)` directly to `entries`.

**Phase 2 — Construct the new field list:**
1. Create `new_list = nodes.field_list()`.
2. For each `entry` in `entries`:
   - If it is a raw `nodes.field`, append it directly to `new_list` (pass-through).
   - Otherwise, unpack `(fieldtype, items)`. Look up field-specific types: `fieldtypes = types.get(fieldtype.name, {})`. Get the environment from `self.directive.state.document.settings.env`. Call `fieldtype.make_field(fieldtypes, self.directive.domain, items, env=env)` and append the result to `new_list`.
3. Replace the original node with the new list: `node.replace_self(new_list)`.

**Return:** None (in-place mutation of the doctree).

---