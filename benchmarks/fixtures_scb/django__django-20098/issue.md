Add validation for models with the same db_table

Description
When declaring two models using a custom db_table setting in the Meta class, I found out that django failed to detect that the two models declared the same db_table and subsequently it will fail on syncdb when trying to create the same table twice.
This, of course, was introduced by copy&paste, but at least django should report this on validate instead of failing when trying to syncdb.