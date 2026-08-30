## pylint/config/argument.py
Now I have the full source code. Here is the complete specification:

---

# Module Specification: `pylint/config/argument.py`

## 1. Module-Level Preamble

### Imports

```python
from __future__ import annotations

import argparse
import os
import pathlib
import re
from collections.abc import Callable
from glob import glob
from typing import Any, Literal, Pattern, Sequence, Tuple, Union

from pylint import interfaces
from pylint import utils as pylint_utils
from pylint.config.callback_actions import _CallbackAction
from pylint.config.deprecation_actions import _NewNamesAction, _OldNamesAction
```

### Constants & Globals

**`_ArgumentTypes`** — A `Union` type alias representing all supported argument value types:
```python
_ArgumentTypes = Union[
    str,
    int,
    float,
    bool,
    Pattern[str],
    Sequence[str],
    Sequence[Pattern[str]],
    Tuple[int, ...],
]
```

**`YES_VALUES`** — A `set[str]` with literal value `{"y", "yes", "true"}`.

**`NO_VALUES`** — A `set[str]` with literal value `{"n", "no", "false"}`.

**`_TYPE_TRANSFORMERS`** — A module-level `dict[str, Callable[[str], _ArgumentTypes]]` mapping argument type names to their string-to-value transformer functions:
| Key | Value (transformer) |
|---|---|
| `"choice"` | `str` (identity) |
| `"csv"` | `_csv_transformer` |
| `"float"` | `float` (builtin) |
| `"int"` | `int` (builtin) |
| `"confidence"` | `_confidence_transformer` |
| `"non_empty_string"` | `_non_empty_string_transformer` |
| `"path"` | `_path_transformer` |
| `"glob_paths_csv"` | `_glob_paths_csv_transformer` |
| `"py_version"` | `_py_version_transformer` |
| `"regexp"` | `_regex_transformer` |
| `"regexp_csv"` | `_regexp_csv_transfomer` |
| `"regexp_paths_csv"` | `_regexp_paths_csv_transfomer` |
| `"string"` | `pylint_utils._unquote` |
| `"yn"` | `_yn_transformer` |

These transformers are invoked only when parsing command-line arguments, configuration files, or string default values. Non-string defaults are assumed to already be of the correct type and bypass transformation.

---

## 2. Transformer Functions (Module-Level)

### `def _confidence_transformer(value: str) -> Sequence[str]`
Transforms a comma-separated string of confidence level names into a sequence. If `value` is falsy (empty), returns `interfaces.CONFIDENCE_LEVEL_NAMES`. Otherwise, splits the input via `pylint_utils._check_csv`, validates each token against `interfaces.CONFIDENCE_LEVEL_NAMES`, and raises `argparse.ArgumentTypeError` with message `f"{value} should be in {*interfaces.CONFIDENCE_LEVEL_NAMES,}"` if any token is invalid. Returns the validated sequence on success.

### `def _csv_transformer(value: str) -> Sequence[str]`
Delegates to `pylint_utils._check_csv(value)` and returns its result — a comma-separated string parsed into a sequence of strings.

### `def _yn_transformer(value: str) -> bool`
Converts a yes/no or stringified boolean string to a Python `bool`. Lowercases the input, then checks membership in `YES_VALUES` (returns `True`) and `NO_VALUES` (returns `False`). Raises `argparse.ArgumentTypeError(None, f"Invalid yn value '{value}', should be in {*YES_VALUES, *NO_VALUES}")` for unrecognized values.

### `def _non_empty_string_transformer(value: str) -> str`
Validates that the input string is non-empty; raises `argparse.ArgumentTypeError("Option cannot be an empty string.")` if falsy. Otherwise returns `pylint_utils._unquote(value)` (strips surrounding quotes).

### `def _path_transformer(value: str) -> str`
Returns `os.path.expandvars(os.path.expanduser(value))`, expanding environment variables and user home directory shortcuts (`~`).

### `def _glob_paths_csv_transformer(value: str) -> Sequence[str]`
Parses a comma-separated list of path strings via `_csv_transformer`. For each resulting path, first applies `_path_transformer` (expanding vars/user), then passes it to `glob(..., recursive=True)` and extends the result list with all matched paths. Returns the accumulated flat list of expanded/globbed file paths.

### `def _py_version_transformer(value: str) -> tuple[int, ...]`
Parses a version string (e.g., `"3.8"`) into a tuple of integers. Replaces commas with dots, splits on `.`, and converts each segment via `int()`. On `ValueError`, raises `argparse.ArgumentTypeError(f"{value} has an invalid format, should be a version string. E.g., '3.8'")` (with `from None` to suppress the chain). Returns the resulting tuple.

### `def _regex_transformer(value: str) -> Pattern[str]`
Calls `re.compile(value)` and returns the compiled pattern. On `re.error`, constructs a message `f"Error in provided regular expression: {value} beginning at index {e.pos}: {e.msg}"` and raises `argparse.ArgumentTypeError(msg)` with `from e`.

### `def _regexp_csv_transfomer(value: str) -> Sequence[Pattern[str]]`
*(Note: method name has a typo — "transfomer" not "transformer".)* Splits the input via `_csv_transformer`, applies `_regex_transformer` to each token, and returns the list of compiled `Pattern[str]` objects.

### `def _regexp_paths_csv_transfomer(value: str) -> Sequence[Pattern[str]]`
*(Note: method name has a typo — "transfomer" not "transformer".)* Splits via `_csv_transformer`. For each pattern string, constructs a regex that matches both the Windows-style and POSIX-style representation of the path: `str(pathlib.PureWindowsPath(pattern)).replace("\\", "\\\\") + "|" + pathlib.PureWindowsPath(pattern).as_posix()`. Compiles this combined regex and appends it to the result list. Returns the list of compiled patterns.

---

## 3. Code Objects (Classes)

### `class _Argument`
Base class representing an argument for `argparse.ArgumentParser`. All attributes are keyword-only in `__init__`.

**`def __init__(self, *, flags: list[str], arg_help: str, hide_help: bool, section: str | None) -> None`**

- **`self.flags: list[str]`** — The flag names for the argument.
- **`self.hide_help: bool`** — Whether to suppress this argument in help output.
- **`self.help: str`** — The description string, with all `%` characters escaped to `%%` (argparse uses %-formatting). If `hide_help` is `True`, set to `argparse.SUPPRESS`.
- **`self.section: str | None`** — The section this argument belongs to.

