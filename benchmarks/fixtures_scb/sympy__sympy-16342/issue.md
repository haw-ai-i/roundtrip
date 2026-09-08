Intersection gives wrong results for some symbolic finite sets
For instance 

```py
>>> Intersection(FiniteSet(1, 2, x), FiniteSet(2, 3, x, y))
Union({2, x}, Intersection({1}, UniversalSet()))
```

It doesn't simplify properly. The above is equal to just `{1, 2, x}`. However, this is wrong. `1` is contained in the intersection iff it is equal to `x` or `y`. Since this cannot be determined, it must be represented as just `Intersection({1, 2, x}, {2, x, y})`, or `Union(2, x, Intersection({1}, {y}))` (note that we don't need to worry about the case where 1 or 3 equals x, because x is already contained in the set unconditionally).

The `Intersection._handle_finite_sets` code is somewhat buggy. I have some fixes to it that avoid recursion errors and fix the above simplification issue, which I'll be pushing up soon. But I'm not sure how to fix this. Maybe there is a simple fix I'm not seeing, or but likely the algorithm needs to be rewritten.
