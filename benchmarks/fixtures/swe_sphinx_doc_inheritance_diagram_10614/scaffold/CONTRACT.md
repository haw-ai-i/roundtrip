# Implementation target
Write the module at `sphinx/ext/inheritance_diagram.py`.

## `sphinx/ext/inheritance_diagram.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `InheritanceDiagram`
- `InheritanceException`
- `InheritanceGraph`
- `get_graph_hash`
- `html_visit_inheritance_diagram`
- `import_classes`
- `inheritance_diagram`
- `latex_visit_inheritance_diagram`
- `module_sig_re`
- `py_builtins`
- `setup`
- `skip`
- `texinfo_visit_inheritance_diagram`
- `try_import`

Implement them to satisfy the specification. Do not write tests.
