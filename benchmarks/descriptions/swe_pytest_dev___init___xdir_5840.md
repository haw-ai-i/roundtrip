## src/_pytest/config/__init__.py
I now have the complete file content. Let me write the comprehensive natural-language specification:

---

# Module Specification: `src/_pytest/config/__init__.py`

## 1. Module-Level Preamble

### Imports

```python
import argparse
import copy
import inspect
import os
import shlex
import sys
import types
import warnings
from functools import lru_cache
from pathlib import Path

import attr
import py
from packaging.version import Version
from pluggy import HookimplMarker
from pluggy import HookspecMarker
from pluggy import PluginManager

import _pytest._code
import _pytest.assertion
import _pytest.deprecated
import _pytest.hookspec  # the extension point definitions
from .exceptions import PrintHelp
from .exceptions import UsageError
from .findpaths import determine_setup
from .findpaths import exists
from _pytest._code import ExceptionInfo
from _pytest._code import filter_traceback
from _pytest.compat import importlib_metadata
from _pytest.outcomes import fail
from _pytest.outcomes import Skipped
from _pytest.pathlib import unique_path
from _pytest.warning_types import PytestConfigWarning
```

### Constants & Globals

- **`hookimpl`**: `HookimplMarker("pytest")` — marker for pytest hook implementations.
- **`hookspec`**: `HookspecMarker("pytest")` — marker for pytest hook specifications.
- **`essential_plugins`**: tuple of 5 strings: `"mark"`, `"main"`, `"runner"`, `"fixtures"`, `"helpconfig"` (the last provides `-p`). These plugins cannot be disabled via `-p no:X`.
- **`default_plugins`**: `essential_plugins + ("python", "terminal", "debugging", "unittest", "capture", "skipping", "tmpdir", "monkeypatch", "recwarn", "pastebin", "nose", "assertion", "junitxml", "resultlog", "doctest", "cacheprovider", "freeze_support", "setuponly", "setupplan", "stepwise", "warnings", "logging", "reports", "faulthandler")` — a tuple of 29 plugin spec strings.
- **`builtin_plugins`**: `set(default_plugins)` with `"pytester"` additionally added — a set of all builtin plugin names.

---

## 2. Code Objects (Classes and Functions)

### Class: `ConftestImportFailure(Exception)`

**Header:** Subclass of `Exception`.

**Attributes:**
- `path` — the path where conftest import failed, set in `__init__`.
- `excinfo` — the exception info tuple (`sys.exc_info()` result), set in `__init__`.

**`__init__(self, path, excinfo)`:** Calls `Exception.__init__(self, path, excinfo)` then assigns `self.path = path` and `self.excinfo = excinfo`.

---

### Function: `main(args=None, plugins=None)`

**Header:** Returns an exit code integer after performing an in-process test run.

**Logic:**
1. Imports `ExitCode` from `_pytest.main`.
2. Enters a try block. Inner try calls `_prepareconfig(args, plugins)` to obtain a `Config` object.
3. If `ConftestImportFailure` is raised: constructs an `ExceptionInfo` from the embedded `excinfo`, creates a `py.io.TerminalWriter(sys.stderr)`, writes `"ImportError while loading conftest '{path}'."` in red, filters the traceback via `filter_traceback`, generates a short representation (or `exconly()` if no traceback), and prints each line in red. Returns `4`.
4. On success: calls `config.hook.pytest_cmdline_main(config=config)` and returns its result. In a finally block, calls `config._ensure_unconfigure()`.
5. Outer except catches `UsageError`, writes `"ERROR: {msg}\n"` for each message in `e.args` to stderr in red, and returns `ExitCode.USAGE_ERROR`.

---

### Class: `cmdline`

**Header:** Compatibility namespace class.

**Attributes (class-level):**
- `main`: `staticmethod(main)` — a static method wrapping the module-level `main` function.

---

### Function: `filename_arg(path, optname)`

**Header:** Argparse type validator for filename arguments. Returns a string path.

**Logic:** If `os.path.isdir(path)`, raises `UsageError("{} must be a filename, given: {}".format(optname, path))`. Otherwise returns `path` unchanged.

---

### Function: `directory_arg(path, optname)`

**Header:** Argparse type validator for directory arguments. Returns a string path.

**Logic:** If not `os.path.isdir(path)`, raises `UsageError("{} must be a directory, given: {}".format(optname, path))`. Otherwise returns `path` unchanged.

---

### Function: `get_config(args=None, plugins=None)`

**Header:** Returns a `Config` instance with default plugins loaded.

**Logic:**
1. Creates a `PytestPluginManager()`.
2. Creates a `Config(pluginmanager, invocation_params=Config.InvocationParams(args=args, plugins=plugins, dir=Path().resolve()))`.
3. If `args is not None`, calls `pluginmanager.consider_preparse(args)` to handle `-p no:plugin` arguments.
4. For each spec in `default_plugins`, calls `pluginmanager.import_plugin(spec)`.
5. Returns the `config` object.

---

### Function: `get_plugin_manager()`

**Header:** Returns a new `PytestPluginManager` with default plugins already loaded.

**Logic:** Calls `get_config().pluginmanager` and returns it.

---

### Function: `_prepareconfig(args=None, plugins=None)`

**Header:** Prepares and returns a fully configured `Config` object.

