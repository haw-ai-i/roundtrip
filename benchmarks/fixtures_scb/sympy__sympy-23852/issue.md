Problem indexing rank-1 `MutableDenseNDimArray`
I am unable to assign values to a rank-1 `MutableDenseNDimArray` because the parser throws an error requiring the index be a tuple.
Minimal working example:
``` python
from sympy import MutableDenseNDimArray as MArray
vec = MArray.zeros(3)
vec[0] = 2
```
Resulting error message:
``` python
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
Input In [72], in <cell line: 2>()
      1 vec = MArray.zeros(3)
----> 2 vec[0] = 2

File ~/Application-Data/miniconda3/lib/python3.9/site-packages/sympy/tensor/array/dense_ndim_array.py:199, in MutableDenseNDimArray.__setitem__(self, index, value)
    197         self._array[self._parse_index(i)] = value[other_i]
    198 else:
--> 199     index = self._parse_index(index)
    200     self._setter_iterable_check(value)
    201     value = _sympify(value)

File ~/Application-Data/miniconda3/lib/python3.9/site-packages/sympy/tensor/array/ndim_array.py:148, in NDimArray._parse_index(self, index)
    146 def _parse_index(self, index):
    147     if isinstance(index, (SYMPY_INTS, Integer)):
--> 148         raise ValueError("Only a tuple index is accepted")
    150     if self._loop_size == 0:
    151         raise ValueError("Index not valide with an empty array")

ValueError: Only a tuple index is accepted
```
I suspect it's just a spurious error thrown that can be fixed by setting a condition to only throw if rank > 1.