### `class _BaseStoreArgument(_Argument)`
Extends `_Argument` with store-specific attributes.

**`def __init__(self, *, flags: list[str], action: str, default: _ArgumentTypes, arg_help: str, hide_help: bool, section: str | None) -> None`**

Calls `super().__init__()` with the shared parameters. Then sets:
- **`self.action: str`** — The argparse action string (e.g., `"store"`, `"store_true"`).
- **`self.default: _ArgumentTypes`** — The default value for this argument.

### `class _StoreArgument(_BaseStoreArgument)`
Represents a standard store argument with type transformation and choice constraints.

**`def __init__(self, *, flags: list[str], action: str, default: _ArgumentTypes, arg_type: str, choices: list[str] | None, arg_help: str, metavar: str, hide_help: bool, section: str | None) -> None`**

Calls `super().__init__()` with shared parameters. Then sets:
- **`self.type: Callable[[str], _ArgumentTypes]`** — Looked up from `_TYPE_TRANSFORMERS[arg_type]`. Transforms a string input into the appropriate typed value.
- **`self.choices: list[str] | None`** — Allowed values; `None` means no restriction.
- **`self.metavar: str`** — The metavar displayed in help messages (per argparse convention).

### `class _StoreTrueArgument(_BaseStoreArgument)`
A narrow delegation class for `store_true` actions. Its `action` parameter is typed as `Literal["store_true"]`.

**`def __init__(self, *, flags: list[str], action: Literal["store_true"], default: _ArgumentTypes, arg_help: str, hide_help: bool, section: str | None) -> None`**

Calls `super().__init__()` with all parameters. No additional attributes beyond those from `_BaseStoreArgument`. The class exists to narrow the type of `action` to `"store_true"`.

### `class _DeprecationArgument(_Argument)`
Extends `_Argument` with deprecation-aware store arguments, including type transformation and action dispatch for old/new name handling.

**`def __init__(self, *, flags: list[str], action: type[argparse.Action], default: _ArgumentTypes, arg_type: str, choices: list[str] | None, arg_help: str, metavar: str, hide_help: bool, section: str | None) -> None`**

Calls `super().__init__()` with shared parameters. Then sets:
- **`self.action: type[argparse.Action]`** — The argparse action class (e.g., `_OldNamesAction`, `_NewNamesAction`).
- **`self.default: _ArgumentTypes`** — Default value.
- **`self.type: Callable[[str], _ArgumentTypes]`** — Looked up from `_TYPE_TRANSFORMERS[arg_type]`.
- **`self.choices: list[str] | None`** — Allowed values or `None`.
- **`self.metavar: str`** — Help metavar.

### `class _ExtendArgument(_DeprecationArgument)`
Represents an argparse `"extend"` action argument, which appends multiple values to a list.

**`def __init__(self, *, flags: list[str], action: Literal["extend"], default: _ArgumentTypes, arg_type: str, metavar: str, arg_help: str, hide_help: bool, section: str | None, choices: list[str] | None, dest: str | None) -> None`**

Sets `action_class = argparse._ExtendAction`. Then sets **`self.dest: str | None`** — the destination attribute name for the argument. Calls `super().__init__()` with `action=action_class` and all other parameters. Inherits all attributes from `_DeprecationArgument`.

### `class _StoreOldNamesArgument(_DeprecationArgument)`
Stores arguments while emitting deprecation warnings for old names, using `_OldNamesAction`.

**`def __init__(self, *, flags: list[str], default: _ArgumentTypes, arg_type: str, choices: list[str] | None, arg_help: str, metavar: str, hide_help: bool, kwargs: dict[str, Any], section: str | None) -> None`**

Calls `super().__init__()` with `action=_OldNamesAction` and all other parameters. Then sets **`self.kwargs: dict[str, Any]`** — additional keyword arguments passed through to the action class.

### `class _StoreNewNamesArgument(_DeprecationArgument)`
Stores arguments while emitting deprecation warnings for new names, using `_NewNamesAction`.

**`def __init__(self, *, flags: list[str], default: _ArgumentTypes, arg_type: str, choices: list[str] | None, arg_help: str, metavar: str, hide_help: bool, kwargs: dict[str, Any], section: str | None) -> None`**

Calls `super().__init__()` with `action=_NewNamesAction` and all other parameters. Then sets **`self.kwargs: dict[str, Any]`** — additional keyword arguments passed through to the action class.

### `class _CallableArgument(_Argument)`
Represents a callback-based argument using `_CallbackAction`.

**`def __init__(self, *, flags: list[str], action: type[_CallbackAction], arg_help: str, kwargs: dict[str, Any], hide_help: bool, section: str | None, metavar: str) -> None`**

Calls `super().__init__()` with shared parameters. Then sets:
- **`self.action: type[_CallbackAction]`** — The callback action class.
- **`self.kwargs: dict[str, Any]`** — Additional keyword arguments for the action.
- **`self.metavar: str`** — Help metavar string.

---

## 4. Class Inheritance Hierarchy

```
_Argument
├── _BaseStoreArgument          (extends _Argument)
│   ├── _StoreArgument          (adds type, choices, metavar)
│   └── _StoreTrueArgument      (narrow delegation; action=Literal["store_true"])
├── _DeprecationArgument        (extends _Argument; adds action, default, type, choices, metavar)
│   ├── _ExtendArgument         (adds dest; uses argparse._ExtendAction)
│   ├── _StoreOldNamesArgument  (uses _OldNamesAction; adds kwargs)
│   └── _StoreNewNamesArgument  (uses _NewNamesAction; adds kwargs)
└── _CallableArgument           (extends _Argument; adds action, kwargs, metavar)
```

---

## 5. Key Behavioral Notes

- **`argparse.SUPPRESS`**: When `hide_help=True`, the `help` attribute is set to `argparse.SUPPRESS` rather than a string, causing argparse to omit this argument from help output entirely.
- **Percent escaping**: All `arg_help` strings have `%` doubled (`%%`) before storage in `self.help`, because argparse internally uses %-formatting on help text.
- **Transformer lookup**: The `_TYPE_TRANSFORMERS` dict is indexed by a string key (e.g., `"csv"`, `"int"`, `"regexp"`). Each value is a callable that accepts a single `str` and returns one of the types in `_ArgumentTypes`. These are stored as instance attributes on `_StoreArgument`, `_DeprecationArgument`, and their subclasses.
- **Typo preservation**: The functions `_regexp_csv_transfomer` and `_regexp_paths_csv_transfomer` contain a deliberate typo ("transfomer" instead of "transformer") in their names — this must be preserved exactly as-is since they are referenced by name elsewhere in the codebase.

