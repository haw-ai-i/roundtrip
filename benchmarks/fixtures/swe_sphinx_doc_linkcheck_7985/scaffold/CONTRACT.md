# Implementation target
Write the module at `sphinx/builders/linkcheck.py`.

## `sphinx/builders/linkcheck.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AnchorCheckParser`
- `CheckExternalLinksBuilder`
- `DEFAULT_REQUEST_HEADERS`
- `check_anchor`
- `logger`
- `setup`
- `uri_re`

Implement them to satisfy the specification. Do not write tests.
