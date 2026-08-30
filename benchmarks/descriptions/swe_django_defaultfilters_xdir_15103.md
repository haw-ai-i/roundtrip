## django/template/defaultfilters.py
Here is the complete natural-language specification of `django/template/defaultfilters.py`:

---

## Module-Level Preamble

### Imports

```python
import random as random_module
import re
import types
from decimal import ROUND_HALF_UP, Context, Decimal, InvalidOperation, getcontext
from functools import wraps
from inspect import unwrap
from operator import itemgetter
from pprint import pformat
from urllib.parse import quote

from django.utils import formats
from django.utils.dateformat import format as date_format_func, time_format as time_format_func
from django.utils.encoding import iri_to_uri
from django.utils.html import avoid_wrapping, conditional_escape, escape, escapejs
from django.utils.html import json_script as _json_script
from django.utils.html import linebreaks, strip_tags
from django.utils.html import urlize as _urlize
from django.utils.safestring import SafeData, mark_safe
from django.utils.text import Truncator, normalize_newlines, phone2numeric
from django.utils.text import slugify as _slugify
from django.utils.text import wrap
from django.utils.timesince import timesince, timeuntil
from django.utils.translation import gettext, ngettext

from .base import VARIABLE_ATTRIBUTE_SEPARATOR
from .library import Library
```

### Constants & Globals

- **`register`**: An instance of `Library()` — the Django template filter registry to which all filters are attached via `@register.filter(...)`.

---

## Code Objects

### Function: `stringfilter(func)`

A decorator factory for filters that must receive only strings. Returns a wrapper `_dec(first, *args, **kwargs)`:
1. Converts `first` to `str(first)`.
2. Calls the original decorated function with the stringified first argument and remaining args/kwargs.
3. If the original `first` was an instance of `SafeData` **and** the unwrapped original function has attribute `is_safe == True`, wraps the result in `mark_safe(result)`.
4. Returns the (possibly re-marked-safe) result.

---

### Filter: `addslashes(value)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Converts `value` to string, then returns it with backslashes, double quotes, and single quotes escaped by prefixing each with a backslash: `"\\", '\\", "\\'"` in that order.

### Filter: `capfirst(value)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns the first character uppercased plus the rest of the string, but only if the value is truthy (non-empty). If falsy, returns an empty/falsy result.

### Filter: `escapejs_filter(value)` *(registered as `"escapejs"`)*

- Decorators: `@register.filter("escapejs")`, `@stringfilter`
- Returns `escapejs(value)`, hex-encoding characters for safe use in JavaScript strings.

### Filter: `json_script(value, element_id=None)`

- Decorators: `@register.filter(is_safe=True)`
- Calls `_json_script(value, element_id)` and returns the result — a JSON-encoded value wrapped in a `<script type="application/json">` tag with an optional id attribute.

### Filter: `floatformat(text, arg=-1)`

- Decorators: `@register.filter(is_safe=True)`
- Formats a floating-point number to a specified decimal place count.
- **Argument parsing:** If `arg` is a string, checks for suffixes: `"gu"` or `"ug"` → force grouping + no localization; `"g"` → force grouping only; `"u"` → no localization only. Strips the suffix and converts remaining part to int (or `-1` if empty).
- **Conversion:** Attempts `Decimal(str(text))`. If that fails, tries `Decimal(str(float(text)))`. On any failure (`ValueError`, `InvalidOperation`, `TypeError`), returns `""`.
- Converts `arg` to int; on `ValueError`, returns the original string input.
- Computes `number_of_digits_and_exponent_sum = len(digits) + abs(exponent)` from the Decimal tuple. If this exceeds 200, returns the raw input (DoS protection).
- Computes `m = int(d) - d` to check for fractional part; on failure, returns input.
- **No-fraction path:** If `m == 0` and `p <= 0`, formats as an integer via `formats.number_format("%d" % int(d), 0, ...)` and marks safe.
- **Fractional path:** Quantizes the Decimal to `abs(p)` places using `ROUND_HALF_UP` with sufficient precision context. Reconstructs the number string from the tuple (sign, digits, exponent) by inserting a decimal point at the correct position, padding with zeros if needed, then prepending `-` for negative values.
- Returns the formatted number via `formats.number_format(number, abs(p), ...)` wrapped in `mark_safe`.