## pylint/utils/__init__.py
Now I have every line of source code across all five submodules. Let me write the complete specification.

---

# Module Specification: `pylint/utils/__init__.py`

## 1. Module-Level Preamble

### Imports (re-exports)

This file is a re-export module that pulls symbols from five sibling submodules and publishes them in its own namespace via `__all__`. The precise import statements are:

```python
from pylint.utils.ast_walker import ASTWalker
from pylint.utils.docs import print_full_documentation
from pylint.utils.file_state import FileState
from pylint.utils.linterstats import LinterStats, ModuleStats, merge_stats
from pylint.utils.utils import (
    HAS_ISORT_5, IsortDriver, _check_csv, _splitstrip, _unquote,
    decoding_stream, diff_string, format_section, get_module_and_frameid,
    get_rst_section, get_rst_title, normalize_text, register_plugins,
    tokenize_module,
)
```

### Constants & Globals

**`__all__`** — a list of 20 exported symbol names in this exact order:
```python
[
    "ASTWalker", "HAS_ISORT_5", "IsortDriver", "_check_csv", "_splitstrip",
    "_unquote", "decoding_stream", "diff_string", "FileState", "format_section",
    "get_module_and_frameid", "get_rst_section", "get_rst_title", "normalize_text",
    "register_plugins", "tokenize_module", "merge_stats", "LinterStats",
    "ModuleStats", "print_full_documentation",
]
```

---

## 2. Code Objects (from all submodules)

### 2.1 `ASTWalker` — from `ast_walker.py`

**Header:** `class ASTWalker`

**Attributes (initialized in `__init__`):**
- `nbstatements: int` — counter of statement nodes visited; initialized to `0`.
- `visit_events: defaultdict[str, list[AstCallback]]` — maps node-type name strings to lists of visit callbacks; initialized as `defaultdict(list)`.
- `leave_events: defaultdict[str, list[AstCallback]]` — same structure for leave callbacks.
- `linter: PyLinter` — reference to the linter instance.
- `exception_msg: bool` — flag indicating whether an exception message has already been printed; initialized to `False`.

**Methods:**

#### `__init__(self, linter: PyLinter) -> None`
Initializes all attributes as described above.

#### `_is_method_enabled(self, method: AstCallback) -> bool`
Determines whether a checker callback method should be registered. If the method lacks an attribute named `"checks_msgs"`, returns `True`. Otherwise, iterates over `method.checks_msgs` and calls `self.linter.is_message_enabled(m)` for each message ID; returns `True` if any one is enabled, `False` otherwise.

#### `add_checker(self, checker: BaseChecker) -> None`
Registers all visit/leave methods from a checker into the walker's event maps.
1. Creates local sets `vcids` and `lcids` to track which node-type CIDs already have callbacks.
2. Iterates over every attribute name in `dir(checker)`. For each, extracts `cid = member[6:]` (the suffix after `"visit_"` or `"leave_"`). Skips if `cid == "default"`.
3. If the member starts with `"visit_"`, retrieves it via `getattr`, checks `_is_method_enabled`; if enabled, appends to `self.visit_events[cid]` and adds `cid` to `vcids`.
4. If the member starts with `"leave_"`, same logic but into `self.leave_events` and `lcids`.
5. After iterating all members, retrieves `visit_default = getattr(checker, "visit_default", None)`. If it exists, iterates over `nodes.ALL_NODE_CLASSES`; for each class whose lowercase name is not already in `vcids`, appends `visit_default` to `self.visit_events[cid]`.
6. No `"leave_default"` support exists (documented as a comment).

#### `walk(self, astroid: nodes.NodeNG) -> None`
Performs a depth-first traversal of the AST tree, invoking registered callbacks.
1. Computes `cid = astroid.__class__.__name__.lower()`.
2. Retrieves `visit_events = self.visit_events.get(cid, ())` and `leave_events = self.leave_events.get(cid, ())`.
3. Enters a try block:
   - If `astroid.is_statement` is truthy, increments `self.nbstatements`.
   - Iterates over each callback in `visit_events or ()`, calling it with `astroid`.
   - Recursively calls `self.walk(child)` for every child returned by `astroid.get_children()`.
   - Iterates over each callback in `leave_events or ()`, calling it with `astroid`.
4. On any exception: if `self.exception_msg` is `False`, prints a diagnostic line `"Exception on node {repr(astroid)} in file '{file}'"` (where `file = getattr(astroid.root(), "file", None)`), calls `traceback.print_exc()`, and sets `self.exception_msg = True`. Then re-raises the exception.

---

### 2.2 `FileState` — from `file_state.py`

**Header:** `class FileState`

**Type alias (module-level):**
```python
MessageStateDict = Dict[str, Dict[int, bool]]
```

**Attributes (initialized in `__init__`):**
- `base_name: str | None` — the module name; initialized from parameter.
- `_module_msgs_state: MessageStateDict` — maps message IDs to line-number→status dicts.
- `_raw_module_msgs_state: MessageStateDict` — snapshot of original state before block-line collection.
- `_ignored_msgs: defaultdict[tuple[str, int], set[int]]` — maps `(msgid, orig_line)` tuples to sets of suppressed lines; initialized as `collections.defaultdict(set)`.
- `_suppression_mapping: dict[tuple[str, int], int]` — maps `(msgid, line)` → original suppression line.
- `_effective_max_line_number: int | None` — the maximum line number of the current module; initialized to `None`.

**Methods:**

#### `__init__(self, modname: str | None = None) -> None`
Initializes all attributes as described above.

#### `collect_block_lines(self, msgs_store: MessageDefinitionStore, module_node: nodes.Module) -> None`
Walks the AST to collect block-level option line numbers.
1. Copies `_module_msgs_state` into `_raw_module_msgs_state`.
2. Saves a copy of current state as `orig_state`, then clears `_module_msgs_state`.
3. Clears `_suppression_mapping`.
4. Sets `_effective_max_line_number = module_node.tolineno`.
5. Calls `_collect_block_lines(msgs_store, module_node, orig_state)`.

