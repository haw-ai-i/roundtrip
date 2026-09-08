Problem in pretty printing
>>>from sympy import *
>>>from sympy.vector import *
>>>x=symbols('x')
>>>e=CoordSys3D('e')
>>>e=((x/2)**x)*e.i
>>> pprint(e)
`
Gives output:
⎛   x⎞ e_i
⎜⎛x⎞ e_i ⎟
⎜⎜─⎟ ⎟    
⎝⎝2⎠ ⎠  

Which isn't proper ( **exponent breaks the bracket** ). Is there any way to fix this?
