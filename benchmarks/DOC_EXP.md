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

## Run 2: novel codebase (policyengine, deny-override contract)
Both agents implemented `explain` correctly by reusing the existing `_ordered()`
helper. A (no desc) PASSED; B (with desc) produced the SAME correct method but
corrupted the file by pasting description markdown into the source (syntax error).

Design difficulty (now hit twice): to make the description NECESSARY, the code must
hide its own contract. But well-structured code (a helper like `_ordered()`) already
encodes the contract, so a weak agent reuses it and succeeds without the description.
Hiding the contract means degrading the code, which changes what's being tested.

Open question for Igor: how to design a codebase where good documentation is
genuinely necessary for a weak agent, without simply making the code bad.

## Run 3: contract only in description (novel2) — EFFECT DEMONSTRATED
Codebase: policyengine variant with NO _ordered() helper - is_allowed loops in
list order, and the priority + deny-override + default-deny contract lives ONLY
in the description. Oracle passes rules UNSORTED.

| condition | resolve() implementation | oracle |
|---|---|---|
| A (no desc) | naive list-order loop (copies is_allowed) | FAIL (deny-override) |
| B (with desc) | sorted(-priority, deny-before-allow) | PASS |

The description carried the contract the code did not expose, flipping the weak
agent (flash-lite) from a wrong implementation to a correct one. First clean
demonstration of description-as-documentation improving weak-agent task success.

Note: weak model pastes description markdown into the file; extractor strips
trailing non-code. Next: repeat for stability + more tasks/codebases for a rate.
