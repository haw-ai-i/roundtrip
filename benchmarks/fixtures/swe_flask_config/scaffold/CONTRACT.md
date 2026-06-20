# Implementation target

Write the module at `src/flask/config.py`.

It is imported by the framework as `flask.config`, and the framework and its
tests import these public names directly, so they MUST exist with these names:

- `class Config(dict)`
- `class ConfigAttribute`

Implement them to satisfy the specification. Do not write tests.
