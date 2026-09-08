Support nullable pandas dtypes in LabelBinarizer
### Describe the workflow you want to enable

I would like to be able to pass the nullable pandas dtypes ("Int64", "Float64", "boolean") into sklearn's LabelBinarizer. Because the dtypes become object dtype when converted to numpy arrays we get `ValueError: Unknown label type:`:

Repro with sklearn 1.2.1:

```python
    import pandas as pd
    import pytest
    from sklearn.preprocessing import LabelBinarizer

    for dtype in ["Int64", "Float64", "boolean"]:

        y_true = pd.Series([1, 0, 0, 1, 0, 1, 1, 0, 1], dtype=dtype)

        lb = LabelBinarizer()

        with pytest.raises(ValueError, match="Unknown label type:"):
            lb.fit(y_true.unique())

```

### Describe your proposed solution

We should get the same behavior as when int64, float64, and bool dtypes are used, which is no error:

```python
    import pandas as pd
    from sklearn.preprocessing import LabelBinarizer

    for dtype in ["int64", "float64", "bool"]:
        y_true = pd.Series([1, 0, 0, 1, 0, 1, 1, 0, 1], dtype=dtype)

        lb = LabelBinarizer()

        lb.fit(y_true.unique())
        y_one_hot_true = lb.transform(y_true)
```

### Describe alternatives you've considered, if relevant

Our current workaround is to convert the data to numpy arrays with the corresponding dtype that works prior to passing it into LabelBinarizer

### Additional context

_No response_
