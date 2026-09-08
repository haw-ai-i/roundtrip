Value error in subs
```
e=(7*x*cos(x) - 12*log(x)**3)*(-log(x)**4 + 2*sin(x) + 1)**2/(2*(x*cos(x) - 2*log(x)**3)*(3*log(x)**4 - 7*sin(x) + 3)**2)
e.subs(x,oo)
```
gives `ValueError: The argument 'nan' is not comparable.`