**Logic:**
1. Initializes `warning = None`.
2. Normalizes `args`: if `None`, sets to `sys.argv[1:]`; if `py.path.local`, converts to `[str(args)]`; if not a list/tuple, raises `TypeError` with message `"args parameter expected to be a list or tuple of strings, got: {!r} (type: {})"`.
3. Calls `get_config(args, plugins)` to create the config and pluginmanager.
4. In a try block: if `plugins` is truthy, iterates each plugin — if string, calls `pluginmanager.consider_pluginarg(plugin)`, else calls `pluginmanager.register(plugin)`. If `warning` is set (currently always falsy), issues it via `_issue_warning_captured`. Returns the result of `pluginmanager.hook.pytest_cmdline_parse(pluginmanager=pluginmanager, args=args)`.
5. On any `BaseException`: calls `config._ensure_unconfigure()` then re-raises.

---

### Function: `_fail_on_non_top_pytest_plugins(conftestpath, confcutdir)`

**Header:** Raises an error for non-top-level conftests using `pytest_plugins`.

**Logic:** Constructs a multi-line error message explaining that defining `pytest_plugins` in a non-top-level conftest is no longer supported, with the conftest path and suggested rootdir path. Calls `fail(msg.format(conftestpath, confcutdir), pytrace=False)`.

---

### Class: `PytestPluginManager(PluginManager)`

**Header:** Extends `pluggy.PluginManager` with pytest-specific functionality for loading plugins from CLI, env vars, `pytest_plugins`, and conftest.py files. Metaclass: none specified (inherits from `PluginManager`).

**Attributes (instance):**
- `_conftest_plugins`: set — registered conftest modules.
- `_dirpath2confmods`: dict — maps directory paths to lists of conftest module objects.
- `_conftestpath2mod`: dict — maps conftest file paths to their loaded module objects.
- `_confcutdir`: path or None — the confcutdir for restricting conftest loading scope.
- `_noconftest`: bool — whether conftest loading is disabled.
- `_duplicatepaths`: set — tracks duplicate paths.
- `rewrite_hook`: assertion rewrite hook (initially `DummyRewriteHook()`).
- `_configured`: bool — True after `pytest_configure` has run.

**`__init__(self)`:**
1. Calls `super().__init__("pytest")`.
2. Initializes all instance attributes listed above.
3. Calls `self.add_hookspecs(_pytest.hookspec)` and `self.register(self)`.
4. If `os.environ.get("PYTEST_DEBUG")` is truthy: opens a duplicate of stderr with proper encoding, sets the trace writer to it, and enables tracing via `self.enable_tracing()`.
5. Sets `self.rewrite_hook = _pytest.assertion.DummyRewriteHook()` (will be replaced later).
6. Sets `self._configured = False`.

**`parse_hookimpl_opts(self, plugin, name)`:**
1. If `name` does not start with `"pytest_"`, returns `None`.
2. If `name == "pytest_plugins"`, returns `None`.
3. Gets the method via `getattr(plugin, name)` and calls `super().parse_hookimpl_opts(plugin, name)` to get base opts.
4. If the method is not a routine (`not inspect.isroutine(method)`), returns `None`.
5. If `opts is None` and name starts with `"pytest_"`, sets `opts = {}`.
6. If `opts is not None`: collects known marks from `getattr(method, "pytestmark", [])`, then for each of `("tryfirst", "trylast", "optionalhook", "hookwrapper")`, calls `opts.setdefault(name, hasattr(method, name) or name in known_marks)`.
7. Returns `opts`.

**`parse_hookspec_opts(self, module_or_class, name)`:**
1. Calls `super().parse_hookspec_opts(module_or_class, name)` to get base opts.
2. If `opts is None` and name starts with `"pytest_"`: collects known marks from the method's `pytestmark`, sets `opts = {"firstresult": hasattr(method, "firstresult") or "firstresult" in known_marks, "historic": hasattr(method, "historic") or "historic" in known_marks}`.
3. Returns `opts`.

**`register(self, plugin, name=None)`:**
1. If `name` is in `_pytest.deprecated.DEPRECATED_EXTERNAL_PLUGINS`, issues a `PytestConfigWarning` that the plugin has been merged into core and returns early (no registration).
2. Calls `super().register(plugin, name)` to get return value `ret`.
3. If `ret` is truthy: calls `self.hook.pytest_plugin_registered.call_historic(kwargs=dict(plugin=plugin, manager=self))`, then if the plugin is a `types.ModuleType`, calls `self.consider_module(plugin)`.
4. Returns `ret`.

**`getplugin(self, name)`:** Deprecated alias — returns `self.get_plugin(name)`.

**`hasplugin(self, name)`:** Returns `bool(self.get_plugin(name))`.

**`pytest_configure(self, config)` (hook):**
1. Calls `config.addinivalue_line("markers", "tryfirst: mark a hook implementation function such that the plugin machinery will try to call it first/as early as possible.")`.
2. Calls `config.addinivalue_line("markers", "trylast: mark a hook implementation function such that the plugin machinery will try to call it last/as late as possible.")`.
3. Sets `self._configured = True`.

**`_set_initial_conftests(self, namespace)`:** Loads initial conftest files from a preparsed namespace.
1. Gets current directory via `py.path.local()`.
2. Sets `_confcutdir` to `unique_path(current.join(namespace.confcutdir, abs=True))` if `namespace.confcutdir` is set, else `None`.
3. Sets `_noconftest = namespace.noconftest`, `_using_pyargs = namespace.pyargs`.
4. For each path in `namespace.file_or_dir`: strips node-id syntax (`::...`), creates an anchor via `current.join(path, abs=1)`, if the anchor exists calls `_try_load_conftest(anchor)` and sets `foundanchor = True`.
5. If no anchor was found, calls `_try_load_conftest(current)`.

