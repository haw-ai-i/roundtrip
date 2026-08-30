## src/_pytest/python.py
Now I have the complete file. Let me write the comprehensive natural-language specification:

---

# Module Specification: `src/_pytest/python.py`

## 1. Module-Level Preamble

### Imports

```python
import enum
import fnmatch
import inspect
import itertools
import os
import sys
import types
import warnings
from collections import Counter
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, Tuple, Union

import py
import _pytest
from _pytest import fixtures, nodes
from _pytest._code import filter_traceback, getfslineno
from _pytest._code.code import ExceptionInfo, TerminalRepr
from _pytest._io import TerminalWriter
from _pytest._io.saferepr import saferepr
from _pytest.compat import ascii_escaped, final, get_default_arg_names, get_real_func, getimfunc, getlocation
from _pytest.compat import is_async_function, is_generator, NOTSET, REGEX_TYPE, safe_getattr, safe_isclass, STRING_TYPES
from _pytest.config import Config, ExitCode, hookimpl
from _pytest.config.argparsing import Parser
from _pytest.deprecated import check_ispytest, FSCOLLECTOR_GETHOOKPROXY_ISINITPATH
from _pytest.fixtures import FuncFixtureInfo
from _pytest.main import Session
from _pytest.mark import MARK_GEN, ParameterSet
from _pytest.mark.structures import get_unpacked_marks, Mark, MarkDecorator, normalize_mark_list
from _pytest.outcomes import fail, skip
from _pytest.pathlib import bestrelpath, fnmatch_ex, import_path, ImportPathMismatchError, parts, visit
from _pytest.warning_types import PytestCollectionWarning, PytestUnhandledCoroutineWarning

if TYPE_CHECKING:
    from typing_extensions import Literal
    from _pytest.fixtures import _Scope
```

### Constants & Globals

- **`IGNORED_ATTRIBUTES`** (frozenset): A pre-computed frozenset of attribute names to skip during collection iteration. Built by unioning `dir(types.ModuleType("empty_module"))`, the set `{"__builtins__", "__file__", "__cached__"}`, `dir(_EmptyClass)`, and `dir(_EmptyClass())`. The temporary `_EmptyClass` is deleted after construction.

---

## 2. Code Objects (Functions and Classes)

### Function: `pytest_addoption(parser: Parser) -> None`
Registers CLI options and ini configuration for test discovery:
- Adds `--fixtures`/`--funcargs` boolean flag (`dest="showfixtures"`, default `False`) to show available fixtures.
- Adds `--fixtures-per-test` boolean flag (`dest="show_fixtures_per_test"`, default `False`).
- Registers ini option `python_files` (type `"args"`, default `["test_*.py", "*_test.py"]`) for glob patterns matching test module files.
- Registers ini option `python_classes` (type `"args"`, default `["Test"]`) for class name prefixes/globs.
- Registers ini option `python_functions` (type `"args"`, default `["test"]`) for function/method name prefixes/globs.
- Registers ini option `disable_test_id_escaping_and_forfeit_all_rights_to_community_support` (type `"bool"`, default `False`).

### Function: `pytest_cmdline_main(config: Config) -> Optional[Union[int, ExitCode]]`
If `config.option.showfixtures` is true, calls `showfixtures(config)` and returns `0`. If `config.option.show_fixtures_per_test` is true, calls `show_fixtures_per_test(config)` and returns `0`. Otherwise returns `None`.

### Function: `pytest_generate_tests(metafunc: "Metafunc") -> None`
Iterates over all `"parametrize"` markers on `metafunc.definition`. For each marker, calls `metafunc.parametrize(*marker.args, **marker.kwargs, _param_mark=marker)`.

### Function: `pytest_configure(config: Config) -> None`
Registers two marker documentation entries via `config.addinivalue_line("markers", ...)`: `"parametrize"` (with full description of usage) and `"usefixtures"`.

### Function: `async_warn_and_skip(nodeid: str) -> None`
Constructs a multi-line warning message explaining that async functions are not natively supported, listing required plugins (anyio, pytest-asyncio, pytest-tornasync, pytest-trio, pytest-twisted). Emits the warning as `PytestUnhandledCoroutineWarning(msg.format(nodeid))`, then calls `skip(msg="async def function and no async plugin installed (see warnings)")`.

### Function: `pytest_pyfunc_call(pyfuncitem: "Function") -> Optional[object]`
Hook implementation with `trylast=True`. Retrieves the test function via `pyfuncitem.obj`. If it is an async function (`is_async_function(testfunction)`), calls `async_warn_and_skip(pyfuncitem.nodeid)`. Builds `testargs` dict from `funcargs` filtered to only those in `pyfuncitem._fixtureinfo.argnames`. Calls `testfunction(**testargs)`. If the result has `__await__` or `__aiter__`, calls `async_warn_and_skip(pyfuncitem.nodeid)`. Returns `True`.

### Function: `pytest_collect_file(fspath: Path, path: py.path.local, parent: nodes.Collector) -> Optional["Module"]`
If `fspath.suffix == ".py"` and either the file is an initpath (`parent.session.isinitpath(fspath)`) or it matches any pattern in `parent.config.getini("python_files") + ["__init__.py"]`, delegates to `ihook.pytest_pycollect_makemodule(fspath=fspath, path=path, parent=parent)` and returns the resulting `Module`. Otherwise returns `None`.

### Function: `path_matches_patterns(path: Path, patterns: Iterable[str]) -> bool`
Returns `any(fnmatch_ex(pattern, path) for pattern in patterns)`.

### Function: `pytest_pycollect_makemodule(fspath: Path, path: py.path.local, parent) -> "Module"`
If `fspath.name == "__init__.py"`, returns `Package.from_parent(parent, fspath=path)`. Otherwise returns `Module.from_parent(parent, fspath=path)`.

