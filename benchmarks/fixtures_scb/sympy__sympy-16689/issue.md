codegen generate wrong signature
When an argument sequence is specified in codegen, any matrix argument that is not present in the expression to be converted will get a default type `double` instead of `double*`.
For instance :

```python
import sympy as sy
from sympy.utilities.codegen import codegen

X = sy.MatrixSymbol('X',3,1)
Y = sy.MatrixSymbol('Y',3,1)
z = sy.symbols('z',integer = True)

[(cf, cs), (hf, hs)] = codegen(('testBug', X[0]+X[1]),
           language='c',argument_sequence = (X,Y,z))
print(hs)
```

generates  a function signature : `double testBug(double *X, double Y, int z);`

where `double testBug(double *X, double *Y, int z);`  is expected

But 

```python
[(cf, cs), (hf, hs)] = codegen(('testBug', X[0]+X[1]+Y[0]),
           language='c',argument_sequence = (X,Y,z))
print(hs)
```
gives the good signature.

I use sympy 1.3
