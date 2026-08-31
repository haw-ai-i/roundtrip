Annotation's original field-name can clash with result field name over aggregation

Description
This is a bit of a continuation of
#34123
With current Django main, if one aggregates over a model, while adding annotations of related fields; and an annotation comes from a field with the same name as a result field, it breaks.
This is easier to explain by example; consider this test, added to the
aggregation_regress
tests, so it uses their models;
Book
carries a FK to
Publisher
, a M2M to
Author
named
authors
, and a FK to
Author
(supposedly picking one of the related authors) named
contact
.
def
test_aggregate_and_annotate_duplicate_columns
(
self
):
results
=
Book
.
objects
.
values
(
'isbn'
)
.
annotate
(
name
=
F
(
'publisher__name'
),
contact_name
=
F
(
'contact__name'
),
num_authors
=
Count
(
'authors'
),
)
self
.
assertTrue
(
results
)
The field
isbn
is not defined as unique, it was chosen in order to make sure there's an aggregation on the main table and not some sort of subquery -- and also, to get the
Book
model's own
name
field out of the way.
This blows up on Sqlite:
======================================================================
ERROR: test_aggregate_and_annotate_duplicate_columns (aggregation_regress.tests.AggregationTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/django/django/django/db/backends/utils.py", line 89, in _execute
    return self.cursor.execute(sql, params)
  File "/home/django/django/django/db/backends/sqlite3/base.py", line 378, in execute
    return super().execute(query, params)
sqlite3.OperationalError: ambiguous column name: name
and on Postgres
======================================================================
ERROR: test_aggregate_and_annotate_duplicate_columns (aggregation_regress.tests.AggregationTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/django/django/django/db/backends/utils.py", line 89, in _execute
    return self.cursor.execute(sql, params)
psycopg2.errors.AmbiguousColumn: column reference "name" is ambiguous
LINE 1: ..._id") GROUP BY "aggregation_regress_book"."isbn", "name", "c...
                                                             ^
Note that if we change the
name
above to something else -- e.g.
pub_name
=
F
(
'publisher__name'
),
then things seem to be working fine. Conversely, if we pick another related field for the name annotation:
name
=
F
(
'publisher__num_awards'
),
then things stay broken.
This used to work, and now it doesn't. I've bisected this regression to
b7b28c7c189615543218e81319473888bc46d831
.
Thanks
​
Matific
for letting me work on this.