### Filter: `iriencode(value)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `iri_to_uri(value)`, escaping an IRI for URL use.

### Filter: `linenumbers(value, autoescape=True)`

- Decorators: `@register.filter(is_safe=True, needs_autoescape=True)`, `@stringfilter`
- Splits value by `"\n"`. Computes zero-padding width from the number of lines. Iterates over lines: if `autoescape` is False or value is already `SafeData`, prefixes each line with its 1-based index (zero-padded); otherwise escapes each line before prefixing. Joins with newlines and returns via `mark_safe`.

### Filter: `lower(value)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `value.lower()`.

### Filter: `make_list(value)`

- Decorators: `@register.filter(is_safe=False)`, `@stringfilter`
- Returns `list(value)` — a list of characters for strings, or digits for integers.

### Filter: `slugify(value)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `_slugify(value)` — converts to ASCII, spaces to hyphens, removes non-alphanumeric/underscore/hyphen characters, lowercases, strips whitespace.

### Filter: `stringformat(value, arg)`

- Decorators: `@register.filter(is_safe=True)`
- If value is a tuple, converts it to string first. Attempts `("%" + str(arg)) % value`. On `ValueError` or `TypeError`, returns `""`.

### Filter: `title(value)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Applies `.title()` then runs two regex substitutions: (1) `"([a-z])'([A-Z])"` → lowercases the matched group to handle contractions like "O'Connor"; (2) `r"\d([A-Z])"` → lowercases letters immediately following digits.

### Filter: `truncatechars(value, arg)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Parses `arg` as int; on failure returns original value. Returns `Truncator(value).chars(length)`.

### Filter: `truncatechars_html(value, arg)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Same as `truncatechars` but calls `Truncator(value).chars(length, html=True)` to preserve HTML.

### Filter: `truncatewords(value, arg)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Parses `arg` as int; on failure returns original value. Returns `Truncator(value).words(length, truncate=" …")`.

### Filter: `truncatewords_html(value, arg)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Same as `truncatewords` but calls `Truncator(value).words(length, html=True, truncate=" …")`.

### Filter: `upper(value)`

- Decorators: `@register.filter(is_safe=False)`, `@stringfilter`
- Returns `value.upper()`.

### Filter: `urlencode(value, safe=None)`

- Decorators: `@register.filter(is_safe=False)`, `@stringfilter`
- Builds kwargs dict with `"safe": safe` if `safe is not None`. Returns `quote(value, **kwargs)`.

### Filter: `urlize(value, autoescape=True)`

- Decorators: `@register.filter(is_safe=True, needs_autoescape=True)`, `@stringfilter`
- Returns `mark_safe(_urlize(value, nofollow=True, autoescape=autoescape))`.

### Filter: `urlizetrunc(value, limit, autoescape=True)`

- Decorators: `@register.filter(is_safe=True, needs_autoescape=True)`, `@stringfilter`
- Returns `mark_safe(_urlize(value, trim_url_limit=int(limit), nofollow=True, autoescape=autoescape))`.

### Filter: `wordcount(value)`

- Decorators: `@register.filter(is_safe=False)`, `@stringfilter`
- Returns `len(value.split())`.

### Filter: `wordwrap(value, arg)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `wrap(value, int(arg))`.

### Filter: `ljust(value, arg)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `value.ljust(int(arg))`.

### Filter: `rjust(value, arg)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `value.rjust(int(arg))`.

### Filter: `center(value, arg)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `value.center(int(arg))`.

### Filter: `cut(value, arg)`

- Decorators: `@register.filter` (no explicit `is_safe`)
- Checks if value is `SafeData`. Replaces all occurrences of `arg` with `""`. If original was safe and `arg != ";"`, returns `mark_safe(result)`. Otherwise returns the raw result.

---

### Filter: `escape_filter(value)` *(registered as `"escape"`)*

- Decorators: `@register.filter("escape", is_safe=True)`, `@stringfilter`
- Returns `conditional_escape(value)`.

### Filter: `escapeseq(value)`

- Decorators: `@register.filter(is_safe=True)`
- Returns a list comprehension: `[conditional_escape(obj) for obj in value]`.

