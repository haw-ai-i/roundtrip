BUG IsotonicRegression errors with set_config(transform_output="pandas")
### Describe the bug

`IsotonicRegression.predict` is broken by `set_config(transform_output="pandas")`. Mabye similar to #25365.

### Steps/Code to Reproduce

```python
import numpy as np
from sklearn.isotonic import IsotonicRegression
y = np.arange(4)
x = np.ones(4)

iso = IsotonicRegression().fit(x, y)
iso.predict([1])  # array([1.5])

iso = IsotonicRegression().set_output(transform="pandas").fit(x, y)
iso.predict([1])
```

### Expected Results

```
array([1.5])
```

Or at least no error!

### Actual Results

```
TypeError: 'builtin_function_or_method' object is not iterable
```

### Versions

```shell
1.2.1
```

