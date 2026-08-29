## pylint/config/argument.py
Now I have every line of the file. Here is the complete specification:

---

## Module-Level Preamble

### Imports

```python
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections.abc import Callable
from typing import Any, Pattern, Sequence, Tuple, Union

from pylint import interfaces
from pylint import utils as pylint_utils
from pylint.config.callback_actions import _CallbackAction, _ExtendAction
from pylint.config.deprecation_actions import _NewNamesAction, _OldNamesAction
from pylint.constants import PY38_PLUS

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal
```

### Constants & Globals

**`_ArgumentTypes`** — A `Union` type alias representing all possible argument value types:
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

**`_TYPE_TRANSFORMERS`** — A module-level `dict[str, Callable[[str], _ArgumentTypes]]` mapping type-name strings to transformer functions:
| Key | Value (transformer) |
|---|---|
| `"choice"` | `str` (identity) |
| `"csv"` | `_csv_transformer` |
| `"float"` | `float` (builtin) |
| `"int"` | `int` (builtin) |
| `"confidence"` | `_confidence_transformer` |
| `"non_empty_string"` | `_non_empty_string_transformer` |
| `"py_version"` | `_py_version_transformer` |
| `"regexp"` | `re.compile` |
| `"regexp_csv"` | `_regexp_csv_transfomer` |
| `"regexp_paths_csv"` | `_regexp_paths_csv_transfomer` |
| `"string"` | `pylint_utils._unquote` |
| `"yn"` | `_yn_transformer` |

These transformers accept a single `str` argument and return one of the types in `_ArgumentTypes`. They are invoked only when parsing command-line arguments, configuration files, or string default values. Non-string defaults are assumed to already be correctly typed.

### Transformer Functions (module-level)

**`_confidence_transformer(value: str) -> Sequence[str]`**
1. Calls `pylint_utils._check_csv(value)` to split the comma-separated input into a sequence of strings.
2. Iterates over each confidence string; if any is not in `interfaces.CONFIDENCE_LEVEL_NAMES`, raises `argparse.ArgumentTypeError` with a message listing all valid names.
3. Returns the validated sequence.

**`_csv_transformer(value: str) -> Sequence[str]`**
- Delegates to `pylint_utils._check_csv(value)` and returns its result (a comma-separated string split into a sequence).

**`_yn_transformer(value: str) -> bool`**
1. Lowercases the input value.
2. If it is in `YES_VALUES`, returns `True`.
3. If it is in `NO_VALUES`, returns `False`.
4. Otherwise raises `argparse.ArgumentTypeError(None, f"Invalid yn value '{value}', should be in {*YES_VALUES, *NO_VALUES}")`.

**`_non_empty_string_transformer(value: str) -> str`**
1. If `value` is falsy (empty string), raises `argparse.ArgumentTypeError("Option cannot be an empty string.")`.
2. Otherwise returns `pylint_utils._unquote(value)` (strips surrounding quotes).

**`_py_version_transformer(value: str) -> tuple[int, ...]`**
1. Replaces commas with dots in the input, then splits on `"."`.
2. Converts each part to `int`, producing a tuple of integers.
3. If any conversion fails (`ValueError`), raises `argparse.ArgumentTypeError(f"{value} has an invalid format, should be a version string. E.g., '3.8'")` (with `from None`).
4. Returns the resulting tuple.

**`_regexp_csv_transfomer(value: str) -> Sequence[Pattern[str]]`** *(note: misspelled "transfomer" in source)*
1. Calls `_csv_transformer(value)` to get a sequence of pattern-string fragments.
2. For each fragment, calls `re.compile(pattern)` and appends the compiled regex to a list.
3. Returns the list of compiled patterns.

**`_regexp_paths_csv_transfomer(value: str) -> Sequence[Pattern[str]]`** *(note: misspelled "transfomer" in source)*
1. Calls `_csv_transformer(value)` to get a sequence of path-string fragments.
2. For each fragment, constructs a regex that matches either the Windows-style escaped version or the POSIX version:
   - `str(pathlib.PureWindowsPath(pattern)).replace("\\", "\\\\")` — converts to a Windows path string and doubles backslashes for regex escaping.
   - `pathlib.PureWindowsPath(pattern).as_posix()` — converts to a forward-slash POSIX-style path.
   - These two are joined with `"|"` (regex alternation) inside `re.compile(...)`.
3. Appends each compiled pattern to a list and returns it.

---

## Code Objects (Classes)

### Class `_Argument`

**Inheritance:** None (base class).

**Attributes set in `__init__`:**

