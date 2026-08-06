# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `django/urls/base.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `clear_script_prefix`
- `clear_url_caches`
- `get_script_prefix`
- `get_urlconf`
- `is_valid_path`
- `resolve`
- `reverse`
- `reverse_lazy`
- `set_script_prefix`
- `set_urlconf`
- `translate_url`

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
