Completeness experiment (does uplift track completeness?)

The hypothesis under test is that a complete description carries the value: the
more completely a description captures what the agent needs, the more the agent
succeeds. We test this with the same comprehension-only settings task, scoring
per value (how many of five documented defaults the agent returns correctly), so
that the result is a gradient rather than a single pass or fail.

Setup. The codebase is settings.py with an unimplemented _default(key). We give
the agent descriptions at graded completeness: none, one value, three values, and
all five. Agent: gemini-2.5-flash-lite, N=5, scored on values correct out of five.

Result. The agent's score rises exactly with completeness: none scores 0 of 5,
one-value scores 1 of 5, three-value scores 3 of 5, and the full description
scores 5 of 5, deterministically across runs. The agent knows precisely what the
description conveys and nothing more, so uplift tracks completeness directly.

Together with the compactness result, this supports the thesis that a compact but
complete description carries the value: completeness drives uplift, while extra
verbosity beyond completeness adds nothing. Completeness is also measurable as the
roundtrip fidelity of the description, connecting this to the Stage 1 benchmark.
