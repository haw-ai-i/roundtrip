Support nullable pandas dtypes in `confusion_matrix`
### Describe the workflow you want to enable

I would like to be able to pass the nullable pandas dtypes ("Int64", "Float64", "boolean") into sklearn's `confusion_matrix` function. Because the dtypes become object dtype when converted to numpy arrays we get `ValueError: Classification metrics can't handle a mix of unknown and binary targets`:

Repro with sklearn 1.2.1:
```python
    import pandas as pd
    import pytest
    from sklearn.metrics import confusion_matrix

    for dtype in ["Int64", "Float64", "boolean"]:
        y_true = pd.Series([1, 0, 0, 1, 0, 1, 1, 0, 1], dtype=dtype)
        y_predicted = pd.Series([0, 0, 1, 1, 0, 1, 1, 1, 1], dtype="int64")

        with pytest.raises(ValueError, match="Classification metrics can't handle a mix of unknown and binary targets"):
            confusion_matrix(y_true, y_predicted)
```

### Describe your proposed solution

We should get the same behavior as when int64, float64, and bool dtypes are used, which is no error:

```python
    import pandas as pd
    from sklearn.metrics import confusion_matrix

    for dtype in ["int64", "float64", "bool"]:
        y_true = pd.Series([1, 0, 0, 1, 0, 1, 1, 0, 1], dtype=dtype)
        y_predicted = pd.Series([0, 0, 1, 1, 0, 1, 1, 1, 1], dtype="int64")

        confusion_matrix(y_true, y_predicted)
```

### Describe alternatives you've considered, if relevant

Our current workaround is to convert the data to numpy arrays with the corresponding dtype that works prior to passing it into `confusion_matrix`

### Additional context

_No response_