#### `_collect_block_lines(self, msgs_store: MessageDefinitionStore, node: nodes.NodeNG, msg_state: MessageStateDict) -> None`
Recursively walks the AST depth-first to collect block-level option line numbers.
1. Recursively processes all children of `node` via `node.get_children()`.
2. Gets `first = node.fromlineno`, `last = node.tolineno`.
3. Determines `firstchildlineno`: if `node` is a `Module`, `ClassDef`, or `FunctionDef` and has a non-empty body, uses `node.body[0].fromlineno`; otherwise uses `last`.
4. For each `(msgid, lines)` in `msg_state`: for each `(lineno, state)` in `list(lines.items())`:
   - Skips if `first > lineno or last < lineno` (line is outside this block).
   - Retrieves message definitions via `msgs_store.get_message_definitions(msgid)`. For each definition:
     - If `message_definition.scope == WarningScope.NODE`: if `lineno > firstchildlineno`, sets `state = True`; computes `(first_, last_) = node.block_range(lineno)`.
     - Otherwise (line scope): sets `first_ = lineno`, `last_ = last`.
   - For each line in `range(first_, last_ + 1)`:
     - Skips if the line already exists in `self._module_msgs_state.get(msgid, ())`.
     - If the line is also present as a key in `lines` (a state change within this block), updates `state = lines[line]` and `original_lineno = line`.
     - If `not state`, records `self._suppression_mapping[(msgid, line)] = original_lineno`.
     - Sets `self._module_msgs_state[msgid][line] = state` (creating the inner dict on KeyError).
   - Deletes `lines[lineno]` from the working copy.

#### `set_msg_status(self, msg: MessageDefinition, line: int, status: bool) -> None`
Sets the enabled/disabled status for a message at a given line. Asserts `line > 0`. Sets `self._module_msgs_state[msg.msgid][line] = status`, creating the inner dict on KeyError.

#### `handle_ignored_message(self, state_scope: Literal[0, 1, 2] | None, msgid: str, line: int | None) -> None`
Reports an ignored message for suppression tracking. If `state_scope == MSG_STATE_SCOPE_MODULE`: asserts `line` is an `int`; tries to look up `self._suppression_mapping[(msgid, line)]` as `orig_line`, then adds `line` to `self._ignored_msgs[(msgid, orig_line)]`. On KeyError (no mapping found), silently passes.

#### `iter_spurious_suppression_messages(self, msgs_store: MessageDefinitionStore) -> Iterator[tuple[Literal["useless-suppression", "suppressed-message"], int, tuple[str] | tuple[str, int]]]`
Yields spurious suppression messages in two phases:
1. For each `(warning, lines)` in `_raw_module_msgs_state`: for each `(line, enable)` where `not enable`, if `(warning, line)` is not in `_ignored_msgs` and `warning` is not in `INCOMPATIBLE_WITH_USELESS_SUPPRESSION`, yields `("useless-suppression", line, (msgs_store.get_msg_display_string(warning),))`.
2. For each `((warning, from_), ignored_lines)` in `list(self._ignored_msgs.items())`: for each `line` in `ignored_lines`, yields `("suppressed-message", line, (msgs_store.get_msg_display_string(warning), from_))`.

#### `get_effective_max_line_number(self) -> int | None`
Returns `self._effective_max_line_number`.

---

### 2.3 `LinterStats`, `ModuleStats`, TypedDicts — from `linterstats.py`

**TypedDict classes (module-level):**

#### `BadNames(TypedDict)`
Keys: `"argument"`, `"attr"`, `"klass"`, `"class_attribute"`, `"class_const"`, `"const"`, `"inlinevar"`, `"function"`, `"method"`, `"module"`, `"variable"`, `"typevar"` — all `int`.

#### `CodeTypeCount(TypedDict)`
Keys: `"code"`, `"comment"`, `"docstring"`, `"empty"`, `"total"` — all `int`.

#### `DuplicatedLines(TypedDict)`
Keys: `"nb_duplicated_lines"` (`int`), `"percent_duplicated_lines"` (`float`).

#### `NodeCount(TypedDict)`
Keys: `"function"`, `"klass"`, `"method"`, `"module"` — all `int`.

#### `UndocumentedNodes(TypedDict)`
Keys: `"function"`, `"klass"`, `"method"`, `"module"` — all `int`.

#### `ModuleStats(TypedDict)`
Keys: `"convention"`, `"error"`, `"fatal"`, `"info"`, `"refactor"`, `"statement"`, `"warning"` — all `int`.

---

**`class LinterStats`**

**Attributes (initialized in `__init__`):**
- `bad_names: BadNames` — initialized from parameter or default zero-filled.
- `by_module: dict[str, ModuleStats]` — module name → stats; default `{}`.
- `by_msg: dict[str, int]` — message ID → count; default `{}`.
- `code_type_count: CodeTypeCount` — initialized from parameter or default zero-filled.
- `dependencies: dict[str, set[str]]` — module → dependency modules; default `{}`.
- `duplicated_lines: DuplicatedLines` — initialized from parameter or default zero-filled.
- `node_count: NodeCount` — initialized from parameter or default zero-filled.
- `undocumented: UndocumentedNodes` — initialized from parameter or default zero-filled.
- `convention: int`, `error: int`, `fatal: int`, `info: int`, `refactor: int`, `statement: int`, `warning: int` — all initialized to `0`.
- `global_note: float` — initialized to `0`.
- `nb_duplicated_lines: int` — initialized to `0`.
- `percent_duplicated_lines: float` — initialized to `0.0`.

**Methods:**

#### `__init__(self, bad_names: BadNames | None = None, by_module: dict[str, ModuleStats] | None = None, by_msg: dict[str, int] | None = None, code_type_count: CodeTypeCount | None = None, dependencies: dict[str, set[str]] | None = None, duplicated_lines: DuplicatedLines | None = None, node_count: NodeCount | None = None, undocumented: UndocumentedNodes | None = None) -> None`
Initializes all attributes. Each TypedDict parameter defaults to a zero-filled instance of the corresponding TypedDict if `None`.

#### `__str__(self) -> str`
Returns a multi-line string containing representations of all attributes in order: `bad_names`, sorted `by_module.items()`, sorted `by_msg.items()`, `code_type_count`, sorted `dependencies.items()`, `duplicated_lines`, `undocumented`, then the scalar counts (`convention` through `warning`), `global_note`, `nb_duplicated_lines`, `percent_duplicated_lines`.