### Filter: `force_escape(value)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `escape(value)` — HTML-escapes the string (as opposed to marking it safe).

### Filter: `linebreaks_filter(value, autoescape=True)` *(registered as `"linebreaks"`)*

- Decorators: `@register.filter("linebreaks", is_safe=True, needs_autoescape=True)`, `@stringfilter`
- Sets `autoescape = autoescape and not isinstance(value, SafeData)`. Returns `mark_safe(linebreaks(value, autoescape))`.

### Filter: `linebreaksbr(value, autoescape=True)`

- Decorators: `@register.filter(is_safe=True, needs_autoescape=True)`, `@stringfilter`
- Sets `autoescape = autoescape and not isinstance(value, SafeData)`. Normalizes newlines via `normalize_newlines(value)`. If autoescaping is on, escapes the value. Returns `mark_safe(value.replace("\n", "<br>"))`.

### Filter: `safe(value)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `mark_safe(value)`.

### Filter: `safeseq(value)`

- Decorators: `@register.filter(is_safe=True)`
- Returns `[mark_safe(obj) for obj in value]`.

### Filter: `striptags(value)`

- Decorators: `@register.filter(is_safe=True)`, `@stringfilter`
- Returns `strip_tags(value)`.

---

### Function: `_property_resolver(arg)`

A helper that returns a callable to resolve an attribute/item from a value.
1. Attempts `float(arg)`. If it succeeds, returns `itemgetter(arg)` (numeric index resolution).
2. On `ValueError`, checks if arg contains `"__"` or starts with `"_"` — raises `AttributeError("Access to private variables is forbidden.")`.
3. Splits arg by `VARIABLE_ATTRIBUTE_SEPARATOR` (`.`). Returns a closure `resolve(value)`: iterates over parts, trying `value[part]` first (getitem), falling back to `getattr(value, part)` on any exception (`AttributeError`, `IndexError`, `KeyError`, `TypeError`, `ValueError`).

### Filter: `dictsort(value, arg)`

- Decorators: `@register.filter(is_safe=False)`
- Returns `sorted(value, key=_property_resolver(arg))`. On `AttributeError` or `TypeError`, returns `""`.

### Filter: `dictsortreversed(value, arg)`

- Decorators: `@register.filter(is_safe=False)`
- Same as `dictsort` but with `reverse=True`. Returns `""` on error.

### Filter: `first(value)`

- Decorators: `@register.filter(is_safe=False)`
- Returns `value[0]`; on `IndexError`, returns `""`.

### Filter: `join(value, arg, autoescape=True)`

- Decorators: `@register.filter(is_safe=True, needs_autoescape=True)`
- If autoescaping is on, joins with `[conditional_escape(v) for v in value]` using `conditional_escape(arg)` as separator. Otherwise plain `arg.join(value)`. On `TypeError`, returns original value. Returns result via `mark_safe`.

### Filter: `last(value)`

- Decorators: `@register.filter(is_safe=True)`
- Returns `value[-1]`; on `IndexError`, returns `""`.

### Filter: `length(value)`

- Decorators: `@register.filter(is_safe=False)`
- Returns `len(value)`. On `ValueError` or `TypeError`, returns `0`.

### Filter: `random(value)`

- Decorators: `@register.filter(is_safe=True)`
- Returns `random_module.choice(value)`. On `IndexError`, returns `""`.

### Filter: `slice_filter(value, arg)` *(registered as `"slice"`)*

- Decorators: `@register.filter("slice", is_safe=True)`
- Parses the slice argument by splitting on `":"`, converting each part to int (or `None` if empty). Returns `value[slice(*bits)]`. On `ValueError`, `TypeError`, or `KeyError`, returns original value.

### Filter: `unordered_list(value, autoescape=True)`

