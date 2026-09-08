Hashing list in Q objects when using __in lookup

Description
This bug was previously reported here -
#29643
.
However I am still getting this error upon rendering QuerySets that use the Q object and include the
__in
filter in the most recent release of django, 2.1.2.
Here is my reproduction of the bug on master:
Code highlighting:
>>>
q
=
Q
(
a__in
=
[
1
,
2
])
>>>
q
.
__hash__
()
Traceback
(
most
recent
call
last
):
File
"<stdin>"
,
line
1
,
in
<
module
>
File
"/Users/aspalding/Documents/django/django/utils/tree.py"
,
line
89
,
in
__hash__
for
child
in
self
.
children
TypeError
:
unhashable
type
:
'list'
Therefor the minimal reproduction for
NodeTest
would look like:
Code highlighting:
hash
(
Node
([(
'a'
,
[
1
,
2
])]))