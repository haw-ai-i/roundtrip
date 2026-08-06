# Implementation target
Write the following 3 modules. They live in the same package and may import each other.

## `sphinx/directives/other.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Acks`
- `Author`
- `Centered`
- `HList`
- `Include`
- `Only`
- `SeeAlso`
- `TabularColumns`
- `TocTree`
- `glob_re`
- `int_or_nothing`
- `logger`
- `setup`

## `sphinx/environment/adapters/toctree.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `TocTree`
- `logger`

## `sphinx/environment/collectors/toctree.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `N`
- `TocTreeCollector`
- `logger`
- `setup`

Implement them to satisfy the specification. Do not write tests.