- Decorators: `@register.filter(is_safe=True, needs_autoescape=True)`
- Recursively converts a self-nested list structure into an HTML unordered list (without outer `<ul>`/`</ul>`).
- Selects escaper function based on `autoescape`: `conditional_escape` or identity.
- **Inner function `walk_items(item_list)`:** An iterator that yields `(item, children)` pairs where `children` is a sub-list/tuple/generator if the next item is iterable, otherwise `None`. Handles nested structures by detecting iterables (excluding non-iterable types via try/except on `iter()`).
- **Inner function `list_formatter(item_list, tabs=1)`:** Recursively builds HTML. For each `(item, children)` pair from `walk_items`, if children exist, wraps them in `<ul>` with proper indentation (`"\t" * tabs`). Each item becomes `<li>escaper(item)<sublist></li>`.
- Returns the result via `mark_safe`.

---

### Filter: `add(value, arg)`

- Decorators: `@register.filter(is_safe=False)`
- Attempts `int(value) + int(arg)`. On failure, tries `value + arg` (fallback for string concatenation). On any exception, returns `""`.

### Filter: `get_digit(value, arg)`

- Decorators: `@register.filter(is_safe=False)`
- Parses both as int; on `ValueError`, returns original value. If `arg < 1`, returns original value. Returns the digit at position `arg` from the right (1-indexed) via `int(str(value)[-arg])`. On `IndexError`, returns `0`.

---

### Filter: `date(value, arg=None)`

- Decorators: `@register.filter(expects_localtime=True, is_safe=False)`
- If value is `None` or `""`, returns `""`. Attempts `formats.date_format(value, arg)`. On `AttributeError`, falls back to `date_format_func(value, arg)`. On any failure, returns `""`.

### Filter: `time(value, arg=None)`

- Decorators: `@register.filter(expects_localtime=True, is_safe=False)`
- If value is `None` or `""`, returns `""`. Attempts `formats.time_format(value, arg)`. On `(AttributeError, TypeError)`, falls back to `time_format_func(value, arg)`. On any failure, returns `""`.

### Filter: `timesince_filter(value, arg=None)` *(registered as `"timesince"`)*

- Decorators: `@register.filter("timesince", is_safe=False)`
- If value is falsy, returns `""`. If `arg` is provided, calls `timesince(value, arg)`, otherwise `timesince(value)`. On `(ValueError, TypeError)`, returns `""`.

### Filter: `timeuntil_filter(value, arg=None)` *(registered as `"timeuntil"`)*

- Decorators: `@register.filter("timeuntil", is_safe=False)`
- If value is falsy, returns `""`. Returns `timeuntil(value, arg)`. On `(ValueError, TypeError)`, returns `""`.

---

### Filter: `default(value, arg)`

- Decorators: `@register.filter(is_safe=False)`
- Returns `value or arg`.

### Filter: `default_if_none(value, arg)`

- Decorators: `@register.filter(is_safe=False)`
- If value is exactly `None`, returns `arg`; otherwise returns `value`.

### Filter: `divisibleby(value, arg)`

- Decorators: `@register.filter(is_safe=False)`
- Returns `int(value) % int(arg) == 0`.

### Filter: `yesno(value, arg=None)`

- Decorators: `@register.filter(is_safe=False)`
- If `arg` is `None`, defaults to `gettext("yes,no,maybe")`. Splits on `,`. If fewer than 2 parts, returns original value. Unpacks into `(yes, no, maybe)`: if only 2 parts exist, sets `maybe = bits[1]` (same as `no`). Returns `maybe` if value is `None`, `yes` if truthy, otherwise `no`.

---

### Filter: `filesizeformat(bytes_)`

- Decorators: `@register.filter(is_safe=True)`
- Converts to int; on `(TypeError, ValueError, UnicodeDecodeError)`, returns localized `"0 byte(s)"` via `avoid_wrapping`.
- Defines inner function `filesize_number_format(value)` → `formats.number_format(round(value, 1), 1)`.
- Thresholds: KB = 2^10, MB = 2^20, GB = 2^30, TB = 2^40, PB = 2^50.
- Tracks negative sign separately (allows formatting of negatives).
- Selects unit based on magnitude range and formats with `ngettext` for bytes (singular/plural) or `gettext` for KB/MB/GB/TB/PB with the formatted number.
- Prepends `"-"` if original was negative. Returns via `avoid_wrapping`.

### Filter: `pluralize(value, arg="s")`

