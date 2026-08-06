# Implementation target
Write the module at `django/utils/http.py`.

## `django/utils/http.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ASCTIME_DATE`
- `ETAG_MATCH`
- `FIELDS_MATCH`
- `MONTHS`
- `RFC1123_DATE`
- `RFC3986_GENDELIMS`
- `RFC3986_SUBDELIMS`
- `RFC850_DATE`
- `base36_to_int`
- `escape_leading_slashes`
- `http_date`
- `int_to_base36`
- `is_safe_url`
- `is_same_domain`
- `limited_parse_qsl`
- `parse_etags`
- `parse_http_date`
- `parse_http_date_safe`
- `quote_etag`
- `url_has_allowed_host_and_scheme`
- `urlencode`
- `urlquote`
- `urlquote_plus`
- `urlsafe_base64_decode`
- `urlsafe_base64_encode`
- `urlunquote`
- `urlunquote_plus`

Implement them to satisfy the specification. Do not write tests.