**`_try_load_conftest(self, anchor)`:**
1. Calls `self._getconftestmodules(anchor)`.
2. If the anchor is a directory (`anchor.check(dir=1)`): for each entry matching `"test*"` that is also a directory, calls `self._getconftestmodules(x)`.

**`_getconftestmodules(self, path)` (cached via `@lru_cache(maxsize=128)`):**
1. If `_noconftest`, returns `[]`.
2. If the path is a file (`path.isfile()`), sets `directory = path.dirpath()`, else `directory = path`.
3. Normalizes directory via `unique_path(directory)`.
4. Iterates over all parent directories of `directory` (via `.parts()`): if `_confcutdir` is set and the parent is a relative child of `_confcutdir` (`self._confcutdir.relto(parent)`), skips it; otherwise, checks for `conftest.py` at each parent — if found, calls `_importconftest(conftestpath)` and appends to `clist`.
5. Stores `clist` in `self._dirpath2confmods[directory]` and returns it.

**`_rget_with_confmod(self, name, path)`:**
1. Gets conftest modules via `_getconftestmodules(path)`.
2. Iterates them in reverse order: tries to get the attribute `name` from each module; if found, returns `(mod, getattr(mod, name))`; if not found on any, raises `KeyError(name)`.

**`_importconftest(self, conftestpath)`:**
1. Normalizes path via `unique_path(conftestpath)` (realpath to avoid duplicate loads from symlinks).
2. Checks `_conftestpath2mod` cache — if present, returns the cached module.
3. Gets package path via `conftestpath.pypkgpath()`; if None, calls `_ensure_removed_sysmodule(conftestpath.purebasename)`.
4. Imports the conftest via `conftestpath.pyimport()`.
5. If the module has a `pytest_plugins` attribute AND `_configured` is True AND `_using_pyargs` is False: calls `_fail_on_non_top_pytest_plugins(conftestpath, self._confcutdir)`.
6. On import exception: raises `ConftestImportFailure(conftestpath, sys.exc_info())`.
7. Adds the module to `_conftest_plugins`, stores in `_conftestpath2mod[conftestpath]`.
8. If the conftest's directory is already a key in `_dirpath2confmods`: iterates all entries and appends the module to any list whose path is under or equal to the conftest's directory.
9. Calls `self.trace("loaded conftestmodule %r" % (mod))` and `self.consider_conftest(mod)`. Returns the module.

**`consider_preparse(self, args)`:** Iterates through args looking for `-p` or `-p<plugin>` flags; for each found plugin spec, calls `consider_pluginarg(parg)`. Handles both `-p value` and `-pvalue` forms.

**`consider_pluginarg(self, arg)`:**
1. If `arg.startswith("no:")`: extracts the name (after `"no:"`). If it's in `essential_plugins`, raises `UsageError`. If name is `"cacheprovider"`, sets both `"stepwise"` and `"pytest_stepwise"` as blocked. Calls `self.set_blocked(name)` and if not already prefixed with `"pytest_"`, also blocks `"pytest_" + name`.
2. Otherwise: unblocks the plugin by deleting from `_name2plugin` if currently blocked (value is None), for both the bare name and `"pytest_" + name` form. Then calls `self.import_plugin(arg, consider_entry_points=True)`.

**`consider_conftest(self, conftestmodule)`:** Calls `self.register(conftestmodule, name=conftestmodule.__file__)`.

**`consider_env(self)`:** Imports plugin specs from the `"PYTEST_PLUGINS"` environment variable via `_import_plugin_specs()`.

**`consider_module(self, mod)`:** Imports plugin specs from `mod.pytest_plugins` via `_import_plugin_specs()`.

**`_import_plugin_specs(self, spec)`:** Calls `_get_plugin_specs_as_list(spec)` to get a list of plugin names, then calls `self.import_plugin(import_spec)` for each.

**`import_plugin(self, modname, consider_entry_points=False)`:**
1. Asserts `modname` is a string; converts via `str(modname)`.
2. If the module name is blocked or already loaded (`get_plugin` returns non-None), returns early.
3. Determines import spec: if in `builtin_plugins`, prepends `"_pytest."`; otherwise uses `modname` as-is.
4. Calls `self.rewrite_hook.mark_rewrite(importspec)`.
5. If `consider_entry_points`: calls `self.load_setuptools_entrypoints("pytest11", name=modname)`; if any were loaded, returns early.
6. Tries `__import__(importspec)`. On `ImportError`: constructs a new `ImportError` with message `'Error importing plugin "{modname}": {e.args[0]}'`, preserves the original traceback via `.with_traceback(tb)`, and re-raises. On `Skipped`: issues a `PytestConfigWarning("skipped plugin {!r}: {}".format(modname, e.msg))` via `_issue_warning_captured`.
7. On success: gets the module from `sys.modules[importspec]` and calls `self.register(mod, modname)`.

---

### Function: `_get_plugin_specs_as_list(specs)`

**Header:** Parses a list of plugin specs into a list of strings. Returns an empty list for `None`, module types, or empty strings.

**Logic:**
1. If `specs is not None` and not a `types.ModuleType`: if it's a string, splits on `","` (empty string → `[]`); if not a list/tuple, raises `UsageError("Plugin specs must be a ','-separated string or a list/tuple of strings for plugin names. Given: %r" % specs)`. Returns `list(specs)`.
2. Otherwise returns `[]`.

---