- Decorators: `@register.filter(is_safe=False)`
- Ensures arg contains a comma (prepends `","` if not). Splits on `,`; if more than 2 parts, returns `""`. Extracts `singular_suffix` and `plural_suffix`.
- Attempts `float(value) == 1` to decide singular vs plural. On `ValueError`, tries `len(value) == 1`. On `TypeError` from `len()`, falls through. Returns the chosen suffix or `""` if neither path succeeds.

### Filter: `phone2numeric_filter(value)` *(registered as `"phone2numeric"`)*

- Decorators: `@register.filter("phone2numeric", is_safe=True)`
- Returns `phone2numeric(value)`.

### Filter: `pprint(value)`

- Decorators: `@register.filter(is_safe=True)`
- Returns `pformat(value)`. On any exception, returns `"Error in formatting: %s: %s" % (e.__class__.__name__, e)`.

## django/utils/html.py
Now I have the complete source. Here is the specification:

---

# Module Specification: `django/utils/html.py`

## 1. Module-Level Preamble

### Imports

```python
import html
import json
import re
from html.parser import HTMLParser
from urllib.parse import (
    parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit,
)

from django.utils.encoding import punycode
from django.utils.functional import Promise, keep_lazy, keep_lazy_text
from django.utils.http import RFC3986_GENDELIMS, RFC3986_SUBDELIMS
from django.utils.regex_helper import _lazy_re_compile
from django.utils.safestring import SafeData, SafeString, mark_safe
from django.utils.text import normalize_newlines
```

### Constants & Globals

**`_js_escapes`** — `dict[int, str]`, maps Unicode code points to their `\uXXXX` escape sequences for safe embedding in JavaScript strings. Initial contents:

| Key (code point) | Value |
|---|---|
| `ord('\\')` (`92`) | `'\\u005C'` |
| `ord("'")` (`39`) | `'\\u0027'` |
| `ord('"')` (`34`) | `'\\u0022'` |
| `ord('>')` (`62`) | `'\\u003E'` |
| `ord('<')` (`60`) | `'\\u003C'` |
| `ord('&')` (`38`) | `'\\u0026'` |
| `ord('=')` (`61`) | `'\\u003D'` |
| `ord('-')` (`45`) | `'\\u002D'` |
| `ord(';')` (`59`) | `'\\u003B'` |
| `` ord('`') `` (96) | `'\\u0060'` |
| `ord('\u2028')` | `'\\u2028'` |
| `ord('\u2029')` | `'\\u2029'` |

After initialization, the dict is extended with entries for every ASCII character whose ordinal value is less than 32: `(ord('%c' % z), '\\u%04X' % z)` for each `z` in `range(32)`.

**`_json_script_escapes`** — `dict[int, str]`, maps code points to `\uXXXX` escapes for safe JSON-in-HTML embedding:

| Key | Value |
|---|---|
| `ord('>')` (`62`) | `'\\u003E'` |
| `ord('<')` (`60`) | `'\\u003C'` |
| `ord('&')` (`38`) | `'\\u0026'` |

**`urlizer`** — module-level singleton instance of the `Urlizer` class: `urlizer = Urlizer()`.

---

## 2. Code Objects

### Function: `escape(text)`

- **Decorator:** `@keep_lazy(str, SafeString)` — if `text` is a lazy `Promise`, returns a lazy result wrapping the function call; otherwise executes immediately.
- **Logic:** Converts `text` to its string representation via `str(text)`, then passes it through Python's standard library `html.escape()`. The result is wrapped with `mark_safe()` and returned.
- **Returns:** A `SafeString` containing the HTML-escaped version of the input (ampersands, quotes, angle brackets encoded). Always escapes even if already escaped (may double-escape).

---

### Function: `escapejs(value)`

- **Decorator:** `@keep_lazy(str, SafeString)`.
- **Logic:** Converts `value` to string via `str(value)`, then applies `.translate(_js_escapes)` using the module-level `_js_escapes` mapping. The result is wrapped with `mark_safe()`.
- **Returns:** A `SafeString` where all characters unsafe for JavaScript strings (including control characters < 32, quotes, angle brackets, etc.) are replaced with `\uXXXX` Unicode escape sequences.

---

### Function: `json_script(value, element_id)`

