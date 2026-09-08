[Bug]: ax.errorbar raises for all-nan data on matplotlib 3.6.2
### Bug summary

The function `ax.errorbar` raises a `StopIteration` error when `yerr` contains only `NaN` values.

### Code for reproduction

```python
import matplotlib.pyplot as plt
import numpy as np
fig, ax = plt.subplots(1, 1)
ax.errorbar([0], [0], [np.nan])
```


### Actual outcome

```shell
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "~/.local/share/virtualenvs/pipeline/lib/python3.9/site-packages/matplotlib/__init__.py", line 1423, in inner
    return func(ax, *map(sanitize_sequence, args), **kwargs)
  File "~.local/share/virtualenvs/pipeline/lib/python3.9/site-packages/matplotlib/axes/_axes.py", line 3488, in errorbar
    yerr = _upcast_err(yerr)
  File "~/.local/share/virtualenvs/pipeline/lib/python3.9/site-packages/matplotlib/axes/_axes.py", line 3470, in _upcast_err
    isinstance(cbook._safe_first_finite(err), np.ndarray)
  File "~/.local/share/virtualenvs/pipeline/lib/python3.9/site-packages/matplotlib/cbook/__init__.py", line 1749, in _safe_first_finite
    return next(val for val in obj if safe_isfinite(val))
StopIteration
```

### Expected outcome

No crash, similar to the case where only some values are NaN.

### Additional information

This happens because  `_upcast_err` unconditionally looks for a first finite element in `xerr` and `yerr`.

### Operating system

Debian

### Matplotlib Version

3.6.2

### Matplotlib Backend

TkAgg

### Python version

3.9.2

### Jupyter version

_No response_

### Installation

pip
