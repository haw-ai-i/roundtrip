sympy cannot simplify sign(x) * abs(x)
```
>>> from sympy import Symbol, sign
>>> x = Symbol('x', real=True)
>>> x_new = abs(x)*sign(x)
>>> x_new
Abs(x)*sign(x)
>>> x_new.simplify()
Abs(x)*sign(x)
```

I would expect the result to be just `x`. gh-19277 may be related.

