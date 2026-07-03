Compactness experiment (does verbosity add value?)

The hypothesis under test is that a compact but complete description carries the
most value, and that extra verbosity should not add anything. We test this with a
comprehension-only task, so that success depends on whether the description
conveyed the facts rather than on the agent's coding ability.

Setup. The codebase is settings.py with an unimplemented _default(key). The
documented default values exist only in the description. The task is to implement
_default so that get() returns those defaults. Implementation is trivial (a dict
lookup), which isolates description quality. Agent: gemini-2.5-flash-lite, N=8.

Result. With no description the agent passes 0 of 8. With the compact 38-word
description it passes 8 of 8. With a verbose 664-word description carrying the same
facts it also passes 8 of 8. The compact description conveys the information as
effectively as one seventeen times longer. No-description runs invent wrong
defaults; compact runs use the exact documented values. Verbosity adds no uplift.

Note. This is a comprehension-only task by design, chosen to isolate description
quality from weak-agent implementation variance. On tasks needing a non-trivial
coding step, weak agents recite a stated contract but implement it inconsistently,
which confounds the signal; the trivial-implementation task removes that confound.
