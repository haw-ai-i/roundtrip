DiagonalMatrix assumes shape is square
`DiagonalMatrix` assumes its shape is (row x row):

```
>>> a=DiagonalMatrix(MatrixSymbol('x', 2, 3))
>>> b=DiagonalMatrix(MatrixSymbol('x', 3, 2))
>>> a.shape, b.shape
((2, 2), (3, 3))
```

So it is not surprising that the multiplication may fail;

```
>>> a*b
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "sympy\matrices\expressions\matexpr.py", line 21, in __sympifyit_wrapper
    b = sympify(b, strict=True)
  File "sympy\core\decorators.py", line 119, in binary_op_wrapper
    return func(self, other)
  File "sympy\matrices\expressions\matexpr.py", line 106, in __mul__
    def __mul__(self, other):
  File "sympy\matrices\expressions\matmul.py", line 38, in __new__
    validate(*matrices)
  File "sympy\matrices\expressions\matmul.py", line 136, in validate
    raise ShapeError("Matrices %s and %s are not aligned"%(A, B))
sympy.matrices.matrices.ShapeError: Matrices DiagonalMatrix(x) and DiagonalMatri
x(x) are not aligned
```

But non-square matrices should be allowed:

```
>>> Matrix(2,3,(1,0,0,0,2,0)) * Matrix(3,2,(4,0,0,5,0,0))
Matrix([
[4,  0],
[0, 10]])
```

The effective matrix size should be the minimum of the given dimensions. When any dimension is symbolic, there should be a way to indicate which one is the smaller. Or if one is symbolic and the other definite then (maybe) the definite one could be taken to be the limiting one. If both are symbolic there should either be an error or else a way to select the smaller of the two dimensions.

A **related issue** is that `DiagonalOf` assumes its shape is (row, 1):

```
>>> DiagonalOf(MatrixSymbol('x', 3, 2)).shape
(3, 1)  <------- that should be (2, 1)
```
