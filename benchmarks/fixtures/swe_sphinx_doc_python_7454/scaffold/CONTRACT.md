# Implementation target
Write the module at `sphinx/domains/python.py`.

## `sphinx/domains/python.py`
Other modules import these names from it, so they MUST exist with these exact names:
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

Implement them to satisfy the specification. Do not write tests.
