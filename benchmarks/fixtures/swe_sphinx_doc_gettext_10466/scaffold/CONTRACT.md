# Implementation target
Write the module at `sphinx/builders/gettext.py`.

## `sphinx/builders/gettext.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `Catalog`
- `GettextRenderer`
- `I18nBuilder`
- `I18nTags`
- `LocalTimeZone`
- `Message`
- `MessageCatalogBuilder`
- `MsgOrigin`
- `logger`
- `ltz`
- `setup`
- `should_write`
- `source_date_epoch`
- `timestamp`
- `tzdelta`

Implement them to satisfy the specification. Do not write tests.