### Function: `_ensure_removed_sysmodule(modname)`

**Header:** Removes a module from `sys.modules` if present.

**Logic:** Tries `del sys.modules[modname]`; catches and ignores `KeyError`.

---

### Class: `Notset`

**Header:** Sentinel class for representing unset values.

**`__repr__(self)`:** Returns the string `"<NOTSET>"`.

---

### Variable: `notset`

**Value:** `Notset()` — a singleton sentinel instance.

---

### Function: `_iter_rewritable_modules(package_files)`

**Header:** Generator yielding module/package names that can be marked for assertion rewriting from a collection of package file paths.

**Logic:** For each filename in `package_files`: if it's a simple `.py` file (no `/` in name, ends with `.py`), yields the stem (without `.py`); if it's a package init (`fn.count("/") == 1` and ends with `"__init__.py"`), yields the directory name.

---

### Class: `Config`

**Header:** Access to configuration values, pluginmanager, and plugin hooks. Contains an inner class `InvocationParams`.

#### Inner Class: `Config.InvocationParams`

**Header:** A frozen attrs dataclass (`@attr.s(frozen=True)`).

**Attributes (all via `attr.ib()`):**
- `args`: the command-line arguments passed to `pytest.main()`.
- `plugins`: list of extra plugins, or `None`.
- `dir`: the directory where `pytest.main()` was invoked from (`Path` object).

#### Instance Attributes (initialized in `__init__`):
- `option`: `argparse.Namespace` — command-line option values.
- `invocation_params`: `InvocationParams` instance.
- `_parser`: `Parser` instance with usage string `"%(prog)s [options] [FILE_OR_DIR] [FILE_OR_DIR] [...]"`, processopt callback set to `self._processopt`.
- `pluginmanager`: the `PytestPluginManager`.
- `trace`: trace root from pluginmanager for "config".
- `hook`: the hook proxy from pluginmanager.
- `_inicache`: dict — caches ini configuration values.
- `_override_ini`: tuple — override-ini options from CLI (`-o` flags).
- `_opt2dest`: dict — maps short/long option names to their dest attribute name.
- `_cleanup`: list — cleanup functions to call on unconfigure.
- `_configured`: bool — False initially, set True during configuration.

**`__init__(self, pluginmanager, *, invocation_params=None)`:**
1. If `invocation_params is None`, creates one with `args=()`, `plugins=None`, `dir=Path().resolve()`.
2. Sets `self.option = argparse.Namespace()` and `self.invocation_params = invocation_params`.
3. Creates `_parser` as a `Parser` (from `.argparsing`) with usage string using `FILE_OR_DIR` placeholder, and `processopt=self._processopt`.
4. Assigns `pluginmanager`, `trace`, `hook`.
5. Initializes `_inicache = {}`, `_override_ini = ()`, `_opt2dest = {}`, `_cleanup = []`.
6. Registers itself with the pluginmanager under name `"pytestconfig"`.
7. Sets `_configured = False`.
8. Calls `self.hook.pytest_addoption.call_historic(kwargs=dict(parser=self._parser))` to allow plugins to add options before preparse.

**Property: `invocation_dir`:** Returns `py.path.local(str(self.invocation_params.dir))` for backward compatibility.

**`add_cleanup(self, func)`:** Appends `func` to `self._cleanup`.

**`_do_configure(self)`:** Asserts `_configured` is False, sets it True, then calls `self.hook.pytest_configure.call_historic(kwargs=dict(config=self))` inside a `warnings.catch_warnings()` context with `"default"` filter.

**`_ensure_unconfigure(self)`:** If `_configured` is True: sets it to False, calls `self.hook.pytest_unconfigure(config=self)`, clears the call history of `pytest_configure`. Then pops and calls each function in `self._cleanup`.

**`get_terminal_writer(self)`:** Returns `self.pluginmanager.get_plugin("terminalreporter")._tw`.

**`pytest_cmdline_parse(self, pluginmanager, args)` (hook):**
1. Calls `self.parse(args)`. On `UsageError`: if `--version` or `-V` is present, calls `_pytest.helpconfig.showversion(self)`; if `--help`, `-h`, or help flag is set, prints the parser's help and a note about minimal help due to UsageError. Re-raises the exception.
2. Returns `self`.

**`notify_exception(self, excinfo, option=None)`:** If `option.fulltrace` is True, sets style to `"long"`, else `"native"`. Gets an exception representation via `excinfo.getrepr(funcargs=True, showlocals=getattr(option, "showlocals", False), style=style)`. Calls `self.hook.pytest_internalerror(excrepr=excrepr, excinfo=excinfo)`. If no handler responded (`not any(res)`), writes each line of the representation prefixed with `"INTERNALERROR> "` to stderr.

**`cwd_relative_nodeid(self, nodeid)`:** If `invocation_dir != rootdir`, joins `nodeid` to `rootdir` then computes relative path from `invocation_dir` via `bestrelpath`. Returns the (possibly modified) nodeid string.

**`fromdictargs(cls, option_dict, args)` (classmethod):** Constructs a config usable for subprocesses. Calls `get_config(args)`, updates `config.option.__dict__` with `option_dict`, calls `config.parse(args, addopts=False)`, then for each plugin in `config.option.plugins`, calls `config.pluginmanager.consider_pluginarg(x)`. Returns the config.

**`_processopt(self, opt)`:** For each short and long option name on `opt`, maps it to `opt.dest` in `_opt2dest`. If `opt` has a `default` attribute and `opt.dest` is set: if the dest doesn't exist as an attribute of `self.option`, sets it to `opt.default`.