#### `init_single_module(self, module_name: str) -> None`
Creates an entry in `self.by_module[module_name]` with a zero-filled `ModuleStats`.

#### `get_bad_names(self, node_name: Literal["argument", "attr", "class", "class_attribute", "class_const", "const", "inlinevar", "function", "method", "module", "variable", "typevar"]) -> int`
Returns the count for a bad-name category. Maps `"class"` → `self.bad_names.get("klass", 0)`; otherwise returns `self.bad_names.get(node_name, 0)`.

#### `increase_bad_name(self, node_name: str, increase: int) -> None`
Validates that `node_name` is one of the allowed names (including `"class"`). Raises `ValueError` if not. Casts to the appropriate Literal type. If `node_name == "class"`, increments `self.bad_names["klass"]`; otherwise increments `self.bad_names[node_name]`.

#### `reset_bad_names(self) -> None`
Replaces `self.bad_names` with a zero-filled `BadNames`.

#### `get_code_count(self, type_name: Literal["code", "comment", "docstring", "empty", "total"]) -> int`
Returns `self.code_type_count.get(type_name, 0)`.

#### `reset_code_count(self) -> None`
Replaces `self.code_type_count` with a zero-filled `CodeTypeCount`.

#### `reset_duplicated_lines(self) -> None`
Replaces `self.duplicated_lines` with `DuplicatedLines(nb_duplicated_lines=0, percent_duplicated_lines=0.0)`.

#### `get_node_count(self, node_name: Literal["function", "class", "method", "module"]) -> int`
Returns the count for a node type. Maps `"class"` → `self.node_count.get("klass", 0)`; otherwise returns `self.node_count.get(node_name, 0)`.

#### `reset_node_count(self) -> None`
Replaces `self.node_count` with `NodeCount(function=0, klass=0, method=0, module=0)`.

#### `get_undocumented(self, node_name: Literal["function", "class", "method", "module"]) -> float`
Returns the undocumented count. Maps `"class"` → `self.undocumented["klass"]`; otherwise returns `self.undocumented[node_name]`.

#### `reset_undocumented(self) -> None`
Replaces `self.undocumented` with `UndocumentedNodes(function=0, klass=0, method=0, module=0)`.

#### `get_global_message_count(self, type_name: str) -> int`
Returns `getattr(self, type_name, 0)` for the message-type scalar attributes (`convention`, `error`, etc.).

#### `get_module_message_count(self, modname: str, type_name: str) -> int`
Returns `getattr(self.by_module[modname], type_name, 0)`.

#### `increase_single_message_count(self, type_name: str, increase: int) -> None`
Increments the global message-type scalar: `setattr(self, type_name, getattr(self, type_name) + increase)`.

#### `increase_single_module_message_count(self, modname: str, type_name: MessageTypesFullName, increase: int) -> None`
Increments a per-module count: `self.by_module[modname][type_name] += increase`.

#### `reset_message_count(self) -> None`
Resets all global message-type scalars (`convention`, `error`, `fatal`, `info`, `refactor`, `warning`) to `0`.

---

**`def merge_stats(stats: list[LinterStats]) -> LinterStats`**
Merges multiple `LinterStats` objects into a new one (used in parallel mode). Creates a fresh `LinterStats()`. For each input stat, sums across all fields:
- Each of the 12 keys in `bad_names` is summed.
- `by_module`: copies entries from each stat (later stats overwrite earlier ones with the same key).
- `by_msg`: sums counts per message ID (creates new keys on KeyError).
- Each of the 5 keys in `code_type_count` is summed.
- `dependencies`: merges sets per module key (updates existing, creates new).
- `duplicated_lines["nb_duplicated_lines"]` and `"percent_duplicated_lines"` are each summed.
- Each of the 4 keys in `node_count` is summed.
- Each of the 4 keys in `undocumented` is summed.
- Global scalars (`convention`, `error`, `fatal`, `info`, `refactor`, `statement`, `warning`) are summed.
- `global_note` is summed.
Returns the merged `LinterStats`.

---

### 2.4 Utility Functions — from `utils.py`

**Module-level constants:**

```python
DEFAULT_LINE_LENGTH = 79
CMPS = ["=", "-", "+"]
```

**Type aliases (module-level):**

```python
GLOBAL_OPTION_BOOL = Literal["suggestion-mode", "analyse-fallback-blocks", "allow-global-unused-variables"]
GLOBAL_OPTION_INT = Literal["max-line-length", "docstring-min-length"]
GLOBAL_OPTION_LIST = Literal["ignored-modules"]
GLOBAL_OPTION_PATTERN = Literal["no-docstring-rgx", "dummy-variables-rgx", "ignored-argument-names", "mixin-class-rgx"]
GLOBAL_OPTION_PATTERN_LIST = Literal["exclude-too-few-public-methods", "ignore-paths"]
GLOBAL_OPTION_TUPLE_INT = Literal["py-version"]
GLOBAL_OPTION_NAMES = Union[GLOBAL_OPTION_BOOL, GLOBAL_OPTION_INT, GLOBAL_OPTION_LIST, GLOBAL_OPTION_PATTERN, GLOBAL_OPTION_PATTERN_LIST, GLOBAL_OPTION_TUPLE_INT]
T_GlobalOptionReturnTypes = TypeVar("T_GlobalOptionReturnTypes", bool, int, List[str], Pattern[str], List[Pattern[str]], Tuple[int, ...])
```

**`HAS_ISORT_5: bool`** — `True` if `isort.api` imports successfully (isort ≥ 5); `False` otherwise. On the `False` branch, also imports bare `isort`.

---

#### `normalize_text(text: str, line_len: int = DEFAULT_LINE_LENGTH, indent: str = "") -> str`
Wraps text using `textwrap.wrap()` with the given `line_len`, `initial_indent=indent`, and `subsequent_indent=indent`. Returns the result joined by newlines.

#### `cmp(a: int | float, b: int | float) -> int`
Returns `(a > b) - (a < b)` — a three-way comparison returning `-1`, `0`, or `1`.

#### `diff_string(old: int | float, new: int | float) -> str`
Computes the absolute difference `diff = abs(old - new)`. Returns a string formatted as `{CMPS[cmp(old, new)]}{diff and f'{diff:.2f}' or ''}` — i.e., `"=0.00"` for equal values, `"+1.50"` for increase, `"-3.00"` for decrease (the sign character from `CMPS` indexed by the comparison result).

