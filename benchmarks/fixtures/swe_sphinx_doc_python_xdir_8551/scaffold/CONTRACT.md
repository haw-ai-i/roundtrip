# Implementation target
Write the following 2 modules. They live in the same package and may import each other.

## `sphinx/domains/python.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `ModuleEntry`
- `ObjectEntry`
- `PyAttribute`
- `PyClassMethod`
- `PyClasslike`
- `PyClassmember`
- `PyCurrentModule`
- `PyDecoratorFunction`
- `PyDecoratorMethod`
- `PyDecoratorMixin`
- `PyField`
- `PyFunction`
- `PyGroupedField`
- `PyMethod`
- `PyModule`
- `PyModulelevel`
- `PyObject`
- `PyStaticMethod`
- `PyTypedField`
- `PyVariable`
- `PyXRefRole`
- `PyXrefMixin`
- `PythonDomain`
- `PythonModuleIndex`
- `_pseudo_parse_arglist`
- `builtin_resolver`
- `filter_meta_fields`
- `logger`
- `pairindextypes`
- `py_sig_re`
- `setup`
- `type_to_xref`

## `sphinx/util/docfields.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `DocFieldTransformer`
- `Field`
- `GroupedField`
- `TypedField`

Implement them to satisfy the specification. Do not write tests.
