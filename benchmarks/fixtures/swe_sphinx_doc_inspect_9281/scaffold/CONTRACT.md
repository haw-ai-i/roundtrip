# Implementation target
Write the module at `sphinx/util/inspect.py`.

## `sphinx/util/inspect.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DefaultValue`
- `TypeAliasForwardRef`
- `TypeAliasModule`
- `TypeAliasNamespace`
- `evaluate_signature`
- `getall`
- `getannotations`
- `getargspec`
- `getdoc`
- `getglobals`
- `getmro`
- `getslots`
- `isNewType`
- `is_builtin_class_method`
- `is_cython_function_or_method`
- `is_singledispatch_function`
- `is_singledispatch_method`
- `isabstractmethod`
- `isattributedescriptor`
- `isbuiltin`
- `isclassmethod`
- `iscoroutinefunction`
- `isdescriptor`
- `isenumattribute`
- `isenumclass`
- `isfunction`
- `isgenericalias`
- `ispartial`
- `isproperty`
- `isroutine`
- `isstaticmethod`
- `logger`
- `memory_address_re`
- `object_description`
- `safe_getattr`
- `signature`
- `signature_from_ast`
- `signature_from_str`
- `stringify_signature`
- `unpartial`
- `unwrap`
- `unwrap_all`

Implement them to satisfy the specification. Do not write tests.
