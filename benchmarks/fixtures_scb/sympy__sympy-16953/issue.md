Intersection of sets with symbolic elements could be empty
We have
```julia
In [4]: FiniteSet(1+x-y) & FiniteSet(1)
Out[4]: {1} ∩ {x - y + 1}

In [5]: FiniteSet(1) & FiniteSet(1+x-y)
Out[5]: {1}
```
Clearly the two expressions should give the same result. The first result is correct since if x!=y then the result is the empty set:
```julia
In [6]: FiniteSet(1) & FiniteSet(1+x-y).subs(x, y+1)
Out[6]: ∅
```
