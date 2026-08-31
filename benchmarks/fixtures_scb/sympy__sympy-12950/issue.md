as_explicit raises an error for MatMul objects (regression in sympy 1.1)
In sympy 1.0, the following works as expected:
```pycon
>>> from sympy import *
>>> M = Matrix([[Symbol("x")]]) * MatrixSymbol("A", 1, 1)
>>> M
Matrix([[x]])*A
>>> M.as_explicit()
Matrix([[x*A[0, 0]]])
```
In sympy 1.1, the last statement from above raises an error:
```pycon
/home/.../matmul.pyc in _entry(self, i, j, expand)
     65             return coeff*Add(*[X[i, k]*Y[k, j] for k in range(X.cols)])
     66         result = Sum(coeff*X[i, k]*Y[k, j], (k, 0, X.cols - 1))
---> 67         if not X.cols.is_number:
     68             # Don't waste time in result.doit() if the sum bounds are symbolic
     69             expand = False

AttributeError: 'int' object has no attribute 'is_number'
```

Bisecting shows that the problem has been introduced with this commit: 6d55b862 (pinging @siefkenj as the commit author).