| Attribute | Type | Description |
|---|---|---|
| `flags` | `list[str]` | The name(s) of the argument. |
| `hide_help` | `bool` | Whether to hide this argument in help output. |
| `help` | `str` | The description; `%` characters are escaped to `%%`. If `hide_help` is `True`, set to `argparse.SUPPRESS`. |
| `section` | `str \| None` | The section to add this argument to. |

**`__init__(self, *, flags: list[str], arg_help: str, hide_help: bool, section: str | None) -> None`**
- Stores `flags`, `hide_help`, and `section` directly as attributes.
- Sets `help = arg_help.replace("%", "%%")`; if `hide_help` is `True`, overrides `self.help = argparse.SUPPRESS`.

---

### Class `_BaseStoreArgument(_Argument)`

**Inheritance:** `_Argument`.

**Attributes set in `__init__`:**

| Attribute | Type | Description |
|---|---|---|
| `action` | `str` | The action to perform with the argument. |
| `default` | `_ArgumentTypes` | The default value of the argument. |

**`__init__(self, *, flags: list[str], action: str, default: _ArgumentTypes, arg_help: str, hide_help: bool, section: str | None) -> None`**
- Calls `super().__init__()` with `flags`, `arg_help`, `hide_help`, and `section`.
- Sets `self.action = action` and `self.default = default`.

---

### Class `_StoreArgument(_BaseStoreArgument)`

**Inheritance:** `_BaseStoreArgument`.

**Attributes set in `__init__`:**

| Attribute | Type | Description |
|---|---|---|
| `type` | `Callable[[str], _ArgumentTypes]` | Transformer function from `_TYPE_TRANSFORMERS[arg_type]`. |
| `choices` | `list[str] \| None` | List of valid choices, or `None` if unrestricted. |
| `metavar` | `str` | The metavar for the argument (see argparse docs). |

**`__init__(self, *, flags: list[str], action: str, default: _ArgumentTypes, arg_type: str, choices: list[str] \| None, arg_help: str, metavar: str, hide_help: bool, section: str | None) -> None`**
- Calls `super().__init__()` with `flags`, `action`, `default`, `arg_help`, `hide_help`, and `section`.
- Sets `self.type = _TYPE_TRANSFORMERS[arg_type]`.
- Sets `self.choices = choices` and `self.metavar = metavar`.

---

### Class `_StoreTrueArgument(_BaseStoreArgument)`

**Inheritance:** `_BaseStoreArgument`.

**Attributes set in `__init__`:**
- No additional attributes beyond those from `_BaseStoreArgument`; it delegates entirely to the parent.

**`__init__(self, *, flags: list[str], action: Literal["store_true"], default: _ArgumentTypes, arg_help: str, hide_help: bool, section: str | None) -> None`**
- Calls `super().__init__()` with all parameters passed through (`flags`, `action`, `default`, `arg_help`, `hide_help`, `section`).
- The `action` parameter is constrained to the literal string `"store_true"`.

---

### Class `_DeprecationArgument(_Argument)`

**Inheritance:** `_Argument`.

**Attributes set in `__init__`:**

| Attribute | Type | Description |
|---|---|---|
| `action` | `type[argparse.Action]` | The action class to perform with the argument. |
| `default` | `_ArgumentTypes` | The default value of the argument. |
| `type` | `Callable[[str], _ArgumentTypes]` | Transformer function from `_TYPE_TRANSFORMERS[arg_type]`. |
| `choices` | `list[str] \| None` | List of valid choices, or `None`. |
| `metavar` | `str` | The metavar for the argument. |

**`__init__(self, *, flags: list[str], action: type[argparse.Action], default: _ArgumentTypes, arg_type: str, choices: list[str] \| None, arg_help: str, metavar: str, hide_help: bool, section: str | None) -> None`**
- Calls `super().__init__()` with `flags`, `arg_help`, `hide_help`, and `section`.
- Sets `self.action = action`.
- Sets `self.default = default`.
- Sets `self.type = _TYPE_TRANSFORMERS[arg_type]`.
- Sets `self.choices = choices` and `self.metavar = metavar`.

---

### Class `_ExtendArgument(_DeprecationArgument)`

**Inheritance:** `_DeprecationArgument`.

**Attributes set in `__init__`:**

| Attribute | Type | Description |
|---|---|---|
| `dest` | `str \| None` | The destination of the argument. |

