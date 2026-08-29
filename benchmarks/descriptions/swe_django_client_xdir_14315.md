## django/db/backends/base/client.py
Here is the complete natural-language specification of `django/db/backends/base/client.py`:

---

## Module-Level Preamble

### Imports
- `import os`
- `import subprocess`

### Constants & Globals
None beyond class-level attributes defined below.

---

## Code Objects

### Class: `BaseDatabaseClient`

**Docstring:** *"Encapsulate backend-specific methods for opening a client shell."*

#### Class-Level Attributes
| Name | Type / Value | Description |
|------|-------------|-------------|
| `executable_name` | `None` (intended to be overridden by subclasses as a `str`) | A string representing the name of the database client executable (e.g., `"psql"`). Subclasses **must** override this with an appropriate value. |

#### Method: `__init__(self, connection)`
- **Parameters:**
  - `connection` — An instance of `BaseDatabaseWrapper`.
- **Logic:** Stores the passed `connection` object as the instance attribute `self.connection`.
- **Return:** None (implicit constructor).

#### Class Method: `settings_to_cmd_args_env(cls, settings_dict, parameters)`
- **Parameters:**
  - `cls` — The class itself (standard classmethod receiver).
  - `settings_dict` — A dictionary containing database connection settings. Its exact shape is backend-specific but originates from Django's `DATABASES` configuration.
  - `parameters` — An optional list of additional shell parameters/arguments to pass through.
- **Logic:** Raises an exception unconditionally. This method exists as a contract hook: subclasses must either override this classmethod or override `runshell()` directly.
- **Return:** Never returns; always raises `NotImplementedError`.
- **Exception raised:** `NotImplementedError` with the message: *'subclasses of BaseDatabaseClient must provide a settings_to_cmd_args_env() method or override a runshell().'*

#### Method: `runshell(self, parameters)`
- **Parameters:**
  - `self` — The instance.
  - `parameters` — An optional list of additional shell parameters/arguments to pass through (type and structure are backend-specific).
- **Logic:**
  1. Calls the class method `self.settings_to_cmd_args_env(self.connection.settings_dict, parameters)` to obtain a tuple `(args, env)`, where:
     - `args` is a list of command-line arguments representing the database client executable and its flags/parameters.
     - `env` is either `None` or a dictionary of additional environment variables to set for the subprocess.
  2. If `env` is truthy (non-`None`, non-empty), merges it with the current process environment: `{**os.environ, **env}` — meaning values in `env` override any existing keys in `os.environ`.
  3. Invokes `subprocess.run(args, env=env, check=True)`:
     - Runs the command described by `args` as a subprocess.
     - Passes the merged environment dictionary (or `None` if no extra env vars were provided).
     - `check=True` causes `subprocess.CalledProcessError` to be raised if the subprocess exits with a non-zero return code.
- **Return:** The `subprocess.CompletedProcess` result returned by `subprocess.run`.
- **Exception raised:** `subprocess.CalledProcessError` if the database client process exits with a non-zero status (due to `check=True`).

---

## django/db/backends/postgresql/client.py
I have the full source of `client.py`. The base class `BaseDatabaseClient` is not installed locally, but it's referenced by name in the import and its `runshell` method is called via `super()`. Here is the complete natural-language specification:

---

## Module-Level Preamble

### Imports
- `import signal` — standard library; used for SIGINT handler management.
- `from django.db.backends.base.client import BaseDatabaseClient` — Django base class providing the foundational `runshell` implementation (subprocess-based shell launcher).

### Constants & Globals
None at module level beyond imports and the class definition below.

---

## Code Objects

### Class: `DatabaseClient(BaseDatabaseClient)`

**Inheritance:** Extends `BaseDatabaseClient`.

**Class Attribute:**
- `executable_name = 'psql'` — string literal; the name of the PostgreSQL command-line client executable to spawn.

#### Class Method: `settings_to_cmd_args_env(cls, settings_dict, parameters)`

**Signature:** `(cls, settings_dict: dict, parameters: list[str]) -> tuple[list[str], dict[str, str]]`

