octave(sinc(x)) doesn't work
```
In [9]: octave_code(sinc(x))
Out[9]: '% Not supported in Octave:\n% sinc\nsinc(x)'
```

Octave does the "normalized sinc function" so the desired output is:

```
'sinc(x/pi)'
```

How to start:
1. clone sympy
2.  look at #11219, changes should be very similar to the `_print_uppergamma` stuff.

