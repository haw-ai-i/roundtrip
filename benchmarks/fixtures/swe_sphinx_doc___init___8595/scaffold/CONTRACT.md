# Implementation target
Write the module at `sphinx/ext/autodoc/__init__.py`.

## `sphinx/ext/autodoc/__init__.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ALL`
- `AttributeDocumenter`
- `ClassDocumenter`
- `ClassLevelDocumenter`
- `DataDocumenter`
- `DataDocumenterMixinBase`
- `DecoratorDocumenter`
- `DocstringSignatureMixin`
- `DocstringStripSignatureMixin`
- `Documenter`
- `EMPTY`
- `ExceptionDocumenter`
- `FunctionDocumenter`
- `GenericAliasMixin`
- `INSTANCEATTR`
- `MethodDescriptorType`
- `MethodDocumenter`
- `ModuleDocumenter`
- `ModuleLevelDocumenter`
- `NewTypeAttributeDocumenter`
- `NewTypeDataDocumenter`
- `NewTypeMixin`
- `NonDataDescriptorMixin`
- `ObjectMember`
- `ObjectMembers`
- `Options`
- `PropertyDocumenter`
- `RuntimeInstanceAttributeMixin`
- `SLOTSATTR`
- `SUPPRESS`
- `SlotsMixin`
- `TypeVarMixin`
- `UNINITIALIZED_ATTR`
- `UninitializedGlobalVariableMixin`
- `UninitializedInstanceAttributeMixin`
- `annotation_option`
- `autodoc_attrgetter`
- `between`
- `bool_option`
- `cut_lines`
- `exclude_members_option`
- `get_documenters`
- `identity`
- `inherited_members_option`
- `logger`
- `member_order_option`
- `members_option`
- `members_set_option`
- `merge_members_option`
- `merge_special_members_option`
- `migrate_autodoc_member_order`
- `py_ext_sig_re`
- `setup`
- `special_member_re`

Implement them to satisfy the specification. Do not write tests.
