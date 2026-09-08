Support pandas nullable dtypes for scoring metrics 
### Describe the workflow you want to enable

I would like to be able to pass data with the nullable pandas dtypes (`Int64`, `Float64`, and `boolean`) into sklearn metrics such as `matthews_corrcoef`, `accuracy_score`, and `f1_score` (and more) even if the data does not contain any nans. Currently, they result in one of several errors:

- If `y_true` and `y_pred` are both nullable types: `ValueError: unknown is not supported`
-  it only one of `y_true` or `y_pred` is nullable and the other is non nullable : `ValueError: Classification metrics can't handle a mix of unknown and binary [or multiclass] targets`
- Some metrics such as `log_loss` result in a different error when `y_true` is nullable:  `ValueError: Unknown label type: (0    1`

Repro with sklearn 1.2.1 and pandas 1.5.3:

```python
    import pandas as pd
    import pytest
    from sklearn import metrics

    for dtype in ['Int64', 'Float64', 'boolean']:
        # Error if only target uses nullable types
        X = pd.DataFrame({"a": pd.Series([1, 2, 3, 4]), 
                          "b": pd.Series([9,8,7,6])})

        # Two nullable dtypes used 
        y_true = pd.Series([1, 0, 1, 0], dtype=dtype)
        y_predicted = pd.Series([1, 0, 1, 0], dtype=dtype)
        with pytest.raises(ValueError, match="unknown is not supported"):
            metrics.accuracy_score(
                    y_true,
                    y_predicted,
                )

        # Only one nullable dtype used 
        y_predicted = pd.Series([1, 0, 1, 0], dtype="float64")
        with pytest.raises(ValueError, match="Classification metrics can't handle a mix of unknown and binary targets"):
            metrics.accuracy_score(
                    y_true,
                    y_predicted,
                )
``` 



### Describe your proposed solution

Sklearn should recognize the pandas nullable dtypes as the correct type of target for their scoring metrics like it does with the non nullable dtypes.

### Describe alternatives you've considered, if relevant

As this data doesn't have null values, we can convert to the non nullable dtype prior to passing to sklearn, but doing that will make it cumbersome to build software that leverages both the latest pandas dtypes and sklearn.

### Additional context

_No response_