### Function: `pytest_pycollect_makeitem(collector: "PyCollector", name: str, obj: object)`
Hook with `trylast=True`. If `obj` is a class (`safe_isclass(obj)`) and `collector.istestclass(obj, name)`, returns `Class.from_parent(collector, name=name, obj=obj)`. If `collector.istestfunction(obj, name)`: unwraps `__func__` if present; checks that `obj` (or its real func via `get_real_func`) is a function — if not, emits a `PytestCollectionWarning`; otherwise if `getattr(obj, "__test__", True)` is true: if it's a generator (`is_generator(obj)`), creates a `Function`, adds an xfail marker with reason "yield tests were removed in pytest 4.0 - {name} will be ignored", warns, and returns the function; else calls `collector._genfunctions(name, obj)` and returns the list.

### Class: `PyobjMixin(nodes.Node)`
A mixin that inherits from `Node` to carry typing information (positioned before Node in MRO). Has class attribute `_ALLOW_MARKERS = True`.

**Properties:**
- **`module`**: Returns the Python module object via `self.getparent(Module)`, returning `node.obj` if found, else `None`.
- **`cls`**: Returns the Python class object via `self.getparent(Class)`, returning `node.obj` if found, else `None`.
- **`instance`**: Returns the Python instance object via `self.getparent(Instance)`, returning `node.obj` if found, else `None`.
- **`obj`** (property with setter): Lazily retrieves the underlying Python object. If `_obj` is None, calls `_getobj()` to populate it. If `_ALLOW_MARKERS` is true, extends `self.own_markers` with `get_unpacked_marks(self.obj)`. Setter directly assigns `self._obj = value`.

**Method: `_getobj(self)`**
Asserts `self.parent is not None`. Returns `getattr(self.parent.obj, self.name)`.

**Method: `getmodpath(self, stopatmodule: bool = True, includemodule: bool = False) -> str`**
Builds a dotted Python path string. Reverses the chain from `self.listchain()`, iterates nodes: skips `Instance`; for `Module`, strips `.py` extension and either breaks (if `stopatmodule`) or appends name; appends all other node names. Reverses back and joins with `"."`.

**Method: `reportinfo(self) -> Tuple[Union[py.path.local, str], int, str]`**
Retrieves `obj`. If `obj` has a `compat_co_firstlineno` integer attribute (nose compatibility), gets the file path from `sys.modules[obj.__module__].__file__` (stripping `.pyc` to `.py`) and uses that lineno. Otherwise calls `getfslineno(obj)`, converting `Path` to `py.path.local` if needed. Calls `self.getmodpath()` for modpath. Returns `(fspath, lineno, modpath)`.

### Class: `_EmptyClass`
A dummy class used only during module-level construction of `IGNORED_ATTRIBUTES`. Deleted immediately after.

### Class: `PyCollector(PyobjMixin, nodes.Collector)`

**Method: `funcnamefilter(self, name: str) -> bool`**
Returns `self._matches_prefix_or_glob_option("python_functions", name)`.

**Method: `isnosetest(self, obj: object) -> bool`**
Returns `safe_getattr(obj, "__test__", False) is True` (strict identity check).

**Method: `classnamefilter(self, name: str) -> bool`**
Returns `self._matches_prefix_or_glob_option("python_classes", name)`.

**Method: `istestfunction(self, obj: object, name: str) -> bool`**
If `funcnamefilter(name)` or `isnosetest(obj)`: unwraps `staticmethod` via `__func__`; returns `callable(obj) and fixtures.getfixturemarker(obj) is None`. Else returns `False`.

**Method: `istestclass(self, obj: object, name: str) -> bool`**
Returns `classnamefilter(name) or isnosetest(obj)`.

**Method: `_matches_prefix_or_glob_option(self, option_name: str, name: str) -> bool`**
Iterates over `self.config.getini(option_name)`. For each option, checks if `name.startswith(option)` (returns True). If the option contains glob characters (`*`, `?`, `[`) and `fnmatch.fnmatch(name, option)` matches, returns True. Otherwise returns False.

**Method: `collect(self) -> Iterable[Union[nodes.Item, nodes.Collector]]`**
If `getattr(self.obj, "__test__", True)` is falsy, returns empty list. Collects `self.obj.__dict__` and each base class's `__dict__` from the MRO into a list of dicts. Iterates over all dicts (using `list()` to avoid mutation issues), skipping names in `IGNORED_ATTRIBUTES` or already-seen names. For each `(name, obj)`, calls `ihook.pytest_pycollect_makeitem(collector=self, name=name, obj=obj)`. Collects results into a list (handling both single items and lists). Sorts by `(str(fspath), lineno)` from `reportinfo()`. Returns the sorted list.

**Method: `_genfunctions(self, name: str, funcobj) -> Iterator["Function"]`**
Gets the parent `Module` object (`modulecol.obj`) and optional parent `Class` object (`clscol.obj`). Gets fixture manager from `self.session._fixturemanager`. Creates a `FunctionDefinition.from_parent(self, name=name, callobj=funcobj)` and retrieves its `_fixtureinfo`. Creates a `Metafunc(definition=..., fixtureinfo=..., config=self.config, cls=cls, module=module, _ispytest=True)`. Collects `pytest_generate_tests` methods from the module (if present) and class (if present, instantiated). Calls `self.ihook.pytest_generate_tests.call_extra(methods, dict(metafunc=metafunc))`. If `not metafunc._calls`, yields a single `Function.from_parent(self, name=name, fixtureinfo=fixtureinfo)`. Otherwise: calls `fixtures.add_funcarg_pseudo_fixture_def(self, metafunc, fm)` to add funcargs as fixturedefs; calls `fixtureinfo.prune_dependency_tree()`; for each `callspec` in `metafunc._calls`, yields a `Function.from_parent(self, name=f"{name}[{callspec.id}]", callspec=callspec, callobj=funcobj, fixtureinfo=fixtureinfo, keywords={callspec.id: True}, originalname=name)`.

### Class: `Module(nodes.File, PyCollector)`
Collector for test classes and functions.

**Method: `_getobj(self)`**
Returns `self._importtestmodule()`.

**Method: `collect(self) -> Iterable[Union[nodes.Item, nodes.Collector]]`**
Calls `_inject_setup_module_fixture()`, then `_inject_setup_function_fixture()`, then `self.session._fixturemanager.parsefactories(self)`, then calls `super().collect()` (inherited from `PyCollector`).

