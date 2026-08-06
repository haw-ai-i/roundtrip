# Implementation target
Write the module at `sphinx/ext/viewcode.py`.

## `sphinx/ext/viewcode.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `OUTPUT_DIRNAME`
- `collect_pages`
- `doctree_read`
- `env_merge_info`
- `get_module_filename`
- `logger`
- `missing_reference`
- `setup`
- `should_generate_module_page`

Implement them to satisfy the specification. Do not write tests.
