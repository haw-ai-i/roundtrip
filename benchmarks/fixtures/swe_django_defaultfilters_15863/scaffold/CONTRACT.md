# Implementation target
Write the module at `django/template/defaultfilters.py`.

## `django/template/defaultfilters.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `add`
- `addslashes`
- `capfirst`
- `center`
- `cut`
- `date`
- `default`
- `default_if_none`
- `dictsort`
- `dictsortreversed`
- `divisibleby`
- `escape_filter`
- `escapejs_filter`
- `filesizeformat`
- `first`
- `floatformat`
- `force_escape`
- `get_digit`
- `iriencode`
- `join`
- `json_script`
- `last`
- `length`
- `length_is`
- `linebreaks_filter`
- `linebreaksbr`
- `linenumbers`
- `ljust`
- `lower`
- `make_list`
- `phone2numeric_filter`
- `pluralize`
- `pprint`
- `random`
- `register`
- `rjust`
- `safe`
- `safeseq`
- `slice_filter`
- `slugify`
- `stringfilter`
- `stringformat`
- `striptags`
- `time`
- `timesince_filter`
- `timeuntil_filter`
- `title`
- `truncatechars`
- `truncatechars_html`
- `truncatewords`
- `truncatewords_html`
- `unordered_list`
- `upper`
- `urlencode`
- `urlize`
- `urlizetrunc`
- `wordcount`
- `wordwrap`
- `yesno`

Implement them to satisfy the specification. Do not write tests.
