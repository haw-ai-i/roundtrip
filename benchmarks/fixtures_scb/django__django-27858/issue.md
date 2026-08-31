Stop read-only management commands from attempting to create a django_migrations table

Description
(last modified by
Tim Graham
)
In multiple different projects now, I've needed to connect Django to legacy databases that aren't under Django's control. Even when setting "manage = False" in all affected models and configuring the DB router to never allow migrate in the legacy database, Django "makemigrations" still attempts to create the django_migrations table, causing permission errors in my use case.
The pull request changes MigrationRecorder is so that for read-only operations, if the django_migrations table doesn't exist, it's assumed that no migrations have been applied, instead of trying to create it. This applies to all migration commands.
Django has always had the problem of being "opinionated", meaning there's often fighting involved if you don't exactly follow The True Django Way. :) This patch is a small step in making Django more flexible.