QuerySet.defer()  raises an AttributeError when the field is ManyToManyField or GenericForeignKey

Description
In Version 4.2.1
Hello, when I try to defer a field that is a
ManyToManyField
or a
GenericForeignKey
it raises an AttributteError.
Having these three models:
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, ContentType

class ModelA(models.Model):
    name = models.CharField(max_length=100)
  

class ModelB(models.Model):
    name = models.CharField(max_length=100)
    model_a = models.ManyToManyField('ModelA')
    

class ModelC(models.Model):
    name = models.CharField(max_length=100)
    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True)
    generic_model = GenericForeignKey('content_type', 'object_id')
Traceback from a ManyToManyField:
>>> ModelB.objects.defer('model_a')
Traceback (most recent call last):
  File "<console>", line 1, in <module>
  File "/usr/local/lib/python3.11/site-packages/django/db/models/query.py", line 374, in __repr__
    data = list(self[: REPR_OUTPUT_SIZE + 1])
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/query.py", line 398, in __iter__
    self._fetch_all()
  File "/usr/local/lib/python3.11/site-packages/django/db/models/query.py", line 1881, in _fetch_all
    self._result_cache = list(self._iterable_class(self))
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/query.py", line 91, in __iter__
    results = compiler.execute_sql(
              ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 1547, in execute_sql
    sql, params = self.as_sql()
                  ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 734, in as_sql
    extra_select, order_by, group_by = self.pre_sql_setup(
                                       ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 84, in pre_sql_setup
    self.setup_query(with_col_aliases=with_col_aliases)
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 73, in setup_query
    self.select, self.klass_info, self.annotation_col_map = self.get_select(
                                                            ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 256, in get_select
    select_mask = self.query.get_select_mask()
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/query.py", line 772, in get_select_mask
    return self._get_defer_select_mask(opts, mask)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/query.py", line 728, in _get_defer_select_mask
    field = opts.get_field(field_name).field
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'ManyToManyField' object has no attribute 'field'
Traceback from defering a GenericForeignKey:
>>> ModelC.objects.defer('generic_model')
Traceback (most recent call last):
  File "<console>", line 1, in <module>
  File "/usr/local/lib/python3.11/site-packages/django/db/models/query.py", line 374, in __repr__
    data = list(self[: REPR_OUTPUT_SIZE + 1])
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/query.py", line 398, in __iter__
    self._fetch_all()
  File "/usr/local/lib/python3.11/site-packages/django/db/models/query.py", line 1881, in _fetch_all
    self._result_cache = list(self._iterable_class(self))
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/query.py", line 91, in __iter__
    results = compiler.execute_sql(
              ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 1547, in execute_sql
    sql, params = self.as_sql()
                  ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 734, in as_sql
    extra_select, order_by, group_by = self.pre_sql_setup(
                                       ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 84, in pre_sql_setup
    self.setup_query(with_col_aliases=with_col_aliases)
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 73, in setup_query
    self.select, self.klass_info, self.annotation_col_map = self.get_select(
                                                            ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/compiler.py", line 256, in get_select
    select_mask = self.query.get_select_mask()
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/query.py", line 772, in get_select_mask
    return self._get_defer_select_mask(opts, mask)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/django/db/models/sql/query.py", line 728, in _get_defer_select_mask
    field = opts.get_field(field_name).field
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'GenericForeignKey' object has no attribute 'field'
PD:
In version 4.1.9 it is working without any error, but in versions 4.2.0 and 4.2.1 raises the
AttributeError