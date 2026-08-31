autodoc_type_aliases does not support dotted name
**Describe the bug**
autodoc_type_aliases does not support dotted name

**To Reproduce**

```
# helloworld.py
from __future__ import annotations  # important!
import struct

def consume_struct(_: struct.Struct) -> None:
    pass
```
```
# conf.py
autodoc_type_aliases = {
    'struct.Struct': 'struct.Struct',
}
```

The autodoc_type_aliases entry does not work as expected.
(refs: #8315)

**Expected behavior**
Supporting

**Your project**
No

**Screenshots**
No

**Environment info**
- OS: Mac
- Python version: 3.8.2
- Sphinx version: HEAD of 3.x
- Sphinx extensions: sphinx.ext.autodoc
- Extra tools: No

**Additional context**
No