**`__init__(self, *, flags: list[str], action: Literal["extend"], default: _ArgumentTypes, arg_type: str, metavar: str, arg_help: str, hide_help: bool, section: str | None, choices: list[str] \| None, dest: str | None) -> None`**
1. Determines the action class: if `PY38_PLUS` is true, uses `argparse._ExtendAction`; otherwise uses `pylint.config.callback_actions._ExtendAction`.
2. Sets `self.dest = dest`.
3. Calls `super().__init__()` with `flags`, `action_class` (the resolved class), `default`, `arg_type`, `choices`, `arg_help`, `metavar`, `hide_help`, and `section`.

---

### Class `_StoreOldNamesArgument(_DeprecationArgument)`

**Inheritance:** `_DeprecationArgument`.

**Attributes set in `__init__`:**

| Attribute | Type | Description |
|---|---|---|
| `kwargs` | `dict[str, Any]` | Additional keyword arguments passed to the action. |

**`__init__(self, *, flags: list[str], default: _ArgumentTypes, arg_type: str, choices: list[str] \| None, arg_help: str, metavar: str, hide_help: bool, kwargs: dict[str, Any], section: str | None) -> None`**
- Calls `super().__init__()` with all parameters except `kwargs`, passing `action=_OldNamesAction`.
- Sets `self.kwargs = kwargs`.

---

### Class `_StoreNewNamesArgument(_DeprecationArgument)`

**Inheritance:** `_DeprecationArgument`.

**Attributes set in `__init__`:**

| Attribute | Type | Description |
|---|---|---|
| `kwargs` | `dict[str, Any]` | Additional keyword arguments passed to the action. |

**`__init__(self, *, flags: list[str], default: _ArgumentTypes, arg_type: str, choices: list[str] \| None, arg_help: str, metavar: str, hide_help: bool, kwargs: dict[str, Any], section: str | None) -> None`**
- Calls `super().__init__()` with all parameters except `kwargs`, passing `action=_NewNamesAction`.
- Sets `self.kwargs = kwargs`.

---

### Class `_CallableArgument(_Argument)`

**Inheritance:** `_Argument`.

**Attributes set in `__init__`:**

| Attribute | Type | Description |
|---|---|---|
| `action` | `type[_CallbackAction]` | The action class to perform with the argument. |
| `kwargs` | `dict[str, Any]` | Additional keyword arguments passed to the action. |

**`__init__(self, *, flags: list[str], action: type[_CallbackAction], arg_help: str, kwargs: dict[str, Any], hide_help: bool, section: str | None) -> None`**
- Calls `super().__init__()` with `flags`, `arg_help`, `hide_help`, and `section`.
- Sets `self.action = action`.
- Sets `self.kwargs = kwargs`.

---

## Class Hierarchy Summary

```
_Argument
├── _BaseStoreArgument
│   ├── _StoreArgument          (adds: type, choices, metavar)
│   └── _StoreTrueArgument      (no additions; delegates to parent)
├── _DeprecationArgument        (adds: action, default, type, choices, metavar)
│   ├── _ExtendArgument         (adds: dest; resolves action class based on Python version)
│   ├── _StoreOldNamesArgument  (adds: kwargs; uses _OldNamesAction)
│   └── _StoreNewNamesArgument  (adds: kwargs; uses _NewNamesAction)
└── _CallableArgument           (adds: action, kwargs)
```

All classes are designed to represent arguments for `argparse.ArgumentParser.add_argument()` within the pylint configuration system. Each class encapsulates a specific argparse action pattern and provides the metadata (`flags`, `help`, `type`, `choices`, `metavar`, etc.) needed by pylint's argument parser infrastructure.

## pylint/config/arguments_manager.py
Here is the complete natural-language specification of `pylint/config/arguments_manager.py`:

---

## Module-Level Preamble

### Imports

```python
from __future__ import annotations

import argparse
import configparser
import copy
import optparse  # deprecated-module
import os
import re
import sys
import textwrap
import warnings
from collections import OrderedDict
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, TextIO, Union

import tomlkit

from pylint import utils
from pylint.config.argument import (
    _Argument,
    _CallableArgument,
    _ExtendArgument,
    _StoreArgument,
    _StoreNewNamesArgument,
    _StoreOldNamesArgument,
    _StoreTrueArgument,
)
from pylint.config.exceptions import (
    UnrecognizedArgumentAction,
    _UnrecognizedOptionError,
)
from pylint.config.help_formatter import _HelpFormatter
from pylint.config.option import Option
from pylint.config.option_parser import OptionParser
from pylint.config.options_provider_mixin import OptionsProviderMixIn
from pylint.config.utils import _convert_option_to_argument, _parse_rich_type_value
from pylint.constants import MAIN_CHECKER_NAME
from pylint.typing import OptionDict

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

if TYPE_CHECKING:
    from pylint.config.arguments_provider import _ArgumentsProvider
```