- **No lazy decorator.**
- **Logic:**
  1. Imports `DjangoJSONEncoder` from `django.core.serializers.json`.
  2. Serializes `value` to a JSON string using `json.dumps(value, cls=DjangoJSONEncoder)`, then translates it through `_json_script_escapes` (escaping `<`, `>`, `&`).
  3. Calls `format_html('<script id="{}" type="application/json">{}</script>', element_id, mark_safe(json_str))`.
- **Returns:** A `SafeString` containing a `<script>` tag with the given `element_id`, `type="application/json"`, and the escaped JSON content as its body.

---

### Function: `conditional_escape(text)`

- **No lazy decorator.**
- **Logic:**
  1. If `text` is an instance of `Promise`, converts it to a string via `str(text)`.
  2. Checks if the result has a `__html__` attribute (the Django "safe data" convention).
     - If yes: calls and returns `text.__html__()`.
     - If no: delegates to `escape(text)` and returns its result.
- **Returns:** Either the output of `__html__()` (already safe) or an HTML-escaped string wrapped with `mark_safe()`.

---

### Function: `format_html(format_string, *args, **kwargs)`

- **No lazy decorator.**
- **Logic:**
  1. Applies `conditional_escape` to every positional argument via `map(conditional_escape, args)`, producing `args_safe`.
  2. Applies `conditional_escape` to every keyword argument value, producing `kwargs_safe = {k: conditional_escape(v) for (k, v) in kwargs.items()}`.
  3. Calls `format_string.format(*args_safe, **kwargs_safe)` and wraps the result with `mark_safe()`.
- **Returns:** A `SafeString` — the format string with all arguments safely escaped before interpolation.

---

### Function: `format_html_join(sep, format_string, args_generator)`

- **No lazy decorator.**
- **Parameters:**
  - `sep`: separator string (also passed through `conditional_escape`).
  - `format_string`: a Python `.format()` style template with `{}` placeholders.
  - `args_generator`: an iterator yielding sequences (tuples/lists) of arguments, one per formatted fragment.
- **Logic:**
  1. For each `args` tuple yielded by `args_generator`, calls `format_html(format_string, *args)` to produce a safely escaped fragment.
  2. Joins all fragments with `conditional_escape(sep)`.
  3. Wraps the joined result with `mark_safe()`.
- **Returns:** A `SafeString` — all formatted fragments joined by the escaped separator.

---

### Function: `linebreaks(value, autoescape=False)`

- **Decorator:** `@keep_lazy_text`.
- **Logic:**
  1. Normalizes newlines in `value` via `normalize_newlines(value)`.
  2. Converts to string and splits on two-or-more consecutive newlines: `re.split('\n{2,}', str(value))`, producing a list of paragraph strings.
  3. If `autoescape` is `True`: for each paragraph `p`, produces `'<p>%s</p>' % escape(p).replace('\n', '<br>')`.
     If `autoescape` is `False`: produces `'<p>%s</p>' % p.replace('\n', '<br>')` (no escaping).
  4. Joins all paragraph strings with `'\n\n'`.
- **Returns:** A string of `<p>` blocks separated by blank lines, with single newlines within paragraphs replaced by `<br>`.

---

### Class: `MLStripper(HTMLParser)`

A custom HTML parser that strips tags and preserves character data.

**`__init__(self)`**
- Calls `super().__init__(convert_charrefs=False)`, then `self.reset()`, and initializes `self.fed = []`.

**`handle_data(self, d)`** — Appends raw text data `d` to `self.fed`.

**`handle_entityref(self, name)`** — Appends `'&%s;' % name` (the entity reference as a string) to `self.fed`.

**`handle_charref(self, name)`** — Appends `'&#%s;' % name` (the numeric character reference as a string) to `self.fed`.

**`get_data(self)`** — Returns `''.join(self.fed)`, i.e., all accumulated text data with entity/char references preserved verbatim.

---

### Function: `_strip_once(value)`

- **Private helper.** No lazy decorator.
- **Logic:** Creates an `MLStripper` instance, feeds it the string `value`, calls `.close()`, then returns `s.get_data()` — the input with all HTML tags stripped in one pass.
- **Returns:** A string with tags removed; entity references and character data preserved.

---

### Function: `strip_tags(value)`

