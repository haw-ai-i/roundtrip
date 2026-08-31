Deprecate sympify string fallback
<!-- Your title above should be a short description of what
was changed. Do not include the issue number in the title. -->

#### References to other Issues or PRs
<!-- If this pull request fixes an issue, write "Fixes #NNNN" in that exact
format, e.g. "Fixes #1234" (see
https://tinyurl.com/auto-closing for more information). Also, please
write a comment on that issue linking back to this pull request once it is
open. -->
Fixes #18066
#18056

#### Brief description of what is fixed or changed

I've noticed that default_sort_key sympifies elements with string fallback.
And the issue #18056 still has problem in the master if it is about sorting
```python3
from sympy import *
from sympy.core.compatibility import default_sort_key

class C:
    def __repr__(self):
        return 'x.y'

a = Symbol('x')
b = C()

sorted([a, b], key=default_sort_key)
```
```
<string> in <module>

AttributeError: 'Symbol' object has no attribute 'y'
```

I think that default_sort_key still have to rely on `str` for ordering any external object with sympy, but it's better not to execute evaluate some nonsensical syntax that can cause problems

#### Other comments


#### Release Notes

<!-- Write the release notes for this release below. See
https://github.com/sympy/sympy/wiki/Writing-Release-Notes for more information
on how to write release notes. The bot will check your release notes
automatically to see if they are formatted correctly. -->

<!-- BEGIN RELEASE NOTES -->
- core
  - Deprecated sympify automatically converting custom objects with `__str__` or `__repr__` implemented.
