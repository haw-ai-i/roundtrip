# Implementation target
Write the module at `sphinx/ext/autodoc/__init__.py`.

## `sphinx/ext/autodoc/__init__.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ALL`
- `AttributeDocumenter`
- `ClassDocumenter`
- `ClassLevelDocumenter`
- `DataDeclarationDocumenter`
- `DataDocumenter`
- `DecoratorDocumenter`
- `DocstringSignatureMixin`
- `DocstringStripSignatureMixin`
- `Documenter`
- `ExceptionDocumenter`
- `FunctionDocumenter`
- `INSTANCEATTR`
- `InstanceAttributeDocumenter`
- `MethodDescriptorType`
- `MethodDocumenter`
- `ModuleDocumenter`
- `ModuleLevelDocumenter`
- `Options`
- `PropertyDocumenter`
- `SLOTSATTR`
- `SUPPRESS`
- `SingledispatchFunctionDocumenter`
- `SingledispatchMethodDocumenter`
- `SlotsAttributeDocumenter`
- `UNINITIALIZED_ATTR`
- `annotation_option`
- `autodoc_attrgetter`
- `between`
- `bool_option`
- `cut_lines`
- `get_documenters`
- `identity`
- `inherited_members_option`
- `logger`
- `member_order_option`
- `members_option`
- `members_set_option`
- `merge_special_members_option`
- `migrate_autodoc_member_order`
- `py_ext_sig_re`
- `setup`

Implement them to satisfy the specification. Do not write tests.
