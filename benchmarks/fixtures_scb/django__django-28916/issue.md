Changing the type of a ForeignKey and changing unique_together creates migrations in the wrong order, causing migrations to fail

Description
(last modified by
fredley
)
models.py before:
class MyModel(models.Model):
    fka = models.ForeignKey(SomethingA, ...)
    date = models.DateField()

    class Meta:
        unique_together = ('fka', 'date')
models.py after:
class MyModel(models.Model):
    fkb = models.ForeignKey(SomethingB, ...)
    date = models.DateField()

    class Meta:
        unique_together = ('fkb', 'date')
This can result in an automatically created migration (using
manage.py makemigrations
) that looks like this:
operations = [
    migrations.AddField(
        model_name='mymodel',
        name='fkb',
        field=models.ForeignKey(... to='myapp.somethingb'),
    ),
    migrations.RemoveField(
        model_name='mymodel',
        name='fka',
    ),
    migrations.AlterUniqueTogether(
        name='mymodel',
        unique_together={('fkb', 'date')},
    ),
]
This migration fails, because
AlterUniqueTogether
needs to come before
RemoveField
, as it references
fka
. This is hard to debug, and can only be fixed by manually reordering the migration operations.