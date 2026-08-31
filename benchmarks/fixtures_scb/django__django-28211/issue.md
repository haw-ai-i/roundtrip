Inefficient query produced when using OR'ed Q objects

Description
(last modified by
Tom Forbes
)
When using OR'ed Q objects in a
.filter()
call Django could be more intelligent about the query it produces.
For example, the following two queries both produce
LEFT OUTER JOIN
:
SomeModel.objects.filter(Q(related_objects__field=1) | Q(related_objects__other_field=1)
SomeModel.objects.filter(Q(related_objects__field=1) | Q())
In the case of the second query it could be reduced to a
INNER JOIN
as the
OR
is redundant and it is functionally the same as a
.filter(related_objects__field=1)
.
It is also quite a common pattern to do:
filters = Q()
if condition:
   filters |= Q(x=1)
if other_condition:
   filters |= Q(y=2)
And with the current implementation it will always produce a query that assumes
filters
is a valid
OR
. Django should/could be more intelligent and detect if there is only one
OR
condition, and reduce it.