#### `get_module_and_frameid(node: nodes.NodeNG) -> tuple[str, str]`
Returns `(module_name, frame_id_string)`. Walks up the frame hierarchy via `node.frame(future=True)` and repeated `frame.parent.frame(future=True)`, collecting names. If a frame is a `Module`, sets `module = frame.name`. Otherwise appends `getattr(frame, "name", "<lambda>")` to an `obj` list. Reverses `obj` and joins with `"."`. Returns `(module, ".".join(obj))`.

#### `get_rst_title(title: str, character: str) -> str`
Returns `f"{title}\n{character * len(title)}\n"` — a ReST-formatted title underlined with the given character repeated to match the title length.

#### `get_rst_section(section: str | None, options: list[tuple[str, OptionDict, Any]], doc: str | None = None) -> str`
Formats an option section as ReST output. If `section` is truthy, prepends a title via `get_rst_title(section, "'")`. If `doc` is provided, appends it wrapped by `normalize_text(doc)` followed by two newlines. For each `(optname, optdict, value)` in options: appends `":{optname}:\n"`, then if `help_opt = optdict.get("help")` exists, appends the help text wrapped with `normalize_text(help_opt, indent="  ")`. If `value` is truthy and `optname != "py-version"`, formats the value via `_format_option_value(optdict, value)`, escapes any existing backtick pairs (`"`` "` → `"```` ``"`), and appends `\n  Default: \`\`{formatted}\`\`\n`. Returns the accumulated string.

#### `decoding_stream(stream: BufferedReader | BytesIO, encoding: str, errors: Literal["strict"] = "strict") -> codecs.StreamReader`
Returns a `codecs.StreamReader` wrapping the given binary stream. Gets the reader class via `codecs.getreader(encoding or sys.getdefaultencoding())`; falls back to `sys.getdefaultencoding()` on `LookupError`. Returns `reader_cls(stream, errors)`.

#### `tokenize_module(node: nodes.Module) -> list[tokenize.TokenInfo]`
Opens the module's source stream via `node.stream()`, creates a readline function from it, and returns `list(tokenize.tokenize(readline))`.

#### `register_plugins(linter: PyLinter, directory: str) -> None`
Loads all Python modules and packages in `directory` that have a `register()` function. Iterates over `os.listdir(directory)`, skipping already-imported bases and `"__pycache__"`. Loads files matching extensions in `PY_EXTS` (excluding `"__init__.py"`) or directories not starting with `"."`. Catches `ValueError` (empty module name, e.g., emacs auto-save) silently; prints `ImportError` to stderr. If the loaded module has a `"register"` attribute, calls `module.register(linter)` and records the base in `imported`.

#### `get_global_option(checker: BaseChecker, option: GLOBAL_OPTION_NAMES, default: T_GlobalOptionReturnTypes | None = None) -> T_GlobalOptionReturnTypes | None | Any`
**DEPRECATED.** Issues a `DeprecationWarning` advising use of `checker.linter.config` instead. Returns `getattr(checker.linter.config, option.replace("-", "_"))`. Has six `@overload` signatures mapping specific option literals to their return types (`bool`, `int`, `list[str]`, `Pattern[str]`, `list[Pattern[str]]`, `tuple[int, ...]`).

#### `_splitstrip(string: str, sep: str = ",") -> list[str]`
Splits `string` on `sep`, strips whitespace from each piece, and discards empty strings. Returns `[word.strip() for word in string.split(sep) if word.strip()]`.

#### `_unquote(string: str) -> str`
Removes optional surrounding quotes (single or double). If the string is falsy, returns it unchanged. Strips a leading `"` or `'` if present, then strips a trailing `"` or `'` if present. Returns the result.

#### `_check_csv(value: list[str] | tuple[str] | str) -> Sequence[str]`
If `value` is already a `list` or `tuple`, returns it directly. Otherwise calls and returns `_splitstrip(value)` (treating it as a comma-separated string).

#### `_comment(string: str) -> str`
Splits the string into lines, strips each line, then joins them with `"\\n# "` prefixing each line after the first. Returns `"# " + f"{sep}# ".join(lines)` where `sep = "\\n"`.

#### `_format_option_value(optdict: OptionDict, value: Any) -> str`
Converts a compiled option value to its user-input string representation. Handles these cases in order:
- If `optdict.get("type") == "py_version"`: joins the tuple/list items with `"."`.
- If `value` is a `list` or `tuple`: recursively formats each item and joins with `","`.
- If `value` is a `dict`: joins key-value pairs as `"k:v"`, joined by `","`.
- If `value` has a `"match"` attribute (compiled regex): uses `value.pattern`.
- If `optdict.get("type") == "yn"`: returns `"yes"` or `"no"`.
- If `value` is a string consisting only of whitespace: wraps in single quotes.
- Otherwise: returns `str(value)`.

#### `format_section(stream: TextIO, section: str, options: list[tuple[str, OptionDict, Any]], doc: str | None = None) -> None`
**DEPRECATED.** Issues a `DeprecationWarning`. If `doc` is provided, prints `_comment(doc)` to the stream. Prints `"[{section}]"`. Then calls `_ini_format(stream, options)` (suppressing deprecation warnings).

#### `_ini_format(stream: TextIO, options: list[tuple[str, OptionDict, Any]]) -> None`
**DEPRECATED.** Issues a `DeprecationWarning`. For each `(optname, optdict, value)`: formats the value via `_format_option_value`; if help text exists, normalizes it with `normalize_text(help_opt, indent="# ")`, prints a blank line, then the help. Prints a blank line regardless. If `value is None`, prints `"#{optname}="`. Otherwise strips the stringified value; if it matches the regex `^([\w-]+,)+[\w-]+$` (a comma-separated list), reformats with line breaks: joins each element plus `","` using `"\n " + " " * len(optname)` as separator, then removes the trailing `","`. Prints `"{optname}={value}"`.

---

### 2.5 `IsortDriver` — from `utils.py`

**Header:** `class IsortDriver`
A wrapper around isort API that abstracts differences between versions 4 and 5.

**Attributes (initialized in `__init__`):**
- If `HAS_ISORT_5`: stores `self.isort5_config = isort.api.Config(extra_standard_library=config.known_standard_library, known_third_party=config.known_third_party)`.
- Else: stores `self.isort4_obj = isort.SortImports(file_contents="", known_standard_library=config.known_standard_library, known_third_party=config.known_third_party)`.

