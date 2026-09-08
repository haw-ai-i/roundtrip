Changing an IntegerField to a ForeignKey generates incorrectly ordered migration operations if the field is in unique_together

Description
(last modified by
Ed Morley
)
Replacing an integer field with a foreign key of the same name, results in an
OperationalError
when creating/applying the migration.
This affects Django master + v1.11.10, and both the SQLite and MySQL backends (others not tested).
STR:
Git clone
​
https://github.com/edmorley/django-migration-int-to-fk-testcase
pip install https://github.com/django/django/archive/master.zip
./manage.py migrate
cp testapp/models_new.py testapp/models.py
./manage.py makemigrations --name broken_migration
./manage.py migrate
Expected:
New migration is created/applied successfully, which converts from the
​
original model
to the
​
new model
.
Actual:
The new
0002_broken_migration.py
migration incorrectly lists the
AddField
operation before the
RemoveField
operation...
operations
=
[
migrations
.
AddField
(
model_name
=
'bar'
,
name
=
'foo'
,
field
=
models
.
ForeignKey
(
null
=
True
,
on_delete
=
django
.
db
.
models
.
deletion
.
CASCADE
,
to
=
'testapp.Foo'
),
),
migrations
.
RemoveField
(
model_name
=
'bar'
,
name
=
'foo_id'
,
),
migrations
.
AlterUniqueTogether
(
name
=
'bar'
,
unique_together
=
{(
'name'
,
'foo'
)},
),
]
Which results in an exception at step 6...
$
./manage.py
migrate
Operations
to
perform:
Apply
all
migrations:
admin,
auth,
contenttypes,
sessions,
testapp
Running
migrations:
Applying
testapp.0002_broken_migration...Traceback
(
most
recent
call
last
)
:
File
".../site-packages/django/db/backends/utils.py"
,
line
83
,
in
_execute
return
self.cursor.execute
(
sql
)
File
".../site-packages/django/db/backends/sqlite3/base.py"
,
line
290
,
in
execute
return
Database.Cursor.execute
(
self,
query
)
sqlite3.OperationalError:
duplicate
column
name:
foo_id
Additional notes:
Without the
unique_together
on model
Bar
, the bug does not occur.
This affects both the SQLite backend and the MySQL backend (others not tested).
At time of testing, django master was at revision
6d794fb76212bb8a62fe2cd97cff173054e1c626
.
The above was using Python 3.6.2.