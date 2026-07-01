# Point 2: description-as-documentation for a weak agent

Setup: weak agent (gemini-2.5-flash-lite) implements a task on a codebase,
with vs without the NL description in context. Effect sought = A fails, B passes.

## Run 1: contains + simplify_result task
Both conditions PASSED. Flash-lite solved the task WITHOUT the description.
Reason: Contains is a well-known sympy class; the weak agent already knows it,
so raw code suffices and the description adds nothing.

Implication: confirms the need (Igor's suggestion) to use a larger model (Pro)
to MATERIALIZE A NOVEL codebase the weak agent has not seen — otherwise training
knowledge masks any effect from the description. Contains is unsuitable (too known).

Next: Pro-materialize a novel codebase (score 1.0), pick a task flash-lite fails
on raw code, test whether the description rescues it.
