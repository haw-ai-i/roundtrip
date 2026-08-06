# Implementation target
Write the following 3 modules. They live in the same package and may import each other.

## `django/contrib/sessions/middleware.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `SessionMiddleware`

## `django/middleware/cache.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CacheMiddleware`
- `FetchFromCacheMiddleware`
- `UpdateCacheMiddleware`

## `django/middleware/security.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `SecurityMiddleware`

Implement them to satisfy the specification. Do not write tests.
