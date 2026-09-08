Fix select_related() + defer() MTI tests marked as @expectedFailure

Description
A couple tests were added as
@expectedFailure
in
f51e409a5fb34020e170494320a421503689aea0
. They raise a message like: "Invalid field name(s) given in select_related: 'child1'. Choices are: child1, child2" so I think it looks like a bug which should be fixed.