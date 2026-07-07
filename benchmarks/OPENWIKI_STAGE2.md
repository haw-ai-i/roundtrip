OpenWiki in the Stage 2 agent-task setting

The regeneration baseline showed OpenWiki's documentation gives lower roundtrip fidelity than
our descriptions. This experiment asks the complementary question: in the Stage 2 setting, where
a weak agent implements a code change, are OpenWiki's docs as useful as ours?

We use the novel2 fixture, where the decision contract is deliberately absent from the code's
behavior and present only in the documentation. The policy engine's is_allowed method simply
trusts the order rules are passed in; the intended contract (evaluate by priority, and at equal
priority let deny override allow) is not implemented in the code. The task asks the agent to add
a resolve method that applies this contract regardless of input order. Success therefore depends
on the agent being told the contract, since it cannot read it from the code.

We compared three conditions with the weak agent (gemini-2.5-flash-lite), four runs each:

  A  no documentation          0/4
  B  our description           4/4
  C  OpenWiki documentation    0/4

OpenWiki's documentation does not help: the agent fails just as it does with no documentation.
The reason is visible in the docs themselves. OpenWiki accurately documented what the code does,
noting that is_allowed "does not use this priority" and processes rules in input order. That is
the observed behavior, but it is the opposite of the contract the task requires. Our description
states the contract (deny-override at equal priority); OpenWiki's does not, because the contract
is not present in the code for it to observe.

This supports the paper's central point from the agent-task side. A description is useful to an
agent when it supplies intent and contract beyond what the code exhibits. A documentation tool
that reports observed behavior captures the code as it is, not the contract it is meant to honor,
so it does not help the agent on tasks that turn on that contract.