**Method: `_inject_setup_module_fixture(self) -> None`**
Gets `setup_module` and `teardown_module` via `_get_first_non_fixture_func`. If both are None, returns. Defines a hidden autouse module-scoped fixture named `f"xunit_setup_module_fixture_{self.obj.__name__}"` that calls `setup_module(request.module)` (if present), yields, then calls `teardown_module(request.module)` (if present). Assigns the fixture to `self.obj.__pytest_setup_module`.

**Method: `_inject_setup_function_fixture(self) -> None`**
Gets `setup_function` and `teardown_function` via `_get_first_non_fixture_func`. If both are None, returns. Defines a hidden autouse function-scoped fixture named `f"xunit_setup_function_fixture_{self.obj.__name__}"`: if `request.instance is not None`, yields and returns (delegates to setup_method); otherwise calls `setup_function(request.function)` (if present), yields, then calls `teardown_function(request.function)` (if present). Assigns the fixture to `self.obj.__pytest_setup_function`.

**Method: `_importtestmodule(self)`**
Gets `--import-mode` option. Calls `import_path(self.fspath, mode=importmode)`. Catches:
- `SyntaxError`: raises `self.CollectError(ExceptionInfo.from_current().getrepr(style="short"))`.
- `ImportPathMismatchError`: raises `self.CollectError("import file mismatch:...")` with details.
- `ImportError`: filters traceback if verbose < 2, formats repr, raises `self.CollectError("ImportError while importing test module...")`.
- `skip.Exception`: re-raises if `e.allow_module_level`, else raises `self.CollectError("Using pytest.skip outside of a test...")`.
Calls `self.config.pluginmanager.consider_module(mod)`. Returns `mod`.

### Class: `Package(Module)`
Collector for package directories.

**Method: `__init__(self, fspath: py.path.local, parent: nodes.Collector, config=None, session=None, nodeid=None) -> None`**
Sets `session = parent.session`, calls `nodes.FSCollector.__init__(self, fspath, parent=parent, config=config, session=session, nodeid=nodeid)`. Sets `self.name = os.path.basename(str(fspath.dirname))`.

**Method: `setup(self) -> None`**
Gets `setup_module` and `teardown_module` via `_get_first_non_fixture_func`. Calls `setup_module(self.obj)` (if present). Adds a finalizer calling `teardown_module(self.obj)` (if present).

**Method: `gethookproxy(self, fspath: "os.PathLike[str]")`**
Warns with `FSCOLLECTOR_GETHOOKPROXY_ISINITPATH`, returns `self.session.gethookproxy(fspath)`.

**Method: `isinitpath(self, path: Union[str, "os.PathLike[str]"]) -> bool`**
Warns with `FSCOLLECTOR_GETHOOKPROXY_ISINITPATH`, returns `self.session.isinitpath(path)`.

**Method: `_recurse(self, direntry: "os.DirEntry[str]") -> bool`**
Returns False for `__pycache__`. Checks `pytest_ignore_collect` hook. Returns False if any pattern from `config.getini("norecursedirs")` matches via `fnmatch_ex`. Otherwise returns True.

**Method: `_collectfile(self, fspath: Path, handle_dupes: bool = True) -> Sequence[nodes.Collector]`**
Asserts the path is a file. Checks `pytest_ignore_collect` hook if not an initpath. If `handle_dupes` and `keepduplicates` option is false, checks `self.config.pluginmanager._duplicatepaths`; skips if already present, otherwise adds to set. Returns `ihook.pytest_collect_file(fspath=fspath, path=path, parent=self)`.