### Constants & Type Aliases

- **`ConfigProvider`** — `Union["_ArgumentsProvider", OptionsProviderMixIn]`. A type alias for the two supported provider types.

---

## Code Objects

### Class `_ArgumentsManager`

**Purpose:** Central manager for command-line arguments and configuration options in pylint. Uses `argparse` as its primary parser, with deprecated optparse-based methods retained for backward compatibility.

#### Attributes (initialized in `__init__`)

| Attribute | Type | Description |
|---|---|---|
| `_config` | `argparse.Namespace` | Namespace holding all option values. |
| `_arg_parser` | `argparse.ArgumentParser` | The primary command-line argument parser, configured with `_HelpFormatter`. |
| `_argument_groups_dict` | `dict[str, argparse._ArgumentGroup]` | Maps section names to their corresponding `argparse` argument groups. |
| `_option_dicts` | `dict[str, OptionDict]` | Maps option name strings to their full option dictionaries (registered by providers). |
| `_options_providers` | `list[ConfigProvider]` | List of registered options providers. |
| `_all_options` | `OrderedDict[str, ConfigProvider]` | Maps option names to the provider that owns them. |
| `_short_options` | `dict[str, str]` | Maps short-option characters (e.g., `"v"`) to their long option names. |
| `_nocallback_options` | `dict[ConfigProvider, str]` | Maps providers to options that use a non-callback action. |
| `_mygroups` | `dict[str, optparse.OptionGroup]` | Deprecated: maps group names to optparse OptionGroups. |
| `_maxlevel` | `int` | Maximum verbosity level seen so far; initialized to `0`. |

#### Methods

##### `__init__(self, prog: str, usage: str \| None = None, description: str \| None = None) -> None`

Initializes the arguments manager. Creates an empty `_config` namespace and an `argparse.ArgumentParser` with the given `prog`, a default `usage` of `"%(prog)s [options]"` if not provided, the optional `description`, and `_HelpFormatter` as its formatter class. Calls `reset_parsers()` (silencing deprecation warnings) to initialize the deprecated optparse-based parsers (`cfgfile_parser` as `configparser.ConfigParser(inline_comment_prefixes=("#", ";"))` and `cmdline_parser` as an `OptionParser`). Initializes all instance attributes listed above.

##### Property `config` — getter/setter

- **Getter:** Returns `_config`.
- **Setter:** Assigns the given `argparse.Namespace` to `_config`.

##### Property `options_providers` — getter/setter (DEPRECATED)

Both emit a `DeprecationWarning` ("options_providers has been deprecated. It will be removed in pylint 3.0.") and then return/assign `_options_providers`.

##### `_register_options_provider(self, provider: _ArgumentsProvider) -> None`

Registers an options provider and loads its defaults into the parser. For each `(opt, optdict)` pair in `provider.options`:
1. Stores `optdict` in `_option_dicts[opt]`.
2. Converts the option to an argument via `_convert_option_to_argument(opt, optdict)`.
3. Determines the section name from `argument.section` or falls back to `provider.name.capitalize()`.
4. Retrieves a section description from `provider.option_groups_descs.get(section)`; if the provider is not `MAIN_CHECKER_NAME` and has a docstring, uses the first paragraph of `__doc__` (split on `"\n\n"`) as the description.
5. Calls `_add_arguments_to_parser(section, section_desc, argument)`.

After processing all options, calls `_load_default_argument_values()`.

##### `_add_arguments_to_parser(self, section: str, section_desc: str \| None, argument: _Argument) -> None`

Adds a single argument to the correct argparse group. Looks up `section` in `_argument_groups_dict`; if not found, creates a new `argparse._ArgumentGroup` via `_arg_parser.add_argument_group(section, section_desc)` (or with only `title=section` if `section_desc` is `None`) and stores it. Then delegates to `_add_parser_option`.

##### `_add_parser_option(self, section_group: argparse._ArgumentGroup, argument: _Argument) -> None` (static method)

Dispatches the argument to `argparse` based on its concrete type:

- **`_StoreArgument`:** Calls `section_group.add_argument(*argument.flags, action=argument.action, default=argument.default, type=argument.type, help=argument.help, metavar=argument.metavar, choices=argument.choices)`.
- **`_StoreOldNamesArgument:** Same as above for the primary flags, then iterates over `argument.kwargs["old_names"]`, adding each old name as a hidden store option (`action="store"`, `help=argparse.SUPPRESS`) so its default value gets loaded.
- **`_StoreNewNamesArgument:** Same as `_StoreOldNamesArgument` but for new names (no hidden old-name loop).
- **`_StoreTrueArgument`:** Calls `section_group.add_argument(*argument.flags, action=argument.action, default=argument.default, help=argument.help)`.
- **`_CallableArgument`:** Calls `section_group.add_argument(*argument.flags, **argument.kwargs, action=argument.action, help=argument.help)`.
- **`_ExtendArgument`:** Calls `section_group.add_argument(*argument.flags, action=argument.action, default=argument.default, type=argument.type, help=argument.help, metavar=argument.metavar, choices=argument.choices, dest=argument.dest)`.