- **Decorator:** `@keep_lazy_text`.
- **Logic:**
  1. Converts `value` to a string.
  2. Enters a `while '<' in value and '>' in value:` loop:
     - Calls `_strip_once(value)` to produce `new_value`.
     - If the count of `<` characters is unchanged between `value` and `new_value`, breaks (no more tags detected).
     - Otherwise, sets `value = new_value` and repeats.
  3. Returns the final `value`.
- **Returns:** A string with all HTML/XML tags stripped. The loop handles malformed or nested tags that a single pass might miss.

---

### Function: `strip_spaces_between_tags(value)`

- **Decorator:** `@keep_lazy_text`.
- **Logic:** Applies `re.sub(r'>\s+<', '><', str(value))` — replaces any sequence of whitespace characters between the closing `>` of one tag and the opening `<` of the next with nothing (direct concatenation).
- **Returns:** A string with inter-tag whitespace removed.

---

### Function: `smart_urlquote(url)`

- **No lazy decorator.** No return-path lazy behavior.
- **Inner function: `unquote_quote(segment)`** — First calls `unquote(segment)`, then re-quotes it using `quote(segment, safe=RFC3986_SUBDELIMS + RFC3986_GENDELIMS + '~')`. The tilde is preserved as an unreserved character per RFC 3986.
- **Logic:**
  1. Attempts to parse the URL with `urlsplit(url)`, yielding `(scheme, netloc, path, query, fragment)`. If this raises `ValueError` (e.g., invalid IPv6 brackets), returns `unquote_quote(url)` directly on the raw input.
  2. Converts the `netloc` to punycode via `punycode(netloc)` (IDN → ACE). If this raises `UnicodeError`, returns `unquote_quote(url)` on the raw input.
  3. If `query` is non-empty: parses it into key-value pairs with `parse_qsl(query, keep_blank_values=True)`, unquotes each key and value individually, then re-encodes via `urlencode(query_parts)`.
  4. Applies `unquote_quote(path)` and `unquote_quote(fragment)`.
  5. Reassembles the URL components with `urlunsplit((scheme, netloc, path, query, fragment))`.
- **Returns:** A string — the URL with unquoted segments re-quoted according to RFC 3986 rules, IDN domains converted to punycode, and query parameters properly encoded.

---

### Class: `Urlizer`

Converts URLs and email addresses in text into clickable HTML anchor tags.

**Class attributes:**
| Name | Value |
|---|---|
| `trailing_punctuation_chars` | `'.,:;!'` |
| `wrapping_punctuation` | `[('(', ')'), ('[', ']')]` |
| `simple_url_re` | `_lazy_re_compile(r'^https?://\[?\w', re.IGNORECASE)` — matches strings starting with `http://` or `https://`, optionally followed by `[`. |
| `simple_url_2_re` | `_lazy_re_compile(r'^www\.|^(?!http)\w[^@]+\.(com|edu|gov|int|mil|net|org)($|/.*)$', re.IGNORECASE)` — matches strings starting with `www.` or a word followed by `.com`, `.edu`, `.gov`, `.int`, `.mil`, `.net`, `.org`. |
| `word_split_re` | `_lazy_re_compile(r'''([\s<>"']+)''')` — splits on whitespace and quote/angle-bracket characters. |
| `mailto_template` | `'mailto:{local}@{domain}'` |
| `url_template` | `'<a href="{href}"{attrs}>{url}</a>'`

**Method: `__call__(self, text, trim_url_limit=None, nofollow=False, autoescape=False)`**

- **Logic:**
  1. Records whether the input is already safe data: `safe_input = isinstance(text, SafeData)`.
  2. Splits `str(text)` into words using `word_split_re.split()`, which separates text at whitespace and `<>"'` boundaries.
  3. For each word, calls `self.handle_word(word, safe_input=safe_input, trim_url_limit=trim_url_limit, nofollow=nofollow, autoescape=autoescape)`.
  4. Joins all results with `''.join(...)` and returns the concatenated string.

**Method: `handle_word(self, word, *, safe_input, trim_url_limit=None, nofollow=False, autoescape=False)`**

