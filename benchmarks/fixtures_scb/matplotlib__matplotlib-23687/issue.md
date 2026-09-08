[Bug]: barplot does not show anything when x or bottom start and end with NaN
### Bug summary

I am not sure if this is a bug or an optimization, but in most cases it is fine to plot bars of arrays containing NaN (only the NaN values are not displayed, the rest is ok).

Here I found that when the `x` array or the `bottom` array have NaNs at the extremities, no bar is displayed.

(`barh` has the same behavior).

### Code for reproduction

```python
import numpy as np, matplotlib as mpl, matplotlib.pyplot as plt

barx = np.arange(3, dtype=float)
barheights = np.array([0.5, 1.5, 2.0])
barstarts=np.array([0.77]*3)

barx[[0,2]] = np.NaN
# alternatively:
#barstarts[[0,2]] = np.NaN

fig, ax = plt.subplots()

ax.bar(barx, barheights, bottom=barstarts)
# Not ok, nothing shown!

# Same behavior with ax.barh:
ax.barh(barx, barheights, left=barstarts)

# However, the behavior is correct when NaN only affect the 'heights' argument:

fig, ax = plt.subplots()
ax.bar(np.arange(3), np.array([np.NaN, 1, np.NaN]), bottom=np.array([0.2, 0.3, 0.4]))
# OK, one bar is displayed.
```


### Actual outcome

zero bar displayed

### Expected outcome

Non-NaN elements should be shown

### Additional information

_No response_

### Operating system

Ubuntu 20.04.3

### Matplotlib Version

3.5.3

### Matplotlib Backend

TkAgg, pdf

### Python version

3.8.10

### Jupyter version

ipython

### Installation

pip