If the argument type is unrecognized, raises `UnrecognizedArgumentAction`.

##### `_load_default_argument_values(self) -> None`

Loads all registered option defaults by calling `self._arg_parser.parse_args([], self.config)` and assigning the result back to `self.config`.

##### `_parse_configuration_file(self, arguments: list[str]) -> None`

Parses a list of configuration-file arguments into the namespace via `self._arg_parser.parse_known_args(arguments, self.config)`. Collects any unrecognized options starting with `"--"` (stripping the prefix), and if any exist, raises `_UnrecognizedOptionError(options=unrecognized_options)`. Returns/updates `self.config` in place.

##### `_parse_command_line_configuration(self, arguments: Sequence[str] \| None = None) -> list[str]`

Parses command-line arguments into the namespace. If `arguments` is `None`, defaults to `sys.argv[1:]`. Calls `self._arg_parser.parse_known_args(arguments, self.config)` and updates `self.config`. Returns the list of unrecognized/parsed args (`parsed_args`).

##### `reset_parsers(self, usage: str = "") -> None` (DEPRECATED)

Emits a `DeprecationWarning`, then re-creates `cfgfile_parser` as `configparser.ConfigParser(inline_comment_prefixes=("#", ";"))` and `cmdline_parser` as `OptionParser(Option, usage=usage)`. Sets `self.cmdline_parser.options_manager = self` and populates `_optik_option_attrs` from the option class's `ATTRS`.

##### `register_options_provider(self, provider: ConfigProvider, own_group: bool = True) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. Appends `provider` to `_options_providers`. Filters out options whose optdict contains `"group"` into `non_group_spec_options`. If `own_group` is true and there are non-group-spec options, creates an option group named after the provider's uppercase name (with docstring as description) via `add_option_group`; otherwise iterates over each non-group-spec option and calls `add_optik_option(provider, self.cmdline_parser, opt, optdict)`. Then for each `(gname, gdoc)` in `provider.option_groups`, uppercases the group name, collects matching options (those whose `"group"` key matches), and calls `add_option_group(gname, gdoc, goptions, provider)`.

##### `add_option_group(self, group_name: str, _: str \| None, options: list[tuple[str, OptionDict]], provider: ConfigProvider) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. Creates or reuses an optparse `OptionGroup` in `_mygroups` and the config parser. For each `(opt, optdict)` in `options`, if the action is not already a string, sets it to `"callback"`, then calls `add_optik_option(provider, group, opt, optdict)`.

##### `add_optik_option(self, provider: ConfigProvider, optikcontainer: optparse.OptionParser \| optparse.OptionGroup, opt: str, optdict: OptionDict) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. Calls `self.optik_option(provider, opt, optdict)` to get `(args, optdict)`, then calls `optikcontainer.add_option(*args, **optdict)`. Records the provider in `_all_options[opt]` and updates `_maxlevel` with the option's level.

##### `optik_option(self, provider: ConfigProvider, opt: str, optdict: OptionDict) -> tuple[list[str], OptionDict]` (DEPRECATED)

Emits a `DeprecationWarning`. Copies `optdict`. If `"action"` is present in `optdict`, records the provider in `_nocallback_options`; otherwise sets action to `"callback"` with callback set to `self.cb_set_provider_option`. If `"default"` exists and help is present (and default is not None, and action is not store_true/store_false), appends `" [current: %default]"` to the help string, then deletes `"default"`. Builds args list starting with `"--"+opt`; if `"short"` is in optdict, records it in `_short_options`, appends `"-"+short` to args, and deletes `"short"`. Removes any keys from `optdict` not in `_optik_option_attrs`. Returns `(args, optdict)`.

##### `generate_config(self, stream: TextIO \| None = None, skipsections: tuple[str, ...] = ()) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. Iterates over `_arg_parser._action_groups`; for each group whose title is not in `skipsections`, collects options (skipping help and those without an optdict). Builds `(optname, optdict, value)` tuples where the value comes from `getattr(self.config, optname.replace("-", "_"))`. Filters out deprecated options. Writes sections via `utils.format_section(stream, section.upper(), sorted(options))` with blank lines between sections.

