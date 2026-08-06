# Implementation target
Write the module at `django/utils/html.py`.

## `django/utils/html.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DOTS`
- `MLStripper`
- `TRAILING_PUNCTUATION_CHARS`
- `WRAPPING_PUNCTUATION`
- `avoid_wrapping`
- `conditional_escape`
- `escape`
- `escapejs`
- `format_html`
- `format_html_join`
- `html_safe`
- `json_script`
- `linebreaks`
- `simple_url_2_re`
- `simple_url_re`
- `smart_urlquote`
- `strip_spaces_between_tags`
- `strip_tags`
- `urlize`
- `word_split_re`

Implement them to satisfy the specification. Do not write tests.
