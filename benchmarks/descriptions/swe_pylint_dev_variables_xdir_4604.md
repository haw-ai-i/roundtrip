## pylint/checkers/variables.py
Now I have read every section of the file. Here is the complete specification:

---

# Module Specification: `pylint/checkers/variables.py`

## 1. Module-Level Preamble

### Imports
```python
import collections
import copy
import itertools
import os
import re
from functools import lru_cache

import astroid

from pylint.checkers import BaseChecker, utils
from pylint.checkers.utils import is_postponed_evaluation_enabled
from pylint.constants import PY39_PLUS
from pylint.interfaces import HIGH, INFERENCE, INFERENCE_FAILURE, IAstroidChecker
from pylint.utils import get_global_option
```

### Constants & Globals

| Name | Type | Value |
|------|------|-------|
| `SPECIAL_OBJ` | `re.Pattern` | Compiled regex `^_{2}[a-z]+_{2}$` — matches dunder-style names like `__doc__`, `__all__` |
| `FUTURE` | `str` | `"__future__"` |
| `IGNORED_ARGUMENT_NAMES` | `re.Pattern` | Compiled regex `_.*|^ignored_|^unused_` |
| `METACLASS_NAME_TRANSFORMS` | `dict[str, str]` | `{"_py_abc": "abc"}` — maps Python 3.7+ abc implementation name to canonical module name |
| `TYPING_TYPE_CHECKS_GUARDS` | `frozenset[str]` | `{"typing.TYPE_CHECKING", "TYPE_CHECKING"}` |
| `BUILTIN_RANGE` | `str` | `"builtins.range"` |
| `TYPING_MODULE` | `str` | `"typing"` |
| `TYPING_NAMES` | `frozenset[str]` | 56 typing module type names: `Any, Callable, ClassVar, Generic, Optional, Tuple, Type, TypeVar, Union, AbstractSet, ByteString, Container, ContextManager, Hashable, ItemsView, Iterable, Iterator, KeysView, Mapping, MappingView, MutableMapping, MutableSequence, MutableSet, Sequence, Sized, ValuesView, Awaitable, AsyncIterator, AsyncIterable, Coroutine, Collection, AsyncGenerator, AsyncContextManager, Reversible, SupportsAbs, SupportsBytes, SupportsComplex, SupportsFloat, SupportsInt, SupportsRound, Counter, Deque, Dict, DefaultDict, List, Set, FrozenSet, NamedTuple, Generator, AnyStr, Text, Pattern, BinaryIO` |

### Helper Functions (module-level)

#### `_is_from_future_import(stmt, name)` → `bool | None`
Imports the module referenced by `stmt.modname`, then checks whether any local binding of `name` in that module comes from a `from __future__ import ...`. Returns `True` if found, `None` otherwise. Catches `astroid.AstroidBuildingException` and returns `None`.

#### `in_for_else_branch(parent, stmt)` → `bool`
Returns `True` if `stmt` is inside the `else` branch of a `For` loop whose parent is `parent`. Checks that `parent` is an `astroid.For` and iterates over `parent.orelse`, testing each else-statement with `else_stmt.parent_of(stmt) or else_stmt == stmt`.

#### `overridden_method(klass, name)` → `astroid.FunctionDef | None`
(LRU-cached, maxsize=1000.) Looks up the ancestor class hierarchy of `klass` for a method named `name`. Returns the `FunctionDef` node if found and is indeed a function; otherwise returns `None`.

#### `_get_unpacking_extra_info(node, inferred)` → `str`
Returns an extra-info string appended to unpacking error messages. If both nodes are in the same root module: on the same line, appends `" %s" % inferred.as_string()`; otherwise `" defined at line %s" % inferred.lineno`. If different modules and `inferred.lineno` is set, returns `f" defined at line {inferred.lineno} of {inferred_module}"`.

#### `_detect_global_scope(node, frame, defframe)` → `bool`
Determines whether two frames share a global scope (neither hidden under a function). Returns `True` when: both frames are within module/class scopes only; they resolve to the same top-level scope; and `frame.lineno < defframe.lineno`. Handles special case where `frame` is a `FunctionDef` — returns `False` unless `node.parent` is also a `FunctionDef` or `Arguments`.

#### `_infer_name_module(node, name)` → iterator
Creates an `astroid.context.InferenceContext`, sets `lookupname=name`, and calls `node.infer(context, asname=False)`.

#### `_fix_dot_imports(not_consumed)` → `list[tuple[str, stmt]]`
Expands dotted imports (e.g., `xml.etree`) from the `not_consumed` dict. Skips statements that are augmented assignments. For each import statement, if the imported module name starts with the key and contains a dot, or the key is in the import names, maps the full dotted name to the statement. Returns sorted list by line number.

