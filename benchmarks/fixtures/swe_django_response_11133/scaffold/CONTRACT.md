# Implementation target
Write the module at `django/http/response.py`.

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