##### `load_provider_defaults(self) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. Iterates over `self.options_providers` and calls each provider's `load_defaults()` method.

##### `read_config_file(self, config_file: Path \| None = None, verbose: bool = False) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. If no config file is given, prints `"No config file found, using default configuration"` to stderr if verbose and returns. Expands environment variables and user home in the path. Raises `OSError` if the file doesn't exist. If the suffix is `.toml`, calls `_parse_toml(config_file, parser)`; otherwise opens with `encoding="utf_8_sig"`, reads into `self.cfgfile_parser`, then normalizes section titles: strips `"pylint."` prefix and uppercases non-uppercase sections that have values. Prints `"Using config file …"` to stderr if verbose.

##### `_parse_toml(self, config_file: Path, parser: configparser.ConfigParser) -> None` (DEPRECATED, static method)

Emits a `DeprecationWarning`. Opens the TOML file in binary mode and loads it with `tomllib.load(fp)`. Extracts `content["tool"]["pylint"]`; if missing, returns. For each section/value pair: uppercases the section name; skips non-dict values; for dict values, converts booleans to `"yes"`/`"no"`, lists to comma-joined strings, and everything else to `str`. Calls `parser.set(section_name, option, value)`; if a `NoSectionError` occurs, adds the section first.

##### `load_config_file(self) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. Iterates over all sections in `self.cfgfile_parser`; for each `(option, value)` pair, calls `self.global_set_option(option, value)`, silently catching `KeyError` and `optparse.OptionError`.

##### `load_configuration(self, **kwargs: Any) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. Delegates to `self.load_configuration_from_config(kwargs)` inside a warning-catch block.

##### `load_configuration_from_config(self, config: dict[str, Any]) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. For each `(opt, opt_value)` in `config`, replaces underscores with dashes in the key, looks up the provider from `_all_options[opt]`, and calls `provider.set_option(opt, opt_value)`.

##### `load_command_line_configuration(self, args: list[str] \| None = None) -> list[str]` (DEPRECATED)

Emits a `DeprecationWarning`. Defaults to `sys.argv[1:]` if `args` is `None`. Parses via `self.cmdline_parser.parse_args(args=args)`. For each provider in `_nocallback_options`, iterates over its config attributes and copies matching values from the parsed options namespace. Returns the remaining (unparsed) args.

##### `help(self, level: int \| None = None) -> str`

If `level` is not `None`, emits a `DeprecationWarning`. Returns `self._arg_parser.format_help()`.

##### `cb_set_provider_option(self, option, opt, value, parser)` (DEPRECATED)

Emits a `DeprecationWarning`. If the option starts with `"--"`, strips it; otherwise looks up the long name in `_short_options` using the character after `"-"`. If `value is None`, sets it to `1`. Calls `self.set_option(opt, value)`.

##### `global_set_option(self, opt: str, value: Any) -> None` (DEPRECATED)

Emits a `DeprecationWarning`. Delegates to `self.set_option(opt, value)`.

##### `_generate_config_file(self) -> None`

Generates a TOML configuration file and prints it to stdout. Creates a `tomlkit.document()` with a `"tool.pylint"` super-table. Iterates over sorted action groups (sorted by: non-"Master" first, then alphabetically). Skips the `"options"` group (help) and empty groups. For each remaining group:
1. Creates a `tomlkit.table()`.
2. Sorts actions by their option name (stripping `"--"` prefix).
3. For each action, looks up its optdict in `_option_dicts`; skips if not found or if `"hide_from_config_file"` is set.
4. Adds help text as TOML comments (wrapped to 79 chars).
5. Gets the current value from `self.config` (replacing `-` with `_`).
6. If the value is falsy, adds a comment line `"{optname} ="` and a newline; skips further processing.
7. Converts `re.Pattern` objects to their `.pattern` string; converts lists/tuples of patterns similarly.
8. Adds the option name and value to the group table, followed by a newline.
9. Adds the group table under its lowercase title in the pylint tool table.

Validates the generated TOML string with `tomllib.loads()`, then prints it.

##### `set_option(self, optname: str, value: Any, action: str \| None = "default_value", optdict: None \| str \| OptionDict = "default_value") -> None`

Sets an option on the namespace object. If `action != "default_value"`, emits a `DeprecationWarning`. If `optdict != "default_value"`, emits a `DeprecationWarning`. Replaces underscores with dashes in `optname`, converts the value to its argument form via `_parse_rich_type_value(value)`, and parses it into the namespace: `self.config = self._arg_parser.parse_known_args([f"--{optname.replace('_', '-')}", _parse_rich_type_value(value)], self.config)[0]`.