#### `_find_frame_imports(name, frame)` → `bool | None`
Iterates over all `Import`/`ImportFrom` nodes in `frame`. For each, checks if any alias matches `name`, or if no alias and the import name matches `name`. Returns `True` on match; returns `None` (not `False`) when no match found.

#### `_import_name_is_global(stmt, global_names)` → `bool`
Checks whether any imported name/alias in `stmt.names` is present in `global_names`. Returns `True` if so.

#### `_flattened_scope_names(iterator)` → `set[str]`
Flattens the `.names` attribute of each import statement in the iterator into a single set.

#### `_assigned_locally(name_node)` → `bool`
Checks whether any `AssignName` node in `name_node.scope()` has the same name as `name_node`. Returns `True` if found.

#### `_is_type_checking_import(node)` → `bool`
Returns `True` if `node.parent` is an `astroid.If` whose test expression string is in `TYPING_TYPE_CHECKS_GUARDS`.

#### `_has_locals_call_after_node(stmt, scope)` → `bool`
Iterates over all `Call` nodes in `scope` (skipping `FunctionDef`, `ClassDef`, `Import`, `ImportFrom`). For each call that infers to the builtin `locals()`, returns `True` if `stmt.lineno < call.lineno`.

### MSGS Dictionary
Maps error codes to `(message_string, symbol_name, description)` tuples:

| Code | Symbol | Message Template | Description |
|------|--------|-----------------|-------------|
| E0601 | `used-before-assignment` | `"Using variable %r before assignment"` | Local variable accessed before its assignment. |
| E0602 | `undefined-variable` | `"Undefined variable %r"` | Undefined variable is accessed. |
| E0603 | `undefined-all-variable` | `"Undefined variable name %r in __all__"` | Undefined name referenced in `__all__`. |
| E0604 | `invalid-all-object` | `"Invalid object %r in __all__, must contain only strings"` | Non-string object in `__all__`. |
| E0605 | `invalid-all-format` | `"Invalid format for __all__, must be tuple or list"` | `__all__` is not a tuple/list. |
| E0611 | `no-name-in-module` | `"No name %r in module %r"` | Name cannot be found in a module. |
| W0601 | `global-variable-undefined` | `"Global variable %r undefined at the module level"` | Global statement references a variable not defined at module scope. |
| W0602 | `global-variable-not-assigned` | `"Using global for %r but no assignment is done"` | Global statement with no assignment to that variable. |
| W0603 | `global-statement` | `"Using the global statement"` | Discouraged usage of global statement. |
| W0604 | `global-at-module-level` | `"Using the global statement at the module level"` | Global statement has no effect at module level. |
| W0611 | `unused-import` | `"Unused %s"` | Imported module/variable not used. |
| W0612 | `unused-variable` | `"Unused variable %r"` | Variable defined but not used. |
| W0613 | `unused-argument` | `"Unused argument %r"` | Function/method argument not used. |
| W0614 | `unused-wildcard-import` | `"Unused import %s from wildcard import"` | Imported name unused from `from X import *`. |
| W0621 | `redefined-outer-name` | `"Redefining name %r from outer scope (line %s)"` | Variable hides an outer-scope name. |
| W0622 | `redefined-builtin` | `"Redefining built-in %r"` | Variable/function overrides a builtin. |
| W0631 | `undefined-loop-variable` | `"Using possibly undefined loop variable %r"` | Loop variable used outside the loop. |
| W0632 | `unbalanced-tuple-unpacking` | `"Possible unbalanced tuple unpacking with sequence%s: left side has %d label(s), right side has %d value(s)"` | Unbalanced tuple unpacking in assignment. Old code E0632. |
| E0633 | `unpacking-non-sequence` | `"Attempting to unpack a non-sequence%s"` | Non-sequence used in unpack assignment. Old code W0633. |
| W0640 | `cell-var-from-loop` | `"Cell variable %s defined in loop"` | Variable in closure defined in a loop (all closures get same value). |
| W0641 | `possibly-unused-variable` | `"Possibly unused variable %r"` | Variable might not be used because `locals()` could consume it. |
| W0642 | `self-cls-assignment` | `"Invalid assignment to %s in method"` | Assignment to self/cls in instance/class method. |

### ScopeConsumer
```python
ScopeConsumer = collections.namedtuple("ScopeConsumer", "to_consume consumed scope_type")
```

---

## 2. Code Objects (Classes and Functions)

### `class NamesConsumer`

**Purpose:** Simple data holder for consumed/to-consume/scope-type info of node locals.

