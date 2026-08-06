# Implementation target
Write the following 3 modules. They live in the same package and may import each other.

## `django/contrib/messages/storage/cookie.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CookieStorage`
- `MessageDecoder`
- `MessageEncoder`

## `django/contrib/sessions/middleware.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `SessionMiddleware`

## `django/http/response.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `BadHeaderError`
- `FileResponse`
- `Http404`
- `HttpResponse`
- `HttpResponseBadRequest`
- `HttpResponseBase`
- `HttpResponseForbidden`
- `HttpResponseGone`
- `HttpResponseNotAllowed`
- `HttpResponseNotFound`
- `HttpResponseNotModified`
- `HttpResponsePermanentRedirect`
- `HttpResponseRedirect`
- `HttpResponseRedirectBase`
- `HttpResponseServerError`
- `JsonResponse`
- `StreamingHttpResponse`

Implement them to satisfy the specification. Do not write tests.