**`pytest_load_initial_conftests(self, early_config)` (hook, `trylast=True`):** Calls `self.pluginmanager._set_initial_conftests(early_config.known_args_namespace)`.

**`_initini(self, args)`:**
1. Parses known/unknown args via `_parser.parse_known_and_unknown_args(args, namespace=copy.copy(self.option))`.
2. Calls `determine_setup(ns.inifilename, ns.file_or_dir + unknown_args, rootdir_cmd_arg=ns.rootdir or None, config=self)` to get `(rootdir, inifile, inicfg)`, assigns all three.
3. Sets `_parser.extra_info["rootdir"]` and `["inifile"]`.
4. Adds ini values `"addopts"` (type `"args"`) and `"minversion"` (type string).
5. Sets `_override_ini = ns.override_ini or ()`.

**`_consider_importhook(self, args)`:** Installs the PEP 302 assertion rewriting import hook.
1. Parses known/unknown args to get `assertmode` (default `"plain"`).
2. If mode is `"rewrite"`: tries `_pytest.assertion.install_importhook(self)`; on `SystemError`, falls back to `"plain"`. On success, calls `_mark_plugins_for_rewrite(hook)`.
3. Calls `_warn_about_missing_assertion(mode)`.

**`_mark_plugins_for_rewrite(self, hook)`:** Marks pytest plugins for assertion rewriting.
1. Sets `self.pluginmanager.rewrite_hook = hook`.
2. If `"PYTEST_DISABLE_PLUGIN_AUTOLOAD"` env var is set, returns early.
3. Builds a generator of package file strings from all distributions that have any entry point in the `"pytest11"` group.
4. For each rewritable module name yielded by `_iter_rewritable_modules(package_files)`, calls `hook.mark_rewrite(name)`.

**`_validate_args(self, args, via)`:** Sets `_parser._config_source_hint = via`, parses known/unknown args with a copy of `self.option`, then deletes the hint. Returns `args`.

**`_preparse(self, args, addopts=True)`:** The main preparse pipeline:
1. If `addopts`: reads `PYTEST_ADDOPTS` from env; if non-empty, splits it via `shlex.split`, validates it, and prepends to `args[:]`.
2. Calls `_initini(args)` to determine rootdir/inifile/inicfg.
3. If `addopts`: gets ini `"addopts"`, validates them, and prepends to `args[:]`.
4. Calls `_checkversion()` to validate minversion.
5. Calls `_consider_importhook(args)`.
6. Calls `pluginmanager.consider_preparse(args)` for `-p` flags.
7. If not disabled by env: calls `pluginmanager.load_setuptools_entrypoints("pytest11")`.
8. Calls `pluginmanager.consider_env()`.
9. Parses known args into `self.known_args_namespace`.
10. If `confcutdir` is None and `inifile` exists, sets it to the inifile's directory.
11. Calls `hook.pytest_load_initial_conftests(early_config=self, args=args, parser=self._parser)`. On `ConftestImportFailure`: if help or version was requested, issues a warning via `_issue_warning_captured`; otherwise re-raises.

**`_checkversion(self)`:** Gets `minver` from `inicfg.get("minversion", None)`. If set and `Version(minver) > Version(pytest.__version__)`, raises `pytest.UsageError` with message showing the ini file path, line number, required version, and actual version.

**`parse(self, args, addopts=True)`:** Parses cmdline arguments into this config object.
1. Asserts `"args"` attribute doesn't already exist (can only parse once).
2. Asserts `invocation_params.args == args`.
3. Calls `hook.pytest_addhooks.call_historic(kwargs=dict(pluginmanager=self.pluginmanager))`.
4. Calls `_preparse(args, addopts=addopts)`.
5. Calls deprecated hook `pytest_cmdline_preparse(config=self, args=args)`.
6. Sets `_parser.after_preparse = True`.
7. Parses and sets option values via `_parser.parse_setoption(args, self.option, namespace=self.option)` into `self.args`. If no test paths remain: if `invocation_dir == rootdir`, uses `getini("testpaths")`; else uses `[str(invocation_dir)]`.
8. On `PrintHelp`: catches and passes (help was already printed).