#### Attributes
| Attribute | Type | Initialization |
|-----------|------|----------------|
| `_atomic` | `ScopeConsumer` | In `__init__`: `ScopeConsumer(copy.copy(node.locals), {}, scope_type)` — shallow-copies the node's `.locals` dict into `to_consume`, empty dict for `consumed`. |
| `node` | `astroid.NodeNG` | Set to constructor argument. |

#### Methods

**`__init__(self, node, scope_type)`** → None  
Stores `node` and creates `_atomic` with a copy of `node.locals` as `to_consume`, empty dict for `consumed`, and the given `scope_type`.

**`__repr__(self)`** → `str`  
Returns a multi-line string showing `to_consume` keys→values, `consumed` keys→values, and `scope_type`.

**`__iter__(self)`** → iterator  
Delegates to `iter(self._atomic)`.

**`@property to_consume`** → `dict`  
Returns `self._atomic.to_consume`.

**`@property consumed`** → `dict`  
Returns `self._atomic.consumed`.

**`@property scope_type`** → `str`  
Returns `self._atomic.scope_type`.

**`mark_as_consumed(self, name, new_node)`** → None  
Moves `name` from `to_consume` to `consumed`: sets `self.consumed[name] = new_node`, then deletes `self.to_consume[name]`.

**`get_next_to_consume(self, node)`** → `list[astroid.AssignName] | None`  
Looks up the name of `node` in `to_consume`. Returns `None` (and thus no match) if:
- The found node's parent is an `ast.Assign` and that assignment's first target has the same name as `node` (self-referencing assignment like `x = x`).
- The found node's parent is an `ast.For` and the iter expression equals `node`, and the for-loop target is in the found nodes (loop variable definition).

Otherwise returns the list of AST nodes from `to_consume[name]`.

---

### `class VariablesChecker(BaseChecker)`

**Purpose:** Checks for unused variables/imports, undefined variables, redefinition of builtins or outer-scope names, use-before-assignment, `__all__` consistency, self/cls assignment.

#### Class Attributes
| Attribute | Type | Value |
|-----------|------|-------|
| `__implements__` | `IAstroidChecker` | Implements the IAstroidChecker interface. |
| `name` | `str` | `"variables"` |
| `msgs` | `dict` | The `MSGS` dictionary defined at module level. |
| `priority` | `int` | `-1` (runs before other checkers). |

#### Options
| Option Name | Default | Type | Description |
|-------------|---------|------|-------------|
| `init-import` | `0` | `yn` | Check for unused imports in `__init__` files. |
| `dummy-variables-rgx` | `"_+$\|(_[a-zA-Z0-9_]*[a-zA-Z0-9]+?$)\|dummy\|^ignored_\|^unused_"` | `regexp` | Regex matching dummy variable names (expected unused). |
| `additional-builtins` | `()` | `csv` | Additional names to treat as builtins. |
| `callbacks` | `("cb_", "_cb")` | `csv` | Prefix/suffix strings identifying callback functions. |
| `redefining-builtins-modules` | `("six.moves", "past.builtins", "future.builtins", "builtins", "io")` | `csv` | Module qualified names whose objects may redefine builtins without warning. |
| `ignored-argument-names` | `IGNORED_ARGUMENT_NAMES` (regex) | `regexp` | Regex for argument names to ignore. |
| `allow-global-unused-variables` | `True` | `yn` | Whether unused global variables should be flagged. |
| `allowed-redefined-builtins` | `()` | `csv` | Names allowed to shadow builtins. |

#### Instance Attributes (initialized in `__init__`)
| Attribute | Type | Value |
|-----------|------|-------|
| `_to_consume` | `list[NamesConsumer] \| None` | `None` — stack of `(to_consume, consumed, scope_type)` tuples. |
| `_checking_mod_attr` | `str \| None` | `None`. |
| `_loop_variables` | `list[tuple[astroid.For, list[str]]]` | `[]` — tracks loop variables for nested-for redefinition detection. |
| `_type_annotation_names` | `list[str]` | `[]` — names collected from type annotations. |
| `_postponed_evaluation_enabled` | `bool` | `False`. |

#### Cached Properties (via `@astroid.decorators.cachedproperty`)
| Property | Type | Source |
|----------|------|--------|
| `_analyse_fallback_blocks` | `bool` | `get_global_option(self, "analyse-fallback-blocks", default=False)` |
| `_ignored_modules` | `list` | `get_global_option(self, "ignored-modules", default=[])` |
| `_allow_global_unused_variables` | `bool` | `get_global_option(self, "allow-global-unused-variables", default=True)` |

#### Visitor Methods (AST traversal hooks)