## pylint/config/utils.py
Now I have the full file. Here is the complete natural-language specification:

---

## Module-Level Preamble

### Imports

```python
from __future__ import annotations

import re
import warnings
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pylint import extensions, utils
from pylint.config.argument import (
    _CallableArgument,
    _ExtendArgument,
    _StoreArgument,
    _StoreNewNamesArgument,
    _StoreOldNamesArgument,
    _StoreTrueArgument,
)
from pylint.config.callback_actions import _CallbackAction
from pylint.config.exceptions import ArgumentPreprocessingError

if TYPE_CHECKING:
    from pylint.lint.run import Run
```

### Constants & Globals

**`PREPROCESSABLE_OPTIONS`**: `dict[str, tuple[bool, Callable[[Run, str | None], None]]]` — a module-level dictionary mapping CLI option strings to `(takes_argument, callback)` tuples. Its exact contents:

| Key | Tuple Value |
|---|---|
| `"--init-hook"` | `(True, _init_hook)` |
| `"--rcfile"` | `(True, _set_rcfile)` |
| `"--output"` | `(True, _set_output)` |
| `"--load-plugins"` | `(True, _add_plugins)` |
| `"--verbose"` | `(False, _set_verbose_mode)` |
| `"--enable-all-extensions"` | `(False, _enable_all_extensions)` |

---

## Code Objects (Functions)

### `_convert_option_to_argument(opt: str, optdict: dict[str, Any]) -> _StoreArgument | _StoreTrueArgument | _CallableArgument | _StoreOldNamesArgument | _StoreNewNamesArgument | _ExtendArgument`

Converts an option dictionary (`optdict`) into the appropriate `pylint.config.argument.Argument` subclass instance. The `opt` parameter is the option name (used to construct the long flag).

**Logic:**

1. **Deprecation warning for `level`:** If `"level"` is present in `optdict` and `"hide"` is absent, emit a `DeprecationWarning` instructing the user to use `"hide"` with a boolean instead.

2. **Build flags list:** Start with `[f"--{opt}"]`. If `"short"` key exists in `optdict`, append `f"-{optdict['short']}"`.

3. **Determine action type** via `action = optdict.get("action", "store")`. Then branch:
   - **`action == "store_true"`:** Return `_StoreTrueArgument(flags=flags, action=action, default=optdict.get("default", True), arg_help=optdict.get("help", ""), hide_help=optdict.get("hide", False), section=optdict.get("group", None))`.
   - **`action` is a subclass of `_CallbackAction`** (checked via `not isinstance(action, str) and issubclass(action, _CallbackAction)`): Return `_CallableArgument(flags=flags, action=action, arg_help=optdict.get("help", ""), kwargs=optdict.get("kwargs", {}), hide_help=optdict.get("hide", False), section=optdict.get("group", None))`.
   - **Otherwise (store/extend/etc.):** Attempt to read `default = optdict["default"]`; if `"default"` is missing, emit a `DeprecationWarning` and set `default = None`. Then:
     - **`action == "extend"`:** Return `_ExtendArgument(flags=flags, action=action, default=default, arg_type=optdict["type"], choices=optdict.get("choices", None), arg_help=optdict.get("help", ""), metavar=optdict.get("metavar", ""), hide_help=optdict.get("hide", False), section=optdict.get("group", None), dest=optdict.get("dest", None))`.
     - **`"kwargs"` in `optdict` and `"old_names"` in `optdict["kwargs"]`:** Return `_StoreOldNamesArgument(flags=flags, default=default, arg_type=optdict["type"], choices=optdict.get("choices", None), arg_help=optdict.get("help", ""), metavar=optdict.get("metavar", ""), hide_help=optdict.get("hide", False), kwargs=optdict.get("kwargs", {}), section=optdict.get("group", None))`.
     - **`"kwargs"` in `optdict` and `"new_names"` in `optdict["kwargs"]`:** Return `_StoreNewNamesArgument(flags=flags, default=default, arg_type=optdict["type"], choices=optdict.get("choices", None), arg_help=optdict.get("help", ""), metavar=optdict.get("metavar", ""), hide_help=optdict.get("hide", False), kwargs=optdict.get("kwargs", {}), section=optdict.get("group", None))`.
     - **`"dest"` in `optdict`:** Return `_StoreOldNamesArgument(flags=flags, default=default, arg_type=optdict["type"], choices=optdict.get("choices", None), arg_help=optdict.get("help", ""), metavar=optdict.get("metavar", ""), hide_help=optdict.get("hide", False), kwargs={"old_names": [optdict["dest"]]}, section=optdict.get("group", None))`.
     - **Fallback:** Return `_StoreArgument(flags=flags, action=action, default=default, arg_type=optdict["type"], choices=optdict.get("choices", None), arg_help=optdict.get("help", ""), metavar=optdict.get("metavar", ""), hide_help=optdict.get("hide", False), section=optdict.get("group", None))`.

