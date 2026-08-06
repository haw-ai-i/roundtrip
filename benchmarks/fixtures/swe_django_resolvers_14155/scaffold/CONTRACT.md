# Implementation target
Write the module at `django/urls/resolvers.py`.

## `django/urls/resolvers.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CheckURLMixin`
- `LocalePrefixPattern`
- `LocaleRegexDescriptor`
- `RegexPattern`
- `ResolverMatch`
- `RoutePattern`
- `URLPattern`
- `URLResolver`
- `get_ns_resolver`
- `get_resolver`

Implement them to satisfy the specification. Do not write tests.