**`visit_for(self, node)`** — decorated with `@utils.check_messages("redefined-outer-name")`  
Collects variable names assigned by the for-loop target (`node.target.nodes_of_class(astroid.AssignName)`). Filters out dummy variables matching `self.config.dummy_variables_rgx`. For each remaining variable, checks if it appears in any outer loop's variable list (from `self._loop_variables`) and is not inside an else branch of that outer loop. If so, emits `"redefined-outer-name"` with the outer loop's line number. Appends `(node, assigned_to)` to `self._loop_variables`.

**`leave_for(self, node)`** — decorated with `@utils.check_messages("redefined-outer-name")`  
Pops from `self._loop_variables`. Calls `_store_type_annotation_names(node)`.

**`visit_module(self, node)`**  
Initializes `self._to_consume = [NamesConsumer(node, "module")]`. Sets `_postponed_evaluation_enabled` via `is_postponed_evaluation_enabled(node)`. Iterates over `node.locals.items()`: for each name that is a builtin (per `utils.is_builtin(name)`), if not ignored by `_should_ignore_redefined_builtin()` and not `"__doc__"`, emits `"redefined-builtin"` on the first statement.

**`leave_module(self, node)`** — decorated with `@utils.check_messages("unused-import", "unused-wildcard-import", "redefined-builtin", "undefined-all-variable", "invalid-all-object", "invalid-all-format", "unused-variable")`  
Asserts exactly one consumer in `_to_consume`. Calls `_check_metaclasses(node)`. Pops the consumer and gets `not_consumed = to_consume`. If `"__all__"` is in `node.locals`, calls `_check_all(node, not_consumed)`. Calls `_check_globals(not_consumed)`. If `init_import` config is False and node is a package, returns early. Otherwise calls `_check_imports(not_consumed)`.

**`visit_classdef(self, node)`**  
Pushes `NamesConsumer(node, "class")` onto `_to_consume`.

**`leave_classdef(self, _)`**  
Pops from `_to_consume`. No unused-local checks performed.

**`visit_lambda(self, node)`**  
Pushes `NamesConsumer(node, "lambda")` onto `_to_consume`.

**`leave_lambda(self, _)`**  
Pops from `_to_consume`. No unused-local checks.

**`visit_generatorexp(self, node)`**  
Pushes `NamesConsumer(node, "comprehension")` onto `_to_consume`.

**`leave_generatorexp(self, _)`**  
Pops from `_to_consume`.

**`visit_dictcomp(self, node)`**  
Pushes `NamesConsumer(node, "comprehension")` onto `_to_consume`.

**`leave_dictcomp(self, _)`**  
Pops from `_to_consume`.

**`visit_setcomp(self, node)`**  
Pushes `NamesConsumer(node, "comprehension")` onto `_to_consume`.

**`leave_setcomp(self, _)`**  
Pops from `_to_consume`.

**`visit_functiondef(self, node)`** — also aliased as `visit_asyncfunctiondef = visit_functiondef`  
Pushes `NamesConsumer(node, "function")` onto `_to_consume`. If `"redefined-outer-name"` or `"redefined-builtin"` messages are enabled: iterates over `node.items()` (local names and their statements). For each name in the module globals (`node.root().globals`) where the statement is not a `Global`:
- Skips if it's a `__future__` import.
- Skips if any definition is inside a type-checking guard (`TYPE_CHECKING`).
- Otherwise emits `"redefined-outer-name"` with the definition line number (if `_is_name_ignored` returns False).

For names that are builtins: if not allowed by `_allowed_redefined_builtin()` and not ignored by `_should_ignore_redefined_builtin()`, emits `"redefined-builtin"`.

**`leave_functiondef(self, node)`** — also aliased as `leave_asyncfunctiondef = leave_functiondef`  
Calls `_check_metaclasses(node)`. Stores type annotation nodes from `type_comment_returns` and `type_comment_args`. Pops the consumer to get `not_consumed`. If unused-variable/possibly-unused-variable/unused-argument messages are disabled, returns. Skips if function is an error handler (`utils.is_error(node)`). Skips abstract methods. Gets flattened global/nonlocal names via `_flattened_scope_names()`. For each `(name, stmts)` in `not_consumed`, calls `_check_is_unused(name, node, stmts[0], global_names, nonlocal_names)`.

