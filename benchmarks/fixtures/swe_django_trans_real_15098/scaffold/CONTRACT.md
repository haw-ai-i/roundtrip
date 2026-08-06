# Implementation target
Write the module at `django/utils/translation/trans_real.py`.

## `django/utils/translation/trans_real.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `CONTEXT_SEPARATOR`
- `DjangoTranslation`
- `TranslationCatalog`
- `accept_language_re`
- `activate`
- `all_locale_paths`
- `catalog`
- `check_for_language`
- `deactivate`
- `deactivate_all`
- `do_ntranslate`
- `get_language`
- `get_language_bidi`
- `get_language_from_path`
- `get_language_from_request`
- `get_languages`
- `get_supported_language_variant`
- `gettext`
- `gettext_noop`
- `language_code_prefix_re`
- `language_code_re`
- `ngettext`
- `npgettext`
- `parse_accept_lang_header`
- `pgettext`
- `reset_cache`
- `translation`

Implement them to satisfy the specification. Do not write tests.
