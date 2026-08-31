Removing a field from index_together/unique_together and from the model generates a migration that crashes

Description
In Django 1.9.11, after deleting a model field and removing it from
index_together
attribute, the
makemigrations
command generates a broken migration code with RemoveField operation preceding AlterIndexTogether operation. That causes the following
migrate
command to raise an exception while trying to apply the generated migration.