**Method: `collect(self) -> Iterable[Union[nodes.Item, nodes.Collector]]`**
Checks for `__init__.py` in the package directory; if it matches `python_files` patterns, yields a `Module.from_parent(self, fspath=...)`. Iterates over `visit(str(this_path), recurse=self._recurse)`: skips own `__init__.py`; skips entries whose path components contain a registered `pkg_prefix` (unless they are the prefix's own `__init__.py`). For files, yields from `_collectfile(path)`; for non-directories, continues; for directories with an `__init__.py`, adds to `pkg_prefixes`.

### Function: `_call_with_optional_argument(func, arg) -> None`
Checks `func.__code__.co_argcount`; decrements by 1 if `inspect.ismethod(func)`. If arg count > 0, calls `func(arg)`; otherwise calls `func()`.

### Function: `_get_first_non_fixture_func(obj: object, names: Iterable[str])`
Iterates over `names`, gets each attribute from `obj`. Returns the first one that is not None and has no fixture marker (`fixtures.getfixturemarker(meth) is None`).

### Class: `Class(PyCollector)`
Collector for test methods.

**Method: `from_parent(cls, parent, *, name, obj=None, **kw)`**
Calls `super().from_parent(name=name, parent=parent, **kw)`.

**Method: `collect(self) -> Iterable[Union[nodes.Item, nodes.Collector]]`**
If `getattr(self.obj, "__test__", True)` is falsy, returns empty list. If `hasinit(self.obj)`, warns about `__init__` constructor and returns []. If `hasnew(self.obj)`, warns about `__new__` constructor and returns []. Calls `_inject_setup_class_fixture()` and `_inject_setup_method_fixture()`. Returns `[Instance.from_parent(self, name="()")]`.

**Method: `_inject_setup_class_fixture(self) -> None`**
Gets `setup_class` and `teardown_class` via `_get_first_non_fixture_func`/`getattr`. If both are None, returns. Defines a hidden autouse class-scoped fixture named `f"xunit_setup_class_fixture_{self.obj.__qualname__}"`: calls `getimfunc(setup_class)` then `_call_with_optional_argument(func, self.obj)`, yields, then does the same for teardown. Assigns to `self.obj.__pytest_setup_class`.

**Method: `_inject_setup_method_fixture(self) -> None`**
Gets `setup_method` and `teardown_method` via `_get_first_non_fixture_func`/`getattr`. If both are None, returns. Defines a hidden autouse function-scoped fixture named `f"xunit_setup_method_fixture_{self.obj.__qualname__}"`: gets `method = request.function`; calls `getattr(self, "setup_method")` with method (if present), yields, then does the same for teardown. Assigns to `self.obj.__pytest_setup_method`.

### Class: `Instance(PyCollector)`
Collector for test class instances. Has `_ALLOW_MARKERS = False`.

**Method: `_getobj(self)`**
Asserts parent is not None. Returns `self.parent.obj()`.

**Method: `collect(self) -> Iterable[Union[nodes.Item, nodes.Collector]]`**
Calls `self.session._fixturemanager.parsefactories(self)`, then calls `super().collect()`.

**Method: `newinstance(self)`**
Sets `self.obj = self._getobj()` and returns it.

### Function: `hasinit(obj: object) -> bool`
Gets `__init__` from obj. If truthy, returns `init != object.__init__`. Otherwise returns False.

### Function: `hasnew(obj: object) -> bool`
Gets `__new__` from obj. If truthy, returns `new != object.__new__`. Otherwise returns False.

### Class: `CallSpec2` (decorated with `@final`)
Holds parametrization call specifications.

**Attributes:**
- `metafunc`: reference to the parent `Metafunc`.
- `funcargs: Dict[str, object]`: function argument values.
- `_idlist: List[str]`: list of ID components.
- `params: Dict[str, object]`: parameter values (for indirect fixtures).
- `_arg2scopenum: Dict[str, int]`: maps arg names to scope numbers for sorting.
- `marks: List[Mark]`: marks applied by parametrization.
- `indices: Dict[str, int]`: maps arg names to param indices.

**Method: `__init__(self, metafunc: "Metafunc") -> None`**
Initializes all attributes to empty containers.

**Method: `copy(self) -> "CallSpec2"`**
Creates a new `CallSpec2(metafunc=self.metafunc)` and copies all dicts/lists (`funcargs`, `params`, `marks`, `indices`, `_arg2scopenum`, `_idlist`). Returns the copy.

**Method: `getparam(self, name: str) -> object`**
Returns `self.params[name]`. Raises `ValueError(name)` on KeyError.

**Property: `id(self) -> str`**
Returns `"-"`.join(map(str, self._idlist)).

**Method: `setmulti2(self, valtypes: Mapping[str, "Literal['params', 'funcargs']"], argnames: Sequence[str], valset: Iterable[object], id: str, marks: Iterable[Union[Mark, MarkDecorator]], scopenum: int, param_index: int) -> None`**
For each `(arg, val)` pair from `zip(argnames, valset)`: raises ValueError if arg already in params or funcargs; sets `self.params[arg] = val` or `self.funcargs[arg] = val` based on `valtypes`; records index and scopenum. Appends `id` to `_idlist`. Extends marks with `normalize_mark_list(marks)`.

### Class: `Metafunc` (decorated with `@final`)
Passed to the `pytest_generate_tests` hook for test parametrization.

**Attributes:**
- `definition`: reference to `FunctionDefinition`.
- `config`: reference to `Config`.
- `module`: module object where test is defined.
- `function`: the underlying Python test function (`definition.obj`).
- `fixturenames`: set of fixture names from `fixtureinfo.names_closure`.
- `cls`: class object or None.
- `_calls: List[CallSpec2]`: accumulated call specifications.
- `_arg2fixturedefs`: fixture definitions dict from `fixtureinfo.name2fixturedefs`.

**Method: `__init__(self, definition: "FunctionDefinition", fixtureinfo: fixtures.FuncFixtureInfo, config: Config, cls=None, module=None, *, _ispytest: bool = False) -> None`**
Calls `check_ispytest(_ispytest)`. Initializes all attributes as described above.

**Method: `parametrize(self, argnames: Union[str, List[str], Tuple[str, ...]], argvalues: Iterable[Union[ParameterSet, Sequence[object], object]], indirect: Union[bool, Sequence[str]] = False, ids: Optional[...] = None, scope: "Optional[_Scope]" = None, *, _param_mark: Optional[Mark] = None) -> None`**
Normalizes `argnames`/`argvalues` via `ParameterSet._for_parametrize`. Rejects `"request"` as an argname. Determines scope (default from `_find_parametrized_scope`). Validates arg names against function signature and fixture usage. Resolves value types ("params" vs "funcargs") based on `indirect`. Handles pre-generated IDs from `_param_mark`. Calls `_resolve_arg_ids` to produce ID strings. Converts scope string to scopenum via `scope2index`. Creates new call specs: for each existing callspec (or a fresh one if none), for each `(param_id, param_set)` pair, copies the callspec, calls `setmulti2(...)` with the resolved values/marks/scopenum/index, and appends to `newcalls`. Replaces `self._calls` with `newcalls`.

**Method: `_resolve_arg_ids(self, argnames: Sequence[str], ids: Optional[...], parameters: Sequence[ParameterSet], nodeid: str) -> List[str]`**
If `ids is None`: sets `idfn = None`, `ids_ = None`. If `callable(ids)`: sets `idfn = ids`, `ids_ = None`. Otherwise: calls `_validate_ids(ids, parameters, self.function.__name__)` to get `ids_`. Returns `idmaker(argnames, parameters, idfn, ids_, self.config, nodeid=nodeid)`.

**Method: `_validate_ids(self, ids: Iterable[...], parameters: Sequence[ParameterSet], func_name: str) -> List[Union[None, str]]`**
Tries to get `len(ids)`; if TypeError, tries to iterate it. If not iterable at all, raises TypeError. Handles special case of `num_ids == 0`. Fails if `num_ids != len(parameters)` and `num_ids != 0`. Iterates over ids (up to num_ids), converting float/int/bool to str, keeping None/str as-is; fails on other types with a descriptive message. Returns the list of validated IDs.

**Method: `_resolve_arg_value_types(self, argnames: Sequence[str], indirect: Union[bool, Sequence[str]]) -> Dict[str, "Literal['params', 'funcargs']"]`**
If `indirect` is bool: maps all argnames to `"params"` if True, `"funcargs"` if False. If `indirect` is a sequence: maps all to `"funcargs"`, then overrides each listed indirect arg to `"params"` (validating existence). Otherwise fails with type error. Returns the dict.

**Method: `_validate_if_using_arg_names(self, argnames: Sequence[str], indirect: Union[bool, Sequence[str]]) -> None`**
Gets default argument names from `self.function`. For each argname: if not in fixturenames and in default args, fails (already has a default value). If not in fixturenames and not in defaults: determines whether it's expected as a "fixture" or "argument" based on `indirect`, then fails with appropriate message.

### Function: `_find_parametrized_scope(argnames: Sequence[str], arg2fixturedefs: Mapping[str, Sequence[fixtures.FixtureDef[object]]], indirect: Union[bool, Sequence[str]]) -> "fixtures._Scope"`
If all arguments are indirect fixtures (all names in `indirect` list or `indirect is True`), collects scopes from the corresponding fixture definitions and returns the most narrow scope by iterating `reversed(fixtures.scopes)`. Otherwise returns `"function"`.

### Function: `_ascii_escaped_by_config(val: Union[str, bytes], config: Optional[Config]) -> str`
If `config is None`, sets `escape_option = False`. Otherwise reads the `disable_test_id_escaping_and_forfeit_all_rights_to_community_support` ini option. Returns `val if escape_option else ascii_escaped(val)`.

### Function: `_idval(val: object, argname: str, idx: int, idfn: Optional[Callable[[Any], Optional[object]]], nodeid: Optional[str], config: Optional[Config]) -> str`
If `idfn` is provided: calls it on `val`; if result is not None, uses that as the new val; catches exceptions and raises ValueError with context. If no idfn but config exists: calls `config.hook.pytest_make_parametrize_id(...)`; returns hook_id if non-empty. Then checks type of val: STRING_TYPES → `_ascii_escaped_by_config`; None/float/int/bool → `str(val)`; regex → `ascii_escaped(val.pattern)`; NOTSET → falls through; enum → `str(val)`; has `__name__` that is str → returns it; else returns `str(argname) + str(idx)`.

### Function: `_idvalset(idx: int, parameterset: ParameterSet, argnames: Iterable[str], idfn: Optional[...], ids: Optional[List[Union[None, str]]], nodeid: Optional[str], config: Optional[Config]) -> str`
If `parameterset.id is not None`, returns it. Otherwise gets the ID at index `idx` from `ids` (or None). If id is None, calls `_idval` for each `(val, argname)` pair and joins with `"-"`. Else returns `_ascii_escaped_by_config(id, config)`.

### Function: `idmaker(argnames: Iterable[str], parametersets: Iterable[ParameterSet], idfn: Optional[...] = None, ids: Optional[List[...]] = None, config: Optional[Config] = None, nodeid: Optional[str] = None) -> List[str]`
Computes `_idvalset` for each parameter set. Checks uniqueness of resolved IDs; if duplicates exist, uses `Counter` to count occurrences and a `defaultdict(int)` suffix tracker to append numeric suffixes (0, 1, ...) to non-unique IDs. Returns the final list.

### Function: `show_fixtures_per_test(config)`
Imports `wrap_session` from `_pytest.main`, returns `wrap_session(config, _show_fixtures_per_test)`.

### Function: `_show_fixtures_per_test(config: Config, session: Session) -> None`
Performs collection. Creates terminal writer. Defines helper `get_best_relpath(func)` using `getlocation` and `bestrelpath`. Defines `write_fixture(fixture_def)`: skips fixtures starting with `_` if verbose ≤ 0; formats argname with location if verbose > 0, else just argname; writes in green; writes docstring via `write_docstring` or red "no docstring available". Defines `write_item(item)`: gets `_fixtureinfo`; if none or empty name2fixturedefs, returns. Writes separator with item name and relative path. For each sorted fixture def group, writes the last (used) fixture. Iterates over `session.items`, calling `write_item` for each.

### Function: `showfixtures(config: Config) -> Union[int, ExitCode]`
Imports `wrap_session`, returns `wrap_session(config, _showfixtures_main)`.

### Function: `_showfixtures_main(config: Config, session: Session) -> None`
Performs collection. Creates terminal writer. Gets fixture manager. Iterates over `fm._arg2fixturedefs`: for each `(argname, fixturedefs)` pair (asserting non-None), iterates fixturedefs; deduplicates by `(argname, location)` in a `seen` set; appends tuples of `(len(baseid), module, bestrelpath, argname, fixturedef)` to `available`. Sorts the list. Iterates over sorted entries: prints module header (skipping `_pytest.` modules) on first occurrence per module. Skips fixtures starting with `_` if verbose ≤ 0. Writes argname in green; scope in cyan if not function; location in yellow if verbose > 0. Writes docstring or red "no docstring available". Prints blank line after each fixture.

### Function: `write_docstring(tw: TerminalWriter, doc: str, indent: str = "    ") -> None`
Splits doc by newlines and writes each prefixed with the indent string.

### Class: `Function(PyobjMixin, nodes.Item)`
Item responsible for setting up and executing a Python test function. `_ALLOW_MARKERS = False`.

**Method: `__init__(self, name: str, parent, config: Optional[Config] = None, callspec: Optional[CallSpec2] = None, callobj=NOTSET, keywords=None, session: Optional[Session] = None, fixtureinfo: Optional[FuncFixtureInfo] = None, originalname: Optional[str] = None) -> None`**
Calls `super().__init__(name, parent, config=config, session=session)`. If `callobj is not NOTSET`, sets `self.obj = callobj`. Sets `originalname = originalname or name`. Updates keywords from `self.obj.__dict__`. Extends markers with `get_unpacked_marks(self.obj)`. If `callspec` provided: sets `self.callspec = callspec`; adds marks to both keywords and own_markers. If `keywords` provided, updates keywords. Adds marker names as True values in keywords (for `-k` matching). If `fixtureinfo is None`, creates it via `session._fixturemanager.getfixtureinfo(self, self.obj, self.cls, funcargs=True)`. Sets `_fixtureinfo`, `fixturenames`, calls `_initrequest()`.

**Method: `from_parent(cls, parent, **kw)`**
Calls `super().from_parent(parent=parent, **kw)`.

**Method: `_initrequest(self) -> None`**
Initializes `self.funcargs = {}` and creates `self._request = fixtures.FixtureRequest(self, _ispytest=True)`.

**Property: `function`**
Returns `getimfunc(self.obj)`.

**Method: `_getobj(self)`**
Asserts parent is not None. Returns `getattr(self.parent.obj, self.originalname)`.

**Property: `_pyfuncitem`**
Returns `self` (compatibility shim).

**Method: `runtest(self) -> None`**
Calls `self.ihook.pytest_pyfunc_call(pyfuncitem=self)`.

**Method: `setup(self) -> None`**
If parent is `Instance`, calls `self.parent.newinstance()` and refreshes `self.obj = self._getobj()`. Calls `self._request._fillfixtures()`.

**Method: `_prunetraceback(self, excinfo: ExceptionInfo[BaseException]) -> None`**
If not fulltrace mode: gets code path/lineno from the real function; cuts traceback at that location (first attempt with firstlineno, second without); if still unchanged, filters via `filter_traceback`; falls back to original traceback. Filters remaining frames. If tbstyle is "auto" and more than 2 frames, sets short repr style on middle frames.

**Method: `repr_failure(self, excinfo: ExceptionInfo[BaseException]) -> Union[str, TerminalRepr]`**
Gets tbstyle (defaulting to "long" if "auto"). Calls `self._repr_failure_py(excinfo, style=style)`.

### Class: `FunctionDefinition(Function)`
A temporary gap solution. Overrides `runtest(self)` to raise `RuntimeError("function definitions are not supposed to be run as tests")`. Sets `setup = runtest` (same behavior).

## src/_pytest/unittest.py
Here is the complete natural-language specification of `src/_pytest/unittest.py`:

---

## Module-Level Preamble

### Imports

```python
import sys
import traceback
import types
from typing import Any, Callable, Generator, Iterable, List, Optional, Tuple, Type, TYPE_CHECKING, Union

import _pytest._code
import pytest
from _pytest.compat import getimfunc, is_async_function
from _pytest.config import hookimpl
from _pytest.fixtures import FixtureRequest
from _pytest.nodes import Collector, Item
from _pytest.outcomes import exit, fail, skip, xfail
from _pytest.python import Class, Function, PyCollector
from _pytest.runner import CallInfo
```

### TYPE_CHECKING block (runtime not executed)

```python
if TYPE_CHECKING:
    import unittest
    import twisted.trial.unittest
    from _pytest.fixtures import _Scope
    _SysExcInfoType = Union[
        Tuple[Type[BaseException], BaseException, types.TracebackType],
        Tuple[None, None, None],
    ]
```

### Constants & Globals

- **`_SysExcInfoType`** (type alias, TYPE_CHECKING only): `Union[Tuple[Type[BaseException], BaseException, types.TracebackType], Tuple[None, None, None]]` — the type of a raw Python exception info tuple as returned by `sys.exc_info()`.

---

## Code Objects

### Function: `pytest_pycollect_makeitem(collector: PyCollector, name: str, obj: object) -> Optional["UnitTestCase"]`

**Purpose:** pytest hook implementation that discovers whether `obj` is a subclass of `unittest.TestCase`, and if so, creates a `UnitTestCase` collector item.

**Logic:**
1. Attempts to retrieve the `unittest` module from `sys.modules`. If the key does not exist or any exception occurs during the check, returns `None`.
2. Checks whether `obj` is a subclass of `ut.TestCase`. If not, returns `None`.
3. If yes, creates and returns a new `UnitTestCase` item via `UnitTestCase.from_parent(collector, name=name, obj=obj)`.

**Return:** A `UnitTestCase` instance if `obj` is a `unittest.TestCase` subclass; otherwise `None`.

---

### Class: `UnitTestCase(Class)`

**Inheritance:** Extends `_pytest.python.Class`.

**Class attribute:**
- `nofuncargs = True` — marker telling the fixture manager that children of this collector do not support funcargs.

#### Method: `collect(self) -> Iterable[Union[Item, Collector]]`

**Purpose:** Yields test items for all test methods defined in the wrapped unittest class.

**Logic:**
1. Imports `TestLoader` from `unittest`.
2. Retrieves the wrapped class via `self.obj`. If the class has `__test__ = False`, returns immediately (yields nothing).
3. Checks whether the class itself is marked with `@unittest.skip` via `_is_skipped(self)`.
4. If not skipped: calls `self._inject_setup_teardown_fixtures(cls)` and `self._inject_setup_class_fixture()`.
5. Registers the class's fixtures with the session's fixture manager via `self.session._fixturemanager.parsefactories(self, unittest=True)`.
6. Creates a `TestLoader()` instance. Iterates over names returned by `loader.getTestCaseNames(self.obj)`:
   - For each name, retrieves the attribute `x = getattr(self.obj, name)`. If `x.__test__` is `False`, skips it.
   - Extracts the underlying function via `getimfunc(x)`.
   - Yields a `TestCaseFunction.from_parent(self, name=name, callobj=funcobj)` for each valid test method. Sets `foundsomething = True`.
7. If no test methods were found (`not foundsomething`): checks whether the class has a `runTest` attribute. If it does and either Twisted is not loaded or `runTest` differs from `twisted.trial.unittest.TestCase.runTest`, yields a single `TestCaseFunction.from_parent(self, name="runTest")`.

#### Method: `_inject_setup_teardown_fixtures(cls: type) -> None`

**Purpose:** Injects hidden auto-use fixtures to invoke the unittest xUnit-style setup/teardown lifecycle hooks (`setUpClass`/`tearDownClass`, `setup_method`/`teardown_method`) and class cleanups.

**Logic:**
1. Calls `_make_xunit_fixture(cls, "setUpClass", "tearDownClass", "doClassCleanups", scope="class", pass_self=False)`. If the returned fixture is not `None`, assigns it to `cls.__pytest_class_setup` as an attribute.
2. Calls `_make_xunit_fixture(cls, "setup_method", "teardown_method", None, scope="function", pass_self=True)`. If the returned fixture is not `None`, assigns it to `cls.__pytest_method_setup` as an attribute.

---

### Function: `_make_xunit_fixture(obj: type, setup_name: str, teardown_name: str, cleanup_name: Optional[str], scope: "_Scope", pass_self: bool) -> Optional[Callable]`

**Purpose:** Creates a pytest fixture that wraps the given unittest xUnit-style setup/teardown/cleanup methods. Returns `None` if neither setup nor teardown exists on `obj`.

**Logic:**
1. Retrieves `setup = getattr(obj, setup_name, None)` and `teardown = getattr(obj, teardown_name, None)`. If both are `None`, returns `None`.
2. Determines the cleanup function: if `cleanup_name` is provided, retrieves it via `getattr(obj, cleanup_name, lambda *args: None)`; otherwise defines a no-op `def cleanup(*args): pass`.
3. Defines and decorates with `@pytest.fixture(scope=scope, autouse=True, name=f"unittest_{setup_name}_fixture_{obj.__qualname__}")` an inner function `fixture(self, request: FixtureRequest) -> Generator[None, None, None]`:
   - If the test case (`self`) is skipped (checked via `_is_skipped(self)`), raises a `pytest.skip.Exception(reason, _use_item_location=True)` where `reason = self.__unittest_skip_why__`.
   - If `setup` exists: calls it — if `pass_self`, invokes `setup(self, request.function)`; otherwise `setup()`. On any exception raised by setup, calls cleanup (with or without `self` depending on `pass_self`) and re-raises.
   - Yields (the test runs here).
   - In a `finally` block: if `teardown` exists, calls it (same `pass_self` logic as above). Then always calls cleanup (with or without `self`).
4. Returns the decorated `fixture` function.

---

### Class: `TestCaseFunction(Function)`

**Inheritance:** Extends `_pytest.python.Function`.

**Class attributes:**
- `nofuncargs = True` — marker that this item does not support funcargs.
- `_excinfo: Optional[List[_pytest._code.ExceptionInfo[BaseException]]] = None` — list of collected exception info objects, populated during test execution via the `TestResult` protocol methods.
- `_testcase: Optional["unittest.TestCase"] = None` — reference to the instantiated unittest `TestCase` object for this test method.

#### Method: `setup(self) -> None`

**Purpose:** Initializes the test case instance and fills fixtures before each test runs.

**Logic:**
1. Sets `self._explicit_tearDown = None`.
2. Asserts `self.parent is not None`.
3. Instantiates the unittest test case: `self._testcase = self.parent.obj(self.name)` (i.e., calls the class with the method name as argument, per `unittest.TestCase` convention).
4. Binds the actual test method: `self._obj = getattr(self._testcase, self.name)`.
5. If `hasattr(self, "_request")`, calls `self._request._fillfixtures()`.

#### Method: `teardown(self) -> None`

**Purpose:** Cleans up after a test completes.

**Logic:**
1. If `self._explicit_tearDown is not None`, calls it and sets it to `None`. (This is used when `--pdb` is active to defer tearDown.)
2. Sets `self._testcase = None` and `self._obj = None`.

#### Method: `startTest(self, testcase: "unittest.TestCase") -> None`

**Purpose:** No-op stub implementing the `TextTestResult.startTest` protocol method. Called by the unittest framework before running a test.

#### Method: `_addexcinfo(rawexcinfo: "_SysExcInfoType") -> None`

**Purpose:** Converts a raw exception info tuple into a pytest `ExceptionInfo` object and appends it to `self._excinfo`. Handles both normal and Twisted-trial incompatible exception representations.

**Logic:**
1. Unwraps the input: if `rawexcinfo` has an attribute `_rawexcinfo`, uses that instead (Twisted trial support).
2. Attempts to create a pytest `_pytest._code.ExceptionInfo(rawexcinfo)`. Invokes `.value` and `.traceback` attributes on it to trigger traceback storage (needed because Twisted causes issues there). Appends the `ExceptionInfo` to `self.__dict__["_excinfo"]` via `setdefault`, which initializes the list if needed.
3. If a `TypeError` occurs during step 2: attempts to format the exception natively using `traceback.format_exception(*rawexcinfo)`. Prepends `"NOTE: Incompatible Exception Representation, displaying natively:\n\n"` and calls `fail("".join(values), pytrace=False)`. Catches `fail.Exception` and `KeyboardInterrupt` to re-raise them; catches any other `BaseException` and calls `fail("ERROR: Unknown Incompatible Exception representation:\n%r" % rawexcinfo, pytrace=False)`.
4. If the inner `fail()` call raised a `fail.Exception`, creates an `ExceptionInfo.from_current()` and appends it to `_excinfo`.

#### Method: `addError(self, testcase: "unittest.TestCase", rawexcinfo: "_SysExcInfoType") -> None`

**Purpose:** Implements the `TestResult.addError` protocol. Called when a test raises an error (non-failure exception).

**Logic:**
1. Attempts to check if the exception value is `exit.Exception`. If so, calls `exit(rawexcinfo[1].msg)` which terminates pytest. Catches `TypeError` and silently passes (the value may not be indexable or comparable).
2. Calls `self._addexcinfo(rawexcinfo)`.

#### Method: `addFailure(self, testcase: "unittest.TestCase", rawexcinfo: "_SysExcInfoType") -> None`

**Purpose:** Implements the `TestResult.addFailure` protocol. Called when a test assertion fails (e.g., `assertRaises`, `assertTrue`).

**Logic:** Calls `self._addexcinfo(rawexcinfo)`.

#### Method: `addSkip(self, testcase: "unittest.TestCase", reason: str) -> None`

**Purpose:** Implements the `TestResult.addSkip` protocol. Called when a test is skipped (e.g., via `@unittest.skipIf`).

**Logic:**
1. Raises `pytest.skip.Exception(reason, _use_item_location=True)`. Catches the resulting `skip.Exception`.
2. Calls `_addexcinfo(sys.exc_info())` to record it.

#### Method: `addExpectedFailure(self, testcase: "unittest.TestCase", rawexcinfo: "_SysExcInfoType", reason: str = "") -> None`

**Purpose:** Implements the `TestResult.addExpectedFailure` protocol. Called when a test marked with `@unittest.expectedFailure` fails as expected.

**Logic:**
1. Calls `xfail(str(reason))`. Catches the resulting `xfail.Exception`.
2. Calls `_addexcinfo(sys.exc_info())` to record it.

#### Method: `addUnexpectedSuccess(self, testcase: "unittest.TestCase", reason: Optional["twisted.trial.unittest.Todo"] = None) -> None`

**Purpose:** Implements the `TestResult.addUnexpectedSuccess` protocol (Twisted trial). Called when a test marked as expected to fail (`@todo`) unexpectedly succeeds.

**Logic:**
1. Constructs message `"Unexpected success"` or `"Unexpected success: {reason.reason}"` if a `Todo` reason is provided.
2. Calls `fail(msg, pytrace=False)`. Catches the resulting `fail.Exception`.
3. Calls `_addexcinfo(sys.exc_info())` to record it.

#### Method: `addSuccess(self, testcase: "unittest.TestCase") -> None`

**Purpose:** No-op stub implementing the `TestResult.addSuccess` protocol. Called when a test passes.

#### Method: `stopTest(self, testcase: "unittest.TestCase") -> None`

**Purpose:** No-op stub implementing the `TextTestResult.stopTest` protocol. Called by the unittest framework after running a test.

#### Method: `runtest(self) -> None`

**Purpose:** Executes the actual unittest test method, using the unittest framework's own execution machinery with this object as the result sink.

**Logic:**
1. Imports `maybe_wrap_pytest_function_for_tracing` from `_pytest.debugging`. Asserts `self._testcase is not None`.
2. Calls `maybe_wrap_pytest_function_for_tracing(self)` (enables debugging/tracing).
3. If the test method is async (`is_async_function(self.obj)`): calls `self._testcase(result=self)`, letting unittest handle async execution internally, passing `self` as the result object.
4. Otherwise (sync case):
   - If `--pdb` option is enabled (`self.config.getoption("usepdb")`) and the test is not skipped: saves a reference to `self._testcase.tearDown` in `self._explicit_tearDown`, then replaces `self._testcase.tearDown` with a no-op lambda. This defers tearDown until after the pdb session so instance variables remain inspectable.
   - Updates the bound method on the test case: `setattr(self._testcase, self.name, self.obj)` — this is necessary because `maybe_wrap_pytest_function_for_tracing` may have replaced `self.obj` with a wrapper.
   - Calls `self._testcase(result=self)`, passing `self` as the result object so that unittest calls back into the protocol methods (`addError`, `addFailure`, etc.).
   - In a `finally` block: removes the attribute via `delattr(self._testcase, self.name)`.

#### Method: `_prunetraceback(self, excinfo: _pytest._code.ExceptionInfo[BaseException]) -> None`

**Purpose:** Prunes unittest internal frames from traceback output.

**Logic:**
1. Calls `Function._prunetraceback(self, excinfo)` (the parent class's pruning logic).
2. Filters the traceback to remove any frame whose globals contain `"__unittest"` as a key: `excinfo.traceback.filter(lambda x: not x.frame.f_globals.get("__unittest"))`.
3. If any frames remain after filtering, assigns the filtered list back to `excinfo.traceback`.

---

### Function: `pytest_runtest_makereport(item: Item, call: CallInfo[None]) -> None`

**Purpose:** pytest hook implementation (`tryfirst=True`) that converts unittest-style test results into pytest test reports. Runs before other makereport hooks.

**Logic:**
1. If `item` is a `TestCaseFunction`:
   - If `item._excinfo` has entries, pops the first one and assigns it to `call.excinfo`.
   - Attempts to delete `call.result` (catches `AttributeError` if not present). This ensures the unittest exception info replaces any default result.
2. Separately, handles conversion of `unittest.SkipTest` exceptions to pytest skip:
   - Retrieves the `unittest` module from `sys.modules`. If it exists and `call.excinfo` is set and its value is an instance of `unittest.SkipTest`:
     - Captures the original excinfo. Creates a new `CallInfo[None]` via `from_call(lambda: pytest.skip(str(excinfo.value)), call.when)`. Replaces `call.excinfo` with the new call's excinfo (a proper pytest skip exception).

---

### Function: `pytest_runtest_protocol(item: Item) -> Generator[None, None, None]`

**Purpose:** pytest hook implementation (`hookwrapper=True`) providing Twisted trial support by monkey-patching `twisted.python.failure.Failure.__init__` to capture raw exception info.

**Logic:**
1. If `item` is a `TestCaseFunction` AND `"twisted.trial.unittest"` is in `sys.modules`:
   - Imports `Failure` from `twisted.python.failure`. Saves the original `Failure.__init__` as `Failure__init__`.
   - Calls `check_testcase_implements_trial_reporter()` to register Twisted trial reporter interface.
   - Defines an inner function `excstore(self, exc_value=None, exc_type=None, exc_tb=None, captureVars=None)` that:
     - Stores the raw exception info on `self._rawexcinfo` — either from `sys.exc_info()` if no arguments given, or constructed as `(exc_type, exc_value, exc_tb)`.
     - Calls the original `Failure__init__`, trying with all four arguments first; catching `TypeError` and retrying without `captureVars`.
   - Replaces `ut.Failure.__init__` with `excstore`.
   - Yields (runs the rest of the protocol).
   - Restores `ut.Failure.__init__ = Failure__init__`.
2. Otherwise: simply yields without modification.

---

### Function: `check_testcase_implements_trial_reporter(done: List[int] = []) -> None`

**Purpose:** One-time registration that declares `TestCaseFunction` implements Twisted's `IReporter` interface, enabling Twisted trial integration. Uses a mutable default list as a guard to run only once per process.

**Logic:**
1. If `done` is non-empty (truthy), returns immediately.
2. Imports `classImplements` from `zope.interface` and `IReporter` from `twisted.trial.itrial`.
3. Calls `classImplements(TestCaseFunction, IReporter)`.
4. Appends `1` to `done` to mark completion.

---

### Function: `_is_skipped(obj) -> bool`

**Purpose:** Utility that checks whether a given object (a unittest test case class or instance) has been decorated with `@unittest.skip`.

**Logic:** Returns `bool(getattr(obj, "__unittest_skip__", False))`. The attribute is set by the `@unittest.skip` decorator family.