**`visit_global(self, node)`** — decorated with `@utils.check_messages("global-variable-undefined", "global-variable-not-assigned", "global-statement", "global-at-module-level", "redefined-builtin")`  
If the frame is a module, emits `"global-at-module-level"` and returns. Gets the root module. For each name in `node.names`:
- Tries `module.getattr(name)` to find assignments; catches `NotFoundError` → empty list.
- Checks if not locally defined by import.
- If no assign nodes and not locally imported: emits `"global-variable-not-assigned"`, sets `default_message = False`.
- For each assign node: if it's an `AssignName` in module special attributes, emits `"redefined-builtin"` and breaks. If the frame is the module, breaks (module-level assignment found).
- After loop (`else`): if no local import and no module-level assignment found, emits `"global-variable-undefined"`, sets `default_message = False`.

If `default_message` remains True after all names, emits `"global-statement"` once.

**`visit_assignname(self, node)`**  
If the assignment type is `AugAssign`, delegates to `self.visit_name(node)`.

**`visit_delname(self, node)`**  
Delegates to `self.visit_name(node)`.

**`visit_name(self, node)`** — core name resolution logic  
Skips if statement line number is None (live code). Gets `name = node.name`, `frame = stmt.scope()`, `start_index = len(self._to_consume) - 1`. Checks whether `"undefined-variable"` and `"used-before-assignment"` messages are enabled.

Iterates through scopes from innermost to outermost (`range(start_index, -1, -1)`):
1. **Class scope filtering:** If current consumer is a class scope and either `is_ancestor_name()` matches or (not the start index) `_ignore_class_scope(node)` returns True → skip this scope.
2. **Keyword in class def:** If class scope and node parent is a `Keyword` whose grandparent is a `ClassDef` → skip.
3. **Function definition context:** If function scope and `_defined_in_function_definition(node, current_consumer.node)` → skip (annotations/decorators are not in the body).
4. **Lambda default argument:** If lambda scope and `is_default_argument(node, ...)` → skip.
5. **Already consumed:** If name is in `consumed` (and no homonym in upper function scope for comprehensions), resolves the definition node, calls `_check_late_binding_closure()` and `_loopvar_name()`, then breaks.
6. **Find definition:** Calls `get_next_to_consume(node)`. If None → continue to next outer scope.
7. **Use-before-assignment check:** Gets `defnode` via `assign_parent()`. If the relevant messages are enabled and defnode is not None:
   - Calls `_check_late_binding_closure(node, defnode)`.
   - Gets `defstmt`, `defframe`.
   - Checks for recursive class self-reference (`recursive_klass`).
   - Special rule for self-referential class in lambda: if inside a lambda and not a direct default argument under the parent self-referring class → break (no undefined-variable possible).
   - Calls `_is_variable_violation(...)` to determine `(maybee0601, annotation_return, use_outer_definition)`.
   - If `use_outer_definition` → continue.
   - If `maybee0601` and not defined before (`not utils.is_defined_before(node)`) and not NameError-excepted:
     - Checks for same-statement cases (augmented assignment, delete, recursive class, annotation return). For these, emits `"undefined-variable"` if not NameError-ignored and not postponed-evaluable.
     - Else if scope is not lambda: emits `"used-before-assignment"` (unless postponed-evaluable).
     - Else if lambda in class scope with name in frame.locals: checks argument defaults line ordering; emits `"used-before-assignment"` or `"undefined-variable"` as appropriate.
     - Else if lambda comprehension scope: emits `"undefined-variable"`.
8. Marks the name as consumed via `current_consumer.mark_as_consumed(name, found_node)`. Calls `_loopvar_name(node, name)`. Breaks out of the loop.

If no consumer found (else branch): checks if undefined-variable is enabled and name is not a builtin/module scope attr/additional-builtin/special `__class__` in method → emits `"undefined-variable"` unless `node_ignores_exception(node, NameError)`.

**`visit_import(self, node)`** — decorated with `@utils.check_messages("no-name-in-module")`  
If not analyzing fallback blocks and is from a fallback block → return. For each `(name, _)` in `node.names`: splits into parts; infers the first part's module via `_infer_name_module`; if it's an `astroid.Module`, calls `_check_module_attrs(node, module, parts[1:])`.

**`visit_importfrom(self, node)`** — decorated with `@utils.check_messages("no-name-in-module")`  
Same fallback-block check. Splits `node.modname` into parts; imports the first part's module via `do_import_module`; calls `_check_module_attrs(node, module, name_parts[1:])`. For each non-wildcard imported name, calls `_check_module_attrs(node, module, name.split("."))`.

**`visit_assign(self, node)`** — decorated with `@utils.check_messages("unbalanced-tuple-unpacking", "unpacking-non-sequence", "self-cls-assignment")`  
Calls `_check_self_cls_assign(node)`. If the first target is not a Tuple/List → return. Gets iterated targets. Infers `node.value`; if not None, calls `_check_unpacking(inferred, node, targets)`. Catches `InferenceError` and returns.