**`addinivalue_line(self, name, line)`:** Gets the ini value list via `getini(name)` (asserts it's a list), appends `line` to it inline.

**`getini(self, name)`:** Returns cached config value from `_inicache[name]`. On cache miss, calls `_getini(name)`, caches the result, and returns it. Raises `ValueError` if the name hasn't been registered via `parser.addini`.

**`_getini(self, name)`:**
1. Looks up `(description, type, default)` from `_parser._inidict[name]`; raises `ValueError("unknown configuration value: {!r}".format(name))` on KeyError.
2. Checks override-ini values via `_get_override_ini_value(name)` (last matching `-o` wins). If a value is found there, uses it; otherwise falls back to `inicfg[name]`, then to `default`, then to type-specific defaults (`""` for None type, `[]` for None default with typed fields).
3. Type conversion: `"pathlist"` — splits value via `shlex.split`, joins each relative path against the ini file's directory as absolute paths; `"args"` — returns `shlex.split(value)`; `"linelist"` — splits on newlines, strips whitespace, filters empty strings; `"bool"` — converts via `_strtobool` then `bool`; otherwise (type is None) returns raw string value.

**`_get_override_ini_value(self, name)`:** Iterates over `_override_ini` list of `"ini=value"` strings. Splits each on first `"="`. If the key matches `name`, sets `value`. Returns the last matching value or `None`. Raises `UsageError` if any entry lacks `"="`.

**`_getconftest_pathlist(self, name, path)`:**
1. Calls `pluginmanager._rget_with_confmod(name, path)` to get `(mod, relroots)`. On `KeyError`, returns `None`.
2. Gets the module's directory via `py.path.local(mod.__file__).dirpath()`.
3. For each relative root: if not already a `py.path.local`, replaces `/` with `os.sep`, joins against modpath as absolute path. Appends to values list and returns it.

**`getoption(self, name, default=notset, skip=False)`:** Returns command-line option value.
1. Maps the name via `_opt2dest.get(name, name)` (supports literal `--OPT` names).
2. Gets the attribute from `self.option`. If `val is None and skip`, raises `AttributeError(name)`. Returns `val`.
3. On `AttributeError`: if `default is not notset`, returns default; if `skip`, calls `pytest.skip("no {!r} option found".format(name))`; otherwise raises `ValueError("no option named {!r}".format(name))`.

**`getvalue(self, name, path=None)`:** Deprecated — returns `self.getoption(name)`.

**`getvalueorskip(self, name, path=None)`:** Deprecated — returns `self.getoption(name, skip=True)`.

---

### Function: `_assertion_supported()`

**Header:** Returns a boolean indicating whether Python assert statements are executable.

**Logic:** Tries `assert False`; if it raises `AssertionError`, returns `True`; else (no exception in the `else` branch), returns `False`.

---

### Function: `_warn_about_missing_assertion(mode)`:**

**Header:** Writes a warning to stderr about disabled assertions.

**Logic:** If not `_assertion_supported()`: if mode is `"plain"`, writes `"WARNING: ASSERTIONS ARE NOT EXECUTED and FAILING TESTS WILL PASS.  Are you using python -O?"`; else, writes `"WARNING: assertions not in test modules or plugins will be ignored because assert statements are not executed by the underlying Python interpreter (are you using python -O?)\n"`.

---

### Function: `setns(obj, dic)`:**

**Header:** Recursively sets namespace attributes on an object and populates `__all__`. Also sets each name on the `pytest` module.

**Logic:** For each `(name, value)` in `dic.items()`: if value is a dict, gets or creates a submodule (`types.ModuleType("pytest.{name}")`, registers it in `sys.modules`, sets `__all__ = []`), appends name to `obj.__all__`, and recursively calls `setns(mod, value)`. Otherwise: sets the attribute on `obj`, appends name to `obj.__all__`, and also sets `setattr(pytest, name, value)`.

---

### Function: `create_terminal_writer(config, *args, **kwargs)`

**Header:** Creates a `py.io.TerminalWriter` instance configured according to the config's color option.

**Logic:** Creates `tw = py.io.TerminalWriter(*args, **kwargs)`. If `config.option.color == "yes"`, sets `tw.hasmarkup = True`; if `"no"`, sets `tw.hasmarkup = False`. Returns `tw`.

---

### Function: `_strtobool(val)`

**Header:** Converts a string representation of truth to 1 (true) or 0 (false). Copied from `distutils.util`.

**Logic:** Lowercases the value. If in `("y", "yes", "t", "true", "on", "1")`, returns `1`; if in `("n", "no", "f", "false", "off", "0")`, returns `0`; otherwise raises `ValueError("invalid truth value {!r}".format(val))`.

## src/_pytest/pathlib.py
Now I have the complete file (346 lines). Here is the full natural-language specification:

---

## Module-Level Preamble

### Imports

```python
import atexit
import fnmatch
import itertools
import operator
import os
import shutil
import sys
import uuid
import warnings
from functools import partial
from os.path import expanduser, expandvars, isabs, normcase, sep
from posixpath import sep as posix_sep
from _pytest.warning_types import PytestWarning
```

Conditional import (Python 3.6+ vs fallback):
- If `sys.version_info[:2] >= (3, 6)`: `from pathlib import Path, PurePath`
- Else: `from pathlib2 import Path, PurePath`

### Constants & Globals

- **`__all__`** = `["Path", "PurePath"]` — exported names.
- **`LOCK_TIMEOUT`** = `60 * 60 * 3` (i.e., 10800 seconds / 3 hours).
- **`get_lock_path`** = `operator.methodcaller("joinpath", ".lock")` — a callable that, given a path-like object, returns the result of calling `.joinpath(".lock")` on it.

---

## Code Objects (Functions)

### `ensure_reset_dir(path)`

Ensures `path` is an empty directory:
1. If `path.exists()` is true, calls `rm_rf(path)` to recursively remove all contents.
2. Calls `path.mkdir()` to create the (now-empty) directory.

No return value.

---

### `on_rm_rf_error(func, path: str, exc, *, start_path)`

Error handler callback for `shutil.rmtree(onerror=...)`. Handles known read-only errors during recursive removal.

1. Extracts `excvalue = exc[1]` from the exception tuple.
2. If `excvalue` is **not** a `PermissionError`, emits a `PytestWarning("(rm_rf) error removing {}: {}".format(path, excvalue))` and returns (no further action).
3. If `func` is not one of `(os.rmdir, os.remove, os.unlink)`, emits the same warning and returns.
4. Otherwise (it's a permission error on a removable file/dir):
   - Imports `stat` locally.
   - Defines inner function `chmod_rw(p: str)` that reads mode via `os.stat(p).st_mode` and calls `os.chmod(p, mode | stat.S_IRUSR | stat.S_IWUSR)`.
   - Converts `path` to a `Path` object. If it is a file (`p.is_file()`), iterates over `p.parents`, calling `chmod_rw(str(parent))` on each parent until reaching `start_path` (inclusive).
   - Calls `chmod_rw(str(path))` on the path itself.
5. Finally, calls `func(path)` to retry the original operation.

No return value; may raise if the retry also fails.

---

### `rm_rf(path: Path)`

Recursively removes a directory tree, even if some elements are read-only.

1. Creates an error handler via `onerror = partial(on_rm_rf_error, start_path=path)`.
2. Calls `shutil.rmtree(str(path), onerror=onerror)`.

No return value.

---

### `find_prefixed(root, prefix)`

Generator that yields all immediate children of `root` whose name starts with `prefix`, case-insensitively.

1. Computes `l_prefix = prefix.lower()`.
2. Iterates over `root.iterdir()`; for each element `x`, if `x.name.lower().startswith(l_prefix)`, yields `x`.

Returns a generator of `Path` objects.

---

### `extract_suffixes(iter, prefix)`

Generator that takes an iterator over path-like objects and yields the suffix portion (the part after the prefix) from each element's name.

1. Computes `p_len = len(prefix)`.
2. For each `p` in `iter`, yields `p.name[p_len:]`.

Returns a generator of strings.

---

### `find_suffixes(root, prefix)`

Combines `find_prefixed` and `extract_suffixes`: returns the suffix portions (after `prefix`) of all immediate children of `root` whose names start with `prefix`, case-insensitively.

1. Calls `find_prefixed(root, prefix)`.
2. Passes its result to `extract_suffixes(..., prefix)`.

Returns a generator of strings.

---

### `parse_num(maybe_num)`

Attempts to parse a string as an integer; returns `-1` on failure.

1. Tries `int(maybe_num)`, returning the result.
2. On `ValueError`, returns `-1`.

Returns an `int`.

---

### `_force_symlink(root, target, link_to)`

Creates (or overwrites) a symlink at `root.joinpath(target)` pointing to `link_to`. Ignores all errors (best-effort).

1. Computes `current_symlink = root.joinpath(target)`.
2. Tries `current_symlink.unlink()`; catches and ignores any `OSError`.
3. Tries `current_symlink.symlink_to(link_to)`; catches and ignores any exception.

No return value.

---

### `make_numbered_dir(root, prefix)`

Creates a new directory under `root` with the given `prefix` followed by an incrementing numeric suffix (e.g., `pytest-of-user/pytest123`). Retries up to 10 times; raises on failure.

1. Loops up to 10 times:
   - Computes `max_existing = max(map(parse_num, find_suffixes(root, prefix)), default=-1)`.
   - Sets `new_number = max_existing + 1`.
   - Constructs `new_path = root.joinpath("{}{}".format(prefix, new_number))`.
   - Tries `new_path.mkdir()`:
     - On success: calls `_force_symlink(root, prefix + "current", new_path)` and returns `new_path`.
     - On any exception: continues to the next iteration.
2. If all 10 attempts fail (the `else` clause of the `for` loop), raises `EnvironmentError("could not create numbered dir with prefix {prefix} in {root} after 10 tries")`.

Returns a `Path` object on success.

---

### `create_cleanup_lock(p)`

Creates an atomic lock file (`.lock`) inside directory `p`, writing the current PID into it. Raises `EnvironmentError` if the lock already exists or is renamed during creation.

1. Computes `lock_path = get_lock_path(p)`.
2. Tries `os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)` to atomically create the file:
   - On `FileExistsError`, raises `EnvironmentError("cannot create lockfile in {path}".format(path=p))` chained from the original exception.
3. Writes the current PID (as bytes) into the open fd via `os.write(fd, str(pid).encode())`.
4. Closes the fd with `os.close(fd)`.
5. Verifies `lock_path.is_file()`; if false, raises `EnvironmentError("lock path got renamed after successful creation")`.
6. Returns `lock_path` (a `Path`).

---

### `register_cleanup_lock_removal(lock_path, register=atexit.register)`

Registers an atexit handler that removes the lock file on process exit, but only if the current PID matches the original PID (to handle forks).

1. Captures `pid = os.getpid()`.
2. Defines inner function `cleanup_on_exit(lock_path=lock_path, original_pid=pid)`:
   - Gets `current_pid = os.getpid()`. If it differs from `original_pid` (fork), returns without action.
   - Tries `lock_path.unlink()`; catches and ignores `(OSError, IOError)`.
3. Calls `register(cleanup_on_exit)` (defaulting to `atexit.register`) and returns its result.

Returns whatever `register(...)` returns.

---

### `maybe_delete_a_numbered_dir(path)`

Atomically removes a numbered directory by first acquiring an exclusive cleanup lock, renaming the directory to a unique "garbage" name, then recursively removing it. Ignores all OS-level errors (races).

1. Initializes `lock_path = None`.
2. In a try block:
   - Calls `create_cleanup_lock(path)` and stores result in `lock_path`.
   - Gets `parent = path.parent`.
   - Creates `garbage = parent.joinpath("garbage-{}".format(uuid.uuid4()))`.
   - Renames `path` to `garbage` via `path.rename(garbage)`.
   - Calls `rm_rf(garbage)` to remove it.
3. Catches `(OSError, EnvironmentError)` and returns silently (known race conditions: concurrent cleanup, deletable folder found, Windows cwd issues).
4. In a finally block: if `lock_path is not None`, tries `lock_path.unlink()`; catches `(OSError, IOError)` and ignores.

No return value.

---

### `ensure_deletable(path, consider_lock_dead_if_created_before)`

Checks whether a numbered directory can be safely deleted by examining its lock file. Returns `True` if deletable, `False` otherwise.

1. If `path.is_symlink()`, returns `False`.
2. Computes `lock = get_lock_path(path)`.
3. If `not lock.exists()`, returns `True` (no lock means safe to delete).
4. Tries `lock_time = lock.stat().st_mtime`:
   - On any exception, returns `False`.
5. Else: if `lock_time < consider_lock_dead_if_created_before`, calls `lock.unlink()` and returns `True`; otherwise returns `False`.

Returns a `bool`.

---

### `try_cleanup(path, consider_lock_dead_if_created_before)`

Attempts to clean up a numbered directory if it is deemed deletable.

1. Calls `ensure_deletable(path, consider_lock_dead_if_created_before)`.
2. If true, calls `maybe_delete_a_numbered_dir(path)`.

No return value.

---

### `cleanup_candidates(root, prefix, keep)`

Generator yielding paths of numbered directories that are candidates for removal (i.e., those with numbers at or below the cutoff). Follows py.path semantics.

1. Computes `max_existing = max(map(parse_num, find_suffixes(root, prefix)), default=-1)`.
2. Sets `max_delete = max_existing - keep`.
3. Creates two independent iterators from `find_prefixed(root, prefix)` via `itertools.tee(paths, paths2)`.
4. Computes `numbers = map(parse_num, extract_suffixes(paths2, prefix))`.
5. Zips `paths` and `numbers`; for each `(path, number)`, if `number <= max_delete`, yields `path`.

Returns a generator of `Path` objects.

---

### `cleanup_numbered_dir(root, prefix, keep, consider_lock_dead_if_created_before)`

Cleans up old numbered directories under `root` with the given `prefix`, keeping only the most recent `keep` directories. Also cleans up any "garbage-*" directories.

1. For each path yielded by `cleanup_candidates(root, prefix, keep)`, calls `try_cleanup(path, consider_lock_dead_if_created_before)`.
2. For each path matching `root.glob("garbage-*")`, calls `try_cleanup(path, consider_lock_dead_if_created_before)`.

No return value.

---

### `make_numbered_dir_with_cleanup(root, prefix, keep, lock_timeout)`

Creates a new numbered directory with cleanup of old ones, retrying up to 10 times on failure.

1. Initializes `e = None`.
2. Loops up to 10 times:
   - Tries:
     - Calls `p = make_numbered_dir(root, prefix)`.
     - Calls `lock_path = create_cleanup_lock(p)`.
     - Calls `register_cleanup_lock_removal(lock_path)`.
   - On exception: stores it in `e` and continues.
   - On success:
     - Computes `consider_lock_dead_if_created_before = p.stat().st_mtime - lock_timeout`.
     - Calls `cleanup_numbered_dir(root=root, prefix=prefix, keep=keep, consider_lock_dead_if_created_before=consider_lock_dead_if_created_before)`.
     - Returns `p`.
3. After the loop (all 10 attempts failed), asserts `e is not None` and raises `e`.

Returns a `Path` object on success; raises `EnvironmentError` on failure.

---

### `resolve_from_str(input, root)`

Resolves a string path relative to a root directory, handling environment variables and user home expansion.

1. Asserts `not isinstance(input, Path)` (would break on Python 2).
2. Converts `root` to `Path(root)`.
3. Applies `expanduser(input)` then `expandvars(input)`.
4. If the result is absolute (`isabs(input)`), returns `Path(input)`.
5. Otherwise, returns `root.joinpath(input)`.

Returns a `Path` object.

---

### `fnmatch_ex(pattern, path)`

FNMatcher port from py.path.common that works with `PurePath` instances. Unlike `PurePath.match()`, this matches the **entire** path against the pattern (not per-component), so patterns like `"tests/**/doc/test*.py"` match `"tests/foo/bar/doc/test_foo.py"`.

1. Converts `path` to `PurePath(path)`.
2. Detects Windows: `iswin32 = sys.platform.startswith("win")`.
3. If on Windows, the pattern contains no Windows separators (`sep`) but does contain POSIX separators (`posix_sep`), replaces all `posix_sep` with `sep` in the pattern.
4. Determines what to match against:
   - If `sep` is not in the pattern: matches only `path.name`.
   - Otherwise: matches `str(path)`. If `path.is_absolute()` but the pattern is not OS-absolute (`not os.path.isabs(pattern)`), prepends `"*{os.sep}"` to the pattern.
5. Returns `fnmatch.fnmatch(name, pattern)`.

Returns a `bool`.

---

### `parts(s)`

Given a path string `s`, returns all its prefix components as a set of strings.

1. Splits `s` by `sep` into `parts`.
2. For each index `i` in range of the split length, joins `parts[:i+1]` with `sep`; if empty (empty input), uses `sep` itself.
3. Returns a set of these joined strings.

Returns a `set` of strings representing all path prefixes including the root separator for absolute paths.

---

### `unique_path(path)`

Returns a case-normalized unique path string, useful on case-insensitive file systems (e.g., Windows). Converts to the same type as the input `path`.

1. Calls `path.realpath()` to resolve symlinks and normalize.
2. Converts to string via `str(...)`, then applies `normcase(...)` for case normalization.
3. Constructs a new path of the same type: `type(path)(...)`.

Returns a path-like object (same type as input).