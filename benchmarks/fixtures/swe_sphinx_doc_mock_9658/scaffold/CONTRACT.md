# Implementation target
Write the module at `sphinx/ext/autodoc/mock.py`.

## `sphinx/ext/autodoc/mock.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `MockFinder`
- `MockLoader`
- `ismock`
- `logger`
- `mock`
- `undecorate`

Implement them to satisfy the specification. Do not write tests.