#### `__init__(self, config: argparse.Namespace) -> None`
Initializes the appropriate isort configuration object based on the detected version.

#### `place_module(self, package: str) -> str`
Returns the isort category classification for a package name. If `HAS_ISORT_5`, calls `isort.api.place_module(package, self.isort5_config)`; otherwise calls `self.isort4_obj.place_module(package)`.

---

### 2.6 Documentation Functions — from `docs.py`

#### `_get_checkers_infos(linter: PyLinter) -> dict[str, dict[str, Any]]`
**Not exported.** Aggregates checker information into a dictionary keyed by checker name. For each non-"master" checker returned by `linter.get_checkers()`: if the name is already in the result dict, appends its options and messages to existing entries (suppressing `DeprecationWarning`); otherwise creates a new entry with `"checker"`, `"options"` (from `checker.options_and_values()`), `"msgs"` (from `dict(checker.msgs)`), and `"reports"` (from `list(checker.reports)`). Returns the dict.

#### `_get_checkers_documentation(linter: PyLinter) -> str`
**Not exported.** Builds full ReST documentation string. Starts with a title for global options, then iterates over all checkers; for the `"master"` checker with non-empty `options`, groups them by section via `checker.options_by_section()` and formats each with `get_rst_title` (using `"~"` as underline) and `get_rst_section`. Then adds a title for per-checker options, followed by an explanatory paragraph. For each sorted checker name in `_get_checkers_infos(linter)`, calls `checker.get_full_documentation(**information)` (with the checker removed from the info dict). Returns the accumulated string.

#### `print_full_documentation(linter: PyLinter, stream: TextIO = sys.stdout) -> None`
**Exported.** Calls `_get_checkers_documentation(linter)`, strips the trailing newline (`[:-1]`), and prints to `stream`.

## pylint/utils/utils.py
Now I have the complete file content. Here is the specification:

---

## Module-Level Preamble

### Imports

```python
from __future__ import annotations

try:
    import isort.api
    import isort.settings
except ImportError:  # isort < 5
    import isort

import argparse
import codecs
import os
import re
import sys
import textwrap
import tokenize
import warnings
from collections.abc import Sequence
from io import BufferedReader, BytesIO
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Literal,
    Pattern,
    TextIO,
    Tuple,
    TypeVar,
    Union,
)

from astroid import Module, modutils, nodes

from pylint.constants import PY_EXTS
from pylint.typing import OptionDict

if TYPE_CHECKING:
    from pylint.lint import PyLinter
```

### Constants & Globals

- **`DEFAULT_LINE_LENGTH = 79`** — Default line length for text wrapping.
- **`HAS_ISORT_5`** — Boolean set to `True` if `isort.api` and `isort.settings` are importable (isort ≥ 5); otherwise `False`.
- **`CMPS = ["=", "-", "+"]`** — List of three characters used by `diff_string()` to indicate no change, decrease, or increase.

### Type Aliases

- **`GLOBAL_OPTION_BOOL = Literal["suggestion-mode", "analyse-fallback-blocks", "allow-global-unused-variables"]`**
- **`GLOBAL_OPTION_INT = Literal["max-line-length", "docstring-min-length"]`**
- **`GLOBAL_OPTION_LIST = Literal["ignored-modules"]`**
- **`GLOBAL_OPTION_PATTERN = Literal["no-docstring-rgx", "dummy-variables-rgx", "ignored-argument-names", "mixin-class-rgx"]`**
- **`GLOBAL_OPTION_PATTERN_LIST = Literal["exclude-too-few-public-methods", "ignore-paths"]`**
- **`GLOBAL_OPTION_TUPLE_INT = Literal["py-version"]`**
- **`GLOBAL_OPTION_NAMES = Union[GLOBAL_OPTION_BOOL, GLOBAL_OPTION_INT, GLOBAL_OPTION_LIST, GLOBAL_OPTION_PATTERN, GLOBAL_OPTION_PATTERN_LIST, GLOBAL_OPTION_TUPLE_INT]`**
- **`T_GlobalOptionReturnTypes = TypeVar("T_GlobalOptionReturnTypes", bool, int, List[str], Pattern[str], List[Pattern[str]], Tuple[int, ...])`**

---

## Code Objects (Functions and Classes)

### `normalize_text(text: str, line_len: int = DEFAULT_LINE_LENGTH, indent: str = "") -> str`

Wraps the input `text` to fit within `line_len` characters. Uses `textwrap.wrap()` with both `initial_indent` and `subsequent_indent` set to `indent`. Returns the wrapped text as a single string with lines joined by `\n`.

---

### `cmp(a: int | float, b: int | float) -> int`

Replaces Python 2's built-in `cmp()`. Returns `(a > b) - (a < b)`, yielding `1` if `a > b`, `-1` if `a < b`, and `0` if equal.

---

### `diff_string(old: int | float, new: int | float) -> str`

Returns a string representing the difference between `old` and `new`. Computes `diff = abs(old - new)`. Uses `CMPS[cmp(old, new)]` to pick the prefix character (`=`, `-`, or `+`). If `diff` is non-zero, appends the formatted value `f'{diff:.2f}'`; if zero, appends nothing. Returns the resulting string (e.g., `"=0.00"`, `"+5.50"`, `"-3.00"`).

---

### `get_module_and_frameid(node: nodes.NodeNG) -> tuple[str, str]`

Walks up the AST frame hierarchy starting from `node.frame()`. Initializes `module = ""` and `obj = []`. For each frame in the walk:
- If the frame is an instance of `Module`, sets `module = frame.name`.
- Otherwise, appends `getattr(frame, "name", "<lambda>")` to `obj`.
After traversing (walking up via `frame.parent.frame()`, breaking on `AttributeError`), reverses `obj` and returns `(module, ".".join(obj))`.

---

### `get_rst_title(title: str, character: str) -> str`

Returns a ReStructuredText-formatted title: the title string followed by `\n`, then `character * len(title)` (the underline), then `\n`.

---

### `get_rst_section(section: str | None, options: list[tuple[str, OptionDict, Any]], doc: str | None = None) -> str`

