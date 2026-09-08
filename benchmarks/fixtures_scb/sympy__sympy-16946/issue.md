is_EmptySet should be replaced by is_empty
There could be another property `is_empty` that could return `None` for `Interval(x, y)`. I think that `is_EmptySet` should be `True` only for `EmptySet` and `False` otherwise. (Then it would, in fact, be redundant as `is EmptySet` would have the same meaning.) So I suggest that `is_EmptySet` be replaced by `is_empty` everywhere.

_Originally posted by @jksuom in https://github.com/sympy/sympy/pull/11522#issuecomment-498056206_


**Update**: see this comment for a short discussion on when to use `is_empty`: https://github.com/sympy/sympy/issues/16946#issuecomment-524762143