- **Logic:**
  1. If the word contains `.`, `@`, or `:`:
     - Calls `self.trim_punctuation(word)` to extract `(lead, middle, trail)`.
     - Initializes `url = None` and `nofollow_attr = ' rel="nofollow"' if nofollow else ''`.
     - **URL detection (in order):**
       a. If `simple_url_re.match(middle)`: sets `url = smart_urlquote(html.unescape(middle))`.
       b. Else if `simple_url_2_re.match(middle)`: sets `url = smart_urlquote('http://%s' % html.unescape(middle))` (prepends `http://`).
       c. Else if `:` is not in middle and `self.is_email_simple(middle)` returns `True`: splits on last `@` into `(local, domain)`, converts domain to punycode (returns original word on `UnicodeError`), sets `url = self.mailto_template.format(local=local, domain=domain)`, and clears `nofollow_attr` (`''`).
     - **If a URL was found:**
       - Trims the display text via `self.trim_url(middle, limit=trim_url_limit)`.
       - If `autoescape and not safe_input`: escapes `lead`, `trail`, and `trimmed` individually.
       - Formats the anchor tag: `middle = self.url_template.format(href=escape(url), attrs=nofollow_attr, url=trimmed)`.
       - Returns `mark_safe(f'{lead}{middle}{trail}')`.
     - **If no URL was found:**
       - If `safe_input`: returns `mark_safe(word)`.
       - Else if `autoescape`: returns `escape(word)`.
  2. Else (word has no `.`, `@`, or `:`):
     - If `safe_input`: returns `mark_safe(word)`.
     - Else if `autoescape`: returns `escape(word)`.
  3. Returns the original `word` unchanged.

**Method: `trim_url(self, x, *, limit)`**

- **Logic:** If `limit is None or len(x) <= limit`, returns `x` unchanged. Otherwise returns `'{}…'.format(x[:max(0, limit - 1)])` — truncates to `limit - 1` characters and appends an ellipsis character (`…`).
- **Returns:** The possibly-truncated string.

**Method: `trim_punctuation(self, word)`**

- **Logic:** Iteratively trims leading wrapping punctuation (opening parens/brackets) from the start of `word`, trailing wrapping punctuation (closing parens/brackets) from the end if balanced, and trailing standard punctuation (`.,:;!`) after unescaping HTML entities. Uses a loop that continues until no more trimming occurs in an iteration.
- **Returns:** A tuple `(lead, middle, trail)` where `middle` is the word with surrounding punctuation removed.

**Method: `is_email_simple(value)` — static method**

- **Logic:** Returns `False` if `@` is absent, at start, or at end of `value`. Splits on `@`; returns `False` if split fails (more than one `@`). Checks that the domain part (`p2`) contains a `.` and does not start with `.`.
- **Returns:** `True` if the value looks like a simple email address; `False` otherwise.

---

### Function: `urlize(text, trim_url_limit=None, nofollow=False, autoescape=False)`

- **Decorator:** `@keep_lazy_text`.
- **Logic:** Delegates to `urlizer(text, trim_url_limit=trim_url_limit, nofollow=nofollow, autoescape=autoescape)`, i.e., calls the module-level `Urlizer` singleton's `__call__` method.
- **Returns:** A string with all detected URLs and email addresses converted into `<a>` anchor tags.

---

### Function: `avoid_wrapping(value)`

- **No lazy decorator.**
- **Logic:** Returns `value.replace(" ", "\xa0")` — replaces every regular space character with a non-breaking space (`\xa0`).
- **Returns:** A string where spaces are replaced by `\xa0`, preventing text wrapping at those positions.

---

### Function: `html_safe(klass)`

- **No lazy decorator.** Decorator factory.
- **Logic:**
  1. Raises `ValueError` if `'__html__' in klass.__dict__` (the class already defines `__html__`).
  2. Raises `ValueError` if `'__str__' not in klass.__dict__` (the class does not define `__str__`).
  3. Saves the original `__str__`: `klass_str = klass.__str__`.
  4. Replaces `klass.__str__` with a lambda: `lambda self: mark_safe(klass_str(self))` — wraps the original string output in `mark_safe()`.
  5. Adds `klass.__html__` as a lambda: `lambda self: str(self)` — returns the (now-safe) string representation.
  6. Returns `klass` (modified in place).
- **Returns:** The same class object, mutated to have safe-string-aware `__str__` and `__html__` methods.