Formats an option's section as ReStructuredText output. Initializes `result = ""`. If `section` is truthy, appends the result of `get_rst_title(section, "'")`. If `doc` is truthy, normalizes it via `normalize_text(doc)` and appends `{formatted_doc}\n\n`. Then iterates over each `(optname, optdict, value)` in `options`:
- Appends `:{optname}:\n`.
- If `help_opt = optdict.get("help")` is truthy (asserted to be a string), normalizes it with indent `"  "` and appends `{formatted_help}\n`.
- If `value` is truthy and `optname != "py-version"`, formats the value via `_format_option_value(optdict, value)`, converts to string, replaces any occurrence of ```` `` `` (four backticks followed by a space) with ```` ```` ```` `` (eight backticks), and appends `\n  Default: \`\`{value}\`\`\n`.
Returns `result`.

---

### `decoding_stream(stream: BufferedReader | BytesIO, encoding: str, errors: Literal["strict"] = "strict") -> codecs.StreamReader`

Attempts to get a codec reader class for the given `encoding` via `codecs.getreader(encoding or sys.getdefaultencoding())`. If a `LookupError` occurs (unknown encoding), falls back to `sys.getdefaultencoding()`. Returns an instance of the resolved reader class, constructed as `reader_cls(stream, errors)`.

---

### `tokenize_module(node: nodes.Module) -> list[tokenize.TokenInfo]`

Opens the module's source stream via `node.stream()`, reads lines with `stream.readline`, and passes that readline function to `tokenize.tokenize(readline)`. Returns the result as a plain `list`.

---

### `register_plugins(linter: PyLinter, directory: str) -> None`

Loads all Python modules and packages from `directory` to register pylint checkers. Initializes an empty dict `imported = {}`. Iterates over `os.listdir(directory)` for each `filename`:
- Splits into `base, extension = os.path.splitext(filename)`.
- Skips if `base in imported` or `base == "__pycache__"`.
- Enters the loading block if either: (a) `extension in PY_EXTS` and `base != "__init__"`, or (b) no extension (`not extension`) and it is a directory (`os.path.isdir(...)`) and does not start with `"."`.
- Attempts to load via `modutils.load_module_from_file(os.path.join(directory, filename))`:
  - Catches `ValueError` (empty module name, e.g., Emacs auto-save files) → continues.
  - Catches `ImportError` → prints `"Problem importing module {filename}: {exc}"` to `sys.stderr`.
- On success (`else`): if the loaded module has a `register` attribute, calls `module.register(linter)` and records `imported[base] = 1`.

---

### `_splitstrip(string: str, sep: str = ",") -> list[str]`

Splits `string` on `sep` (default `","`), strips whitespace from each resulting token, discards empty strings, and returns the remaining tokens as a list. Example: `'a, b, c   ,  4,,'.split(',') → ['a', 'b', 'c', '4']`.

---

### `_unquote(string: str) -> str`

Removes optional surrounding quotes (single or double) from `string`. If `string` is falsy, returns it unchanged. If the first character (`string[0]`) is `"'"` or `'"'`, strips it. If the last character (`string[-1]`) is `"'"` or `'"'`, strips it. Returns the resulting string (unchanged if no quotes were present).

---

### `_check_csv(value: list[str] | tuple[str] | str) -> Sequence[str]`

If `value` is a `list` or `tuple`, returns it directly. Otherwise, treats it as a string and calls `_splitstrip(value)` to produce a list of stripped tokens. Returns a `Sequence[str]`.

---

### `_comment(string: str) -> str`

Converts each line of `string` (split by `\n`) into a commented form. Strips whitespace from each line, then joins them with `\n# `, prefixing the entire result with `"# "`. Returns the fully commented string.

---

### `_format_option_value(optdict: OptionDict, value: Any) -> str`

Formats an option value for display based on its type in `optdict`:
- If `optdict.get("type") == "py_version"`: joins each item of `value` (assumed iterable) as `".".join(str(item))`.
- Else if `value` is a `list` or `tuple`: recursively formats each element and joins with `","`.
- Else if `value` is a `dict`: formats each key-value pair as `"k:v"` and joins with `","`.
- Else if `value` has a `.match` attribute (compiled regex): uses `value.pattern`.
- Else if `optdict.get("type") == "yn"`: returns `"yes"` if truthy, `"no"` otherwise.
- Else if `value` is a string and `value.isspace()`: wraps in single quotes as `f"'{value}'"`.
- Otherwise: returns `str(value)`.

---

### `format_section(stream: TextIO, section: str, options: list[tuple[str, OptionDict, Any]], doc: str | None = None) -> None` *(deprecated)*

Emits an INI-format option section to `stream`. Emits a deprecation warning (`DeprecationWarning`, stacklevel 2). If `doc` is truthy, prints the commented doc via `_comment(doc)` followed by `\n[section]`. Then calls `_ini_format(stream, options)` inside a `warnings.catch_warnings()` context that filters out `DeprecationWarning`.

---

### `_ini_format(stream: TextIO, options: list[tuple[str, OptionDict, Any]]) -> None` *(deprecated)*

Formats options in INI format to `stream`. Emits a deprecation warning. For each `(optname, optdict, value)`:
- Skips if `"kwargs"` is in `optdict` and `optdict["kwargs"]["new_names"]` exists (migration alias).
- Formats the value via `_format_option_value(optdict, value)`.
- If `help_opt = optdict.get("help")` is truthy: normalizes it with indent `"# "`, prints a blank line, then prints the help. Otherwise prints only a blank line.
- If the formatted value equals `"None"` or `"False"`: prints `#{optname}=` (commented out).
- Otherwise: strips whitespace from the value string; if it matches the regex `^([\w-]+,)+[\w-]+$` (a comma-separated list of word-dash tokens), reformats with line breaks: each element except the last gets a trailing `,` followed by `\n ` + spaces matching `len(optname)`. The final element has no trailing comma. Prints `{optname}={value}`.

---

### `class IsortDriver`

A wrapper around isort's API to abstract differences between versions 4 and 5.

#### `__init__(self, config: argparse.Namespace) -> None`

- If `HAS_ISORT_5` is true: creates `self.isort5_config = isort.settings.Config(extra_standard_library=config.known_standard_library, known_third_party=config.known_third_party)`.
- Otherwise (isort < 5): creates `self.isort4_obj = isort.SortImports(file_contents="", known_standard_library=config.known_standard_library, known_third_party=config.known_third_party)`.

#### `place_module(self, package: str) -> str`

Returns the isort category classification for a given package name.
- If `HAS_ISORT_5`: calls `isort.api.place_module(package, self.isort5_config)` and returns its result.
- Otherwise: calls `self.isort4_obj.place_module(package)` and returns its result.