**`visit_listcomp(self, node)`** — aliased: `visit_listcomp = visit_dictcomp` equivalent  
Pushes `NamesConsumer(node, "comprehension")` onto `_to_consume`.

**`leave_listcomp(self, _)`** — aliased: `leave_listcomp = leave_dictcomp` equivalent  
Pops from `_to_consume`.

**`leave_assign(self, node)`**  
Calls `_store_type_annotation_names(node)`.

**`leave_with(self, node)`**  
Calls `_store_type_annotation_names(node)`.

**`visit_arguments(self, node)`**  
For each `type_comment_args`, calls `_store_type_annotation_node(annotation)`.

---

#### Internal Helper Methods

**`_defined_in_function_definition(node, frame)` → `bool` (static)**  
Returns True if `node` is within a function definition's annotation/default/decorator/return type context. Checks: node in any of the args' annotations; node is parented by args; node is parented by decorators; node is or is parented by the return annotation. Only applies when frame is a FunctionDef and node's statement is that frame.

**`_in_lambda_or_comprehension_body(node, frame)` → `bool` (static)**  
Walks up from `node` to root. Returns True if it encounters a Lambda body (not args) or a Comprehension body/generator expression body (not the first generator's iter). Returns False if it reaches `frame` first.

**`_is_variable_violation(node, name, defnode, stmt, defstmt, frame, defframe, base_scope_type, recursive_klass)` → `(bool, bool, bool)` (static)**  
Determines whether a variable access constitutes a "used-before-assignment" violation. Returns `(maybee0601, annotation_return, use_outer_definition)`.

Logic:
- If `frame != defframe`: calls `_detect_global_scope()` to set `maybee0601`.
- Else if `defframe.parent is None` (module level): checks builtins; if builtin exists → `maybee0601 = False`.
- Else (same local scope): checks for outer/builtin definitions via `defframe.root().lookup(name)`. If found and statement matches, sets `use_outer_definition = True` (unless defnode is a Comprehension). Checks for nonlocal declarations.
- Lambda + class scope special rule: if base_scope_type is lambda and frame is ClassDef with name in locals → checks default argument ordering; `maybee0601 = not (defnode is Arguments and node in defaults and class_def_lineno < defstmt_lineno)`.
- ClassDef frame, FunctionDef usage: if node is the function's return annotation and defframe contains it → `annotation_return = True`. If name matches class name and defined before frame → `maybee0601 = False`. If node parent is Arguments → checks line ordering.
- Recursive klass → `maybee0601 = True`.
- Otherwise: `maybee0601` depends on `stmt.fromlineno <= defstmt.fromlineno`. Special same-line cases: single-statement function, assignment expression (walrus), named expressions — all set `maybee0601 = False`.
- Type-checking guard imports: if defstmt is Import/ImportFrom inside a TYPE_CHECKING If block and the node is not in that branch and name is not defined in both branches → `maybee0601 = True`.

**`_ignore_class_scope(self, node)` → `bool`**  
Returns True to skip class scope lookup. Checks if node is in annotation/default/decorator context or ancestor list; uses parent's scope locals in that case, otherwise frame's locals. Returns negation of: (frame is ClassDef or in defn context) AND not in lambda/comprehension body AND name in frame_locals.

**`_loopvar_name(self, node, name)`**  
Checks for undefined loop variable usage outside the loop. Gets assignment statements via `node.lookup(name)`. If inside a function defined within the same loop → safe (returns). Filters assignments by statement/parent relationship and for-else branches. If exactly one assignment remains:
- Must be from For/Comprehension/GeneratorExp, and not on the same statement as node.
- If not a For: emits `"undefined-loop-variable"`.
- If For: infers the iterated object. `range()` is always safe. Literal sequences (List, Tuple, Dict, Set, FrozenSet) are checked for empty elements → emit if empty. Otherwise emits `"undefined-loop-variable"` for non-sequence iterators.

**`_check_is_unused(self, name, node, stmt, global_names, nonlocal_names)`**  
Checks whether an unconsumed variable should be flagged as unused.
- Skips if `_is_name_ignored()` matches (dummy variables/arguments).
- Skips auto-generated `__class__` in function scope.
- Skips imports assigned to global statements (`_import_name_is_global`).
- If name is an argument: delegates to `_check_unused_arguments()`.
- Otherwise: if parent is Assign/AnnAssign and name is nonlocal → skip.
- For Import/ImportFrom, extracts `qname` and `asname`; updates `name = asname or qname`.
- If `_has_locals_call_after_node()` → message is `"possibly-unused-variable"`, else `"unused-variable"` for regular vars or `"unused-import"` for imports.
- Skips decorated functions and overload stubs.
- Emits the appropriate message.

**`_is_name_ignored(self, stmt, name)` → `bool`**  
Returns True if the name matches a configured regex. For argument nodes (AssignName whose parent is Arguments, or Arguments itself), uses `self.config.ignored_argument_names`; otherwise uses `self.config.dummy_variables_rgx`.

**`_check_unused_arguments(self, name, node, stmt, argnames)`**  
Checks unused function/method arguments.
- Sets confidence: INFERENCE if method in class with known bases; INFERENCE_FAILURE if unknown bases; HIGH otherwise.
- Skips first argument of non-static methods.
- Skips overridden method arguments (via `overridden_method()`).
- Skips Python magic methods except `__init__`/`__new__`.
- Skips callback-named functions (matching `self.config.callbacks`).
- Skips singledispatch-registered functions, overload stubs, protocol classes.
- Otherwise emits `"unused-argument"`.

**`_check_late_binding_closure(self, node, assignment_node)`**  
Detects cell-var-from-loop issues in closures.
- If scope is not Lambda/FunctionDef → return. Skips if parent is Arguments (default).
- If assignment_node is Comprehension and its grandparent contains the scope → emits `"cell-var-from-loop"`.
- Otherwise walks up from assignment_node to find a For loop. If found, the scope is inside it, not a direct lambda call, and not a return statement → emits `"cell-var-from-loop"`.

**`_should_ignore_redefined_builtin(self, stmt)` → `bool`**  
Returns True if stmt is an ImportFrom from a module in `self.config.redefining_builtins_modules`.

**`_allowed_redefined_builtin(self, name)` → `bool`**  
Returns True if name is in `self.config.allowed_redefined_builtins`.

**`_has_homonym_in_upper_function_scope(self, node, index)` → `bool`**  
Walks backward through `_to_consume` from `index-1` to 0. Returns True if any consumer with scope_type `"function"` has the node's name in its `to_consume`.

**`_store_type_annotation_node(self, type_annotation)`**  
Stores names referenced by a type annotation into `self._type_annotation_names`.
- If Name: appends `.name`.
- If Subscript with Attribute value where expr is Name `"typing"`: appends `"typing"`.
- Otherwise: extends with all Name node names in the annotation.

**`_store_type_annotation_names(self, node)`**  
Extracts `node.type_annotation` and calls `_store_type_annotation_node()` if present.

**`_check_self_cls_assign(self, node)`**  
Checks for invalid assignment to self/cls in methods.
- Collects target names from targets that are AssignName.
- Checks for nonlocal statements with matching names → uses parent scope instead.
- If not a method (or is staticmethod) → return.
- Gets first argument name (`self_cls_name`). If any target matches it, emits `"self-cls-assignment"`.

**`_check_unpacking(self, inferred, node, targets)`**  
Checks for unbalanced tuple unpacking and non-sequence unpacking.
- Skips inside abstract classes, comprehensions, Uninferable, vararg assignments.
- If inferred is Tuple/List: gets iterated values; if count differs from targets (and no starred targets) → emits `"unbalanced-tuple-unpacking"` with extra info.
- Else if not iterable → emits `"unpacking-non-sequence"`.

**`_check_module_attrs(self, node, module, module_names)`** → `astroid.Module | None`  
Checks that a chain of attribute names exists in a module. Pops names one at a time; for each, tries to get and infer the attribute. If NotFoundError: if module is ignored → return None; else emits `"no-name-in-module"` and returns None. If InferenceError → return None. When all names resolved, if remaining names exist (partial resolution), emits `"no-name-in-module"`. Returns the final module if it's an astroid.Module, else None.

**`_check_all(self, node, not_consumed)`**  
Validates `__all__` definitions.
- Infers `__all__`; if Uninferable → return.
- If not Tuple/List → emits `"invalid-all-format"`.
- For each element: infers it; skips Uninferable/no-parent. If not a string Const → emits `"invalid-all-object"`.
- If the string is in `not_consumed`, removes it (it's exported).
- If not in node.locals: if not a package → emits `"undefined-all-variable"`; if package, tries to resolve as submodule via `astroid.modutils.file_from_modpath()`; on ImportError → emits `"undefined-all-variable"`.

**`_check_globals(self, not_consumed)`**  
If `_allow_global_unused_variables` is False, iterates over all unconsumed names and emits `"unused-variable"` for each.

**`_check_imports(self, not_consumed)`**  
Checks unused imports.
- Calls `_fix_dot_imports(not_consumed)` to expand dotted imports into `local_names`.
- For each `(name, stmt)`: resolves the real import name and alias. Skips if already checked or name doesn't match real/alias.
- For `Import` (or `from X import ...` with empty modname): skips special objects (`SPECIAL_OBJ`), type annotation imports, `_` aliases. Emits `"unused-import"` with appropriate message format unless inside a type-checking guard.
- For `ImportFrom` with non-empty modname: skips special objects, future reimports, type annotation imports. If wildcard import → emits `"unused-wildcard-import"`. Otherwise emits `"unused-import"` (unless type-checking guarded).
- Deletes `self._to_consume`.

**`_check_metaclasses(self, node)`**  
Updates consumption analysis for metaclass references to avoid false positives. Iterates over children; if ClassDef, calls `_check_classdef_metaclasses()`. Pops consumed items from scope locals.

**`_check_classdef_metaclasses(self, klass, parent_node)` → `list[tuple[dict, str]]`**  
Handles metaclass name consumption to avoid unused-import false positives.
- If no explicit metaclass (`klass._metaclass`) → return [].
- Extracts the metaclass name from `klass._metaclass` (Name node, or Attribute chain's root Name). Applies `METACLASS_NAME_TRANSFORMS`.
- Searches `_to_consume` from innermost scope for the name; if found, records `(scope_locals, name)` in consumed list.
- If not found and no metaclass: re-extracts name; if still present and not in scope_attrs/builtins/additional_builtins/parent.locals → emits `"undefined-variable"`.
- Returns the consumed list for later popping.

---

### `register(linter)` → None
Required entry point. Creates a `VariablesChecker(linter)` instance and registers it with the linter via `linter.register_checker()`.

## pylint/constants.py
Here is the complete natural-language specification of `pylint/constants.py`:

---

## Module-Level Preamble

### Imports

- `import sys` — standard library, used for runtime version introspection.
- `import astroid` — third-party dependency, used to read its own `__version__`.
- `from pylint.__pkginfo__ import __version__` — internal package metadata; provides the pylint version string.

### Constants & Globals

| Name | Type | Value / Description |
|---|---|---|
| `PY38_PLUS` | `bool` | `sys.version_info[:2] >= (3, 8)` — True when running on Python ≥ 3.8. |
| `PY39_PLUS` | `bool` | `sys.version_info[:2] >= (3, 9)`. |
| `PY310_PLUS` | `bool` | `sys.version_info[:2] >= (3, 10)`. |
| `PY_EXTS` | `tuple[str, ...]` | `(".py", ".pyc", ".pyo", ".pyw", ".so", ".dll")` — file extensions associated with Python modules. |
| `MSG_STATE_CONFIDENCE` | `int` | `2`. |
| `_MSG_ORDER` | `str` | `"EWRCIF"` — ordering string for message severity levels (Error, Warning, Refactor, Convention, Info, Fatal). |
| `MSG_STATE_SCOPE_CONFIG` | `int` | `0`. |
| `MSG_STATE_SCOPE_MODULE` | `int` | `1`. |
| `_SCOPE_EXEMPT` | `str` | `"FR"` — message types exempt from the line/node distinction (Fatal and Report). |
| `MSG_TYPES` | `dict[str, str]` | Maps single-letter codes to human-readable names: `{"I": "info", "C": "convention", "R": "refactor", "W": "warning", "E": "error", "F": "fatal"}`. |
| `MSG_TYPES_LONG` | `dict[str, str]` | Reverse mapping of `MSG_TYPES`: keys are the human-readable names, values are the single-letter codes (e.g., `{"info": "I", "convention": "C", ...}`). Constructed via `{v: k for k, v in MSG_TYPES.items()}`. |
| `MSG_TYPES_STATUS` | `dict[str, int]` | Maps each message type code to a numeric status value: `{"I": 0, "C": 16, "R": 8, "W": 4, "E": 2, "F": 1}`. |
| `MAIN_CHECKER_NAME` | `str` | `"master"` — the canonical name for the main checker; affects rcfile generation and retro-compatibility (projects using `[MASTER]` in their rcfile). |

### Code Objects

#### Class: `WarningScope`

- **Attributes:**
  - `LINE` (`str`) = `"line-based-msg"` — constant identifying line-based message scope.
  - `NODE` (`str`) = `"node-based-msg"` — constant identifying node-based message scope.
- No methods, no inheritance (implicitly inherits from `object`). These are class-level string constants used to distinguish between two warning scoping modes.

#### Module-Level Variable: `full_version`

- **Type:** `str`
- **Value:** A multi-line f-string formatted as:
  ```
  pylint {__version__}
  astroid {astroid.__version__}
  Python {sys.version}
  ```
  Concatenates the pylint version, the astroid library version, and the full running Python interpreter version string into a single newline-separated string.

---