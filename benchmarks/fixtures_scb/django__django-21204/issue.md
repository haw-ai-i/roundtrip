Query.defer() failure - deferred columns calculated per table instead per alias

Description
In sql.compiler the deferred columns are calculated per table. This doesn't work correctly as it is possible to have the same table multiple times in the query. For example (using models from tests/queries/models.py):
qs = Tag.objects.select_related(
            'parent', 'parent__parent'
        ).defer(
            'parent__name', 'parent__parent__category'
        )
Currently this causes both name and category to be deferred for the base model, its parent, and parent's parent. The correct interpretation is that for base model all columns are loaded, for parent category is loaded, name is deferred and for parent's parent name is loaded and category is deferred.
The proper solution is to key the only_load dictionary by alias instead of db_table. This doesn't look to be particularly easy case to solve, as both only_load's construction and usage are somewhat complex.
The bug has likely existed for as long as defer has existed. I'll mark this as master as I don't see a reason why this must be backpatched. The user-visible result of this bug is that more queries than expected are executed in some rare situations, so this isn't too severe.
Failing test case at:
​
https://github.com/akaariai/django/compare/only_load_bug