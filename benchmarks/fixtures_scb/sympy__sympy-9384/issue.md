Refine doesn't simplify piecewise function
```
In [8]: from sympy import *
In [9]: from sympy.abc import l
In [10]: refine(Piecewise((1, l<0), (0, True)), Q.positive(l))
Out[10]: Piecewise((1, l < 0), (0, True))
```

The output should be zero, like in Mathematica:

```
In[1]:= Piecewise[{{1, l<0}, {0, True}}]
In[3]:= Refine[%, l > 0]
Out[3]= 0
```