**Parameters:**
- `settings_dict` — a dictionary representing Django's database connection configuration (typically from `DATABASES` in `settings.py`). Expected keys: `'HOST'`, `'PORT'`, `'NAME'`, `'USER'`, `'PASSWORD'`, and optionally `'OPTIONS'`.
- `parameters` — an optional list of extra command-line arguments to pass through to the `psql` executable.

**Implementation Logic:**
1. Initialize `args` as a list starting with `[cls.executable_name]` (i.e., `['psql']`).
2. Extract `options = settings_dict.get('OPTIONS', {})`.
3. Extract connection values from `settings_dict`:
   - `host = settings_dict.get('HOST')` — may be `None`.
   - `port = settings_dict.get('PORT')` — may be `None`.
   - `dbname = settings_dict.get('NAME')` — may be `None`.
   - `user = settings_dict.get('USER')` — may be `None`.
   - `passwd = settings_dict.get('PASSWORD')` — may be `None`.
4. Extract optional connection values from `options`:
   - `passfile = options.get('passfile')` — may be `None`.
   - `service = options.get('service')` — may be `None`.
   - `sslmode = options.get('sslmode')` — may be `None`.
   - `sslrootcert = options.get('sslrootcert')` — may be `None`.
   - `sslcert = options.get('sslcert')` — may be `None`.
   - `sslkey = options.get('sslkey')` — may be `None`.
5. **Default database fallback:** If both `dbname` and `service` are falsy, set `dbname = 'postgres'` to connect to the default PostgreSQL administrative database.
6. **Build command-line args (appended in order):**
   - If `user` is truthy: append `['-U', user]`.
   - If `host` is truthy: append `['-h', host]`.
   - If `port` is truthy: append `['-p', str(port)]` (port is stringified).
   - If `dbname` is truthy: append `[dbname]`.
7. Append all items from `parameters` to `args` via `args.extend(parameters)`.
8. **Build environment dictionary:** Initialize `env = {}`, then conditionally populate it:
   - If `passwd` is truthy: set `env['PGPASSWORD'] = str(passwd)`.
   - If `service` is truthy: set `env['PGSERVICE'] = str(service)`.
   - If `sslmode` is truthy: set `env['PGSSLMODE'] = str(sslmode)`.
   - If `sslrootcert` is truthy: set `env['PGSSLROOTCERT'] = str(sslrootcert)`.
   - If `sslcert` is truthy: set `env['PGSSLCERT'] = str(sslcert)`.
   - If `sslkey` is truthy: set `env['PGSSLKEY'] = str(sslkey)`.
   - If `passfile` is truthy: set `env['PGPASSFILE'] = str(passfile)`.
9. **Return:** `(args, env)` — a tuple of the constructed argument list and environment variable dictionary.

**Return Value:** A 2-tuple `(list[str], dict[str, str])` containing the full command-line arguments for invoking `psql` and the environment variables to pass to the subprocess.

#### Instance Method: `runshell(self, parameters)`

**Signature:** `(self, parameters: list[str] | None = None) -> None`

**Parameters:**
- `parameters` — optional list of extra command-line arguments forwarded to `psql`.

**Implementation Logic:**
1. Capture the current SIGINT handler via `sigint_handler = signal.getsignal(signal.SIGINT)`.
2. Enter a `try/finally` block:
   - **In the `try` body:**
     1. Override the SIGINT handler to `signal.SIG_IGN` (ignore), so that pressing Ctrl+C does not terminate Django itself — instead, it passes through to `psql`, allowing interactive query abortion within the shell session.
     2. Call `super().runshell(parameters)`, which invokes the base class's subprocess-spawning logic using the command-line arguments and environment derived from Django settings (the base class internally calls `settings_to_cmd_args_env` or equivalent).
   - **In the `finally` block:**
     1. Restore the original SIGINT handler via `signal.signal(signal.SIGINT, sigint_handler)`, ensuring Django's signal handling is not permanently altered after the shell session exits (whether normally or due to an exception).

**Return Value:** None (blocks until the `psql` subprocess terminates).

**Exception Behavior:** Any exception raised by `super().runshell(parameters)` propagates outward, but the `finally` clause guarantees the SIGINT handler is always restored regardless.

---