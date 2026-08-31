index_together warning after migration to new style

Description
I've got deprecation warning about
index_together
after migration to new style with
model.Index(fields=[...])
. I'm using pytest as test suite. I created minimal example, it is available on my GH:
​
https://github.com/Behoston/idx_to_bug
logs:
x/tests.py::test_x
  /home/behoston/venv/idx_to/lib/python3.11/site-packages/django/db/models/options.py:210: RemovedInDjango51Warning: 'index_together' is deprecated. Use 'Meta.indexes' in 'x.Item' instead.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
For fresh indexes it works fine (no warning), so I assume that problem is only during migrations when models from migrations files are evaluated.