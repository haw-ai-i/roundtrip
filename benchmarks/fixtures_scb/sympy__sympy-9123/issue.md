apart drops term
As identified [here](https://groups.google.com/forum/#!topic/sympy/V2qydfXuw7Y) `apart` will sometimes drop a term:

``` python
>>> (x/2).apart()
x/2
>>> (x/2).apart(x)
x/2
>>> (x/2).apart(y)  <------ problem
0
>>> (x/a).apart(y)
x/a
>>> (2*x).apart(y)
2*x
```