**Return:** An instance of one of the six `Argument` subclasses, selected by the action type and optdict contents.

---

### `_parse_rich_type_value(value: Any) -> str`

Recursively converts rich TOML-compatible types into comma-separated string representations.

**Logic (recursive):**
1. If `value` is a `list` or `tuple`: return `",".join(_parse_rich_type_value(i) for i in value)` — recursively process each element and join with commas.
2. If `value` is a compiled regex pattern (`re.Pattern`): return `value.pattern` (the raw pattern string).
3. If `value` is a `dict`: return `",".join(f"{k}:{v}" for k, v in value.items())` — join each key-value pair as `"key:value"`, separated by commas.
4. Otherwise: return `str(value)`.

**Return:** A single flat string representation of the input value.

---

### `_init_hook(run: Run, value: str | None) -> None`

Executes arbitrary Python code from an init hook configuration value.

**Logic:** Asserts `value is not None`, then calls `exec(value)` to execute the code string in the current scope.

**Return:** `None`.

---

### `_set_rcfile(run: Run, value: str | None) -> None`

Sets the rcfile path on a `Run` instance.

**Logic:** Asserts `value is not None`, then assigns `run._rcfile = value`.

**Return:** `None`.

---

### `_set_output(run: Run, value: str | None) -> None`

Sets the output file/path on a `Run` instance.

**Logic:** Asserts `value is not None`, then assigns `run._output = value`.

**Return:** `None`.

---

### `_add_plugins(run: Run, value: str | None) -> None`

Adds plugin module names to the list of loadable plugins on a `Run` instance.

**Logic:** Asserts `value is not None`, then calls `utils._splitstrip(value)` (which splits the string by whitespace and strips each token) and extends `run._plugins` with the resulting list.

**Return:** `None`.

---

### `_set_verbose_mode(run: Run, value: str | None) -> None`

Enables verbose mode on a `Run` instance. This option takes no argument.

**Logic:** Asserts `value is None` (confirming no value was provided), then sets `run.verbose = True`.

**Return:** `None`.

---

### `_enable_all_extensions(run: Run, value: str | None) -> None`

Enables all pylint extension modules by scanning the extensions package directory. This option takes no argument.

**Logic:** Asserts `value is None`, then iterates over every file in the parent directory of `extensions.__file__`. For each entry whose suffix is `.py` and whose stem does not start with `"_"`:
- Construct the extension module name as `f"pylint.extensions.{filename.stem}"`.
- If that name is not already present in `run._plugins`, append it.

**Return:** `None`.

---

### `_preprocess_options(run: Run, args: Sequence[str]) -> list[str]`

Preprocesses command-line arguments before full config parsing begins. Handles special options from `PREPROCESSABLE_OPTIONS` by executing their callbacks immediately and removing them from the output; all other arguments pass through unchanged.

**Logic:**
1. Initialize `processed_args = []` (empty list).
2. Iterate with index `i` over `args`:
   - If `args[i]` does **not** start with `"--"`: append it to `processed_args`, increment `i`, continue.
   - Attempt to split the argument on `"="` into `(option, value)`. If no `"="` is found (raises `ValueError`), set `value = None`.
   - If `option` is **not** in `PREPROCESSABLE_OPTIONS`: append the original `argument` string to `processed_args`, increment `i`, continue.
   - Look up `(takearg, cb) = PREPROCESSABLE_OPTIONS[option]`:
     - If `takearg` is `True` and `value is None`: advance `i` by 1; if `i >= len(args)` or the next argument starts with `"-"`, raise `ArgumentPreprocessingError(f"Option {option} expects a value")`; otherwise set `value = args[i]`.
     - If `takearg` is `False` and `value is not None`: raise `ArgumentPreprocessingError(f"Option {option} doesn't expects a value")`.
   - Call `cb(run, value)` to execute the callback.
   - Increment `i` by 1 (the argument has been consumed; it is **not** appended to `processed_args`).
3. Return `processed_args`.

**Return:** A list of strings containing only the arguments that were not recognized as preprocessable options (in their original form, including any `"=value"` suffix).

## pylint/lint/base_options.py
I need to read the full file content since the structural summary elided most of it. Let me read it in chunks.