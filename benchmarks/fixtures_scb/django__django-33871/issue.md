JSONField with default is not detected as changed when invalidated in inlines.

Description
(last modified by
Raphael
)
Apparently the JSONField field modification in a TabularInline is ignored after a validation error.
To reproduce I attached the generated project based of the basic Django tutorial with changes to use a JSONField and TabularInline
user: admin
password: admin
Sequence:
Edit the Question
Change both Text field to "test"
Change both JsonField to 'test' (Any Valid Json)
Save
Edit again
Change both two JsonField to 'test 123' (Any Valid Json)
Delete text from Text field of the second item
Save
Error message will appear
Set the Choice Text field to 'test 123' of the second item
Save
Edit again, only the second JsonField was changed to 'test 123' (Any Valid Json)