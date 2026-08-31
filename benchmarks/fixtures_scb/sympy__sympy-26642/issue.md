parse_mathematica cannot handle greek letters
```py
from sympy.parsing.mathematica import parse_mathematica
parse_mathematica('α')
```
Output
```
Traceback (most recent call last):

  File ~/.local/lib/python3.10/site-packages/IPython/core/interactiveshell.py:3508 in run_code
    exec(code_obj, self.user_global_ns, self.user_ns)

  Cell In[71], line 1
    parse_mathematica('α')

  File ~/.local/lib/python3.10/site-packages/sympy/parsing/mathematica.py:82 in parse_mathematica
    return parser.parse(s)

  File ~/.local/lib/python3.10/site-packages/sympy/parsing/mathematica.py:535 in parse
    s3 = self._from_tokens_to_fullformlist(s2)

  File ~/.local/lib/python3.10/site-packages/sympy/parsing/mathematica.py:740 in _from_tokens_to_fullformlist
    return self._parse_after_braces(stack[0])

  File ~/.local/lib/python3.10/site-packages/sympy/parsing/mathematica.py:909 in _parse_after_braces
    raise SyntaxError("unable to create a single AST for the expression")

  File <string>
SyntaxError: unable to create a single AST for the expression
```
