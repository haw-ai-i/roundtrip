# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `sphinx/application.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ENV_PICKLE_FILENAME`
- `Sphinx`
- `TemplateBridge`
- `builtin_extensions`
- `logger`

## `sphinx/locale/__init__.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `admonitionlabels`
- `get_translation`
- `get_translator`
- `init`
- `init_console`
- `is_translator_registered`
- `pairindextypes`
- `setlocale`
- `translators`
- `versionlabels`

Implement them to satisfy the specification. Do not write tests.
