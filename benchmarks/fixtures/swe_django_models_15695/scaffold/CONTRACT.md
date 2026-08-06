# Implementation target
Write the module at `django/db/migrations/operations/models.py`.

## `django/db/migrations/operations/models.py`
Other modules import these names from it, so they MUST exist with these exact names:
- `AddConstraint`
- `AddIndex`
- `AlterIndexTogether`
- `AlterModelManagers`
- `AlterModelOptions`
- `AlterModelTable`
- `AlterOrderWithRespectTo`
- `AlterTogetherOptionOperation`
- `AlterUniqueTogether`
- `CreateModel`
- `DeleteModel`
- `IndexOperation`
- `ModelOperation`
- `ModelOptionOperation`
- `RemoveConstraint`
- `RemoveIndex`
- `RenameIndex`
- `RenameModel`

Implement them to satisfy the specification. Do not write tests.
