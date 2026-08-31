[Bug]: Calling matplotlib.pyplot.show() outside of matplotlib.pyplot.rc_context no longer works
### Bug summary

Creating a plot inside of matplotlib.pyplot.rc_context and then calling matplotlib.pyplot.show() outside said context causes the program to freeze.

### Code for reproduction

```python
import matplotlib.pyplot as plt

with plt.rc_context():
    plt.plot([1, 3, 2])

plt.show()
```


### Actual outcome

The program freezes.

### Expected outcome

The plot is shown.

### Additional information

* matplotlib.pyplot.savefig() works as expected.
* The bug did not occur in earlier versions.
* The bug does not occur when using Jupyter, only when using the regular Python interpreter.
* The bug does not occur if plt.show() is called inside of plt.rc_context.

### Operating system

Linux, 5.17.9-1-MANJARO, all packages up-to-date

### Matplotlib Version

3.5.2

### Matplotlib Backend

QtAgg

### Python version

3.10.4

### Jupyter version

3.4.2

### Installation

Linux package manager
